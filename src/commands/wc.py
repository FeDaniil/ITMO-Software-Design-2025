from typing import IO, TYPE_CHECKING
from . import Command

if TYPE_CHECKING:
    from environment import EnvironmentManager

class WcCommand(Command):
    """Считает строки, слова и символы."""
    
    def __init__(self, args: list[str]) -> None:
        self.args = args

    def execute(self, env_manager: 'EnvironmentManager', stdin: IO[str], stdout: IO[str], stderr: IO[str]) -> int:
        lines = 0
        words = 0
        chars = 0
        
        if not self.args:
            content = stdin.read()
            lines = content.count('\n')
            words = len(content.split())
            chars = len(content)
        else:
            for filename in self.args:
                try:
                    with open(filename, 'r') as f:
                        content = f.read()
                        lines += content.count('\n')
                        words += len(content.split())
                        chars += len(content)
                except FileNotFoundError:
                    print(f"wc: {filename}: No such file or directory", file=stderr)
                    return 1
        
        print(f"{lines} {words} {chars}", file=stdout)
        return 0
