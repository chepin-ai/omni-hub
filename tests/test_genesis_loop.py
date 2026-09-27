"""
Tests for Genesis Loop (创世循环) — OMNI-HUB v140
"""

import time
import pytest
from typing import Dict, Any

from core.genesis_loop import GenesisLoop, get_genesis_loop


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton before every test."""
    import core.genesis_loop as gl
    gl._module = None
    yield
    gl._module = None


@pytest.fixture
def fresh_loop() -> GenesisLoop:
    """Return a fresh GenesisLoop instance (not the singleton)."""
    return GenesisLoop()


@pytest.fixture
def healthy_state() -> Dict[str, Any]:
    return {
        "modules": {
            "alpha": {"health": 0.9, "coherence": 0.95},
            "beta":  {"health": 0.8, "coherence": 0.85},
            "gamma": {"health": 0.7, "coherence": 0.75},
        },
        "critical_modules": ["alpha", "beta", "gamma"],
    }


@pytest.fixture
def degraded_state() -> Dict[str, Any]:
    return {
        "modules": {
            "alpha": {"health": 0.9, "coherence": 0.95},
            "beta":  {"health": 0.8, "coherence": 0.20},
            "gamma": {"health": 0.7, "coherence": 0.75},
        },
        "critical_modules": ["alpha", "beta", "gamma"],
    }


# ---------------------------------------------------------------------------
# Construction & defaults
# ---------------------------------------------------------------------------
class TestConstruction:
    def test_default_state(self, fresh_loop: GenesisLoop) -> None:
        assert fresh_loop.initialized is False
        assert fresh_loop.running is False
        assert fresh_loop.cycle_count == 0
        assert fresh_loop.boot_time is None

    def test_get_status_before_boot(self, fresh_loop: GenesisLoop) -> None:
        status = fresh_loop.get_status()
        assert status["running"] is False
        assert status["cycle_count"] == 0
        assert status["uptime"] is None
        assert status["next_evolution"] == "none"


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_singleton_identity(self) -> None:
        a = get_genesis_loop()
        b = get_genesis_loop()
        assert a is b

    def test_singleton_is_genesis_loop(self) -> None:
        assert isinstance(get_genesis_loop(), GenesisLoop)


# ---------------------------------------------------------------------------
# Boot sequence
# ---------------------------------------------------------------------------
class TestBoot:
    def test_boot_sets_initialized(self, fresh_loop, healthy_state) -> None:
        result = fresh_loop.boot(healthy_state)
        assert result["success"] is True
        assert fresh_loop.initialized is True

    def test_boot_sets_running(self, fresh_loop, healthy_state) -> None:
        fresh_loop.boot(healthy_state)
        assert fresh_loop.running is True

    def test_boot_sets_boot_time(self, fresh_loop, healthy_state) -> None:
        before = time.time()
        fresh_loop.boot(healthy_state)
        after = time.time()
        assert fresh_loop.boot_time is not None
        assert before <= fresh_loop.boot_time <= after

    def test_boot_resets_cycle_count(self, fresh_loop, healthy_state) -> None:
        fresh_loop.cycle_count = 42
        fresh_loop.boot(healthy_state)
        assert fresh_loop.cycle_count == 0

    def test_boot_returns_modules_present(self, fresh_loop, healthy_state) -> None:
        result = fresh_loop.boot(healthy_state)
        assert "alpha" in result["modules_present"]
        assert "beta" in result["modules_present"]
        assert "gamma" in result["modules_present"]

    def test_boot_missing_module_fails(self, fresh_loop) -> None:
        state = {
            "modules": {"alpha": {"health": 1.0}},
            "critical_modules": ["alpha", "missing"],
        }
        result = fresh_loop.boot(state)
        assert result["success"] is False
        assert fresh_loop.initialized is False
        assert fresh_loop.running is False

    def test_boot_empty_critical_list_succeeds(self, fresh_loop) -> None:
        state = {"modules": {"alpha": 1.0}, "critical_modules": []}
        result = fresh_loop.boot(state)
        assert result["success"] is True

    def test_boot_no_modules_succeeds_when_critical_empty(self, fresh_loop) -> None:
        result = fresh_loop.boot({})
        assert result["success"] is True

    def test_boot_records_evolution(self, fresh_loop, degraded_state) -> None:
        fresh_loop.boot(degraded_state)
        assert fresh_loop._next_evolution == "coherence_beta"


# ---------------------------------------------------------------------------
# Tick
# ---------------------------------------------------------------------------
class TestTick:
    def test_tick_increments_cycle_count(self, fresh_loop, healthy_state) -> None:
        fresh_loop.boot(healthy_state)
        fresh_loop.tick(healthy_state)
        assert fresh_loop.cycle_count == 1

    def test_tick_multiple_times(self, fresh_loop, healthy_state) -> None:
        fresh_loop.boot(healthy_state)
        for _ in range(5):
            fresh_loop.tick(healthy_state)
        assert fresh_loop.cycle_count == 5

    def test_tick_returns_health(self, fresh_loop, healthy_state) -> None:
        fresh_loop.boot(healthy_state)
        result = fresh_loop.tick(healthy_state)
        assert "health" in result
        assert 0.0 <= result["health"] <= 1.0

    def test_tick_returns_suggestion(self, fresh_loop, healthy_state) -> None:
        fresh_loop.boot(healthy_state)
        result = fresh_loop.tick(healthy_state)
        assert "suggestion" in result
        assert result["suggestion"].startswith("strengthen_")

    def test_tick_without_boot(self, fresh_loop, healthy_state) -> None:
        result = fresh_loop.tick(healthy_state)
        assert result["suggestion"] == "boot_required"
        assert "error" in result

    def test_tick_with_degraded_state(self, fresh_loop, degraded_state) -> None:
        fresh_loop.boot(degraded_state)
        result = fresh_loop.tick(degraded_state)
        assert result["suggestion"] == "coherence_beta"

    def test_tick_health_calculation(self, fresh_loop) -> None:
        state = {
            "modules": {
                "a": {"health": 1.0, "coherence": 1.0},
                "b": {"health": 0.0, "coherence": 0.0},
            },
            "critical_modules": ["a", "b"],
        }
        fresh_loop.boot(state)
        result = fresh_loop.tick(state)
        assert result["health"] == 0.5


# ---------------------------------------------------------------------------
# Evolve
# ---------------------------------------------------------------------------
class TestEvolve:
    def test_evolve_identifies_weakest_module(self, fresh_loop, degraded_state) -> None:
        fresh_loop.boot(degraded_state)
        result = fresh_loop.evolve(degraded_state)
        assert result["target_module"] == "beta"
        assert result["action"] == "coherence_beta"
        assert result["priority"] == "high"

    def test_evolve_normal_priority(self, fresh_loop, healthy_state) -> None:
        fresh_loop.boot(healthy_state)
        result = fresh_loop.evolve(healthy_state)
        assert result["priority"] == "normal"

    def test_evolve_no_modules(self, fresh_loop) -> None:
        result = fresh_loop.evolve({})
        assert result["target_module"] == "system_expansion"
        assert result["action"] == "system_expansion"

    def test_evolve_updates_next_evolution(self, fresh_loop, degraded_state) -> None:
        fresh_loop.boot(degraded_state)
        fresh_loop.evolve(degraded_state)
        assert fresh_loop._next_evolution == "coherence_beta"


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------
class TestGetStatus:
    def test_status_after_boot(self, fresh_loop, healthy_state) -> None:
        fresh_loop.boot(healthy_state)
        time.sleep(0.01)
        status = fresh_loop.get_status()
        assert status["running"] is True
        assert status["cycle_count"] == 0
        assert status["uptime"] is not None
        assert status["uptime"] >= 0.01
        assert status["next_evolution"] != "none"

    def test_status_after_ticks(self, fresh_loop, healthy_state) -> None:
        fresh_loop.boot(healthy_state)
        fresh_loop.tick(healthy_state)
        fresh_loop.tick(healthy_state)
        status = fresh_loop.get_status()
        assert status["cycle_count"] == 2
        assert status["running"] is True


# ---------------------------------------------------------------------------
# Health assessment
# ---------------------------------------------------------------------------
class TestHealthAssessment:
    def test_all_healthy(self, fresh_loop) -> None:
        state = {
            "modules": {"a": 1.0, "b": 1.0, "c": 1.0},
            "critical_modules": ["a", "b", "c"],
        }
        fresh_loop.boot(state)
        result = fresh_loop.tick(state)
        assert result["health"] == 1.0

    def test_all_dead(self, fresh_loop) -> None:
        state = {
            "modules": {"a": 0.0, "b": 0.0},
            "critical_modules": ["a", "b"],
        }
        fresh_loop.boot(state)
        result = fresh_loop.tick(state)
        assert result["health"] == 0.0

    def test_empty_modules(self, fresh_loop) -> None:
        fresh_loop.boot({})
        result = fresh_loop.tick({})
        assert result["health"] == 0.0


# ---------------------------------------------------------------------------
# Evolution suggestion edge cases
# ---------------------------------------------------------------------------
class TestEvolutionEdgeCases:
    def test_numeric_module_scores(self, fresh_loop) -> None:
        state = {
            "modules": {"x": 0.1, "y": 0.9},
            "critical_modules": ["x", "y"],
        }
        fresh_loop.boot(state)
        result = fresh_loop.evolve(state)
        assert result["target_module"] == "x"

    def test_coherence_trumps_health(self, fresh_loop) -> None:
        state = {
            "modules": {
                "strong": {"health": 0.1, "coherence": 1.0},
                "weak":   {"health": 1.0, "coherence": 0.1},
            },
            "critical_modules": ["strong", "weak"],
        }
        fresh_loop.boot(state)
        result = fresh_loop.evolve(state)
        assert result["target_module"] == "weak"

    def test_threshold_for_coherence_action(self, fresh_loop) -> None:
        state = {
            "modules": {
                "mod": {"health": 0.5, "coherence": 0.29},
            },
            "critical_modules": ["mod"],
        }
        fresh_loop.boot(state)
        result = fresh_loop.evolve(state)
        assert result["action"] == "coherence_mod"

    def test_threshold_for_strengthen_action(self, fresh_loop) -> None:
        state = {
            "modules": {
                "mod": {"health": 0.5, "coherence": 0.31},
            },
            "critical_modules": ["mod"],
        }
        fresh_loop.boot(state)
        result = fresh_loop.evolve(state)
        assert result["action"] == "strengthen_mod"


# ---------------------------------------------------------------------------
# Error resilience
# ---------------------------------------------------------------------------
class TestErrorResilience:
    def test_boot_with_bad_state_type(self, fresh_loop) -> None:
        result = fresh_loop.boot(None)  # type: ignore
        assert result["success"] is False
        assert "error" in result

    def test_tick_with_bad_state_type(self, fresh_loop, healthy_state) -> None:
        fresh_loop.boot(healthy_state)
        result = fresh_loop.tick(None)  # type: ignore
        assert "error" in result

    def test_evolve_with_bad_state_type(self, fresh_loop) -> None:
        result = fresh_loop.evolve(None)  # type: ignore
        assert "error" in result
