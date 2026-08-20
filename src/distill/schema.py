"""The extraction contract: a receipt document → this fixed JSON object.

This is the single most important interface in the project. The teacher must emit it,
the student is trained to emit it, and ``parse_and_validate`` is the deterministic
router signal in Phase 5 (valid → keep; invalid → escalate). Keep it small and stable:
changing a field here ripples through every later phase.

Design choices (locked in Phase 1, see docs/task-selection.md):
- Every top-level key is *present* in a valid object (fixed shape) but most values are
  nullable, because real receipts legitimately omit tax, a subtotal, or a clear date.
- Money is a plain ``float``; the evaluator compares amounts at 2-decimal tolerance.
  We do not enforce arithmetic consistency (subtotal + tax == total) — receipts round
  and the teacher should report what is printed, not "fix" it.
- ``vendor`` and ``total`` are the anchor fields we care most about; per-field accuracy
  in evaluate.py shows which fields are actually hard.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field

# Bump when the *meaning* of the schema changes so old labels can be distinguished.
SCHEMA_VERSION = "receipt-v1"


class LineItem(BaseModel):
    """One purchased line on the receipt."""

    model_config = ConfigDict(extra="forbid")

    description: str
    quantity: float | None = None
    unit_price: float | None = None
    total_price: float | None = None


class Receipt(BaseModel):
    """A single receipt parsed into a fixed set of fields.

    ``extra="forbid"`` makes the shape strict: an output with hallucinated extra keys
    is *invalid*, which is exactly the signal the router wants.
    """

    model_config = ConfigDict(extra="forbid")

    vendor: str | None = None
    date: str | None = None  # normalized to ISO 8601 (YYYY-MM-DD) by the extractor/eval
    currency: str | None = None  # ISO 4217, uppercase (e.g. "USD")
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None


# The JSON Schema of the contract, handy for the teacher's structured-output constraint
# and for documentation. Computed once.
RECEIPT_JSON_SCHEMA: dict = Receipt.model_json_schema()


def _strip_code_fence(text: str) -> str:
    """Return the JSON body of ``text``, tolerating a ```json ... ``` markdown fence.

    Models sometimes wrap JSON in a fenced block despite instructions. We do the minimal
    unwrapping — find the outermost ``{...}`` — rather than a full markdown parse.
    """
    s = text.strip()
    if s.startswith("```"):
        # Drop the first fence line (``` or ```json) and any trailing fence.
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.rstrip().endswith("```"):
            s = s.rstrip()[: -len("```")]
        s = s.strip()
    # Fall back to the outermost brace span if there is leading/trailing prose.
    if not s.startswith("{"):
        start, end = s.find("{"), s.rfind("}")
        if start != -1 and end != -1 and end > start:
            s = s[start : end + 1]
    return s


class SchemaError(ValueError):
    """Raised when text cannot be parsed/validated into a ``Receipt``."""


def parse_and_validate(text: str) -> Receipt:
    """Parse model output ``text`` into a validated ``Receipt`` or raise ``SchemaError``.

    This is the deterministic gate used everywhere: pass == schema-valid.
    """
    body = _strip_code_fence(text)
    try:
        obj = json.loads(body)
    except json.JSONDecodeError as e:
        raise SchemaError(f"not valid JSON: {e}") from e
    try:
        return Receipt.model_validate(obj)
    except Exception as e:  # pydantic.ValidationError and friends
        raise SchemaError(f"does not match schema: {e}") from e


def is_valid(text: str) -> bool:
    """True iff ``text`` parses and validates against the schema. Never raises."""
    try:
        parse_and_validate(text)
        return True
    except SchemaError:
        return False
