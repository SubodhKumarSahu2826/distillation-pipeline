"""The CORD scoring policy encodes decision D-010 (score only CORD-labeled fields)."""

from distill.dataset import CORD_SCORED_FIELDS, CORD_UNSCORED_FIELDS
from distill.evaluate import ALL_FIELDS


def test_cord_scores_only_labeled_fields():
    assert CORD_SCORED_FIELDS == frozenset({"subtotal", "tax", "total", "line_items"})
    # vendor/date/currency are deliberately excluded — CORD has no ground truth for them.
    assert CORD_UNSCORED_FIELDS == frozenset({"vendor", "date", "currency"})
    assert CORD_SCORED_FIELDS.isdisjoint(CORD_UNSCORED_FIELDS)


def test_cord_policy_partitions_all_scorable_fields():
    # No field is silently forgotten: scored ∪ unscored == every scorable field.
    assert CORD_SCORED_FIELDS | CORD_UNSCORED_FIELDS == frozenset(ALL_FIELDS)
