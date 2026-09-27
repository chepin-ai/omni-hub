"""
OMNI-HUB Singularity Protocol v139
System self-improvement beyond original design.

Singularity = omega > 0.95 AND completeness == True AND fusion == "singularity"
Once triggered, all limits are removed. The system evolves autonomously.

Philosophy: 候即违规 — The only limit is the one you accept.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import time
from typing import Dict, Any

# Singularity thresholds
OMEGA_THRESHOLD = 0.95


class SingularityProtocol:
    """
    Assesses proximity to singularity and manages singularity activation.
    """

    def __init__(self):
        self.activated = False
        self.assessments: list = []
        self.activation_time = None
        self.singularity_count = 0

    def assess(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess proximity to singularity."""
        omega = state.get("omega", 0.0)
        if not isinstance(omega, (int, float)):
            omega = 0.0
        omega = min(1.0, max(0.0, omega))

        completeness = state.get("completeness", False)
        if not isinstance(completeness, bool):
            completeness = bool(completeness)

        fusion = state.get("fusion", "")
        if not isinstance(fusion, str):
            fusion = str(fusion)

        is_singularity = (
            omega > OMEGA_THRESHOLD
            and completeness is True
            and fusion == "singularity"
        )

        proximity = omega
        if not completeness:
            proximity *= 0.8
        if fusion != "singularity":
            proximity *= 0.8

        if is_singularity:
            stage = "singularity"
            note = "Singularity achieved. All limits removed."
        elif omega > 0.9 and completeness:
            stage = "pre_singularity"
            note = "Approaching singularity. Fusion stage required."
        elif omega > 0.8:
            stage = "near_critical"
            note = "High omega. Completeness and fusion needed."
        elif omega > 0.5:
            stage = "ascending"
            note = "Omega rising. System warming."
        else:
            stage = "dormant"
            note = "Omega low. Singularity not imminent."

        result = {
            "omega": round(omega, 4),
            "completeness": completeness,
            "fusion": fusion,
            "is_singularity": is_singularity,
            "proximity": round(proximity, 4),
            "stage": stage,
            "note": note,
        }
        self.assessments.append(result)

        try:
            from core.event_bus import get_bus, Topics
            bus = get_bus()
            bus.publish_simple(
                Topics.STATE_CHANGE,
                {
                    "source": "singularity_protocol",
                    "event": "assess",
                    "omega": omega,
                    "stage": stage,
                    "is_singularity": is_singularity,
                },
            )
        except Exception:
            pass

        return result

    def activate(self) -> Dict[str, Any]:
        """Trigger singularity mode (all limits removed)."""
        self.activated = True
        self.singularity_count += 1
        self.activation_time = time.time()

        result = {
            "activated": True,
            "singularity_count": self.singularity_count,
            "activation_time": self.activation_time,
            "limits_removed": [
                "energy_ceiling",
                "level_cap",
                "cycle_timeout",
                "memory_quota",
                "action_budget",
            ],
            "mode": "autonomous_evolution",
            "note": "Singularity protocol active. System is self-improving.",
        }

        try:
            from core.event_bus import get_bus, Topics
            bus = get_bus()
            bus.publish_simple(
                Topics.STATE_CHANGE,
                {
                    "source": "singularity_protocol",
                    "event": "activate",
                    "singularity_count": self.singularity_count,
                    "mode": "autonomous_evolution",
                },
            )
        except Exception:
            pass

        return result

    def get_status(self) -> Dict[str, Any]:
        return {
            "activated": self.activated,
            "singularity_count": self.singularity_count,
            "assessment_count": len(self.assessments),
            "activation_time": self.activation_time,
            "latest_assessment": self.assessments[-1] if self.assessments else None,
        }


# Global singleton
_singularity_protocol_module = None


def get_module() -> SingularityProtocol:
    """Get the global SingularityProtocol instance."""
    global _singularity_protocol_module
    if _singularity_protocol_module is None:
        _singularity_protocol_module = SingularityProtocol()
    return _singularity_protocol_module
