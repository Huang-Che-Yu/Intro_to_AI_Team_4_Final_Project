import os

from term_assistant.config import load_config


def test_load_config():
    os.environ["ASSISTANT_CONFIG"] = "tests/assistant.yaml"
    config = load_config()
    assert config is not None
    assert config.generation.temperature == 0.7
    assert not config.generation.with_tools
    assert config.default_model == "openai/gpt-4o"
    assert set(config.contexts) == {"shell", "pwd", "history"}
    assert config.history_context_options.size == 0
    assert config.system_messages["default"]
    assert config.providers["openai"].api_key == "sk-xxxxx"
    assert config.providers["ollama"].base_url == "http://localhost:11434"
