# Cost Analysis

The economic core of the project. **Do not assume self-hosting is cheaper — prove it.** Every
number is measured or an explicit, labelled assumption (pricing knobs live in `config.py`). Model
prices are pulled at implementation time (see the `claude-api` skill) — no stale prices hardcoded
in docs.

---

## 1. Generation cost — pilot estimate (Phase 1) → full run (Phase 2)

### 1a. Pilot cost estimate (Phase 1) — estimate only, **nothing spent yet**

The pilot is the money gate: run ~50 receipts through the teacher, score against independent gold,
then decide the bulk tier. The numbers below are **labelled assumptions** (D-009), not measurements.

| Knob | Value (assumption) |
|------|:--|
| Pilot size | 50 receipts (`--limit 50`; may raise to 100) |
| Mean input tokens / request | ~700 (chars÷4 heuristic; **replace with free `count_tokens` on real inputs before spend**) |
| Assumed output tokens / request | ~300 (compact `receipt-v1` JSON) |
| Ceiling model | `claude-opus-5` — $5 in / $25 out per Mtok (list price; confirm on endpoint) |
| Cost-tier model | `claude-haiku-4-5` — cheaper; **confirm price on the agentrouter endpoint** before estimating |

Formula (as printed by `scripts/run_teacher.py`, which is dry-run by default):
`cost = N · (mean_in · price_in + mean_out · price_out) / 1e6`

- **Opus 5, 50 samples:** 50 · (700·5 + 300·25) / 1e6 = **~$0.55**  (100 samples ≈ **$1.10**).
- **Haiku 4.5, 50 samples:** far lower; exact figure pending confirmed Haiku pricing on the endpoint.

Method before any paid call (guardrails, CLAUDE.md §3): (1) acquire the receipts dataset;
(2) run the free `count_tokens` on the real pilot inputs and replace the ~700 estimate;
(3) confirm endpoint pricing; (4) re-run the dry-run to print the real projected cost;
(5) present it for **explicit approval**; (6) only then `--confirm`.

### 1b. Full-run generation cost (Phase 2) — the main cash outlay

| Item | Value |
|------|:-----:|
| Pilot size / cost | _TBD_ (measured in the Phase-1 pilot) |
| Estimated full-run cost (from pilot) | _TBD_ |
| **Actual full-run cost** | _TBD_ |
| Examples kept after filtering | _TBD_ |
| Effective $ per kept example | _TBD_ |

## 2. Cost model (defined here; implemented in `economics.py`, Phase 6)

**Teacher cost per request**
```
teacher_cost = in_tokens * price_in + out_tokens * price_out
teacher_cost_per_1k = 1000 * mean(teacher_cost)
```

**Student cost per request (amortized, incl. idle)**
```
gpu_cost_per_hour            = <rented GPU $/hr>
requests_per_hour_at_util    = throughput_req_per_s * 3600 * utilization   # utilization<1 => idle counted
student_cost_per_request     = gpu_cost_per_hour / requests_per_hour_at_util
student_cost_per_1k          = 1000 * student_cost_per_request
```
> Idle time is charged: `utilization` < 1 makes the effective per-request cost rise, which is the
> honest treatment the spec demands.

**Fallback-adjusted (router) cost per request**
```
blended = (1 - escalation_rate) * student_cost_per_request
        +      escalation_rate  * (student_cost_per_request + teacher_cost_per_request)
```
(The escalated request pays for the student attempt *and* the teacher call.)

## 3. Break-even (Phase 6) — the headline number

Self-hosting has a fixed-ish GPU spend regardless of volume; the API scales linearly. Break-even
is where the blended self-hosted cost per day equals the teacher-only cost per day:

```
teacher_daily(V)   = V * teacher_cost_per_request
selfhost_daily(V)  = gpu_cost_per_day + V * escalation_rate * teacher_cost_per_request
break_even_V       = gpu_cost_per_day / ( teacher_cost_per_request * (1 - escalation_rate) )
```

| Output | Value |
|--------|:-----:|
| **Break-even requests/day** | _TBD_ |
| Break-even requests/month | _TBD_ |
| GPU $/day (serving) | _TBD_ |
| Escalation rate used | _TBD_ (from Phase 5) |

## 4. Savings at different traffic levels (Phase 6)

| Requests/day | Teacher-only $/mo | Self-host (blended) $/mo | Savings $/mo | Winner |
|:------------:|:-----------------:|:------------------------:|:------------:|:------:|
| 1k | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 10k | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 100k | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| 1M | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

## 5. Training cost (one-time, Phase 3)

| Item | Value |
|------|:-----:|
| GPU $/hr | _TBD_ |
| Hours (r8 + r32 + smoke) | _TBD_ |
| **Total training cost** | _TBD_ |

> Note whether one-time training cost is amortized into break-even or reported separately
> (default: reported separately + a sensitivity note).
