"""kbio enrollment pipeline.

Handles the enrollment phase (sessions 1-5) when building a user's
initial behavioral profile. Buffers session embeddings and descriptors
until enough data is collected for initial clustering.

Pure computation -- no I/O, no external dependencies beyond stdlib.
"""

from __future__ import annotations

import uuid
from typing import Any

from . import cluster_manager


# Minimum sessions before initial clustering can run
_MIN_ENROLLMENT_SESSIONS = 3

# Reclustering thresholds
_RECLUSTER_SESSION_INTERVAL = 50
_RECLUSTER_DAY_INTERVAL = 30


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def process_enrollment_batch(
    embeddings_buffer: list[list[float]],
    descriptors_buffer: list[dict[str, Any]],
    new_embedding: list[float],
    new_descriptor: dict[str, Any],
) -> dict[str, Any]:
    """Process a batch during enrollment phase.

    Adds to buffers. When buffer reaches threshold, triggers initial clustering.

    Returns:
        {
            "status": "buffering" | "ready_to_cluster",
            "sessions_collected": int,
            "sessions_needed": int,  # minimum 3 for initial cluster
            "embeddings_buffer": list,
            "descriptors_buffer": list,
        }
    """
    # Build new buffers (immutability: never mutate inputs)
    updated_embeddings = list(embeddings_buffer) + [list(new_embedding)]
    updated_descriptors = list(descriptors_buffer) + [dict(new_descriptor)]

    collected = len(updated_embeddings)
    needed = _MIN_ENROLLMENT_SESSIONS

    status = "ready_to_cluster" if collected >= needed else "buffering"

    return {
        "status": status,
        "sessions_collected": collected,
        "sessions_needed": needed,
        "embeddings_buffer": updated_embeddings,
        "descriptors_buffer": updated_descriptors,
    }


def create_initial_profile(
    embeddings_buffer: list[list[float]],
    descriptors_buffer: list[dict[str, Any]],
    user_hash: str,
) -> dict[str, Any]:
    """Create initial user profile from enrollment buffer.

    Runs cluster discovery, computes intra-distance stats.
    Sets baseline_quality to 'forming'.

    Returns a UserProfile-shaped dict.
    """
    if not embeddings_buffer or not descriptors_buffer:
        return {
            "user_hash": user_hash,
            "profile_id": str(uuid.uuid4()),
            "clusters": [],
            "baseline_quality": "insufficient",
            "total_sessions": 0,
            "enrollment_complete": False,
        }

    clusters = cluster_manager.discover_clusters(
        session_descriptors=descriptors_buffer,
        session_embeddings=embeddings_buffer,
        max_clusters=5,  # conservative during enrollment
        min_cluster_sessions=1,  # relax during enrollment
    )

    # Compute intra-distance stats for each cluster
    enriched_clusters = []
    for c in clusters:
        indices = c.get("session_indices", [])
        member_embeddings = [
            embeddings_buffer[i]
            for i in indices
            if i < len(embeddings_buffer)
        ]
        centroid = c.get("embedding_centroid", [])
        intra_stats = cluster_manager.compute_intra_distance_stats(
            centroid, member_embeddings,
        )
        enriched = {**c, "intra_distance_stats": intra_stats}
        enriched_clusters.append(enriched)

    total = len(embeddings_buffer)
    baseline = "forming" if total >= _MIN_ENROLLMENT_SESSIONS else "insufficient"

    return {
        "user_hash": user_hash,
        "profile_id": str(uuid.uuid4()),
        "clusters": enriched_clusters,
        "baseline_quality": baseline,
        "total_sessions": total,
        "enrollment_complete": total >= _MIN_ENROLLMENT_SESSIONS,
        "sessions_since_last_cluster": 0,
        "days_since_last_cluster": 0,
    }


def should_recluster(
    profile: dict[str, Any],
    sessions_since_last: int = 0,
    days_since_last: int = 0,
) -> bool:
    """Determine if the profile needs re-clustering.

    Re-cluster every 50 sessions or 30 days, whichever comes first.
    Also recluster if any cluster has 0 recent sessions (stale).
    """
    if sessions_since_last >= _RECLUSTER_SESSION_INTERVAL:
        return True

    if days_since_last >= _RECLUSTER_DAY_INTERVAL:
        return True

    # Check for stale clusters (0 sessions in their session_indices)
    clusters = profile.get("clusters", [])
    for c in clusters:
        indices = c.get("session_indices", [])
        if not indices:
            return True

    # Also recluster if enrollment was minimal and we now have enough data
    total = profile.get("total_sessions", 0)
    baseline = profile.get("baseline_quality", "insufficient")
    if baseline == "forming" and total >= _RECLUSTER_SESSION_INTERVAL:
        return True

    return False
