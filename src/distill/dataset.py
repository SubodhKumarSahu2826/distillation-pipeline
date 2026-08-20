"""Dataset-specific facts that the general code (schema, evaluate, teacher) stays free of.

Today this holds only the **scored-field policy** per source dataset: which ``receipt-v1``
fields that dataset actually provides independent ground truth for. The evaluator is
dataset-agnostic — it takes an allow-list (``evaluate(..., scored_fields=...)``) — and the
allow-list lives here. (The CORD → ``receipt-v1`` converter will also live in this module
in Phase 2; it is deliberately **not** written yet — we have not acquired the data.)

CORD scoring decision (docs/decisions.md D-010)
------------------------------------------------
We use the **original** CORD corpus (``clovaai/cord``), not the Hugging Face ``cord-v2``
variant. CORD ships ground-truth parses for:
  - line items — ``menu``: name → ``description``, ``cnt`` → ``quantity``,
    ``unitprice`` → ``unit_price``, ``price`` → ``total_price``;
  - the ``sub_total`` block — ``subtotal_price`` → ``subtotal``, ``tax_price`` → ``tax``;
  - the ``total`` block — ``total_price`` → ``total``.
It has **no** ground-truth field for the merchant name, the purchase date, or the currency.

Our ``receipt-v1`` schema still asks the model for ``vendor``/``date``/``currency`` — they
are real, useful fields and the output must remain a valid full-schema object — but *scoring*
the model on fields CORD never labels would be dishonest in both directions: a correct vendor
extraction would count as a false positive against an empty gold, and a correct value could
never be credited. So on CORD we score **only the fields CORD labels**; vendor/date/currency
are excluded from the headline metric. Schema-validity is unaffected — it always checks the
full ``receipt-v1`` contract.
"""

from __future__ import annotations

# The only fields scored against CORD gold — the fields CORD provides ground truth for.
CORD_SCORED_FIELDS: frozenset[str] = frozenset({"subtotal", "tax", "total", "line_items"})

# Excluded from CORD scoring: CORD has no ground truth for these (see the module docstring).
# The model is still asked to extract them; we simply do not score their values on CORD.
CORD_UNSCORED_FIELDS: frozenset[str] = frozenset({"vendor", "date", "currency"})
