# ADR-0201 — Pricing scope for MVP (linear instruments only)

    **Status:** Accepted
    **Date:** 2026-01-08

    ## Context
    QuantLab requires a deterministic mark-to-market layer to support later risk and stress modules.
Early inclusion of curves, accruals, or nonlinear derivatives tends to create premature coupling and fragile assumptions.
The instruments module is complete and provides pure domain objects.
Pricing must remain a pure computation layer.

    ## Options considered
    1. Implement broad pricing coverage early (bonds with curves, options, structured products).
2. Implement only linear mark-to-market pricing first (cash, equities, linear futures).
3. Implement “placeholders” for many asset classes without correct economics (toy coverage).

    ## Decision
    Choose option 2.
The MVP pricing module prices only linear instruments:
cash, equities, tradable index proxies, and linear futures.
Anything requiring curves, accruals, or nonlinear payoffs is explicitly out of scope in the MVP.

    ## Consequences
    - The layer is small, testable, and interview-defensible.
- Risk and stress can be built on stable valuation outputs.
- Fixed income and derivatives will be added only after their input contracts (curves, volatility surfaces) are explicitly defined.

    ## Notes / Migration
    - Any breaking change must bump the relevant schema version(s) and include a short migration note.
