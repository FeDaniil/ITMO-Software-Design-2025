import os
from typing import IO, TYPE_CHECKING
from . import Command

if TYPE_CHECKING:
    from environment import EnvironmentManager

class PwdCommand(Command):
    """Показывает текущий каталог."""
    
    def __init__(self, args: list[str]) -> None:
        self.args = args

    def execute(self, env_manager: 'EnvironmentManager', stdin: IO[str], stdout: IO[str], stderr: IO[str]) -> int:
        print(os.getcwd(), file=stdout)
        return 0
