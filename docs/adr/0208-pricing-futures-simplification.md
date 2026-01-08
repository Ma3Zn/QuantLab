# ADR-0208 — Futures pricing simplification in MVP (no margining/roll)

    **Status:** Accepted
    **Date:** 2026-01-08

    ## Context
    Futures valuation can be modelled with mark-to-market plus multiplier.
Full treatment requires margin accounts, settlement conventions, and contract roll rules.
These details are important but not required to unblock the MVP risk/stress pipeline.

    ## Options considered
    1. Full futures lifecycle (margining, settlement, roll).
2. Mark-to-market notional only: `q * price * multiplier`.
3. Ignore futures entirely in MVP.

    ## Decision
    Choose option 2.
Futures in the MVP are valued as mark-to-market notionals only.
The output explicitly states that margining/roll are not modelled.

    ## Consequences
    - Futures can be included in portfolios early with explicit limitations.
- Downstream risk must treat futures exposure appropriately and not interpret results as fully cash-realistic.
- A later milestone can add margining/roll as an extension module without breaking the core API.

    ## Notes / Migration
    - Any breaking change must bump the relevant schema version(s) and include a short migration note.
