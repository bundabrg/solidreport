import os

from filters import FILTERS
from lib import emailclient
from models.config import Config


def email(cfg: Config):
    # Load Email Manager
    email_manager = emailclient.Manager(
        host=cfg.email.host,
        port=cfg.email.port,
        username=cfg.email.username,
        password=cfg.email.password,
        from_name=cfg.email.from_name,
        from_email=cfg.email.from_email,
        templates=[os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "templates/email")],
    )

    # Add on our filters
    for filter_name, filter in FILTERS.items():
        email_manager.jinja.filters[filter_name] = filter

    return email_manager
