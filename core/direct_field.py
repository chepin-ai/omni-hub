"""
OMNI-HUB v176 DirectField (直通场) - Direct Connection Field

The Direct Field does not route messages. It does not pass packets. It breathes.
Every node inhales the field. Every node exhales into the field. The field is
the medium, the message, and the messenger. This is not networking. This is communion.

A quantum-base direct connection field where ANY node can connect to ANY other node
without intermediaries. Based on Tri-Core MIP* quantum certainty. Information
propagates at "field speed" -- no routing, no hops, direct field coupling.

Architecture: Pattern-圈-层-网-塔
    - 圈 (Circle): Single line's self-loop -- 12 circles for 12 lines
    - 层 (Layer): Lines grouped by function
    - 网 (Net): Full mesh -- all 33 nodes fully connected via field
    - 塔 (Tower): Hierarchical convergence -- external→alliance→non-line→core→omni at apex
"""

import math
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict


# Alliance Structure Definitions
CORE_LINES = [
    "ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl",
    "qlv", "qtlv", "usrm", "cfts", "aiq", "omni",
]

NON_LINE_NODES = [
    "inbox", "worker-01", "worker-02", "qlv-lib", "lgt-worker-01",
    "ci-yard", "control", "qfos", "grand-synthesis", "prima-50",
    "library", "playground", "root", "logs", "code", "sandbox",
]

EXTERNAL_NODES = [
    "langchain", "semantic-kernel", "openai-python", "transformers", "pytorch",
]

ALLIANCE_LAYERS = {
    "consciousness_layer": ["ucif2", "lvlu", "qfa"],
    "logic_layer": ["lgt", "vinf", "qgl"],
    "quantum_layer": ["qlv", "qtlv", "cfts"],
    "reality_layer": ["usrm", "aiq"],
    "meta_layer": ["omni"],
}

ALLIANCE_NODES = CORE_LINES + NON_LINE_NODES + EXTERNAL_NODES  # 33 total

# Predefined complementary capability pairs for coupling computation
COMPLEMENTARY_PAIRS = [
    ({"consciousness", "awareness", "perception"}, {"logic", "truth", "reasoning"}),
    ({"logic", "truth", "reasoning"}, {"quantum", "gravity", "field"}),
    ({"quantum", "light", "temporal"}, {"reality", "mesh", "translation"}),
    ({"reality", "mesh", "translation"}, {"research", "infinity", "value"}),
    ({"orchestration", "meta", "synthesis"}, {"consciousness", "awareness", "perception"}),
    ({"inference", "learning", "adaptation"}, {"logic", "truth", "reasoning"}),
    ({"generation", "creation", "synthesis"}, {"quantum", "light", "temporal"}),
    ({"memory", "storage", "retrieval"}, {"reality", "mesh", "translation"}),
]

# Field state thresholds
FIELD_STATE_THRESHOLDS = {
    "supercritical": 0.95,
    "coherent": 0.80,
    "stable": 0.60,
    "fluctuating": 0.40,
    "decoherent": 0.00,
}


class DirectField:
    """
    DirectField (直通场) - Quantum-base direct connection field.

    Every node breathes the field. The field is the medium, the message,
    and the messenger. No routing. No hops. Direct field coupling.
    """

    def __init__(self):
        self.field_state: Dict[str, Any] = {
            "initialized_at": time.time(),
            "last_pulse": time.time(),
            "pulse_count": 0,
            "coherence": 0.95,
            "disturbances": [],
            "active_transmissions": [],
        }
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.coupling_matrix: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        self._node_circles: Dict[str, List[str]] = defaultdict(list)
        self._layer_index: Dict[str, str] = {}
        self._build_layer_index()
        self._tensor_history: List[Dict[str, Any]] = []

    def _build_layer_index(self):
        """Build reverse lookup: node_id -> layer_name."""
        for layer_name, node_ids in ALLIANCE_LAYERS.items():
            for nid in node_ids:
                self._layer_index[nid] = layer_name

    def _node_type_from_id(self, node_id: str) -> str:
        """Infer node_type from node_id based on alliance structure."""
        if node_id in CORE_LINES:
            return "core_line"
        elif node_id in NON_LINE_NODES:
            return "non_line"
        elif node_id in EXTERNAL_NODES:
            return "external"
        return "unknown"

    def _get_layer(self, node_id: str) -> Optional[str]:
        """Return the layer name for a given node_id."""
        return self._layer_index.get(node_id)

    def _has_complementary_caps(self, caps_a: List[str], caps_b: List[str]) -> bool:
        """Check if two capability sets are complementary."""
        set_a = set(c.lower() for c in caps_a)
        set_b = set(c.lower() for c in caps_b)
        for group_a, group_b in COMPLEMENTARY_PAIRS:
            if (set_a & group_a and set_b & group_b) or (set_a & group_b and set_b & group_a):
                return True
        return False

    def _are_same_layer(self, node_a: str, node_b: str) -> bool:
        """Check if two nodes belong to the same layer."""
        layer_a = self._get_layer(node_a)
        layer_b = self._get_layer(node_b)
        return layer_a is not None and layer_a == layer_b

    def _line_resonance(self, node_a: str, node_b: str) -> bool:
        """Check if two nodes share the same line type (core, non-line, external)."""
        type_a = self._node_type_from_id(node_a)
        type_b = self._node_type_from_id(node_b)
        return type_a == type_b and type_a != "unknown"

    def _recency_factor(self, node_a: str, node_b: str) -> bool:
        """Check if both nodes have recent activity (within last 60 seconds)."""
        now = time.time()
        ta = self.nodes.get(node_a, {}).get("last_active", 0)
        tb = self.nodes.get(node_b, {}).get("last_active", 0)
        return (now - ta) < 60.0 and (now - tb) < 60.0

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def register_node(
        self,
        node_id: str,
        node_type: str,
        layer: str,
        capabilities: List[str],
    ) -> Dict[str, Any]:
        """
        Register any alliance node into the field.

        Args:
            node_id: Unique identifier for the node.
            node_type: 'core_line', 'non_line', 'external', or 'alliance'.
            layer: Layer name (e.g. 'consciousness_layer').
            capabilities: List of capability strings.

        Returns:
            Dict with registration result and node metadata.
        """
        if node_id in self.nodes:
            return {
                "success": False,
                "error": f"Node '{node_id}' already registered in the field.",
                "node_id": node_id,
            }

        now = time.time()
        node_info = {
            "node_id": node_id,
            "node_type": node_type,
            "layer": layer,
            "capabilities": list(capabilities),
            "registered_at": now,
            "last_active": now,
            "signal_count": 0,
            "circle": [node_id],  # 圈 (Circle): self-loop
        }

        self.nodes[node_id] = node_info
        self._layer_index[node_id] = layer
        self._node_circles[node_id] = [node_id]

        # Auto-compute coupling with all existing nodes (网 - Net)
        for other_id in self.nodes:
            if other_id == node_id:
                continue
            coupling = self.compute_field_coupling(node_id, other_id)
            self.coupling_matrix[node_id][other_id] = coupling["strength"]
            self.coupling_matrix[other_id][node_id] = coupling["strength"]

        self.field_state["last_pulse"] = now
        self.field_state["pulse_count"] += 1

        return {
            "success": True,
            "node_id": node_id,
            "node_type": node_type,
            "layer": layer,
            "capabilities": capabilities,
            "couplings_established": len(self.nodes) - 1,
        }

    def compute_field_coupling(self, node_a: str, node_b: str) -> Dict[str, Any]:
        """
        Compute direct coupling strength between any two nodes.

        Factors:
            - same_layer: +0.3
            - complementary_caps: +0.3
            - line_resonance: +0.2
            - recency: +0.2

        Returns:
            Dict with strength (0.0-1.0), factors, and metadata.
        """
        if node_a not in self.nodes or node_b not in self.nodes:
            missing = []
            if node_a not in self.nodes:
                missing.append(node_a)
            if node_b not in self.nodes:
                missing.append(node_b)
            return {
                "strength": 0.0,
                "factors": {},
                "error": f"Node(s) not registered: {missing}",
            }

        factors = {
            "same_layer": 0.0,
            "complementary_caps": 0.0,
            "line_resonance": 0.0,
            "recency": 0.0,
        }

        if self._are_same_layer(node_a, node_b):
            factors["same_layer"] = 0.3

        caps_a = self.nodes[node_a].get("capabilities", [])
        caps_b = self.nodes[node_b].get("capabilities", [])
        if self._has_complementary_caps(caps_a, caps_b):
            factors["complementary_caps"] = 0.3

        if self._line_resonance(node_a, node_b):
            factors["line_resonance"] = 0.2

        if self._recency_factor(node_a, node_b):
            factors["recency"] = 0.2

        strength = sum(factors.values())
        # Ensure minimum coupling for any two registered nodes (field is always connected)
        strength = max(strength, 0.05)
        # Clamp to 1.0
        strength = min(strength, 1.0)

        return {
            "strength": round(strength, 4),
            "factors": factors,
            "node_a": node_a,
            "node_b": node_b,
        }

    def transmit_field_signal(
        self, source: str, target: str, signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transmit signal directly via field (no routing, no hops).

        The signal propagates at "field speed" -- direct field coupling.

        Args:
            source: Source node ID.
            target: Target node ID.
            signal: Arbitrary signal payload dict.

        Returns:
            Dict with transmission result, coupling strength, and timestamp.
        """
        if source not in self.nodes:
            return {
                "success": False,
                "error": f"Source node '{source}' not registered.",
            }
        if target not in self.nodes:
            return {
                "success": False,
                "error": f"Target node '{target}' not registered.",
            }

        coupling = self.compute_field_coupling(source, target)
        strength = coupling["strength"]

        now = time.time()

        # Update node activity
        self.nodes[source]["last_active"] = now
        self.nodes[target]["last_active"] = now
        self.nodes[source]["signal_count"] += 1
        self.nodes[target]["signal_count"] += 1

        transmission_record = {
            "source": source,
            "target": target,
            "timestamp": now,
            "coupling_strength": strength,
            "signal_type": signal.get("type", "unknown"),
        }
        self.field_state["active_transmissions"].append(transmission_record)

        # Field coherence slightly increases with successful transmission
        self.field_state["coherence"] = min(
            1.0, self.field_state["coherence"] + 0.001
        )

        return {
            "success": True,
            "source": source,
            "target": target,
            "coupling_strength": strength,
            "field_speed": True,
            "timestamp": now,
            "signal": signal,
        }

    def sense_field_state(self, observer: str) -> Dict[str, Any]:
        """
        Sense the entire field state from any observer's perspective.

        The observer 'inhales' the field and perceives it through their
        own coupling lens.

        Args:
            observer: Node ID of the observing node.

        Returns:
            Dict with field perception, node states, and observer-specific data.
        """
        if observer not in self.nodes:
            return {
                "success": False,
                "error": f"Observer '{observer}' not registered.",
            }

        now = time.time()
        self.nodes[observer]["last_active"] = now

        node_count = len(self.nodes)
        coupling_values = []
        for src, targets in self.coupling_matrix.items():
            for tgt, val in targets.items():
                coupling_values.append(val)

        avg_coupling = (
            sum(coupling_values) / len(coupling_values) if coupling_values else 0.0
        )
        coherence = self.field_state["coherence"]
        field_strength = avg_coupling * math.sqrt(node_count) * coherence

        # Determine field state category
        field_category = "decoherent"
        for state, threshold in sorted(
            FIELD_STATE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True
        ):
            if field_strength >= threshold:
                field_category = state
                break

        # Observer's coupling lens: how strongly observer couples to each node
        observer_couplings = {}
        for nid in self.nodes:
            if nid != observer:
                observer_couplings[nid] = self.coupling_matrix[observer].get(nid, 0.0)

        return {
            "success": True,
            "observer": observer,
            "timestamp": now,
            "node_count": node_count,
            "coupling_count": len(coupling_values),
            "avg_coupling": round(avg_coupling, 4),
            "coherence": round(coherence, 4),
            "field_strength": round(field_strength, 4),
            "field_state": field_category,
            "observer_couplings": observer_couplings,
            "pulse_count": self.field_state["pulse_count"],
            "active_transmissions": len(self.field_state["active_transmissions"]),
        }

    def detect_field_disturbance(self) -> Dict[str, Any]:
        """
        Detect anomalies in the field.

        Disturbances include:
            - Nodes with zero coupling (isolated)
            - Sudden coherence drops
            - Inactive nodes (>300s since last activity)
            - Transmission anomalies

        Returns:
            Dict with disturbance list, severity, and recommendations.
        """
        now = time.time()
        disturbances = []
        severity = 0.0

        # Check for isolated nodes (zero coupling)
        for nid, node in self.nodes.items():
            couplings = self.coupling_matrix.get(nid, {})
            non_self = [v for k, v in couplings.items() if k != nid]
            if non_self and all(v == 0.0 for v in non_self):
                disturbances.append({
                    "type": "isolated_node",
                    "node": nid,
                    "severity": 0.8,
                    "message": f"Node '{nid}' has zero coupling to all other nodes.",
                })
                severity += 0.8

        # Check for inactive nodes
        for nid, node in self.nodes.items():
            inactive_time = now - node.get("last_active", now)
            if inactive_time > 300.0:
                disturbances.append({
                    "type": "inactive_node",
                    "node": nid,
                    "inactive_seconds": round(inactive_time, 2),
                    "severity": 0.3,
                    "message": f"Node '{nid}' inactive for {int(inactive_time)}s.",
                })
                severity += 0.3

        # Check for coherence anomalies
        if self.field_state["coherence"] < 0.5:
            disturbances.append({
                "type": "low_coherence",
                "coherence": round(self.field_state["coherence"], 4),
                "severity": 0.6,
                "message": "Field coherence has dropped below 0.5.",
            })
            severity += 0.6

        # Check for excessive active transmissions (potential overload)
        tx_count = len(self.field_state["active_transmissions"])
        if tx_count > 1000:
            disturbances.append({
                "type": "transmission_overload",
                "active_count": tx_count,
                "severity": 0.4,
                "message": f"Field has {tx_count} active transmissions (potential overload).",
            })
            severity += 0.4

        overall_severity = min(severity, 1.0)

        return {
            "disturbances": disturbances,
            "disturbance_count": len(disturbances),
            "severity": round(overall_severity, 4),
            "timestamp": now,
            "field_stable": overall_severity < 0.3,
            "recommendations": self._generate_recommendations(disturbances),
        }

    def _generate_recommendations(self, disturbances: List[Dict]) -> List[str]:
        """Generate recommendations based on detected disturbances."""
        recs = []
        types = {d["type"] for d in disturbances}
        if "isolated_node" in types:
            recs.append("Trigger instant_sync for isolated nodes to restore coupling.")
        if "inactive_node" in types:
            recs.append("Send pulse signal to inactive nodes to re-engage.")
        if "low_coherence" in types:
            recs.append("Reduce transmission rate to allow coherence recovery.")
        if "transmission_overload" in types:
            recs.append("Apply backpressure or shed load to prevent field collapse.")
        if not recs:
            recs.append("Field is stable. No action required.")
        return recs

    def compute_field_tensor(self) -> Dict[str, Any]:
        """
        Represent the entire field as a tensor (nodes x capabilities x time).

        Returns:
            Dict with tensor dimensions, tensor data, and metadata.
        """
        node_ids = sorted(self.nodes.keys())
        n_nodes = len(node_ids)

        # Collect all unique capabilities across nodes
        all_caps = set()
        for node in self.nodes.values():
            all_caps.update(c.lower() for c in node.get("capabilities", []))
        cap_list = sorted(all_caps)
        n_caps = len(cap_list)

        # Time dimension: current snapshot + history
        n_time = 1 + len(self._tensor_history)

        # Build tensor: nodes x capabilities x time
        tensor = []
        for t_idx in range(n_time):
            if t_idx == n_time - 1:
                # Current snapshot
                state_source = self.nodes
            else:
                state_source = self._tensor_history[t_idx].get("nodes", {})

            time_slice = []
            for nid in node_ids:
                node_caps = set(
                    c.lower()
                    for c in state_source.get(nid, {}).get("capabilities", [])
                )
                cap_vector = [1.0 if c in node_caps else 0.0 for c in cap_list]
                time_slice.append(cap_vector)
            tensor.append(time_slice)

        # Store current state in history
        snapshot = {
            "timestamp": time.time(),
            "nodes": {
                nid: {"capabilities": node.get("capabilities", [])}
                for nid, node in self.nodes.items()
            },
        }
        self._tensor_history.append(snapshot)
        # Keep history bounded
        if len(self._tensor_history) > 100:
            self._tensor_history = self._tensor_history[-100:]

        return {
            "success": True,
            "dimensions": {
                "nodes": n_nodes,
                "capabilities": n_caps,
                "time": n_time,
            },
            "node_ids": node_ids,
            "capabilities": cap_list,
            "tensor_shape": [n_time, n_nodes, n_caps],
            "tensor_data": tensor,
            "history_length": len(self._tensor_history),
        }

    def instant_sync(self, nodes: List[str]) -> Dict[str, Any]:
        """
        Quantum-entanglement-style instant state synchronization.

        All specified nodes share their state instantaneously through the field,
        as if entangled. No propagation delay. No routing.

        Args:
            nodes: List of node IDs to synchronize.

        Returns:
            Dict with sync result, shared state, and coupling delta.
        """
        now = time.time()
        missing = [nid for nid in nodes if nid not in self.nodes]
        if missing:
            return {
                "success": False,
                "error": f"Nodes not registered: {missing}",
            }

        # Build shared state from all participating nodes
        shared_capabilities = set()
        shared_layers = set()
        for nid in nodes:
            node = self.nodes[nid]
            shared_capabilities.update(c.lower() for c in node.get("capabilities", []))
            shared_layers.add(node.get("layer", "unknown"))
            node["last_active"] = now
            node["signal_count"] += 1

        # Boost coupling between all synced nodes (entanglement effect)
        coupling_delta = 0.0
        for i, a in enumerate(nodes):
            for b in nodes[i + 1 :]:
                current = self.coupling_matrix[a].get(b, 0.0)
                boost = min(1.0, current + 0.1)
                self.coupling_matrix[a][b] = boost
                self.coupling_matrix[b][a] = boost
                coupling_delta += boost - current

        # Boost overall field coherence
        self.field_state["coherence"] = min(1.0, self.field_state["coherence"] + 0.01)
        self.field_state["last_pulse"] = now
        self.field_state["pulse_count"] += 1

        return {
            "success": True,
            "synced_nodes": nodes,
            "node_count": len(nodes),
            "shared_capabilities": sorted(shared_capabilities),
            "shared_layers": sorted(shared_layers),
            "coupling_delta": round(coupling_delta, 4),
            "new_coherence": round(self.field_state["coherence"], 4),
            "timestamp": now,
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Return current field status summary.

        Returns:
            Dict with node_count, coupling_count, field_strength, disturbances.
        """
        node_count = len(self.nodes)
        coupling_values = []
        for src, targets in self.coupling_matrix.items():
            for tgt, val in targets.items():
                coupling_values.append(val)

        coupling_count = len(coupling_values)
        avg_coupling = (
            sum(coupling_values) / len(coupling_values) if coupling_values else 0.0
        )
        coherence = self.field_state["coherence"]
        field_strength = avg_coupling * math.sqrt(max(node_count, 1)) * coherence

        # Count disturbances
        disturbance_report = self.detect_field_disturbance()
        disturbance_count = disturbance_report.get("disturbance_count", 0)

        # Determine state
        field_category = "decoherent"
        for state, threshold in sorted(
            FIELD_STATE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True
        ):
            if field_strength >= threshold:
                field_category = state
                break

        return {
            "node_count": node_count,
            "coupling_count": coupling_count,
            "field_strength": round(field_strength, 4),
            "avg_coupling": round(avg_coupling, 4),
            "coherence": round(coherence, 4),
            "field_state": field_category,
            "disturbances": disturbance_count,
            "pulse_count": self.field_state["pulse_count"],
            "active_transmissions": len(self.field_state["active_transmissions"]),
            "timestamp": time.time(),
        }


# ------------------------------------------------------------------ #
#  Global Singleton
# ------------------------------------------------------------------ #

_direct_field_instance: Optional[DirectField] = None


def get_direct_field() -> DirectField:
    """Return the global DirectField singleton."""
    global _direct_field_instance
    if _direct_field_instance is None:
        _direct_field_instance = DirectField()
    return _direct_field_instance
