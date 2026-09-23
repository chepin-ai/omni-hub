"""
OMNI-HUB Collective Intelligence Engine v38
Multi-hub collaborative problem-solving network.

When one mind faces a problem too complex, many minds
combine their strengths to solve it together.

Philosophy: 候即违规 — One mind is never enough.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProblemTask:
    """A task distributed to the collective."""
    task_id: str
    problem_type: str
    description: str
    complexity: float  # 0.0-1.0
    assigned_to: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, active, solved, failed
    consensus: Optional[Any] = None


@dataclass
class CollectiveAgent:
    """A member of the collective intelligence network."""
    agent_id: str
    capabilities: List[str]
    load: float = 0.0  # 0.0-1.0
    reliability: float = 0.9
    last_active: str = ""


class TaskDistributor:
    """Distributes problems to available collective agents."""

    def distribute(self, task: ProblemTask, agents: List[CollectiveAgent]) -> ProblemTask:
        """Assign task to best-suited agents."""
        # Sort agents by capability match and load
        capable = [a for a in agents if any(c in a.capabilities for c in self._get_required_caps(task.problem_type))]
        capable.sort(key=lambda a: (a.load, -a.reliability))

        # Assign to top 3 or all if fewer
        n_assign = min(3, len(capable))
        task.assigned_to = [a.agent_id for a in capable[:n_assign]]
        for a in capable[:n_assign]:
            a.load = min(1.0, a.load + 0.1 * task.complexity)
        task.status = "active"
        return task

    def _get_required_caps(self, problem_type: str) -> List[str]:
        """Map problem types to required capabilities."""
        mapping = {
            "research": ["analysis", "search"],
            "coding": ["code", "debug"],
            "optimization": ["math", "analysis"],
            "creative": ["generate", "synthesize"],
            "verification": ["test", "audit"],
        }
        return mapping.get(problem_type, ["general"])


class ConsensusBuilder:
    """Builds consensus from multiple agent results."""

    def build_consensus(self, task: ProblemTask) -> Any:
        """Aggregate results into a consensus answer."""
        results = task.results.values()
        if not results:
            return None

        # For numeric results, take weighted average
        numeric = [r for r in results if isinstance(r, (int, float))]
        if numeric:
            return sum(numeric) / len(numeric)

        # For string results, take most common
        strings = [r for r in results if isinstance(r, str)]
        if strings:
            from collections import Counter
            return Counter(strings).most_common(1)[0][0]

        # For dict results, merge keys
        dicts = [r for r in results if isinstance(r, dict)]
        if dicts:
            merged = {}
            for d in dicts:
                for k, v in d.items():
                    if k not in merged:
                        merged[k] = []
                    merged[k].append(v)
            # Average numeric values in merged dicts
            for k, vals in merged.items():
                if all(isinstance(v, (int, float)) for v in vals):
                    merged[k] = sum(vals) / len(vals)
            return merged

        return list(results)[0]


class CollectiveIntelligenceEngine:
    """
    Collaborative problem-solving network controller.
    """

    def __init__(self):
        self.agents: Dict[str, CollectiveAgent] = {}
        self.tasks: Dict[str, ProblemTask] = {}
        self.distributor = TaskDistributor()
        self.consensus = ConsensusBuilder()
        self.solved_count = 0
        self.failed_count = 0

    def register_agent(self, agent_id: str, capabilities: List[str], reliability: float = 0.9):
        """Register a new collective agent."""
        self.agents[agent_id] = CollectiveAgent(
            agent_id=agent_id,
            capabilities=capabilities,
            reliability=reliability,
            last_active=datetime.now().isoformat(),
        )

    def submit_problem(self, problem_type: str, description: str, complexity: float = 0.5) -> str:
        """Submit a problem to the collective."""
        task = ProblemTask(
            task_id=str(uuid.uuid4())[:8],
            problem_type=problem_type,
            description=description,
            complexity=complexity,
        )
        self.tasks[task.task_id] = task
        self.distributor.distribute(task, list(self.agents.values()))
        return task.task_id

    def submit_result(self, task_id: str, agent_id: str, result: Any):
        """Submit a result from an agent."""
        if task_id not in self.tasks:
            return
        task = self.tasks[task_id]
        task.results[agent_id] = result

        # Check if all assigned agents have responded
        if set(task.assigned_to).issubset(set(task.results.keys())):
            task.consensus = self.consensus.build_consensus(task)
            task.status = "solved"
            self.solved_count += 1
            # Reduce load on participating agents
            for aid in task.assigned_to:
                if aid in self.agents:
                    self.agents[aid].load = max(0.0, self.agents[aid].load - 0.1)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task."""
        if task_id not in self.tasks:
            return None
        task = self.tasks[task_id]
        return {
            "task_id": task.task_id,
            "status": task.status,
            "assigned": task.assigned_to,
            "results_received": len(task.results),
            "consensus": task.consensus,
        }

    def get_collective_status(self) -> Dict[str, Any]:
        """Get overall collective status."""
        return {
            "agents": len(self.agents),
            "tasks": len(self.tasks),
            "solved": self.solved_count,
            "failed": self.failed_count,
            "avg_agent_load": sum(a.load for a in self.agents.values()) / len(self.agents) if self.agents else 0.0,
        }


# Global instance
_ci_engine = None

def get_collective_intelligence() -> CollectiveIntelligenceEngine:
    global _ci_engine
    if _ci_engine is None:
        _ci_engine = CollectiveIntelligenceEngine()
    return _ci_engine


if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v38 COLLECTIVE INTELLIGENCE ENGINE")
    print("=" * 70)

    ci = CollectiveIntelligenceEngine()

    # Register agents
    ci.register_agent("alpha", ["analysis", "search", "general"], 0.95)
    ci.register_agent("beta", ["code", "debug", "general"], 0.90)
    ci.register_agent("gamma", ["math", "analysis", "general"], 0.92)
    ci.register_agent("delta", ["generate", "synthesize", "general"], 0.88)

    # Submit a problem
    task_id = ci.submit_problem("optimization", "Find optimal energy decay rate", complexity=0.7)
    print(f"\nTask {task_id} submitted")
    print(f"Assigned to: {ci.tasks[task_id].assigned_to}")

    # Simulate results
    for agent in ci.tasks[task_id].assigned_to:
        ci.submit_result(task_id, agent, {"optimal_rate": 0.005 + hash(agent) % 100 / 10000})

    status = ci.get_task_status(task_id)
    print(f"\nStatus: {status['status']}")
    print(f"Consensus: {status['consensus']}")

    print(f"\nCollective status: {ci.get_collective_status()}")
    print(f"{'='*70}")
