from dataclasses import dataclass
from typing import Callable
from .terminal import run_command, read_file
from mistralai import (
    Tool as MistralTool,
    Function as MistralFunction,
)
from openai.types.shared_params.function_definition import FunctionDefinition
from openai.types.chat import ChatCompletionToolParam as OpenAITool


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
        mistral_tool (MistralTool)
            A property to represent the tool in the format required by Mistral.
    """

    function: Callable
    parameters: dict[str, Parameter]

    @property
    def openai_tool(self) -> OpenAITool:
        return OpenAITool(
            function=FunctionDefinition(
                name=self.function.__name__,
                description=(
                    self.function.__doc__.strip() if self.function.__doc__ else ""
                ),
                parameters={
                    "type": "object",
                    "properties": {k: v.__dict__ for k, v in self.parameters.items()},
                    "required": [
                        k for k, v in self.parameters.items() if not v.optional
                    ],
                },
            ),
            type="function",
        )

    @property
    def mistral_tool(self) -> MistralTool:
        return MistralTool(
            function=MistralFunction(
                name=self.function.__name__,
                description=(
                    self.function.__doc__.strip() if self.function.__doc__ else ""
                ),
                parameters={
                    "type": "object",
                    "properties": {**self.parameters},
                    "required": [
                        k for k, v in self.parameters.items() if not v.optional
                    ],
                },
            ),
            type="function",
        )


tools: dict[str, Tool] = {
    run_command.__name__: Tool(
        run_command, {"command": Parameter("string", "The command to execute")}
    ),
    read_file.__name__: Tool(
        read_file, {"file_path": Parameter("string", "The path to the file to read")}
    ),
}
