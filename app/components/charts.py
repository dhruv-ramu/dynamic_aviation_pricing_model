"""Plotly chart helpers — restrained styling for portfolio demos."""

from __future__ import annotations

from typing import Sequence

import pandas as pd
import plotly.graph_objects as go

POLICY_COLORS = {
    "static": "#5c6b73",
    "rule_based": "#2e6f95",
    "dynamic": "#c45c26",
}

POLICY_ORDER: Sequence[str] = ("static", "rule_based", "dynamic")


def _policy_labels() -> dict[str, str]:
    return {"static": "Static", "rule_based": "Rule-based", "dynamic": "Dynamic"}


def chart_policy_grouped_bar(
    df: pd.DataFrame,
    *,
    value_col: str,
    y_title: str,
    title: str,
    scenarios: list[str] | None = None,
) -> go.Figure:
    """One grouped bar per scenario on x-axis; policies as traces."""
    sub = df.copy()
    if scenarios is not None:
        sub = sub[sub["scenario"].isin(scenarios)]
    scen_list = list(sub["scenario"].unique())
    fig = go.Figure()
    labels = _policy_labels()
    for pol in POLICY_ORDER:
        vals = []
        for s in scen_list:
            row = sub[(sub["scenario"] == s) & (sub["policy"] == pol)]
            vals.append(float(row[value_col].iloc[0]) if len(row) else 0.0)
        fig.add_trace(
            go.Bar(
                name=labels[pol],
                x=[s.replace("_", " ") for s in scen_list],
                y=vals,
                marker_color=POLICY_COLORS[pol],
            )
        )
    fig.update_layout(
        barmode="group",
        title=title,
        yaxis_title=y_title,
        xaxis_tickangle=-35,
        template="plotly_white",
        legend_orientation="h",
        legend_yanchor="bottom",
        legend_y=1.02,
        legend_xanchor="right",
        legend_x=1,
        margin=dict(l=40, r=20, t=60, b=100),
        height=420,
    )
    return fig


def chart_one_metric_three_policies(
    df: pd.DataFrame,
    scenario: str,
    *,
    value_col: str,
    y_title: str,
    title: str,
) -> go.Figure | None:
    """Single metric, three bars (one per policy) for one scenario."""
    sub = df[df["scenario"] == scenario]
    labels = _policy_labels()
    xs: list[str] = []
    ys: list[float] = []
    colors: list[str] = []
    for pol in POLICY_ORDER:
        r = sub[sub["policy"] == pol]
        if r.empty:
            continue
        xs.append(labels[pol])
        ys.append(float(r.iloc[0][value_col]))
        colors.append(POLICY_COLORS[pol])
    if not xs:
        return None
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=colors, showlegend=False))
    fig.update_layout(
        title=title,
        yaxis_title=y_title,
        template="plotly_white",
        height=360,
    )
    return fig


def chart_fare_trajectories(traj: pd.DataFrame, scenario: str) -> go.Figure | None:
    sub = traj[traj["scenario"] == scenario]
    if sub.empty:
        return None
    fig = go.Figure()
    for pol in ("rule_based", "dynamic"):
        t = sub[sub["policy"] == pol]
        if t.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=t["sales_day"],
                y=t["fare"],
                mode="lines",
                name="Rule-based" if pol == "rule_based" else "Dynamic",
                line=dict(width=2, color=POLICY_COLORS[pol]),
            )
        )
    fig.update_layout(
        title=f"Representative fare paths — {scenario.replace('_', ' ')}",
        xaxis_title="Sales day (1 = start of horizon)",
        yaxis_title="Fare ($)",
        template="plotly_white",
        height=400,
        legend_orientation="h",
        legend_y=1.1,
    )
    return fig


def chart_denied_boardings_histogram(run_df: pd.DataFrame, scenario: str) -> go.Figure | None:
    sub = run_df[run_df["scenario"] == scenario]
    if sub.empty:
        return None
    fig = go.Figure()
    labels = _policy_labels()
    for pol in POLICY_ORDER:
        vals = sub[sub["policy"] == pol]["denied_boardings"]
        if vals.empty:
            continue
        mx = int(vals.max()) if len(vals) else 0
        fig.add_trace(
            go.Histogram(
                x=vals,
                name=labels[pol],
                opacity=0.55,
                marker_color=POLICY_COLORS[pol],
                nbinsx=max(8, mx + 2),
            )
        )
    fig.update_layout(
        barmode="overlay",
        title=f"Denied boardings per run — {scenario.replace('_', ' ')}",
        xaxis_title="Denied count",
        yaxis_title="Runs",
        template="plotly_white",
        height=400,
    )
    return fig


def chart_profit_histogram(run_df: pd.DataFrame, scenario: str) -> go.Figure | None:
    sub = run_df[run_df["scenario"] == scenario]
    if sub.empty:
        return None
    fig = go.Figure()
    labels = _policy_labels()
    for pol in POLICY_ORDER:
        vals = sub[sub["policy"] == pol]["profit"]
        if vals.empty:
            continue
        fig.add_trace(
            go.Histogram(
                x=vals,
                name=labels[pol],
                opacity=0.55,
                marker_color=POLICY_COLORS[pol],
                nbinsx=20,
            )
        )
    fig.update_layout(
        barmode="overlay",
        title=f"Profit distribution (Monte Carlo) — {scenario.replace('_', ' ')}",
        xaxis_title="Profit ($)",
        yaxis_title="Runs",
        template="plotly_white",
        height=400,
    )
    return fig


