import io
import sys
from unittest.mock import patch, MagicMock
import pytest
from src.cli import CLI
from src.environment import EnvironmentManager

@pytest.fixture
def env_vars():
    return {'PS1': '$ '}

@patch('builtins.input', side_effect=['echo hello world', 'exit'])
@patch('sys.stdout', new_callable=io.StringIO)
@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_echo_and_exit(mock_stderr, mock_stdout, mock_input, env_vars):
    cli = CLI(env_vars)
    with pytest.raises(SystemExit):
        cli.loop()
    output = mock_stdout.getvalue()
    assert 'hello world' in output

@patch('builtins.input', side_effect=['VAR=test', 'echo $VAR', 'exit'])
@patch('sys.stdout', new_callable=io.StringIO)
@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_variable_substitution(mock_stderr, mock_stdout, mock_input, env_vars):
    cli = CLI(env_vars)
    with pytest.raises(SystemExit):
        cli.loop()
    output = mock_stdout.getvalue()
    assert 'test' in output

@patch('builtins.input', side_effect=['pwd', 'exit'])
@patch('sys.stdout', new_callable=io.StringIO)
@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_pwd(mock_stderr, mock_stdout, mock_input, env_vars):
    cli = CLI(env_vars)
    with pytest.raises(SystemExit):
        cli.loop()
    output = mock_stdout.getvalue()
    assert cli.env_manager.get_var('PWD', '') in output

@patch('subprocess.run', side_effect=OSError('command not found'))
@patch('builtins.input', side_effect=['unknown_command', 'exit'])
@patch('sys.stdout', new_callable=io.StringIO)
@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_unknown_command(mock_stderr, mock_stdout, mock_input, mock_subprocess, env_vars):
    cli = CLI(env_vars)
    with pytest.raises(SystemExit):
        cli.loop()
    error = mock_stderr.getvalue()
    assert 'command not found' in error

@patch('builtins.input', side_effect=['x=5', 'y=10', 'echo $x $y', 'exit'])
@patch('sys.stdout', new_callable=io.StringIO)
@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_multiple_variables(mock_stderr, mock_stdout, mock_input, env_vars):
    cli = CLI(env_vars)
    with pytest.raises(SystemExit):
        cli.loop()
    output = mock_stdout.getvalue()
    assert '5 10' in output

@patch('subprocess.run')
@patch('builtins.input', side_effect=['python --version', 'exit'])
@patch('sys.stdout', new_callable=io.StringIO)
@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_external_command(mock_stderr, mock_stdout, mock_input, mock_subprocess, env_vars):
    def mock_run(*args, **kwargs):
        kwargs['stdout'].write('Python 3.12\n')
        return MagicMock(returncode=0)
    mock_subprocess.side_effect = mock_run
    cli = CLI(env_vars)
    with pytest.raises(SystemExit):
        cli.loop()
    output = mock_stdout.getvalue()
    assert 'Python 3.12' in output
