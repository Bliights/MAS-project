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
from src.communication.service import MessageService
from src.core.enums import ActionType, Strategy, WasteType
from src.core.percepts import Percepts, TileContent
from src.core.zones import Zones
from src.objects import DisposalZone, Radioactivity, Waste

if TYPE_CHECKING:
    from src.core.actions import Action


class RobotMission(Model):
    def __init__(
        self,
        width: int,
        height: int,
        strategy: Strategy,
        n_green_waste: int,
        n_green_robots: int,
        n_yellow_robots: int,
        n_red_robots: int,
    ) -> None:
        """
        Initialize the robot mission environment

        Parameters
        ----------
        width : int
            Width of the grid
        height : int
            Height of the grid
        strategy : Strategy
            Strategy of the robots
        n_green_waste : int
            Initial number of green waste objects
        n_green_robots : int
            Number of green robots
        n_yellow_robots : int
            Number of yellow robots
        n_red_robots : int
            Number of red robots
        """
        super().__init__()
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, torus=False)
        self.strategy = strategy
        self.current_step = 0

        self.zones = Zones.ALL
        self.zone_width = width // len(self.zones)

        self.messages_service = MessageService(self, False)

        self.datacollector = DataCollector(
            model_reporters={
                "green_waste": self.count_green,
                "yellow_waste": self.count_yellow,
                "red_waste": self.count_red,
            },
        )
        self.init_environment(
            strategy,
            n_green_waste,
            n_green_robots,
            n_yellow_robots,
            n_red_robots,
        )
        self.datacollector.collect(self)

    def _spawn_robot(self, robot_cls: BaseRobot, n: int, strategy: Strategy) -> None:
        """
        Spawn robots of a given class in valid zones

        Parameters
        ----------
        robot_cls : BaseRobot
            The robot class to instantiate
        n : int
            Number of robots to create
        strategy : Strategy
            Strategy of the robots
        """
        width = self.grid.width
        height = self.grid.height

        for i in range(n):
            name = f"{robot_cls.__name__}_{i}"
            robot = robot_cls(self, name, strategy)

            for _ in range(100):
                x = self.random.randrange(width)
                y = self.random.randrange(height)

                cell = self.grid.get_cell_list_contents((x, y))

                radio = next(o for o in cell if isinstance(o, Radioactivity))
                zone = radio.zone

                if zone in robot.allowed_zones:
                    self.grid.place_agent(robot, (x, y))
                    break

    def _init_robot_knowledge(self) -> None:
        """
        Initialize each robot's knowledge with initial percepts
        """
        all_robots = self._all_agent_instance(BaseRobot)
        for robot in all_robots:
            percepts = self.get_percepts(robot)
            robot.knowledge.update(percepts)
            robot.knowledge.agents = [
                other for other in all_robots if type(other) is type(robot) and other is not robot
            ]

    def init_environment(
        self,
        strategy: Strategy,
        n_green_waste: int,
        n_green_robots: int,
        n_yellow_robots: int,
        n_red_robots: int,
    ) -> None:
        """
        Initialize the environment

        Parameters
        ----------
        strategy : Strategy
            Strategy of the robots
        n_green_waste : int
            Number of green wastes to generate
        n_green_robots : int
            Number of green robots
        n_yellow_robots : int
            Number of yellow robots
        n_red_robots : int
            Number of red robots
        """
        width = self.grid.width
        height = self.grid.height

        for x in range(width):
            zone_index = min(x // self.zone_width, len(self.zones) - 1)
            zone = self.zones[zone_index]

            for y in range(height):
                radio = Radioactivity(self, zone)
                self.grid.place_agent(radio, (x, y))

                if x == width - 1:
                    self.grid.place_agent(DisposalZone(self), (x, y))

        for _ in range(n_green_waste):
            x = self.random.randrange(0, self.zone_width)
            y = self.random.randrange(height)
            waste = Waste(self, WasteType.GREEN)
            self.grid.place_agent(waste, (x, y))

        self._spawn_robot(GreenRobot, n_green_robots, strategy)
        self._spawn_robot(YellowRobot, n_yellow_robots, strategy)
        self._spawn_robot(RedRobot, n_red_robots, strategy)

        self._init_robot_knowledge()

    def do(self, agent: Agent, action: Action) -> Percepts:
        """
        Execute an action for a given agent and return updated percepts

        Parameters
        ----------
        agent : Agent
            The acting agent
        action : Action
            The action to execute

        Returns
        -------
        Percepts
            Updated percepts after action execution
        """
        if action.type == ActionType.MOVE:
            new_pos = action.payload.get("pos")

            if not self.grid.out_of_bounds(new_pos):
                cell = self.grid.get_cell_list_contents(new_pos)
                radio = next(o for o in cell if isinstance(o, Radioactivity))

                if radio.zone in agent.allowed_zones:
                    self.grid.move_agent(agent, new_pos)

        elif action.type == ActionType.PICK:
            cell = self.grid.get_cell_list_contents(agent.pos)
            waste_type = action.payload.get("type")
            for obj in cell:
                if (
                    isinstance(obj, Waste)
                    and obj.type in agent.allowed_pick
                    and obj.type == waste_type
                ):
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

        elif action.type == ActionType.SEND_MESSAGES:
            messages = agent.mailbox.flush_outbox()
            for message in messages:
                self.messages_service.send_message(message)

        elif action.type == ActionType.READ_MESSAGES:
            messages = agent.mailbox.get_new_messages()
            agent.process_messages(messages)

        return self.get_percepts(agent)

    def get_percepts(self, agent: Agent) -> Percepts:
        """
        Retrieve percepts for an agent

        Parameters
        ----------
        agent : Agent
            The agent requesting percepts

        Returns
        -------
        Percepts
            The perceived environment information
        """
        neighbors = self.grid.get_neighborhood(
            agent.pos,
            moore=False,
            include_center=True,
        )
        percepts = {}

        for pos in neighbors:
            cell = self.grid.get_cell_list_contents(pos)

            wastes = [o for o in cell if isinstance(o, Waste)]
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

        waste_count = {}
        agent_carrying = {}

        for obj in self.agents:
            if isinstance(obj, Waste):
                waste_count[obj.type] = waste_count.get(obj.type, 0) + 1
            elif isinstance(obj, type(agent)) and obj.inventory.wastes:
                if (
                    obj.allowed_transform is not None
                    and obj.inventory.count(obj.allowed_transform) >= 2
                ):
                    continue
                waste_type = obj.inventory.wastes[0].type
                agent_carrying[waste_type] = agent_carrying.get(waste_type, 0) + 1

        return Percepts(
            current_position=agent.pos,
            current_tile=percepts.get(agent.pos),
            neighbors=percepts,
            waste_count=waste_count,
            agent_carrying=agent_carrying,
        )

    def _all_agent_instance(self, instance: type[Agent]) -> list[BaseRobot]:
        """
        Retrieve all agents of a given type

        Parameters
        ----------
        instance : type[Agent]
            The class type to filter

        Returns
        -------
        list[BaseRobot]
            List of matching agents
        """
        return [a for a in self.agents if isinstance(a, instance)]

    def _count_waste(self, waste_type: WasteType) -> int:
        """
        Count all waste agents of a given type in the environment

        Parameters
        ----------
        waste_type : WasteType
            The waste type to count

        Returns
        -------
        int
            Number of wastes of that type
        """
        return sum(1 for obj in self.agents if (isinstance(obj, Waste) and obj.type == waste_type))

    def count_green(self) -> int:
        """
        Count green wastes

        Returns
        -------
        int
            The count
        """
        return self._count_waste(WasteType.GREEN)

    def count_yellow(self) -> int:
        """
        Count yellow wastes

        Returns
        -------
        int
            The count
        """
        return self._count_waste(WasteType.YELLOW)

    def count_red(self) -> int:
        """
        Count red wastes

        Returns
        -------
        int
            The count
        """
        return self._count_waste(WasteType.RED)

    def step(self) -> None:
        """
        Execute one simulation step
        """
        self.messages_service.dispatch_messages()
        robots = list(self._all_agent_instance(BaseRobot))
        self.random.shuffle(robots)
        for robot in robots:
            robot.step()
        self.current_step += 1
        self.datacollector.collect(self)
