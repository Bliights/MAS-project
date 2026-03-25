from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mesa import Agent, Model

    from src.communication.enums import Message


class MessageService:
    _instance = None

    @staticmethod
    def get_instance() -> MessageService:
        """Static access method."""
        return MessageService._instance

    def __init__(self, model: Model, instant_delivery: bool = True) -> None:
        """Create a new MessageService object."""
        if MessageService._instance is not None:
            raise Exception("This class is a singleton!")
        MessageService._instance = self
        self.model = model
        self.instant_delivery = instant_delivery
        self.messages_to_proceed = []

    def send_message(self, message: Message) -> None:
        """Dispatch message if instant delivery active, otherwise add the message to proceed list."""
        if self.instant_delivery:
            self.dispatch_message(message)
        else:
            self.messages_to_proceed.append(message)

    def dispatch_message(self, message: Message) -> None:
        """Dispatch the message to the right agent."""
        agent = self.find_agent_from_name(message.receiver)
        if agent:
            agent.mailbox.receive_messages(message)

    def dispatch_messages(self) -> None:
        """Proceed each message received by the message service."""
        if len(self.messages_to_proceed) > 0:
            for message in self.messages_to_proceed:
                self.dispatch_message(message)

        self.messages_to_proceed.clear()

    def find_agent_from_name(self, agent_name: str) -> Agent | None:
        """Return the agent according to the agent name given."""
        for agent in self.model.agents:
            if getattr(agent, "name", None) == agent_name:
                return agent
        return None
