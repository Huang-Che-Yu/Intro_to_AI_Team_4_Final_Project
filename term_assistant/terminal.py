import os
import subprocess


def get_history(size: int) -> list[str]:
    """Get the command history.

    Args:
        size (int): The number of lines of history to include

    Returns:
        list[str]: The command history
    """

    shell = get_current_shell()
    command = ""
    if "fish" in shell:
        command = f"history --max={size}"
    elif "zsh" in shell:
        command = "history 0"
    else:
        command = f"history {size + 1}"

    result = (
        subprocess.run(
            [shell, "-c", command],
            capture_output=True,
            text=True,
            shell=True,
        )
        .stdout.strip()
        .split("\n")
    )

    if "fish" in shell:
        return result
    else:
        return result[:-1]


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
    return os.environ.get("SHELL", "/usr/bin/fish")


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

    with open(file_path) as f:
        return f.read()
