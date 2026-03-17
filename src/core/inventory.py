"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.enums import WasteType
    from src.objects import Waste


class Inventory:
    def __init__(self) -> None:
        self.wastes: list[Waste] = []

    def add(self, waste: Waste) -> None:
        self.wastes.append(waste)

    def remove(self, waste_type: WasteType, n: int) -> None:
        removed = 0
        new = []
        for w in self.wastes:
            if w.type == waste_type and removed < n:
                removed += 1
            else:
                new.append(w)

        self.wastes = new

    def drop(self, waste_type: WasteType) -> Waste | None:
        for i, w in enumerate(self.wastes):
            if w.type == waste_type:
                return self.wastes.pop(i)

        return None

    def count(self, waste_type: WasteType) -> int:
        return sum(1 for w in self.wastes if w.type == waste_type)

    def has(self, waste_type: WasteType, n: int = 1) -> bool:
        return self.count(waste_type) >= n
