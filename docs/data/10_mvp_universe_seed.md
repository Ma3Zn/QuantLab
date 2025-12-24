# MVP Instrument Universe Seed

## Goal
Provide a **small but realistic** universe to test ingestion, normalization, calendars, and joins.

---

## Equities (EOD)
Initial seed (indicative):
- XNYS: AAPL, MSFT
- XNAS: NVDA, AMZN
- XLON: VOD
- XPAR: AIR
- XETR: SAP
- XTKS: 7203 (Toyota)

Per instrument:
- MIC
- vendor_symbol
- currency
- timezone_local

Universe size target: ~10–20 equities.

---

## FX Spot
Initial pairs:
- EURUSD
- USDJPY
- GBPUSD
- USDCHF

Fixing convention (MVP):
- Provider EOD fix (explicitly flagged).

---

## Versioning
- Universe defined as a versioned artifact (`universe_v1.yaml`).
- Hash recorded in ingest config and dataset registry.

---

## Known limitations
- Not survivorship-safe.
- No sector/index membership.
