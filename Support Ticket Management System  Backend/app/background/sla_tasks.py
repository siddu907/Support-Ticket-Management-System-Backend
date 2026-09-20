import asyncio

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.sla_service import create_sla_breach_notifications


def process_sla_breaches(db: Session) -> int:
	return create_sla_breach_notifications(db)


async def _sla_worker_loop(interval_seconds: int) -> None:
	while True:
		await asyncio.sleep(interval_seconds)
		db = SessionLocal()
		try:
			process_sla_breaches(db)
		finally:
			db.close()


def start_sla_worker(enable_worker: bool = False, interval_seconds: int = 3600):
	if not enable_worker or interval_seconds <= 0:
		return None
	loop = asyncio.get_running_loop()
	return loop.create_task(_sla_worker_loop(interval_seconds))
