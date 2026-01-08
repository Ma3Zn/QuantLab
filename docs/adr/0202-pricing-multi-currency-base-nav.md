# ADR-0202 — Multi-currency valuation with base-currency NAV (Policy B)

    **Status:** Accepted
    **Date:** 2026-01-08

    ## Context
    QuantLab portfolios may contain instruments in multiple currencies.
Downstream modules (risk/stress/optimization) typically require a single base-currency NAV and exposure decomposition.
Currency conversion must be explicit and auditable.

    ## Options considered
    1. Single-currency portfolios only (error if multiple currencies).
2. Multi-currency: report NAV per currency only; no conversion.
3. Multi-currency: compute base-currency NAV via explicit FX conversion and also report per-currency breakdown.

    ## Decision
    Choose option 3.
Portfolios declare a `base_currency`.
Pricing computes:
- native-currency notional per position
- base-currency notional per position
- portfolio NAV in base currency
and includes a per-currency breakdown for explainability.

    ## Consequences
    - Pricing must depend on FX market data.
- Outputs must record FX inputs (pair, inversion, effective rate).
- Missing FX becomes a first-class failure mode with typed errors.
- This increases complexity slightly but avoids later refactors in risk/stress layers.

    ## Notes / Migration
    - Any breaking change must bump the relevant schema version(s) and include a short migration note.
