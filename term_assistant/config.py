import os
import sys
from dataclasses import dataclass, field

import yaml


@dataclass
class GenerationConfig:
    """
    Configuration settings for generation.

    Attributes:
        temperature (float): The temperature setting for the model.
        top_p (float): The top-p setting for the model.
        with_tools (bool): Whether to use tools in generation.
    """

    temperature: float = 0.7
    top_p: float = 1.0
    with_tools: bool = True


@dataclass
class ProviderConfig:
    """
    Configuration settings for a provider.

    Attributes:
        base_url (str): The base URL for the API.
        api_key (str): The API key for the API.
    """

    base_url: str = ""
    api_key: str = ""


@dataclass
class HistoryContextOptions:
    """
    Options for the history context.

    Attributes:
        size (int): The size of the history context.
        all_panes (bool): Whether to include all panes in the history context.
    """

    size: int = 0
    all_panes: bool = False


@dataclass
class Config:
    """
    Configuration settings for the term assistant application.

    Attributes:
        default_model (str): The default model to be used.
        default_system_message (str): The default system message to be used.
        generation (GenerationConfig): The generation configuration.
        system_messages (dict): A dictionary of system messages.
        contexts (list): A list of contexts to be used.
        history_context_options (HistoryContextOptions): The history context options.
        providers (dict): A dictionary of provider configurations.
    """

    default_model: str = "openai/gpt-4o"
    default_system_message: str = "default"
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    system_messages: dict[str, str] = field(default_factory=dict)
    contexts: list[str] = field(default_factory=lambda: ["shell", "pwd", "history"])
    history_context_options: HistoryContextOptions = field(
        default_factory=HistoryContextOptions
    )
    providers: dict[str, ProviderConfig] = field(default_factory=dict)

    def __getitem__(self, key):
        return getattr(self, key)

    def __post_init__(self):
        if isinstance(self.generation, dict):
            self.generation = GenerationConfig(
                temperature=self.generation.get("temperature", 0.7),
                top_p=self.generation.get("top_p", 1.0),
                with_tools=self.generation.get("with_tools", True),
            )
        self.providers = {
            provider: (
                config
                if isinstance(config, ProviderConfig)
                else ProviderConfig(**config)
            )
            for provider, config in self.providers.items()
        }
        if isinstance(self.history_context_options, dict):
            self.history_context_options = HistoryContextOptions(
                size=self.history_context_options.get("size", 0),
                all_panes=self.history_context_options.get("all_panes", False),
            )

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
            try:
                return Config(**config)
            except Exception as e:
                print(f"Error loading config file: {e}")
                sys.exit(1)
    else:
        print(f"Config file not found at {filename}, using defaults.")
    return DEFAULT_CONFIG
