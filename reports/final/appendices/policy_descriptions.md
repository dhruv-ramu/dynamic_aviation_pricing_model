# Policy descriptions (plain English)

## static
Quotes a fixed fare bucket for the entire horizon (default: highest bucket). Does not react to load, time, or competitor. Useful as a high-list-price baseline.

## rule_based
Maps time-to-departure and seat slack to a fare bucket using transparent thresholds, then applies a mild competitor undercut response. Designed to mimic a simple revenue-management playbook.

## dynamic
Stateful controller: yesterday’s bucket carries forward. Each day adjusts using compact scores for booking pace vs the curve, physical-seat scarcity, and residual demand pressure vs seats left. Competitor influence is capped and muted late in the horizon. Aims for profit-oriented seat protection rather than pure load-chasing.
