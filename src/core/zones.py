"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

import random
from abc import ABC


class Zone(ABC):
    min_radioactivity: float
    max_radioactivity: float

    @classmethod
    def contains(cls, radioactivity: float) -> bool:
        return cls.min_radioactivity <= radioactivity < cls.max_radioactivity

    @classmethod
    def random_radioactivity(cls) -> float:
        return random.uniform(cls.min_radioactivity, cls.max_radioactivity)


class Z1(Zone):
    min_radioactivity = 0.0
    max_radioactivity = 0.33


class Z2(Zone):
    min_radioactivity = 0.33
    max_radioactivity = 0.66


class Z3(Zone):
    min_radioactivity = 0.66
    max_radioactivity = 1.0


class Zones:
    ALL = [Z1, Z2, Z3]

    @staticmethod
    def get_zone_from_radioactivity(value: float) -> type[Zone] | None:
        for zone_cls in Zones.ALL:
            if zone_cls.contains(value):
                return zone_cls
        return None
