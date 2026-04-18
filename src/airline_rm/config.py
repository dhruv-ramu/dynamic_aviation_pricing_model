"""YAML configuration loading and the primary simulation configuration model."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from airline_rm.types import SimulationConfig

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


def _coerce_simulation_config(raw: Mapping[str, Any]) -> SimulationConfig:
    try:
        fare_buckets = raw["fare_buckets"]
        if not isinstance(fare_buckets, (list, tuple)) or not fare_buckets:
            raise TypeError("fare_buckets must be a non-empty list of numbers")
        buckets = tuple(float(x) for x in fare_buckets)

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
            route_origin=str(raw.get("route_origin", "UNK")),
            route_destination=str(raw.get("route_destination", "UNK")),
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
    return _coerce_simulation_config(raw)
