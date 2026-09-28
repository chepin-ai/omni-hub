"""
Tests for OMNI-HUB Module v158: Cross-Repo Knowledge Transfer
"""

from __future__ import annotations

import pytest
from core.cross_repo_knowledge_transfer import (
    KNOWLEDGE_TYPES,
    CrossRepoKnowledgeTransfer,
    get_cross_repo_knowledge_transfer,
)


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset the global singleton before each test."""
    import core.cross_repo_knowledge_transfer as _mod

    _mod._MODULE = None
    yield
    _mod._MODULE = None


@pytest.fixture
def crt() -> CrossRepoKnowledgeTransfer:
    return CrossRepoKnowledgeTransfer()


# ---------------------------------------------------------------------------
# identify_transfer_opportunities
# ---------------------------------------------------------------------------
class TestIdentifyTransferOpportunities:
    def test_returns_list(self, crt: CrossRepoKnowledgeTransfer) -> None:
        ops = crt.identify_transfer_opportunities()
        assert isinstance(ops, list)

    def test_opportunity_structure(self, crt: CrossRepoKnowledgeTransfer) -> None:
        ops = crt.identify_transfer_opportunities()
        assert len(ops) > 0
        op = ops[0]
        assert set(op.keys()) == {
            "source",
            "target",
            "resonance",
            "capability_gap",
            "source_capability",
            "target_capability",
        }
        assert op["source"] != op["target"]
        assert op["resonance"] >= 0.3
        assert op["capability_gap"] >= 0.05
        assert op["source_capability"] >= op["target_capability"]

    def test_sorted_by_resonance_desc(self, crt: CrossRepoKnowledgeTransfer) -> None:
        ops = crt.identify_transfer_opportunities()
        if len(ops) > 1:
            for i in range(len(ops) - 1):
                assert ops[i]["resonance"] >= ops[i + 1]["resonance"]

    def test_direction_high_to_low(self, crt: CrossRepoKnowledgeTransfer) -> None:
        ops = crt.identify_transfer_opportunities()
        for op in ops:
            assert op["source_capability"] >= op["target_capability"]


# ---------------------------------------------------------------------------
# extract_knowledge
# ---------------------------------------------------------------------------
class TestExtractKnowledge:
    def test_extract_valid_repo_and_type(self, crt: CrossRepoKnowledgeTransfer) -> None:
        result = crt.extract_knowledge("omni-hub", "architecture_pattern")
        assert "error" not in result
        assert result["repo"] == "omni-hub"
        assert result["knowledge_type"] == "architecture_pattern"
        assert "data" in result
        assert "capability" in result
        assert "extracted_at" in result

    def test_extract_all_types(self, crt: CrossRepoKnowledgeTransfer) -> None:
        for kt in KNOWLEDGE_TYPES:
            result = crt.extract_knowledge("vci-ucif2", kt)
            assert "error" not in result, f"Failed for {kt}"
            assert result["data"]

    def test_extract_unknown_repo(self, crt: CrossRepoKnowledgeTransfer) -> None:
        result = crt.extract_knowledge("nonexistent-repo", "code_style")
        assert "error" in result

    def test_extract_unknown_type(self, crt: CrossRepoKnowledgeTransfer) -> None:
        result = crt.extract_knowledge("omni-hub", "unknown_type_xyz")
        assert "error" in result
        assert "supported_types" in result


# ---------------------------------------------------------------------------
# transfer_knowledge
# ---------------------------------------------------------------------------
class TestTransferKnowledge:
    def test_transfer_success_structure(self, crt: CrossRepoKnowledgeTransfer) -> None:
        knowledge = crt.extract_knowledge("omni-hub", "testing_strategy")
        result = crt.transfer_knowledge("omni-hub", "vci-playground", knowledge)
        assert "error" not in result
        assert "transfer_id" in result
        assert result["from_repo"] == "omni-hub"
        assert result["to_repo"] == "vci-playground"
        assert 0.0 <= result["resonance"] <= 1.0
        assert result["success_probability"] in (0.3, 0.6, 0.9)
        assert result["status"] == "pending"

    def test_transfer_unknown_source(self, crt: CrossRepoKnowledgeTransfer) -> None:
        result = crt.transfer_knowledge(
            "unknown-src", "omni-hub", {"knowledge_type": "code_style"}
        )
        assert "error" in result

    def test_transfer_unknown_target(self, crt: CrossRepoKnowledgeTransfer) -> None:
        result = crt.transfer_knowledge(
            "omni-hub", "unknown-tgt", {"knowledge_type": "code_style"}
        )
        assert "error" in result

    def test_high_resonance_high_probability(
        self, crt: CrossRepoKnowledgeTransfer
    ) -> None:
        # Two Python repos in alliance_core should have high resonance
        knowledge = crt.extract_knowledge("omni-hub", "architecture_pattern")
        result = crt.transfer_knowledge("omni-hub", "vci-ucif2", knowledge)
        if result["resonance"] > 0.7:
            assert result["success_probability"] == 0.9
        elif result["resonance"] >= 0.5:
            assert result["success_probability"] == 0.6
        else:
            assert result["success_probability"] == 0.3

    def test_transfer_records_history(self, crt: CrossRepoKnowledgeTransfer) -> None:
        before = len(crt.transfer_history)
        knowledge = crt.extract_knowledge("omni-hub", "documentation_practice")
        crt.transfer_knowledge("omni-hub", "vci-inbox", knowledge)
        assert len(crt.transfer_history) == before + 1


# ---------------------------------------------------------------------------
# verify_transfer
# ---------------------------------------------------------------------------
class TestVerifyTransfer:
    def test_verify_pending_transfer(self, crt: CrossRepoKnowledgeTransfer) -> None:
        knowledge = crt.extract_knowledge("omni-hub", "ci_cd_setup")
        tx = crt.transfer_knowledge("omni-hub", "vci-playground", knowledge)
        tid = tx["transfer_id"]
        result = crt.verify_transfer(tid)
        assert "error" not in result
        assert result["transfer_id"] == tid
        assert result["status"] == "verified"
        assert isinstance(result["adopted"], bool)
        assert "verified_at" in result

    def test_verify_idempotent(self, crt: CrossRepoKnowledgeTransfer) -> None:
        knowledge = crt.extract_knowledge("omni-hub", "code_style")
        tx = crt.transfer_knowledge("omni-hub", "vci-playground", knowledge)
        tid = tx["transfer_id"]
        r1 = crt.verify_transfer(tid)
        r2 = crt.verify_transfer(tid)
        assert r1["adopted"] == r2["adopted"]
        assert r1["verified_at"] == r2["verified_at"]

    def test_verify_unknown_transfer(self, crt: CrossRepoKnowledgeTransfer) -> None:
        result = crt.verify_transfer("does-not-exist")
        assert "error" in result

    def test_success_rate_ranges(self, crt: CrossRepoKnowledgeTransfer) -> None:
        # Create a few transfers and verify them
        for src, tgt in [("omni-hub", "vci-playground"), ("vci-ucif2", "omni-hub")]:
            knowledge = crt.extract_knowledge(src, "architecture_pattern")
            tx = crt.transfer_knowledge(src, tgt, knowledge)
            crt.verify_transfer(tx["transfer_id"])
        metrics = crt.get_transfer_metrics()
        assert 0.0 <= metrics["success_rate"] <= 1.0


# ---------------------------------------------------------------------------
# get_transfer_metrics
# ---------------------------------------------------------------------------
class TestGetTransferMetrics:
    def test_metrics_structure(self, crt: CrossRepoKnowledgeTransfer) -> None:
        metrics = crt.get_transfer_metrics()
        assert set(metrics.keys()) == {
            "total_transfers",
            "verified_transfers",
            "successful_adoptions",
            "success_rate",
            "knowledge_flow_graph",
            "pending_transfers",
        }
        assert isinstance(metrics["total_transfers"], int)
        assert isinstance(metrics["success_rate"], float)

    def test_metrics_consistency(self, crt: CrossRepoKnowledgeTransfer) -> None:
        # Seed a transfer
        knowledge = crt.extract_knowledge("omni-hub", "testing_strategy")
        crt.transfer_knowledge("omni-hub", "vci-playground", knowledge)
        metrics = crt.get_transfer_metrics()
        assert metrics["pending_transfers"] + metrics["verified_transfers"] == metrics["total_transfers"]
        assert metrics["successful_adoptions"] <= metrics["verified_transfers"]
        assert 0.0 <= metrics["success_rate"] <= 1.0

    def test_flow_graph(self, crt: CrossRepoKnowledgeTransfer) -> None:
        knowledge = crt.extract_knowledge("omni-hub", "code_style")
        crt.transfer_knowledge("omni-hub", "vci-playground", knowledge)
        metrics = crt.get_transfer_metrics()
        graph = metrics["knowledge_flow_graph"]
        assert "omni-hub" in graph
        assert graph["omni-hub"]["total_transfers"] >= 1
        assert any(o["target"] == "vci-playground" for o in graph["omni-hub"]["outgoing"])


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------
class TestGetStatus:
    def test_status_keys(self, crt: CrossRepoKnowledgeTransfer) -> None:
        status = crt.get_status()
        assert set(status.keys()) == {
            "opportunity_count",
            "transfer_count",
            "success_rate",
            "pending_transfers",
            "verified_transfers",
            "repo_count",
        }

    def test_status_values(self, crt: CrossRepoKnowledgeTransfer) -> None:
        status = crt.get_status()
        assert status["repo_count"] == 33
        assert status["opportunity_count"] > 0
        assert status["transfer_count"] >= 0
        assert 0.0 <= status["success_rate"] <= 1.0
        assert status["pending_transfers"] >= 0
        assert status["verified_transfers"] >= 0

    def test_status_after_transfer(self, crt: CrossRepoKnowledgeTransfer) -> None:
        before = crt.get_status()
        knowledge = crt.extract_knowledge("omni-hub", "documentation_practice")
        crt.transfer_knowledge("omni-hub", "vci-playground", knowledge)
        after = crt.get_status()
        assert after["transfer_count"] == before["transfer_count"] + 1


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_singleton_returns_same_instance(self) -> None:
        a = get_cross_repo_knowledge_transfer()
        b = get_cross_repo_knowledge_transfer()
        assert a is b

    def test_singleton_is_populated(self) -> None:
        inst = get_cross_repo_knowledge_transfer()
        assert len(inst._repos) == 33
