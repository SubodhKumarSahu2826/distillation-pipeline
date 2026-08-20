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
- `src/distill/dataset.py` — **NEW**: `CORD_SCORED_FIELDS = {subtotal, tax, total, line_items}`
  and `CORD_UNSCORED_FIELDS = {vendor, date, currency}` (D-010). No converter yet.
- `src/distill/teacher.py` — prompt `extract-v1`, offline token/cost estimators, and a paid
  `extract()` path (`anthropic` imported lazily; captures usage + cost).
- `scripts/run_teacher.py` — pilot runner, **dry-run by default**; prints requests/tokens/price/
  projected-cost and refuses `*test*.jsonl` without `--allow-test`; needs `--confirm` (+ API key)
  to spend.
- `config.py` teacher defaults set to the Opus 5 ceiling + labelled list prices (D-009);
  `pydantic` promoted to a runtime dep (D-008).
- Tests: `pytest` **26 passed** (3 smoke + 10 schema + 11 evaluate + 2 dataset); `ruff check` clean.

## Next exact action

**Acquire the CORD dataset (user-run), build the frozen test set, then run the approved paid pilot.**
The CORD **scoring policy is resolved** (D-010) — no more eval-policy work is needed before acquisition.

1. **Get the data** — use the **original CORD** (`clovaai/cord`), *not* `cord-v2` (D-006, D-010).
   *Blocked in-sandbox* — network is limited to `agentrouter.org` + `api.anthropic.com`, so download
   is a **user-run step**. Land the raw parquet/JSON under `data/raw/cord/` (train/validation/test).
   The Phase-2 converter (not yet written) maps CORD `gt_parse` → `receipt-v1`
   (`menu`→line_items, `sub_total`→subtotal/tax, `total`→total; vendor/date/currency left null).
2. **Build the frozen test set** — hash-split on normalized input (no near-dup leakage), write
   `data/splits/test.jsonl`. It is **not read again until Phase 4**; the runner already guards it.
3. **Cost gate before any spend** (CLAUDE.md §3 / the verbatim approval protocol):
   run the free `count_tokens` on real pilot inputs → replace the ~700-token estimate → confirm
   endpoint pricing → `python scripts/run_teacher.py --input data/raw/cord/receipts.jsonl --limit 50`
   (dry run) → **present requests / tokens / cost / pilot size and WAIT for explicit approval.**
4. Only after approval: re-run with `--confirm` for Opus 5, then the same for `claude-haiku-4-5`
   (D-007). Score both with `evaluate.py` **using `scored_fields=dataset.CORD_SCORED_FIELDS`** (D-010),
   record E-001 + the teacher table in `benchmarking.md`, and the actual pilot cost in
   `cost-analysis.md` §1b.

## Do NOT

- **Do not make any paid teacher call without the approval protocol** (explain call, #requests,
  tokens, cost, pilot size → wait for explicit approval). Never bulk-call without approval.
- **Never** use `data/splits/test.jsonl` for generation/tuning — read-only, Phase 4 only.
- **Do not write the CORD→`receipt-v1` converter yet** — it needs the real data files and belongs in
  Phase 2 (`src/distill/dataset.py`). This session only fixed the scoring *policy*.
- Do not generate the full 5k–10k training set, fine-tune, download the 8B student, start vLLM,
  build the router or economics — those are Phases 2–6.
- Do not begin Phase 2 automatically.

## Pre-flight for the next session

1. `git log --oneline` → `71e14d9` (Phase-1 code) on top; **this session's scored-field-policy change
   (`evaluate.py`, `dataset.py`, tests, docs) is uncommitted** until the user runs the commit (sandbox
   denies `.git` writes, D-005).
2. `.venv/bin/python -m pytest` → **26 passed**; lint via `/opt/anaconda3/bin/ruff check .` (the venv
   has no `ruff`/`pytest` console scripts — use `python -m pytest` and the anaconda `ruff` binary).
3. Read `PROJECT_STATE.md` + this file + `docs/handoffs/latest.md`, then the Phase 1 doc.
4. Create `.env` from `.env.example` with a real `ANTHROPIC_API_KEY` only when running the approved
   pilot; confirm `ANTHROPIC_BASE_URL` (agentrouter) pricing first (D-009).
