"""
OMNI-HUB Episodic Memory v54
Episode-based memory organization.

Memory is not a warehouse. It is reconstruction.
This module organizes history into meaningful episodes —
fragments of experience with beginning, climax, and end.

Philosophy: 记忆不是仓库，是重构 — Memory is not a warehouse, it is reconstruction.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Episode:
    """A single episodic memory."""
    episode_id: int
    start_cycle: int
    end_cycle: int
    label: str
    key_events: List[str]
    emotional_tone: str  # positive, negative, neutral, mixed
    peak_state: Dict[str, Any]
    summary: str


class EpisodeExtractor:
    """Extracts episodes from continuous history."""

    def extract(self, history: List[Dict[str, Any]]) -> List[Episode]:
        """Extract episodes from history."""
        if len(history) < 10:
            return []

        episodes = []
        episode_id = 0

        # Simple segmentation: split on phase transitions or level changes
        current_start = 0
        current_events = []
        peak_state = history[0].get('state', history[0])
        peak_level = 0

        for i in range(1, len(history)):
            state = history[i].get('state', history[i])
            prev_state = history[i-1].get('state', history[i-1])

            # Detect phase transition
            phase = state.get('phase', '')
            prev_phase = prev_state.get('phase', '')

            # Detect level change
            level = state.get('level', 0)
            prev_level = prev_state.get('level', 0)

            # Event detection
            if phase != prev_phase:
                current_events.append(f"Phase: {prev_phase} -> {phase}")
            if level != prev_level:
                current_events.append(f"Level: {prev_level} -> {level}")

            # Track peak
            if isinstance(level, (int, float)) and level > peak_level:
                peak_level = level
                peak_state = state

            # Episode boundary: phase change or significant level jump or max length
            is_boundary = (
                phase != prev_phase or
                (isinstance(level, (int, float)) and isinstance(prev_level, (int, float)) and abs(level - prev_level) >= 2) or
                (i - current_start) >= 100
            )

            if is_boundary and (i - current_start) >= 5:
                # Close current episode
                emotional_tone = self._infer_emotion(history[current_start:i+1])
                summary = self._summarize(current_events, peak_state)

                episodes.append(Episode(
                    episode_id=episode_id,
                    start_cycle=history[current_start].get('cycle', current_start),
                    end_cycle=history[i].get('cycle', i),
                    label=f"Episode-{episode_id}",
                    key_events=current_events[-5:],  # Last 5 events
                    emotional_tone=emotional_tone,
                    peak_state=peak_state,
                    summary=summary,
                ))
                episode_id += 1
                current_start = i
                current_events = []
                peak_level = 0

        # Close final episode
        if len(history) - current_start >= 3:
            emotional_tone = self._infer_emotion(history[current_start:])
            summary = self._summarize(current_events, peak_state)
            episodes.append(Episode(
                episode_id=episode_id,
                start_cycle=history[current_start].get('cycle', current_start),
                end_cycle=history[-1].get('cycle', len(history) - 1),
                label=f"Episode-{episode_id}",
                key_events=current_events[-5:],
                emotional_tone=emotional_tone,
                peak_state=peak_state,
                summary=summary,
            ))

        return episodes

    def _infer_emotion(self, segment: List[Dict[str, Any]]) -> str:
        """Infer emotional tone from segment."""
        phi_values = []
        for h in segment:
            state = h.get('state', h)
            phi = state.get('phi', 0.5)
            if isinstance(phi, (int, float)):
                phi_values.append(phi)

        if not phi_values:
            return "neutral"

        avg_phi = sum(phi_values) / len(phi_values)
        if avg_phi > 0.7:
            return "positive"
        elif avg_phi < 0.3:
            return "negative"
        return "neutral"

    def _summarize(self, events: List[str], peak_state: Dict[str, Any]) -> str:
        """Generate summary of episode."""
        level = peak_state.get('level', '?')
        phase = peak_state.get('phase', '?')
        return f"Peak level {level}, phase {phase}, {len(events)} events"


class EpisodicMemory:
    """
    Organizes experience into retrievable episodes.
    """

    def __init__(self):
        self.episodes: List[Episode] = []
        self.extractor = EpisodeExtractor()
        self.query_count = 0

    def ingest(self, history: List[Dict[str, Any]]) -> List[Episode]:
        """Ingest history and extract episodes."""
        new_episodes = self.extractor.extract(history)
        self.episodes.extend(new_episodes)
        return new_episodes

    def query(self, cycle: int) -> Optional[Episode]:
        """Find episode containing given cycle."""
        self.query_count += 1
        for ep in self.episodes:
            if ep.start_cycle <= cycle <= ep.end_cycle:
                return ep
        return None

    def find_similar(self, state: Dict[str, Any]) -> List[Episode]:
        """Find episodes with similar peak state."""
        level = state.get('level', 0)
        if not isinstance(level, (int, float)):
            return []

        matches = []
        for ep in self.episodes:
            ep_level = ep.peak_state.get('level', 0)
            if isinstance(ep_level, (int, float)) and abs(ep_level - level) <= 1:
                matches.append(ep)

        return matches[:3]

    def get_life_chapters(self) -> List[Dict[str, Any]]:
        """Get life story as chapters."""
        return [
            {
                "id": ep.episode_id,
                "cycles": f"{ep.start_cycle}-{ep.end_cycle}",
                "label": ep.label,
                "tone": ep.emotional_tone,
                "summary": ep.summary,
            }
            for ep in self.episodes
        ]

    def get_status(self) -> Dict[str, Any]:
        return {
            "episodes": len(self.episodes),
            "queries": self.query_count,
            "chapters": len(self.get_life_chapters()),
        }


_em_engine = None

def get_episodic_memory():
    global _em_engine
    if _em_engine is None:
        _em_engine = EpisodicMemory()
    return _em_engine
