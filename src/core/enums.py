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
    READ_MESSAGES = "read messages"
    SEND_MESSAGES = "send messages"


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

    def all_previous(self) -> list[WasteType]:
        """
        Return all the previous waste in the order

        Returns
        -------
        list[WasteType]
            List of all the previous waste
        """
        order = self.order()
        i = order.index(self)
        previous = []
        while i - 1 >= 0:
            previous.append(order[i - 1])
            i -= 1
        return previous


class Strategy(StrEnum):
    RANDOM = "random"
    COMMUNICATION = "communication"


class ProtocolStep(StrEnum):
    NONE = "None"
    SEARCHING = "searching"
    WAITING_CONNECTION = "waiting connection"
    COMMUNICATING = "communicating"
    MOVING = "moving"
    TRANSFERING = "transfering"
