import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cli import CLI

def main() -> None:
    env_vars = dict(os.environ)
    
    # Создание и запуск CLI Engine
    cli = CLI(env_vars)
    cli.loop()

if __name__ == "__main__":
    main()