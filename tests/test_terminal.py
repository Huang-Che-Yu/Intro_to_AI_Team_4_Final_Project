import os

from term_assistant.terminal import (
    get_current_dir,
    get_current_shell,
    read_file,
    run_command,
)


def test_get_current_dir() -> None:
    assert get_current_dir() == os.getcwd()


def test_get_current_shell() -> None:
    assert get_current_shell() == os.environ.get("SHELL", "/usr/bin/bash")


def test_run_command() -> None:
    result = run_command("ls /")
    assert "bin" in result
    result = run_command("pwd")
    assert os.getcwd() in result


def test_run_command_error() -> None:
    result = run_command("ls /notfound")
    assert "No such file or directory" in result


def test_read_file() -> None:
    text = "test read file"
    with open("/tmp/test_file.txt", "w") as f:
        f.write(text)
    assert read_file("/tmp/test_file.txt") == text


def test_read_file_not_found() -> None:
    filename = "/tmp/not_found.txt"
    assert read_file(filename) == f"File not found: {filename}"
