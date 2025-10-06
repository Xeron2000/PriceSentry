"""Compatibility wrapper for the monitoring dashboard CLI."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.dashboard import display_monitoring_dashboard


def main() -> None:
    display_monitoring_dashboard()


if __name__ == "__main__":
    print("启动 PriceSentry 监控仪表板...")
    main()
