# CURRENT_PHASE.md — Active Phase Pointer

> The one thing to work on now. Update at the end of every session.

## Active phase

**Phase 1 — Task selection + teacher baseline. 🟡 IN PROGRESS.**

> **⚠️ $0 STRATEGY PIVOT (D-013, 2026-08-22).** The paid Anthropic/Claude teacher plan is
> **CANCELLED** — the project must now cost **$0**. The teacher becomes an **open-source model run
> locally / on free compute (TBD — not chosen)**. There is **no paid pilot**, no `--confirm` spend,
> no `count_tokens`/endpoint-pricing step. The paid steps once described here are **void**; the live
> next action is the **$0/open-source teacher strategy**. Models and the reframed economics are
> **deliberately not decided in this pass.**

Built & verified **offline** in Phase 1 so far (no money spent):
- `src/distill/schema.py` — the output contract, `SCHEMA_VERSION = "receipt-v1"`
  (Pydantic v2, `extra="forbid"`, `parse_and_validate` / `is_valid`). **Unchanged by D-010.**
- `src/distill/evaluate.py` — deterministic metrics: micro field-F1, schema-validity rate,
  exact-match, per-field accuracy; order-insensitive line-item matching. Now takes an optional
  **`scored_fields` allow-list** (default = all fields) so a dataset's unlabeled fields are neither
  rewarded nor penalized; `Report` records the scored set. Evaluator stays dataset-agnostic.
- `src/distill/dataset.py` — `CORD_SCORED_FIELDS = {subtotal, tax, total, line_items}` and
  `CORD_UNSCORED_FIELDS = {vendor, date, currency}` (D-010), **plus the deterministic CORD→`receipt-v1`
  converter** (D-011): `convert_record` → `{id, text, gold}`, with `build_gold` (groups `menu.*` by
  `group_id`; `sub_total.*`/`total.*` scalars), `build_text` (reconstructs OCR text from `quad` boxes),
  and `parse_amount` (last pure-numeric non-rate word; normalizes mixed separators).
- `scripts/convert_cord.py` — thin CLI: `data/raw/cord/*/json/*.json` → `data/cord/{train,dev,
  test}.jsonl` (offline, $0). Produced **1000** schema-valid records (800/100/100); 5 receipts legitimately
  have no line items; raw CORD verified unmodified (sha256 identical before/after).
- `src/distill/dataset.py::input_hash` + `scripts/freeze_test_set.py` — **frozen test set (D-012)**:
  froze CORD's own 100-record test split as-is → `data/splits/test.jsonl` + `test.manifest.json` (100
  normalized-input hashes, aggregate `872bec26…`). The split is internally clean (100 unique, 0 dup, 0
  empty); the leakage check found **9** test inputs also in train/val (8 train, 2 dev) — fixed on the
  *train/val* side in Phase 2, never by touching the test anchor. Offline, $0, idempotent.
- `src/distill/teacher.py` — prompt `extract-v1`, offline token/cost estimators, and a paid
  `extract()` path (`anthropic` imported lazily; captures usage + cost).
- `scripts/run_teacher.py` — pilot runner, **dry-run by default**; prints requests/tokens/price/
  projected-cost and refuses `*test*.jsonl` without `--allow-test`; needs `--confirm` (+ API key)
  to spend. It reads exactly the `{id, text}` records the converter emits.
- `config.py` teacher defaults set to the Opus 5 ceiling + labelled list prices (D-009);
  `pydantic` promoted to a runtime dep (D-008). **(⚠️ the paid Opus 5 defaults are SUPERSEDED by
  D-013 and now dormant/unused — no source change made this pass.)**
- Tests: `pytest` **42 passed** (3 smoke + 10 schema + 11 evaluate + 18 dataset); `ruff check` clean.

## Next exact action

**The CORD data is converted (D-011) and the test set is frozen (D-012). The remaining Phase-1 work is
NO LONGER a paid pilot (cancelled, D-013) — it is to define the $0/open-source teacher strategy, then
measure the ceiling at $0.** No further data-prep is needed.

1. **DONE — frozen test set (D-012).** `scripts/freeze_test_set.py` wrote `data/splits/test.jsonl`
   (100 records) + `data/splits/test.manifest.json` (100 input hashes, aggregate `872bec26…`). CORD's
   test split was internally clean, so it was frozen as-is; **9** test inputs leak into train/val —
   Phase 2 drops those *train/val* inputs (never the test anchor). Not read again until Phase 4.
2. **NEXT (a real decision session, not planning): choose the $0/open-source teacher** — an
   open-source model that can do `receipt-v1` extraction and can run at **$0** (locally / free
   compute). Record it as a new decision. **Nothing is chosen yet — do not assume a model.**
3. **Then measure the ceiling at $0:** run that teacher over ~50 inputs from `data/cord/train.jsonl`,
   score with `evaluate(..., scored_fields=dataset.CORD_SCORED_FIELDS)` (D-010), record E-001 + the
   teacher table in `benchmarking.md`. **No `--confirm`, no API spend — the run must cost $0.** The
   paid Claude path in `run_teacher.py` stays dormant until repointed (a later, explicit source change).

## Do NOT

- **Do not spend any money — the project is now $0 (D-013).** No paid teacher calls, no `--confirm`,
  no rented GPU. The old paid-pilot approval protocol is moot because there is no paid pilot.
- **Do not choose the teacher/student model in a planning pass** — that is a separate, explicit
  decision session (D-013 defers it).
- **Never** use `data/cord/test.jsonl` / `data/splits/test.jsonl` for generation/tuning — held out,
  Phase 4 only (`run_teacher.py` already refuses `*test*.jsonl` without `--allow-test`).
- The converter is done, but **do not start the rest of Phase 2** — no teacher labelling, no
  generating the full training set. Do not fine-tune, download the 8B student, start vLLM, or build
  the router/economics (Phases 2–6). Do not begin Phase 2 automatically.
- Treat `data/raw/cord/` as **read-only** input — the converter only reads it (verified sha256
  unchanged this session); never write there.

## Pre-flight for the next session

1. `git log --oneline` → `d07213e feat: freeze CORD test set` on top (D-012 committed). This
   session's **$0-pivot doc edits are uncommitted** — hand the commit to the user (D-005; sandbox
   denies `.git` writes). Suggested message:
   `docs: pivot to $0/open-source strategy; cancel paid teacher (D-013)`.
2. `.venv/bin/python -m pytest` → **42 passed**; lint via `/opt/anaconda3/bin/ruff check .` (the venv
   has no `ruff`/`pytest` console scripts — use `python -m pytest` and the anaconda `ruff` binary).
3. `data/cord/{train,dev,test}.jsonl` is a **gitignored build artifact** — regenerate any time with
   `.venv/bin/python scripts/convert_cord.py` (deterministic, offline, $0; reads `data/raw/cord/` read-only).
   `data/splits/test.jsonl` + `test.manifest.json` likewise rebuild via
   `.venv/bin/python scripts/freeze_test_set.py` (idempotent — aggregate stays `872bec26…`; `--check`
   re-runs the leakage report without writing).
4. Read `PROJECT_STATE.md` + this file + `docs/handoffs/latest.md`, then the Phase 1 doc.
5. **No `.env` / `ANTHROPIC_API_KEY` / agentrouter step** — the paid pilot is cancelled (D-013). The
   next real step is deciding the $0/open-source teacher, not wiring a paid key.
