"""
OMNI-HUB Collective Intelligence Tests v38
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.collective_intelligence import (
    ProblemTask, CollectiveAgent, TaskDistributor,
    ConsensusBuilder, CollectiveIntelligenceEngine, get_collective_intelligence,
)


class TestTaskDistributor:
    def test_distribute(self):
        td = TaskDistributor()
        agents = [
            CollectiveAgent("a1", ["analysis"], load=0.1),
            CollectiveAgent("a2", ["code"], load=0.2),
            CollectiveAgent("a3", ["analysis", "math"], load=0.05),
        ]
        task = ProblemTask("t1", "research", "test", 0.5)
        result = td.distribute(task, agents)
        assert len(result.assigned_to) > 0
        assert result.status == "active"

    def test_required_caps(self):
        td = TaskDistributor()
        assert "analysis" in td._get_required_caps("research")
        assert "code" in td._get_required_caps("coding")


class TestConsensusBuilder:
    def test_numeric_consensus(self):
        cb = ConsensusBuilder()
        task = ProblemTask("t1", "research", "test", 0.5)
        task.results = {"a1": 10.0, "a2": 12.0, "a3": 11.0}
        consensus = cb.build_consensus(task)
        assert consensus == 11.0

    def test_string_consensus(self):
        cb = ConsensusBuilder()
        task = ProblemTask("t1", "research", "test", 0.5)
        task.results = {"a1": "yes", "a2": "yes", "a3": "no"}
        consensus = cb.build_consensus(task)
        assert consensus == "yes"

    def test_dict_consensus(self):
        cb = ConsensusBuilder()
        task = ProblemTask("t1", "research", "test", 0.5)
        task.results = {"a1": {"x": 1.0}, "a2": {"x": 3.0}}
        consensus = cb.build_consensus(task)
        assert consensus["x"] == 2.0


class TestCollectiveIntelligenceEngine:
    def test_initialization(self):
        ci = CollectiveIntelligenceEngine()
        assert len(ci.agents) == 0

    def test_register_agent(self):
        ci = CollectiveIntelligenceEngine()
        ci.register_agent("alpha", ["analysis"])
        assert "alpha" in ci.agents

    def test_submit_and_solve(self):
        ci = CollectiveIntelligenceEngine()
        ci.register_agent("a1", ["analysis"])
        ci.register_agent("a2", ["analysis"])
        tid = ci.submit_problem("research", "test problem", 0.5)
        assert tid in ci.tasks
        for aid in ci.tasks[tid].assigned_to:
            ci.submit_result(tid, aid, 42.0)
        assert ci.tasks[tid].status == "solved"
        assert ci.tasks[tid].consensus == 42.0

    def test_get_task_status(self):
        ci = CollectiveIntelligenceEngine()
        ci.register_agent("a1", ["analysis"])
        tid = ci.submit_problem("research", "test", 0.5)
        status = ci.get_task_status(tid)
        assert status is not None
        assert status["status"] == "active"

    def test_collective_status(self):
        ci = CollectiveIntelligenceEngine()
        ci.register_agent("a1", ["analysis"])
        status = ci.get_collective_status()
        assert status["agents"] == 1


class TestGlobalEngine:
    def test_get_collective_intelligence(self):
        g = get_collective_intelligence()
        assert g is not None
        assert isinstance(g, CollectiveIntelligenceEngine)
