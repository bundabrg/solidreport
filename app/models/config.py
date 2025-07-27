import uuid

from pydantic import BaseModel

class Defaults(BaseModel):
    """
    If not specified on the commandline, these will be used instead
    """
    organization: uuid.UUID | None = None

class Db(BaseModel):
    host: str
    database: str
    username: str
    password: str

class Gotenberg(BaseModel):
    uri: str = "http://127.0.0.1:3000"

class Config(BaseModel):
    defaults: Defaults = Defaults()
    db: Db | None = None
    gotenberg: Gotenberg = Gotenberg()
