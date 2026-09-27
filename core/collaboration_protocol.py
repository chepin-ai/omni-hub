"""
OMNI-HUB Collaboration Protocol v78
Multi-agent coordination and negotiation.

No one is an island.
This module enables coordination between multiple agents —
task delegation, resource negotiation, consensus building.

Philosophy: 和而不同 — Harmony in diversity.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Agent:
    """A collaborating agent."""
    name: str
    role: str
    capacity: float  # 0-1
    load: float  # current load 0-1


@dataclass
class CollaborationTask:
    """A task for collaboration."""
    name: str
    required_capacity: float
    assigned_to: Optional[str] = None
    status: str = "unassigned"


class CollaborationProtocol:
    """
    Multi-agent coordination and negotiation.
    """

    def __init__(self):
        self.agents: List[Agent] = []
        self.tasks: List[CollaborationTask] = []
        self.negotiations: List[Dict[str, Any]] = []
        self.collaboration_count = 0
        self._init_agents()

    def _init_agents(self):
        """Initialize default agents."""
        self.agents = [
            Agent("orchestrator", "coordinator", 1.0, 0.0),
            Agent("self_awareness", "introspection", 0.8, 0.0),
            Agent("learning", "adaptation", 0.9, 0.0),
            Agent("reasoning", "inference", 0.85, 0.0),
            Agent("execution", "action", 0.9, 0.0),
        ]

    def register_agent(self, name: str, role: str, capacity: float):
        """Register a new agent."""
        self.agents.append(Agent(name, role, capacity, 0.0))

    def propose_task(self, name: str, required_capacity: float):
        """Propose a new collaborative task."""
        self.tasks.append(CollaborationTask(name, required_capacity))

    def negotiate_assignment(self) -> List[CollaborationTask]:
        """Negotiate task assignments based on capacity."""
        assigned = []

        for task in self.tasks:
            if task.status != "unassigned":
                continue

            # Find agent with most available capacity
            candidates = [a for a in self.agents if a.capacity - a.load >= task.required_capacity]

            if candidates:
                best = max(candidates, key=lambda a: a.capacity - a.load)
                task.assigned_to = best.name
                task.status = "assigned"
                best.load += task.required_capacity
                assigned.append(task)

                self.negotiations.append({
                    "task": task.name,
                    "assigned_to": best.name,
                    "reason": "highest_available_capacity",
                })

        self.collaboration_count += len(assigned)
        return assigned

    def resolve_conflict(self, task1: str, task2: str) -> str:
        """Resolve conflict between competing tasks."""
        # Higher required capacity wins (more important)
        t1 = next((t for t in self.tasks if t.name == task1), None)
        t2 = next((t for t in self.tasks if t.name == task2), None)

        if t1 and t2:
            return t1.name if t1.required_capacity >= t2.required_capacity else t2.name
        return task1 if t1 else task2

    def coordinate_from_state(self, state: Dict[str, Any]):
        """Derive collaboration needs from state."""
        # Add tasks based on system needs
        goals = state.get('generated_goals', [])
        for goal in goals[:3]:
            self.propose_task(f"achieve_{goal}", required_capacity=0.3)

        # Add risk mitigation tasks
        risks = state.get('risk_analyzer', {}).get('risks_found', 0)
        if risks > 0:
            self.propose_task("mitigate_risks", required_capacity=0.5)

        # Add opportunity tasks
        best_opp = state.get('best_opportunity')
        if best_opp:
            self.propose_task(f"seize_{best_opp.get('name', 'opportunity')}", required_capacity=0.4)

        # Reset loads and negotiate
        for agent in self.agents:
            agent.load = 0.0

        return self.negotiate_assignment()

    def get_status(self) -> Dict[str, Any]:
        return {
            "agents": len(self.agents),
            "tasks": len(self.tasks),
            "assigned": sum(1 for t in self.tasks if t.status == "assigned"),
            "collaborations": self.collaboration_count,
            "agent_status": [
                {"name": a.name, "role": a.role, "available": round(a.capacity - a.load, 2)}
                for a in self.agents
            ],
        }


_cp_engine = None

def get_collaboration_protocol():
    global _cp_engine
    if _cp_engine is None:
        _cp_engine = CollaborationProtocol()
    return _cp_engine
