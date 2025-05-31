import os
from dataclasses import dataclass, field

import yaml


@dataclass
class OpenAIConfig:
    """
    Configuration settings for OpenAI.

    Attributes:
        BASE_URL (str): The base URL for the OpenAI API.
        API_KEY (str): The API key for the OpenAI API.
    """

    BASE_URL: str = "https://api.openai.com/v1"
    API_KEY: str = ""


@dataclass
class MistralConfig:
    """
    Configuration settings for Mistral.

    Attributes:
        BASE_URL (str): The base URL for the Mistral API.
        API_KEY (str): The API key for the Mistral API.
    """

    BASE_URL: str = "https://api.mistral.ai"
    API_KEY: str = ""


@dataclass
class GeminiConfig:
    """
    Configuration settings for Gemini.

    Attributes:
        BASE_URL (str): The base URL for the Gemini API.
        API_KEY (str): The API key for the Gemini API.
    """

    BASE_URL: str = "https://api.gemini.com"
    API_KEY: str = ""


@dataclass
class OllamaConfig:
    """
    Configuration settings for Ollama.

    Attributes:
        BASE_URL (str): The base URL for the Ollama API.
        API_KEY (str): The API key for the Ollama API.
    """

    BASE_URL: str = "https://api.ollama.com"
    API_KEY: str = ""


@dataclass
class Config:
    """
    Configuration settings for the term assistant application.

    Attributes:
        HISTORY_CONTEXT_SIZE (int): The size of the history context to be used.
        TEMPERATURE (float): The temperature setting for the model.
        TOP_P (float): The top-p setting for the model.
        DEFAULT_MODEL (str): The default model to be used.
        DEFAULT_SYSTEM_MESSAGE (str): The default system message to be used.
        SYSTEM_MESSAGES (dict): A dictionary of system messages.
        OPENAI (OpenAIConfig): Configuration settings for OpenAI.
        MISTRAL (MistralConfig): Configuration settings for Mistral.
        GEMINI (GeminiConfig): Configuration settings for Gemini.
        OLLAMA (OllamaConfig): Configuration settings for Ollama.
    """

    HISTORY_CONTEXT_SIZE: int = 5
    TEMPERATURE: float = 0.7
    TOP_P: float = 1.0
    DEFAULT_MODEL: str = "gpt-4o"
    DEFAULT_SYSTEM_MESSAGE: str = "default"
    SYSTEM_MESSAGES: dict[str, str] = field(default_factory=dict)
    CONTEXTS: list[str] = field(default_factory=lambda: ["shell", "pwd", "history"])
    OPENAI: OpenAIConfig = field(default_factory=OpenAIConfig)
    MISTRAL: MistralConfig = field(default_factory=MistralConfig)
    GEMINI: GeminiConfig = field(default_factory=GeminiConfig)
    OLLAMA: OllamaConfig = field(default_factory=OllamaConfig)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


DEFAULT_CONFIG = Config()


def load_config() -> Config:
    """Load the configuration from the config file.

    Returns:
        Config: The configuration object
    """

    filename = os.getenv(
        "ASSISTANT_CONFIG", f'{os.path.expanduser("~")}/.assistant.yaml'
    )
    # load config file
    if os.path.exists(filename):
        with open(filename, "r") as f:
            config = yaml.safe_load(f)
            return Config(**config)
    else:
        print(f"Config file not found at {filename}, using defaults.")
    return DEFAULT_CONFIG
