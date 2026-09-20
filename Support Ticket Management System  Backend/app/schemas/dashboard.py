from pydantic import BaseModel


class AdminDashboardResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    overdue_tickets: int
    critical_tickets: int
    total_customers: int
    total_agents: int
    active_agents: int
    tickets_per_agent: dict


class AgentDashboardResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    overdue_tickets: int
    critical_tickets: int


class CustomerDashboardResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int