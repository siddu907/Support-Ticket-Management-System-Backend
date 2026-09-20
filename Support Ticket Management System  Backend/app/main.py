import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.background.sla_tasks import start_sla_worker
from app.config import settings
from app.core.exception_handlers import http_exception_handler, unhandled_exception_handler, validation_exception_handler
from app.routers import auth, users, categories, tickets, comments, attachments, notifications, dashboard, audit_logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = start_sla_worker(
        enable_worker=settings.enable_sla_worker,
        interval_seconds=settings.sla_worker_interval_seconds,
    )
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(title="Support Ticket Management System", version="1.0.0", lifespan=lifespan)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
app.include_router(comments.router, tags=["Comments"])
app.include_router(attachments.router, tags=["Attachments"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
