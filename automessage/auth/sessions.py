from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from automessage.config import Settings
from automessage.models import AuthSession, User

SESSION_COOKIE = "am_session"

DEFAULT_USER_EMAIL = "default@example.com"
DEFAULT_USER_NAME = "Default User"
DEFAULT_USER_PASSWORD = "automessage"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


async def create_session(
    session: AsyncSession,
    user: User,
    settings: Settings,
) -> AuthSession:
    token = new_session_token()
    row = AuthSession(
        id=token,
        user_id=user.id,
        expires_at=_utcnow() + timedelta(hours=settings.session_ttl_hours),
    )
    session.add(row)
    await session.flush()
    return row


async def get_user_for_token(session: AsyncSession, token: str | None) -> User | None:
    if not token:
        return None
    result = await session.execute(
        select(AuthSession)
        .where(AuthSession.id == token)
        .options(selectinload(AuthSession.user))
    )
    row = result.scalar_one_or_none()
    if row is None or row.revoked_at is not None:
        return None
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < _utcnow():
        return None
    return row.user


async def revoke_session(session: AsyncSession, token: str | None) -> None:
    if not token:
        return
    result = await session.execute(select(AuthSession).where(AuthSession.id == token))
    row = result.scalar_one_or_none()
    if row is not None and row.revoked_at is None:
        row.revoked_at = _utcnow()


async def ensure_default_user(session: AsyncSession) -> User:
    from automessage.auth.passwords import hash_password

    result = await session.execute(select(User).where(User.email == DEFAULT_USER_EMAIL))
    user = result.scalar_one_or_none()
    if user is not None:
        return user
    user = User(
        email=DEFAULT_USER_EMAIL,
        name=DEFAULT_USER_NAME,
        password_hash=hash_password(DEFAULT_USER_PASSWORD),
        is_default=True,
    )
    session.add(user)
    await session.flush()
    return user
