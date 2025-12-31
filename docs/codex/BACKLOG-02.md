# QuantLab Backlog — Data Access + Alignment (Raw + Guardrails)

**Scope:** Extend `src/data/` to provide a production-grade data access façade with market-calendar alignment, raw-only prices, guardrails, lineage, and robust tests.

**Start PR numbering:** PR-16

## Acceptance criteria (global)
By the end of PR-21:
- `MarketDataService.get_timeseries()` returns aligned daily time series indexed by `date` for multiple assets.
- Market calendar is used for the target index.
- Only raw prices are supported; suspect corporate actions are detected and reported (no correction).
- Persistent cache exists (parquet + manifest) with deterministic request hash and replay.
- Unit + property + integration tests pass; golden snapshots exist for manifests/bundles.

---

## PR-16 — Add typed request/policy models + deterministic request hashing

### Goal
Create the core typed, serializable request/policy models and a canonical hashing scheme for caching and reproducibility.

### Tasks
1. Create module `src/data/schemas/requests.py`:
   - `AssetId` (alias/type)
   - `CalendarSpec`, `AlignmentPolicy`, `MissingDataPolicy`, `ValidationPolicy`
   - `TimeSeriesRequest` (ensure JSON serialization)
2. Create `src/data/schemas/quality.py`:
   - `QualityFlag` constants
   - `QualityReport` (dataclass / pydantic) + `to_json()` / `from_json()`
3. Create `src/data/schemas/lineage.py`:
   - `LineageMeta`
4. Implement `src/data/transforms/hashing.py`:
   - `canonical_request_dict(request) -> dict`
   - `request_hash(request) -> str` (sha256)
   - Ensure order-invariance for assets/fields
5. Add `src/data/schemas/errors.py` with typed exceptions.

### Tests (must be included in this PR)
- `tests/data/test_request_hashing.py`:
  - Hash stability across permutations of `assets` and `fields`.
  - Hash changes when any policy field changes.
- `tests/data/test_models_serialization.py`:
  - Round-trip JSON serialization for Request/Policies/QualityReport/LineageMeta.

### Definition of done
- All new models are typed, serializable, documented in docstrings.
- Hashing is deterministic and order-invariant.
- Tests green.

---

## PR-17 — Market calendar adapter + alignment transform (date index)

### Goal
Introduce a calendar abstraction and implement deterministic alignment to target market sessions.

### Tasks
1. Add `src/data/transforms/calendars.py`:
   - `TradingCalendar` protocol/interface
   - `MarketCalendarAdapter` using `pandas_market_calendars` (dependency update in `pyproject.toml`)
   - `sessions(start, end) -> list[date]`
2. Add `src/data/transforms/alignment.py`:
   - `build_target_index(request) -> pd.Index` of `date`
   - `align_frame(raw_frame, target_dates, missing_policy) -> aligned_frame`
   - Missing policies: `NAN_OK`, `DROP_DATES`, `ERROR`
3. Add minimal docs: `src/data/transforms/README.md` describing alignment semantics.

### Tests
- `tests/data/test_calendar_sessions.py`:
  - For a known market (e.g. XNYS), ensure a known holiday is excluded (choose a specific date).
- `tests/data/test_alignment_policies.py`:
  - Synthetic series with missing dates → verify behavior per policy.

### Definition of done
- Target calendar sessions drive the output index.
- Alignment deterministic; tests cover edge cases.

---

## PR-18 — Validation + guardrails (raw + suspect corporate actions)

### Goal
Implement validation layer producing `QualityReport` with flags, including split-like jump detection.

### Tasks
1. Add `src/data/transforms/validation.py`:
   - `validate_and_flag(aligned_frame, validation_policy) -> (frame, QualityReport)`
   - Dedup handling (LAST/FIRST/ERROR) with `DUPLICATE_RESOLVED` flag
   - Nonpositive price detection (error if enabled)
   - Compute simple returns on close; flag `SUSPECT_CORP_ACTION` if abs(return) >= threshold
   - Optional `OUTLIER_RETURN` if `max_abs_return` set
2. Ensure flags are aggregated into `QualityReport` per asset.
3. Add structured logging hooks (request_hash/asset) without excessive verbosity.

### Tests
- `tests/data/test_validation_dedup.py`
- `tests/data/test_validation_nonpositive.py`
- `tests/data/test_guardrails_corp_action.py`:
  - Construct synthetic split jump (e.g., price halves) and assert flagging.
- `tests/data/test_quality_report_contents.py`

### Definition of done
- No corrections applied; only flagging + deterministic errors.
- QualityReport is meaningful and JSON-serializable.

---

## PR-19 — Parquet store + manifest (versioned cache) + replay

### Goal
Add storage layer to persist per-asset parquet and per-request manifest; enable replay via request_hash.

### Tasks
1. Add `src/data/storage/parquet_store.py`:
   - `ParquetMarketDataStore(root_path: Path)`
   - `write_asset_frame(asset_id, frame, meta) -> list[Path]`
   - `read_assets(asset_ids, start, end, fields) -> frames`
2. Add `src/data/storage/manifests.py`:
   - `write_manifest(request_hash, LineageMeta, QualityReport, paths)`
   - `read_manifest(request_hash) -> manifest dict`
3. Add `src/data/storage/layout.py` to centralize path conventions.
4. Ensure manifests include:
   - request_json, request_hash, provider, ingestion_ts, as_of, dataset_version, code_version (optional)
5. Add gitignore note / docs for `data/cache/`.

### Tests
- `tests/data/test_parquet_store_roundtrip.py`
- `tests/data/test_manifest_roundtrip.py`
- Golden snapshot: `tests/data/golden/manifests/<hash>.json` (freeze times or strip timestamps deterministically).

### Definition of done
- Store can read/write deterministic data.
- Manifest exists and is consistent with stored files.

---

## PR-20 — MarketDataService façade (provider + store + transforms composition)

### Goal
Implement the orchestration layer that the rest of QuantLab will depend on.

### Tasks
1. Add `src/data/service.py`:
   - `MarketDataService(provider, store, calendar)`
   - `get_timeseries(request) -> TimeSeriesBundle`
   - Cache-first: if manifest + data exist, read; else fetch→write→read
2. Define `TimeSeriesBundle` in `src/data/schemas/bundle.py`
3. Implement a **provider protocol** in `src/data/providers/base.py`:
   - `fetch_eod(provider_symbols, start, end, fields) -> pd.DataFrame`
4. Add a `SymbolMapper` minimal in `src/data/providers/symbols.py`:
   - map `AssetId -> provider_symbol` from config/dict.
5. Ensure the service never returns raw provider frames; always aligned+validated.

### Tests
- `tests/data/test_service_cache_miss_then_hit.py` with a stub provider:
  - first call triggers fetch+write, second call hits cache and does not call provider
- `tests/data/test_service_bundle_schema.py`:
  - columns MultiIndex structure, index is `date`, lineage present, quality present.

### Definition of done
- One public entrypoint exists for downstream layers.
- Composition and contracts are stable.

---

## PR-21 — Robust testing + documentation + example script (end-to-end)

### Goal
Make the extension defensible: clear docs, ADR, property-based tests, and an example “data pull + inspect” workflow.

### Tasks
1. Documentation
   - `src/data/README.md`: responsibilities, non-goals, public API, examples, failure modes.
   - `docs/adr/ADR-00X-raw-prices-guardrails.md`: decision record explaining raw-only + guardrails.
2. Property-based tests (Hypothesis)
   - `tests/data/test_properties_normalization.py`: uniqueness/monotonic/idempotence.
3. Integration test end-to-end
   - `tests/data/test_e2e_service_to_manifest.py`
4. Example script
   - `scripts/data_pull_demo.py`:
     - loads a simple config
     - pulls 2–3 assets
     - prints coverage, suspect CA dates
     - writes a small report JSON to `data/sample/` (committable small output)
5. Optional: minimal CLI hook in `tools/cli.py` (only if already planned); otherwise skip.

### Definition of done
- A new user can run the example and understand outputs.
- Tests provide confidence against regressions.
- ADR documents the trade-off and limitations.

---

## Notes for Codex execution
- Each PR must be self-contained, with passing tests at the end of the PR.
- Avoid refactors across PR boundaries: keep interfaces stable; add new modules rather than reshaping existing ones unless necessary.
- No silent fallbacks: missing provider symbol mapping or calendar errors must raise typed exceptions with actionable messages.
