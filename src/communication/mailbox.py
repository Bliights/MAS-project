from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.communication.enums import Message


class Mailbox:
    """Mailbox class.
    Class implementing the mailbox object which manages messages in communicating agents.

    attr:
        unread_messages: The list of unread messages
        read_messages: The list of read messages
    """

    def __init__(self) -> None:
        """Create a new Mailbox."""
        self.unread_messages = []
        self.read_messages = []

    def receive_messages(self, message: Message) -> None:
        """Receive a message and add it in the unread messages list."""
        self.unread_messages.append(message)

    def get_new_messages(self) -> list[Message]:
        """Return all the messages from unread messages list."""
        unread_messages = self.unread_messages.copy()
        if len(unread_messages) > 0:
            for messages in unread_messages:
                self.read_messages.append(messages)
        self.unread_messages.clear()
        return unread_messages
