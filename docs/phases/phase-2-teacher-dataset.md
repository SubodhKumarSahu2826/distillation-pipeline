# Phase 2 — Teacher Dataset Generation

> Start only on **"Start Phase 2."** This is the **main cash cost** of the project. Estimate,
> approve, then run. Put the actual number in the docs.

## Objective
Produce a high-quality, schema-valid, deduplicated training corpus by running the teacher over
**real inputs**, filtering ruthlessly, and splitting train/val (test already frozen in Phase 1).

## Prerequisites
- Phase 1 complete: schema, teacher client, frozen test set, passed ceiling gate.
- **Approved generation cost estimate** in `docs/cost-analysis.md` (from the Phase-1 pilot).

## Tasks
1. **Assemble real inputs** (5–10k target, per spec) matching the serving distribution; exclude
   any input whose hash is in the frozen test set.
2. **Cost gate:** re-confirm projected cost from the pilot's $/example; require an explicit
   confirm flag on the full run. Support resumable batching (checkpoint progress) so a failure
   doesn't re-bill completed calls.
3. **Generate** teacher labels over the inputs (concurrency + retry + usage capture).
4. **Validate & filter** — drop every schema-invalid output (don't teach failures); log drop rate.
5. **Deduplicate** near-identical inputs (normalized hash / MinHash-lite); log dup rate.
6. **Split** train/val by input-hash (test stays frozen); write `data/splits/{train,val}.jsonl`.
7. **Profile the dataset** — field-value distributions, length stats, class balance where
   relevant → E-002 in `docs/experiments.md`.
8. **Record actual cost** → `docs/cost-analysis.md` §1.

## Files/components expected
`src/distill/dataset.py` (validate/filter/dedup/split + stats), `scripts/generate_dataset.py`
(`--dry-run/--limit/--confirm/--resume`), `data/splits/{train,val}.jsonl` (gitignored),
tests for filter/dedup/split logic (on synthetic fixtures, no network).

## Experiments
- **E-002 Dataset quality profile** — validity %, drop %, dup %, distribution, cost.

## Tests
- Filtering: invalid outputs are dropped; valid kept.
- Dedup: known near-duplicates collapse; distinct kept.
- Split: no hash appears in two splits; test hashes never appear.
- Resume: re-running with `--resume` does not re-issue completed calls (mock the client).

## Expected outputs
- `train.jsonl`, `val.jsonl` (paths recorded), dataset stats, **actual generation cost**.

## Acceptance criteria
- [ ] Train/val exist, sized as planned; **zero** overlap with frozen test (verified by hash).
- [ ] Schema-validity, drop, and dup rates recorded (E-002).
- [ ] Actual generation cost in `cost-analysis.md`.
- [ ] All kept examples pass `schema.parse_and_validate`.

## Risks
| Risk | Likelihood | Impact | Mitigation | Detection |
|------|:--:|:--:|------|------|
| Cost overrun | Med | **High** | Pilot-based estimate, `--confirm`, resumable checkpoints | live $ vs budget counter |
| Bad teacher labels taught to student | Med | High | Schema validation + drop; spot-check a sample | high drop rate / manual audit |
| Test leakage via near-dups | Med | High | Hash/near-dup exclusion vs test set | intersection check = ∅ |
| Distribution mismatch (synthetic vs real) | Med | Med | Use real inputs; profile distribution | E-002 distribution looks off |
| Duplicates inflate apparent data | Med | Med | Dedup step + report rate | dup rate metric |

## Estimated complexity
**Medium–High.** 1–2 sessions; the run itself may be long (batch offline).

## What must NOT be done in this phase
- No training yet (Phase 3).
- Do not touch the frozen test set.
- Do not launch the full run without the approved estimate + `--confirm`.

## Persist for next session
- Commit `dataset.py` + stats; record dataset paths + counts in `PROJECT_STATE.md`.
- Handoff: dataset ready, sizes, cost; next action = choose base model + smoke-train (Phase 3).
