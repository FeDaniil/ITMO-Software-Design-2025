import io
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from src.environment import EnvironmentManager
from src.commands.echo import EchoCommand
from src.commands.cat import CatCommand
from src.commands.wc import WcCommand
from src.commands.pwd import PwdCommand
from src.commands.exit_cmd import ExitCommand
from src.commands.assignment import AssignmentCommand
from src.commands.external import ExternalCommand
from src.commands.grep import GrepCommand

@pytest.fixture
def env_manager():
    return EnvironmentManager()

def test_echo_command(env_manager):
    cmd = EchoCommand(['hello', 'world'])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO()
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 0
    assert stdout.getvalue() == 'hello world\n'

def test_cat_command_file(env_manager):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write('line1\nline2\n')
        temp_file = f.name
    try:
        cmd = CatCommand([temp_file])
        stdout = io.StringIO()
        stderr = io.StringIO()
        stdin = io.StringIO()
        result = cmd.execute(env_manager, stdin, stdout, stderr)
        assert result == 0
        assert stdout.getvalue() == 'line1\nline2\n'
    finally:
        os.unlink(temp_file)

def test_echo_command_no_args(env_manager):
    cmd = EchoCommand([])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO()
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 0
    assert stdout.getvalue() == '\n'

def test_echo_command_empty_string(env_manager):
    cmd = EchoCommand([''])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO()
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 0
    assert stdout.getvalue() == '\n'

def test_cat_command_multiple_files(env_manager):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
        f1.write('file1\n')
        temp_file1 = f1.name
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
        f2.write('file2\n')
        temp_file2 = f2.name
    try:
        cmd = CatCommand([temp_file1, temp_file2])
        stdout = io.StringIO()
        stderr = io.StringIO()
        stdin = io.StringIO()
        result = cmd.execute(env_manager, stdin, stdout, stderr)
        assert result == 0
        assert stdout.getvalue() == 'file1\nfile2\n'
    finally:
        os.unlink(temp_file1)
        os.unlink(temp_file2)

def test_wc_command_file(env_manager):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write('line1\nline2\nline3\n')
        temp_file = f.name
    try:
        cmd = WcCommand([temp_file])
        stdout = io.StringIO()
        stderr = io.StringIO()
        stdin = io.StringIO()
        result = cmd.execute(env_manager, stdin, stdout, stderr)
        assert result == 0
        assert stdout.getvalue() == '3 3 18\n'
    finally:
        os.unlink(temp_file)

def test_wc_command_multiple_files(env_manager):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
        f1.write('line1\nline2\n')
        temp_file1 = f1.name
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
        f2.write('line3\n')
        temp_file2 = f2.name
    try:
        cmd = WcCommand([temp_file1, temp_file2])
        stdout = io.StringIO()
        stderr = io.StringIO()
        stdin = io.StringIO()
        result = cmd.execute(env_manager, stdin, stdout, stderr)
        assert result == 0
        assert stdout.getvalue() == '3 3 18\n'  # total
    finally:
        os.unlink(temp_file1)
        os.unlink(temp_file2)

def test_pwd_command(env_manager):
    cmd = PwdCommand([])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO()
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 0
    assert stdout.getvalue() == os.getcwd() + '\n'

@patch('sys.exit')
def test_exit_command(mock_exit, env_manager):
    cmd = ExitCommand([])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO()
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    mock_exit.assert_called_once_with(0)

def test_assignment_command_with_spaces(env_manager):
    cmd = AssignmentCommand('VAR=hello world')
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO()
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 0
    assert env_manager.get_var('VAR') == 'hello world'

def test_assignment_command_empty_value(env_manager):
    cmd = AssignmentCommand('VAR=')
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO()
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 0
    assert env_manager.get_var('VAR') == ''

@patch('subprocess.run')
def test_external_command_success(mock_run, env_manager):
    mock_run.return_value = MagicMock(returncode=0)
    cmd = ExternalCommand(['echo', 'test'])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO()
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 0
    mock_run.assert_called_once()

@patch('subprocess.run')
def test_external_command_failure(mock_run, env_manager):
    mock_run.side_effect = FileNotFoundError()
    cmd = ExternalCommand(['nonexistent'])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO()
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 127
    assert 'command not found' in stderr.getvalue()

def test_grep_command_stdin(env_manager):
    cmd = GrepCommand(['hello'])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO('hello world\nsecond line\nhello again\n')
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 0
    output = stdout.getvalue()
    assert 'hello world' in output
    assert 'hello again' in output
    assert 'second line' not in output

def test_grep_command_file(env_manager):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write('line1 hello\nline2\nline3 hello\n')
        temp_file = f.name
    try:
        cmd = GrepCommand(['hello', temp_file])
        stdout = io.StringIO()
        stderr = io.StringIO()
        stdin = io.StringIO()
        result = cmd.execute(env_manager, stdin, stdout, stderr)
        assert result == 0
        output = stdout.getvalue()
        assert f'{temp_file}:line1 hello' in output
        assert f'{temp_file}:line3 hello' in output
    finally:
        os.unlink(temp_file)

def test_grep_command_word(env_manager):
    cmd = GrepCommand(['-w', 'hello'])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO('hello world\nhelloworld\nhello\n')
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 0
    output = stdout.getvalue()
    assert 'hello world' in output
    assert 'hello' in output
    assert 'helloworld' not in output

def test_grep_command_ignore_case(env_manager):
    cmd = GrepCommand(['-i', 'HELLO'])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO('hello world\nHello\nHELLO\n')
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 0
    output = stdout.getvalue()
    assert 'hello world' in output
    assert 'Hello' in output
    assert 'HELLO' in output

def test_grep_command_after_context(env_manager):
    cmd = GrepCommand(['-A', '1', 'line1'])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO('line1\nline2\nline3\nline1\nline4\n')
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 0
    output = stdout.getvalue()
    lines = output.strip().split('\n')
    assert 'line1' in lines[0]
    assert 'line2' in lines[1]
    assert 'line1' in lines[2]
    assert 'line4' in lines[3]

def test_grep_command_no_match(env_manager):
    cmd = GrepCommand(['nomatch'])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO('line1\nline2\n')
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 1
    assert stdout.getvalue() == ''

def test_grep_command_invalid_regex(env_manager):
    cmd = GrepCommand(['[invalid'])
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO('line1\n')
    result = cmd.execute(env_manager, stdin, stdout, stderr)
    assert result == 2
    assert 'unterminated character set' in stderr.getvalue()
