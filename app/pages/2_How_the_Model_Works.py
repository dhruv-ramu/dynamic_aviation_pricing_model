from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components.text_blocks import architecture_md, model_steps_numbered
from components.ui import render_sidebar_glossary

st.set_page_config(page_title="How the model works", page_icon="✈️", layout="wide")
render_sidebar_glossary()

st.title("How the simulator works")
st.markdown(
    """
The goal of this page is simple: after reading it, someone who is **not** an airline RM specialist should be able
to say: “I understand what is being simulated, step by step.”
"""
)

st.subheader("End-to-end flow (numbered)")
st.markdown(model_steps_numbered())

st.subheader("Architecture (conceptual)")
st.markdown(architecture_md())

with st.expander("Technical detail (optional)"):
    st.markdown(
        """
- **Fare buckets**: discrete prices from configuration—not a continuous price surface.
- **Segments**: business vs leisure travelers with different willingness-to-pay distributions; the mix can shift
  across the horizon.
- **Booking limit**: may exceed physical seats when overbooking is enabled.
- **Monte Carlo**: many independent runs with controlled RNG seeds to summarize mean outcomes and distributions.
        """
    )

st.subheader("Where to go next")
st.markdown(
    "- **Policies** — what static, rule-based, and dynamic actually do.\n"
    "- **Scenarios & findings** — numbers and charts for each stress test.\n"
    "- **Overbooking stress test** — bump risk in plain English."
)
