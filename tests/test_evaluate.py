"""Metric tests: exact values on tiny hand-built cases (Phase 1 acceptance)."""

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
