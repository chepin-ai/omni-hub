"""
Tests for OMNI-HUB v150 — Universal Federation (全域联邦).

Coverage:
* Singleton lifecycle
* Node join federation (all recognised types + unknown)
* Broadcast messaging
* Governance voting (majority, minority, tie, empty)
* Federation health computation
* Status aggregation
* Defensive behaviour (duplicate joins, broadcast from non-member, invalid input)
"""

import pytest
from core.universal_federation import (
    UniversalFederation,
    get_universal_federation,
    NodeType,
    FederationLevel,
    DEFAULT_CHARTER,
    _module,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton before every test to avoid cross-test leakage."""
    import core.universal_federation as uf

    uf._module = None
    yield
    uf._module = None


@pytest.fixture
def fresh_fed():
    """Return a pristine ``UniversalFederation`` instance."""
    return UniversalFederation()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
def test_singleton_returns_same_instance():
    a = get_universal_federation()
    b = get_universal_federation()
    assert a is b


def test_singleton_is_initially_none():
    import core.universal_federation as uf

    assert uf._module is None


# ---------------------------------------------------------------------------
# join_federation
# ---------------------------------------------------------------------------
def test_join_basic(fresh_fed):
    result = fresh_fed.join_federation("node-1", "internal_line", ["compute", "store"])
    assert result["success"] is True
    assert result["node_id"] == "node-1"
    assert result["node_count"] == 1
    assert result["federation_level"] == FederationLevel.NASCENT.value


def test_join_all_node_types(fresh_fed):
    types = [
        NodeType.INTERNAL_LINE,
        NodeType.EXTERNAL_REPO,
        NodeType.AI_PEER,
        NodeType.HUMAN_USER,
        NodeType.UNKNOWN,
    ]
    for i, nt in enumerate(types, 1):
        res = fresh_fed.join_federation(f"n{i}", nt.value, ["cap"])
        assert res["success"] is True
        assert fresh_fed.nodes[f"n{i}"]["node_type"] == nt.value


def test_join_unknown_type_fallback(fresh_fed):
    res = fresh_fed.join_federation("x1", "sentient_cloud", ["rain"])
    assert res["success"] is True
    assert fresh_fed.nodes["x1"]["node_type"] == NodeType.UNKNOWN.value


def test_join_duplicate_rejected(fresh_fed):
    fresh_fed.join_federation("dup", "internal_line", [])
    res = fresh_fed.join_federation("dup", "internal_line", [])
    assert res["success"] is False
    assert "already" in res["error"].lower()


def test_join_empty_node_id_rejected(fresh_fed):
    res = fresh_fed.join_federation("", "internal_line", [])
    assert res["success"] is False
    assert "node_id" in res["error"].lower()


def test_join_federation_levels(fresh_fed):
    """Exercise level thresholds: nascent -> seed -> growing -> expansive -> universal."""
    levels_seen = []
    for i in range(1, 102):
        res = fresh_fed.join_federation(f"n{i}", "ai_peer", ["chat"])
        levels_seen.append(res["federation_level"])

    assert levels_seen[4] == FederationLevel.NASCENT.value    # 5 nodes  -> nascent (threshold is >5)
    assert levels_seen[5] == FederationLevel.SEED.value       # 6 nodes  -> seed
    assert levels_seen[19] == FederationLevel.SEED.value      # 20 nodes -> seed (threshold is >20)
    assert levels_seen[20] == FederationLevel.GROWING.value   # 21 nodes -> growing
    assert levels_seen[49] == FederationLevel.GROWING.value   # 50 nodes -> growing (threshold is >50)
    assert levels_seen[50] == FederationLevel.EXPANSIVE.value # 51 nodes -> expansive
    assert levels_seen[99] == FederationLevel.EXPANSIVE.value # 100 nodes -> expansive (threshold is >100)
    assert levels_seen[100] == FederationLevel.UNIVERSAL.value # 101 nodes -> universal


# ---------------------------------------------------------------------------
# broadcast
# ---------------------------------------------------------------------------
def test_broadcast_basic(fresh_fed):
    fresh_fed.join_federation("alpha", "internal_line", [])
    fresh_fed.join_federation("beta", "external_repo", [])
    fresh_fed.join_federation("gamma", "human_user", [])

    result = fresh_fed.broadcast("alpha", {"text": "hello federation"})
    assert result["success"] is True
    assert result["recipients"] == 2
    assert "message_id" in result

    # Verify side-effects
    assert fresh_fed.nodes["alpha"]["messages_sent"] == 1
    assert fresh_fed.nodes["beta"]["messages_received"] == 1
    assert fresh_fed.nodes["gamma"]["messages_received"] == 1


def test_broadcast_from_non_member_rejected(fresh_fed):
    res = fresh_fed.broadcast("impostor", {"text": "foo"})
    assert res["success"] is False
    assert "not a federation member" in res["error"].lower()


def test_broadcast_to_empty_federation(fresh_fed):
    fresh_fed.join_federation("lonely", "internal_line", [])
    res = fresh_fed.broadcast("lonely", {"text": "echo"})
    assert res["success"] is True
    assert res["recipients"] == 0


# ---------------------------------------------------------------------------
# governance_vote
# ---------------------------------------------------------------------------
def test_governance_majority_passes(fresh_fed):
    for i in range(1, 4):
        fresh_fed.join_federation(f"n{i}", "ai_peer", [])
    votes = {"n1": True, "n2": True, "n3": False}
    res = fresh_fed.governance_vote("Expand charter", votes)
    assert res["success"] is True
    assert res["passed"] is True
    assert res["yes"] == 2
    assert res["no"] == 1
    assert res["participation_rate"] == 1.0


def test_governance_minority_fails(fresh_fed):
    for i in range(1, 4):
        fresh_fed.join_federation(f"n{i}", "human_user", [])
    votes = {"n1": False, "n2": False, "n3": True}
    res = fresh_fed.governance_vote("Shutdown", votes)
    assert res["passed"] is False
    assert res["yes"] == 1
    assert res["no"] == 2


def test_governance_tie_fails(fresh_fed):
    for i in range(1, 5):
        fresh_fed.join_federation(f"n{i}", "internal_line", [])
    votes = {"n1": True, "n2": True, "n3": False, "n4": False}
    res = fresh_fed.governance_vote("Neutral proposal", votes)
    assert res["passed"] is False  # tie -> not > 50 %
    assert res["yes"] == 2
    assert res["no"] == 2


def test_governance_empty_votes(fresh_fed):
    fresh_fed.join_federation("only", "unknown", [])
    res = fresh_fed.governance_vote("Ghost proposal", {})
    assert res["success"] is True
    assert res["passed"] is False
    assert res["yes"] == 0
    assert res["no"] == 0
    assert res["participation_rate"] == 0.0


def test_governance_ignores_invalid_voters(fresh_fed):
    fresh_fed.join_federation("a", "ai_peer", [])
    res = fresh_fed.governance_vote("X", {"a": True, "b": False})
    assert res["success"] is True
    assert res["yes"] == 1
    assert res["no"] == 0


def test_governance_invalid_proposal_rejected(fresh_fed):
    res = fresh_fed.governance_vote("", {"a": True})
    assert res["success"] is False
    assert "proposal" in res["error"].lower()


# ---------------------------------------------------------------------------
# compute_federation_health
# ---------------------------------------------------------------------------
def test_health_empty_federation():
    fed = UniversalFederation()
    h = fed.compute_federation_health()
    assert h["score"] == 0.0
    assert h["status"] == "empty"


def test_health_improves_with_nodes_and_messages(fresh_fed):
    fresh_fed.join_federation("n1", "internal_line", ["c1"])
    h1 = fresh_fed.compute_federation_health()
    assert h1["status"] in ("critical", "fragile", "stable")

    # Add more nodes to push node_count_score
    for i in range(2, 51):
        fresh_fed.join_federation(f"n{i}", "ai_peer", [])

    # Simulate connectivity via broadcasts
    for _ in range(10):
        fresh_fed.broadcast("n1", {"ping": "pong"})

    # Add a successful vote to boost consensus
    votes = {f"n{i}": True for i in range(1, 26)}
    fresh_fed.governance_vote("Unity", votes)

    h2 = fresh_fed.compute_federation_health()
    assert h2["score"] > h1["score"]
    assert h2["components"]["node_count_score"] == 0.5  # 50 / 100
    assert h2["status"] in ("stable", "healthy", "radiant")


def test_health_consensus_history(fresh_fed):
    fresh_fed.join_federation("a", "internal_line", [])
    fresh_fed.join_federation("b", "internal_line", [])
    # Two votes: one unanimous, one split
    fresh_fed.governance_vote("P1", {"a": True, "b": True})
    fresh_fed.governance_vote("P2", {"a": False, "b": True})
    h = fresh_fed.compute_federation_health()
    # consensus history = [1.0, 0.5] -> average 0.75
    assert h["components"]["consensus_score"] == 0.75


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------
def test_status_shape(fresh_fed):
    fresh_fed.join_federation("n1", "internal_line", ["x"])
    fresh_fed.join_federation("n2", "human_user", ["y"])
    s = fresh_fed.get_status()
    assert s["node_count"] == 2
    assert s["federation_level"] == FederationLevel.NASCENT.value
    assert s["charter_adopted"] is True
    assert s["active_proposals"] == 0
    assert s["closed_proposals_count"] == 0
    assert "health" in s
    assert s["node_type_breakdown"] == {
        NodeType.INTERNAL_LINE.value: 1,
        NodeType.HUMAN_USER.value: 1,
    }


def test_status_after_vote(fresh_fed):
    fresh_fed.join_federation("a", "ai_peer", [])
    fresh_fed.governance_vote("Q", {"a": True})
    s = fresh_fed.get_status()
    assert s["closed_proposals_count"] == 1


# ---------------------------------------------------------------------------
# Charter immutability guard
# ---------------------------------------------------------------------------
def test_charter_deep_copied(fresh_fed):
    mutable_charter = {
        "principles": {"autonomy": "original"},
        "adoption_date": "2024-01-01T00:00:00Z",
    }
    fed = UniversalFederation(charter=mutable_charter)
    mutable_charter["principles"]["autonomy"] = "tampered"
    assert fed.charter["principles"]["autonomy"] == "original"


# ---------------------------------------------------------------------------
# Event bus stub safety
# ---------------------------------------------------------------------------
def test_emit_event_stub_does_not_crash(fresh_fed):
    # The stub should be callable and not raise.
    fresh_fed._emit_event("test.event", {"foo": "bar"})
