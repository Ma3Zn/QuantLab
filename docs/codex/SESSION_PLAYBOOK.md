# Codex Session Playbook (long-running work)

## 0) Preconditions
- Work on a clean git working tree.
- Ensure docs under `docs/data/` and ADRs are present.
- Confirm the repo structure matches `repo-structure.txt`.

## 1) Start each task
1. State objective + non-goals.
2. List files to read (docs + relevant src).
3. Propose plan: modules, APIs, tests, commands.
4. Create/checkout a task branch.

## 2) Execution loop
- Implement smallest vertical slice first (API + one test).
- Run tests early and often.
- Add structured logging only where it adds diagnostic value.
- Keep all I/O in provider/storage layer; keep transformations pure.

## 3) Completion
- use the local virtual environment .venv
- Run full checks: ruff, mypy, pytest.
- Update docs if file paths/config changed.
- Provide a final summary:
  - what changed,
  - how it maps to docs/ADRs,
  - remaining known limitations.

## 4) Handover notes
- If you could not complete a subtask, leave a TODO with:
  - exact file/line,
  - why blocked,
  - next step.
