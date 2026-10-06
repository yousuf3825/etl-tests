from datetime import date

import pytest
pytestmark = pytest.mark.critical     # every test in this file is critical
from bank_rules import clean_txn_type, parse_txn_date

pytestmark = pytest.mark.critical     # every test in this file is critical


@pytest.mark.parametrize("raw, expected", [
    ("DEBIT", "DEBIT"),
    ("DR", "DEBIT"),
    ("debit", "DEBIT"),
    ("Debit", "DEBIT"),
    ("CREDIT", "CREDIT"),
    ("CR", "CREDIT"),
    ("credit", "CREDIT"),
    ("REFUND", "REFUND"),
])
def test_type_spelling(raw, expected):
    assert clean_txn_type(raw) == expected, f"type {raw!r} should become {expected!r}"


def test_blank_type_is_an_error():
    with pytest.raises(ValueError):
        clean_txn_type("  ")


@pytest.mark.parametrize("text, expected", [
    ("01/04/2026", date(2026, 4, 1)),
    ("03/04/2026", date(2026, 4, 3)),     # day first: 3 April, not 4 March
    ("31/04/2026", None),                 # April has 30 days
    ("2026-04-03", None),                 # wrong format
], ids=["first_of_april", "day_first", "impossible_date", "wrong_format"])
def test_date_rule(text, expected):
    assert parse_txn_date(text) == expected
