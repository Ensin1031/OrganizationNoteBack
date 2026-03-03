import datetime

from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey, Boolean, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from starlette import status
from starlette.exceptions import HTTPException

from app.db import Base
from app.schemas.notes import NoteSync
from app.utils.note_priority_enum import NotePriority

if TYPE_CHECKING:
    from app.db.models import User, Meeting


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
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )

    @classmethod
    async def get_sync_note(cls, db: AsyncSession, note_data: NoteSync) -> 'Note':

        try:
            priority = getattr(NotePriority, note_data.priority)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Некорректное значение приоритета",
            )

        dt_now = datetime.datetime.now(tz=datetime.timezone.utc)

        if note_data.created_at is not None:
            try:
                created_at = datetime.datetime.fromtimestamp(note_data.created_at / 1000.0, tz=datetime.timezone.utc)
            except Exception as _e:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=f'created_at: {_e}',
                )
        else:
            created_at = dt_now

        if note_data.updated_at is not None:
            try:
                updated_at = datetime.datetime.fromtimestamp(note_data.updated_at / 1000.0, tz=datetime.timezone.utc)
            except Exception as _e:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=f'updated_at: {_e}',
                )
        else:
            updated_at = dt_now

        db_item = None
        if note_data.external_id:
            base_stmt = select(cls).where(
                cls.id == note_data.external_id,
                cls.user_id == note_data.external_user_id,
            ).limit(1)

            result = await db.execute(base_stmt)
            db_item: Optional[Note] = result.scalar_one_or_none()

        if db_item is None:
            db_item = cls(
                user_id=note_data.external_user_id,
                parent_note_id=note_data.external_parent_note_id,
                meeting_id=note_data.external_meeting_id,
                title=note_data.title,
                content=note_data.content,
                priority=priority,
                created_at=created_at,
                updated_at=dt_now,
                is_active=note_data.is_active,
            )
            db.add(db_item)
            await db.commit()
            await db.refresh(db_item)

            db_item.ka_id = note_data.id
            db_item.ka_user_id = note_data.user_id
            db_item.ka_parent_note_id = note_data.parent_note_id
            db_item.ka_meeting_id = note_data.meeting_id

            return db_item

        if db_item.updated_at and db_item.updated_at.tzinfo is None:
            db_item_updated_aware = db_item.updated_at.replace(tzinfo=datetime.timezone.utc)
        else:
            db_item_updated_aware = db_item.updated_at

        if (db_item_updated_aware is not None and db_item_updated_aware < updated_at) or db_item_updated_aware is None:
            db_item.parent_note_id = note_data.external_parent_note_id
            db_item.meeting_id = note_data.external_meeting_id
            db_item.title = note_data.title
            db_item.content = note_data.content
            db_item.priority = priority
            db_item.is_active = note_data.is_active
            db_item.created_at = created_at
            db_item.updated_at = updated_at

        if db_item.is_active != note_data.is_active:
            db_item.is_active = note_data.is_active
            db_item.updated_at = dt_now

        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)

        db_item.ka_id = note_data.id
        db_item.ka_user_id = note_data.user_id
        db_item.ka_parent_note_id = note_data.parent_note_id
        db_item.ka_meeting_id = note_data.meeting_id

        return db_item
