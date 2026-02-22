from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer


class UserRead(BaseModel):
    """ для GET """
    id: int
    name: str
    login: str
    email: str
    verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    birthdate_at: Optional[datetime] = None
    gender: int

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at', 'updated_at', 'birthdate_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[int]:
        """Преобразует datetime в Unix timestamp (целое число секунд)."""
        if value is None:
            return None
        return int(value.timestamp()) * 1000

    @field_serializer('gender')
    def serialize_gender(self, value):
        """Преобразует GenderType (IntEnum) в целое число."""
        return int(value)


class UserCreate(BaseModel):
    """ для POST """
    name: str
    login: str
    email: str
    password: str

    model_config = ConfigDict(extra="forbid")


class UserUpdate(BaseModel):
    """ для PATCH """
    name: str | None = None
    login: str | None = None
    email: str | None = None
    password: str | None = None

    model_config = ConfigDict(extra="forbid")


class UserPut(BaseModel):
    """ для PUT """
    name: str
    login: str
    email: str
    password: str

    model_config = ConfigDict(extra="forbid")
