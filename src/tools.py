from dataclasses import dataclass
from .terminal import run_command, read_file


@dataclass
class Parameter:
    type: str
    description: str
    optional: bool = False


@dataclass
class Tool:
    function: callable
    parameters: dict[str, Parameter]

    def generate_tool_call(self):
        return {
            "type": "function",
            "function": {
                "name": self.function.__name__,
                "description": self.function.__doc__.strip(),
                "parameters": {
                    "type": "object",
                    "properties": {**self.parameters},
                    "required": [
                        k for k, v in self.parameters.items() if not v.optional
                    ],
                },
            },
        }


tools = {
    run_command.__name__: Tool(
        run_command, {"command": Parameter("string", "The command to execute")}
    ),
    read_file.__name__: Tool(
        read_file, {"file_path": Parameter("string", "The path to the file to read")}
    ),
}
