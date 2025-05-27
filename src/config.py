import os
import yaml


# default config
CONFIG = {
    "HISTORY_CONTEXT_SIZE": 5,
    "TEMPERATURE": 0.7,
    "TOP_P": 1,
    "DEFAULT_MODEL": "gpt-4o",
    "OPENAI": {
        "BASE_URL": "https://api.openai.com/v1",
        "API_KEY": "",
    },
    "MISTRAL": {
        "BASE_URL": "https://api.mistral.ai",
        "API_KEY": "",
    },
}


def load_config():
    filename = os.getenv(
        "ASSISTANT_CONFIG", f'{os.path.expanduser("~")}/.assistant.yaml'
    )
    # load config file
    if os.path.exists(filename):
        with open(filename, "r") as f:
            CONFIG.update(yaml.safe_load(f))
    else:
        print(f"Config file not found at {filename}, using defaults.")
    return CONFIG
