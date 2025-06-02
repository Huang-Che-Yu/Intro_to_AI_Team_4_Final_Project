import json
from typing import Generator

import litellm
from colorama import Fore, Style
from litellm.types.utils import ModelResponse, ModelResponseStream

from .config import load_config
from .logging import LoggerManager
from .tools import tools

litellm.suppress_debug_info = True


class Provider:
    """Provider class for interacting with language models."""

    def __init__(
        self,
        model_name,
        api_key=None,
        base_url=None,
        temperature=None,
        top_p=None,
        no_tools=False,
        dry_run=False,
    ):
        """
        Provider class for interacting with language models.

        Attributes:
            model_name (str): The name of the model to use.
            api_key (str, optional): The API key for authenticating with OpenAI. Defaults to None.
            base_url (str, optional): The base URL for the OpenAI API. Defaults to None.
            temperature (float, optional): The temperature for the model's output. Defaults to None.
            top_p (float, optional): The top-p value for the model's output. Defaults to None.
            no_tools (bool, optional): Flag to disable tool usage. Defaults to False.
            dry_run (bool, optional): Flag to enable dry run mode. Defaults to False.
        """

        if len(model_name.split("/")) != 2:
            raise ValueError(
                "The model name should be in the format of 'provider/model'."
            )
        self.model_name: str = model_name
        self.api_key: str | None = api_key
        self.base_url: str | None = base_url
        self.temperature: float | None = temperature
        self.top_p: float | None = top_p
        self.no_tools: bool = no_tools
        self.dry_run: bool = dry_run

    def utilize_tool(self, name: str, args: str) -> str:
        """Utilize a tool.

        Args:
            tool (ChoiceDeltaToolCallFunction): The tool to utilize

        Returns:
            str: The output of the tool
        """

        args = args if isinstance(args, dict) else json.loads(args or "{}")
        if tools.get(name):
            tool = tools[name]
            if tool.message:
                print(tool.message)
            confirm = input(f"Use tool {name} with arguments {args}? (y/n): ").lower()
            return (
                tool.function(**args if isinstance(args, dict) else {"arg": args})
                if confirm == "y"
                else "User cancelled."
            )
        return ""

    def get_llm_response(
        self, messages: list[litellm.AllMessageValues]
    ) -> ModelResponse | litellm.CustomStreamWrapper:
        # Generate documentation for the get_llm_response method
        """
        Get a response from the language model.

        Args:
            messages (list[litellm.AllMessageValues]):
                A list of messages to send to the model.

        Returns:
            ModelResponse | litellm.CustomStreamWrapper:
                The response from the language model.
        """

        return litellm.completion(
            # generation config
            model=self.model_name,
            messages=messages,
            tools=(
                [tool.openai_tool for tool in tools.values()]
                if not self.no_tools
                else None
            ),
            temperature=self.temperature,
            top_p=self.top_p,
            stream=True,
            stream_options={"include_usage": True},
            # provider config
            api_key=self.api_key or None,
            base_url=self.base_url or None,
            # dry run
            mock_response="Dry run completed." if self.dry_run else None,
        )

    def assist(
        self,
        messages: list[litellm.AllMessageValues],
    ) -> Generator[str, None, None]:
        """
        Assist the user by generating responses from the language model.

        Args:
            messages (list[litellm.AllMessageValues]):
                A list of messages to send to the model.

        Yields:
            Generator[str, None, None]:
                A generator yielding the model's responses as strings.
        """

        response = self.get_llm_response(messages)

        # Log the context, prompts, and tool messages
        logger = LoggerManager.get_logger()
        logger.debug(f"Context: {messages}")

        full_response: str = ""
        tool_call_id: str = ""
        tool_name: str = ""
        tool_args: str = ""
        for chunk in response or []:
            if not isinstance(chunk, ModelResponseStream):
                continue

            message = chunk.choices[0].delta
            role = message.role
            tool_calls = message.tool_calls
            content = message.content
            finish_reason = chunk.choices[0].finish_reason

            if role:
                # First chunk, so also print the system message
                yield f"{Fore.GREEN}{role}({chunk.model}): {Style.RESET_ALL}"

            if not finish_reason:
                if tool_calls is not None:
                    # Middle chunk with tool calls
                    tool_call = tool_calls[0]
                    tool_call_id = tool_call.id or ""
                    func = tool_call.function
                    if func:
                        tool_name = func.name or tool_name
                        tool_args += func.arguments or ""
                elif usage := chunk.get("usage"):
                    # Usage chunk
                    logger.debug(f"Response Usage Info: {usage}")
                else:
                    # Middle chunk, so just print the content
                    new_content = content or ""
                    full_response += new_content
                    yield new_content
            elif finish_reason == "tool_calls":
                # Tool calls, so utilize the tools and feed the output back to the LLM
                tool_output = ""

                # Utilize the tools and log the output
                if tool_call_id:
                    if tool_name in tools:
                        yield f"{Fore.GREEN}Using tool {tool_name}...{Style.RESET_ALL}"
                        tool_output = self.utilize_tool(tool_name, tool_args)
                        logger.debug(f"Use tool: {tool_name}, Output: {tool_output}")
                    yield "\n"

                # If there are tool outputs, feed them back to the LLM
                if tool_output:
                    for next_response in self.assist(
                        messages=[
                            *messages,
                            *self._compose_tool_messages(
                                tool_call_id, tool_name, tool_args, tool_output
                            ),
                        ]
                    ):
                        yield next_response
            elif finish_reason == "stop":
                # Last chunk, so log the full response and the response info, and yield a newline
                logger.debug(f"Response: {full_response}")
                yield "\n"

    @staticmethod
    def _compose_tool_messages(
        tool_call_id: str,
        tool_name: str,
        tool_args: str,
        tool_output: str,
    ) -> list[litellm.AllMessageValues]:
        """
        Compose tool messages for the language model.

        Args:
            tool_call_id (str): The ID of the tool call.
            tool_name (str): The name of the tool.
            tool_args (str): The arguments for the tool.
            tool_output (str): The output from the tool.

        Returns:
            list[litellm.AllMessageValues]:
                A list of messages formatted for the language model.
        """

        return [
            litellm.ChatCompletionAssistantMessage(
                role="assistant",
                tool_calls=[
                    litellm.ChatCompletionAssistantToolCall(
                        id=tool_call_id,
                        type="function",
                        function=litellm.ChatCompletionToolCallFunctionChunk(
                            name=tool_name, arguments=tool_args
                        ),
                    )
                ],
            ),
            litellm.ChatCompletionToolMessage(
                role="tool",
                content=tool_output,
                tool_call_id=tool_call_id,
            ),
        ]

    @staticmethod
    def compose_messages(
        system_messages: list[str], user_messages: list[str]
    ) -> list[litellm.AllMessageValues]:
        """
        Compose messages for the language model.

        Args:
            system_messages (list[str]): A list of system messages.
            user_messages (list[str]): A list of user messages.

        Returns:
            list[litellm.AllMessageValues]:
                A combined list of system and user messages formatted
                for the language model.
        """

        _system_messages = [
            litellm.ChatCompletionSystemMessage(role="system", content=msg)
            for msg in system_messages
        ]
        _user_messages = [
            litellm.ChatCompletionUserMessage(role="user", content=msg)
            for msg in user_messages
        ]
        return [*_system_messages, *_user_messages]


def create_assistant(
    model_name: str,
    temperature: float | None = None,
    top_p: float | None = None,
    no_tools: bool = False,
    dry_run: bool = False,
) -> Provider | None:
    """Create an assistant from the given provider and model name.

    Args:
        model_name (str): The model name
        temperature (float, optional): LLM temperature. Defaults to None.
        top_p (float, optional): LLM Top-P value. Defaults to None.
        no_tools (bool, optional): Do not pass tool list to LLM if set to True. It can reduce the token usage but also the functionality. Defaults to False.
        dry_run (bool, optional): Dry run mode. Defaults to False.

    Returns:
        OpenAIAPI | MistralAPI | None: The assistant instance or None if the provider or model is not found
    """

    config = load_config()
    provider = model_name.split("/")[0]
    providers_config = config.providers
    generation_config = config.generation
    provider_config = providers_config.get(provider) or None
    if provider_config and provider_config.api_key:
        return Provider(
            model_name=model_name,
            api_key=provider_config.api_key if provider_config else None,
            base_url=provider_config.base_url if provider_config else None,
            temperature=(temperature or generation_config.temperature),
            top_p=(top_p or generation_config.top_p),
            no_tools=False if no_tools or not generation_config.with_tools else True,
            dry_run=dry_run,
        )
    return None
