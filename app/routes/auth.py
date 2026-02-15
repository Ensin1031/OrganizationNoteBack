from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, or_, exists
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

    qs = await db.execute(select(User).where(User.login == data.login).limit(1))
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

    existing = await db.execute(select(
        exists(User).where(
            or_(
                User.email == data.email,
                User.login == data.login,
            )
        )
    ))

    if existing.scalar():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Пользователь с таким логином или Email уже зарегистрирован в системе"
        )

    salt = PasswordHasher.generate_salt()
    hashed = PasswordHasher.hash_password(data.password, salt)

    user = User(
        name=data.name,
        login=data.login,
        email=data.email,
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
