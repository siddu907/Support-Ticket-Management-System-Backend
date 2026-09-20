# Support Ticket Management System API

FastAPI-based support ticket backend for managing customers, support agents, administrators, ticket lifecycles, comments, attachments, notifications, and SLA monitoring.

## Project overview

This project is designed for a support ticket system where:

- Customers create and view their own tickets.
- Support agents work on assigned tickets.
- Admins manage users, categories, assignments, audit logs, and full ticket operations.
- SLA tracking monitors overdue tickets and creates breach notifications for the assigned agent.

## Roles

The system uses three roles:

- Admin
- Support Agent
- Customer

## Authentication and authorization

The API uses JWT-based authentication with a manual bearer token flow.

- Login returns an `access_token` and a `refresh_token`.
- Protected routes expect the token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

- Refresh tokens are used only to obtain a new access token.
- Access tokens are used for protected endpoints.
- Logout invalidates the current user token session and refresh tokens.

## Setup

1. Create a PostgreSQL database.
2. Copy the sample environment file if needed.
3. Update the environment variables in `.env`.
4. Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

5. Apply database migrations:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

6. Start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload or

uvicorn app.main:app --reload
```

## API documentation

Swagger and OpenAPI documentation are available at:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

A detailed API reference with endpoint summaries and request/response samples is available in:

- [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

## Postman collection

The project includes a single consolidated Postman collection:

- [Support-Ticket-Management-System.postman_collection.json](Support-Ticket-Management-System.postman_collection.json)

## Authentication examples

### Login

```http
POST /auth/login
Content-Type: application/json
```

```json
{
  "email": "admin@example.com",
  "password": "Admin1!x"
}
```

Response example:

```json
{
  "access_token": "<jwt_access_token>",
  "refresh_token": "<jwt_refresh_token>",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Admin User",
    "email": "admin@example.com",
    "role": "Admin",
    "role_id": 1,
    "is_active": true,
    "created_at": "2026-01-01 09:00 AM",
    "updated_at": "2026-01-01 09:00 AM"
  }
}
```

### Refresh token

```http
POST /auth/refresh
Content-Type: application/json
```

```json
{
  "refresh_token": "<refresh_token>"
}
```

## SLA worker configuration

The SLA worker is controlled by environment variables:

```env
ENABLE_SLA_WORKER=true
SLA_WORKER_INTERVAL_SECONDS=3600
```

- `ENABLE_SLA_WORKER=true` enables the background SLA monitoring job.
- `SLA_WORKER_INTERVAL_SECONDS=3600` means the worker checks overdue tickets every 3600 seconds (1 hour).
- If set to false, the worker is disabled and no automatic SLA breach checks run.

## Ticket behavior summary

- Customers can create tickets.
- Admins can assign tickets to agents.
- Reassignment is used for tickets already assigned.
- Status updates include Open, In Progress, Resolved, and Closed.
- Ticket access is restricted based on role and ownership.
- Ticket time values are returned in 12-hour format, such as `2026-09-20 09:45 AM`.

## Core modules

- app/main.py
- app/routers/
- app/services/
- app/models/
- app/schemas/
- app/core/

## Testing

Run tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q

or py -m pytest -q
```

## Notes

- Protected endpoints require a valid bearer token.
- Unauthorized requests return 401.
- Insufficient permission requests return 403.
- Validation errors return 400.
- The backend follows a router → service → repository → model structure.
