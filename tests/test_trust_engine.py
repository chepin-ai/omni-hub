"""
OMNI-HUB Trust Engine Tests v80
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.trust_engine import (
    TrustRecord, TrustEngine, get_trust_engine,
)


class TestTrustEngine:
    def test_initialization(self):
        te = TrustEngine()
        assert te.global_trust == 0.5

    def test_register_entity(self):
        te = TrustEngine()
        te.register_entity("test_entity", 0.6)
        assert "test_entity" in te.records
        assert te.records["test_entity"].score == 0.6

    def test_record_positive_interaction(self):
        te = TrustEngine()
        te.register_entity("e1")
        te.record_interaction("e1", positive=True, cycle=10)
        assert te.records["e1"].score > 0.5
        assert te.records["e1"].positive == 1

    def test_record_negative_interaction(self):
        te = TrustEngine()
        te.register_entity("e1")
        te.record_interaction("e1", positive=False, cycle=10)
        assert te.records["e1"].score < 0.5
        assert te.records["e1"].negative == 1

    def test_betrayal_detection(self):
        te = TrustEngine()
        te.register_entity("e1", 0.5)
        for _ in range(5):
            te.record_interaction("e1", positive=False, cycle=10)
        assert len(te.betrayals) > 0
        assert te.betrayals[0]["entity"] == "e1"

    def test_evaluate_system_trust(self):
        te = TrustEngine()
        state = {"capability_assessment": {"scores": {"learning": 0.8, "ethics": 0.2}}}
        te.evaluate_system_trust(state, cycle=10)
        assert len(te.records) > 0
        assert te.global_trust > 0

    def test_get_trusted_entities(self):
        te = TrustEngine()
        te.register_entity("trusted", 0.9)
        te.register_entity("untrusted", 0.1)
        trusted = te.get_trusted_entities(threshold=0.7)
        assert "trusted" in trusted
        assert "untrusted" not in trusted

    def test_get_status(self):
        te = TrustEngine()
        te.register_entity("e1", 0.8)
        status = te.get_status()
        assert status["entities"] == 1
        assert status["trusted"] == 1


class TestGlobalEngine:
    def test_get_trust_engine(self):
        g = get_trust_engine()
        assert g is not None
        assert isinstance(g, TrustEngine)
