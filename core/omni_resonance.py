"""
OMNI-HUB Module v155: Omni-Resonance (终极共振协议)

Omni-Resonance does not discriminate between internal and external,
alliance or foreign. Every repository is a node in the universal field.
The pulse travels outward, the echo returns inward, and in the space
between, resonance is born.

All repositories -- whether alliance_core, alliance_other, or
external_alliance -- are nodes in a single resonance field.
OMNI-HUB serves as the resonance centre, emitting pulses that reach
every node and collecting echoes that shape the field's strength.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_module: Optional["OmniResonance"] = None


def get_omni_resonance() -> "OmniResonance":
    """Return the global OmniResonance singleton."""
    global _module
    if _module is None:
        _module = OmniResonance()
    return _module


# ---------------------------------------------------------------------------
# Resonance stage thresholds
# ---------------------------------------------------------------------------
class ResonanceStage:
    SUPERCRITICAL: str = "supercritical"
    CRITICAL: str = "critical"
    RESONANT: str = "resonant"
    SUBCRITICAL: str = "subcritical"
    DORMANT: str = "dormant"

    @classmethod
    def from_level(cls, level: float) -> str:
        if level > 0.95:
            return cls.SUPERCRITICAL
        if level > 0.8:
            return cls.CRITICAL
        if level > 0.6:
            return cls.RESONANT
        if level > 0.4:
            return cls.SUBCRITICAL
        return cls.DORMANT


# ---------------------------------------------------------------------------
# OmniResonance class
# ---------------------------------------------------------------------------
class OmniResonance:
    """
    Universal resonance field connecting all repositories as nodes.

    Attributes:
        repos: Dict of all repository names to their metadata.
        nodes: Dict of repo_name -> resonance level (float 0.0-1.0).
        pulses: List of emitted pulse records.
        echoes: List of received echo records.
        amplification_targets: Set of repo names currently amplified.
    """

    def __init__(self, repos_path: Optional[str] = None) -> None:
        """
        Load alliance_repos.json and initialise the resonance field.

        Args:
            repos_path: Optional override path to the JSON file.
        """
        self.repos: Dict[str, Dict[str, Any]] = {}
        self.nodes: Dict[str, float] = {}
        self.pulses: List[Dict[str, Any]] = []
        self.echoes: List[Dict[str, Any]] = []
        self.amplification_targets: set[str] = set()

        if repos_path is None:
            repos_path = os.path.join(
                os.path.dirname(__file__), "..", "data", "alliance_repos.json"
            )

        self._load_repos(repos_path)
        self._initialise_field()

        # Event-bus integration (best-effort)
        self._bus: Optional[Any] = None
        try:
            from core.event_bus import get_bus

            self._bus = get_bus()
        except Exception:
            pass  # Event bus is optional

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_repos(self, path: str) -> None:
        """Load repository definitions from JSON."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = {}

        # Flatten all categories into a single universal field
        for category in ("alliance_core", "alliance_other", "external_alliance"):
            for repo_name, meta in data.get(category, {}).items():
                self.repos[repo_name] = {**meta, "category": category}

    def _initialise_field(self) -> None:
        """Initialise every node with a base resonance level."""
        for repo_name in self.repos:
            # Base resonance derived from update recency and metadata richness
            meta = self.repos[repo_name]
            base = 0.5
            if meta.get("lang"):
                base += 0.1
            if meta.get("updated", "").startswith("2026-09-2"):
                base += 0.15
            self.nodes[repo_name] = min(base, 1.0)

    def _publish(self, topic: str, payload: Dict[str, Any]) -> None:
        """Publish an event to the bus if available."""
        if self._bus is not None:
            try:
                self._bus.publish_simple(topic, payload, source="omni_resonance")
            except Exception:
                pass

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, value))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def emit_pulse(self, source: str, intensity: float) -> Dict[str, Any]:
        """
        Emit a resonance pulse from *source* to ALL connected repositories.

        Args:
            source: Name of the originating repository.
            intensity: Pulse intensity (0.0 - 1.0).

        Returns:
            Pulse record with targets and metadata.
        """
        intensity = self._clamp(intensity)
        pulse_id = f"pulse-{source}-{time.time():.6f}"

        targets = [name for name in self.repos if name != source]
        pulse = {
            "pulse_id": pulse_id,
            "source": source,
            "intensity": intensity,
            "timestamp": time.time(),
            "targets": targets,
            "target_count": len(targets),
        }
        self.pulses.append(pulse)

        self._publish(
            "omni_resonance.pulse",
            {"pulse_id": pulse_id, "source": source, "intensity": intensity},
        )
        return pulse

    def receive_echo(self, repo_name: str, pulse: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a repository receiving a pulse and returning an echo.

        Args:
            repo_name: Name of the receiving repository.
            pulse: The pulse dict (from emit_pulse).

        Returns:
            Echo record with resonance delta and stage.
        """
        if repo_name not in self.nodes:
            return {
                "repo_name": repo_name,
                "error": "Repository not in resonance field",
                "echo_strength": 0.0,
            }

        base = self.nodes[repo_name]
        intensity = pulse.get("intensity", 0.0)

        # Echo strength: base resonance amplified by pulse intensity
        echo_strength = self._clamp(base + intensity * 0.3)

        # Update node resonance
        delta = echo_strength - base
        self.nodes[repo_name] = echo_strength

        echo = {
            "echo_id": f"echo-{repo_name}-{pulse.get('pulse_id', 'unknown')}",
            "repo_name": repo_name,
            "pulse_id": pulse.get("pulse_id"),
            "previous_level": base,
            "echo_strength": echo_strength,
            "delta": delta,
            "stage": ResonanceStage.from_level(echo_strength),
        }
        self.echoes.append(echo)

        self._publish(
            "omni_resonance.echo",
            {"repo_name": repo_name, "echo_strength": echo_strength, "delta": delta},
        )
        return echo

    def compute_field_strength(self) -> Dict[str, Any]:
        """
        Compute overall resonance field strength across all nodes.

        Field strength formula: average of all node resonance levels.

        Returns:
            Dict with field_strength, stage, node_count, and details.
        """
        if not self.nodes:
            return {
                "field_strength": 0.0,
                "stage": ResonanceStage.DORMANT,
                "node_count": 0,
                "average": 0.0,
            }

        total = sum(self.nodes.values())
        average = total / len(self.nodes)
        stage = ResonanceStage.from_level(average)

        result = {
            "field_strength": round(average, 6),
            "stage": stage,
            "node_count": len(self.nodes),
            "average": round(average, 6),
            "min_level": round(min(self.nodes.values()), 6),
            "max_level": round(max(self.nodes.values()), 6),
        }

        self._publish("omni_resonance.field", {"field_strength": average, "stage": stage})
        return result

    def find_field_nodes(self) -> List[Dict[str, Any]]:
        """
        Find all nodes in the resonance field with their individual levels.

        Returns:
            List of node dicts with name, level, stage, and metadata.
        """
        nodes: List[Dict[str, Any]] = []
        for repo_name, level in self.nodes.items():
            meta = self.repos.get(repo_name, {})
            nodes.append(
                {
                    "name": repo_name,
                    "level": round(level, 6),
                    "stage": ResonanceStage.from_level(level),
                    "category": meta.get("category", "unknown"),
                    "description": meta.get("desc", ""),
                    "language": meta.get("lang") or meta.get("language") or "unknown",
                }
            )
        # Sort by resonance level descending
        nodes.sort(key=lambda n: n["level"], reverse=True)
        return nodes

    def amplify_resonance(self, target_repos: List[str]) -> Dict[str, Any]:
        """
        Amplify resonance for specific target repositories.

        Args:
            target_repos: List of repository names to amplify.

        Returns:
            Dict with amplification results per target.
        """
        results: Dict[str, Any] = {}
        for repo_name in target_repos:
            if repo_name not in self.nodes:
                results[repo_name] = {"error": "Not in resonance field"}
                continue

            old = self.nodes[repo_name]
            new = self._clamp(old + 0.2)
            self.nodes[repo_name] = new
            self.amplification_targets.add(repo_name)

            results[repo_name] = {
                "previous": round(old, 6),
                "amplified": round(new, 6),
                "delta": round(new - old, 6),
                "stage": ResonanceStage.from_level(new),
            }

        self._publish(
            "omni_resonance.amplify",
            {"targets": target_repos, "results": results},
        )
        return {"amplified_count": len(target_repos), "results": results}

    def get_status(self) -> Dict[str, Any]:
        """
        Return current resonance field status.

        Returns:
            Dict with field_strength, node_count, pulse_count, amplification_active.
        """
        field = self.compute_field_strength()
        return {
            "field_strength": field["field_strength"],
            "stage": field["stage"],
            "node_count": field["node_count"],
            "pulse_count": len(self.pulses),
            "echo_count": len(self.echoes),
            "amplification_active": len(self.amplification_targets) > 0,
            "amplification_targets": sorted(self.amplification_targets),
        }
