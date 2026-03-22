"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents import BaseRobot
    from src.core.zones import Zone
    from src.objects import Waste


@dataclass
class TileContent:
    wastes: list[Waste]
    robots: list[BaseRobot]
    radioactivity: float
    zone: Zone
    is_disposal_zone: bool


@dataclass
class Percepts:
    current_position: tuple[int, int]
    current_tile: TileContent
    neighbors: dict[tuple[int, int], TileContent]
