# Benchmarking

All measured quality/latency/throughput results land here. **Never fabricate numbers** — every
cell is either measured or `TBD`. Raw outputs live in `artifacts/`; this file holds the summary.

---

## Teacher baseline (Phase 1)

| Metric | Value | Notes |
|--------|:-----:|-------|
| Field-level F1 (primary) | _TBD_ | on frozen test set |
| Schema-validity rate | _TBD_ | |
| Full-record exact match | _TBD_ | |
| Test set size | _TBD_ | frozen, untouched until Phase 4 |
| Teacher model / prompt version | _TBD_ | |

> This is the **ceiling**. All retention numbers are relative to it.

## Student per-config (Phase 3 → val; Phase 4 → test)

| Config | Val F1 | Test F1 | Schema-valid % | Overfit epoch? | W&B |
|--------|:------:|:------:|:--------------:|:--------------:|-----|
| LoRA r8 | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| LoRA r32 | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

## Final 3-axis comparison (Phase 4) — the required table

| Metric | Teacher | Student (best) | Difference |
|--------|:-------:|:--------------:|:----------:|
| Quality — field F1 | _TBD_ | _TBD_ | _TBD_ |
| Quality — schema-valid % | _TBD_ | _TBD_ | _TBD_ |
| **Quality retention** (student ÷ teacher) | 100% | _TBD_ | — |
| Cost per 1k requests | _TBD_ | _TBD_ | _TBD_ |
| Latency p50 | _TBD_ | _TBD_ | _TBD_ |
| Latency p95 | _TBD_ | _TBD_ | _TBD_ |
| Throughput (req/s @ concurrency C) | _TBD_ | _TBD_ | _TBD_ |
| Error rate | _TBD_ | _TBD_ | _TBD_ |

Measurement conditions (fill in): concurrency level(s), hardware, input length distribution,
sampling params, date. Teacher and student measured under **comparable** conditions.

## Serving throughput sweep (Phase 5)

| Concurrency | Throughput (req/s) | p50 | p95 | Notes |
|:-----------:|:------------------:|:---:|:---:|-------|
| 1 | _TBD_ | _TBD_ | _TBD_ | |
| 8 | _TBD_ | _TBD_ | _TBD_ | |
| 32 | _TBD_ | _TBD_ | _TBD_ | knee? |
| … | _TBD_ | _TBD_ | _TBD_ | find where p95 degrades |

## Router (Phase 5)

| Metric | Value | Notes |
|--------|:-----:|-------|
| Escalation rate (test workload) | _TBD_ | fraction routed to teacher |
| Post-router effective quality | _TBD_ | should meet/exceed student-only |
| Escalation triggers breakdown | _TBD_ | schema-fail vs low-confidence |
