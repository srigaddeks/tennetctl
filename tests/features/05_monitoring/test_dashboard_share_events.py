"""Tests for dashboard share events."""

import pytest

from backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.repository import (
    count_recent_passphrase_failures,
    create_internal_grant,
    list_events,
    record_event,
)


class TestEventRecording:
    """Test event recording and timeline."""

    @pytest.mark.asyncio
    async def test_record_granted_event(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Record a grant event."""
        granted_user_id = "granted-user-uuid"

        share_id = await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            granted_user_id,
            None,
        )

        # Verify event was recorded by grant creation
        events = await list_events(test_conn, share_id)
        assert len(events) > 0

        granted_events = [e for e in events if e["kind_code"] == "granted"]
        assert len(granted_events) == 1
        assert granted_events[0]["actor_user_id"] == test_user_id

    @pytest.mark.asyncio
    async def test_record_viewed_event(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Record a view event."""
        granted_user_id = "viewer-user-uuid"

        share_id = await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            granted_user_id,
            None,
        )

        # Record a view
        await record_event(
            test_conn,
            share_id=share_id,
            kind_id=2,  # viewed
            actor_user_id=None,
            viewer_email=None,
            viewer_ip="192.0.2.1",
            viewer_ua="Mozilla/5.0",
            payload={"source": "test"},
        )

        events = await list_events(test_conn, share_id)
        viewed_events = [e for e in events if e["kind_code"] == "viewed"]
        assert len(viewed_events) == 1
        assert viewed_events[0]["viewer_ip"] == "192.0.2.1"

    @pytest.mark.asyncio
    async def test_events_ordered_by_time(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Events are returned in reverse chronological order."""
        granted_user_id = "test-user-uuid"

        share_id = await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            granted_user_id,
            None,
        )

        # Record multiple events
        for i in range(3):
            await record_event(
                test_conn,
                share_id=share_id,
                kind_id=2,  # viewed
                actor_user_id=None,
                viewer_email=None,
                viewer_ip=f"192.0.2.{i}",
                viewer_ua="Mozilla",
                payload={},
            )

        events = await list_events(test_conn, share_id)

        # Most recent should be first
        for i in range(len(events) - 1):
            assert events[i]["occurred_at"] >= events[i + 1]["occurred_at"]

    @pytest.mark.asyncio
    async def test_count_passphrase_failures(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Count recent passphrase failures."""
        share_id = await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            "other-user",
            None,
        )

        viewer_ip = "192.0.2.10"

        # Record 3 failures
        for i in range(3):
            await record_event(
                test_conn,
                share_id=share_id,
                kind_id=7,  # passphrase_failed
                actor_user_id=None,
                viewer_email=None,
                viewer_ip=viewer_ip,
                viewer_ua="Mozilla",
                payload={},
            )

        count = await count_recent_passphrase_failures(test_conn, share_id, viewer_ip, 10)
        assert count >= 3

    @pytest.mark.asyncio
    async def test_count_failures_different_ip(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Failures from different IPs are tracked separately."""
        share_id = await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            "other-user",
            None,
        )

        ip1 = "192.0.2.10"
        ip2 = "192.0.2.20"

        # Record 3 failures from IP1
        for i in range(3):
            await record_event(
                test_conn,
                share_id=share_id,
                kind_id=7,  # passphrase_failed
                actor_user_id=None,
                viewer_email=None,
                viewer_ip=ip1,
                viewer_ua="Mozilla",
                payload={},
            )

        # Record 1 failure from IP2
        await record_event(
            test_conn,
            share_id=share_id,
            kind_id=7,
            actor_user_id=None,
            viewer_email=None,
            viewer_ip=ip2,
            viewer_ua="Mozilla",
            payload={},
        )

        count_ip1 = await count_recent_passphrase_failures(test_conn, share_id, ip1, 10)
        count_ip2 = await count_recent_passphrase_failures(test_conn, share_id, ip2, 10)

        assert count_ip1 >= 3
        assert count_ip2 == 1
