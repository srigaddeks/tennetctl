"""Social engineering threat types."""
from __future__ import annotations

from ._registry import threat_type


@threat_type(
    code="se-coercion",
    name="Social Engineering: Coercion Detected",
    description="Challenges sessions where coercion signals are detected with frequent rhythm breaks.",
    category="social_engineering",
    severity=75,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.coercion_detected", "op": "==", "value": True},
            {"field": "signals.rhythm_breaks_frequent", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "Social engineering: coercion with rhythm breaks",
    },
    default_config={},
    reason_template="Social engineering: coercion with rhythm breaks",
    tags=["social_engineering", "coercion"],
)
def se_coercion():
    pass


@threat_type(
    code="se-coached-transfer",
    name="Social Engineering: Coached Transfer",
    description="Blocks sessions with coached behavior combined with payment method changes.",
    category="social_engineering",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.coached_behavior", "op": "==", "value": True},
            {"field": "signals.payment_method_change", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Social engineering: coached transfer with payment change",
    },
    default_config={},
    reason_template="Social engineering: coached transfer with payment change",
    tags=["social_engineering", "fraud", "critical"],
)
def se_coached_transfer():
    pass


@threat_type(
    code="se-hesitation-critical",
    name="Social Engineering: Hesitation on Critical Action",
    description="Challenges sessions with hesitation before high-value actions with low trust.",
    category="social_engineering",
    severity=70,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.hesitation_before_action", "op": "==", "value": True},
            {"field": "signals.high_value_action_low_trust", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "Social engineering: hesitation before critical action",
    },
    default_config={},
    reason_template="Social engineering: hesitation before critical action",
    tags=["social_engineering"],
)
def se_hesitation_critical():
    pass


@threat_type(
    code="se-re-entry-pattern",
    name="Social Engineering: Re-entry Pattern",
    description="Monitors sessions with repeated re-entry and heavy credential backspacing.",
    category="social_engineering",
    severity=50,
    default_action="monitor",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.re_entry_pattern", "op": "==", "value": True},
            {"field": "signals.credential_backspace_heavy", "op": "==", "value": True},
        ],
        "action": "monitor",
        "reason_template": "Social engineering: re-entry pattern with heavy backspacing",
    },
    default_config={},
    reason_template="Social engineering: re-entry pattern with heavy backspacing",
    tags=["social_engineering"],
)
def se_re_entry_pattern():
    pass


@threat_type(
    code="se-duress-transfer",
    name="Social Engineering: Duress Transfer",
    description="Blocks sessions with coercion, high cognitive load, and new beneficiary addition.",
    category="social_engineering",
    severity=90,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.coercion_detected", "op": "==", "value": True},
            {"field": "signals.high_cognitive_load", "op": "==", "value": True},
            {"field": "signals.beneficiary_add_new_session", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Social engineering: duress transfer with new beneficiary",
    },
    default_config={},
    reason_template="Social engineering: duress transfer with new beneficiary",
    tags=["social_engineering", "fraud", "critical"],
)
def se_duress_transfer():
    pass


@threat_type(
    code="se-impersonation-call",
    name="Social Engineering: Impersonation Call",
    description="Challenges sessions with impersonation, hesitation, and frequent rhythm breaks.",
    category="social_engineering",
    severity=70,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.impersonation_detected", "op": "==", "value": True},
            {"field": "signals.hesitation_before_action", "op": "==", "value": True},
            {"field": "signals.rhythm_breaks_frequent", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "Social engineering: impersonation with hesitation and rhythm breaks",
    },
    default_config={},
    reason_template="Social engineering: impersonation with hesitation and rhythm breaks",
    tags=["social_engineering", "impersonation"],
)
def se_impersonation_call():
    pass
