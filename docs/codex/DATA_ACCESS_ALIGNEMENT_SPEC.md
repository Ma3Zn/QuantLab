# QuantLab — Data Access + Alignment Extension (Raw + Guardrails)

**Status:** Design specification for implementation (MVP + near-term extensions)
**Scope:** `src/data/` module — *access*, *alignment*, *validation*, *lineage* (no risk/strategy logic)

## 1. Objectives (what “done” means)

### 1.1 Functional objectives
The data layer must provide a **single, stable façade** to retrieve **daily (1D) EOD** market data for multiple assets, aligned to a **market calendar**, returning:

- a **normalized time index** (`date`, not timestamp) aligned to a target market calendar;
- **raw prices only** (no corporate action adjustments);
- **guardrails** that detect and report likely corporate-action discontinuities (split-like jumps) and other quality issues;
- **lineage metadata** sufficient for reproducibility (request hash, as-of, ingestion timestamp, provider, code version if available);
- persisted data in a **versioned cache** (parquet + JSON manifests) with deterministic replays.

### 1.2 Non-goals (explicitly out of scope for this iteration)
- No intraday support (no 1m/5m).
- No corporate action adjustments (no split/dividend correction).
- No FX conversion or cross-currency normalization.
- No portfolio / risk / optimization computations.
- No “smart cleaning” that modifies the economic meaning of prices.

## 2. Architectural constraints (non-negotiable)

- **Separation of concerns:** provider fetching ≠ storage ≠ transforms/validation ≠ façade.
- **Composition over inheritance:** plug providers/stores into a service object.
- **Pure domain objects:** requests/policies/quality reports are serializable and side-effect free.
- **Standardized outputs:** bundle includes `data + meta + quality + lineage`, JSON-serializable.

## 3. Public API (service façade)

### 3.1 Core dataclasses / models
All models must be type-annotated, serializable (JSON), and hashable where required.

#### `AssetId`
- Canonical internal identifier (string), e.g. `EQ:SPY`, `INDEX:^SPX`.
- Mapping to provider symbols is handled separately.

#### `TimeSeriesRequest`
Fields (MVP):
- `assets: list[AssetId]`
- `start: datetime.date` (inclusive)
- `end: datetime.date` (inclusive)
- `frequency: Literal["1D"] = "1D"`
- `fields: set[Literal["close","open","high","low","volume"]]` (MVP default `{"close"}`)
- `price_type: Literal["raw"] = "raw"`
- `calendar: CalendarSpec` (market calendar required)
- `timezone: Literal["UTC"] = "UTC"` (for metadata only; index is `date`)
- `alignment: AlignmentPolicy`
- `missing: MissingDataPolicy`
- `validate: ValidationPolicy`
- `as_of: datetime.datetime | None` (snapshots / replay semantics)

#### `CalendarSpec`
MVP:
- `kind: Literal["MARKET"]`
- `market: str` (e.g. `XNYS`, `XNAS`, `XEUR`)

#### `AlignmentPolicy`
MVP:
- `index_mode: Literal["TARGET_CALENDAR"] = "TARGET_CALENDAR"`

#### `MissingDataPolicy`
MVP fields:
- `policy: Literal["NAN_OK","DROP_DATES","ERROR"] = "NAN_OK"`
- `min_coverage: float = 0.98`
- `asset_drop_policy: Literal["ERROR","DROP_ASSET"] = "ERROR"`

No forward-fill by default.

#### `ValidationPolicy`
MVP fields:
- `no_nonpositive_prices: bool = True` (for price fields)
- `deduplicate: Literal["ERROR","LAST","FIRST"] = "LAST"`
- `max_abs_return: float | None = None` (outlier flagging; not correction)
- `corp_action_jump_threshold: float = 0.40` (absolute return threshold for *suspect* CA)
- `monotonic_index: bool = True`
- `type_checks: bool = True`

#### `QualityFlag`
Enum-like strings:
- `MISSING`
- `DUPLICATE_RESOLVED`
- `OUTLIER_RETURN`
- `SUSPECT_CORP_ACTION`
- `NONPOSITIVE_PRICE`
- `NONMONOTONIC_INDEX`

#### `QualityReport`
JSON-serializable structure containing:
- per-asset coverage (%)
- counts of missing/outlier/duplicate/suspect-CA points
- list of first N problematic dates per asset and flag type
- actions taken (e.g., dedup=LAST)

#### `LineageMeta`
- `request_hash: str`
- `request_json: dict`
- `provider: str`
- `ingestion_ts_utc: str`
- `as_of_utc: str | None`
- `dataset_version: str`
- `code_version: str | None` (git commit if available)
- `storage_paths: list[str]`

### 3.2 Output: `TimeSeriesBundle`
Contains:
- `data: pandas.DataFrame` with:
  - index: `date` (daily)
  - columns: `pd.MultiIndex` with levels `(asset_id, field)`
- `assets_meta: dict[AssetId, dict]` (currency/venue/provider_symbol/reference)
- `quality: QualityReport`
- `lineage: LineageMeta`

### 3.3 Service façade
`MarketDataService.get_timeseries(request: TimeSeriesRequest) -> TimeSeriesBundle`

Rules:
- Checks local store/cache first (by request_hash + as_of rules).
- If missing, fetches from provider, writes to store, generates manifest, then reads back normalized output.
- Always returns aligned/validated bundle, never raw provider frames.

## 4. Calendars and alignment

### 4.1 Calendar adapter
Implement `TradingCalendar` abstraction in `src/data/transforms/calendars.py`:
- `sessions(start: date, end: date) -> pd.DatetimeIndex` or `list[date]` (daily)
- For MVP: rely on `pandas_market_calendars` (or equivalent) via adapter.
- Store canonical `date` list for the target calendar.

### 4.2 Alignment procedure (deterministic)
Given target calendar dates `D`:
1. Reindex each asset series onto `D`.
2. Apply missing policy (NAN_OK / DROP_DATES / ERROR) *after* reindexing.
3. Ensure output index is strictly increasing, unique.

## 5. Guardrails (raw + detection, no correction)

### 5.1 Duplicate handling
If duplicates in provider data for the same `date`:
- If `deduplicate="LAST"` keep last, flag `DUPLICATE_RESOLVED`.
- If `ERROR` raise a typed exception.

### 5.2 Nonpositive prices
If any price field <= 0:
- Flag `NONPOSITIVE_PRICE`
- If `no_nonpositive_prices=True` raise `DataValidationError` unless policy explicitly allows (MVP: raise).

### 5.3 Suspect corporate actions (split-like jumps)
Compute daily returns from raw close:
- simple return: `r_t = P_t / P_{t-1} - 1`
Flag `SUSPECT_CORP_ACTION` for dates where `abs(r_t) >= corp_action_jump_threshold` (default 0.40).
Notes:
- This is a *heuristic*; do not correct prices.
- Include counts and example dates in `QualityReport`.
- Provide an option in policy to treat this as `warning-only` vs `hard error` (MVP: warning-only, but report prominently).

### 5.4 Outlier returns (non-CA)
If `max_abs_return` is set, flag `OUTLIER_RETURN` for `abs(r_t) >= max_abs_return`.

## 6. Storage and versioning

### 6.1 Storage layout (parquet + manifest)
Under project `data/cache/` (gitignored):
- `data/cache/market/<provider>/<asset_id>/1D/part-YYYY.parquet`
- `data/cache/manifests/<request_hash>.json`

Parquet records (per asset):
- `date`
- `open/high/low/close/volume` (subset permitted)
- `vendor_symbol`
- `ingestion_ts_utc`
- optional `source_ts` if provider supplies it

Manifest includes `LineageMeta` + `QualityReport` summary + storage paths.

### 6.2 Deterministic request hashing
`request_hash = sha256(canonical_json(request_without_nondeterministic_fields))`
- Assets sorted
- Fields sorted
- Dates ISO
- Policies fully included
- `as_of` included if specified

## 7. Errors and observability

- Define typed exceptions in `src/data/schemas/errors.py`:
  - `DataError` base
  - `ProviderFetchError`
  - `StorageError`
  - `DataValidationError`
- Logging: structured logs with request_hash, provider, asset_id counts.

## 8. Testing requirements

### 8.1 Unit tests (pytest)
- Request hashing stability and order-invariance
- Calendar sessions correctness (known holiday edges)
- Alignment with missing points under each MissingDataPolicy
- Dedup behavior + flags
- Nonpositive price detection
- Suspect CA flagging on synthetic split jump
- QualityReport JSON serialization

### 8.2 Property-based tests (Hypothesis)
- After normalization: index unique, increasing
- Idempotence: normalize(normalize(x)) == normalize(x)
- Reindex shape equals target calendar length when NAN_OK

### 8.3 Integration tests
- Stub provider returns deterministic frames
- Store writes parquet + manifest, service reads back same content
- Golden manifest snapshot (excluding timestamps if needed; or freeze time)

## 9. Documentation deliverables
- Module README: responsibilities, I/O, non-goals, examples
- ADR: “Raw prices + guardrails (no corporate action adjustment)”
- Example script under `scripts/` fetching 2–3 assets and printing quality/coverage
