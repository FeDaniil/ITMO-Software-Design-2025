import re
import argparse
from typing import IO, TYPE_CHECKING
from . import Command

if TYPE_CHECKING:
    from environment import EnvironmentManager

class GrepCommand(Command):
    """Ищет строки по регулярному выражению с опциями."""

    def __init__(self, args: list[str]) -> None:
        self.args = args

    def execute(self, env_manager: 'EnvironmentManager', stdin: IO[str], stdout: IO[str], stderr: IO[str]) -> int:
        parser = argparse.ArgumentParser(prog='grep', add_help=False)
        parser.add_argument('pattern', help='Регулярное выражение для поиска')
        parser.add_argument('files', nargs='*', help='Файлы для поиска (если не указано, stdin)')
        parser.add_argument('-w', '--word', action='store_true', help='Искать только целые слова')
        parser.add_argument('-i', '--ignore-case', action='store_true', help='Регистронезависимый поиск')
        parser.add_argument('-A', '--after-context', type=int, default=0, help='Количество строк после совпадения')

        try:
            parsed = parser.parse_args(self.args)
        except SystemExit:
            return 1

        pattern = parsed.pattern
        flags = re.IGNORECASE if parsed.ignore_case else 0
        if parsed.word:
            pattern = r'\b' + re.escape(pattern) + r'\b'

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            print(f"grep: {e}", file=stderr)
            return 2

        sources = parsed.files if parsed.files else [None]
        found = False

        for source in sources:
            lines = []
            if source:
                try:
                    with open(source, 'r') as f:
                        lines = f.readlines()
                except FileNotFoundError:
                    print(f"grep: {source}: No such file or directory", file=stderr)
                    return 1
            else:
                lines = stdin.readlines()

            i = 0
            while i < len(lines):
                line = lines[i]
                if regex.search(line):
                    found = True
                    if source:
                        print(f"{source}:{line.rstrip()}", file=stdout)
                    else:
                        print(line.rstrip(), file=stdout)
                    for j in range(1, parsed.after_context + 1):
                        if i + j < len(lines):
                            next_line = lines[i + j]
                            if source:
                                print(f"{source}:{next_line.rstrip()}", file=stdout)
                            else:
                                print(next_line.rstrip(), file=stdout)
                    i += parsed.after_context + 1
                else:
                    i += 1

        return 0 if found else 1