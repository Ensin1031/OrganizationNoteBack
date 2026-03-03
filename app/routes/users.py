import datetime
from typing import Optional

from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy import select, func, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db import get_db
from app.db.models import Meeting, Note
from app.db.models.users import User, TIMESTAMP_1900
from app.schemas import UserRead, UserUpdate
from app.schemas.meetings import SyncUserData, SyncUserDataResponse
from app.utils.gender_enum import GenderType
from app.utils.password_hasher import PasswordHasher
from app.utils.request_with_token_data import get_current_user_id

router = APIRouter(
    prefix='/users',
    tags=["Пользователи"],
)


@router.post("/{user_id}/sync-data/", response_model=SyncUserDataResponse)
async def sync_user_data(
    user_id: int,
    sync_data: SyncUserData,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    if current_user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    try:
        local_notes = [
            await Note.get_sync_note(db=db, note_data=note) for note in sync_data.notes
        ] if sync_data.notes else []
        local_notes_ids = [n.id for n in local_notes]
        notes_stmt = select(Note).where(
            Note.user_id == current_user_id,
            Note.is_deleted == False,  # noqa
            Note.parent_note_id == None,  # noqa
            Note.meeting_id == None,  # noqa
            ~Note.id.in_(local_notes_ids),
        )
        notes_result = await db.execute(notes_stmt)
        notes_results = notes_result.scalars().all()

        local_meetings = [
            {
                'meeting': await Meeting.get_sync_meeting(db=db, meeting=meeting_data.meeting),
                'notes': [
                    await Note.get_sync_note(db=db, note_data=note) for note in meeting_data.notes
                ],
            } for meeting_data in sync_data.meetings
        ]
        meetings_stmt = select(Meeting).where(
            Meeting.user_id == current_user_id,
            Meeting.is_deleted == False,  # noqa
        )
        meetings_result = await db.execute(meetings_stmt)
        meetings_results_qs = meetings_result.scalars().all()
        meetings_results = []
        for _meeting in meetings_results_qs:
            row = next((r for r in local_meetings if r.get('meeting').id == _meeting.id), Note)
            stmt = select(Note).where(
                Note.user_id == current_user_id,
                Note.is_deleted == False,  # noqa
                Note.meeting_id == _meeting.id,
            )
            result = await db.execute(stmt)
            results = result.scalars().all()
            if row is None:
                meetings_results.append({
                    'meeting': _meeting,
                    'notes': list(results)
                })
            else:
                for note_base in list(results):
                    if note_base.id not in [r.id for r in row['notes']]:
                        row['notes'] = [*row['notes'], note_base]

        return {
            'meetings': [*local_meetings, *meetings_results],
            'notes': [*local_notes, *notes_results],
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


@router.patch("/{user_id}/", response_model=UserRead)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Обновление записи модели
    По данному хвосту смена данных пользователя доступна ТОЛЬКО самому себе
    """
    if current_user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    result = await db.execute(
        select(User).where(
            User.id == user_id)
    )
    db_item: Optional[User] = result.scalar_one_or_none()

    if not db_item:
        # Этот вариант скорее невозможен, прописываю на всякий случай
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.name:
        if user.name.strip() == db_item.name.strip():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Введите новое имя пользователя"
            )
        # проверим на наличие значения
        db_item.name = user.name

    if user.login:
        if user.login.strip() == db_item.login.strip():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Введите новый логин пользователя"
            )
        # необходимо проверить на уникальность
        existing = await db.execute(select(
            exists(User).where(
                and_(func.lower(User.login) == user.login.lower().strip())
            )
        ))

        if existing.scalar():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким логином уже зарегистрирован в системе"
            )
        db_item.login = user.login

    if user.email:
        if user.email.strip() == db_item.email.strip():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Введите новый Email пользователя"
            )
        # необходимо проверить на уникальность
        existing = await db.execute(select(
            exists(User).where(
                and_(func.lower(User.email) == user.email.lower().strip())
            )
        ))

        if existing.scalar():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким Email уже зарегистрирован в системе"
            )
        db_item.email = user.email

    if user.gender is not None:
        try:
            new_gender = GenderType(user.gender)
        except Exception:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Некорректное значение пола",
            )
        if new_gender == db_item.gender:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Установите новое значение"
            )
        db_item.gender = new_gender

    if user.birthdate_at:
        if user.birthdate_at <= TIMESTAMP_1900:
            birthdate_at = None
        else:
            try:
                birthdate_at = datetime.datetime.fromtimestamp(user.birthdate_at / 1000.0, tz=datetime.timezone.utc)
            except Exception as _e:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=str(_e),
                )
        if birthdate_at == db_item.birthdate_at:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Введите новую дату рождения пользователя"
            )
        db_item.birthdate_at = birthdate_at

    if user.new_password and user.old_password:
        if not PasswordHasher.verify_password(user.old_password, db_item.password, db_item.salt):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Неверный пароль"
            )
        if len(user.new_password) <= 4:  # пока так, как пример минимальной валидации.
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Ненадежный пароль"
            )
        salt = PasswordHasher.generate_salt()
        db_item.salt = salt
        db_item.password = PasswordHasher.hash_password(user.new_password, salt)

    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item
