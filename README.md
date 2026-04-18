# airline_rm_project

Modular, source-backed **simulation engine** for short-haul U.S. domestic airline **revenue management** (single-leg focus, roughly 300–800 miles). The codebase is organized for extension into stochastic demand, dynamic fare policies, disruption costs, and policy comparison—not for training machine learning models or serving a web UI.

## What this is

- A typed Python package (`airline_rm`) with a clear pipeline: **config → environment entities → pricing policy → simulation → metrics**.
- Phase 1 provides YAML-driven configuration, core datamodels, a **minimal static fare policy**, a **placeholder demand loop**, transparent **KPI metrics**, and a **CLI** to run one experiment end-to-end.

## What this is not (yet)

- Not a dataset project, notebook-first workflow, or RL training stack.
- No live fare scraping, databases, Streamlit frontends, or Docker orchestration.
- No full stochastic demand system, booking curves, willingness-to-pay, no-show draws, overbooking optimization, or competitor reaction models (those are explicitly deferred).

## Repository layout

- `configs/` — YAML parameters (`base_config.yaml` extends `route_shorthaul_default.yaml`).
- `src/airline_rm/` — package code (`entities`, `demand`, `pricing`, `revenue`, `cost`, `simulation`, `evaluation`, `utils`, `cli`).
- `tests/` — `pytest` coverage for config, entities, engine, metrics.
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
pytest
```

### Packaging note

Sources live under `src/airline_rm/` (src layout). Install with `pip install -e .` so `python -m airline_rm.cli.run_experiment` resolves cleanly without manual `PYTHONPATH` edits.

## Roadmap (later phases)

- Replace placeholder demand with calibrated booking arrivals, segment mix, and conversion.
- Add stochastic no-shows, overbooking limits, denied boarding costs, and richer ancillary models.
- Implement dynamic and competitor-aware policies plus Monte Carlo runners and policy comparison tables.

## License

TBD — add a license file when you publish the portfolio version.
