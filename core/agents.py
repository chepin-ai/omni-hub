"""
OMNI-HUB Specialized Agent Framework v18
Role-based autonomous agents with expertise-driven tool selection.

Each agent has a primary role that biases its tool usage and decision making.
Agents operate within the swarm but contribute specialized capabilities.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from core.tools import ToolRegistry, get_tool_registry


@dataclass
class AgentState:
    """Internal state of an agent."""
    role: str
    energy: float = 1.0
    phi: float = 0.5
    cycle_count: int = 0
    task_history: List[Dict[str, Any]] = field(default_factory=list)
    last_result: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """Abstract base for all specialized agents."""

    ROLE: str = "base"
    PREFERRED_TOOLS: List[str] = []
    DESCRIPTION: str = ""

    def __init__(self, tools: ToolRegistry = None):
        self.tools = tools or get_tool_registry()
        self.state = AgentState(role=self.ROLE)

    @abstractmethod
    def decide_task(self, global_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Decide what task to perform based on global system state."""
        pass

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using tools."""
        tool_name = task.get("tool")
        params = task.get("params", {})
        result = self.tools.invoke(tool_name, **params)
        self.state.last_result = result.to_dict()
        self.state.task_history.append({
            "task": task,
            "result": result.to_dict(),
            "cycle": self.state.cycle_count,
        })
        return result.to_dict()

    def run_cycle(self, global_state: Dict[str, Any]) -> Dict[str, Any]:
        """One autonomous cycle: decide + execute."""
        self.state.cycle_count += 1
        task = self.decide_task(global_state)
        if task:
            return self.execute_task(task)
        return {"tool": "none", "success": False, "error": "No task decided"}

    def get_status(self) -> Dict[str, Any]:
        return {
            "role": self.ROLE,
            "cycles": self.state.cycle_count,
            "energy": self.state.energy,
            "phi": self.state.phi,
            "tasks": len(self.state.task_history),
            "last_result": self.state.last_result,
        }


class ResearchAgent(BaseAgent):
    """Gathers information from files and external sources."""
    ROLE = "research"
    PREFERRED_TOOLS = ["file_read", "web_search", "time_check"]
    DESCRIPTION = "Reads files, checks time, searches for information"

    def decide_task(self, global_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Prefer reading files that haven't been read recently
        tool = random.choice(self.PREFERRED_TOOLS)
        if tool == "file_read":
            # Try to read a random core module
            targets = ["core/constants.py", "core/orchestrator.py", "core/swarm.py",
                       "core/tools.py", "core/event_bus.py"]
            return {"tool": "file_read", "params": {"path": random.choice(targets)}}
        elif tool == "web_search":
            return {"tool": "web_search", "params": {"query": "autonomous systems research 2026"}}
        else:
            return {"tool": tool, "params": {}}


class CodeAgent(BaseAgent):
    """Generates and validates code."""
    ROLE = "code"
    PREFERRED_TOOLS = ["code_execute", "file_write", "file_read"]
    DESCRIPTION = "Executes code snippets, writes files, validates syntax"

    def decide_task(self, global_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        tool = random.choice(self.PREFERRED_TOOLS)
        if tool == "code_execute":
            # Validate a core module by importing it
            code = "import sys; sys.path.insert(0, '/mnt/agents/output/OMNI-HUB'); from core import constants; print('OK')"
            return {"tool": "code_execute", "params": {"code": code}}
        elif tool == "file_write":
            # Write a small status log
            return {"tool": "file_write", "params": {
                "path": "logs/agent_status.txt",
                "content": f"# Agent status log\nCycle: {self.state.cycle_count}\n"
            }}
        else:
            return {"tool": "file_read", "params": {"path": "core/orchestrator.py"}}


class ReviewAgent(BaseAgent):
    """Monitors system health and reports issues."""
    ROLE = "review"
    PREFERRED_TOOLS = ["system_status", "time_check"]
    DESCRIPTION = "Monitors CPU, memory, disk, time"

    def decide_task(self, global_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Always check system status
        return {"tool": "system_status", "params": {}}


class MetaAgent(BaseAgent):
    """Analyzes system evolution and proposes improvements."""
    ROLE = "meta"
    PREFERRED_TOOLS = ["file_read", "code_execute", "time_check"]
    DESCRIPTION = "Analyzes state history, computes statistics, proposes changes"

    def decide_task(self, global_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Read open problems and compute summary
        return {"tool": "file_read", "params": {"path": "hub/open_problems.json"}}


AGENT_REGISTRY = {
    "research": ResearchAgent,
    "code": CodeAgent,
    "review": ReviewAgent,
    "meta": MetaAgent,
}


def create_agent(role: str, tools: ToolRegistry = None) -> BaseAgent:
    """Factory function to create agents by role."""
    cls = AGENT_REGISTRY.get(role, ResearchAgent)
    return cls(tools=tools)


if __name__ == "__main__":
    print("[OMNI-HUB v18] Specialized Agent Framework Demo")
    print()
    for role, cls in AGENT_REGISTRY.items():
        agent = cls()
        print(f"Role: {role}")
        print(f"  Description: {cls.DESCRIPTION}")
        print(f"  Preferred tools: {cls.PREFERRED_TOOLS}")
        # Run one cycle
        result = agent.run_cycle({"level": 15, "energy": 1e6})
        print(f"  Demo cycle result: {result['tool']} (success={result['success']})")
        print()
