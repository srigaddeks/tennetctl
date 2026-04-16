from __future__ import annotations

import re
from typing import Mapping


POLICY_CONTAINER_CODE_PROPERTY = "policy_container_code"
POLICY_CONTAINER_NAME_PROPERTY = "policy_container_name"

_POLICY_CONTAINER_CODE_PATTERN = re.compile(r"^[a-z0-9_]{2,80}$")


def extract_policy_container(
    properties: Mapping[str, str] | None,
) -> tuple[str | None, str | None]:
    if not properties:
        return None, None
    return (
        _clean_value(properties.get(POLICY_CONTAINER_CODE_PROPERTY)),
        _clean_value(properties.get(POLICY_CONTAINER_NAME_PROPERTY)),
    )


def normalize_policy_container_properties(
    properties: Mapping[str, str] | None,
    *,
    required: bool,
) -> dict[str, str]:
    normalized = dict(properties or {})
    code, name = extract_policy_container(normalized)

    if name and not code:
        code = slugify_policy_container(name)
    if code and not name:
        name = _label_from_code(code)
    if not code and not name:
        normalized.pop(POLICY_CONTAINER_CODE_PROPERTY, None)
        normalized.pop(POLICY_CONTAINER_NAME_PROPERTY, None)

    if required and (not code or not name):
        raise ValueError("Policy container selection is required.")
    if code and not _POLICY_CONTAINER_CODE_PATTERN.fullmatch(code):
        raise ValueError(
            "Policy container code must use 2-80 lowercase letters, numbers, or underscores."
        )
    if (code is None) != (name is None):
        raise ValueError("Policy container code and name must be provided together.")

    if code and name:
        normalized[POLICY_CONTAINER_CODE_PROPERTY] = code
        normalized[POLICY_CONTAINER_NAME_PROPERTY] = name

    return normalized


def slugify_policy_container(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _label_from_code(code: str) -> str:
    return " ".join(part.capitalize() for part in code.split("_"))
