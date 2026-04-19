"""Airline RM explainer — run with: ``streamlit run app/streamlit_app.py`` (from workspace root)."""

from __future__ import annotations

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parent
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

import streamlit as st

from components import charts, data_loader
from components.text_blocks import home_intro, navigation_hint
from components.ui import render_sidebar_glossary

st.set_page_config(
    page_title="Airline RM Simulator",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_sidebar_glossary()

st.title("Airline revenue management — interactive walkthrough")
st.caption("Single-leg simulator · three policies · Monte Carlo scenarios · results from `reports/final`")

st.markdown(home_intro())

policy_df = data_loader.load_csv("policy_results_by_scenario.csv")
winner_df = data_loader.load_csv("winner_table.csv")

if policy_df is None or winner_df is None:
    st.error(
        "Could not load core tables. Generate the bundle first:\n\n"
        "`cd airline_rm_project && PYTHONPATH=src python -m airline_rm.evaluation.final_report_export`"
    )
else:
    n_scen = winner_df["scenario"].nunique()
    dyn_wins = int((winner_df["winner"] == "dynamic").sum())
    rb_wins = int((winner_df["winner"] == "rule_based").sum())
    st_wins = int((winner_df["winner"] == "static").sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Scenarios compared", n_scen)
    c2.metric("Rule-based wins (mean profit)", rb_wins)
    c3.metric("Dynamic wins", dyn_wins)
    c4.metric("Static wins", st_wins)

    st.markdown("#### Key results snapshot")
    st.info(
        "In **stable / moderate** presets, **rule-based** pricing often leads on mean profit. "
        "In **strong demand**, **very strong late demand**, and the **overbook bump stress** preset, **dynamic** "
        "leads—illustrating that adaptation and bump-risk management can matter more than a fixed playbook."
    )

    img = data_loader.figure_path("scenario_policy_mean_profit.png")
    if img:
        st.image(str(img), use_container_width=True, caption="Mean profit by scenario and policy (pre-rendered figure from the final report bundle).")
    else:
        st.warning("`scenario_policy_mean_profit.png` not found — open **Scenarios & findings** for Plotly charts from CSVs.")

st.divider()
st.markdown("### How to navigate")
st.markdown(navigation_hint())
