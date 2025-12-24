"""
Async gRPC client for the chat system
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from grpc import aio

from chat_project.generated import chat_pb2, chat_pb2_grpc

logger = logging.getLogger(__name__)


class ChatClient:
    """Async gRPC client for chat service"""

    def __init__(self, server_host: str = "localhost", server_port: int = 50051):
        self.server_host = server_host
        self.server_port = server_port
        self.channel: Optional[aio.Channel] = None
        self.stub: Optional[chat_pb2_grpc.ChatServiceStub] = None
        self.user_name: Optional[str] = None
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._stream_task: Optional[asyncio.Task] = None
        self._connected = False
        self._shutdown_event = asyncio.Event()

    async def connect(self, user_name: str, use_local_credentials: bool = True) -> bool:
        """Connect to the chat server and join chat."""
        if self._connected:
            logger.warning("Already connected")
            return True

        self.user_name = user_name
        self._shutdown_event.clear()

        try:
            # Create channel
            target = f"{self.server_host}:{self.server_port}"

            if use_local_credentials:
                channel_credentials = grpc.local_channel_credentials()
                self.channel = aio.secure_channel(target, channel_credentials)
            else:
                self.channel = aio.insecure_channel(target)

            # Use the unified ChatServiceStub
            self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)

            # Join chat
            join_response = await self.stub.JoinChat(
                chat_pb2.JoinRequest(user_name=user_name), timeout=10.0
            )

            if not join_response.success:
                logger.error(f"Failed to join: {join_response.message}")
                await self.disconnect()
                return False

            logger.info(f"Connected as '{user_name}'")
            self._connected = True

            # Start the non-polling message stream
            self._stream_task = asyncio.create_task(self._stream_messages_forever())

            return True

        except grpc.aio.AioRpcError as e:
            logger.error(f"gRPC connection error: {e.code()}, {e.details()}")
            await self.disconnect()
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            await self.disconnect()
            return False

    async def _stream_messages_forever(self):
        """Continuously stream messages without polling."""
        if not self.stub or not self.user_name:
            return

        metadata = (("user", self.user_name),)
        retry_count = 0
        max_retries = 3

        while not self._shutdown_event.is_set() and retry_count < max_retries:
            try:
                # Direct async iteration over the gRPC stream
                async for event in self.stub.StreamMessages(
                    chat_pb2.Empty(), metadata=metadata, timeout=None
                ):
                    # Non-blocking put with timeout to prevent deadlock
                    try:
                        await asyncio.wait_for(
                            self._message_queue.put(event), timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        logger.warning("Message queue full, dropping message")

                    # Check if we should stop
                    if self._shutdown_event.is_set():
                        break

                # If we get here, the stream ended gracefully
                break

            except grpc.aio.AioRpcError as e:
                if e.code() == grpc.StatusCode.CANCELLED:
                    break  # Normal shutdown

                logger.error(f"Stream error: {e.code()}, {e.details()}")
                retry_count += 1

                if retry_count < max_retries:
                    logger.info(
                        f"Retrying connection in 2 seconds (attempt {retry_count}/{max_retries})"
                    )
                    await asyncio.sleep(2)
                else:
                    break

            except Exception as e:
                logger.error(f"Unexpected stream error: {e}")
                break

        self._connected = False

    async def wait_for_message(self):
        """
        Wait for the next message from the server.
        Returns None if the stream has ended.
        """
        try:
            return await self._message_queue.get()
        except asyncio.CancelledError:
            return None

    async def send_message(self, text: str, room: str = "global") -> bool:
        """Send a chat message to the server."""
        if not self._connected or not self.stub:
            logger.error("Not connected to server")
            return False

        try:
            timestamp = Timestamp()
            timestamp.FromDatetime(datetime.now())

            message = chat_pb2.ChatMessage(
                user=self.user_name, text=text, room=room, timestamp=timestamp
            )

            await self.stub.SendMessage(message, timeout=5.0)
            return True

        except grpc.aio.AioRpcError as e:
            logger.error(f"Failed to send message: {e.code()}, {e.details()}")
            if e.code() in (
                grpc.StatusCode.UNAVAILABLE,
                grpc.StatusCode.DEADLINE_EXCEEDED,
            ):
                self._connected = False
            return False
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False

    async def disconnect(self):
        """Gracefully disconnect from the server."""
        self._shutdown_event.set()
        self._connected = False

        # Cancel stream task
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass

        # Close channel
        if self.channel:
            await self.channel.close()

        # Clear the queue to unblock any waiting tasks
        while not self._message_queue.empty():
            try:
                self._message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        logger.info("Disconnected from server")

    @property
    def is_connected(self) -> bool:
        """Check if client is connected and streaming."""
        return self._connected and not self._shutdown_event.is_set()
