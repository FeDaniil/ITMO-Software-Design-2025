from typing import IO, TYPE_CHECKING
from . import Command

if TYPE_CHECKING:
    from environment import EnvironmentManager

class EchoCommand(Command):
    """Выводит аргументы."""
    
    def __init__(self, args: list[str]) -> None:
        self.args = args

    def execute(self, env_manager: 'EnvironmentManager', stdin: IO[str], stdout: IO[str], stderr: IO[str]) -> int:
        if not self.args:
            output = ''.join(stdin)
        else:
            output = ' '.join(self.args)
        print(output, file=stdout)
        return 0
