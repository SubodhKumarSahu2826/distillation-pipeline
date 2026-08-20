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

### E-001 — Teacher baseline (ceiling)   [Phase 1]
- Hypothesis: teacher achieves ≥ high-80s field-F1 on the frozen test set → a usable ceiling.
- Variable: none (single measurement).
- Control: frozen test set, fixed prompt, fixed teacher model.
- Expected: high F1; if not, **stop and reconsider the task** (documented failure mode).
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
