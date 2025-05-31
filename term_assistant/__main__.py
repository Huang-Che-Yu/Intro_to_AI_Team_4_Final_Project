import logging
from .llm import get_provider, get_available_models, create_assistant
from .terminal import get_history, get_current_dir
from .config import load_config
from .logging import get_logger

import click
from colorama import Fore, Style

from .config import load_config
from .llm import create_assistant, get_available_models, get_provider
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
    "--history-context-size",
    type=int,
    help="Number of lines of history to include in the context",
    default=0,
)
@click.option(
    "-p",
    "--provider",
    type=str,
    help="Provider to use for completion",
    default=None,
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
    history_context_size,
    provider,
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
        system_msg = config["SYSTEM_MESSAGES"].get(config["DEFAULT_SYSTEM_MESSAGE"], "")
    else:
        system_msg = (
            system if " " in system else config["SYSTEM_MESSAGES"].get(system, "")
        )
    if system_msg != "":
        context.append(system_msg)
    else:
        logger.warning(
            f"System message {system} not found in the configuration, using empty message."
        )
    # Prepare the context
    if not no_context:
        if not no_pwd and "pwd" in config["CONTEXTS"]:
            context.append(f"The current directory is {get_current_dir()}")
        if not no_shell and "shell" in config["CONTEXTS"]:
            context.append(f"The current shell is {get_current_shell()}")
        if not no_history and "history" in config["CONTEXTS"]:
            history_context_size = (
                history_context_size or config["HISTORY_CONTEXT_SIZE"]
            )
            context.append(
                "The terminal session are: "
                "\n".join(get_history(history_context_size))
            )

    # Prepare the model and provider
    if model is None:
        model = config["DEFAULT_MODEL"]
    if not provider:
        provider = get_provider(model)

    # Create the assistant and get the response
    assistant = create_assistant(provider, model, temperature, top_p, no_tools)
    if assistant:
        logger.info(f"Using model {model} from provider {assistant.__class__.__name__}")
        if not dry_run:
            for response in assistant.assist(context, [prompt]):
                print(response, end="", flush=True)
        else:
            logger.debug(f"[Dry run] Context: {context}")
            logger.debug(f"[Dry run] Prompt: {prompt}")
            logger.info("Dry run completed.")
    else:
        logger.warning(f"Model {model} not found in any provider.")


@cli.command()
def models():
    """
    Lists all available models from all providers.
    """
    available_models = get_available_models()
    for provider, model_names in available_models.items():
        print(f"{Fore.BLUE}Provider: {provider}{Style.RESET_ALL}")
        for model in model_names:
            print(f"  {model}")


if __name__ == "__main__":
    cli()
