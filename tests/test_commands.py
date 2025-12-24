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
