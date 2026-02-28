from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer, Field


class UserRead(BaseModel):
    """ для GET """
    external_id: int = Field(validation_alias='id')
    name: str
    login: str
    email: str
    verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    birthdate_at: Optional[datetime] = None
    gender: int

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @field_serializer('created_at', 'updated_at', 'birthdate_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[int]:
        """Преобразует datetime в Unix timestamp (целое число секунд)."""
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
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
    old_password: str | None = None
    new_password: str | None = None
    birthdate_at: int | None = None
    gender: int | None = None

    model_config = ConfigDict(extra="ignore")


class UserPut(BaseModel):
    """ для PUT """
    name: str
    login: str
    email: str
    password: str

    model_config = ConfigDict(extra="forbid")
