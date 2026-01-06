# PROMPT_TEMPLATE.md — Codex PR Execution Template (QuantLab)

Use this template to instruct Codex to implement **one PR at a time** from the backlog (e.g., `BACKLOG-03.md`).
This template is optimized for: strict layering, minimal coupling, high testability, reproducibility, and reviewable PRs.

> Operating principle: **small PRs, explicit acceptance criteria, no scope creep**.

---

## 0) PR Header (fill all fields)

- **PR ID:** PR-XX (e.g., PR-27)
- **PR Title:** <short imperative title>
- **Module:** `<module>` (e.g., `instruments/`)
- **Branch name:** `pr-XX-<slug>`
- **Related Backlog file:** `BACKLOG-03.md`
- **Primary references (must read first):**
  - ADR(s): `docs/adr/....md`
  - Module docs: `docs/modules/<module>.md`
  - Implementation plan: `docs/<module>/90_codex_implementation_plan.md`
  - Any spec docs: `docs/<module>/*.md`
- **Non-goals (explicit):**
  - <list what must NOT be added in this PR>

---

## 1) Objective (crisp)

### What you must implement
- <bulleted list, 5–10 items max, concrete and testable>

### What you must NOT implement
- <bulleted list of tempting additions that must be avoided>

---

## 2) Architectural Guardrails (non-negotiable)

Codex MUST adhere to the following. If any guardrail conflicts with the PR tasks, STOP and explain the conflict.

### 2.1 Layer separation
- Domain objects in `<module>` are **pure**: no I/O, no provider calls, no caching, no environment reads.
- No leakage of responsibilities from other layers (pricing/risk/stress/optimization/decision).

### 2.2 Composition over inheritance
- Prefer discriminated unions + composition.
- Avoid deep inheritance trees unless explicitly required by ADR.

### 2.3 Determinism and reproducibility
- No implicit time: never call `datetime.now()` inside models.
- Canonical ordering for serialized outputs when required.
- Reject invalid numeric values (NaN/Inf) rather than “handle silently”.

### 2.4 Error handling
- Fail fast with clear diagnostics.
- No silent fallbacks.
- Prefer typed validation errors (e.g., Pydantic) over ad-hoc checks unless specified.

### 2.5 Testing discipline
- Every new invariant must have a test.
- Tests must be deterministic (no network, no randomness without fixed seed).
- Prefer unit tests; use property-based tests only when requested by the PR or clearly beneficial.

---

## 3) Preconditions Check (required)

Before coding, Codex MUST:

1. **List the exact files** it will modify/create (paths).
2. **Restate acceptance criteria** from the PR verbatim as a checklist.
3. **Identify dependencies** and confirm versions/constraints (e.g., Pydantic v2, Hypothesis).
4. **Scan existing code** to reuse types rather than duplicating (e.g., `data.AssetId`).

If any precondition cannot be satisfied, Codex must propose a minimal fix and ask for approval (or fail clearly).

---

## 4) Implementation Plan (step-by-step)

Codex should provide a short plan with:
- Step 1: <what, where, why>
- Step 2: ...
- Step N: ...

Constraints:
- Keep the plan aligned to PR scope only.
- Prefer minimal changes per file.
- Prefer additive changes; avoid refactors unless required by acceptance criteria.

---

## 5) Detailed Task Breakdown (copy from backlog and expand)

### Task A — <name>
- **Files:** <paths>
- **Implementation notes:**
  - <explicit invariants/validators/configs>
  - <typing constraints>
- **Tests to add:**
  - <test name + what it asserts>
- **Edge cases:**
  - <what can go wrong and how you guard it>

Repeat for each task.

---

## 6) Code Quality Checklist (must satisfy)

### 6.1 Python quality
- Type hints everywhere for public APIs.
- No circular imports; reorganize modules if needed.
- No heavyweight dependencies introduced without ADR approval.

### 6.2 Readability and maintainability
- Small functions.
- Clear naming matching domain semantics.
- Comments only for “why”, not “what”.

### 6.3 Pydantic v2 usage (if applicable)
- `extra='forbid'`
- `frozen=True` (unless PR says otherwise)
- Use discriminated unions properly (`Field(discriminator=...)`)
- Validators:
  - prefer `@field_validator` / `@model_validator` (v2 style)
  - keep validators pure and deterministic

### 6.4 Deterministic JSON (if applicable)
- Define explicit `to_canonical_dict()` / `to_canonical_json()` if required.
- Ensure stable ordering and consistent `exclude_none` policy.

---

## 7) Testing Requirements (must be explicit)

Codex MUST add/modify tests that cover:
- Happy path construction
- Failure path for each invariant
- Determinism (if part of PR)

### Required output
At the end, Codex MUST provide:
- exact commands to run tests (e.g., `pytest -q tests/unit/instruments`)
- summary of new tests added and what they cover

---

## 8) Documentation Updates (only if required by PR)

If the PR changes public contracts, Codex must:
- update the module README quickstart (import paths must compile)
- update `docs/<module>/INDEX.md` if new docs/tests/fixtures were added

Do not edit ADRs unless the PR explicitly requires it.

---

## 9) Deliverables Checklist (must be in final message)

Codex must conclude with:

- [ ] All acceptance criteria satisfied
- [ ] All tests pass locally (`pytest -q`)
- [ ] No out-of-scope changes included
- [ ] Lint/typecheck status (if configured): <pass/fail/NA>
- [ ] Files changed (list)
- [ ] Notes for reviewer (short)

---

## 10) Example “Filled Prompt” Skeleton (copy/paste and edit)

### PR Header
- PR ID: PR-27
- PR Title: Implement Instrument model + cross-validation
- Module: instruments
- Branch: pr-27-instrument-model
- References:
  - docs/adr/0102-instruments-identifier-contract.md
  - docs/adr/0105-instruments-composition-over-inheritance.md
  - docs/instruments/02_pydantic_models_contract.md
  - docs/instruments/03_instrument_specs_mvp.md
- Non-goals:
  - do not implement pricing logic
  - do not add provider symbol mapping

### Objective
Must implement:
- `InstrumentType` enum
- `Instrument` model with discriminated `spec`
- validators for type/spec alignment and market-data binding rules
Must NOT implement:
- pricers, risk metrics, or data fetching

### Acceptance criteria (from backlog)
- <paste PR acceptance criteria here>

### Files to change
- src/instruments/types.py
- src/instruments/specs.py
- tests/unit/instruments/test_instrument.py

### Implementation plan
1) Add enum and model skeleton
2) Add validators for invariants
3) Add unit tests for success/failure cases

### Final checklist
- tests: `pytest -q tests/unit/instruments`
