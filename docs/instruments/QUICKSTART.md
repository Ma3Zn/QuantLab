# Instruments Quickstart

This quickstart verifies the `instruments/` domain model end-to-end:
- construct instruments and a portfolio snapshot
- validate invariants
- serialize to canonical JSON
- round-trip deserialize

## Steps
1. Ensure dependencies are installed (Pydantic v2, pytest, hypothesis).
2. Run unit tests:
   - `pytest -q tests/unit/instruments`
3. Run golden tests:
   - `pytest -q tests/golden -k instruments` (if filtered)

## Minimal example (conceptual)
- Create a cash instrument and an equity instrument (with a `market_data_id` from `data/`).
- Build a portfolio snapshot at `as_of`.
- Serialize and compare with a reference JSON fixture.
