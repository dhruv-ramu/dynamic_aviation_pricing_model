"""YAML configuration loading and the primary simulation configuration model."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from airline_rm.types import BookingCurveTypeName, SimulationConfig

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


def _coerce_simulation_config(raw: Mapping[str, Any]) -> SimulationConfig:
    try:
        fare_buckets = raw["fare_buckets"]
        if not isinstance(fare_buckets, (list, tuple)) or not fare_buckets:
            raise TypeError("fare_buckets must be a non-empty list of numbers")
        buckets = tuple(float(x) for x in fare_buckets)

        booking_curve_type = _parse_booking_curve_type(str(raw["booking_curve_type"]))

        demand_stochastic = bool(raw.get("demand_stochastic", True))

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
            competitor_mode=str(raw["competitor_mode"]),
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
