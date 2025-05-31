import os
import shutil
import subprocess

from .logging import LoggerManager


def get_history(size: int) -> list[str]:
    """Get the command history.

    Args:
        size (int): The number of lines of history to include.
                    0 for the terminal screen, -1 for full history.

    Returns:
        list[str]: The terminal history
    """

    logger = LoggerManager.get_logger()
    if not os.path.exists(os.path.expanduser("~/.assistant.cast")):
        logger.warning("No asciinema cast file found.")
        return []
    asciinema_path = shutil.which("asciinema")
    if not asciinema_path:
        logger.warning("No asciinema program found.")
        return []
    result = subprocess.run(
        [
            asciinema_path,
            "convert",
            os.path.expanduser("~/.assistant.cast"),
            "-f",
            "txt",
            "/dev/stdout",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f"Failed to convert asciinema cast file, error: {result.stderr}")
        return []
    history = []
    for line in result.stdout.splitlines():
        if line.strip():
            history.append(" ".join(line.strip().split()))
    if size == -1:
        # full
        return history[:-1]
    elif size == 0:
        # within the terminal screen
        height = int(os.getenv("LINES", "50"))
        return history[-height:-1]
    return history[-size:-1]


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
