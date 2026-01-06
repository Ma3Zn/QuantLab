# Pydantic v2 Domain Model Contract (02)

## Modeling stance
Use Pydantic v2 for all public domain objects.

### Base configuration (recommended)
- `extra='forbid'` (no silent fields)
- `frozen=True` (immutable domain objects)
- strict where feasible (`StrictStr`, `StrictInt`, etc.)
- whitespace stripping for IDs
- timezone-aware datetimes

Rationale:
- immutable objects are easier to reason about and snapshot-test
- forbidding extra fields prevents schema drift

## Discriminated union specs
Instrument type-specific fields live in `Spec` models.
Use a discriminator key (e.g., `kind`) with `Literal[...]` values.
Example (conceptual):
- `EquitySpec(kind="equity", exchange: str | None, ...)`
- `FutureSpec(kind="future", expiry: date, multiplier: float, ...)`

Then:
- `Instrument.spec` is a union with `Field(discriminator="kind")`
- `Instrument.instrument_type` is validated to match `spec.kind` (avoid inconsistencies)

## Schema versioning
Define a module constant:
- `INSTRUMENTS_SCHEMA_VERSION = 1`

Embed `schema_version` in:
- `Instrument`
- `Position` (optional, but recommended for stability)
- `Portfolio`

Breaking changes require bump and migration notes.

## Canonicalization hooks
Canonicalization must occur at validation-time:
- positions sorted and uniqueness enforced
- cash dict keys normalized/sorted

Use Pydantic validators:
- `@field_validator("positions")` to sort and validate uniqueness
- `@field_validator("cash")` to normalize and sort keys

## Type constraints (MVP)
- `Currency`: regex `^[A-Z]{3}$`
- `quantity`: `>= 0` (long-only)
- futures: expiry required, multiplier > 0

## Serialization
Use Pydantic `.model_dump()` / `.model_dump_json()`; ensure canonical ordering and stable field names.
If needed, implement explicit `.to_canonical_dict()` that calls `model_dump()` and post-processes ordering.
