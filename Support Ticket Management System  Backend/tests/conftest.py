import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
	engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
	Base.metadata.create_all(engine)
	session_factory = sessionmaker(bind=engine)

	def override_db():
		session = session_factory()
		try:
			yield session
		finally:
			session.close()

	app.dependency_overrides[get_db] = override_db
	with TestClient(app) as test_client:
		yield test_client
	app.dependency_overrides.clear()
