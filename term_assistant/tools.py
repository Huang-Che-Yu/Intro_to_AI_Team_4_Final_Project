from dataclasses import dataclass
from typing import Callable

from openai.types.chat import ChatCompletionToolParam as OpenAITool
from openai.types.shared_params.function_definition import FunctionDefinition

from .terminal import read_file, run_command


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
        openai_tool (OpenAITool)
            A property to represent the tool in the format required by OpenAI.
    """

    function: Callable
    parameters: dict[str, Parameter]
    message: str = ""

    @property
    def openai_tool(self) -> OpenAITool:
        """
        Returns:
            OpenAITool: The tool formatted for OpenAI's API.
        """

        return OpenAITool(
            function=FunctionDefinition(
                name=self.function.__name__,
                description=(
                    self.function.__doc__.strip() if self.function.__doc__ else ""
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        k: {"type": v.type, "description": v.description}
                        for k, v in self.parameters.items()
                    },
                    "required": [
                        k for k, v in self.parameters.items() if not v.optional
                    ],
                },
            ),
            type="function",
        )


tools: dict[str, Tool] = {
    run_command.__name__: Tool(
        run_command,
        {"command": Parameter("string", "The command to execute")},
        "\033[33mCaution: This tool may do something dangerous. Please use with caution.\033[0m",
    ),
    read_file.__name__: Tool(
        read_file, {"file_path": Parameter("string", "The path to the file to read")}
    ),
}
