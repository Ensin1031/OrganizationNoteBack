import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Time, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List, Optional

from app.db import Base

if TYPE_CHECKING:
    from app.db.models import User, Note


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
    start_date: Mapped[datetime.date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    start_time: Mapped[datetime.time] = mapped_column(
        Time,
        nullable=False,
    )
    end_date: Mapped[Optional[datetime.date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )
    end_time: Mapped[Optional[datetime.time]] = mapped_column(
        Time,
        nullable=True,
    )
    location: Mapped[str] = mapped_column(
        String,
        index=True,
        default="",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
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
