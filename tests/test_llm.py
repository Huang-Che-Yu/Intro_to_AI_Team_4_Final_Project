import os

from litellm import CustomStreamWrapper

from term_assistant.llm import Provider, create_assistant


def test_create_assistant():
    os.environ["ASSISTANT_CONFIG"] = "tests/assistant.yaml"
    assistant = create_assistant(
        model_name="openai/gpt-4o",
        dry_run=True,
    )
    assert assistant is not None
    assert assistant.model_name == "openai/gpt-4o"
    assert assistant.api_key == "sk-xxxxx"
    assert assistant.dry_run is True


def test_compose_messages():
    system_msg = ["You are a terminal assistant."]
    user_msg = ["How to use ps command"]
    messages = Provider.compose_messages(
        system_msg,
        user_msg,
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == system_msg[0]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == user_msg[0]


def test_get_llm_response():
    os.environ["ASSISTANT_CONFIG"] = "tests/assistant.yaml"
    assistant = create_assistant(
        model_name="openai/gpt-4o",
        dry_run=True,
    )
    assert assistant is not None
    response = assistant.get_llm_response([])
    assert response is not None
    assert isinstance(response, CustomStreamWrapper)
    full_response = ""
    for chunk in response:
        full_response += chunk.choices[0].delta.content or ""
    assert full_response == "Dry run completed."
