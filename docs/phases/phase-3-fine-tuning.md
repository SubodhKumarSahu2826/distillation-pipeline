# Phase 3 — Student Fine-Tuning (LoRA / QLoRA)

> Start only on **"Start Phase 3."** Smoke-train before full-train. Log everything to W&B.

## Objective
Fine-tune a 7–8B open student on the teacher-labelled data with LoRA/QLoRA, producing **at least
two configurations** (LoRA rank 8 vs 32) so there is a real trade-off to discuss — not one lucky
run.

## Prerequisites
- Phase 2 complete: `train.jsonl`, `val.jsonl`, dataset stats.
- GPU access (rented). `WANDB_API_KEY`, `HF_TOKEN` in `.env`.
- Base model chosen — recommend **Llama-3.1-8B-Instruct** (broad vLLM/PEFT support) or
  **Qwen2.5-7B-Instruct** (strong structured output). Record choice in `decisions.md`.

## Tasks
1. **Baseline the base model** (no fine-tune) on val → shows the lift fine-tuning provides.
2. **Training module** `src/distill/train.py`: load base (4-bit for QLoRA), attach LoRA, format
   examples to the schema (prompt→JSON), mask prompt tokens, W&B logging (loss, LR, per-epoch val
   metric, sample outputs at each checkpoint), save adapter.
3. **SMOKE RUN (compute gate):** a few steps on a tiny subset — proves the loop runs, fits GPU
   memory, and produces a valid-JSON sample. Record peak VRAM. **Only then** full runs.
4. **E-003 — rank 8 vs rank 32**, everything else identical (seed, data, LR, epochs, batch).
5. Watch for **overfitting after 2–3 epochs** and LR-too-aggressive degradation; use early stop /
   best-checkpoint on val.
6. (Optional **E-004**) QLoRA-4bit vs LoRA-bf16 if GPU-constrained.
7. Record training cost (GPU $/hr × hours) → `docs/cost-analysis.md` §5. Pick the best adapter
   for serving; record val metrics in `benchmarking.md` (student per-config table).

## Files/components expected
`src/distill/train.py`, `configs/lora_r8.yaml`, `configs/lora_r32.yaml`,
`scripts/train.py` (`--config`, `--smoke`), `models/lora-r8/`, `models/lora-r32/` (gitignored),
tests for the data-formatting/masking function (no GPU).

## Experiments
- **E-003 rank 8 vs 32** (required). Optional **E-004 QLoRA vs LoRA**.

## Tests
- Prompt/label formatting: prompt tokens masked, target = JSON, round-trips through tokenizer.
- Config loading: yaml → typed run config.
- (No GPU in CI — training itself is run manually and logged to W&B.)

## Expected outputs
- Two adapters, W&B runs with curves + sample outputs, per-config val metrics, training cost,
  chosen best adapter.

## Acceptance criteria
- [ ] Base-model baseline recorded (lift is visible).
- [ ] Smoke run passed with recorded peak VRAM before any full run.
- [ ] Both r8 and r32 trained under identical conditions; E-003 filled with actual results.
- [ ] Overfitting checked (val curve), best checkpoint selected on val (not test).
- [ ] Training cost recorded.

## Risks
| Risk | Likelihood | Impact | Mitigation | Detection |
|------|:--:|:--:|------|------|
| OOM / doesn't fit GPU | Med | High | QLoRA 4-bit, smoke run measures VRAM first | smoke-run VRAM |
| Overfitting on small data | **High** | Med | early stop, 2–3 epoch watch, val-based selection | val metric turns down |
| LR too aggressive → degradation | Med | Med | conservative LR + warmup; compare to base | loss spikes / val drop |
| Unfair r8-vs-r32 comparison | Med | Med | hold everything else fixed + same seed | config diff review |
| Tuning on test set (leakage) | Low | **High** | selection uses val only; test still frozen | code review of selection |
| Wasted GPU $ | Med | Med | smoke first, cap epochs, spot instances | GPU hours vs plan |

## Estimated complexity
**High.** 2–3 sessions (setup + two runs + analysis).

## What must NOT be done in this phase
- No touching the frozen test set (all selection on val).
- No serving/router work (Phase 5).
- No open-ended hyperparameter sweeps — just the planned configs.

## Persist for next session
- Commit `train.py`, configs; record adapter paths + val metrics + training cost.
- Handoff: best adapter path, its val metric, W&B links; next action = full test-set benchmark.
