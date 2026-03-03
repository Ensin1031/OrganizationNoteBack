import datetime
from typing import Optional

from fastapi import Depends, APIRouter, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db import get_db
from app.db.models import Note
from app.schemas import PaginatedResponse, NoteRead, NoteCreate
from app.schemas.notes import NoteSync
from app.utils.note_priority_enum import NotePriority
from app.utils.request_with_token_data import get_current_user_id

router = APIRouter(
    prefix='/notes',
    tags=["Заметки пользователя"],
)


@router.get("/", response_model=PaginatedResponse[NoteRead])
async def get_notes(
    parent_note_id: Optional[int] = Query(None),
    meeting_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """ Получение данных по списку записей модели """

    base_stmt = select(Note).where(Note.user_id == current_user_id)

    if parent_note_id is not None:
        base_stmt = base_stmt.where(Note.parent_note_id == parent_note_id)

    if meeting_id is not None:
        base_stmt = base_stmt.where(Note.meeting_id == meeting_id)

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
    path="/sync/",
    response_model=NoteRead,
    status_code=status.HTTP_200_OK,
)
async def sync_note(
    note: NoteSync,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):

    if current_user_id != note.external_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    try:
        return await Note.get_sync_note(db=db, note_data=note)
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


@router.post(
    path="/",
    response_model=NoteRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    note: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    if current_user_id != note.external_user_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    try:
        priority = getattr(NotePriority, note.priority)
    except Exception:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Некорректное значение приоритета",
        )

    s_fields = dict()

    if note.created_at is not None:
        try:
            created_at = datetime.datetime.fromtimestamp(note.created_at / 1000.0, tz=datetime.timezone.utc)
        except Exception as _e:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=str(_e),
            )

        s_fields["created_at"] = created_at
    else:
        s_fields["created_at"] = datetime.datetime.now(tz=datetime.timezone.utc)

    if note.updated_at is not None:
        try:
            updated_at = datetime.datetime.fromtimestamp(note.updated_at / 1000.0, tz=datetime.timezone.utc)
        except Exception as _e:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=str(_e),
            )

        s_fields["updated_at"] = updated_at
    else:
        s_fields["updated_at"] = datetime.datetime.now(tz=datetime.timezone.utc)

    db_item = Note(
        user_id=note.external_user_id,
        parent_note_id=note.external_parent_note_id,
        meeting_id=note.external_meeting_id,
        title=note.title,
        content=note.content,
        priority=priority,
        **s_fields,
    )

    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)

    return db_item


@router.delete(
    path="/{note_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Удаление записи',
)
async def delete_note(
    note_id: int,
    archive: bool,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):

    base_stmt = select(Note).where(
        Note.id == note_id,
    ).limit(1)

    result = await db.execute(base_stmt)
    note: Optional[Note] = result.scalar_one_or_none()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    if current_user_id != note.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    if archive:
        note.is_active = False
    else:
        note.is_deleted = True

    db.add(note)

    await db.commit()
