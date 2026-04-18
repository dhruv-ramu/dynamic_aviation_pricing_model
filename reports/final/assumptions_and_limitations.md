# Assumptions and limitations

- **Synthetic calibration**: route YAML is illustrative, not fitted to a carrier PNR extract.
- **Demand / WTP**: logistic booking curve, Poisson arrivals (if stochastic), segment mix, and lognormal WTP draws are stylized approximations.
- **Scenario dependence**: results are conditional on discrete presets; small parameter shifts can reorder winners.
- **Overbooking realism**: fixed percentage cap on accepted bookings vs cabin; no re-accommodation, no voluntary denied boarding modeling.
- **No network effects**: isolated leg; no connecting traffic or hub gate constraints.
- **No industrial optimization**: policies are heuristics, not a CDLP/DP/choice-optimizer benchmark.
