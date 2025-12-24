import io
import sys
from unittest.mock import patch, MagicMock
import pytest
from src.cli import CLI
from src.environment import EnvironmentManager

@pytest.fixture
def env_vars():
    return {'PS1': '$ '}

@patch('builtins.input', side_effect=['echo hello world | cat', 'exit'])
@patch('sys.stdout', new_callable=io.StringIO)
@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_pipeline_builtin_builtin(mock_stderr, mock_stdout, mock_input, env_vars):
    cli = CLI(env_vars)
    with pytest.raises(SystemExit):
        cli.loop()
    output = mock_stdout.getvalue()
    assert 'hello world' in output

@patch('builtins.input', side_effect=['VAR=test', 'echo $VAR | wc', 'exit'])
@patch('sys.stdout', new_callable=io.StringIO)
@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_pipeline_with_variables(mock_stderr, mock_stdout, mock_input, env_vars):
    cli = CLI(env_vars)
    with pytest.raises(SystemExit):
        cli.loop()
    output = mock_stdout.getvalue()
    assert '1 1 5' in output  # test: 1 line, 1 word, 5 chars (t e s t \n)

@patch('builtins.input', side_effect=['echo line1 | cat | wc', 'exit'])
@patch('sys.stdout', new_callable=io.StringIO)
@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_pipeline_three_commands(mock_stderr, mock_stdout, mock_input, env_vars):
    cli = CLI(env_vars)
    with pytest.raises(SystemExit):
        cli.loop()
    output = mock_stdout.getvalue()
    assert '1 1 6' in output  # line1: 1 line, 1 word, 6 chars

@patch('builtins.input', side_effect=['exit | echo should not run', 'exit'])
@patch('sys.stdout', new_callable=io.StringIO)
@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_pipeline_exit_in_pipeline(mock_stderr, mock_stdout, mock_input, env_vars):
    cli = CLI(env_vars)
    with pytest.raises(SystemExit):
        cli.loop()
    output = mock_stdout.getvalue()
    assert 'should not run' not in output  # exit должен прервать пайп

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
