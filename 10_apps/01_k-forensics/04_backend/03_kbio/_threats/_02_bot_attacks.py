"""Bot attack threat types."""
from __future__ import annotations

from ._registry import threat_type


@threat_type(
    code="bot-high-confidence",
    name="Bot: High Confidence Detection",
    description="Blocks sessions identified as bots with high confidence.",
    category="bot_attacks",
    severity=95,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.is_bot_high_confidence", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Bot: high confidence bot detected",
    },
    default_config={},
    reason_template="Bot: high confidence bot detected",
    tags=["bot", "automation", "critical"],
)
def bot_high_confidence():
    pass


@threat_type(
    code="bot-medium-confidence",
    name="Bot: Medium Confidence Detection",
    description="Challenges sessions with bot signals but below high-confidence threshold.",
    category="bot_attacks",
    severity=70,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.is_bot", "op": "==", "value": True},
            {"field": "signals.is_bot_high_confidence", "op": "==", "value": False},
        ],
        "action": "challenge",
        "reason_template": "Bot: medium confidence bot detected",
    },
    default_config={},
    reason_template="Bot: medium confidence bot detected",
    tags=["bot", "automation"],
)
def bot_medium_confidence():
    pass


@threat_type(
    code="bot-headless",
    name="Bot: Headless Browser",
    description="Blocks sessions originating from headless browsers.",
    category="bot_attacks",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.headless_browser", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Bot: headless browser detected",
    },
    default_config={},
    reason_template="Bot: headless browser detected",
    tags=["bot", "automation"],
)
def bot_headless():
    pass


@threat_type(
    code="bot-automation-framework",
    name="Bot: Automation Framework",
    description="Blocks sessions using known automation frameworks.",
    category="bot_attacks",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.automation_framework", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Bot: automation framework detected",
    },
    default_config={},
    reason_template="Bot: automation framework detected",
    tags=["bot", "automation"],
)
def bot_automation_framework():
    pass


@threat_type(
    code="bot-replay",
    name="Bot: Replay Attack",
    description="Blocks sessions where replayed behavioral data is detected.",
    category="bot_attacks",
    severity=90,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.replay_attack", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Bot: replay attack detected",
    },
    default_config={},
    reason_template="Bot: replay attack detected",
    tags=["bot", "fraud", "critical"],
)
def bot_replay():
    pass


@threat_type(
    code="bot-impossible-timing",
    name="Bot: Impossible Keystroke Timing",
    description="Blocks sessions with impossible keystroke timing and zero variance dwell.",
    category="bot_attacks",
    severity=85,
    default_action="block",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.impossible_keystroke_timing", "op": "==", "value": True},
            {"field": "signals.zero_variance_dwell", "op": "==", "value": True},
        ],
        "action": "block",
        "reason_template": "Bot: impossible keystroke timing with zero variance",
    },
    default_config={},
    reason_template="Bot: impossible keystroke timing with zero variance",
    tags=["bot", "keystroke"],
)
def bot_impossible_timing():
    pass


@threat_type(
    code="bot-linear-pointer",
    name="Bot: Linear Pointer Movement",
    description="Challenges sessions with linear pointer movement and uniform batch timing.",
    category="bot_attacks",
    severity=70,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.linear_pointer_movement", "op": "==", "value": True},
            {"field": "signals.uniform_batch_timing", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "Bot: linear pointer movement with uniform timing",
    },
    default_config={},
    reason_template="Bot: linear pointer movement with uniform timing",
    tags=["bot", "pointer"],
)
def bot_linear_pointer():
    pass


@threat_type(
    code="bot-fingerprint-mismatch",
    name="Bot: Fingerprint Mismatch",
    description="Challenges sessions with user-agent behavior mismatch and zero plugins.",
    category="bot_attacks",
    severity=65,
    default_action="challenge",
    conditions={
        "operator": "AND",
        "rules": [
            {"field": "signals.ua_behavior_mismatch", "op": "==", "value": True},
            {"field": "signals.plugins_zero", "op": "==", "value": True},
        ],
        "action": "challenge",
        "reason_template": "Bot: fingerprint mismatch with zero plugins",
    },
    default_config={},
    reason_template="Bot: fingerprint mismatch with zero plugins",
    tags=["bot", "fingerprint"],
)
def bot_fingerprint_mismatch():
    pass
