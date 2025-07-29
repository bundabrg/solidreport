import datetime
import tempfile
from typing import List, Dict

import systems
from lib import emailclient
from models.config import Config
from reports import staff_times
from .models import ActionModel


def execute(cfg: Config, action_cfg: ActionModel, var: Dict[str, str]):
    db = systems.database(cfg)
    env = systems.jinja(cfg)
    gotenberg = systems.gotenberg(cfg)
    email_manager = systems.email(cfg)

    # Apply defaults
    args = {
        "organization_id": var.get("organization_id"),
        "template": var.get("template"),
        "footer_template": var.get("footer_template"),
        "start": (
            datetime.datetime.strptime(var.get("start"), "%Y-%m-%d").date()
            if var.get("start")
            else None
        ),
        "end": (
            datetime.datetime.strptime(var.get("end"), "%Y-%m-%d").date()
            if var.get("end")
            else None
        ),
        "project_filter": var.get("project_filter"),
        "member_filter": var.get("member_filter"),
        "client_filter": var.get("client_filter"),
        "member_id_filter": var.get("member_id_filter"),
    }
    defaults = {
        "start": datetime.date.today(),
        "end": datetime.date.today(),
    }
    args = {
        k: (
            v
            if v is not None
            else action_cfg.defaults.get(k, cfg.defaults.get(k, defaults.get(k)))
        )
        for k, v in args.items()
    }

    attachment_name = var.get("attachment_name", action_cfg.attachment_name)
    email_logo = var.get("email_logo", action_cfg.email_logo)
    subject = var.get("subject", action_cfg.subject)

    if subject:
        subject = subject.format(
            start=args["start"].strftime("%d/%m/%Y"),
            end=args["end"].strftime("%d/%m/%Y"),
        )

    # Add resources if any passed
    resource = (
        cfg.defaults.get("resource", [])
        + action_cfg.defaults.get("resource", [])
        + list(var.get("resource", []))
    )

    args["resources"] = {}
    for r in resource:
        r_split = r.split(":", 1)
        r_path = r_split[1] if len(r_split) == 2 else r
        args["resources"][r_split[0]] = cfg.sr_data.joinpath(r_path)

    with tempfile.NamedTemporaryFile() as tmp:
        # Generate summary times
        data = staff_times.report(
            db,
            env,
            gotenberg,
            output=tmp.name,
            **{k: v for k, v in args.items() if v is not None}
        )

        # Email to each recipient
        for r in action_cfg.recipients:
            print("    - Sending to {}".format(r.email))

            email = email_manager.new()
            email.to.append(r.email)
            email.subject = subject
            email.template = var.get("email_template", action_cfg.email_template)
            email.template_args = {
                "name": r.name,
                "from_name": action_cfg.from_name,
                "logo": "logo.png" if email_logo else None,
                "start": args["start"].strftime("%d/%m/%Y"),
                "end": args["end"].strftime("%d/%m/%Y"),
                "data": data,
            }
            if email_logo:
                email.embed.append(
                    emailclient.File(
                        str(cfg.sr_data .joinpath(email_logo)), "logo.png", typeof=email.AttachType.IMAGE
                    )
                )

            email.attach.append(
                emailclient.File(
                    tmp.name, name=attachment_name, typeof=email.AttachType.APPLICATION
                )
            )
            email.send()
