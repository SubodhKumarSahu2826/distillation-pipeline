# CURRENT_PHASE.md — Active Phase Pointer

> The one thing to work on now. Update at the end of every session.

## Active phase

**Phase 1 — Task selection + teacher baseline. 🟡 IN PROGRESS.**

Built & verified **offline** this session (no money spent):
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
- `scripts/convert_cord.py` — **NEW** thin CLI: `data/raw/cord/*/json/*.json` → `data/cord/{train,dev,
  test}.jsonl` (offline, $0). Produced **1000** schema-valid records (800/100/100); 5 receipts legitimately
  have no line items; raw CORD verified unmodified (sha256 identical before/after).
- `src/distill/teacher.py` — prompt `extract-v1`, offline token/cost estimators, and a paid
  `extract()` path (`anthropic` imported lazily; captures usage + cost).
- `scripts/run_teacher.py` — pilot runner, **dry-run by default**; prints requests/tokens/price/
  projected-cost and refuses `*test*.jsonl` without `--allow-test`; needs `--confirm` (+ API key)
  to spend. It reads exactly the `{id, text}` records the converter emits.
- `config.py` teacher defaults set to the Opus 5 ceiling + labelled list prices (D-009);
  `pydantic` promoted to a runtime dep (D-008).
- Tests: `pytest` **40 passed** (3 smoke + 10 schema + 11 evaluate + 16 dataset); `ruff check` clean.

## Next exact action

**The CORD data is acquired and converted (D-011). Next: build the frozen test set, then run the
approved paid pilot.** No further data-prep or eval-policy work is needed first.

1. **Build the frozen test set.** The converter already wrote `data/cord/test.jsonl` (CORD's own
   100 held-out test records, `{id, text, gold}`). Decide whether to freeze that split as-is or apply
   a hash-split / near-dup check across splits, then finalize `data/splits/test.jsonl`. It is **not
   read again until Phase 4**; `run_teacher.py` already refuses `*test*.jsonl` without `--allow-test`.
2. **Cost gate before any spend** (CLAUDE.md §3 / the approval protocol): the converter's output is
   already a valid pilot input (`run_teacher.py` reads the `{id, text}` fields, ignores `gold`). Run
   the free `count_tokens` on real inputs from `data/cord/train.jsonl` → replace the ~700-token
   estimate → confirm endpoint pricing → `python scripts/run_teacher.py --input data/cord/train.jsonl
   --limit 50` (dry run) → **present requests / tokens / cost / pilot size and WAIT for approval.**
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

1. `git log --oneline` → `b5f8052` on top (scored-field policy committed at `a185e5e`); **this
   session's converter change is uncommitted** — `src/distill/dataset.py` + `tests/test_dataset.py`
   modified, `scripts/convert_cord.py` new — until the user runs the commit (sandbox denies `.git`
   writes, D-005). Suggested message: `feat(phase-1): add deterministic CORD→receipt-v1 converter (D-011)`.
2. `.venv/bin/python -m pytest` → **40 passed**; lint via `/opt/anaconda3/bin/ruff check .` (the venv
   has no `ruff`/`pytest` console scripts — use `python -m pytest` and the anaconda `ruff` binary).
3. `data/cord/{train,dev,test}.jsonl` is a **gitignored build artifact** — regenerate any time with
   `.venv/bin/python scripts/convert_cord.py` (deterministic, offline, $0; reads `data/raw/cord/` read-only).
4. Read `PROJECT_STATE.md` + this file + `docs/handoffs/latest.md`, then the Phase 1 doc.
5. Create `.env` from `.env.example` with a real `ANTHROPIC_API_KEY` only when running the approved
   pilot; confirm `ANTHROPIC_BASE_URL` (agentrouter) pricing first (D-009).
