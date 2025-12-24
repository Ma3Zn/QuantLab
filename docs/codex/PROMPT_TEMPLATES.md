# Codex Prompt Templates (efficient prompts for long sessions)

## Template A — “Implement module with contracts + tests”
You are working in this repo. Your task is to implement <MODULE> for the Data layer MVP.

Constraints:
- Follow docs in `docs/data/00_data_layer_spec_mvp_onepager.md` and `docs/data/02a_canonical_schema_contract_onepager.md`.
- Follow storage layout + registry rules in `docs/data/09_snapshot_layout_and_registry_schema.md` and ADR 0007.
- No cross-layer dependencies: `src/data` must not import from pricing/risk/stress/optimization/decision.
- Add unit tests and update docs if needed.
- Keep diffs minimal; no refactors outside touched modules.

Deliverables:
1) Code in `src/data/<...>` implementing <MODULE> with typed API and typed exceptions.
2) Tests under `tests/unit/data/...` and/or `tests/integration/...`.
3) A short summary of design choices and how they map to docs/ADRs.
4) Commands to run (lint/typecheck/test).

Start by:
- listing files you will read,
- proposing an implementation plan,
- then implementing in small commits.

## Template B — “Code review agent”
Review the changes on branch <BRANCH> for correctness against Data layer docs.
Check:
- schema invariants (UTC ts, required metadata),
- storage snapshot immutability + registry correctness,
- no silent cleaning,
- tests and error handling,
- dependency boundaries.
Suggest precise diffs and missing tests.

## Template C — “Golden test creation”
Given a fixed raw payload fixture, generate canonical output and freeze it as a golden snapshot.
Add a test that:
- rebuilds canonical from raw fixture,
- asserts content hash and key records match,
- fails if schema semantics drift without a version bump.
