#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v175 - FederationProtocol Tests

Tests:
- register_agent_card
- discover_capabilities
- delegate_cross_repo_task
- share_knowledge
- compute_federation_health
- detect_federation_anomaly
- get_status
- singleton
"""

import pytest
import sys
import os

# Ensure core module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.federation_protocol import (
    FederationProtocol,
    get_federation_protocol,
    AgentCard,
    Task,
    KnowledgePacket,
    FEDERATION_HEALTH_LEVELS,
    KNOWLEDGE_TYPES,
    SHARING_LEVELS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def fresh_protocol():
    """Return a fresh FederationProtocol instance."""
    return FederationProtocol()


@pytest.fixture
def populated_protocol(fresh_protocol):
    """Return a protocol with sample repos registered."""
    proto = fresh_protocol
    proto.register_agent_card(
        repo_name="repo-alpha",
        capabilities=["data-processing", "ml-inference", "vector-search"],
        endpoints={"rest": "http://alpha.local:8080", "grpc": "alpha.local:50051"},
        version="2.1.0",
    )
    proto.register_agent_card(
        repo_name="repo-beta",
        capabilities=["ml-inference", "model-training", "gpu-scheduling"],
        endpoints={"rest": "http://beta.local:8080"},
        version="1.5.0",
    )
    proto.register_agent_card(
        repo_name="repo-gamma",
        capabilities=["vector-search", "indexing", "data-processing"],
        endpoints={"rest": "http://gamma.local:8080"},
        version="3.0.0",
    )
    return proto


# ---------------------------------------------------------------------------
# register_agent_card
# ---------------------------------------------------------------------------
class TestRegisterAgentCard:
    def test_register_basic(self, fresh_protocol):
        proto = fresh_protocol
        result = proto.register_agent_card(
            repo_name="test-repo",
            capabilities=["cap-a", "cap-b"],
            endpoints={"api": "http://test.local"},
        )
        assert result["success"] is True
        assert result["repo_name"] == "test-repo"
        assert result["card"]["name"] == "test-repo"
        assert result["card"]["capabilities"] == ["cap-a", "cap-b"]
        assert result["card"]["endpoints"]["api"] == "http://test.local"
        assert result["card"]["health"] == 1.0

    def test_register_invalid_repo_name(self, fresh_protocol):
        proto = fresh_protocol
        result = proto.register_agent_card(
            repo_name="",
            capabilities=["cap-a"],
            endpoints={},
        )
        assert result["success"] is False
        assert "error" in result

    def test_register_invalid_capabilities(self, fresh_protocol):
        proto = fresh_protocol
        result = proto.register_agent_card(
            repo_name="repo-x",
            capabilities="not-a-list",
            endpoints={},
        )
        assert result["success"] is False

    def test_register_invalid_endpoints(self, fresh_protocol):
        proto = fresh_protocol
        result = proto.register_agent_card(
            repo_name="repo-x",
            capabilities=["cap-a"],
            endpoints="not-a-dict",
        )
        assert result["success"] is False

    def test_capability_registry_updated(self, fresh_protocol):
        proto = fresh_protocol
        proto.register_agent_card(
            repo_name="repo-x",
            capabilities=["search", "index"],
            endpoints={},
        )
        assert "search" in proto.capability_registry
        assert "index" in proto.capability_registry
        assert "repo-x" in proto.capability_registry["search"]


# ---------------------------------------------------------------------------
# discover_capabilities
# ---------------------------------------------------------------------------
class TestDiscoverCapabilities:
    def test_discover_exact_match(self, populated_protocol):
        proto = populated_protocol
        results = proto.discover_capabilities("ml-inference")
        assert len(results) >= 2
        # repo-alpha and repo-beta both have ml-inference
        names = [r["repo_name"] for r in results]
        assert "repo-alpha" in names
        assert "repo-beta" in names

    def test_discover_no_match(self, populated_protocol):
        proto = populated_protocol
        results = proto.discover_capabilities("quantum-computing")
        assert results == []

    def test_discover_multiple_tokens(self, populated_protocol):
        proto = populated_protocol
        results = proto.discover_capabilities("data-processing vector-search")
        # repo-alpha and repo-gamma both match both
        names = [r["repo_name"] for r in results]
        assert "repo-alpha" in names
        assert "repo-gamma" in names

    def test_discover_returns_scores(self, populated_protocol):
        proto = populated_protocol
        results = proto.discover_capabilities("ml-inference")
        for r in results:
            assert "match_score" in r
            assert "jaccard" in r
            assert "health" in r
            assert "recency" in r
            assert 0.0 <= r["match_score"] <= 1.0

    def test_discover_sorted_by_score(self, populated_protocol):
        proto = populated_protocol
        results = proto.discover_capabilities("ml-inference")
        scores = [r["match_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_discover_empty_query(self, populated_protocol):
        proto = populated_protocol
        assert proto.discover_capabilities("") == []
        assert proto.discover_capabilities("   ") == []


# ---------------------------------------------------------------------------
# delegate_cross_repo_task
# ---------------------------------------------------------------------------
class TestDelegateCrossRepoTask:
    def test_delegate_success(self, populated_protocol):
        proto = populated_protocol
        result = proto.delegate_cross_repo_task(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            task={
                "type": "ml-inference",
                "payload": {"model": "resnet50", "batch_size": 32},
                "priority": 7,
                "timeout": 60.0,
                "callback": "http://alpha.local/callback",
            },
        )
        assert result["success"] is True
        assert result["task_id"] is not None
        assert result["status"] == "completed"
        assert "result" in result
        assert "flow" in result
        assert result["flow"] == ["discover", "negotiate", "execute", "verify", "callback"]

    def test_delegate_source_not_found(self, populated_protocol):
        proto = populated_protocol
        result = proto.delegate_cross_repo_task(
            from_repo="nonexistent",
            to_repo="repo-beta",
            task={"type": "test"},
        )
        assert result["success"] is False
        assert "source_repo_not_found" in result["error"]

    def test_delegate_target_not_found(self, populated_protocol):
        proto = populated_protocol
        result = proto.delegate_cross_repo_task(
            from_repo="repo-alpha",
            to_repo="nonexistent",
            task={"type": "test"},
        )
        assert result["success"] is False
        assert "target_repo_not_found" in result["error"]

    def test_delegate_invalid_task_format(self, populated_protocol):
        proto = populated_protocol
        result = proto.delegate_cross_repo_task(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            task="not-a-dict",
        )
        assert result["success"] is False
        assert "invalid_task_format" in result["error"]

    def test_delegate_task_tracked(self, populated_protocol):
        proto = populated_protocol
        result = proto.delegate_cross_repo_task(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            task={"type": "test"},
        )
        task_id = result["task_id"]
        assert task_id in proto.tasks
        task_obj = proto.tasks[task_id]
        assert task_obj.from_repo == "repo-alpha"
        assert task_obj.to_repo == "repo-beta"

    def test_delegate_default_task_values(self, populated_protocol):
        proto = populated_protocol
        result = proto.delegate_cross_repo_task(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            task={},
        )
        assert result["success"] is True
        task_id = result["task_id"]
        assert proto.tasks[task_id].task_type == "generic"
        assert proto.tasks[task_id].priority == 5
        assert proto.tasks[task_id].timeout == 30.0


# ---------------------------------------------------------------------------
# share_knowledge
# ---------------------------------------------------------------------------
class TestShareKnowledge:
    def test_share_unicast(self, populated_protocol):
        proto = populated_protocol
        result = proto.share_knowledge(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            knowledge={
                "type": "insight",
                "content": {"key": "value"},
                "sharing_level": "unicast",
            },
        )
        assert result["success"] is True
        assert result["recipients"] == ["repo-beta"]
        assert result["knowledge_type"] == "insight"
        assert result["sharing_level"] == "unicast"
        assert result["packet_count"] == 1

    def test_share_broadcast(self, populated_protocol):
        proto = populated_protocol
        result = proto.share_knowledge(
            from_repo="repo-alpha",
            to_repo="*",
            knowledge={
                "type": "pattern",
                "content": {"alert": "new-pattern"},
                "sharing_level": "broadcast",
            },
        )
        assert result["success"] is True
        assert "repo-beta" in result["recipients"]
        assert "repo-gamma" in result["recipients"]
        assert "repo-alpha" not in result["recipients"]
        assert result["packet_count"] == 2

    def test_share_multicast(self, populated_protocol):
        proto = populated_protocol
        result = proto.share_knowledge(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            knowledge={
                "type": "warning",
                "content": {"cpu": "high"},
                "sharing_level": "multicast",
            },
        )
        assert result["success"] is True
        # Should share to repos with overlapping capabilities
        # repo-alpha has [data-processing, ml-inference, vector-search]
        # repo-beta shares ml-inference
        # repo-gamma shares data-processing and vector-search
        assert len(result["recipients"]) >= 1

    def test_share_private(self, populated_protocol):
        proto = populated_protocol
        result = proto.share_knowledge(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            knowledge={
                "type": "opportunity",
                "content": {"secret": "internal"},
                "sharing_level": "private",
            },
        )
        assert result["success"] is True
        assert result["recipients"] == ["repo-alpha"]

    def test_share_invalid_source(self, populated_protocol):
        proto = populated_protocol
        result = proto.share_knowledge(
            from_repo="nonexistent",
            to_repo="repo-beta",
            knowledge={"type": "insight"},
        )
        assert result["success"] is False

    def test_share_invalid_knowledge_format(self, populated_protocol):
        proto = populated_protocol
        result = proto.share_knowledge(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            knowledge="not-a-dict",
        )
        assert result["success"] is False

    def test_share_unknown_knowledge_type_defaults(self, populated_protocol):
        proto = populated_protocol
        result = proto.share_knowledge(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            knowledge={
                "type": "unknown-type",
                "content": {},
            },
        )
        assert result["success"] is True
        assert result["knowledge_type"] == "insight"

    def test_share_unknown_sharing_level_defaults(self, populated_protocol):
        proto = populated_protocol
        result = proto.share_knowledge(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            knowledge={
                "type": "insight",
                "content": {},
                "sharing_level": "unknown-level",
            },
        )
        assert result["success"] is True
        assert result["sharing_level"] == "unicast"

    def test_knowledge_ledger_populated(self, populated_protocol):
        proto = populated_protocol
        before = len(proto.knowledge_ledger)
        proto.share_knowledge(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            knowledge={"type": "insight", "content": {"a": 1}},
        )
        after = len(proto.knowledge_ledger)
        assert after > before


# ---------------------------------------------------------------------------
# compute_federation_health
# ---------------------------------------------------------------------------
class TestComputeFederationHealth:
    def test_health_empty_federation(self, fresh_protocol):
        proto = fresh_protocol
        health = proto.compute_federation_health()
        assert health["overall_score"] == 0.0
        assert health["level"] == "fractured"
        assert "register_agent_cards" in health["recommendations"]

    def test_health_populated(self, populated_protocol):
        proto = populated_protocol
        health = proto.compute_federation_health()
        assert 0.0 <= health["overall_score"] <= 1.0
        assert health["level"] in [l[1] for l in FEDERATION_HEALTH_LEVELS]
        assert "factors" in health
        factors = health["factors"]
        assert "connected_nodes" in factors
        assert "avg_latency_ms" in factors
        assert "task_success_rate" in factors
        assert "knowledge_flow_rate" in factors

    def test_health_levels(self, populated_protocol):
        proto = populated_protocol
        health = proto.compute_federation_health()
        level = health["level"]
        score = health["overall_score"]
        if score > 0.9:
            assert level == "thriving"
        elif score > 0.7:
            assert level == "healthy"
        elif score > 0.5:
            assert level == "stable"
        elif score > 0.3:
            assert level == "degraded"
        else:
            assert level == "fractured"

    def test_health_after_task(self, populated_protocol):
        proto = populated_protocol
        proto.delegate_cross_repo_task(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            task={"type": "test"},
        )
        health = proto.compute_federation_health()
        assert health["factors"]["total_tasks"] >= 1

    def test_health_after_knowledge(self, populated_protocol):
        proto = populated_protocol
        proto.share_knowledge(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            knowledge={"type": "insight", "content": {}},
        )
        health = proto.compute_federation_health()
        assert health["factors"]["knowledge_flow_rate"] >= 0.0


# ---------------------------------------------------------------------------
# detect_federation_anomaly
# ---------------------------------------------------------------------------
class TestDetectFederationAnomaly:
    def test_anomaly_empty(self, fresh_protocol):
        proto = fresh_protocol
        result = proto.detect_federation_anomaly()
        assert result["anomaly_detected"] is False
        assert result["anomaly_count"] == 0
        assert result["severity"] == "none"

    def test_anomaly_no_failure(self, populated_protocol):
        proto = populated_protocol
        result = proto.detect_federation_anomaly()
        # Freshly registered nodes should not show node_failure
        assert result["severity"] in ("none", "info")

    def test_anomaly_tracked(self, populated_protocol):
        proto = populated_protocol
        before = len(proto.anomaly_history)
        proto.detect_federation_anomaly()
        after = len(proto.anomaly_history)
        assert after > before

    def test_anomaly_types_valid(self, populated_protocol):
        proto = populated_protocol
        result = proto.detect_federation_anomaly()
        for anomaly in result["anomalies"]:
            assert anomaly["type"] in {
                "node_failure",
                "communication_degradation",
                "knowledge_stagnation",
                "security_breach",
            }
            assert anomaly["severity"] in {"info", "warning", "critical"}


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------
class TestGetStatus:
    def test_status_empty(self, fresh_protocol):
        proto = fresh_protocol
        status = proto.get_status()
        assert status["registered_nodes"] == 0
        assert status["active_connections"] == 0
        assert status["task_count"] == 0
        assert status["health_score"] == 0.0
        assert status["protocol_version"] == "175.0"

    def test_status_populated(self, populated_protocol):
        proto = populated_protocol
        status = proto.get_status()
        assert status["registered_nodes"] == 3
        assert status["active_connections"] == 3
        assert status["task_count"] == 0
        assert status["knowledge_packets"] == 0
        assert status["anomalies_detected"] == 0
        assert status["uptime_seconds"] >= 0.0

    def test_status_after_activity(self, populated_protocol):
        proto = populated_protocol
        proto.delegate_cross_repo_task(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            task={"type": "test"},
        )
        proto.share_knowledge(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            knowledge={"type": "insight", "content": {}},
        )
        proto.detect_federation_anomaly()
        status = proto.get_status()
        assert status["task_count"] == 1
        assert status["knowledge_packets"] == 1
        assert status["anomalies_detected"] == 1


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_singleton_identity(self):
        proto1 = get_federation_protocol()
        proto2 = get_federation_protocol()
        assert proto1 is proto2

    def test_singleton_is_federation_protocol(self):
        proto = get_federation_protocol()
        assert isinstance(proto, FederationProtocol)


# ---------------------------------------------------------------------------
# Edge cases & Defensive programming
# ---------------------------------------------------------------------------
class TestEdgeCases:
    def test_multiple_registrations_same_repo(self, fresh_protocol):
        proto = fresh_protocol
        proto.register_agent_card("repo-x", ["a", "b"], {})
        proto.register_agent_card("repo-x", ["b", "c"], {})
        assert len(proto.agent_cards) == 1
        # Latest registration wins
        assert set(proto.agent_cards["repo-x"].capabilities) == {"b", "c"}

    def test_discover_with_special_chars(self, populated_protocol):
        proto = populated_protocol
        # Should not crash with special characters
        results = proto.discover_capabilities("!@#$%")
        assert isinstance(results, list)

    def test_task_with_negative_priority(self, populated_protocol):
        proto = populated_protocol
        result = proto.delegate_cross_repo_task(
            from_repo="repo-alpha",
            to_repo="repo-beta",
            task={"priority": -5},
        )
        assert result["success"] is True
        assert proto.tasks[result["task_id"]].priority == -5

    def test_health_recommendations(self, populated_protocol):
        proto = populated_protocol
        # Ensure recommendations exist for various states
        health = proto.compute_federation_health()
        assert len(health["recommendations"]) >= 1
