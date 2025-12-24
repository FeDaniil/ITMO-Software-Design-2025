import pytest

import io
import pathlib
import unittest.mock

from sd_cli.executor import Executor
from sd_cli.commands import CatCommand


@pytest.fixture
def _cat_command():
    mock_stdout = io.StringIO()
    command = CatCommand(stdout=mock_stdout)
    return command


@unittest.mock.patch('builtins.open', create=True)
def test_executor_cat_command(mock_open, _cat_command):
    test_content = 'Hello, this is a test file.'
    mock_file = unittest.mock.MagicMock()
    mock_file.__enter__.return_value = test_content.splitlines(True)
    mock_open.return_value = mock_file
    test_path = pathlib.Path('test_file.txt')
    _cat_command.set_args([test_path])

    executor_ = Executor()
    ret_code = executor_.execute([_cat_command])

    assert ret_code == 0
    assert Executor.output_data.getvalue() == test_content


@unittest.mock.patch('builtins.open', create=True)
def test_executor_cat_command_file_not_found(mock_open, _cat_command):
    mock_open.side_effect = FileNotFoundError
    test_path = pathlib.Path('non_existent_file.txt')
    _cat_command.set_args([test_path])

    executor_ = Executor()
    ret_code = executor_.execute([_cat_command])

    assert ret_code == 1


@unittest.mock.patch('builtins.open', create=True)
def test_executor_cat_command_permission_error(mock_open, _cat_command):
    mock_open.side_effect = PermissionError
    test_path = pathlib.Path('restricted_file.txt')
    _cat_command.set_args([test_path])

    executor_ = Executor()
    ret_code = executor_.execute([_cat_command])

    assert ret_code == 1


@unittest.mock.patch('builtins.open', create=True)
def test_executor_cat_command_unexpected_error(mock_open, _cat_command):
    mock_open.side_effect = Exception('Unexpected error')
    test_path = pathlib.Path('some_file.txt')
    _cat_command.set_args([test_path])

    executor_ = Executor()
    ret_code = executor_.execute([_cat_command])

    assert ret_code == 1