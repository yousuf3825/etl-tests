"""Great Expectations on the bank's silver table. Run: python gx_checks.py approved   (or release)"""
import sqlite3
import sys

import great_expectations as gx
import pandas as pd

VERSION = sys.argv[1]                                     # approved or release
TABLE = f"{VERSION}_silver_transactions"

# 1. The data: one silver table from bank.db, as a pandas DataFrame
conn = sqlite3.connect("file:data/bank.db?mode=ro", uri=True)
silver = pd.read_sql(f"SELECT * FROM {TABLE}", conn, parse_dates=["txn_date"])
print(f"{TABLE}: {len(silver):,} rows")

# 2. The GX project (a folder called gx) and where the data comes from
context = gx.get_context(mode="file")
batch_def = (context.data_sources.add_or_update_pandas("bank")
             .add_dataframe_asset(TABLE)
             .add_batch_definition_whole_dataframe("whole table"))



# 3. The expectation suite: what good data looks like
suite = context.suites.add_or_update(gx.ExpectationSuite(name="silver_transactions", expectations=[
    gx.expectations.ExpectColumnValuesToNotBeNull(column="transaction_id"),
    gx.expectations.ExpectColumnValuesToNotBeNull(column="account_id"),
    gx.expectations.ExpectColumnValuesToNotBeNull(column="channel", mostly=0.99),
    gx.expectations.ExpectColumnValuesToBeUnique(column="transaction_id"),
    gx.expectations.ExpectColumnValuesToBeInSet(column="txn_type", value_set=["DEBIT", "CREDIT", "REFUND"]),
    gx.expectations.ExpectColumnValuesToBeBetween(column="amount", min_value=-5000, max_value=150000),
    gx.expectations.ExpectColumnValuesToBeBetween(column="txn_date", min_value=pd.Timestamp("2026-04-01"),
                                                  max_value=pd.Timestamp("2026-06-30")),
]))

# 4. Validate this version and read the result
validation = context.validation_definitions.add_or_update(
    gx.ValidationDefinition(name=f"{TABLE} check", data=batch_def, suite=suite))
result = validation.run(batch_parameters={"dataframe": silver})

stats = result.statistics
print("PASSED" if result.success else "FAILED",
      f"{stats['successful_expectations']} of {stats['evaluated_expectations']} expectations met")
for r in result.results:
    if not r.success:
        e = r.expectation_config
        print(f"  {e.type} on {e.kwargs['column']}: {r.result['unexpected_count']:,} bad rows,"
              f" for example {[str(v) for v in r.result['partial_unexpected_list'][:3]]}")

# 5. Save the result as a readable report (Data Docs) and open it
checkpoint = context.checkpoints.add_or_update(gx.Checkpoint(
    name=f"{TABLE} checkpoint", validation_definitions=[validation],
    actions=[gx.checkpoint.UpdateDataDocsAction(name="update data docs")]))
checkpoint.run(batch_parameters={"dataframe": silver})
context.open_data_docs()