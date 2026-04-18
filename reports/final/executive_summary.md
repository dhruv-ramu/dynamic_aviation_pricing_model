            # Executive summary — factual bullets for the report writer

            ## Strongest findings (quantitative)

            - Winner counts across scenarios (by mean profit):  
            ```
            winner
rule_based    8
dynamic       3
            ```
            - Largest **dynamic minus rule_based** mean-profit gap (scenario: `overbook_bump_stress`): **9,838.41** USD.
            - Most negative dynamic vs rule gap (`baseline`): **-929.20** USD.

            ## Surprising / scenario-dependent

            - `overbook_bump_stress`: compare **bump_risk** and **mean_denied_boardings** across policies in `tables/bump_risk_table.csv` — static vs dynamic pricing interacts with sell-up and IDB costs differently than mid-fare heuristics.
            - `strong_competitor_pressure` + reactive competitor: check fare and profit deltas vs baseline.

            ## Weakest / most uncertain

            - Single-leg, synthetic demand and WTP — not an econometric fit to a real market.
            - Fare trajectories are **single representative runs** per policy, not ensemble bands.
            - No network spill, no multi-leg, no government policy shocks.
