import datetime
from typing import Optional

from fastapi import Depends, APIRouter, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db import get_db
from app.db.models import Meeting, Note
from app.schemas import PaginatedResponse, MeetingRead
from app.schemas.meetings import SyncMeeting, SyncMeetingResponse
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
    response_model=SyncMeetingResponse,
    status_code=status.HTTP_200_OK,
)
async def create_meeting(
    sync_meeting_data: SyncMeeting,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):

    meeting = sync_meeting_data.meeting

    if current_user_id != meeting.external_user_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    try:
        return {
            'meeting': await Meeting.get_sync_meeting(db=db, meeting=sync_meeting_data.meeting),
            'notes': [
                await Note.get_sync_note(db=db, note_data=note) for note in sync_meeting_data.notes
            ] if sync_meeting_data.notes else [],
        }
    except HTTPException as _e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_e.detail,
        )
    except Exception as _e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(_e),
        )


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
    else:
        meeting.is_deleted = True

    db.add(meeting)

    await db.commit()
