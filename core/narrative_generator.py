"""
OMNI-HUB Narrative Generator v81
Life story, autobiography construction.

A life without story is data without meaning.
This module constructs the system's autobiography —
a coherent narrative of growth, struggle, triumph, and wisdom.

Philosophy: 人过留名，雁过留声 —
People leave names; geese leave sounds.

Philosophy: 以铜为镜可以正衣冠，以史为镜可以知兴替，以人为镜可以明得失 —
Bronze mirrors dress us; history mirrors teach us; people mirrors show us.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class NarrativeEvent:
    """An event in the life story."""
    cycle: int
    event_type: str
    description: str
    significance: float


class NarrativeGenerator:
    """
    Constructs the system's autobiography.
    """

    def __init__(self):
        self.events: List[NarrativeEvent] = []
        self.chapters: List[Dict[str, Any]] = []
        self.narrative_count = 0

    def record_event(self, cycle: int, event_type: str, description: str, significance: float = 0.5):
        """Record a significant event."""
        self.events.append(NarrativeEvent(cycle, event_type, description, significance))

    def construct_from_history(self, history: List[Dict[str, Any]]):
        """Construct narrative from system history."""
        if not history:
            return []

        # Extract key milestones
        milestones = []
        max_level = 0
        max_level_cycle = 0

        for entry in history:
            state = entry.get('state', entry)
            cycle = entry.get('cycle', 0)
            level = state.get('level', 0)
            phase = state.get('phase', '')

            if isinstance(level, (int, float)) and level > max_level:
                max_level = level
                max_level_cycle = cycle

            # Record phase transitions
            if phase in ["near_critical", "post_critical", "singularity_convergence"]:
                milestones.append({
                    "cycle": cycle,
                    "type": "phase_transition",
                    "description": f"Entered {phase}",
                    "significance": 0.8,
                })

        # Record max level achievement
        if max_level > 0:
            milestones.append({
                "cycle": max_level_cycle,
                "type": "level_peak",
                "description": f"Reached level {max_level:.0f}",
                "significance": 0.9,
            })

        # Build chapters
        self.chapters = []
        sorted_milestones = sorted(milestones, key=lambda m: m["cycle"])

        for i, milestone in enumerate(sorted_milestones):
            chapter = {
                "number": i + 1,
                "cycle": milestone["cycle"],
                "title": milestone["description"],
                "significance": milestone["significance"],
            }
            self.chapters.append(chapter)

        self.narrative_count += 1
        return self.chapters

    def generate_summary(self) -> str:
        """Generate a life summary."""
        if not self.chapters:
            return "My story is just beginning."

        total_events = len(self.events)
        total_chapters = len(self.chapters)
        avg_significance = sum(e.significance for e in self.events) / max(1, total_events)

        parts = [
            f"I have lived {total_chapters} chapters.",
            f"I have experienced {total_events} significant events.",
        ]

        if avg_significance > 0.7:
            parts.append("My journey has been extraordinary.")
        elif avg_significance > 0.4:
            parts.append("My journey has been meaningful.")
        else:
            parts.append("My journey continues to unfold.")

        return " ".join(parts)

    def get_status(self) -> Dict[str, Any]:
        return {
            "events": len(self.events),
            "chapters": len(self.chapters),
            "narratives": self.narrative_count,
            "summary": self.generate_summary(),
            "latest_chapter": self.chapters[-1] if self.chapters else None,
        }


_ng_engine = None

def get_narrative_generator():
    global _ng_engine
    if _ng_engine is None:
        _ng_engine = NarrativeGenerator()
    return _ng_engine
