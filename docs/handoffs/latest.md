# Handoff — latest

> Overwrite this file at the end of every session. It is the first thing the next session reads
> after the three control files. Keep it concrete: what changed, what's next, how to verify.

---

## Session date
2026-08-22 — **Phase 1 (Task selection + teacher baseline) — IN PROGRESS.** Recovery + verification
session. The prior session built the **frozen test set (D-012)** but died on a Claude Desktop
API/streaming error before updating the control docs. This session verified the on-disk state and
brought the docs back in sync. Offline, **$0 spent**, no API call.

## What happened this session
No code was written or changed — this was a state-recovery pass. Findings:
- The **CORD converter (D-011) is now committed** at `dd6bcf8` (`feat(phase-1): add deterministic
  CORD converter`) — the docs previously said it was uncommitted at `b5f8052`; that was stale.
- The **uncommitted** working tree is now the **frozen-test-set** work from the prior session:
  `src/distill/dataset.py` + `tests/test_dataset.py` modified, `scripts/freeze_test_set.py` new.
- Verified the frozen artifact and recorded the leakage finding as **D-012** (it was not yet in
  `docs/decisions.md`). Updated `PROJECT_STATE.md`, `CURRENT_PHASE.md`, and this handoff.

## Verification results (all green)
- `git status`: 2 modified (`dataset.py`, `test_dataset.py`) + 1 untracked (`scripts/freeze_test_set.py`).
- **Frozen test set exists:** `data/splits/test.jsonl` = **100** records; `data/splits/test.manifest.json`
  = **100** unique input hashes + aggregate `872bec26…`, `schema_version=receipt-v1`,
  recipe `sha256(casefold(collapse_whitespace(text)))`.
- **Leakage (`freeze_test_set.py --check`):** test internally clean (100 unique, 0 dup, 0 empty);
  **test ∩ train = 8, test ∩ dev = 2 → 9 distinct** test inputs leak into train/val. Also surfaced
  32 intra-train + 1 intra-dev duplicates and 12 train∩dev overlaps (all deferred to Phase-2 dedup).
- `.venv/bin/python -m pytest` → **42 passed** (was 40; +2 `input_hash` tests). `ruff check .` → clean.
- **Raw CORD unchanged:** 2004 files, tree sha256 `433be823fd026f8f…` = the D-011 baseline `433be82…`;
  nothing under `data/raw/cord/` modified after the freeze (mtimes all predate it).

## State of the repo
- 🟡 Phase 1 in progress. HEAD `dd6bcf8`. Frozen-test code **UNCOMMITTED** — hand the commit to the
  user (D-005; sandbox denies `.git` writes). Suggested message:
  `feat(phase-1): freeze CORD test set + input_hash leakage check (D-012)`.
- **Data:** `data/cord/{train,dev,test}.jsonl` = 1000 records (D-011, gitignored, rebuildable).
  `data/splits/test.jsonl` (100) + `test.manifest.json` = the frozen anchor (D-012, gitignored,
  rebuildable via `scripts/freeze_test_set.py`, idempotent).
- **$0 spent.** Pilot still **estimated** ~$0.55 (50 × Opus 5, labelled assumption), not yet run.

## Exact next action
Phase-1 data prep is **complete** (D-011 + D-012). The only remaining Phase-1 work is the **approved
paid pilot** to measure the teacher ceiling:
1. **Cost gate first** (CLAUDE.md §3): free `count_tokens` on real inputs from `data/cord/train.jsonl`
   → replace the ~700-token estimate → confirm endpoint pricing (D-009) → dry-run
   `python scripts/run_teacher.py --input data/cord/train.jsonl --limit 50` →
   **present requests / tokens / cost / pilot size and WAIT for explicit approval.**
2. After approval: `--confirm` pilot for Opus 5, then Haiku 4.5 (D-007); **score with
   `evaluate(..., scored_fields=dataset.CORD_SCORED_FIELDS)`** (D-010); record E-001 +
   `benchmarking.md` teacher table + actual cost in `cost-analysis.md` §1b.

## How the next session verifies it's on track
- `.venv/bin/python -m pytest` → **42 passed**; `/opt/anaconda3/bin/ruff check .` clean.
- `.venv/bin/python scripts/freeze_test_set.py --check` reprints the split summary + leakage
  (test: 100 / 100 unique / 0 dup / 0 empty; 9 test inputs in train/val).
- `data/splits/test.jsonl` has 100 lines; `test.manifest.json` aggregate is `872bec26…`.

## Watch-outs handed forward
- **Every git commit is user-run** (D-005). Venv has **no `ruff`/`pytest` console scripts** — use
  `.venv/bin/python -m pytest` and the anaconda `ruff` at `/opt/anaconda3/bin/ruff`.
- **Do not mutate or re-shuffle the frozen test set** — it is the measurement anchor (D-012). Leakage
  is fixed on the **train/val** side in Phase 2 (drop any train/val input whose `input_hash` is in
  `test.manifest.json`), never by touching `data/splits/test.jsonl`.
- **Never read `data/splits/test.jsonl` / `data/cord/test.jsonl`** until Phase 4; `run_teacher.py`
  refuses `*test*.jsonl` without `--allow-test`.
- **`data/raw/cord/` is read-only input** — verified sha256 `433be82…` unchanged.
- **Use `scored_fields=CORD_SCORED_FIELDS` for every CORD score** (D-010) or vendor/date/currency get
  silently penalized.
- **Pricing is a labelled assumption** (D-009) — confirm on the endpoint + run free `count_tokens`
  before spend. The pilot is the **first money step**: pilot 50, get explicit approval on the estimate.
- **Do not start the rest of Phase 2** (teacher labelling / full training set) or any later phase.
