import datetime

from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db import Base
from app.utils.note_priority_enum import NotePriority

if TYPE_CHECKING:
    from app.db.models import User, Meeting

TIMESTAMP_1900 = -2208988800000


class Note(Base):
    """ Заметка пользователя """

    __tablename__ = "notes"

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
        back_populates="notes",
    )
    parent_note_id: Mapped[int | None] = mapped_column(
        ForeignKey("notes.id"),
        nullable=True,
    )
    parent_note: Mapped["Note | None"] = relationship(
        "Note",
        remote_side=[id],
        back_populates="children_notes",
    )
    children_notes: Mapped[list["Note"]] = relationship(
        "Note",
        back_populates="parent_note",
        cascade="all, delete-orphan",
    )
    meeting_id: Mapped[int | None] = mapped_column(
        ForeignKey("meetings.id"),
        nullable=True,
    )
    meeting: Mapped["Meeting | None"] = relationship(
        "Meeting",
        back_populates="notes",
    )
    title: Mapped[str] = mapped_column(
        String,
        index=True,
        default="",
    )
    content: Mapped[str] = mapped_column(
        String,
        index=True,
        default="",
    )
    priority: Mapped[NotePriority] = mapped_column(
        Enum(NotePriority),
        nullable=False,
        default=NotePriority.HIGH,
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
