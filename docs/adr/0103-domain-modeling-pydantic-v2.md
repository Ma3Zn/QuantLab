## Status
Accepted

## Date
2026-01-06

## Decision
Use **Pydantic v2** models for the public domain objects in `instruments/`:
- `Instrument`
- `Position`
- `Portfolio`
- Instrument “spec” objects (e.g., `EquitySpec`, `FutureSpec`, `BondSpec`, `CashSpec`)
- Value objects where validation is critical (e.g., `Currency`, `Quantity` constraints)

Primary motivations:
- robust validation (invariants enforced at construction)
- consistent JSON serialization
- schema evolution via explicit `schema_version`
- straightforward golden/snapshot testing of canonical JSON outputs

## Context
This project aims to be “defendible” and robust. Domain objects are consumed by multiple modules; weak validation produces late failures in pricing/risk where debugging is more expensive.

## Options Considered
1. dataclasses with manual validation
2. attrs with validators
3. **Pydantic v2 (chosen)**

## Trade-offs
- Dependency and runtime overhead vs dataclasses.
- Need to manage model configuration (serialization, strictness).
- Potential lock-in to Pydantic semantics (mitigated by keeping models thin and stable).

## Consequences
- Constructors validate invariants early; invalid portfolios fail fast.
- JSON is standardized, enabling stable snapshots and reproducible outputs.
- Types become a “contract surface” for other modules.

## Guardrails
- Models MUST remain “pure domain”: no provider calls, no I/O, no global state.
- Keep models stable; avoid embedding pricing logic.
- Prefer composition: `Instrument(type, spec)` rather than deep inheritance.

## Migration / Follow-ups
- If performance becomes a bottleneck, retain Pydantic at boundaries and use lighter internal representations, but only after profiling.

## Acceptance Criteria
- Invalid inputs (negative quantity in long-only mode, missing futures expiry, etc.) raise typed validation errors.
- `model_dump()` and JSON outputs are deterministic and stable under the same input.
