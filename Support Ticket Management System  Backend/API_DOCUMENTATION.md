# Support Ticket Management System API Documentation

## 1. Swagger / OpenAPI

FastAPI exposes interactive API documentation automatically.

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

These pages provide request models, validation rules, example payloads, and the generated schema for every endpoint.

## 2. Authentication

The API uses JWT bearer tokens.

### Token flow
1. Call `POST /auth/login` with email and password.
2. Copy the `access_token` from the response.
3. Set the Authorization header as:

```http
Authorization: Bearer <access_token>
```

### Login example

Request:

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

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
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

### Refresh token example

```http
POST /auth/refresh
Content-Type: application/json
```

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Change password example

```http
PUT /auth/change-password
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "new_password": "NewPass@123"
}
```

## 3. API Endpoint Documentation

### Authentication

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| POST | /auth/register | Register a new customer account | No |
| POST | /auth/login | Authenticate user and return JWT token pair | No |
| GET | /auth/profile | Get current authenticated user profile | Yes |
| PUT | /auth/change-password | Change current user password | Yes |
| POST | /auth/refresh | Issue a new access token using refresh token | No |
| POST | /auth/logout | Invalidate the active user session and tokens | Yes |

### Users

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| POST | /users | Create a user | Yes |
| GET | /users | List all visible users | Yes |
| GET | /users/{user_id} | Get user details | Yes |
| PUT | /users/{user_id} | Update user information | Yes |
| GET | /users/{user_id}/tickets | View tickets for a user | Yes |
| PUT | /users/{user_id}/activate | Activate a user account | Yes |
| PUT | /users/{user_id}/deactivate | Deactivate a user account | Yes |
| PUT | /users/{user_id}/role | Change a user role | Yes |

### Categories

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| POST | /categories | Create a support category | Yes |
| GET | /categories | List categories | Yes |
| GET | /categories/{category_id} | Get category by id | Yes |
| PUT | /categories/{category_id} | Update category | Yes |
| PUT | /categories/{category_id}/activate | Activate category | Yes |
| PUT | /categories/{category_id}/deactivate | Deactivate category | Yes |

### Tickets

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| POST | /tickets | Create a new ticket | Yes |
| GET | /tickets | List tickets with filters and pagination | Yes |
| GET | /tickets/{ticket_id} | Get a single ticket | Yes |
| PUT | /tickets/{ticket_id} | Update ticket details or status | Yes |
| DELETE | /tickets/{ticket_id} | Delete a ticket | Yes |
| PUT | /tickets/{ticket_id}/assign | Assign a ticket to an agent | Yes |
| PUT | /tickets/{ticket_id}/reassign | Reassign an already assigned ticket | Yes |
| PUT | /tickets/{ticket_id}/resolve | Mark a ticket as resolved | Yes |
| PUT | /tickets/{ticket_id}/close | Mark a ticket as closed | Yes |
| PUT | /tickets/{ticket_id}/reopen | Reopen a ticket | Yes |

### Comments

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| POST | /tickets/{ticket_id}/comments | Add a comment to a ticket | Yes |
| GET | /tickets/{ticket_id}/comments | List comments for a ticket | Yes |
| PUT | /comments/{comment_id} | Update a comment | Yes |
| DELETE | /comments/{comment_id} | Delete a comment | Yes |

### Attachments

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| POST | /tickets/{ticket_id}/attachments | Upload attachment to a ticket | Yes |
| GET | /tickets/{ticket_id}/attachments | List ticket attachments | Yes |
| GET | /attachments/{attachment_id} | Download a file by attachment id | Yes |
| DELETE | /attachments/{attachment_id} | Delete an attachment | Yes |

### Notifications

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| GET | /notifications | List notifications for current user | Yes |
| PUT | /notifications/{notification_id}/read | Mark a notification as read | Yes |
| PUT | /notifications/read-all | Mark all notifications as read | Yes |

### Dashboard

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| GET | /dashboard/admin | Admin dashboard summary | Yes |
| GET | /dashboard/support-agent | Support-agent dashboard summary | Yes |

### Audit Logs

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| GET | /audit-logs | List audit events | Yes |
| GET | /audit-logs/{log_id} | Get log by id | Yes |

## 4. Request and Response Examples

### Create ticket

Request:

```http
POST /tickets
Authorization: Bearer <customer_token>
Content-Type: application/json
```

```json
{
  "title": "Login issue",
  "description": "Unable to login after password reset",
  "category_id": 1,
  "priority": "High"
}
```

Response:

```json
{
  "id": 12,
  "ticket_number": "TKT-AB12CD34EF",
  "title": "Login issue",
  "description": "Unable to login after password reset",
  "customer_id": 3,
  "agent_id": null,
  "category_id": 1,
  "priority": "High",
  "status": "Open",
  "due_date": "2026-09-20 10:00 AM",
  "created_at": "2026-09-20 09:45 AM",
  "updated_at": "2026-09-20 09:45 AM"
}
```

### Assign ticket

Request:

```http
PUT /tickets/12/assign
Authorization: Bearer <admin_token>
Content-Type: application/json
```

```json
{
  "agent_id": 7
}
```

### Add comment

Request:

```http
POST /tickets/12/comments
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "content": "I confirmed the issue and requested additional information."
}
```

Response:

```json
{
  "id": 5,
  "ticket_id": 12,
  "user_id": 7,
  "content": "I confirmed the issue and requested additional information.",
  "created_at": "2026-09-20 11:15 AM",
  "updated_at": "2026-09-20 11:15 AM"
}
```

### Upload attachment

```http
POST /tickets/12/attachments
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

Form-data:

```text
file: screenshot.png
```

## 5. Response and validation notes

- Authentication errors return HTTP 401 when the token is missing, invalid, or expired.
- Permission errors return HTTP 403 when the user is authenticated but not allowed to access a resource.
- Validation errors return HTTP 400 with a detailed message.
- Date and time values use 12-hour format like `YYYY-MM-DD hh:mm AM/PM`.
- Role-based access is enforced for Admin, Support Agent, and Customer users.

## 6. Common status values

Ticket status values include:

- Open
- In Progress
- Resolved
- Closed

Priority values include:

- Low
- Medium
- High
- Critical

## 7. Example full flow

```http
POST /auth/login
POST /tickets
PUT /tickets/12/assign
POST /tickets/12/comments
GET /tickets/12
GET /notifications
```

This flow represents the standard lifecycle for a customer support ticket.
