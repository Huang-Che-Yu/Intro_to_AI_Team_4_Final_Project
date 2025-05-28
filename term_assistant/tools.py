from dataclasses import dataclass
from typing import Callable
from .terminal import run_command, read_file


@dataclass
class Parameter:
    """
    A class to represent a parameter.

    Attributes:
        type (str): The type of the parameter.
        description (str): A brief description of the parameter.
        optional (bool): Indicates if the parameter is optional. Defaults to False.
    """

    type: str
    description: str
    optional: bool = False


@dataclass
class Tool:
    """
    The Tool class represents a tool with a callable function and its parameters.
    Attributes:
        function (callable): The function that the tool will execute.
        parameters (dict[str, Parameter]): A dictionary of parameters for the function,
            where the key is the parameter name and the value is a Parameter object.
    Methods:
        generate_tool_call():
            Generates a dictionary representing the tool call, including the function's
            name, description, parameters, and required parameters.
            Returns:
                dict: A dictionary with the structure of the tool call.
    """

    function: Callable
    parameters: dict[str, Parameter]

    def generate_tool_call(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.function.__name__,
                "description": (
                    self.function.__doc__.strip() if self.function.__doc__ else ""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {**self.parameters},
                    "required": [
                        k for k, v in self.parameters.items() if not v.optional
                    ],
                },
            },
        }


tools: dict[str, Tool] = {
    run_command.__name__: Tool(
        run_command, {"command": Parameter("string", "The command to execute")}
    ),
    read_file.__name__: Tool(
        read_file, {"file_path": Parameter("string", "The path to the file to read")}
    ),
}
