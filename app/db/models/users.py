import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Integer, String, Boolean, select, exists, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db.database import SyncSessionLocal
from app.utils.gender_enum import GenderType

if TYPE_CHECKING:
    from app.db.models import Note, Meeting

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
        default=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=datetime.datetime.now(tz=datetime.timezone.utc),
        onupdate=datetime.datetime.now(tz=datetime.timezone.utc),
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

    notes: Mapped[List["Note"]] = relationship(
        "Note",
        back_populates="user",
    )
    meetings: Mapped[List["Meeting"]] = relationship(
        "Meeting",
        back_populates="user",
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
