import re
import subprocess

from sd_cli.commands import (
    Commands,
    BaseCommand,
    CatCommand,
)


class InvalidCommandError(ValueError):
    """Raise if input cmd is not Linux command."""

    pass


class Parser:
    """Parser logic."""

    # TODO: tests

    PIPE_SYMBOL = '|'

    @staticmethod
    def _is_valid_cmd(cmd: str) -> bool:
        """Summary of _is_valid_cmd.

        Args:
            cmd (str): Check that input cmd is Linux acceptable cmd

        Returns:
            bool: Is cmd is Linux cmd?
        """
        result = subprocess.run(
            [Commands.WHICH, cmd],
            capture_output=True,
        )
        return any([
            result.returncode == 0,
            cmd == 'exit',  # we support exit cmd in our CLI
        ])

    @staticmethod
    def _validate_input_cmd(input_cmd: str) -> None:
        """Summary of _validate_input_cmd.

        Args:
            input_cmd (str): Cmd to validate

        Returns:
            None
        """
        if not Parser._is_valid_cmd(input_cmd):
            raise InvalidCommandError(f'Command {input_cmd} is not valid Linux command!')
        return None

    def parse(self, cli_input: str) -> list[BaseCommand]:
        """Summary of parse.

        Args:
            cli_input (str): CLI user input as a string

        Returns:
            typing.List[base_command.BaseCommand]: Parsed commands
        """
        result: list[BaseCommand] = []
        for cmd_line in cli_input.split(Parser.PIPE_SYMBOL):
            cmd_line.strip()
            cmd_line_splitted = cmd_line.split()
            if len(cmd_line_splitted) == 0:
                continue
            filtered_tokens = []
            for token in cmd_line_splitted:
                if re.match(r'^[A-Za-z_]\w*=\S+$', token):
                    key, value = token.split('=', 1)
                    self.storage.set(key, value)
                    continue
                elif re.match(r'^\$[A-Za-z_]\w*$', token):
                    key = token[1:]
                    val = self.storage.get(key)
                    filtered_tokens.append(val)
                else:
                    filtered_tokens.append(token)

            if len(filtered_tokens) == 0:
                continue

            input_cmd = filtered_tokens[0]
            Parser._validate_input_cmd(input_cmd)
            args = filtered_tokens[1:]
            args = [arg for arg in args if arg != '']
            match input_cmd:
                case Commands.CAT:
                    if len(args) != 1:
                        raise Exception('Wrong number of arguments!')
                    cat_cmd = CatCommand()
                    cat_cmd.set_args(args)
                    result.append(cat_cmd)
                # TODO: implement other commands
                case _:
                    raise NotImplementedError()

        return result