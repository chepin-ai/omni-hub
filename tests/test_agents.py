"""
OMNI-HUB Specialized Agent Framework Tests v18
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.agents import (
    BaseAgent, ResearchAgent, CodeAgent, ReviewAgent, MetaAgent,
    create_agent, AGENT_REGISTRY, AgentState,
)
from core.tools import ToolRegistry


class TestAgentCreation:
    def test_create_research(self):
        agent = create_agent("research")
        assert isinstance(agent, ResearchAgent)
        assert agent.state.role == "research"

    def test_create_code(self):
        agent = create_agent("code")
        assert isinstance(agent, CodeAgent)
        assert agent.state.role == "code"

    def test_create_review(self):
        agent = create_agent("review")
        assert isinstance(agent, ReviewAgent)
        assert agent.state.role == "review"

    def test_create_meta(self):
        agent = create_agent("meta")
        assert isinstance(agent, MetaAgent)
        assert agent.state.role == "meta"

    def test_create_unknown_defaults(self):
        agent = create_agent("nonexistent")
        assert isinstance(agent, BaseAgent)

    def test_all_roles_in_registry(self):
        for role in ["research", "code", "review", "meta"]:
            assert role in AGENT_REGISTRY


class TestAgentExecution:
    def test_research_agent_cycle(self):
        agent = ResearchAgent()
        result = agent.run_cycle({"level": 15})
        assert "tool" in result
        assert "success" in result

    def test_code_agent_cycle(self):
        agent = CodeAgent()
        result = agent.run_cycle({"level": 15})
        assert "tool" in result
        assert "success" in result

    def test_review_agent_cycle(self):
        agent = ReviewAgent()
        result = agent.run_cycle({"level": 15})
        assert result["tool"] == "system_status"
        assert result["success"] is True

    def test_meta_agent_cycle(self):
        agent = MetaAgent()
        result = agent.run_cycle({"level": 15})
        assert "tool" in result
        assert "success" in result

    def test_task_history_accumulates(self):
        agent = ResearchAgent()
        agent.run_cycle({"level": 15})
        agent.run_cycle({"level": 15})
        assert len(agent.state.task_history) == 2

    def test_get_status(self):
        agent = ReviewAgent()
        agent.run_cycle({"level": 15})
        status = agent.get_status()
        assert status["role"] == "review"
        assert status["cycles"] == 1
        assert status["tasks"] == 1


class TestAgentState:
    def test_default_state(self):
        s = AgentState(role="test")
        assert s.energy == 1.0
        assert s.phi == 0.5
        assert s.cycle_count == 0

    def test_state_mutation(self):
        s = AgentState(role="test")
        s.energy += 1
        s.cycle_count += 1
        assert s.energy == 2.0
        assert s.cycle_count == 1
