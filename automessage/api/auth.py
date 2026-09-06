from __future__ import annotations

import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from automessage.auth.deps import get_optional_user
from automessage.auth.passwords import hash_password, verify_password
from automessage.auth.sessions import (
    DEFAULT_USER_EMAIL,
    SESSION_COOKIE,
    create_session,
    ensure_default_user,
    revoke_session,
)
from automessage.config import Settings, get_settings
from automessage.db import get_session
from automessage.models import User
from automessage.schemas import (
    AuthMeResponse,
    AuthOkResponse,
    LoginRequest,
    SignupRequest,
    UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Simple in-process rate limit: email -> list of attempt timestamps
_login_attempts: dict[str, list[float]] = defaultdict(list)
_MAX_ATTEMPTS = 10
_WINDOW_SECONDS = 300


def _check_login_rate(email: str) -> None:
    now = time.time()
    bucket = [t for t in _login_attempts[email.lower()] if now - t < _WINDOW_SECONDS]
    _login_attempts[email.lower()] = bucket
    if len(bucket) >= _MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in a few minutes.",
        )


def _record_login_attempt(email: str) -> None:
    _login_attempts[email.lower()].append(time.time())


def _set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # local HTTP by default; enable when terminating TLS
        max_age=settings.session_ttl_hours * 3600,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE, path="/")


@router.get("/me", response_model=AuthMeResponse)
async def auth_me(
    user: User | None = Depends(get_optional_user),
    settings: Settings = Depends(get_settings),
) -> AuthMeResponse:
    return AuthMeResponse(
        authenticated=user is not None,
        user=UserOut.model_validate(user) if user else None,
        default_user_mode=settings.default_user_mode,
    )


@router.post("/signup", response_model=AuthOkResponse)
async def signup(
    body: SignupRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuthOkResponse:
    email = str(body.email).strip().lower()
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=email,
        name=body.name.strip(),
        password_hash=hash_password(body.password),
        is_default=False,
    )
    session.add(user)
    await session.flush()
    auth_session = await create_session(session, user, settings)
    _set_session_cookie(response, auth_session.id, settings)
    return AuthOkResponse(user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthOkResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuthOkResponse:
    email = str(body.email).strip().lower()
    _check_login_rate(email)

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        _record_login_attempt(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    auth_session = await create_session(session, user, settings)
    _set_session_cookie(response, auth_session.id, settings)
    return AuthOkResponse(user=UserOut.model_validate(user))


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    token = request.cookies.get(SESSION_COOKIE)
    await revoke_session(session, token)
    _clear_session_cookie(response)
    return {"ok": True}


@router.post("/default-session", response_model=AuthOkResponse)
async def default_session(
    response: Response,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuthOkResponse:
    """Issue a session for the seeded default user. Only when started with `start default`."""
    if not settings.default_user_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Default user mode is not enabled. Start with: automessage start default",
        )
    user = await ensure_default_user(session)
    auth_session = await create_session(session, user, settings)
    _set_session_cookie(response, auth_session.id, settings)
    return AuthOkResponse(user=UserOut.model_validate(user))


async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(User))
    return int(result.scalar_one())
