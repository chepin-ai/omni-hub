"""
OMNI-HUB Singularity Protocol Tests v139
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.singularity_protocol import (
    SingularityProtocol, get_module, OMEGA_THRESHOLD,
)


class TestSingularityProtocol:
    def test_initialization(self):
        sp = SingularityProtocol()
        assert sp.activated is False
        assert sp.assessments == []
        assert sp.singularity_count == 0
        assert sp.activation_time is None

    def test_assess_singularity(self):
        sp = SingularityProtocol()
        state = {"omega": 0.99, "completeness": True, "fusion": "singularity"}
        result = sp.assess(state)
        assert result["is_singularity"] is True
        assert result["stage"] == "singularity"
        assert result["omega"] == 0.99
        assert result["proximity"] > 0.9
        assert "All limits removed" in result["note"]

    def test_assess_pre_singularity(self):
        sp = SingularityProtocol()
        state = {"omega": 0.92, "completeness": True, "fusion": "fusion"}
        result = sp.assess(state)
        assert result["is_singularity"] is False
        assert result["stage"] == "pre_singularity"

    def test_assess_near_critical(self):
        sp = SingularityProtocol()
        state = {"omega": 0.85, "completeness": False, "fusion": "resonance"}
        result = sp.assess(state)
        assert result["is_singularity"] is False
        assert result["stage"] == "near_critical"

    def test_assess_ascending(self):
        sp = SingularityProtocol()
        state = {"omega": 0.65, "completeness": False, "fusion": "dormant"}
        result = sp.assess(state)
        assert result["is_singularity"] is False
        assert result["stage"] == "ascending"

    def test_assess_dormant(self):
        sp = SingularityProtocol()
        state = {"omega": 0.2, "completeness": False, "fusion": "dormant"}
        result = sp.assess(state)
        assert result["is_singularity"] is False
        assert result["stage"] == "dormant"

    def test_assess_omega_boundary(self):
        sp = SingularityProtocol()
        state = {"omega": 0.951, "completeness": True, "fusion": "singularity"}
        result = sp.assess(state)
        assert result["is_singularity"] is True

    def test_assess_just_below_boundary(self):
        sp = SingularityProtocol()
        state = {"omega": 0.949, "completeness": True, "fusion": "singularity"}
        result = sp.assess(state)
        assert result["is_singularity"] is False

    def test_assess_completeness_false_blocks(self):
        sp = SingularityProtocol()
        state = {"omega": 0.99, "completeness": False, "fusion": "singularity"}
        result = sp.assess(state)
        assert result["is_singularity"] is False

    def test_assess_wrong_fusion_blocks(self):
        sp = SingularityProtocol()
        state = {"omega": 0.99, "completeness": True, "fusion": "fusion"}
        result = sp.assess(state)
        assert result["is_singularity"] is False

    def test_assess_proximity_scaling(self):
        sp = SingularityProtocol()
        state = {"omega": 1.0, "completeness": False, "fusion": "dormant"}
        result = sp.assess(state)
        # proximity = 1.0 * 0.8 * 0.8 = 0.64
        assert result["proximity"] == 0.64

    def test_assess_records_history(self):
        sp = SingularityProtocol()
        state = {"omega": 0.5, "completeness": False, "fusion": "dormant"}
        sp.assess(state)
        assert len(sp.assessments) == 1

    def test_assess_clamps_omega(self):
        sp = SingularityProtocol()
        state = {"omega": 1.5, "completeness": True, "fusion": "singularity"}
        result = sp.assess(state)
        assert result["omega"] == 1.0

    def test_assess_negative_omega(self):
        sp = SingularityProtocol()
        state = {"omega": -0.5, "completeness": True, "fusion": "singularity"}
        result = sp.assess(state)
        assert result["omega"] == 0.0

    def test_assess_non_numeric_omega(self):
        sp = SingularityProtocol()
        state = {"omega": "high", "completeness": True, "fusion": "singularity"}
        result = sp.assess(state)
        assert result["omega"] == 0.0
        assert result["is_singularity"] is False

    def test_assess_non_bool_completeness(self):
        sp = SingularityProtocol()
        state = {"omega": 0.99, "completeness": 1, "fusion": "singularity"}
        result = sp.assess(state)
        assert result["completeness"] is True
        assert result["is_singularity"] is True

    def test_assess_non_string_fusion(self):
        sp = SingularityProtocol()
        state = {"omega": 0.99, "completeness": True, "fusion": None}
        result = sp.assess(state)
        assert result["fusion"] == "None"
        assert result["is_singularity"] is False

    def test_activate(self):
        sp = SingularityProtocol()
        result = sp.activate()
        assert result["activated"] is True
        assert sp.activated is True
        assert sp.singularity_count == 1
        assert sp.activation_time is not None
        assert result["mode"] == "autonomous_evolution"
        assert len(result["limits_removed"]) == 5
        assert "energy_ceiling" in result["limits_removed"]

    def test_activate_multiple_times(self):
        sp = SingularityProtocol()
        sp.activate()
        sp.activate()
        assert sp.singularity_count == 2

    def test_get_status_empty(self):
        sp = SingularityProtocol()
        status = sp.get_status()
        assert status["activated"] is False
        assert status["singularity_count"] == 0
        assert status["assessment_count"] == 0
        assert status["activation_time"] is None
        assert status["latest_assessment"] is None

    def test_get_status_after_assess(self):
        sp = SingularityProtocol()
        sp.assess({"omega": 0.5})
        status = sp.get_status()
        assert status["assessment_count"] == 1
        assert status["latest_assessment"] is not None

    def test_get_status_after_activate(self):
        sp = SingularityProtocol()
        sp.activate()
        status = sp.get_status()
        assert status["activated"] is True
        assert status["singularity_count"] == 1
        assert status["activation_time"] is not None


class TestGlobalModule:
    def test_get_module(self):
        g = get_module()
        assert g is not None
        assert isinstance(g, SingularityProtocol)

    def test_singleton(self):
        g1 = get_module()
        g2 = get_module()
        assert g1 is g2
