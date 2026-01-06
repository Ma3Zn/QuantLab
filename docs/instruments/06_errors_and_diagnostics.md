# Errors and Diagnostics (06)

## Philosophy
Fail fast and loudly on invalid states.
Prefer early validation errors to downstream silent corruption.

## Primary mechanism
Pydantic validation errors are the default mechanism.
They are:
- structured
- field-localized
- rich enough for debugging

## Optional domain wrappers
Use thin wrappers only when they improve semantics:
- `DuplicatePositionError(instrument_id=...)`
- `InvalidMarketDataBindingError(...)`

Do not create a large hierarchy unless necessary.

## Logging
This module should not emit logs in constructors by default.
Validation failures should be exceptions.
Logging is handled by orchestrators (CLI, services) with structured logging utilities.

## Error message requirements
- include the offending `instrument_id` or field path
- state the invariant that was violated
- suggest a remediation (e.g., “positions must be unique; merge quantities upstream”)
