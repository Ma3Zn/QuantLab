# Data Transforms (Alignment)

This module hosts deterministic, pure transforms used by the data-access layer.

## Alignment semantics (MVP)
- Build a target index from the requested market calendar sessions (inclusive start/end).
- Reindex raw frames onto the target session dates (index is pure `date`).
- Apply missing-data policy after reindexing:
  - `NAN_OK`: leave missing values as NaN.
  - `DROP_DATES`: drop any date where one or more fields are missing.
  - `ERROR`: raise a `DataValidationError` if any missing values remain.

No forward-filling or silent cleaning is performed.
