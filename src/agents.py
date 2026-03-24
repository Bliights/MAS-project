"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod

from mesa import Agent, Model

from src.core.actions import Action
from src.core.enums import ActionType, Colour, Strategy, WasteType
from src.core.inventory import Inventory
from src.core.knowledge import Knowledge
from src.core.zones import Z1, Z2, Z3, Zone


class BaseRobot(Agent, ABC):
    colour: Colour | None = None
    allowed_zones: list[Zone] = []
    allowed_pick: list[WasteType] | None
    allowed_transform: WasteType | None

    def __init__(self, model: Model, name: str, strategy: Strategy) -> None:
        super().__init__(model)
        self.knowledge = Knowledge()
        self.inventory = Inventory()
        self.name = name
        self.strategy = strategy

    def step(self) -> None:
        """
        Execute one simulation step
        """
        action = self.deliberate()
        percepts = self.model.do(self, action)
        self.knowledge.update(percepts)

    @abstractmethod
    def deliberate(self) -> Action:
        """
        Decide the next action to perform

        Returns
        -------
        Action
            The action chosen by the robot
        """

    def is_valid_position(self, pos: tuple[int, int]) -> bool:
        """
        Check whether a position is reachable and allowed

        Parameters
        ----------
        pos : tuple[int, int]
            The target position

        Returns
        -------
        bool
            True if the position is valid, False otherwise
        """
        current_pos = self.knowledge.position

        if abs(pos[0] - current_pos[0]) + abs(pos[1] - current_pos[1]) != 1:
            return False

        tile = self.knowledge.map_memory.get(pos)

        if tile is None:
            return False

        return tile.zone in self.allowed_zones

    def random_move(self, wastes_to_pick: list[WasteType]) -> Action:
        """
        Select a random valid neighboring position and move there

        Parameters
        ----------
        wastes_to_pick : list[WasteType]
            Type of waste to pick in priority if seen in close tile

        Returns
        -------
        Action
            A MOVE action to a random valid position, or IDLE
        """
        valid_positions = [
            (pos, tile)
            for pos, tile in self.knowledge.map_memory.items()
            if self.is_valid_position(pos)
        ]
        for pos, tile in valid_positions:
            if tile.wastes:
                for waste in tile.wastes:
                    if waste.type in wastes_to_pick:
                        return Action(
                            ActionType.MOVE,
                            {"pos": pos},
                        )

        if not valid_positions:
            return Action(ActionType.IDLE)

        return Action(
            ActionType.MOVE,
            {"pos": random.choice([pos for pos, _ in valid_positions])},
        )


class GreenRobot(BaseRobot):
    colour = Colour.GREEN
    allowed_zones = [Z1]
    allowed_pick = [WasteType.GREEN]
    allowed_transform = WasteType.GREEN

    def __init__(self, model: Model, name: str, strategy: Strategy) -> None:
        super().__init__(model, name, strategy)

    def deliberate(self) -> Action:
        """
        Decision policy for the green robot

        Priority:
            1. If carrying transformed waste -> move right or drop if blocked
            2. If holding 2 green wastes -> transform
            3. If green waste present -> pick
            4. Otherwise -> random move

        Returns
        -------
        Action
            The selected action
        """
        current_pos = self.knowledge.position
        tile = self.knowledge.map_memory.get(current_pos)
        next_type = self.allowed_transform.next() if self.allowed_transform else None
        right_pos = (current_pos[0] + 1, current_pos[1])

        if next_type and self.inventory.has(next_type):
            if not self.is_valid_position(right_pos):
                return Action(ActionType.DROP, {"type": next_type})
            return Action(ActionType.MOVE, {"pos": right_pos})

        if self.allowed_transform and self.inventory.count(self.allowed_transform) == 2:
            return Action(ActionType.TRANSFORM)

        if any((w.type in self.allowed_pick and w.type == WasteType.GREEN) for w in tile.wastes):
            return Action(ActionType.PICK)

        return self.random_move([WasteType.GREEN])


class YellowRobot(BaseRobot):
    colour = Colour.YELLOW
    allowed_zones = [Z1, Z2]
    allowed_pick = [WasteType.GREEN, WasteType.YELLOW]
    allowed_transform = WasteType.YELLOW

    def __init__(self, model: Model, name: str, strategy: Strategy) -> None:
        super().__init__(model, name, strategy)

    def deliberate(self) -> Action:
        """
        Decision policy for the yellow robot

        Priority:
            1. If carrying transformed waste -> move right or drop if blocked
            2. If holding 2 yellow wastes -> transform
            3. If yellow waste present -> pick
            4. Otherwise -> random move

        Returns
        -------
        Action
            The selected action
        """
        current_pos = self.knowledge.position
        tile = self.knowledge.map_memory.get(current_pos)
        next_type = self.allowed_transform.next() if self.allowed_transform else None
        right_pos = (current_pos[0] + 1, current_pos[1])

        if next_type and self.inventory.has(next_type):
            if not self.is_valid_position(right_pos):
                return Action(ActionType.DROP, {"type": next_type})
            return Action(ActionType.MOVE, {"pos": right_pos})

        if self.allowed_transform and self.inventory.count(self.allowed_transform) == 2:
            return Action(ActionType.TRANSFORM)

        if any((w.type in self.allowed_pick and w.type == WasteType.YELLOW) for w in tile.wastes):
            return Action(ActionType.PICK)

        return self.random_move([WasteType.YELLOW])


class RedRobot(BaseRobot):
    colour = Colour.RED
    allowed_zones = [Z1, Z2, Z3]
    allowed_pick = [WasteType.GREEN, WasteType.YELLOW, WasteType.RED]
    allowed_transform = None

    def __init__(self, model: Model, name: str, strategy: Strategy) -> None:
        super().__init__(model, name, strategy)

    def deliberate(self) -> Action:
        """
        Decision policy for the red robot

        Priority:
            1. If carrying waste:
                - drop it in a disposal zone,
                - otherwise move right
            2. If on waste (not in disposal zone) -> pick
            3. Otherwise -> random move

        Returns
        -------
        Action
            The selected action
        """
        current_pos = self.knowledge.position
        tile = self.knowledge.map_memory.get(current_pos)
        right_pos = (current_pos[0] + 1, current_pos[1])

        if self.inventory.has(WasteType.RED):
            if tile.is_disposal_zone:
                return Action(ActionType.DROP, {"type": WasteType.RED})
            return Action(ActionType.MOVE, {"pos": right_pos})

        if not tile.is_disposal_zone and any(
            (w.type in self.allowed_pick and w.type == WasteType.RED) for w in tile.wastes
        ):
            return Action(ActionType.PICK)

        neighbors = [
            (current_pos[0] + 1, current_pos[1]),
            (current_pos[0] - 1, current_pos[1]),
            (current_pos[0], current_pos[1] + 1),
            (current_pos[0], current_pos[1] - 1),
        ]

        for pos in neighbors:
            tile = self.knowledge.map_memory.get(pos)
            if tile and tile.is_disposal_zone:
                return self.random_move([])

        return self.random_move([WasteType.RED])
