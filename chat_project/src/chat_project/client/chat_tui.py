"""
Textual TUI application for the chat client.
Uses Textual 6.11.0 features and async workers.
Supports both terminal and web deployment via textual serve.
"""

import asyncio
from datetime import datetime
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Input, RichLog, Static
from textual.worker import Worker, WorkerState

from .grpc_client import ChatClient


class ChatTUI(App):
    """Main Textual TUI application for chat."""

    CSS = """
    Screen {
        background: $surface;
    }

    /* Login screen styling */
    #login_container {
        height: 1fr;
        align: center middle;
    }

    #login_box {
        width: 50%;
        min-height: 10;
        border: solid $primary;
        padding: 2;
        background: $surface;
    }

    #login_title {
        text-align: center;
        text-style: bold;
        margin-bottom: 2;
        color: $primary;
    }

    #username_input {
        width: 100%;
        height: 3;
        margin-bottom: 1;
        background: $surface;
        color: $text;
        border: solid $panel;
    }

    #username_input:focus {
        border: solid $primary;
    }

    #login_button {
        width: 100%;
        height: 3;
        margin-top: 1;
    }

    /* Chat screen styling (initially hidden) */
    #chat_container {
        height: 1fr;
        margin: 1;
        display: none;
    }

    #message_log {
        height: 1fr;
        border: solid $primary;
        padding: 0 1;
        background: $surface;
        overflow-y: auto;
    }

    #input_container {
        height: auto;
        margin-top: 1;
        border-top: solid $panel;
        padding-top: 1;
    }

    #message_input {
        width: 100%;
        height: 3;
    }

    #status_bar {
        height: 1;
        padding: 0 1;
        background: $panel;
        color: $text;
        text-style: bold;
    }

    .message {
        margin: 0 0 1 0;
    }

    .message_user {
        color: $primary;
        text-style: bold;
    }

    .message_text {
        color: $text;
        margin-left: 1;
    }

    .message_time {
        color: $text-muted;
        margin-left: 1;
        text-style: italic;
    }

    .user_joined {
        color: $success;
        text-style: italic;
    }

    .user_left {
        color: $error;
        text-style: italic;
    }

    .server_notice {
        color: $warning;
        text-style: italic;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("f1", "toggle_dark", "Toggle dark mode"),
        ("f2", "clear_chat", "Clear chat"),
    ]

    status = reactive("Disconnected")

    def __init__(self, server_host: str = "localhost", server_port: int = 50051):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.client: Optional[ChatClient] = None
        self.user_name: Optional[str] = None
        self._message_worker: Optional[Worker] = None
        self._is_connecting = False

    def compose(self) -> ComposeResult:
        """Create the UI layout with login screen."""
        yield Header()

        # Login screen (visible initially)
        with Container(id="login_container"):
            with Container(id="login_box"):
                yield Static("Welcome to Chat", id="login_title")
                yield Input(
                    placeholder="Enter your username...",
                    id="username_input",
                )
                yield Button("Join Chat", variant="primary", id="login_button")

        # Chat screen (hidden until login)
        with Container(id="chat_container"):
            yield RichLog(id="message_log", wrap=True, markup=True)

            with Vertical(id="input_container"):
                yield Static("", id="status_bar")
                yield Input(
                    placeholder="Type your message here...",
                    id="message_input",
                    disabled=True,
                )

        yield Footer()

    async def on_mount(self) -> None:
        """Called when app is mounted."""
        self.client = ChatClient(self.server_host, self.server_port)
        self.query_one("#username_input", Input).focus()

    @on(Button.Pressed, "#login_button")
    @on(Input.Submitted, "#username_input")
    async def on_login_attempt(self, event=None) -> None:
        """Handle login attempt via button press or Enter key."""
        if self._is_connecting:
            return  # Prevent multiple connection attempts

        username_input = self.query_one("#username_input", Input)
        self.user_name = username_input.value.strip()

        if not self.user_name:
            self.notify("Please enter a username", severity="error")
            username_input.focus()
            return

        self._is_connecting = True
        login_button = self.query_one("#login_button", Button)
        login_button.disabled = True
        login_button.label = "Connecting..."

        self.status = f"Connecting as {self.user_name}..."

        if await self.client.connect(self.user_name):
            self.query_one("#login_container").display = False
            self.query_one("#chat_container").display = True

            self.status = f"Connected as {self.user_name}"
            self.query_one("#message_input", Input).disabled = False
            self.query_one("#message_input", Input).focus()

            self._message_worker = self.run_worker(
                self._poll_messages(),
                name="message_poller",
                group="network",
                exclusive=True,
            )
        else:
            self.status = "Connection failed"
            self.notify("Failed to connect to server", severity="error")
            login_button.disabled = False
            login_button.label = "Join Chat"
            username_input.focus()
            self._is_connecting = False

    async def _poll_messages(self):
        """Non-polling message worker that waits efficiently for messages."""
        try:
            while self.client and self.client.is_connected:
                event = await self.client.wait_for_message()

                if event is None:
                    self.status = "Disconnected from server"
                    self.notify("Connection to server lost", severity="warning")
                    break

                await self._handle_chat_event(event)

        except asyncio.CancelledError:
            logger.debug("Message worker cancelled")
        except Exception as e:
            self.log(f"Error in message worker: {e}")
            self.status = "Message worker error"
            self.notify(f"Error receiving messages: {e}", severity="error")

    async def _handle_chat_event(self, event):
        """Handle incoming chat events."""
        message_log = self.query_one("#message_log", RichLog)

        if event.HasField("message"):
            msg = event.message
            time_str = datetime.now().strftime("%H:%M:%S")
            message_log.write(
                f"[{time_str}] [@class=message_user]{msg.user}[/]: "
                f"[@class=message_text]{msg.text}[/]",
                expand=False,
            )

        elif event.HasField("user_event"):
            user_event = event.user_event
            action = "joined" if user_event.action == 0 else "left"
            style = "user_joined" if user_event.action == 0 else "user_left"
            message_log.write(
                f"[@class={style}]{user_event.user_name} {action} the chat[/]",
                expand=False,
            )

        elif event.HasField("notice"):
            notice = event.notice
            message_log.write(f"[@class=server_notice]{notice.text}[/]", expand=False)

    @on(Input.Submitted, "#message_input")
    async def on_message_submitted(self, event: Input.Submitted) -> None:
        """Handle message input submission."""
        if not event.value.strip():
            return

        if self.client and self.client.is_connected:
            # Send message
            success = await self.client.send_message(event.value)

            if success:
                # Clear input
                event.input.value = ""
            else:
                self.notify("Failed to send message", severity="error")
        else:
            self.notify("Not connected to server", severity="error")

    def watch_status(self, status: str) -> None:
        """Update status bar when status changes."""
        self.query_one("#status_bar", Static).update(status)

    async def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes."""
        if event.worker.name == "message_poller":
            if event.state == WorkerState.ERROR:
                self.status = "Message worker error"
                self.notify("Message polling stopped", severity="error")
            elif event.state == WorkerState.CANCELLED:
                self.status = "Disconnected"

    def action_clear_chat(self) -> None:
        """Clear the chat log."""
        self.query_one("#message_log", RichLog).clear()
        self.notify("Chat cleared", severity="information")

    async def on_unmount(self) -> None:
        """Clean up on unmount."""
        if self.client:
            await self.client.disconnect()

        if self._message_worker:
            self._message_worker.cancel()


# Web deployment entry point - simpler version for textual serve
class ChatWebApp(ChatTUI):
    """Web-optimized version of the chat app for textual serve."""

    # Override __init__ to set default values for web deployment
    def __init__(self):
        # For web deployment, connect to localhost gRPC server
        super().__init__(server_host="localhost", server_port=50051)


# Terminal entry points
async def main():
    """Main entry point for the TUI client."""
    import argparse

    parser = argparse.ArgumentParser(description="Start the Textual chat client")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=50051, help="Server port")
    parser.add_argument(
        "--insecure", action="store_true", help="Use insecure connection"
    )

    args = parser.parse_args()

    app = ChatTUI(args.host, args.port)
    await app.run_async()


def sync_main() -> None:
    """Synchronous entry point for terminal client."""
    asyncio.run(main())


def web_main() -> ChatWebApp:
    """Entry point for web deployment with textual serve."""
    # Create and run the web-optimized app
    # Note: textual serve will handle the async execution
    app = ChatWebApp()
    return app


if __name__ == "__main__":
    sync_main()
