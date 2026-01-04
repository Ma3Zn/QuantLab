# QuantLab — TASKBOARD (Data Access + Alignment Extension: Raw + Guardrails)

This checklist is intended as a **post-backlog verification gate**. Once PR-16…PR-21 are merged, ticking all items below should imply the extension is genuinely complete, reproducible, and defensible.

**Scope:** `src/data/` only — access façade, market-calendar alignment, raw-only prices, guardrails/quality, lineage, storage/cache. No risk/portfolio/strategy logic.

---

## 1) Public contracts and models (PR-16)

### 1.1 Request and policy models
- [x] `TimeSeriesRequest` exists and includes at least:
  - [x] `assets: list[AssetId]`
  - [x] `start: date` inclusive
  - [x] `end: date` inclusive
  - [x] `frequency: "1D"`
  - [x] `fields` (supports at least `close`; can include OHLCV)
  - [x] `price_type: "raw"` (and **only** raw is accepted)
  - [x] `calendar: CalendarSpec(kind="MARKET", market=...)`
  - [x] `alignment: AlignmentPolicy` (MVP: target calendar)
  - [x] `missing: MissingDataPolicy` (NAN_OK / DROP_DATES / ERROR)
  - [x] `validate: ValidationPolicy` (see below)
  - [x] `as_of: datetime | None`
- [x] Policy defaults are conservative and match spec:
  - [x] Missing default does **not** forward-fill.
  - [x] Nonpositive prices are disallowed by default.
  - [x] Deduplicate default is deterministic (e.g., LAST).

### 1.2 Quality / lineage models
- [x] `QualityFlag` definitions exist, including at least:
  - [x] `MISSING`
  - [x] `DUPLICATE_RESOLVED`
  - [x] `OUTLIER_RETURN`
  - [x] `SUSPECT_CORP_ACTION`
  - [x] `NONPOSITIVE_PRICE`
  - [x] `NONMONOTONIC_INDEX`
- [x] `QualityReport` exists and is JSON-serializable; includes:
  - [x] per-asset coverage
  - [x] per-asset counts per flag
  - [x] example dates (bounded list) per flag type
  - [x] actions taken (e.g., dedup policy applied)
- [x] `LineageMeta` exists and includes at least:
  - [x] `request_hash`
  - [x] `request_json`
  - [x] `provider`
  - [x] `ingestion_ts_utc`
  - [x] `as_of_utc` (nullable)
  - [x] `dataset_version`
  - [x] `code_version` (nullable; if available)
  - [x] `storage_paths`

### 1.3 Typed errors
- [x] Typed exceptions exist under `src/data/schemas/errors.py` (or equivalent) and are used consistently:
  - [x] `ProviderFetchError`
  - [x] `StorageError`
  - [x] `DataValidationError`
- [x] Exceptions carry actionable context (asset_id, provider, request_hash, failing dates/counts).

### 1.4 Canonical hashing
- [x] `canonical_request_dict()` exists and:
  - [x] sorts `assets` deterministically
  - [x] sorts `fields` deterministically
  - [x] serializes dates as ISO strings
  - [x] includes all policy fields
  - [x] includes `as_of` if present
- [x] `request_hash()` exists and uses sha256 of canonical JSON.

---

## 2) Market calendar adapter + alignment transform (PR-17)

### 2.1 Market calendar adapter
- [x] `TradingCalendar` abstraction exists.
- [x] `MarketCalendarAdapter` exists and uses a real market calendar library (e.g., `pandas_market_calendars`).
- [x] `sessions(start, end)` returns the correct set of trading **dates** (not timestamps).
- [x] Known market holidays are excluded (validated by test against a specific known holiday).

### 2.2 Alignment semantics
- [x] Target index is derived from the requested market calendar sessions (not weekday fallback).
- [x] Output index type is **pure `date`**.
- [x] Alignment logic is deterministic:
  - [x] reindex each asset onto target dates
  - [x] apply missing-data policy only after reindex
  - [x] ensure uniqueness and monotonicity

### 2.3 Missing data policies
- [x] `NAN_OK` leaves missing values as NaN and reports them.
- [x] `DROP_DATES` drops dates where any required field is missing (define exact semantics and test them).
- [x] `ERROR` raises a typed validation error when missing data exists.
- [x] Coverage computation exists and is consistent with the chosen missing policy.

---

## 3) Validation + guardrails (PR-18)

### 3.1 Deduplication
- [x] Duplicates on the same `date` are handled deterministically (LAST/FIRST/ERROR).
- [x] When dedup occurs, `DUPLICATE_RESOLVED` is present in quality outputs.
- [x] Dedup behavior is tested with synthetic inputs.

### 3.2 Nonpositive price rule
- [x] For price fields (`open/high/low/close`), values `<= 0` are flagged.
- [x] Default behavior raises `DataValidationError` when `no_nonpositive_prices=True`.
- [x] Test coverage includes negative, zero, and borderline cases.

### 3.3 Suspect corporate action detection (raw + heuristic)
- [x] Simple returns are computed from **raw close** as guardrail input: `r_t = P_t / P_{t-1} - 1`.
- [x] `SUSPECT_CORP_ACTION` is flagged when `abs(r_t) >= corp_action_jump_threshold` (default 0.40).
- [x] Behavior is **warning-only** (does not block by default), but is reported prominently.
- [x] A synthetic split-like series is used in tests to confirm flagging.

### 3.4 Outlier returns (non-CA)
- [x] If `max_abs_return` is set, `OUTLIER_RETURN` is flagged when exceeded.
- [x] Outlier flagging does not mutate/correct the data.

### 3.5 QualityReport correctness
- [x] QualityReport aggregates per asset:
  - [x] missing counts
  - [x] duplicates resolved counts
  - [x] suspect CA counts + example dates
  - [x] outlier counts + example dates
- [x] QualityReport JSON round-trip is covered by tests.

### 3.6 Logging / observability
- [x] Structured logs include at least: `request_hash`, `provider`, `asset_id`, key counts.
- [x] Logs are not excessively noisy in normal flows.

---

## 4) Storage + manifests (PR-19)

### 4.1 Storage layout and git hygiene
- [x] Cache root exists under `data/cache/` and is gitignored.
- [x] Parquet path conventions are centralized (single source of truth).
- [x] Per-asset parquet partitioning exists (e.g., by year) and can be read back reliably.

### 4.2 Parquet schema (minimum)
- [x] Stored rows include at least:
  - [x] `date`
  - [x] requested price/volume fields
  - [x] `vendor_symbol`
  - [x] `ingestion_ts_utc`
  - [x] optional `source_ts` if present
- [x] Types are stable (dates, floats, ints) and validated.

### 4.3 Manifest schema and content
- [x] Manifest is written under `data/cache/manifests/<request_hash>.json`.
- [x] Manifest contains:
  - [x] `LineageMeta` (full)
  - [x] request_json
  - [x] provider identifier
  - [x] dataset_version
  - [x] storage_paths (parquet files)
  - [x] quality summary (at least coverage + suspect CA counts)

### 4.4 Replay capability
- [x] Given a request_hash, the system can load data + manifest without calling provider.
- [x] `as_of` semantics are respected or explicitly documented as “best effort” if not fully enforced.

### 4.5 Store + manifest tests
- [x] Parquet write/read round-trip test exists.
- [x] Manifest read/write round-trip test exists.
- [x] Golden snapshot(s) exist for manifests; timestamps are stable or normalized.

---

## 5) MarketDataService façade (PR-20)

### 5.1 Provider protocol and symbol mapping
- [x] Provider protocol exists (e.g., `fetch_eod(...) -> DataFrame`).
- [x] SymbolMapper exists and:
  - [x] maps `AssetId` to provider symbols deterministically
  - [x] raises a typed error if mapping is missing

### 5.2 Bundle schema
- [x] `TimeSeriesBundle` exists and includes:
  - [x] `data` (DataFrame with MultiIndex columns `(asset_id, field)`)
  - [x] index is `date`
  - [x] `assets_meta`
  - [x] `quality`
  - [x] `lineage`

### 5.3 Cache-first orchestration
- [x] On cache hit, provider is not called (tested with a stub provider).
- [x] On cache miss, service:
  - [x] fetches from provider
  - [x] writes to store
  - [x] writes manifest
  - [x] returns **normalized** bundle (aligned + validated)
- [x] Service never returns raw provider frames.

### 5.4 Failure behavior
- [x] Provider errors surface as `ProviderFetchError` with context.
- [x] Storage errors surface as `StorageError` with context.
- [x] Validation errors surface as `DataValidationError` with context.

### 5.5 Service tests
- [x] Cache miss → hit test exists.
- [x] Bundle structure test exists:
  - [x] MultiIndex columns shape
  - [x] date index type
  - [x] lineage fields present
  - [x] quality present

---

## 6) Robust testing + documentation + example workflow (PR-21)

### 6.1 Documentation
- [x] `src/data/README.md` exists and explains:
  - [x] responsibilities and non-goals
  - [x] public API usage example
  - [x] calendar/alignment semantics
  - [x] missing-data policies
  - [x] guardrails (suspect CA heuristic) and limitations
  - [x] reproducibility / manifests / request_hash
- [x] An ADR exists in `docs/adr/` documenting the decision **raw-only + guardrails**:
  - [x] Decision
  - [x] Context
  - [x] Options considered
  - [x] Trade-offs
  - [x] Consequences and follow-ups

### 6.2 Property-based tests (Hypothesis)
- [x] Property tests exist to verify:
  - [x] output index is unique and monotonic
  - [x] alignment is idempotent (`normalize(normalize(x)) == normalize(x)`)
  - [x] hashing order-invariance holds

### 6.3 Integration tests
- [x] End-to-end test exists: stub provider → service → store → manifest.
- [x] Test asserts:
  - [x] manifest written
  - [x] lineage consistent with request
  - [x] data can be read back on second call without provider

### 6.4 Example script
- [x] A runnable example exists under `examples/scripts/` (or `scripts/`):
  - [x] loads simple mapping/config
  - [x] pulls 2–3 assets
  - [x] prints or writes a small JSON report including coverage and suspect CA dates
  - [x] writes output to `data/sample/` (tiny, committable)

---

## 7) Final “definition of complete” acceptance checks

### 7.1 Functional acceptance
- [x] Calling `MarketDataService.get_timeseries()` with multiple assets returns:
  - [x] a DataFrame indexed by `date`
  - [x] aligned to the requested market calendar
  - [x] raw-only values
  - [x] a QualityReport that flags missing and suspect CA jumps
  - [x] a LineageMeta with request hash, provider, ingestion timestamp, storage paths

### 7.2 Guardrails acceptance
- [x] A synthetic split-like jump produces at least one `SUSPECT_CORP_ACTION` flag and appears in report examples.
- [x] Nonpositive price input fails deterministically with `DataValidationError` (default policy).
- [x] Duplicates are resolved deterministically and flagged.

### 7.3 Reproducibility acceptance
- [x] Re-running the same request (same policies + as_of) produces the same request_hash.
- [x] With cache present, the second run does not hit the provider.
- [x] Manifests enable audit: you can locate the exact stored parquet files and re-load them.

### 7.4 Test suite acceptance
- [x] Unit tests pass.
- [x] Property-based tests pass.
- [x] Integration tests pass.
- [x] Golden manifest snapshots pass.

### 7.5 Engineering acceptance (optional but recommended)
- [ ] Lint/format checks pass (ruff/black if configured).
- [ ] Type checks pass (mypy/pyright if configured).
- [ ] No TODOs or placeholder `pass` remain in code paths exercised by service.

---

## 8) Manual audit steps (quick, high-signal)

- [x] Open a manifest JSON and confirm it includes: request_json, request_hash, provider, ingestion_ts, dataset_version, storage_paths, quality summary.
- [x] Inspect a cached parquet file and confirm `date` is the primary time key and types look correct.
- [x] Run the example script and verify it prints (or writes) coverage + suspect CA dates for at least one asset.
- [x] Trigger a deliberate error (missing symbol mapping) and confirm a typed exception with actionable message.

---

## 9) Notes / known limitations (must be explicitly documented)

- [x] Survivorship bias risk is acknowledged (tickers/delistings).
- [x] Corporate actions are not corrected; suspect events are only flagged.
- [x] Vendor “close” semantics may vary (official close vs last vs NAV vs settlement) and are tracked as metadata when available.
