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

### E-001 — Teacher baseline (ceiling) at $0   [Phase 1]  · ⚠️ REFRAMED by D-013
- **D-013 pivot:** the original paid A/B (Opus 5 ceiling vs Haiku 4.5 cost-tier, D-007) is
  **cancelled** — no paid teacher, no ~$0.55 pilot. Reframed to a single **$0 / open-source** teacher
  ceiling; the model is **TBD (not chosen)**.
- Hypothesis: an open-source teacher run at $0 achieves a usably high field-F1 on the frozen receipts
  test set → a usable ceiling. If it does **not**, **stop and reconsider** (documented failure mode).
- Variable: teacher model (**open-source, TBD**) — no paid cost tier anymore.
- Control: frozen test set, fixed extraction prompt, same evaluator code path.
- Metrics to record: field-F1, schema-validity rate, exact-match, per-field accuracy. **Teacher $ = 0**
  (no per-call cost to record).
- Status: **not yet run** — schema / evaluator / converter / frozen-test built & tested offline; now
  blocked on the **$0/open-source teacher decision** (D-013), not on paid-pilot approval.
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
