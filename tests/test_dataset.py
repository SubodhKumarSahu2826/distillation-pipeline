"""CORD dataset module: the scored-field policy (D-010) and the CORD→receipt-v1 converter."""

import pytest

from distill.dataset import (
    CORD_SCORED_FIELDS,
    CORD_UNSCORED_FIELDS,
    build_gold,
    convert_record,
    parse_amount,
)
from distill.evaluate import ALL_FIELDS
from distill.schema import Receipt


def test_cord_scores_only_labeled_fields():
    assert CORD_SCORED_FIELDS == frozenset({"subtotal", "tax", "total", "line_items"})
    # vendor/date/currency are deliberately excluded — CORD has no ground truth for them.
    assert CORD_UNSCORED_FIELDS == frozenset({"vendor", "date", "currency"})
    assert CORD_SCORED_FIELDS.isdisjoint(CORD_UNSCORED_FIELDS)


def test_cord_policy_partitions_all_scorable_fields():
    # No field is silently forgotten: scored ∪ unscored == every scorable field.
    assert CORD_SCORED_FIELDS | CORD_UNSCORED_FIELDS == frozenset(ALL_FIELDS)


# --- parse_amount: CORD's number formats -----------------------------------------

@pytest.mark.parametrize(
    "words,expected",
    [
        (["1,346,000"], 1346000.0),   # comma thousands
        (["23.000"], 23000.0),        # dot thousands (Indonesian)
        (["45,000.00"], 45000.0),     # US: comma thousands, dot decimal
        (["9.500,00"], 9500.0),       # EU: dot thousands, comma decimal
        (["5272.73"], 5272.73),       # plain decimal
        (["0"], 0.0),
        (["2", "x"], 2.0),            # menu.cnt spells the quantity with an "x" symbol
        (["PB1", "144,695"], 144695.0),   # label carries a stray digit; amount is the value
        (["PB1:", "0"], 0.0),
        (["TAX", "10.00", "%", "4,964"], 4964.0),  # skip the percentage rate, take the amount
        (["x"], None),                # no numeric value
        ([], None),
    ],
)
def test_parse_amount(words, expected):
    assert parse_amount(words) == expected


# --- convert_record: CORD valid_line → receipt-v1 --------------------------------

def _entry(category, text, group_id=None, y=0, x=0):
    """A minimal CORD valid_line entry: split ``text`` into words with placeholder quads."""
    words, xx = [], x
    for tok in text.split():
        words.append({"text": tok, "quad": {
            "x1": xx, "y1": y, "x2": xx + 10, "y2": y,
            "x3": xx + 10, "y3": y + 10, "x4": xx, "y4": y + 10,
        }})
        xx += 20
    return {"words": words, "category": category, "group_id": group_id}


def _doc():
    return {"valid_line": [
        _entry("menu.cnt", "2 x", group_id=1, y=10, x=0),
        _entry("menu.nm", "Coffee Latte", group_id=1, y=10, x=60),
        _entry("menu.price", "50,000", group_id=1, y=10, x=200),
        _entry("menu.price", "9.500", group_id=2, y=40, x=200),   # group with no name → dropped
        _entry("sub_total.subtotal_price", "Sub-Total 50,000", y=80, x=0),
        _entry("sub_total.tax_price", "TAX 10.00 % 5,000", y=100, x=0),
        _entry("total.total_price", "Grand Total 55,000", y=120, x=0),
    ]}


def test_convert_record_maps_cord_fields():
    rec = convert_record(_doc(), "train/receipt_00000")
    assert rec["id"] == "train/receipt_00000"

    gold = rec["gold"]
    # scored scalars come from the labelled spans (rate "10.00 %" is not taken as the tax)
    assert gold["subtotal"] == 50000.0
    assert gold["tax"] == 5000.0
    assert gold["total"] == 55000.0
    # unscored fields CORD never labels stay null
    assert gold["vendor"] is None and gold["date"] is None and gold["currency"] is None
    # one line item (the name-less group is skipped)
    assert gold["line_items"] == [
        {"description": "Coffee Latte", "quantity": 2.0, "unit_price": None, "total_price": 50000.0}
    ]
    # the gold is a valid receipt-v1 object and the reconstructed text carries the content
    Receipt.model_validate(gold)
    assert "Coffee Latte" in rec["text"] and "55,000" in rec["text"]


def test_build_gold_is_schema_valid_even_with_no_items():
    gold = build_gold({"valid_line": [_entry("total.total_price", "TOTAL 12.000", y=0, x=0)]})
    assert gold["line_items"] == [] and gold["total"] == 12000.0
    Receipt.model_validate(gold)
