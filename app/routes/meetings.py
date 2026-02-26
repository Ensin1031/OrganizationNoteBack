import datetime

from fastapi import Depends, APIRouter, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db import get_db
from app.db.models import Meeting
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
    status_code=status.HTTP_201_CREATED,
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

    s_fields = dict()

    if meeting.created_at is not None:
        try:
            created_at = datetime.datetime.fromtimestamp(meeting.created_at / 1000.0, tz=datetime.timezone.utc)
        except Exception as _e:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=str(_e),
            )

        s_fields["created_at"] = created_at
    else:
        s_fields["created_at"] = datetime.datetime.now(tz=datetime.timezone.utc)

    if meeting.updated_at is not None:
        try:
            updated_at = datetime.datetime.fromtimestamp(meeting.updated_at / 1000.0, tz=datetime.timezone.utc)
        except Exception as _e:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=str(_e),
            )

        s_fields["updated_at"] = updated_at
    else:
        s_fields["updated_at"] = datetime.datetime.now(tz=datetime.timezone.utc)

    if meeting.meeting_at is not None:
        try:
            meeting_at = datetime.datetime.fromtimestamp(meeting.meeting_at / 1000.0, tz=datetime.timezone.utc)
        except Exception as _e:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=str(_e),
            )
    else:
        meeting_at = None

    s_fields["meeting_at"] = meeting_at

    db_item = Meeting(
        user_id=meeting.external_user_id,
        title=meeting.title,
        description=meeting.description,
        location=meeting.location or '',
        **s_fields,
    )

    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)

    return db_item
