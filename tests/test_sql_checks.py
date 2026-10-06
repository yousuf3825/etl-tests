import pytest

from checks import assert_no_bad_rows

pytestmark = pytest.mark.critical     # every check in this file blocks the release

# Each check: the table it reports on, and a query that returns the bad rows.
# {v} becomes approved or release.
CHECKS = {
    "no_duplicate_ids": ("{v}_silver_transactions", """
        SELECT transaction_id FROM {v}_silver_transactions
        GROUP BY transaction_id HAVING COUNT(*) > 1"""),

        "no_blank_keys": ("{v}_silver_transactions", """
        SELECT transaction_id FROM {v}_silver_transactions
        WHERE transaction_id IS NULL OR txn_date IS NULL OR account_id IS NULL"""),

    "types_allowed": ("{v}_silver_transactions", """
        SELECT transaction_id FROM {v}_silver_transactions
        WHERE txn_type NOT IN ('DEBIT', 'CREDIT', 'REFUND')"""),

    "every_bronze_row_accounted": ("bronze_transactions", """
        SELECT txn_id FROM bronze_transactions
        WHERE txn_id NOT IN (SELECT transaction_id FROM {v}_silver_transactions)
          AND txn_id NOT IN (SELECT transaction_id FROM {v}_silver_transactions_reject)"""),
}


@pytest.mark.parametrize("version", ["approved", "release"])
@pytest.mark.parametrize("check", CHECKS)
def test_sql_check(db, check, version):
    table, sql = CHECKS[check]
    assert_no_bad_rows(db, f"{check} ({version})", table.format(v=version), sql.format(v=version))