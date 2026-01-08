# ADR-0203 — Canonical FX quote convention using FX.EURUSD (USD per EUR)

    **Status:** Accepted
    **Date:** 2026-01-08

    ## Context
    Supporting EUR and USD requires a stable FX quote convention.
Data providers may report FX pairs in different base/quote directions.
Without a canonical convention, conversions become ambiguous and hard to audit.

    ## Options considered
    1. Store both EURUSD and USDEUR series and pick whichever matches the need.
2. Store a single canonical series and invert when necessary.
3. Store FX as a full graph and triangulate for all currencies (overkill for MVP).

    ## Decision
    Choose option 2 for the MVP.
The canonical FX series is `FX.EURUSD`, quoted as USD per 1 EUR.
USD→EUR conversion uses the inverse of this rate.
The output must record whether inversion was applied and the effective rate used.

    ## Consequences
    - Only one FX time series is required for EUR/USD support.
- Inversion becomes part of the explainability contract.
- Extending beyond EUR/USD will require either additional canonical pairs or an FX graph module.

    ## Notes / Migration
    - Any breaking change must bump the relevant schema version(s) and include a short migration note.
