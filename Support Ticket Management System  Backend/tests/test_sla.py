import asyncio
from datetime import datetime, timedelta, timezone

from app.background.sla_tasks import start_sla_worker
from app.models.ticket import Ticket
from app.services.sla_service import overdue_tickets


def test_overdue_ticket_detection_uses_due_date():
	class FakeSession:
		def scalars(self, query):
			class Result:
				def all(self):
					return [Ticket(due_date=datetime.now(timezone.utc) - timedelta(hours=1), status="Open")]
			return Result()

	assert len(overdue_tickets(FakeSession())) == 1


def test_start_sla_worker_starts_when_enabled(monkeypatch):
	created = {}

	class FakeLoop:
		def create_task(self, coro):
			created["task"] = coro
			coro.close()
			return object()

	monkeypatch.setattr(asyncio, "get_running_loop", lambda: FakeLoop())
	result = start_sla_worker(enable_worker=True, interval_seconds=60)

	assert result is not None
	assert "task" in created
