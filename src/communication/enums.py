"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from dataclasses import dataclass
from enum import StrEnum


class Performative(StrEnum):
    CFP = "cfp"
    REFUSE = "refuse"
    PROPOSE = "propose"
    ACCEPT_PROPOSAL = "accept-proposal"
    REJECT_PROPOSAL = "reject-proposal"
    INFORM = "inform"
    CONFIRM = "confirm"
    REQUEST = "request"
    AGREE = "agree"


class MessageType(StrEnum):
    WASTE_CFP = "Do you have a Waste ?"
    REFUSE_CFP = "No I don't have or I am busy"

    COMMUNICATION_PROPOSAL = "Start communicating ?"
    COMMUNICATION_REJECT = "Already busy"
    COMMUNICATION_ACCEPT = "Start of communication"

    RESERVED_TILE_INFORM = "Tile reserved"

    MOVE_TO_TILE_REQUEST = "Move to a tile"
    MOVE_TO_TILE_AGREE = "Ok I am on my way"

    TRANSFER_PROPOSAL = "Can I transfer Waste"
    TRANSFER_REJECT = "Not on the tile yet"
    TRANSFER_ACCEPT = "Ready to reseive"

    EXCHANGE_INFORM = "Waste on ground"
    EXCHANGE_CONFIRM = " Waste received"

    FREE_TILE_INFORM = "Tile available"


@dataclass
class Message:
    sender: str
    receiver: str
    performative: Performative
    type: MessageType
    data: dict
