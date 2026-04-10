"""kbio multi-profile cluster manager.

Discovers, updates, merges, and prunes behavioral clusters per user.
Pure computation -- no I/O, no external dependencies beyond stdlib.

V2 innovation: up to 15 auto-discovered behavioral clusters per user
via pure-Python K-Means with K-Means++ initialization, replacing V1's
flat centroid matching (platform + input_method).
"""

from __future__ import annotations

import math
import uuid
from collections import Counter
from typing import Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def discover_clusters(
    session_descriptors: list[dict[str, Any]],
    session_embeddings: list[list[float]],
    *,
    max_clusters: int = 15,
    min_cluster_sessions: int = 3,
) -> list[dict[str, Any]]:
    """Run K-Means clustering on session descriptors to discover behavioral modes.

    Uses a pure-Python K-Means implementation (no sklearn dependency for portability).
    Selects optimal k using simplified silhouette score.

    Args:
        session_descriptors: List of session context vectors (numeric features).
        session_embeddings: Corresponding behavioral embeddings (128d).
        max_clusters: Maximum clusters per user.
        min_cluster_sessions: Minimum sessions to form a cluster.

    Returns:
        List of cluster dicts with:
        - cluster_id: str (UUID)
        - centroid: list[float] (descriptor space centroid)
        - embedding_centroid: list[float] (behavioral embedding centroid)
        - session_indices: list[int] (which sessions belong)
        - weight: float (proportion of total sessions)
        - context_prototype: dict (dominant context features)
    """
    n = len(session_descriptors)
    if n == 0 or len(session_embeddings) == 0:
        return []

    if n != len(session_embeddings):
        raise ValueError(
            f"Descriptor count ({n}) != embedding count ({len(session_embeddings)})"
        )

    # Flatten descriptors to numeric vectors for clustering
    desc_vectors = _descriptors_to_vectors(session_descriptors)

    # Edge case: single session -> single cluster
    if n == 1:
        return [_build_cluster(
            session_indices=[0],
            desc_vectors=desc_vectors,
            session_embeddings=session_embeddings,
            session_descriptors=session_descriptors,
            total_sessions=n,
        )]

    # Edge case: all identical descriptor vectors -> single cluster
    if _all_identical(desc_vectors):
        return [_build_cluster(
            session_indices=list(range(n)),
            desc_vectors=desc_vectors,
            session_embeddings=session_embeddings,
            session_descriptors=session_descriptors,
            total_sessions=n,
        )]

    # Determine k range: 1 to min(max_clusters, floor(n / 3))
    max_k = min(max_clusters, max(1, n // 3))

    best_score = -1.0
    best_assignments: list[int] = [0] * n

    for k in range(1, max_k + 1):
        assignments, _centroids = _kmeans(desc_vectors, k)

        if k == 1:
            # Silhouette undefined for k=1; use as fallback
            best_assignments = assignments
            continue

        score = _silhouette_score(desc_vectors, assignments)
        if score > best_score:
            best_score = score
            best_assignments = assignments

    # Build clusters from best assignments
    cluster_map: dict[int, list[int]] = {}
    for idx, label in enumerate(best_assignments):
        cluster_map.setdefault(label, []).append(idx)

    clusters = [
        _build_cluster(
            session_indices=indices,
            desc_vectors=desc_vectors,
            session_embeddings=session_embeddings,
            session_descriptors=session_descriptors,
            total_sessions=n,
        )
        for indices in cluster_map.values()
    ]

    # Merge small clusters
    clusters = merge_clusters(clusters, min_sessions=min_cluster_sessions)

    return clusters


def merge_clusters(
    clusters: list[dict[str, Any]],
    min_sessions: int = 3,
) -> list[dict[str, Any]]:
    """Merge clusters with fewer than min_sessions into their nearest neighbor.

    Returns a new list of clusters (never mutates input).
    """
    if len(clusters) <= 1:
        return [dict(c) for c in clusters]

    large: list[dict[str, Any]] = []
    small: list[dict[str, Any]] = []

    for c in clusters:
        if len(c.get("session_indices", [])) >= min_sessions:
            large.append(dict(c))
        else:
            small.append(dict(c))

    # If no large clusters, keep the biggest as anchor
    if not large and small:
        small.sort(key=lambda c: len(c.get("session_indices", [])), reverse=True)
        large.append(small.pop(0))

    # Merge each small cluster into nearest large cluster
    for sc in small:
        sc_centroid = sc.get("embedding_centroid", [])
        if not sc_centroid or not large:
            # Cannot compute distance; merge into first large cluster
            if large:
                large[0] = _merge_two_clusters(large[0], sc)
            continue

        best_idx = 0
        best_dist = float("inf")
        for i, lc in enumerate(large):
            lc_centroid = lc.get("embedding_centroid", [])
            if lc_centroid:
                dist = _euclidean_distance(sc_centroid, lc_centroid)
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i

        large[best_idx] = _merge_two_clusters(large[best_idx], sc)

    # Recalculate weights
    total = sum(len(c.get("session_indices", [])) for c in large)
    result = []
    for c in large:
        updated = dict(c)
        updated["weight"] = round(
            len(c.get("session_indices", [])) / total if total > 0 else 0.0,
            4,
        )
        result.append(updated)

    return result


def compute_context_prototype(
    session_descriptors: list[dict[str, Any]],
    session_indices: list[int],
) -> dict[str, Any]:
    """Determine the dominant context features for a cluster.

    Returns most common platform, input_method, time_bucket, etc.
    """
    if not session_indices or not session_descriptors:
        return {}

    context_keys = ["platform", "input_method", "time_bucket", "screen_class", "locale"]
    prototype: dict[str, Any] = {}

    for key in context_keys:
        values = [
            session_descriptors[i].get(key)
            for i in session_indices
            if i < len(session_descriptors) and session_descriptors[i].get(key) is not None
        ]
        if values:
            counter = Counter(values)
            most_common_val, most_common_count = counter.most_common(1)[0]
            prototype[key] = most_common_val
            prototype[f"{key}_dominance"] = round(most_common_count / len(values), 4)

    return prototype


def update_cluster_centroid(
    cluster: dict[str, Any],
    new_embedding: list[float],
    *,
    alpha: float = 0.10,
) -> dict[str, Any]:
    """EMA update of a cluster centroid with a new genuine session embedding.

    Returns updated cluster dict (new object, not mutated).
    """
    old_centroid = cluster.get("embedding_centroid", [])

    if not old_centroid:
        return {**cluster, "embedding_centroid": [round(v, 4) for v in new_embedding]}

    if len(old_centroid) != len(new_embedding):
        raise ValueError(
            f"Centroid dim ({len(old_centroid)}) != embedding dim ({len(new_embedding)})"
        )

    updated_centroid = [
        round(old_centroid[i] * (1.0 - alpha) + new_embedding[i] * alpha, 4)
        for i in range(len(old_centroid))
    ]

    return {**cluster, "embedding_centroid": updated_centroid}


def compute_intra_distance_stats(
    centroid: list[float],
    member_embeddings: list[list[float]],
) -> dict[str, float]:
    """Compute intra-class distance statistics for a cluster.

    Returns {mean, stdev, p95, p99, sample_count}.
    Uses cosine distance from centroid to each member.
    """
    if not centroid or not member_embeddings:
        return {
            "mean": 0.0,
            "stdev": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "sample_count": 0.0,
        }

    distances = [_cosine_distance(centroid, emb) for emb in member_embeddings]
    n = len(distances)

    mean = round(sum(distances) / n, 4)
    variance = sum((d - mean) ** 2 for d in distances) / n
    stdev = round(math.sqrt(variance), 4)

    sorted_dists = sorted(distances)
    p95 = round(_percentile(sorted_dists, 0.95), 4)
    p99 = round(_percentile(sorted_dists, 0.99), 4)

    return {
        "mean": mean,
        "stdev": stdev,
        "p95": p95,
        "p99": p99,
        "sample_count": float(n),
    }


# ---------------------------------------------------------------------------
# K-Means implementation (pure Python, no numpy/sklearn)
# ---------------------------------------------------------------------------


def _kmeans(
    vectors: list[list[float]], k: int, max_iter: int = 50,
) -> tuple[list[int], list[list[float]]]:
    """Pure-Python K-Means clustering.

    Returns (assignments, centroids).
    Uses K-Means++ initialization for better convergence.
    """
    n = len(vectors)
    if n == 0:
        return [], []
    if k <= 0:
        raise ValueError("k must be positive")
    if k >= n:
        # Each point is its own cluster
        assignments = list(range(n))
        centroids = [list(v) for v in vectors]
        return assignments, centroids

    centroids = _kmeans_plus_plus_init(vectors, k)
    assignments = [0] * n

    for _ in range(max_iter):
        # Assignment step
        new_assignments = [0] * n
        for i, vec in enumerate(vectors):
            best_c = 0
            best_dist = float("inf")
            for c_idx, centroid in enumerate(centroids):
                dist = _euclidean_distance(vec, centroid)
                if dist < best_dist:
                    best_dist = dist
                    best_c = c_idx
            new_assignments[i] = best_c

        # Check convergence
        if new_assignments == assignments:
            break
        assignments = new_assignments

        # Update step
        dim = len(vectors[0])
        new_centroids: list[list[float]] = [[0.0] * dim for _ in range(k)]
        counts = [0] * k
        for i, vec in enumerate(vectors):
            label = assignments[i]
            counts[label] += 1
            for d in range(dim):
                new_centroids[label][d] += vec[d]

        for c_idx in range(k):
            if counts[c_idx] > 0:
                for d in range(dim):
                    new_centroids[c_idx][d] /= counts[c_idx]
            else:
                # Empty cluster: keep old centroid
                new_centroids[c_idx] = list(centroids[c_idx])

        centroids = new_centroids

    return assignments, centroids


def _kmeans_plus_plus_init(
    vectors: list[list[float]], k: int,
) -> list[list[float]]:
    """K-Means++ centroid initialization.

    Pick first centroid uniformly at random.
    Subsequent centroids chosen proportional to squared distance
    from nearest existing centroid.
    """
    import random

    n = len(vectors)
    if k >= n:
        return [list(v) for v in vectors]

    # Deterministic-friendly: use hash of data for seed in tests,
    # but allow true randomness in production
    centroids: list[list[float]] = []

    # First centroid: pick the vector closest to the overall mean
    # (more stable than random for reproducibility)
    mean_vec = _vector_mean(vectors)
    first_idx = min(range(n), key=lambda i: _euclidean_distance(vectors[i], mean_vec))
    centroids.append(list(vectors[first_idx]))

    for _ in range(1, k):
        # Compute squared distances to nearest centroid
        sq_distances = []
        for vec in vectors:
            min_dist = min(
                _euclidean_distance(vec, c) for c in centroids
            )
            sq_distances.append(min_dist * min_dist)

        total = sum(sq_distances)
        if total == 0.0:
            # All remaining points are identical to existing centroids
            # Pick any unselected point
            for vec in vectors:
                if list(vec) not in centroids:
                    centroids.append(list(vec))
                    break
            else:
                centroids.append(list(vectors[0]))
            continue

        # Weighted random selection
        threshold = random.random() * total
        cumulative = 0.0
        selected = 0
        for i, sq_d in enumerate(sq_distances):
            cumulative += sq_d
            if cumulative >= threshold:
                selected = i
                break

        centroids.append(list(vectors[selected]))

    return centroids


def _silhouette_score(
    vectors: list[list[float]], assignments: list[int],
) -> float:
    """Simplified silhouette score to select optimal k.

    Returns average silhouette coefficient across all points.
    Range: -1.0 to 1.0, higher is better.
    """
    n = len(vectors)
    if n <= 1:
        return 0.0

    unique_labels = set(assignments)
    if len(unique_labels) <= 1:
        return 0.0

    # Group indices by cluster
    cluster_members: dict[int, list[int]] = {}
    for i, label in enumerate(assignments):
        cluster_members.setdefault(label, []).append(i)

    total_silhouette = 0.0
    counted = 0

    for i in range(n):
        label_i = assignments[i]
        same_cluster = cluster_members[label_i]

        # a(i): mean distance to same-cluster members
        if len(same_cluster) <= 1:
            a_i = 0.0
        else:
            a_i = sum(
                _euclidean_distance(vectors[i], vectors[j])
                for j in same_cluster if j != i
            ) / (len(same_cluster) - 1)

        # b(i): min mean distance to any other cluster
        b_i = float("inf")
        for other_label, other_members in cluster_members.items():
            if other_label == label_i or not other_members:
                continue
            mean_dist = sum(
                _euclidean_distance(vectors[i], vectors[j])
                for j in other_members
            ) / len(other_members)
            if mean_dist < b_i:
                b_i = mean_dist

        if b_i == float("inf"):
            b_i = 0.0

        denom = max(a_i, b_i)
        if denom == 0.0:
            s_i = 0.0
        else:
            s_i = (b_i - a_i) / denom

        total_silhouette += s_i
        counted += 1

    return round(total_silhouette / counted if counted > 0 else 0.0, 4)


def _euclidean_distance(a: list[float], b: list[float]) -> float:
    """Euclidean distance between two vectors."""
    if len(a) != len(b):
        return float("inf")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _cosine_distance(a: list[float], b: list[float]) -> float:
    """Cosine distance for L2-normalized vectors. Returns 0.0-2.0."""
    if len(a) != len(b) or len(a) == 0:
        return 1.0  # maximum ambiguity
    dot = sum(x * y for x, y in zip(a, b))
    return round(1.0 - dot, 4)


def _vector_mean(vectors: list[list[float]]) -> list[float]:
    """Compute the element-wise mean of a list of vectors."""
    if not vectors:
        return []
    dim = len(vectors[0])
    n = len(vectors)
    result = [0.0] * dim
    for vec in vectors:
        for d in range(dim):
            result[d] += vec[d]
    return [result[d] / n for d in range(dim)]


def _all_identical(vectors: list[list[float]]) -> bool:
    """Check if all vectors are identical."""
    if len(vectors) <= 1:
        return True
    first = vectors[0]
    return all(v == first for v in vectors[1:])


def _descriptors_to_vectors(descriptors: list[dict[str, Any]]) -> list[list[float]]:
    """Convert session descriptor dicts to numeric vectors for clustering.

    Encodes categorical features as one-hot-ish numeric values.
    """
    # Collect all unique values per categorical key
    cat_keys = ["platform", "input_method", "time_bucket", "screen_class", "locale"]
    num_keys = ["session_duration", "event_count", "avg_velocity"]

    # Build vocabulary for each categorical key
    vocab: dict[str, dict[str, int]] = {}
    for key in cat_keys:
        unique_vals = sorted({
            str(d.get(key, "unknown")) for d in descriptors
        })
        vocab[key] = {val: idx for idx, val in enumerate(unique_vals)}

    vectors: list[list[float]] = []
    for desc in descriptors:
        vec: list[float] = []

        # Categorical features as one-hot
        for key in cat_keys:
            val = str(desc.get(key, "unknown"))
            n_unique = len(vocab[key])
            one_hot = [0.0] * n_unique
            idx = vocab[key].get(val, 0)
            one_hot[idx] = 1.0
            vec.extend(one_hot)

        # Numeric features (normalized with simple min-max would require
        # two passes, so just use raw values -- K-Means handles this OK
        # for our use case since we mainly care about categorical splits)
        for key in num_keys:
            val = desc.get(key, 0.0)
            vec.append(float(val) if val is not None else 0.0)

        vectors.append(vec)

    return vectors


def _build_cluster(
    *,
    session_indices: list[int],
    desc_vectors: list[list[float]],
    session_embeddings: list[list[float]],
    session_descriptors: list[dict[str, Any]],
    total_sessions: int,
) -> dict[str, Any]:
    """Build a cluster dict from assigned session indices."""
    # Descriptor-space centroid
    member_desc_vecs = [desc_vectors[i] for i in session_indices]
    centroid = _vector_mean(member_desc_vecs) if member_desc_vecs else []

    # Embedding-space centroid
    member_embeddings = [session_embeddings[i] for i in session_indices]
    embedding_centroid = _vector_mean(member_embeddings) if member_embeddings else []

    weight = round(
        len(session_indices) / total_sessions if total_sessions > 0 else 0.0,
        4,
    )

    context_proto = compute_context_prototype(session_descriptors, session_indices)

    return {
        "cluster_id": str(uuid.uuid4()),
        "centroid": [round(v, 4) for v in centroid],
        "embedding_centroid": [round(v, 4) for v in embedding_centroid],
        "session_indices": list(session_indices),
        "weight": weight,
        "context_prototype": context_proto,
    }


def _merge_two_clusters(
    target: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    """Merge source cluster into target. Returns new dict."""
    merged_indices = list(target.get("session_indices", [])) + list(
        source.get("session_indices", [])
    )

    # Weighted average of embedding centroids
    t_emb = target.get("embedding_centroid", [])
    s_emb = source.get("embedding_centroid", [])
    t_count = len(target.get("session_indices", []))
    s_count = len(source.get("session_indices", []))
    total = t_count + s_count

    if t_emb and s_emb and len(t_emb) == len(s_emb) and total > 0:
        merged_emb = [
            round((t_emb[d] * t_count + s_emb[d] * s_count) / total, 4)
            for d in range(len(t_emb))
        ]
    elif t_emb:
        merged_emb = list(t_emb)
    else:
        merged_emb = list(s_emb) if s_emb else []

    # Weighted average of descriptor centroids
    t_cen = target.get("centroid", [])
    s_cen = source.get("centroid", [])
    if t_cen and s_cen and len(t_cen) == len(s_cen) and total > 0:
        merged_cen = [
            round((t_cen[d] * t_count + s_cen[d] * s_count) / total, 4)
            for d in range(len(t_cen))
        ]
    elif t_cen:
        merged_cen = list(t_cen)
    else:
        merged_cen = list(s_cen) if s_cen else []

    return {
        "cluster_id": target.get("cluster_id", str(uuid.uuid4())),
        "centroid": merged_cen,
        "embedding_centroid": merged_emb,
        "session_indices": merged_indices,
        "weight": target.get("weight", 0.0),  # recalculated by caller
        "context_prototype": target.get("context_prototype", {}),
    }


def _percentile(sorted_values: list[float], p: float) -> float:
    """Compute the p-th percentile from a sorted list (0.0 <= p <= 1.0)."""
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    rank = p * (n - 1)
    low = int(math.floor(rank))
    high = min(low + 1, n - 1)
    frac = rank - low
    return sorted_values[low] + frac * (sorted_values[high] - sorted_values[low])
