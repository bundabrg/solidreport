import contextlib

from gotenberg_client import GotenbergClient

from models.config import Config


def gotenberg(cfg: Config):

    @contextlib.contextmanager
    def wrapper():
        yield GotenbergClient(cfg.gotenberg.uri)

    return wrapper