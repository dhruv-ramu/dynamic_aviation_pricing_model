# Chat / report evidence bundle

Minimal artifacts to support a defensible write-up. **Regenerate** after changing simulator or configs:

```bash
cd airline_rm_project
PYTHONPATH=src python -m airline_rm.evaluation.chat_exp_export
```

| Path | Use |
|------|-----|
| `tables/scenario_policy_results.csv` | Primary numbers: profit, revenue, load, fare, bumps |
| `tables/winner_summary.csv` | Who wins per scenario and key gaps |
| `tables/validation_summary.csv` | Compressed robustness (from `reports/validation/` if present) |
| `tables/config_snapshot.yaml` | Baseline effective parameters |
| `figures/*.png` | One profit chart, three fare overlays, bump-risk bar |
| `raw/minimal_run_sample.csv` | Tiny MC sample for sanity checks |
| `key_results.md` | Bullet factual interpretation |
| `methodology.md` | Short methods blurb |
| `limitations.md` | Honest scope limits |

Monte Carlo: **n_runs=100**, **seed 2026** (policy blocks as in main experiments).
