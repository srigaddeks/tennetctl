"""Tests for incident CRUD operations."""

import pytest
from datetime import datetime, timezone
from importlib import import_module

_core_id = import_module("backend.01_core.id")
_incidents = import_module("backend.02_features.05_monitoring.sub_features.10_incidents")


class TestIncidentCreation:
    """Test incident creation and retrieval."""

    async def test_create_incident(self, conn, org_id):
        """Create an incident."""
        incident = await _incidents.repository.create_incident(
            conn,
            org_id=org_id,
            group_key="test-group-key",
            title="Test Incident",
            severity_id=1,
        )
        assert incident["id"]
        assert incident["org_id"] == org_id
        assert incident["group_key"] == "test-group-key"
        assert incident["state_id"] == 1  # open

    async def test_get_incident(self, conn, org_id):
        """Retrieve created incident."""
        created = await _incidents.repository.create_incident(
            conn,
            org_id=org_id,
            group_key="test-group-2",
            title="Test Incident 2",
            severity_id=2,
        )
        retrieved = await _incidents.repository.get_incident(conn, created["id"])
        assert retrieved["id"] == created["id"]
        assert retrieved["title"] == "Test Incident 2"

    async def test_list_incidents(self, conn, org_id):
        """List incidents with filters."""
        # Create multiple incidents
        for i in range(3):
            await _incidents.repository.create_incident(
                conn,
                org_id=org_id,
                group_key=f"group-{i}",
                title=f"Incident {i}",
                severity_id=i + 1,
            )

        rows, total = await _incidents.repository.list_incidents(
            conn,
            org_id=org_id,
            limit=10,
            offset=0,
        )
        assert len(rows) >= 3
        assert total >= 3

    async def test_find_open_incident_within_window(self, conn, org_id):
        """Find open incident within group window."""
        incident = await _incidents.repository.create_incident(
            conn,
            org_id=org_id,
            group_key="test-window",
            title="Test Window",
            severity_id=1,
        )
        found = await _incidents.grouper.find_open_incident(
            conn,
            org_id=org_id,
            group_key="test-window",
            window_seconds=300,
        )
        assert found
        assert found["id"] == incident["id"]

    async def test_find_open_incident_outside_window(self, conn, org_id):
        """Should not find incident older than window."""
        # Create incident, manually set opened_at to old time
        incident = await _incidents.repository.create_incident(
            conn,
            org_id=org_id,
            group_key="test-old",
            title="Old Incident",
            severity_id=1,
        )
        # Manually set opened_at to 1 hour ago
        await conn.execute(
            """
            UPDATE "05_monitoring"."10_fct_monitoring_incidents"
            SET opened_at = CURRENT_TIMESTAMP - INTERVAL '1 hour'
            WHERE id = $1
            """,
            incident["id"],
        )
        found = await _incidents.grouper.find_open_incident(
            conn,
            org_id=org_id,
            group_key="test-old",
            window_seconds=300,  # 5 minutes
        )
        assert found is None


class TestIncidentStateTransitions:
    """Test incident state machine."""

    async def test_transition_to_acknowledged(self, conn, org_id, user_id):
        """Transition incident to acknowledged."""
        incident = await _incidents.repository.create_incident(
            conn,
            org_id=org_id,
            group_key="test-ack",
            title="Test Ack",
            severity_id=1,
        )
        await _incidents.repository.update_incident_state(
            conn, incident["id"], 2, user_id=user_id
        )
        updated = await _incidents.repository.get_incident(conn, incident["id"])
        assert updated["state_id"] == 2
        assert updated["ack_user_id"] == user_id
        assert updated["acknowledged_at"] is not None

    async def test_transition_to_resolved(self, conn, org_id, user_id):
        """Transition incident to resolved."""
        incident = await _incidents.repository.create_incident(
            conn,
            org_id=org_id,
            group_key="test-resolved",
            title="Test Resolved",
            severity_id=1,
        )
        await _incidents.repository.update_incident_state(
            conn, incident["id"], 3, user_id=user_id
        )
        updated = await _incidents.repository.get_incident(conn, incident["id"])
        assert updated["state_id"] == 3
        assert updated["resolved_at"] is not None

    async def test_transition_to_closed(self, conn, org_id, user_id):
        """Transition incident to closed."""
        incident = await _incidents.repository.create_incident(
            conn,
            org_id=org_id,
            group_key="test-closed",
            title="Test Closed",
            severity_id=1,
        )
        await _incidents.repository.update_incident_state(
            conn, incident["id"], 4, user_id=None
        )
        updated = await _incidents.repository.get_incident(conn, incident["id"])
        assert updated["state_id"] == 4
        assert updated["closed_at"] is not None

    async def test_update_incident_summary(self, conn, org_id):
        """Update incident summary/root_cause/postmortem_ref."""
        incident = await _incidents.repository.create_incident(
            conn,
            org_id=org_id,
            group_key="test-summary",
            title="Test Summary",
            severity_id=1,
        )
        await _incidents.repository.update_incident_summary(
            conn,
            incident["id"],
            summary="Test summary",
            root_cause="Root cause analysis",
            postmortem_ref="https://postmortem.example.com",
        )
        updated = await _incidents.repository.get_incident(conn, incident["id"])
        assert updated["summary"] == "Test summary"
        assert updated["root_cause"] == "Root cause analysis"
        assert updated["postmortem_ref"] == "https://postmortem.example.com"


class TestIncidentTimeline:
    """Test incident timeline events."""

    async def test_add_timeline_event(self, conn, org_id, user_id):
        """Add event to timeline."""
        incident = await _incidents.repository.create_incident(
            conn,
            org_id=org_id,
            group_key="test-timeline",
            title="Test Timeline",
            severity_id=1,
        )
        event = await _incidents.repository.add_timeline_event(
            conn,
            incident["id"],
            3,  # acknowledged kind_id
            actor_user_id=user_id,
            payload={"test": "data"},
        )
        assert event["id"]
        assert event["incident_id"] == incident["id"]
        assert event["kind_id"] == 3

    async def test_get_timeline(self, conn, org_id, user_id):
        """Retrieve timeline events."""
        incident = await _incidents.repository.create_incident(
            conn,
            org_id=org_id,
            group_key="test-timeline-get",
            title="Test Timeline Get",
            severity_id=1,
        )
        # Add multiple events
        for i in range(3):
            await _incidents.repository.add_timeline_event(
                conn,
                incident["id"],
                i + 1,
                actor_user_id=user_id,
                payload={"index": i},
            )
        events = await _incidents.repository.get_incident_timeline(
            conn, incident["id"]
        )
        assert len(events) >= 3


class TestIncidentAlertLinking:
    """Test linking alerts to incidents."""

    async def test_link_alert_to_incident(self, conn, org_id, alert_event_id):
        """Link alert to incident."""
        incident = await _incidents.repository.create_incident(
            conn,
            org_id=org_id,
            group_key="test-link",
            title="Test Link",
            severity_id=1,
        )
        await _incidents.repository.link_alert_to_incident(
            conn, incident["id"], alert_event_id
        )
        alerts = await _incidents.repository.get_linked_alerts(conn, incident["id"])
        assert len(alerts) > 0


# ─ Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
async def org_id(conn):
    """Create a test org."""
    org_row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."10_fct_orgs" LIMIT 1'
    )
    return org_row["id"] if org_row else "test-org"


@pytest.fixture
async def user_id(conn):
    """Create a test user."""
    user_row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."10_fct_users" LIMIT 1'
    )
    return user_row["id"] if user_row else "test-user"


@pytest.fixture
async def alert_event_id(conn, org_id):
    """Create a test alert event."""
    # This requires existing alerts infrastructure
    pass
