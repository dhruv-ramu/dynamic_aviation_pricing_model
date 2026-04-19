from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components import data_loader
from components.text_blocks import credibility_footer
from components.ui import render_sidebar_glossary

st.set_page_config(page_title="Methodology & limitations", page_icon="✈️", layout="wide")
render_sidebar_glossary()

st.title("Methodology and limitations")
st.markdown(
    "This page exists to keep the demo **credible**: what was simulated, how scenarios were built, and what the "
    "model is **not** claiming to do."
)

method = data_loader.load_markdown("methodology.md")
assum = data_loader.load_markdown("assumptions_and_limitations.md")
repro = data_loader.load_markdown("appendices/reproducibility.md")
mc = data_loader.load_markdown("appendices/monte_carlo_settings.md")

tabs = st.tabs(["Methodology", "Assumptions & limits", "Monte Carlo", "Reproducibility"])
with tabs[0]:
    if method:
        st.markdown(method)
    else:
        st.warning("`methodology.md` not found in `reports/final`.")
with tabs[1]:
    if assum:
        st.markdown(assum)
    else:
        st.warning("`assumptions_and_limitations.md` not found.")
with tabs[2]:
    if mc:
        st.markdown(mc)
    else:
        st.warning("`appendices/monte_carlo_settings.md` not found.")
with tabs[3]:
    if repro:
        st.markdown(repro)
    else:
        st.warning("`appendices/reproducibility.md` not found.")

st.subheader("Where the charts and tables came from")
st.markdown(
    """
Tables and figures are produced by the repository’s **`final_report_export`** pipeline into:

`airline_rm_project/reports/final/`

This app **reads** those artifacts. If you change simulator code, regenerate the bundle so the UI stays aligned.
"""
)

st.markdown(credibility_footer())
