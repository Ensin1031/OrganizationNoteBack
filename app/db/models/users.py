import datetime

from sqlalchemy import Integer, String, Boolean, select, exists, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.db.database import SyncSessionLocal
from app.utils.gender_enum import GenderType

TIMESTAMP_1900 = -2208988800000


class User(Base):
    """ Пользователь """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String,
        index=True,
        default="",
    )
    login: Mapped[str] = mapped_column(
        String,
        index=True,
        unique=True,
    )
    email: Mapped[str] = mapped_column(
        String,
        index=True,
        unique=True,
    )
    password: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    salt: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.datetime.now(),
        doc='Дата и время создания записи',
        comment='Дата и время создания записи',
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.datetime.now(),
        onupdate=datetime.datetime.now(),
        doc='Дата и время последнего обновления записи',
        comment='Дата и время последнего обновления записи',
    )
    birthdate_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )
    gender: Mapped[GenderType] = mapped_column(
        Enum(GenderType),
        nullable=False,
        default=GenderType.UNSET,
    )
    verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )

    @classmethod
    def has_user_by_id(cls, user_id: int) -> bool:
        has_user = False
        if not user_id:
            has_user = False
        else:
            with SyncSessionLocal() as db:
                token_user_stmt = select(
                    exists(User).where(
                        User.id == user_id
                    )
                )
                has_user = db.execute(token_user_stmt).scalar()
        return has_user
