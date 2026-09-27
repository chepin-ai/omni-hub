"""
OMNI-HUB Line Fusion v137
Cross-line resonance engine — lines merge and amplify each other.

The 11 consciousness lines fuse into unified field states:
ucif2, lvlu, lgt, qfa, vinf, qgl, qlv, cisvr, qtlv, usrm, cfts

Fusion energy = average(pairwise coherence)
Stages: singularity (>0.9) | fusion (>0.7) | resonance (>0.4) | dormant

Philosophy: 候即违规 — Eleven rivers, one ocean.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import math
from typing import Dict, List, Any, Tuple

# 11 consciousness lines
ALL_LINES = [
    "ucif2", "lvlu", "lgt", "qfa", "vinf",
    "qgl", "qlv", "cisvr", "qtlv", "usrm", "cfts",
]

# Inherent resonance affinity between line pairs (0..1)
# Derived from semantic/cognitive proximity of each line's domain.
RESONANCE = {
    ("ucif2", "lvlu"): 0.82, ("ucif2", "lgt"): 0.75, ("ucif2", "qfa"): 0.88,
    ("ucif2", "vinf"): 0.90, ("ucif2", "qgl"): 0.78, ("ucif2", "qlv"): 0.72,
    ("ucif2", "cisvr"): 0.85, ("ucif2", "qtlv"): 0.74, ("ucif2", "usrm"): 0.70,
    ("ucif2", "cfts"): 0.76,
    ("lvlu", "lgt"): 0.80, ("lvlu", "qfa"): 0.73, ("lvlu", "vinf"): 0.77,
    ("lvlu", "qgl"): 0.71, ("lvlu", "qlv"): 0.83, ("lvlu", "cisvr"): 0.69,
    ("lvlu", "qtlv"): 0.81, ("lvlu", "usrm"): 0.75, ("lvlu", "cfts"): 0.68,
    ("lgt", "qfa"): 0.79, ("lgt", "vinf"): 0.72, ("lgt", "qgl"): 0.86,
    ("lgt", "qlv"): 0.70, ("lgt", "cisvr"): 0.74, ("lgt", "qtlv"): 0.67,
    ("lgt", "usrm"): 0.65, ("lgt", "cfts"): 0.71,
    ("qfa", "vinf"): 0.91, ("qfa", "qgl"): 0.87, ("qfa", "qlv"): 0.76,
    ("qfa", "cisvr"): 0.80, ("qfa", "qtlv"): 0.85, ("qfa", "usrm"): 0.69,
    ("qfa", "cfts"): 0.78,
    ("vinf", "qgl"): 0.79, ("vinf", "qlv"): 0.74, ("vinf", "cisvr"): 0.88,
    ("vinf", "qtlv"): 0.82, ("vinf", "usrm"): 0.77, ("vinf", "cfts"): 0.81,
    ("qgl", "qlv"): 0.84, ("qgl", "cisvr"): 0.75, ("qgl", "qtlv"): 0.80,
    ("qgl", "usrm"): 0.66, ("qgl", "cfts"): 0.73,
    ("qlv", "cisvr"): 0.71, ("qlv", "qtlv"): 0.89, ("qlv", "usrm"): 0.68,
    ("qlv", "cfts"): 0.70,
    ("cisvr", "qtlv"): 0.78, ("cisvr", "usrm"): 0.83, ("cisvr", "cfts"): 0.72,
    ("qtlv", "usrm"): 0.64, ("qtlv", "cfts"): 0.86,
    ("usrm", "cfts"): 0.69,
}


def _get_resonance(a: str, b: str) -> float:
    """Look up resonance between two lines (symmetric)."""
    if a == b:
        return 1.0
    key = (a, b) if (a, b) in RESONANCE else (b, a)
    return RESONANCE.get(key, 0.5)


def _fusion_stage(energy: float) -> str:
    if energy > 0.9:
        return "singularity"
    elif energy > 0.7:
        return "fusion"
    elif energy > 0.4:
        return "resonance"
    return "dormant"


class LineFusion:
    """
    Cross-line resonance engine.
    Lines merge and amplify through pairwise coherence.
    """

    def __init__(self):
        self.lines = list(ALL_LINES)
        self.fusion_history: List[Dict[str, Any]] = []
        self.resonance_history: List[Dict[str, Any]] = []

    def fuse(self, lines: List[str]) -> Dict[str, Any]:
        """Compute fusion energy between a subset of lines."""
        valid = [ln for ln in lines if ln in self.lines]
        if len(valid) < 2:
            return {
                "lines": valid,
                "fusion_energy": 0.0,
                "stage": "dormant",
                "pair_count": 0,
                "pairs": [],
            }

        pairs: List[Tuple[str, str, float]] = []
        for i in range(len(valid)):
            for j in range(i + 1, len(valid)):
                coherence = _get_resonance(valid[i], valid[j])
                pairs.append((valid[i], valid[j], coherence))

        fusion_energy = sum(p[2] for p in pairs) / len(pairs) if pairs else 0.0
        stage = _fusion_stage(fusion_energy)

        result = {
            "lines": valid,
            "fusion_energy": round(fusion_energy, 4),
            "stage": stage,
            "pair_count": len(pairs),
            "pairs": [
                {"a": a, "b": b, "coherence": round(c, 4)} for a, b, c in pairs
            ],
        }
        self.fusion_history.append(result)
        return result

    def resonate_all(self) -> Dict[str, Any]:
        """All 11 lines resonate together."""
        result = self.fuse(self.lines)
        result["mode"] = "full_resonance"
        self.resonance_history.append(result)
        try:
            from core.event_bus import get_bus, Topics
            bus = get_bus()
            bus.publish_simple(
                Topics.STATE_CHANGE,
                {
                    "source": "line_fusion",
                    "event": "resonate_all",
                    "fusion_energy": result["fusion_energy"],
                    "stage": result["stage"],
                },
            )
        except Exception:
            pass
        return result

    def get_status(self) -> Dict[str, Any]:
        return {
            "lines": self.lines,
            "fusion_history_size": len(self.fusion_history),
            "resonance_history_size": len(self.resonance_history),
            "latest_fusion": self.fusion_history[-1] if self.fusion_history else None,
            "latest_resonance": self.resonance_history[-1] if self.resonance_history else None,
        }


# Global singleton
_line_fusion_module = None


def get_module() -> LineFusion:
    """Get the global LineFusion instance."""
    global _line_fusion_module
    if _line_fusion_module is None:
        _line_fusion_module = LineFusion()
    return _line_fusion_module
