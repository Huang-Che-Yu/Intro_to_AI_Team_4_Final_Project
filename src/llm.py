import json
from .logging import get_logger
from .config import load_config
from .tools import tools
from mistralai import Mistral
from openai import OpenAI
from colorama import Fore, Style


# TODO: Implement the OpenAIAPI class
class OpenAIAPI:
    def __init__(
        self, model_name, api_key=None, base_url=None, temperature=None, top_p=None, no_tools=False
    ):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.llm = OpenAI(api_key=api_key, base_url=base_url)

    def get_models(self, full=False):
        if full:
            return sorted([m.id for m in self.llm.models.list()])
        return ["gpt-4", "gpt-4o", "gpt-4-mini"]

    def assist(self, context, prompt, file=None):
        if file:
            with open(file, "r") as f:
                content = f.read()
                prompt += f"\nFilename: {file}\n{content}"
        response = self.llm.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "\n".join(
                        [f"{k}:\n{v}" for k, v in context.items() if v]
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            tools=tools,
        )
        message = response.choices[0].message
        return f"{Fore.GREEN}{message.role}({response.model}): {Style.RESET_ALL}{message.content}"


class MistralAPI:
    def __init__(
        self, model_name, api_key=None, base_url=None, temperature=None, top_p=None, no_tools=False
    ):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.top_p = top_p
        self.llm = Mistral(api_key=api_key, server_url=base_url)
        self.no_tools = no_tools

    def get_models(self, full=False):
        if full:
            return sorted([m.id for m in self.llm.models.list().data])
        return [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "mistral-tiny-latest",
            "codestral-latest",
            "open-mistral-nemo",
        ]

    def utilize_tool(self, tool):
        name = tool.name
        args = json.loads(tool.arguments)
        if tools.get(name):
            confirm = input(f"Use tool {name} with arguments {args}? (y/n): ").lower()
            return tools[name].function(**args) if confirm == "y" else "User cancelled."
        return ""

    def assist(self, context, prompts, tool_messages=[]):
        response = self.llm.chat.stream(
            model=self.model_name,
            messages=[
                *[
                    {"role": "system", "content": f"{k}: {v}"}
                    for k, v in context.items()
                    if v
                ],
                *[{"role": "user", "content": prompt} for prompt in prompts],
                *[{"role": "user", "content": msg} for msg in tool_messages],
            ],
            tools=[tool.generate_tool_call() for tool in tools.values()] if not self.no_tools else [],
            temperature=self.temperature,
            top_p=self.top_p,
        )
        logger = get_logger()
        logger.debug(f"Context: {context}")
        logger.debug(f"Prompts: {prompts}")
        logger.debug(f"Tool Messages: {tool_messages}")

        full_response = ""

        for chunk in response:
            message = chunk.data.choices[0].delta
            finish_reason = chunk.data.choices[0].finish_reason
            if message.role:
                # First chunk, so also print the system message
                yield f"{Fore.GREEN}{message.role}({chunk.data.model}): {Style.RESET_ALL}"
            if not finish_reason:
                full_response += message.content
                yield message.content
            elif finish_reason == "tool_calls":
                tool_outputs = {}
                for tool in message.tool_calls:
                    yield f"{Fore.GREEN}Using tool {tool.function.name}...{Style.RESET_ALL} "
                    tool_output = self.utilize_tool(tool.function)
                    tool_outputs[tool.function.name] = tool_output
                    logger.debug(f"Use tool: {tool}, Output: {tool_output}")
                yield "\n"
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
                logger.debug(f"Reponse Info: {chunk.data.usage}")
                yield "\n"
                logger.debug("Streaming complete.")


LLM_PROVIDERS = {"OPENAI": OpenAIAPI, "MISTRAL": MistralAPI}


def create_assistant(provider, model_name, temperature=None, top_p=None, no_tools=False):
    config = load_config()
    provider = provider.upper()
    provider_config = config.get(provider, {})
    if provider_config.get("API_KEY", None):
        provider_class = LLM_PROVIDERS.get(provider)
        if provider_class:
            return provider_class(
                model_name=model_name,
                api_key=provider_config["API_KEY"],
                base_url=provider_config["BASE_URL"],
                temperature=temperature or provider_config.get("TEMPERATURE"),
                top_p=top_p or provider_config.get("TOP_P"),
                no_tools=no_tools,
            )
    return None


def get_provider(model):
    for provider in LLM_PROVIDERS.keys():
        assistant = create_assistant(provider, None)
        if model.lower() in [m.lower() for m in assistant.get_models()]:
            return provider
    return ""


def get_available_models():
    available_models = {}
    for provider in LLM_PROVIDERS.keys():
        assistant = create_assistant(provider, None)
        if assistant:
            available_models[provider] = assistant.get_models()
    return available_models
