from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path

from app.db import engine, Base
from app.routes import router
from app.settings import settings

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(root_app: FastAPI):
    root_app.state.engine = engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()

app = FastAPI(
    lifespan=lifespan,
    title=settings.app_title,
    description=settings.app_description,
    debug=settings.debug,
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    root_path=settings.root_path,
)

app.include_router(router)
