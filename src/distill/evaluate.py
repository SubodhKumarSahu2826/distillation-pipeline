"""Deterministic scoring for the extraction task — no LLM judge (see docs/decisions.md D-003).

The same code scores the teacher (Phase 1 ceiling) and the student (Phase 4), so the
comparison is fair by construction. Everything here is pure and reproducible.

Metrics produced by :func:`evaluate`:
- ``field_f1`` — micro-averaged precision/recall/F1 over every leaf field slot
  (the six scalar fields plus each line-item's fields). This is the **primary** metric.
- ``schema_validity`` — fraction of raw outputs that parse + validate.
- ``exact_match`` — fraction of records that match gold on every normalized field.
- ``per_field_accuracy`` — accuracy per scalar field (+ ``line_items`` as a block),
  to show which fields are hard.

Scoring model for a field "slot": a slot exists when gold and/or prediction has a
non-null value for that field. Both present and equal → TP; both present but unequal →
FP **and** FN; only gold → FN; only prediction → FP. An unparseable prediction
contributes no values (so it is pure FN against gold — invalid output hurts recall,
which is the honest treatment). Line items are aligned order-insensitively by
normalized description before their sub-fields are scored.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .schema import LineItem, Receipt, parse_and_validate

SCALAR_FIELDS = ("vendor", "date", "currency", "subtotal", "tax", "total")
ITEM_FIELDS = ("description", "quantity", "unit_price", "total_price")

_DATE_FORMATS = (
    "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d.%m.%Y",
    "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
    "%m/%d/%y", "%d/%m/%y",
)


# --- normalization ---------------------------------------------------------------

def _norm_str(x: object) -> str | None:
    if x is None:
        return None
    s = str(x).strip().casefold()
    return s or None


def _norm_num(x: object) -> float | None:
    if x is None:
        return None
    try:
        return round(float(x), 2)
    except (TypeError, ValueError):
        return None


def _norm_date(x: object) -> str | None:
    """Return an ISO ``YYYY-MM-DD`` string when parseable, else the casefolded text."""
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s.casefold()


def _norm_scalar(field: str, value: object) -> object | None:
    if field == "date":
        return _norm_date(value)
    if field in ("subtotal", "tax", "total"):
        return _norm_num(value)
    return _norm_str(value)  # vendor, currency


def _norm_item(item: LineItem) -> tuple:
    return (
        _norm_str(item.description),
        _norm_num(item.quantity),
        _norm_num(item.unit_price),
        _norm_num(item.total_price),
    )


def canonical(r: Receipt | None) -> dict:
    """Normalized, comparison-ready view of a record. ``None`` → empty record."""
    if r is None:
        return {**{f: None for f in SCALAR_FIELDS}, "line_items": []}
    out = {f: _norm_scalar(f, getattr(r, f)) for f in SCALAR_FIELDS}
    out["line_items"] = sorted((_norm_item(it) for it in r.line_items), key=lambda t: repr(t))
    return out


# --- counts ----------------------------------------------------------------------

@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    def add(self, other: "Counts") -> None:
        self.tp += other.tp
        self.fp += other.fp
        self.fn += other.fn

    def _slot(self, gold: object, pred: object) -> None:
        """Score one field slot given normalized gold/pred values (None == absent)."""
        if gold is None and pred is None:
            return
        if gold is not None and pred is not None:
            if gold == pred:
                self.tp += 1
            else:
                self.fp += 1
                self.fn += 1
        elif gold is not None:
            self.fn += 1
        else:
            self.fp += 1

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 0.0

    @property
    def f1(self) -> float:
        if self.tp + self.fp + self.fn == 0:
            return 1.0  # nothing expected and nothing wrongly produced
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    def as_dict(self) -> dict:
        return {
            "tp": self.tp, "fp": self.fp, "fn": self.fn,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
        }


def _align_items(
    gold: list[tuple], pred: list[tuple]
) -> tuple[list[tuple[tuple, tuple]], list[tuple], list[tuple]]:
    """Greedy order-insensitive alignment by normalized description.

    Returns (matched_pairs, unmatched_gold, unmatched_pred). Deterministic: both sides
    are processed in sorted order and matched on description equality.
    """
    buckets: dict[object, list[tuple]] = {}
    for g in sorted(gold, key=lambda t: repr(t)):
        buckets.setdefault(g[0], []).append(g)
    matched: list[tuple[tuple, tuple]] = []
    unmatched_pred: list[tuple] = []
    for p in sorted(pred, key=lambda t: repr(t)):
        bucket = buckets.get(p[0])
        if bucket:
            matched.append((bucket.pop(0), p))
        else:
            unmatched_pred.append(p)
    unmatched_gold = [g for rest in buckets.values() for g in rest]
    return matched, unmatched_gold, unmatched_pred


def score_pair(pred: Receipt | None, gold: Receipt) -> Counts:
    """Field-slot counts for one (prediction, gold) pair."""
    c = Counts()
    g, p = canonical(gold), canonical(pred)
    for f in SCALAR_FIELDS:
        c._slot(g[f], p[f])

    matched, un_g, un_p = _align_items(g["line_items"], p["line_items"])
    for gi, pi in matched:
        # description matched by construction → TP; score the remaining sub-fields.
        c.tp += 1
        for k in range(1, len(ITEM_FIELDS)):
            c._slot(gi[k], pi[k])
    for gi in un_g:  # missed items: every non-null sub-field is a FN
        for k in range(len(ITEM_FIELDS)):
            if gi[k] is not None:
                c.fn += 1
    for pi in un_p:  # spurious items: every non-null sub-field is a FP
        for k in range(len(ITEM_FIELDS)):
            if pi[k] is not None:
                c.fp += 1
    return c


# --- top-level report ------------------------------------------------------------

@dataclass
class Report:
    n: int
    field_f1: dict
    schema_validity: float
    exact_match: float
    per_field_accuracy: dict

    def as_dict(self) -> dict:
        return {
            "n": self.n,
            "field_f1": self.field_f1,
            "schema_validity": round(self.schema_validity, 4),
            "exact_match": round(self.exact_match, 4),
            "per_field_accuracy": {k: round(v, 4) for k, v in self.per_field_accuracy.items()},
        }


def parse_predictions(texts: list[str]) -> list[Receipt | None]:
    """Parse raw model outputs; unparseable/invalid → ``None`` (counts against recall)."""
    out: list[Receipt | None] = []
    for t in texts:
        try:
            out.append(parse_and_validate(t))
        except Exception:
            out.append(None)
    return out


def schema_validity_rate(texts: list[str]) -> float:
    if not texts:
        return 0.0
    valid = sum(1 for r in parse_predictions(texts) if r is not None)
    return valid / len(texts)


def _per_field_accuracy(preds: list[Receipt | None], golds: list[Receipt]) -> dict:
    acc = {f: 0 for f in SCALAR_FIELDS}
    acc["line_items"] = 0
    for pred, gold in zip(preds, golds):
        g, p = canonical(gold), canonical(pred)
        for f in SCALAR_FIELDS:
            if g[f] == p[f]:
                acc[f] += 1
        if g["line_items"] == p["line_items"]:
            acc["line_items"] += 1
    n = len(golds) or 1
    return {k: v / n for k, v in acc.items()}


def evaluate(pred_texts: list[str], golds: list[Receipt]) -> Report:
    """Full deterministic report for raw predictions ``pred_texts`` vs ``golds``.

    ``pred_texts`` and ``golds`` are aligned by index. Gold records are assumed valid.
    """
    if len(pred_texts) != len(golds):
        raise ValueError(f"length mismatch: {len(pred_texts)} preds vs {len(golds)} golds")
    preds = parse_predictions(pred_texts)

    micro = Counts()
    for pred, gold in zip(preds, golds):
        micro.add(score_pair(pred, gold))

    exact = 0
    for pred, gold in zip(preds, golds):
        if canonical(pred) == canonical(gold):
            exact += 1
    n = len(golds)

    return Report(
        n=n,
        field_f1=micro.as_dict(),
        schema_validity=(sum(1 for p in preds if p is not None) / n) if n else 0.0,
        exact_match=(exact / n) if n else 0.0,
        per_field_accuracy=_per_field_accuracy(preds, golds),
    )
