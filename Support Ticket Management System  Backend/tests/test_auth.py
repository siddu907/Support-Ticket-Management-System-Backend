from pydantic import ValidationError
import pytest

from app.schemas.auth import RegisterRequest
from app.repositories.refresh_token_repository import get_active


def test_registration_validation_accepts_required_credentials():
	request = RegisterRequest(name="A", email="a@example.com", password="Strong1!")
	assert request.email == "a@example.com"


@pytest.mark.parametrize("password", ["weakpass", "short1!"])
def test_registration_validation_rejects_invalid_credentials(password):
	with pytest.raises(ValidationError):
		RegisterRequest(name="A", email="a@example.com", password=password)


def test_register_and_login(client):
	response = client.post("/auth/register", json={"name": "A", "email": "a@example.com", "password": "Strong1!"})
	assert response.status_code == 201
	login = client.post("/auth/login", json={"email": "a@example.com", "password": "Strong1!"})
	assert login.status_code == 200
	payload = login.json()
	assert payload["access_token"]
	assert payload["user"]["email"] == "a@example.com"
	assert payload["user"]["role"] == "Customer"


def test_refresh_token_is_persisted_and_rotated(client):
	client.post("/auth/register", json={"name": "A", "email": "a@example.com", "password": "Strong1!"})
	login = client.post("/auth/login", json={"email": "a@example.com", "password": "Strong1!"}).json()
	refreshed = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
	assert refreshed.status_code == 200
	assert refreshed.json()["refresh_token"] != login["refresh_token"]
	assert client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]}).status_code == 401


def test_refresh_token_is_rejected_for_protected_routes(client):
	client.post("/auth/register", json={"name": "A", "email": "a@example.com", "password": "Strong1!"})
	login = client.post("/auth/login", json={"email": "a@example.com", "password": "Strong1!"}).json()
	response = client.get("/auth/profile", headers={"Authorization": f"Bearer {login['refresh_token']}"})
	assert response.status_code == 401


def test_logout_revokes_current_access_token(client):
	client.post("/auth/register", json={"name": "A", "email": "a@example.com", "password": "Strong1!"})
	login = client.post("/auth/login", json={"email": "a@example.com", "password": "Strong1!"}).json()
	profile_before = client.get("/auth/profile", headers={"Authorization": f"Bearer {login['access_token']}"})
	assert profile_before.status_code == 200

	logout = client.post("/auth/logout", headers={"Authorization": f"Bearer {login['access_token']}"})
	assert logout.status_code == 200

	profile_after = client.get("/auth/profile", headers={"Authorization": f"Bearer {login['access_token']}"})
	assert profile_after.status_code == 401


def test_change_password_accepts_new_password_only(client):
	client.post("/auth/register", json={"name": "A", "email": "a@example.com", "password": "Strong1!"})
	login = client.post("/auth/login", json={"email": "a@example.com", "password": "Strong1!"}).json()
	response = client.put(
		"/auth/change-password",
		headers={"Authorization": f"Bearer {login['access_token']}"},
		json={"new_password": "Newpass@123"},
	)
	assert response.status_code == 200
	assert response.json()["message"] == "Password changed successfully"


def test_change_password_rejects_same_password(client):
	client.post("/auth/register", json={"name": "A", "email": "a@example.com", "password": "Strong1!"})
	login = client.post("/auth/login", json={"email": "a@example.com", "password": "Strong1!"}).json()
	response = client.put(
		"/auth/change-password",
		headers={"Authorization": f"Bearer {login['access_token']}"},
		json={"new_password": "Strong1!"},
	)
	assert response.status_code == 400
	assert response.json()["error"]["message"] == "New password must be different from the current password"


def test_refresh_token_repository_rejects_expired_token():
	from datetime import datetime, timedelta, timezone

	class FakeSession:
		def scalar(self, query):
			class Token:
				expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
			return Token()

	assert get_active(FakeSession(), "expired") is None


def test_unhandled_exception_handler_returns_consistent_500_payload():
	import asyncio

	from starlette.requests import Request

	from app.core.exception_handlers import unhandled_exception_handler

	request = Request({"type": "http", "method": "GET", "path": "/", "headers": [], "query_string": b"", "scheme": "http", "server": ("test", 80), "client": ("test", 1)})
	response = asyncio.run(unhandled_exception_handler(request, RuntimeError("boom")))

	assert response.status_code == 500
	assert response.body == b'{"success":false,"error":{"code":"INTERNAL_SERVER_ERROR","message":"An unexpected internal server error occurred"}}'
