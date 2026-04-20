"""Tests for dashboard share CRUD operations."""

import pytest
from datetime import datetime, timedelta

from backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.repository import (
    create_internal_grant,
    create_public_token_grant,
    get_share,
    list_shares,
    revoke_share,
    soft_delete_share,
)
from backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.token import (
    hash_token,
    mint,
)


class TestInternalShareCRUD:
    """Test internal user grant creation and retrieval."""

    @pytest.mark.asyncio
    async def test_create_internal_grant(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Create an internal user grant."""
        granted_to_user_id = "test-user-2-uuid"

        share_id = await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            granted_to_user_id,
            expires_at=None,
        )

        assert share_id is not None
        share = await get_share(test_conn, share_id)
        assert share is not None
        assert share["scope_code"] == "internal_user"
        assert share["granted_to_user_id"] == granted_to_user_id

    @pytest.mark.asyncio
    async def test_create_grant_with_expiry(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Create internal grant with expiration."""
        expires_at = datetime.utcnow() + timedelta(days=7)
        granted_to_user_id = "test-user-3-uuid"

        share_id = await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            granted_to_user_id,
            expires_at,
        )

        share = await get_share(test_conn, share_id)
        assert share["expires_at"] is not None
        assert share["status"] == "active"

    @pytest.mark.asyncio
    async def test_revoke_grant(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Revoke a grant."""
        granted_to_user_id = "test-user-4-uuid"

        share_id = await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            granted_to_user_id,
            None,
        )

        await revoke_share(test_conn, share_id, test_user_id)

        share = await get_share(test_conn, share_id)
        assert share["status"] == "revoked"
        assert share["revoked_at"] is not None

    @pytest.mark.asyncio
    async def test_list_shares(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """List shares for a dashboard."""
        # Create 3 grants
        for i in range(3):
            await create_internal_grant(
                test_conn,
                test_dashboard_id,
                test_org_id,
                test_user_id,
                f"test-user-{i}-uuid",
                None,
            )

        shares = await list_shares(test_conn, test_dashboard_id)
        assert len(shares) >= 3


class TestPublicTokenCRUD:
    """Test public token share creation and retrieval."""

    @pytest.mark.asyncio
    async def test_create_public_token_grant(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Create a public token share."""
        token = mint(test_dashboard_id, 9999999999, 1, b"test-secret-32-bytes-minimum-")
        token_hash_val = hash_token(token)

        share_id = await create_public_token_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            expires_at=None,
            recipient_email="user@example.com",
            token_hash=token_hash_val,
            key_version=1,
            passphrase_hash=None,
        )

        assert share_id is not None
        share = await get_share(test_conn, share_id)
        assert share is not None
        assert share["scope_code"] == "public_token"
        assert share["recipient_email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_create_public_token_with_passphrase(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Create a public token with passphrase."""
        token = mint(test_dashboard_id, 9999999999, 1, b"test-secret-32-bytes-minimum-")
        token_hash_val = hash_token(token)

        import bcrypt

        passphrase_hash = bcrypt.hashpw(b"hunter2", bcrypt.gensalt()).decode("utf-8")

        share_id = await create_public_token_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            expires_at=None,
            recipient_email=None,
            token_hash=token_hash_val,
            key_version=1,
            passphrase_hash=passphrase_hash,
        )

        share = await get_share(test_conn, share_id)
        assert share["has_passphrase"] is True

    @pytest.mark.asyncio
    async def test_soft_delete_share(self, test_conn, test_org_id, test_user_id, test_dashboard_id):
        """Soft-delete a share."""
        granted_to_user_id = "test-user-5-uuid"

        share_id = await create_internal_grant(
            test_conn,
            test_dashboard_id,
            test_org_id,
            test_user_id,
            granted_to_user_id,
            None,
        )

        await soft_delete_share(test_conn, share_id)

        # Share should be hidden from list
        shares = await list_shares(test_conn, test_dashboard_id)
        share_ids = [s["id"] for s in shares]
        assert share_id not in share_ids
