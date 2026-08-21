# Handoff — latest

> Overwrite this file at the end of every session. It is the first thing the next session reads
> after the three control files. Keep it concrete: what changed, what's next, how to verify.

---

## Session date
2026-08-21 — **Phase 1 (Task selection + teacher baseline) — IN PROGRESS.** Built the deterministic
**CORD→`receipt-v1` converter** (D-011), pulled forward from Phase 2 at the user's request. Offline,
$0 spent, no API call, no dataset download (raw CORD was already on disk).

## What happened this session
Inspected the real raw corpus at `data/raw/cord/{train,dev,test}/json/*.json` (800/100/100 files) and
found the docs' assumption was **wrong**: CORD ships **no `gt_parse` dict**. Ground truth lives as
word-level spans in a `valid_line` list — `{"words":[{"text","quad"}], "category":"menu.nm"|…,
"group_id":N}` — so both the model input text and the gold must be built *from* `valid_line`. Recorded
this as **D-011** and built a small deterministic converter accordingly.

Implementation (minimal, plain functions, no new deps):
- **`src/distill/dataset.py`** — added the converter alongside the existing D-010 policy constants:
  - `convert_record(doc, id) → {id, text, gold}`.
  - `build_gold` — groups primary `menu.*` spans by `group_id` into line items
    (`nm`→description, `cnt`→quantity, `unitprice`→unit_price, `price`→total_price; `menu.sub*` and
    minor categories dropped; name-less groups skipped since `description` is required),
    `sub_total.subtotal_price`→subtotal, `sub_total.tax_price`→tax, `total.total_price`→total;
    `vendor/date/currency` left `null` (D-010). Every gold is `Receipt.model_validate`-d by construction.
  - `build_text` — reconstructs OCR text from word `quad` boxes (sort top→bottom then left→right; new
    line when the vertical gap exceeds ~0.6× median word height).
  - `parse_amount` — takes the **last** pure-numeric, non-percentage word (skips labels with stray
    digits like `PB1` and rate spans like `10.00 %`), normalizes mixed thousands/decimal separators.
- **`scripts/convert_cord.py`** — NEW thin CLI mirroring `run_teacher.py`'s style: reads the raw json,
  writes `data/cord/{train,dev,test}.jsonl`, prints per-split record / line-item / no-item / fail counts.
- **`tests/test_dataset.py`** — kept the 2 policy tests; added 12 `parse_amount` parametrized cases
  (comma/dot thousands, US/EU mixed, decimals, rate-skipping, label-with-digit) + a synthetic-CORD
  `convert_record` test (field mapping, name-less group dropped, rate not taken as tax, gold validates)
  + a no-line-items `build_gold` test. All use inline synthetic dicts — no real data files.
- **`schema.py` / `evaluate.py` unchanged.**

## State of the repo
- 🟡 Phase 1 in progress. `pytest` → **40 passed** (was 26; +14 dataset); `ruff check` → clean.
- **This session's change is UNCOMMITTED** — `src/distill/dataset.py` + `tests/test_dataset.py`
  modified, `scripts/convert_cord.py` new. HEAD is `b5f8052` (policy committed at `a185e5e`). Hand the
  commit to the user (sandbox denies `.git` writes, D-005). Suggested message:
  `feat(phase-1): add deterministic CORD→receipt-v1 converter (D-011)`.
- **Data:** `data/cord/{train,dev,test}.jsonl` = 800/100/100 = **1000** records, all schema-valid; 0
  empty texts; 5 receipts with no line items (genuine — no `menu.nm`). `data/` is gitignored → this is
  a rebuildable artifact (`.venv/bin/python scripts/convert_cord.py`), not committed.
- **Raw CORD verified unmodified** — sha256 over the whole `data/raw/cord` tree identical before and
  after the run (`433be82…`, 2004 files).
- **$0 spent.** Pilot still **estimated** ~$0.55 (50 × Opus 5, labelled assumption), not yet run.

## Exact next action
1. **Build the frozen test set.** `data/cord/test.jsonl` (100 held-out CORD test records) already
   exists; decide whether to freeze it as-is or apply a hash-split / near-dup check, then finalize
   `data/splits/test.jsonl`. Do not read it again until Phase 4 (`run_teacher.py` guards `*test*.jsonl`).
2. **Before any paid call**, follow the approval protocol: the converter output is already a valid
   pilot input (`run_teacher.py` reads `{id, text}`, ignores `gold`). Free `count_tokens` on real
   inputs from `data/cord/train.jsonl` → confirm endpoint pricing → dry-run
   `run_teacher.py --input data/cord/train.jsonl --limit 50` → **present requests/tokens/cost/pilot-size
   and wait for explicit approval.**
3. After approval: `--confirm` pilot for Opus 5, then Haiku 4.5 (D-007); **score with
   `evaluate(..., scored_fields=dataset.CORD_SCORED_FIELDS)`** (D-010); record E-001 +
   `benchmarking.md` teacher table + actual cost in `cost-analysis.md` §1b.

## How the next session verifies it's on track
- `.venv/bin/python -m pytest` → **40 passed**; `/opt/anaconda3/bin/ruff check .` clean.
- `.venv/bin/python scripts/convert_cord.py` reprints `train: 800 …`, `dev: 100 …`, `test: 100 …`
  with 0 FAILED.
- `python -c "from distill.dataset import convert_record"` imports cleanly; every line of
  `data/cord/*.jsonl` re-validates as a `Receipt`.

## Watch-outs handed forward
- **Every git commit is user-run** (D-005). Venv has **no `ruff`/`pytest` console scripts** — use
  `.venv/bin/python -m pytest` and the anaconda `ruff` at `/opt/anaconda3/bin/ruff`.
- **`data/raw/cord/` is read-only input** — never write there; the converter only reads it.
- **Use `scored_fields=CORD_SCORED_FIELDS` for every CORD score** — a bare `evaluate(...)` would
  silently penalize vendor/date/currency and understate both the ceiling and retention.
- **Known ~1% parse noise** (a few double-tax receipts, space-split thousands) is accepted, not
  special-cased (D-011) — revisit only if it moves the teacher/student numbers materially.
- **Pricing is a labelled assumption** (D-009) — confirm on the endpoint + run free `count_tokens`
  before spend. The pilot is the **first money step**: pilot 50, get explicit approval on the estimate.
- **Do not start the rest of Phase 2** (teacher labelling / full training set) or any later phase.
