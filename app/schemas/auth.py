from pydantic import BaseModel, EmailStr

from app.schemas import UserRead


class RegisterRequest(BaseModel):
    name: str = ""
    login: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    login: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    user: UserRead
