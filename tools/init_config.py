"""Interactive initializer for PriceSentry configuration."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

import yaml


DEFAULT_TEMPLATE = Path("config/config.yaml.example")
DEFAULT_OUTPUT = Path("config/config.yaml")


class InitError(Exception):
    """Raised when initialization cannot proceed."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactively create config/config.yaml from the example template."
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        help="Template YAML path (default: config/config.yaml.example)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination YAML path (default: config/config.yaml)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite destination without prompting.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip prompts and copy the template as-is (same as legacy flow).",
    )
    return parser.parse_args()


def load_template(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise InitError(f"Template not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise InitError("Template root must be a mapping")
    return data


def ensure_destination(path: Path, *, force: bool) -> bool:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        return True

    if force:
        return True

    response = input(
        f"[init-config] Destination {path} already exists. Overwrite? (y/N): "
    ).strip().lower()
    return response in {"y", "yes"}


def copy_template(template: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, output)


def prompt(message: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{message}{suffix}: ").strip()
    return value if value else (default or "")


def parse_list(text: str) -> List[str]:
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def parse_float(text: str, default: float) -> float:
    if not text:
        return default
    try:
        return float(text)
    except ValueError as exc:
        raise InitError(f"Expected numeric value, got '{text}'") from exc


def parse_bool(text: str, default: bool) -> bool:
    if not text:
        return default
    lowered = text.lower()
    if lowered in {"y", "yes", "true", "1"}:
        return True
    if lowered in {"n", "no", "false", "0"}:
        return False
    raise InitError(f"Invalid boolean answer: '{text}'")


def get_nested(config: Dict[str, Any], path: Iterable[str]) -> Any:
    current: Any = config
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def set_nested(config: Dict[str, Any], path: Iterable[str], value: Any) -> None:
    keys = list(path)
    current = config
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


@dataclass
class PromptSpec:
    path: List[str]
    message: str
    formatter: Callable[[str, Any], Any]


def interactive_customize(config: Dict[str, Any]) -> Dict[str, Any]:
    specs: List[PromptSpec] = [
        PromptSpec(["exchange"], "Exchange (binance/okx/bybit)", lambda text, default: text or default),
        PromptSpec(["defaultTimeframe"], "Default timeframe", lambda text, default: text or default),
        PromptSpec(["checkInterval"], "Monitoring interval", lambda text, default: text or default),
        PromptSpec(["defaultThreshold"], "Default threshold (%)", lambda text, default: parse_float(text, float(default))),
        PromptSpec(
            ["notificationChannels"],
            "Notification channels (comma separated)",
            lambda text, default: parse_list(text) or list(default or []),
        ),
        PromptSpec(["notificationTimezone"], "Notification timezone", lambda text, default: text or default),
        PromptSpec(
            ["notificationSymbols"],
            "Notification symbols (comma separated, empty for all)",
            lambda text, default: parse_list(text) or list(default or []),
        ),
        PromptSpec(
            ["telegram", "token"],
            "Telegram bot token (required for Telegram alerts)",
            lambda text, default: text or default,
        ),
        PromptSpec(
            ["telegram", "chatId"],
            "Telegram fallback chat ID (optional)",
            lambda text, default: text or default,
        ),
        PromptSpec(
            ["attachChart"],
            "Attach chart images by default? (y/N)",
            lambda text, default: parse_bool(text, bool(default)),
        ),
    ]

    for spec in specs:
        while True:
            default_value = get_nested(config, spec.path)
            if isinstance(default_value, list):
                default_display = ",".join(str(item) for item in default_value)
            elif isinstance(default_value, bool):
                default_display = "yes" if default_value else "no"
            else:
                default_display = "" if default_value is None else str(default_value)

            try:
                answer = prompt(spec.message, default_display)
                effective_default = default_value
                if isinstance(default_value, list):
                    effective_default = list(default_value)
                formatted = spec.formatter(answer, effective_default)
            except InitError as exc:
                print(f"[init-config] {exc}. Please try again.")
                continue

            set_nested(config, spec.path, formatted)
            break

    return config


def dump_preview(config: Dict[str, Any]) -> None:
    print("\n[init-config] Preview of generated configuration:\n")
    print(json.dumps(config, indent=2, ensure_ascii=False))
    print()


def write_config(config: Dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(config, fh, default_flow_style=False, allow_unicode=True, sort_keys=False)


def main() -> int:
    args = parse_args()

    try:
        template_data = load_template(args.template)

        if not ensure_destination(args.output, force=args.force):
            print("[init-config] Aborted by user.")
            return 0

        if args.non_interactive:
            copy_template(args.template, args.output)
            print(f"[init-config] Template copied to {args.output}")
            return 0

        config = interactive_customize(template_data)
        dump_preview(config)
        confirmation = input("Write this configuration to disk? (Y/n): ").strip().lower()
        if confirmation not in {"", "y", "yes"}:
            print("[init-config] Aborted by user.")
            return 0

        write_config(config, args.output)
        print(f"[init-config] Configuration written to {args.output}")
        return 0

    except InitError as exc:
        print(f"[init-config] Failed: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[init-config] Interrupted by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
