# Methodology (short)

**Simulator:** single flight, discrete booking days, stochastic arrivals, segment mix (business/leisure),
fare buckets, no-shows at departure, optional overbooking with denied-boarding costs. One simulation run
yields bookings, revenues, costs, and profit.

**Policies:** static (fixed bucket), rule-based (time/load thresholds + mild competitor response),
dynamic (pace/scarcity/demand-pressure heuristic).

**Scenarios:** named YAML-style overrides on a common base route (11 presets in this export).

**Monte Carlo:** `n_runs=100`, policy RNG blocks `seed = 2026 + policy_index×1_000_003`, run index
`0…n−1`. Metrics are per-run from `compute_metrics`, then averaged unless noted.

**Fare path figures:** one representative run per policy (profit closest to that policy’s mean profit), same
convention as the full report export.
