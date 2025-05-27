from .llm import get_provider, get_available_models, create_assistant
from .terminal import get_history, get_current_dir
from .config import load_config
from .logging import get_logger
import click
from colorama import Fore, Style


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        ctx.invoke(talk)


@cli.command()
@click.argument("prompt", required=False)
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
def talk(
    prompt,
    model,
    history_context_size,
    provider,
    dry_run,
    no_context,
    no_pwd,
    no_history,
    temperature,
    top_p,
    no_tools,
):
    logger = get_logger()
    config = load_config()
    context = {}
    if not no_context:
        if not no_pwd:
            context["The current directory is"] = get_current_dir()
        if not no_history:
            history_context_size = (
                history_context_size or config["HISTORY_CONTEXT_SIZE"]
            )
            context["The commands executed above are"] = get_history(
                history_context_size
            )
    if model is None:
        model = config["DEFAULT_MODEL"]
    if not prompt:
        prompt = input("(Enter your prompt) >>> ")
    if not provider:
        provider = get_provider(model)
    assistant = create_assistant(provider, model, temperature, top_p, no_tools)
    if assistant:
        logger.info(f"Using model {model} from provider {assistant.__class__.__name__}")
        if not dry_run:
            for response in assistant.assist(context, [prompt]):
                print(response, end="", flush=True)
    else:
        logger.warning(f"Model {model} not found in any provider.")


@cli.command()
def models():
    models = get_available_models()
    for provider, models in models.items():
        print(f"{Fore.BLUE}Provider: {provider}{Style.RESET_ALL}")
        for model in models:
            print(f"  {model}")


if __name__ == "__main__":
    cli()
