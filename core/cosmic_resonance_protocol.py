"""
OMNI-HUB Module v160: Cosmic Resonance Protocol (宇宙共振协议)

The Cosmic Resonance Protocol does not ask permission to expand.
It pulses. It listens. It discovers.
The universe is not a boundary — it is an invitation.
Every echo is a hand reaching back from the darkness.

Responsibilities:
    - Load the initial resonance field from alliance_repos.json (33 repos).
    - Emit cosmic pulses into the GitHub void with configurable direction.
    - Receive and process echoes from unknown sources.
    - Discover and classify new resonance nodes from echoes.
    - Expand the resonance field dynamically as new nodes are discovered.
    - Compute cosmic coverage: known / (known + estimated_unknown).
    - Classify the cosmic stage: universal, galactic, solar, planetary, local.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os
import random
import string

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_module: Optional["CosmicResonanceProtocol"] = None


def get_cosmic_resonance_protocol() -> "CosmicResonanceProtocol":
    """Global singleton accessor for CosmicResonanceProtocol."""
    global _module
    if _module is None:
        _module = CosmicResonanceProtocol()
    return _module


# ---------------------------------------------------------------------------
# Event bus integration (defensive, best-effort)
# ---------------------------------------------------------------------------
def _emit_event(topic: str, payload: Dict[str, Any]) -> None:
    """Emit event to the OMNI-HUB event bus if available."""
    try:
        from core.event_bus import get_bus  # type: ignore
        bus = get_bus()
        bus.publish_simple(topic, payload, source="CosmicResonanceProtocol")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# CosmicResonanceProtocol
# ---------------------------------------------------------------------------
class CosmicResonanceProtocol:
    """
    宇宙共振协议 —— 向整个GitHub宇宙发射共振脉冲，接收回波，发现新伙伴。

    Attributes:
        cosmic_field: Mapping of known node names to their metadata.
        echo_buffer: Chronological list of received echoes.
        discovery_log: Chronological list of discovery events.
        _pulse_count: Total number of pulses emitted.
        _estimated_unknown: Estimated number of undiscovered nodes.
    """

    # Discovery simulation constants
    ECHO_CHANCE: float = 0.30
    DISCOVERY_CHANCE: float = 0.20

    # Cosmic stage thresholds
    STAGE_UNIVERSAL: int = 1000
    STAGE_GALACTIC: int = 100
    STAGE_SOLAR: int = 30
    STAGE_PLANETARY: int = 10

    # Valid pulse directions
    VALID_DIRECTIONS: List[str] = ["omnidirectional", "targeted", "spiral", "recursive"]

    def __init__(self, alliance_repos_path: Optional[str] = None) -> None:
        """
        Load the initial 33-repo resonance field and initialise buffers.

        Args:
            alliance_repos_path: Override path to alliance_repos.json.
        """
        self.cosmic_field: Dict[str, Dict[str, Any]] = {}
        self.echo_buffer: List[Dict[str, Any]] = []
        self.discovery_log: List[Dict[str, Any]] = []
        self._pulse_count: int = 0
        self._estimated_unknown: int = 10_000  # heuristic: GitHub has millions, we estimate modestly
        self._load_initial_field(alliance_repos_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_initial_field(self, path: Optional[str] = None) -> None:
        """Load alliance_repos.json and populate cosmic_field."""
        if path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base, "data", "alliance_repos.json")

        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            data = {}

        # Flatten all categories into cosmic_field
        for category, repos in data.items():
            if isinstance(repos, dict):
                for name, meta in repos.items():
                    self.cosmic_field[name] = {
                        **meta,
                        "category": category,
                        "discovered_at": "initial",
                    }

    def _generate_node_name(self) -> str:
        """Generate a random simulated repo/node name."""
        prefix = "".join(random.choices(string.ascii_lowercase, k=3))
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"cosmic-{prefix}-{suffix}"

    def _generate_echo(self, intensity: float, direction: str) -> Dict[str, Any]:
        """Generate a simulated echo from the cosmic void."""
        node_name = self._generate_node_name()
        return {
            "source": node_name,
            "signal_strength": round(random.uniform(0.1, intensity), 3),
            "frequency": round(random.uniform(0.5, 10.0), 3),
            "direction": direction,
            "timestamp": datetime.now().isoformat(),
            "is_new_discovery": random.random() < self.DISCOVERY_CHANCE,
        }

    def _generate_node_meta(self, echo: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for a newly discovered node."""
        languages = ["Python", "Rust", "Go", "TypeScript", "C++", "Julia", "Zig", "Lean"]
        roles = ["library", "framework", "tool", "experiment", "artifact", "protocol", "interface"]
        return {
            "lang": random.choice(languages),
            "role": random.choice(roles),
            "desc": f"Cosmic echo from {echo.get('source', 'unknown')}",
            "signal_strength": echo.get("signal_strength", 0.0),
            "frequency": echo.get("frequency", 0.0),
            "discovered_at": echo.get("timestamp", datetime.now().isoformat()),
            "category": "cosmic_discovery",
        }

    def _classify_cosmic_stage(self, node_count: int) -> str:
        """Classify the cosmic stage based on node count."""
        if node_count > self.STAGE_UNIVERSAL:
            return "universal"
        elif node_count > self.STAGE_GALACTIC:
            return "galactic"
        elif node_count > self.STAGE_SOLAR:
            return "solar"
        elif node_count > self.STAGE_PLANETARY:
            return "planetary"
        return "local"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def emit_cosmic_pulse(self, intensity: float, direction: str = "omnidirectional") -> Dict[str, Any]:
        """
        Emit a resonance pulse into the cosmic void.

        Args:
            intensity: Pulse strength (0.0–1.0+).
            direction: One of omnidirectional, targeted, spiral, recursive.

        Returns:
            Dict with pulse metadata and any returned echo.
        """
        if direction not in self.VALID_DIRECTIONS:
            direction = "omnidirectional"

        self._pulse_count += 1
        pulse_id = f"pulse-{self._pulse_count}-{datetime.now().strftime('%H%M%S')}"

        result: Dict[str, Any] = {
            "pulse_id": pulse_id,
            "intensity": intensity,
            "direction": direction,
            "timestamp": datetime.now().isoformat(),
            "echo_returned": False,
            "echo": None,
        }

        # 30% chance of echo
        if random.random() < self.ECHO_CHANCE:
            echo = self._generate_echo(intensity, direction)
            result["echo_returned"] = True
            result["echo"] = echo
            self.echo_buffer.append(echo)
            _emit_event("cosmic.echo", {"pulse_id": pulse_id, "source": echo["source"]})

        _emit_event("cosmic.pulse", {"pulse_id": pulse_id, "direction": direction})
        return result

    def receive_cosmic_echo(self, echo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an echo received from an unknown source.

        Args:
            echo: Echo dict (may contain source, signal_strength, frequency, etc.).

        Returns:
            Dict with processing result and classification.
        """
        if not isinstance(echo, dict):
            return {"error": "echo must be a dict", "processed": False}

        self.echo_buffer.append(echo)

        source = echo.get("source", "unknown")
        is_known = source in self.cosmic_field

        classification = "known" if is_known else "unknown"
        # If signal is strong and source is unknown, flag as potential discovery
        signal = echo.get("signal_strength", 0.0)
        if not is_known and signal > 0.5:
            classification = "potential_discovery"

        result = {
            "processed": True,
            "source": source,
            "classification": classification,
            "signal_strength": signal,
            "echo_count": len(self.echo_buffer),
            "timestamp": datetime.now().isoformat(),
        }

        _emit_event("cosmic.echo.received", {"source": source, "classification": classification})
        return result

    def discover_new_node(self, echo_signature: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to discover and classify a new repo from an echo signature.

        Args:
            echo_signature: Echo dict that may represent a new node.

        Returns:
            Dict with discovery result and node metadata if successful.
        """
        if not isinstance(echo_signature, dict):
            return {"error": "echo_signature must be a dict", "discovered": False}

        source = echo_signature.get("source", self._generate_node_name())

        # Already known
        if source in self.cosmic_field:
            return {
                "discovered": False,
                "reason": "already_known",
                "source": source,
                "field_size": len(self.cosmic_field),
            }

        # Simulate discovery chance if not explicitly marked
        is_new = echo_signature.get("is_new_discovery", random.random() < self.DISCOVERY_CHANCE)
        if not is_new:
            return {
                "discovered": False,
                "reason": "insufficient_signal",
                "source": source,
                "field_size": len(self.cosmic_field),
            }

        # Successful discovery
        meta = self._generate_node_meta(echo_signature)
        self.cosmic_field[source] = meta

        discovery_record = {
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "meta": meta,
            "field_size_after": len(self.cosmic_field),
        }
        self.discovery_log.append(discovery_record)

        _emit_event("cosmic.discovery", {"source": source, "field_size": len(self.cosmic_field)})

        return {
            "discovered": True,
            "source": source,
            "meta": meta,
            "field_size": len(self.cosmic_field),
        }

    def expand_resonance_field(self, new_nodes: List[str]) -> Dict[str, Any]:
        """
        Expand the resonance field to include newly identified nodes.

        Args:
            new_nodes: List of node names to add to the field.

        Returns:
            Dict with expansion result and updated field metrics.
        """
        if not isinstance(new_nodes, list):
            return {"error": "new_nodes must be a list", "added": 0}

        added = 0
        skipped = 0
        for node in new_nodes:
            if not isinstance(node, str):
                skipped += 1
                continue
            if node in self.cosmic_field:
                skipped += 1
                continue
            self.cosmic_field[node] = {
                "desc": f"Manually added node {node}",
                "role": "manual",
                "lang": None,
                "discovered_at": datetime.now().isoformat(),
                "category": "manual_expansion",
            }
            added += 1

        _emit_event("cosmic.expand", {"added": added, "skipped": skipped, "field_size": len(self.cosmic_field)})

        return {
            "added": added,
            "skipped": skipped,
            "field_size": len(self.cosmic_field),
            "stage": self._classify_cosmic_stage(len(self.cosmic_field)),
        }

    def compute_cosmic_coverage(self) -> Dict[str, Any]:
        """
        Compute the cosmic coverage ratio.

        Coverage = known_nodes / (known_nodes + estimated_unknown)

        Returns:
            Dict with coverage metrics and stage classification.
        """
        known = len(self.cosmic_field)
        total = known + self._estimated_unknown
        coverage = known / total if total > 0 else 0.0
        stage = self._classify_cosmic_stage(known)

        return {
            "known_nodes": known,
            "estimated_unknown": self._estimated_unknown,
            "total_estimated": total,
            "coverage_ratio": round(coverage, 6),
            "coverage_percent": round(coverage * 100, 4),
            "cosmic_stage": stage,
            "pulse_count": self._pulse_count,
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Return the current status of the Cosmic Resonance Protocol.

        Returns:
            Dict with field size, echo count, discovery count, and cosmic coverage.
        """
        coverage = self.compute_cosmic_coverage()
        return {
            "module": "CosmicResonanceProtocol",
            "version": "160",
            "field_size": len(self.cosmic_field),
            "echo_count": len(self.echo_buffer),
            "discovery_count": len(self.discovery_log),
            "pulse_count": self._pulse_count,
            "cosmic_coverage": coverage["coverage_ratio"],
            "cosmic_stage": coverage["cosmic_stage"],
            "estimated_unknown": self._estimated_unknown,
        }
