from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer, Field


class MeetingRead(BaseModel):
    """ для GET """
    external_id: int = Field(validation_alias='id')
    external_user_id: int = Field(validation_alias='user_id')
    title: str
    description: str
    meeting_at: datetime
    created_at: datetime
    updated_at: datetime
    location: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @field_serializer('created_at', 'updated_at', 'meeting_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[int]:
        """Преобразует datetime в Unix timestamp (целое число секунд)."""
        if value is None:
            return None
        return int(value.timestamp()) * 1000


class MeetingCreate(BaseModel):
    """ для POST """
    external_user_id: int
    title: str
    description: str
    location: str
    meeting_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(extra="ignore")


class MeetingUpdate(BaseModel):
    """ для PATCH """
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    meeting_at: Optional[datetime] = None

    model_config = ConfigDict(extra="ignore")
