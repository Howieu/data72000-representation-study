"""Load the fixed analysis protocol."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "protocol" / "analysis_protocol.json"


def load_protocol(path: Path = PROTOCOL_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def classix_radii(protocol: dict) -> tuple[float, ...]:
    spec = protocol["classix"]
    start = Decimal(str(spec["radius_start"]))
    stop = Decimal(str(spec["radius_stop"]))
    step = Decimal(str(spec["radius_step"]))
    count = int((stop - start) / step) + 1
    return tuple(float(start + step * index) for index in range(count))
