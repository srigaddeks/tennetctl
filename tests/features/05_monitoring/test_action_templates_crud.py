"""Tests for action template CRUD operations."""

import pytest
from datetime import datetime
from importlib import import_module
import asyncpg

_core_id = import_module("backend.01_core.id")


@pytest.fixture
async def action_templates_service(pool: asyncpg.Pool):
    """Provide ActionTemplateService with test database."""
    from backend.02_features.05_monitoring.sub_features.09_action_templates.service import (
        ActionTemplateService,
    )

    conn = await pool.acquire()
    try:
        service = ActionTemplateService(conn)
        yield service
    finally:
        await pool.release(conn)


class TestActionTemplateCRUD:
    """Test CRUD operations for action templates."""

    @pytest.mark.asyncio
    async def test_create_webhook_template(self, action_templates_service):
        """Test creating a webhook action template."""
        from backend.02_features.05_monitoring.sub_features.09_action_templates import schemas

        org_id = str(_core_id.uuid7())
        user_id = str(_core_id.uuid7())

        input_data = schemas.ActionTemplateCreate(
            name="Test Webhook",
            description="Test webhook template",
            kind="webhook",
            target_url="https://example.com/webhook",
            body_template='{"alert": "{{rule_name}}", "value": {{value}}}',
            headers_template={"X-Custom": "Header"},
            signing_secret_vault_ref="vault://secret/webhook",
            retry_policy={"max_attempts": 3, "base_seconds": 5, "max_seconds": 300},
            is_active=True,
        )

        result = await action_templates_service.create(org_id, user_id, input_data)

        assert result is not None
        assert result["id"]
        assert result["name"] == "Test Webhook"
        assert result["kind_code"] == "webhook"
        assert result["target_url"] == "https://example.com/webhook"
        assert result["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_email_template(self, action_templates_service):
        """Test creating an email action template."""
        from backend.02_features.05_monitoring.sub_features.09_action_templates import schemas

        org_id = str(_core_id.uuid7())
        user_id = str(_core_id.uuid7())

        input_data = schemas.ActionTemplateCreate(
            name="Test Email",
            kind="email",
            target_address="ops@example.com",
            body_template="""
{% block subject %}Alert: {{rule_name}}{% endblock %}
{% block text %}Value is {{value}}{% endblock %}
{% block html %}<p>Value is {{value}}</p>{% endblock %}
            """,
            is_active=True,
        )

        result = await action_templates_service.create(org_id, user_id, input_data)

        assert result["kind_code"] == "email"
        assert result["target_address"] == "ops@example.com"

    @pytest.mark.asyncio
    async def test_template_parse_error_at_create(self, action_templates_service):
        """Test that invalid Jinja2 syntax is caught at create-time."""
        from backend.02_features.05_monitoring.sub_features.09_action_templates import schemas
        from backend.01_core.response import DomainError

        org_id = str(_core_id.uuid7())
        user_id = str(_core_id.uuid7())

        input_data = schemas.ActionTemplateCreate(
            name="Bad Template",
            kind="webhook",
            target_url="https://example.com",
            body_template='{{unclosed_var',
            is_active=True,
        )

        with pytest.raises(DomainError) as exc_info:
            await action_templates_service.create(org_id, user_id, input_data)

        assert exc_info.value.code == "RENDER_PARSE_ERROR"

    @pytest.mark.asyncio
    async def test_update_template(self, action_templates_service):
        """Test updating an action template."""
        from backend.02_features.05_monitoring.sub_features.09_action_templates import schemas

        org_id = str(_core_id.uuid7())
        user_id = str(_core_id.uuid7())

        # Create
        create_input = schemas.ActionTemplateCreate(
            name="Original Name",
            kind="webhook",
            target_url="https://example.com",
            body_template='{"test": "{{var}}"}',
        )
        created = await action_templates_service.create(org_id, user_id, create_input)
        template_id = created["id"]

        # Update
        update_input = schemas.ActionTemplateUpdate(
            name="Updated Name",
            body_template='{"updated": "{{var}}"}',
        )
        updated = await action_templates_service.update(template_id, org_id, user_id, update_input)

        assert updated["name"] == "Updated Name"
        assert updated["id"] == template_id

    @pytest.mark.asyncio
    async def test_delete_template(self, action_templates_service):
        """Test soft-deleting an action template."""
        from backend.02_features.05_monitoring.sub_features.09_action_templates import schemas

        org_id = str(_core_id.uuid7())
        user_id = str(_core_id.uuid7())

        # Create
        create_input = schemas.ActionTemplateCreate(
            name="To Delete",
            kind="webhook",
            target_url="https://example.com",
            body_template='{}',
        )
        created = await action_templates_service.create(org_id, user_id, create_input)
        template_id = created["id"]

        # Delete
        await action_templates_service.delete(template_id, org_id, user_id)

        # Verify soft-delete (should not appear in get)
        result = await action_templates_service.repo.get_by_id(template_id, org_id)
        assert result is None


class TestActionTemplateValidation:
    """Test validation rules for action templates."""

    @pytest.mark.asyncio
    async def test_webhook_requires_target_url(self, action_templates_service):
        """Test that webhook kind requires target_url."""
        from backend.02_features.05_monitoring.sub_features.09_action_templates import schemas
        from backend.01_core.response import DomainError

        org_id = str(_core_id.uuid7())
        user_id = str(_core_id.uuid7())

        input_data = schemas.ActionTemplateCreate(
            name="Missing URL",
            kind="webhook",
            target_url=None,  # Missing!
            body_template='{}',
        )

        # Should fail at DB constraint level
        with pytest.raises(Exception):
            await action_templates_service.create(org_id, user_id, input_data)

    @pytest.mark.asyncio
    async def test_email_requires_target_address(self, action_templates_service):
        """Test that email kind requires target_address."""
        from backend.02_features.05_monitoring.sub_features.09_action_templates import schemas

        org_id = str(_core_id.uuid7())
        user_id = str(_core_id.uuid7())

        input_data = schemas.ActionTemplateCreate(
            name="Missing Address",
            kind="email",
            target_address=None,  # Missing!
            body_template='{}',
        )

        # Should fail at DB constraint level
        with pytest.raises(Exception):
            await action_templates_service.create(org_id, user_id, input_data)
