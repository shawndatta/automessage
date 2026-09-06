from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from automessage import __version__
from automessage.db import get_session
from automessage.models import AppSettings, ChannelAccount
from automessage.schemas import AppStateResponse

router = APIRouter(tags=["state"])


@router.get("/api/state", response_model=AppStateResponse)
async def get_app_state(session: AsyncSession = Depends(get_session)) -> AppStateResponse:
    result = await session.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()
    onboarded = bool(settings and settings.onboarded)

    channel_status: str | None = None
    ch = await session.execute(
        select(ChannelAccount).where(ChannelAccount.status == "active").limit(1)
    )
    account = ch.scalar_one_or_none()
    if account is not None:
        channel_status = account.status
    else:
        any_ch = await session.execute(select(ChannelAccount).limit(1))
        first = any_ch.scalar_one_or_none()
        channel_status = first.status if first else None

    return AppStateResponse(
        onboarded=onboarded,
        channel_status=channel_status,
        version=__version__,
    )
