from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from automessage import __version__
from automessage.auth.sessions import SESSION_COOKIE, get_user_for_token
from automessage.config import get_settings
from automessage.db import get_session
from automessage.models import AppSettings, ChannelAccount, User
from automessage.schemas import AppStateResponse

router = APIRouter(tags=["state"])


@router.get("/api/state", response_model=AppStateResponse)
async def get_app_state(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AppStateResponse:
    settings = get_settings()
    result = await session.execute(select(AppSettings).limit(1))
    app_settings = result.scalar_one_or_none()
    onboarded = bool(app_settings and app_settings.onboarded)

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

    token = request.cookies.get(SESSION_COOKIE)
    user = await get_user_for_token(session, token)

    count_result = await session.execute(select(func.count()).select_from(User))
    has_users = int(count_result.scalar_one()) > 0

    return AppStateResponse(
        onboarded=onboarded,
        channel_status=channel_status,
        version=__version__,
        authenticated=user is not None,
        default_user_mode=settings.default_user_mode,
        has_users=has_users,
    )
