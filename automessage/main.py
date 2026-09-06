from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from automessage import __version__
from automessage.api import auth_router, state_router
from automessage.auth.sessions import SESSION_COOKIE, ensure_default_user, get_user_for_token
from automessage.config import Settings, get_settings
from automessage.crypto import CredentialCrypto
from automessage.db import get_store, init_store
from automessage.models import AppSettings

_PUBLIC_API_PREFIXES = (
    "/api/auth/signup",
    "/api/auth/login",
    "/api/auth/logout",
    "/api/auth/me",
    "/api/auth/default-session",
    "/api/state",
)


def _static_dir() -> Path | None:
    """Prefer a local frontend build, then packaged static files."""
    repo_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if repo_dist.is_dir() and (repo_dist / "index.html").exists():
        return repo_dist
    packaged = Path(__file__).resolve().parent / "static"
    if packaged.is_dir() and (packaged / "index.html").exists():
        return packaged
    return None


def _is_public_api(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix + "/") for prefix in _PUBLIC_API_PREFIXES)


class AuthGateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/") and not _is_public_api(path):
            token = request.cookies.get(SESSION_COOKIE)
            store = get_store()
            async with store.session_factory()() as session:
                user = await get_user_for_token(session, token)
            if user is None:
                return JSONResponse({"detail": "Authentication required"}, status_code=401)
        return await call_next(request)


async def _ensure_app_settings_row() -> None:
    store = get_store()
    async with store.session() as session:
        result = await session.execute(select(AppSettings).limit(1))
        row = result.scalar_one_or_none()
        if row is None:
            settings = get_settings()
            crypto = CredentialCrypto.from_path(settings.key_path)
            session.add(
                AppSettings(
                    onboarded=False,
                    llm=None,
                    encryption_check=crypto.encrypt("ok"),
                )
            )


async def _bootstrap_default_user(settings: Settings) -> None:
    if not settings.default_user_mode:
        return
    store = get_store()
    async with store.session() as session:
        await ensure_default_user(session)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    settings.ensure_dirs()
    store = init_store(settings.database_url)
    await store.create_all()
    await _ensure_app_settings_row()
    await _bootstrap_default_user(settings)
    CredentialCrypto.from_path(settings.key_path)
    yield
    await store.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="AutoMessage",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.add_middleware(AuthGateMiddleware)
    app.include_router(auth_router)
    app.include_router(state_router)

    static = _static_dir()
    if static is not None:
        assets = static / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(static / "index.html")

        @app.get("/{full_path:path}", response_model=None)
        async def spa_fallback(full_path: str) -> FileResponse | JSONResponse:
            if (
                full_path.startswith("api/")
                or full_path.startswith("docs")
                or full_path.startswith("openapi")
            ):
                return JSONResponse({"detail": "Not Found"}, status_code=404)
            candidate = static / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(static / "index.html")

    return app
