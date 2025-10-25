from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.ext.asyncio.session import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///./triggerflow_canvas.db"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine) as session:
        yield session
