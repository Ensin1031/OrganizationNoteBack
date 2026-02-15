from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    "sqlite+aiosqlite:///" + settings.sqlite_url,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

# В некоторых местах нужна синхронная бд, т. к. функция/метод не могут быть асинхронными
sync_engine = create_engine(
    settings.sqlite_url_alembic,
    echo=False
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine
)
