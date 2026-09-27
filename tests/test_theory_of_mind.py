"""
OMNI-HUB Theory of Mind Tests v90
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.theory_of_mind import (
    AgentModel, TheoryOfMind, get_theory_of_mind,
)


class TestTheoryOfMind:
    def test_initialization(self):
        tom = TheoryOfMind()
        assert len(tom.models) == 0

    def test_observe_interaction(self):
        tom = TheoryOfMind()
        tom.observe_interaction("agent1", "help_request", {}, 10)
        assert "agent1" in tom.models
        assert tom.models["agent1"].inferred_intent == "cooperative"

    def test_observe_competitive(self):
        tom = TheoryOfMind()
        tom.observe_interaction("agent1", "compete_action", {}, 10)
        assert tom.models["agent1"].inferred_intent == "competitive"

    def test_infer_goals(self):
        tom = TheoryOfMind()
        tom.observe_interaction("agent1", "test", {"phase": "near_critical"}, 10)
        goals = tom.infer_goals("agent1", {"phase": "near_critical", "level": 15})
        assert len(goals) > 0

    def test_perspective_take(self):
        tom = TheoryOfMind()
        tom.observe_interaction("agent1", "help", {}, 10)
        p = tom.perspective_take("agent1", {})
        assert p["agent_id"] == "agent1"
        assert "cooperative" in p["perspective_summary"]

    def test_build_from_peers(self):
        tom = TheoryOfMind()
        state = {"peers": [{"id": "p1", "status": "active"}, {"id": "p2", "status": "idle"}]}
        tom.build_from_peers(state, cycle=10)
        assert len(tom.models) == 2

    def test_get_status(self):
        tom = TheoryOfMind()
        tom.observe_interaction("a1", "test", {}, 10)
        status = tom.get_status()
        assert status["models"] == 1
        assert status["interactions"] == 1


class TestGlobalEngine:
    def test_get_theory_of_mind(self):
        g = get_theory_of_mind()
        assert g is not None
        assert isinstance(g, TheoryOfMind)
