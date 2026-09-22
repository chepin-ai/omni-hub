"""
OMNI-HUB Goal Planning System v20
Multi-step objective pursuit with hierarchical goal decomposition.

The system can autonomously set goals, decompose them into sub-goals,
track progress, and adapt when blocked. Goals have priorities,
deadlines (in cycles), and success criteria.

Philosophy: 候即违规 — drifting without purpose is the ultimate violation.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class GoalStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class Goal:
    """A single goal with tracking metadata."""
    id: str
    title: str
    description: str
    status: GoalStatus = GoalStatus.PENDING
    priority: int = 5  # 1-10, higher = more important
    created_cycle: int = 0
    deadline_cycle: Optional[int] = None  # None = no deadline
    parent_id: Optional[str] = None
    progress: float = 0.0  # 0.0 - 1.0
    sub_goals: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_overdue(self, current_cycle: int) -> bool:
        if self.deadline_cycle is None:
            return False
        return current_cycle > self.deadline_cycle and self.status not in (GoalStatus.COMPLETED, GoalStatus.ABANDONED)


class GoalPlanner:
    """Manages hierarchical goal decomposition and progress tracking."""

    def __init__(self):
        self.goals: Dict[str, Goal] = {}
        self.active_stack: List[str] = []  # Current focus stack
        self.cycle_count = 0
        self.completed_count = 0
        self._id_counter = 0

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"G{self._id_counter:04d}"

    def set_goal(self, title: str, description: str = "", priority: int = 5,
                 deadline: Optional[int] = None, parent_id: Optional[str] = None) -> str:
        """Set a new goal. Returns goal ID."""
        gid = self._next_id()
        goal = Goal(
            id=gid, title=title, description=description,
            status=GoalStatus.ACTIVE if parent_id is None else GoalStatus.PENDING,
            priority=priority, created_cycle=self.cycle_count,
            deadline_cycle=deadline, parent_id=parent_id,
        )
        self.goals[gid] = goal
        if parent_id and parent_id in self.goals:
            self.goals[parent_id].sub_goals.append(gid)
        if parent_id is None:
            self.active_stack.append(gid)
        return gid

    def decompose(self, goal_id: str, sub_tasks: List[Dict[str, Any]]) -> List[str]:
        """Decompose a goal into sub-goals."""
        if goal_id not in self.goals:
            return []
        sub_ids = []
        for task in sub_tasks:
            gid = self.set_goal(
                title=task['title'],
                description=task.get('description', ''),
                priority=task.get('priority', 5),
                deadline=task.get('deadline'),
                parent_id=goal_id,
            )
            sub_ids.append(gid)
        return sub_ids

    def update_progress(self, goal_id: str, progress: float, note: str = ""):
        """Update goal progress (0.0-1.0)."""
        if goal_id not in self.goals:
            return
        goal = self.goals[goal_id]
        goal.progress = max(0.0, min(1.0, progress))
        if note:
            goal.metadata.setdefault('notes', []).append({"cycle": self.cycle_count, "note": note})
        if goal.progress >= 1.0:
            goal.status = GoalStatus.COMPLETED
            self.completed_count += 1
            # Update parent progress if applicable
            if goal.parent_id and goal.parent_id in self.goals:
                self._update_parent_progress(goal.parent_id)

    def _update_parent_progress(self, parent_id: str):
        parent = self.goals[parent_id]
        if not parent.sub_goals:
            return
        total = sum(self.goals[sg].progress for sg in parent.sub_goals if sg in self.goals)
        parent.progress = total / len(parent.sub_goals)
        if parent.progress >= 1.0:
            parent.status = GoalStatus.COMPLETED
            self.completed_count += 1

    def block_goal(self, goal_id: str, reason: str):
        """Mark a goal as blocked."""
        if goal_id in self.goals:
            self.goals[goal_id].status = GoalStatus.BLOCKED
            self.goals[goal_id].metadata['block_reason'] = reason
            self.goals[goal_id].metadata['blocked_at'] = self.cycle_count

    def abandon_goal(self, goal_id: str, reason: str):
        """Abandon a goal and its sub-goals."""
        if goal_id not in self.goals:
            return
        self._abandon_recursive(goal_id, reason)

    def _abandon_recursive(self, goal_id: str, reason: str):
        goal = self.goals[goal_id]
        goal.status = GoalStatus.ABANDONED
        goal.metadata['abandon_reason'] = reason
        for sg in goal.sub_goals:
            if sg in self.goals:
                self._abandon_recursive(sg, reason)

    def get_next_action(self) -> Optional[Dict[str, Any]]:
        """Determine the next most important action based on active goals."""
        # Filter active, non-blocked goals
        active = [g for g in self.goals.values()
                  if g.status == GoalStatus.ACTIVE and not g.is_overdue(self.cycle_count)]
        if not active:
            return None
        # Sort by priority desc, then by progress asc (focus on least progressed)
        active.sort(key=lambda g: (-g.priority, g.progress))
        top = active[0]
        # If it has pending sub-goals, activate the first one
        for sg_id in top.sub_goals:
            sg = self.goals.get(sg_id)
            if sg and sg.status == GoalStatus.PENDING:
                sg.status = GoalStatus.ACTIVE
                return {"type": "sub_goal", "goal_id": sg_id, "title": sg.title, "parent": top.id}
        return {"type": "direct", "goal_id": top.id, "title": top.title}

    def run_cycle(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one planning cycle."""
        self.cycle_count += 1

        # Check for overdue goals
        overdue = [g for g in self.goals.values() if g.is_overdue(self.cycle_count)]
        for g in overdue:
            g.status = GoalStatus.BLOCKED
            g.metadata['overdue_at'] = self.cycle_count

        # Auto-generate goals based on system state
        self._auto_goal_generation(system_state)

        next_action = self.get_next_action()

        return {
            "cycle": self.cycle_count,
            "active_goals": len([g for g in self.goals.values() if g.status == GoalStatus.ACTIVE]),
            "completed": self.completed_count,
            "overdue": len(overdue),
            "next_action": next_action,
        }

    def _auto_goal_generation(self, state: Dict[str, Any]):
        """Automatically create goals based on system needs."""
        level = state.get('level', 0)
        energy = state.get('energy', 0)
        open_probs = state.get('open_problems', {})

        # Goal: Level advancement
        if level < 20:
            goal_title = f"Reach Level {level + 1}"
            if not any(g.title == goal_title and g.status != GoalStatus.COMPLETED for g in self.goals.values()):
                self.set_goal(goal_title, f"Advance from Level {level} to {level + 1}", priority=8, deadline=self.cycle_count + 500)

        # Goal: Resolve critical problems
        critical = open_probs.get('critical', 0)
        if critical > 0:
            goal_title = "Resolve critical issues"
            if not any(g.title == goal_title and g.status != GoalStatus.COMPLETED for g in self.goals.values()):
                self.set_goal(goal_title, f"Fix {critical} critical open problem(s)", priority=10, deadline=self.cycle_count + 100)

        # Goal: Meta-evolution at high levels
        if level >= 24:
            goal_title = "Optimize meta-multipliers"
            if not any(g.title == goal_title and g.status != GoalStatus.COMPLETED for g in self.goals.values()):
                self.set_goal(goal_title, "Self-modify growth parameters for efficiency", priority=7)

    def get_status(self) -> Dict[str, Any]:
        by_status = {
            "pending": [],
            "active": [],
            "blocked": [],
            "completed": [],
            "abandoned": [],
        }
        for g in self.goals.values():
            by_status[g.status.value].append({
                "id": g.id, "title": g.title, "priority": g.priority,
                "progress": g.progress, "deadline": g.deadline_cycle,
            })
        return {
            "total": len(self.goals),
            "completed": self.completed_count,
            "by_status": by_status,
            "top_priority": by_status["active"][:3] if by_status["active"] else [],
        }


if __name__ == "__main__":
    print("[OMNI-HUB v20] Goal Planning System Demo")
    planner = GoalPlanner()

    # Simulate system state
    state = {"level": 15, "energy": 1e6, "open_problems": {"critical": 1}}

    for c in range(10):
        result = planner.run_cycle(state)
        print(f"  C{c+1:2d}: Active={result['active_goals']}, Completed={result['completed']}, Next={result['next_action']['title'] if result['next_action'] else 'None'}")
        # Simulate progress
        if result['next_action'] and c % 3 == 0:
            planner.update_progress(result['next_action']['goal_id'], 0.3 * ((c // 3) + 1))

    status = planner.get_status()
    print(f"\nFinal: {status['total']} goals, {status['completed']} completed")
    print(f"Active: {[g['title'] for g in status['by_status']['active']]}")
