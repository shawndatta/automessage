from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

Capability = Literal[
    "text",
    "media",
    "quick_replies",
    "typing",
    "comment_to_dm",
    "messaging_window",
]


class InboundEvent(BaseModel):
    channel: str
    channel_account_id: int
    type: Literal["message_received", "postback_clicked", "comment_created"]
    external_contact_id: str
    external_conversation_id: str
    text: str | None = None
    payload: dict = Field(default_factory=dict)
    provider_message_id: str | None = None
    dedupe_key: str | None = None


class OutboundAction(BaseModel):
    type: Literal["send_text", "send_media", "send_quick_replies", "typing_on", "mark_seen"]
    external_conversation_id: str
    text: str | None = None
    media_url: str | None = None
    buttons: list[dict] = Field(default_factory=list)


class DeliveryResult(BaseModel):
    ok: bool
    provider_message_id: str | None = None
    error: str | None = None
    unsubscribe: bool = False


@runtime_checkable
class ChannelAdapter(Protocol):
    channel: str

    def capabilities(self) -> set[Capability]: ...

    async def validate_credentials(self, creds: dict) -> dict: ...

    async def start(self, account: object) -> None: ...

    async def stop(self, account: object) -> None: ...

    async def send(self, account: object, action: OutboundAction) -> DeliveryResult: ...
