# Phase 0 — Foundation

> Do this phase only when the user says **"Start Phase 0."** Implement Phase 0 and nothing else.

## Objective
A clean, reproducible, testable repository skeleton — the scaffolding every later phase builds
on. No task logic yet.

## Prerequisites
- Planning docs exist (they do).
- Nothing else. No API keys, GPU, or model downloads needed.

## Tasks
1. `pyproject.toml` — package `distill` under `src/`, Python pin, dev tooling (ruff, pytest).
   List runtime deps but keep heavy ones (torch/transformers/vllm) in optional extras so Phase 0
   installs fast; real installs happen in the phase that needs them.
2. `.gitignore` — ignore `data/`, `models/`, `runs/`, `artifacts/`, `.env`, `venv/`, caches, W&B.
3. `.env.example` — `ANTHROPIC_API_KEY=`, `WANDB_API_KEY=`, `HF_TOKEN=` (empty placeholders).
4. `src/distill/__init__.py`, `src/distill/config.py` — typed config: paths, model-id knobs,
   pricing knobs (empty/default), all read from env with safe defaults.
5. `src/distill/logging.py` (or a small helper) — one logging setup used everywhere.
6. `tests/test_smoke.py` — imports the package, asserts config loads. Fast, no network/GPU.
7. `README.md` stub — one paragraph + "status: in progress" (real results added in Phase 7).
8. `git init`, initial commit `chore: initialize project`.

## Files/components expected
`pyproject.toml`, `.gitignore`, `.env.example`, `src/distill/{__init__,config,logging}.py`,
`tests/test_smoke.py`, `README.md`.

## Experiments
None (no measurements this phase).

## Tests
- `pytest -q` passes (smoke test).
- `ruff check` clean.
- `python -c "from distill.config import CONFIG; print(CONFIG)"` works.

## Expected outputs
An installable, importable, test-passing skeleton committed to git.

## Acceptance criteria
- [ ] `pip install -e .` (or `uv`/env of choice) succeeds with light deps only.
- [ ] `pytest -q` green.
- [ ] `git log` shows the init commit; `git status` clean.
- [ ] `.env` is gitignored; `.env.example` committed.

## Risks
| Risk | Likelihood | Impact | Mitigation | Detection |
|------|:--:|:--:|------|------|
| Over-scaffolding (empty `api/`, `utils/`, factories) | Med | Low | Follow complexity policy; create modules only when a phase needs them | Review dir tree vs `architecture.md` §4 |
| Heavy deps installed too early | Med | Med | Optional extras; defer torch/vllm | Check `pyproject` extras |

## Estimated complexity
**Low.** ~1 short session.

## What must NOT be done in this phase
- No teacher calls, no dataset code, no training/serving code.
- No model downloads, no GPU, no paid API.
- No speculative modules or abstractions.

## Persist for next session
- Mark Phase 0 ✅ in `PROJECT_STATE.md`; point `CURRENT_PHASE.md` at Phase 1.
- Handoff: confirm skeleton + how to run tests; next action = "Start Phase 1".
