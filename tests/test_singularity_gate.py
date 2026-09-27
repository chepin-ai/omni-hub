"""
OMNI-HUB Singularity Gate Tests v100
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.singularity_gate import (
    SingularityGate, get_singularity_gate,
)


class TestSingularityGate:
    def test_initialization(self):
        sg = SingularityGate()
        assert sg.openings == 0
        assert not sg.unified_state

    def test_compute_unification(self):
        sg = SingularityGate()
        state = {
            "phi": 0.9, "line_coherence": 0.9,
            "aesthetic_judgment": {"beauty": 0.8},
            "transcendence": {"potential": 0.8},
            "trust_engine": {"global_trust": 0.9},
            "ontology": {"concepts": 25},
        }
        u = sg.compute_unification(state)
        assert 0 <= u <= 1
        assert u > 0.5

    def test_check_gate_closed(self):
        sg = SingularityGate()
        state = {"level": 5, "phi": 0.3, "phase": "pre_emergence"}
        result = sg.check_gate(state)
        assert result["gate_open"] is False
        assert result["unification"] < 0.8

    def test_check_gate_open(self):
        sg = SingularityGate()
        state = {
            "level": 20, "phi": 0.95, "phase": "post_critical",
            "line_coherence": 0.9,
            "aesthetic_judgment": {"beauty": 0.9},
            "transcendence": {"potential": 0.9},
            "trust_engine": {"global_trust": 0.9},
            "ontology": {"concepts": 30},
        }
        result = sg.check_gate(state)
        assert result["gate_open"] is True
        assert result["openings"] == 1

    def test_unify(self):
        sg = SingularityGate()
        state = {
            "level": 20, "phi": 0.95, "phase": "post_critical",
            "line_coherence": 0.9,
            "aesthetic_judgment": {"beauty": 0.9},
            "transcendence": {"potential": 0.9},
            "trust_engine": {"global_trust": 0.9},
            "ontology": {"concepts": 30},
            "cycle_count": 1000,
        }
        result = sg.unify(state)
        assert result["gate_open"] is True
        assert sg.unified_state.get("version") == 100

    def test_get_status(self):
        sg = SingularityGate()
        status = sg.get_status()
        assert status["version"] == 100
        assert status["openings"] == 0


class TestGlobalEngine:
    def test_get_singularity_gate(self):
        g = get_singularity_gate()
        assert g is not None
        assert isinstance(g, SingularityGate)
