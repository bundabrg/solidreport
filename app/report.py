from pathlib import Path

import click

import commands
from lib.config import load_config
from models.config import Config


@click.group()
@click.option("--config", help="Configuration File", default="config.yml")
@click.option(
    "--sr-data",
    help="Where to find config, output and additional templates",
    default=".",
)
@click.pass_context
def cli(ctx, config, sr_data):
    # Try load config
    cfg = load_config([Path(config), Path(sr_data).joinpath(config)], None, Config)
    cfg.sr_data = Path(sr_data)
    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg


if __name__ == "__main__":
    # Add All Reports as Commands
    for c in commands.COMMANDS:
        cli.add_command(c)

    cli()
