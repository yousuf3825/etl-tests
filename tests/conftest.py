from pathlib import Path
import sqlite3
import pandas as pd
import pytest
from bank_rules import clean_transactions
import os
from databricks import sql
from dotenv import load_dotenv


DATA = Path(__file__).parent.parent / "data"
load_dotenv()


@pytest.fixture(scope="session")
def raw_txns():
    """The bank's sample file, every value kept as text, exactly as sent."""
    print("\n[fixture] reading sample_txns.csv")
    return pd.read_csv(DATA / "sample_txns.csv", dtype=str, keep_default_na=False)


@pytest.fixture(scope="session")
def clean_txns(raw_txns):
    """The same rows after the engineer's cleaning code."""
    return clean_transactions(raw_txns)

@pytest.fixture(scope="session")
def db(target):
    """One connection for the whole run: bank.db, or Databricks with --target databricks."""
    if target == "databricks":
        conn = sql.connect(
            server_hostname=need("DATABRICKS_SERVER_HOSTNAME"),
            http_path=need("DATABRICKS_HTTP_PATH"),
            access_token=need("DATABRICKS_TOKEN"),
            catalog="etl_testing",
            schema="test_results"
        )
    else:
        path = DATA / "bank.db"
        if not path.exists():
            pytest.exit(
                f"bank.db not found in {DATA}. "
                "Unzip bank_db.zip into the data folder."
            )
        conn = sqlite3.connect(
            path.as_uri() + "?mode=ro",
            uri=True
        )

    cursor = conn.cursor()
    yield cursor
    cursor.close()
    conn.close()

def pytest_addoption(parser):
    """Adds --target to pytest: local (the bank.db file) or databricks (the real tables)."""
    parser.addoption("--target", default="local", choices=["local", "databricks"])


@pytest.fixture(scope="session")
def target(request):
    return request.config.getoption("--target")

def need(name):
    """Read one setting from the environment. Stop the run if it is missing."""
    value = os.getenv(name)
    if not value:
        pytest.exit(f"{name} is not set. Add it to the .env file.")
    return value