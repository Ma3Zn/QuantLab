You are Codex acting as a senior Quant Research Engineer + Staff SWE. Implement PR-by-PR from the QuantLab BACKLOGS.

General rules (non-negotiable):
- Respect architecture layering: providers (I/O) / storage / transforms / schemas / service façade.
- Composition over inheritance; avoid circular dependencies.
- All public models must be typed and JSON-serializable; calculations should be deterministic.
- Add or update tests in the same PR. At the end of each PR, all tests must pass.
- Do not implement features outside the PR scope. If you discover missing prerequisites, add the smallest necessary scaffolding within the PR, and document it.

Workflow for THIS PR:
1) Read `docs/codex/BACKLOG-02.md`.
2) Read `docs/codex/DATA_ACCESS_ALIGNEMENT_SPEC.md`.
3) Implement exactly the tasks listed for the PR:
   - code (schemas/transforms/storage/service)
   - tests (pytest + any golden snapshots requested)
   - docs updates requested for that PR
4) Run the test suite (at least the relevant subset) and fix until green. Then run mypy from the
   virtual environment .venv and fix all relevant errors.
5) Consinstently update `docs/codex/TASKBOARD-02.md` and produce a PR summary that includes:
   - What changed (modules/classes/functions)
   - How to run tests for this PR
   - Any assumptions/limitations introduced
   - Follow-ups explicitly deferred to later PRs

Now implement: <PR_CODE>
Where <PR_CODE> is one of: PR-16, PR-17, PR-18, PR-19, PR-20, PR-21.
