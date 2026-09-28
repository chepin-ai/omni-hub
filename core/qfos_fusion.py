"""
QF-OS Fusion (QF-OS融合) — OMNI-HUB Module v161

Deep fusion of chepin-ai's Quantum Field Operating System (qfos-autonomous-engine)
into OMNI-HUB. Extracts the autonomous navigation engine's core patterns
(perception → decision → execution → feedback → evolution) and translates them
into OMNI-HUB native kernel-level capabilities.

QF-OS is no longer an external repository — it becomes an OMNI-HUB kernel extension.
"""

import json
import os
from typing import Dict, Any, Optional, List

# ---------------------------------------------------------------------------
# Simulated QF-OS core patterns (perception → decision → execution → feedback → evolution)
# ---------------------------------------------------------------------------
DEFAULT_QFOS_PATTERNS: Dict[str, Dict[str, Any]] = {
    "perception_loop": {
        "type": "sensor_fusion",
        "inputs": ["lidar", "camera", "gps"],
        "frequency": "realtime",
    },
    "decision_graph": {
        "type": "neural_policy",
        "layers": 12,
        "activation": "swish",
    },
    "execution_engine": {
        "type": "motor_control",
        "precision": 0.001,
        "latency_ms": 5,
    },
    "feedback_mechanism": {
        "type": "slam_loop",
        "convergence_rate": 0.98,
    },
    "evolution_protocol": {
        "type": "meta_learning",
        "adaptation_speed": "fast",
    },
}

# Valid pattern types for extraction
VALID_PATTERN_TYPES: List[str] = list(DEFAULT_QFOS_PATTERNS.keys())

# Fusion level thresholds
FUSION_LEVELS = [
    (0.9, "merged"),
    (0.7, "fused"),
    (0.5, "linked"),
    (0.3, "connected"),
]

# Alliance repos data path (for loading QF-OS metadata)
DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "alliance_repos.json",
)

# Global singleton instance
_module: Optional["QFOSFusion"] = None


def get_qfos_fusion(
    fusion_state: Optional[Dict[str, Any]] = None,
    qfos_patterns: Optional[Dict[str, Any]] = None,
) -> "QFOSFusion":
    """Return the global QFOSFusion singleton."""
    global _module
    if _module is None:
        _module = QFOSFusion(
            fusion_state=fusion_state,
            qfos_patterns=qfos_patterns,
        )
    return _module


class QFOSFusion:
    """
    QF-OS Fusion engine.

    Establishes deep fusion between OMNI-HUB and QF-OS (Quantum Field Operating
    System), extracting and translating QF-OS autonomous navigation patterns into
    OMNI-HUB native kernel capabilities.
    """

    def __init__(
        self,
        fusion_state: Optional[Dict[str, Any]] = None,
        qfos_patterns: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialise the QFOSFusion instance.

        Args:
            fusion_state: Optional initial fusion state dictionary.
            qfos_patterns: Optional override for QF-OS pattern definitions.
        """
        self._fusion_state: Dict[str, Any] = fusion_state or {
            "fusion_score": 0.0,
            "active": False,
        }
        self._qfos_patterns: Dict[str, Any] = qfos_patterns or dict(
            DEFAULT_QFOS_PATTERNS
        )
        self._extracted_patterns: Dict[str, Dict[str, Any]] = {}
        self._translation_count: int = 0
        self._fusion_level: str = "detached"
        self._qfos_metadata: Dict[str, Any] = {}
        self._load_qfos_metadata()

    def _load_qfos_metadata(self) -> None:
        """Load QF-OS metadata from alliance_repos.json if available."""
        try:
            if os.path.exists(DEFAULT_DATA_PATH):
                with open(DEFAULT_DATA_PATH, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                other = data.get("alliance_other", {})
                if "qfos-autonomous-engine" in other:
                    self._qfos_metadata = other["qfos-autonomous-engine"]
        except Exception:
            # Defensive: silently skip if file is missing or malformed
            self._qfos_metadata = {}

    def _compute_fusion_level(self, score: float) -> str:
        """Map a fusion score [0.0, 1.0] to a named fusion level."""
        for threshold, level in FUSION_LEVELS:
            if score >= threshold:
                return level
        return "detached"

    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit an event to the OMNI-HUB event bus if available."""
        try:
            # Attempt lazy import of event bus (may not exist in all environments)
            from core.event_bus import get_event_bus  # type: ignore

            bus = get_event_bus()
            bus.emit(event_type, payload)
        except Exception:
            # Defensive: event bus is optional
            pass

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def fuse_with_qfos(self) -> Dict[str, Any]:
        """
        Establish deep fusion with QF-OS and extract its core patterns.

        Returns:
            Dict containing extracted patterns, fusion score, and metadata.
        """
        self._extracted_patterns = {}
        for name, pattern in self._qfos_patterns.items():
            self._extracted_patterns[name] = dict(pattern)

        # Fusion score is proportional to how many patterns were extracted
        total = len(self._qfos_patterns)
        extracted = len(self._extracted_patterns)
        score = extracted / total if total > 0 else 0.0
        self._fusion_state["fusion_score"] = round(score, 4)
        self._fusion_level = self._compute_fusion_level(score)

        result = {
            "status": "fusion_complete",
            "extracted_patterns": list(self._extracted_patterns.keys()),
            "fusion_score": self._fusion_state["fusion_score"],
            "fusion_level": self._fusion_level,
            "qfos_metadata": self._qfos_metadata,
        }

        self._emit_event("qfos.fusion.complete", result)
        return result

    def extract_navigation_pattern(self, pattern_type: str) -> Dict[str, Any]:
        """
        Extract a specific navigation pattern from QF-OS.

        Args:
            pattern_type: One of the five QF-OS pattern keys.

        Returns:
            Dict with the pattern details or an error dict if invalid.
        """
        if pattern_type not in VALID_PATTERN_TYPES:
            return {
                "error": f"Unknown pattern_type '{pattern_type}'. "
                f"Valid: {VALID_PATTERN_TYPES}",
                "pattern_type": pattern_type,
            }

        pattern = self._qfos_patterns.get(pattern_type, {})
        extracted = dict(pattern)
        self._extracted_patterns[pattern_type] = extracted

        result = {
            "pattern_type": pattern_type,
            "pattern": extracted,
            "extracted_at": "fusion_layer",
        }

        self._emit_event("qfos.pattern.extracted", result)
        return result

    def translate_to_omni_hub(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate a QF-OS pattern into an OMNI-HUB compatible format.

        Args:
            pattern: A QF-OS pattern dictionary (must contain 'type' key).

        Returns:
            Dict with the translated OMNI-HUB module specification.
        """
        if not isinstance(pattern, dict):
            return {
                "error": "Pattern must be a dictionary",
                "pattern": pattern,
            }

        pattern_type_key = pattern.get("type", "unknown")

        # Map QF-OS pattern types to OMNI-HUB kernel capabilities
        omni_hub_mapping: Dict[str, str] = {
            "sensor_fusion": "kernel.perception",
            "neural_policy": "kernel.decision",
            "motor_control": "kernel.execution",
            "slam_loop": "kernel.feedback",
            "meta_learning": "kernel.evolution",
        }

        omni_capability = omni_hub_mapping.get(pattern_type_key, "kernel.unknown")

        translated = {
            "source": "qfos",
            "target": "omni_hub",
            "original_pattern": dict(pattern),
            "omni_hub_capability": omni_capability,
            "integration_layer": "kernel_extension",
            "native": True,
            "translated_at": "fusion_layer",
        }

        self._translation_count += 1
        self._emit_event("qfos.pattern.translated", translated)
        return translated

    def activate_fusion_mode(self) -> Dict[str, Any]:
        """
        Activate full fusion mode — QF-OS capabilities become OMNI-HUB native.

        Returns:
            Dict with activation status and capability manifest.
        """
        # Ensure patterns have been extracted
        if not self._extracted_patterns:
            self.fuse_with_qfos()

        # Build capability manifest
        capabilities = []
        for name, pattern in self._extracted_patterns.items():
            translated = self.translate_to_omni_hub(pattern)
            capabilities.append(
                {
                    "pattern": name,
                    "capability": translated.get("omni_hub_capability", "unknown"),
                    "native": True,
                }
            )

        # Recompute fusion level after translation
        score = self._fusion_state.get("fusion_score", 0.0)
        if self._translation_count >= len(self._qfos_patterns):
            score = min(1.0, score + 0.15)
            self._fusion_state["fusion_score"] = round(score, 4)

        self._fusion_level = self._compute_fusion_level(score)
        self._fusion_state["active"] = True

        result = {
            "status": "activated",
            "fusion_level": self._fusion_level,
            "fusion_score": self._fusion_state["fusion_score"],
            "capabilities": capabilities,
            "native_integration": True,
        }

        self._emit_event("qfos.fusion.activated", result)
        return result

    def get_status(self) -> Dict[str, Any]:
        """
        Return the current fusion status.

        Returns:
            Dict with fusion_level, extracted_patterns, translation_count, active.
        """
        return {
            "fusion_level": self._fusion_level,
            "extracted_patterns": list(self._extracted_patterns.keys()),
            "translation_count": self._translation_count,
            "active": self._fusion_state.get("active", False),
            "fusion_score": self._fusion_state.get("fusion_score", 0.0),
        }
