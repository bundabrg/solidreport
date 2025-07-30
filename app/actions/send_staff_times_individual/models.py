from typing import Dict, Any

from models import config


class ActionModel(config.Action):
    defaults: Dict[str, Any] = {}
    from_name: str | None = "Reporting Bot"
    subject: str | None = None
    email_logo: str | None = None
    attachment_name: str = "Report Summary.pdf"
    email_template: str = "send_staff_times_individual"

    # Send to force_recipient instead of the user themselves
    force_recipient: str | None = None
