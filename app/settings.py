import os

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


"""""""""""""""""
Настройка дефолтного таймаута для async запросов с бэка.
"""""""""""""""""


timeout = httpx.Timeout(
    connect=5.0,
    read=30.0,
    write=10.0,
    pool=5.0
)


"""""""""""""""""
Настройка версии.
"""""""""""""""""
if os.path.exists('Version.txt'):
    with open('Version.txt') as version_file:
        STATIC_VERSION = version_file.readline().rstrip()
else:
    STATIC_VERSION = 'Версия не указана'


"""""""""""""""""""""""
Общие настройки системы.
"""""""""""""""""""""""


class Settings(BaseSettings):
    """ Настройки сервиса """

    # Настройка адреса переменной окружения .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_title: str = Field(
        default="Сервис лицензирования",
        description="Имя проекта",
    )

    app_description: str = Field(
        default="Сервис лицензирования",
        description="Описание проекта",
    )

    app_version: str = Field(
        default=STATIC_VERSION,
        description="Версия проекта",
    )

    debug: bool = Field(
        default=False,
        description="Режим отладки",
    )

    backend_host: str = Field(
        default="",
        description="Хост бэкенда монолита"
    )

    secret_key: str = Field(
        default="",
        description="Секретный ключ"
    )

    # Пути для отображения документации
    # http://127.0.0.1:5000/swagger либо http://127.0.0.1:5000/api/v1/swagger
    docs_url: str = Field(
        default="/swagger",
        description="Путь до SWAGGER",
    )
    # http://127.0.0.1:5000/redoc либо http://127.0.0.1:5000/api/v1/redoc
    redoc_url: str = Field(
        default="/redoc",
        description="Путь до REDOC",
    )

    # Пути к БД
    sqlite_url: str = Field(
        default="./licence.db",  # "sqlite+aiosqlite:///./licence.db",
        description="SQLite DB URL",
    )
    sqlite_url_alembic: str = Field(
        default="sqlite:///./licence.db",
        description="SQLite DB URL FOR ALEMBIC (SHOULD BE SYNC)",
    )

    # ROOT путь для отображения REST хвостов
    root_path: str = Field(
        default="/api/v1",
        description="ROOT путь для URL API",
    )

    # Часовой пояс приложения
    app_timezone: str = Field("UTC", description="Часовой пояс приложения")


# Инициализируем настройки
settings = Settings()
