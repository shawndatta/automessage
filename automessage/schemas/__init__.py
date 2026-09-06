from __future__ import annotations

from pydantic import BaseModel


class AppStateResponse(BaseModel):
    onboarded: bool
    channel_status: str | None = None
    version: str
