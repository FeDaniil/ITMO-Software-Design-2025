from typing import List, TYPE_CHECKING
from registry import CommandRegistry

if TYPE_CHECKING:
    from commands import Command

class CommandPipeline:
    """Хранит список команд в пайплайне."""
    
    def __init__(self, command_lists: List[List[str]], stdout_file: str = None) -> None:
        self.commands: List['Command'] = []
        self.stdout_file = stdout_file
        registry = CommandRegistry()
        
        for cmd_list in command_lists:
            if cmd_list:
                name = cmd_list[0]
                args = cmd_list[1:]
                self.commands.append(registry.get_command(name, args))
