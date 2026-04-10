"""kbio Bayesian cluster selector.

Replaces V1's crude platform+input_method centroid matching with
Bayesian posterior-based cluster selection.

For each cluster k:
    prior_k   = P(cluster_k | session_context)
    likelihood = 1 / (1 + embedding_distance_k)
    posterior  = prior_k * likelihood_k

Select the cluster with the highest posterior.
Pure computation -- no I/O, no external dependencies beyond stdlib.
"""

from __future__ import annotations

import math
from typing import Any


# Context feature weights for prior computation
_CONTEXT_WEIGHTS: dict[str, float] = {
    "platform": 0.30,
    "input_method": 0.25,
    "time_bucket": 0.20,
    "screen_class": 0.15,
    "locale": 0.10,
}

# Mismatch penalty: not 0 (allows embedding to override context)
_MISMATCH_SCORE = 0.1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def select_cluster(
    clusters: list[dict[str, Any]],
    session_descriptor: dict[str, Any],
    current_embedding: list[float],
) -> dict[str, Any]:
    """Select the best-matching cluster using Bayesian posterior.

    For each cluster k:
        prior_k = P(cluster_k | session_context)
        likelihood_k = 1 / (1 + embedding_distance_k)
        posterior_k = prior_k * likelihood_k

    Select cluster with highest posterior.

    Returns:
        {
            "cluster": selected_cluster_dict or None,
            "cluster_id": str,
            "posterior": float,  # confidence in selection
            "match_quality": float,  # posterior / sum(all posteriors)
            "is_new_context": bool,  # True if match_quality < 0.3
            "all_posteriors": dict[str, float],  # cluster_id -> posterior
        }
    """
    if not clusters:
        return {
            "cluster": None,
            "cluster_id": "",
            "posterior": 0.0,
            "match_quality": 0.0,
            "is_new_context": True,
            "all_posteriors": {},
        }

    # Compute raw context scores for softmax normalization
    raw_context_scores = [
        _raw_context_score(c, session_descriptor) for c in clusters
    ]

    # Softmax-normalize into priors
    priors = _softmax(raw_context_scores)

    # Compute posteriors
    all_posteriors: dict[str, float] = {}
    best_idx = 0
    best_posterior = -1.0

    for i, cluster in enumerate(clusters):
        prior = priors[i]
        likelihood = _compute_embedding_likelihood(cluster, current_embedding)
        posterior = round(prior * likelihood, 4)

        cid = cluster.get("cluster_id", f"cluster_{i}")
        all_posteriors[cid] = posterior

        if posterior > best_posterior:
            best_posterior = posterior
            best_idx = i

    posterior_sum = sum(all_posteriors.values())
    match_quality = round(
        best_posterior / posterior_sum if posterior_sum > 0.0 else 0.0,
        4,
    )

    selected = clusters[best_idx]

    return {
        "cluster": dict(selected),
        "cluster_id": selected.get("cluster_id", ""),
        "posterior": best_posterior,
        "match_quality": match_quality,
        "is_new_context": match_quality < 0.3,
        "all_posteriors": all_posteriors,
    }


# ---------------------------------------------------------------------------
# Prior computation
# ---------------------------------------------------------------------------


def _compute_context_prior(
    cluster: dict[str, Any],
    session_descriptor: dict[str, Any],
) -> float:
    """Compute raw (unnormalized) context similarity score.

    Uses weighted feature matching:
    - platform match: 0.30 weight
    - input_method match: 0.25 weight
    - time_bucket match: 0.20 weight
    - screen_class match: 0.15 weight
    - locale match: 0.10 weight

    Exact match on a feature = 1.0, mismatch = 0.1 (not 0, to allow override).
    """
    prototype = cluster.get("context_prototype", {})
    if not prototype:
        return _MISMATCH_SCORE  # no context info -> low prior

    score = 0.0
    for feature, weight in _CONTEXT_WEIGHTS.items():
        proto_val = prototype.get(feature)
        session_val = session_descriptor.get(feature)

        if proto_val is None or session_val is None:
            # Missing data: assign neutral score
            score += weight * 0.5
        elif str(proto_val) == str(session_val):
            score += weight * 1.0
        else:
            score += weight * _MISMATCH_SCORE

    return round(score, 4)


def _raw_context_score(
    cluster: dict[str, Any],
    session_descriptor: dict[str, Any],
) -> float:
    """Compute raw context score (before softmax normalization)."""
    return _compute_context_prior(cluster, session_descriptor)


# ---------------------------------------------------------------------------
# Likelihood computation
# ---------------------------------------------------------------------------


def _compute_embedding_likelihood(
    cluster: dict[str, Any],
    current_embedding: list[float],
) -> float:
    """Compute likelihood from embedding distance.

    likelihood = 1 / (1 + cosine_distance(embedding, centroid))
    """
    centroid = cluster.get("embedding_centroid", [])
    if not centroid or not current_embedding:
        return 0.5  # neutral likelihood when data missing

    dist = _cosine_distance(centroid, current_embedding)
    return round(1.0 / (1.0 + dist), 4)


# ---------------------------------------------------------------------------
# Math helpers (self-contained, no imports from _scoring)
# ---------------------------------------------------------------------------


def _cosine_distance(a: list[float], b: list[float]) -> float:
    """Cosine distance for L2-normalized vectors. Returns 0.0-2.0."""
    if len(a) != len(b) or len(a) == 0:
        return 1.0  # maximum ambiguity
    dot = sum(x * y for x, y in zip(a, b))
    return round(max(0.0, 1.0 - dot), 4)


def _softmax(values: list[float]) -> list[float]:
    """Numerically stable softmax normalization.

    Returns list of probabilities summing to 1.0.
    """
    if not values:
        return []
    if len(values) == 1:
        return [1.0]

    max_val = max(values)
    exps = [math.exp(v - max_val) for v in values]
    total = sum(exps)
    if total == 0.0:
        uniform = 1.0 / len(values)
        return [round(uniform, 4)] * len(values)
    return [round(e / total, 4) for e in exps]
