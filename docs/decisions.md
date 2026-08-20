# Decisions Log (ADR-lite)

Append-only. One entry per meaningful decision. Newest at top. Keep each entry short:
context → decision → why → consequence. Reference by ID (D-00N) from other docs.

---

### D-009 — Teacher pricing is a labelled assumption pending endpoint confirmation
- **Context:** `ANTHROPIC_BASE_URL=https://agentrouter.org/` is a third-party router; real
  per-token pricing there may differ from Anthropic list prices.
- **Decision:** seed `config.py` with **Opus 5 list prices** ($5 in / $25 out per Mtok) as an
  explicit, labelled assumption for cost estimation; before any paid/bulk run, confirm actual
  endpoint pricing **and** run the free `count_tokens` on real inputs to replace the ~4-char/token
  estimate. All prices overridable via env (`TEACHER_INPUT/OUTPUT_USD_PER_MTOK`).
- **Why:** honest cost estimates must not silently hardcode possibly-wrong prices; the money
  guardrails require a real estimate before spend.
- **Consequence:** the dry-run cost plan is labelled an estimate; Phase 6 replaces it with measured
  numbers. (Phase 1, 2026-08-21)

### D-008 — Pydantic promoted to a required runtime dependency
- **Context:** D-004 declared zero required runtime deps for Phase 0. Phase 1's `schema.py` is the
  pipeline-wide output contract, imported by `evaluate`/`teacher`/(later) `router`.
- **Decision:** move `pydantic>=2` from an optional extra into core `dependencies`; drop the
  now-empty `data` extra. `anthropic` stays in the `teacher` extra (lazy-imported).
- **Why:** the schema is core to every phase; keeping it optional would break imports everywhere.
- **Consequence:** `pip install -e .` now installs pydantic; tests still run fully offline
  (`anthropic` imported lazily only on a paid call). Updates D-004's "zero runtime deps."
  (Phase 1, 2026-08-21)

### D-007 — Teacher tiers: Opus 5 ceiling + Haiku 4.5 cost-tier pilot
- **Context:** Phase 1 measures the teacher *ceiling*; Phase 2 must pick the *cheapest* teacher
  that still clears the quality bar for bulk labelling. `task-selection.md` left the bulk tier open.
- **Decision:** measure the ceiling with **claude-opus-5** (config default); in the same pilot,
  also run **claude-haiku-4-5** on the same inputs to see whether a cheaper tier retains enough
  field-F1 to be the bulk-generation teacher. The bulk tier is chosen from pilot numbers, not
  assumed.
- **Why:** separates "best achievable quality" (the honest retention denominator) from "cheapest
  acceptable generator" (drives generation cost + break-even).
- **Consequence:** the pilot runs two small batches; E-001 records both. Bulk tier locked in
  Phase 2 from the A/B. (Phase 1, 2026-08-21)

### D-006 — Document type & dataset for extraction (pilot target, not yet locked)
- **Context:** the task is structured extraction (D-001); we need one concrete document type and a
  corpus with independent gold parses to measure a teacher ceiling and later train the student.
- **Decision:** target **receipts** (short, semi-structured) as the pilot document type; primary
  dataset candidate **CORD** (receipt parsing — line items + OCR text layer + ground-truth JSON,
  permissive license), fallback **SROIE**. Final confirmation is **gated on the Phase-1 pilot**:
  lock it only once the teacher clears the field-F1 bar on real inputs and the dataset's gold maps
  cleanly onto `schema.py` (`receipt-v1`).
- **Why:** receipts have strong format regularity, real public corpora with ground-truth, and fit
  an 8B student; keeps eval deterministic against *independent* gold (not teacher self-labels).
- **Consequence:** schema is `receipt-v1` (no `invoice_no`; line items carry description / quantity
  / unit_price / total_price). Dataset acquisition + gold verification is the next action. **The
  sandbox network is limited to `agentrouter.org` + `api.anthropic.com`, so the dataset cannot be
  downloaded in-sandbox** — acquisition is a user-run step or needs a network allowance.
  (Phase 1, 2026-08-21)

### D-005 — Sandbox blocks `.git` writes in the workspace
- **Context:** Phase 0 must `git init` + commit here (D-002), but the execution sandbox denies
  creating a `.git` directory anywhere in the workspace tree (normal dirs, and `.git` under
  `$TMPDIR`, are writable; `<repo>/.git` is not). The sandbox cannot be disabled.
- **Decision:** run every other Phase 0 step in-sandbox; the `git init` + initial commit is run by
  the user in a normal terminal (exact commands provided), or after the sandbox is adjusted to
  allow `.git` in this project.
- **Why:** can't fight the sandbox; a git dir under `$TMPDIR`/an alternate allow-listed path would
  be non-durable and non-standard — not a real repo.
- **Consequence:** Phase 0 code/tests/lint are complete and verified; the git-commit acceptance
  criterion is pending one user-run command. (Phase 0, 2026-08-20)

### D-004 — Phase 0 carries zero required runtime dependencies
- **Context:** the phase-0 doc's example listed `python-dotenv`, but no Phase 0 code reads `.env`
  (secrets are first consumed by the teacher client in Phase 1).
- **Decision:** Phase 0 declares **no** required runtime deps; config uses the stdlib only. Heavy,
  phase-specific deps live in optional extras (`teacher`/`data`/`train`/`serve`); dev tooling
  (`ruff`, `pytest`) is the only non-extra tooling. `.env` loading arrives in Phase 1.
- **Why:** "every dependency must have a concrete purpose right now"; keeps the install fast and the
  smoke test fully offline.
- **Consequence:** `pip install -e .` installs nothing heavy; `.env.example` ships now, `.env`
  wiring lands with the teacher client. (Phase 0, 2026-08-20)

### D-003 — Deterministic evaluation; no LLM judge
- **Context:** the spec allows an LLM judge (from Project 4) for open-ended outputs.
- **Decision:** choose a task with deterministic metrics (field-F1 + schema validity); do **not**
  use an LLM judge.
- **Why:** reproducible, cheap, honest scoring; removes a cross-project dependency and a source of
  eval noise.
- **Consequence:** evaluation is pure code; no Project-4 coupling. *(Planning)*

### D-002 — Project location & isolation
- **Context:** workspace holds several independent projects, one git repo each.
- **Decision:** project lives at `AI Projects/distillation-pipeline/` with its own git repo.
- **Why:** matches the user's convention; keeps history and state self-contained.
- **Consequence:** `git init` happens in Phase 0. *(Planning)*

### D-001 — Task = structured extraction (document → fixed JSON)
- **Context:** must pick one narrow task the teacher already does well (see `task-selection.md`).
- **Decision:** structured extraction into a fixed JSON schema.
- **Why:** honest deterministic eval, abundant real inputs, reliable teacher, 8B-feasible, and a
  free deterministic router signal (schema validation).
- **Consequence:** schema is the central contract; drives Phases 1–6. *(Planning)*

---
_Template for new entries:_
```
### D-00N — <title>
- **Context:** …
- **Decision:** …
- **Why:** …
- **Consequence:** … (<phase/date>)
```
