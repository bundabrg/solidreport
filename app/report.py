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
from models.config import Config


@click.group()
@click.option("--config", help="Configuration File", default="config.yml")
@click.pass_context
def cli(ctx, config):
    # Try load config
    cfg = load_config(Path(config), None, Config)
    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg

if __name__ == "__main__":
    # Add All Reports as Commands
    for c in commands.COMMANDS:
        cli.add_command(c)

    cli()
