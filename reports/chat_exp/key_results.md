# Key results (factual)

## Winners by scenario (mean profit)

- **baseline**: `rule_based` (static $14,403; rule $17,698; dynamic $16,769).
- **weak_demand**: `rule_based` (static $8,974; rule $11,664; dynamic $10,900).
- **strong_demand**: `dynamic` (static $22,212; rule $22,046; dynamic $23,393).
- **very_strong_late_demand**: `dynamic` (static $22,254; rule $22,604; dynamic $23,213).
- **high_no_show**: `rule_based` (static $15,024; rule $18,585; dynamic $17,657).
- **low_no_show**: `rule_based` (static $13,984; rule $17,106; dynamic $16,191).
- **business_heavy**: `rule_based` (static $19,536; rule $20,033; dynamic $19,611).
- **leisure_heavy**: `rule_based` (static $12,932; rule $16,965; dynamic $16,110).
- **higher_overbooking**: `rule_based` (static $14,403; rule $17,698; dynamic $16,769).
- **overbook_bump_stress**: `dynamic` (static $23,857; rule $14,277; dynamic $24,116).
- **strong_competitor_pressure**: `rule_based` (static $14,403; rule $17,458; dynamic $16,679).

## Where dynamic leads on mean profit

- `strong_demand` (dynamic − rule = $1,347).
- `very_strong_late_demand` (dynamic − rule = $608).
- `overbook_bump_stress` (dynamic − rule = $9,838).

## Where rule-based leads

- `baseline`.
- `weak_demand`.
- `high_no_show`.
- `low_no_show`.
- `business_heavy`.
- `leisure_heavy`.
- `higher_overbooking`.
- `strong_competitor_pressure`.

## Weak / not statistically significant (dynamic vs rule, paired MC)

- `baseline`: 95% CI on (dynamic−rule) includes zero (see `validation_summary.csv`).
- `weak_demand`: 95% CI on (dynamic−rule) includes zero (see `validation_summary.csv`).
- `very_strong_late_demand`: 95% CI on (dynamic−rule) includes zero (see `validation_summary.csv`).
- `high_no_show`: 95% CI on (dynamic−rule) includes zero (see `validation_summary.csv`).
- `low_no_show`: 95% CI on (dynamic−rule) includes zero (see `validation_summary.csv`).
- `business_heavy`: 95% CI on (dynamic−rule) includes zero (see `validation_summary.csv`).
- `leisure_heavy`: 95% CI on (dynamic−rule) includes zero (see `validation_summary.csv`).
- `higher_overbooking`: 95% CI on (dynamic−rule) includes zero (see `validation_summary.csv`).
- `strong_competitor_pressure`: 95% CI on (dynamic−rule) includes zero (see `validation_summary.csv`).

## overbook_bump_stress

- High denied-boarding cost regime; mean-profit winner and bump_risk differ by policy — see figures and `scenario_policy_results.csv`.
