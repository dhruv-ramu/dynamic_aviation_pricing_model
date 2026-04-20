# LaTeX report

## Build

From this directory:

```bash
pdflatex report.tex
pdflatex report.tex
```

Figures are loaded from `../airline_rm_project/reports/chat_exp/figures/`. Regenerate those PNGs if needed:

```bash
cd ../airline_rm_project
PYTHONPATH=src python -m airline_rm.evaluation.chat_exp_export
```

Requires a TeX distribution with `pdflatex` (e.g. MacTeX, TeX Live, MiKTeX).

## Files

| File | Role |
|------|------|
| `report.tex` | Full report (title → conclusion) |
