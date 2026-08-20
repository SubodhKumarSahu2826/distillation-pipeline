# Phase 5 — vLLM Serving + Fallback Router

> Start only on **"Start Phase 5."** Keep the router deterministic and simple. No distributed
> architecture.

## Objective
Serve the student with vLLM (continuous batching, paged attention), find the concurrency where
latency degrades, and put a **router** in front that escalates to the teacher on low confidence or
schema-validation failure — reporting the **escalation rate**.

## Prerequisites
- Phase 3 best adapter; Phase 4 benchmark for context.
- GPU for serving.

## Tasks
1. **Serve** `src/distill/serve.py`: launch vLLM (OpenAI-compatible) with the base model + best
   adapter; health check; documented request/response format.
2. **Throughput sweep:** raise concurrency (1 → N), record throughput + p50/p95, find the knee
   where p95 degrades → `benchmarking.md` sweep table. **Small warm-up sweep before the full one.**
3. **Router** `src/distill/router.py` (deterministic function):
   - call student → `schema.parse_and_validate`;
   - **escalate if invalid**, or if the confidence signal is below a threshold (low seq log-prob /
     required-field nulls; keep simple);
   - on escalation, call teacher, return its (validated) result; **record which model served**.
4. **Confidence threshold** tuned on **val**, reported on test; report escalation-trigger breakdown
   (schema-fail vs low-confidence).
5. **Measure escalation rate** on the test workload; measure post-router effective quality.
6. Error handling: teacher/API failure, malformed output, timeouts → graceful fallback + logged.

## Files/components expected
`src/distill/serve.py`, `src/distill/router.py`, `scripts/serve.py`, `scripts/route_eval.py`,
optional `Dockerfile` (serving repro only), router/serve tests (mock the endpoints), sweep +
router results in `benchmarking.md`.

## Experiments
- Throughput/concurrency sweep (find degradation knee).
- Escalation-rate measurement + threshold selection.

## Tests
- Router unit tests (mocked student/teacher): valid student output → returned, not escalated;
  invalid → escalates to teacher; teacher failure → graceful error.
- Schema-fail path deterministically triggers escalation.
- Health check returns ready only when the model is loaded.

## Expected outputs
- A running endpoint; concurrency sweep table; **escalation rate**; router that provably falls
  back to the teacher.

## Acceptance criteria
- [ ] Endpoint serves the student and passes health checks.
- [ ] Throughput sweep shows the latency-degradation point.
- [ ] Router escalates on schema-fail and low-confidence; escalation rate recorded.
- [ ] Post-router quality ≥ student-only quality; error paths handled.

## Risks
| Risk | Likelihood | Impact | Mitigation | Detection |
|------|:--:|:--:|------|------|
| vLLM/adapter incompatibility | Med | High | verify base+LoRA supported; merge adapter if needed | serve smoke test |
| Escalation rate too high → economics collapse | Med | **High** | improve student/threshold; report honestly; it feeds break-even | measured rate |
| Router over-engineered | Med | Med | keep it one deterministic function | code review vs complexity policy |
| Confidence signal unreliable | Med | Med | primary signal = schema validity (deterministic) | ablation: schema-only vs +confidence |
| Serving OOM at high concurrency | Med | Med | cap concurrency at measured knee; set KV limits | sweep OOM point |

## Estimated complexity
**Medium–High.** 2 sessions.

## What must NOT be done in this phase
- No Kubernetes/Redis/queue/distributed anything.
- No retuning the model to the test set.
- No elaborate confidence ML — thresholded signal only.

## Persist for next session
- Commit `serve.py`, `router.py`; record endpoint run cmd, sweep table, escalation rate.
- Handoff: escalation rate + serving throughput/util numbers; next action = finalize economics.
