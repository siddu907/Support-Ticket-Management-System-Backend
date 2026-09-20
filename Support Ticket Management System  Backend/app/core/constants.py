ROLES = {"Admin", "Support Agent", "Customer"}
PRIORITY_SLA_HOURS = {"Low": 72, "Medium": 48, "High": 24, "Critical": 4}
STATUS_TRANSITIONS = {
	"Open": {"In Progress"},
	"In Progress": {"Resolved"},
	"Resolved": {"Closed", "Open"},
	"Closed": set(),
}
