"""Dataset-specific facts that the general code (schema, evaluate, teacher) stays free of.

Two jobs live here, both CORD-specific:
1. the **scored-field policy** — which ``receipt-v1`` fields CORD actually labels (D-010);
2. the **CORD → internal record converter** — turn each raw CORD json into an
   ``{id, text, gold}`` record the pipeline can use (input text + gold ``receipt-v1`` object).

CORD ground-truth structure (as it really is on disk)
-----------------------------------------------------
We use the **original** CORD corpus (``clovaai/cord``), not the Hugging Face ``cord-v2``
variant. Each ``json/receipt_NNNNN.json`` has a ``valid_line`` list; there is **no**
pre-parsed ``gt_parse`` dict. Every ``valid_line`` entry is a labelled span:
``{"words": [{"text", "quad", ...}], "category": "menu.nm" | ..., "group_id": N}``. So both
the OCR text (word ``text`` + bounding-box ``quad``) and the gold labels (``category``) live
in ``valid_line`` together — we reconstruct each separately (see ``build_text`` / ``build_gold``).

Field mapping (only the categories that map to receipt-v1 are used):
  - line items — one per ``menu`` ``group_id``: ``menu.nm`` → ``description``,
    ``menu.cnt`` → ``quantity``, ``menu.unitprice`` → ``unit_price``,
    ``menu.price`` → ``total_price``;
  - ``sub_total.subtotal_price`` → ``subtotal``; ``sub_total.tax_price`` → ``tax``;
  - ``total.total_price`` → ``total``.
CORD has **no** ground truth for the merchant name, the purchase date, or the currency, so
``vendor``/``date``/``currency`` are left ``null``. Sub-item tags (``menu.sub_*``) and the many
minor categories (``menu.num``/``discountprice``, ``sub_total.service_price``, the ``total.*``
payment breakdown, ``void_menu.*``, …) have no slot in the flat ``receipt-v1`` shape and are
intentionally dropped.

CORD scoring decision (docs/decisions.md D-010)
------------------------------------------------
Our ``receipt-v1`` schema still asks the model for ``vendor``/``date``/``currency`` — they
are real, useful fields and the output must remain a valid full-schema object — but *scoring*
the model on fields CORD never labels would be dishonest in both directions: a correct vendor
extraction would count as a false positive against an empty gold, and a correct value could
never be credited. So on CORD we score **only the fields CORD labels**; vendor/date/currency
are excluded from the headline metric. Schema-validity is unaffected — it always checks the
full ``receipt-v1`` contract.
"""

from __future__ import annotations

import hashlib
import re
import statistics

from .schema import Receipt

# The only fields scored against CORD gold — the fields CORD provides ground truth for.
CORD_SCORED_FIELDS: frozenset[str] = frozenset({"subtotal", "tax", "total", "line_items"})

# Excluded from CORD scoring: CORD has no ground truth for these (see the module docstring).
# The model is still asked to extract them; we simply do not score their values on CORD.
CORD_UNSCORED_FIELDS: frozenset[str] = frozenset({"vendor", "date", "currency"})


# --- input hashing (leakage-safe splitting / dedup) ------------------------------

_WHITESPACE = re.compile(r"\s+")


def input_hash(text: str) -> str:
    """Stable content hash of a record's **input text**, for leakage and dedup checks.

    Normalizes away cosmetic OCR-text differences — surrounding space, internal
    whitespace runs, and case — so that byte-for-byte or near-identical receipts collide,
    then hashes with SHA-256. Two records sharing an ``input_hash`` share an input and must
    never straddle the train/val/test boundary. Used to freeze the test set (record its
    input hashes) and, in Phase 2, to drop any train/val input that collides with it.
    """
    normalized = _WHITESPACE.sub(" ", text.strip()).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()



# --- CORD → receipt-v1 conversion ------------------------------------------------

# A word that is *only* an optional sign, digits, and thousands/decimal separators.
_PURE_NUMBER = re.compile(r"[-+]?\d[\d.,]*$")


def parse_amount(words: list[str]) -> float | None:
    """Return the monetary amount spelled out in ``words`` as a float, or ``None``.

    CORD amount spans interleave a label, an optional percentage rate, and the value, e.g.
    ``["TAX", "10.00", "%", "4,964"]`` or ``["Grand", "Total", "1,591,600"]``. We take the
    **last** word that is purely numeric and is **not** a percentage rate (a rate ends with
    ``%`` or is immediately followed by a ``%`` word), which skips both labels like ``PB1``
    (not pure-numeric) and the ``10.00 %`` rate. CORD writes numbers with either separator as
    thousands (``1,346,000``, ``23.000``) and occasionally both (US ``45,000.00`` /
    EU ``9.500,00``); we normalize to a plain float. A single separator with 1–2 trailing
    digits is a decimal, otherwise it is a thousands separator.
    """
    tok: str | None = None
    for i, w in enumerate(words):
        s = w.strip()
        nxt = words[i + 1].strip() if i + 1 < len(words) else ""
        if s.endswith("%") or nxt == "%":
            continue  # a rate (e.g. "10%" / "10.00 %"), not the amount
        if _PURE_NUMBER.match(s):
            tok = s  # keep the last pure-numeric, non-rate word
    if tok is None:
        return None
    if "," in tok and "." in tok:
        dec = "," if tok.rfind(",") > tok.rfind(".") else "."  # last separator is the decimal
        tok = tok.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif "," in tok or "." in tok:
        sep = "," if "," in tok else "."
        head, _, tail = tok.rpartition(sep)
        if tok.count(sep) == 1 and len(tail) in (1, 2):
            tok = f"{head}.{tail}"  # single separator, 1–2 trailing digits → decimal point
        else:
            tok = tok.replace(sep, "")  # otherwise a thousands separator
    try:
        return round(float(tok), 2)
    except ValueError:
        return None


def _words_where(entries: list[dict], category: str) -> list[str]:
    """All word texts tagged ``category`` across ``entries`` (a valid_line or one group)."""
    return [w["text"] for e in entries if e["category"] == category for w in e["words"]]


def _line_items(valid_line: list[dict]) -> list[dict]:
    """Build one line item per primary ``menu`` group_id.

    Sub-items (``menu.sub_*``) and minor menu categories are dropped (no receipt-v1 slot).
    A group without a ``menu.nm`` is skipped — the schema requires a ``description``.
    """
    groups: dict[object, list[dict]] = {}
    for e in valid_line:
        c = e["category"]
        if c.startswith("menu.") and not c.startswith("menu.sub"):
            groups.setdefault(e["group_id"], []).append(e)
    items = []
    for gid in sorted(groups, key=repr):
        g = groups[gid]
        name = " ".join(_words_where(g, "menu.nm")).strip()
        if not name:
            continue
        items.append({
            "description": name,
            "quantity": parse_amount(_words_where(g, "menu.cnt")),
            "unit_price": parse_amount(_words_where(g, "menu.unitprice")),
            "total_price": parse_amount(_words_where(g, "menu.price")),
        })
    return items


def build_gold(doc: dict) -> dict:
    """Gold ``receipt-v1`` object for one CORD json dict, validated against the schema."""
    vl = doc["valid_line"]
    gold = {
        "vendor": None,
        "date": None,
        "currency": None,
        "line_items": _line_items(vl),
        "subtotal": parse_amount(_words_where(vl, "sub_total.subtotal_price")),
        "tax": parse_amount(_words_where(vl, "sub_total.tax_price")),
        "total": parse_amount(_words_where(vl, "total.total_price")),
    }
    return Receipt.model_validate(gold).model_dump()  # canonical form; raises on a bad mapping


def build_text(doc: dict) -> str:
    """Reconstruct the receipt's OCR text (the model input) from word bounding boxes.

    ``valid_line`` is not stored in reading order, so we sort every word top-to-bottom then
    left-to-right and start a new line when the vertical gap exceeds ~0.6× the median word
    height. The result is a plain-text receipt: the teacher/student never sees the image.
    """
    words = []
    for e in doc["valid_line"]:
        for w in e["words"]:
            q = w["quad"]
            ys = (q["y1"], q["y2"], q["y3"], q["y4"])
            xs = (q["x1"], q["x2"], q["x3"], q["x4"])
            words.append((sum(ys) / 4.0, min(xs), max(ys) - min(ys), w["text"]))
    if not words:
        return ""
    words.sort(key=lambda t: (t[0], t[1]))
    tol = 0.6 * statistics.median(h for _, _, h, _ in words)
    lines, row, row_y = [], [], None
    for ymid, x, _h, text in words:
        if row_y is None or ymid - row_y <= tol:
            row.append((x, text))
            row_y = ymid if row_y is None else row_y
        else:
            lines.append(" ".join(t for _, t in sorted(row)))
            row, row_y = [(x, text)], ymid
    if row:
        lines.append(" ".join(t for _, t in sorted(row)))
    return "\n".join(lines)


def convert_record(doc: dict, rec_id: str) -> dict:
    """Convert one CORD json dict into an internal ``{id, text, gold}`` record."""
    return {"id": rec_id, "text": build_text(doc), "gold": build_gold(doc)}
