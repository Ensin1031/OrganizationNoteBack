from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, or_, exists, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db import get_db
from app.db.models import User
from app.schemas import AuthResponse, LoginRequest, RegisterRequest
from app.settings import settings
from app.utils.password_hasher import PasswordHasher
from app.utils.token_manager import TokenManager

router = APIRouter(
    prefix='/auth',
)


@router.post("/login/", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):

    search_value = data.login.lower().strip() if data.login and isinstance(data.login, str) else ""

    if not search_value or not data.password:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Введены некорректные значения",
        )

    qs = await db.execute(select(User).where(
        or_(
            func.lower(User.login) == search_value,
            func.lower(User.email) == search_value
        )
    ).limit(1))
    user: Optional[User] = qs.scalars().one_or_none()

    if user is None or not (
            user is not None and PasswordHasher.verify_password(data.password, user.password, user.salt)
    ):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Неверный логин или пароль",
        )

    token_manager = TokenManager(settings.secret_key)

    return {
        "access_token": token_manager.create_access_token(token_data={"user_id": user.id}),
        "user": user,
    }


@router.post("/register/", response_model=AuthResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):

    errors = {}
    email_existing = await db.execute(select(
        exists(User).where(and_(
            func.lower(User.email) == data.email.lower().strip(),
        ))
    ))

    if email_existing.scalar():
        errors['login'] = "Пользователь с таким Email уже зарегистрирован в системе"

    login_existing = await db.execute(select(
        exists(User).where(and_(
            func.lower(User.login) == data.login.lower().strip(),
        ))
    ))

    if login_existing.scalar():
        errors['login'] = "Пользователь с таким логином уже зарегистрирован в системе"

    if len(data.password) <= 4:  # пока так, как пример минимальной валидации.
        errors['password'] = "Ненадежный пароль"

    if errors or len(errors.keys()) > 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            errors
        )

    salt = PasswordHasher.generate_salt()
    hashed = PasswordHasher.hash_password(data.password, salt)

    user = User(
        name=data.name,
        login=data.login.lower().strip(),
        email=data.email.lower().strip(),
        password=hashed,
        salt=salt,
        is_admin=False,
        verified=False,
    )

    db.add(user)
    await db.commit()

    token_manager = TokenManager(settings.secret_key)

    return {
        "access_token": token_manager.create_access_token(token_data={"user_id": user.id}),
        "user": user,
    }
