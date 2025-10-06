"""Compatibility wrapper for the simplified configuration checker."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.config_check import main as run_config_check


def main() -> None:
    run_config_check()


if __name__ == "__main__":
    main()
