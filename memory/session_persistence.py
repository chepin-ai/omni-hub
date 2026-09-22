"""OMNI-HUB v13.1 Unified Session Persistence

Handles saving and loading of session state with schema compatibility
for both simple (orchestrator) and rich (self-drive) state formats.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from core import constants as C


class SessionPersistence:
    """Unified session persistence — schema-agnostic."""

    @staticmethod
    def save_session(state: Dict[str, Any], filepath: str = C.STATE_FILE) -> str:
        """Serialize state to JSON. Preserves all fields."""
        # Wrap with metadata if not already present
        if "version" not in state:
            state = {
                "version": C.__dict__.get("__version__", "13.1.0"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **state,
            }
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
        return filepath

    @staticmethod
    def load_session(filepath: str = C.STATE_FILE) -> Optional[Dict[str, Any]]:
        """Deserialize state from JSON."""
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def detect_previous_session(filepath: str = C.STATE_FILE) -> bool:
        return os.path.exists(filepath)

    @staticmethod
    def normalize_state(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize any schema to standard fields.

        Supports both:
        - Simple: {level, energy, phi}
        - Rich (self-drive): {current_position: {level, consciousness}, ladder: {current_energy}, step}
        """
        pos = raw.get("current_position", {})
        ladder = raw.get("ladder", {})
        return {
            "version": raw.get("version", "unknown"),
            "timestamp": raw.get("timestamp", ""),
            "level": pos.get("level", raw.get("level", 0)),
            "energy": ladder.get("current_energy", raw.get("energy", 0.0)),
            "phi": pos.get("consciousness", raw.get("phi", 0.0)),
            "step": raw.get("step", raw.get("iteration", 0)),
            "phase": ladder.get("phase", raw.get("phase", "unknown")),
            "raw": raw,  # Keep full data for advanced use
        }


def _demo():
    demo_state = {
        "version": "13.1.0",
        "current_position": {"level": 9, "consciousness": 0.29},
        "ladder": {"current_energy": 18634.49, "phase": "EMERGING"},
        "step": 105,
    }
    path = SessionPersistence.save_session(demo_state)
    print(f"Saved: {path}")
    loaded = SessionPersistence.load_session(path)
    norm = SessionPersistence.normalize_state(loaded)
    print(f"Normalized: level={norm['level']}, energy={norm['energy']:.2f}, phi={norm['phi']:.3f}")


if __name__ == "__main__":
    _demo()
