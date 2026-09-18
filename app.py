"""Fintech Risk Dashboard (Streamlit).

Usage:
    pip install streamlit pandas
    streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

# --- local imports (same folder) ---
from anomaly import flag_transactions
from scoring import compute_score

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "transactions.csv"

st.set_page_config(page_title="Fintech Risk Dashboard", layout="wide")
st.title("💳 Fintech Risk Dashboard")


@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"])
    df = flag_transactions(df)
    df = compute_score(df)
    return df


df = load_data()
st.caption(f"Rows: {len(df):,} | Merchants: {df.merchant_id.nunique()} | Payers: {df.payer_id.nunique()}")

# --- sidebar: merchant selector ---
st.sidebar.header("Select Merchant")
all_merchants = sorted(df["merchant_id"].unique())
selected = st.sidebar.selectbox("Merchant", all_merchants)

m = df[df.merchant_id == selected].iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Risk Score", f"{m.score:.1f}")
col2.metric("Risk Band", m.risk_band.upper())
col3.metric("Loan Limit", f"₹{m.loan_limit:,.0f}")
col4.metric("Flagged Txns", int(df[df.merchant_id == selected].is_flagged.sum()))

# --- feature contributions ---
st.subheader(f"Merchant {selected} — Feature Contributions")
contribs = m.feature_contributions
st.json(contribs)

# --- transaction trends (daily volume) ---
st.subheader("Daily Transaction Trend")
daily = (
    df[df.merchant_id == selected]
    .set_index("timestamp")
    .resample("D")
    .agg(total=("amount", "sum"), count=("txn_id", "count"))
    .fillna(0)
)
st.line_chart(daily[["total", "count"]])

# --- flagged transactions ---
st.subheader("Flagged Transactions")
flagged = df[(df.merchant_id == selected) & (df.is_flagged)].sort_values("timestamp", ascending=False)
st.dataframe(
    flagged[["txn_id", "payer_id", "amount", "flag_reason", "status", "timestamp"]],
    use_container_width=True,
)
