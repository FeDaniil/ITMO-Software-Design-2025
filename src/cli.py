import sys
from typing import Dict
from parser import CommandParser
from executor import CommandExecutor
from environment import EnvironmentManager

class CLI:
    """Основной цикл работы интерпретатора командной строки."""
    
    def __init__(self, env_vars: Dict[str, str]) -> None:
        self.env_manager = EnvironmentManager(env_vars)
        self.parser = CommandParser(self.env_manager)
        self.executor = CommandExecutor(self.env_manager)
        self.running = True

    def loop(self) -> None:
        while self.running:
            try:
                prompt = self.env_manager.get_var('PS1', '$ ')
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Парсинг команды
                pipeline = self.parser.parse(user_input)
                
                # Выполнение команды
                self.executor.execute(pipeline)
                
            except KeyboardInterrupt:
                print("\nExiting...")
                self.running = False
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
