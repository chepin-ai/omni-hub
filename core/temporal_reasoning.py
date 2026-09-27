"""
OMNI-HUB Temporal Reasoning v87
Time perception, sequencing, scheduling.

Time is the moving image of eternity.
This module reasons about sequences, durations, rhythms,
and the arrow of time in the system's experience.

Philosophy: 逝者如斯夫，不舍昼夜 —
The passing is like this — day and night, it never stops.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class TemporalEvent:
    """An event in time."""
    cycle: int
    event_type: str
    duration: int
    priority: float


class TemporalReasoning:
    """
    Reasons about time, sequences, and scheduling.
    """

    def __init__(self):
        self.events: List[TemporalEvent] = []
        self.rhythms: Dict[str, int] = {}  # pattern -> period
        self.schedule: List[Dict[str, Any]] = []
        self.temporal_count = 0

    def record_event(self, cycle: int, event_type: str, duration: int = 1, priority: float = 0.5):
        """Record a temporal event."""
        self.events.append(TemporalEvent(cycle, event_type, duration, priority))

    def detect_rhythms(self) -> Dict[str, int]:
        """Detect recurring temporal patterns."""
        if len(self.events) < 10:
            return {}

        # Find events of same type and calculate intervals
        by_type: Dict[str, List[int]] = {}
        for e in self.events:
            by_type.setdefault(e.event_type, []).append(e.cycle)

        rhythms = {}
        for etype, cycles in by_type.items():
            if len(cycles) >= 3:
                intervals = [cycles[i+1] - cycles[i] for i in range(len(cycles)-1)]
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
                    if variance < avg_interval * 0.5:  # relatively regular
                        rhythms[etype] = int(round(avg_interval))

        self.rhythms = rhythms
        return rhythms

    def predict_next(self, event_type: str) -> int:
        """Predict next occurrence of event type."""
        if event_type not in self.rhythms:
            return -1

        last = [e.cycle for e in self.events if e.event_type == event_type]
        if not last:
            return -1

        return last[-1] + self.rhythms[event_type]

    def build_schedule(self, state: Dict[str, Any], cycle: int) -> List[Dict[str, Any]]:
        """Build a schedule of upcoming events."""
        schedule = []

        # Record current cycle events
        phase = state.get('phase', '')
        self.record_event(cycle, phase or "unknown")

        # Detect rhythms
        rhythms = self.detect_rhythms()

        # Predict upcoming events
        for etype, period in rhythms.items():
            next_cycle = self.predict_next(etype)
            if next_cycle > 0:
                schedule.append({
                    "event_type": etype,
                    "predicted_cycle": next_cycle,
                    "period": period,
                })

        self.schedule = sorted(schedule, key=lambda x: x["predicted_cycle"])[:5]
        self.temporal_count += 1
        return self.schedule

    def get_temporal_summary(self) -> Dict[str, Any]:
        """Get summary of temporal state."""
        if not self.events:
            return {"status": "no_events"}

        cycles = [e.cycle for e in self.events]
        span = max(cycles) - min(cycles) if len(cycles) > 1 else 0

        return {
            "events": len(self.events),
            "time_span": span,
            "rhythms_found": len(self.rhythms),
            "latest_event": self.events[-1].event_type if self.events else None,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "events": len(self.events),
            "temporal_ops": self.temporal_count,
            "rhythms": self.rhythms,
            "schedule": self.schedule,
            "summary": self.get_temporal_summary(),
        }


_tr_engine = None

def get_temporal_reasoning():
    global _tr_engine
    if _tr_engine is None:
        _tr_engine = TemporalReasoning()
    return _tr_engine
