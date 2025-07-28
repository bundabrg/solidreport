from typing import List

import jinja2

from .email import Email


class Manager(object):
    """
    Email Manager
    """

    def __init__(
            self,
            *,
            host: str,
            port: int = 587,
            username: str,
            password: str,
            from_name: str,
            from_email: str,
            templates: List[str],
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_name = from_name
        self.from_email = from_email
        self.templates = templates or []

        # Load Jinja Template Manager
        self.jinja = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.templates),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

    @property
    def from_full(self) -> str:
        return "{} <{}>".format(self.from_name, self.from_email)

    def new(self) -> Email:
        return Email(self)
