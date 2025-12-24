import sys
from typing import IO, TYPE_CHECKING
from . import Command

if TYPE_CHECKING:
    from environment import EnvironmentManager

class CatCommand(Command):
    """Выводит содержимое файлов или stdin."""
    
    def __init__(self, args: list[str]) -> None:
        self.args = args

    def execute(self, env_manager: 'EnvironmentManager', stdin: IO[str], stdout: IO[str], stderr: IO[str]) -> int:
        if not self.args:
            for line in stdin:
                stdout.write(line)
        else:
            for filename in self.args:
                try:
                    with open(filename, 'r') as f:
                        for line in f:
                            stdout.write(line)
                except FileNotFoundError:
                    print(f"cat: {filename}: No such file or directory", file=stderr)
                    return 1
        return 0
