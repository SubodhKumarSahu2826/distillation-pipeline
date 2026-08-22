# CURRENT_PHASE.md — Active Phase Pointer

> The one thing to work on now. Update at the end of every session.

## Active phase

**Phase 1 — Task selection + teacher baseline. 🟡 IN PROGRESS.**

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
  `pydantic` promoted to a runtime dep (D-008).
- Tests: `pytest` **42 passed** (3 smoke + 10 schema + 11 evaluate + 18 dataset); `ruff check` clean.

## Next exact action

**The CORD data is converted (D-011) and the test set is frozen (D-012). The ONLY remaining Phase-1
work is the approved paid pilot to measure the teacher ceiling.** No further data-prep is needed.

1. **DONE — frozen test set (D-012).** `scripts/freeze_test_set.py` wrote `data/splits/test.jsonl`
   (100 records) + `data/splits/test.manifest.json` (100 input hashes, aggregate `872bec26…`). CORD's
   test split was internally clean, so it was frozen as-is; **9** test inputs leak into train/val —
   Phase 2 drops those *train/val* inputs (never the test anchor). Not read again until Phase 4.
2. **Cost gate before any spend** (CLAUDE.md §3 / the approval protocol): run the free `count_tokens`
   on real inputs from `data/cord/train.jsonl` → replace the ~700-token estimate → confirm endpoint
   pricing (D-009) → `python scripts/run_teacher.py --input data/cord/train.jsonl --limit 50` (dry
   run) → **present requests / tokens / cost / pilot size and WAIT for approval.**
3. Only after approval: re-run with `--confirm` for Opus 5, then the same for `claude-haiku-4-5`
   (D-007). Score both with `evaluate.py` **using `scored_fields=dataset.CORD_SCORED_FIELDS`** (D-010),
   record E-001 + the teacher table in `benchmarking.md`, and the actual pilot cost in
   `cost-analysis.md` §1b.

## Do NOT

- **Do not make any paid teacher call without the approval protocol** (explain call, #requests,
  tokens, cost, pilot size → wait for explicit approval). Never bulk-call without approval.
- **Never** use `data/cord/test.jsonl` / `data/splits/test.jsonl` for generation/tuning — held out,
  Phase 4 only (`run_teacher.py` already refuses `*test*.jsonl` without `--allow-test`).
- The converter is done, but **do not start the rest of Phase 2** — no teacher labelling, no
  generating the full training set. Do not fine-tune, download the 8B student, start vLLM, or build
  the router/economics (Phases 2–6). Do not begin Phase 2 automatically.
- Treat `data/raw/cord/` as **read-only** input — the converter only reads it (verified sha256
  unchanged this session); never write there.

## Pre-flight for the next session

1. `git log --oneline` → `dd6bcf8` on top (converter committed). **The frozen-test change is
   uncommitted** — `src/distill/dataset.py` + `tests/test_dataset.py` modified, `scripts/freeze_test_set.py`
   new — until the user runs the commit (sandbox denies `.git` writes, D-005). Suggested message:
   `feat(phase-1): freeze CORD test set + input_hash leakage check (D-012)`.
2. `.venv/bin/python -m pytest` → **42 passed**; lint via `/opt/anaconda3/bin/ruff check .` (the venv
   has no `ruff`/`pytest` console scripts — use `python -m pytest` and the anaconda `ruff` binary).
3. `data/cord/{train,dev,test}.jsonl` is a **gitignored build artifact** — regenerate any time with
   `.venv/bin/python scripts/convert_cord.py` (deterministic, offline, $0; reads `data/raw/cord/` read-only).
   `data/splits/test.jsonl` + `test.manifest.json` likewise rebuild via
   `.venv/bin/python scripts/freeze_test_set.py` (idempotent — aggregate stays `872bec26…`; `--check`
   re-runs the leakage report without writing).
4. Read `PROJECT_STATE.md` + this file + `docs/handoffs/latest.md`, then the Phase 1 doc.
5. Create `.env` from `.env.example` with a real `ANTHROPIC_API_KEY` only when running the approved
   pilot; confirm `ANTHROPIC_BASE_URL` (agentrouter) pricing first (D-009).
