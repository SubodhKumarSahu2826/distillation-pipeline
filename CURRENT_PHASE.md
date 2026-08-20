# CURRENT_PHASE.md — Active Phase Pointer

> The one thing to work on now. Update at the end of every session.

## Active phase

**Phase 1 — Task selection + teacher baseline. 🟡 IN PROGRESS.**

Built & verified **offline** this session (no money spent):
- `src/distill/schema.py` — the output contract, `SCHEMA_VERSION = "receipt-v1"`
  (Pydantic v2, `extra="forbid"`, `parse_and_validate` / `is_valid`).
- `src/distill/evaluate.py` — deterministic metrics: micro field-F1, schema-validity rate,
  exact-match, per-field accuracy; order-insensitive line-item matching.
- `src/distill/teacher.py` — prompt `extract-v1`, offline token/cost estimators, and a paid
  `extract()` path (`anthropic` imported lazily; captures usage + cost).
- `scripts/run_teacher.py` — pilot runner, **dry-run by default**; prints requests/tokens/price/
  projected-cost and refuses `*test*.jsonl` without `--allow-test`; needs `--confirm` (+ API key)
  to spend.
- `config.py` teacher defaults set to the Opus 5 ceiling + labelled list prices (D-009);
  `pydantic` promoted to a runtime dep (D-008).
- Tests: `pytest` **20 passed** (3 smoke + 10 schema + 7 evaluate); `ruff check` clean.

## Next exact action

**Acquire the receipts dataset, build the frozen test set, then run the approved paid pilot.**

1. **Get the data** (candidate **CORD**, fallback **SROIE**; D-006). *Blocked in-sandbox* — network
   is limited to `agentrouter.org` + `api.anthropic.com`, so download is a user-run step or needs a
   network allowance. Land raw docs as JSONL (`{"id", "text", ...gold...}`) under `data/raw/`.
2. **Build the frozen test set** — hash-split on normalized input (no near-dup leakage), write
   `data/splits/test.jsonl`. It is **not read again until Phase 4**; the runner already guards it.
3. **Cost gate before any spend** (CLAUDE.md §3 / the verbatim approval protocol):
   run the free `count_tokens` on real pilot inputs → replace the ~700-token estimate → confirm
   endpoint pricing → `python scripts/run_teacher.py --input data/raw/receipts.jsonl --limit 50`
   (dry run) → **present requests / tokens / cost / pilot size and WAIT for explicit approval.**
4. Only after approval: re-run with `--confirm` for Opus 5, then the same for `claude-haiku-4-5`
   (D-007). Score both with `evaluate.py`, record E-001 + the teacher table in `benchmarking.md`,
   and the actual pilot cost in `cost-analysis.md` §1b.

## Do NOT

- **Do not make any paid teacher call without the approval protocol** (explain call, #requests,
  tokens, cost, pilot size → wait for explicit approval). Never bulk-call without approval.
- **Never** use `data/splits/test.jsonl` for generation/tuning — read-only, Phase 4 only.
- Do not generate the full 5k–10k training set, fine-tune, download the 8B student, start vLLM,
  build the router or economics — those are Phases 2–6.
- Do not begin Phase 2 automatically.

## Pre-flight for the next session

1. `git log --oneline` → `069518e` on top; the Phase-1 code below is uncommitted until the user runs
   the commit (sandbox denies `.git` writes, D-005).
2. `.venv/bin/python -m pytest` → 20 passed; lint via `/opt/anaconda3/bin/ruff check .` (the venv has
   no `ruff`/`pytest` console scripts — use `python -m pytest` and the anaconda `ruff` binary).
3. Read `PROJECT_STATE.md` + this file + `docs/handoffs/latest.md`, then the Phase 1 doc.
4. Create `.env` from `.env.example` with a real `ANTHROPIC_API_KEY` only when running the approved
   pilot; confirm `ANTHROPIC_BASE_URL` (agentrouter) pricing first (D-009).
