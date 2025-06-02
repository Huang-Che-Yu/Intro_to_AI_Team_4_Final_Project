import logging
from .llm import get_provider, get_available_models, create_assistant
from .terminal import get_history, get_current_dir
from .config import load_config
from .logging import get_logger

import click

from .config import load_config
from .llm import Provider, create_assistant
from .logging import LoggerManager
from .terminal import get_current_dir, get_current_shell, get_history


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        ctx.invoke(talk)


@cli.command()
@click.argument("prompt", required=True)
@click.option(
    "-m", "--model", type=str, help="Model to use for completion", default=None
)
@click.option(
    "-h",
    "--history-size",
    type=int,
    help="Number of lines of history to include in the context",
    default=0,
)
@click.option(
    "--all-panes",
    is_flag=True,
    help="Include history from all panes in the context",
)
@click.option("-s", "--system", type=str, help="The system message", default=None)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Perform a dry run without executing the assistant",
)
@click.option(
    "--no-context",
    is_flag=True,
    help="Do not include any context in the prompt",
)
@click.option(
    "--no-pwd",
    is_flag=True,
    help="Do not include the current directory in the context",
)
@click.option(
    "--no-shell",
    is_flag=True,
    help="Do not include the current shell in the context",
)
@click.option(
    "--no-history",
    is_flag=True,
    help="Do not include the command history in the context",
)
@click.option(
    "--temperature",
    type=float,
    help="The temperature to use for sampling",
    default=None,
)
@click.option(
    "--top-p",
    type=float,
    help="The top-p value to use for sampling",
    default=None,
)
@click.option(
    "--no-tools",
    is_flag=True,
    help="Do not include the tools in the context",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose mode")
def talk(
    prompt,
    model,
    history_size,
    all_panes,
    system,
    dry_run,
    no_context,
    no_pwd,
    no_shell,
    no_history,
    temperature,
    top_p,
    no_tools,
    verbose,
):
    """
    Takes a prompt and returns a response from the assistant.
    """
    logger = LoggerManager.get_logger(level=logging.DEBUG if verbose else logging.INFO)
    config = load_config()

    context: list[str] = []
    # System message
    system_msg = ""
    if system is None:
        system_msg = config.system_messages.get(config.default_system_message, "")
    else:
        system_msg = system if " " in system else config.system_messages.get(system, "")
    if system_msg != "":
        context.append(system_msg)
    else:
        logger.warning(
            f"System message {system} not found in the configuration, using empty message."
        )
    # Prepare the context
    if not no_context:
        selected_contexts = config.contexts
        if not no_pwd and "pwd" in selected_contexts:
            context.append(f"The current directory is {get_current_dir()}")
        if not no_shell and "shell" in selected_contexts:
            context.append(f"The current shell is {get_current_shell()}")
        if not no_history and "history" in selected_contexts:
            history_size = history_size or config.history_context_options.size
            context.append(
                f"The terminal session are: \n"
                f"{'\n'.join(get_history(history_size, all_panes=all_panes or config.history_context_options.all_panes))}"
            )

    # Prepare the model
    if model is None:
        model = config.default_model
    model = model.lower()

    # Create the assistant and get the response
    assistant = create_assistant(model, temperature, top_p, no_tools)
    if assistant:
        logger.info(f"Using model {model}")
        if not dry_run:
            for response in assistant.assist(
                Provider.compose_messages(context, [prompt])
            ):
                print(response, end="", flush=True)
        else:
            logger.debug(f"[Dry run] Context: {context}")
            logger.debug(f"[Dry run] Prompt: {prompt}")
            logger.info("Dry run completed.")
    else:
        logger.warning(f"Model {model} not found.")


@cli.command()
def models():
    """
    Lists all available models from all providers.
    """
    print(
        "Please visit https://docs.litellm.ai/docs/providers to "
        "view the available providers and models."
    )


if __name__ == "__main__":
    cli()
