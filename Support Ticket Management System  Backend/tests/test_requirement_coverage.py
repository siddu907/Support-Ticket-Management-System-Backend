from datetime import datetime, timedelta, timezone
from io import BytesIO

from app.core.security import hash_password
from app.database import get_db
from app.models import Role, Ticket, TicketCategory, User
from app.services.sla_service import create_sla_breach_notifications


def get_db_session(client):
    override = client.app.dependency_overrides.get(get_db)
    if override is None:
        raise RuntimeError("No database override configured")
    return next(override())


def seed_support_data(client):
    db = get_db_session(client)

    admin_role = db.query(Role).filter_by(name="Admin").first()
    if admin_role is None:
        admin_role = Role(name="Admin")
        db.add(admin_role)

    agent_role = db.query(Role).filter_by(name="Support Agent").first()
    if agent_role is None:
        agent_role = Role(name="Support Agent")
        db.add(agent_role)

    customer_role = db.query(Role).filter_by(name="Customer").first()
    if customer_role is None:
        customer_role = Role(name="Customer")
        db.add(customer_role)

    db.flush()

    category = db.query(TicketCategory).filter_by(name="General").first()
    if category is None:
        category = TicketCategory(name="General", is_active=True)
        db.add(category)
        db.flush()

    admin = db.query(User).filter_by(email="admin@example.com").first()
    if admin is None:
        admin = User(name="Admin", email="admin@example.com", hashed_password=hash_password("Admin1!x"), role_id=admin_role.id, is_active=True)
        db.add(admin)

    agent = db.query(User).filter_by(email="agent@example.com").first()
    if agent is None:
        agent = User(name="Agent", email="agent@example.com", hashed_password=hash_password("Agent1!x"), role_id=agent_role.id, is_active=True)
        db.add(agent)

    customer = db.query(User).filter_by(email="customer@example.com").first()
    if customer is None:
        customer = User(name="Customer", email="customer@example.com", hashed_password=hash_password("Customer1!"), role_id=customer_role.id, is_active=True)
        db.add(customer)

    db.commit()
    db.refresh(category)
    db.refresh(admin)
    db.refresh(agent)
    db.refresh(customer)
    db.close()

    return {
        "admin_id": admin.id,
        "agent_id": agent.id,
        "customer_id": customer.id,
        "category_id": category.id,
        "admin_email": admin.email,
        "agent_email": agent.email,
        "customer_email": customer.email,
    }


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def login(client, email, password):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_auth_register_login_profile_and_invalid_credentials(client):
    response = client.post("/auth/register", json={"name": "Tester", "email": "tester@example.com", "password": "Strong1!"})
    assert response.status_code == 201

    login_response = client.post("/auth/login", json={"email": "tester@example.com", "password": "Strong1!"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token

    profile = client.get("/auth/profile", headers=auth_headers(token))
    assert profile.status_code == 200
    assert profile.json()["email"] == "tester@example.com"

    unauthenticated = client.get("/auth/profile")
    assert unauthenticated.status_code == 401

    invalid_login = client.post("/auth/login", json={"email": "tester@example.com", "password": "WrongPass1!"})
    assert invalid_login.status_code == 401


def test_admin_user_management_and_duplicate_email(client):
    seed_support_data(client)
    admin_token = login(client, "admin@example.com", "Admin1!x")
    customer_token = login(client, "customer@example.com", "Customer1!")

    customer_forbidden = client.get("/users", headers=auth_headers(customer_token))
    assert customer_forbidden.status_code == 403

    duplicate = client.post("/auth/register", json={"name": "Dup", "email": "customer@example.com", "password": "Strong1!"})
    assert duplicate.status_code == 409

    users = client.get("/users", headers=auth_headers(admin_token))
    assert users.status_code == 200
    assert len(users.json()) >= 3

    user_id = next(item["id"] for item in users.json() if item["email"] == "customer@example.com")
    deactivate = client.put(f"/users/{user_id}/deactivate", headers=auth_headers(admin_token))
    assert deactivate.status_code == 200
    assert deactivate.json()["is_active"] is False

    activate = client.put(f"/users/{user_id}/activate", headers=auth_headers(admin_token))
    assert activate.status_code == 200
    assert activate.json()["is_active"] is True

    user_tickets = client.get(f"/users/{user_id}/tickets", headers=auth_headers(admin_token))
    assert user_tickets.status_code == 200


def test_ticket_crud_invalid_category_and_invalid_transition(client):
    seed = seed_support_data(client)
    customer_token = login(client, seed["customer_email"], "Customer1!")
    admin_token = login(client, seed["admin_email"], "Admin1!x")

    created = client.post(
        "/tickets",
        json={"title": "Issue", "description": "Need help", "category_id": seed["category_id"], "priority": "High"},
        headers=auth_headers(customer_token),
    )
    assert created.status_code == 201
    ticket = created.json()
    ticket_id = ticket["id"]

    fetched = client.get(f"/tickets/{ticket_id}", headers=auth_headers(customer_token))
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Issue"

    updated = client.put(f"/tickets/{ticket_id}", json={"title": "Updated issue"}, headers=auth_headers(customer_token))
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated issue"

    invalid_category = client.post(
        "/tickets",
        json={"title": "Bad category", "description": "x", "category_id": 9999, "priority": "Low"},
        headers=auth_headers(customer_token),
    )
    assert invalid_category.status_code == 400

    invalid_transition = client.put(f"/tickets/{ticket_id}/close", headers=auth_headers(admin_token))
    assert invalid_transition.status_code == 400

    deleted = client.delete(f"/tickets/{ticket_id}", headers=auth_headers(admin_token))
    assert deleted.status_code == 200


def test_ticket_assignment_rules_and_inactive_agent_block(client):
    seed = seed_support_data(client)
    customer_token = login(client, seed["customer_email"], "Customer1!")
    admin_token = login(client, seed["admin_email"], "Admin1!x")
    agent_token = login(client, seed["agent_email"], "Agent1!x")

    created = client.post(
        "/tickets",
        json={"title": "Assignment test", "description": "Assign me", "category_id": seed["category_id"], "priority": "Low"},
        headers=auth_headers(customer_token),
    )
    ticket = created.json()

    unauthorized_assign = client.put(
        f"/tickets/{ticket['id']}/assign",
        json={"agent_id": seed["agent_id"]},
        headers=auth_headers(agent_token),
    )
    assert unauthorized_assign.status_code == 403

    assigned = client.put(
        f"/tickets/{ticket['id']}/assign",
        json={"agent_id": seed["agent_id"]},
        headers=auth_headers(admin_token),
    )
    assert assigned.status_code == 200

    db = get_db_session(client)
    agent = db.get(User, seed["agent_id"])
    agent.is_active = False
    db.commit(); db.close()

    inactive = client.put(
        f"/tickets/{ticket['id']}/reassign",
        json={"agent_id": seed["agent_id"]},
        headers=auth_headers(admin_token),
    )
    assert inactive.status_code == 400


def test_comments_and_attachments_rules(client):
    seed = seed_support_data(client)
    customer_token = login(client, seed["customer_email"], "Customer1!")
    agent_token = login(client, seed["agent_email"], "Agent1!x")
    ticket = client.post(
        "/tickets",
        json={"title": "Comment issue", "description": "Discuss", "category_id": seed["category_id"], "priority": "Medium"},
        headers=auth_headers(customer_token),
    ).json()

    comment = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "Initial comment"},
        headers=auth_headers(customer_token),
    )
    assert comment.status_code == 201
    comment_id = comment.json()["id"]

    comment_list = client.get(f"/tickets/{ticket['id']}/comments", headers=auth_headers(customer_token))
    assert comment_list.status_code == 200
    assert len(comment_list.json()) >= 1

    unauthorized_update = client.put(
        f"/comments/{comment_id}",
        json={"content": "Changed by someone else"},
        headers=auth_headers(agent_token),
    )
    assert unauthorized_update.status_code == 403

    invalid_upload = client.post(
        f"/tickets/{ticket['id']}/attachments",
        headers=auth_headers(customer_token),
        files={"file": ("bad.pdf", b"not-a-real-pdf", "application/pdf")},
    )
    assert invalid_upload.status_code == 400


def test_notifications_dashboard_and_sla(client):
    seed = seed_support_data(client)
    customer_token = login(client, seed["customer_email"], "Customer1!")
    admin_token = login(client, seed["admin_email"], "Admin1!x")
    agent_token = login(client, seed["agent_email"], "Agent1!x")

    ticket = client.post(
        "/tickets",
        json={"title": "Notification issue", "description": "Need attention", "category_id": seed["category_id"], "priority": "Critical"},
        headers=auth_headers(customer_token),
    ).json()

    notifications = client.get("/notifications", headers=auth_headers(customer_token))
    assert notifications.status_code == 200
    assert len(notifications.json()) >= 1

    notification_id = notifications.json()[0]["id"]
    read_response = client.put(f"/notifications/{notification_id}/read", headers=auth_headers(customer_token))
    assert read_response.status_code == 200

    mark_all = client.put("/notifications/read-all", headers=auth_headers(customer_token))
    assert mark_all.status_code == 200

    admin_dashboard = client.get("/dashboard/admin", headers=auth_headers(admin_token))
    assert admin_dashboard.status_code == 200
    for key in ["total_tickets", "open_tickets", "resolved_tickets", "closed_tickets", "overdue_tickets", "critical_tickets"]:
        assert key in admin_dashboard.json()

    agent_dashboard = client.get("/dashboard/support-agent", headers=auth_headers(agent_token))
    assert agent_dashboard.status_code == 200
    for key in ["total_tickets", "my_open_tickets", "my_overdue_tickets", "my_resolved_tickets"]:
        assert key in agent_dashboard.json()

    db = get_db_session(client)
    ticket_row = db.get(Ticket, ticket["id"])
    ticket_row.agent_id = seed["agent_id"]
    ticket_row.due_date = datetime.now(timezone.utc) - timedelta(days=2)
    ticket_row.status = "Open"
    db.commit()
    created = create_sla_breach_notifications(db)
    db.close()
    assert created >= 1
