# LLM in Terminal

LLM in Terminal is a command-line tool designed to assist users with prompt-based responses from various models. It supports customizable contexts, different models and providers, and options for managing input and output behaviors.

## Installation

You can download the repository and install the development dependencies.

```bash
$ git clone https://github.com/Huang-Che-Yu/Intro_to_AI_Team_4_Final_Project.git
$ poetry install
```

## Usage

The tool must run in tmux context (`$TMUX` environemnt variable must be set) since it uses tmux to capture the terminal history.

### Config

You can copy the `assistant.yaml.example` to your home directory and rename it to `assistant.yaml`.

You can fill your API keys to the `providers` section, for example

```yaml
...
providers:
  openai:
    base_url: ''
    api_key: 'sk-abc123456'
```

After filling the key, you can use all openai models.

#### More Providers

LLM in Terminal uses [litellm](https://github.com/BerriAI/litellm) as the SDK, so you can use any provider and model that litellm supports.

The full list of providers and models can be found in the [litellm documentation](https://docs.litellm.ai/docs/providers).

To use a provider, you need to fill the `api_key` in `providers` section in the config file (even if the key is not required for that provider, e.g., ollama).

The `base_url` is optional, and you can leave it empty if you are using the official providers.

#### Advanced Config

- `generation.temperature`: The temperature setting for the model.
- `generation.top_p`: The top-p setting for the model.
- `generation.with_tools`: Whether to use the tools in the generation.
- `default_model`: The default model to use.
- `default_system_message`: The default system message name to use. See the `system_messages` section.
- `contexts`: The contexts to use.
- `history_context_options.size`: The nunber of lines of the history context.
- `history_context_options.all_panes`: Whether to use all panes in the history context.
- `system_messages`: The list of available system messages, and you can add your own ones.

### Example

Ask what happened in this session:

```bash
term_assistant talk "what happened"
```

You can specify the model if you do not want to use the default model:

```bash
term_assistant talk "what happened" -m openai/gpt-4o-mini
```

You can also specify the system messages:

```bash
term_assistant talk "how to install nginx" -s "another_assistant_prompt"
```

Or you can directly pass the system message:

```bash
term_assistant talk "how to use tmux" -s "You are a terminal assistant, and you must not answer the questions unrelated to terminal."
```

### Logging

The chat context, user prompts, model responses, etc. will be recorded to the log file `~/.assistant.log`.
