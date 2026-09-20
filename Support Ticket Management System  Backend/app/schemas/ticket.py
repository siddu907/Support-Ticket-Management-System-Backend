from pydantic import BaseModel


class TicketCreate(BaseModel):
    title: str
    description: str
    category_id: int
    priority: str


class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category_id: int | None = None
    priority: str | None = None
    status: str | None = None


class TicketAssign(BaseModel):
    agent_id: int


class TicketStatusUpdate(BaseModel):
    status: str


class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    title: str
    description: str
    customer_id: int
    agent_id: int | None
    category_id: int
    priority: str
    status: str
    due_date: str | None
    created_at: str
    updated_at: str


class TicketListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TicketResponse]