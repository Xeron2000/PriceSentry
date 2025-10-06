"""Compatibility wrapper for the monitoring report generator."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.monitoring_report import main as run_report


def main() -> None:
    run_report()


if __name__ == "__main__":
    main()
