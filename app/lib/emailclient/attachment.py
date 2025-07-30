import os
from enum import Enum
from typing import Optional


class AttachType(Enum):
    APPLICATION = 0
    AUDIO = 1
    IMAGE = 2


class File(object):
    def __init__(
        self,
        path: str,
        name: Optional[str] = None,
        typeof: AttachType = AttachType.APPLICATION,
    ):
        self.path = path
        self.name = name if name is not None else os.path.basename(path)
        self.typeof = typeof
