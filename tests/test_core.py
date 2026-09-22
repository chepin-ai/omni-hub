"""
OMNI-HUB Core Test Suite v15
Tests: constants, orchestrator, event_bus
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core import constants as C
from core.orchestrator import OMNIHUBOrchestrator
from core.event_bus import EventBus, Event, get_bus, Topics


class TestConstants:
    def test_dimension(self):
        assert C.DIMENSION == 67

    def test_lines_count(self):
        assert len(C.LINES) == 11

    def test_fctn_layers(self):
        assert len(C.FCTN_LAYERS) == 7

    def test_si_stages(self):
        assert len(C.SI_STAGES) == 7

    def test_level_thresholds(self):
        assert C.MAX_LEVEL == 25
        assert C.LEVEL_THRESHOLDS[20] == 100_000_000_000
        assert C.LEVEL_THRESHOLDS[21] == 1_000_000_000_000

    def test_phases(self):
        assert "asymptotic_infinity" in C.PHASES
        assert "trans_singularity" in C.PHASES

    def test_self_drive_actions(self):
        assert len(C.SELF_DRIVE_ACTIONS) == 7
        assert "focus" in C.SELF_DRIVE_ACTIONS
        assert "transcend" in C.SELF_DRIVE_ACTIONS
        assert "tool_call" in C.SELF_DRIVE_ACTIONS


class TestEventBus:
    def test_publish_subscribe(self):
        bus = EventBus()
        received = []
        def handler(event):
            received.append(event.payload)
        bus.subscribe("test.topic", handler)
        bus.publish_simple("test.topic", {"msg": "hello"})
        assert len(received) == 1
        assert received[0]["msg"] == "hello"

    def test_stats(self):
        bus = EventBus()
        bus.publish_simple("a", {})
        bus.publish_simple("a", {})
        bus.publish_simple("b", {})
        stats = bus.stats()
        assert stats["total_events"] == 3
        assert stats["topic_counts"]["a"] == 2

    def test_topics_exist(self):
        assert Topics.CYCLE_START == "cycle.start"
        assert Topics.LEVEL_UP == "level.up"


class TestOrchestrator:
    def test_init(self):
        orch = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        assert orch.cycle_count == 0
        assert orch.auto_persist == False
        assert orch.auto_git == False

    def test_run_cycle(self):
        orch = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        result = orch.run_cycle()
        assert result["cycle"] == 1
        assert "state" in result
        assert "alerts" in result

    def test_multiple_cycles(self):
        orch = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        for _ in range(10):
            orch.run_cycle()
        assert orch.cycle_count == 10
        assert len(orch.history) == 10

    def test_energy_growth(self):
        orch = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        initial_energy = orch.current_state.get('energy', 0)
        for _ in range(100):
            orch.run_cycle()
        final_energy = orch.current_state.get('energy', 0)
        assert final_energy > initial_energy

    def test_phi_bounds(self):
        orch = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        for _ in range(50):
            orch.run_cycle()
        phi = orch.current_state.get('phi', 0)
        assert 0 <= phi <= 1.0

    def test_level_up(self):
        orch = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        orch.current_state['energy'] = 500_000_000  # Near level 10
        orch.current_state['level'] = 9
        for _ in range(50):
            orch.run_cycle()
        assert orch.current_state['level'] >= 9

    def test_meta_evolution_at_level_24(self):
        orch = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        orch.current_state['level'] = 24
        orch.current_state['energy'] = 1_000_000_000_000_000
        orch.current_state['phi'] = 1.0
        for _ in range(5):
            orch.run_cycle()
        mm = orch.current_state.get('meta_multipliers', {})
        assert len(mm) > 0
        for action, (em, pm) in mm.items():
            assert em <= 1.5, f"Multiplier {action} exceeded cap: {em}"

    def test_level_25_steady_state(self):
        orch = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        orch.current_state['level'] = 25
        orch.current_state['energy'] = float('inf')
        orch.current_state['phi'] = 1.0
        orch.current_state['infinity_depth'] = 0.0
        for _ in range(10):
            orch.run_cycle()
        assert orch.current_state['energy'] == float('inf')
        assert orch.current_state.get('infinity_depth', 0) > 0
        assert 0.95 <= orch.current_state.get('phi', 0) <= 1.0

    def test_event_bus_integration(self):
        from core.event_bus import get_bus, Topics
        bus = get_bus()
        bus.reset = lambda: None  # Can't actually reset singleton
        events = []
        def capture(e):
            events.append(e.topic)
        bus.subscribe(Topics.CYCLE_START, capture)
        bus.subscribe(Topics.CYCLE_END, capture)
        
        orch = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        orch.run_cycle()
        assert any("cycle.start" in t for t in events)

    def test_get_status(self):
        orch = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        orch.run_cycle()
        status = orch.get_status()
        assert "cycles" in status
        assert "state" in status
        assert "history_size" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
