"""Tests for dashboard access control."""

import pytest

from backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.access import can_view
from backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.repository import (
    create_internal_grant,
)


class TestAccessControl:
    """Test access control for dashboard viewing."""

    @pytest.mark.asyncio
    async def test_owner_can_view(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Dashboard owner can always view."""
        can_view_result = await can_view(test_conn, test_dashboard_id, test_user_id)
        assert can_view_result is True

    @pytest.mark.asyncio
    async def test_non_owner_cannot_view_without_grant(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Non-owner without grant cannot view."""
        other_user_id = "other-user-uuid"
        can_view_result = await can_view(test_conn, test_dashboard_id, other_user_id)
        assert can_view_result is False

    @pytest.mark.asyncio
    async def test_granted_user_can_view(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """User with internal grant can view."""
        granted_user_id = "granted-user-uuid"

        # Create grant
        await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            granted_user_id,
            expires_at=None,
        )

        # Granted user can view
        can_view_result = await can_view(test_conn, test_dashboard_id, granted_user_id)
        assert can_view_result is True

    @pytest.mark.asyncio
    async def test_revoked_grant_cannot_view(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """User with revoked grant cannot view."""
        from backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.repository import (
            revoke_share,
        )

        granted_user_id = "revoked-user-uuid"

        # Create grant
        share_id = await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            granted_user_id,
            expires_at=None,
        )

        # Revoke it
        await revoke_share(test_conn, share_id, test_user_id)

        # Granted user cannot view
        can_view_result = await can_view(test_conn, test_dashboard_id, granted_user_id)
        assert can_view_result is False

    @pytest.mark.asyncio
    async def test_expired_grant_cannot_view(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """User with expired grant cannot view."""
        from datetime import datetime, timedelta

        granted_user_id = "expired-user-uuid"
        expires_at = datetime.utcnow() - timedelta(hours=1)  # Already expired

        # Create grant with past expiration
        await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            granted_user_id,
            expires_at,
        )

        # Granted user cannot view (grant expired)
        can_view_result = await can_view(test_conn, test_dashboard_id, granted_user_id)
        assert can_view_result is False
