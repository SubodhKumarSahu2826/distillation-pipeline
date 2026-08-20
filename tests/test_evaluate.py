"""Metric tests: exact values on tiny hand-built cases (Phase 1 acceptance)."""

import pytest

from distill.dataset import CORD_SCORED_FIELDS
from distill.evaluate import Counts, canonical, evaluate, score_pair
from distill.schema import LineItem, Receipt


def test_perfect_match_scores_one():
    gold = Receipt(vendor="ACME", total=10.0)
    rep = evaluate([gold.model_dump_json()], [gold])
    assert rep.field_f1["f1"] == 1.0
    assert rep.schema_validity == 1.0
    assert rep.exact_match == 1.0


def test_one_wrong_scalar_gives_half_f1():
    gold = Receipt(vendor="ACME", total=10.0)
    pred = Receipt(vendor="ACME", total=12.0)  # vendor right, total wrong
    rep = evaluate([pred.model_dump_json()], [gold])
    # vendor: TP; total: FP+FN  -> tp=1, fp=1, fn=1 -> f1 = 0.5
    assert rep.field_f1["tp"] == 1
    assert rep.field_f1["fp"] == 1
    assert rep.field_f1["fn"] == 1
    assert rep.field_f1["f1"] == 0.5
    assert rep.exact_match == 0.0
    assert rep.per_field_accuracy["vendor"] == 1.0
    assert rep.per_field_accuracy["total"] == 0.0


def test_invalid_output_is_pure_fn():
    gold = Receipt(vendor="ACME", total=10.0)
    rep = evaluate(["not valid json"], [gold])
    assert rep.schema_validity == 0.0
    # nothing produced -> tp=0, fp=0, fn=2 (vendor+total) -> f1 = 0.0
    assert rep.field_f1["tp"] == 0
    assert rep.field_f1["fn"] == 2
    assert rep.field_f1["f1"] == 0.0


def test_line_item_matching_by_description():
    item = LineItem(description="Widget", total_price=5.0)
    gold = Receipt(vendor="A", total=5.0, line_items=[item])
    # Prediction drops the line item entirely.
    pred = Receipt(vendor="A", total=5.0, line_items=[])
    c = score_pair(pred, gold)
    # scalars vendor+total -> 2 TP; missed item -> description+total_price = 2 FN
    assert (c.tp, c.fp, c.fn) == (2, 0, 2)
    assert c.recall == 0.5


def test_line_items_order_insensitive():
    a = LineItem(description="Apple", total_price=1.0)
    b = LineItem(description="Banana", total_price=2.0)
    gold = Receipt(line_items=[a, b])
    pred = Receipt(line_items=[b, a])  # reversed order
    assert canonical(pred) == canonical(gold)
    c = score_pair(pred, gold)
    assert (c.fp, c.fn) == (0, 0)


def test_normalization_casefold_and_rounding():
    gold = Receipt(vendor="ACME", total=10.0)
    pred = Receipt(vendor="acme", total=10.004)  # case + sub-cent difference
    c = score_pair(pred, gold)
    assert (c.tp, c.fp, c.fn) == (2, 0, 0)  # both normalize equal


def test_counts_f1_empty_is_one():
    # No gold slots and no predictions => nothing to get wrong => f1 = 1.0
    assert Counts().f1 == 1.0


# --- scored-field policy (D-010: score only the fields a dataset labels) ---

def test_scored_fields_allowlist_excludes_unlabeled_fields():
    # CORD-style gold labels amounts + items but not vendor/date/currency; the model
    # still extracts those three. They must not be scored against absent gold.
    gold = Receipt(subtotal=10.0, tax=1.0, total=11.0)
    pred = Receipt(
        vendor="ACME", date="2026-01-01", currency="USD",
        subtotal=10.0, tax=1.0, total=11.0,
    )
    pj = pred.model_dump_json()

    # Default policy scores every field → the 3 extracted-but-unlabeled fields are FPs.
    full = evaluate([pj], [gold])
    assert full.field_f1["tp"] == 3 and full.field_f1["fp"] == 3
    assert full.exact_match == 0.0

    # CORD policy scores only labeled fields → perfect, no penalty for vendor/date/currency.
    cord = evaluate([pj], [gold], scored_fields=CORD_SCORED_FIELDS)
    assert cord.field_f1["tp"] == 3  # subtotal, tax, total
    assert (cord.field_f1["fp"], cord.field_f1["fn"]) == (0, 0)
    assert cord.field_f1["f1"] == 1.0
    assert cord.exact_match == 1.0  # unscored fields are ignored by exact-match too
    assert set(cord.scored_fields) == set(CORD_SCORED_FIELDS)
    assert "vendor" not in cord.per_field_accuracy  # unscored → not reported
    assert cord.schema_validity == 1.0  # still validated against the full receipt-v1 schema


def test_scored_fields_still_penalizes_wrong_labeled_field():
    gold = Receipt(subtotal=10.0, tax=1.0, total=11.0)
    pred = Receipt(vendor="ACME", subtotal=10.0, tax=1.0, total=99.0)  # total wrong
    cord = evaluate([pred.model_dump_json()], [gold], scored_fields=CORD_SCORED_FIELDS)
    assert cord.field_f1["tp"] == 2  # subtotal, tax
    assert (cord.field_f1["fp"], cord.field_f1["fn"]) == (1, 1)  # total wrong
    assert cord.per_field_accuracy["total"] == 0.0


def test_scored_fields_score_pair_ignores_unscored_scalars():
    gold = Receipt(vendor="ACME", total=10.0)
    pred = Receipt(vendor="OTHER", total=10.0)  # vendor wrong, total right
    # vendor excluded → only total scored → clean TP, no penalty for the wrong vendor.
    c = score_pair(pred, gold, scored_fields={"total"})
    assert (c.tp, c.fp, c.fn) == (1, 0, 0)


def test_unknown_scored_field_is_rejected():
    gold = Receipt(total=1.0)
    with pytest.raises(ValueError):
        evaluate([gold.model_dump_json()], [gold], scored_fields={"bogus"})
