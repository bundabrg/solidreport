import os

from jinja2 import Environment, FileSystemLoader

from filters import FILTERS
from lib.utils import override_str
from models.config import Config


def jinja(cfg: Config):
    templates_location = [
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "templates/html"
        )
    ]
    if cfg.override:
        templates_location = [
            os.path.join(cfg.override, "templates/html")
        ] + templates_location

    # Setup Template Environment
    env = Environment(loader=FileSystemLoader(templates_location))
    for filter_name, filter in FILTERS.items():
        env.filters[filter_name] = filter
    return env
