import os
from dataclasses import dataclass, field

import yaml


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
        temperature (float): The temperature setting for the model.
        top_p (float): The top-p setting for the model.
        default_model (str): The default model to be used.
        default_system_message (str): The default system message to be used.
        system_messages (dict): A dictionary of system messages.
        contexts (list): A list of contexts to be used.
        contexts_options (dict): A dictionary of context options.
        providers (dict): A dictionary of provider configurations.
    """

    temperature: float = 0.7
    top_p: float = 1.0
    default_model: str = "gpt-4o"
    default_system_message: str = "default"
    system_messages: dict[str, str] = field(default_factory=dict)
    contexts: list[str] = field(default_factory=lambda: ["shell", "pwd", "history"])
    history_context_options: HistoryContextOptions = field(
        default_factory=HistoryContextOptions
    )
    providers: dict[str, ProviderConfig] = field(default_factory=dict)

    def __getitem__(self, key):
        return getattr(self, key)

    def __post_init__(self):
        self.providers = {
            provider: (
                config
                if isinstance(config, ProviderConfig)
                else ProviderConfig(**config)
            )
            for provider, config in self.providers.items()
        }
        self.history_context_options = (
            HistoryContextOptions(**self.history_context_options)
            if isinstance(self.history_context_options, dict)
            else self.history_context_options
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
            return Config(**config)
    else:
        print(f"Config file not found at {filename}, using defaults.")
    return DEFAULT_CONFIG
