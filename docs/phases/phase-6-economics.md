# Phase 6 — Economics + Break-Even

> Start only on **"Start Phase 6."** This produces the headline artifact: the break-even number.
> No new model work — this is analysis on measured inputs.

## Objective
Turn the measured numbers (Phase 4 throughput/latency/cost, Phase 5 escalation rate) into a
defensible cost model and compute the **break-even requests/day**, plus a savings curve. Do **not**
assume self-hosting is cheaper — let the math decide.

## Prerequisites
- Phase 4 cost/latency/throughput measured.
- Phase 5 escalation rate measured.
- Pricing knobs in `config.py` (teacher $/token via `claude-api` skill; GPU $/hr from the rental).

## Tasks
1. `src/distill/economics.py` implementing the model in `docs/cost-analysis.md`:
   - `teacher_cost_per_1k` from measured tokens × current price;
   - `student_cost_per_1k` = GPU-hour ÷ measured throughput, **including idle** (utilization<1);
   - `blended` fallback-adjusted cost using the escalation rate;
   - `break_even_requests_per_day` (+ per month).
2. **Savings curve** at 1k / 10k / 100k / 1M req/day → table + a plot in `artifacts/`.
3. **Sensitivity analysis:** vary utilization, escalation rate, GPU price → show how break-even
   moves (honesty about assumptions). Note whether one-time training cost is amortized or separate.
4. Fill `docs/cost-analysis.md` §3–§5 with actual outputs; write the one-line economic result.

## Files/components expected
`src/distill/economics.py`, `scripts/economics.py`, `artifacts/savings_curve.(png|json)`,
completed `docs/cost-analysis.md`, unit tests for the cost math.

## Experiments
- Break-even computation + sensitivity sweep (documented assumptions).

## Tests
- Cost math on hand-checked inputs (e.g. known throughput/price → known $/1k).
- Break-even formula: at V = break_even, teacher_daily ≈ selfhost_daily.
- Edge cases: escalation_rate = 0 and = 1 behave sensibly.

## Expected outputs
- **Break-even requests/day** (the number), monthly figure, savings table + curve, sensitivity
  notes.

## Acceptance criteria
- [ ] Break-even computed from **measured** throughput, escalation rate, and current prices.
- [ ] Idle GPU time is included in the student cost (verified in the formula).
- [ ] Savings shown at multiple traffic levels; winner labelled at each.
- [ ] Sensitivity to key assumptions documented; nothing fabricated.

## Risks
| Risk | Likelihood | Impact | Mitigation | Detection |
|------|:--:|:--:|------|------|
| Misleading cost (idle ignored) | Med | **High** | idle in denominator; peer-check formula | formula review + unit test |
| Stale prices | Med | Med | pull current prices at run time; label date | price date recorded |
| Break-even hides high escalation cost | Med | High | fallback-adjusted blended cost drives it | escalation term present |
| Over-precise single number | Med | Low | report with sensitivity band | sensitivity table |

## Estimated complexity
**Low–Medium.** ~1 session (pure computation).

## What must NOT be done in this phase
- No new training/serving/benchmarks — only analysis on already-measured inputs.
- No assuming self-hosting wins; report it even if the API is cheaper at realistic volumes.

## Persist for next session
- Commit `economics.py` + results; record the break-even number in `PROJECT_STATE.md`.
- Handoff: break-even + savings summary; next action = finalize README/docs/repro (Phase 7).
