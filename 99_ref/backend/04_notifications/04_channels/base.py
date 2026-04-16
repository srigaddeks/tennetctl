from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    success: bool
    provider_message_id: str | None = None
    provider_response: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class ChannelProvider(abc.ABC):
    @abc.abstractmethod
    async def send(
        self,
        *,
        recipient: str,
        subject: str | None,
        body_html: str | None,
        body_text: str | None,
        body_short: str | None,
        metadata: dict[str, str] | None = None,
    ) -> DeliveryResult: ...

    @abc.abstractmethod
    async def close(self) -> None: ...
