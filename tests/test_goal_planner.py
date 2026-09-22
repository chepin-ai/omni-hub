"""
OMNI-HUB Goal Planning System Tests v20
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.goal_planner import GoalPlanner, Goal, GoalStatus


class TestGoalCreation:
    def test_set_goal(self):
        planner = GoalPlanner()
        gid = planner.set_goal("Test Goal", "A test", priority=8)
        assert gid in planner.goals
        assert planner.goals[gid].title == "Test Goal"
        assert planner.goals[gid].status == GoalStatus.ACTIVE

    def test_set_sub_goal(self):
        planner = GoalPlanner()
        parent = planner.set_goal("Parent", "Parent goal")
        child = planner.set_goal("Child", "Child goal", parent_id=parent)
        assert child in planner.goals[parent].sub_goals
        assert planner.goals[child].parent_id == parent

    def test_auto_goal_generation(self):
        planner = GoalPlanner()
        state = {"level": 15, "energy": 1e6, "open_problems": {"critical": 1}}
        planner.run_cycle(state)
        assert len(planner.goals) >= 2  # level + critical


class TestGoalProgress:
    def test_update_progress(self):
        planner = GoalPlanner()
        gid = planner.set_goal("Progress Test", "")
        planner.update_progress(gid, 0.5)
        assert planner.goals[gid].progress == 0.5

    def test_complete_goal(self):
        planner = GoalPlanner()
        gid = planner.set_goal("Complete Test", "")
        planner.update_progress(gid, 1.0)
        assert planner.goals[gid].status == GoalStatus.COMPLETED
        assert planner.completed_count == 1

    def test_parent_progress_aggregation(self):
        planner = GoalPlanner()
        parent = planner.set_goal("Parent", "")
        child1 = planner.set_goal("Child1", "", parent_id=parent)
        child2 = planner.set_goal("Child2", "", parent_id=parent)
        planner.update_progress(child1, 1.0)
        planner.update_progress(child2, 1.0)
        assert planner.goals[parent].progress == 1.0
        assert planner.goals[parent].status == GoalStatus.COMPLETED


class TestGoalLifecycle:
    def test_block_goal(self):
        planner = GoalPlanner()
        gid = planner.set_goal("Blocked", "")
        planner.block_goal(gid, "External dependency missing")
        assert planner.goals[gid].status == GoalStatus.BLOCKED

    def test_abandon_goal(self):
        planner = GoalPlanner()
        gid = planner.set_goal("Abandoned", "")
        planner.abandon_goal(gid, "No longer relevant")
        assert planner.goals[gid].status == GoalStatus.ABANDONED

    def test_abandon_recursive(self):
        planner = GoalPlanner()
        parent = planner.set_goal("Parent", "")
        child = planner.set_goal("Child", "", parent_id=parent)
        planner.abandon_goal(parent, "Strategy changed")
        assert planner.goals[parent].status == GoalStatus.ABANDONED
        assert planner.goals[child].status == GoalStatus.ABANDONED

    def test_overdue_detection(self):
        planner = GoalPlanner()
        planner.cycle_count = 100
        gid = planner.set_goal("Overdue", "", deadline=50)
        assert planner.goals[gid].is_overdue(100)


class TestNextAction:
    def test_next_action_priority(self):
        planner = GoalPlanner()
        planner.set_goal("Low", "", priority=3)
        planner.set_goal("High", "", priority=9)
        action = planner.get_next_action()
        assert action['title'] == "High"

    def test_next_action_skips_blocked(self):
        planner = GoalPlanner()
        gid = planner.set_goal("Blocked", "", priority=10)
        planner.block_goal(gid, "Blocked")
        action = planner.get_next_action()
        assert action is None or action['title'] != "Blocked"

    def test_sub_goal_activation(self):
        planner = GoalPlanner()
        parent = planner.set_goal("Parent", "")
        child = planner.set_goal("Child", "", parent_id=parent)
        action = planner.get_next_action()
        assert action['type'] == "sub_goal"
        assert action['goal_id'] == child


class TestDecomposition:
    def test_decompose_goal(self):
        planner = GoalPlanner()
        parent = planner.set_goal("Build Feature", "")
        sub_ids = planner.decompose(parent, [
            {"title": "Design", "priority": 8},
            {"title": "Implement", "priority": 7},
        ])
        assert len(sub_ids) == 2
        assert all(sg in planner.goals[parent].sub_goals for sg in sub_ids)
