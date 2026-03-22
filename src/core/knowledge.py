"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.percepts import Percepts


class Knowledge:
    def __init__(self) -> None:
        self.history = []
        self.position = None
        self.map_memory = {}

    def update(self, percepts: Percepts) -> None:
        """
        Update the agent's knowledge based on new percepts

        Parameters
        ----------
        percepts : Percepts
            The percepts returned by the environment, containing:
                - the agent's current position,
                - information about the current tile,
                - information about neighboring tiles
        """
        self.history.append(percepts)

        self.position = percepts.current_position
        self.map_memory[percepts.current_position] = percepts.current_tile

        for pos, tile in percepts.neighbors.items():
            self.map_memory[pos] = tile
