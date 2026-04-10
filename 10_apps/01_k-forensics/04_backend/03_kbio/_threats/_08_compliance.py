"""Compliance and AML threat types."""
from __future__ import annotations

from ._registry import threat_type


@threat_type(
    code="aml-structuring",
    name="AML: Structuring Pattern",
    description="Monitors sessions with transaction structuring patterns.",
    category="compliance",
    severity=75,
    default_action="monitor",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.structuring_pattern", "op": "==", "value": True},
        ],
        "action": "monitor",
        "reason_template": "AML: structuring pattern detected",
    },
    default_config={},
    reason_template="AML: structuring pattern detected",
    tags=["compliance", "aml"],
)
def aml_structuring():
    pass


@threat_type(
    code="aml-rapid-movement",
    name="AML: Rapid Fund Movement",
    description="Challenges rapid fund movement on dormant accounts.",
    category="compliance",
    severity=70,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.rapid_fund_movement", "op": "==", "value": True},
            {"field": "signals.dormant_account", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "AML: rapid fund movement on dormant account",
    },
    default_config={},
    reason_template="AML: rapid fund movement on dormant account",
    tags=["compliance", "aml"],
)
def aml_rapid_movement():
    pass


@threat_type(
    code="aml-round-amounts",
    name="AML: Round Amount Pattern",
    description="Monitors sessions with round amount patterns and unusual transaction activity.",
    category="compliance",
    severity=50,
    default_action="monitor",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.round_amount_pattern", "op": "==", "value": True},
            {"field": "signals.unusual_transaction_pattern", "op": "==", "value": True},
        ],
        "action": "monitor",
        "reason_template": "AML: round amounts with unusual transaction pattern",
    },
    default_config={},
    reason_template="AML: round amounts with unusual transaction pattern",
    tags=["compliance", "aml"],
)
def aml_round_amounts():
    pass


@threat_type(
    code="sanctions-violation",
    name="Sanctions: Violation",
    description="Blocks sessions originating from sanctioned countries.",
    category="compliance",
    severity=95,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.sanctions_country", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Sanctions: session from sanctioned country",
    },
    default_config={},
    reason_template="Sanctions: session from sanctioned country",
    tags=["compliance", "sanctions", "critical"],
)
def sanctions_violation():
    pass


@threat_type(
    code="compliance-high-risk",
    name="Compliance: High Risk Jurisdiction",
    description="Monitors sessions from high-risk jurisdictions with unusual transaction patterns.",
    category="compliance",
    severity=60,
    default_action="monitor",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.high_risk_jurisdiction", "op": "==", "value": True},
            {"field": "signals.unusual_transaction_pattern", "op": "==", "value": True},
        ],
        "action": "monitor",
        "reason_template": "Compliance: high-risk jurisdiction with unusual transactions",
    },
    default_config={},
    reason_template="Compliance: high-risk jurisdiction with unusual transactions",
    tags=["compliance", "jurisdiction"],
)
def compliance_high_risk():
    pass
