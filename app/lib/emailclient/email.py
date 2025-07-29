from __future__ import annotations

import sys

import jinja2 as jinja2
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText
from mjml import mjml2html
from smtplib import SMTP
from typing import List, Optional, Dict, TYPE_CHECKING

from .attachment import AttachType, File

if TYPE_CHECKING:
    from .manager import Manager


class Email(object):
    """
    Specifies an Email message
    """

    AttachType = AttachType

    def __init__(self, manager: Manager):
        self._manager: Manager = manager
        self.to: List[str] = []
        self.subject: str = ""
        self.template: Optional[str] = None
        self.template_args: Dict[str, str] = {}
        self.attach: List[File] = []
        self.embed: List[File] = []

    def send(self) -> None:
        """
        Send the email
        """

        msg = MIMEMultipart('mixed')
        msg['Subject'] = self.subject
        msg['From'] = self._manager.from_full
        msg['To'] = ", ".join(self.to)
        msg.preamble = 'This is a multi-part message in MIME format.'

        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)

        # Try to attach plain text template
        if self.template is not None:
            try:
                msg_alternative.attach(
                    MIMEText(
                        self._manager.jinja.get_template("{}.txt".format(self.template)).render(**self.template_args),
                        'plain')
                )
            except jinja2.TemplateNotFound:
                # None found
                pass

            # Try to attach html template
            msg_html = MIMEMultipart('related')
            msg_html.attach(
                MIMEText(
                    mjml2html(self._manager.jinja.get_template("{}.mjml".format(self.template)).render(
                        **self.template_args)),
                    'html', 'UTF-8')
            )

            # Attach embedded files
            data: MIMENonMultipart
            for a in self.embed:
                try:
                    with open(a.path, 'rb') as f:
                        if a.typeof == AttachType.IMAGE:
                            data = MIMEImage(f.read())
                        elif a.typeof == AttachType.AUDIO:
                            data = MIMEAudio(f.read())
                        else:
                            data = MIMEApplication(f.read())

                        data.add_header("Content-ID", "<{}>".format(a.name))

                    msg_html.attach(data)
                except IOError:
                    # Failed Embed
                    pass

            msg_alternative.attach(msg_html)

        # Attach files
        for a in self.attach:
            with open(a.path, 'rb') as f:
                if a.typeof == AttachType.IMAGE:
                    data = MIMEImage(f.read())
                elif a.typeof == AttachType.AUDIO:
                    data = MIMEAudio(f.read())
                else:
                    data = MIMEApplication(f.read())

                data.add_header("Content-ID", "<{}>".format(a.name))
                data.add_header('Content-Disposition', 'attachment; filename="{}"'.format(a.name))
                msg.attach(data)

        # Send Email
        s = SMTP(self._manager.host, self._manager.port)
        s.login(self._manager.username, self._manager.password)
        s.sendmail(self._manager.from_email, msg['To'], msg.as_string())
        s.quit()
