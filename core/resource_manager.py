"""
OMNI-HUB Resource Manager v77
Energy/time/attention allocation optimization.

Resources are finite. Wants are infinite.
Wisdom lies in the allocation.
This module optimizes resource distribution —
energy, time, attention — across competing demands.

Philosophy: 物有本末，事有终始，知所先后，则近道矣 —
Things have roots and branches; affairs have ends and beginnings.
Know the sequence and you are near the Way.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ResourceAllocation:
    """Allocation of a resource to a task."""
    resource: str
    task: str
    amount: float
    priority: float


class ResourceManager:
    """
    Optimizes allocation of energy, time, and attention.
    """

    def __init__(self):
        self.allocations: List[ResourceAllocation] = []
        self.resources = {
            "energy": 1000.0,
            "time": 100.0,
            "attention": 100.0,
        }
        self.allocation_count = 0

    def set_available(self, resource: str, amount: float):
        """Set available resource amount."""
        self.resources[resource] = amount

    def allocate(self, demands: List[Dict[str, Any]]) -> List[ResourceAllocation]:
        """Allocate resources based on demands."""
        self.allocations = []

        # Sort demands by priority descending
        sorted_demands = sorted(demands, key=lambda d: -d.get('priority', 0.5))

        remaining = self.resources.copy()

        for demand in sorted_demands:
            task = demand.get('task', 'unknown')
            priority = demand.get('priority', 0.5)
            requested = demand.get('amount', 10.0)
            resource = demand.get('resource', 'energy')

            if resource not in remaining:
                continue

            # Allocate min(requested, remaining * priority)
            available = remaining[resource]
            alloc = min(requested, available * priority)

            if alloc > 0:
                self.allocations.append(ResourceAllocation(
                    resource=resource,
                    task=task,
                    amount=round(alloc, 2),
                    priority=priority,
                ))
                remaining[resource] -= alloc

        self.allocation_count += 1
        return self.allocations

    def optimize_from_state(self, state: Dict[str, Any]) -> List[ResourceAllocation]:
        """Derive demands from system state and allocate."""
        energy = state.get('energy', 1000.0)
        level = state.get('level', 0)
        phase = state.get('phase', '')
        active_task = state.get('executive_function', {}).get('active')
        risks = state.get('risk_analyzer', {}).get('risks_found', 0)
        opportunities = state.get('opportunity_scanner', {}).get('opportunities', 0)

        self.set_available('energy', energy if isinstance(energy, (int, float)) else 1000.0)
        self.set_available('time', 100.0)
        self.set_available('attention', 100.0)

        demands = []

        # Growth demand
        if isinstance(level, (int, float)) and level < 10:
            demands.append({'task': 'growth', 'priority': 0.7, 'amount': 30.0, 'resource': 'energy'})

        # Integration demand
        if active_task == "activate_all_lines":
            demands.append({'task': 'integration', 'priority': 0.8, 'amount': 25.0, 'resource': 'energy'})

        # Risk mitigation demand
        if risks > 0:
            demands.append({'task': 'risk_mitigation', 'priority': 0.9, 'amount': 20.0, 'resource': 'attention'})

        # Opportunity pursuit demand
        if opportunities > 0:
            demands.append({'task': 'opportunity', 'priority': 0.75, 'amount': 20.0, 'resource': 'energy'})

        # Phase-specific demands
        if phase == "near_critical":
            demands.append({'task': 'phase_transition', 'priority': 0.95, 'amount': 40.0, 'resource': 'energy'})

        # Rest demand if energy is low
        if isinstance(energy, (int, float)) and energy < 300:
            demands.append({'task': 'rest', 'priority': 0.85, 'amount': 30.0, 'resource': 'energy'})

        return self.allocate(demands)

    def get_utilization(self) -> Dict[str, float]:
        """Get resource utilization rates."""
        util = {}
        for res, total in self.resources.items():
            used = sum(a.amount for a in self.allocations if a.resource == res)
            util[res] = round(used / max(1.0, total), 3)
        return util

    def get_status(self) -> Dict[str, Any]:
        return {
            "allocations": self.allocation_count,
            "current": [
                {"resource": a.resource, "task": a.task, "amount": a.amount, "priority": a.priority}
                for a in self.allocations
            ],
            "utilization": self.get_utilization(),
            "available": self.resources,
        }


_rm_engine = None

def get_resource_manager():
    global _rm_engine
    if _rm_engine is None:
        _rm_engine = ResourceManager()
    return _rm_engine
