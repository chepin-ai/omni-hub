"""
OMNI-HUB Resource Manager Tests v77
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.resource_manager import (
    ResourceAllocation, ResourceManager, get_resource_manager,
)


class TestResourceManager:
    def test_initialization(self):
        rm = ResourceManager()
        assert rm.allocation_count == 0
        assert rm.resources["energy"] == 1000.0

    def test_allocate(self):
        rm = ResourceManager()
        demands = [
            {"task": "growth", "priority": 0.8, "amount": 30.0, "resource": "energy"},
            {"task": "rest", "priority": 0.5, "amount": 20.0, "resource": "energy"},
        ]
        allocations = rm.allocate(demands)
        assert len(allocations) == 2
        assert allocations[0].task == "growth"  # Higher priority first

    def test_allocate_respects_priority(self):
        rm = ResourceManager()
        demands = [
            {"task": "low", "priority": 0.2, "amount": 500.0, "resource": "energy"},
            {"task": "high", "priority": 0.9, "amount": 500.0, "resource": "energy"},
        ]
        allocations = rm.allocate(demands)
        assert allocations[0].task == "high"
        assert allocations[0].amount > allocations[1].amount

    def test_optimize_from_state(self):
        rm = ResourceManager()
        state = {
            "energy": 500.0, "level": 3, "phase": "near_critical",
            "executive_function": {"active": None},
            "risk_analyzer": {"risks_found": 1},
            "opportunity_scanner": {"opportunities": 0},
        }
        allocations = rm.optimize_from_state(state)
        assert len(allocations) > 0

    def test_get_utilization(self):
        rm = ResourceManager()
        rm.allocate([{"task": "t1", "priority": 0.5, "amount": 50.0, "resource": "energy"}])
        util = rm.get_utilization()
        assert "energy" in util
        assert util["energy"] > 0

    def test_get_status(self):
        rm = ResourceManager()
        rm.optimize_from_state({"energy": 1000.0, "level": 3, "phase": "pre_emergence",
                                "executive_function": {}, "risk_analyzer": {}, "opportunity_scanner": {}})
        status = rm.get_status()
        assert "allocations" in status
        assert "utilization" in status


class TestGlobalEngine:
    def test_get_resource_manager(self):
        g = get_resource_manager()
        assert g is not None
        assert isinstance(g, ResourceManager)
