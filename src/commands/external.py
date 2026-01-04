import subprocess
from typing import IO, TYPE_CHECKING
from . import Command

if TYPE_CHECKING:
    from environment import EnvironmentManager

class ExternalCommand(Command):
    """Запускает внешние команды."""
    
    def __init__(self, args: list[str]) -> None:
        self.args = args

    def execute(self, env_manager: 'EnvironmentManager', stdin: IO[str], stdout: IO[str], stderr: IO[str]) -> int:
        try:
            result = subprocess.run(self.args, stdin=stdin, stdout=stdout, stderr=stderr, env=env_manager.get_all_vars())
            return result.returncode
        except FileNotFoundError:
            print(f"{self.args[0]}: command not found", file=stderr)
            return 127

    def execute_external(self, stdin: IO[str], stdout: IO[str], stderr: IO[str], env: dict[str, str]) -> subprocess.Popen:
        return subprocess.Popen(self.args, stdin=stdin, stdout=stdout, stderr=stderr, env=env)
