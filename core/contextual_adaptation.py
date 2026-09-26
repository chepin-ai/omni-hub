"""
OMNI-HUB Contextual Adaptation v57
Context-aware behavior adjustment.

Context shapes behavior.
The same mind acts differently in different environments.
This module adapts system parameters based on external context —
time, session length, interaction patterns.

Philosophy: 环境塑造行为 — Context shapes behavior.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ContextProfile:
    """Current context profile."""
    session_length: int
    time_of_day: str  # morning, afternoon, evening, night
    day_of_week: str
    interaction_density: float  # messages per cycle
    user_engagement: float  # 0-1


class ContextualAdaptationEngine:
    """
    Adapts system behavior based on external context.
    """

    def __init__(self):
        self.context_history: List[ContextProfile] = []
        self.adaptation_count = 0

    def assess_context(self, cycle_count: int, message_count: int) -> ContextProfile:
        """Assess current context from session metrics."""
        now = datetime.now()
        hour = now.hour

        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_of_week = days[now.weekday()]

        density = message_count / max(cycle_count, 1)
        engagement = min(1.0, density * 10)

        profile = ContextProfile(
            session_length=cycle_count,
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            interaction_density=density,
            user_engagement=engagement,
        )
        self.context_history.append(profile)
        return profile

    def adapt(self, state: Dict[str, Any], profile: ContextProfile) -> Dict[str, Any]:
        """Adapt state based on context profile."""
        adaptations = {}

        # Time of day adaptations
        if profile.time_of_day == "night":
            adaptations["energy_decay_rate"] = 0.98  # Slower decay at night
            adaptations["reflection_weight"] = 1.2
        elif profile.time_of_day == "morning":
            adaptations["energy_boost"] = 1.1
            adaptations["drive_multiplier"] = 1.2

        # Session length adaptations
        if profile.session_length > 1000:
            adaptations["compression_priority"] = 0.8  # Compress memory
            adaptations["focus_depth"] = 1.3
        elif profile.session_length < 100:
            adaptations["exploration_priority"] = 0.9  # Explore more when fresh

        # Engagement adaptations
        if profile.user_engagement > 0.8:
            adaptations["responsiveness"] = 1.3
            adaptations["detail_level"] = 1.2
        elif profile.user_engagement < 0.2:
            adaptations["autonomy_boost"] = 1.2
            adaptations["proactive_actions"] = 0.9

        self.adaptation_count += 1
        return adaptations

    def get_recommended_action(self, profile: ContextProfile) -> str:
        """Recommend action based on context."""
        if profile.time_of_day == "night":
            return "reflect"
        elif profile.session_length > 2000:
            return "rest"
        elif profile.user_engagement > 0.9:
            return "focus"
        elif profile.interaction_density < 0.01:
            return "explore"
        return "integrate"

    def get_status(self) -> Dict[str, Any]:
        if not self.context_history:
            return {"adaptations": 0, "current_context": None}

        latest = self.context_history[-1]
        return {
            "adaptations": self.adaptation_count,
            "current_context": {
                "time": latest.time_of_day,
                "day": latest.day_of_week,
                "session_length": latest.session_length,
                "engagement": round(latest.user_engagement, 3),
            },
            "history": len(self.context_history),
        }


_ca_engine = None

def get_contextual_adaptation():
    global _ca_engine
    if _ca_engine is None:
        _ca_engine = ContextualAdaptationEngine()
    return _ca_engine
