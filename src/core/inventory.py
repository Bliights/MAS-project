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
        """
        Add a waste object to the inventory

        Parameters
        ----------
        waste : Waste
            The waste object to add to the inventory
        """
        self.wastes.append(waste)

    def remove(self, waste_type: WasteType, n: int) -> None:
        """
        Remove and destroy a given number of wastes of a specific type

        Parameters
        ----------
        waste_type : WasteType
            The type of waste to remove
        n : int
            The number of wastes to remove
        """
        removed = 0
        new = []
        for w in self.wastes:
            if w.type == waste_type and removed < n:
                removed += 1
                w.remove()
            else:
                new.append(w)

        self.wastes = new

    def drop(self, waste_type: WasteType) -> Waste | None:
        """
        Remove and return one waste of a given type from the inventory

        Parameters
        ----------
        waste_type : WasteType
            The type of waste to drop

        Returns
        -------
        Waste | None
            The removed waste if found, otherwise None
        """
        for i, w in enumerate(self.wastes):
            if w.type == waste_type:
                return self.wastes.pop(i)

        return None

    def count(self, waste_type: WasteType) -> int:
        """
        Count how many wastes of a given type are in the inventory

        Parameters
        ----------
        waste_type : WasteType
            The type of waste to count

        Returns
        -------
        int
            The number of wastes of the given type
        """
        return sum(1 for w in self.wastes if w.type == waste_type)

    def has(self, waste_type: WasteType, n: int = 1) -> bool:
        """
        Check whether the inventory contains at least n wastes of a given type

        Parameters
        ----------
        waste_type : WasteType
            The type of waste to check
        n : int, optional
            The minimum number of wastes required

        Returns
        -------
        bool
            True if the inventory contains at least n wastes of the given type, False otherwise.
        """
        return self.count(waste_type) >= n
