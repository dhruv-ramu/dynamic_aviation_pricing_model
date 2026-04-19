from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components import charts, data_loader
from components.formatting import fmt_usd, policy_label, scenario_title
from components.ui import render_sidebar_glossary

st.set_page_config(page_title="Scenarios & findings", page_icon="✈️", layout="wide")
render_sidebar_glossary()

st.title("Scenarios and findings")
st.markdown(
    """
Each **scenario** is a named preset: a small set of parameter overrides on the same base route configuration.
We then run **Monte Carlo** replications and compare policies on **average profit** and other operational KPIs.
"""
)

policy_df = data_loader.load_csv("policy_results_by_scenario.csv")
winner_df = data_loader.load_csv("winner_table.csv")
summary_df = data_loader.load_csv("scenario_summary_table.csv")
run_df = data_loader.load_csv("run_level_results_full.csv", subdir="raw_exports")

if policy_df is None or winner_df is None:
    st.error("Missing `policy_results_by_scenario.csv` or `winner_table.csv`. Generate `reports/final` first.")
    st.stop()

scenarios = sorted(policy_df["scenario"].unique().tolist())
choice = st.selectbox("Choose a scenario", scenarios, format_func=scenario_title, index=0)

row_w = winner_df[winner_df["scenario"] == choice].iloc[0]
winner = str(row_w["winner"])
sub_pol = policy_df[policy_df["scenario"] == choice]

st.subheader(f"Selected: {scenario_title(choice)}")
c1, c2, c3 = st.columns(3)
c1.metric("Winner (mean profit)", policy_label(winner))
rb_gap = float(row_w["rule_based_minus_static"])
dyn_gap = float(row_w["dynamic_minus_static"])
c2.metric("Rule-based vs static", fmt_usd(rb_gap))
c3.metric("Dynamic vs static", fmt_usd(dyn_gap))

if summary_df is not None and not summary_df[summary_df["scenario"] == choice].empty:
    srow = summary_df[summary_df["scenario"] == choice].iloc[0]
    st.markdown(
        f"**Regime label (from export):** {srow['likely_regime_type']}  \n"
        f"**Automated short note:** {srow['key_takeaway_short']}"
    )

st.markdown(
    f"""
**Why this scenario is economically different:** presets tweak demand level, segment mix, no-show behavior,
overbooking cap, and competitor settings. The point is not to mimic a real city-pair—it is to **isolate mechanisms**
so we can see when a playbook vs an adaptive controller wins.
"""
)

st.markdown("#### Policy comparison (this scenario)")
st.dataframe(
    sub_pol,
    use_container_width=True,
    hide_index=True,
    column_config={
        "mean_profit": st.column_config.NumberColumn("Mean profit", format="$%.0f"),
        "mean_revenue": st.column_config.NumberColumn("Mean revenue", format="$%.0f"),
        "mean_boarded_load_factor": st.column_config.NumberColumn("Boarded LF", format="%.2f"),
        "mean_accepted_booking_load_factor": st.column_config.NumberColumn("Accepted LF", format="%.2f"),
        "mean_booking_rate": st.column_config.NumberColumn("Booking rate", format="%.2f"),
        "mean_avg_fare": st.column_config.NumberColumn("Avg fare", format="$%.0f"),
        "bump_risk": st.column_config.NumberColumn("Bump risk", format="%.2f"),
        "mean_denied_boardings": st.column_config.NumberColumn("Mean denied", format="%.2f"),
    },
)

st.markdown("#### Charts (interactive, from CSV)")
col_a, col_b = st.columns(2)
with col_a:
    f1 = charts.chart_one_metric_three_policies(
        policy_df,
        choice,
        value_col="mean_profit",
        y_title="USD",
        title="Mean profit",
    )
    if f1:
        st.plotly_chart(f1, use_container_width=True)
with col_b:
    f2 = charts.chart_one_metric_three_policies(
        policy_df,
        choice,
        value_col="mean_revenue",
        y_title="USD",
        title="Mean revenue",
    )
    if f2:
        st.plotly_chart(f2, use_container_width=True)

col_c, col_d = st.columns(2)
with col_c:
    f3 = charts.chart_one_metric_three_policies(
        policy_df,
        choice,
        value_col="mean_boarded_load_factor",
        y_title="0–1 fraction",
        title="Mean boarded load factor",
    )
    if f3:
        st.plotly_chart(f3, use_container_width=True)
with col_d:
    f4 = charts.chart_one_metric_three_policies(
        policy_df,
        choice,
        value_col="mean_avg_fare",
        y_title="USD",
        title="Mean average fare",
    )
    if f4:
        st.plotly_chart(f4, use_container_width=True)

traj_df = data_loader.load_csv("fare_trajectories_sampled.csv", subdir="raw_exports")
if traj_df is not None and choice in set(traj_df["scenario"].astype(str)):
    st.markdown("#### Representative fare paths (rule-based vs dynamic)")
    st.caption("From `fare_trajectories_sampled.csv` (runs closest to each policy’s mean profit).")
    ft = charts.chart_fare_trajectories(traj_df, choice)
    if ft:
        st.plotly_chart(ft, use_container_width=True)

if run_df is not None:
    st.markdown("#### Profit distribution (run-level)")
    fh = charts.chart_profit_histogram(run_df, choice)
    if fh:
        st.plotly_chart(fh, use_container_width=True)
else:
    st.caption("`run_level_results_full.csv` not found — skipping profit histogram.")

sd = data_loader.load_markdown("scenario_definitions.md")
if sd:
    with st.expander("Scenario definitions (from `scenario_definitions.md`)"):
        st.markdown(sd)

st.divider()
st.subheader("Across all scenarios")
st.markdown("**Winner table** (who wins on mean profit in each preset).")
st.dataframe(
    winner_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "mean_profit_static": st.column_config.NumberColumn(format="$%.0f"),
        "mean_profit_rule_based": st.column_config.NumberColumn(format="$%.0f"),
        "mean_profit_dynamic": st.column_config.NumberColumn(format="$%.0f"),
        "rule_based_minus_static": st.column_config.NumberColumn(format="$%.0f"),
        "dynamic_minus_static": st.column_config.NumberColumn(format="$%.0f"),
        "dynamic_minus_rule_based": st.column_config.NumberColumn(format="$%.0f"),
    },
)

img = data_loader.figure_path("scenario_policy_mean_profit.png")
if img:
    st.image(str(img), use_container_width=True, caption="Pre-rendered: mean profit by scenario × policy.")
else:
    fall = charts.chart_policy_grouped_bar(
        policy_df,
        value_col="mean_profit",
        y_title="Mean profit ($)",
        title="Mean profit by scenario (fallback from CSV)",
    )
    st.plotly_chart(fall, use_container_width=True)
