import os

from filters import FILTERS
from lib import emailclient
from lib.utils import override_str
from models.config import Config


def email(cfg: Config):
    templates_location = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "templates/email")]
    if cfg.override:
        templates_location = [os.path.join(cfg.override, "templates/email")] + templates_location

    # Load Email Manager
    email_manager = emailclient.Manager(
        host=cfg.email.host,
        port=cfg.email.port,
        username=cfg.email.username,
        password=cfg.email.password,
        from_name=cfg.email.from_name,
        from_email=cfg.email.from_email,
        templates=templates_location,
    )

    # Add on our filters
    for filter_name, filter in FILTERS.items():
        email_manager.jinja.filters[filter_name] = filter

    return email_manager
