from typing import IO, TYPE_CHECKING
from . import Command

if TYPE_CHECKING:
    from environment import EnvironmentManager

class AssignmentCommand(Command):
    """Присваивает переменные."""
    
    def __init__(self, assignment_str: str) -> None:
        self.var, self.value = assignment_str.split('=', 1)

    def execute(self, env_manager: 'EnvironmentManager', stdin: IO[str], stdout: IO[str], stderr: IO[str]) -> int:
        env_manager.set_var(self.var, self.value)
        return 0
