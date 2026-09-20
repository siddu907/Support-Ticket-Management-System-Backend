from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_serializer


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    ticket_id: int | None
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %I:%M %p")


class NotificationRead(BaseModel):
    is_read: bool