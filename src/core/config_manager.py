"""Runtime configuration management for PriceSentry."""

from __future__ import annotations

import copy
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import yaml

from utils.config_io import write_config
from utils.config_validator import ValidationRule, config_validator

CONFIG_PATH = Path("config/config.yaml")

Listener = Callable[["ConfigUpdateEvent"], None]


@dataclass(frozen=True)
class ConfigDiff:
    """Describes changes between two configuration snapshots."""

    changed_keys: Set[str]
    requires_exchange_reload: bool
    requires_symbol_reload: bool


@dataclass(frozen=True)
class ConfigUpdateEvent:
    """Payload emitted after configuration updates."""

    new_config: Dict[str, Any]
    previous_config: Dict[str, Any]
    warnings: List[str]
    diff: ConfigDiff


@dataclass(frozen=True)
class ManagerUpdateResult:
    """Result returned by ConfigManager.update_config."""

    success: bool
    errors: List[str]
    warnings: List[str]
    message: Optional[str]
    diff: Optional[ConfigDiff]
    config: Dict[str, Any]


class ConfigManager:
    """Centralised configuration loader, validator, and notifier."""

    _instance: Optional["ConfigManager"] = None
    _instance_lock = threading.Lock()

    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self._config_path = config_path
        self._lock = threading.RLock()
        self._listeners: List[Listener] = []
        self._config: Dict[str, Any] = {}
        self._last_loaded_at: float = 0.0
        self._load_initial()

    @classmethod
    def instance(cls) -> "ConfigManager":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def subscribe(self, listener: Listener) -> None:
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def unsubscribe(self, listener: Listener) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def get_config(self, *, copy_result: bool = True) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._config) if copy_result else self._config

    def update_config(self, candidate: Dict[str, Any]) -> ManagerUpdateResult:
        """Validate, persist, and broadcast a configuration update."""
        with self._lock:
            normalized = self._normalize(candidate)
            validation = config_validator.validate_config(normalized)

            if not validation.is_valid:
                return ManagerUpdateResult(
                    success=False,
                    errors=validation.errors,
                    warnings=validation.warnings,
                    message="Configuration validation failed",
                    diff=None,
                    config=copy.deepcopy(self._config),
                )

            previous = copy.deepcopy(self._config)

            if previous == normalized:
                diff = ConfigDiff(set(), False, False)
                result = ManagerUpdateResult(
                    success=True,
                    errors=[],
                    warnings=validation.warnings,
                    message="Configuration unchanged",
                    diff=diff,
                    config=previous,
                )
                # Still notify listeners to allow soft refresh behaviour.
                self._notify_listeners(previous, previous, validation.warnings, diff)
                return result

            diff = self._diff(previous, normalized)
            write_config(normalized, path=self._config_path)
            self._config = copy.deepcopy(normalized)
            self._last_loaded_at = time.time()

        # Notify listeners outside lock to avoid deadlocks.
        self._notify_listeners(normalized, previous, validation.warnings, diff)

        return ManagerUpdateResult(
            success=True,
            errors=[],
            warnings=validation.warnings,
            message="Configuration updated successfully",
            diff=diff,
            config=copy.deepcopy(normalized),
        )

    def reload_from_disk(self) -> Dict[str, Any]:
        """Force reload configuration from the YAML file."""
        with self._lock:
            config = self._load_from_disk()
            self._config = copy.deepcopy(config)
            self._last_loaded_at = time.time()
            return copy.deepcopy(self._config)

    def last_loaded_at(self) -> float:
        return self._last_loaded_at

    # Internal helpers -------------------------------------------------

    def _load_initial(self) -> None:
        config = self._load_from_disk()
        validation = config_validator.validate_config(config)
        if not validation.is_valid:
            raise ValueError(
                "Initial configuration failed validation: "
                + "; ".join(validation.errors)
            )
        self._config = copy.deepcopy(config)
        self._last_loaded_at = time.time()

    def _load_from_disk(self) -> Dict[str, Any]:
        if not self._config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self._config_path}")
        with self._config_path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        if not isinstance(raw, dict):
            raise ValueError("Configuration root must be a mapping")
        return self._normalize(raw)

    def _normalize(self, config: Dict[str, Any]) -> Dict[str, Any]:
        normalized = copy.deepcopy(config)
        for key_path, rule in config_validator.rules.items():
            value = config_validator.get_value_by_path(normalized, key_path)
            if value is None:
                continue
            coerced, changed = self._coerce_value(value, rule)
            if changed:
                self._set_value_by_path(normalized, key_path, coerced)
        return normalized

    def _coerce_value(self, value: Any, rule: ValidationRule) -> Tuple[Any, bool]:
        target_type = rule.data_type
        # Handle tuples like (int, float)
        if isinstance(target_type, tuple):
            coerced, changed = self._coerce_numeric_union(value, target_type)
            if changed:
                return coerced, True
        elif target_type is int:
            coerced, changed = self._coerce_int(value)
            if changed:
                return coerced, True
        elif target_type is float:
            coerced, changed = self._coerce_float(value)
            if changed:
                return coerced, True
        elif target_type is bool:
            coerced, changed = self._coerce_bool(value)
            if changed:
                return coerced, True
        elif target_type is list:
            coerced, changed = self._coerce_list(value, rule)
            if changed:
                return coerced, True
        return value, False

    def _coerce_numeric_union(
        self, value: Any, types: Tuple[type, ...]
    ) -> Tuple[Any, bool]:
        if isinstance(value, types):
            return value, False
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return value, False
            try:
                if any(t is float for t in types) and ("." in value or "e" in value.lower()):
                    return float(value), True
                if int in types and (value.lstrip("+-").isdigit()):
                    return int(value), True
                if float in types:
                    return float(value), True
            except ValueError:
                return value, False
        return value, False

    def _coerce_int(self, value: Any) -> Tuple[Any, bool]:
        if isinstance(value, int):
            return value, False
        if isinstance(value, str):
            value = value.strip()
            if value.lstrip("+-").isdigit():
                return int(value), True
            try:
                return int(float(value)), True
            except ValueError:
                return value, False
        return value, False

    def _coerce_float(self, value: Any) -> Tuple[Any, bool]:
        if isinstance(value, float):
            return value, False
        if isinstance(value, (int, str)):
            try:
                return float(value), True
            except ValueError:
                return value, False
        return value, False

    def _coerce_bool(self, value: Any) -> Tuple[Any, bool]:
        if isinstance(value, bool):
            return value, False
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "yes", "1"}:
                return True, True
            if lowered in {"false", "no", "0"}:
                return False, True
        return value, False

    def _coerce_list(self, value: Any, rule: ValidationRule) -> Tuple[Any, bool]:
        if isinstance(value, list):
            return value, False
        if isinstance(value, str):
            # Split comma separated strings into list when expecting list
            parts = [part.strip() for part in value.split(",") if part.strip()]
            return parts, True
        return value, False

    def _set_value_by_path(self, config: Dict[str, Any], key_path: str, new_value: Any) -> None:
        keys = key_path.split(".")
        target = config
        for key in keys[:-1]:
            if key not in target or not isinstance(target[key], dict):
                target[key] = {}
            target = target[key]
        target[keys[-1]] = new_value

    def _diff(self, old: Dict[str, Any], new: Dict[str, Any]) -> ConfigDiff:
        old_flat = self._flatten(old)
        new_flat = self._flatten(new)
        changed = {key for key in new_flat if new_flat.get(key) != old_flat.get(key)}
        removed = {key for key in old_flat if key not in new_flat}
        changed.update(removed)

        reload_exchange = any(key in changed for key in {"exchange"})
        reload_symbols = reload_exchange or any(
            key in changed for key in {"symbols", "symbolsFilePath"}
        )

        return ConfigDiff(changed_keys=changed, requires_exchange_reload=reload_exchange, requires_symbol_reload=reload_symbols)

    def _flatten(self, config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        items: Dict[str, Any] = {}
        for key, value in config.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                items.update(self._flatten(value, new_key))
            else:
                items[new_key] = value
        return items

    def _notify_listeners(
        self,
        new_config: Dict[str, Any],
        previous_config: Dict[str, Any],
        warnings: List[str],
        diff: ConfigDiff,
    ) -> None:
        listeners: List[Listener]
        with self._lock:
            listeners = list(self._listeners)

        event = ConfigUpdateEvent(
            new_config=copy.deepcopy(new_config),
            previous_config=copy.deepcopy(previous_config),
            warnings=list(warnings),
            diff=diff,
        )

        for listener in listeners:
            try:
                listener(event)
            except Exception:
                # Listener errors should not terminate notification chain.
                continue


config_manager = ConfigManager.instance()

__all__ = [
    "ConfigDiff",
    "ConfigUpdateEvent",
    "ManagerUpdateResult",
    "ConfigManager",
    "config_manager",
]
