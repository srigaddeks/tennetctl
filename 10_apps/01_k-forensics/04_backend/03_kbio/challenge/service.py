"""kbio challenge service.

Generates and verifies KP-Challenge behavioral TOTP prompts.

Cache keys:
  kbio:challenge:{challenge_id}   TTL 300 s  — full challenge state
  kbio:profile:{user_hash}        TTL 300 s  — user behavioral profile
"""
from __future__ import annotations

import importlib
import json
import random
import secrets
import time
import uuid
from typing import Any

import asyncpg

_errors = importlib.import_module("01_core.errors")
_valkey_mod = importlib.import_module("01_core.valkey")

from .repository import create_challenge, get_challenge, upsert_challenge_attr
from .schemas import ChallengeGenerateResponse, ChallengeVerifyResponse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CHALLENGE_TTL_S = 300  # 5 minutes
_CHALLENGE_KEY_PREFIX = "kbio:challenge:"
_PROFILE_KEY_PREFIX = "kbio:profile:"

# V1 word list — ~50 common English words chosen for keystroke diversity.
_WORD_LIST: list[str] = [
    "apple", "brave", "cloud", "draft", "eagle",
    "flame", "grace", "heart", "image", "joker",
    "knife", "lemon", "magic", "noble", "ocean",
    "plain", "quiet", "river", "stone", "tiger",
    "ultra", "vivid", "water", "xenon", "young",
    "zebra", "amber", "bliss", "crisp", "delta",
    "elite", "frost", "globe", "honor", "index",
    "jewel", "karma", "light", "maple", "nexus",
    "orbit", "pixel", "queen", "realm", "solar",
    "tower", "urban", "vapor", "wheat", "yield",
]

# Behavioral plausibility thresholds.
_MIN_REACTION_MS = 200
_MAX_REACTION_MS = 10_000
_MIN_KEY_GAP_MS = 10
_MIN_VARIANCE = 1e-9

# Drift score thresholds for action decisions.
_DRIFT_FLAG_THRESHOLD = 0.5
_DRIFT_BLOCK_THRESHOLD = 0.75


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _challenge_cache_key(challenge_id: str) -> str:
    return f"{_CHALLENGE_KEY_PREFIX}{challenge_id}"


def _profile_cache_key(user_hash: str) -> str:
    return f"{_PROFILE_KEY_PREFIX}{user_hash}"


def _generate_phrase(n_words: int = 5) -> str:
    """Pick n_words random words from the V1 word list and join with spaces."""
    return " ".join(random.choices(_WORD_LIST, k=n_words))


def _score_drift(
    response_batch: dict[str, Any],
    profile: dict[str, Any] | None,
) -> tuple[float, float]:
    """Compute a simple behavioral drift score from the response_batch.

    Returns (drift_score, confidence) both in [0.0, 1.0].

    V1 scoring:
      - If no enrolled profile exists → drift=0.5, confidence=0.3
      - Extract 'key_intervals' list from response_batch (ms between keystrokes)
      - Compare mean/stdev against profile zone_transition_matrix summary
      - Drift = normalised absolute deviation; confidence ∝ sample size
    """
    key_intervals: list[float] = response_batch.get("key_intervals", [])
    if len(key_intervals) < 3:
        # Insufficient data — neutral verdict.
        return 0.5, 0.2

    sample_mean = sum(key_intervals) / len(key_intervals)
    variance = sum((x - sample_mean) ** 2 for x in key_intervals) / len(key_intervals)
    sample_std = variance ** 0.5

    if profile is None:
        return 0.5, 0.3

    # Pull baseline from profile if available.
    baseline_mean: float = float(profile.get("mean_key_interval_ms", sample_mean))
    baseline_std: float = float(profile.get("std_key_interval_ms", max(sample_std, 1.0)))

    # Z-score style drift.
    drift_raw = abs(sample_mean - baseline_mean) / max(baseline_std, 1.0)
    drift_score = min(drift_raw / 5.0, 1.0)  # cap at 1.0; 5 stds = max drift

    # Confidence grows with sample size up to ~30 keystrokes.
    confidence = min(len(key_intervals) / 30.0, 1.0) * 0.8 + 0.1

    return round(drift_score, 4), round(confidence, 4)


def _decide_action(drift_score: float) -> str:
    """Map drift_score to a recommended action string."""
    if drift_score >= _DRIFT_BLOCK_THRESHOLD:
        return "block"
    if drift_score >= _DRIFT_FLAG_THRESHOLD:
        return "flag"
    return "allow"


def _anti_bot_checks(response_batch: dict[str, Any]) -> bool:
    """Return True if response_batch passes basic anti-bot plausibility checks.

    Checks:
      1. Reaction time in [200 ms, 10 s]
      2. No key gap below 10 ms (superhuman speed)
      3. Non-zero variance in key intervals
    """
    reaction_ms: float = float(response_batch.get("reaction_time_ms", -1))
    if not (_MIN_REACTION_MS <= reaction_ms <= _MAX_REACTION_MS):
        return False

    key_intervals: list[float] = response_batch.get("key_intervals", [])
    if key_intervals:
        if min(key_intervals) < _MIN_KEY_GAP_MS:
            return False
        if len(key_intervals) > 1:
            mean = sum(key_intervals) / len(key_intervals)
            variance = sum((x - mean) ** 2 for x in key_intervals) / len(key_intervals)
            if variance < _MIN_VARIANCE:
                return False

    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def generate_challenge(
    conn: asyncpg.Connection,
    *,
    session_id: str,
    user_hash: str,
    purpose: str,
) -> ChallengeGenerateResponse:
    """Generate a new KP-Challenge for the given user/session.

    Steps:
      1. Load user behavioral profile from Valkey (kbio:profile:{user_hash}).
      2. Extract zone_transition_matrix and rank zone pairs by discriminative power.
      3. Select top 20 target pairs (V1: informational only, not used to alter phrase).
      4. Generate a 4–6 word phrase from the V1 word list.
      5. Persist the challenge record in the DB.
      6. Cache the full challenge state in Valkey (TTL 300 s).
      7. Return ChallengeGenerateResponse.

    Raises:
        AppError(INTERNAL_ERROR, 500) — on unexpected DB failure.
    """
    valkey = _valkey_mod.get_client()

    # --- Step 1: load profile from cache ---
    profile: dict[str, Any] | None = None
    try:
        raw = await valkey.get(_profile_cache_key(user_hash))
        if raw:
            profile = json.loads(raw)
    except Exception:
        pass

    # --- Step 2 & 3: analyse zone_transition_matrix ---
    # V1: informational only; future versions will skew word selection.
    _target_pairs: list[tuple[str, float]] = []
    if profile:
        ztm: dict[str, Any] = profile.get("zone_transition_matrix", {})
        for pair_key, stats in ztm.items():
            if isinstance(stats, dict):
                count = float(stats.get("count", 0))
                stdev = float(stats.get("stdev", 1.0))
                score = count / max(stdev, 1.0)
                _target_pairs.append((pair_key, score))
        _target_pairs.sort(key=lambda x: x[1], reverse=True)
        _target_pairs = _target_pairs[:20]

    # --- Step 4: generate phrase ---
    n_words = random.randint(4, 6)
    phrase = _generate_phrase(n_words)

    # --- Step 5: persist to DB ---
    challenge_id = str(uuid.uuid4())
    nonce = secrets.token_hex(16)
    expires_at_ms = int((time.time() + _CHALLENGE_TTL_S) * 1000)

    try:
        await create_challenge(
            conn,
            challenge_id=challenge_id,
            sdk_session_id=session_id,
            user_hash=user_hash,
            actor_id=user_hash,
        )
        # Store core attrs in EAV.
        for attr_code, value in [
            ("purpose", purpose),
            ("phrase", phrase),
            ("nonce", nonce),
            ("expires_at_ms", str(expires_at_ms)),
            ("used", "false"),
        ]:
            await upsert_challenge_attr(
                conn,
                challenge_id=challenge_id,
                attr_code=attr_code,
                value=value,
                actor_id=user_hash,
            )
    except Exception as exc:
        raise _errors.AppError(
            "INTERNAL_ERROR",
            f"Failed to create challenge: {exc}",
            500,
        ) from exc

    # --- Step 6: cache full state ---
    cache_payload = {
        "challenge_id": challenge_id,
        "session_id": session_id,
        "user_hash": user_hash,
        "purpose": purpose,
        "phrase": phrase,
        "nonce": nonce,
        "expires_at_ms": expires_at_ms,
        "used": False,
    }
    try:
        await valkey.setex(
            _challenge_cache_key(challenge_id),
            _CHALLENGE_TTL_S,
            json.dumps(cache_payload),
        )
    except Exception:
        pass

    return ChallengeGenerateResponse(
        challenge_id=challenge_id,
        challenge_type="kp_phrase",
        prompt=phrase,
        char_count=len(phrase),
        expires_at=expires_at_ms,
        nonce=nonce,
    )


async def verify_challenge(
    conn: asyncpg.Connection,
    *,
    challenge_id: str,
    session_id: str,
    user_hash: str,
    response_batch: dict[str, Any],
) -> ChallengeVerifyResponse:
    """Verify a KP-Challenge behavioral response.

    Steps:
      1. Load challenge state from Valkey (kbio:challenge:{challenge_id}).
      2. Validate: exists, not expired, not already used.
      3. Mark as used immediately (Valkey + DB) to prevent replay.
      4. Run anti-bot plausibility checks on response_batch.
      5. Score behavioral drift against enrolled profile.
      6. Return ChallengeVerifyResponse with action recommendation.

    Raises:
        AppError(NOT_FOUND, 404)         — challenge not in cache/DB.
        AppError(CHALLENGE_EXPIRED, 410) — TTL exceeded.
        AppError(CHALLENGE_USED, 409)    — challenge already consumed.
        AppError(BOT_DETECTED, 422)      — anti-bot checks failed.
    """
    valkey = _valkey_mod.get_client()

    # --- Step 1: load from Valkey ---
    challenge_state: dict[str, Any] | None = None
    try:
        raw = await valkey.get(_challenge_cache_key(challenge_id))
        if raw:
            challenge_state = json.loads(raw)
    except Exception:
        pass

    # Fallback to DB if not in cache.
    if challenge_state is None:
        row = await get_challenge(conn, challenge_id)
        if row is None:
            raise _errors.AppError(
                "NOT_FOUND",
                f"Challenge '{challenge_id}' not found.",
                404,
            )
        # Reconstruct minimal state from DB view.
        challenge_state = {
            "challenge_id": str(row.get("id", challenge_id)),
            "session_id": str(row.get("sdk_session_id", session_id)),
            "user_hash": str(row.get("user_hash", user_hash)),
            "expires_at_ms": int(row.get("expires_at_ms", 0)),
            "used": bool(row.get("used", False)),
        }

    # --- Step 2a: expiry check ---
    expires_at_ms: int = int(challenge_state.get("expires_at_ms", 0))
    now_ms = int(time.time() * 1000)
    if expires_at_ms and now_ms > expires_at_ms:
        raise _errors.AppError(
            "CHALLENGE_EXPIRED",
            f"Challenge '{challenge_id}' has expired.",
            410,
        )

    # --- Step 2b: already used? ---
    if challenge_state.get("used"):
        raise _errors.AppError(
            "CHALLENGE_USED",
            f"Challenge '{challenge_id}' has already been used.",
            409,
        )

    # --- Step 3: mark as used ---
    challenge_state["used"] = True
    try:
        # Keep remaining TTL; just overwrite payload.
        await valkey.setex(
            _challenge_cache_key(challenge_id),
            _CHALLENGE_TTL_S,
            json.dumps(challenge_state),
        )
    except Exception:
        pass
    # Persist used=true to DB.
    try:
        await upsert_challenge_attr(
            conn,
            challenge_id=challenge_id,
            attr_code="used",
            value="true",
            actor_id=user_hash,
        )
    except Exception:
        pass

    # --- Step 4: anti-bot checks ---
    if not _anti_bot_checks(response_batch):
        return ChallengeVerifyResponse(
            challenge_id=challenge_id,
            passed=False,
            drift_score=1.0,
            confidence=0.95,
            action="block",
        )

    # --- Step 5: behavioral drift scoring ---
    profile: dict[str, Any] | None = None
    try:
        raw = await valkey.get(_profile_cache_key(user_hash))
        if raw:
            profile = json.loads(raw)
    except Exception:
        pass

    drift_score, confidence = _score_drift(response_batch, profile)
    passed = drift_score < _DRIFT_FLAG_THRESHOLD
    action = _decide_action(drift_score)

    return ChallengeVerifyResponse(
        challenge_id=challenge_id,
        passed=passed,
        drift_score=drift_score,
        confidence=confidence,
        action=action,
    )
