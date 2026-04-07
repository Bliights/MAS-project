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

from src.communication.enums import Message, MessageType, Performative
from src.communication.mailbox import Mailbox
from src.core.actions import Action
from src.core.enums import ActionType, Colour, ProtocolStep, Strategy, WasteType
from src.core.inventory import Inventory
from src.core.knowledge import Knowledge
from src.core.zones import Z1, Z2, Z3, Zone


class BaseRobot(Agent, ABC):
    colour: Colour | None = None
    allowed_zones: list[Zone] = []
    allowed_pick: list[WasteType] | None
    allowed_transform: WasteType | None

    def __init__(self, model: Model, name: str, strategy: Strategy) -> None:
        """
        Initialize the robots

        Parameters
        ----------
        model : Model
            The simulation model
        name : str
            Unique identifier of the robot
        strategy : Strategy
            Decision strategy
        """
        super().__init__(model)
        self.knowledge = Knowledge()
        self.inventory = Inventory()
        self.name = name
        self.strategy = strategy
        self.reserved_tiles = set()
        self.last_infos = {
            "agent": self.name,
            "pos": self.pos,
            "status": self.protocol_step.name if hasattr(self, "protocol_step") else "-",
            "wastes": list(self.inventory.wastes),
        }

        if strategy == Strategy.COMMUNICATION:
            self.init_communication()

    def init_communication(self) -> None:
        """
        Initialize communication-related attributes for the robot
        """
        self.mailbox = Mailbox()
        self.cooldown_duration = 10
        self.available = 0
        self.current_partner = None
        self.meeting_point = None
        self.next_action = None
        self.protocol_step = ProtocolStep.NONE

    def step(self) -> None:
        """
        Execute one simulation step
        """
        action = self.deliberate()
        self.last_infos = {
            "agent": self.name,
            "pos": self.pos,
            "status": self.protocol_step.name if hasattr(self, "protocol_step") else "-",
            "available": self.available if hasattr(self, "available") else -1,
            "reserved": sorted(self.reserved_tiles),
            "current_partner": self.current_partner if hasattr(self, "current_partner") else "-",
            "meeting_point": self.meeting_point if hasattr(self, "meeting_point") else "-",
            "wastes": list(self.inventory.wastes),
            "message_receive": list(self.mailbox.unread_messages)
            if hasattr(self, "mailbox")
            else [],
            "message_outbox": list(self.mailbox.outbox_messages)
            if hasattr(self, "mailbox")
            else [],
            "action": action.type.name,
            "payload": action.payload,
        }
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

        if pos in self.reserved_tiles and pos != self.meeting_point:
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
        """
        Move the agent one step closer to a destination

        Parameters
        ----------
        destination : tuple[int, int]
            Target position to reach

        Returns
        -------
        Action
            MOVE action toward the destination or a fallback random move
        """
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
        """
        Determine whether the robot should initiate a communication protocol

        Returns
        -------
        bool
            True if communication should be started, False otherwise
        """
        if self.inventory.count(self.allowed_transform) < 1:
            return False
        if self.protocol_step != ProtocolStep.NONE:
            return False
        waste_type = self.allowed_transform
        prev_types = waste_type.all_previous()

        waste_count = self.knowledge.waste_count.get(waste_type, 0)
        prev_count = sum([self.knowledge.waste_count.get(prev, 0) for prev in prev_types])

        robot_carrying = self.knowledge.agent_carrying.get(waste_type, 0)
        return waste_count > 1 and waste_count == robot_carrying and prev_count <= 1

    def can_start_search(self) -> bool:
        """
        Check whether the robot is allowed to start a communication search phase

        Returns
        -------
        bool
            True if the robot can start searching for a partner
        """
        return self.protocol_step == ProtocolStep.NONE and self.model.current_step >= self.available

    def reset_protocol(self) -> None:
        """
        Reset the communication protocol state
        """
        self.current_partner = None
        self.meeting_point = None
        self.next_action = None
        self.protocol_step = ProtocolStep.NONE
        self.available = self.model.current_step

    def choose_meeting_point(self) -> tuple[int, int]:
        """
        Select a valid meeting point for communication

        Returns
        -------
        tuple[int, int]
            Selected meeting position
        """
        forbidden_positions = {
            pos
            for pos in (
                getattr(self, "target_position", None),
                getattr(self, "start_position", None),
            )
            if pos is not None
        }

        candidates = [
            pos
            for pos, tile in self.knowledge.map_memory.items()
            if tile.zone in self.allowed_zones
            and pos not in self.reserved_tiles
            and pos not in forbidden_positions
        ]

        if not candidates:
            return self.knowledge.position

        return random.choice(candidates)

    def must_read_messages(self) -> bool:
        """
        Determine whether the robot should read incoming messages

        Returns
        -------
        bool
            True if there are relevant unread messages to process
        """
        if self.protocol_step in {
            ProtocolStep.COMMUNICATING,
            ProtocolStep.MOVING,
            ProtocolStep.TRANSFERING,
        }:
            return self.mailbox.has_unread_matching(
                lambda m: (
                    m.sender == self.current_partner
                    or m.type in {MessageType.RESERVED_TILE_INFORM, MessageType.FREE_TILE_INFORM}
                ),
            )
        if self.protocol_step == ProtocolStep.WAITING_CONNECTION:
            return self.mailbox.has_unread_matching(
                lambda m: (
                    (
                        m.sender == self.current_partner
                        and m.performative
                        in {Performative.ACCEPT_PROPOSAL, Performative.REJECT_PROPOSAL}
                    )
                    or m.type in {MessageType.RESERVED_TILE_INFORM, MessageType.FREE_TILE_INFORM}
                ),
            )

        if self.protocol_step == ProtocolStep.SEARCHING:
            return self.mailbox.has_unread_matching(
                lambda m: (
                    (
                        m.performative == Performative.PROPOSE
                        and m.type == MessageType.COMMUNICATION_PROPOSAL
                    )
                    or m.type in {MessageType.RESERVED_TILE_INFORM, MessageType.FREE_TILE_INFORM}
                    or (m.performative == Performative.CFP and m.type == MessageType.WASTE_CFP)
                ),
            )

        return self.mailbox.has_unread_messages

    def all_present(self) -> bool:
        """
        Check whether both agents are present at the meeting point

        Returns
        -------
        bool
            True if both the robot and its partner are at the meeting point
        """
        if self.current_partner is None:
            return False

        for agent in self.knowledge.agents:
            if agent.name == self.current_partner:
                return agent.pos == self.knowledge.position == self.meeting_point

        return False

    def process_messages(self, messages: list[Message]) -> None:
        """
        Process a list of incoming messages

        Parameters
        ----------
        messages : list[Message]
            Messages to process
        """
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

    def broadcast_tile_reserved(self, pos: tuple[int, int]) -> None:
        """
        Inform all agents that a tile has been reserved

        Parameters
        ----------
        pos : tuple[int, int]
            Position of the reserved tile
        """
        for agent in self.knowledge.agents:
            self.mailbox.queue_outgoing(
                Message(
                    sender=self.name,
                    receiver=agent.name,
                    performative=Performative.INFORM,
                    type=MessageType.RESERVED_TILE_INFORM,
                    data={"pos": pos},
                ),
            )

    def broadcast_tile_freed(self, pos: tuple[int, int]) -> None:
        """
        Inform all agents that a tile is no longer reserved

        Parameters
        ----------
        pos : tuple[int, int]
            Position of the freed tile
        """
        for agent in self.knowledge.agents:
            self.mailbox.queue_outgoing(
                Message(
                    sender=self.name,
                    receiver=agent.name,
                    performative=Performative.INFORM,
                    type=MessageType.FREE_TILE_INFORM,
                    data={"pos": pos},
                ),
            )

    def start_communication(self, waste_type: WasteType) -> None:
        """
        Initiate a communication protocol to exchange a specific waste type

        Parameters
        ----------
        waste_type : WasteType
            Type of waste involved in the communication
        """
        self.protocol_step = ProtocolStep.SEARCHING
        self.available = self.model.current_step + self.cooldown_duration

        for agent in self.knowledge.agents:
            self.mailbox.queue_outgoing(
                Message(
                    sender=self.name,
                    receiver=agent.name,
                    performative=Performative.CFP,
                    type=MessageType.WASTE_CFP,
                    data={"waste": waste_type},
                ),
            )

    def other_has_priority(self, other_name: str) -> bool:
        """
        Determine if another agent has priority over this one

        Parameters
        ----------
        other_name : str
            Name of the other agent

        Returns
        -------
        bool
            True if the other agent has priority
        """
        return other_name < self.name

    def handle_cfp(self, message: Message) -> None:
        """
        Handle a CFP message

        Parameters
        ----------
        message : Message
            Incoming CFP message
        """
        if self.protocol_step in {
            ProtocolStep.WAITING_CONNECTION,
            ProtocolStep.COMMUNICATING,
            ProtocolStep.MOVING,
            ProtocolStep.TRANSFERING,
        }:
            self.mailbox.queue_outgoing(
                Message(
                    sender=self.name,
                    receiver=message.sender,
                    performative=Performative.REFUSE,
                    type=MessageType.REFUSE_CFP,
                    data={},
                ),
            )
        elif self.protocol_step == ProtocolStep.SEARCHING:
            if self.other_has_priority(message.sender) and self.inventory.has(
                message.data["waste"],
            ):
                self.protocol_step = ProtocolStep.WAITING_CONNECTION
                self.current_partner = message.sender
                self.available = self.model.current_step + self.cooldown_duration
                self.mailbox.queue_outgoing(
                    Message(
                        sender=self.name,
                        receiver=message.sender,
                        performative=Performative.PROPOSE,
                        type=MessageType.COMMUNICATION_PROPOSAL,
                        data={},
                    ),
                )
            else:
                self.mailbox.queue_outgoing(
                    Message(
                        sender=self.name,
                        receiver=message.sender,
                        performative=Performative.REFUSE,
                        type=MessageType.REFUSE_CFP,
                        data={},
                    ),
                )
        elif self.protocol_step == ProtocolStep.NONE:
            if self.inventory.has(message.data["waste"]):
                self.protocol_step = ProtocolStep.WAITING_CONNECTION
                self.current_partner = message.sender
                self.available = self.model.current_step + self.cooldown_duration
                self.mailbox.queue_outgoing(
                    Message(
                        sender=self.name,
                        receiver=message.sender,
                        performative=Performative.PROPOSE,
                        type=MessageType.COMMUNICATION_PROPOSAL,
                        data={},
                    ),
                )
            else:
                self.mailbox.queue_outgoing(
                    Message(
                        sender=self.name,
                        receiver=message.sender,
                        performative=Performative.REFUSE,
                        type=MessageType.REFUSE_CFP,
                        data={},
                    ),
                )

    def handle_propose(self, message: Message) -> None:
        """
        Handle a proposal message

        Parameters
        ----------
        message : Message
            Incoming proposal message
        """
        if message.type == MessageType.COMMUNICATION_PROPOSAL:
            if self.protocol_step == ProtocolStep.SEARCHING:
                self.protocol_step = ProtocolStep.COMMUNICATING
                self.current_partner = message.sender
                self.available = self.model.current_step
                self.mailbox.queue_outgoing(
                    Message(
                        sender=self.name,
                        receiver=message.sender,
                        performative=Performative.ACCEPT_PROPOSAL,
                        type=MessageType.COMMUNICATION_ACCEPT,
                        data={},
                    ),
                )
            else:
                self.mailbox.queue_outgoing(
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
                self.mailbox.queue_outgoing(
                    Message(
                        sender=self.name,
                        receiver=message.sender,
                        performative=Performative.REJECT_PROPOSAL,
                        type=MessageType.TRANSFER_REJECT,
                        data={},
                    ),
                )
            else:
                self.protocol_step = ProtocolStep.TRANSFERING
                self.mailbox.queue_outgoing(
                    Message(
                        sender=self.name,
                        receiver=message.sender,
                        performative=Performative.ACCEPT_PROPOSAL,
                        type=MessageType.TRANSFER_ACCEPT,
                        data={},
                    ),
                )

    def handle_accept(self, message: Message) -> None:
        """
        Handle an acceptance message

        Parameters
        ----------
        message : Message
            Incoming acceptance message
        """
        if message.type == MessageType.COMMUNICATION_ACCEPT:
            self.available = self.model.current_step
            self.protocol_step = ProtocolStep.MOVING
            self.meeting_point = self.choose_meeting_point()
            self.reserved_tiles.add(self.meeting_point)
            self.broadcast_tile_reserved(self.meeting_point)

            self.mailbox.queue_outgoing(
                Message(
                    sender=self.name,
                    receiver=message.sender,
                    performative=Performative.REQUEST,
                    type=MessageType.MOVE_TO_TILE_REQUEST,
                    data={"pos": self.meeting_point},
                ),
            )

        elif message.type == MessageType.TRANSFER_ACCEPT:
            self.protocol_step = ProtocolStep.TRANSFERING
            self.next_action = Action(ActionType.DROP, {"type": self.allowed_transform})
            self.mailbox.queue_outgoing(
                Message(
                    sender=self.name,
                    receiver=message.sender,
                    performative=Performative.INFORM,
                    type=MessageType.EXCHANGE_INFORM,
                    data={"type": self.allowed_transform},
                ),
            )

    def handle_request(self, message: Message) -> None:
        """
        Handle a request message

        Parameters
        ----------
        message : Message
            Incoming request message
        """
        if message.type == MessageType.MOVE_TO_TILE_REQUEST:
            self.meeting_point = message.data["pos"]
            self.protocol_step = ProtocolStep.MOVING
            self.mailbox.queue_outgoing(
                Message(
                    sender=self.name,
                    receiver=message.sender,
                    performative=Performative.AGREE,
                    type=MessageType.MOVE_TO_TILE_AGREE,
                    data={},
                ),
            )

    def handle_inform(self, message: Message) -> None:
        """
        Handle an inform message

        Parameters
        ----------
        message : Message
            Incoming inform message
        """
        if message.type == MessageType.RESERVED_TILE_INFORM:
            self.reserved_tiles.add(message.data["pos"])
        elif message.type == MessageType.FREE_TILE_INFORM:
            self.reserved_tiles.discard(message.data["pos"])
        elif message.type == MessageType.EXCHANGE_INFORM:
            self.mailbox.queue_outgoing(
                Message(
                    sender=self.name,
                    receiver=message.sender,
                    performative=Performative.CONFIRM,
                    type=MessageType.EXCHANGE_CONFIRM,
                    data={},
                ),
            )
            self.reset_protocol()
            self.next_action = Action(ActionType.PICK, {"type": message.data["type"]})

    def handle_confirm(self, message: Message) -> None:
        """
        Handle a confirmation message

        Parameters
        ----------
        message : Message
            Incoming confirmation message
        """
        if message.type == MessageType.EXCHANGE_CONFIRM:
            old_meeting_point = self.meeting_point
            self.reset_protocol()
            self.reserved_tiles.discard(old_meeting_point)
            self.broadcast_tile_freed(old_meeting_point)

    def transfert_protocol(self) -> Action | None:
        """
        Execute the communication protocol logic

        Returns
        -------
        Action | None
            The next action dictated by the protocol, or None if inactive
        """
        if self.next_action is not None:
            action = self.next_action
            self.next_action = None
            return action

        if self.mailbox.has_outgoing_messages():
            return Action(ActionType.SEND_MESSAGES)

        if self.must_read_messages():
            return Action(ActionType.READ_MESSAGES)

        if self.model.current_step >= self.available and (
            self.protocol_step == ProtocolStep.SEARCHING
            or self.protocol_step == ProtocolStep.WAITING_CONNECTION
        ):
            self.protocol_step = ProtocolStep.NONE
            self.available = self.model.current_step + self.cooldown_duration
            return None

        if self.protocol_step == ProtocolStep.MOVING:
            if self.knowledge.position != self.meeting_point:
                return self.move_towards(self.meeting_point)
            if not self.all_present():
                return Action(ActionType.IDLE)
            if not self.other_has_priority(self.current_partner):
                self.protocol_step = ProtocolStep.TRANSFERING
                self.mailbox.queue_outgoing(
                    Message(
                        sender=self.name,
                        receiver=self.current_partner,
                        performative=Performative.PROPOSE,
                        type=MessageType.TRANSFER_PROPOSAL,
                        data={},
                    ),
                )
                return Action(ActionType.SEND_MESSAGES)
            return Action(ActionType.IDLE)

        if self.protocol_step != ProtocolStep.NONE:
            return Action(ActionType.IDLE)

        return None


class GreenRobot(BaseRobot):
    colour = Colour.GREEN
    allowed_zones = [Z1]
    allowed_pick = [WasteType.GREEN]
    allowed_transform = WasteType.GREEN

    def __init__(self, model: Model, name: str, strategy: Strategy) -> None:
        """
        Initialize a GreenRobot

        Parameters
        ----------
        model : Model
            The simulation model
        name : str
            Unique identifier of the robot
        strategy : Strategy
            Decision strategy
        """
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
            return Action(ActionType.PICK, {"type": self.allowed_transform})

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

        # If a protocole action is needed
        if protocol_action is not None:
            return protocol_action

        # Last waste
        if self.knowledge.waste_count.get(self.allowed_transform, 0) == 1 and self.inventory.has(
            self.allowed_transform,
        ):
            if current_pos == self.target_position:
                return Action(ActionType.DROP, {"type": self.allowed_transform})
            return self.move_towards(self.target_position)

        # Blocked
        if self.need_communication() and self.can_start_search():
            self.start_communication(self.allowed_transform)
            return Action(ActionType.SEND_MESSAGES)

        # Has transformed waste
        if next_type and self.inventory.has(next_type):
            if current_pos == self.target_position:
                return Action(ActionType.DROP, {"type": next_type})
            return self.move_towards(self.target_position)

        # Can transformed
        if self.allowed_transform and self.inventory.count(self.allowed_transform) == 2:
            return Action(ActionType.TRANSFORM)

        # If on a tile with a waste
        if any(
            (w.type in self.allowed_pick and w.type == self.allowed_transform) for w in tile.wastes
        ):
            # To avoid picking the last waste on the target position
            if (
                self.knowledge.waste_count.get(self.allowed_transform, 0) == 1
                and current_pos == self.target_position
            ):
                return Action(ActionType.IDLE)

            return Action(ActionType.PICK, {"type": self.allowed_transform})

        return self.random_move([self.allowed_transform])


class YellowRobot(BaseRobot):
    colour = Colour.YELLOW
    allowed_zones = [Z1, Z2]
    allowed_pick = [WasteType.GREEN, WasteType.YELLOW]
    allowed_transform = WasteType.YELLOW

    def __init__(self, model: Model, name: str, strategy: Strategy) -> None:
        """
        Initialize a YellowRobot

        Parameters
        ----------
        model : Model
            The simulation model
        name : str
            Unique identifier of the robot
        strategy : Strategy
            Decision strategy
        """
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
            return Action(ActionType.PICK, {"type": self.allowed_transform})

        return self.random_move([self.allowed_transform])

    def deliberate_communication(self) -> Action:
        """
        Decision policy for the communication strategy of the yellow robot

        Returns
        -------
        Action
            The selected action
        """
        protocol_action = self.transfert_protocol()
        current_pos = self.knowledge.position
        tile = self.knowledge.map_memory.get(current_pos)
        next_type = self.allowed_transform.next() if self.allowed_transform else None
        prev_types = self.allowed_transform.all_previous()
        prev_count = sum([self.knowledge.waste_count.get(prev, 0) for prev in prev_types])

        # If a protocole action is needed
        if protocol_action is not None:
            return protocol_action

        # Last waste
        if (
            prev_count <= 1
            and self.knowledge.waste_count.get(self.allowed_transform, 0) == 1
            and self.inventory.has(
                self.allowed_transform,
            )
        ):
            if current_pos == self.target_position:
                return Action(ActionType.DROP, {"type": self.allowed_transform})
            return self.move_towards(self.target_position)

        # Blocked
        if self.need_communication() and self.can_start_search():
            self.start_communication(self.allowed_transform)
            return Action(ActionType.SEND_MESSAGES)

        # Has transformed waste
        if next_type and self.inventory.has(next_type):
            if current_pos == self.target_position:
                return Action(ActionType.DROP, {"type": next_type})
            return self.move_towards(self.target_position)

        # Has other waste
        for prev in prev_types:
            if self.inventory.has(prev):
                if current_pos == self.target_position:
                    return Action(ActionType.DROP, {"type": prev})
                return self.move_towards(self.target_position)

        # Can transformed
        if self.allowed_transform and self.inventory.count(self.allowed_transform) == 2:
            return Action(ActionType.TRANSFORM)

        # If on a tile with a waste
        for w in tile.wastes:
            if w.type in self.allowed_pick:
                if w.type == self.allowed_transform:
                    # To avoid picking the last waste on the target position
                    if (
                        self.knowledge.waste_count.get(self.allowed_transform, 0) == 1
                        and current_pos == self.target_position
                    ):
                        return self.move_towards(self.start_position)

                    return Action(ActionType.PICK, {"type": self.allowed_transform})
                # If it's the last waste we pick it
                if self.knowledge.waste_count.get(w.type, 0) == 1:
                    return Action(ActionType.PICK, {"type": w.type})

        if current_pos == self.start_position:
            return Action(ActionType.IDLE)

        return self.move_towards(self.start_position)


class RedRobot(BaseRobot):
    colour = Colour.RED
    allowed_zones = [Z1, Z2, Z3]
    allowed_pick = [WasteType.GREEN, WasteType.YELLOW, WasteType.RED]
    allowed_transform = None

    def __init__(self, model: Model, name: str, strategy: Strategy) -> None:
        """
        Initialize a RedRobot

        Parameters
        ----------
        model : Model
            The simulation model
        name : str
            Unique identifier of the robot
        strategy : Strategy
            Decision strategy
        """
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
            return Action(ActionType.PICK, {"type": WasteType.RED})

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
        protocol_action = self.transfert_protocol()
        current_pos = self.knowledge.position
        tile = self.knowledge.map_memory.get(current_pos)

        # If a protocole action is needed
        if protocol_action is not None:
            return protocol_action

        # Has waste
        for waste_type in self.allowed_pick:
            if self.inventory.has(waste_type):
                if current_pos == self.target_position:
                    return Action(ActionType.DROP, {"type": waste_type})
                return self.move_towards(self.target_position)

        # If on a tile with a waste
        for w in tile.wastes:
            if w.type in self.allowed_pick and current_pos != self.target_position:
                return Action(ActionType.PICK, {"type": w.type})

        if current_pos == self.start_position:
            return Action(ActionType.IDLE)

        return self.move_towards(self.start_position)
