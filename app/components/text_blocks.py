"""Project-specific narrative copy (plain English, tied to this simulator)."""

from __future__ import annotations

GLOSSARY: dict[str, str] = {
    "Load factor": "How full the flight is, as a share of physical seats. "
    "We show **accepted booking** load (tickets sold) and **boarded** load (people who fly)—they differ when "
    "there are no-shows or denied boardings.",
    "Fare bucket": "A discrete price level the airline can quote (from a small menu of fares), not a continuous "
    "dial. Policies move between buckets over the booking horizon.",
    "Willingness to pay (WTP)": "The maximum fare a traveler would accept. If the quoted fare is above their WTP, "
    "they do not book.",
    "No-show": "A passenger who bought a ticket but does not show up at departure. That frees a seat—but if the "
    "airline oversold, show-ups can still exceed seats.",
    "Denied boarding (bump)": "When more passengers show up than there are seats, some travelers may be denied "
    "boarding. The model charges compensation and goodwill costs.",
    "Bump risk": "The fraction of Monte Carlo runs where at least one denied boarding happened. It is a simple "
    "tail-risk indicator, not a probability forecast for a real airline.",
    "Booking rate": "Accepted bookings divided by the **booking limit** (which can exceed cabin seats when "
    "overbooking is allowed).",
}


def home_intro() -> str:
    return """
This project is a **single-flight revenue management (RM) simulator**: a stylized airline sells tickets over a
booking horizon, faces uncertain demand, and earns profit after operating and bump-related costs.

We compare **three pricing policies** across **eleven demand and operations scenarios** using Monte Carlo runs.
The headline result is **regime-dependent**: no policy wins in every environment—what “good pricing” means depends
on demand strength, mix, competitor pressure, and how aggressively the airline fills the plane.
"""


def rm_problem_plain() -> str:
    return """
Airlines must decide **what fare to offer each day** while seats are still available. Sell too cheap early, and you
leave money on the table. Push prices up too hard, and bookings stall. If you **oversell** to hedge no-shows, you
can raise revenue—but you may pay steep costs if too many passengers show up.

**Revenue management** is the discipline of balancing those tradeoffs under uncertainty. This project does not
solve a real network—instead, it builds a transparent simulator so we can **stress-test policies** and see when
simple rules beat—or lose to—adaptive control.
"""


def navigation_hint() -> str:
    return """
Use the **sidebar** (or the pages menu) to move through the story:

1. **Project overview** — context and headline results  
2. **How the model works** — what the simulator actually does, step by step  
3. **Policies** — static vs rule-based vs dynamic  
4. **Scenarios & findings** — interactive results  
5. **Overbooking stress test** — bump risk in plain English  
6. **Methodology & limitations** — how runs were produced and what we did *not* model  
"""


def model_steps_numbered() -> str:
    return """
1. **Calendar**: The simulation runs day-by-day from the start of the booking horizon until departure.
2. **Travelers**: Each day, potential travelers arrive (business vs leisure mix can shift over time).
3. **Fare**: The active policy picks a **fare bucket** (a discrete price).
4. **Purchase**: Travelers compare the fare to their **willingness to pay**; some book, some walk.
5. **Capacity**: The airline stops selling when it hits a **booking limit** that may exceed cabin seats
   (overbooking).
6. **Departure**: **No-shows** are realized. If show-ups exceed physical seats, **denied boardings** occur and
   costs apply.
7. **Profit**: Ticket revenue plus simple ancillary revenue minus operating and bump-related costs.
"""


def architecture_md() -> str:
    return """
```text
Config (route + behavior parameters)
        │
        ▼
┌───────────────────┐     random arrivals / WTP / no-shows
│  Booking loop     │◄──────────────────────────────────
│  (day-by-day)     │
└─────────┬─────────┘
          │ quoted fare from policy
          ▼
┌───────────────────┐
│  Policy           │  static │ rule-based │ dynamic
└─────────┬─────────┘
          ▼
   Flight result: bookings, fares, loads, bumps, profit
```
"""


def policy_when_wins_intro() -> str:
    return (
        "The table below is derived from **mean profit** in the final Monte Carlo export "
        "(`policy_results_by_scenario.csv`). Use it as a compact map of **which policy led on average** "
        "in each preset environment."
    )


def overbooking_plain() -> str:
    return """
**Overbooking** means the airline may accept **more bookings than seats**, expecting some passengers not to show up.
If too many show up, the flight is **over capacity** at the gate: the model applies **denied boarding** counts and
costs (compensation + goodwill).

**Bump risk** here means: “In what share of simulation runs did we see at least one denied boarding?” It is useful
for comparing policies **inside this simulator**—not a forecast for a real operation.
"""


def credibility_footer() -> str:
    return """
Results are **illustrative**: parameters come from merged YAML presets rather than an airline’s proprietary data.
The value of the project is **clear comparative dynamics**—when adaptation helps, when simple rules suffice, and
when operational tail risk dominates—not a calibrated production forecaster.
"""
