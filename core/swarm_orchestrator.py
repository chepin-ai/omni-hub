"""
OMNI-HUB Swarm Orchestrator v172
集群编排器 — Swarm Commander for thousands of sub-agents.

Research Basis:
- OpenAI's 10,000-agent swarm solving Navier-Stokes (Sept 2026)
- Google's A2A protocol v1.0 (April 2026)
- OpenClaw persistent runtime

Key insight: massive swarms can solve the unsolvable, but need
orchestration, emergence monitoring, and sandboxing.

This is the leap from "single brain" to "swarm mind".
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import time
import random
import uuid
from typing import Dict, List, Any, Optional

# Valid agent types
AGENT_TYPES = {"worker", "scout", "coordinator", "specialist", "sentinel"}

# Agent role descriptions
AGENT_ROLES = {
    "worker": "executes tasks",
    "scout": "explores new opportunities",
    "coordinator": "manages other agents",
    "specialist": "deep expertise in one area",
    "sentinel": "monitors for anomalies",
}

# Emergence behavior types
EMERGENCE_TYPES = [
    "self_organization",
    "task_specialization",
    "load_balancing",
    "consensus_formation",
    "anomaly_coordination",
]

# Emergence level thresholds
EMERGENCE_LEVELS = [
    (0.9, "superorganism"),
    (0.7, "collective"),
    (0.5, "coordinated"),
    (0.3, "group"),
]

# Swarm intelligence thresholds
INTELLIGENCE_LEVELS = [
    (150, "genius"),
    (120, "gifted"),
    (100, "bright"),
    (80, "average"),
]


def _generate_agent_id() -> str:
    """Generate a unique agent identifier."""
    return f"AGENT-{uuid.uuid4().hex[:8].upper()}"


class SwarmOrchestrator:
    """
    Orchestrates a swarm of heterogeneous agents.

    Manages agent lifecycle, task delegation, broadcast communication,
    emergence detection, conflict resolution, and swarm health.
    """

    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.task_queue: List[Dict[str, Any]] = []
        self.emergence_log: List[Dict[str, Any]] = []
        self.swarm_state: Dict[str, Any] = {
            "total_tasks_delegated": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "conflicts_resolved": 0,
            "agents_culled": 0,
            "spawn_count": 0,
            "emergence_events": 0,
            "connectivity_edges": 0,
        }
        self._emergence_counter = 0

    def spawn_agent(
        self,
        agent_type: str,
        capabilities: List[str],
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Spawn a new agent into the swarm."""
        if not isinstance(agent_type, str):
            return {
                "success": False,
                "error": f"agent_type must be str, got {type(agent_type).__name__}",
            }

        agent_type = agent_type.lower()
        if agent_type not in AGENT_TYPES:
            return {
                "success": False,
                "error": f"Invalid agent_type '{agent_type}'. Valid: {sorted(AGENT_TYPES)}",
            }

        if parent_id is not None and parent_id not in self.agents:
            return {
                "success": False,
                "error": f"Parent agent '{parent_id}' not found",
            }

        agent_id = _generate_agent_id()
        agent = {
            "id": agent_id,
            "type": agent_type,
            "capabilities": list(capabilities) if capabilities else [],
            "parent_id": parent_id,
            "created_at": time.time(),
            "performance": 0.5,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "status": "active",
            "connections": [],
        }

        # Inherit some connections from parent if specified
        if parent_id is not None:
            parent = self.agents[parent_id]
            agent["connections"] = [parent_id] + parent.get("connections", [])[:3]
            parent.setdefault("connections", []).append(agent_id)
            self.swarm_state["connectivity_edges"] += 2
        else:
            # Connect to a few random existing agents for density
            existing = list(self.agents.keys())
            if existing:
                peers = random.sample(existing, min(3, len(existing)))
                agent["connections"] = peers
                for peer_id in peers:
                    self.agents[peer_id].setdefault("connections", []).append(agent_id)
                self.swarm_state["connectivity_edges"] += len(peers) * 2

        self.agents[agent_id] = agent
        self.swarm_state["spawn_count"] += 1

        try:
            from core.event_bus import get_bus, Topics
            bus = get_bus()
            bus.publish_simple(
                Topics.STATE_CHANGE,
                {
                    "source": "swarm_orchestrator",
                    "event": "agent_spawned",
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "parent_id": parent_id,
                },
            )
        except Exception:
            pass

        return {
            "success": True,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "parent_id": parent_id,
            "capabilities": agent["capabilities"],
        }

    def delegate_task(self, task: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Delegate a task to a specific agent."""
        if not isinstance(task, dict):
            return {
                "success": False,
                "error": f"task must be dict, got {type(task).__name__}",
            }
        if not isinstance(agent_id, str):
            return {
                "success": False,
                "error": f"agent_id must be str, got {type(agent_id).__name__}",
            }

        if agent_id not in self.agents:
            return {
                "success": False,
                "error": f"Agent '{agent_id}' not found",
            }

        agent = self.agents[agent_id]
        if agent.get("status") != "active":
            return {
                "success": False,
                "error": f"Agent '{agent_id}' is {agent.get('status')}",
            }

        task_entry = {
            "task_id": f"TASK-{uuid.uuid4().hex[:8].upper()}",
            "agent_id": agent_id,
            "payload": task,
            "delegated_at": time.time(),
            "status": "delegated",
        }
        self.task_queue.append(task_entry)
        self.swarm_state["total_tasks_delegated"] += 1

        # Simulate execution outcome based on agent performance
        success_probability = agent.get("performance", 0.5)
        if random.random() < success_probability:
            agent["tasks_completed"] += 1
            agent["performance"] = min(1.0, agent["performance"] + 0.02)
            task_entry["status"] = "completed"
            self.swarm_state["total_tasks_completed"] += 1
            result_status = "completed"
        else:
            agent["tasks_failed"] += 1
            agent["performance"] = max(0.0, agent["performance"] - 0.03)
            task_entry["status"] = "failed"
            self.swarm_state["total_tasks_failed"] += 1
            result_status = "failed"

        try:
            from core.event_bus import get_bus, Topics
            bus = get_bus()
            bus.publish_simple(
                Topics.ACTION_SELECTED,
                {
                    "source": "swarm_orchestrator",
                    "event": "task_delegated",
                    "task_id": task_entry["task_id"],
                    "agent_id": agent_id,
                    "result": result_status,
                },
            )
        except Exception:
            pass

        return {
            "success": True,
            "task_id": task_entry["task_id"],
            "agent_id": agent_id,
            "status": result_status,
            "agent_performance": round(agent["performance"], 4),
        }

    def broadcast_task(
        self,
        task: Dict[str, Any],
        filter_criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Broadcast a task to multiple matching agents."""
        if not isinstance(task, dict):
            return {
                "success": False,
                "error": f"task must be dict, got {type(task).__name__}",
            }
        if not isinstance(filter_criteria, dict):
            return {
                "success": False,
                "error": f"filter_criteria must be dict, got {type(filter_criteria).__name__}",
            }

        matched = []
        required_type = filter_criteria.get("agent_type")
        required_capabilities = filter_criteria.get("capabilities", [])
        min_performance = filter_criteria.get("min_performance", 0.0)

        for agent_id, agent in self.agents.items():
            if agent.get("status") != "active":
                continue
            if required_type and agent.get("type") != required_type:
                continue
            if agent.get("performance", 0.0) < min_performance:
                continue
            if required_capabilities:
                caps = set(agent.get("capabilities", []))
                if not all(c in caps for c in required_capabilities):
                    continue
            matched.append(agent_id)

        results = []
        for agent_id in matched:
            result = self.delegate_task(task, agent_id)
            results.append(result)

        return {
            "success": True,
            "matched_agents": matched,
            "match_count": len(matched),
            "results": results,
        }

    def monitor_emergence(self) -> Dict[str, Any]:
        """Monitor for emergent swarm behaviors."""
        if not self.agents:
            return {
                "emergence_detected": False,
                "emergence_level": "disorganized",
                "emergence_score": 0.0,
                "type": None,
                "details": "No agents in swarm",
            }

        # Compute emergence score from swarm properties
        avg_perf = self._avg_agent_performance()
        connectivity = self._connectivity_density()
        completion_rate = self._task_completion_rate()
        type_balance = self._type_diversity_score()

        # Emergence score: higher when agents are diverse, connected, and performing
        emergence_score = min(1.0, (avg_perf * 0.3 + connectivity * 0.25 +
                              completion_rate * 0.25 + type_balance * 0.2))

        # Determine level
        level = "disorganized"
        for threshold, label in EMERGENCE_LEVELS:
            if emergence_score > threshold:
                level = label
                break

        # Pick emergence type based on swarm state
        dominant_type = self._dominant_emergence_type()

        # Log emergence event if above group threshold
        if emergence_score > 0.3:
            self._emergence_counter += 1
            eid = f"EMRG-SWARM-{self._emergence_counter:04d}"
            event = {
                "id": eid,
                "timestamp": time.time(),
                "level": level,
                "score": round(emergence_score, 4),
                "type": dominant_type,
                "agent_count": len(self.agents),
            }
            self.emergence_log.append(event)
            self.swarm_state["emergence_events"] += 1

            try:
                from core.event_bus import get_bus, Topics
                bus = get_bus()
                bus.publish_simple(
                    Topics.STATE_CHANGE,
                    {
                        "source": "swarm_orchestrator",
                        "event": "emergence_detected",
                        "emergence_id": eid,
                        "level": level,
                        "score": emergence_score,
                        "type": dominant_type,
                    },
                )
            except Exception:
                pass

        return {
            "emergence_detected": emergence_score > 0.3,
            "emergence_level": level,
            "emergence_score": round(emergence_score, 4),
            "type": dominant_type,
            "details": {
                "avg_performance": round(avg_perf, 4),
                "connectivity_density": round(connectivity, 4),
                "task_completion_rate": round(completion_rate, 4),
                "type_diversity": round(type_balance, 4),
            },
        }

    def _avg_agent_performance(self) -> float:
        """Compute average agent performance."""
        if not self.agents:
            return 0.0
        return sum(a.get("performance", 0.0) for a in self.agents.values()) / len(self.agents)

    def _connectivity_density(self) -> float:
        """Compute graph connectivity density (0-1)."""
        n = len(self.agents)
        if n <= 1:
            return 0.0
        max_edges = n * (n - 1)
        actual_edges = self.swarm_state.get("connectivity_edges", 0)
        return min(1.0, actual_edges / max_edges) if max_edges > 0 else 0.0

    def _task_completion_rate(self) -> float:
        """Compute task completion rate."""
        total = self.swarm_state.get("total_tasks_delegated", 0)
        completed = self.swarm_state.get("total_tasks_completed", 0)
        if total == 0:
            return 0.5  # neutral when no tasks
        return completed / total

    def _type_diversity_score(self) -> float:
        """Compute type diversity score (0-1)."""
        if not self.agents:
            return 0.0
        types_present = set(a.get("type") for a in self.agents.values())
        return len(types_present) / len(AGENT_TYPES)

    def _dominant_emergence_type(self) -> str:
        """Determine the dominant emergence type based on swarm composition."""
        type_counts = {}
        for a in self.agents.values():
            t = a.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        n = len(self.agents)
        if n == 0:
            return "self_organization"

        coordinator_ratio = type_counts.get("coordinator", 0) / n
        worker_ratio = type_counts.get("worker", 0) / n
        sentinel_ratio = type_counts.get("sentinel", 0) / n
        specialist_ratio = type_counts.get("specialist", 0) / n

        if coordinator_ratio > 0.3 and worker_ratio > 0.3:
            return "self_organization"
        elif specialist_ratio > 0.3:
            return "task_specialization"
        elif worker_ratio > 0.5:
            return "load_balancing"
        elif coordinator_ratio > 0.2:
            return "consensus_formation"
        elif sentinel_ratio > 0.15:
            return "anomaly_coordination"
        return "self_organization"

    def resolve_agent_conflicts(self, agent_a: str, agent_b: str) -> Dict[str, Any]:
        """Resolve conflicts between two agents."""
        if not isinstance(agent_a, str) or not isinstance(agent_b, str):
            return {
                "success": False,
                "error": "agent_a and agent_b must be strings",
            }

        if agent_a not in self.agents:
            return {
                "success": False,
                "error": f"Agent '{agent_a}' not found",
            }
        if agent_b not in self.agents:
            return {
                "success": False,
                "error": f"Agent '{agent_b}' not found",
            }

        a = self.agents[agent_a]
        b = self.agents[agent_b]

        # Conflict resolution strategy: higher performance wins
        perf_a = a.get("performance", 0.5)
        perf_b = b.get("performance", 0.5)

        if perf_a > perf_b:
            winner, loser = agent_a, agent_b
            winner_perf, loser_perf = perf_a, perf_b
        elif perf_b > perf_a:
            winner, loser = agent_b, agent_a
            winner_perf, loser_perf = perf_b, perf_a
        else:
            # Tie-break by tasks completed
            tasks_a = a.get("tasks_completed", 0)
            tasks_b = b.get("tasks_completed", 0)
            if tasks_a >= tasks_b:
                winner, loser = agent_a, agent_b
                winner_perf, loser_perf = perf_a, perf_b
            else:
                winner, loser = agent_b, agent_a
                winner_perf, loser_perf = perf_b, perf_a

        # Winner gets a small boost, loser gets a small penalty
        self.agents[winner]["performance"] = min(1.0, winner_perf + 0.05)
        self.agents[loser]["performance"] = max(0.0, loser_perf - 0.02)
        self.swarm_state["conflicts_resolved"] += 1

        # Remove connection between them if exists
        if loser in self.agents[winner].get("connections", []):
            self.agents[winner]["connections"].remove(loser)
        if winner in self.agents[loser].get("connections", []):
            self.agents[loser]["connections"].remove(winner)

        try:
            from core.event_bus import get_bus, Topics
            bus = get_bus()
            bus.publish_simple(
                Topics.ALERT,
                {
                    "source": "swarm_orchestrator",
                    "event": "conflict_resolved",
                    "winner": winner,
                    "loser": loser,
                    "strategy": "performance_based",
                },
            )
        except Exception:
            pass

        return {
            "success": True,
            "winner": winner,
            "loser": loser,
            "strategy": "performance_based",
            "winner_performance": round(self.agents[winner]["performance"], 4),
            "loser_performance": round(self.agents[loser]["performance"], 4),
        }

    def cull_swarm(self, threshold: float) -> Dict[str, Any]:
        """Remove underperforming agents below the threshold."""
        if not isinstance(threshold, (int, float)):
            return {
                "success": False,
                "error": f"threshold must be numeric, got {type(threshold).__name__}",
            }

        if not 0.0 <= threshold <= 1.0:
            return {
                "success": False,
                "error": f"threshold must be in [0.0, 1.0], got {threshold}",
            }

        culled = []
        for agent_id in list(self.agents.keys()):
            agent = self.agents[agent_id]
            if agent.get("performance", 0.0) < threshold:
                agent["status"] = "culled"
                culled.append(agent_id)
                self.swarm_state["agents_culled"] += 1

                # Remove connections to culled agent
                for other in self.agents.values():
                    if agent_id in other.get("connections", []):
                        other["connections"].remove(agent_id)
                        self.swarm_state["connectivity_edges"] = max(
                            0, self.swarm_state.get("connectivity_edges", 0) - 1
                        )

        try:
            from core.event_bus import get_bus, Topics
            bus = get_bus()
            bus.publish_simple(
                Topics.ALERT,
                {
                    "source": "swarm_orchestrator",
                    "event": "swarm_culled",
                    "culled_count": len(culled),
                    "threshold": threshold,
                    "culled_ids": culled,
                },
            )
        except Exception:
            pass

        return {
            "success": True,
            "culled_count": len(culled),
            "culled_ids": culled,
            "threshold": threshold,
            "remaining_agents": len(self.agents) - len(culled),
        }

    def get_swarm_intelligence_score(self) -> Dict[str, Any]:
        """Compute the collective IQ of the swarm."""
        if not self.agents:
            return {
                "score": 0,
                "category": "below_average",
                "formula": "avg_performance * connectivity_density * task_completion_rate * emergence_positive_ratio",
                "components": {
                    "avg_performance": 0.0,
                    "connectivity_density": 0.0,
                    "task_completion_rate": 0.0,
                    "emergence_positive_ratio": 0.0,
                },
            }

        avg_perf = self._avg_agent_performance()
        connectivity = self._connectivity_density()
        completion_rate = self._task_completion_rate()
        emergence_positive = self._emergence_positive_ratio()

        # Base formula gives a score roughly in 0-200 range
        raw_score = (
            avg_perf * connectivity * completion_rate * emergence_positive
        )
        # Scale to IQ-like range (multiply by 200 for meaningful range)
        score = int(round(raw_score * 200))

        category = "below_average"
        for threshold, label in INTELLIGENCE_LEVELS:
            if score > threshold:
                category = label
                break

        return {
            "score": score,
            "category": category,
            "formula": "avg_performance * connectivity_density * task_completion_rate * emergence_positive_ratio * 200",
            "components": {
                "avg_performance": round(avg_perf, 4),
                "connectivity_density": round(connectivity, 4),
                "task_completion_rate": round(completion_rate, 4),
                "emergence_positive_ratio": round(emergence_positive, 4),
            },
        }

    def _emergence_positive_ratio(self) -> float:
        """Ratio of positive emergence events to total."""
        if not self.emergence_log:
            return 0.5  # neutral
        positive_levels = {"superorganism", "collective", "coordinated"}
        positive_count = sum(
            1 for e in self.emergence_log if e.get("level") in positive_levels
        )
        return positive_count / len(self.emergence_log)

    def get_status(self) -> Dict[str, Any]:
        """Return current swarm status."""
        active_count = sum(
            1 for a in self.agents.values() if a.get("status") == "active"
        )
        health = self._compute_swarm_health()

        # Determine emergence level from health
        level = "disorganized"
        for threshold, label in EMERGENCE_LEVELS:
            if health > threshold:
                level = label
                break

        return {
            "agent_count": len(self.agents),
            "active_agents": active_count,
            "task_count": len(self.task_queue),
            "emergence_events": len(self.emergence_log),
            "swarm_health": round(health, 4),
            "emergence_level": level,
            "swarm_state": self.swarm_state.copy(),
        }

    def _compute_swarm_health(self) -> float:
        """
        Swarm health formula:
        avg_agent_performance * connectivity_density * task_completion_rate * emergence_positive_ratio
        """
        avg_perf = self._avg_agent_performance()
        connectivity = self._connectivity_density()
        completion_rate = self._task_completion_rate()
        emergence_positive = self._emergence_positive_ratio()

        if not self.agents:
            return 0.0

        return avg_perf * connectivity * completion_rate * emergence_positive


# Global singleton
_module = None


def get_swarm_orchestrator() -> SwarmOrchestrator:
    """Get the global SwarmOrchestrator instance."""
    global _module
    if _module is None:
        _module = SwarmOrchestrator()
    return _module


def reset_swarm_orchestrator():
    """Reset the global SwarmOrchestrator (for testing)."""
    global _module
    _module = SwarmOrchestrator()
