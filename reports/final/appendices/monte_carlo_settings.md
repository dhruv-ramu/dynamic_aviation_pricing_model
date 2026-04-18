# Monte Carlo settings

- `n_runs`: **100**
- `BASE_SEED` (policy blocks): **2026**
- Per-policy `seed_block`: `2026 + policy_index * 1_000_003`
- Per-run RNG: `default_rng(seed_block + run_id)` for `run_id` in `0..99`
- Policies: static, rule_based, dynamic
- Scenarios: baseline, weak_demand, strong_demand, very_strong_late_demand, high_no_show, low_no_show, business_heavy, leisure_heavy, higher_overbooking, overbook_bump_stress, strong_competitor_pressure
