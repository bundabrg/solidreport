import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from filters import FILTERS
from models.config import Config


def jinja(cfg: Config):
    # Setup Template Environment
    env = Environment(
        loader=FileSystemLoader(
            [
                cfg.sr_data.joinpath("templates/html"),
                Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                    "../templates/html"
                ),
            ]
        )
    )
    for filter_name, filter in FILTERS.items():
        env.filters[filter_name] = filter
    return env
