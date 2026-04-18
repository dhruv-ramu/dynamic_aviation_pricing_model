# airline_rm_project

Modular, source-backed **simulation engine** for short-haul U.S. domestic airline **revenue management** (single-leg focus, roughly 300–800 miles). The codebase is organized for extension into stochastic demand, dynamic fare policies, disruption costs, and policy comparison—not for training machine learning models or serving a web UI.

## What this is

- A typed Python package (`airline_rm`) with a clear pipeline: **config → environment entities → pricing policy → simulation → metrics**.
- Phase 1 provides YAML-driven configuration, core datamodels, and a **minimal static fare policy**.
- **Phase 2 demand** adds a modular stochastic demand path: **logistic booking curve** (time-varying arrival intensity), **Poisson daily arrivals**, **segment mix** (leisure-early / business-late logistic), **lognormal willingness-to-pay** (USD mean/std), and **threshold conversion** vs the quoted fare.
- **Phase 3 pricing** adds a **sorted fare-bucket ladder**, **static** (fixed bucket), **rule-based** (time/load + mild competitor match), and **dynamic heuristic** (pace vs booking curve + inventory + competitor nudge) policies, plus a simple **competitor fare model** (`none` / `static` / `reactive`). The engine quotes a policy **each day** before simulating arrivals; `evaluation/policy_comparison.compare_default_policies` runs static vs rule-based vs dynamic on the same YAML.

## What this is not (yet)

- Not a dataset project, notebook-first workflow, or RL training stack.
- No live fare scraping, databases, Streamlit frontends, or Docker orchestration.
- No-show realization, overbooking optimization, denied boarding, competitor reaction, dynamic/rule-based pricing, or policy comparison runners are **not** implemented yet.

## Repository layout

- `configs/` — YAML parameters (`base_config.yaml` extends `route_shorthaul_default.yaml`).
- `src/airline_rm/` — package code (`entities`, `demand`, `pricing`, `revenue`, `cost`, `simulation`, `evaluation`, `utils`, `cli`).
- `tests/` — `pytest` coverage for config, entities, demand modules, engine, metrics.
- `notebooks/` — scratch space for validation/debug (not part of the runtime library).
- `data/`, `outputs/` — reserved for future artifacts (kept empty with `.gitkeep` markers).

## Quickstart

Create a virtual environment, install the package in editable mode, then run the CLI from the **project root** (`airline_rm_project/`):

```bash
cd airline_rm_project
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m airline_rm.cli.run_experiment --config configs/base_config.yaml
python -m airline_rm.cli.run_experiment --config configs/base_config.yaml --policy rule_based
pytest
```

### Packaging note

Sources live under `src/airline_rm/` (src layout). Install with `pip install -e .` so `python -m airline_rm.cli.run_experiment` resolves cleanly without manual `PYTHONPATH` edits.

## Roadmap (later phases)

- Calibrate demand parameters to data (optional) and extend conversion (e.g. logit) or ancillary heterogeneity.
- Add stochastic no-shows, overbooking limits, denied boarding costs, and richer ancillary models.
- Implement dynamic and competitor-aware policies plus Monte Carlo runners and policy comparison tables.

## License

TBD — add a license file when you publish the portfolio version.
