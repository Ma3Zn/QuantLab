# ADR-0207 — Valuation outputs are typed and serialized as canonical JSON

    **Status:** Accepted
    **Date:** 2026-01-08

    ## Context
    Pricing outputs must be usable by downstream modules and also directly reportable.
They must be stable across runs given the same inputs.
They must be auditable and snapshot-testable.

    ## Options considered
    1. Return untyped dicts and rely on ad-hoc conventions.
2. Return typed models (Pydantic v2) and define a canonical JSON schema contract.
3. Return pandas DataFrames only (harder to version and explain).

    ## Decision
    Choose option 2.
`PositionValuation` and `PortfolioValuation` are typed models.
They serialize to JSON with stable field meanings and explicit schema versions.

    ## Consequences
    - Enables golden snapshot tests.
- Improves explainability and long-term maintainability.
- Requires disciplined schema evolution (version bumps and migrations).

    ## Notes / Migration
    - Any breaking change must bump the relevant schema version(s) and include a short migration note.
