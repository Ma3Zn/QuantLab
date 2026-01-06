## Status
Accepted

## Date
2026-01-06

## Decision
Represent a `Portfolio` as a deterministic snapshot:
- `as_of` timestamp (required)
- `positions` collection with deterministic ordering or canonicalization
- `cash` as a mapping `Currency -> Amount`
- optional metadata (name, book, tags)

No rebalancing logic, no strategy logic, no lifecycle events inside `Portfolio`.

## Context
Risk/stress/testing require deterministic inputs. Non-deterministic ordering breaks golden tests and reproducibility.

## Options Considered
1. Deterministic portfolio snapshot model (chosen)
2. Event-sourced portfolio (trades/events)
3. Strategy-managed mutable portfolio

## Trade-offs
- Less expressive for execution simulation.
- Much simpler and stable interface for downstream analytics.

## Consequences
- Simulation module can later build event-sourcing on top, producing snapshots as outputs.
- Optimization/decision layers consume snapshots, output target exposures.

## Acceptance Criteria
- Canonical ordering for positions in serialization.
- Multi-currency cash supported structurally even if not used initially.
