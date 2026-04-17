"""Log redaction engine.

Loads rules from v_monitoring_redaction_rules; caches compiled regex; applies
rules in priority order. Immutable — returns a new LogRecord dict.

Two rule kinds:
- regex: pattern is a Python regex. If applies_to in (body, both), substitute
  on body. If applies_to in (attribute, both), substitute on any string-valued
  attribute (keys unchanged; values mutated to replacement).
- denylist: pattern is an attribute-key match (case-insensitive, substring).
  If applies_to in (attribute, both), drop any attribute whose key contains
  the pattern. applies_to=body is a no-op for denylist.

Cache TTL is 60s. Engine is safe for concurrent reads — load() is a full
replacement of the internal rule list + regex cache.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger("tennetctl.monitoring.redaction")

_CACHE_TTL_S = 60.0


@dataclass(frozen=True)
class RedactionRule:
    id: int
    code: str
    pattern: str
    applies_to: str       # body | attribute | both
    kind: str             # regex | denylist
    replacement: str
    priority: int
    compiled: Any = None  # re.Pattern for regex kind, lowered str for denylist


@dataclass(frozen=True)
class RedactionResult:
    """Return value from apply() — a new LogRecord dict + extra dropped count."""
    record: dict[str, Any] = field(default_factory=dict)
    extra_dropped: int = 0


def _compile_rule(row: dict[str, Any]) -> RedactionRule | None:
    """Compile one row from the view into a RedactionRule; None on bad regex."""
    kind = row["kind"]
    pattern = row["pattern"]
    compiled: Any
    if kind == "regex":
        try:
            compiled = re.compile(pattern)
        except re.error as e:
            logger.warning(
                "redaction: skipping rule code=%s — invalid regex: %s",
                row.get("code"), e,
            )
            return None
    elif kind == "denylist":
        compiled = pattern.lower()
    else:
        logger.warning("redaction: skipping rule code=%s — unknown kind %r", row.get("code"), kind)
        return None

    return RedactionRule(
        id=int(row["id"]),
        code=str(row["code"]),
        pattern=pattern,
        applies_to=str(row["applies_to"]),
        kind=kind,
        replacement=str(row["replacement"]),
        priority=int(row["priority"]),
        compiled=compiled,
    )


class RedactionEngine:
    """Thread-safe (single-process async) redaction engine.

    ``load(pool)`` refreshes rules; ``apply(record)`` returns a new dict with
    body/attributes rewritten. Designed to run inside the logs consumer hot
    path — ``apply`` does no DB I/O.
    """

    def __init__(self) -> None:
        self._rules: list[RedactionRule] = []
        self._loaded_at: float = 0.0

    @property
    def rules(self) -> list[RedactionRule]:
        return list(self._rules)

    async def load(self, pool: Any) -> int:
        """Load rules from DB. Returns number of active rules loaded."""
        sql = (
            'SELECT id, code, pattern, applies_to, kind, replacement, priority '
            'FROM "05_monitoring"."v_monitoring_redaction_rules" '
            'WHERE is_active = TRUE '
            'ORDER BY priority ASC, id ASC'
        )
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql)
        compiled: list[RedactionRule] = []
        for r in rows:
            rule = _compile_rule(dict(r))
            if rule is not None:
                compiled.append(rule)
        self._rules = compiled
        self._loaded_at = time.monotonic()
        logger.info("redaction: loaded %d rules", len(compiled))
        return len(compiled)

    async def maybe_reload(self, pool: Any) -> None:
        """Reload rules if cache TTL has expired."""
        if time.monotonic() - self._loaded_at >= _CACHE_TTL_S:
            try:
                await self.load(pool)
            except Exception as e:  # noqa: BLE001
                logger.warning("redaction: reload failed, keeping cached rules: %s", e)

    def set_rules(self, rules: list[RedactionRule]) -> None:
        """For tests — inject pre-compiled rules without hitting the DB."""
        self._rules = list(rules)
        self._loaded_at = time.monotonic()

    def apply(self, record: dict[str, Any]) -> RedactionResult:
        """Apply all rules. Returns new RedactionResult; input is not mutated."""
        new_body: str = record.get("body", "") or ""
        attrs_in: dict[str, Any] = dict(record.get("attributes") or {})
        new_attrs: dict[str, Any] = {}
        dropped = 0

        denylist_rules = [r for r in self._rules if r.kind == "denylist" and r.applies_to in ("attribute", "both")]
        regex_body_rules = [r for r in self._rules if r.kind == "regex" and r.applies_to in ("body", "both")]
        regex_attr_rules = [r for r in self._rules if r.kind == "regex" and r.applies_to in ("attribute", "both")]

        # Apply regex rules to body.
        for rule in regex_body_rules:
            new_body = rule.compiled.sub(rule.replacement, new_body)

        # Filter + rewrite attributes.
        for key, value in attrs_in.items():
            key_lower = key.lower() if isinstance(key, str) else ""
            # Denylist: drop if any rule matches the key.
            if any(rule.compiled in key_lower for rule in denylist_rules):
                dropped += 1
                continue
            # Regex: substitute on string-valued attributes only.
            if isinstance(value, str):
                new_value = value
                for rule in regex_attr_rules:
                    new_value = rule.compiled.sub(rule.replacement, new_value)
                new_attrs[key] = new_value
            else:
                new_attrs[key] = value

        new_record = dict(record)
        new_record["body"] = new_body
        new_record["attributes"] = new_attrs
        existing_dropped = int(new_record.get("dropped_attributes_count") or 0)
        new_record["dropped_attributes_count"] = existing_dropped + dropped
        return RedactionResult(record=new_record, extra_dropped=dropped)


__all__ = ["RedactionEngine", "RedactionRule", "RedactionResult"]
