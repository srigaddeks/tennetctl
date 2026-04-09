"""kbio challenge schemas.

Pydantic v2 models for KP-Challenge behavioral TOTP generation and verification.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChallengeGenerateRequest(BaseModel):
    """Request body for generating a new KP-Challenge."""

    session_id: str = Field(..., description="SDK session identifier")
    user_hash: str = Field(..., description="Pseudonymous user identifier")
    purpose: str = Field(
        ...,
        description="Intent context — e.g. 'login_2fa', 'high_value_transfer'",
    )


class ChallengeGenerateResponse(BaseModel):
    """Payload returned when a challenge is created."""

    challenge_id: str = Field(..., description="Unique challenge UUID")
    challenge_type: str = Field(
        default="kp_phrase",
        description="Challenge variant (always 'kp_phrase' for V1)",
    )
    prompt: str = Field(..., description="The phrase the user must type")
    char_count: int = Field(..., description="Number of characters in the phrase")
    expires_at: int = Field(..., description="Unix epoch milliseconds for expiry")
    nonce: str = Field(..., description="Random nonce for replay protection")


class ChallengeVerifyRequest(BaseModel):
    """Request body for verifying a KP-Challenge response."""

    challenge_id: str = Field(..., description="Challenge UUID to verify")
    session_id: str = Field(..., description="SDK session identifier")
    user_hash: str = Field(..., description="Pseudonymous user identifier")
    response_batch: dict[str, Any] = Field(
        ...,
        description="Behavioral telemetry captured while typing the phrase",
    )


class ChallengeVerifyResponse(BaseModel):
    """Result of a challenge verification attempt."""

    challenge_id: str
    passed: bool = Field(..., description="True if the challenge was passed")
    drift_score: float = Field(
        ..., description="Behavioral drift vs. enrolled profile (0–1)"
    )
    confidence: float = Field(
        ..., description="Model confidence in the verdict (0–1)"
    )
    action: str = Field(
        ...,
        description="Recommended action — 'allow', 'flag', or 'block'",
    )
