"""Compatibility wrapper for the main PriceSentry runner."""

from pathlib import Path
import asyncio
import sys

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.runner import main as _run_main


def main() -> None:
    """Entry point used by CLI wrappers."""
    asyncio.run(_run_main())


if __name__ == "__main__":
    main()
