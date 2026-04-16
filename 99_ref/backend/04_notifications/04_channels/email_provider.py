from __future__ import annotations

import email.utils
import logging

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .base import ChannelProvider, DeliveryResult

logger = logging.getLogger(__name__)


class EmailProvider(ChannelProvider):
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        from_email: str,
        from_name: str,
        use_tls: bool = False,
        start_tls: bool = True,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._from_name = from_name
        self._use_tls = use_tls
        self._start_tls = start_tls

    async def send(
        self,
        *,
        recipient: str,
        subject: str | None,
        body_html: str | None,
        body_text: str | None,
        body_short: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> DeliveryResult:
        # ── Build MIME message ──────────────────────────────────────────
        # Always send as single text/html when HTML is available.
        # multipart/alternative causes many webmail clients (yopmail, some
        # Outlook versions, temp-mail) to prefer the text/plain part over HTML.
        # This matches the behavior of Mailchimp, SendGrid, and Mautic which
        # send HTML-only for transactional emails.
        if body_html:
            msg = MIMEText(body_html, "html", "utf-8")
        else:
            msg = MIMEText(body_text or "", "plain", "utf-8")

        # ── Headers ─────────────────────────────────────────────────────
        _meta = metadata or {}
        msg["From"] = f"{self._from_name} <{self._from_email}>"
        msg["To"] = recipient
        msg["Subject"] = subject or ""
        msg["Message-ID"] = email.utils.make_msgid(
            domain=self._from_email.split("@")[-1] if "@" in self._from_email else "localhost",
        )
        msg["X-Mailer"] = "K-Control Notification Service"

        # Reply-To (defaults to from_email if not set in metadata)
        _reply_to = _meta.get("reply_to", self._from_email)
        if _reply_to:
            msg["Reply-To"] = _reply_to

        # Priority (critical notifications get high priority headers)
        _priority = _meta.get("priority")
        if _priority == "critical":
            msg["X-Priority"] = "1"
            msg["X-MSMail-Priority"] = "High"
            msg["Importance"] = "High"

        # RFC 8058 one-click unsubscribe
        _unsub_url = _meta.get("unsubscribe_url")
        if _unsub_url:
            msg["List-Unsubscribe"] = f"<{_unsub_url}>"
            msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

        # ── Send ────────────────────────────────────────────────────────
        try:
            response = await aiosmtplib.send(
                msg,
                hostname=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                use_tls=self._use_tls,
                start_tls=self._start_tls,
            )
            return DeliveryResult(
                success=True,
                provider_message_id=msg["Message-ID"],
                provider_response=str(response),
            )
        except Exception as exc:
            logger.error("Email send failed: %s", exc)
            return DeliveryResult(
                success=False,
                error_code="smtp_error",
                error_message=str(exc),
            )

    async def close(self) -> None:
        pass
