from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_serializer

class TicketCommentCreate(BaseModel):
    content: str


class TicketCommentUpdate(BaseModel):
    content: str


class TicketCommentResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %I:%M %p")