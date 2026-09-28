"""
Tests for QF-OS Fusion (QF-OS融合) — OMNI-HUB Module v161
"""

import os
import sys
import pytest
from typing import Dict, Any

# Ensure core/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.qfos_fusion import (
    QFOSFusion,
    get_qfos_fusion,
    DEFAULT_QFOS_PATTERNS,
    VALID_PATTERN_TYPES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fusion() -> QFOSFusion:
    """Provide a fresh QFOSFusion instance."""
    return QFOSFusion()


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton before each test."""
    import core.qfos_fusion as _mod
    _mod._module = None
    yield
    _mod._module = None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestQFOSFusion:
    """Comprehensive tests for QFOSFusion."""

    # -- __init__ ------------------------------------------------------------

    def test_init_default_state(self, fusion: QFOSFusion) -> None:
        """Default fusion_state should start with score 0.0 and inactive."""
        assert fusion._fusion_state["fusion_score"] == 0.0
        assert fusion._fusion_state["active"] is False

    def test_init_custom_state(self) -> None:
        """Custom fusion_state should be accepted."""
        custom = {"fusion_score": 0.5, "active": True}
        f = QFOSFusion(fusion_state=custom)
        assert f._fusion_state["fusion_score"] == 0.5
        assert f._fusion_state["active"] is True

    def test_init_custom_patterns(self) -> None:
        """Custom qfos_patterns should override defaults."""
        custom = {"custom_pattern": {"type": "test"}}
        f = QFOSFusion(qfos_patterns=custom)
        assert f._qfos_patterns == custom

    # -- fuse_with_qfos ------------------------------------------------------

    def test_fuse_with_qfos_structure(self, fusion: QFOSFusion) -> None:
        """fuse_with_qfos must return a dict with expected keys."""
        result = fusion.fuse_with_qfos()
        assert isinstance(result, dict)
        assert result["status"] == "fusion_complete"
        assert "extracted_patterns" in result
        assert "fusion_score" in result
        assert "fusion_level" in result

    def test_fuse_with_qfos_extracts_all_patterns(self, fusion: QFOSFusion) -> None:
        """All five default patterns should be extracted."""
        result = fusion.fuse_with_qfos()
        extracted = result["extracted_patterns"]
        for pattern in VALID_PATTERN_TYPES:
            assert pattern in extracted
        assert result["fusion_score"] == 1.0
        assert result["fusion_level"] == "merged"

    def test_fuse_updates_internal_state(self, fusion: QFOSFusion) -> None:
        """fuse_with_qfos should update internal extracted_patterns."""
        fusion.fuse_with_qfos()
        assert len(fusion._extracted_patterns) == len(DEFAULT_QFOS_PATTERNS)

    # -- extract_navigation_pattern ------------------------------------------

    def test_extract_perception_loop(self, fusion: QFOSFusion) -> None:
        """Extract perception_loop pattern."""
        result = fusion.extract_navigation_pattern("perception_loop")
        assert result["pattern_type"] == "perception_loop"
        assert result["pattern"]["type"] == "sensor_fusion"
        assert "lidar" in result["pattern"]["inputs"]

    def test_extract_decision_graph(self, fusion: QFOSFusion) -> None:
        """Extract decision_graph pattern."""
        result = fusion.extract_navigation_pattern("decision_graph")
        assert result["pattern_type"] == "decision_graph"
        assert result["pattern"]["type"] == "neural_policy"
        assert result["pattern"]["layers"] == 12

    def test_extract_execution_engine(self, fusion: QFOSFusion) -> None:
        """Extract execution_engine pattern."""
        result = fusion.extract_navigation_pattern("execution_engine")
        assert result["pattern_type"] == "execution_engine"
        assert result["pattern"]["type"] == "motor_control"
        assert result["pattern"]["latency_ms"] == 5

    def test_extract_feedback_mechanism(self, fusion: QFOSFusion) -> None:
        """Extract feedback_mechanism pattern."""
        result = fusion.extract_navigation_pattern("feedback_mechanism")
        assert result["pattern_type"] == "feedback_mechanism"
        assert result["pattern"]["type"] == "slam_loop"
        assert result["pattern"]["convergence_rate"] == 0.98

    def test_extract_evolution_protocol(self, fusion: QFOSFusion) -> None:
        """Extract evolution_protocol pattern."""
        result = fusion.extract_navigation_pattern("evolution_protocol")
        assert result["pattern_type"] == "evolution_protocol"
        assert result["pattern"]["type"] == "meta_learning"
        assert result["pattern"]["adaptation_speed"] == "fast"

    def test_extract_unknown_pattern(self, fusion: QFOSFusion) -> None:
        """Unknown pattern_type should return an error dict."""
        result = fusion.extract_navigation_pattern("nonexistent")
        assert "error" in result
        assert result["pattern_type"] == "nonexistent"

    # -- translate_to_omni_hub -----------------------------------------------

    def test_translate_perception(self, fusion: QFOSFusion) -> None:
        """Translate a perception pattern to OMNI-HUB format."""
        pattern = {"type": "sensor_fusion", "inputs": ["lidar"]}
        result = fusion.translate_to_omni_hub(pattern)
        assert result["source"] == "qfos"
        assert result["target"] == "omni_hub"
        assert result["omni_hub_capability"] == "kernel.perception"
        assert result["native"] is True

    def test_translate_decision(self, fusion: QFOSFusion) -> None:
        """Translate a decision pattern to OMNI-HUB format."""
        pattern = {"type": "neural_policy", "layers": 12}
        result = fusion.translate_to_omni_hub(pattern)
        assert result["omni_hub_capability"] == "kernel.decision"

    def test_translate_execution(self, fusion: QFOSFusion) -> None:
        """Translate an execution pattern to OMNI-HUB format."""
        pattern = {"type": "motor_control", "precision": 0.001}
        result = fusion.translate_to_omni_hub(pattern)
        assert result["omni_hub_capability"] == "kernel.execution"

    def test_translate_feedback(self, fusion: QFOSFusion) -> None:
        """Translate a feedback pattern to OMNI-HUB format."""
        pattern = {"type": "slam_loop", "convergence_rate": 0.98}
        result = fusion.translate_to_omni_hub(pattern)
        assert result["omni_hub_capability"] == "kernel.feedback"

    def test_translate_evolution(self, fusion: QFOSFusion) -> None:
        """Translate an evolution pattern to OMNI-HUB format."""
        pattern = {"type": "meta_learning", "adaptation_speed": "fast"}
        result = fusion.translate_to_omni_hub(pattern)
        assert result["omni_hub_capability"] == "kernel.evolution"

    def test_translate_unknown_pattern(self, fusion: QFOSFusion) -> None:
        """Translate an unknown pattern type."""
        pattern = {"type": "unknown_type"}
        result = fusion.translate_to_omni_hub(pattern)
        assert result["omni_hub_capability"] == "kernel.unknown"

    def test_translate_non_dict(self, fusion: QFOSFusion) -> None:
        """translate_to_omni_hub with non-dict should return error."""
        result = fusion.translate_to_omni_hub("not_a_dict")
        assert "error" in result

    def test_translation_count_increments(self, fusion: QFOSFusion) -> None:
        """translation_count should increment on each translation."""
        assert fusion._translation_count == 0
        fusion.translate_to_omni_hub({"type": "sensor_fusion"})
        assert fusion._translation_count == 1
        fusion.translate_to_omni_hub({"type": "neural_policy"})
        assert fusion._translation_count == 2

    # -- activate_fusion_mode ------------------------------------------------

    def test_activate_fusion_mode_structure(self, fusion: QFOSFusion) -> None:
        """activate_fusion_mode must return dict with expected keys."""
        result = fusion.activate_fusion_mode()
        assert isinstance(result, dict)
        assert result["status"] == "activated"
        assert "fusion_level" in result
        assert "fusion_score" in result
        assert "capabilities" in result
        assert result["native_integration"] is True

    def test_activate_fusion_mode_all_capabilities(self, fusion: QFOSFusion) -> None:
        """All five capabilities should be present after activation."""
        result = fusion.activate_fusion_mode()
        caps = result["capabilities"]
        assert len(caps) == len(DEFAULT_QFOS_PATTERNS)
        cap_names = [c["capability"] for c in caps]
        assert "kernel.perception" in cap_names
        assert "kernel.decision" in cap_names
        assert "kernel.execution" in cap_names
        assert "kernel.feedback" in cap_names
        assert "kernel.evolution" in cap_names

    def test_activate_sets_active(self, fusion: QFOSFusion) -> None:
        """activate_fusion_mode should set active to True."""
        assert fusion._fusion_state["active"] is False
        fusion.activate_fusion_mode()
        assert fusion._fusion_state["active"] is True

    def test_activate_without_prior_fuse(self, fusion: QFOSFusion) -> None:
        """activate_fusion_mode should auto-fuse if not already fused."""
        assert len(fusion._extracted_patterns) == 0
        fusion.activate_fusion_mode()
        assert len(fusion._extracted_patterns) == len(DEFAULT_QFOS_PATTERNS)

    # -- get_status ----------------------------------------------------------

    def test_get_status_initial(self, fusion: QFOSFusion) -> None:
        """Initial status should reflect empty state."""
        status = fusion.get_status()
        assert status["fusion_level"] == "detached"
        assert status["extracted_patterns"] == []
        assert status["translation_count"] == 0
        assert status["active"] is False
        assert status["fusion_score"] == 0.0

    def test_get_status_after_fuse(self, fusion: QFOSFusion) -> None:
        """Status should reflect fused state."""
        fusion.fuse_with_qfos()
        status = fusion.get_status()
        assert status["fusion_level"] == "merged"
        assert len(status["extracted_patterns"]) == len(DEFAULT_QFOS_PATTERNS)
        assert status["fusion_score"] == 1.0

    def test_get_status_after_activate(self, fusion: QFOSFusion) -> None:
        """Status should reflect activated state."""
        fusion.activate_fusion_mode()
        status = fusion.get_status()
        assert status["active"] is True
        assert status["translation_count"] == len(DEFAULT_QFOS_PATTERNS)

    # -- fusion levels -------------------------------------------------------

    def test_fusion_level_detached(self, fusion: QFOSFusion) -> None:
        """Score below 0.3 should be detached."""
        assert fusion._compute_fusion_level(0.0) == "detached"
        assert fusion._compute_fusion_level(0.29) == "detached"

    def test_fusion_level_connected(self, fusion: QFOSFusion) -> None:
        """Score 0.3–0.49 should be connected."""
        assert fusion._compute_fusion_level(0.3) == "connected"
        assert fusion._compute_fusion_level(0.49) == "connected"

    def test_fusion_level_linked(self, fusion: QFOSFusion) -> None:
        """Score 0.5–0.69 should be linked."""
        assert fusion._compute_fusion_level(0.5) == "linked"
        assert fusion._compute_fusion_level(0.69) == "linked"

    def test_fusion_level_fused(self, fusion: QFOSFusion) -> None:
        """Score 0.7–0.89 should be fused."""
        assert fusion._compute_fusion_level(0.7) == "fused"
        assert fusion._compute_fusion_level(0.89) == "fused"

    def test_fusion_level_merged(self, fusion: QFOSFusion) -> None:
        """Score 0.9+ should be merged."""
        assert fusion._compute_fusion_level(0.9) == "merged"
        assert fusion._compute_fusion_level(1.0) == "merged"

    # -- singleton -----------------------------------------------------------

    def test_singleton_returns_same_instance(self) -> None:
        """get_qfos_fusion should return the same instance."""
        f1 = get_qfos_fusion()
        f2 = get_qfos_fusion()
        assert f1 is f2

    def test_singleton_is_qfos_fusion(self) -> None:
        """get_qfos_fusion should return a QFOSFusion instance."""
        f = get_qfos_fusion()
        assert isinstance(f, QFOSFusion)
