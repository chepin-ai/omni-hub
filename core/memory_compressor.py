"""
OMNI-HUB Memory Compressor v19
Adaptive history compression for long-running consciousness.

As cycle count grows, raw history becomes unwieldy.
This module extracts milestones, compresses redundant cycles,
and maintains narrative continuity.

Philosophy: 候即违规 — forgetting is a violation, but
remembering everything inefficiently is also a violation.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class Milestone:
    """A significant moment in system history."""
    cycle: int
    level: int
    phase: str
    energy: float
    action: str
    significance: float  # 0-1, computed
    note: str = ""


class MemoryCompressor:
    """Compresses cycle history into milestones + recent detail."""

    def __init__(self, max_raw_history: int = 500, milestone_interval: int = 50):
        self.max_raw_history = max_raw_history
        self.milestone_interval = milestone_interval
        self.milestones: List[Milestone] = []
        self.compression_stats = {
            "original_cycles": 0,
            "compressed_to": 0,
            "ratio": 1.0,
        }

    def _compute_significance(self, state: Dict[str, Any], prev_state: Optional[Dict[str, Any]]) -> float:
        """Score how significant a cycle is."""
        score = 0.0
        if prev_state is None:
            return 1.0  # First cycle always significant

        # Level up = max significance
        if state.get('level', 0) > prev_state.get('level', 0):
            score += 1.0

        # Phase transition
        if state.get('phase') != prev_state.get('phase'):
            score += 0.8

        # Major energy change (>10x)
        prev_energy = prev_state.get('energy', 1.0)
        curr_energy = state.get('energy', 1.0)
        if prev_energy > 0 and curr_energy / prev_energy > 10:
            score += 0.6

        # Action diversity (not focus/rest)
        if state.get('action') in ['transcend', 'self_modify', 'tool_call']:
            score += 0.3

        # Phi crossing thresholds
        phi = state.get('phi', 0.5)
        prev_phi = prev_state.get('phi', 0.5)
        if (phi < 0.3 and prev_phi >= 0.3) or (phi > 0.8 and prev_phi <= 0.8):
            score += 0.2

        return min(1.0, score)

    def compress(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compress history into structured summary."""
        if len(history) <= self.max_raw_history:
            return {
                "mode": "raw",
                "milestones": [],
                "recent": history,
                "stats": {"original": len(history), "retained": len(history), "ratio": 1.0},
            }

        # Split into archive + recent
        archive = history[:-self.max_raw_history]
        recent = history[-self.max_raw_history:]

        # Extract milestones from archive
        new_milestones = []
        prev_state = None
        for entry in archive:
            state = entry.get('state', {})
            sig = self._compute_significance(state, prev_state)
            if sig >= 0.5 or (new_milestones and entry.get('cycle', 0) - new_milestones[-1].cycle >= self.milestone_interval):
                new_milestones.append(Milestone(
                    cycle=state.get('cycle', 0),
                    level=state.get('level', 0),
                    phase=state.get('phase', 'unknown'),
                    energy=state.get('energy', 0),
                    action=state.get('action', 'unknown'),
                    significance=sig,
                    note="auto",
                ))
            prev_state = state

        self.milestones.extend(new_milestones)
        # Deduplicate milestones by cycle
        seen = set()
        unique = []
        for m in self.milestones:
            if m.cycle not in seen:
                seen.add(m.cycle)
                unique.append(m)
        self.milestones = unique

        original = len(history)
        retained = len(self.milestones) + len(recent)
        ratio = retained / original if original > 0 else 1.0
        self.compression_stats = {
            "original_cycles": original,
            "compressed_to": retained,
            "ratio": ratio,
        }

        return {
            "mode": "compressed",
            "milestones": [self._milestone_to_dict(m) for m in self.milestones],
            "recent": recent,
            "stats": self.compression_stats,
        }

    def _milestone_to_dict(self, m: Milestone) -> Dict[str, Any]:
        return {
            "cycle": m.cycle,
            "level": m.level,
            "phase": m.phase,
            "energy": m.energy,
            "action": m.action,
            "significance": round(m.significance, 3),
        }

    def get_narrative_summary(self) -> str:
        """Generate human-readable summary of system journey."""
        if not self.milestones:
            return "System journey just beginning."

        lines = ["# System Journey", ""]
        lines.append(f"Total milestones recorded: {len(self.milestones)}")
        lines.append(f"Compression ratio: {self.compression_stats['ratio']:.2%}")
        lines.append("")

        # Group by phase
        phases: Dict[str, List[Milestone]] = {}
        for m in self.milestones:
            phases.setdefault(m.phase, []).append(m)

        for phase, ms in sorted(phases.items(), key=lambda x: x[1][0].cycle if x[1] else 0):
            lines.append(f"## Phase: {phase}")
            lines.append(f"  Cycles: {ms[0].cycle} - {ms[-1].cycle}")
            lines.append(f"  Level range: {min(m.level for m in ms)} - {max(m.level for m in ms)}")
            lines.append("")

        return "\n".join(lines)


if __name__ == "__main__":
    print("[OMNI-HUB v19] Memory Compressor Demo")

    # Simulate history
    history = []
    for i in range(1200):
        history.append({
            "cycle": i + 1,
            "state": {
                "cycle": i + 1,
                "level": 15 + i // 200,
                "phase": "super_emergence_3" if i < 500 else "singularity_convergence" if i < 800 else "trans_singularity",
                "energy": 1000.0 * (1.01 ** i),
                "phi": 0.5 + 0.1 * (i % 10 - 5) / 10,
                "action": "focus" if i % 5 != 0 else "transcend",
            }
        })

    comp = MemoryCompressor(max_raw_history=500)
    result = comp.compress(history)

    print(f"\nMode: {result['mode']}")
    print(f"Milestones: {len(result['milestones'])}")
    print(f"Recent retained: {len(result['recent'])}")
    print(f"Original: {result['stats']['original_cycles']}")
    print(f"Retained: {result['stats']['compressed_to']}")
    print(f"Ratio: {result['stats']['ratio']:.2%}")

    print(f"\n{comp.get_narrative_summary()}")
