"""Utility helpers for reading and writing PriceSentry configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

CONFIG_PATH = Path("config/config.yaml")


def write_config(config: Dict[str, Any], path: Path = CONFIG_PATH) -> None:
    """Persist the configuration dictionary to disk as YAML."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            config,
            fh,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
        )
