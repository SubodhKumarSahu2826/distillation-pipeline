# Fine-Tuning Model Distillation Pipeline

Distill one narrow capability — **structured extraction** (a document type → a fixed JSON
schema) — from a frontier **teacher** (Claude API) into a self-hosted **~8B student**
(LoRA/QLoRA), then measure whether owning the model beats renting it. The headline
deliverable is a **number**: the break-even requests/day above which the self-hosted
student is cheaper than the teacher API, fallback-adjusted.

**Status: in progress (Phase 0 — foundation).** Measured results — the 3-axis benchmark
table, the break-even volume, and a served vLLM endpoint with teacher fallback — are added
in Phase 7. See `CLAUDE.md` for how the project runs across sessions, `PROJECT_STATE.md`
for status, and `docs/` for the plan.

## Quickstart (dev)

```bash
pip install -e ".[dev]"
pytest -q
```

Heavy, phase-specific dependencies (teacher API, training, serving) live in optional
extras and are installed by the phase that needs them — see `pyproject.toml` and `docs/`.
