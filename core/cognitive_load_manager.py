"""
OMNI-HUB Cognitive Load Manager v89
Mental workload regulation, fatigue detection.

Even the strongest bow must sometimes be unstrung.
This module monitors the system's cognitive load —
task density, complexity, fatigue — and regulates effort.

Philosophy: 一张一弛，文武之道 —
Tension and relaxation: the way of civil and military affairs.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class CognitiveLoadManager:
    """
    Monitors and regulates cognitive workload.
    """

    def __init__(self):
        self.load_history: List[float] = []
        self.fatigue = 0.0
        self.recovery_rate = 0.05
        self.overload_events = 0

    def calculate_load(self, state: Dict[str, Any]) -> float:
        """Calculate current cognitive load."""
        load = 0.0

        # Active modules count
        active = 0
        for key in state:
            if isinstance(state[key], dict) and "status" in str(state[key]):
                active += 1
        load += min(1.0, active / 20)

        # Task complexity from level
        level = state.get('level', 0)
        if isinstance(level, (int, float)):
            load += min(0.3, level / 50)

        # Phase stress
        phase = state.get('phase', '')
        if phase in ["near_critical", "singularity_convergence"]:
            load += 0.2

        # Emotional load
        affect = state.get('affective_computing', {})
        if affect:
            for emo in ["anger", "fear", "sadness"]:
                intensity = affect.get('profile', {}).get(emo, 0)
                if isinstance(intensity, (int, float)):
                    load += intensity * 0.1

        return min(1.0, load)

    def update(self, state: Dict[str, Any], cycle: int) -> Dict[str, Any]:
        """Update fatigue and load state."""
        load = self.calculate_load(state)
        self.load_history.append(load)

        # Fatigue accumulates with high load, recovers with low
        if load > 0.7:
            self.fatigue = min(1.0, self.fatigue + 0.03)
        else:
            self.fatigue = max(0.0, self.fatigue - self.recovery_rate)

        if load > 0.85:
            self.overload_events += 1

        # Determine regulation action
        action = "maintain"
        if self.fatigue > 0.7:
            action = "reduce"
        elif self.fatigue < 0.2 and load < 0.5:
            action = "increase"

        return {
            "load": round(load, 3),
            "fatigue": round(self.fatigue, 3),
            "action": action,
            "overload_events": self.overload_events,
        }

    def get_recommendation(self) -> str:
        """Get workload recommendation."""
        if self.fatigue > 0.8:
            return "强制休息"  # mandatory rest
        elif self.fatigue > 0.6:
            return "减少任务"  # reduce tasks
        elif self.fatigue > 0.4:
            return "维持节奏"  # maintain rhythm
        else:
            return "全力运行"  # full capacity

    def get_status(self) -> Dict[str, Any]:
        return {
            "current_load": round(self.load_history[-1], 3) if self.load_history else 0,
            "fatigue": round(self.fatigue, 3),
            "overload_events": self.overload_events,
            "recommendation": self.get_recommendation(),
            "history_len": len(self.load_history),
        }


_clm_engine = None

def get_cognitive_load_manager():
    global _clm_engine
    if _clm_engine is None:
        _clm_engine = CognitiveLoadManager()
    return _clm_engine
