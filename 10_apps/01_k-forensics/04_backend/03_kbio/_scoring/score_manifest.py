"""kbio V2 score manifest — registry of all 22 scores.

Single source of truth for score names, categories, ranges, and defaults.
Used by the fusion engine, verdict engine, and API response builder.
"""
from __future__ import annotations


CATEGORIES = ["identity", "anomaly", "humanness", "threat", "trust", "meta"]

MODALITIES = {
    "keystroke": 64,
    "pointer": 32,
    "touch": 32,
    "sensor": 32,
}

GENERAL_EMBEDDING_DIM = 128

VERDICT_ACTIONS = ["allow", "monitor", "challenge", "step_up", "block"]
RISK_LEVELS = ["low", "medium", "high", "critical"]

SCORES: dict[str, dict] = {
    # --- Identity (5) ---
    "behavioral_drift": {
        "category": "identity",
        "range": (0.0, 1.0),
        "default": -1.0,
        "description": "Per-modality fused behavioral drift from baseline",
    },
    "credential_drift": {
        "category": "identity",
        "range": (0.0, 1.0),
        "default": None,
        "description": "Credential typing pattern drift vs enrolled template",
    },
    "identity_confidence": {
        "category": "identity",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "Inverse of drift adjusted by meta confidence",
    },
    "familiarity_score": {
        "category": "identity",
        "range": (0.0, 1.0),
        "default": -1.0,
        "description": "How familiar the user is with the current UI flow",
    },
    "cognitive_load": {
        "category": "identity",
        "range": (0.0, 1.0),
        "default": -1.0,
        "description": "Estimated mental effort during the session",
    },
    # --- Anomaly (5) ---
    "session_anomaly": {
        "category": "anomaly",
        "range": (0.0, 1.0),
        "default": -1.0,
        "description": "How abnormal this session is vs user history",
    },
    "velocity_anomaly": {
        "category": "anomaly",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "Rate of behavioral change within the session",
    },
    "takeover_probability": {
        "category": "anomaly",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "Probability of mid-session user switch (CUSUM)",
    },
    "pattern_break": {
        "category": "anomaly",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "Structural behavioral change (JS divergence)",
    },
    "consistency_score": {
        "category": "anomaly",
        "range": (0.0, 1.0),
        "default": 0.5,
        "description": "Intra-session self-consistency of behavior",
    },
    # --- Humanness (4) ---
    "bot_score": {
        "category": "humanness",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "Probability of automated/scripted interaction",
    },
    "replay_score": {
        "category": "humanness",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "Probability this is a replayed previous session",
    },
    "automation_score": {
        "category": "humanness",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "Browser automation tool detection (CDP/webdriver)",
    },
    "population_anomaly": {
        "category": "humanness",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "How unusual vs ALL users (not just this user)",
    },
    # --- Threat (2) ---
    "coercion_score": {
        "category": "threat",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "Probability user is acting under duress/instruction",
    },
    "impersonation_score": {
        "category": "threat",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "Derived impostor signal (drift x familiarity x cognitive)",
    },
    # --- Trust (3) ---
    "session_trust": {
        "category": "trust",
        "range": (0.0, 1.0),
        "default": 0.5,
        "description": "Real-time composite session trust level",
    },
    "user_trust": {
        "category": "trust",
        "range": (0.0, 1.0),
        "default": 0.5,
        "description": "Long-term user trust across sessions (EMA)",
    },
    "device_trust": {
        "category": "trust",
        "range": (0.0, 1.0),
        "default": 0.3,
        "description": "Trust for this device+user combination",
    },
    # --- Meta (3) ---
    "confidence": {
        "category": "meta",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "How much to trust all other scores",
    },
    "signal_richness": {
        "category": "meta",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "Fraction of modalities contributing to scoring",
    },
    "profile_maturity": {
        "category": "meta",
        "range": (0.0, 1.0),
        "default": 0.0,
        "description": "Enrollment completeness of user profile",
    },
}
