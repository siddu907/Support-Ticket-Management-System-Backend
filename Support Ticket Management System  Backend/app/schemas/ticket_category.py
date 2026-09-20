from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_serializer


class TicketCategoryCreate(BaseModel):
    name: str
    description: str | None = None


class TicketCategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class TicketCategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %I:%M %p")