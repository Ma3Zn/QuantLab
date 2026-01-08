# ADR-0205 — Missing data policy: fail fast, no implicit fills in pricing

    **Status:** Accepted
    **Date:** 2026-01-08

    ## Context
    Silent filling of missing prices or FX rates destroys auditability.
The data layer may implement controlled alignment and imputation, but pricing must not add hidden heuristics.

    ## Options considered
    1. Pricing forward-fills missing values.
2. Pricing falls back to the last available value automatically.
3. Pricing fails fast when required values are missing and only propagates upstream imputation flags.

    ## Decision
    Choose option 3.
Missing required prices or FX points raise typed errors.
Pricing does not forward-fill.
If the data layer provides imputed values, pricing may use them but must emit warnings.

    ## Consequences
    - Stronger auditability and reproducibility.
- Some real-world workflows require upstream alignment; that remains a data-layer concern.
- Users can later add policy-driven tolerances, but only explicitly and via configuration.

    ## Notes / Migration
    - Any breaking change must bump the relevant schema version(s) and include a short migration note.
