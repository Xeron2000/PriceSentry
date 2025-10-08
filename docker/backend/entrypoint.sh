#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="/app/config/config.yaml"
EXAMPLE_CONFIG="/app/config/config.yaml.example"

# Prepare runtime configuration
if [[ ! -f "${CONFIG_FILE}" ]]; then
  if [[ -f "${EXAMPLE_CONFIG}" ]]; then
    cp "${EXAMPLE_CONFIG}" "${CONFIG_FILE}"
  else
    echo "Missing configuration file and example template" >&2
    exit 1
  fi
fi

python <<'PYCODE'
import os
from pathlib import Path

import yaml

config_path = Path("/app/config/config.yaml")

with config_path.open("r", encoding="utf-8") as fh:
    data = yaml.safe_load(fh) or {}

def set_nested(keys, value):
    cursor = data
    for key in keys[:-1]:
        cursor = cursor.setdefault(key, {})
    cursor[keys[-1]] = value

overrides = {
    ("exchange",): os.environ.get("PRICESENTRY_EXCHANGE"),
    ("telegram", "token"): os.environ.get("PRICESENTRY_TELEGRAM_TOKEN"),
    ("telegram", "chatId"): os.environ.get("PRICESENTRY_TELEGRAM_CHAT_ID"),
    ("logLevel",): os.environ.get("PRICESENTRY_LOG_LEVEL"),
    ("security", "dashboardAccessKey"): os.environ.get("PRICESENTRY_DASHBOARD_ACCESS_KEY"),
}

changed = False
for path, value in overrides.items():
    if value:
        set_nested(path, value)
        changed = True

if changed:
    with config_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)
PYCODE

exec "$@"
