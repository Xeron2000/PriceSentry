"""Compatibility wrapper for the interactive config generator."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.config_generator import main as run_generator


def main() -> None:
    run_generator()


if __name__ == "__main__":
    main()
