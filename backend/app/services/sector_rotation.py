from dataclasses import dataclass
from pathlib import Path

import yaml

SECTOR_MAP_PATH = Path(__file__).resolve().parent.parent / "data" / "sector_map.yaml"


@dataclass
class SectorMomentum:
    sector: str
    momentum: float
    rank: int


def load_sector_map() -> dict[str, str]:
    if SECTOR_MAP_PATH.exists():
        with open(SECTOR_MAP_PATH) as f:
            return yaml.safe_load(f) or {}
    return {
        "RELIANCE": "ENERGY",
        "TCS": "IT",
        "HDFCBANK": "BANKING",
        "INFY": "IT",
        "ICICIBANK": "BANKING",
        "SBIN": "BANKING",
        "BHARTIARTL": "IT",
        "ITC": "FMCG",
        "LT": "AUTO",
        "AXISBANK": "BANKING",
    }


def compute_sector_heatmap(symbol_changes: dict[str, float]) -> list[SectorMomentum]:
    sector_map = load_sector_map()
    sector_vals: dict[str, list[float]] = {}
    for symbol, change in symbol_changes.items():
        sector = sector_map.get(symbol.upper(), "OTHER")
        sector_vals.setdefault(sector, []).append(change)

    momentums = []
    for sector, changes in sector_vals.items():
        momentum = sum(changes) / len(changes)
        momentums.append(SectorMomentum(sector=sector, momentum=momentum, rank=0))

    momentums.sort(key=lambda x: x.momentum, reverse=True)
    for i, m in enumerate(momentums):
        m.rank = i + 1
    return momentums
