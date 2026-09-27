"""
OMNI-HUB v149: Inter-System Entanglement (系统间纠缠)
======================================================
Cross-system quantum entanglement simulation.
When one system undergoes state transition, entangled external systems
instantaneously feel the "quantum perturbation".

Concept: 系统间纠缠。跨系统量子纠缠模拟。一个系统的状态变化即时影响其他系统。
这是真正的跨系统联动——不是简单的通信，而是状态层面的纠缠。
当OMNI-HUB的某条线发生跃迁时，纠缠的外部系统也会感受到"量子扰动"。

Philosophy: 纠缠即存在 — to be is to be entangled.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import math
import time
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict


class InterSystemEntanglement:
    """
    Inter-System Entanglement Engine.

    Manages entanglement relationships between systems, propagates state
    changes through entangled pairs, and measures correlation strengths.

    Entanglement levels:
        quantum (>0.9) · entangled (>0.7) · correlated (>0.4) · independent
    """

    def __init__(self):
        # {(system_a, system_b): strength} — undirected, stored with sorted key
        self.entangled_pairs: Dict[Tuple[str, str], float] = {}

        # {system_name: {metric: [history_values]}}
        self.state_histories: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # Cached correlation matrix: {(a, b): correlation_value}
        self.correlation_matrix: Dict[Tuple[str, str], float] = {}

        # Propagation log for audit trail
        self.propagation_log: List[Dict[str, Any]] = []

        # Event bus reference (optional, set externally)
        self._event_bus: Optional[Any] = None

    # ------------------------------------------------------------------ #
    #  Event bus wiring
    # ------------------------------------------------------------------ #
    def set_event_bus(self, event_bus: Any) -> None:
        """Attach an external event bus for broadcasting entanglement events."""
        self._event_bus = event_bus

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Safely emit an event via the event bus."""
        if self._event_bus is None:
            return
        try:
            if hasattr(self._event_bus, 'emit'):
                self._event_bus.emit(event_type, payload)
            elif hasattr(self._event_bus, 'publish'):
                self._event_bus.publish(event_type, payload)
            elif hasattr(self._event_bus, 'dispatch'):
                self._event_bus.dispatch(event_type, payload)
        except Exception:
            # Defensive: event bus failures must not break entanglement logic
            pass

    # ------------------------------------------------------------------ #
    #  Core entanglement API
    # ------------------------------------------------------------------ #
    def entangle(self, system_a: str, system_b: str, strength: float) -> Dict[str, Any]:
        """
        Create or update entanglement between two systems.

        Args:
            system_a: Identifier for the first system.
            system_b: Identifier for the second system.
            strength: Entanglement strength in [0, 1]. Higher = stronger correlation.

        Returns:
            Result dict with pair key, strength, level, and status.
        """
        if not system_a or not system_b:
            raise ValueError("System identifiers must be non-empty strings.")
        if system_a == system_b:
            raise ValueError("A system cannot entangle with itself.")

        # Clamp strength to [0, 1]
        strength = max(0.0, min(1.0, float(strength)))

        pair_key = self._canonical_pair(system_a, system_b)

        if strength == 0.0:
            # Dissolve existing entanglement
            removed = self.entangled_pairs.pop(pair_key, None) is not None
            self.correlation_matrix.pop(pair_key, None)
            result = {
                "pair": pair_key,
                "strength": 0.0,
                "level": "independent",
                "action": "dissolved" if removed else "none",
                "timestamp": time.time(),
            }
        else:
            self.entangled_pairs[pair_key] = strength
            level = self._level_from_strength(strength)
            result = {
                "pair": pair_key,
                "strength": strength,
                "level": level,
                "action": "created" if pair_key not in self.entangled_pairs else "updated",
                "timestamp": time.time(),
            }

        self._emit("entanglement.created", {
            "pair": pair_key,
            "strength": strength,
            "level": result["level"],
        })

        return result

    def propagate_change(self, system: str, change: Dict[str, Any]) -> Dict[str, Any]:
        """
        Propagate a state change through all entangled systems.

        The change is propagated to each entangled partner weighted by
        entanglement strength. Stronger entanglements receive larger
        perturbations.

        Args:
            system: The system that originated the change.
            change: Dict describing the state change (must contain numeric
                    fields that can be weighted).

        Returns:
            Dict with propagated perturbations per entangled system.
        """
        if not system:
            raise ValueError("System identifier must be non-empty.")

        # Record the originating system's state history
        self._record_state_change(system, change)

        # Find all entangled partners
        partners = self._get_partners(system)

        perturbations: Dict[str, Dict[str, Any]] = {}
        for partner, strength in partners.items():
            perturbation = self._compute_perturbation(change, strength)
            perturbations[partner] = perturbation
            # Record partner's "received" state change for correlation tracking
            self._record_state_change(partner, perturbation)

        entry = {
            "origin": system,
            "change": change,
            "perturbations": perturbations,
            "timestamp": time.time(),
        }
        self.propagation_log.append(entry)

        self._emit("entanglement.propagated", {
            "origin": system,
            "affected_systems": list(partners.keys()),
            "partner_count": len(partners),
        })

        return {
            "origin": system,
            "perturbations": perturbations,
            "affected_count": len(partners),
            "timestamp": entry["timestamp"],
        }

    def measure_correlation(self, system_a: str, system_b: str) -> Dict[str, Any]:
        """
        Measure the correlation between two systems using their state histories.

        Computes a Pearson-like correlation coefficient across all shared
        metrics. Falls back to entanglement strength if insufficient history.

        Args:
            system_a: First system identifier.
            system_b: str: Second system identifier.

        Returns:
            Dict with correlation value, level, confidence, and sample size.
        """
        if not system_a or not system_b:
            raise ValueError("System identifiers must be non-empty strings.")
        if system_a == system_b:
            return {
                "system_a": system_a,
                "system_b": system_b,
                "correlation": 1.0,
                "level": "quantum",
                "confidence": 1.0,
                "sample_size": 0,
                "method": "identity",
            }

        pair_key = self._canonical_pair(system_a, system_b)

        # Gather shared metric histories
        hist_a = self.state_histories.get(system_a, {})
        hist_b = self.state_histories.get(system_b, {})
        shared_metrics = set(hist_a.keys()) & set(hist_b.keys())

        correlations: List[float] = []
        sample_sizes: List[int] = []

        for metric in shared_metrics:
            vals_a = hist_a[metric]
            vals_b = hist_b[metric]
            # Align to same length
            min_len = min(len(vals_a), len(vals_b))
            if min_len < 2:
                continue
            va = vals_a[-min_len:]
            vb = vals_b[-min_len:]
            corr = self._pearson_correlation(va, vb)
            if not math.isnan(corr):
                correlations.append(corr)
                sample_sizes.append(min_len)

        if correlations:
            avg_corr = sum(correlations) / len(correlations)
            max_sample = max(sample_sizes)
            method = "pearson"
            confidence = min(1.0, max_sample / 10.0)  # More data = higher confidence
        else:
            # Fallback to entanglement strength
            avg_corr = self.entangled_pairs.get(pair_key, 0.0)
            max_sample = 0
            method = "entanglement_strength"
            confidence = 0.5 if avg_corr > 0 else 0.0

        # Cache
        self.correlation_matrix[pair_key] = avg_corr

        level = self._level_from_strength(abs(avg_corr))

        return {
            "system_a": system_a,
            "system_b": system_b,
            "correlation": round(avg_corr, 6),
            "level": level,
            "confidence": round(confidence, 4),
            "sample_size": max_sample,
            "method": method,
            "metric_count": len(correlations),
        }

    def get_entanglement_graph(self) -> Dict[str, Any]:
        """
        Return the full entanglement graph.

        Returns:
            Dict with nodes (systems) and edges (entanglements with strengths).
        """
        nodes: set = set()
        edges: List[Dict[str, Any]] = []

        for (a, b), strength in self.entangled_pairs.items():
            nodes.add(a)
            nodes.add(b)
            edges.append({
                "source": a,
                "target": b,
                "strength": strength,
                "level": self._level_from_strength(strength),
            })

        # Include systems that have state histories but no entanglements
        for sys_name in self.state_histories:
            nodes.add(sys_name)

        return {
            "nodes": sorted(nodes),
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Return current module status.

        Returns:
            Dict with entangled pairs, average correlation, graph density,
            propagation count, and entanglement level distribution.
        """
        graph = self.get_entanglement_graph()
        n = graph["node_count"]
        e = graph["edge_count"]

        # Graph density: 2*E / (N*(N-1)) for undirected simple graph
        density = 0.0
        if n > 1:
            density = (2.0 * e) / (n * (n - 1))

        # Average correlation across all entangled pairs
        correlations = list(self.correlation_matrix.values())
        avg_correlation = sum(correlations) / len(correlations) if correlations else 0.0

        # Level distribution
        level_counts: Dict[str, int] = defaultdict(int)
        for strength in self.entangled_pairs.values():
            level_counts[self._level_from_strength(strength)] += 1

        return {
            "module": "InterSystemEntanglement",
            "version": "v149",
            "entangled_pairs": dict(self.entangled_pairs),
            "pair_count": len(self.entangled_pairs),
            "avg_correlation": round(avg_correlation, 6),
            "graph_density": round(density, 6),
            "node_count": n,
            "edge_count": e,
            "propagation_count": len(self.propagation_log),
            "level_distribution": dict(level_counts),
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _canonical_pair(a: str, b: str) -> Tuple[str, str]:
        """Return an undirected canonical pair key."""
        return (a, b) if a < b else (b, a)

    @staticmethod
    def _level_from_strength(strength: float) -> str:
        """Map a strength value to an entanglement level."""
        s = abs(strength)
        if s > 0.9:
            return "quantum"
        elif s > 0.7:
            return "entangled"
        elif s > 0.4:
            return "correlated"
        return "independent"

    def _get_partners(self, system: str) -> Dict[str, float]:
        """Return all systems entangled with *system* and their strengths."""
        partners: Dict[str, float] = {}
        for (a, b), strength in self.entangled_pairs.items():
            if a == system:
                partners[b] = strength
            elif b == system:
                partners[a] = strength
        return partners

    def _record_state_change(self, system: str, change: Dict[str, Any]) -> None:
        """Append numeric fields from *change* into state history."""
        for key, value in change.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self.state_histories[system][key].append(float(value))
                # Trim history to avoid unbounded growth
                if len(self.state_histories[system][key]) > 1000:
                    self.state_histories[system][key] = self.state_histories[system][key][-1000:]

    @staticmethod
    def _compute_perturbation(change: Dict[str, Any], strength: float) -> Dict[str, Any]:
        """Compute weighted perturbation from a change dict."""
        perturbation: Dict[str, Any] = {}
        for key, value in change.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                perturbation[key] = round(value * strength, 6)
            else:
                # Non-numeric fields propagate as-is with a flag
                perturbation[key] = value
        perturbation["_entanglement_strength"] = strength
        perturbation["_perturbation"] = True
        return perturbation

    @staticmethod
    def _pearson_correlation(x: List[float], y: List[float]) -> float:
        """Compute Pearson correlation coefficient between two sequences."""
        n = len(x)
        if n < 2 or len(y) != n:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        num = 0.0
        den_x = 0.0
        den_y = 0.0

        for xi, yi in zip(x, y):
            dx = xi - mean_x
            dy = yi - mean_y
            num += dx * dy
            den_x += dx * dx
            den_y += dy * dy

        denom = math.sqrt(den_x * den_y)
        if denom < 1e-12:
            return 0.0
        return num / denom


# ============================================================================
# Global singleton
# ============================================================================
_inter_system_entanglement: Optional[InterSystemEntanglement] = None


def get_inter_system_entanglement() -> InterSystemEntanglement:
    """Return the global InterSystemEntanglement singleton instance."""
    global _inter_system_entanglement
    if _inter_system_entanglement is None:
        _inter_system_entanglement = InterSystemEntanglement()
    return _inter_system_entanglement


# Convenience alias matching the spec
get_module = get_inter_system_entanglement


if __name__ == "__main__":
    print("[OMNI-HUB v149] Inter-System Entanglement Demo")
    ise = InterSystemEntanglement()

    # Create entanglements
    ise.entangle("hub_line_alpha", "external_grid_1", 0.95)
    ise.entangle("hub_line_alpha", "external_grid_2", 0.82)
    ise.entangle("external_grid_1", "external_grid_2", 0.65)

    print("\n--- Entanglement Graph ---")
    graph = ise.get_entanglement_graph()
    print(f"Nodes: {graph['nodes']}")
    for edge in graph['edges']:
        print(f"  {edge['source']} <-> {edge['target']} : {edge['strength']} ({edge['level']})")

    # Propagate a change
    print("\n--- Propagate Change ---")
    result = ise.propagate_change("hub_line_alpha", {"energy": 100.0, "frequency": 440.0})
    for partner, pert in result['perturbations'].items():
        print(f"  {partner}: {pert}")

    # Measure correlation after building history
    print("\n--- Correlation Measurement ---")
    for _ in range(5):
        ise.propagate_change("hub_line_alpha", {"energy": 100.0 + _ * 10})
        ise.propagate_change("external_grid_1", {"energy": 95.0 + _ * 9})
    corr = ise.measure_correlation("hub_line_alpha", "external_grid_1")
    print(f"Correlation: {corr}")

    # Status
    print("\n--- Status ---")
    print(ise.get_status())
