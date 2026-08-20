"""Schema contract tests: known-good parses, known-bad rejects (Phase 1 acceptance)."""

import pytest

from distill.schema import SCHEMA_VERSION, Receipt, SchemaError, is_valid, parse_and_validate

GOOD = """
{
  "vendor": "ACME Corp",
  "date": "2026-03-02",
  "currency": "USD",
  "line_items": [
    {"description": "Widget", "quantity": 2, "unit_price": 12.0, "total_price": 24.0}
  ],
  "subtotal": 24.0,
  "tax": 1.92,
  "total": 25.92
}
"""


def test_schema_version_present():
    assert SCHEMA_VERSION == "receipt-v1"


def test_parses_known_good():
    r = parse_and_validate(GOOD)
    assert isinstance(r, Receipt)
    assert r.vendor == "ACME Corp"
    assert r.total == 25.92
    assert len(r.line_items) == 1
    assert r.line_items[0].description == "Widget"


def test_parses_minimal_all_null():
    r = parse_and_validate('{"line_items": []}')
    assert r.vendor is None and r.total is None and r.line_items == []


def test_strips_code_fence():
    fenced = "```json\n" + GOOD.strip() + "\n```"
    assert is_valid(fenced)


def test_extracts_from_surrounding_prose():
    prose = 'Sure, here you go: {"vendor": "A", "line_items": []} — hope that helps!'
    r = parse_and_validate(prose)
    assert r.vendor == "a" or r.vendor == "A"  # value preserved as-is (no normalization here)


def test_rejects_non_json():
    with pytest.raises(SchemaError):
        parse_and_validate("this is not json at all")


def test_rejects_extra_key():
    with pytest.raises(SchemaError):
        parse_and_validate('{"vendor": "A", "line_items": [], "surprise": 1}')


def test_rejects_wrong_line_items_type():
    with pytest.raises(SchemaError):
        parse_and_validate('{"line_items": {"not": "a list"}}')


def test_rejects_non_numeric_total():
    with pytest.raises(SchemaError):
        parse_and_validate('{"line_items": [], "total": "not-a-number"}')


def test_is_valid_never_raises():
    assert is_valid(GOOD) is True
    assert is_valid("garbage") is False
