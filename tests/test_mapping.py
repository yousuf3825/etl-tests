from pathlib import Path
from checks import assert_no_bad_rows
import pandas as pd
import pytest
from checks import assert_no_bad_rows, column_types

pytestmark = pytest.mark.critical     # every mapping rule blocks the release

MAPPING_FILE = Path(__file__).parent.parent / "data" / "S2T_transactions_v1.4.csv"
MAPPING = pd.read_csv(MAPPING_FILE).to_dict("records")          # one dict per mapping row

ROWS = [pytest.param(row, id=row["Target column"]) for row in MAPPING]
VERSIONS = ["approved", "release"]
SQLITE_TYPE = {"STRING": "TEXT", "DATE": "TEXT", "DECIMAL(12,2)": "REAL"}    # SQLite has fewer types


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("row", ROWS)
def test_column_type(db, row, version):
    table = f"{version}_silver_transactions"
    columns = {info[1]: info[2] for info in db.execute(f"PRAGMA table_info({table})")}   # name: type
    column, expected = row["Target column"], SQLITE_TYPE[row["Data type"]]
    if column not in columns:
        pytest.fail(f"mapping row {row['#']} ({column}): no such column in {table}", pytrace=False)
    if columns[column] != expected:
        pytest.fail(f"mapping row {row['#']} ({column}): {table} has {columns[column]}, "
                    f"mapping says {row['Data type']}", pytrace=False)

NOT_NULL_ROWS = [pytest.param(row, id=row["Target column"]) for row in MAPPING if row["Nulls"] == "No"]

@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("row", ROWS)
def test_column_type(db, target, row, version):
    table = f"{version}_silver_transactions"
    columns = column_types(db, table, target)
    column = row["Target column"]
    expected = (
        row["Data type"]
        if target == "databricks"
        else SQLITE_TYPE[row["Data type"]]
    )
    
@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("row", NOT_NULL_ROWS)
def test_not_null(db, row, version):
    table, column = f"{version}_silver_transactions", row["Target column"]
    assert_no_bad_rows(db, f"mapping row {row['#']} ({column} is null)", table,
                       f"SELECT transaction_id FROM {table} WHERE {column} IS NULL")

# One query per mapping rule. It returns the bad rows. {t} is the silver table.
RULES = {
    "transaction_id": "SELECT transaction_id FROM {t} GROUP BY transaction_id HAVING COUNT(*) > 1",
    "txn_date": """SELECT DISTINCT s.transaction_id FROM {t} s
                   JOIN bronze_transactions b ON b.txn_id = s.transaction_id
                   WHERE s.txn_date <> substr(b.txn_dt, 7, 4) || '-' || substr(b.txn_dt, 4, 2) || '-' || substr(b.txn_dt, 1, 2)""",
    "txn_type": "SELECT transaction_id FROM {t} WHERE txn_type NOT IN ('DEBIT', 'CREDIT', 'REFUND')",
    "amount": "SELECT transaction_id FROM {t} WHERE txn_type = 'REFUND' AND amount >= 0",
    "account_id": "SELECT transaction_id FROM {t} WHERE account_id <> TRIM(account_id)",
    "branch_code": "SELECT transaction_id FROM {t} WHERE branch_code <> UPPER(branch_code)",
}


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("row", ROWS)
def test_rule(db, row, version):
    column = row["Target column"]
    if column not in RULES:
        pytest.skip(f"no check written yet for mapping row {row['#']} ({column})")
    table = f"{version}_silver_transactions"
    assert_no_bad_rows(db, f"mapping row {row['#']} ({column})", table, RULES[column].format(t=table))