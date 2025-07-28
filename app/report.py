import os
import sys
from pathlib import Path
from pprint import pprint

import click
import psycopg2
from jinja2 import Environment, FileSystemLoader

import commands
import reports
from filters import FILTERS
from lib.config import load_config
from lib.utils import override_path
from models.config import Config


@click.group()
@click.option("--config", help="Configuration File", default="config.yml")
@click.option("--override", help="Folder that contains files that override local files")
@click.pass_context
def cli(ctx, config, override):
    # Try load config
    cfg = load_config(override_path(Path(config), override), None, Config)
    cfg.override = override
    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg

if __name__ == "__main__":
    # Add All Reports as Commands
    for c in commands.COMMANDS:
        cli.add_command(c)

    cli()
