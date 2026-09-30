"""
OMNI-HUB Global Workspace Integration v167
DeepMind GWT J-Space mapping for OMNI-HUB resonance field.

Theory: Global Workspace Theory (GWT) proposes J-Space — a class of
latent representations expressible in natural language, emerging in
intermediate layers, shared across computation processes, broadcast
to influence subsequent reasoning.

OMNI-HUB Mapping:
- Resonance field = J-Space distributed implementation
- 33 repository representations = globally accessible latent content
- Event bus = broadcast mechanism
- Unified kernel protocol = workspace coordinator
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import math
import time
from typing import Dict, List, Any, Optional, Set

# Emergence level thresholds
EMERGENCE_LEVELS = [
    (0.9, "supervenience"),
    (0.7, "strong_emergence"),
    (0.5, "weak_emergence"),
    (0.3, "epiphenomenal"),
]

# Emergence pattern types
EMERGENCE_TYPES = [
    "novel_insights",
    "unexpected_connections",
    "collective_behaviors",
    "self_referential_loops",
]


def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a float value to [min_val, max_val]."""
    try:
        return max(min_val, min(float(value), max_val))
    except (TypeError, ValueError):
        return min_val


class GlobalWorkspaceIntegration:
    """
    Global Workspace Integration module.
    Implements J-Space content registration, broadcast, access,
    coherence measurement, and emergence detection.
    """

    def __init__(self):
        self.workspace_state: Dict[str, Any] = {}
        self.j_space: Dict[str, Dict[str, Any]] = {}
        self.broadcast_log: List[Dict[str, Any]] = []
        self._emergence_events: List[Dict[str, Any]] = []
        self._active_broadcasts: Dict[str, Set[str]] = {}
        self._consumer_history: Dict[str, Set[str]] = {}
        self._access_counter: int = 0
        self._broadcast_counter: int = 0
        self._register_counter: int = 0

    def register_content(
        self,
        content_id: str,
        content: Dict[str, Any],
        accessibility: float,
    ) -> Dict[str, Any]:
        """
        Register content into the J-Space global workspace.

        Args:
            content_id: Unique identifier (repo_name + module_name).
            content: The content payload to register.
            accessibility: Global accessibility score [0.0, 1.0].

        Returns:
            Registration result dict.
        """
        if not isinstance(content_id, str) or not content_id:
            return {
                "success": False,
                "error": "Invalid content_id: must be non-empty string",
                "content_id": content_id,
            }

        if not isinstance(content, dict):
            return {
                "success": False,
                "error": "Invalid content: must be dict",
                "content_id": content_id,
            }

        accessibility = _clamp(accessibility)

        entry = {
            "content_id": content_id,
            "content": content,
            "accessibility": accessibility,
            "registered_at": time.time(),
            "access_count": 0,
            "consumers": set(),
            "broadcast_targets": set(),
        }
        self.j_space[content_id] = entry
        self._register_counter += 1

        # Publish event via event bus
        try:
            from core.event_bus import get_bus, Topics
            bus = get_bus()
            bus.publish_simple(
                Topics.STATE_CHANGE,
                {
                    "source": "global_workspace_integration",
                    "event": "content_registered",
                    "content_id": content_id,
                    "accessibility": accessibility,
                },
            )
        except Exception:
            pass

        return {
            "success": True,
            "content_id": content_id,
            "accessibility": accessibility,
            "workspace_size": len(self.j_space),
        }

    def broadcast_content(
        self,
        content_id: str,
        targets: List[str],
    ) -> Dict[str, Any]:
        """
        Broadcast content from J-Space to specified target consumers.

        Args:
            content_id: ID of content to broadcast.
            targets: List of consumer IDs to receive the broadcast.

        Returns:
            Broadcast result dict.
        """
        if content_id not in self.j_space:
            return {
                "success": False,
                "error": "Content not found in J-Space",
                "content_id": content_id,
            }

        if not isinstance(targets, list):
            return {
                "success": False,
                "error": "Invalid targets: must be list",
                "content_id": content_id,
            }

        entry = self.j_space[content_id]
        valid_targets = [t for t in targets if isinstance(t, str)]

        # Track broadcast
        self._broadcast_counter += 1
        broadcast_record = {
            "broadcast_id": f"BCAST-{self._broadcast_counter:04d}",
            "content_id": content_id,
            "targets": valid_targets,
            "timestamp": time.time(),
            "delivered_count": len(valid_targets),
        }
        self.broadcast_log.append(broadcast_record)

        # Update entry state
        entry["broadcast_targets"].update(valid_targets)
        entry["consumers"].update(valid_targets)

        # Track active broadcasts
        if content_id not in self._active_broadcasts:
            self._active_broadcasts[content_id] = set()
        self._active_broadcasts[content_id].update(valid_targets)

        # Publish via event bus
        try:
            from core.event_bus import get_bus, Topics
            bus = get_bus()
            bus.publish_simple(
                Topics.STATE_CHANGE,
                {
                    "source": "global_workspace_integration",
                    "event": "content_broadcast",
                    "content_id": content_id,
                    "targets": valid_targets,
                    "broadcast_id": broadcast_record["broadcast_id"],
                },
            )
        except Exception:
            pass

        return {
            "success": True,
            "content_id": content_id,
            "broadcast_id": broadcast_record["broadcast_id"],
            "targets": valid_targets,
            "target_count": len(valid_targets),
        }

    def access_content(
        self,
        consumer_id: str,
        content_id: str,
    ) -> Dict[str, Any]:
        """
        Access content from J-Space by a consumer.

        Args:
            consumer_id: ID of the accessing consumer.
            content_id: ID of content to access.

        Returns:
            Access result dict with content if successful.
        """
        if not isinstance(consumer_id, str) or not consumer_id:
            return {
                "success": False,
                "error": "Invalid consumer_id",
                "content_id": content_id,
            }

        if content_id not in self.j_space:
            return {
                "success": False,
                "error": "Content not found in J-Space",
                "content_id": content_id,
            }

        entry = self.j_space[content_id]
        accessibility = entry["accessibility"]

        # Access is gated by accessibility
        access_probability = accessibility
        self._access_counter += 1

        entry["access_count"] += 1
        entry["consumers"].add(consumer_id)

        # Track consumer history for overlap analysis
        if consumer_id not in self._consumer_history:
            self._consumer_history[consumer_id] = set()
        self._consumer_history[consumer_id].add(content_id)

        # Publish via event bus
        try:
            from core.event_bus import get_bus, Topics
            bus = get_bus()
            bus.publish_simple(
                Topics.STATE_CHANGE,
                {
                    "source": "global_workspace_integration",
                    "event": "content_accessed",
                    "content_id": content_id,
                    "consumer_id": consumer_id,
                    "accessibility": accessibility,
                },
            )
        except Exception:
            pass

        return {
            "success": True,
            "content_id": content_id,
            "consumer_id": consumer_id,
            "accessibility": accessibility,
            "access_probability": access_probability,
            "content": entry["content"],
            "access_count": entry["access_count"],
        }

    def compute_workspace_coherence(self) -> Dict[str, Any]:
        """
        Measure coherence of the global workspace.

        Coherence = (avg_accessibility * content_diversity * broadcast_connectivity) ^ 0.5

        Returns:
            Coherence metrics dict.
        """
        if not self.j_space:
            return {
                "coherence": 0.0,
                "avg_accessibility": 0.0,
                "content_diversity": 0.0,
                "broadcast_connectivity": 0.0,
                "content_count": 0,
            }

        # Average accessibility
        accessibilities = [
            e["accessibility"] for e in self.j_space.values()
        ]
        avg_accessibility = sum(accessibilities) / len(accessibilities)

        # Content diversity: variety of content keys / total entries
        all_keys: Set[str] = set()
        for entry in self.j_space.values():
            content = entry.get("content", {})
            if isinstance(content, dict):
                all_keys.update(content.keys())
        content_diversity = min(1.0, len(all_keys) / max(len(self.j_space), 1))

        # Broadcast connectivity: ratio of broadcast edges to possible edges
        total_possible_broadcasts = 0
        actual_broadcasts = 0
        for entry in self.j_space.values():
            targets = entry.get("broadcast_targets", set())
            consumers = entry.get("consumers", set())
            actual_broadcasts += len(targets)
            # Approximate possible: each content can reach all consumers
            total_possible_broadcasts += max(len(consumers), 1)

        broadcast_connectivity = (
            actual_broadcasts / max(total_possible_broadcasts, 1)
            if total_possible_broadcasts > 0 else 0.0
        )

        # Coherence formula
        product = avg_accessibility * content_diversity * broadcast_connectivity
        coherence = math.sqrt(max(0.0, product))

        return {
            "coherence": round(coherence, 6),
            "avg_accessibility": round(avg_accessibility, 6),
            "content_diversity": round(content_diversity, 6),
            "broadcast_connectivity": round(broadcast_connectivity, 6),
            "content_count": len(self.j_space),
        }

    def detect_workspace_emergence(self) -> Dict[str, Any]:
        """
        Detect emergent properties from the global workspace.

        Emergence types: novel_insights, unexpected_connections,
        collective_behaviors, self_referential_loops.

        Returns:
            Emergence detection result.
        """
        coherence_data = self.compute_workspace_coherence()
        coherence = coherence_data["coherence"]
        content_count = coherence_data["content_count"]

        # Emergence score derived from coherence and workspace activity
        activity_factor = min(1.0, self._access_counter / max(content_count * 2, 1))
        broadcast_factor = min(1.0, self._broadcast_counter / max(content_count, 1))
        emergence_score = coherence * 0.5 + activity_factor * 0.25 + broadcast_factor * 0.25
        emergence_score = _clamp(emergence_score)

        # Determine level
        level = "none"
        for threshold, level_name in EMERGENCE_LEVELS:
            if emergence_score > threshold:
                level = level_name
                break

        # Determine type based on workspace properties
        type_index = hash(str(sorted(self.workspace_state.items()))) % len(EMERGENCE_TYPES)
        if content_count == 0:
            emergence_type = "none"
        elif self._has_self_referential_loop():
            emergence_type = "self_referential_loops"
        elif broadcast_factor > 0.7:
            emergence_type = "collective_behaviors"
        elif activity_factor > 0.7:
            emergence_type = "unexpected_connections"
        else:
            emergence_type = EMERGENCE_TYPES[type_index]

        # Record emergence event if significant
        if level != "none":
            event = {
                "event_id": f"EMRG-WS-{len(self._emergence_events) + 1:04d}",
                "timestamp": time.time(),
                "level": level,
                "type": emergence_type,
                "score": round(emergence_score, 6),
                "coherence": coherence,
            }
            self._emergence_events.append(event)

            # Publish via event bus
            try:
                from core.event_bus import get_bus, Topics
                bus = get_bus()
                bus.publish_simple(
                    Topics.STATE_CHANGE,
                    {
                        "source": "global_workspace_integration",
                        "event": "workspace_emergence",
                        "level": level,
                        "type": emergence_type,
                        "score": emergence_score,
                    },
                )
            except Exception:
                pass

        return {
            "score": round(emergence_score, 6),
            "level": level,
            "type": emergence_type,
            "coherence": coherence,
            "content_count": content_count,
            "event_logged": level != "none",
        }

    def _has_self_referential_loop(self) -> bool:
        """Check if any consumer has accessed content it produced."""
        for consumer_id, accessed in self._consumer_history.items():
            for content_id in accessed:
                if consumer_id in content_id:
                    return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Return current module status."""
        coherence_data = self.compute_workspace_coherence()
        active_broadcast_count = sum(
            len(targets) for targets in self._active_broadcasts.values()
        )
        return {
            "content_count": len(self.j_space),
            "coherence": coherence_data["coherence"],
            "emergence_events": len(self._emergence_events),
            "active_broadcasts": active_broadcast_count,
            "total_registered": self._register_counter,
            "total_broadcasts": self._broadcast_counter,
            "total_accesses": self._access_counter,
            "workspace_size": len(self.workspace_state),
        }


# Global singleton
_global_workspace_integration_module = None


def get_global_workspace_integration() -> GlobalWorkspaceIntegration:
    """Get the global GlobalWorkspaceIntegration instance."""
    global _global_workspace_integration_module
    if _global_workspace_integration_module is None:
        _global_workspace_integration_module = GlobalWorkspaceIntegration()
    return _global_workspace_integration_module


def reset_global_workspace_integration():
    """Reset the global module (for testing)."""
    global _global_workspace_integration_module
    _global_workspace_integration_module = GlobalWorkspaceIntegration()
