import json
from typing import Generator, Type

import google.generativeai as Gemini
import ollama
from colorama import Fore, Style
from google.ai.generativelanguage import FunctionCall as GeminiFunctionCall
from google.ai.generativelanguage import FunctionResponse, Part
from google.generativeai import GenerationConfig
from google.generativeai.protos import Content
from google.protobuf.struct_pb2 import Struct
from mistralai import FunctionCall, Mistral, SystemMessage, UserMessage
from openai import OpenAI
from openai._types import NOT_GIVEN
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_chunk import ChoiceDelta

from .config import load_config
from .logging import LoggerManager
from .tools import tools


class Provider:
    def __init__(
        self,
        model_name,
        api_key=None,
        base_url=None,
        temperature=None,
        top_p=None,
        no_tools=False,
    ):
        pass

    def get_models(self, full=False):
        raise NotImplementedError

    def assist(
        self,
        context: list[str],
        prompts: list[str],
        tool_messages: list[str] | None = None,
    ):
        raise NotImplementedError


# TODO: Implement the OpenAIAPI class
class OpenAIAPI(Provider):
    def __init__(
        self,
        model_name,
        api_key=None,
        base_url=None,
        temperature=None,
        top_p=None,
        no_tools=False,
    ):
        """
        OpenAIAPI class for interacting with OpenAI's API.

        Attributes:
            model_name (str): The name of the model to use.
            api_key (str, optional): The API key for authenticating with OpenAI. Defaults to None.
            base_url (str, optional): The base URL for the OpenAI API. Defaults to None.
            temperature (float, optional): The temperature for the model's output. Defaults to None.
            top_p (float, optional): The top-p value for the model's output. Defaults to None.
            no_tools (bool, optional): Flag to disable tool usage. Defaults to False.
        """

        self.model_name: str = model_name
        self.api_key: str | None = api_key
        self.base_url: str | None = base_url
        self.temperature: float | None = temperature
        self.top_p: float | None = top_p
        self.llm: OpenAI = OpenAI(api_key=api_key, base_url=base_url)
        self.no_tools: bool = no_tools

    def get_models(self, full: bool = False) -> list[str]:
        """
        Get available models from the OpenAI API.

        Args:
            full (bool, optional): If True, fetch the full list of models from the API. Defaults to False.

        Returns:
            list[str]: The list of available model names.
        """

        if full:
            return sorted([m.id for m in self.llm.models.list()])
        return ["o1-preview", "o1-mini", "gpt-4o", "gpt-4o-mini"]

    def utilize_tool(self, name: str, args: str) -> str:
        """Utilize a tool.

        Args:
            tool (ChoiceDeltaToolCallFunction): The tool to utilize

        Returns:
            str: The output of the tool
        """

        args = args if isinstance(args, dict) else json.loads(args or "{}")
        if tools.get(name):
            confirm = input(f"Use tool {name} with arguments {args}? (y/n): ").lower()
            return (
                tools[name].function(
                    **args if isinstance(args, dict) else {"arg": args}
                )
                if confirm == "y"
                else "User cancelled."
            )
        return ""

    def assist(
        self,
        context: list[str],
        prompts: list[str],
        tool_messages: list[str] | None = None,
    ) -> Generator[str, None, None]:
        """Assist the user with the given context and prompts.

        Args:
            context (dict[str, str]): The context, which are system messages
            prompts (list[str]): The prompts, which are user messages
            tool_messages (list[str], optional): The output from tools, which are user messages. Defaults to [].

        Yields:
            Generator[str, None, None]: The response from the LLM
        """

        # Get the response stream from the LLM
        response = self.llm.chat.completions.create(
            model=self.model_name,
            messages=[
                *[
                    ChatCompletionSystemMessageParam(role="system", content=msg)
                    for msg in context
                ],
                *[
                    ChatCompletionUserMessageParam(role="user", content=prompt)
                    for prompt in prompts
                ],
                *[
                    ChatCompletionUserMessageParam(role="user", content=msg)
                    for msg in (tool_messages or [])
                ],
            ],
            tools=(
                [tool.openai_tool for tool in tools.values()]
                if not self.no_tools
                else NOT_GIVEN
            ),
            temperature=self.temperature,
            top_p=self.top_p,
            stream=True,
            stream_options={"include_usage": True},
        )

        # Log the context, prompts, and tool messages
        logger = LoggerManager.get_logger()
        logger.debug(f"Context: {context}")
        logger.debug(f"Prompts: {prompts}")
        logger.debug(f"Tool Messages: {tool_messages}")

        full_response = ""
        tool_name = ""
        tool_args = ""
        for chunk in response or []:
            message = ChoiceDelta()
            finish_reason = ""
            if len(chunk.choices) == 0:
                # No choices, so finish with usage
                finish_reason = "usage"
            else:
                message = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason

            if message.role:
                # First chunk, so also print the system message
                yield f"{Fore.GREEN}{message.role}({chunk.model}): {Style.RESET_ALL}"

            if not finish_reason:
                if message.tool_calls is not None:
                    # Middle chunk with tool calls
                    tool_call = message.tool_calls[0]
                    func = tool_call.function
                    if func:
                        if func.name is not None:
                            tool_name = func.name
                        tool_args += func.arguments or ""
                else:
                    # Middle chunk, so just print the content
                    full_response += message.content or ""
                    yield message.content or ""
            elif finish_reason == "tool_calls":
                # Tool calls, so utilize the tools and feed the output back to the LLM
                tool_outputs = {}

                # Utilize the tools and log the output
                if tool_name and tool_args:
                    if tool_name in tools:
                        yield f"{Fore.GREEN}Using tool {tool_name}...{Style.RESET_ALL}\n"
                        tool_output = self.utilize_tool(tool_name, tool_args)
                        tool_outputs[tool_name] = tool_output
                        logger.debug(f"Use tool: {tool_name}, Output: {tool_output}")
                    yield "\n"

                # If there are tool outputs, feed them back to the LLM
                if tool_outputs:
                    for next_response in self.assist(
                        context,
                        prompts,
                        tool_messages=[
                            f"Output from {k}: {v}" for k, v in tool_outputs.items()
                        ],
                    ):
                        yield next_response
            elif finish_reason == "stop":
                # Last chunk, so log the full response and the response info, and yield a newline
                logger.debug(f"Response: {full_response}")
                yield "\n"
            elif finish_reason == "usage":
                logger.debug(f"Response Info: {chunk.usage}")
                logger.debug("Streaming complete.")


class MistralAPI(Provider):
    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        no_tools: bool = False,
    ):
        """Initialize the MistralAPI class.

        Args:
            model_name (str): Model name
            api_key (str, optional): The API key. Defaults to None.
            base_url (str, optional): The base URL. Defaults to None, which means the official Mistral API.
            temperature (float, optional): LLM Temperature. Defaults to None.
            top_p (float, optional): LLM Top-P value. Defaults to None.
            no_tools (bool, optional): No-tools flag. Defaults to False.
        """

        self.model_name: str = model_name
        self.api_key: str | None = api_key
        self.base_url: str | None = base_url
        self.temperature: float | None = temperature
        self.top_p: float | None = top_p
        self.llm: Mistral = Mistral(api_key=api_key, server_url=base_url)
        self.no_tools: bool = no_tools

    def get_models(self, full: bool = False) -> list[str]:
        """Get available models from the Mistral API.

        Args:
            full (bool, optional): Read from official model list if set to True, otherwise, return the hardcoded list. Defaults to False.

        Returns:
            list[str]: The available models
        """

        if full:
            model_response = self.llm.models.list()
            model_list = model_response.data if model_response else []
            return sorted([model.id for model in (model_list or [])])
        return [
            "mistral-large-latest",
            "mistral-small-latest",
            "codestral-latest",
            "open-mistral-nemo",
        ]

    def utilize_tool(self, tool: FunctionCall) -> str:
        """Utilize a tool.

        Args:
            tool (FunctionCallTypedDict): The tool to utilize

        Returns:
            str: The output of the tool
        """

        name: str = tool.name
        args = (
            tool.arguments
            if isinstance(tool.arguments, dict)
            else json.loads(tool.arguments)
        )
        if tools.get(name):
            confirm = input(f"Use tool {name} with arguments {args}? (y/n): ").lower()
            return (
                tools[name].function(
                    **args if isinstance(args, dict) else {"arg": args}
                )
                if confirm == "y"
                else "User cancelled."
            )
        return ""

    def assist(
        self,
        context: list[str],
        prompts: list[str],
        tool_messages: list[str] | None = None,
    ) -> Generator[str, None, None]:
        """Assist the user with the given context and prompts.

        Args:
            context (dict[str, str]): The context, which are system messages
            prompts (list[str]): The prompts, which are user messages
            tool_messages (list[str], optional): The output from tools, which are user messages. Defaults to [].

        Yields:
            Generator[str, None, None]: The response from the LLM
        """

        # Get the response stream from the LLM
        response = self.llm.chat.stream(
            model=self.model_name,
            messages=[
                *[SystemMessage(role="system", content=msg) for msg in context],
                *[UserMessage(role="user", content=prompt) for prompt in prompts],
                *[
                    UserMessage(role="user", content=msg)
                    for msg in (tool_messages or [])
                ],
            ],
            tools=(
                [tool.mistral_tool for tool in tools.values()]
                if not self.no_tools
                else None
            ),
            temperature=self.temperature,
            top_p=self.top_p,
        )

        # Log the context, prompts, and tool messages
        logger = LoggerManager.get_logger()
        logger.debug(f"Context: {context}")
        logger.debug(f"Prompts: {prompts}")
        logger.debug(f"Tool Messages: {tool_messages}")

        full_response = ""
        for chunk in response or []:
            message = chunk.data.choices[0].delta
            finish_reason = chunk.data.choices[0].finish_reason

            if message.role:
                # First chunk, so also print the system message
                yield f"{Fore.GREEN}{message.role}({chunk.data.model}): {Style.RESET_ALL}"

            if not finish_reason:
                # Middle chunk, so just print the content
                if not message.content:
                    yield ""
                elif isinstance(message.content, str):
                    full_response += message.content
                    yield message.content
                elif isinstance(message.content, list):
                    cancatenated_content = " ".join(
                        [str(msg) for msg in message.content]
                    )
                    full_response += cancatenated_content
                    yield cancatenated_content
            elif finish_reason == "tool_calls":
                # Tool calls, so utilize the tools and feed the output back to the LLM
                tool_outputs = {}

                # Utilize the tools and log the output
                tool_calls = message.tool_calls
                if tool_calls:
                    for tool in tool_calls:
                        yield f"{Fore.GREEN}Using tool {tool.function.name}...{Style.RESET_ALL}\n"
                        tool_output = self.utilize_tool(tool.function)
                        tool_outputs[tool.function.name] = tool_output
                        logger.debug(f"Use tool: {tool}, Output: {tool_output}")
                    yield "\n"

                # If there are tool outputs, feed them back to the LLM
                if tool_outputs:
                    for next_response in self.assist(
                        context,
                        prompts,
                        tool_messages=[
                            f"Output from tool {k}: {v}"
                            for k, v in tool_outputs.items()
                        ],
                    ):
                        yield next_response
            elif finish_reason == "stop":
                # Last chunk, so log the full response and the response info, and yield a newline
                logger.debug(f"Response: {full_response}")
                logger.debug(f"Response Info: {chunk.data.usage}")
                yield "\n"
                logger.debug("Streaming complete.")


class GeminiAPI(Provider):
    def __init__(
        self,
        model_name,
        api_key=None,
        base_url=None,
        temperature=None,
        top_p=None,
        no_tools=False,
    ):
        self.model_name: str = model_name
        self.api_key: str | None = api_key
        self.base_url: str | None = base_url
        self.temperature: float | None = temperature
        self.top_p: float | None = top_p
        self.no_tools: bool = no_tools
        Gemini.configure(api_key=api_key)
        self.llm: Gemini.GenerativeModel = Gemini.GenerativeModel(
            model_name,
            generation_config=GenerationConfig(
                temperature=self.temperature,
                top_p=self.top_p,
            ),
            tools=(
                [tool.gemini_tool for tool in tools.values()]
                if not self.no_tools
                else None
            ),
        )

    def get_models(self, full=False) -> list[str]:
        if full:
            return sorted([model["name"] for model in Gemini.list_models()])
        return ["gemini-1.5-pro-002", "gemini-1.5-flash-002", "gemini-1.5-flash-8b-001"]

    def utilize_tool(self, name: str, args: dict[str, str]) -> str:
        if tools.get(name):
            confirm = input(f"Use tool {name} with arguments {args}? (y/n): ").lower()
            return (
                tools[name].function(
                    **args if isinstance(args, dict) else {"arg": args}
                )
                if confirm == "y"
                else "User cancelled."
            )
        return ""

    def assist(
        self,
        context: list[str],
        prompts: list[str],
        tool_calls: list[dict] = [],
        tool_messages: list[str] | None = None,
    ) -> Generator[str, None, None]:
        """Assist the user with the given context and prompts.

        Args:
            context (list[str]): The context, which are system messages
            prompts (list[str]): The prompts, which are user messages
            tool_messages (list[str], optional): The output from tools, which are user messages. Defaults to None.

        Yields:
            Generator[str, None, None]: The response from the LLM
        """

        # Get the response stream from the LLM
        tool_messages_gemini_use = []
        for msg in tool_messages or []:
            tool_msg_struct = Struct()
            tool_msg_struct.update({"result": msg})
            tool_messages_gemini_use.append(
                Part(
                    function_response=FunctionResponse(
                        name="run_command", response=tool_msg_struct
                    )
                )
            )
        chat = self.llm.start_chat(
            history=[
                *[Content(role="user", parts=[Part(text=msg)]) for msg in context],
                *[
                    Content(role="user", parts=[Part(text=prompt)])
                    for prompt in prompts[:-1]
                ],
                *[
                    Content(
                        role="model",
                        parts=[
                            Part(
                                function_call=GeminiFunctionCall(
                                    name=tool_call["name"], args=tool_call["args"]
                                )
                            )
                        ],
                    )
                    for tool_call in tool_calls
                ],
                *[
                    Content(role="user", parts=[msg])
                    for msg in tool_messages_gemini_use
                ],
            ],
        )
        response = chat.send_message(
            prompts[-1],
            # TODO: The `google.generativeai` SDK currently does not support the combination of `stream=True` and `enable_automatic_function_calling=True`.
            # stream=True,
        )

        logger = LoggerManager.get_logger()
        logger.debug(f"Context: {context}")
        logger.debug(f"Prompts: {prompts}")
        logger.debug(f"Tool Messages: {tool_messages}")

        logger.debug(f"Response: {response}")
        tool_calls = []
        tool_outputs = {}
        parts = response.parts
        for part in parts:
            if part.text:
                logger.debug(f"Response: {part.text}")
                logger.debug(f"Response Info: {response.usage_metadata}")
                logger.debug("Responsing complete.")
                yield part.text
            elif part.function_call:
                tool_name = part.function_call.name
                tool_args = {k: str(v) for k, v in part.function_call.args.items()}
                tool_output = self.utilize_tool(tool_name, tool_args)
                tool_calls.append({"name": tool_name, "args": tool_args})
                tool_outputs[tool_name] = tool_output
                logger.debug(f"Use tool: {tool_name}, Output: {tool_output}")
                yield "\n"

        if tool_outputs:
            for next_response in self.assist(
                context,
                prompts,
                tool_calls=tool_calls,
                tool_messages=[f"{v}" for k, v in tool_outputs.items()],
            ):
                yield next_response


class OllamaAPI(Provider):
    def __init__(
        self,
        model_name,
        api_key=None,
        base_url=None,
        temperature=None,
        top_p=None,
        no_tools=False,
    ):
        self.model_name: str = model_name
        self.base_url: str | None = base_url
        self.temperature: float | None = temperature
        self.top_p: float | None = top_p
        self.llm: ollama.Client = ollama.Client(host=base_url)
        self.no_tools: bool = no_tools

    def get_models(self, full=False) -> list[str]:
        return [model["name"] for model in ollama.list()["models"]]

    def utilize_tool(self, tool) -> str: ...

    def assist(
        self,
        context: list[str],
        prompts: list[str],
        tool_messages: list[str] | None = None,
    ) -> Generator[str, None, None]: ...


LLM_PROVIDERS: dict[str, Type[Provider]] = {
    "OPENAI": OpenAIAPI,
    "MISTRAL": MistralAPI,
    "GEMINI": GeminiAPI,
    "OLLAMA": OllamaAPI,
}


def create_assistant(
    provider: str,
    model_name: str,
    temperature: float | None = None,
    top_p: float | None = None,
    no_tools: bool = False,
) -> Provider | None:
    """Create an assistant from the given provider and model name.

    Args:
        provider (str): The provider
        model_name (str): The model name
        temperature (float, optional): LLM temperature. Defaults to None.
        top_p (float, optional): LLM Top-P value. Defaults to None.
        no_tools (bool, optional): Do not pass tool list to LLM if set to True. It can reduce the token usage but also the functionality. Defaults to False.

    Returns:
        OpenAIAPI | MistralAPI | None: The assistant instance or None if the provider or model is not found
    """

    config = load_config()
    provider = provider.upper()
    provider_config: dict = config.get(provider) or {}
    if provider_config.get("API_KEY", None):
        provider_class: Type[Provider] | None = LLM_PROVIDERS.get(provider, None)
        if provider_class:
            return provider_class(
                model_name=model_name,
                api_key=provider_config.get("API_KEY") if provider_config else None,
                base_url=provider_config.get("BASE_URL") if provider_config else None,
                temperature=(
                    temperature or provider_config.get("TEMPERATURE")
                    if provider_config
                    else None
                ),
                top_p=(
                    top_p or provider_config.get("TOP_P") if provider_config else None
                ),
                no_tools=no_tools,
            )
    return None


def get_provider(model: str) -> str:
    """Get the provider for the given model.

    Args:
        model (str): The model name

    Returns:
        str: The provider name
    """

    for provider in LLM_PROVIDERS:
        assistant = create_assistant(provider, "")
        if assistant:
            if model.lower() in [m.lower() for m in assistant.get_models()]:
                return provider
    return ""


def get_available_models() -> dict[str, list[str]]:
    """Get all available models from all providers.

    Returns:
        dict[str, list[str]]: The available models, where the key is the provider and the value is the list of models
    """

    available_models: dict[str, list[str]] = {}
    for provider in LLM_PROVIDERS:
        assistant = create_assistant(provider, "")
        if assistant:
            available_models[provider] = assistant.get_models()
    return available_models
