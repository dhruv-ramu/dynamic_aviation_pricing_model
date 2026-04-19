# Validation summary

Auto-generated from validation CSVs. **Interpretation:** paired policy comparisons use the same run index across policies but **different RNG streams** (policy seed blocks), so per-run “wins” are indicative—not a common random path experiment.

## Seed sensitivity
- **2** (scenario, seed) cells where seed ≠ 2026 and winner differs from the reference run at seed 2026.

## Winner consistency (per-run)
- Scenarios with **max win_rate below 0.45** (no policy dominates run-by-run): business_heavy.

## Dynamic vs rule-based (paired difference of profits)
- Scenarios where **95% CI for (dynamic − rule) excludes zero**: strong_demand, overbook_bump_stress.

## Scenario perturbations
- Perturbations with **same winner** as baseline: **5 / 6**.

## Monte Carlo stability (prefix lengths)
- Scenario×n rows where **winner at n ≠ winner at n=500**: **1**.

## Strongest vs weakest claims
- **Strongest:** scenarios where paired CI excludes zero and perturbations preserve the winner.
- **Weakest / borderline:** high per-run tie counts, seed flips, or winner changes between n=50 and n=500.
