import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List

from app.db import Base

if TYPE_CHECKING:
    from app.db.models import User, Note

TIMESTAMP_1900 = -2208988800000


class Meeting(Base):
    """ Встреча пользователя """

    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="meetings",
    )
    title: Mapped[str] = mapped_column(
        String,
        index=True,
        default="",
    )
    description: Mapped[str] = mapped_column(
        String,
        index=True,
        default="",
    )
    meeting_at: Mapped[DateTime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    location: Mapped[str] = mapped_column(
        String,
        index=True,
        default="",
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
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
    )

    notes: Mapped[List["Note"]] = relationship(
        "Note",
        back_populates="meeting",
    )
