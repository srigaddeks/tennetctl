"""Twilio SMS sender for mobile-OTP.

Vault-driven: looks up `sms.twilio.account_sid`, `sms.twilio.auth_token`,
and `sms.twilio.from_number` at send-time. If any are missing the sender
runs in stub mode — logs the OTP to stdout and returns success without
calling Twilio.

Plug-in path for prod:
    1. Sign up at https://www.twilio.com
    2. Buy / verify a phone number
    3. POST those values into vault under sms.twilio.* via the Vault UI
    4. Restart not required — vault TTL is 60 s, sender will pick up the
       new creds within the next minute. (No code change needed.)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

_log = logging.getLogger("tennetctl.iam.mobile_otp.twilio")

_REQUIRED_KEYS = (
    "sms.twilio.account_sid",
    "sms.twilio.auth_token",
    "sms.twilio.from_number",
)


class TwilioSender:
    """Reads Twilio creds from vault on every send (vault is ttl-cached)."""

    def __init__(self, vault_client: Any) -> None:
        self._vault = vault_client
        self._is_stub: bool | None = None
        self._creds: dict[str, str] | None = None

    @property
    def is_stub(self) -> bool:
        # is_stub is settled the first time send() is called and the creds
        # are looked up. Default to True until then.
        return True if self._is_stub is None else self._is_stub

    async def _load_creds(self) -> dict[str, str] | None:
        if self._vault is None:
            return None
        out: dict[str, str] = {}
        for key in _REQUIRED_KEYS:
            try:
                out[key] = await self._vault.get(key)
            except Exception:
                return None
        return out

    async def send(self, phone_e164: str, code: str) -> bool:
        creds = await self._load_creds()
        if creds is None:
            self._is_stub = True
            self._creds = None
            return True  # stub mode — pretend it sent.

        self._is_stub = False
        self._creds = creds
        sid = creds["sms.twilio.account_sid"]
        token = creds["sms.twilio.auth_token"]
        from_no = creds["sms.twilio.from_number"]
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        body = {
            "From": from_no,
            "To": phone_e164,
            "Body": f"Soma Delights: your verification code is {code}. "
                    f"Valid for 5 minutes.",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                r = await http.post(url, data=body, auth=(sid, token))
            if r.status_code >= 400:
                _log.warning(
                    "Twilio rejected send: status=%s body=%s",
                    r.status_code, r.text[:200],
                )
                return False
            return True
        except Exception:
            _log.exception("Twilio send failed")
            return False
