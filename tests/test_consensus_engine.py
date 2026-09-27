"""
Tests for OMNI-HUB v132: Consensus Engine
"""

import pytest
from core.consensus_engine import ConsensusEngine, get_consensus_engine, _reset_singleton


class TestConsensusEngine:
    """Comprehensive tests for the ConsensusEngine."""

    def test_propose_returns_valid_hash(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic_a", "value_1")
        assert isinstance(pid, str)
        assert len(pid) == 64  # SHA-256 hex

    def test_propose_increases_proposal_count(self):
        ce = ConsensusEngine()
        ce.propose("t1", "v1")
        ce.propose("t2", "v2")
        status = ce.get_status()
        assert status["proposal_count"] == 2

    def test_vote_updates_tally(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        tally = ce.vote(pid, "node_1", True)
        assert tally["total_votes"] == 1
        assert tally["approvals"] == 1
        assert tally["rejections"] == 0
        assert tally["approval_ratio"] == 1.0

    def test_multiple_votes_tally(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        ce.vote(pid, "node_a", True)
        ce.vote(pid, "node_b", True)
        ce.vote(pid, "node_c", False)
        tally = ce.vote(pid, "node_d", True)
        assert tally["total_votes"] == 4
        assert tally["approvals"] == 3
        assert tally["rejections"] == 1
        assert tally["approval_ratio"] == 0.75

    def test_vote_on_nonexistent_proposal_raises(self):
        ce = ConsensusEngine()
        with pytest.raises(KeyError):
            ce.vote("deadbeef" * 4, "node_1", True)

    def test_vote_on_resolved_proposal_raises(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        ce.vote(pid, "n1", True)
        ce.vote(pid, "n2", True)
        ce.vote(pid, "n3", True)
        ce.resolve(pid)
        with pytest.raises(RuntimeError):
            ce.vote(pid, "n4", True)

    def test_consensus_reached_above_two_thirds(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        ce.vote(pid, "n1", True)
        ce.vote(pid, "n2", True)
        ce.vote(pid, "n3", True)
        result = ce.resolve(pid)
        assert result["consensus_reached"] is True
        assert result["result"] == "approved"

    def test_consensus_not_reached_at_exactly_two_thirds(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        ce.vote(pid, "n1", True)
        ce.vote(pid, "n2", True)
        ce.vote(pid, "n3", False)
        result = ce.resolve(pid)
        # 2/3 is not strictly > 2/3
        assert result["consensus_reached"] is False
        assert result["result"] == "rejected"

    def test_consensus_not_reached_below_two_thirds(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        ce.vote(pid, "n1", True)
        ce.vote(pid, "n2", False)
        ce.vote(pid, "n3", False)
        result = ce.resolve(pid)
        assert result["consensus_reached"] is False
        assert result["result"] == "rejected"

    def test_resolve_no_votes_pending(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        result = ce.resolve(pid)
        assert result["consensus_reached"] is False
        assert result["result"] == "pending"

    def test_resolve_already_resolved_returns_cached(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        ce.vote(pid, "n1", True)
        ce.vote(pid, "n2", True)
        ce.vote(pid, "n3", True)
        r1 = ce.resolve(pid)
        r2 = ce.resolve(pid)
        assert r1 == r2

    def test_resolve_nonexistent_proposal_raises(self):
        ce = ConsensusEngine()
        with pytest.raises(KeyError):
            ce.resolve("deadbeef" * 4)

    def test_get_status_counts(self):
        ce = ConsensusEngine()
        pid1 = ce.propose("t1", "v1")
        pid2 = ce.propose("t2", "v2")
        ce.vote(pid1, "n1", True)
        ce.vote(pid1, "n2", True)
        ce.vote(pid1, "n3", True)
        ce.resolve(pid1)
        status = ce.get_status()
        assert status["proposal_count"] == 2
        assert status["resolved_count"] == 1
        assert status["pending_count"] == 1
        assert pid1 in status["resolved_ids"]
        assert pid2 in status["proposal_ids"]

    def test_get_proposal(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic_x", "val_y")
        prop = ce.get_proposal(pid)
        assert prop is not None
        assert prop["topic"] == "topic_x"
        assert prop["value"] == "val_y"
        assert prop["status"] == "pending"

    def test_get_votes(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        ce.vote(pid, "n1", True)
        ce.vote(pid, "n2", False)
        votes = ce.get_votes(pid)
        assert votes == {"n1": True, "n2": False}

    def test_list_proposals(self):
        ce = ConsensusEngine()
        pid = ce.propose("t", "v")
        assert ce.list_proposals() == [pid]

    def test_different_proposals_different_hashes(self):
        ce = ConsensusEngine()
        pid1 = ce.propose("topic", "value")
        pid2 = ce.propose("topic", "value")
        assert pid1 != pid2

    def test_tally_rounding(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        ce.vote(pid, "n1", True)
        ce.vote(pid, "n2", False)
        tally = ce.vote(pid, "n3", False)
        # 1/3 ≈ 0.3333
        assert tally["approval_ratio"] == 0.3333

    def test_7_nodes_consensus(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        # 5/7 ≈ 71.4% > 66.7%
        for i in range(5):
            ce.vote(pid, f"n{i}", True)
        for i in range(5, 7):
            ce.vote(pid, f"n{i}", False)
        result = ce.resolve(pid)
        assert result["consensus_reached"] is True
        assert result["result"] == "approved"

    def test_7_nodes_no_consensus(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        # 4/7 ≈ 57.1% < 66.7%
        for i in range(4):
            ce.vote(pid, f"n{i}", True)
        for i in range(4, 7):
            ce.vote(pid, f"n{i}", False)
        result = ce.resolve(pid)
        assert result["consensus_reached"] is False
        assert result["result"] == "rejected"

    def test_node_can_change_vote(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        ce.vote(pid, "n1", False)
        ce.vote(pid, "n1", True)
        votes = ce.get_votes(pid)
        assert votes["n1"] is True


class TestSingleton:
    """Tests for the global singleton."""

    def setup_method(self):
        _reset_singleton()

    def teardown_method(self):
        _reset_singleton()

    def test_singleton_returns_same_instance(self):
        ce1 = get_consensus_engine()
        ce2 = get_consensus_engine()
        assert ce1 is ce2

    def test_singleton_state_persists(self):
        ce = get_consensus_engine()
        pid = ce.propose("singleton_topic", "singleton_value")
        ce2 = get_consensus_engine()
        assert ce2.get_proposal(pid) is not None


class TestEdgeCases:
    """Edge case and defensive programming tests."""

    def test_propose_empty_topic(self):
        ce = ConsensusEngine()
        pid = ce.propose("", "value")
        assert isinstance(pid, str)
        assert len(pid) == 64

    def test_propose_none_value(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", None)
        prop = ce.get_proposal(pid)
        assert prop["value"] is None

    def test_propose_dict_value(self):
        ce = ConsensusEngine()
        pid = ce.propose("config", {"key": "val"})
        prop = ce.get_proposal(pid)
        assert prop["value"] == {"key": "val"}

    def test_100_nodes_consensus(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        # 67/100 = 67% > 66.7%
        for i in range(67):
            ce.vote(pid, f"n{i}", True)
        for i in range(67, 100):
            ce.vote(pid, f"n{i}", False)
        result = ce.resolve(pid)
        assert result["consensus_reached"] is True
        assert result["result"] == "approved"

    def test_100_nodes_no_consensus(self):
        ce = ConsensusEngine()
        pid = ce.propose("topic", 42)
        # 66/100 = 66% not > 66.7%
        for i in range(66):
            ce.vote(pid, f"n{i}", True)
        for i in range(66, 100):
            ce.vote(pid, f"n{i}", False)
        result = ce.resolve(pid)
        assert result["consensus_reached"] is False
        assert result["result"] == "rejected"
