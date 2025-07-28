import os

from jinja2 import Environment, FileSystemLoader

from filters import FILTERS
from models.config import Config


def jinja(cfg: Config):
    # Setup Template Environment
    env = Environment(
        loader=FileSystemLoader(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "templates/html")
        )
    )
    for filter_name, filter in FILTERS.items():
        env.filters[filter_name] = filter
    return env
