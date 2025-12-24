"""
gRPC servicer implementation using grpc.aio API.
"""

import asyncio
import logging
from datetime import datetime
from typing import AsyncIterator

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from grpc import aio

from chat_project.generated import chat_pb2, chat_pb2_grpc

from .core.chat_room import ChatRoom
from .core.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


def datetime_to_proto(dt: datetime) -> Timestamp:
    """Convert Python datetime to protobuf Timestamp."""
    timestamp = Timestamp()
    timestamp.FromDatetime(dt)
    return timestamp


class ChatServicer(chat_pb2_grpc.ChatServiceServicer):
    """Implements the gRPC ChatService using async API."""

    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.global_room = ChatRoom(name="global")
        logger.info("ChatServicer initialized")

    async def JoinChat(
        self,
        request: chat_pb2.JoinRequest,
        context: aio.ServicerContext,
    ) -> chat_pb2.JoinResponse:
        """Handle client join request with username validation."""
        user_name = request.user_name.strip()

        if not user_name:
            return chat_pb2.JoinResponse(
                success=False,
                message="Username cannot be empty",
            )

        try:
            # Get peer information for logging
            peer = context.peer() if hasattr(context, "peer") else "unknown"

            # Add client to connection manager
            client = await self.connection_manager.add_client(user_name, peer)

            # Broadcast user joined event
            user_event = chat_pb2.ChatEvent(
                user_event=chat_pb2.UserEvent(
                    action=chat_pb2.UserEvent.Action.JOINED,
                    user_name=user_name,
                )
            )
            await self.connection_manager.broadcast_event(user_event)

            logger.info(f"User '{user_name}' joined successfully from {peer}")

            return chat_pb2.JoinResponse(
                success=True,
                message=f"Welcome {user_name}! There are {self.connection_manager.client_count - 1} other users online.",
            )

        except ValueError as e:
            logger.warning(f"Join failed for '{user_name}': {e}")
            return chat_pb2.JoinResponse(
                success=False,
                message=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error during join: {e}")
            return chat_pb2.JoinResponse(
                success=False,
                message="Internal server error",
            )

    async def SendMessage(
        self,
        request: chat_pb2.ChatMessage,
        context: aio.ServicerContext,
    ) -> chat_pb2.Empty:
        """Handle incoming chat messages from clients."""
        user_name = request.user

        # Verify user is connected
        client = await self.connection_manager.get_client(user_name)
        if not client:
            logger.warning(f"Message from disconnected user: {user_name}")
            return chat_pb2.Empty()

        try:
            # Store message
            stored_message = await self.global_room.add_message(
                user=user_name,
                text=request.text,
            )

            # Create ChatEvent with timestamp
            chat_event = chat_pb2.ChatEvent(
                message=chat_pb2.ChatMessage(
                    user=user_name,
                    text=request.text,
                    room=request.room or "global",
                    timestamp=datetime_to_proto(stored_message.timestamp),
                )
            )

            # Broadcast to all clients
            await self.connection_manager.broadcast_event(chat_event)

            logger.debug(f"Broadcast message from '{user_name}'")
            return chat_pb2.Empty()

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def StreamMessages(
        self,
        request: chat_pb2.Empty,
        context: aio.ServicerContext,
    ) -> AsyncIterator[chat_pb2.ChatEvent]:
        """Stream chat events to a connected client."""
        # Extract username from metadata
        metadata = dict(context.invocation_metadata())
        user_name = metadata.get("user")

        if not user_name:
            await context.abort(
                grpc.StatusCode.UNAUTHENTICATED, "User identification required"
            )
            return

        client = await self.connection_manager.get_client(user_name)
        if not client:
            await context.abort(grpc.StatusCode.NOT_FOUND, "User not found")
            return

        logger.info(f"Starting message stream for '{user_name}'")

        try:
            # Send recent history
            recent_messages = await self.global_room.get_recent_messages(20)
            for msg in recent_messages:
                yield chat_pb2.ChatEvent(
                    message=chat_pb2.ChatMessage(
                        user=msg.user,
                        text=msg.text,
                        room=msg.room,
                        timestamp=datetime_to_proto(msg.timestamp),
                    )
                )

            # Send welcome notice
            yield chat_pb2.ChatEvent(
                notice=chat_pb2.ServerNotice(
                    text=f"Welcome! {self.connection_manager.client_count} users online."
                )
            )

            # Stream new messages
            # FIX: Use context.done() to check if stream is still active
            while not context.done():
                try:
                    # Get next message with timeout
                    event = await asyncio.wait_for(
                        client.message_queue.get(),
                        timeout=0.5,
                    )
                    yield event
                except asyncio.TimeoutError:
                    # Continue checking if context is done
                    continue
                except asyncio.CancelledError:
                    logger.debug(f"Stream cancelled for '{user_name}'")
                    break

        except Exception as e:
            logger.error(f"Stream error: {e}")
            # Don't abort here - just let the stream end naturally
        finally:
            # Clean up on disconnect
            if user_name:
                await self.connection_manager.remove_client(user_name)
                user_event = chat_pb2.ChatEvent(
                    user_event=chat_pb2.UserEvent(
                        action=chat_pb2.UserEvent.Action.LEFT,
                        user_name=user_name,
                    )
                )
                await self.connection_manager.broadcast_event(user_event)
                logger.info(f"Message stream ended for '{user_name}'")
