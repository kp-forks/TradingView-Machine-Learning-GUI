from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_DEFAULTS: dict[str, Any] = {
    "exchange": "NASDAQ",
    "timeframe": "1h",
    "session": "regular",
    "adjustment": "splits",
    "initial_capital": 100_000,
    "data_dir": "data",
    "output_dir": "results",
    "optimization": {
        "search_method": "grid",
        "n_trials": 200,
        "objective": "net_profit_pct",
        "top_n": 10,
        "fine_factor": 2,
        "sl_range": {"min": 1.0, "max": 15.0, "step": 0.5},
        "tp_range": {"min": 1.0, "max": 15.0, "step": 0.5},
    },
}

_SEARCH_PATHS = [
    Path("config.json"),
    Path("hyperview.json"),
]


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from a JSON file, falling back to built-in defaults."""
    config = _deep_copy(_DEFAULTS)
    file_path = _resolve_config_path(path)
    if file_path is not None:
        with open(file_path, encoding="utf-8") as fh:
            user_config = json.load(fh)
        _deep_merge(config, user_config)
    return config


def _resolve_config_path(path: str | Path | None) -> Path | None:
    if path is not None:
        candidate = Path(path)
        if candidate.is_file():
            return candidate
        raise FileNotFoundError(f"Config file not found: {candidate}")
    for candidate in _SEARCH_PATHS:
        if candidate.is_file():
            return candidate
    return None


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _deep_copy(obj: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(obj))
