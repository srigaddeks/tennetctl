from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._transport import Transport


class Notify:
    """Transactional notify.send wrapper."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def send(
        self,
        *,
        template_key: str,
        recipient_user_id: str,
        variables: dict[str, Any] | None = None,
        channel: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {
            "template_key": template_key,
            "recipient_user_id": recipient_user_id,
        }
        if variables is not None:
            body["variables"] = variables
        if channel is not None:
            body["channel"] = channel

        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return await self._t.request(
            "POST",
            "/v1/notify/send",
            json=body,
            headers=headers,
        )
