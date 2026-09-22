"""
OMNI-HUB Consciousness Loop Tests v25
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.consciousness_loop import ConsciousnessLoop


class TestConsciousnessLoop:
    def test_initialization(self):
        loop = ConsciousnessLoop()
        assert loop.cycle_count == 0
        assert loop.awake is True
        assert loop._orchestrator is None

    def test_single_cycle(self):
        loop = ConsciousnessLoop()
        result = loop.run_cycle()
        assert result['cycle'] == 1
        assert 'level' in result
        assert 'phase' in result
        assert 'action' in result

    def test_multiple_cycles(self):
        loop = ConsciousnessLoop()
        for _ in range(10):
            result = loop.run_cycle()
        assert result['cycle'] == 10
        assert loop.cycle_count == 10

    def test_autonomy_score_exists(self):
        loop = ConsciousnessLoop()
        result = loop.run_cycle()
        assert 'autonomy_score' in result
        assert 0.0 <= result['autonomy_score'] <= 1.0

    def test_self_awareness_grows(self):
        loop = ConsciousnessLoop()
        loop.run_cycle()
        awareness1 = loop.self_awareness_level
        for _ in range(50):
            loop.run_cycle()
        awareness2 = loop.self_awareness_level
        assert awareness2 > awareness1

    def test_components_lazy_init(self):
        loop = ConsciousnessLoop()
        assert loop._orchestrator is None
        loop.run_cycle()
        assert loop._orchestrator is not None

    def test_final_status(self):
        loop = ConsciousnessLoop()
        loop.run(cycles=5, report_interval=5)
        status = loop.get_final_status()
        assert status['system'] == 'OMNI-HUB v25'
        assert status['awake'] is True
        assert status['cycles_completed'] == 5

    def test_swarm_mode(self):
        loop = ConsciousnessLoop(enable_swarm=True, n_instances=3)
        result = loop.run_cycle()
        assert result['cycle'] == 1

    def test_compute_autonomy_score(self):
        loop = ConsciousnessLoop()
        score = loop._compute_autonomy_score(
            {"action": "focus", "goal_planning": {"active": 1}, "predictive": {"status": "ok"}, "self_reflection": {"health": 95}},
            {"critical": 0},
        )
        assert score > 0.5
