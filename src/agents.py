from __future__ import annotations

import random
from abc import ABC, abstractmethod

from mesa import Agent, Model

from src.communication.enums import Message, MessageType, Performative, ProtocolStep
from src.communication.mailbox import Mailbox
from src.communication.service import MessageService
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
        self.reserved_tiles = set()
        if strategy == Strategy.COMMUNICATION:
            self.init_communication()

    def init_communication(self) -> None:
        self.mailbox = Mailbox()
        self.messages_service = MessageService.get_instance()

        self.current_partner = None
        self.meeting_point = None
        self.next_action = None
        self.protocol_step = ProtocolStep.NONE

    def step(self) -> None:
        """
        Execute one simulation step
        """
        action = self.deliberate()
        percepts = self.model.do(self, action)
        self.knowledge.update(percepts)

    def deliberate(self) -> Action:
        """
        Decide the next action to perform

        Returns
        -------
        Action
            The action chosen by the robot
        """
        if self.strategy == Strategy.RANDOM:
            return self.deliberate_random()
        self.handle_messages()
        return self.deliberate_communication()

    @abstractmethod
    def deliberate_random(self) -> Action:
        """
        Decide the next action to perform for the random strategy

        Returns
        -------
        Action
            The action chosen by the robot
        """

    @abstractmethod
    def deliberate_communication(self) -> Action:
        """
        Decide the next action to perform for the communication strategy

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

        if pos in self.reserved_tiles:
            return False

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

    def move_towards(self, destination: tuple[int, int]) -> Action:
        current_x, current_y = self.knowledge.position
        dest_x, dest_y = destination
        candidates = []
        if dest_x > current_x:
            candidates.append((current_x + 1, current_y))
        elif dest_x < current_x:
            candidates.append((current_x - 1, current_y))
        if dest_y > current_y:
            candidates.append((current_x, current_y + 1))
        elif dest_y < current_y:
            candidates.append((current_x, current_y - 1))

        for pos in candidates:
            if self.is_valid_position(pos):
                return Action(ActionType.MOVE, {"pos": pos})

        return self.random_move([])

    def need_communication(self) -> bool:
        if not self.inventory.wastes:
            return False
        if self.protocol_step != ProtocolStep.NONE:
            return False
        waste_type = self.inventory.wastes[0].type
        waste_count = self.knowledge.waste_count.get(waste_type, 0)
        robot_carrying = self.knowledge.agent_carrying.get(waste_type, 0)
        return waste_count > 1 and waste_count == robot_carrying

    def reset_protocol(self) -> None:
        old_meeting_point = self.meeting_point

        self.current_partner = None
        self.meeting_point = None
        self.next_action = None
        self.protocol_step = ProtocolStep.NONE

        if old_meeting_point is not None:
            self.broadcast_tile_freed(old_meeting_point)

    def choose_meeting_point(self) -> tuple[int, int]:
        candidates = [
            pos
            for pos, tile in self.knowledge.map_memory.items()
            if tile.zone in self.allowed_zones and pos not in self.reserved_tiles
        ]

        if not candidates:
            return self.knowledge.position

        return random.choice(candidates)

    def broadcast_tile_reserved(self, pos: tuple[int, int]) -> None:
        for agent in self.knowledge.agents:
            self.messages_service.send_message(
                Message(
                    sender=self.name,
                    receiver=agent.name,
                    performative=Performative.INFORM,
                    type=MessageType.RESERVED_TILE_INFORM,
                    data={"pos": pos},
                ),
            )

    def broadcast_tile_freed(self, pos: tuple[int, int]) -> None:
        for agent in self.knowledge.agents:
            self.messages_service.send_message(
                Message(
                    sender=self.name,
                    receiver=agent.name,
                    performative=Performative.INFORM,
                    type=MessageType.FREE_TILE_INFORM,
                    data={"pos": pos},
                ),
            )

    def start_communication(self, waste_type: WasteType) -> None:
        for agent in self.knowledge.agents:
            self.messages_service.send_message(
                Message(
                    sender=self.name,
                    receiver=agent.name,
                    performative=Performative.CFP,
                    type=MessageType.WASTE_CFP,
                    data={"waste": waste_type},
                ),
            )

    def handle_cfp(self, message: Message) -> None:
        if self.current_partner is not None or not self.inventory.has(message.data["waste"]):
            self.messages_service.send_message(
                Message(
                    sender=self.name,
                    receiver=message.sender,
                    performative=Performative.REFUSE,
                    type=MessageType.REFUSE_CFP,
                    data={},
                ),
            )
        else:
            self.messages_service.send_message(
                Message(
                    sender=self.name,
                    receiver=message.sender,
                    performative=Performative.PROPOSE,
                    type=MessageType.COMMUNICATION_PROPOSAL,
                    data={},
                ),
            )

    def handle_propose(self, message: Message) -> None:
        if message.type == MessageType.COMMUNICATION_PROPOSAL:
            if self.current_partner is None:
                self.current_partner = message.sender
                self.protocol_step = ProtocolStep.MOVE
                self.messages_service.send_message(
                    Message(
                        sender=self.name,
                        receiver=message.sender,
                        performative=Performative.ACCEPT_PROPOSAL,
                        type=MessageType.COMMUNICATION_ACCEPT,
                        data={},
                    ),
                )
            else:
                self.messages_service.send_message(
                    Message(
                        sender=self.name,
                        receiver=message.sender,
                        performative=Performative.REJECT_PROPOSAL,
                        type=MessageType.COMMUNICATION_REJECT,
                        data={},
                    ),
                )
        elif message.type == MessageType.TRANSFER_PROPOSAL:
            if self.knowledge.position != self.meeting_point:
                self.messages_service.send_message(
                    Message(
                        sender=self.name,
                        receiver=message.sender,
                        performative=Performative.REJECT_PROPOSAL,
                        type=MessageType.TRANSFER_REJECT,
                        data={},
                    ),
                )
            else:
                self.protocol_step = ProtocolStep.TRANSFER
                self.messages_service.send_message(
                    Message(
                        sender=self.name,
                        receiver=message.sender,
                        performative=Performative.ACCEPT_PROPOSAL,
                        type=MessageType.TRANSFER_ACCEPT,
                        data={},
                    ),
                )

    def handle_accept(self, message: Message) -> None:
        if message.type == MessageType.COMMUNICATION_ACCEPT:
            self.protocol_step = ProtocolStep.MOVE
            self.meeting_point = self.choose_meeting_point()

            self.reserved_tiles.add(self.meeting_point)
            self.broadcast_tile_reserved(self.meeting_point)

            self.messages_service.send_message(
                Message(
                    sender=self.name,
                    receiver=message.sender,
                    performative=Performative.REQUEST,
                    type=MessageType.MOVE_TO_TILE_REQUEST,
                    data={"pos": self.meeting_point},
                ),
            )

        elif message.type == MessageType.TRANSFER_ACCEPT:
            self.protocol_step = ProtocolStep.TRANSFER
            self.next_action = Action(ActionType.DROP, {"type": self.inventory.wastes[0].type})
            self.messages_service.send_message(
                Message(
                    sender=self.name,
                    receiver=message.sender,
                    performative=Performative.INFORM,
                    type=MessageType.EXCHANGE_INFORM,
                    data={},
                ),
            )

    def handle_request(self, message: Message) -> None:
        if message.type == MessageType.MOVE_TO_TILE_REQUEST:
            self.meeting_point = message.data["pos"]
            self.messages_service.send_message(
                Message(
                    sender=self.name,
                    receiver=message.sender,
                    performative=Performative.AGREE,
                    type=MessageType.MOVE_TO_TILE_AGREE,
                    data={},
                ),
            )

    def handle_inform(self, message: Message) -> None:
        if message.type == MessageType.RESERVED_TILE_INFORM:
            self.reserved_tiles.add(message.data["pos"])
        elif message.type == MessageType.EXCHANGE_INFORM:
            self.messages_service.send_message(
                Message(
                    sender=self.name,
                    receiver=message.sender,
                    performative=Performative.CONFIRM,
                    type=MessageType.EXCHANGE_CONFIRM,
                    data={},
                ),
            )
            self.reset_protocol()
            self.next_action = Action(ActionType.PICK)
        elif message.type == MessageType.FREE_TILE_INFORM:
            self.reserved_tiles.discard(message.data["pos"])

    def handle_confirm(self, message: Message) -> None:
        if message.type == MessageType.EXCHANGE_CONFIRM:
            self.reset_protocol()

    def handle_messages(self) -> None:
        messages = self.mailbox.get_new_messages()
        for message in messages:
            if message.performative == Performative.CFP:
                self.handle_cfp(message)
            elif message.performative == Performative.PROPOSE:
                self.handle_propose(message)
            elif message.performative == Performative.REFUSE:
                continue
            elif message.performative == Performative.ACCEPT_PROPOSAL:
                self.handle_accept(message)
            elif message.performative == Performative.REJECT_PROPOSAL:
                continue
            elif message.performative == Performative.REQUEST:
                self.handle_request(message)
            elif message.performative == Performative.AGREE:
                continue
            elif message.performative == Performative.INFORM:
                self.handle_inform(message)
            elif message.performative == Performative.CONFIRM:
                self.handle_confirm(message)

    def transfert_protocol(self) -> Action:
        if self.next_action is not None:
            action = self.next_action
            self.next_action = None
            return action

        if self.meeting_point is not None and self.knowledge.position != self.meeting_point:
            return self.move_towards(self.meeting_point)

        if (
            self.meeting_point
            and self.knowledge.position == self.meeting_point
            and self.protocol_step != ProtocolStep.TRANSFER
        ):
            self.messages_service.send_message(
                Message(
                    sender=self.name,
                    receiver=self.current_partner,
                    performative=Performative.PROPOSE,
                    type=MessageType.TRANSFER_PROPOSAL,
                    data={},
                ),
            )
            return Action(ActionType.IDLE)

        return None


class GreenRobot(BaseRobot):
    colour = Colour.GREEN
    allowed_zones = [Z1]
    allowed_pick = [WasteType.GREEN]
    allowed_transform = WasteType.GREEN

    def __init__(self, model: Model, name: str, strategy: Strategy) -> None:
        super().__init__(model, name, strategy)

        if strategy == Strategy.COMMUNICATION:
            self.target_position = (model.zone_width - 1, model.height // 2)

    def deliberate_random(self) -> Action:
        """
        Decision policy for the random strategy of the green robot

        Priority:
            1. If carrying transformed waste -> move right or drop if blocked
            2. If holding 2 green wastes -> transform
            3. If green waste present -> pick
            4. Otherwise -> random move but if waste close go on the tile

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

        if any(
            (w.type in self.allowed_pick and w.type == self.allowed_transform) for w in tile.wastes
        ):
            return Action(ActionType.PICK)

        return self.random_move([self.allowed_transform])

    def deliberate_communication(self) -> Action:
        """
        Decision policy for the communication strategy of the green robot

        Priority:

        Returns
        -------
        Action
            The selected action
        """
        protocol_action = self.transfert_protocol()
        current_pos = self.knowledge.position
        tile = self.knowledge.map_memory.get(current_pos)
        next_type = self.allowed_transform.next() if self.allowed_transform else None

        if protocol_action is not None:
            return protocol_action

        if self.knowledge.waste_count.get(self.allowed_transform, 0) == 1 and self.inventory.has(
            self.allowed_transform,
        ):
            if current_pos == self.target_position:
                return Action(ActionType.DROP, {"type": self.allowed_transform})
            return self.move_towards(self.target_position)

        if self.need_communication():
            self.start_communication(self.allowed_transform)
            return Action(ActionType.IDLE)

        if next_type and self.inventory.has(next_type):
            if current_pos == self.target_position:
                return Action(ActionType.DROP, {"type": next_type})
            return self.move_towards(self.target_position)

        if self.allowed_transform and self.inventory.count(self.allowed_transform) == 2:
            return Action(ActionType.TRANSFORM)

        if any(
            (w.type in self.allowed_pick and w.type == self.allowed_transform) for w in tile.wastes
        ):
            return Action(ActionType.PICK)

        return self.random_move([self.allowed_transform])


class YellowRobot(BaseRobot):
    colour = Colour.YELLOW
    allowed_zones = [Z1, Z2]
    allowed_pick = [WasteType.GREEN, WasteType.YELLOW]
    allowed_transform = WasteType.YELLOW

    def __init__(self, model: Model, name: str, strategy: Strategy) -> None:
        super().__init__(model, name, strategy)

        if strategy == Strategy.COMMUNICATION:
            self.start_position = (model.zone_width - 1, model.height // 2)
            self.target_position = (model.zone_width * 2 - 1, model.height // 2)

    def deliberate_random(self) -> Action:
        """
        Decision policy for the random strategy of the yellow robot

        Priority:
            1. If carrying transformed waste -> move right or drop if blocked
            2. If holding 2 yellow wastes -> transform
            3. If yellow waste present -> pick
            4. Otherwise -> random move but if waste close go on the tile

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

        if any(
            (w.type in self.allowed_pick and w.type == self.allowed_transform) for w in tile.wastes
        ):
            return Action(ActionType.PICK)

        return self.random_move([self.allowed_transform])

    def deliberate_communication(self) -> Action:
        """
        Decision policy for the communication strategy of the yellow robot

        Returns
        -------
        Action
            The selected action
        """


class RedRobot(BaseRobot):
    colour = Colour.RED
    allowed_zones = [Z1, Z2, Z3]
    allowed_pick = [WasteType.GREEN, WasteType.YELLOW, WasteType.RED]
    allowed_transform = None

    def __init__(self, model: Model, name: str, strategy: Strategy) -> None:
        super().__init__(model, name, strategy)

        if strategy == Strategy.COMMUNICATION:
            self.start_position = (model.zone_width * 2 - 1, model.height // 2)
            self.target_position = (model.zone_width * 3 - 1, model.height // 2)

    def deliberate_random(self) -> Action:
        """
        Decision policy for the random strategy of the red robot

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

    def deliberate_communication(self) -> Action:
        """
        Decision policy for the communication strategy of the red robot

        Returns
        -------
        Action
            The selected action
        """
