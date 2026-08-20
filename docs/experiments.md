# Experiments Log

Every experiment is registered here **before** running it, with a hypothesis, then updated with
the actual result. This is how we avoid "a single lucky run." Newest at top. Keep raw curves in
W&B; keep only the summary here.

Format (mandatory):

```
### E-00N — <name>   [Phase N]
- Hypothesis:
- Variable (what changes):
- Control (held fixed):
- Expected result:
- Actual result:
- Conclusion / decision:
- Evidence: <W&B run URL / artifact path>
```

---

## Planned experiments (hypotheses to fill on execution)

### E-001 — Teacher baseline (ceiling) + cost-tier A/B   [Phase 1]
- Hypothesis: the ceiling teacher (Opus 5) achieves ≥ high-80s field-F1 on the frozen receipts test
  set → a usable ceiling; a cheaper tier (Haiku 4.5) may retain most of that F1 at a fraction of the
  cost → good enough for bulk generation (informs Phase 2, D-007).
- Variable: teacher model tier (**claude-opus-5** vs **claude-haiku-4-5**) on identical inputs/prompt.
- Control: frozen test set, fixed prompt (`extract-v1`), same evaluator code path, `effort=low`.
- Metrics to record: field-F1, schema-validity rate, exact-match, per-field accuracy, and
  **actual pilot $** for each tier.
- Expected: Opus 5 high F1 (usable ceiling); Haiku 4.5 close behind. If the ceiling F1 is **not**
  high, **stop and reconsider the task** (documented failure mode) rather than proceed to tuning.
- Status: **not yet run** — schema, evaluator, teacher client and the dry-run cost gate are built &
  tested offline; blocked on acquiring the dataset + building the frozen test set, then explicit
  pilot approval (paid). Estimate ~$0.55 for a 50-sample Opus 5 pilot (see `cost-analysis.md` §1a).
- Actual: _TBD_
- Conclusion: _TBD_

### E-002 — Dataset quality profile   [Phase 2]
- Hypothesis: ≥ ~90% of teacher outputs are schema-valid; duplicates < ~10%.
- Variable: none (measurement of the generation run).
- Control: fixed prompt/model from Phase 1.
- Metrics to record: validity rate, filter/drop rate, near-dup rate, field-value distribution,
  examples kept, **actual generation cost**.
- Actual: _TBD_

### E-003 — LoRA rank 8 vs rank 32   [Phase 3]  ← the required trade-off run
- Hypothesis: r32 gives higher val metric but risks earlier overfitting; r8 is cheaper and may
  suffice → a real trade-off to discuss.
- Variable: LoRA rank (8 vs 32). **Everything else identical** (base model, data, LR, epochs,
  seed, batch size).
- Control: same train/val split, same seed.
- Expected: r32 ≥ r8 on val by a small margin; watch overfitting after 2–3 epochs.
- Actual: _TBD_
- Evidence: W&B run URLs _TBD_

### E-004 — (optional) QLoRA 4-bit vs LoRA bf16   [Phase 3, if GPU-constrained]
- Hypothesis: 4-bit training costs little quality vs bf16 but fits a 24GB GPU → cheaper.
- Variable: quantization. Control: rank, data, schedule.
- Actual: _TBD_

### E-005 — (stretch) 4-bit serving quantization re-measure   [Phase 7 stretch]
- Hypothesis: 4-bit **serving** keeps quality within a small delta while raising throughput.
- Actual: _TBD_

---
_(Add E-00N entries as new experiments are designed. Never delete a negative result — a reported
negative result is more trustworthy than a suspiciously perfect one.)_
