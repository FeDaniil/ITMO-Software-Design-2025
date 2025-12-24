import subprocess
import sys
import os
from typing import IO, TYPE_CHECKING
from environment import EnvironmentManager
from pipeline import CommandPipeline

if TYPE_CHECKING:
    from commands.external import ExternalCommand

class CommandExecutor:
    """Выполняет команды и пайплайны."""
    
    def __init__(self, env_manager: EnvironmentManager) -> None:
        self.env_manager = env_manager

    def execute(self, pipeline: CommandPipeline) -> None:
        if len(pipeline.commands) == 1:
            return pipeline.commands[0].execute(self.env_manager, sys.stdin, sys.stdout, sys.stderr)
        else:
            return self.execute_pipeline(pipeline)

    def execute_pipeline(self, pipeline: CommandPipeline) -> None:
        processes: List[subprocess.Popen] = []
        prev_stdout: Optional[IO[str]] = None
        
        for i, command in enumerate(pipeline.commands):
            if i == 0:
                stdin = sys.stdin
                stdout = subprocess.PIPE if len(pipeline.commands) > 1 else sys.stdout
            elif i == len(pipeline.commands) - 1:
                stdin = prev_stdout
                stdout = sys.stdout
            else:
                stdin = prev_stdout
                stdout = subprocess.PIPE
            
            if hasattr(command, 'execute_external'):
                proc = command.execute_external(stdin, stdout, sys.stderr, self.env_manager.get_all_vars())
                processes.append(proc)
                prev_stdout = proc.stdout
            else:
                pass
        
        for proc in processes:
            proc.wait()
