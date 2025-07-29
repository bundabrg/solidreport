from typing import List, Dict, Any

from pydantic import BaseModel

from models import config


class Recipient(BaseModel):
    name: str
    email: str


class ActionModel(config.Action):
    defaults: Dict[str, Any] = {}
    from_name: str | None = "Reporting Bot"
    subject: str | None = None
    email_logo: str | None = None
    attachment_name: str = "Report Summary.pdf"
    email_template: str = "send_client_times"
    recipients: List[Recipient]
