import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Time, Date, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List, Optional

from starlette import status
from starlette.exceptions import HTTPException

from app.db import Base
from app.schemas.meetings import MeetingCreate

if TYPE_CHECKING:
    from app.db.models import User, Note


def offset_to_time(offset: int) -> datetime.time:
    """
    Преобразует смещение от полуночи в миллисекундах в объект time.
    Смещение должно быть в пределах 0..86399999 мс (24 часа - 1 мс).
    """
    # Переводим в секунды и ограничиваем сутками (86400 секунд)
    total_seconds = (offset // 1000) % (24 * 3600)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return datetime.time(hours, minutes, seconds)


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
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )

    notes: Mapped[List["Note"]] = relationship(
        "Note",
        back_populates="meeting",
    )

    @classmethod
    async def get_sync_meeting(cls, db: AsyncSession, meeting: MeetingCreate) -> 'Meeting':

        dt_now = datetime.datetime.now(tz=datetime.timezone.utc)

        if meeting.created_at is not None:
            try:
                created_at = datetime.datetime.fromtimestamp(meeting.created_at / 1000.0, tz=datetime.timezone.utc)
            except Exception as _e:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=str(_e),
                )
        else:
            created_at = dt_now

        if meeting.updated_at is not None:
            try:
                updated_at = datetime.datetime.fromtimestamp(meeting.updated_at / 1000.0, tz=datetime.timezone.utc)
            except Exception as _e:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=str(_e),
                )
        else:
            updated_at = dt_now

        try:
            start_date = datetime.datetime.fromtimestamp(meeting.start_date / 1000.0, tz=datetime.timezone.utc).date()
        except Exception:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Некорректное значение даты начала",
            )

        try:
            end_date = datetime.datetime.fromtimestamp(meeting.end_date / 1000.0, tz=datetime.timezone.utc).date()
        except Exception:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Некорректное значение даты окончания",
            )

        try:
            start_time = offset_to_time(offset=meeting.start_time)
        except Exception:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Некорректное значение времени начала",
            )

        try:
            end_time = offset_to_time(offset=meeting.end_time)
        except Exception:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Некорректное значение времени окончания",
            )

        # валидация
        if start_date > end_date:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Окончание (по дате) должно быть позже начала",
            )
        if start_time >= end_time:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Окончание (по времени) должно быть позже начала",
            )

        db_item = None
        if meeting.external_id is not None:
            base_stmt = select(cls).where(
                cls.id == meeting.external_id,
                cls.user_id == meeting.external_user_id,
            ).limit(1)

            result = await db.execute(base_stmt)
            db_item: Optional[Meeting] = result.scalar_one_or_none()

        if db_item is None:
            db_item = cls(
                user_id=meeting.external_user_id,
                title=meeting.title or '',
                description=meeting.description or '',
                location=meeting.location or '',
                is_active=meeting.is_active,
                created_at=created_at,
                updated_at=updated_at,
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
            )
        else:
            if db_item.updated_at and db_item.updated_at.tzinfo is None:
                db_item_updated_aware = db_item.updated_at.replace(tzinfo=datetime.timezone.utc)
            else:
                db_item_updated_aware = db_item.updated_at

            if (
                db_item_updated_aware is not None and db_item_updated_aware < updated_at
            ) or db_item_updated_aware is None:
                db_item.updated_at = updated_at
                db_item.created_at = created_at
                db_item.title = meeting.title or ''
                db_item.description = meeting.description or ''
                db_item.location = meeting.location or ''
                db_item.start_date = start_date
                db_item.end_date = end_date
                db_item.start_time = start_time
                db_item.end_time = end_time

            if db_item.is_active != meeting.is_active:
                db_item.is_active = meeting.is_active
                db_item.updated_at = dt_now

        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)

        db_item.ka_id = meeting.id
        db_item.ka_user_id = meeting.user_id

        return db_item
