def test_no_duplicate_ids(db):
    rows = db.execute("""
        SELECT transaction_id FROM release_silver_transactions
        GROUP BY transaction_id HAVING COUNT(*) > 1
    """).fetchall()
    assert rows == []