# ADR-0209 — Testing strategy: invariants + golden snapshots

    **Status:** Accepted
    **Date:** 2026-01-08

    ## Context
    Pricing correctness is mostly about invariants (linearity, currency conversions, determinism).
Example-based tests alone tend to miss edge cases.
Golden snapshots provide audit-friendly regression coverage.

    ## Options considered
    1. Only unit tests for each pricer.
2. Unit tests + property-based tests + golden snapshot tests.
3. Only integration tests (too coarse and slow).

    ## Decision
    Choose option 2.
Combine:
- unit tests for pricers and FX conversion
- property-based tests for invariants
- golden snapshot tests for end-to-end portfolio valuations

    ## Consequences
    - Higher confidence and better regression protection.
- Requires stable fixtures and schema version discipline.
- Slightly more test engineering work, but manageable for MVP scope.

    ## Notes / Migration
    - Any breaking change must bump the relevant schema version(s) and include a short migration note.
