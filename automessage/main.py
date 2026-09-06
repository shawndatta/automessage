from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from automessage import __version__
from automessage.api import state_router
from automessage.config import Settings, get_settings
from automessage.crypto import CredentialCrypto
from automessage.db import get_store, init_store
from automessage.models import AppSettings


def _static_dir() -> Path | None:
    """Prefer a local frontend build, then packaged static files."""
    repo_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if repo_dist.is_dir() and (repo_dist / "index.html").exists():
        return repo_dist
    packaged = Path(__file__).resolve().parent / "static"
    if packaged.is_dir() and (packaged / "index.html").exists():
        return packaged
    return None


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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    settings.ensure_dirs()
    store = init_store(settings.database_url)
    await store.create_all()
    await _ensure_app_settings_row()
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
            if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
                return JSONResponse({"detail": "Not Found"}, status_code=404)
            candidate = static / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(static / "index.html")

    return app
