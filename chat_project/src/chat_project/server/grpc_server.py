"""
Main gRPC chat server using grpc.aio.server.
Supports local credentials for secure development.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

import grpc
from grpc import aio

from chat_project.generated import chat_pb2_grpc

from .servicer import ChatServicer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ChatServer:
    """Manages the async gRPC server lifecycle."""

    def __init__(self, host: str = "localhost", port: int = 50051):
        self.host = host
        self.port = port
        self.server: Optional[aio.Server] = None
        self._shutdown_event = asyncio.Event()

    async def start(self, use_local_credentials: bool = True) -> None:
        """Start the async gRPC server."""
        # Create async server with optimized settings
        self.server = aio.server(
            options=[
                ("grpc.max_send_message_length", 50 * 1024 * 1024),
                ("grpc.max_receive_message_length", 50 * 1024 * 1024),
                ("grpc.max_concurrent_streams", 100),
                ("grpc.so_reuseport", 1),
            ]
        )

        # Add servicer
        servicer = ChatServicer()
        chat_pb2_grpc.add_ChatServiceServicer_to_server(servicer, self.server)

        # Configure listening address
        listen_addr = f"{self.host}:{self.port}"

        if use_local_credentials:
            # Use local credentials for secure development
            server_credentials = grpc.local_server_credentials()
            self.server.add_secure_port(listen_addr, server_credentials)
            logger.info(f"Server starting with LOCAL credentials on {listen_addr}")
        else:
            # Fallback to insecure for compatibility
            self.server.add_insecure_port(listen_addr)
            logger.info(f"Server starting with INSECURE port on {listen_addr}")

        # Start server
        await self.server.start()
        logger.info(f"Chat server started successfully")

        # Register graceful shutdown handlers
        self._register_signal_handlers()

        # Wait for shutdown
        await self._shutdown_event.wait()

        # Begin graceful shutdown
        await self.stop()

    async def stop(self, grace_period: float = 5.0) -> None:
        """Gracefully stop the server."""
        if self.server:
            logger.info(f"Starting graceful shutdown (timeout: {grace_period}s)")
            self._shutdown_event.set()
            await self.server.stop(grace_period)
            logger.info("Server stopped gracefully")

    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        loop = asyncio.get_event_loop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig, lambda s=sig: asyncio.create_task(self._handle_signal(s))
            )

    async def _handle_signal(self, sig: signal.Signals):
        """Handle shutdown signals."""
        logger.info(f"Received signal {sig.name}")
        await self.stop()


async def main() -> None:
    """Main entry point for the chat server."""
    import argparse

    parser = argparse.ArgumentParser(description="Start the async gRPC chat server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=50051, help="Port to bind to")
    parser.add_argument(
        "--insecure", action="store_true", help="Use insecure connection"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.debug else logging.INFO
    logging.getLogger().setLevel(level)

    server = ChatServer(args.host, args.port)

    try:
        await server.start(use_local_credentials=not args.insecure)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        await server.stop()
        sys.exit(1)


def sync_main() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    sync_main()
