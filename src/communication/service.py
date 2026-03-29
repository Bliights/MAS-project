"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mesa import Agent, Model

    from src.communication.enums import Message


class MessageService:
    def __init__(self, model: Model, instant_delivery: bool = True) -> None:
        """
        Initialize a message service used to route messages between agents

        Parameters
        ----------
        model : Model
            The simulation model
        instant_delivery : bool, optional
            If True, messages are delivered immediately when sent, otherwise they are stored and delivered later when
            dispatch_messages is called
        """
        self.model = model
        self.instant_delivery = instant_delivery
        self.messages_to_proceed = []

    def send_message(self, message: Message) -> None:
        """
        Send a message through the service

        Parameters
        ----------
        message : Message
            The message to send
        """
        if self.instant_delivery:
            self.dispatch_message(message)
        else:
            self.messages_to_proceed.append(message)

    def dispatch_message(self, message: Message) -> None:
        """
        Deliver a message to its receiver

        Parameters
        ----------
        message : Message
            The message to dispatch
        """
        agent = self.find_agent_from_name(message.receiver)
        if agent:
            agent.mailbox.receive_messages(message)

    def dispatch_messages(self) -> None:
        """
        Dispatch all messages currently waiting in the pending queue
        """
        if len(self.messages_to_proceed) > 0:
            for message in self.messages_to_proceed:
                self.dispatch_message(message)

        self.messages_to_proceed.clear()

    def find_agent_from_name(self, agent_name: str) -> Agent | None:
        """
        Find an agent in the model from its name

        Parameters
        ----------
        agent_name : str
            The name of the agent to search for

        Returns
        -------
        Agent | None
            The matching agent if found, otherwise None
        """
        for agent in self.model.agents:
            if getattr(agent, "name", None) == agent_name:
                return agent
        return None
