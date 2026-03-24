"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

from enum import StrEnum


class Colour(StrEnum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


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
        """
        Define the ordered sequence of waste types

        Returns
        -------
        list[WasteType]
            The ordered list of waste types
        """
        return [cls.GREEN, cls.YELLOW, cls.RED]

    def next(self) -> WasteType | None:
        """
        Get the next waste type in the transformation pipeline

        Returns
        -------
        WasteType | None
            The next waste type, or None if this is the last stage
        """
        order = self.order()
        i = order.index(self)

        return order[i + 1] if i + 1 < len(order) else None


class Strategy(StrEnum):
    RANDOM = "random"
    COMMUNICATION = "communication"
