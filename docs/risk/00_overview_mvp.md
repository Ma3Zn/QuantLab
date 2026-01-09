# Risk — MVP overview

## Cosa fa (MVP)
- Computes standard risk diagnostics on a portfolio and its underlying market data.
- Produces an auditable report with explicit assumptions.

## Cosa non fa
- No data fetching or caching.
- No optimization or decision output.
- No hidden statistical modeling.

## Key design principle
Every number must be traceable to:
1) an explicit input dataset,
2) an explicit convention,
3) an explicit computation path.

If any of these is ambiguous, the implementation must raise a typed error or emit a warning.

## MVP computation paths
Preferred:
- Risk on portfolio return series (from `pricing/`), if available and consistent.

Fallback (explicit and reported):
- Risk on synthetic portfolio returns derived from a static weight vector and asset returns.
