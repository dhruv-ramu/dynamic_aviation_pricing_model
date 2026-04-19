from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components import charts, data_loader
from components.text_blocks import overbooking_plain
from components.ui import render_sidebar_glossary

st.set_page_config(page_title="Overbooking stress test", page_icon="✈️", layout="wide")
render_sidebar_glossary()

st.title("Stress test: overbooking and bump risk")
st.markdown(overbooking_plain())

SCEN = "overbook_bump_stress"

policy_df = data_loader.load_csv("policy_results_by_scenario.csv")
winner_df = data_loader.load_csv("winner_table.csv")
run_df = data_loader.load_csv("run_level_results_full.csv", subdir="raw_exports")

if policy_df is None:
    st.error("Missing `policy_results_by_scenario.csv`.")
    st.stop()

sub = policy_df[policy_df["scenario"] == SCEN]
if sub.empty:
    st.error(f"Scenario `{SCEN}` not found in policy results.")
    st.stop()

st.subheader("What bump risk means here")
st.info(
    "**Bump risk** = fraction of Monte Carlo runs where **denied boardings > 0**. "
    "It is a simple tail-risk counter, not a calibrated operational forecast."
)

if winner_df is not None:
    wr = winner_df[winner_df["scenario"] == SCEN]
    if not wr.empty:
        st.success(
            f"In **`{SCEN}`**, the highest **mean profit** policy was **`{wr.iloc[0]['winner']}`** — "
            "this is the scenario where aggressive fill can collide with show-ups."
        )

st.subheader("Bump risk and mean denied boardings (by policy)")
col1, col2 = st.columns(2)
with col1:
    f1 = charts.chart_one_metric_three_policies(
        policy_df,
        SCEN,
        value_col="bump_risk",
        y_title="Fraction of runs",
        title="Bump risk",
    )
    if f1:
        st.plotly_chart(f1, use_container_width=True)
with col2:
    f2 = charts.chart_one_metric_three_policies(
        policy_df,
        SCEN,
        value_col="mean_denied_boardings",
        y_title="Passengers (mean)",
        title="Mean denied boardings",
    )
    if f2:
        st.plotly_chart(f2, use_container_width=True)

st.subheader("Booking rate vs boarded load (gap story)")
st.markdown(
    """
**Accepted booking load factor** counts tickets sold against cabin seats (can exceed 1 when overselling).
**Boarded load factor** counts who actually flies. A wide gap often means **no-shows** helped—but under stress,
**denied boardings** can also appear when show-ups exceed seats.
"""
)
for fname, cap in [
    ("booking_vs_boarded_load_factor__overbook_bump_stress.png", "Pre-rendered scatter from the final report."),
]:
    p = data_loader.figure_path(fname)
    if p:
        st.image(str(p), use_container_width=True, caption=cap)
    else:
        st.caption(f"Missing `{fname}`.")

st.subheader("Denied boarding distribution (run-level)")
pimg = data_loader.figure_path("denied_boarding_distribution__overbook_bump_stress.png")
if pimg:
    st.image(str(pimg), use_container_width=True, caption="Pre-rendered histogram from the final report bundle.")
elif run_df is not None:
    fd = charts.chart_denied_boardings_histogram(run_df, SCEN)
    if fd:
        st.plotly_chart(fd, use_container_width=True)
else:
    st.caption("No denied-boarding chart available (missing PNG and run-level CSV).")

if run_df is not None:
    st.subheader("Profit distribution (same scenario)")
    fig = charts.chart_profit_histogram(run_df, SCEN)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Plain-English interpretation (project-specific)")
st.markdown(
    """
- **Static** can look “safe” on bumps in some environments because it does not chase bookings as aggressively—but
  that safety can come at the cost of **revenue left on the table**.
- **Rule-based** can **overfill** relative to bump costs when thresholds keep pushing sell-up in a high-show-up
  regime; once denied-boarding costs bite, mean profit can collapse.
- **Dynamic** can **win here** by reacting to pace/scarcity in a way that reduces bump incidence while still
  capturing revenue—your exported means should be read as **evidence inside this simulator**, not a universal law.
"""
)
