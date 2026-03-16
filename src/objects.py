"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mesa import Agent, Model

if TYPE_CHECKING:
    from src.core.enums import WasteType
    from src.core.zones import Zone


class Radioactivity(Agent):
    def __init__(self, model: Model, zone: type[Zone]) -> None:
        super().__init__(model)

        self.zone = zone
        self.level = zone.random_radioactivity()


class DisposalZone(Agent):
    def __init__(self, model: Model) -> None:
        super().__init__(model)


class Waste(Agent):
    def __init__(self, model: Model, waste_type: WasteType) -> None:
        super().__init__(model)

        self.type = waste_type
