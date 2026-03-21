from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / ".vendor"

if VENDOR.exists():
    vendor_str = str(VENDOR)
    if vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)
