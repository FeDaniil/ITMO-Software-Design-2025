from typing import Dict, Type, TYPE_CHECKING
from commands.echo import EchoCommand
from commands.cat import CatCommand
from commands.wc import WcCommand
from commands.pwd import PwdCommand
from commands.exit_cmd import ExitCommand
from commands.assignment import AssignmentCommand
from commands.external import ExternalCommand
from commands.grep import GrepCommand

if TYPE_CHECKING:
    from commands import Command

class CommandRegistry:
    """Создает объекты команд по имени."""
    
    def __init__(self) -> None:
        self.commands: Dict[str, Type['Command']] = {
            'echo': EchoCommand,
            'cat': CatCommand,
            'wc': WcCommand,
            'pwd': PwdCommand,
            'exit': ExitCommand,
            'grep': GrepCommand,
        }

    def get_command(self, name: str, args: list[str]) -> 'Command':
        if '=' in name and len(args) == 0:
            return AssignmentCommand(name)
        elif name in self.commands:
            return self.commands[name](args)
        else:
            # Внешняя команда
            return ExternalCommand([name] + args)
