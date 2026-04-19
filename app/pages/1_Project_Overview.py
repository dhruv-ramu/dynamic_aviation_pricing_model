from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components import charts, data_loader
from components.text_blocks import navigation_hint, rm_problem_plain
from components.ui import render_sidebar_glossary

st.set_page_config(page_title="Project overview", page_icon="✈️", layout="wide")
render_sidebar_glossary()

st.title("Project overview")
st.markdown(rm_problem_plain())

st.subheader("What this project simulates")
st.markdown(
    """
We simulate **one flight** with a fixed cabin size, a **booking horizon** of many days, and **stochastic**
travelers who may or may not purchase at the quoted fare. The airline can **overbook** (sell past the seat count)
up to a cap, then faces **no-shows** and occasional **denied boardings** with explicit costs.

Three automated **pricing policies** choose fares day by day. We compare their **distribution of profit** across
hundreds of randomized runs for each scenario.
"""
)

st.subheader("The three policies (high level)")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Static**")
    st.caption("One fare posture for the whole horizon—useful as a simple baseline.")
with c2:
    st.markdown("**Rule-based**")
    st.caption("If-then style rules using time and how full the plane is—like a compact RM playbook.")
with c3:
    st.markdown("**Dynamic**")
    st.caption("Adapts using booking pace, remaining seats, and demand pressure—aims for profit, not just load.")

st.subheader("Main finding (plain English)")
st.markdown(
    """
- **No single policy wins everywhere.** The best choice depends on the demand regime and how much operational tail
  risk (bumps) shows up.
- **Rule-based** tends to win when conditions are **stable** and the playbook’s sell-up behavior matches the
  environment.
- **Dynamic** tends to pull ahead when **demand is strong**, when **late bookings** are economically important, or
  when **overbooking stress** makes bump costs material—because it can throttle aggressiveness differently than
  fixed thresholds.
"""
)

policy_df = data_loader.load_csv("policy_results_by_scenario.csv")
winner_df = data_loader.load_csv("winner_table.csv")
if policy_df is not None and winner_df is not None:
    st.subheader("Key results (from your final export)")
    w1, w2 = st.columns((1, 2))
    with w1:
        st.dataframe(
            winner_df[["scenario", "winner", "dynamic_minus_static", "rule_based_minus_static"]],
            use_container_width=True,
            height=380,
            column_config={
                "dynamic_minus_static": st.column_config.NumberColumn("Dynamic − static", format="$%.0f"),
                "rule_based_minus_static": st.column_config.NumberColumn("Rule − static", format="$%.0f"),
            },
        )
    with w2:
        fig = charts.chart_policy_grouped_bar(
            policy_df,
            value_col="mean_profit",
            y_title="Mean profit ($)",
            title="Mean profit across scenarios",
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Load `reports/final/tables/*.csv` to populate results (see sidebar status).")

st.divider()
st.markdown("### How to navigate this app")
st.markdown(navigation_hint())
