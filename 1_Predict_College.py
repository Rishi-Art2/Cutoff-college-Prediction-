# """
# pages/1_Predict_College.py
# ---------------------------
# Core prediction page. Takes the user's percentile + category (+ optional
# branch) and shows every college/branch combination they're eligible for,
# using the cutoff dataset in data/cutoff_data.csv.
# """

import os

import numpy as np
import pandas as pd
import streamlit as st

from database import save_prediction

st.set_page_config(page_title="Predict College", page_icon="🎯", layout="wide")

# ---- must be logged in ----
if not st.session_state.get("logged_in"):
    st.warning("Please log in first from the main page (sidebar → app).")
    st.stop()

st.title("🎯 Predict Your College")

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cutoff_data.csv"
)


@st.cache_data
def load_data(path):
    return pd.read_csv(path)


df = load_data(DATA_PATH)

st.caption(
    "⚠️ Demo data: cutoffs below are randomly generated sample values, **not** real "
    "exam cutoffs. Swap in your own `data/cutoff_data.csv` for real predictions."
)

col1, col2 = st.columns(2)
with col1:
    percentile = st.number_input(
        "Your Percentile / Score",
        min_value=0.0,
        max_value=100.0,
        value=90.0,
        step=0.01,
        help="Enter your entrance exam percentile (0-100).",
    )
with col2:
    category = st.selectbox("Category", sorted(df["Category"].unique()))

col3, col4 = st.columns(2)
with col3:
    branch_options = ["All Branches"] + sorted(df["Branch"].unique().tolist())
    branch = st.selectbox("Branch (optional)", branch_options)
with col4:
    round_options = ["All Rounds"] + sorted(df["Round"].unique().tolist())
    cap_round = st.selectbox("CAP Round", round_options, help="Cutoffs usually ease a bit in later rounds.")

if st.button("🔍 Predict Colleges", type="primary"):
    eligible = df[(df["Category"] == category) & (df["Cutoff_Percentile"] <= percentile)].copy()
    if branch != "All Branches":
        eligible = eligible[eligible["Branch"] == branch]
    if cap_round != "All Rounds":
        eligible = eligible[eligible["Round"] == cap_round]

    eligible = eligible.sort_values(["Round", "Cutoff_Percentile"], ascending=[True, False])

    # NumPy: compute how much percentile margin the student has over each cutoff
    eligible["Margin"] = np.round(percentile - eligible["Cutoff_Percentile"].to_numpy(), 2)

    # Save this search into the SQL history for the logged-in user
    save_prediction(
        st.session_state.user["id"],
        percentile,
        category,
        branch,
        cap_round,
        len(eligible),
    )

    if eligible.empty:
        st.error(
            "No colleges found for this percentile/category/branch/round combination. "
            "Try a different branch, round, or double-check your percentile."
        )
    else:
        st.success(f"✅ You're eligible for {len(eligible)} college-branch option(s)!")
        st.dataframe(
            eligible[
                ["College", "Branch", "Category", "Round", "Cutoff_Percentile", "Margin"]
            ].reset_index(drop=True),
            use_container_width=True,
        )

        st.download_button(
            "⬇️ Download results as CSV",
            data=eligible.to_csv(index=False).encode("utf-8"),
            file_name="my_eligible_colleges.csv",
            mime="text/csv",
        )