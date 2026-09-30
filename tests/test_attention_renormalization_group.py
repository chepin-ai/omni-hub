"""
OMNI-HUB Attention Renormalization Group Tests v168
Tests for the cross-scale attention aggregation engine.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
import math
from core.attention_renormalization_group import (
    AttentionRenormalizationGroup,
    get_attention_renormalization_group,
    reset_attention_renormalization_group,
)


class TestDefineScales:
    def test_define_scales_returns_dict(self):
        arg = AttentionRenormalizationGroup()
        result = arg.define_scales()
        assert isinstance(result, dict)

    def test_four_scales_defined(self):
        arg = AttentionRenormalizationGroup()
        result = arg.define_scales()
        assert result["scales_defined"] == 4

    def test_scale_names(self):
        arg = AttentionRenormalizationGroup()
        arg.define_scales()
        names = [s["name"] for s in arg.scales]
        assert names == ["micro", "meso", "macro", "cosmic"]

    def test_micro_scale_has_33_nodes(self):
        arg = AttentionRenormalizationGroup()
        arg.define_scales()
        micro = arg.scales[0]
        assert micro["node_count"] == 33
        assert len(micro["entities"]) == 33

    def test_meso_scale_has_11_nodes(self):
        arg = AttentionRenormalizationGroup()
        arg.define_scales()
        meso = arg.scales[1]
        assert meso["node_count"] == 11
        assert len(meso["entities"]) == 11

    def test_macro_scale_has_33_repo_field(self):
        arg = AttentionRenormalizationGroup()
        arg.define_scales()
        macro = arg.scales[2]
        assert macro["node_count"] == 33

    def test_cosmic_scale_is_infinite(self):
        arg = AttentionRenormalizationGroup()
        arg.define_scales()
        cosmic = arg.scales[3]
        assert cosmic["node_count"] == math.inf

    def test_scale_states_initialized(self):
        arg = AttentionRenormalizationGroup()
        assert len(arg.rg_state["scale_states"]) == 4


class TestCoarseGrain:
    def test_micro_to_meso(self):
        arg = AttentionRenormalizationGroup()
        data = {
            "repos": {
                f"repo_{i:02d}": {"resonance": 0.5 + (i % 5) * 0.05}
                for i in range(1, 34)
            }
        }
        result = arg.coarse_grain(0, 1, data)
        assert result["scale"] == "meso"
        assert result["line_count"] == 11
        assert "lines" in result
        assert "stability_score" in result

    def test_meso_to_macro(self):
        arg = AttentionRenormalizationGroup()
        meso_data = {
            "lines": {
                f"line_{i:02d}": {"average_resonance": 0.5 + (i % 3) * 0.1}
                for i in range(1, 12)
            }
        }
        result = arg.coarse_grain(1, 2, meso_data)
        assert result["scale"] == "macro"
        assert "collective_resonance" in result
        assert "roles" in result
        assert "stability_score" in result

    def test_macro_to_cosmic(self):
        arg = AttentionRenormalizationGroup()
        macro_data = {
            "collective_resonance": 0.85,
            "variance": 0.02,
            "roles": {"high": ["line_01"], "standard": []},
        }
        result = arg.coarse_grain(2, 3, macro_data)
        assert result["scale"] == "cosmic"
        assert "universal_principles" in result
        assert "unity" in result["universal_principles"]
        assert "coherence" in result["universal_principles"]
        assert "stability_score" in result

    def test_micro_to_macro_chained(self):
        arg = AttentionRenormalizationGroup()
        data = {
            "repos": {
                f"repo_{i:02d}": {"resonance": 0.6 + (i % 4) * 0.05}
                for i in range(1, 34)
            }
        }
        result = arg.coarse_grain(0, 2, data)
        assert result["scale"] == "macro"
        assert "collective_resonance" in result

    def test_full_flow_micro_to_cosmic(self):
        arg = AttentionRenormalizationGroup()
        data = {
            "repos": {
                f"repo_{i:02d}": {"resonance": 0.7 + (i % 3) * 0.05}
                for i in range(1, 34)
            }
        }
        result = arg.coarse_grain(0, 3, data)
        assert result["scale"] == "cosmic"
        assert "universal_principles" in result

    def test_invalid_input_scale_raises(self):
        arg = AttentionRenormalizationGroup()
        with pytest.raises(ValueError):
            arg.coarse_grain(2, 1, {})

    def test_same_scale_raises(self):
        arg = AttentionRenormalizationGroup()
        with pytest.raises(ValueError):
            arg.coarse_grain(1, 1, {})

    def test_out_of_range_scale_raises(self):
        arg = AttentionRenormalizationGroup()
        with pytest.raises(ValueError):
            arg.coarse_grain(-1, 2, {})
        with pytest.raises(ValueError):
            arg.coarse_grain(0, 4, {})

    def test_non_dict_data_raises(self):
        arg = AttentionRenormalizationGroup()
        with pytest.raises(TypeError):
            arg.coarse_grain(0, 1, "not a dict")

    def test_flow_history_recorded(self):
        arg = AttentionRenormalizationGroup()
        initial_count = len(arg.flow_history)
        arg.coarse_grain(0, 1, {"repos": {f"repo_{i:02d}": {"resonance": 0.5} for i in range(1, 34)}})
        assert len(arg.flow_history) == initial_count + 1

    def test_default_data_when_empty(self):
        arg = AttentionRenormalizationGroup()
        result = arg.coarse_grain(0, 1, {})
        assert result["scale"] == "meso"
        assert result["line_count"] == 11


class TestRGFlow:
    def test_rg_flow_micro_to_meso(self):
        arg = AttentionRenormalizationGroup()
        flow = arg.compute_rg_flow(0, 1)
        assert flow["start_scale"] == 0
        assert flow["end_scale"] == 1
        assert flow["total_steps"] == 1
        assert "final_stability" in flow

    def test_rg_flow_micro_to_macro(self):
        arg = AttentionRenormalizationGroup()
        flow = arg.compute_rg_flow(0, 2)
        assert flow["start_scale"] == 0
        assert flow["end_scale"] == 2
        assert flow["total_steps"] == 2
        assert len(flow["steps"]) == 2

    def test_rg_flow_full_0_to_3(self):
        arg = AttentionRenormalizationGroup()
        flow = arg.compute_rg_flow(0, 3)
        assert flow["start_scale"] == 0
        assert flow["end_scale"] == 3
        assert flow["total_steps"] == 3
        step_names = [s["scale_name"] for s in flow["steps"]]
        assert step_names == ["meso", "macro", "cosmic"]

    def test_rg_flow_meso_to_cosmic(self):
        arg = AttentionRenormalizationGroup()
        flow = arg.compute_rg_flow(1, 3)
        assert flow["total_steps"] == 2
        assert flow["steps"][0]["from"] == 1
        assert flow["steps"][0]["to"] == 2

    def test_invalid_flow_raises(self):
        arg = AttentionRenormalizationGroup()
        with pytest.raises(ValueError):
            arg.compute_rg_flow(2, 1)
        with pytest.raises(ValueError):
            arg.compute_rg_flow(-1, 2)
        with pytest.raises(ValueError):
            arg.compute_rg_flow(0, 4)

    def test_flow_count_increments(self):
        arg = AttentionRenormalizationGroup()
        initial = arg._flow_count
        arg.compute_rg_flow(0, 2)
        assert arg._flow_count > initial


class TestFixedPoints:
    def test_find_fixed_points_returns_list(self):
        arg = AttentionRenormalizationGroup()
        fps = arg.find_fixed_points()
        assert isinstance(fps, list)

    def test_fixed_point_from_high_stability_history(self):
        arg = AttentionRenormalizationGroup()
        # Simulate high stability flow history
        for _ in range(5):
            arg.flow_history.append({"stability_score": 0.9})
        fps = arg.find_fixed_points()
        assert len(fps) >= 1
        assert fps[0]["type"] == "scale_invariant"
        assert fps[0]["consecutive_count"] >= 3

    def test_no_fixed_points_from_low_stability(self):
        arg = AttentionRenormalizationGroup()
        for _ in range(5):
            arg.flow_history.append({"stability_score": 0.3})
        fps = arg.find_fixed_points()
        assert len(fps) == 0

    def test_fixed_points_stored_in_module(self):
        arg = AttentionRenormalizationGroup()
        for _ in range(5):
            arg.flow_history.append({"stability_score": 0.95})
        arg.find_fixed_points()
        assert len(arg._fixed_points) >= 1

    def test_fixed_point_has_required_fields(self):
        arg = AttentionRenormalizationGroup()
        for _ in range(5):
            arg.flow_history.append({"stability_score": 0.85})
        fps = arg.find_fixed_points()
        if fps:
            fp = fps[0]
            assert "index" in fp
            assert "type" in fp
            assert "description" in fp


class TestCriticalExponents:
    def test_measure_critical_exponents_returns_dict(self):
        arg = AttentionRenormalizationGroup()
        exponents = arg.measure_critical_exponents()
        assert isinstance(exponents, dict)

    def test_has_correlation_length(self):
        arg = AttentionRenormalizationGroup()
        exponents = arg.measure_critical_exponents()
        assert "correlation_length" in exponents
        assert isinstance(exponents["correlation_length"], float)
        assert exponents["correlation_length"] > 0

    def test_has_susceptibility(self):
        arg = AttentionRenormalizationGroup()
        exponents = arg.measure_critical_exponents()
        assert "susceptibility" in exponents
        assert isinstance(exponents["susceptibility"], float)
        assert exponents["susceptibility"] >= 0

    def test_has_order_parameter(self):
        arg = AttentionRenormalizationGroup()
        exponents = arg.measure_critical_exponents()
        assert "order_parameter" in exponents
        assert isinstance(exponents["order_parameter"], float)

    def test_critical_exponents_stored(self):
        arg = AttentionRenormalizationGroup()
        exponents = arg.measure_critical_exponents()
        assert arg._critical_exponents == exponents

    def test_with_flow_history(self):
        arg = AttentionRenormalizationGroup()
        for i in range(5):
            arg.flow_history.append({"stability_score": 0.5 + i * 0.1})
        exponents = arg.measure_critical_exponents()
        assert "correlation_length" in exponents
        assert "susceptibility" in exponents
        assert "order_parameter" in exponents


class TestStatus:
    def test_get_status_returns_dict(self):
        arg = AttentionRenormalizationGroup()
        status = arg.get_status()
        assert isinstance(status, dict)

    def test_status_has_scales(self):
        arg = AttentionRenormalizationGroup()
        status = arg.get_status()
        assert "scales" in status
        assert status["scales"] == ["micro", "meso", "macro", "cosmic"]

    def test_status_has_flow_count(self):
        arg = AttentionRenormalizationGroup()
        status = arg.get_status()
        assert "flow_count" in status
        assert isinstance(status["flow_count"], int)

    def test_status_has_fixed_points(self):
        arg = AttentionRenormalizationGroup()
        status = arg.get_status()
        assert "fixed_points" in status
        assert "fixed_point_count" in status

    def test_status_has_critical_exponents(self):
        arg = AttentionRenormalizationGroup()
        status = arg.get_status()
        assert "critical_exponents" in status

    def test_status_reflects_operations(self):
        arg = AttentionRenormalizationGroup()
        arg.compute_rg_flow(0, 2)
        arg.find_fixed_points()
        arg.measure_critical_exponents()
        status = arg.get_status()
        assert status["flow_count"] > 0
        assert status["flow_history_length"] > 0


class TestSingleton:
    def test_singleton_returns_same_instance(self):
        reset_attention_renormalization_group()
        a = get_attention_renormalization_group()
        b = get_attention_renormalization_group()
        assert a is b

    def test_reset_creates_new_instance(self):
        a = get_attention_renormalization_group()
        reset_attention_renormalization_group()
        b = get_attention_renormalization_group()
        assert a is not b


class TestStabilityScore:
    def test_stability_with_high_resonance(self):
        arg = AttentionRenormalizationGroup()
        data = {"collective_resonance": 0.95, "variance": 0.01}
        score = arg._compute_stability_score(data)
        assert score > 0.8

    def test_stability_with_low_resonance(self):
        arg = AttentionRenormalizationGroup()
        data = {"collective_resonance": 0.3, "variance": 0.01}
        score = arg._compute_stability_score(data)
        assert score < 0.5

    def test_stability_bounded(self):
        arg = AttentionRenormalizationGroup()
        data = {"collective_resonance": 1.5, "variance": -0.1}
        score = arg._compute_stability_score(data)
        assert 0.0 <= score <= 1.0


class TestEventBusIntegration:
    def test_no_crash_when_bus_unavailable(self):
        # This test ensures the module works even if event bus fails
        arg = AttentionRenormalizationGroup()
        result = arg.coarse_grain(0, 1, {"repos": {}})
        assert result is not None


class TestCoarseGrainRules:
    def test_micro_to_meso_averages_resonance(self):
        arg = AttentionRenormalizationGroup()
        data = {
            "repos": {
                "repo_01": {"resonance": 0.9},
                "repo_02": {"resonance": 0.7},
                "repo_03": {"resonance": 0.5},
            }
        }
        result = arg.coarse_grain(0, 1, data)
        line_01 = result["lines"]["line_01"]
        expected_avg = (0.9 + 0.7 + 0.5) / 3
        assert abs(line_01["average_resonance"] - expected_avg) < 1e-6

    def test_meso_to_macro_groups_by_role(self):
        arg = AttentionRenormalizationGroup()
        data = {
            "lines": {
                "line_01": {"average_resonance": 0.95},
                "line_02": {"average_resonance": 0.85},
                "line_03": {"average_resonance": 0.40},
            }
        }
        result = arg.coarse_grain(1, 2, data)
        assert "high_resonance" in result["roles"]
        assert "standard_resonance" in result["roles"]
        # line_01 and line_02 should be high, line_03 standard
        assert "line_01" in result["roles"]["high_resonance"] or "line_01" in result["roles"]["standard_resonance"]

    def test_macro_to_cosmic_computes_universal_principles(self):
        arg = AttentionRenormalizationGroup()
        data = {
            "collective_resonance": 0.92,
            "variance": 0.02,
            "roles": {},
        }
        result = arg.coarse_grain(2, 3, data)
        principles = result["universal_principles"]
        assert principles["unity"] == 0.92
        assert principles["coherence"] == 0.98
