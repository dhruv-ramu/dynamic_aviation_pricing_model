# Scenario definitions

## `baseline`

- **Overrides**: none (baseline)

- **Intent**: baseline stress-test.

## `weak_demand`

- **Overrides**: `{'expected_total_demand': 168.0, 'demand_multiplier': 0.93}`

- **Intent**: weak demand stress-test.

## `strong_demand`

- **Overrides**: `{'expected_total_demand': 255.0, 'demand_multiplier': 1.12}`

- **Intent**: strong demand stress-test.

## `very_strong_late_demand`

- **Overrides**: `{'expected_total_demand': 238.0, 'demand_multiplier': 1.1, 'booking_curve_midpoint': 11.0, 'booking_curve_steepness': 0.56, 'late_business_share': 0.5, 'segment_transition_midpoint_days': 11.0, 'segment_transition_steepness': 0.3}`

- **Intent**: late-demand-heavy stress-test.

## `high_no_show`

- **Overrides**: `{'no_show_mean': 0.19}`

- **Intent**: no-show-heavy stress-test.

## `low_no_show`

- **Overrides**: `{'no_show_mean': 0.04}`

- **Intent**: no-show-light stress-test.

## `business_heavy`

- **Overrides**: `{'early_business_share': 0.22, 'late_business_share': 0.68, 'segment_transition_midpoint_days': 16.0, 'segment_transition_steepness': 0.22}`

- **Intent**: business-heavy mix stress-test.

## `leisure_heavy`

- **Overrides**: `{'early_business_share': 0.06, 'late_business_share': 0.38, 'segment_transition_midpoint_days': 12.0, 'segment_transition_steepness': 0.2}`

- **Intent**: leisure-heavy mix stress-test.

## `higher_overbooking`

- **Overrides**: `{'overbooking_limit_pct': 0.09}`

- **Intent**: higher overbooking cap stress-test.

## `overbook_bump_stress`

- **Overrides**: `{'expected_total_demand': 268.0, 'demand_multiplier': 1.14, 'overbooking_limit_pct': 0.125, 'no_show_mean': 0.045, 'booking_curve_midpoint': 14.0, 'booking_curve_steepness': 0.5}`

- **Intent**: bump-stress stress-test.

## `strong_competitor_pressure`

- **Overrides**: `{'competitor_mode': 'reactive', 'competitor_base_offset': -32.0, 'competitor_noise_std': 7.0, 'competitor_match_threshold': 14.0, 'competitor_response_strength': 0.55}`

- **Intent**: competitor-heavy stress-test.
