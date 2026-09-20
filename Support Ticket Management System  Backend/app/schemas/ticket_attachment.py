from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_serializer

class TicketAttachmentResponse(BaseModel):
    id: int
    ticket_id: int
    uploader_id: int
    file_name: str
    file_type: str
    file_size: int
    file_path: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %I:%M %p")