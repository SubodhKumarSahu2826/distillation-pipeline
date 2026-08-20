# Phase 7 — Finalization

> Start only on **"Start Phase 7."** No new capability — package the evidence so a stranger can
> reproduce it and a reviewer can trust it.

## Objective
Ship a coherent, reproducible repository: README with **measured** results, an architecture
diagram, reproducibility instructions, and a final verification pass. This is what makes the
project portfolio-defensible.

## Prerequisites
- Phases 0–6 complete with results recorded in the docs.

## Tasks
1. **README.md** — problem, task, approach, the **3-axis table**, **quality retention**,
   **break-even req/day**, generation + training cost, escalation rate, how to reproduce, and an
   honest limitations section. **Every number copied from the measured docs — none invented.**
2. **Architecture diagram** — render the data flow (`docs/architecture.md` §1) to an image in
   `artifacts/`; embed in README.
3. **Reproducibility** — pinned deps, seeds, exact commands per phase, hardware used, dataset
   provenance/license; a `make`-style or documented command list.
4. **Final verification** — fresh `pytest -q`; re-run the evaluation on the frozen test set to
   confirm the headline numbers reproduce; confirm the served endpoint + escalation path work.
5. **Resume line** — fill X/Y/Z from actual results (never invented).
6. **Cleanup** — ensure gitignored artifacts aren't committed; docs cross-links valid; decisions
   log current. Consider a git tag `v1.0`.
7. (Optional **stretch**, only if time): 4-bit serving re-measure (E-005); per-customer adapters;
   continuous data collection for retraining — each documented as clearly optional.

## Files/components expected
Final `README.md`, `artifacts/architecture.(svg|png)`, updated docs, pinned dependency file,
version tag.

## Experiments
- None new (optional stretch experiments only).

## Tests
- Full `pytest -q` green.
- Reproduction check: re-running evaluation yields the README's numbers (within noise).

## Expected outputs
- A complete repo a stranger can clone and understand; README with real numbers; diagram; repro
  steps; final benchmark confirmed.

## Acceptance criteria
- [ ] README contains the 3-axis table, retention, break-even, costs, escalation rate — all
      matching the measured docs.
- [ ] Reproduction steps verified end-to-end (at least evaluation + serving smoke).
- [ ] Diagram embedded; docs cross-referenced; no secrets/large artifacts committed.
- [ ] Resume line filled from actual results.

## Risks
| Risk | Likelihood | Impact | Mitigation | Detection |
|------|:--:|:--:|------|------|
| README numbers drift from measured docs | Med | **High** | copy from `benchmarking.md`/`cost-analysis.md`; cross-check | diff numbers |
| Not actually reproducible | Med | High | pin deps/seeds; dry-run the steps on a clean checkout | repro check |
| Fabricated/rounded results slip in | Low | **High** | rule: only measured numbers; cite source doc | review |
| Scope creep via stretch goals | Med | Med | stretch is optional + time-boxed | phase gate |

## Estimated complexity
**Low.** ~1 session (excluding optional stretch).

## What must NOT be done in this phase
- Do not invent, round-up, or "estimate" any headline number.
- Do not add new frameworks/services for polish.
- Do not start stretch goals before the core README + repro are done.

## Persist (project close-out)
- Mark all phases ✅ in `PROJECT_STATE.md`; final handoff summarizing outcomes + any stretch
  follow-ups; tag the release.
