# Final report artifact bundle

Generated for **Monte Carlo**: `n_runs=100`, `seed_block = 2026 + policy_index*1_000_003` (same as `compare_policies_monte_carlo`), `SimulationConfig.rng_seed=2026` after scenario apply.

## Regenerate

```bash
cd airline_rm_project
PYTHONPATH=src python -m airline_rm.evaluation.final_report_export
```

## Trajectory convention

Fare trajectory figures and `raw_exports/fare_trajectories_sampled.csv` use, **per policy**, the run whose realized **profit** is closest to that policy's mean profit (`trajectory_id` / `representative_run_id`). Rule-based and dynamic may use **different** run indices.

## Complete file inventory

- `README.md`
- `appendices/monte_carlo_settings.md`
- `appendices/policy_descriptions.md`
- `appendices/reproducibility.md`
- `appendices/scenario_matrix_full.md`
- `assumptions_and_limitations.md`
- `executive_summary.md`
- `figures/booking_vs_boarded_load_factor__baseline.png`
- `figures/booking_vs_boarded_load_factor__overbook_bump_stress.png`
- `figures/booking_vs_boarded_load_factor__strong_demand.png`
- `figures/booking_vs_boarded_load_factor__very_strong_late_demand.png`
- `figures/denied_boarding_distribution__overbook_bump_stress.png`
- `figures/fare_trajectory_rule_vs_dynamic__baseline.png`
- `figures/fare_trajectory_rule_vs_dynamic__overbook_bump_stress.png`
- `figures/fare_trajectory_rule_vs_dynamic__strong_demand.png`
- `figures/fare_trajectory_rule_vs_dynamic__very_strong_late_demand.png`
- `figures/profit_delta_vs_static.png`
- `figures/profit_distribution__baseline.png`
- `figures/profit_distribution__overbook_bump_stress.png`
- `figures/profit_distribution__strong_demand.png`
- `figures/profit_distribution__very_strong_late_demand.png`
- `figures/scenario_policy_bump_risk.png`
- `figures/scenario_policy_mean_avg_fare.png`
- `figures/scenario_policy_mean_boarded_load_factor.png`
- `figures/scenario_policy_mean_denied_boardings.png`
- `figures/scenario_policy_mean_profit.png`
- `figures/scenario_policy_mean_revenue.png`
- `key_findings.md`
- `methodology.md`
- `raw_exports/fare_trajectories_sampled.csv`
- `raw_exports/run_level_results_full.csv`
- `raw_exports/scenario_policy_results_full.csv`
- `scenario_definitions.md`
- `tables/bump_risk_table.csv`
- `tables/config_snapshot_base.yaml`
- `tables/config_snapshot_effective_by_scenario.csv`
- `tables/metric_definitions.csv`
- `tables/policy_results_by_scenario.csv`
- `tables/profit_delta_vs_static.csv`
- `tables/scenario_summary_table.csv`
- `tables/segment_mix_table.csv`
- `tables/winner_table.csv`