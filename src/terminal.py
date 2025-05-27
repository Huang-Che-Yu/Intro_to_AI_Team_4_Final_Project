import os
import subprocess


def get_history(size):
    return subprocess.run(
        [get_current_shell(), "-c", f"history --max={size}"],
        capture_output=True,
        text=True,
    ).stdout.strip()


def get_current_dir():
    return os.getcwd()


def get_current_shell():
    return os.environ["SHELL"]


def run_command(command):
    """
    Execute a command in the terminal and return the output.
    """
    result = subprocess.run(command.split(), capture_output=True, text=True)
    return result.stdout.strip() + "\n" + result.stderr.strip()


def read_file(file_path):
    """
    Read the contents of a file and return it as a string
    """
    with open(file_path) as f:
        return f.read()
