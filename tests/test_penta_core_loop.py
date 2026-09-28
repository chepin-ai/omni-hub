"""
Tests for OMNI-HUB Module v163: Penta-Core Loop (五核闭环)
"""

import pytest
from core.penta_core_loop import (
    PentaCoreLoop,
    get_penta_core_loop,
    HEALTH_LEVELS,
    EVOLUTION_LEVELS,
    CORE_NAMES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def fresh_loop() -> PentaCoreLoop:
    """Return a fresh PentaCoreLoop instance."""
    return PentaCoreLoop()


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton before each test."""
    import core.penta_core_loop as mod
    mod._module = None
    yield
    mod._module = None


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------
class TestInitializeLoop:
    def test_initialize_loop_returns_dict(self, fresh_loop: PentaCoreLoop) -> None:
        result = fresh_loop.initialize_loop()
        assert isinstance(result, dict)
        assert result["status"] == "initialized"
        assert "initialized_at" in result
        assert "cores" in result

    def test_all_five_cores_initialized(self, fresh_loop: PentaCoreLoop) -> None:
        result = fresh_loop.initialize_loop()
        cores = result["cores"]
        for name in CORE_NAMES:
            assert name in cores
            assert cores[name]["status"] == "ready"
            assert cores[name]["quality"] == 1.0

    def test_loop_state_after_init(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        assert fresh_loop.loop_state["initialized"] is True
        assert fresh_loop.loop_state["running"] is True
        assert fresh_loop.loop_state["current_phase"] == "idle"

    def test_cycle_count_reset_on_init(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.cycle_count = 42
        fresh_loop.initialize_loop()
        assert fresh_loop.cycle_count == 0


# ---------------------------------------------------------------------------
# Tick loop tests
# ---------------------------------------------------------------------------
class TestTickLoop:
    def test_tick_returns_dict(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        result = fresh_loop.tick_loop()
        assert isinstance(result, dict)
        assert "cycle" in result
        assert "cores" in result
        assert "health" in result
        assert "bottleneck" in result

    def test_tick_increments_cycle_count(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        assert fresh_loop.cycle_count == 0
        fresh_loop.tick_loop()
        assert fresh_loop.cycle_count == 1
        fresh_loop.tick_loop()
        assert fresh_loop.cycle_count == 2

    def test_tick_sequence_executed(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        result = fresh_loop.tick_loop()
        cores = result["cores"]
        for name in CORE_NAMES:
            assert name in cores
            assert "output" in cores[name]
            assert "latency_ms" in cores[name]
            assert cores[name]["latency_ms"] >= 0.0

    def test_tick_auto_initializes(self, fresh_loop: PentaCoreLoop) -> None:
        # tick_loop should auto-initialize if not already initialized
        assert fresh_loop.loop_state["initialized"] is False
        result = fresh_loop.tick_loop()
        assert fresh_loop.loop_state["initialized"] is True
        assert result["cycle"] == 1

    def test_tick_updates_core_status(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        fresh_loop.tick_loop()
        for name in CORE_NAMES:
            assert fresh_loop.cores[name]["status"] == "completed"


# ---------------------------------------------------------------------------
# Health measurement tests
# ---------------------------------------------------------------------------
class TestMeasureLoopHealth:
    def test_health_is_dict(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        health = fresh_loop.measure_loop_health()
        assert isinstance(health, dict)
        assert "score" in health
        assert "level" in health
        assert "breakdown" in health

    def test_perfect_health_on_init(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        health = fresh_loop.measure_loop_health()
        assert health["score"] == 1.0
        assert health["level"] == "perfect"

    def test_health_breakdown_sums(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        # After init without tick, cores have quality=1.0
        health = fresh_loop.measure_loop_health()
        breakdown = health["breakdown"]
        expected = sum(breakdown.values()) / 5.0
        assert health["score"] == pytest.approx(expected, abs=0.0001)

    def test_health_levels(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        # Manually degrade one core to test level boundaries
        fresh_loop.cores["sense"]["quality"] = 0.5
        fresh_loop.cores["decide"]["quality"] = 0.5
        fresh_loop.cores["act"]["quality"] = 0.5
        fresh_loop.cores["feedback"]["quality"] = 0.5
        fresh_loop.cores["evolve"]["quality"] = 0.5
        health = fresh_loop.measure_loop_health()
        assert health["score"] == 0.5
        assert health["level"] == "degraded"

    def test_health_level_broken(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        for name in CORE_NAMES:
            fresh_loop.cores[name]["quality"] = 0.0
        health = fresh_loop.measure_loop_health()
        assert health["score"] == 0.0
        assert health["level"] == "broken"

    def test_health_level_healthy(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        for name in CORE_NAMES:
            fresh_loop.cores[name]["quality"] = 0.85
        health = fresh_loop.measure_loop_health()
        assert health["score"] == 0.85
        assert health["level"] == "healthy"

    def test_health_level_functional(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        for name in CORE_NAMES:
            fresh_loop.cores[name]["quality"] = 0.65
        health = fresh_loop.measure_loop_health()
        assert health["score"] == 0.65
        assert health["level"] == "functional"


# ---------------------------------------------------------------------------
# Bottleneck detection tests
# ---------------------------------------------------------------------------
class TestDetectLoopBottleneck:
    def test_bottleneck_returns_dict(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        bottleneck = fresh_loop.detect_loop_bottleneck()
        assert isinstance(bottleneck, dict)
        assert "bottleneck_core" in bottleneck
        assert "reason" in bottleneck
        assert "metrics" in bottleneck

    def test_bottleneck_lowest_quality(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        fresh_loop.cores["act"]["quality"] = 0.3
        fresh_loop.cores["sense"]["quality"] = 0.9
        bottleneck = fresh_loop.detect_loop_bottleneck()
        assert bottleneck["bottleneck_core"] == "act"

    def test_bottleneck_tie_break_by_latency(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        # Set all equal quality, one with higher latency
        for name in CORE_NAMES:
            fresh_loop.cores[name]["quality"] = 0.8
            fresh_loop.cores[name]["latency_ms"] = 1.0
        fresh_loop.cores["feedback"]["latency_ms"] = 100.0
        bottleneck = fresh_loop.detect_loop_bottleneck()
        assert bottleneck["bottleneck_core"] == "feedback"

    def test_bottleneck_no_cores(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.cores = {}
        bottleneck = fresh_loop.detect_loop_bottleneck()
        assert bottleneck["bottleneck_core"] is None


# ---------------------------------------------------------------------------
# Status tests
# ---------------------------------------------------------------------------
class TestGetStatus:
    def test_status_structure(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        status = fresh_loop.get_status()
        assert "cycle_count" in status
        assert "health" in status
        assert "bottleneck" in status
        assert "evolution_level" in status
        assert "loop_state" in status

    def test_status_after_ticks(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        for _ in range(3):
            fresh_loop.tick_loop()
        status = fresh_loop.get_status()
        assert status["cycle_count"] == 3

    def test_evolution_levels(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        level_checks = [
            (0, "nascent"),
            (3, "nascent"),
            (6, "developing"),
            (21, "mature"),
            (51, "advanced"),
            (101, "transcendent"),
        ]
        for cycles, expected_level in level_checks:
            fresh_loop.cycle_count = cycles
            status = fresh_loop.get_status()
            assert status["evolution_level"] == expected_level, f"Failed at {cycles} cycles"


# ---------------------------------------------------------------------------
# Singleton tests
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_singleton_same_instance(self) -> None:
        a = get_penta_core_loop()
        b = get_penta_core_loop()
        assert a is b

    def test_singleton_is_penta_core_loop(self) -> None:
        instance = get_penta_core_loop()
        assert isinstance(instance, PentaCoreLoop)


# ---------------------------------------------------------------------------
# Integration / end-to-end tests
# ---------------------------------------------------------------------------
class TestIntegration:
    def test_multiple_ticks_health_evolution(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        for _ in range(10):
            result = fresh_loop.tick_loop()
            assert result["health"]["score"] > 0.0
            assert result["health"]["level"] in [
                "perfect",
                "healthy",
                "functional",
                "degraded",
                "broken",
            ]
            assert result["bottleneck"]["bottleneck_core"] in CORE_NAMES
        assert fresh_loop.cycle_count == 10

    def test_data_flows_between_cores(self, fresh_loop: PentaCoreLoop) -> None:
        fresh_loop.initialize_loop()
        result = fresh_loop.tick_loop()
        # Sense produces observations
        sense_out = result["cores"]["sense"]["output"]
        assert "observations" in sense_out
        # Decide consumes observations
        decide_out = result["cores"]["decide"]["output"]
        assert "decisions" in decide_out
        # Act consumes decisions
        act_out = result["cores"]["act"]["output"]
        assert "actions_executed" in act_out
        # Feedback consumes actions
        feedback_out = result["cores"]["feedback"]["output"]
        assert "results" in feedback_out
        # Evolve consumes results
        evolve_out = result["cores"]["evolve"]["output"]
        assert "improvements" in evolve_out
