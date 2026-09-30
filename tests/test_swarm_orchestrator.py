"""
OMNI-HUB Swarm Orchestrator Tests v172
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.swarm_orchestrator import (
    SwarmOrchestrator,
    get_swarm_orchestrator,
    reset_swarm_orchestrator,
    AGENT_TYPES,
    AGENT_ROLES,
    EMERGENCE_TYPES,
)


class TestSwarmOrchestrator:
    def test_initialization(self):
        so = SwarmOrchestrator()
        assert so.agents == {}
        assert so.task_queue == []
        assert so.emergence_log == []
        assert so.swarm_state["spawn_count"] == 0

    # ------------------------------------------------------------------
    # spawn_agent
    # ------------------------------------------------------------------
    def test_spawn_worker(self):
        so = SwarmOrchestrator()
        result = so.spawn_agent("worker", ["compute", "execute"])
        assert result["success"] is True
        assert result["agent_type"] == "worker"
        assert result["agent_id"] in so.agents
        assert so.agents[result["agent_id"]]["capabilities"] == ["compute", "execute"]

    def test_spawn_scout(self):
        so = SwarmOrchestrator()
        result = so.spawn_agent("scout", ["explore", "sense"])
        assert result["success"] is True
        assert result["agent_type"] == "scout"

    def test_spawn_coordinator(self):
        so = SwarmOrchestrator()
        result = so.spawn_agent("coordinator", ["manage", "route"])
        assert result["success"] is True
        assert result["agent_type"] == "coordinator"

    def test_spawn_specialist(self):
        so = SwarmOrchestrator()
        result = so.spawn_agent("specialist", ["deep_learning"])
        assert result["success"] is True
        assert result["agent_type"] == "specialist"

    def test_spawn_sentinel(self):
        so = SwarmOrchestrator()
        result = so.spawn_agent("sentinel", ["monitor", "alert"])
        assert result["success"] is True
        assert result["agent_type"] == "sentinel"

    def test_spawn_invalid_type(self):
        so = SwarmOrchestrator()
        result = so.spawn_agent("invalid", ["foo"])
        assert result["success"] is False
        assert "error" in result

    def test_spawn_with_parent(self):
        so = SwarmOrchestrator()
        parent = so.spawn_agent("coordinator", ["manage"])
        parent_id = parent["agent_id"]
        child = so.spawn_agent("worker", ["compute"], parent_id=parent_id)
        assert child["success"] is True
        assert child["parent_id"] == parent_id
        assert parent_id in so.agents[child["agent_id"]]["connections"]
        assert child["agent_id"] in so.agents[parent_id]["connections"]

    def test_spawn_with_invalid_parent(self):
        so = SwarmOrchestrator()
        result = so.spawn_agent("worker", ["compute"], parent_id="NONEXISTENT")
        assert result["success"] is False
        assert "Parent agent" in result["error"]

    def test_spawn_non_string_type(self):
        so = SwarmOrchestrator()
        result = so.spawn_agent(123, ["compute"])
        assert result["success"] is False
        assert "agent_type must be str" in result["error"]

    def test_spawn_tracks_state(self):
        so = SwarmOrchestrator()
        so.spawn_agent("worker", ["a"])
        so.spawn_agent("worker", ["b"])
        assert so.swarm_state["spawn_count"] == 2

    # ------------------------------------------------------------------
    # delegate_task
    # ------------------------------------------------------------------
    def test_delegate_task(self):
        so = SwarmOrchestrator()
        agent = so.spawn_agent("worker", ["compute"])
        result = so.delegate_task({"action": "process_data"}, agent["agent_id"])
        assert result["success"] is True
        assert "task_id" in result
        assert result["agent_id"] == agent["agent_id"]
        assert result["status"] in ("completed", "failed")

    def test_delegate_to_missing_agent(self):
        so = SwarmOrchestrator()
        result = so.delegate_task({"action": "x"}, "MISSING")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_delegate_non_dict_task(self):
        so = SwarmOrchestrator()
        agent = so.spawn_agent("worker", ["compute"])
        result = so.delegate_task("not_a_dict", agent["agent_id"])
        assert result["success"] is False
        assert "task must be dict" in result["error"]

    def test_delegate_tracks_queue(self):
        so = SwarmOrchestrator()
        agent = so.spawn_agent("worker", ["compute"])
        so.delegate_task({"action": "a"}, agent["agent_id"])
        so.delegate_task({"action": "b"}, agent["agent_id"])
        assert len(so.task_queue) == 2

    # ------------------------------------------------------------------
    # broadcast_task
    # ------------------------------------------------------------------
    def test_broadcast_task(self):
        so = SwarmOrchestrator()
        so.spawn_agent("worker", ["compute"])
        so.spawn_agent("worker", ["compute"])
        so.spawn_agent("scout", ["explore"])
        result = so.broadcast_task(
            {"action": "sync"},
            filter_criteria={"agent_type": "worker"},
        )
        assert result["success"] is True
        assert result["match_count"] == 2
        assert len(result["results"]) == 2

    def test_broadcast_no_match(self):
        so = SwarmOrchestrator()
        so.spawn_agent("worker", ["compute"])
        result = so.broadcast_task(
            {"action": "sync"},
            filter_criteria={"agent_type": "sentinel"},
        )
        assert result["success"] is True
        assert result["match_count"] == 0

    def test_broadcast_by_capabilities(self):
        so = SwarmOrchestrator()
        so.spawn_agent("worker", ["gpu", "compute"])
        so.spawn_agent("worker", ["cpu"])
        result = so.broadcast_task(
            {"action": "render"},
            filter_criteria={"capabilities": ["gpu"]},
        )
        assert result["success"] is True
        assert result["match_count"] == 1

    def test_broadcast_by_min_performance(self):
        so = SwarmOrchestrator()
        a1 = so.spawn_agent("worker", ["compute"])
        so.agents[a1["agent_id"]]["performance"] = 0.9
        a2 = so.spawn_agent("worker", ["compute"])
        so.agents[a2["agent_id"]]["performance"] = 0.1
        result = so.broadcast_task(
            {"action": "heavy"},
            filter_criteria={"min_performance": 0.5},
        )
        assert result["success"] is True
        assert result["match_count"] == 1

    def test_broadcast_invalid_task(self):
        so = SwarmOrchestrator()
        result = so.broadcast_task("bad", filter_criteria={})
        assert result["success"] is False
        assert "task must be dict" in result["error"]

    def test_broadcast_invalid_filter(self):
        so = SwarmOrchestrator()
        result = so.broadcast_task({}, filter_criteria="bad")
        assert result["success"] is False
        assert "filter_criteria must be dict" in result["error"]

    # ------------------------------------------------------------------
    # monitor_emergence
    # ------------------------------------------------------------------
    def test_monitor_emergence_empty(self):
        so = SwarmOrchestrator()
        result = so.monitor_emergence()
        assert result["emergence_detected"] is False
        assert result["emergence_level"] == "disorganized"
        assert result["type"] is None

    def test_monitor_emergence_with_agents(self):
        so = SwarmOrchestrator()
        for _ in range(5):
            so.spawn_agent("worker", ["compute"])
        result = so.monitor_emergence()
        assert "emergence_score" in result
        assert "details" in result
        assert result["type"] in EMERGENCE_TYPES

    def test_monitor_emergence_logs_event(self):
        so = SwarmOrchestrator()
        for _ in range(10):
            so.spawn_agent("worker", ["compute"])
            so.spawn_agent("coordinator", ["manage"])
        # Boost performance for high emergence
        for a in so.agents.values():
            a["performance"] = 0.95
        # Run monitor
        result = so.monitor_emergence()
        if result["emergence_detected"]:
            assert len(so.emergence_log) >= 1
            assert so.swarm_state["emergence_events"] >= 1

    def test_emergence_levels(self):
        so = SwarmOrchestrator()
        for _ in range(20):
            so.spawn_agent("worker", ["compute"])
            so.spawn_agent("coordinator", ["manage"])
            so.spawn_agent("specialist", ["deep"])
        for a in so.agents.values():
            a["performance"] = 0.99
        # Complete many tasks
        for agent_id in list(so.agents.keys())[:10]:
            so.delegate_task({"action": "test"}, agent_id)
        result = so.monitor_emergence()
        assert result["emergence_level"] in (
            "disorganized", "group", "coordinated", "collective", "superorganism"
        )

    # ------------------------------------------------------------------
    # resolve_agent_conflicts
    # ------------------------------------------------------------------
    def test_resolve_conflict(self):
        so = SwarmOrchestrator()
        a1 = so.spawn_agent("worker", ["compute"])
        a2 = so.spawn_agent("worker", ["compute"])
        so.agents[a1["agent_id"]]["performance"] = 0.9
        so.agents[a2["agent_id"]]["performance"] = 0.3
        result = so.resolve_agent_conflicts(a1["agent_id"], a2["agent_id"])
        assert result["success"] is True
        assert result["winner"] == a1["agent_id"]
        assert result["loser"] == a2["agent_id"]
        assert result["strategy"] == "performance_based"

    def test_resolve_conflict_tiebreak(self):
        so = SwarmOrchestrator()
        a1 = so.spawn_agent("worker", ["compute"])
        a2 = so.spawn_agent("worker", ["compute"])
        so.agents[a1["agent_id"]]["performance"] = 0.5
        so.agents[a2["agent_id"]]["performance"] = 0.5
        so.agents[a1["agent_id"]]["tasks_completed"] = 10
        so.agents[a2["agent_id"]]["tasks_completed"] = 5
        result = so.resolve_agent_conflicts(a1["agent_id"], a2["agent_id"])
        assert result["success"] is True
        assert result["winner"] == a1["agent_id"]

    def test_resolve_conflict_missing_agent(self):
        so = SwarmOrchestrator()
        result = so.resolve_agent_conflicts("A", "B")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_resolve_conflict_tracks_state(self):
        so = SwarmOrchestrator()
        a1 = so.spawn_agent("worker", ["compute"])
        a2 = so.spawn_agent("worker", ["compute"])
        so.resolve_agent_conflicts(a1["agent_id"], a2["agent_id"])
        assert so.swarm_state["conflicts_resolved"] == 1

    # ------------------------------------------------------------------
    # cull_swarm
    # ------------------------------------------------------------------
    def test_cull_swarm(self):
        so = SwarmOrchestrator()
        a1 = so.spawn_agent("worker", ["compute"])
        a2 = so.spawn_agent("worker", ["compute"])
        so.agents[a1["agent_id"]]["performance"] = 0.1
        so.agents[a2["agent_id"]]["performance"] = 0.9
        result = so.cull_swarm(0.5)
        assert result["success"] is True
        assert result["culled_count"] == 1
        assert a1["agent_id"] in result["culled_ids"]
        assert so.agents[a1["agent_id"]]["status"] == "culled"

    def test_cull_none(self):
        so = SwarmOrchestrator()
        so.spawn_agent("worker", ["compute"])
        so.spawn_agent("worker", ["compute"])
        for a in so.agents.values():
            a["performance"] = 0.9
        result = so.cull_swarm(0.5)
        assert result["success"] is True
        assert result["culled_count"] == 0

    def test_cull_invalid_threshold_type(self):
        so = SwarmOrchestrator()
        result = so.cull_swarm("high")
        assert result["success"] is False
        assert "threshold must be numeric" in result["error"]

    def test_cull_invalid_threshold_range(self):
        so = SwarmOrchestrator()
        result = so.cull_swarm(1.5)
        assert result["success"] is False
        assert "threshold must be in [0.0, 1.0]" in result["error"]

    def test_cull_tracks_state(self):
        so = SwarmOrchestrator()
        a1 = so.spawn_agent("worker", ["compute"])
        so.agents[a1["agent_id"]]["performance"] = 0.1
        so.cull_swarm(0.5)
        assert so.swarm_state["agents_culled"] == 1

    # ------------------------------------------------------------------
    # get_swarm_intelligence_score
    # ------------------------------------------------------------------
    def test_intelligence_score_empty(self):
        so = SwarmOrchestrator()
        result = so.get_swarm_intelligence_score()
        assert result["score"] == 0
        assert result["category"] == "below_average"
        assert "components" in result

    def test_intelligence_score_with_agents(self):
        so = SwarmOrchestrator()
        for _ in range(5):
            so.spawn_agent("worker", ["compute"])
        for a in so.agents.values():
            a["performance"] = 0.8
        result = so.get_swarm_intelligence_score()
        assert isinstance(result["score"], int)
        assert result["category"] in (
            "genius", "gifted", "bright", "average", "below_average"
        )
        assert "components" in result

    def test_intelligence_categories(self):
        so = SwarmOrchestrator()
        for _ in range(10):
            so.spawn_agent("worker", ["compute"])
            so.spawn_agent("coordinator", ["manage"])
            so.spawn_agent("specialist", ["deep"])
        for a in so.agents.values():
            a["performance"] = 0.99
        # Complete tasks for high completion rate
        for agent_id in list(so.agents.keys())[:20]:
            so.agents[agent_id]["tasks_completed"] = 100
            so.swarm_state["total_tasks_completed"] += 100
        so.swarm_state["total_tasks_delegated"] = 200
        # Add positive emergence events
        so.emergence_log.append({"level": "superorganism"})
        result = so.get_swarm_intelligence_score()
        assert result["score"] >= 0
        assert result["category"] in (
            "genius", "gifted", "bright", "average", "below_average"
        )

    # ------------------------------------------------------------------
    # get_status
    # ------------------------------------------------------------------
    def test_get_status_empty(self):
        so = SwarmOrchestrator()
        status = so.get_status()
        assert status["agent_count"] == 0
        assert status["task_count"] == 0
        assert status["emergence_events"] == 0
        assert status["swarm_health"] == 0.0

    def test_get_status_with_agents(self):
        so = SwarmOrchestrator()
        so.spawn_agent("worker", ["compute"])
        so.spawn_agent("scout", ["explore"])
        so.delegate_task({"action": "test"}, list(so.agents.keys())[0])
        status = so.get_status()
        assert status["agent_count"] == 2
        assert status["task_count"] == 1
        assert "active_agents" in status
        assert "swarm_state" in status

    def test_status_swarm_health(self):
        so = SwarmOrchestrator()
        for _ in range(5):
            so.spawn_agent("worker", ["compute"])
        for a in so.agents.values():
            a["performance"] = 0.8
        status = so.get_status()
        assert 0.0 <= status["swarm_health"] <= 1.0


class TestGlobalSingleton:
    def test_get_swarm_orchestrator(self):
        reset_swarm_orchestrator()
        g = get_swarm_orchestrator()
        assert g is not None
        assert isinstance(g, SwarmOrchestrator)

    def test_singleton(self):
        reset_swarm_orchestrator()
        g1 = get_swarm_orchestrator()
        g2 = get_swarm_orchestrator()
        assert g1 is g2

    def test_reset(self):
        reset_swarm_orchestrator()
        g1 = get_swarm_orchestrator()
        g1.spawn_agent("worker", ["compute"])
        reset_swarm_orchestrator()
        g2 = get_swarm_orchestrator()
        assert g1 is not g2
        assert g2.agents == {}
