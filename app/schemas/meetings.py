from datetime import datetime, date, time, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer, Field


class MeetingRead(BaseModel):
    """ для GET """
    external_id: int = Field(validation_alias='id')
    external_user_id: int = Field(validation_alias='user_id')
    title: str
    description: str
    start_date: Optional[date]
    end_date: Optional[date]
    start_time: Optional[time]
    end_time: Optional[time]
    created_at: datetime
    updated_at: datetime
    location: str
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

    @field_serializer('start_date', 'end_date')
    def serialize_date(self, value: Optional[date]) -> Optional[int]:
        if value is None:
            return None
        dt = datetime(
            year=value.year,
            month=value.month,
            day=value.day,
            tzinfo=timezone.utc
        )
        return int(dt.timestamp() * 1000)

    @field_serializer('start_time', 'end_time')
    def serialize_time(self, value: Optional[time]) -> Optional[int]:
        if value is None:
            return None
        total_ms = (
            value.hour * 60 * 60 * 1000 +
            value.minute * 60 * 1000 +
            value.second * 1000 +
            value.microsecond // 1000
        )
        return total_ms


class MeetingCreate(BaseModel):
    """ для POST """
    external_user_id: int
    title: str
    description: str
    location: str
    start_date: Optional[int] = None
    end_date: Optional[int] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    is_active: bool = True

    model_config = ConfigDict(extra="ignore")


class MeetingUpdate(BaseModel):
    """ для PATCH """
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[int] = None
    end_date: Optional[int] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="ignore")
