from __future__ import annotations

from typing import TYPE_CHECKING

from mesa import Agent, Model

if TYPE_CHECKING:
    from src.core.enums import WasteType
    from src.core.zones import Zone


class Radioactivity(Agent):
    def __init__(self, model: Model, zone: type[Zone]) -> None:
        """
        Initialize a radioactivity marker for a grid cell

        Parameters
        ----------
        model : Model
            The simulation model
        zone : type[Zone]
            The zone class defining the radioactivity range
        """
        super().__init__(model)
        self.zone = zone
        self.level = zone.random_radioactivity()


class DisposalZone(Agent):
    def __init__(self, model: Model) -> None:
        """
        Initialize a disposal zone

        Parameters
        ----------
        model : Model
            The simulation model
        """
        super().__init__(model)


class Waste(Agent):
    def __init__(self, model: Model, waste_type: WasteType) -> None:
        """
        Initialize a waste object

        Parameters
        ----------
        model : Model
            The simulation model
        waste_type : WasteType
            The type of waste
        """
        super().__init__(model)
        self.type = waste_type
