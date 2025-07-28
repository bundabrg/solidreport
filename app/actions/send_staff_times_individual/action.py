import sys
from datetime import datetime, timedelta
import tempfile
from psycopg2 import Error
from typing import List, Dict

from psycopg2.extras import NamedTupleCursor

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

    add = var.get("add", action_cfg.defaults.get("add", cfg.defaults.get("add")))
    organization = var.get(
        "organization",
        action_cfg.defaults.get("organization", cfg.defaults.get("organization")),
    )
    start = (
        datetime.strptime(var.get("start"), "%Y-%m-%d") if var.get("start") else datetime.today()
    )
    end = datetime.strptime(var.get("end"), "%Y-%m-%d") if var.get("end") else datetime.today()
    attachment_name = var.get("attachment_name", action_cfg.attachment_name)
    email_logo = var.get("email_logo", action_cfg.email_logo)
    subject = var.get("subject", action_cfg.subject)

    if subject:
        subject = subject.format(
            start=start.strftime("%d/%m/%Y"),
            end=end.strftime("%d/%m/%Y"),
        )

    # Lookup each staff member who has any time in this period
    try:
        with db.cursor(cursor_factory=NamedTupleCursor) as cursor:
            sql = """
                SELECT DISTINCT users.name as user_name, users.email as user_email
                FROM users JOIN members ON (members.user_id = users.id)
                    JOIN time_entries te ON (te.member_id = members.id)
                WHERE te.organization_id = %(organization_id)s
                    AND te.start >= %(start)s
                    AND te.end < %(end)s
                  """

            cursor.execute(
                sql,
                {
                    "organization_id": organization,
                    "start": start.isoformat(),
                    "end": (end + timedelta(days=1)).isoformat(),
                },
            )
            records = cursor.fetchall()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return
    finally:
        cursor.close()

    for r in records:
        with tempfile.NamedTemporaryFile() as tmp:
            user_name = r.user_name

            # Generate summary times
            data = staff_times.report(
                db,
                env,
                gotenberg,
                output=tmp.name,
                **{
                    k: v
                    for k, v in {
                        "add": add,
                        "organization": organization,
                        "start": start,
                        "end": end,
                        "member": user_name,
                    }.items()
                    if v is not None
                }
            )

            # Email to recipient
            email_address = action_cfg.force_recipient if action_cfg.force_recipient is not None else r.user_email
            print("    - Sending Times for {} to {}".format(r.user_name, email_address))

            email = email_manager.new()
            email.to.append(email_address)
            email.subject = subject
            email.template = action_cfg.email_template
            email.template_args = {
                "name": user_name,
                "from_name": action_cfg.from_name,
                "logo": "logo.png" if email_logo else None,
                "start": start.strftime("%d/%m/%Y"),
                "end": end.strftime("%d/%m/%Y"),
                "data": data,
            }
            if email_logo:
                email.embed.append(
                    emailclient.File(
                        email_logo, "logo.png", typeof=email.AttachType.IMAGE
                    )
                )

            email.attach.append(
                emailclient.File(
                    tmp.name, name=attachment_name, typeof=email.AttachType.APPLICATION
                )
            )
            email.send()
