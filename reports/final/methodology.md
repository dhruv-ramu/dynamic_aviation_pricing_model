# Methodology

## Simulator and config

- Merged YAML: `configs/base_config.yaml` (extends `route_shorthaul_default.yaml`).
- Full merged snapshot: `tables/config_snapshot_base.yaml`.

## Policies

- **static**: fixed bucket from config (default max fare bucket).
- **rule_based**: time/load heuristic ladder + mild competitor reaction.
- **dynamic**: stateful score controller (pace, scarcity, demand pressure; weak competitor nudge).

## Scenarios

Presets from `airline_rm.simulation.scenario.SCENARIO_PRESETS` applied via `dataclasses.replace`. Effective parameters per scenario: `tables/config_snapshot_effective_by_scenario.csv`.

## Monte Carlo

- Replications: **100** per scenario-policy pair.
- RNG: `numpy.random.default_rng(seed_block + run_id)` with `seed_block = 2026 + policy_index * 1_000_003`, `run_id = 0..99` — matches `run_many` / `compare_policies_monte_carlo` policy separation.
- After scenario overrides, `SimulationConfig.rng_seed` set to **2026** (for any code paths that read it; primary randomness is the injected Generator).

## Aggregated metrics

- Per run: `compute_metrics` on `FlightSimulationResult`.
- Table means: arithmetic mean across runs unless noted.

## Representative fare trajectories

For each scenario and each of **rule_based** and **dynamic**:
1. Re-run the same `100` Monte Carlo block.
2. Choose `representative_run_id = argmin_k |profit_k − mean(profit)|`.
3. Re-simulate once with `Generator(seed_block + representative_run_id)` and export `fare_series`.

Plots overlay both policies’ chosen runs (possibly different `representative_run_id`). See `raw_exports/fare_trajectories_sampled.csv` for long form.
