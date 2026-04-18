# Reproducibility

From the `airline_rm_project` directory:

```bash
PYTHONPATH=src python -m airline_rm.evaluation.final_report_export
```

This overwrites `reports/final/` tables, figures, markdown, and raw exports using the committed simulator code and `configs/base_config.yaml`.
