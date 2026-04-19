"""Resolve paths to ``reports/final`` and load CSV / markdown / images safely."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def app_dir() -> Path:
    """Directory containing ``streamlit_app.py`` (the ``app/`` folder)."""
    return Path(__file__).resolve().parent.parent


def workspace_root() -> Path:
    """Repo workspace root (parent of ``app/``)."""
    return app_dir().parent


def reports_final_root() -> Path:
    """Path to ``airline_rm_project/reports/final``."""
    return workspace_root() / "airline_rm_project" / "reports" / "final"


def tables_dir() -> Path:
    return reports_final_root() / "tables"


def figures_dir() -> Path:
    return reports_final_root() / "figures"


def appendices_dir() -> Path:
    return reports_final_root() / "appendices"


def raw_exports_dir() -> Path:
    return reports_final_root() / "raw_exports"


def artifact_status() -> dict[str, Any]:
    root = reports_final_root()
    out: dict[str, Any] = {"root": str(root), "exists": root.is_dir(), "missing": []}
    if not root.is_dir():
        out["missing"].append(str(root))
        return out
    expected = [
        tables_dir() / "policy_results_by_scenario.csv",
        tables_dir() / "winner_table.csv",
        tables_dir() / "scenario_summary_table.csv",
        tables_dir() / "bump_risk_table.csv",
        figures_dir() / "scenario_policy_mean_profit.png",
        raw_exports_dir() / "run_level_results_full.csv",
    ]
    for p in expected:
        if not p.is_file():
            out["missing"].append(str(p.relative_to(workspace_root())))
    return out


def load_csv(name: str, *, subdir: str = "tables") -> pd.DataFrame | None:
    base = reports_final_root() / subdir / name
    if not base.is_file():
        return None
    try:
        return pd.read_csv(base)
    except Exception:
        return None


def load_markdown(rel: str) -> str | None:
    """``rel`` is relative to ``reports/final``, e.g. ``methodology.md``."""
    p = reports_final_root() / rel
    if not p.is_file():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return None


def figure_path(filename: str) -> Path | None:
    p = figures_dir() / filename
    return p if p.is_file() else None
