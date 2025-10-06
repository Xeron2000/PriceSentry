"""确保 src/ 目录在系统路径中。"""
import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parent / "src"
if SRC_PATH.is_dir():
    src_str = str(SRC_PATH)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
