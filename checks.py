import time

import pytest


def assert_no_bad_rows(conn, check, table, sql):
    """Every row the query returns is a bad row. No rows means pass. The first column is the key."""
    cursor = conn.execute(sql)
    rows = cursor.fetchall()
    if rows:
        key = cursor.description[0][0]
        first = ", ".join(str(row[0]) for row in rows[:5])
        pytest.fail(f"{check}: {len(rows):,} bad rows in {table}. Key {key}, first 5: {first}",
                    pytrace=False)

def column_types(cursor, table, target):
    """{column name: TYPE} for one table, on SQLite or on Databricks."""
    if target == "databricks":
        for attempt in range(3):
            try:
                rows = cursor.execute(
                    f"DESCRIBE TABLE {table}"
                ).fetchall()
                break
            except Exception as exc:
                if "Deadlock found when trying to get lock" not in str(exc) or attempt == 2:
                    raise
                time.sleep(1 + attempt)
    else:
        rows = [
            (r[1], r[2])
            for r in cursor.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
        ]

    return {
        name: col_type.upper()
        for name, col_type, *_ in rows
        if name and not name.startswith("#")
    }