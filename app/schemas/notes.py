from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer, Field


class NoteRead(BaseModel):
    """ для GET """
    external_id: int = Field(validation_alias='id')
    external_user_id: int = Field(validation_alias='user_id')
    external_parent_note_id: int = Field(validation_alias='parent_note_id')
    external_meeting_id: int = Field(validation_alias='meeting_id')
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    priority: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[int]:
        """Преобразует datetime в Unix timestamp (целое число секунд)."""
        if value is None:
            return None
        return int(value.timestamp()) * 1000


class NoteCreate(BaseModel):
    """ для POST """
    external_user_id: int
    external_parent_note_id: Optional[int] = None
    external_meeting_id: Optional[int] = None
    title: str
    content: str
    priority: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(extra="ignore")


class NoteUpdate(BaseModel):
    """ для PATCH """
    external_parent_note_id: Optional[int] = None
    external_meeting_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None

    model_config = ConfigDict(extra="ignore")
