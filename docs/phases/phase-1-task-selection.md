# Phase 1 — Task Selection + Teacher Baseline

> Start only on **"Start Phase 1."** The task is already chosen (structured extraction); this
> phase locks the concrete instantiation, builds the schema + frozen test set, and measures the
> **teacher ceiling** — the single most important number for every later comparison.

> **⚠️ $0 STRATEGY PIVOT (D-013, 2026-08-22).** The paid Claude teacher below is **cancelled** — the
> project must cost **$0**. Prereq `ANTHROPIC_API_KEY`, the "Claude call" client, the paid **PILOT
> (cost gate)** in Task 5, and the "pilot cost" acceptance criteria are **void**: the teacher is now
> an **open-source model run at $0** (TBD — not chosen) and the ceiling is measured at $0 with no
> approval gate. Schema / frozen-test / evaluator work is unaffected. Do not choose the model in a
> planning pass.

## Objective
Finalize the schema, acquire real inputs, build a **frozen, uncontaminated test set** with gold
labels, and honestly measure teacher quality on it. That number is the ceiling.

## Prerequisites
- Phase 0 complete.
- `ANTHROPIC_API_KEY` in `.env`.
- Decide teacher model tier (pull current model IDs/pricing via the `claude-api` skill).

## Tasks
1. **Lock the dataset & document type** — pick a public corpus of one document type; prefer one
   that ships human gold parses. Record source + license in `docs/decisions.md`.
2. **Define the schema** — `src/distill/schema.py` (Pydantic): fields, types, required vs optional,
   normalization rules; `parse_and_validate(text)`.
3. **Prompt template** — `src/distill/teacher.py`: a single, versioned extraction prompt.
4. **Teacher client** — Claude call with retry/rate-limit + **per-call token/cost capture**.
5. **PILOT (cost gate):** run the teacher on **50–100** inputs with `--limit`; inspect outputs,
   validity, and cost. Write pilot cost → `docs/cost-analysis.md`. **Do not scale yet.**
6. **Build the frozen test set** — a few hundred examples with gold labels (dataset gold, or a
   small human-verified set built here). Hash-split so it can never overlap train/val later.
   Write `data/splits/test.jsonl`; add the `--allow-test` guard so nothing reads it until Phase 4.
7. **Measure teacher baseline** — score teacher outputs vs gold on the test set with
   `evaluate.py`; write E-001 + the teacher table in `docs/benchmarking.md`.
8. **Ceiling gate:** if teacher quality is not usably high, **stop and reconsider** (documented
   #1 failure mode) before spending on Phase 2.

## Files/components expected
`src/distill/schema.py`, `src/distill/teacher.py`, `src/distill/evaluate.py` (metrics),
`scripts/run_teacher.py` (with `--dry-run/--limit/--allow-test`), `data/splits/test.jsonl`
(gitignored), tests for schema + metrics.

## Experiments
- **E-001 Teacher baseline** — hypothesis + actual in `docs/experiments.md`.

## Tests
- Schema: valid/invalid fixtures parse/reject correctly.
- Metrics: field-F1 / exact-match on tiny hand-made cases match expected values.
- Guard: split loader refuses `test.jsonl` without `--allow-test`.

## Expected outputs
- `schema.py` (the contract), frozen test set, teacher baseline number, pilot cost.

## Acceptance criteria
- [ ] Schema validates known-good and rejects known-bad outputs.
- [ ] Test set is frozen, hashed, and guarded; size recorded.
- [ ] Teacher field-F1 + schema-validity recorded in `benchmarking.md` (E-001 filled).
- [ ] Pilot cost recorded; full generation cost estimated **before** Phase 2.
- [ ] Ceiling gate explicitly passed (or task revised).

## Risks
| Risk | Likelihood | Impact | Mitigation | Detection |
|------|:--:|:--:|------|------|
| Teacher mediocre on task | Med | **High** | Ceiling gate; swap to runner-up task (SQL/PII) | Low F1 in E-001 |
| Test-set contamination | Med | **High** | Hash-split by input; freeze + `--allow-test` guard | Test hashes ∩ train hashes = ∅ check |
| Ambiguous gold labels | Med | Med | Tighten schema/normalization; human-verify gold | Low teacher F1 from label noise, not model |
| Prompt not representative | Low | Med | Version prompt; inspect pilot outputs | Pilot manual review |
| Pilot cost surprise | Low | Med | `--limit`, print est. before run | Pilot $ vs projection |

## Estimated complexity
**Medium.** 1–2 sessions (schema + gold set are the work).

## What must NOT be done in this phase
- No bulk generation (that's Phase 2 — only the 50–100 pilot here).
- No training, no serving.
- Do not read/modify `test.jsonl` after freezing it.

## Persist for next session
- Commit schema, test set (path only), baseline table, pilot cost.
- Update `PROJECT_STATE.md` (teacher ceiling), `decisions.md` (dataset + teacher tier), handoff
  with the exact generation-run plan + estimated cost awaiting approval.
