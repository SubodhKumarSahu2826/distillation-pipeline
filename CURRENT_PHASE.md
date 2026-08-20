# CURRENT_PHASE.md — Active Phase Pointer

> The one thing to work on now. Update at the end of every session.

## Active phase

**Phase 0 ✅ COMPLETE. Next: Phase 1 — awaiting "Start Phase 1" (not yet begun).**

Phase 0 delivered a verified skeleton, committed as `4b2413a` ("chore: initialize project
(Phase 0)"): `pyproject.toml` (zero runtime deps, heavy deps in extras), `.gitignore`,
`.env.example`, `src/distill/{__init__,config,logging}.py`, `tests/test_smoke.py`, `README.md`.
`pytest` → 3 passed; `ruff check` → clean; `pip install -e .` verified; working tree clean.

## Next exact action

> When the user says **"Start Phase 1"**, open `docs/phases/phase-1-task-selection.md` and do
> **only** that phase. Do not begin it before then.

Phase 1 is task selection + teacher baseline (schema, held-out test set, teacher ceiling number).
It is the first phase that can spend money — enforce the money guardrails (pilot first, `--dry-run`,
`--limit N`, cost estimate + explicit approval before any bulk teacher run).

## Do NOT

- Do not begin Phase 1 until explicitly told "Start Phase 1".
- Do not skip ahead to later phases.
- Do not call paid APIs, rent GPUs, or download models until the phase that needs them.

## Pre-flight for the next session

1. `git log --oneline` should show `4b2413a`; `git status` clean.
2. Read `PROJECT_STATE.md` + this file + `docs/handoffs/latest.md`, then the Phase 1 doc.
3. **Git commits must be run by the user** (or after adjusting the sandbox): this sandbox denies
   `.git` writes in the workspace (D-005). Prepare the commit and hand the command to the user.
4. `.env` loading (python-dotenv) lands in Phase 1 with the teacher client; create `.env` from
   `.env.example` when a real `ANTHROPIC_API_KEY` is needed.
