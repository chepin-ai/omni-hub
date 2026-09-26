"""
OMNI-HUB Executive Function v70
Top-down control, task switching, inhibition.

The mind is a ship. Executive function is the captain.
It decides which course to take, when to change direction,
and what to ignore in the storm.
This module provides top-down cognitive control —
task switching, inhibition, working memory management.

Philosophy: 制心一处，无事不办 — When the mind is unified, nothing is impossible.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Task:
    """A cognitive task."""
    name: str
    priority: float
    deadline: int  # cycle count
    status: str  # pending, active, completed, inhibited


class ExecutiveFunction:
    """
    Top-down cognitive control.
    """

    def __init__(self):
        self.tasks: List[Task] = []
        self.active_task: Optional[Task] = None
        self.task_history: List[str] = []
        self.inhibitions: List[str] = []  # Suppressed impulses
        self.switch_count = 0

    def add_task(self, name: str, priority: float, deadline: int):
        """Add a new task."""
        self.tasks.append(Task(name, priority, deadline, "pending"))

    def prioritize(self) -> Optional[Task]:
        """Select highest priority task."""
        pending = [t for t in self.tasks if t.status == "pending"]
        if not pending:
            return None

        # Sort by priority descending, then deadline ascending
        pending.sort(key=lambda t: (-t.priority, t.deadline))
        return pending[0]

    def switch_task(self, cycle: int):
        """Switch to highest priority task."""
        next_task = self.prioritize()

        if next_task is None:
            return None

        # Check if we should switch
        if self.active_task is None or self.active_task.name != next_task.name:
            if self.active_task:
                self.active_task.status = "pending"
                self.switch_count += 1

            self.active_task = next_task
            next_task.status = "active"
            self.task_history.append(next_task.name)

        return next_task

    def inhibit(self, impulse: str):
        """Inhibit an inappropriate impulse."""
        self.inhibitions.append(impulse)

    def evaluate_impulse(self, impulse: str, state: Dict[str, Any]) -> bool:
        """Evaluate whether to allow or inhibit an impulse."""
        # Inhibit if energy is very low and impulse is demanding
        energy = state.get('energy', 1000.0)
        if isinstance(energy, (int, float)) and energy < 50:
            if impulse in ["focus", "transcend", "explore"]:
                self.inhibit(f"{impulse}_low_energy")
                return False

        # Inhibit if system is in critical phase and impulse is risky
        phase = state.get('phase', '')
        if phase == "near_critical" and impulse == "transcend":
            self.inhibit(f"{impulse}_critical_phase")
            return False

        return True

    def derive_tasks_from_state(self, state: Dict[str, Any], cycle: int):
        """Derive tasks from system state."""
        energy = state.get('energy', 1000.0)
        level = state.get('level', 0)
        phase = state.get('phase', '')

        # Task 1: Maintain energy if low
        if isinstance(energy, (int, float)) and energy < 200:
            self.add_task("restore_energy", priority=0.9, deadline=cycle + 20)

        # Task 2: Grow if stable
        if isinstance(level, (int, float)) and level < 10:
            self.add_task("continue_growth", priority=0.7, deadline=cycle + 100)

        # Task 3: Integrate if fragmented
        active_lines = state.get('active_lines', 0)
        if isinstance(active_lines, int) and active_lines < 11:
            self.add_task("activate_all_lines", priority=0.8, deadline=cycle + 50)

        # Task 4: Monitor convergence
        convergence = state.get('convergence', {})
        if convergence and convergence.get('is_diverging'):
            self.add_task("address_divergence", priority=0.95, deadline=cycle + 10)

    def get_status(self) -> Dict[str, Any]:
        return {
            "tasks": len(self.tasks),
            "pending": sum(1 for t in self.tasks if t.status == "pending"),
            "active": self.active_task.name if self.active_task else None,
            "switches": self.switch_count,
            "inhibitions": len(self.inhibitions),
            "history": self.task_history[-5:],
        }


_ef_engine = None

def get_executive_function():
    global _ef_engine
    if _ef_engine is None:
        _ef_engine = ExecutiveFunction()
    return _ef_engine
