# PROJECT_STATE.md — Status Ledger

> Single source of truth for **what exists and what is done**. Update at the end of every
> session. Keep it terse — pointers and status, not prose.

**Project:** Fine-Tuning Model Distillation Pipeline
**Task distilled:** structured extraction — document → fixed JSON schema (see `docs/task-selection.md`)
**Last updated:** 2026-08-22 (Phase 1 — task selection + teacher baseline, in progress; frozen test set built & leakage-checked D-012; converter now committed at `dd6bcf8`)
**Overall status:** 🟡 PHASE 1 IN PROGRESS — schema (`receipt-v1`), deterministic evaluator (with a
dataset-specific **scored-field policy**), teacher client, and a dry-run cost gate are built & tested
offline. The deterministic **CORD→`receipt-v1` converter** (D-011) produces
`data/cord/{train,dev,test}.jsonl` — **1000** schema-valid gold records — and CORD's 100-record test
split is now **frozen** at `data/splits/test.jsonl` + a hash manifest (D-012). `pytest` **42 passed**,
`ruff` clean.
**Not yet done:** measure the teacher baseline (needs an approved **paid** pilot). The frozen-test work
(`input_hash` + `scripts/freeze_test_set.py` + 2 tests) is **uncommitted** — hand the commit to the
user (D-005; HEAD is `dd6bcf8`). **$0 spent** (pilot estimated ~$0.55, unspent).

---

## Phase status

| Phase | Name | Status | Key output | Doc |
|------:|------|--------|-----------|-----|
| — | Planning | ✅ done | this doc set | `docs/project-plan.md` |
| 0 | Foundation | ✅ done | repo skeleton, config, logging, smoke tests (commit `4b2413a`) | `docs/phases/phase-0-foundation.md` |
| 1 | Task selection + teacher baseline | 🟡 in progress | schema ✅, evaluator ✅, teacher client ✅ (dry-run gate), CORD converter ✅ (D-011), frozen test set ✅ (D-012); ceiling number pending | `docs/phases/phase-1-task-selection.md` |
| 2 | Teacher dataset generation | ⬜ not started | filtered train/val/test JSONL + generation cost | CORD→`receipt-v1` converter already built early (D-011); teacher labelling not started — `docs/phases/phase-2-teacher-dataset.md` |
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
| Output schema | `src/distill/schema.py` | Phase 1 | ✅ `receipt-v1` Pydantic contract + parse/validate (unchanged by D-010) |
| Evaluator | `src/distill/evaluate.py` | Phase 1 | ✅ field-F1 / schema-validity / exact-match / per-field; optional `scored_fields` allow-list (D-010) |
| Dataset policy + converter | `src/distill/dataset.py` | Phase 1 | ✅ `CORD_SCORED_FIELDS` (D-010) + deterministic CORD→`receipt-v1` converter `convert_record`/`build_gold`/`build_text`/`parse_amount` (D-011) + `input_hash` (D-012) |
| CORD conversion CLI | `scripts/convert_cord.py` | Phase 1 | ✅ reads `data/raw/cord/*/json/*.json` → writes `data/cord/{train,dev,test}.jsonl` (offline, $0) |
| Frozen-test CLI | `scripts/freeze_test_set.py` | Phase 1 | ✅ freezes `data/cord/test.jsonl` → `data/splits/test.jsonl` + manifest; cross-split leakage check (D-012); offline, $0 |
| Converted CORD gold | `data/cord/{train,dev,test}.jsonl` | Phase 1 | ✅ 800/100/100 = **1000** schema-valid `{id,text,gold}` records (gitignored build artifact; rebuild via the CLI) |
| Teacher client | `src/distill/teacher.py` | Phase 1 | ✅ prompt `extract-v1`; token/cost capture (lazy anthropic) |
| Pilot runner | `scripts/run_teacher.py` | Phase 1 | ✅ dry-run cost gate; `--confirm` + `--allow-test` guards |
| Held-out test set | `data/splits/test.jsonl` | Phase 1 | ✅ 100 frozen CORD test records (D-012); **do not touch until Phase 4** |
| Frozen-test manifest | `data/splits/test.manifest.json` | Phase 1 | ✅ 100 input hashes + aggregate `872bec26…`; Phase 2 drops train/val inputs colliding with these |
| Teacher baseline | `docs/benchmarking.md` §teacher | Phase 1 | ⬜ TBD — needs approved pilot |
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
- **D-006** Doc type = **receipts** (dataset candidate **CORD**, fallback SROIE); final only after the pilot. Schema locked as `receipt-v1`. *Phase 1.*
- **D-007** Teacher tiers: measure ceiling with **Opus 5**; A/B **Haiku 4.5** as the cheaper bulk-generation tier (locked in Phase 2). *Phase 1.*
- **D-008** `pydantic>=2` promoted to a required runtime dep (schema is core); updates D-004. *Phase 1.*
- **D-009** Teacher pricing in `config.py` is a **labelled assumption** (Opus 5 list price); confirm on the agentrouter endpoint + `count_tokens` before any spend. *Phase 1.*
- **D-010** CORD scoring policy: use original `clovaai/cord`; score **only** CORD-labelled fields (`subtotal/tax/total/line_items`), **exclude** `vendor/date/currency` from the headline metric via a general `scored_fields` allow-list (`dataset.CORD_SCORED_FIELDS`). Schema unchanged. *Phase 1.*
- **D-011** CORD gold lives in `valid_line` word+`category` spans (**no** `gt_parse`); a small deterministic converter builds `{id,text,gold}` (gold from `menu.*`/`sub_total.*`/`total.*` spans, text reconstructed from `quad` boxes). Converter pulled forward from Phase 2; teacher labelling not started. *Phase 1.*
- **D-012** Freeze CORD's test split as-is → `data/splits/test.jsonl` + hash manifest; found **9** test inputs leaking into train/val — fixed on the **train/val** side in Phase 2, never the test anchor. *Phase 1.*

## Open questions (resolve in the phase that needs them)

- Confirm receipts/CORD as final (vs SROIE) + pick the bulk teacher tier — both gated on the Phase-1
  pilot. CORD is **on disk, converted** (D-011), and its test split is **frozen** (D-012); CORD
  **scoring** policy is resolved (D-010). What remains is clearing the **paid** pilot (blocked on
  explicit cost approval, not on data) and measuring the teacher ceiling.
- GPU tier for training vs serving — locked in Phase 3 / Phase 5 from measured memory + throughput.

## Known costs incurred to date

$0.00 — no paid API/GPU calls. Phase-1 pilot is **estimated** ~$0.55 (50 × Opus 5, labelled
assumption); not yet run or approved.
