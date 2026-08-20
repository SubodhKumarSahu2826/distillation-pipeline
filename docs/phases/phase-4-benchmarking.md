# Phase 4 — Teacher vs Student Benchmark

> Start only on **"Start Phase 4."** This is where the **frozen test set is finally used** —
> exactly once, for final numbers.

## Objective
Produce the honest **3-axis comparison** — quality, cost, latency — between teacher and the best
student, plus the **quality-retention** figure, all on the untouched test set under comparable
conditions.

## Prerequisites
- Phase 3 complete: best adapter selected on val.
- Phase 1 teacher baseline available. Frozen `test.jsonl` untouched.

## Tasks
1. **Unfreeze test set for evaluation only** (`--allow-test`). Run **teacher** and **student** on
   the identical test inputs.
2. **Quality axis:** field-F1, schema-validity, exact-match for both; compute
   **retention = student ÷ teacher**. Reuse the *same* `evaluate.py` code for both.
3. **Latency axis:** p50 & p95 for both **under comparable concurrency** (`bench.py`). Student
   served via the Phase-5 path or a local vLLM instance; teacher via API. Record conditions.
4. **Cost axis:** teacher $/1k from measured tokens×price; student $/1k from GPU-hour ÷ measured
   throughput (incl. idle) — use the `economics.py` model (may be stubbed here, finalized Phase 6).
5. **Warm-up benchmark first** (small N) before the full timed run (avoid a costly misconfigured
   sweep).
6. Fill the **3-axis table** in `docs/benchmarking.md`; write an honest narrative — if the student
   underperforms, **publish it and explain why** (a reported negative result reads as trustworthy).

## Files/components expected
`src/distill/bench.py` (latency/throughput/error-rate harness), extend `evaluate.py`,
`scripts/benchmark.py` (`--warmup`, `--allow-test`), results in `artifacts/bench/*.json`,
final tables in `docs/benchmarking.md`.

## Experiments
- Final quality/latency/cost measurements (not a hypothesis run, but recorded with conditions).

## Tests
- Metric functions already unit-tested (Phase 1); add a test that teacher & student go through the
  **same** metric path.
- Latency harness: percentile math verified on a synthetic list.

## Expected outputs
- The completed **Metric | Teacher | Student | Difference** table; retention %; measurement
  conditions documented.

## Acceptance criteria
- [ ] Test set used exactly once, via the guard flag; no tuning done here.
- [ ] All three axes measured for both models under comparable conditions.
- [ ] Quality retention reported; narrative is honest about any shortfall.
- [ ] Raw results stored in `artifacts/`, summary in `benchmarking.md`.

## Risks
| Risk | Likelihood | Impact | Mitigation | Detection |
|------|:--:|:--:|------|------|
| Non-comparable conditions (concurrency/prompt) | Med | **High** | fix identical inputs, sampling, concurrency; document | conditions table review |
| Idle GPU time ignored → flattering cost | Med | **High** | amortize over measured throughput incl. idle | economics formula review |
| Accidental tuning-to-test | Low | **High** | single-use guard; no config changes after seeing test | git diff after unfreeze |
| Latency noise | Med | Med | warm-up, enough samples, report p50/p95 | variance across repeats |
| Cherry-picked favorable result | Low | High | report full table + negatives | peer/self review |

## Estimated complexity
**Medium.** 1–2 sessions.

## What must NOT be done in this phase
- No changing the model/config after seeing test numbers (that would contaminate the claim).
- No fabricated or rounded-up numbers.
- No new training.

## Persist for next session
- Commit `bench.py`, results; fill `benchmarking.md` final table + `PROJECT_STATE.md`.
- Handoff: the three-axis numbers + retention; next action = stand up vLLM serving + router.
