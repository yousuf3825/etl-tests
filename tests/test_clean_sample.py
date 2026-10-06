import pytest

REQUIRED = ["transaction_id", "txn_date", "txn_type", "amount", "account_id", "branch_code"]


@pytest.mark.critical
def test_raw_file_has_13_rows(raw_txns):
    assert len(raw_txns) == 13


@pytest.mark.critical
def test_clean_rows(clean_txns):
    # 13 rows - 1 duplicate - 1 "N/A" amount - 1 blank account = 10
    assert len(clean_txns) == 10


@pytest.mark.critical
def test_no_duplicate_ids(clean_txns):
    dups = clean_txns[clean_txns["transaction_id"].duplicated()]["transaction_id"].tolist()
    assert not dups, f"duplicate transaction_ids: {dups}"


@pytest.mark.critical
@pytest.mark.parametrize("column", REQUIRED)
def test_no_blanks(clean_txns, column):
    blanks = clean_txns[clean_txns[column].isna() | (clean_txns[column].astype(str) == "")]
    assert blanks.empty, f"{column}: {len(blanks)} blank value(s) in {blanks['transaction_id'].tolist()}"


@pytest.mark.critical
def test_types_allowed(clean_txns):
    bad = sorted(set(clean_txns["txn_type"]) - {"DEBIT", "CREDIT", "REFUND"})
    assert not bad, f"txn_type has values outside DEBIT, CREDIT, REFUND: {bad}"


@pytest.mark.warning
def test_unknown_branch_share(clean_txns):
    share = float((clean_txns["branch_code"] == "UNK").mean())
    assert share <= 0.05, f"{share:.0%} of rows have an unknown branch (UNK), limit is 5%"


@pytest.mark.warning
def test_blank_channel_share(clean_txns):
    share = float((clean_txns["channel"] == "").mean())
    assert share <= 0.05, f"{share:.0%} of rows have a blank channel, limit is 5%"