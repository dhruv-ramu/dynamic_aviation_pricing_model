from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from components import data_loader
from components.formatting import policy_label
from components.text_blocks import policy_when_wins_intro
from components.ui import render_sidebar_glossary

st.set_page_config(page_title="Policies", page_icon="✈️", layout="wide")
render_sidebar_glossary()

st.title("Pricing policies")
st.markdown(
    """
Three policies share the **same simulator** and **same demand model**—only the **fare path** changes. That makes
comparisons interpretable: differences come from pricing behavior, not from changing the world model per policy.
"""
)

st.subheader("Static")
st.markdown(
    """
**How it works:** keeps a **fixed fare bucket** across the booking horizon (a simple list-price baseline).

**Strengths:** transparent, predictable, and can be surprisingly competitive when high list fares match a
calm demand environment.

**Weaknesses:** cannot respond to fast fill-rates, late demand surges, or competitor pressure; may leave revenue on
the table—or push too hard—depending on the regime.

**Simple intuition:** *“We pick one price and stick with it.”*
"""
)

st.subheader("Rule-based")
st.markdown(
    """
**How it works:** maps **time to departure** and **seat slack** to a fare bucket using fixed thresholds, with a
mild competitor reaction.

**Strengths:** mirrors how many carriers **operationalize** RM—easy to audit and explain.

**Weaknesses:** thresholds are not automatically optimal across environments; in some regimes the rules **overfill**
relative to bump costs.

**Simple intuition:** *“If we are here on the calendar and this full, use this price.”*
"""
)

st.subheader("Dynamic")
st.markdown(
    """
**How it works:** a **stateful controller** adjusts the bucket using signals like booking **pace vs a target curve**,
**physical-seat scarcity**, and **residual demand pressure**; competitor effects are capped and muted late.

**Strengths:** can **reallocate** aggressiveness across days when the booking curve is nonlinear or late demand is
economically important.

**Weaknesses:** more moving parts; still a heuristic—not a full optimization engine.

**Simple intuition:** *“Each day, nudge prices based on how sales are pacing and how many seats are truly left.”*
"""
)

st.subheader("Side-by-side comparison")
comp = pd.DataFrame(
    [
        {
            "Policy": "Static",
            "What moves prices?": "Nothing (fixed bucket).",
            "Best when": "Simple baseline; some stable environments.",
            "Watch out for": "No response to demand spikes or bump-risk buildup.",
        },
        {
            "Policy": "Rule-based",
            "What moves prices?": "Calendar position + load thresholds (+ mild competitor rule).",
            "Best when": "Stable demand; playbook matches environment.",
            "Watch out for": "Rigid thresholds in unfamiliar regimes.",
        },
        {
            "Policy": "Dynamic",
            "What moves prices?": "Pace, scarcity, demand-pressure scores (stateful).",
            "Best when": "Strong/late demand; bump-stress where sell-up needs restraint.",
            "Watch out for": "Harder to explain than a ladder of rules.",
        },
    ]
)
st.dataframe(comp, use_container_width=True, hide_index=True)

st.subheader("When should each policy win?")
st.markdown(policy_when_wins_intro())

winner_df = data_loader.load_csv("winner_table.csv")
policy_df = data_loader.load_csv("policy_results_by_scenario.csv")
if winner_df is None or policy_df is None:
    st.warning("Winner table / policy results not found under `reports/final/tables/`.")
else:
    wcol = winner_df.copy()
    wcol["winner_label"] = wcol["winner"].map(policy_label)
    st.dataframe(
        wcol[["scenario", "winner_label", "mean_profit_static", "mean_profit_rule_based", "mean_profit_dynamic"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "mean_profit_static": st.column_config.NumberColumn("Static profit", format="$%.0f"),
            "mean_profit_rule_based": st.column_config.NumberColumn("Rule profit", format="$%.0f"),
            "mean_profit_dynamic": st.column_config.NumberColumn("Dynamic profit", format="$%.0f"),
        },
    )

    st.markdown("#### Plain-English read")
    dyn_scens = list(winner_df[winner_df["winner"] == "dynamic"]["scenario"])
    rb_scens = list(winner_df[winner_df["winner"] == "rule_based"]["scenario"])
    st.markdown(
        f"- **Dynamic** led (on average) in: **{', '.join(dyn_scens) or '—'}**.\n"
        f"- **Rule-based** led in: **{', '.join(rb_scens) or '—'}**.\n"
        "- **Static** did not take first place in these presets—its role here is primarily a **reference** list fare."
    )

    append = data_loader.load_markdown("appendices/policy_descriptions.md")
    if append:
        with st.expander("Source text from the final report appendices"):
            st.markdown(append)
