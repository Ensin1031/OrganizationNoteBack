import datetime
from typing import Optional

from fastapi import HTTPException, Depends, APIRouter, Query
from sqlalchemy import select, func, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db import get_db
from app.db.models.users import User, TIMESTAMP_1900
from app.schemas import UserRead, UserUpdate, PaginatedResponse
from app.utils.gender_enum import GenderType
from app.utils.password_hasher import PasswordHasher
from app.utils.request_with_token_data import get_current_user_id

router = APIRouter(
    prefix='/users',
    tags=["Пользователи"],
)


@router.get("/", response_model=PaginatedResponse[UserRead])
async def get_users(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
):
    """ Получение данных по списку записей модели """

    base_stmt = select(User)

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


@router.get("/{user_id}", response_model=UserRead)
async def get_user(item_id: int, db: AsyncSession = Depends(get_db)):
    """ Получение данных по конкретной записи модели """
    result = await db.execute(select(User).where(User.id == item_id))
    db_item = result.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return db_item


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

    if user.password:
        # TODO реализовать смену пароля
        if len(user.password) <= 4:  # пока так, как пример минимальной валидации.
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Ненадежный пароль"
            )
        db_item.password = PasswordHasher.hash_password(user.password, db_item.salt)

    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item
