# Architecture

How the system is decomposed, why each piece exists, the technology choices (with explicit
exclusions), the repository layout, and the code-complexity rules the implementation must obey.

---

## 1. Data flow

```
                          ┌─────────────── build time (offline) ───────────────┐
 real document inputs ──▶ Teacher (Claude API) ──▶ teacher outputs ──▶ Validation/Filter
                                                                            │
                                     (schema-invalid or dup → dropped)      ▼
                                                                    Training dataset
                                                                    (train/val/test split)
                                                                            │
                                                                            ▼
                                                       Student fine-tuning (LoRA/QLoRA)
                                                                            │
                                                                            ▼
                                                                     Student adapter
                                                                            │
                    ┌──────────────── evaluation & benchmark (offline) ─────┘
                    ▼
        Evaluate on FROZEN test set  ──▶  3-axis benchmark (quality/cost/latency)
                                                                            │
                          ┌─────────────── serve time (online) ────────────┘
                          ▼
                 vLLM server (student)
                          ▲
   request ──▶ Router ────┘──▶ student output ──▶ validate (schema) + confidence
                 │                                          │
                 │                          valid & confident ──▶ return
                 └───────────────── invalid / low-confidence ──▶ escalate to Teacher ──▶ return
```

Two worlds: **offline** (label → train → evaluate) and **online** (serve → route → maybe
escalate). The schema (`src/distill/schema.py`) is the contract shared by both.

## 2. Components

Each has: responsibility · inputs · outputs · dependencies · why it exists · required/optional.

### 2.1 Output schema — `schema.py` **[required]**
- **Responsibility:** define the fixed JSON structure the teacher must emit and the student must
  learn; provide `parse_and_validate(text) -> (obj|None, error)`.
- **In:** raw model text. **Out:** validated typed object or a validation error.
- **Deps:** Pydantic.
- **Why:** it is the single contract used for teacher labelling, dataset filtering, evaluation,
  and the router's deterministic escalation signal. Everything else depends on it.

### 2.2 Teacher client — `teacher.py` **[required]**
- **Responsibility:** call Claude on an input, return parsed output; batch with rate-limit +
  retry; **track token usage & cost per call.**
- **In:** document text (+ prompt template). **Out:** validated object + usage record.
- **Deps:** Anthropic SDK, `schema.py`, `config.py`.
- **Why:** the teacher is both the quality ceiling (Phase 1) and the label source (Phase 2).
  Cost tracking here feeds the economics.

### 2.3 Dataset builder — `dataset.py` **[required]**
- **Responsibility:** validate teacher outputs against schema, **drop failures**, deduplicate
  near-identical inputs, and split into train/val/test with **leakage-safe hashing**.
- **In:** raw (input, teacher-output) pairs. **Out:** `data/splits/{train,val,test}.jsonl` +
  filtering stats.
- **Deps:** `schema.py`. **Why:** "don't teach the student the teacher's mistakes"; guarantees
  the test set is uncontaminated.

### 2.4 Trainer — `train.py` **[required]**
- **Responsibility:** LoRA/QLoRA SFT of the 8B student on train split; validate each epoch; log
  to W&B; save adapter.
- **In:** train/val JSONL, a run config (`configs/*.yaml`). **Out:** adapter in `models/…`,
  W&B run, metrics.
- **Deps:** Transformers, PEFT, TRL, bitsandbytes, W&B. **Why:** produces the student.

### 2.5 Evaluator — `evaluate.py` **[required]**
- **Responsibility:** compute task metrics (field-F1, schema-validity, exact-match) for any model
  (teacher or student) on a split; compute **quality retention**.
- **In:** predictions + gold (or reference) on a split. **Out:** metrics JSON → `benchmarking.md`.
- **Deps:** `schema.py`. **Why:** one metric definition used identically for teacher and student —
  the comparison is only honest if it's the same code.

### 2.6 Benchmark harness — `bench.py` **[required]**
- **Responsibility:** measure latency (p50/p95), throughput, error rate under comparable
  concurrency for teacher and student; write raw results to `artifacts/`.
- **In:** a request workload (from test set). **Out:** timing/throughput JSON.
- **Deps:** the serving endpoint, teacher client. **Why:** the cost & latency axes need measured,
  not assumed, numbers.

### 2.7 vLLM server — `serve.py` **[required]**
- **Responsibility:** launch vLLM (OpenAI-compatible) serving the student + adapter, with
  continuous batching / paged attention; health check.
- **In:** model + adapter path, config. **Out:** an HTTP endpoint. **Deps:** vLLM. **Why:** the
  spec requires a real served endpoint and realistic throughput.

### 2.8 Router — `router.py` **[required]**
- **Responsibility:** the online path — call student, `parse_and_validate`, check a confidence
  signal; **escalate to teacher on invalid/low-confidence**; record escalation rate.
- **In:** a request. **Out:** final validated response + which model served it.
- **Deps:** `serve` endpoint, `teacher.py`, `schema.py`. **Why:** the escalation path is a
  definition-of-done item and the thing that makes economics honest (fallback-adjusted).

### 2.9 Economics — `economics.py` **[required]**
- **Responsibility:** cost model → teacher $/1k, student $/1k (GPU-hour ÷ measured throughput,
  incl. idle), fallback-adjusted blended cost, and **break-even req/day**; savings curve.
- **In:** measured throughput/latency (Phase 4), pricing knobs (`config.py`), escalation rate
  (Phase 5). **Out:** `docs/cost-analysis.md` tables + a plot in `artifacts/`.
- **Deps:** none heavy. **Why:** the headline artifact.

### 2.10 Config — `config.py` **[required]**
- **Responsibility:** one typed place for paths, model IDs, pricing knobs, defaults.
- **Why:** avoid scattered magic constants; make cost knobs explicit and reviewable.

### 2.11 CLI entrypoints — `scripts/` **[required, thin]**
- **Responsibility:** argparse wrappers (`--dry-run`, `--limit`, confirm flags) that call into
  `src/distill`. No business logic here. **Why:** money-guardrails + reproducible commands.

**Optional / deferred:** a Dockerfile for the serving env (repro on rented GPU) — Phase 5/7
only if time permits. Nothing else.

## 3. Technology decisions

For each: why · problem solved · could we skip it · worth the complexity.

| Tech | Why / problem solved | Skip? | Verdict |
|------|----------------------|-------|---------|
| **Python** | ecosystem for ML + serving | no | ✅ core |
| **PyTorch** | training backend for HF/PEFT | no | ✅ core |
| **HF Transformers** | load 8B model, tokenizer, Trainer | no | ✅ core |
| **PEFT (LoRA)** | parameter-efficient tuning; small adapters | could full-FT but needs huge GPU/$ | ✅ core |
| **QLoRA (bitsandbytes 4-bit)** | fit 8B tuning on one 24GB GPU → cheap | skip if you rent a 40–80GB GPU | ✅ default, keep A100 path as fallback |
| **TRL (SFTTrainer)** | removes SFT boilerplate (packing, masking) | could hand-write a loop | ✅ worth it; thin usage |
| **Weights & Biases** | loss/LR/val curves, sample outputs, run compare | could log CSV | ✅ real value for the 2-config comparison |
| **vLLM** | continuous batching + paged attention = real throughput | spec-required; HF generate too slow | ✅ core |
| **FastAPI** | tiny HTTP layer for the router | could use vLLM's server alone, but router needs custom logic | ✅ minimal |
| **Pydantic** | the schema contract + validation = router signal | could hand-validate; error-prone | ✅ core |
| **HF datasets** | load/stream inputs, manage splits | plain files possible | ✅ convenient, low cost |
| **pytest** | fast unit tests for schema/dataset/router/economics | no | ✅ core |

### Explicitly evaluated and **excluded** (not for résumé keywords)

| Tech | Verdict | Reason |
|------|---------|--------|
| LangChain / LangGraph | ❌ exclude | No multi-step agent/graph here; a client + a router `if` is clearer and debuggable. |
| Redis | ❌ exclude | No shared cache/queue need at this scale; adds an ops dependency. |
| Celery | ❌ exclude | Batch labelling is a script with concurrency, not a distributed task queue. |
| Kafka | ❌ exclude | No streaming ingestion; wildly over-scaled. |
| PostgreSQL | ❌ exclude | Outputs are JSONL files; a DB earns nothing here. |
| Vector DB | ❌ exclude | No retrieval/similarity search in the task. |
| Kubernetes | ❌ exclude | One model, one GPU, one endpoint; a process (or one container) suffices. |
| MLflow | ❌ exclude | W&B already covers tracking; two trackers is redundant. |
| Airflow | ❌ exclude | Phases are run by hand/CLI; no recurring DAG to schedule. |
| Docker | 🟡 optional | Only as a single serving image for reproducibility (Phase 5/7), never required to run locally. |

## 4. Repository structure (and why each dir exists)

```
distillation-pipeline/
├── src/distill/     # all importable logic in ONE package (imports stay clean, tests target it)
├── scripts/         # thin CLIs w/ money-guardrails (separate so logic stays import-safe)
├── tests/           # fast unit tests, no network/GPU by default (keeps CI-lite quick)
├── configs/         # yaml experiment configs (diffable, reproducible runs)
├── data/            # gitignored: inputs, teacher labels, splits (never in context)
├── models/          # gitignored: adapters/checkpoints (large binaries)
├── runs/ artifacts/ # gitignored: logs, benchmark/plot outputs (large, regenerable)
└── docs/            # committed: plan, decisions, results, phases, handoffs (the memory)
```

No directory exists without a job. We do **not** pre-create `api/`, `services/`, `core/`,
`utils/` scaffolding — modules are added under `src/distill/` when a phase needs them.

## 5. Complexity rules (enforced at review)

Every abstraction must answer **"what concrete problem does this solve now?"** If not, delete it.

- Functions by default; a class only for genuine state+behavior (`TeacherClient`, `Router`).
- No inheritance unless it removes real duplication; no ABCs "for the future".
- No factories, generic wrappers, "manager/handler" layers, config frameworks, or plugin systems.
- One helper per job; no near-duplicate utilities.
- Config centralized in `config.py`; no magic numbers sprinkled around (esp. pricing).
- Split a file only when it passes ~300–400 lines **and** owns two responsibilities; otherwise
  keep it together. Don't create dozens of 10-line files.
- Prefer boring, debuggable control flow (the router is a small deterministic function, not a
  framework).
