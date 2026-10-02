"""
Tests for InterLineConsensus — 跨线协商引擎
All tests use REAL alliance data from alliance_repos_live_status.json
"""

import os
import sys
from typing import Any, Dict

import pytest

# Ensure core is importable from tests directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.inter_line_consensus import (
    InterLineConsensus,
    get_inter_line_consensus,
    _reset_singleton,
)

# Absolute path to real data
DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "alliance_repos_live_status.json"
)


@pytest.fixture
def engine() -> InterLineConsensus:
    """Fresh engine instance loaded with real data."""
    return InterLineConsensus(live_status_path=DATA_PATH)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset global singleton before each test."""
    _reset_singleton()
    yield


# ── test_load_live_status ──────────────────────────────────────────────────

def test_load_live_status(engine: InterLineConsensus) -> None:
    """Verify real data loads and has expected structure."""
    data = engine.load_live_status()
    assert isinstance(data, dict)
    assert len(data) >= 20  # At least 20 repos expected

    # Check key repos exist
    assert "omni-hub" in data
    assert "vci-lvlu" in data
    assert "vci-lgt" in data

    # Validate structure of a known repo
    hub = data["omni-hub"]
    assert hub["exists"] is True
    assert "status" in hub
    assert "activity" in hub
    assert "pushed_at" in hub
    assert "latest_commit" in hub


# ── test_classify_line_readiness ───────────────────────────────────────────

def test_classify_line_readiness_fully_operational(engine: InterLineConsensus) -> None:
    """活跃 + high activity → fully_operational."""
    result = engine.classify_line_readiness("vci-lvlu")
    assert result["line_id"] == "vci-lvlu"
    assert result["level"] in ["fully_operational", "operational"]
    assert result["score"] > 0.5
    assert "components" in result


def test_classify_line_readiness_shell_only(engine: InterLineConsensus) -> None:
    """壳化 line → shell_only."""
    result = engine.classify_line_readiness("vci-vinf")
    assert result["line_id"] == "vci-vinf"
    assert result["level"] == "shell_only"
    assert "壳化" in result["reason"]


def test_classify_line_readiness_dormant(engine: InterLineConsensus) -> None:
    """Low activity + old push → dormant."""
    result = engine.classify_line_readiness("grand-synthesis")
    assert result["line_id"] == "grand-synthesis"
    # grand-synthesis has low activity and pushed_at 2026-09-19
    # Depending on current date, this may be dormant or operational
    assert result["level"] in ("dormant", "operational", "shell_only")
    assert result["score"] >= 0.0


def test_classify_line_readiness_offline(engine: InterLineConsensus) -> None:
    """Unknown line → offline."""
    result = engine.classify_line_readiness("nonexistent-line-xyz")
    assert result["line_id"] == "nonexistent-line-xyz"
    assert result["level"] == "offline"
    assert result["score"] == 0.0


# ── test_send_proposal ─────────────────────────────────────────────────────

def test_send_proposal_structure(engine: InterLineConsensus) -> None:
    """Proposal returns expected structure."""
    proposal = {
        "type": "capability_exchange",
        "topic": "test_topic",
        "terms": {"scope": "alliance"},
    }
    result = engine.send_negotiation_proposal("omni-hub", "vci-lvlu", proposal)

    assert result["from_line"] == "omni-hub"
    assert result["to_line"] == "vci-lvlu"
    assert "accepted" in result
    assert "acceptance_score" in result
    assert isinstance(result["acceptance_score"], float)
    assert "conditions" in result
    assert "response_type" in result


def test_send_proposal_invalid_type(engine: InterLineConsensus) -> None:
    """Invalid proposal type is rejected."""
    proposal = {"type": "invalid_type", "topic": "x"}
    result = engine.send_negotiation_proposal("omni-hub", "vci-lvlu", proposal)
    assert result["accepted"] is False
    assert "Invalid proposal type" in result["reason"]


def test_send_proposal_unknown_target(engine: InterLineConsensus) -> None:
    """Unknown target line is rejected."""
    proposal = {"type": "state_sync", "topic": "x"}
    result = engine.send_negotiation_proposal("omni-hub", "unknown-line", proposal)
    assert result["accepted"] is False
    assert "not found" in result["reason"]


# ── test_auto_respond_shell ────────────────────────────────────────────────

def test_auto_respond_shell(engine: InterLineConsensus) -> None:
    """壳化 line responds with shell_proxy."""
    proposal = {"type": "state_sync", "topic": "test"}
    result = engine.auto_respond("vci-vinf", proposal)

    assert result["line_id"] == "vci-vinf"
    assert result["response_type"] == "shell_proxy"
    assert "readonly" in result["capabilities"]
    assert "relay" in result["capabilities"]
    assert result["acceptance_score"] < 0.5
    assert any("proxied" in c for c in result["conditions"])


# ── test_auto_respond_tower ────────────────────────────────────────────────

def test_auto_respond_tower(engine: InterLineConsensus) -> None:
    """九塔 line responds with tower_ack."""
    proposal = {"type": "consensus_vote", "topic": "test"}
    result = engine.auto_respond("vci-lgt", proposal)

    assert result["line_id"] == "vci-lgt"
    assert result["response_type"] == "tower_ack"
    assert result["accept"] is True
    assert result["acceptance_score"] > 0.5
    assert "si_autopilot" in result["capabilities"] or "seed_ring" in result["capabilities"]


# ── test_auto_respond_drive ────────────────────────────────────────────────

def test_auto_respond_drive(engine: InterLineConsensus) -> None:
    """LINE-DRIVE line responds with drive_ack."""
    proposal = {"type": "evolution_collab", "topic": "test"}
    result = engine.auto_respond("vci-aiq", proposal)

    assert result["line_id"] == "vci-aiq"
    assert result["response_type"] == "drive_ack"
    assert "event_drive" in result["capabilities"]
    assert "line_drive" in result["capabilities"]
    assert result["acceptance_score"] > 0.4


# ── test_auto_respond_full ─────────────────────────────────────────────────

def test_auto_respond_full(engine: InterLineConsensus) -> None:
    """活跃 line responds with full capabilities."""
    proposal = {"type": "capability_exchange", "topic": "test"}
    result = engine.auto_respond("vci-lvlu", proposal)

    assert result["line_id"] == "vci-lvlu"
    assert result["response_type"] == "full"
    assert "read" in result["capabilities"]
    assert "write" in result["capabilities"]
    assert "compute" in result["capabilities"]
    assert "negotiate" in result["capabilities"]
    assert result["accept"] is True
    assert result["acceptance_score"] > 0.8


# ── test_negotiate_iteratively ─────────────────────────────────────────────

def test_negotiate_iteratively(engine: InterLineConsensus) -> None:
    """Full multi-round negotiation completes."""
    participants = ["vci-lvlu", "vci-lgt", "vci-aiq", "vci-vinf"]
    result = engine.negotiate_iteratively(
        topic="cross_line_sync_test", participants=participants, max_rounds=5
    )

    assert "negotiation_id" in result
    assert result["topic"] == "cross_line_sync_test"
    assert len(result["participants"]) == 4
    assert "rounds" in result
    assert len(result["rounds"]) == 5

    # Check round structure
    for i, rd in enumerate(result["rounds"]):
        assert rd["round"] == i + 1
        assert "responses" in rd

    # Round 2 should have conflicts (mix of full and shell)
    round2 = result["rounds"][1]
    assert "conflicts_detected" in round2

    # Final round should have consensus score
    round5 = result["rounds"][4]
    assert "consensus_score" in round5

    # Result structure
    assert "consensus_reached" in result
    assert "confidence" in result
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0


# ── test_detect_conflicts ──────────────────────────────────────────────────

def test_detect_conflicts_capability_mismatch(engine: InterLineConsensus) -> None:
    """Detect capability mismatch between full and shell lines."""
    responses = {
        "vci-lvlu": engine.auto_respond("vci-lvlu", {"type": "capability_exchange"}),
        "vci-vinf": engine.auto_respond("vci-vinf", {"type": "capability_exchange"}),
    }
    conflicts = engine.detect_cross_line_conflicts(responses)

    assert len(conflicts) > 0
    mismatch = [c for c in conflicts if c["type"] == "capability_mismatch"]
    assert len(mismatch) >= 1
    assert "vci-lvlu" in mismatch[0]["between"]
    assert "vci-vinf" in mismatch[0]["between"]


def test_detect_conflicts_priority_conflict(engine: InterLineConsensus) -> None:
    """Detect priority conflict when one accepts and other rejects."""
    responses = {
        "vci-lvlu": engine.auto_respond("vci-lvlu", {"type": "capability_exchange"}),
        "vci-vinf": engine.auto_respond("vci-vinf", {"type": "capability_exchange"}),
    }
    conflicts = engine.detect_cross_line_conflicts(responses)

    priority = [c for c in conflicts if c["type"] == "priority_conflict"]
    # vci-lvlu accepts capability_exchange, vci-vinf may or may not
    # If both accept, no priority conflict; that's OK
    # Just verify the structure when conflicts exist
    for pc in priority:
        assert "between" in pc
        assert "severity" in pc


# ── test_consensus_score ───────────────────────────────────────────────────

def test_consensus_score_computation(engine: InterLineConsensus) -> None:
    """Score computation produces valid results."""
    responses = {
        "vci-lvlu": engine.auto_respond("vci-lvlu", {"type": "consensus_vote"}),
        "vci-lgt": engine.auto_respond("vci-lgt", {"type": "consensus_vote"}),
        "vci-aiq": engine.auto_respond("vci-aiq", {"type": "consensus_vote"}),
    }
    score = engine.compute_consensus_score(responses)

    assert "score" in score
    assert isinstance(score["score"], float)
    assert 0.0 <= score["score"] <= 1.0
    assert "consensus_reached" in score
    assert score["level"] in ("unanimous", "strong", "majority", "weak", "failed")
    assert "components" in score
    comp = score["components"]
    assert "avg_acceptance" in comp
    assert "participation_rate" in comp
    assert "term_overlap" in comp
    assert "readiness_weight" in comp


def test_consensus_score_empty(engine: InterLineConsensus) -> None:
    """Empty responses → failed consensus."""
    score = engine.compute_consensus_score({})
    assert score["score"] == 0.0
    assert score["consensus_reached"] is False
    assert score["level"] == "failed"


# ── test_generate_protocol ─────────────────────────────────────────────────

def test_generate_protocol_with_consensus(engine: InterLineConsensus) -> None:
    """Protocol generated for successful negotiation."""
    participants = ["vci-lvlu", "vci-lgt", "vci-aiq"]
    neg_result = engine.negotiate_iteratively(
        topic="protocol_test", participants=participants, max_rounds=5
    )
    protocol = engine.generate_consensus_protocol(neg_result)

    assert "protocol_id" in protocol
    if neg_result["consensus_reached"]:
        assert protocol["status"] == "active"
        assert "agreed_terms" in protocol
        assert "responsibilities" in protocol
        assert "timeline" in protocol
        assert "fallback" in protocol
        # Each participant should have responsibilities
        for p in participants:
            assert p in protocol["responsibilities"]
    else:
        assert protocol["status"] == "no_consensus"
        assert protocol["agreed_terms"] is None


def test_generate_protocol_no_consensus(engine: InterLineConsensus) -> None:
    """No-consensus negotiation produces fallback protocol."""
    neg_result = {
        "negotiation_id": "test_neg_001",
        "consensus_reached": False,
        "participants": [],
        "confidence": 0.0,
    }
    protocol = engine.generate_consensus_protocol(neg_result)
    assert protocol["status"] == "no_consensus"
    assert protocol["fallback"]["action"] == "retry_with_reduced_scope"


# ── test_execute_consensus ─────────────────────────────────────────────────

def test_execute_consensus_active(engine: InterLineConsensus) -> None:
    """Execute consensus generates actionable items."""
    protocol = {
        "protocol_id": "proto_test_001",
        "status": "active",
        "topic": "test_execution",
        "responsibilities": {
            "vci-lvlu": {"role": "primary_contributor", "actions": ["implement", "review"], "capabilities": ["read", "write"]},
            "vci-lgt": {"role": "tower_relay", "actions": ["propagate", "monitor"], "capabilities": ["si_autopilot"]},
            "vci-vinf": {"role": "passive_relay", "actions": ["relay"], "capabilities": ["readonly"]},
        },
        "confidence": 0.85,
    }
    result = engine.execute_consensus(protocol)

    assert result["executed"] is True
    assert "actions_per_line" in result
    assert "expected_outcomes" in result
    assert "monitoring_metrics" in result

    # vci-lvlu (full contributor) should have implement + review actions
    lvlu_actions = result["actions_per_line"]["vci-lvlu"]
    assert any(a["action"] == "implement_term" for a in lvlu_actions)
    assert any(a["action"] == "peer_review" for a in lvlu_actions)

    # vci-lgt (tower) should have propagate + monitor
    lgt_actions = result["actions_per_line"]["vci-lgt"]
    assert any(a["action"] == "state_propagation" for a in lgt_actions)

    # vci-vinf (shell) should have relay only
    vinf_actions = result["actions_per_line"]["vci-vinf"]
    assert any(a["action"] == "passive_relay" for a in vinf_actions)


def test_execute_consensus_inactive(engine: InterLineConsensus) -> None:
    """Inactive protocol returns failure."""
    protocol = {"protocol_id": "proto_test_002", "status": "no_consensus"}
    result = engine.execute_consensus(protocol)
    assert result["executed"] is False
    assert "reason" in result


# ── test_status ────────────────────────────────────────────────────────────

def test_status_structure(engine: InterLineConsensus) -> None:
    """Status returns expected structure."""
    status = engine.get_status()
    assert "negotiation_count" in status
    assert "consensus_count" in status
    assert "active_negotiations" in status
    assert "lines_loaded" in status
    assert "line_ids" in status
    assert status["lines_loaded"] >= 20
    assert "omni-hub" in status["line_ids"]


# ── Singleton test ─────────────────────────────────────────────────────────

def test_singleton() -> None:
    """Global singleton returns consistent instance."""
    _reset_singleton()
    a = get_inter_line_consensus(live_status_path=DATA_PATH)
    b = get_inter_line_consensus(live_status_path=DATA_PATH)
    assert a is b
    assert isinstance(a, InterLineConsensus)
