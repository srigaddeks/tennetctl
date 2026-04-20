"""Tests for incident grouping rules and dedup strategies."""

import pytest
import json
from importlib import import_module

_incidents = import_module("backend.02_features.05_monitoring.sub_features.10_incidents")
_grouper = import_module("backend.02_features.05_monitoring.sub_features.10_incidents.grouper")


class TestGroupingRuleCreation:
    """Test creating and retrieving grouping rules."""

    async def test_create_grouping_rule(self, conn, rule_id):
        """Create grouping rule with fingerprint strategy."""
        await _incidents.repository.upsert_grouping_rule(
            conn,
            rule_id=rule_id,
            dedup_strategy="fingerprint",
            group_by=[],
            group_window_seconds=300,
            custom_template=None,
            is_active=True,
        )
        rule = await _incidents.repository.get_grouping_rule(conn, rule_id)
        assert rule is not None
        assert rule["dedup_strategy"] == "fingerprint"
        assert rule["group_window_seconds"] == 300

    async def test_update_grouping_rule(self, conn, rule_id):
        """Update existing grouping rule."""
        await _incidents.repository.upsert_grouping_rule(
            conn,
            rule_id=rule_id,
            dedup_strategy="label_set",
            group_by=["service", "env"],
            group_window_seconds=600,
        )
        rule = await _incidents.repository.get_grouping_rule(conn, rule_id)
        assert rule["dedup_strategy"] == "label_set"
        assert rule["group_by"] == ["service", "env"]
        assert rule["group_window_seconds"] == 600

    async def test_disable_grouping_rule(self, conn, rule_id):
        """Disable grouping rule."""
        await _incidents.repository.upsert_grouping_rule(
            conn,
            rule_id=rule_id,
            dedup_strategy="fingerprint",
            is_active=False,
        )
        rule = await _incidents.repository.get_grouping_rule(conn, rule_id)
        assert rule["is_active"] is False


class TestGroupKeyComputation:
    """Test group key computation with different strategies."""

    def test_compute_group_key_fingerprint(self):
        """Compute group key with fingerprint strategy."""
        rule_id = "rule-1"
        fp = "abc123"
        labels = {"host": "web-1", "service": "api"}
        grouping_rule = {
            "dedup_strategy": "fingerprint",
            "is_active": True,
        }
        key1 = _grouper.compute_group_key(rule_id, fp, labels, grouping_rule)
        key2 = _grouper.compute_group_key(rule_id, fp, labels, grouping_rule)
        # Same inputs should produce same key
        assert key1 == key2
        # Different fingerprint should produce different key
        key3 = _grouper.compute_group_key(rule_id, "def456", labels, grouping_rule)
        assert key3 != key1

    def test_compute_group_key_label_set(self):
        """Compute group key with label_set strategy."""
        rule_id = "rule-1"
        fp = "abc123"
        grouping_rule = {
            "dedup_strategy": "label_set",
            "group_by": ["service", "env"],
            "is_active": True,
        }
        labels1 = {"service": "api", "env": "prod", "host": "web-1"}
        labels2 = {"service": "api", "env": "prod", "host": "web-2"}
        # Same service+env should produce same key (host is ignored)
        key1 = _grouper.compute_group_key(rule_id, fp, labels1, grouping_rule)
        key2 = _grouper.compute_group_key(rule_id, fp, labels2, grouping_rule)
        assert key1 == key2

        # Different env should produce different key
        labels3 = {"service": "api", "env": "staging", "host": "web-1"}
        key3 = _grouper.compute_group_key(rule_id, fp, labels3, grouping_rule)
        assert key3 != key1

    def test_compute_group_key_custom_template(self):
        """Compute group key with custom Jinja2 template."""
        rule_id = "rule-1"
        fp = "abc123"
        grouping_rule = {
            "dedup_strategy": "custom_key",
            "custom_template": "{{ rule_id }}-{{ labels.service }}",
            "is_active": True,
        }
        labels = {"service": "api"}
        key = _grouper.compute_group_key(rule_id, fp, labels, grouping_rule)
        # Should be deterministic
        assert isinstance(key, str)
        assert len(key) == 64  # sha256 hex

    def test_compute_group_key_default_no_grouping(self):
        """Default to fingerprint when no grouping rule."""
        rule_id = "rule-1"
        fp = "abc123"
        labels = {"host": "web-1"}
        key = _grouper.compute_group_key(rule_id, fp, labels, grouping_rule=None)
        # Should use fingerprint strategy
        assert isinstance(key, str)
        assert len(key) == 64

    def test_compute_group_key_inactive_rule(self):
        """Inactive grouping rule falls back to fingerprint."""
        rule_id = "rule-1"
        fp = "abc123"
        labels = {"service": "api"}
        grouping_rule = {
            "dedup_strategy": "label_set",
            "group_by": ["service"],
            "is_active": False,  # Disabled
        }
        key1 = _grouper.compute_group_key(rule_id, fp, labels, grouping_rule)
        # Should use fingerprint despite label_set config
        key2 = _grouper.compute_group_key(
            rule_id,
            fp,
            labels,
            {"dedup_strategy": "fingerprint", "is_active": True},
        )
        assert key1 == key2


class TestGroupKeyCollisions:
    """Test group key determinism and collision handling."""

    def test_group_key_deterministic(self):
        """Group key computation is deterministic."""
        rule_id = "rule-1"
        fp = "abc123"
        labels = {"a": "1", "b": "2", "c": "3"}
        grouping_rule = {"dedup_strategy": "fingerprint", "is_active": True}

        keys = [
            _grouper.compute_group_key(rule_id, fp, labels, grouping_rule)
            for _ in range(5)
        ]
        # All keys should be identical
        assert len(set(keys)) == 1

    def test_group_key_order_independent(self):
        """Label order shouldn't affect group key for label_set."""
        rule_id = "rule-1"
        fp = "abc123"
        grouping_rule = {
            "dedup_strategy": "label_set",
            "group_by": ["service", "env"],
            "is_active": True,
        }
        labels = {"service": "api", "env": "prod", "host": "web-1"}
        # Since we sort group_by keys, this should be deterministic
        key1 = _grouper.compute_group_key(rule_id, fp, labels, grouping_rule)

        grouping_rule["group_by"] = ["env", "service"]  # Reversed order
        key2 = _grouper.compute_group_key(rule_id, fp, labels, grouping_rule)
        # Same labels, should produce same key
        assert key1 == key2


# ─ Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
async def rule_id(conn, org_id):
    """Create a test alert rule."""
    rule_row = await conn.fetchrow(
        'SELECT id FROM "05_monitoring"."12_fct_monitoring_alert_rules" '
        'WHERE org_id = $1 LIMIT 1',
        org_id,
    )
    if rule_row:
        return rule_row["id"]
    # Create a dummy rule if needed
    from importlib import import_module
    _core_id = import_module("backend.01_core.id")
    rule_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."12_fct_monitoring_alert_rules"
            (id, org_id, name, condition, dsl, target, severity_id, notify_template_key, created_at, updated_at)
        VALUES ($1, $2, 'Test Rule', '{}', '{}', 'metrics', 1, 'default', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        rule_id, org_id,
    )
    return rule_id


@pytest.fixture
async def org_id(conn):
    """Create a test org."""
    org_row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."10_fct_orgs" LIMIT 1'
    )
    return org_row["id"] if org_row else "test-org"
