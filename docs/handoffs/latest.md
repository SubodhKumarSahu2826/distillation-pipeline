# Handoff — latest

> Overwrite this file at the end of every session. It is the first thing the next session reads
> after the three control files. Keep it concrete: what changed, what's next, how to verify.

---

## Session date
2026-08-21 — **Phase 1 (Task selection + teacher baseline) — IN PROGRESS.** Resolved the **CORD
evaluation policy** (D-010). Non-paid, offline work only; no dataset downloaded, no API call.

## What happened this session
Resolved *how CORD is scored* before acquiring data or spending anything. Decision (D-010): use the
**original** CORD (`clovaai/cord`, not `cord-v2`); on CORD, **score only the fields CORD labels** —
`{subtotal, tax, total, line_items}` — and **exclude `vendor`/`date`/`currency`** from the headline
metric, because CORD provides no ground truth for them (scoring them would count correct extractions
as false positives and could never credit a correct value).

Implementation (minimal, general, reusable — no CORD names in the evaluator):
- **`src/distill/evaluate.py`** — added an optional **`scored_fields` allow-list** to `evaluate` and
  `score_pair` (subset of the new `ALL_FIELDS`; default `None` = score every field → **existing
  behavior byte-for-byte unchanged**). Fields the policy excludes contribute **no TP/FP/FN** and are
  dropped from exact-match and per-field accuracy. `Report` now carries `scored_fields` (self-
  documenting). **Schema-validity is untouched** — outputs are still validated against the full
  `receipt-v1` contract regardless of the policy. Helpers `_resolve_fields` (validates the allow-list,
  rejects unknown names) and `_restrict` (projects exact-match onto scored fields).
- **`src/distill/dataset.py`** — **NEW** (the pre-designated module per the repo map). Holds
  `CORD_SCORED_FIELDS = {subtotal, tax, total, line_items}` and `CORD_UNSCORED_FIELDS =
  {vendor, date, currency}` with a docstring explaining CORD's label coverage. **No converter yet.**
- **`schema.py` unchanged** — `receipt-v1` is intact (requirement honored).
- Tests: `tests/test_evaluate.py` +4 (allow-list excludes unlabeled fields with no penalty; still
  penalizes a wrong labeled field; `score_pair` ignores unscored scalars; unknown field rejected);
  `tests/test_dataset.py` NEW +2 (CORD constants exact; scored ∪ unscored == `ALL_FIELDS`).
- Docs: **D-010** in `decisions.md`; scored-field policy subsection in `task-selection.md`; scored-
  field note + row in `benchmarking.md`; `PROJECT_STATE.md` / `CURRENT_PHASE.md` updated.

Concrete effect (illustrative 1-record case): default scoring gives F1 **0.77** (fp=3 from the three
unlabeled fields); CORD policy gives F1 **1.00**, fp=0 — a ~23-point artifact removed.

## State of the repo
- 🟡 Phase 1 in progress. `pytest` → **26 passed** (was 20; +4 evaluate, +2 dataset);
  `ruff check .` → clean.
- Phase-1 code is committed at **`71e14d9`**. **This session's change is UNCOMMITTED**
  (`evaluate.py`, `test_evaluate.py` modified; `dataset.py`, `test_dataset.py` new; docs) — hand the
  commit to the user (sandbox denies `.git` writes, D-005). Suggested message:
  `feat(phase-1): add dataset-specific scored-field policy for CORD (D-010)`.
- **$0 spent.** Pilot still **estimated** ~$0.55 (50 × Opus 5, labelled assumption), not yet run.

## Exact next action
1. **Acquire the original CORD** (`clovaai/cord`, **not** `cord-v2`) — *user-run* (network is
   sandbox-blocked). Land the ground-truth JSON for **train / dev(validation) / test** under
   **`data/raw/cord/`**. We need the **text layer + category labels** (word text + `menu.*` /
   `sub_total.*` / `total.*` tags); images are **not** needed (text-only pipeline). Verify the gold
   maps onto `receipt-v1` on arrival (D-006).
2. **Phase 2** (not now): write the CORD→`receipt-v1` converter in `src/distill/dataset.py`
   (`menu`→line_items, `sub_total.subtotal_price`→subtotal, `sub_total.tax_price`→tax,
   `total.total_price`→total; vendor/date/currency left `null`).
3. **Build the frozen test set** `data/splits/test.jsonl` (hash-split, no near-dup leakage);
   do not read it again until Phase 4.
4. **Before any paid call**, follow the approval protocol: free `count_tokens` on real inputs →
   confirm endpoint pricing → dry-run `run_teacher.py --input data/raw/cord/… --limit 50` →
   **present requests/tokens/cost/pilot-size and wait for explicit approval.**
5. After approval: `--confirm` pilot for Opus 5, then Haiku 4.5; **score with
   `evaluate(..., scored_fields=dataset.CORD_SCORED_FIELDS)`** (D-010); record E-001 +
   `benchmarking.md` teacher table + actual cost in `cost-analysis.md` §1b.

## How the next session verifies it's on track
- `.venv/bin/python -m pytest` → **26 passed**; `/opt/anaconda3/bin/ruff check .` clean.
- `python -c "from distill.evaluate import evaluate; from distill.dataset import CORD_SCORED_FIELDS"`
  imports cleanly; `evaluate([...], [...], scored_fields=CORD_SCORED_FIELDS)` returns a `Report`
  whose `.scored_fields == ('subtotal','tax','total','line_items')`.
- `PROJECT_STATE.md` shows Phase 1 🟡 with `dataset.py` in the artifacts index; D-010 in `decisions.md`.

## Watch-outs handed forward
- **Every git commit is user-run** (D-005). Venv has **no `ruff`/`pytest` console scripts** — use
  `.venv/bin/python -m pytest` and the anaconda `ruff` at `/opt/anaconda3/bin/ruff`.
- **Do NOT write the CORD converter until the data files exist** (requirement + Phase-2 scope).
- **Dataset download is blocked in-sandbox** (network allow-list) — gates the whole pilot.
- **Use `scored_fields=CORD_SCORED_FIELDS` for every CORD score** — a bare `evaluate(...)` would
  silently penalize vendor/date/currency and understate both the ceiling and retention.
- **Pricing is a labelled assumption** (D-009) — confirm on the endpoint + run free `count_tokens`
  before spend. The pilot is the **first money step**: pilot 50, get explicit approval on the estimate.
