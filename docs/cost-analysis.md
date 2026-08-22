# Cost Analysis

The economic core of the project. **Do not assume self-hosting is cheaper — prove it.** Every
number is measured or an explicit, labelled assumption (pricing knobs live in `config.py`). Model
prices are pulled at implementation time (see the `claude-api` skill) — no stale prices hardcoded
in docs.

---

> **⚠️ $0 STRATEGY PIVOT (D-013, 2026-08-22).** The paid Anthropic/Claude teacher plan is
> **CANCELLED**; the project must now cost **$0**. Every paid-teacher figure below — the ~$0.55 Opus 5
> pilot (§1a) and the "teacher API" rent baseline (§2–§3) — is a **void placeholder** pending a
> $0/open-source reframe. The teacher is now an open-source model run at $0 (TBD — not chosen); there
> is **no paid pilot** and no per-call teacher cost. Models and the reframed break-even are
> **deliberately not decided in this pass.**

## 1. Generation cost — pilot estimate (Phase 1) → full run (Phase 2)

### 1a. Teacher ceiling run (Phase 1) — **$0, open-source (D-013)** · *paid pilot cancelled*

**Superseded by D-013.** The paid pilot once described here (run ~50 receipts through a paid Claude
teacher; ~$0.55 on Opus 5; A/B Haiku 4.5) is **CANCELLED — $0 spent, never to run.** Under the $0
constraint the ceiling is measured by running an **open-source teacher at $0** (locally / free
compute) over the same ~50 CORD inputs and scoring vs gold. There is **no per-call teacher cost** to
estimate and no paid-approval gate to clear.

_TBD (deferred to the $0-teacher decision session; no model chosen here):_

| Knob | Value |
|------|:--|
| Teacher cost | **$0** (open-source; local / free compute) |
| Teacher model | _TBD — open-source, not yet chosen (D-013)_ |
| Ceiling inputs | ~50 from `data/cord/train.jsonl`, scored with `CORD_SCORED_FIELDS` (D-010) |
| Compute host | _TBD — must be $0 (local GPU / free tier)_ |

### 1b. Full-run generation cost (Phase 2) — **must be $0 (D-013)** *(was: the main cash outlay)*

| Item | Value |
|------|:-----:|
| Teacher generation cost | **$0** — open-source teacher (D-013); no paid pilot |
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

## 3. Break-even (Phase 6) — the headline number  · ⚠️ reframe pending (D-013: the paid teacher_cost baseline is void)

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
