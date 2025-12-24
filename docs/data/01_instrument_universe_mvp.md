# Step 1 — Instrument Universe (MVP) + Identifier Policy

## Goal
Define a minimal but *globally usable* instrument universe for the first end-to-end pipeline, and specify an identifier policy that prevents vendor lock-in and reduces downstream refactors.

## What this step includes
- **MVP asset classes** and their required fields at EOD frequency.
- **Internal identifiers** (`instrument_id`) and how external identifiers map to them.
- Normalization rules for tickers, venues, currencies, and timezones.

## What this step excludes
- Intraday data (tick or minute bars).
- Futures continuous series, roll rules, and contract chains.
- Options chains, implied vols, vol surfaces.
- Robust survivorship-safe universes (handled later via a dedicated policy + datasets).

---

## MVP Universe

### A) Cash Equities (Global) — EOD Bars
**Purpose**
- Provide a broad, interpretable baseline for portfolio, risk, and walk-forward validation.

**Required fields**
- `open`, `high`, `low`, `close`, `volume`
- Optional (recommended): `adj_close` *or* explicit adjustment factors dataset (see notes).

**Coverage principles**
- Multi-venue support via **MIC** (ISO 10383) and explicit `exchange_timezone` metadata.
- Currency is per listing (e.g., a company with multiple listings generates multiple instruments).

### B) FX Spot — Daily
**Purpose**
- Currency normalization for global portfolios, basic stress tests, and reporting in a base currency.

**Required fields**
- `mid` (preferred), or `close` where mid is unavailable.
- Optional: `bid`, `ask` (kept only if the provider truly supports it at daily freq).

**Conventions**
- Currency pair is **BASE/QUOTE** (e.g., EURUSD means 1 EUR = X USD).
- `ts` corresponds to a defined fixing time (provider-specific); store `fixing_convention` in metadata.

---

## Identifier Policy

### Internal identifiers (canonical)
Downstream modules MUST reference instruments by `instrument_id` only.

- Format: opaque, stable string (e.g., `inst_<uuid>`).
- Stability rule: once created, `instrument_id` never changes; mappings evolve via reference tables.

### External identifiers (non-canonical, for mapping)
Store as attributes in an **instrument master** table.

**Equities (listing-level)**
- `isin` (when available), `figi` (when available), vendor symbol
- `ticker` (raw), `mic` (ISO 10383), `exchange` (human label), `currency`
- `company_id` (optional future: entity-level aggregation across listings)

**FX spot**
- `base_ccy`, `quote_ccy`
- `pair_code` (e.g., `EURUSD`), plus vendor pair code if different

### Venue and ticker normalization
- Venue: key by `mic` (not exchange name).
- Ticker: store both `ticker_raw` and `ticker_norm`.
  - `ticker_norm` is **uppercase**, stripped of whitespace, and preserves meaningful punctuation.
- If a provider uses a composite symbol (e.g., “AAPL.O”), store it as `vendor_symbol` and parse into components when possible.

### Time and calendar conventions (MVP)
- Canonical `ts` stored as **UTC**.
- Store exchange timezone as `exchange_timezone` (IANA tz, e.g., `America/New_York`).
- EOD bars are attributed to a `trading_date` (local) and represented with a canonical `ts` (UTC) chosen by policy.
  - MVP policy: canonical `ts = exchange_close_time_local converted to UTC` *when available*, else provider EOD timestamp.

---

## Minimal Instrument Master (conceptual schema)
Each row defines one instrument.

**Required columns**
- `instrument_id` (internal)
- `instrument_type` ∈ {`EQUITY`, `FX_SPOT`}
- `mic` (for EQUITY), `currency` (for EQUITY)
- `base_ccy`, `quote_ccy` (for FX_SPOT)
- `status` ∈ {`ACTIVE`, `INACTIVE`} (MVP; later add `DELISTED`, etc.)

---

## Bias / failure modes (explicitly acknowledged)
- **Survivorship bias** if the initial universe is built from “today’s listings.” MVP accepts this risk; later we add time-valid membership datasets.
- **Corporate actions ambiguity** if `adj_close` is used inconsistently across sources; MVP requires explicit metadata fields.
- **Timezone misalignment** if provider timestamps differ; MVP stores timestamp provenance and adds later a stricter calendar policy.
