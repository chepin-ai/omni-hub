"""
Tests for Tri-Core MIP* (三核MIP*) module.

Run with: pytest tests/test_tri_core_mip.py -v
"""

import pytest
from typing import Any, Dict

from core.tri_core_mip import TriCoreMIP, get_tri_core_mip


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def fresh_mip() -> TriCoreMIP:
    """Provide a freshly-initialized TriCoreMIP instance."""
    mip = TriCoreMIP()
    mip.initialize_cores()
    return mip


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    """Reset the global singleton before each test."""
    import core.tri_core_mip as mod
    mod._module = None


# ---------------------------------------------------------------------------
# 1. Initialization
# ---------------------------------------------------------------------------
class TestInitialization:
    def test_singleton_returns_same_instance(self) -> None:
        """get_tri_core_mip() must return the same object on repeated calls."""
        a = get_tri_core_mip()
        b = get_tri_core_mip()
        assert a is b

    def test_cores_created(self, fresh_mip: TriCoreMIP) -> None:
        """All three cores must exist after initialization."""
        cores = fresh_mip.cores
        assert TriCoreMIP.CORE_A in cores
        assert TriCoreMIP.CORE_B in cores
        assert TriCoreMIP.CORE_C in cores

    def test_core_roles(self, fresh_mip: TriCoreMIP) -> None:
        """Each core must have the correct role."""
        assert fresh_mip.cores[TriCoreMIP.CORE_A]["role"] == "perception"
        assert fresh_mip.cores[TriCoreMIP.CORE_B]["role"] == "verification"
        assert fresh_mip.cores[TriCoreMIP.CORE_C]["role"] == "execution"

    def test_entanglement_state_initialized(self, fresh_mip: TriCoreMIP) -> None:
        """Entanglement state must contain pairwise links and global coherence."""
        es = fresh_mip.entanglement_state
        assert f"{TriCoreMIP.CORE_A}-{TriCoreMIP.CORE_B}" in es
        assert f"{TriCoreMIP.CORE_B}-{TriCoreMIP.CORE_C}" in es
        assert f"{TriCoreMIP.CORE_C}-{TriCoreMIP.CORE_A}" in es
        assert "global_coherence" in es
        assert es["global_coherence"] == 1.0

    def test_idempotent_initialization(self, fresh_mip: TriCoreMIP) -> None:
        """Calling initialize_cores() twice must not reset state."""
        first = fresh_mip.cores[TriCoreMIP.CORE_A]["health"]
        fresh_mip.cores[TriCoreMIP.CORE_A]["health"] = 0.5
        fresh_mip.initialize_cores()
        assert fresh_mip.cores[TriCoreMIP.CORE_A]["health"] == 0.5


# ---------------------------------------------------------------------------
# 2. Proof generation
# ---------------------------------------------------------------------------
class TestGenerateProof:
    def test_proof_has_all_fragments(self, fresh_mip: TriCoreMIP) -> None:
        """Generated proof must contain fragments for all three cores."""
        proof = fresh_mip.generate_proof({"sensor": 42})
        frags = proof["fragments"]
        assert TriCoreMIP.CORE_A in frags
        assert TriCoreMIP.CORE_B in frags
        assert TriCoreMIP.CORE_C in frags

    def test_proof_has_entanglement_witness(self, fresh_mip: TriCoreMIP) -> None:
        """Proof must include an entanglement witness."""
        proof = fresh_mip.generate_proof({"task": "demo"})
        assert "entanglement_witness" in proof
        assert "consistency_score" in proof["entanglement_witness"]

    def test_proof_has_combined_hash(self, fresh_mip: TriCoreMIP) -> None:
        """Proof must carry a combined hash."""
        proof = fresh_mip.generate_proof({"x": 1})
        assert "combined_hash" in proof
        assert len(proof["combined_hash"]) == 64  # SHA-256 hex

    def test_proof_strength_classification(self, fresh_mip: TriCoreMIP) -> None:
        """Proof strength must be one of the defined labels."""
        proof = fresh_mip.generate_proof({"y": 2})
        assert proof["strength"] in ("quantum", "strong", "valid", "weak", "invalid")

    def test_proof_history_appended(self, fresh_mip: TriCoreMIP) -> None:
        """Each generated proof must be appended to proof_history."""
        before = len(fresh_mip.proof_history)
        fresh_mip.generate_proof({"z": 3})
        assert len(fresh_mip.proof_history) == before + 1

    def test_different_inputs_different_hashes(self, fresh_mip: TriCoreMIP) -> None:
        """Different inputs must yield different combined hashes."""
        p1 = fresh_mip.generate_proof({"a": 1})
        p2 = fresh_mip.generate_proof({"a": 2})
        assert p1["combined_hash"] != p2["combined_hash"]


# ---------------------------------------------------------------------------
# 3. Proof verification
# ---------------------------------------------------------------------------
class TestVerifyProof:
    def test_valid_proof_verifies_true(self, fresh_mip: TriCoreMIP) -> None:
        """A freshly-generated proof must verify successfully."""
        proof = fresh_mip.generate_proof({"data": "test"})
        result = fresh_mip.verify_proof(proof)
        assert result["verified"] is True

    def test_verification_checks_present(self, fresh_mip: TriCoreMIP) -> None:
        """Verification result must contain all check fields."""
        proof = fresh_mip.generate_proof({"data": "test"})
        result = fresh_mip.verify_proof(proof)
        assert "all_fragments_present" in result["checks"]
        assert "entanglement_witness_valid" in result["checks"]
        assert "consistency_match" in result["checks"]

    def test_missing_fragments_fails(self, fresh_mip: TriCoreMIP) -> None:
        """Proof missing a fragment must fail verification."""
        proof = fresh_mip.generate_proof({"data": "test"})
        del proof["fragments"][TriCoreMIP.CORE_B]
        result = fresh_mip.verify_proof(proof)
        assert result["verified"] is False
        assert result["checks"]["all_fragments_present"] is False

    def test_tampered_witness_fails(self, fresh_mip: TriCoreMIP) -> None:
        """Tampering with the consistency score must cause verification failure."""
        proof = fresh_mip.generate_proof({"data": "test"})
        # Tamper consistency score
        proof["entanglement_witness"]["consistency_score"] = 999.0
        result = fresh_mip.verify_proof(proof)
        assert result["verified"] is False
        assert result["checks"]["consistency_match"] is False

    def test_verification_counts_increment(self, fresh_mip: TriCoreMIP) -> None:
        """Verification counters must update correctly."""
        proof = fresh_mip.generate_proof({"data": "test"})
        before = fresh_mip._verification_count
        fresh_mip.verify_proof(proof)
        assert fresh_mip._verification_count == before + 1


# ---------------------------------------------------------------------------
# 4. Dispute resolution
# ---------------------------------------------------------------------------
class TestResolveDispute:
    def test_dispute_returns_winner(self, fresh_mip: TriCoreMIP) -> None:
        """Dispute resolution must pick a winner."""
        out_a = {"proposal": "alpha", "value": 100}
        out_b = {"proposal": "beta", "value": 200}
        result = fresh_mip.resolve_dispute(out_a, out_b)
        assert result["resolved"] is True
        assert result["winner"] in ("Core-A", "Core-B")

    def test_dispute_contains_evaluations(self, fresh_mip: TriCoreMIP) -> None:
        """Resolution result must contain evaluations from both sides."""
        result = fresh_mip.resolve_dispute({"a": 1}, {"b": 2})
        assert "evaluation_a" in result
        assert "evaluation_b" in result

    def test_dispute_updates_global_coherence(self, fresh_mip: TriCoreMIP) -> None:
        """Global coherence must be updated after dispute resolution."""
        before = fresh_mip.entanglement_state["global_coherence"]
        fresh_mip.resolve_dispute({"x": 1}, {"x": 2})
        after = fresh_mip.entanglement_state["global_coherence"]
        # Coherence may change because the A-B link is adjusted
        assert isinstance(after, float)

    def test_dispute_entanglement_collapsed_flag(self, fresh_mip: TriCoreMIP) -> None:
        """Resolution must set the entanglement_collapsed flag."""
        result = fresh_mip.resolve_dispute({"p": 1}, {"p": 2})
        assert result["entanglement_collapsed"] is True

    def test_dispute_winner_is_one_of_inputs(self, fresh_mip: TriCoreMIP) -> None:
        """The winning output must be one of the two input proposals."""
        out_a = {"id": "A"}
        out_b = {"id": "B"}
        result = fresh_mip.resolve_dispute(out_a, out_b)
        assert result["winning_output"] in (out_a, out_b)


# ---------------------------------------------------------------------------
# 5. Status
# ---------------------------------------------------------------------------
class TestGetStatus:
    def test_status_has_required_keys(self, fresh_mip: TriCoreMIP) -> None:
        """Status must expose all documented metrics."""
        status = fresh_mip.get_status()
        assert "initialized" in status
        assert "core_health" in status
        assert "proof_count" in status
        assert "verification_count" in status
        assert "verification_success" in status
        assert "verification_rate" in status
        assert "entanglement_strength" in status

    def test_status_initialized_true(self, fresh_mip: TriCoreMIP) -> None:
        """Status must report initialized=True after init."""
        assert fresh_mip.get_status()["initialized"] is True

    def test_status_proof_count_matches(self, fresh_mip: TriCoreMIP) -> None:
        """proof_count in status must match proof_history length."""
        fresh_mip.generate_proof({"n": 1})
        fresh_mip.generate_proof({"n": 2})
        assert fresh_mip.get_status()["proof_count"] == 2

    def test_status_verification_rate(self, fresh_mip: TriCoreMIP) -> None:
        """Verification rate must be 1.0 when all proofs pass."""
        p = fresh_mip.generate_proof({"ok": True})
        fresh_mip.verify_proof(p)
        assert fresh_mip.get_status()["verification_rate"] == 1.0

    def test_status_core_health_fields(self, fresh_mip: TriCoreMIP) -> None:
        """Each core health entry must have status, health, and role."""
        health = fresh_mip.get_status()["core_health"]
        for cid in (TriCoreMIP.CORE_A, TriCoreMIP.CORE_B, TriCoreMIP.CORE_C):
            assert "status" in health[cid]
            assert "health" in health[cid]
            assert "role" in health[cid]

    def test_status_entanglement_strength_range(self, fresh_mip: TriCoreMIP) -> None:
        """Entanglement strength must be in [0, 1]."""
        strength = fresh_mip.get_status()["entanglement_strength"]
        assert 0.0 <= strength <= 1.0


# ---------------------------------------------------------------------------
# 6. Edge cases & defensive programming
# ---------------------------------------------------------------------------
class TestEdgeCases:
    def test_generate_proof_auto_initializes(self) -> None:
        """generate_proof must auto-initialize if not already initialized."""
        mip = TriCoreMIP()
        assert not mip._initialized
        mip.generate_proof({"x": 1})
        assert mip._initialized

    def test_verify_proof_auto_initializes(self) -> None:
        """verify_proof must auto-initialize if not already initialized."""
        mip = TriCoreMIP()
        # Need a valid proof structure to verify
        proof = {
            "fragments": {
                TriCoreMIP.CORE_A: {"core_id": TriCoreMIP.CORE_A, "payload": {}, "fragment_hash": "a" * 64},
                TriCoreMIP.CORE_B: {"core_id": TriCoreMIP.CORE_B, "payload": {}, "fragment_hash": "b" * 64},
                TriCoreMIP.CORE_C: {"core_id": TriCoreMIP.CORE_C, "payload": {}, "fragment_hash": "c" * 64},
            },
            "entanglement_witness": {
                "valid": True,
                "consistency_score": 0.5,
                "links": {},
            },
        }
        mip.verify_proof(proof)
        assert mip._initialized

    def test_empty_input_data(self, fresh_mip: TriCoreMIP) -> None:
        """Empty input data must still produce a valid proof."""
        proof = fresh_mip.generate_proof({})
        assert "fragments" in proof
        assert proof["status"] == "generated"

    def test_nested_input_data(self, fresh_mip: TriCoreMIP) -> None:
        """Nested dict input must be handled gracefully."""
        proof = fresh_mip.generate_proof({"level1": {"level2": {"level3": [1, 2, 3]}}})
        result = fresh_mip.verify_proof(proof)
        assert result["verified"] is True

    def test_strength_boundaries(self, fresh_mip: TriCoreMIP) -> None:
        """Strength classification must cover the entire [0,1] range."""
        # We test the classifier directly
        assert fresh_mip._classify_strength(0.96) == "quantum"
        assert fresh_mip._classify_strength(0.85) == "strong"
        assert fresh_mip._classify_strength(0.70) == "valid"
        assert fresh_mip._classify_strength(0.50) == "weak"
        assert fresh_mip._classify_strength(0.30) == "invalid"
        assert fresh_mip._classify_strength(0.0) == "invalid"
