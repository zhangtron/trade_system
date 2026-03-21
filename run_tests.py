from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / ".vendor"

if VENDOR.exists():
    sys.path.insert(0, str(VENDOR))

import pytest


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", "tests", "--basetemp=.pytest_tmp"]))
