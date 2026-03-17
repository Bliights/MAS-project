"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

from enum import StrEnum


class ActionType(StrEnum):
    MOVE = "move"
    PICK = "pick"
    TRANSFORM = "transform"
    DROP = "drop"
    IDLE = "idle"


class WasteType(StrEnum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

    @classmethod
    def order(cls) -> list[WasteType]:
        return [cls.GREEN, cls.YELLOW, cls.RED]

    def next(self) -> WasteType | None:
        order = self.order()
        i = order.index(self)

        return order[i + 1] if i + 1 < len(order) else None
