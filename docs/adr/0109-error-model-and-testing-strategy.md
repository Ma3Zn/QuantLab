## Status
Accepted

## Date
2026-01-06

## Decision
Adopt an explicit error model and a serious testing strategy:
- Typed domain exceptions where appropriate (e.g., `InstrumentValidationError`, `PortfolioInvariantError`)
- Rely on Pydantic validation errors as primary mechanism, wrapped only when needed for clearer domain messaging.
- Tests include:
  - Unit tests for invariants and edge cases
  - Property-based tests (Hypothesis) for round-trip JSON and canonicalization
  - Golden/snapshot tests on canonical JSON examples

## Context
Silent acceptance of invalid states is catastrophic downstream. Testing must target invariants and reproducibility rather than performance claims.

## Options Considered
1. Pydantic validation + typed wrappers + strong tests (chosen)
2. Manual checks sprinkled throughout codebase
3. Minimal testing until later

## Trade-offs
- Slightly more upfront time in tests.
- Large reduction in long-term debugging and refactoring cost.

## Acceptance Criteria
- Invalid constructs fail fast with informative messages.
- Round-trip (object -> JSON -> object) preserves semantics.
- Canonical JSON golden files remain stable across runs.
