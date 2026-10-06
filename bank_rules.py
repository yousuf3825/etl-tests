"""The engineer's code: the mapping sheet rules for transactions (S2T_transactions_v1.3)."""
from datetime import datetime
from decimal import Decimal, InvalidOperation

import pandas as pd

TYPE_MAP = {"DEBIT": "DEBIT", "DR": "DEBIT", "debit": "DEBIT", "Debit": "DEBIT",
            "CREDIT": "CREDIT", "CR": "CREDIT", "credit": "CREDIT",
            "REFUND": "REFUND"}
KNOWN_BRANCHES = {"CHN01", "CHN02", "CHN03", "CHN04", "CBE01", "CBE02", "MDU01", "TRY01"}


def clean_txn_type(value):
    """Mapping row 3: every spelling becomes DEBIT, CREDIT or REFUND."""
    if value is None or value.strip() == "":
        raise ValueError("txn type is blank")
    return TYPE_MAP.get(value, value)


def parse_txn_date(text):
    """Mapping row 2: dd/MM/yyyy text to a date. A date that cannot exist gives None."""
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None


def clean_amount(text):
    """Mapping row 4: text to a decimal with 2 places. "N/A" gives None."""
    try:
        return Decimal(text).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def clean_transactions(raw):
    """Apply every rule to a raw file. Duplicates and rejected rows are removed."""
    df = raw.drop_duplicates(subset="txn_id", keep="first").copy()
    out = pd.DataFrame({
        "transaction_id": df["txn_id"],
        "txn_date": df["txn_dt"].map(parse_txn_date),
        "txn_type": df["type"].map(clean_txn_type),
        "amount": df["amt"].map(clean_amount),
        "account_id": df["acct_no"].str.strip(),
        "branch_code": df["branch"].str.strip().str.upper()
                         .where(lambda b: b.isin(KNOWN_BRANCHES), "UNK"),
        "channel": df["channel"],
    })
    keep = out["txn_date"].notna() & out["amount"].notna() & (out["account_id"] != "")
    return out[keep].reset_index(drop=True)