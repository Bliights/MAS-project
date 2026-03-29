"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.communication.enums import Message


class Mailbox:
    def __init__(self) -> None:
        self.unread_messages = []
        self.read_messages = []
        self.outbox_messages = []
        self.has_unread_messages = False

    def receive_messages(self, message: Message) -> None:
        """
        Receive a message and store it as unread

        Parameters
        ----------
        message : Message
            The message received by the agent
        """
        self.unread_messages.append(message)
        self.has_unread_messages = True

    def queue_outgoing(self, message: Message) -> None:
        """
        Add a message to the outgoing queue

        Parameters
        ----------
        message : Message
            The message to send later
        """
        self.outbox_messages.append(message)

    def has_outgoing_messages(self) -> bool:
        """
        Check whether the mailbox contains messages waiting to be sent

        Returns
        -------
        bool
            True if at least one message is in the outbox
        """
        return len(self.outbox_messages) > 0

    def flush_outbox(self) -> list[Message]:
        """
        Return all queued outgoing messages and clear the outbox

        Returns
        -------
        list[Message]
            The list of outgoing messages that were waiting to be sent
        """
        messages = self.outbox_messages.copy()
        self.outbox_messages.clear()
        return messages

    def get_new_messages(self) -> list[Message]:
        """
        Return all unread messages and mark them as read

        Returns
        -------
        list[Message]
            The list of newly received unread messages
        """
        unread_messages = self.unread_messages.copy()
        if len(unread_messages) > 0:
            for messages in unread_messages:
                self.read_messages.append(messages)
        self.unread_messages.clear()
        self.has_unread_messages = False
        return unread_messages

    def has_unread_matching(self, predicate: Callable[[Message], bool]) -> bool:
        """
        Check whether at least one unread message satisfies a condition

        Parameters
        ----------
        predicate : Callable[[Message], bool]
            A function that takes a message as input and returns True

        Returns
        -------
        bool
            True if at least one unread message satisfies the predicate, False otherwise
        """
        return any(predicate(message) for message in self.unread_messages)
