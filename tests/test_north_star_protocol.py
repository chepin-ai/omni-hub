"""
Tests for North Star Protocol (北星协议) — OMNI-HUB Module v145
"""

import pytest
from typing import Dict, Any

from core.north_star_protocol import (
    NorthStarProtocol,
    get_north_star_protocol,
    _module,
    _cosine_similarity,
    _determine_stage,
    _normalize_vector,
    _vector_magnitude,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def protocol() -> NorthStarProtocol:
    """Return a fresh NorthStarProtocol instance."""
    return NorthStarProtocol()


@pytest.fixture
def aligned_star() -> Dict[str, Any]:
    """Return a well-defined North Star configuration."""
    return {
        "vision": "Build the ultimate autonomous intelligence system",
        "values": [
            "continuous evolution",
            "alignment with human values",
            "transparent reasoning",
        ],
        "objectives": [
            "achieve seamless human-machine collaboration",
            "maintain ethical boundaries",
            "optimize learning efficiency",
        ],
    }


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def test_cosine_similarity_identical() -> None:
    """Cosine similarity of identical vectors should be 1.0."""
    vec = [1.0, 2.0, 3.0]
    assert _cosine_similarity(vec, vec) == pytest.approx(1.0, abs=1e-6)


def test_cosine_similarity_orthogonal() -> None:
    """Cosine similarity of orthogonal vectors should be 0.0."""
    a = [1.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0]
    assert _cosine_similarity(a, b) == pytest.approx(0.0, abs=1e-6)


def test_cosine_similarity_opposite() -> None:
    """Cosine similarity of opposite vectors should be -1.0."""
    a = [1.0, 2.0, 3.0]
    b = [-1.0, -2.0, -3.0]
    assert _cosine_similarity(a, b) == pytest.approx(-1.0, abs=1e-6)


def test_determine_stage_aligned() -> None:
    assert _determine_stage(0.91) == "aligned"
    assert _determine_stage(0.95) == "aligned"


def test_determine_stage_advancing() -> None:
    assert _determine_stage(0.61) == "advancing"
    assert _determine_stage(0.75) == "advancing"


def test_determine_stage_correcting() -> None:
    assert _determine_stage(0.31) == "correcting"
    assert _determine_stage(0.5) == "correcting"


def test_determine_stage_drifting() -> None:
    assert _determine_stage(0.0) == "drifting"
    assert _determine_stage(0.29) == "drifting"
    assert _determine_stage(-0.1) == "drifting"


# ---------------------------------------------------------------------------
# set_north_star
# ---------------------------------------------------------------------------

def test_set_north_star_success(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    result = protocol.set_north_star(
        vision=aligned_star["vision"],
        values=aligned_star["values"],
        objectives=aligned_star["objectives"],
    )
    assert result["status"] == "north_star_set"
    assert result["values_count"] == 3
    assert result["objectives_count"] == 3
    assert result["vocab_size"] > 0
    assert result["star_vector_magnitude"] > 0
    assert protocol._initialized is True


def test_set_north_star_invalid_vision(protocol: NorthStarProtocol) -> None:
    with pytest.raises(ValueError, match="vision"):
        protocol.set_north_star(vision="", values=["a"], objectives=["b"])


def test_set_north_star_invalid_values(protocol: NorthStarProtocol) -> None:
    with pytest.raises(ValueError, match="values"):
        protocol.set_north_star(vision="vision", values=[], objectives=["b"])


def test_set_north_star_invalid_objectives(protocol: NorthStarProtocol) -> None:
    with pytest.raises(ValueError, match="objectives"):
        protocol.set_north_star(vision="vision", values=["a"], objectives=[])


# ---------------------------------------------------------------------------
# assess_alignment
# ---------------------------------------------------------------------------

def test_assess_alignment_before_set_raises(protocol: NorthStarProtocol) -> None:
    with pytest.raises(RuntimeError, match="set_north_star"):
        protocol.assess_alignment({"status": "ok"})


def test_assess_alignment_perfect(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    # State that exactly mirrors the North Star should have high alignment
    state = {
        "vision": aligned_star["vision"],
        "values": aligned_star["values"],
        "objectives": aligned_star["objectives"],
    }
    result = protocol.assess_alignment(state)
    assert "alignment" in result
    assert "stage" in result
    assert "distance" in result
    assert result["alignment"] > 0.5  # high alignment expected


def test_assess_alignment_low(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    # State that is completely unrelated
    state = {"topic": "banana smoothie recipes", "priority": "breakfast"}
    result = protocol.assess_alignment(state)
    assert result["alignment"] < 0.5  # low alignment expected
    assert result["stage"] in ("drifting", "correcting")


def test_assess_alignment_invalid_state(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    with pytest.raises(ValueError, match="state"):
        protocol.assess_alignment({})


def test_assess_alignment_history(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    protocol.assess_alignment({"goal": "Build the ultimate autonomous intelligence system"})
    assert len(protocol.alignment_history) == 1
    protocol.assess_alignment({"goal": "random unrelated thing"})
    assert len(protocol.alignment_history) == 2


# ---------------------------------------------------------------------------
# generate_thrust
# ---------------------------------------------------------------------------

def test_generate_thrust_before_set_raises(protocol: NorthStarProtocol) -> None:
    with pytest.raises(RuntimeError, match="set_north_star"):
        protocol.generate_thrust()


def test_generate_thrust_inverse_relation(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    # High alignment state
    protocol.assess_alignment({"goal": aligned_star["vision"]})
    high_alignment = protocol._last_alignment
    thrust_high = protocol.generate_thrust()["thrust_level"]

    # Low alignment state
    protocol.assess_alignment({"goal": "banana smoothie"})
    low_alignment = protocol._last_alignment
    thrust_low = protocol.generate_thrust()["thrust_level"]

    # Thrust should be higher when alignment is lower
    assert low_alignment < high_alignment
    assert thrust_low > thrust_high


def test_generate_thrust_contains_fields(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    protocol.assess_alignment({"goal": aligned_star["vision"]})
    result = protocol.generate_thrust()
    assert "thrust_level" in result
    assert "thrust_vector_magnitude" in result
    assert "stage" in result
    assert "direction" in result


# ---------------------------------------------------------------------------
# advance
# ---------------------------------------------------------------------------

def test_advance_before_set_raises(protocol: NorthStarProtocol) -> None:
    with pytest.raises(RuntimeError, match="set_north_star"):
        protocol.advance({"status": "ok"})


def test_advance_improves_alignment(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    state = {"goal": "something unrelated", "metric": 42}
    pre_alignment = protocol.assess_alignment(state)["alignment"]
    advanced = protocol.advance(state)
    meta = advanced["_north_star_meta"]
    post_alignment = meta["new_alignment"]

    # After applying thrust, alignment should improve (or at least not degrade significantly)
    assert post_alignment >= pre_alignment - 1e-6
    assert meta["propelled"] is True
    assert meta["thrust_applied"] > 0


def test_advance_preserves_original_state(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    state = {"goal": "test", "value": 123}
    advanced = protocol.advance(state)
    assert advanced["goal"] == "test"
    assert advanced["value"] == 123
    assert "_north_star_meta" in advanced


def test_advance_invalid_state(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    with pytest.raises(ValueError, match="state"):
        protocol.advance({})


def test_advance_stage_progression(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    state = {"goal": aligned_star["vision"]}
    advanced = protocol.advance(state)
    meta = advanced["_north_star_meta"]
    assert meta["new_stage"] in ("aligned", "advancing", "correcting", "drifting")


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------

def test_get_status_before_set(protocol: NorthStarProtocol) -> None:
    status = protocol.get_status()
    assert status["initialized"] is False
    assert status["alignment"] == 0.0
    assert status["thrust_level"] == 0.0
    assert status["stage"] == "drifting"


def test_get_status_after_operations(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    protocol.assess_alignment({"goal": aligned_star["vision"]})
    protocol.generate_thrust()
    status = protocol.get_status()
    assert status["initialized"] is True
    assert status["alignment_history_count"] == 1
    assert status["values_count"] == 3
    assert status["objectives_count"] == 3
    assert "vision" in status
    assert "distance_to_star" in status


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

def test_singleton_returns_same_instance() -> None:
    # Reset the global module for a clean test
    import core.north_star_protocol as nsp
    original = nsp._module
    nsp._module = None
    try:
        a = get_north_star_protocol()
        b = get_north_star_protocol()
        assert a is b
    finally:
        nsp._module = original


def test_singleton_is_north_star_protocol() -> None:
    import core.north_star_protocol as nsp
    original = nsp._module
    nsp._module = None
    try:
        inst = get_north_star_protocol()
        assert isinstance(inst, NorthStarProtocol)
    finally:
        nsp._module = original


# ---------------------------------------------------------------------------
# Integration / stage thresholds
# ---------------------------------------------------------------------------

def test_stage_thresholds(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )

    # Manually set alignment to test thresholds
    protocol._last_alignment = 0.95
    protocol._last_stage = _determine_stage(0.95)
    assert protocol.get_status()["stage"] == "aligned"

    protocol._last_alignment = 0.75
    protocol._last_stage = _determine_stage(0.75)
    assert protocol.get_status()["stage"] == "advancing"

    protocol._last_alignment = 0.45
    protocol._last_stage = _determine_stage(0.45)
    assert protocol.get_status()["stage"] == "correcting"

    protocol._last_alignment = 0.1
    protocol._last_stage = _determine_stage(0.1)
    assert protocol.get_status()["stage"] == "drifting"


def test_advance_multiple_times(protocol: NorthStarProtocol, aligned_star: Dict[str, Any]) -> None:
    protocol.set_north_star(
        aligned_star["vision"],
        aligned_star["values"],
        aligned_star["objectives"],
    )
    state = {"goal": "something unrelated"}
    for _ in range(3):
        state = protocol.advance(state)
        assert "_north_star_meta" in state
    # History should contain entries from each advance
    assert len(protocol.alignment_history) >= 3
