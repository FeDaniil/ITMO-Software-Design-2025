"""
Manages chat rooms and message history.
Designed for extensibility to multiple rooms.
"""
import asyncio
from typing import List
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class StoredMessage:
    """Represents a stored chat message with metadata."""
    user: str
    text: str
    timestamp: datetime
    room: str = "global"


class ChatRoom:
    """Manages a single chat room with message history."""

    def __init__(self, name: str = "global", max_history: int = 1000):
        self.name = name
        self.max_history = max_history
        self.message_history: deque[StoredMessage] = deque(maxlen=max_history)
        self._lock = asyncio.Lock()

    async def add_message(self, user: str, text: str) -> StoredMessage:
        """Add a new message to the room's history."""
        message = StoredMessage(
            user=user,
            text=text,
            timestamp=datetime.now(),
            room=self.name
        )

        async with self._lock:
            self.message_history.append(message)

        logger.debug(f"Message from {user} added to room {self.name}")
        return message

    async def get_recent_messages(self, count: int = 50) -> List[StoredMessage]:
        """Get recent messages from the room's history."""
        async with self._lock:
            return list(self.message_history)[-count:]

    @property
    def message_count(self) -> int:
        """Get current number of messages in history."""
        return len(self.message_history)
