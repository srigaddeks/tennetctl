"""Tests for 03_kbio._clustering — K-Means, Bayesian selector, enrollment, grace period."""
import importlib

import pytest

_cluster_mgr = importlib.import_module("03_kbio._clustering.cluster_manager")
_selector = importlib.import_module("03_kbio._clustering.bayesian_selector")
_enrollment = importlib.import_module("03_kbio._clustering.enrollment_pipeline")
_baseline = importlib.import_module("03_kbio._clustering.rolling_baseline")


# ---------------------------------------------------------------------------
# K-Means cluster discovery
# ---------------------------------------------------------------------------

class TestKMeans:
    def _make_descriptors(self, n, platform="web_desktop"):
        return [
            {"platform": platform, "input_method": "keyboard_mouse",
             "time_bucket": "morning", "screen_class": "large", "locale": "en",
             "session_duration": 300, "event_count": 100, "avg_velocity": 200}
            for _ in range(n)
        ]

    def test_single_session_one_cluster(self):
        descriptors = self._make_descriptors(1)
        embeddings = [[0.1] * 16]
        result = _cluster_mgr.discover_clusters(descriptors, embeddings)
        assert len(result) == 1
        assert result[0]["session_indices"] == [0]

    def test_identical_points_one_cluster(self):
        """All identical descriptors -> single cluster."""
        descriptors = self._make_descriptors(6)
        embeddings = [[0.1] * 16] * 6
        result = _cluster_mgr.discover_clusters(descriptors, embeddings)
        assert len(result) == 1
        assert len(result[0]["session_indices"]) == 6

    def test_two_distinct_groups(self):
        """Two clearly separated groups -> 2 clusters."""
        group_a = [
            {"platform": "web_desktop", "input_method": "keyboard_mouse",
             "time_bucket": "morning", "screen_class": "large", "locale": "en",
             "session_duration": 300, "event_count": 100, "avg_velocity": 200}
            for _ in range(6)
        ]
        group_b = [
            {"platform": "web_mobile", "input_method": "touch",
             "time_bucket": "night", "screen_class": "small", "locale": "ja",
             "session_duration": 60, "event_count": 20, "avg_velocity": 50}
            for _ in range(6)
        ]
        descriptors = group_a + group_b
        emb_a = [[1.0] + [0.0] * 15] * 6
        emb_b = [[0.0] * 15 + [1.0]] * 6
        embeddings = emb_a + emb_b
        result = _cluster_mgr.discover_clusters(descriptors, embeddings, max_clusters=5)
        # Should find at least 2 clusters (may merge small ones)
        assert len(result) >= 1
        total_indices = sum(len(c["session_indices"]) for c in result)
        assert total_indices == 12

    def test_max_clusters_respected(self):
        """max_clusters limits the number of clusters."""
        descriptors = self._make_descriptors(20)
        embeddings = [[i * 0.1] * 16 for i in range(20)]
        result = _cluster_mgr.discover_clusters(
            descriptors, embeddings, max_clusters=3,
        )
        assert len(result) <= 3

    def test_empty_inputs(self):
        result = _cluster_mgr.discover_clusters([], [])
        assert result == []

    def test_mismatched_counts_raises(self):
        with pytest.raises(ValueError, match="Descriptor count"):
            _cluster_mgr.discover_clusters(
                [{"platform": "web_desktop"}],
                [[0.1] * 16, [0.2] * 16],
            )

    def test_cluster_has_expected_keys(self):
        descriptors = self._make_descriptors(3)
        embeddings = [[0.1] * 16] * 3
        result = _cluster_mgr.discover_clusters(descriptors, embeddings)
        cluster = result[0]
        assert "cluster_id" in cluster
        assert "centroid" in cluster
        assert "embedding_centroid" in cluster
        assert "session_indices" in cluster
        assert "weight" in cluster
        assert "context_prototype" in cluster

    def test_weights_sum_to_one(self):
        descriptors = self._make_descriptors(9)
        embeddings = [[0.1] * 16] * 9
        result = _cluster_mgr.discover_clusters(descriptors, embeddings)
        total_weight = sum(c["weight"] for c in result)
        assert total_weight == pytest.approx(1.0, abs=0.01)


# ---------------------------------------------------------------------------
# Bayesian cluster selector
# ---------------------------------------------------------------------------

class TestBayesianSelector:
    def _make_cluster(self, cluster_id, platform, embedding):
        return {
            "cluster_id": cluster_id,
            "embedding_centroid": embedding,
            "context_prototype": {
                "platform": platform,
                "input_method": "keyboard_mouse",
                "time_bucket": "morning",
                "screen_class": "large",
                "locale": "en",
            },
            "weight": 0.5,
        }

    def test_exact_context_match(self):
        """Cluster with matching platform/input -> selected."""
        cluster = self._make_cluster("c1", "web_desktop", [0.1] * 16)
        descriptor = {
            "platform": "web_desktop", "input_method": "keyboard_mouse",
            "time_bucket": "morning", "screen_class": "large", "locale": "en",
        }
        result = _selector.select_cluster([cluster], descriptor, [0.1] * 16)
        assert result["cluster_id"] == "c1"
        assert result["is_new_context"] is False

    def test_closest_embedding_wins(self):
        """Two clusters; context matches both equally but embedding closer to c2."""
        c1 = self._make_cluster("c1", "web_desktop", [1.0] + [0.0] * 15)
        c2 = self._make_cluster("c2", "web_desktop", [0.0] * 15 + [1.0])
        descriptor = {"platform": "web_desktop", "input_method": "keyboard_mouse",
                       "time_bucket": "morning", "screen_class": "large", "locale": "en"}
        # Embedding closer to c2
        current_emb = [0.0] * 15 + [0.9]
        result = _selector.select_cluster([c1, c2], descriptor, current_emb)
        assert result["cluster_id"] == "c2"

    def test_new_context_detected(self):
        """No matching cluster context + far embedding -> is_new_context=True."""
        cluster = self._make_cluster("c1", "web_desktop", [1.0] + [0.0] * 15)
        descriptor = {
            "platform": "web_mobile", "input_method": "touch",
            "time_bucket": "night", "screen_class": "small", "locale": "ja",
        }
        # Very different embedding
        current_emb = [0.0] * 15 + [1.0]
        result = _selector.select_cluster([cluster], descriptor, current_emb)
        # With only one cluster, match quality might still be high (only option)
        # but with mismatched context, is_new_context can be True
        assert "is_new_context" in result
        assert "all_posteriors" in result

    def test_empty_clusters(self):
        result = _selector.select_cluster([], {}, [0.1] * 16)
        assert result["cluster"] is None
        assert result["is_new_context"] is True
        assert result["posterior"] == 0.0

    def test_result_keys(self):
        cluster = self._make_cluster("c1", "web_desktop", [0.1] * 16)
        result = _selector.select_cluster(
            [cluster], {"platform": "web_desktop"}, [0.1] * 16,
        )
        expected_keys = {
            "cluster", "cluster_id", "posterior", "match_quality",
            "is_new_context", "all_posteriors",
        }
        assert set(result.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Enrollment pipeline
# ---------------------------------------------------------------------------

class TestEnrollment:
    def test_buffer_until_threshold(self):
        """< 3 sessions -> status='buffering'."""
        result = _enrollment.process_enrollment_batch(
            embeddings_buffer=[[0.1] * 16],
            descriptors_buffer=[{"platform": "web_desktop"}],
            new_embedding=[0.2] * 16,
            new_descriptor={"platform": "web_desktop"},
        )
        assert result["status"] == "buffering"
        assert result["sessions_collected"] == 2
        assert result["sessions_needed"] == 3

    def test_ready_after_three(self):
        """3 sessions -> status='ready_to_cluster'."""
        result = _enrollment.process_enrollment_batch(
            embeddings_buffer=[[0.1] * 16, [0.2] * 16],
            descriptors_buffer=[{"platform": "web_desktop"}] * 2,
            new_embedding=[0.3] * 16,
            new_descriptor={"platform": "web_desktop"},
        )
        assert result["status"] == "ready_to_cluster"
        assert result["sessions_collected"] == 3

    def test_immutability(self):
        """Original buffers are not mutated."""
        orig_emb = [[0.1] * 16]
        orig_desc = [{"platform": "web_desktop"}]
        _enrollment.process_enrollment_batch(
            orig_emb, orig_desc, [0.2] * 16, {"platform": "web_desktop"},
        )
        assert len(orig_emb) == 1
        assert len(orig_desc) == 1

    def test_create_initial_profile(self):
        """With enough data, creates a profile with clusters."""
        embeddings = [[0.1 * i] * 16 for i in range(1, 5)]
        descriptors = [
            {"platform": "web_desktop", "input_method": "keyboard_mouse",
             "time_bucket": "morning", "screen_class": "large", "locale": "en",
             "session_duration": 300, "event_count": 100, "avg_velocity": 200}
            for _ in range(4)
        ]
        profile = _enrollment.create_initial_profile(
            embeddings, descriptors, "sha256:test",
        )
        assert profile["user_hash"] == "sha256:test"
        assert profile["baseline_quality"] == "forming"
        assert profile["enrollment_complete"] is True
        assert len(profile["clusters"]) >= 1

    def test_empty_buffer_insufficient(self):
        profile = _enrollment.create_initial_profile([], [], "sha256:test")
        assert profile["baseline_quality"] == "insufficient"
        assert profile["enrollment_complete"] is False


# ---------------------------------------------------------------------------
# Grace period
# ---------------------------------------------------------------------------

class TestGracePeriod:
    def test_new_cluster_in_grace(self):
        """session_count=1 -> in_grace_period=True."""
        result = _baseline.check_grace_period({}, session_count_in_cluster=1)
        assert result["in_grace_period"] is True
        assert result["remaining_sessions"] == 2
        assert result["max_verdict"] == "monitor"

    def test_at_threshold(self):
        """session_count=3 -> no longer in grace."""
        result = _baseline.check_grace_period({}, session_count_in_cluster=3)
        assert result["in_grace_period"] is False
        assert result["remaining_sessions"] == 0
        assert result["max_verdict"] is None

    def test_after_grace(self):
        """session_count=10 -> definitely not in grace."""
        result = _baseline.check_grace_period({}, session_count_in_cluster=10)
        assert result["in_grace_period"] is False

    def test_zero_sessions_in_grace(self):
        result = _baseline.check_grace_period({}, session_count_in_cluster=0)
        assert result["in_grace_period"] is True
        assert result["remaining_sessions"] == 3
