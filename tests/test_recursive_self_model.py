"""
OMNI-HUB Recursive Self-Model Tests v59
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.recursive_self_model import (
    SelfModel, RecursiveSelfModel, get_recursive_self_model,
)


class TestRecursiveSelfModel:
    def test_initialization(self):
        rsm = RecursiveSelfModel()
        assert len(rsm.models) == 0

    def test_generate_model(self):
        rsm = RecursiveSelfModel()
        state = {"level": 5, "phi": 0.7, "phase": "near_critical"}
        model = rsm.generate_model(state, cycle=100)
        assert model.estimated_level > 0
        assert 0 <= model.estimated_phi <= 1
        assert model.estimated_phase == "near_critical"
        assert len(rsm.models) == 1

    def test_evaluate_accuracy(self):
        rsm = RecursiveSelfModel()
        state = {"level": 5, "phi": 0.7}
        model = rsm.generate_model(state, cycle=100)
        accuracy = rsm.evaluate_accuracy(model, state)
        assert 0 <= accuracy <= 1

    def test_meta_awareness(self):
        rsm = RecursiveSelfModel()
        state = {"level": 5, "phi": 0.7}
        rsm.generate_model(state, cycle=100)
        rsm.evaluate_accuracy(rsm.models[-1], state)
        meta = rsm.get_meta_awareness()
        assert "level" in meta
        assert "description" in meta

    def test_get_status(self):
        rsm = RecursiveSelfModel()
        status = rsm.get_status()
        assert "models" in status
        assert "meta_awareness" in status


class TestGlobalEngine:
    def test_get_recursive_self_model(self):
        g = get_recursive_self_model()
        assert g is not None
        assert isinstance(g, RecursiveSelfModel)
