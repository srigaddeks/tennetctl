"""Unit tests for RedactionEngine — no DB required."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_red: Any = import_module("backend.02_features.05_monitoring.workers.redaction")
RedactionEngine = _red.RedactionEngine
RedactionRule = _red.RedactionRule
_compile_rule = _red._compile_rule


def _rule(code: str, pattern: str, kind: str, applies_to: str, repl: str = "[REDACTED]", priority: int = 100) -> Any:
    row = {
        "id": abs(hash(code)) % 10_000,
        "code": code,
        "pattern": pattern,
        "applies_to": applies_to,
        "kind": kind,
        "replacement": repl,
        "priority": priority,
    }
    return _compile_rule(row)


def test_credit_card_redaction_in_body():
    eng = RedactionEngine()
    eng.set_rules([_rule("cc", r"\b(?:\d[ -]*?){13,19}\b", "regex", "both", "[REDACTED_CC]", priority=10)])
    rec = {"body": "Charged 4111 1111 1111 1111 today", "attributes": {}}
    out = eng.apply(rec).record
    assert "4111" not in out["body"]
    assert "[REDACTED_CC]" in out["body"]


def test_jwt_redaction_in_attribute_string_value():
    eng = RedactionEngine()
    jwt_re = r"eyJ[A-Za-z0-9\-_=]+\.eyJ[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_.+/=]*"
    eng.set_rules([_rule("jwt", jwt_re, "regex", "attribute", "[REDACTED_JWT]", priority=30)])
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.abc123"
    rec = {"body": "ok", "attributes": {"auth.header": f"Bearer {jwt}"}}
    out = eng.apply(rec).record
    assert jwt not in out["attributes"]["auth.header"]
    assert "[REDACTED_JWT]" in out["attributes"]["auth.header"]


def test_denylist_drops_password_attribute_and_increments_count():
    eng = RedactionEngine()
    eng.set_rules([_rule("deny_pwd", "password", "denylist", "attribute", priority=100)])
    rec = {
        "body": "hello",
        "attributes": {"password": "hunter2", "user": "alice"},
        "dropped_attributes_count": 0,
    }
    result = eng.apply(rec)
    out = result.record
    assert "password" not in out["attributes"]
    assert out["attributes"]["user"] == "alice"
    assert out["dropped_attributes_count"] == 1
    assert result.extra_dropped == 1


def test_multiple_rules_applied_in_priority_order():
    eng = RedactionEngine()
    rules = [
        _rule("cc", r"\d{4}-\d{4}-\d{4}-\d{4}", "regex", "body", "[CC]", priority=10),
        _rule("jwt", r"eyJ\w+\.\w+\.\w+", "regex", "body", "[JWT]", priority=20),
    ]
    eng.set_rules(rules)
    rec = {"body": "card=1111-2222-3333-4444 token=eyJabc.eyJdef.xyz", "attributes": {}}
    out = eng.apply(rec).record
    assert "[CC]" in out["body"]
    assert "[JWT]" in out["body"]


def test_original_record_is_not_mutated():
    eng = RedactionEngine()
    eng.set_rules([_rule("deny", "secret", "denylist", "attribute")])
    rec = {"body": "x", "attributes": {"secret": "v"}, "dropped_attributes_count": 0}
    original_attrs = rec["attributes"]
    out = eng.apply(rec).record
    # Original must be unchanged.
    assert "secret" in rec["attributes"]
    assert rec["attributes"] is original_attrs
    assert rec["dropped_attributes_count"] == 0
    # Output is a new dict.
    assert "secret" not in out["attributes"]
    assert out is not rec


def test_no_rules_loaded_passthrough():
    eng = RedactionEngine()
    rec = {"body": "password=hunter2", "attributes": {"password": "x"}}
    out = eng.apply(rec).record
    assert out["body"] == "password=hunter2"
    assert out["attributes"] == {"password": "x"}


def test_invalid_regex_is_skipped():
    bad = _compile_rule({
        "id": 1, "code": "bad", "pattern": "[unclosed",
        "applies_to": "body", "kind": "regex", "replacement": "", "priority": 1,
    })
    assert bad is None


def test_denylist_substring_match_on_attribute_key():
    eng = RedactionEngine()
    eng.set_rules([_rule("deny_auth", "authorization", "denylist", "attribute")])
    rec = {"body": "x", "attributes": {"HTTP.Authorization": "Bearer abc", "ok": "y"}}
    out = eng.apply(rec).record
    assert "HTTP.Authorization" not in out["attributes"]
    assert out["attributes"]["ok"] == "y"
