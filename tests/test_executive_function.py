"""
OMNI-HUB Executive Function Tests v70
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.executive_function import (
    Task, ExecutiveFunction, get_executive_function,
)


class TestExecutiveFunction:
    def test_initialization(self):
        ef = ExecutiveFunction()
        assert len(ef.tasks) == 0
        assert ef.active_task is None

    def test_add_task(self):
        ef = ExecutiveFunction()
        ef.add_task("test_task", 0.8, 100)
        assert len(ef.tasks) == 1
        assert ef.tasks[0].name == "test_task"

    def test_prioritize(self):
        ef = ExecutiveFunction()
        ef.add_task("low", 0.3, 100)
        ef.add_task("high", 0.9, 50)
        ef.add_task("mid", 0.6, 100)
        best = ef.prioritize()
        assert best.name == "high"

    def test_switch_task(self):
        ef = ExecutiveFunction()
        ef.add_task("task1", 0.8, 100)
        ef.switch_task(cycle=10)
        assert ef.active_task is not None
        assert ef.active_task.name == "task1"
        assert ef.switch_count == 0

        ef.add_task("task2", 0.9, 100)
        ef.switch_task(cycle=20)
        assert ef.active_task.name == "task2"
        assert ef.switch_count == 1

    def test_inhibit(self):
        ef = ExecutiveFunction()
        ef.inhibit("bad_impulse")
        assert len(ef.inhibitions) == 1

    def test_evaluate_impulse_low_energy(self):
        ef = ExecutiveFunction()
        state = {"energy": 30.0, "phase": "pre_emergence"}
        result = ef.evaluate_impulse("focus", state)
        assert result is False
        assert len(ef.inhibitions) == 1

    def test_evaluate_impulse_allowed(self):
        ef = ExecutiveFunction()
        state = {"energy": 1000.0, "phase": "pre_emergence"}
        result = ef.evaluate_impulse("focus", state)
        assert result is True

    def test_derive_tasks_from_state(self):
        ef = ExecutiveFunction()
        state = {"energy": 50.0, "level": 3, "active_lines": 8, "phase": "pre_emergence"}
        ef.derive_tasks_from_state(state, cycle=10)
        assert len(ef.tasks) > 0
        task_names = [t.name for t in ef.tasks]
        assert "restore_energy" in task_names

    def test_get_status(self):
        ef = ExecutiveFunction()
        ef.add_task("task1", 0.8, 100)
        ef.switch_task(cycle=10)
        status = ef.get_status()
        assert status["tasks"] == 1
        assert status["active"] == "task1"


class TestGlobalEngine:
    def test_get_executive_function(self):
        g = get_executive_function()
        assert g is not None
        assert isinstance(g, ExecutiveFunction)
