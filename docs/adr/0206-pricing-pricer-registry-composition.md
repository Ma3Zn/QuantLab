# ADR-0206 — Pricer architecture: composition + registry (no inheritance tree)

    **Status:** Accepted
    **Date:** 2026-01-08

    ## Context
    QuantLab aims for modularity and replaceable components.
Inheritance-heavy pricer hierarchies tend to couple unrelated instruments and complicate testing.
The instruments layer uses discriminated specs; pricing should mirror this structure.

    ## Options considered
    1. Inheritance hierarchy with a base pricer and many subclasses.
2. Small pricer components registered by instrument spec kind.
3. Single monolithic pricing function with many branches.

    ## Decision
    Choose option 2.
Each instrument kind has a small pricer component.
A registry maps instrument spec kind → pricer.
The valuation engine is generic and delegates to the registry.

    ## Consequences
    - Adding a new instrument class does not require modifying existing pricers.
- Unit tests are localized.
- Registry configuration becomes a controlled integration point.

    ## Notes / Migration
    - Any breaking change must bump the relevant schema version(s) and include a short migration note.
