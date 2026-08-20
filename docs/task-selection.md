# Task Selection

Decision record for **which capability we distill**. This is the highest-leverage choice in the
project: it fixes the dataset, the evaluation metric, and the router's escalation signal.

---

## Decision

**Distill: structured extraction from one document type into a fixed JSON schema.**
Concrete instantiation (locked with a pilot in Phase 1): extract a fixed set of fields from a
short semi-structured business document (e.g. **receipts/invoices**) into the schema in §4.

## Selection method

Candidate tasks scored against the criteria the spec cares about (1 = poor, 5 = excellent):

| Criterion | Structured extraction | SQL (one schema) | PII redaction | Classification | Open-ended chat |
|-----------|:--:|:--:|:--:|:--:|:--:|
| Teacher reliability on the task | 5 | 4 | 4 | 5 | 2 |
| Ease / honesty of evaluation | 5 | 5 | 4 | 5 | 2 |
| Availability of realistic inputs | 5 | 3 | 4 | 4 | 5 |
| Output is structured (router signal) | 5 | 5 | 4 | 3 | 1 |
| Dataset generation cost | 4 | 4 | 4 | 5 | 3 |
| 8B student feasibility | 5 | 4 | 4 | 5 | 2 |
| Serving feasibility | 5 | 5 | 5 | 5 | 4 |
| Business usefulness | 5 | 5 | 5 | 4 | 3 |
| Demonstrates real teacher→student transfer | 5 | 5 | 4 | 3 | 2 |
| **Total** | **44** | **40** | **38** | **39** | **24** |

**Winner: structured extraction.** Runner-up: SQL generation (execution accuracy is the single
cleanest metric, but realistic NL-question inputs and a controlled DB add setup cost, and it
leans on `sqlite`/schema plumbing). Classification is the easiest but the least impressive to
defend as "distillation" (thin output structure). PII redaction is strong and interchangeable
if the chosen extraction dataset disappoints.

## Rejected tasks (and why)

- **Open-ended chat / assistant** — no reliable metric, teacher itself is not a clean ceiling,
  output unstructured → no deterministic router signal. *You'd be creating capability, not
  transferring it.*
- **Broad world-knowledge QA** — the student lacks the teacher's parametric knowledge; you'd be
  measuring memorization, not distillation.
- **Any task where the teacher is only mediocre** — caps the student below usable (the #1
  documented failure mode).
- **Summarization / rewriting** as the *primary* task — would force an LLM judge (fuzzy eval,
  cross-project dependency). Deliberately avoided.

## Why structured extraction is the right call

1. **Honest, deterministic evaluation.** Field-level exact/normalized match → precision/recall/
   **F1**, plus a **schema-validity rate**. No LLM judge, no human-in-the-loop for scoring, so
   quality claims are reproducible and cheap. **This removes the spec's optional Project-4 judge
   dependency entirely.**
2. **Real inputs are abundant and cheap.** Public document/receipt corpora exist; we run the
   teacher over *real* inputs (per the spec) so the training distribution matches serving traffic.
3. **The teacher is genuinely strong here.** Frontier models do schema-constrained extraction
   very reliably → a high, honest ceiling.
4. **An 8B student can realistically learn it.** The task is a bounded input→structured-output
   mapping with strong format regularity; it needs pattern transfer, not broad knowledge —
   exactly what LoRA on a few thousand examples is good at.
5. **The router gets a crisp deterministic signal for free.** `parse_and_validate` either passes
   the Pydantic schema or not → invalid output is an unambiguous "escalate to teacher" trigger.
   No fragile heuristics required for the primary signal.
6. **Clear business value** (invoice/receipt/document processing) → the economics story lands.

## Input / output shapes

**Input:** raw text of one document (for image sources, the OCR'd text layer — the student is a
*text* 8B model, so we linearize to text and keep OCR/vision out of scope).

**Output:** a fixed JSON object validated by `schema.py`. Illustrative (final fields locked in
Phase 1):

```json
{
  "vendor": "ACME Corp",
  "invoice_no": "4471",
  "date": "2026-03-02",
  "currency": "USD",
  "line_items": [{"description": "Widget", "quantity": 2, "unit_price": 12.00}],
  "subtotal": 24.00,
  "tax": 1.92,
  "total": 25.92
}
```

## Evaluation method (defined here, implemented in Phase 1 / used in Phase 4)

- **Primary metric:** micro-averaged **field-level F1** over the schema fields (normalized
  comparison: trim/casefold strings, parse numbers/dates before compare).
- **Schema-validity rate:** % of outputs that parse + validate against `schema.py`.
- **Secondary:** full-record exact-match rate; per-field accuracy (to see which fields are hard).
- **Quality retention** = student_primary_metric ÷ teacher_primary_metric (reported as %).
- **Same evaluator code path for teacher and student** — the comparison is only fair if identical.

### Gold labels & honest ceiling

Two independent quality anchors, kept distinct:
- **Teacher ceiling (Phase 1):** teacher outputs scored against *independent* gold on the frozen
  test set. If the dataset ships human gold (e.g. a receipt corpus with ground-truth parses), use
  it. If not, construct a small **human-verified** gold test set (a few hundred examples) — this
  is the only place we may hand-verify, and it must be built before any tuning.
- **Student (Phase 4):** scored against the *same* frozen gold test set, never the teacher's
  labels for those inputs.

### Leakage prevention
Splitting is by a **hash of the normalized input** so near-duplicate documents cannot straddle
train/test. The **test set is written in Phase 1 and not read again until Phase 4**; scripts that
touch splits refuse to open `test.jsonl` unless invoked with an explicit `--allow-test` flag
(set only by the Phase-4 evaluator).

## Router escalation signal (defined here, built in Phase 5)

- **Primary (deterministic):** student output fails `parse_and_validate` → escalate.
- **Secondary (confidence):** low sequence log-prob / presence of required-field nulls / optional
  self-consistency check → escalate. Kept simple and thresholded; tuned on val, reported on test.

## Open items for Phase 1 (locked via a 50–100 sample pilot)
- Exact dataset + document type; whether human gold exists or must be built.
- Final schema fields + which are required vs optional.
- Teacher model tier (quality vs $ trade-off) for the bulk run.
