import datetime
from typing import Optional

from fastapi import Depends, APIRouter, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db import get_db
from app.db.models import Meeting
from app.db.models.meetings import offset_to_time
from app.schemas import PaginatedResponse, MeetingRead, MeetingCreate
from app.utils.request_with_token_data import get_current_user_id

router = APIRouter(
    prefix='/meetings',
    tags=["Встречи пользователя"],
)


@router.get("/", response_model=PaginatedResponse[MeetingRead])
async def get_meetings(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """ Получение данных по списку записей модели """

    base_stmt = select(Meeting).where(Meeting.user_id == current_user_id)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    count = await db.scalar(count_stmt)

    stmt = (
        base_stmt
        .offset((page - 1) * size)
        .limit(size)
    )

    result = await db.execute(stmt)
    results = result.scalars().all()

    return {
        "results": results,
        "page": page,
        "page_size": size,
        "count": count,
    }


@router.post(
    path="/",
    response_model=MeetingRead,
    status_code=status.HTTP_200_OK,
)
async def create_meeting(
    meeting: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    if current_user_id != meeting.external_user_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

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
        base_stmt = select(Meeting).where(
            Meeting.id == meeting.external_id,
            Meeting.user_id == meeting.external_user_id,
        ).limit(1)

        result = await db.execute(base_stmt)
        db_item: Optional[Meeting] = result.scalar_one_or_none()

    if db_item is None:
        db_item = Meeting(
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

        if (db_item_updated_aware is not None and db_item_updated_aware < updated_at) or db_item_updated_aware is None:
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

    return db_item


@router.delete(
    path="/{meeting_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Удаление записи',
)
async def delete_meeting(
    meeting_id: int,
    archive: bool,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):

    base_stmt = select(Meeting).where(
        Meeting.id == meeting_id,
    ).limit(1)

    result = await db.execute(base_stmt)
    meeting: Optional[Meeting] = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    if current_user_id != meeting.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    if archive:
        meeting.is_active = False
        db.add(meeting)
    else:
        await db.delete(meeting)

    await db.commit()
