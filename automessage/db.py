from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from automessage.models import Base


@runtime_checkable
class Store(Protocol):
    """Persistence interface — SQLite now, Postgres later without touching business logic."""

    @property
    def engine(self) -> AsyncEngine: ...

    def session_factory(self) -> async_sessionmaker[AsyncSession]: ...

    @asynccontextmanager
    def session(self) -> AsyncIterator[AsyncSession]: ...

    async def create_all(self) -> None: ...

    async def dispose(self) -> None: ...


class SqliteStore:
    """SQLite-backed Store implementation using SQLAlchemy async + aiosqlite."""

    def __init__(self, database_url: str) -> None:
        self._engine = create_async_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_all(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        await self._engine.dispose()


_store: SqliteStore | None = None


def get_store() -> SqliteStore:
    if _store is None:
        raise RuntimeError("Store not initialized — call init_store() first")
    return _store


def init_store(database_url: str) -> SqliteStore:
    global _store
    _store = SqliteStore(database_url)
    return _store


async def get_session() -> AsyncIterator[AsyncSession]:
    store = get_store()
    session_maker = store.session_factory()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDepFactory = Callable[[], AsyncIterator[AsyncSession]]
