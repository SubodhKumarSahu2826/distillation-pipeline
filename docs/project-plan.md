# Project Plan — Fine-Tuning Model Distillation Pipeline

Master plan and hub. Links out to `architecture.md`, `task-selection.md`, the per-phase docs,
and the living ledgers (`decisions.md`, `experiments.md`, `benchmarking.md`, `cost-analysis.md`).

---

## 1. Objective (the real one)

Not "fine-tune an 8B model." The objective is to **demonstrate, with measured evidence,
whether a frontier teacher's capability on one narrow task can be distilled into a smaller
self-hosted student while retaining sufficient quality and improving inference economics** —
and to compute the **break-even request volume** above which self-hosting wins.

The project succeeds if it produces *evidence*, not claims:

| Evidence | Where measured |
|----------|----------------|
| Teacher quality (the ceiling) | Phase 1 |
| Student quality | Phase 4 |
| Quality retention (student ÷ teacher) | Phase 4 |
| Training cost | Phase 3 |
| Inference cost (teacher API vs student GPU-hour, incl. idle) | Phase 4 / 6 |
| GPU utilization & idle cost | Phase 4 / 6 |
| Latency p50 / p95 | Phase 4 |
| Throughput & concurrency ceiling | Phase 4 / 5 |
| Escalation (fallback) rate | Phase 5 |
| Fallback-adjusted cost | Phase 6 |
| **Break-even requests/day** | **Phase 6** |

## 2. Definition of done (from the spec)

1. A **3-axis benchmark table** — quality, cost, latency — teacher vs student.
2. A **stated break-even request volume** (requests/day).
3. A **served endpoint** (vLLM) with a **working escalation path back to the teacher**, with a
   reported escalation rate.
4. A README containing **only measured numbers** (never fabricated).

Resume line this unlocks (numbers filled from experiments, never invented):
> "Distilled a frontier-model task into an 8B student at **X%** of teacher accuracy and **~1/Y**
> the cost; served with vLLM, break-even at **Z requests/day**."

## 3. Chosen task (summary)

**Structured extraction: one document type → a fixed JSON schema.** Full justification, schema,
eval method, and rejected alternatives in `docs/task-selection.md`. Why it fits: deterministic
honest eval (field-F1 + schema validity), abundant real inputs, the teacher is reliable at it,
an 8B student can learn a bounded-format mapping, and **schema validation gives the router a
crisp deterministic escalation signal** — so we need no LLM judge.

## 4. Architecture (summary)

Input → Teacher → validate/filter → dataset → fine-tune → student → evaluate → benchmark →
vLLM serve → router (student → validate/confidence → escalate to teacher). Component-by-component
spec in `docs/architecture.md`.

## 5. Technology stack (summary)

Python · PyTorch · HF Transformers · PEFT (LoRA/QLoRA) · TRL (SFT) · bitsandbytes (4-bit) ·
Weights & Biases · vLLM · FastAPI · Pydantic · HF datasets · pytest. **Deliberately excluded:**
LangChain, LangGraph, Redis, Celery, Kafka, PostgreSQL, vector DB, Kubernetes, MLflow, Airflow.
Docker optional (serving repro only). Full justification + exclusions in `docs/architecture.md`.

## 6. Phase breakdown

| Phase | Name | Core output | Complexity | Spends money? |
|------:|------|-------------|:---------:|:---:|
| 0 | Foundation | repo skeleton, config, tests, logging, repro | Low | No |
| 1 | Task selection + teacher baseline | schema, untouched test set, **teacher ceiling** | Medium | Yes (pilot: small) |
| 2 | Teacher dataset generation | filtered train/val/test + generation cost | Medium–High | **Yes (main cash cost)** |
| 3 | Student fine-tuning (LoRA r8 & r32) | adapters + W&B curves | High | Yes (GPU) |
| 4 | Teacher vs student benchmark | 3-axis table + retention | Medium | Yes (GPU + some API) |
| 5 | vLLM serving + router | endpoint + escalation rate | Medium–High | Yes (GPU) |
| 6 | Economics + break-even | **break-even req/day** + savings curve | Low–Medium | No |
| 7 | Finalization | README w/ measured results, repro, diagram | Low | No |

Each phase is scoped to fit one Claude Code session's context. Detail per phase lives in
`docs/phases/phase-N-*.md` and each contains: objective · prerequisites · tasks · files ·
experiments · tests · expected outputs · acceptance criteria · risks · complexity ·
**what must NOT be done** · what to persist for the next session.

## 7. Implementation order & dependencies

Strictly sequential 0 → 7. Hard dependencies: 2 needs 1's schema + inputs; 3 needs 2's splits;
4 needs 3's adapters **and** 1's untouched test set; 5 needs 3's best adapter; 6 needs 4's
latency/throughput + 5's escalation rate; 7 needs everything.

## 8. Cost-control principle (applies to every expensive step)

```
small sample → validate pipeline → estimate cost → get approval → large run
```

Concretely: 50–100 teacher calls before thousands; a few training steps before full training;
a small benchmark before the full concurrency sweep. Every money-spending script has
`--dry-run`, `--limit N`, prints an estimate, and requires an explicit confirm flag. See
`CLAUDE.md` §3.

## 9. Top risks (summary; full register in each phase doc)

1. Distilling a task the teacher is only mediocre at → student ceiling too low. *(Mitigate: Phase 1 ceiling gate.)*
2. Test-set contamination → inflated claims. *(Mitigate: hash-based split, test frozen until Phase 4.)*
3. Cost comparison that ignores idle GPU time → misleading. *(Mitigate: amortize over measured throughput incl. idle in Phase 6.)*
4. High escalation rate → economics collapse. *(Mitigate: measure it; break-even is fallback-adjusted.)*
5. Runaway API/GPU spend. *(Mitigate: pilots + confirm flags.)*

## 10. Context-continuity strategy

The repo is the memory. Control files (`CLAUDE.md`, `PROJECT_STATE.md`, `CURRENT_PHASE.md`) +
`docs/handoffs/latest.md` let any session resume in minutes. Big data/logs/outputs stay out of
context (gitignored dirs, summarized in docs). See `CLAUDE.md` §2 and §5.

## 11. Final outputs checklist (Phase 7 verifies all)

- [ ] Working repo, reproducible from README
- [ ] Teacher labelling + dataset pipeline
- [ ] Training pipeline (2 configs)
- [ ] Evaluation pipeline (frozen test set)
- [ ] Benchmark pipeline + 3-axis table
- [ ] Student adapter(s)
- [ ] vLLM endpoint + fallback router (escalation rate reported)
- [ ] Cost analysis + **break-even requests/day**
- [ ] Experiment records with hypotheses + actual results
- [ ] Architecture doc + diagram
- [ ] README with **measured** numbers only
