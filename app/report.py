import os
from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader

import reports
from filters import FILTERS
from lib.config import load_config
from models.config import Config


@click.group()
@click.option("--config", help="Configuration File", default="config.yml")
@click.pass_context
def cli(ctx, config):
    # Try load config
    cfg = load_config(Path(config), None, Config)
    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg

    # Setup Template Environment
    env = Environment(
        loader=FileSystemLoader(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")
        )
    )
    for filter_name, filter in FILTERS.items():
        env.filters[filter_name] = filter
    ctx.obj["template"] = env


if __name__ == "__main__":
    # Add All Reports as Commands
    for c in reports.GENERATE:
        cli.add_command(c)

    cli()
