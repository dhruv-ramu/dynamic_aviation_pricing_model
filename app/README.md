# Airline RM — Streamlit explainer

Polished local web UI for recruiters and analytics-minded readers. It reads **pre-generated** artifacts from:

`airline_rm_project/reports/final/`

## Prerequisite

Generate (or refresh) the final report bundle:

```bash
cd airline_rm_project
PYTHONPATH=src python -m airline_rm.evaluation.final_report_export
```

## Setup

From the **workspace root** (the folder that contains both `app/` and `airline_rm_project/`):

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r app/requirements.txt
```

## Run

```bash
streamlit run app/streamlit_app.py
```

Streamlit opens a browser tab at `http://localhost:8501` by default.

## Layout

| Path | Role |
|------|------|
| `streamlit_app.py` | Home / entry + headline metrics |
| `pages/` | Multi-page walkthrough (overview → methodology) |
| `components/data_loader.py` | Paths to `reports/final`, safe CSV/MD/image loading |
| `components/charts.py` | Plotly charts from CSVs (fallbacks if PNGs missing) |
| `components/text_blocks.py` | Project-specific narrative |
| `components/ui.py` | Sidebar glossary + artifact status |

## Notes

- The app assumes the workspace layout: `app/` and `airline_rm_project/` are **siblings**.
- If a figure or markdown file is missing, the UI shows a **warning** and uses **Plotly fallbacks** from CSVs where possible.
