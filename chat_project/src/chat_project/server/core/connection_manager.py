"""
Manages active client connections and message broadcasting.
Uses asyncio primitives for thread safety.
"""
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Client:
    """Represents a connected client with their message queue."""
    user_name: str
    message_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    connected_at: datetime = field(default_factory=datetime.now)
    peer: Optional[str] = None


class ConnectionManager:
    """Thread-safe manager for client connections."""

    def __init__(self):
        self._active_clients: Dict[str, Client] = {}
        self._lock = asyncio.Lock()

    async def add_client(self, user_name: str, peer: str = None) -> Client:
        """Add a new client. Raises ValueError if username is taken."""
        async with self._lock:
            if user_name in self._active_clients:
                raise ValueError(f"Username '{user_name}' is already taken")

            client = Client(user_name=user_name, peer=peer)
            self._active_clients[user_name] = client
            logger.info(f"Client '{user_name}' connected from {peer}")
            return client

    async def remove_client(self, user_name: str):
        """Remove a client from active connections."""
        async with self._lock:
            if user_name in self._active_clients:
                del self._active_clients[user_name]
                logger.info(f"Client '{user_name}' disconnected")

    async def get_active_users(self) -> list[str]:
        """Get list of currently active usernames."""
        async with self._lock:
            return list(self._active_clients.keys())

    async def broadcast_event(self, event, exclude_user: str = None):
        """Broadcast an event to all connected clients."""
        async with self._lock:
            for user_name, client in self._active_clients.items():
                if user_name == exclude_user:
                    continue
                try:
                    await client.message_queue.put(event)
                except Exception as e:
                    logger.error(f"Failed to send event to {user_name}: {e}")

    async def get_client(self, user_name: str) -> Optional[Client]:
        """Get a client by username."""
        async with self._lock:
            return self._active_clients.get(user_name)

    @property
    def client_count(self) -> int:
        """Get number of active clients."""
        return len(self._active_clients)
