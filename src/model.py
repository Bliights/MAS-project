"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid

from src.agents import BaseRobot, GreenRobot, RedRobot, YellowRobot
from src.core.enums import ActionType, WasteType
from src.core.percepts import Percepts, TileContent
from src.core.zones import Zones
from src.objects import DisposalZone, Radioactivity, Waste

if TYPE_CHECKING:
    from src.core.actions import Action


class RobotMission(Model):
    def __init__(
        self,
        width: int = 30,
        height: int = 10,
        n_waste: int = 10,
        n_green: int = 5,
        n_yellow: int = 0,
        n_red: int = 0,
    ) -> None:
        super().__init__()

        self.grid = MultiGrid(width, height, torus=False)

        self.datacollector = DataCollector(
            model_reporters={
                "green_waste": self.count_green,
                "yellow_waste": self.count_yellow,
                "red_waste": self.count_red,
            },
        )
        self.init_environment(n_waste, n_green, n_yellow, n_red)

    def _spawn_robot(self, robot_cls: BaseRobot, n: int) -> None:
        width = self.grid.width
        height = self.grid.height

        for _ in range(n):
            robot = robot_cls(self)

            for _ in range(100):
                x = self.random.randrange(width)
                y = self.random.randrange(height)

                cell = self.grid.get_cell_list_contents((x, y))

                radio = next(o for o in cell if isinstance(o, Radioactivity))
                zone = radio.zone

                if zone in robot.allowed_zones:
                    self.grid.place_agent(robot, (x, y))
                    break

    def init_environment(
        self,
        n_waste: int,
        n_green: int,
        n_yellow: int,
        n_red: int,
    ) -> None:
        width = self.grid.width
        height = self.grid.height

        zones = Zones.ALL
        zone_width = width // len(zones)

        for x in range(width):
            zone_index = min(x // zone_width, len(zones) - 1)
            zone = zones[zone_index]

            for y in range(height):
                radio = Radioactivity(self, zone)
                self.grid.place_agent(radio, (x, y))

                if x == width - 1:
                    self.grid.place_agent(DisposalZone(self), (x, y))

        for _ in range(n_waste):
            x = self.random.randrange(0, zone_width)
            y = self.random.randrange(height)
            waste = Waste(self, WasteType.GREEN)
            self.grid.place_agent(waste, (x, y))

        self._spawn_robot(GreenRobot, n_green)
        self._spawn_robot(YellowRobot, n_yellow)
        self._spawn_robot(RedRobot, n_red)

    def do(self, agent: Agent, action: Action) -> Percepts:
        if action.type == ActionType.MOVE:
            new_pos = action.payload.get("pos")

            if not self.grid.out_of_bounds(new_pos):
                cell = self.grid.get_cell_list_contents(new_pos)
                radio = next(o for o in cell if isinstance(o, Radioactivity))

                if radio.zone in agent.allowed_zones:
                    self.grid.move_agent(agent, new_pos)

        elif action.type == ActionType.PICK:
            cell = self.grid.get_cell_list_contents(agent.pos)

            for obj in cell:
                if isinstance(obj, Waste) and obj.type == agent.allowed_pick:
                    agent.inventory.add(obj)
                    self.grid.remove_agent(obj)
                    break

        elif action.type == ActionType.TRANSFORM:
            if agent.allowed_transform and agent.inventory.count(agent.allowed_transform) == 2:
                next_type = agent.allowed_transform.next()
                if next_type:
                    agent.inventory.remove(agent.allowed_transform, 2)
                    agent.inventory.add(Waste(self, next_type))

        elif action.type == ActionType.DROP:
            waste_type = action.payload.get("type")
            if agent.inventory.has(waste_type):
                waste = agent.inventory.drop(waste_type)
                if waste:
                    self.grid.place_agent(waste, agent.pos)

        return self.get_percepts(agent)

    def get_percepts(self, agent: Agent) -> Percepts:
        neighbors = self.grid.get_neighborhood(
            agent.pos,
            moore=False,
            include_center=True,
        )
        percepts = {}

        for pos in neighbors:
            cell = self.grid.get_cell_list_contents(pos)

            wastes = [o.type for o in cell if isinstance(o, Waste)]
            robots = [o for o in cell if isinstance(o, BaseRobot) and o is not agent]
            radio = next(o for o in cell if isinstance(o, Radioactivity))
            is_disposal = any(isinstance(o, DisposalZone) for o in cell)
            percepts[pos] = TileContent(
                wastes=wastes,
                robots=robots,
                radioactivity=radio.level,
                zone=radio.zone,
                is_disposal_zone=is_disposal,
            )

        return Percepts(agent.pos, percepts.get(agent.pos), percepts)

    def _all_robots(self) -> list[BaseRobot]:
        return [a for a in self.grid.get_all_cell_contents() if isinstance(a, BaseRobot)]

    def _count_waste(self, waste_type: WasteType) -> int:
        grid_count = sum(
            1
            for obj in self.grid.get_all_cell_contents()
            if isinstance(obj, Waste) and obj.type == waste_type
        )

        inventory_count = sum(robot.inventory.count(waste_type) for robot in self._all_robots())

        return grid_count + inventory_count

    def count_green(self) -> int:
        return self._count_waste(WasteType.GREEN)

    def count_yellow(self) -> int:
        return self._count_waste(WasteType.YELLOW)

    def count_red(self) -> int:
        return self._count_waste(WasteType.RED)
