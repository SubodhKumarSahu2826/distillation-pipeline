# PROJECT_STATE.md — Status Ledger

> Single source of truth for **what exists and what is done**. Update at the end of every
> session. Keep it terse — pointers and status, not prose.

**Project:** Fine-Tuning Model Distillation Pipeline
**Task distilled:** structured extraction — document → fixed JSON schema (see `docs/task-selection.md`)
**Last updated:** 2026-08-20 (Phase 0 — foundation, complete)
**Overall status:** ✅ PHASE 0 COMPLETE — skeleton built; `pytest` (3) + `ruff` green; editable
install verified; committed as `4b2413a` "chore: initialize project (Phase 0)", working tree clean.
Awaiting **"Start Phase 1"**. $0 spent.

---

## Phase status

| Phase | Name | Status | Key output | Doc |
|------:|------|--------|-----------|-----|
| — | Planning | ✅ done | this doc set | `docs/project-plan.md` |
| 0 | Foundation | ✅ done | repo skeleton, config, logging, smoke tests (commit `4b2413a`) | `docs/phases/phase-0-foundation.md` |
| 1 | Task selection + teacher baseline | ⬜ not started | schema, held-out test set, **teacher ceiling number** | `docs/phases/phase-1-task-selection.md` |
| 2 | Teacher dataset generation | ⬜ not started | filtered train/val/test JSONL + generation cost | `docs/phases/phase-2-teacher-dataset.md` |
| 3 | Student fine-tuning | ⬜ not started | LoRA r8 & r32 adapters + W&B runs | `docs/phases/phase-3-fine-tuning.md` |
| 4 | Teacher vs student benchmark | ⬜ not started | 3-axis table + quality retention | `docs/phases/phase-4-benchmarking.md` |
| 5 | vLLM serving + router | ⬜ not started | served endpoint + escalation rate | `docs/phases/phase-5-serving-routing.md` |
| 6 | Economics + break-even | ⬜ not started | **break-even req/day** + savings curve | `docs/phases/phase-6-economics.md` |
| 7 | Finalization | ⬜ not started | README w/ measured results, repro | `docs/phases/phase-7-finalization.md` |

Legend: ⬜ not started · 🟡 in progress · ✅ done · ⛔ blocked

---

## Artifacts index (fill in as produced — path + one-line summary)

| Artifact | Path | Produced in | Notes |
|----------|------|-------------|-------|
| Output schema | `src/distill/schema.py` | Phase 1 | the JSON contract |
| Held-out test set | `data/splits/test.jsonl` | Phase 1 | **do not touch until Phase 4** |
| Teacher baseline | `docs/benchmarking.md` §teacher | Phase 1 | the quality ceiling |
| Train/val splits | `data/splits/{train,val}.jsonl` | Phase 2 | |
| Generation cost | `docs/cost-analysis.md` §generation | Phase 2 | actual $ spent |
| Adapters | `models/lora-r8/`, `models/lora-r32/` | Phase 3 | |
| Benchmark table | `docs/benchmarking.md` §final | Phase 4 | |
| Router | `src/distill/router.py` | Phase 5 | escalation rate recorded |
| Break-even | `docs/cost-analysis.md` §break-even | Phase 6 | the headline number |
| README | `README.md` | Phase 7 | measured numbers only |

---

## Key decisions (pointer)

Full log: `docs/decisions.md`. Most consequential so far:
- **D-001** Task = structured extraction (doc → fixed JSON). *Planning.*
- **D-002** Project lives at `AI Projects/distillation-pipeline/`, own git repo. *Planning.*
- **D-003** Deterministic eval (field-F1 + schema-validity) → **no LLM-judge / no Project-4 dependency.** *Planning.*
- **D-004** Phase 0 has **zero required runtime deps**; heavy deps in optional extras; `.env` wiring deferred to Phase 1. *Phase 0.*
- **D-005** Sandbox blocks `.git` writes in the workspace → `git init` + first commit is a user-run step. *Phase 0.*

## Open questions (resolve in the phase that needs them)

- Exact document dataset + teacher model tier — locked in Phase 1 via a 50-sample pilot.
- GPU tier for training vs serving — locked in Phase 3 / Phase 5 from measured memory + throughput.

## Known costs incurred to date

$0.00 (planning only; no API/GPU used).
