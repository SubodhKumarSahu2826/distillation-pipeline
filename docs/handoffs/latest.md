# Handoff — latest

> Overwrite this file at the end of every session. It is the first thing the next session reads
> after the three control files. Keep it concrete: what changed, what's next, how to verify.

---

## Session date
2026-08-21 — **Phase 1 (Task selection + teacher baseline) — IN PROGRESS** (non-paid work done)

## What happened this session
Recovered state from the repo and did the **non-paid** Phase-1 work — the schema, the deterministic
evaluator, the teacher client, and the money gate — all built and verified offline. No dataset was
downloaded and **no paid API call was made**.

- **Confirmed the task** (D-006): structured extraction from **receipts**; dataset candidate
  **CORD** (fallback **SROIE**) — *final only after the pilot clears the field-F1 bar*.
- **Locked the schema** as `receipt-v1` in `src/distill/schema.py` (Pydantic v2, `extra="forbid"`;
  `vendor/date/currency`, `line_items[description,quantity,unit_price,total_price]`,
  `subtotal/tax/total`; all optional/nullable except the always-present `line_items`). Reconciled
  `task-selection.md` to match (dropped `invoice_no`, added line-item `total_price`).
- **Deterministic metrics** in `src/distill/evaluate.py`: micro field-F1 (primary), schema-validity
  rate, exact-match, per-field accuracy; normalized compare (trim/casefold/round/ISO-date);
  order-insensitive line-item matching. **No LLM judge** (D-003).
- **Teacher client** `src/distill/teacher.py`: prompt `extract-v1` (JSON-only, fixed keys, ISO date,
  ISO-4217 currency, report-don't-compute), offline token/cost estimators, and a paid `extract()`
  (`anthropic` lazy-imported; captures input/output tokens + cost).
- **Money gate** `scripts/run_teacher.py`: **dry-run by default** — prints endpoint/model/requests/
  tokens/price/projected-cost and exits without spending; `--confirm` (+ `ANTHROPIC_API_KEY`)
  required to spend; refuses `*test*.jsonl` without `--allow-test`.
- **Config/deps:** teacher default = `claude-opus-5` with **labelled** list prices $5/$25 per Mtok
  (D-009); `pydantic>=2` promoted to a required runtime dep, `data` extra removed (D-008).
- Recorded **D-006..D-009**; updated E-001 (Opus vs Haiku A/B); added the pilot cost estimate to
  `cost-analysis.md` §1a.

## State of the repo
- 🟡 Phase 1 in progress. `pytest` → **20 passed** (3 smoke + 10 schema + 7 evaluate);
  `ruff check .` → clean.
- Last commit `069518e`; **all Phase-1 code + doc edits are uncommitted** (sandbox denies `.git`
  writes, D-005 — hand the commit to the user; command in the "Exact next action" chat message).
- **$0 spent.** Pilot **estimated** ~$0.55 (50 × Opus 5, labelled assumption), not yet run.

## Exact next action
1. **Acquire the receipts dataset** (CORD/SROIE) into `data/raw/*.jsonl` (`{"id","text",...gold...}`).
   *Can't be done in-sandbox* — network is limited to `agentrouter.org` + `api.anthropic.com`.
2. **Build the frozen test set** `data/splits/test.jsonl` (hash-split, no near-dup leakage);
   do not read it again until Phase 4.
3. **Before any paid call**, follow the approval protocol: run free `count_tokens` on real inputs →
   confirm endpoint pricing → dry-run `run_teacher.py --input … --limit 50` → **present requests/
   tokens/cost/pilot-size and wait for explicit approval.**
4. After approval: `--confirm` pilot for Opus 5, then Haiku 4.5; score with `evaluate.py`; record
   E-001 + `benchmarking.md` teacher table + actual cost in `cost-analysis.md` §1b.

## How the next session verifies it's on track
- `.venv/bin/python -m pytest` → 20 passed; `/opt/anaconda3/bin/ruff check .` clean.
- `python scripts/run_teacher.py --limit 50` prints a plan and "DRY RUN — no API calls made".
- `PROJECT_STATE.md` shows Phase 1 🟡; `schema.py`/`evaluate.py`/`teacher.py`/`run_teacher.py` exist.

## Watch-outs handed forward
- **Every git commit is user-run** (D-005). The venv has **no `ruff`/`pytest` console scripts** —
  use `.venv/bin/python -m pytest` and the anaconda `ruff` binary at `/opt/anaconda3/bin/ruff`.
- **Dataset download is blocked in-sandbox** (network allow-list). This gates the whole pilot.
- **Pricing is a labelled assumption** (D-009) — confirm on the agentrouter endpoint before spend;
  the `count_tokens` call is free and should replace the ~700-token/req heuristic first.
- The pilot is the **first money-spending step**: pilot 50 before any bulk run; get explicit
  approval on the printed estimate.
