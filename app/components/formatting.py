"""Display helpers: currency, percentages, scenario labels."""

from __future__ import annotations


def fmt_usd(n: float, *, decimals: int = 0) -> str:
    return f"${n:,.{decimals}f}"


def fmt_pct_share(x: float, *, decimals: int = 1) -> str:
    """Format a 0–1 fraction as percent."""
    return f"{100.0 * x:.{decimals}f}%"


def scenario_title(slug: str) -> str:
    return slug.replace("_", " ").title()


def policy_label(slug: str) -> str:
    return {"static": "Static", "rule_based": "Rule-based", "dynamic": "Dynamic"}.get(slug, slug)
