# Handoff — latest

> Overwrite this file at the end of every session. It is the first thing the next session reads
> after the three control files. Keep it concrete: what changed, what's next, how to verify.

---

## Session date
2026-08-22 — **Phase 1 — IN PROGRESS.** **$0 strategy-pivot / planning-doc realignment session.**
The user cancelled the paid Anthropic/Claude teacher plan: **the entire project must now cost $0.**
No code, data, models, or APIs were touched — **docs only**, offline, **$0 spent**.

## What happened this session
Recorded a new hard constraint and realigned the planning/state docs to it. **No teacher/student
model was chosen; no economics were re-derived; no source or architecture was changed** (all
deliberately deferred).
- **New anchor decision `D-013`** in `docs/decisions.md`: $0 hard constraint; paid Claude teacher
  **cancelled**; pivot to an open-source/free ($0) strategy (TBD). It **supersedes D-007** (Opus 5 /
  Haiku 4.5 tiers) **and D-009** (paid pricing), and qualifies D-006's Anthropic-network note. D-007
  and D-009 headers now carry a `⚠️ SUPERSEDED by D-013` flag.
- **Control files** (`PROJECT_STATE.md`, `CURRENT_PHASE.md`): status/next-action now reflect $0. The
  next action is no longer a paid pilot — it is to **decide the $0/open-source teacher, then measure
  the ceiling at $0**. Removed the `.env`/`ANTHROPIC_API_KEY`/agentrouter/`count_tokens` pre-flight.
- **Paid figures neutralized as clearly-marked $0 placeholders** in `docs/cost-analysis.md` (§1a
  ~$0.55 Opus/Haiku pilot), `docs/experiments.md` (E-001 A/B), `docs/project-plan.md` (the
  "Spends money?" column + break-even framing), `docs/task-selection.md` (open teacher-tier line),
  and phase docs `phase-1`, `phase-2`, `phase-6` (banners).
- **Corrected stale state:** the D-012 frozen-test work is in fact **committed** at `d07213e` (the
  prior docs still said "uncommitted at `dd6bcf8`").

## Verification results
- **No source changed:** edits are confined to `*.md` (docs + 3 control files). `src/`, `tests/`,
  `scripts/`, `configs/`, `config.py` untouched — verify with `git diff --stat` (all `.md`).
- Tests/lint not re-run (no code changed); last known green: `pytest` **42 passed**, `ruff` clean.
- `git status` before this session: clean tree except untracked `.claude/`. HEAD `d07213e`.

## State of the repo
- 🟡 Phase 1 in progress. HEAD `d07213e`. **This session's doc edits are UNCOMMITTED** — hand the
  commit to the user (D-005; sandbox denies `.git` writes). Suggested message:
  `docs: pivot to $0/open-source strategy; cancel paid teacher (D-013)`.
- **Offline assets unchanged and still valid:** `receipt-v1` schema, evaluator, CORD converter
  (D-011), frozen test set (D-012, `data/splits/test.jsonl` = 100, aggregate `872bec26…`).
- **$0 spent; the project is now bound to stay at $0.** The ~$0.55 Opus 5 pilot will never run.

## Exact next action
1. **Decide the $0/open-source teacher (a real decision session, not a planning pass):** pick an
   open-source model that can perform `receipt-v1` extraction and can be run at **$0** (locally or on
   free compute); record it as a new decision (supersedes the model half of D-006/D-007). **Do not
   assume a model in planning.**
2. **Measure the ceiling at $0:** run that teacher over ~50 inputs from `data/cord/train.jsonl`, score
   with `evaluate(..., scored_fields=dataset.CORD_SCORED_FIELDS)` (D-010), record E-001 + the teacher
   table in `benchmarking.md`. **No `--confirm`, no API spend.** Repointing `run_teacher.py` off the
   dormant paid Claude path is a later, explicit **source** change — out of scope for a planning pass.

## Watch-outs handed forward
- **$0 is now a hard constraint (D-013)** — no paid teacher, no `--confirm`, no rented GPU, at any
  phase. Every later "Spends money?" assumption in the older docs is void unless it can be done free.
- **Models are NOT chosen** — teacher and student are both open TBD; don't infer one from old docs.
- **Every git commit is user-run** (D-005). Venv has no `ruff`/`pytest` console scripts — use
  `.venv/bin/python -m pytest` and the anaconda `ruff` at `/opt/anaconda3/bin/ruff`.
- **Do not mutate the frozen test set** (D-012); never read `data/splits/test.jsonl` /
  `data/cord/test.jsonl` until Phase 4. **`data/raw/cord/` is read-only.**
- **The teacher client's paid `extract()` path is dormant, not deleted** — left untouched this pass.
- **Do not start Phase 2+** (bulk generation / training / serving / economics).
