from fastapi import HTTPException, Depends, APIRouter, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db import get_db
from app.db.models.users import User
from app.schemas import UserRead, UserCreate, UserUpdate, PaginatedResponse, UserPut

router = APIRouter(
    prefix='/users',
    tags=["Пользователи"],
    # dependencies=[Depends(request_shoule_be_with_token)]
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


@router.post("/", response_model=UserRead)
async def create_item(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    db_item = User(name=user.name, user=user.count)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.patch("/{item_id}", response_model=UserRead)
async def update_item(
    item_id: int,
    item: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    """ Обновление записи модели """
    result = await db.execute(select(User).where(User.id == item_id))
    db_item = result.scalar_one_or_none()

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if item.name is not None:
        db_item.name = item.name
    if item.count is not None:
        db_item.count = item.count

    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.put("/{item_id}", response_model=UserRead)
async def replace_item(
    item_id: int,
    item: UserPut,
    db: AsyncSession = Depends(get_db),
):
    """ Перезапись записи модели """
    result = await db.execute(select(User).where(User.id == item_id))
    db_item = result.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=404, detail="User not found")

    db_item.name = item.name
    db_item.count = item.count

    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """ Удаление записи модели """
    result = await db.execute(
        select(User).where(User.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(item)
    await db.commit()
