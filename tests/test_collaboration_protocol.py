"""
OMNI-HUB Collaboration Protocol Tests v78
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.collaboration_protocol import (
    Agent, CollaborationTask, CollaborationProtocol, get_collaboration_protocol,
)


class TestCollaborationProtocol:
    def test_initialization(self):
        cp = CollaborationProtocol()
        assert len(cp.agents) == 5
        assert len(cp.tasks) == 0

    def test_register_agent(self):
        cp = CollaborationProtocol()
        cp.register_agent("new_agent", "specialist", 0.7)
        assert len(cp.agents) == 6

    def test_propose_task(self):
        cp = CollaborationProtocol()
        cp.propose_task("test_task", 0.5)
        assert len(cp.tasks) == 1
        assert cp.tasks[0].status == "unassigned"

    def test_negotiate_assignment(self):
        cp = CollaborationProtocol()
        cp.propose_task("heavy_task", 0.9)
        assigned = cp.negotiate_assignment()
        assert len(assigned) == 1
        assert assigned[0].assigned_to is not None

    def test_negotiate_multiple_tasks(self):
        cp = CollaborationProtocol()
        cp.propose_task("task1", 0.3)
        cp.propose_task("task2", 0.3)
        assigned = cp.negotiate_assignment()
        assert len(assigned) == 2

    def test_resolve_conflict(self):
        cp = CollaborationProtocol()
        cp.propose_task("task_a", 0.8)
        cp.propose_task("task_b", 0.5)
        winner = cp.resolve_conflict("task_a", "task_b")
        assert winner == "task_a"

    def test_coordinate_from_state(self):
        cp = CollaborationProtocol()
        state = {
            "generated_goals": ["grow", "explore"],
            "risk_analyzer": {"risks_found": 1},
            "best_opportunity": {"name": "phase_breakthrough"},
        }
        assigned = cp.coordinate_from_state(state)
        assert len(assigned) > 0

    def test_get_status(self):
        cp = CollaborationProtocol()
        cp.coordinate_from_state({"generated_goals": ["grow"], "risk_analyzer": {}, "best_opportunity": None})
        status = cp.get_status()
        assert status["agents"] == 5
        assert status["assigned"] > 0


class TestGlobalEngine:
    def test_get_collaboration_protocol(self):
        g = get_collaboration_protocol()
        assert g is not None
        assert isinstance(g, CollaborationProtocol)
