# Decisions Log (ADR-lite)

Append-only. One entry per meaningful decision. Newest at top. Keep each entry short:
context → decision → why → consequence. Reference by ID (D-00N) from other docs.

---

### D-005 — Sandbox blocks `.git` writes in the workspace
- **Context:** Phase 0 must `git init` + commit here (D-002), but the execution sandbox denies
  creating a `.git` directory anywhere in the workspace tree (normal dirs, and `.git` under
  `$TMPDIR`, are writable; `<repo>/.git` is not). The sandbox cannot be disabled.
- **Decision:** run every other Phase 0 step in-sandbox; the `git init` + initial commit is run by
  the user in a normal terminal (exact commands provided), or after the sandbox is adjusted to
  allow `.git` in this project.
- **Why:** can't fight the sandbox; a git dir under `$TMPDIR`/an alternate allow-listed path would
  be non-durable and non-standard — not a real repo.
- **Consequence:** Phase 0 code/tests/lint are complete and verified; the git-commit acceptance
  criterion is pending one user-run command. (Phase 0, 2026-08-20)

### D-004 — Phase 0 carries zero required runtime dependencies
- **Context:** the phase-0 doc's example listed `python-dotenv`, but no Phase 0 code reads `.env`
  (secrets are first consumed by the teacher client in Phase 1).
- **Decision:** Phase 0 declares **no** required runtime deps; config uses the stdlib only. Heavy,
  phase-specific deps live in optional extras (`teacher`/`data`/`train`/`serve`); dev tooling
  (`ruff`, `pytest`) is the only non-extra tooling. `.env` loading arrives in Phase 1.
- **Why:** "every dependency must have a concrete purpose right now"; keeps the install fast and the
  smoke test fully offline.
- **Consequence:** `pip install -e .` installs nothing heavy; `.env.example` ships now, `.env`
  wiring lands with the teacher client. (Phase 0, 2026-08-20)

### D-003 — Deterministic evaluation; no LLM judge
- **Context:** the spec allows an LLM judge (from Project 4) for open-ended outputs.
- **Decision:** choose a task with deterministic metrics (field-F1 + schema validity); do **not**
  use an LLM judge.
- **Why:** reproducible, cheap, honest scoring; removes a cross-project dependency and a source of
  eval noise.
- **Consequence:** evaluation is pure code; no Project-4 coupling. *(Planning)*

### D-002 — Project location & isolation
- **Context:** workspace holds several independent projects, one git repo each.
- **Decision:** project lives at `AI Projects/distillation-pipeline/` with its own git repo.
- **Why:** matches the user's convention; keeps history and state self-contained.
- **Consequence:** `git init` happens in Phase 0. *(Planning)*

### D-001 — Task = structured extraction (document → fixed JSON)
- **Context:** must pick one narrow task the teacher already does well (see `task-selection.md`).
- **Decision:** structured extraction into a fixed JSON schema.
- **Why:** honest deterministic eval, abundant real inputs, reliable teacher, 8B-feasible, and a
  free deterministic router signal (schema validation).
- **Consequence:** schema is the central contract; drives Phases 1–6. *(Planning)*

---
_Template for new entries:_
```
### D-00N — <title>
- **Context:** …
- **Decision:** …
- **Why:** …
- **Consequence:** … (<phase/date>)
```
