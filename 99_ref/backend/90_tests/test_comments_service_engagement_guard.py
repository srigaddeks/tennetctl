from __future__ import annotations

import unittest
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock

import asyncpg


service_module = import_module("backend.08_comments.01_comments.service")
schemas_module = import_module("backend.08_comments.01_comments.schemas")
cache_module = import_module("backend.01_core.cache")
errors_module = import_module("backend.01_core.errors")

ValidationError = errors_module.ValidationError


class _TransactionContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeDatabasePool:
    def transaction(self):
        return _TransactionContext()


class CommentServiceEngagementGuardTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_comment_returns_validation_error_for_stale_entity_constraint(self) -> None:
        service = service_module.CommentService(
            settings=SimpleNamespace(notification_enabled=False),
            database_pool=_FakeDatabasePool(),
            cache=cache_module.NullCacheManager(),
        )
        service._repository = SimpleNamespace(
            validate_user_ids=AsyncMock(return_value={"af88f921-2e07-48aa-a3e5-c556a2b2c223"}),
            create_comment=AsyncMock(side_effect=asyncpg.CheckViolationError("entity_type constraint mismatch")),
        )

        request = schemas_module.CreateCommentRequest(
            entity_type="engagement",
            entity_id="2c21824c-f57c-4f34-aac9-6d61cec9baae",
            content="@[test123@kreesalis.com](af88f921-2e07-48aa-a3e5-c556a2b2c223)\n\nHey admin",
            content_format="markdown",
            visibility="external",
        )

        with self.assertRaises(ValidationError) as exc:
            await service.create_comment(
                user_id="ae3a11dc-7b84-4555-8226-45ab48b70082",
                tenant_key="default",
                request=request,
                portal_mode=None,
            )

        self.assertIn("not enabled in the current database schema", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
