"""YAML configuration loading and the primary simulation configuration model."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from airline_rm.types import BookingCurveTypeName, PricingPolicyName, SimulationConfig

REQUIRED_FIELDS: tuple[str, ...] = (
    "booking_horizon_days",
    "route_distance_miles",
    "capacity",
    "base_fare",
    "fare_buckets",
    "business_share_late",
    "leisure_elasticity",
    "business_elasticity",
    "no_show_mean",
    "overbooking_limit_pct",
    "ancillary_mean",
    "casm_ex",
    "fixed_flight_cost",
    "competitor_mode",
    "rng_seed",
    "expected_total_demand",
    "demand_multiplier",
    "booking_curve_type",
    "booking_curve_steepness",
    "booking_curve_midpoint",
    "early_business_share",
    "late_business_share",
    "segment_transition_midpoint_days",
    "segment_transition_steepness",
    "leisure_wtp_mean",
    "leisure_wtp_sigma",
    "business_wtp_mean",
    "business_wtp_sigma",
)


def _merge_shallow(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if key == "extends":
            continue
        merged[key] = value
    return merged


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)

    if loaded is None:
        raise ValueError(f"Config file is empty: {path}")
    if not isinstance(loaded, Mapping):
        raise TypeError(f"Config root must be a mapping, got {type(loaded).__name__} in {path}")

    return dict(loaded)


def _resolve_extends(extends_value: str, relative_to: Path) -> Path:
    candidate = Path(extends_value)
    if not candidate.is_absolute():
        candidate = (relative_to.parent / candidate).resolve()
    return candidate


def load_raw_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML config, recursively applying ``extends`` relative to the file directory."""

    primary = Path(path).expanduser().resolve()
    merged = _load_recursive_config(primary)
    merged.pop("extends", None)
    return merged


def _load_recursive_config(path: Path) -> dict[str, Any]:
    data = _load_yaml_mapping(path)
    extends = data.get("extends")
    if extends is None:
        return dict(data)

    if not isinstance(extends, str) or not extends.strip():
        raise ValueError(f"Invalid 'extends' value in {path}: {extends!r}")

    parent_path = _resolve_extends(extends, path)
    parent = _load_recursive_config(parent_path)
    return _merge_shallow(parent, data)


def _validate_required_fields(raw: Mapping[str, Any], source: Path) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    if missing:
        raise KeyError(
            f"Missing required config keys after loading {source}: {', '.join(missing)}"
        )


def _parse_pricing_policy(value: str) -> PricingPolicyName:
    normalized = str(value).strip().lower()
    allowed = {"static", "rule_based", "dynamic"}
    if normalized not in allowed:
        raise ValueError(f"pricing_policy must be one of {sorted(allowed)}, got {value!r}")
    return normalized  # type: ignore[return-value]


def _parse_competitor_mode(value: str) -> str:
    normalized = str(value).strip().lower()
    allowed = {"none", "static", "reactive"}
    if normalized not in allowed:
        raise ValueError(f"competitor_mode must be one of {sorted(allowed)}, got {value!r}")
    return normalized


def _parse_booking_curve_type(value: str) -> BookingCurveTypeName:
    normalized = str(value).strip().lower()
    if normalized != "logistic":
        raise ValueError(f"booking_curve_type must be 'logistic', got {value!r}")
    return "logistic"


def _validate_simulation_config(cfg: SimulationConfig) -> None:
    """Cross-field sanity checks beyond per-field typing."""

    if cfg.capacity <= 0:
        raise ValueError("capacity must be positive")
    if cfg.booking_horizon_days < 1:
        raise ValueError("booking_horizon_days must be >= 1")
    if cfg.expected_total_demand < 0:
        raise ValueError("expected_total_demand must be non-negative")
    if cfg.demand_multiplier < 0:
        raise ValueError("demand_multiplier must be non-negative")
    if cfg.booking_curve_steepness <= 0:
        raise ValueError("booking_curve_steepness must be positive")
    if cfg.booking_curve_midpoint <= 0:
        raise ValueError("booking_curve_midpoint must be positive")
    if cfg.segment_transition_midpoint_days <= 0:
        raise ValueError("segment_transition_midpoint_days must be positive")
    if cfg.segment_transition_steepness <= 0:
        raise ValueError("segment_transition_steepness must be positive")
    if cfg.leisure_wtp_mean <= 0 or cfg.business_wtp_mean <= 0:
        raise ValueError("WTP means must be positive")
    if cfg.leisure_wtp_sigma < 0 or cfg.business_wtp_sigma < 0:
        raise ValueError("WTP sigma values must be non-negative")
    if cfg.business_wtp_mean < cfg.leisure_wtp_mean:
        raise ValueError("business_wtp_mean should be >= leisure_wtp_mean for a sensible segment ladder")
    if not (0.0 < cfg.early_business_share < 1.0 and 0.0 < cfg.late_business_share < 1.0):
        raise ValueError("business share parameters must lie strictly between 0 and 1")
    if cfg.early_business_share > cfg.late_business_share + 1e-6:
        raise ValueError("early_business_share must be <= late_business_share")
    if cfg.low_load_factor_threshold >= cfg.high_load_factor_threshold:
        raise ValueError("low_load_factor_threshold must be < high_load_factor_threshold")
    if cfg.pace_gap_lower_threshold >= cfg.pace_gap_raise_threshold:
        raise ValueError("pace_gap_lower_threshold must be < pace_gap_raise_threshold")
    if not (0.0 <= cfg.competitor_response_strength <= 1.0):
        raise ValueError("competitor_response_strength should be in [0, 1]")
    max_bucket = len(cfg.fare_buckets) - 1
    if cfg.dynamic_initial_bucket_index is not None and (
        cfg.dynamic_initial_bucket_index < 0 or cfg.dynamic_initial_bucket_index > max_bucket
    ):
        raise ValueError("dynamic_initial_bucket_index out of range for fare_buckets")
    if cfg.dynamic_weight_pace < 0 or cfg.dynamic_weight_scarcity < 0 or cfg.dynamic_weight_demand_pressure < 0:
        raise ValueError("dynamic score weights must be non-negative")
    if not (cfg.dynamic_score_strong_lower < 0 < cfg.dynamic_score_mild_raise < cfg.dynamic_score_strong_raise):
        raise ValueError("dynamic score thresholds must satisfy strong_lower < 0 < mild_raise < strong_raise")
    if cfg.dynamic_bucket_change_deadband < 0:
        raise ValueError("dynamic_bucket_change_deadband must be non-negative")
    if cfg.dynamic_two_step_pace_ratio <= 1.0:
        raise ValueError("dynamic_two_step_pace_ratio must be > 1")
    if not (0.0 < cfg.dynamic_two_step_scarcity_fill <= 1.0):
        raise ValueError("dynamic_two_step_scarcity_fill must lie in (0, 1]")
    if cfg.dynamic_two_step_demand_score < 0:
        raise ValueError("dynamic_two_step_demand_score must be non-negative")
    if not (0.0 <= cfg.dynamic_pace_late_dampen <= 1.0):
        raise ValueError("dynamic_pace_late_dampen must lie in [0, 1]")
    if cfg.dynamic_late_floor_days_until_departure < 0:
        raise ValueError("dynamic_late_floor_days_until_departure must be non-negative")
    if cfg.dynamic_min_bucket_index_late < 0 or cfg.dynamic_late_window_min_bucket_index < 0:
        raise ValueError("dynamic late bucket floors must be non-negative")
    if cfg.dynamic_min_bucket_index_late > max_bucket or cfg.dynamic_late_window_min_bucket_index > max_bucket:
        raise ValueError("dynamic late bucket floor exceeds highest fare bucket index")
    if not (0.0 < cfg.dynamic_scarcity_fill_ratio_1 < cfg.dynamic_scarcity_fill_ratio_2 < 1.0):
        raise ValueError("dynamic scarcity fill thresholds must satisfy 0 < t1 < t2 < 1")
    if cfg.dynamic_demand_pressure_neutral_ratio < 0:
        raise ValueError("dynamic_demand_pressure_neutral_ratio must be non-negative")
    if cfg.dynamic_demand_ratio_score_scale < 0:
        raise ValueError("dynamic_demand_ratio_score_scale must be non-negative")
    if not (0.0 < cfg.dynamic_competitor_disable_fill_ratio <= 1.0):
        raise ValueError("dynamic_competitor_disable_fill_ratio must lie in (0, 1]")
    if cfg.dynamic_competitor_late_ignore_days < 0:
        raise ValueError("dynamic_competitor_late_ignore_days must be non-negative")
    if cfg.dynamic_min_days_between_bucket_changes < 0:
        raise ValueError("dynamic_min_days_between_bucket_changes must be non-negative")
    if cfg.static_bucket_index is not None and (
        cfg.static_bucket_index < 0 or cfg.static_bucket_index >= len(cfg.fare_buckets)
    ):
        raise ValueError("static_bucket_index out of range for fare_buckets")
    if cfg.denied_boarding_compensation_multiplier < 0 or cfg.denied_boarding_compensation_cap < 0:
        raise ValueError("Denied-boarding compensation parameters must be non-negative")
    if cfg.goodwill_penalty_per_bumped_passenger < 0:
        raise ValueError("goodwill_penalty_per_bumped_passenger must be non-negative")
    if cfg.denied_boarding_delay_hours < 0:
        raise ValueError("denied_boarding_delay_hours must be non-negative")
    if not (0.0 <= cfg.no_show_mean <= 1.0):
        raise ValueError("no_show_mean must lie in [0, 1]")
    if cfg.overbooking_limit_pct < 0:
        raise ValueError("overbooking_limit_pct must be non-negative")


def _coerce_simulation_config(raw: Mapping[str, Any]) -> SimulationConfig:
    try:
        bucket_src = raw.get("fare_bucket_values", raw["fare_buckets"])
        if not isinstance(bucket_src, (list, tuple)) or not bucket_src:
            raise TypeError("fare_buckets / fare_bucket_values must be a non-empty list of numbers")
        buckets = tuple(float(x) for x in bucket_src)

        booking_curve_type = _parse_booking_curve_type(str(raw["booking_curve_type"]))

        demand_stochastic = bool(raw.get("demand_stochastic", True))
        pricing_policy = _parse_pricing_policy(str(raw.get("pricing_policy", "static")))
        competitor_mode = _parse_competitor_mode(str(raw["competitor_mode"]))

        static_bucket_raw = raw.get("static_bucket_index")
        static_bucket_index: int | None
        if static_bucket_raw is None or static_bucket_raw == "":
            static_bucket_index = None
        else:
            static_bucket_index = int(static_bucket_raw)

        return SimulationConfig(
            booking_horizon_days=int(raw["booking_horizon_days"]),
            route_distance_miles=float(raw["route_distance_miles"]),
            capacity=int(raw["capacity"]),
            base_fare=float(raw["base_fare"]),
            fare_buckets=buckets,
            business_share_late=float(raw["business_share_late"]),
            leisure_elasticity=float(raw["leisure_elasticity"]),
            business_elasticity=float(raw["business_elasticity"]),
            no_show_mean=float(raw["no_show_mean"]),
            overbooking_limit_pct=float(raw["overbooking_limit_pct"]),
            ancillary_mean=float(raw["ancillary_mean"]),
            casm_ex=float(raw["casm_ex"]),
            fixed_flight_cost=float(raw["fixed_flight_cost"]),
            competitor_mode=competitor_mode,
            rng_seed=int(raw["rng_seed"]),
            expected_total_demand=float(raw["expected_total_demand"]),
            demand_multiplier=float(raw["demand_multiplier"]),
            booking_curve_type=booking_curve_type,
            booking_curve_steepness=float(raw["booking_curve_steepness"]),
            booking_curve_midpoint=float(raw["booking_curve_midpoint"]),
            early_business_share=float(raw["early_business_share"]),
            late_business_share=float(raw["late_business_share"]),
            segment_transition_midpoint_days=float(raw["segment_transition_midpoint_days"]),
            segment_transition_steepness=float(raw["segment_transition_steepness"]),
            leisure_wtp_mean=float(raw["leisure_wtp_mean"]),
            leisure_wtp_sigma=float(raw["leisure_wtp_sigma"]),
            business_wtp_mean=float(raw["business_wtp_mean"]),
            business_wtp_sigma=float(raw["business_wtp_sigma"]),
            route_origin=str(raw.get("route_origin", "UNK")),
            route_destination=str(raw.get("route_destination", "UNK")),
            demand_stochastic=demand_stochastic,
            pricing_policy=pricing_policy,
            early_window_days=int(raw.get("early_window_days", 45)),
            late_window_days=int(raw.get("late_window_days", 14)),
            low_load_factor_threshold=float(raw.get("low_load_factor_threshold", 0.35)),
            high_load_factor_threshold=float(raw.get("high_load_factor_threshold", 0.85)),
            pace_gap_raise_threshold=float(raw.get("pace_gap_raise_threshold", 6.0)),
            pace_gap_lower_threshold=float(raw.get("pace_gap_lower_threshold", -6.0)),
            competitor_base_offset=float(raw.get("competitor_base_offset", -12.0)),
            competitor_noise_std=float(raw.get("competitor_noise_std", 4.0)),
            competitor_match_threshold=float(raw.get("competitor_match_threshold", 12.0)),
            competitor_response_strength=float(raw.get("competitor_response_strength", 0.3)),
            static_bucket_index=static_bucket_index,
            overbooking_enabled=bool(raw.get("overbooking_enabled", True)),
            denied_boarding_delay_hours=float(raw.get("denied_boarding_delay_hours", 2.5)),
            denied_boarding_compensation_multiplier=float(
                raw.get("denied_boarding_compensation_multiplier", 4.0)
            ),
            denied_boarding_compensation_cap=float(raw.get("denied_boarding_compensation_cap", 2150.0)),
            goodwill_penalty_per_bumped_passenger=float(
                raw.get("goodwill_penalty_per_bumped_passenger", 150.0)
            ),
            dynamic_initial_bucket_index=(
                None
                if raw.get("dynamic_initial_bucket_index") in (None, "")
                else int(raw["dynamic_initial_bucket_index"])
            ),
            dynamic_weight_pace=float(raw.get("dynamic_weight_pace", 0.88)),
            dynamic_weight_scarcity=float(raw.get("dynamic_weight_scarcity", 1.22)),
            dynamic_weight_demand_pressure=float(raw.get("dynamic_weight_demand_pressure", 1.62)),
            dynamic_score_strong_raise=float(raw.get("dynamic_score_strong_raise", 1.02)),
            dynamic_score_mild_raise=float(raw.get("dynamic_score_mild_raise", 0.24)),
            dynamic_score_strong_lower=float(raw.get("dynamic_score_strong_lower", -0.88)),
            dynamic_bucket_change_deadband=float(raw.get("dynamic_bucket_change_deadband", 0.32)),
            dynamic_strong_raise_allows_two_steps=bool(
                raw.get("dynamic_strong_raise_allows_two_steps", True)
            ),
            dynamic_two_step_pace_ratio=float(raw.get("dynamic_two_step_pace_ratio", 1.07)),
            dynamic_two_step_scarcity_fill=float(raw.get("dynamic_two_step_scarcity_fill", 0.82)),
            dynamic_two_step_demand_score=float(raw.get("dynamic_two_step_demand_score", 0.72)),
            dynamic_pace_late_dampen=float(raw.get("dynamic_pace_late_dampen", 0.30)),
            dynamic_scarcity_fill_ratio_1=float(raw.get("dynamic_scarcity_fill_ratio_1", 0.68)),
            dynamic_scarcity_fill_ratio_2=float(raw.get("dynamic_scarcity_fill_ratio_2", 0.84)),
            dynamic_demand_pressure_neutral_ratio=float(
                raw.get("dynamic_demand_pressure_neutral_ratio", 0.98)
            ),
            dynamic_demand_ratio_score_scale=float(raw.get("dynamic_demand_ratio_score_scale", 0.92)),
            dynamic_competitor_disable_fill_ratio=float(
                raw.get("dynamic_competitor_disable_fill_ratio", 0.78)
            ),
            dynamic_competitor_late_ignore_days=int(raw.get("dynamic_competitor_late_ignore_days", 12)),
            dynamic_competitor_ignore_if_ahead_of_pace=bool(
                raw.get("dynamic_competitor_ignore_if_ahead_of_pace", True)
            ),
            dynamic_late_floor_days_until_departure=int(
                raw.get("dynamic_late_floor_days_until_departure", 10)
            ),
            dynamic_min_bucket_index_late=int(raw.get("dynamic_min_bucket_index_late", 2)),
            dynamic_late_window_min_bucket_index=int(
                raw.get("dynamic_late_window_min_bucket_index", 3)
            ),
            dynamic_min_days_between_bucket_changes=int(
                raw.get("dynamic_min_days_between_bucket_changes", 0)
            ),
            dynamic_policy_debug=bool(raw.get("dynamic_policy_debug", False)),
        )
    except KeyError as exc:  # pragma: no cover - defensive; validated earlier
        raise KeyError(f"Missing key while building SimulationConfig: {exc}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid config value types or ranges: {exc}") from exc


def load_simulation_config(path: str | Path) -> SimulationConfig:
    """Load ``path`` (with optional ``extends`` chain) into a :class:`SimulationConfig`."""

    resolved = Path(path).expanduser().resolve()
    raw = load_raw_config(resolved)
    _validate_required_fields(raw, resolved)
    cfg = _coerce_simulation_config(raw)
    _validate_simulation_config(cfg)
    return cfg
