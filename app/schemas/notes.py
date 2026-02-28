from datetime import datetime, timezone
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, field_serializer, Field

from app.utils.note_priority_enum import NotePriority


class NoteRead(BaseModel):
    """ для GET """
    external_id: int = Field(validation_alias='id')
    external_user_id: int = Field(validation_alias='user_id')
    external_parent_note_id: Optional[int] = Field(validation_alias='parent_note_id', default=None)
    external_meeting_id: Optional[int] = Field(validation_alias='meeting_id', default=None)
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    priority: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[int]:
        """Преобразует datetime в Unix timestamp (целое число секунд)."""
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return int(value.timestamp()) * 1000

    @field_serializer('priority')
    def serialize_priority(self, value: Optional[Union[int, str, NotePriority]]) -> str:
        """ Преобразует NotePriority.name """
        if value is None:
            return ""
        if isinstance(value, NotePriority):
            return value.name
        if isinstance(value, str):
            try:
                return NotePriority(int(value)).name
            except Exception:
                return ""
        if isinstance(value, int):
            try:
                return NotePriority(value).name
            except Exception:
                return ""
        return ""


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
    is_active: bool

    model_config = ConfigDict(extra="ignore")


class NoteSync(BaseModel):
    external_id: Optional[int] = None
    external_user_id: int
    external_parent_note_id: Optional[int] = None
    external_meeting_id: Optional[int] = None
    title: str
    content: str
    priority: str
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    is_active: bool

    model_config = ConfigDict(extra="ignore")


class NoteUpdate(BaseModel):
    """ для PATCH """
    external_parent_note_id: Optional[int] = None
    external_meeting_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None

    model_config = ConfigDict(extra="ignore")
