"""Shared Streamlit layout: sidebar glossary and artifact status."""

from __future__ import annotations

import streamlit as st

from components import data_loader
from components.text_blocks import GLOSSARY


def render_sidebar_glossary() -> None:
    st.sidebar.markdown("### Explore")
    st.sidebar.caption("Use **Scenarios & findings** for the interactive scenario picker.")
    status = data_loader.artifact_status()
    if not status["exists"]:
        st.sidebar.error("Report bundle not found.")
        st.sidebar.code(str(status["root"]), language="text")
    elif status["missing"]:
        st.sidebar.warning("Some expected artifacts are missing:")
        for m in status["missing"][:8]:
            st.sidebar.text(m)
        if len(status["missing"]) > 8:
            st.sidebar.caption(f"+ {len(status['missing']) - 8} more")
    else:
        st.sidebar.success("Loaded `reports/final` bundle.")

    with st.sidebar.expander("Glossary (quick definitions)"):
        for term, expl in GLOSSARY.items():
            st.markdown(f"**{term}**")
            st.caption(expl)
    return None
