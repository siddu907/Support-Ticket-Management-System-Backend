from app.core.constants import PRIORITY_SLA_HOURS


def test_dashboard_priorities_have_sla_hours():
	assert PRIORITY_SLA_HOURS == {"Low": 72, "Medium": 48, "High": 24, "Critical": 4}
