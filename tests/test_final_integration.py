"""
OMNI-HUB Final Integration Tests v112
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.final_integration import (
    FinalIntegration, get_final_integration,
)


class TestFinalIntegration:
    def test_initialization(self):
        fi = FinalIntegration()
        assert fi.integration_count == 0
        assert fi.get_status()["version"] == 112

    def test_count_active_modules(self):
        fi = FinalIntegration()
        state = {
            "self_awareness": {"status": "ok"},
            "trust_engine": {"global_trust": 0.9},
            "phi": 0.8,
            "level": 15,
        }
        count = fi.count_active_modules(state)
        assert count >= 2

    def test_compute_unity_low(self):
        fi = FinalIntegration()
        state = {"phi": 0.3, "line_coherence": 0.2, "level": 2}
        result = fi.compute_unity(state)
        assert result["unity"] < 0.5
        assert result["stage"] == "differentiation"

    def test_compute_unity_high(self):
        fi = FinalIntegration()
        state = {
            "phi": 0.95, "line_coherence": 0.95, "level": 22,
            "self_awareness": {}, "trust_engine": {}, "aesthetic_judgment": {},
            "ontology": {}, "transcendence": {}, "moral_reasoning": {},
            "wisdom_synthesis": {}, "singularity_gate": {}, "intentionality": {},
            "predictive_model": {}, "creative_destruction": {}, "field_awareness": {},
            "stochastic_resonance": {}, "final_integration": {},
            "embodied_cognition": {}, "extended_mind": {}, "enactive_cognition": {},
            "dialectic": {}, "humor_perception": {}, "metaphorical_reasoning": {},
        }
        result = fi.compute_unity(state)
        assert result["unity"] > 0.5
        assert result["stage"] in ["integration", "convergence", "omega"]

    def test_compute_unity_omega(self):
        fi = FinalIntegration()
        state = {
            "phi": 0.95, "line_coherence": 0.95, "level": 22,
            "self_awareness": {}, "trust_engine": {}, "aesthetic_judgment": {},
            "ontology": {}, "transcendence": {}, "moral_reasoning": {},
            "wisdom_synthesis": {}, "singularity_gate": {}, "intentionality": {},
            "predictive_model": {}, "creative_destruction": {}, "field_awareness": {},
        }
        result = fi.compute_unity(state)
        assert result["version"] == 112

    def test_get_status(self):
        fi = FinalIntegration()
        fi.compute_unity({"phi": 0.5, "line_coherence": 0.5, "level": 5})
        status = fi.get_status()
        assert status["integrations"] == 1
        assert status["latest"] is not None


class TestGlobalEngine:
    def test_get_final_integration(self):
        g = get_final_integration()
        assert g is not None
        assert isinstance(g, FinalIntegration)
