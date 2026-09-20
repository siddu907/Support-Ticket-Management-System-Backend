from app.services.notification_service import create


def test_notification_service_creates_notification():
	class FakeSession:
		def add(self, value):
			self.value = value

	session = FakeSession()
	notification = create(session, 1, "TEST", "Test", "Message", 2)
	assert session.value is notification
	assert notification.ticket_id == 2
