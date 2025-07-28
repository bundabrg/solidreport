import uuid
from typing import Dict, List, Any

from pydantic import BaseModel, ConfigDict


class Db(BaseModel):
    host: str
    database: str
    username: str
    password: str


class Gotenberg(BaseModel):
    uri: str = "http://127.0.0.1:3000"


class Email(BaseModel):
    host: str
    port: int = 587
    username: str | None = None
    password: str | None = None
    from_name: str | None = None
    from_email: str | None = None


class Action(BaseModel):
    description: str | None = None
    action: str
    model_config = ConfigDict(extra="allow")


class Config(BaseModel):
    defaults: Dict[str, Any]
    db: Db | None = None
    email: Email | None = None
    gotenberg: Gotenberg = Gotenberg()
    actions: Dict[str, List[Action]] = {}
