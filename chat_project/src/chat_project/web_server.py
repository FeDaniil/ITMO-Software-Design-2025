"""
Web server for deploying the chat client using textual-serve.
This wraps the Textual TUI app for web browser access.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from textual_serve.server import Server


def main():
    """Start the textual-serve web server."""

    command = "hatch run chat-client"

    server = Server(
        command=command,
        title="Chat Client - Web Version",
        public_url=None,
    )

    server.serve(debug=True)


if __name__ == "__main__":
    main()
