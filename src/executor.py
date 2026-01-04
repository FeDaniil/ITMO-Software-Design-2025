import subprocess
import sys
import io
from typing import TYPE_CHECKING
from environment import EnvironmentManager
from pipeline import CommandPipeline

if TYPE_CHECKING:
    pass

class CommandExecutor:
    """Выполняет команды и пайплайны."""
    
    def __init__(self, env_manager: EnvironmentManager) -> None:
        self.env_manager = env_manager

    def execute(self, pipeline: CommandPipeline) -> None:
        final_stdout = open(pipeline.stdout_file, 'w') if pipeline.stdout_file else sys.stdout
        try:
            if len(pipeline.commands) == 1:
                return pipeline.commands[0].execute(self.env_manager, sys.stdin, final_stdout, sys.stderr)
            else:
                return self.execute_pipeline(pipeline, final_stdout)
        finally:
            if pipeline.stdout_file:
                final_stdout.close()

    def execute_pipeline(self, pipeline: CommandPipeline, final_stdout) -> None:
        """
        Выполняет пайплайн команд, передавая вывод одной команды на вход следующей.
        
        Для каждой команды в пайпе:
        - Первая команда читает из sys.stdin.
        - Промежуточные команды передают данные через StringIO.
        - Последняя команда пишет в final_stdout.
        - External команды используют subprocess с пайпами.
        - Built-in команды выполняются последовательно с передачей IO.
        - Если команда 'exit', прерывает выполнение.
        """
        prev_output = None
        
        for i, command in enumerate(pipeline.commands):
            stdin = prev_output if prev_output else sys.stdin
            stdout = io.StringIO() if i < len(pipeline.commands) - 1 else final_stdout
            
            if hasattr(command, 'args') and command.args and command.args[0] == 'exit':
                raise SystemExit(0)
            
            if hasattr(command, 'execute_external'):
                if i == 0:
                    proc = command.execute_external(stdin, stdout, sys.stderr, self.env_manager.get_all_vars())
                    if len(pipeline.commands) > 1:
                        prev_output = proc.stdout
                    else:
                        proc.wait()
                elif i == len(pipeline.commands) - 1:
                    proc = subprocess.Popen(command.args, stdin=stdin, stdout=stdout, stderr=sys.stderr, env=self.env_manager.get_all_vars())
                    proc.wait()
                else:
                    proc = subprocess.Popen(command.args, stdin=stdin, stdout=subprocess.PIPE, stderr=sys.stderr, env=self.env_manager.get_all_vars())
                    prev_output = proc.stdout
            else:
                command.execute(self.env_manager, stdin, stdout, sys.stderr)
                if i < len(pipeline.commands) - 1 and hasattr(stdout, 'seek'):
                    stdout.seek(0)
                if i < len(pipeline.commands) - 1:
                    prev_output = stdout
