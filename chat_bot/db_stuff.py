import json
from typing import Callable, Awaitable, Dict, Any

from aiogram.fsm.middleware import BaseMiddleware
from aiogram.types.base import TelegramObject
from sqlalchemy import String, Integer, DateTime, func, Column, Text
from sqlalchemy.ext.asyncio import (async_sessionmaker, create_async_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


engine = create_async_engine('sqlite+aiosqlite:///db.sqlite3', echo=True)
session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def on_startup():
    await create_db()


class DatabaseSession(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with self.session_pool() as session:
            data['session'] = session
            return await handler(event, data)


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    last_session: Mapped[DateTime] = mapped_column(DateTime, default=func.now())


class User(Base):
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(65), default="")
    replies_count: Mapped[int] = mapped_column(Integer, default=5)
    context = Column(Text, default="[]")
    
    def get_context(self):
        return json.loads(self.context)
    
    def set_context(self, context_list):
        self.context = json.dumps(context_list)
    
    def __repr__(self) -> str:
        return (f"User(id={self.id!r}, role={repr(self.role)}, "
                f"replies_count={self.replies_count}")
