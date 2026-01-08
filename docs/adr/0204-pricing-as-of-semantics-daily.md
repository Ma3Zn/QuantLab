# ADR-0204 — As-of semantics: date-only daily valuation

    **Status:** Accepted
    **Date:** 2026-01-08

    ## Context
    The MVP market data model is daily bars.
Using timestamps and session rules too early would introduce complexity and subtle bugs (time zones, partial trading days).
Pricing needs deterministic as-of semantics aligned with the data layer.

    ## Options considered
    1. Date-only `as_of` for daily bars (MVP).
2. Full datetime `as_of` with exchange session rules.
3. Hybrid with optional datetime, defaulting to date.

    ## Decision
    Choose option 1 for the MVP.
`as_of` is a date (YYYY-MM-DD).
Pricing uses a single price field (default `close`) per asset at that date.
Any alignment across markets is the responsibility of the data layer (with quality flags).

    ## Consequences
    - Simplifies determinism, testing, and documentation.
- Intraday valuation and session rules are deferred to a later milestone.
- Pricing must propagate any upstream alignment flags as warnings when available.

    ## Notes / Migration
    - Any breaking change must bump the relevant schema version(s) and include a short migration note.
