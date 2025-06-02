import os
import subprocess

import libtmux

from .logging import LoggerManager


def get_history(size: int, all_panes: bool = False) -> list[str]:
    """Get the command history.

    Args:
        size (int): The number of lines of history to include.
                    0 for the terminal screen.

    Returns:
        list[str]: The terminal history
    """

    logger = LoggerManager.get_logger()
    if not os.getenv("TMUX"):
        logger.error(
            "TMUX environment variable not set, please run inside a tmux session"
        )
        return []
    tmux_server = libtmux.Server()
    session, window, pane = (
        tmux_server.cmd("display-message", "-p", "#S:#I:#P").stdout[0].split(":")
    )
    captured_texts: list[str] = []
    raw_panes = tmux_server.cmd("list-panes").stdout
    for raw_pane in raw_panes:
        pane_id = raw_pane.split(":")[0]
        if all_panes or pane_id == pane:
            captured_texts += tmux_server.cmd(
                "capture-pane", "-p", "-t", f"{session}:{window}.{pane_id}"
            ).stdout
    if size == 0:
        return captured_texts
    return captured_texts[-size:]


def get_current_dir() -> str:
    """Get the current directory.

    Returns:
        str: The current directory
    """

    return os.getcwd()


def get_current_shell() -> str:
    """Get the current shell.

    Returns:
        str: The current shell
    """
    return os.environ.get("SHELL", "/usr/bin/bash")


def run_command(command: str) -> str:
    """
    Run a command in the shell and return the output.
    """

    result = subprocess.run(command.split(), capture_output=True, text=True)
    return result.stdout.strip() + "\n" + result.stderr.strip()


def read_file(file_path: str) -> str:
    """
    Read a file and return the contents.
    """

    try:
        with open(file_path) as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error reading file {file_path}: {e}"
