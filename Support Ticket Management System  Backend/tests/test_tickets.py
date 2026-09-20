from app.core.security import hash_password
from app.models import Role, TicketCategory, User
from app.repositories.ticket_repository import build_list_query

import pytest


def seed_admin_and_agent(client):
	override = next(iter(client.app.dependency_overrides.values()))
	db = next(override())
	admin_role = Role(name="Admin")
	agent_role = Role(name="Support Agent")
	db.add_all([admin_role, agent_role])
	db.flush()
	admin = User(name="Admin", email="admin@example.com", hashed_password=hash_password("Admin1!x"), role_id=admin_role.id)
	agent = User(name="Agent", email="agent@example.com", hashed_password=hash_password("Agent1!x"), role_id=agent_role.id)
	db.add_all([admin, agent, TicketCategory(name="Technical")])
	db.commit()
	agent_id = agent.id
	db.close()
	return agent_id


def test_assign_requires_reassign_for_existing_assignment(client):
	agent_id = seed_admin_and_agent(client)
	admin_token = client.post("/auth/login", json={"email": "admin@example.com", "password": "Admin1!x"}).json()["access_token"]
	client.post("/auth/register", json={"name": "Customer", "email": "customer@example.com", "password": "Customer1!"})
	customer_token = client.post("/auth/login", json={"email": "customer@example.com", "password": "Customer1!"}).json()["access_token"]
	ticket = client.post("/tickets", json={"title": "Issue", "description": "Details", "category_id": 1, "priority": "High"}, headers={"Authorization": f"Bearer {customer_token}"}).json()
	headers = {"Authorization": f"Bearer {admin_token}"}
	assert client.put(f"/tickets/{ticket['id']}/assign", json={"agent_id": agent_id}, headers=headers).status_code == 200
	response = client.put(f"/tickets/{ticket['id']}/assign", json={"agent_id": agent_id}, headers=headers)
	assert response.status_code == 400
	assert response.json()["error"]["message"] == "This task is already assigned to this agent"


def test_reassign_requires_assign_for_unassigned_ticket(client):
	agent_id = seed_admin_and_agent(client)
	admin_token = client.post("/auth/login", json={"email": "admin@example.com", "password": "Admin1!x"}).json()["access_token"]
	client.post("/auth/register", json={"name": "Customer", "email": "customer@example.com", "password": "Customer1!"})
	customer_token = client.post("/auth/login", json={"email": "customer@example.com", "password": "Customer1!"}).json()["access_token"]
	ticket = client.post("/tickets", json={"title": "Issue", "description": "Details", "category_id": 1, "priority": "High"}, headers={"Authorization": f"Bearer {customer_token}"}).json()
	response = client.put(f"/tickets/{ticket['id']}/reassign", json={"agent_id": agent_id}, headers={"Authorization": f"Bearer {admin_token}"})
	assert response.status_code == 400
	assert response.json()["error"]["message"] == "Unassigned tickets must be assigned through the assign endpoint"


def test_agent_cannot_initially_assign(client):
	agent_id = seed_admin_and_agent(client)
	client.post("/auth/register", json={"name": "Customer", "email": "customer@example.com", "password": "Customer1!"})
	customer_token = client.post("/auth/login", json={"email": "customer@example.com", "password": "Customer1!"}).json()["access_token"]
	ticket = client.post("/tickets", json={"title": "Issue", "description": "Details", "category_id": 1, "priority": "Low"}, headers={"Authorization": f"Bearer {customer_token}"}).json()
	agent_token = client.post("/auth/login", json={"email": "agent@example.com", "password": "Agent1!x"}).json()["access_token"]
	response = client.put(f"/tickets/{ticket['id']}/assign", json={"agent_id": agent_id}, headers={"Authorization": f"Bearer {agent_token}"})
	assert response.status_code == 403


def test_agent_cannot_resolve_ticket_assigned_to_another_agent(client):
	seed_admin_and_agent(client)
	override = next(iter(client.app.dependency_overrides.values()))
	db = next(override())
	agent_role = db.query(Role).filter_by(name="Support Agent").first()
	other_agent = User(name="Other Agent", email="otheragent@example.com", hashed_password=hash_password("Agent2!x"), role_id=agent_role.id)
	db.add(other_agent)
	db.commit()
	db.refresh(other_agent)
	admin_token = client.post("/auth/login", json={"email": "admin@example.com", "password": "Admin1!x"}).json()["access_token"]
	client.post("/auth/register", json={"name": "Customer", "email": "customer@example.com", "password": "Customer1!"})
	customer_token = client.post("/auth/login", json={"email": "customer@example.com", "password": "Customer1!"}).json()["access_token"]
	ticket = client.post("/tickets", json={"title": "Issue", "description": "Details", "category_id": 1, "priority": "Low"}, headers={"Authorization": f"Bearer {customer_token}"}).json()
	assign_response = client.put(f"/tickets/{ticket['id']}/assign", json={"agent_id": 2}, headers={"Authorization": f"Bearer {admin_token}"})
	assert assign_response.status_code == 200
	other_agent_token = client.post("/auth/login", json={"email": "otheragent@example.com", "password": "Agent2!x"}).json()["access_token"]
	response = client.put(f"/tickets/{ticket['id']}/resolve", headers={"Authorization": f"Bearer {other_agent_token}"})
	assert response.status_code == 403
	assert response.json()["error"]["message"] == "You cannot access this ticket"


def test_reassign_creates_reassigned_notification_for_new_agent(client):
	seed_admin_and_agent(client)
	override = next(iter(client.app.dependency_overrides.values()))
	db = next(override())
	agent_role = db.query(Role).filter_by(name="Support Agent").first()
	new_agent = User(name="New Agent", email="newagent@example.com", hashed_password=hash_password("Agent2!x"), role_id=agent_role.id)
	db.add(new_agent)
	db.commit()
	db.refresh(new_agent)
	admin_token = client.post("/auth/login", json={"email": "admin@example.com", "password": "Admin1!x"}).json()["access_token"]
	client.post("/auth/register", json={"name": "Customer", "email": "customer@example.com", "password": "Customer1!"})
	customer_token = client.post("/auth/login", json={"email": "customer@example.com", "password": "Customer1!"}).json()["access_token"]
	ticket = client.post("/tickets", json={"title": "Issue", "description": "Details", "category_id": 1, "priority": "Low"}, headers={"Authorization": f"Bearer {customer_token}"}).json()
	client.put(f"/tickets/{ticket['id']}/assign", json={"agent_id": 2}, headers={"Authorization": f"Bearer {admin_token}"})
	response = client.put(f"/tickets/{ticket['id']}/reassign", json={"agent_id": new_agent.id}, headers={"Authorization": f"Bearer {admin_token}"})
	assert response.status_code == 200
	new_agent_token = client.post("/auth/login", json={"email": "newagent@example.com", "password": "Agent2!x"}).json()["access_token"]
	notifications = client.get("/notifications", headers={"Authorization": f"Bearer {new_agent_token}"})
	assert notifications.status_code == 200
	assert any(item["title"] == "Ticket reassigned" for item in notifications.json())


def test_invalid_status_transition_is_rejected(client):
	seed_admin_and_agent(client)
	admin_token = client.post("/auth/login", json={"email": "admin@example.com", "password": "Admin1!x"}).json()["access_token"]
	client.post("/auth/register", json={"name": "Customer", "email": "customer@example.com", "password": "Customer1!"})
	token = client.post("/auth/login", json={"email": "customer@example.com", "password": "Customer1!"}).json()["access_token"]
	ticket = client.post("/tickets", json={"title": "Issue", "description": "Details", "category_id": 1, "priority": "Low"}, headers={"Authorization": f"Bearer {token}"}).json()
	response = client.put(f"/tickets/{ticket['id']}/close", headers={"Authorization": f"Bearer {admin_token}"})
	assert response.status_code == 400


def test_ticket_repository_rejects_invalid_sort_field():
	with pytest.raises(ValueError, match="Unsupported ticket sort field"):
		build_list_query(sort_by="unknown")


def test_ticket_repository_rejects_invalid_sort_order():
	with pytest.raises(ValueError, match="Unsupported ticket sort order"):
		build_list_query(sort_order="sideways")


def test_only_customers_can_create_tickets(client):
	seed_admin_and_agent(client)
	admin_token = client.post("/auth/login", json={"email": "admin@example.com", "password": "Admin1!x"}).json()["access_token"]
	agent_token = client.post("/auth/login", json={"email": "agent@example.com", "password": "Agent1!x"}).json()["access_token"]
	admin_response = client.post("/tickets", json={"title": "Issue", "description": "Details", "category_id": 1, "priority": "Low"}, headers={"Authorization": f"Bearer {admin_token}"})
	agent_response = client.post("/tickets", json={"title": "Issue", "description": "Details", "category_id": 1, "priority": "Low"}, headers={"Authorization": f"Bearer {agent_token}"})
	assert admin_response.status_code == 403
	assert agent_response.status_code == 403


def test_admin_can_delete_ticket_with_notifications(client):
	seed_admin_and_agent(client)
	admin_token = client.post("/auth/login", json={"email": "admin@example.com", "password": "Admin1!x"}).json()["access_token"]
	client.post("/auth/register", json={"name": "Customer", "email": "customer@example.com", "password": "Customer1!"})
	customer_token = client.post("/auth/login", json={"email": "customer@example.com", "password": "Customer1!"}).json()["access_token"]
	ticket = client.post("/tickets", json={"title": "Issue", "description": "Details", "category_id": 1, "priority": "Low"}, headers={"Authorization": f"Bearer {customer_token}"}).json()

	delete_response = client.delete(f"/tickets/{ticket['id']}", headers={"Authorization": f"Bearer {admin_token}"})

	assert delete_response.status_code == 200
	assert delete_response.json()["message"] == "Ticket deleted"


def test_ticket_list_accepts_12_hour_datetime_query_format(client):
	seed_admin_and_agent(client)
	admin_token = client.post("/auth/login", json={"email": "admin@example.com", "password": "Admin1!x"}).json()["access_token"]
	client.post("/auth/register", json={"name": "Customer", "email": "customer@example.com", "password": "Customer1!"})
	customer_token = client.post("/auth/login", json={"email": "customer@example.com", "password": "Customer1!"}).json()["access_token"]
	client.post("/tickets", json={"title": "Issue", "description": "Details", "category_id": 1, "priority": "Low"}, headers={"Authorization": f"Bearer {customer_token}"})

	response = client.get(
		"/tickets",
		params={"date_from": "2024-01-01 12:00 PM", "date_to": "2035-01-01 11:59 PM"},
		headers={"Authorization": f"Bearer {admin_token}"},
	)

	assert response.status_code == 200
	assert "items" in response.json()
