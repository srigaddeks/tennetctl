from __future__ import annotations

from enum import StrEnum


class FrameworkAuditEventType(StrEnum):
    FRAMEWORK_CREATED = "framework_created"
    FRAMEWORK_UPDATED = "framework_updated"
    FRAMEWORK_DELETED = "framework_deleted"
    VERSION_CREATED = "version_created"
    VERSION_PUBLISHED = "version_published"
    VERSION_DEPRECATED = "version_deprecated"
    REQUIREMENT_CREATED = "requirement_created"
    REQUIREMENT_UPDATED = "requirement_updated"
    REQUIREMENT_DELETED = "requirement_deleted"
    CONTROL_CREATED = "control_created"
    CONTROL_UPDATED = "control_updated"
    CONTROL_DELETED = "control_deleted"
    TEST_CREATED = "test_created"
    TEST_UPDATED = "test_updated"
    TEST_DELETED = "test_deleted"
    EVIDENCE_TEMPLATE_CREATED = "evidence_template_created"
    EVIDENCE_TEMPLATE_UPDATED = "evidence_template_updated"
    EVIDENCE_TEMPLATE_DELETED = "evidence_template_deleted"
    TEST_MAPPING_CREATED = "test_mapping_created"
    TEST_MAPPING_DELETED = "test_mapping_deleted"
    EQUIVALENCE_CREATED = "equivalence_created"
    EQUIVALENCE_DELETED = "equivalence_deleted"
    SETTING_UPDATED = "framework_setting_updated"
    SETTING_DELETED = "framework_setting_deleted"
