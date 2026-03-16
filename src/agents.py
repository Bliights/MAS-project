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

from src.core.actions import Action, ActionType
from src.core.enums import WasteType
from src.core.inventory import Inventory
from src.core.knowledge import Knowledge
from src.core.zones import Z1, Z2, Z3, Zone


class BaseRobot(Agent, ABC):
    allowed_zones: list[Zone] = []
    allowed_pick: WasteType | None
    allowed_transform: WasteType | None

    def __init__(self, model: Model) -> None:
        super().__init__(model)

        self.knowledge = Knowledge()
        self.inventory = Inventory()

    def step(self) -> None:
        action = self.deliberate()
        percepts = self.model.do(self, action)
        self.knowledge.update(percepts)

    @abstractmethod
    def deliberate(self) -> Action:
        pass

    def is_valid_position(self, pos: tuple[int, int]) -> bool:
        current_pos = self.knowledge.position

        if abs(pos[0] - current_pos[0]) + abs(pos[1] - current_pos[1]) != 1:
            return False

        tile = self.knowledge.map_memory.get(pos)

        if tile is None:
            return False

        return tile.zone in self.allowed_zones

    def random_move(self) -> Action:
        valid_positions = [pos for pos in self.knowledge.map_memory if self.is_valid_position(pos)]

        if not valid_positions:
            return Action(ActionType.IDLE)

        return Action(
            ActionType.MOVE,
            {"pos": random.choice(valid_positions)},
        )


class GreenRobot(BaseRobot):
    allowed_zones = [Z1]
    allowed_pick = WasteType.GREEN
    allowed_transform = WasteType.GREEN

    def __init__(self, model: Model) -> None:
        super().__init__(model)

    def deliberate(self) -> Action:
        current_pos = self.knowledge.position
        tile = self.knowledge.map_memory[current_pos]
        next_type = self.allowed_transform.next() if self.allowed_transform else None
        right_pos = (current_pos[0] + 1, current_pos[1])

        if self.inventory.has(next_type):
            if not self.is_valid_position(right_pos):
                return Action(ActionType.DROP, {"type": next_type})
            return Action(ActionType.MOVE, {"pos": right_pos})

        if self.allowed_transform and self.inventory.count(self.allowed_transform) >= 2:
            return Action(ActionType.TRANSFORM)

        if any(w.type == self.allowed_pick for w in tile.wastes):
            return Action(ActionType.PICK)

        return self.random_move()


class YellowRobot(BaseRobot):
    allowed_zones = [Z1, Z2]
    allowed_pick = WasteType.YELLOW
    allowed_transform = WasteType.YELLOW

    def __init__(self, model: Model) -> None:
        super().__init__(model)

    def deliberate(self) -> Action:
        current_pos = self.knowledge.position
        tile = self.knowledge.map_memory[current_pos]
        next_type = self.allowed_transform.next() if self.allowed_transform else None
        right_pos = (current_pos[0] + 1, current_pos[1])

        if self.inventory.has(next_type):
            if not self.is_valid_position(right_pos):
                return Action(ActionType.DROP, {"type": next_type})
            return Action(ActionType.MOVE, {"pos": right_pos})

        if self.allowed_transform and self.inventory.count(self.allowed_transform) >= 2:
            return Action(ActionType.TRANSFORM)

        if any(w.type == self.allowed_pick for w in tile.wastes):
            return Action(ActionType.PICK)

        return self.random_move()


class RedRobot(BaseRobot):
    allowed_zones = [Z1, Z2, Z3]
    allowed_pick = WasteType.RED
    allowed_transform = None

    def __init__(self, model: Model) -> None:
        super().__init__(model)

    def deliberate(self) -> Action:
        current_pos = self.knowledge.position
        tile = self.knowledge.map_memory[current_pos]
        right_pos = (current_pos[0] + 1, current_pos[1])

        if self.inventory.has(self.allowed_pick):
            if tile.is_disposal_zone:
                return Action(ActionType.DROP, {"type": self.allowed_pick})
            return Action(ActionType.MOVE, {"pos": right_pos})

        if any(w.type == self.allowed_pick for w in tile.wastes):
            return Action(ActionType.PICK)

        return self.random_move()
