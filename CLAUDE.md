# CLAUDE.md — Operating Manual for This Repository

> **Read this file first, every session.** It is the entry point. It tells you how to
> resume work, where state lives, what the rules are, and what you must never do by accident.
> This project is built across many Claude Code sessions. **The repository is the memory.**
> Never rely on remembering a previous chat.

---

## 1. What this project is

**Fine-Tuning Model Distillation Pipeline.** We distill one narrow capability from a
frontier **teacher** (Claude API) into a self-hosted **~8B student** (LoRA/QLoRA), then
prove — with measured evidence — whether owning the model beats renting it.

- **Task being distilled:** structured extraction — one document type → a fixed JSON schema.
  (Rationale + schema: `docs/task-selection.md`.)
- **The headline deliverable is a number**, not a model: the **break-even requests/day**
  above which the self-hosted student is cheaper than the teacher API, fallback-adjusted.
- **Definition of done (from the spec):** a 3-axis benchmark table (quality / cost / latency),
  a stated break-even request volume, and a served vLLM endpoint with a working escalation
  path back to the teacher.

Full plan: `docs/project-plan.md`. Architecture: `docs/architecture.md`.

---

## 2. Session protocol (FOLLOW EXACTLY)

### Start of every session
1. Read `CLAUDE.md` (this file).
2. Read `PROJECT_STATE.md` — what is done, what artifacts exist.
3. Read `CURRENT_PHASE.md` — the single active phase and the exact next action.
4. Read `docs/handoffs/latest.md` — the last session's handoff.
5. Run `git status` and `git log --oneline -10`.
6. Open **only** the phase doc for the current phase (`docs/phases/phase-N-*.md`) and the
   specific source files it names. Do **not** load the whole codebase.
7. Restate the exact unfinished task in one sentence, then continue from there.

### End of every session
1. Run the relevant tests (`pytest -q`) and record pass/fail.
2. Update `PROJECT_STATE.md` (phase table, artifacts index).
3. Update `CURRENT_PHASE.md` (active phase + next exact action).
4. Overwrite `docs/handoffs/latest.md` with a fresh handoff (template inside it).
5. Append any decisions to `docs/decisions.md`, experiments to `docs/experiments.md`.
6. Commit with a small, meaningful message (see §7).
7. State the next exact action so the next session starts in one step.

---

## 3. Hard guardrails — money & compute

This project spends real money on **teacher API calls** and **GPU rental**. Treat both as
dangerous. **Always pilot before scaling.**

- **Never launch a bulk teacher-labelling run** (thousands of calls) without: (a) a 50–100
  sample pilot, (b) a written cost estimate in `docs/cost-analysis.md`, (c) explicit user
  approval of that estimate.
- **Never start full training** without a short smoke run (a few steps / tiny subset) that
  proves the loop works end-to-end and fits in GPU memory.
- **Never start a full concurrency benchmark** without a small warm-up benchmark first.
- **Never call a paid API or rent a GPU during a *planning* session.**
- Every script that spends money must support `--dry-run` and `--limit N`, and must print an
  estimated cost and require a confirmation flag before the full run.
- Do not download model weights until the phase that needs them (Phase 3 / Phase 5).
- Secrets (`ANTHROPIC_API_KEY`, `WANDB_API_KEY`, `HF_TOKEN`) come from `.env` / environment.
  Never hardcode or commit them. `.env` is gitignored.

---

## 4. Complexity policy (enforced in review)

Write code that reads like a competent engineer wrote it under time pressure — plain and
direct. Before adding any abstraction, answer in one sentence: **what concrete problem does
this solve right now?** If there is no good answer, do not add it.

- Prefer plain functions. Use a class only when it owns state + behavior (e.g. a client, the
  router). No inheritance unless it removes real duplication.
- No factories, no generic "manager/handler/wrapper" layers, no plugin systems, no config
  frameworks, no premature microservices.
- One utility per job; don't create a second helper that does 90% of an existing one.
- Config lives in one typed place (`config.py` / `.yaml`), not scattered constants.
- Keep source files focused; split a module when it exceeds ~300–400 lines *and* has two jobs.
  Don't shatter code into dozens of 10-line files.

See `docs/architecture.md` §Complexity for the full rules.

---

## 5. Context-window discipline

Keep sessions cheap and continuable:
- **Datasets, model weights, raw logs, and large model outputs never go into context.**
  They live under `data/`, `models/`, `runs/`, `artifacts/` — all gitignored — and are
  referenced by path + summary statistics only.
- Experiment results are summarized as small tables/JSON in `docs/experiments.md` and
  `docs/benchmarking.md`; the raw run stays in W&B and `runs/`.
- When you inspect a dataset, print counts/schema/a few samples — never dump the file.
- Each phase names the exact files it touches (see its phase doc). Stay within that set.

---

## 6. Repository map (where things will live)

```
distillation-pipeline/
├── CLAUDE.md              # this file — always read first
├── PROJECT_STATE.md       # status ledger
├── CURRENT_PHASE.md       # active phase + next action
├── README.md              # (Phase 7) public writeup w/ MEASURED results
├── pyproject.toml         # (Phase 0) deps + tooling
├── .env.example           # (Phase 0) required env vars
├── src/distill/           # all importable code (single package)
│   ├── config.py          # typed config (paths, models, pricing knobs)
│   ├── schema.py          # Pydantic output schema (the contract)
│   ├── teacher.py         # Claude client + labelling
│   ├── dataset.py         # validate / filter / dedup / split
│   ├── train.py           # LoRA/QLoRA fine-tuning
│   ├── evaluate.py        # metrics + quality retention
│   ├── serve.py           # vLLM launch + FastAPI router
│   ├── router.py          # student→validate→escalate logic
│   ├── economics.py       # cost model + break-even
│   └── bench.py           # latency/throughput/cost harness
├── scripts/               # thin CLI entrypoints calling src/distill
├── tests/                 # pytest; fast, no network/GPU by default
├── configs/               # experiment configs (yaml)
├── data/                  # (gitignored) inputs, teacher labels, splits
├── models/                # (gitignored) adapters/checkpoints
├── runs/ , artifacts/     # (gitignored) logs, benchmark outputs
└── docs/                  # all planning + results docs (see below)
```

`docs/`: `project-plan.md`, `architecture.md`, `task-selection.md`, `decisions.md`,
`experiments.md`, `benchmarking.md`, `cost-analysis.md`, `phases/phase-0..7-*.md`,
`handoffs/latest.md`.

> Only `docs/`, the three control files, and (later) `src/`, `tests/`, `configs/`, `scripts/`
> are committed. `data/`, `models/`, `runs/`, `artifacts/`, `.env`, `venv/` are gitignored.

---

## 7. Git strategy

Small, meaningful commits. One logical change each. Suggested arc:

```
chore: initialize project (Phase 0)
feat: add output schema and teacher baseline (Phase 1)
feat: add teacher dataset generation + validation (Phase 2)
feat: add LoRA/QLoRA training (Phase 3)
feat: add teacher-vs-student benchmark (Phase 4)
feat: add vLLM serving + fallback router (Phase 5)
feat: add break-even economics (Phase 6)
docs: final results, README, reproducibility (Phase 7)
```

Commit at the end of each session even mid-phase (`wip:` prefix is fine). Never one giant commit.

---

## 8. Phase gate

Work **one phase at a time**, in order. Do not start a phase until the user says
"Start Phase N". Do not do work that belongs to a later phase. Each phase doc lists an
explicit **"What must NOT be done in this phase"** section — respect it.

Current phase is always in `CURRENT_PHASE.md`.
