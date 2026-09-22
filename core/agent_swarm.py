"""
OMNI-HUB Agent Swarm v18
Role-specialized multi-agent orchestration layer.

Builds on core/swarm.py by adding heterogeneous agent roles,
task routing, and collective intelligence aggregation.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import random
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from core.agents import BaseAgent, create_agent, AGENT_REGISTRY
from core.swarm import SwarmIntelligence, SwarmConfig


@dataclass
class AgentSwarmConfig:
    """Configuration for heterogeneous agent swarm."""
    n_research: int = 2
    n_code: int = 2
    n_review: int = 1
    n_meta: int = 1
    cycle_limit: int = 1000
    report_interval: int = 100


class AgentSwarm:
    """Orchestrates a mixed team of specialized agents."""

    def __init__(self, config: AgentSwarmConfig = None):
        self.config = config or AgentSwarmConfig()
        self.agents: List[BaseAgent] = []
        self.cycle_count = 0
        self.collective_results: List[Dict[str, Any]] = []
        self._init_agents()

    def _init_agents(self):
        """Create agent team according to config."""
        counts = {
            "research": self.config.n_research,
            "code": self.config.n_code,
            "review": self.config.n_review,
            "meta": self.config.n_meta,
        }
        for role, count in counts.items():
            for _ in range(count):
                self.agents.append(create_agent(role))
        print(f"[AgentSwarm] Initialized: {len(self.agents)} agents")
        for role in counts:
            n = sum(1 for a in self.agents if a.state.role == role)
            print(f"  - {role}: {n}")

    def run_cycle(self, global_state: Optional[Dict[str, Any]] = None):
        """Run one collective cycle: all agents act."""
        self.cycle_count += 1
        if global_state is None:
            global_state = {"cycle": self.cycle_count, "level": 15}

        cycle_results = []
        for agent in self.agents:
            result = agent.run_cycle(global_state)
            cycle_results.append({
                "role": agent.state.role,
                "result": result,
            })

        self.collective_results.append({
            "cycle": self.cycle_count,
            "results": cycle_results,
        })

        # Update global state with collective insights
        self._update_global_state(global_state, cycle_results)

    def _update_global_state(self, global_state: Dict[str, Any], cycle_results: List[Dict[str, Any]]):
        """Aggregate agent outputs into global state."""
        # Count successful operations per role
        success_by_role: Dict[str, int] = {}
        for r in cycle_results:
            role = r["role"]
            success = r["result"].get("success", False)
            if role not in success_by_role:
                success_by_role[role] = 0
            if success:
                success_by_role[role] += 1

        # Boost global energy based on successful operations
        current_energy = global_state.get("energy", 1.0)
        total_success = sum(success_by_role.values())
        global_state["energy"] = current_energy * (1 + total_success * 0.001)
        global_state["agent_success"] = success_by_role
        global_state["cycle"] = self.cycle_count

    def run(self, cycles: int = None, report_interval: int = None):
        """Run multiple cycles with reporting."""
        cycles = cycles or self.config.cycle_limit
        interval = report_interval or self.config.report_interval

        for c in range(cycles):
            self.run_cycle()
            if (c + 1) % interval == 0:
                status = self.get_status()
                print(f"\n  C{c+1:4d}: Agents={status['n_agents']}, "
                      f"Cycles={status['cycles']}, "
                      f"Success={status['total_successful_tasks']}")

    def get_status(self) -> Dict[str, Any]:
        """Return swarm status."""
        total_tasks = sum(a.state.cycle_count for a in self.agents)
        successful = sum(
            1 for r in self.collective_results
            for res in r["results"]
            if res["result"].get("success", False)
        )
        by_role: Dict[str, Dict[str, Any]] = {}
        for agent in self.agents:
            role = agent.state.role
            if role not in by_role:
                by_role[role] = {"count": 0, "tasks": 0, "last_results": []}
            by_role[role]["count"] += 1
            by_role[role]["tasks"] += len(agent.state.task_history)
            if agent.state.last_result:
                by_role[role]["last_results"].append(agent.state.last_result)

        return {
            "n_agents": len(self.agents),
            "cycles": self.cycle_count,
            "total_tasks": total_tasks,
            "total_successful_tasks": successful,
            "by_role": by_role,
        }


if __name__ == "__main__":
    print("=" * 60)
    print("OMNI-HUB v18 AGENT SWARM DEMO")
    print("=" * 60)

    swarm = AgentSwarm(AgentSwarmConfig(
        n_research=2, n_code=2, n_review=1, n_meta=1,
        cycle_limit=50, report_interval=10,
    ))
    swarm.run()

    status = swarm.get_status()
    print(f"\n{'='*60}")
    print("FINAL AGENT SWARM STATUS")
    print(f"{'='*60}")
    print(f"Total agents: {status['n_agents']}")
    print(f"Collective cycles: {status['cycles']}")
    print(f"Total tasks executed: {status['total_tasks']}")
    print(f"Successful operations: {status['total_successful_tasks']}")
    print(f"\nBy role:")
    for role, info in status['by_role'].items():
        print(f"  {role:10s}: {info['count']} agents, {info['tasks']} tasks")

    print(f"\n{'='*60}")
    print("AGENT SWARM DEMO COMPLETE")
    print(f"{'='*60}")
