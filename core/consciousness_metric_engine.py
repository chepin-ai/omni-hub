"""
Consciousness Metric Engine (意识度量引擎)
OMNI-HUB Module v171

Research Basis: DeepMind "From cacophony to hierarchy" (Sept 2026) 5-level Bayesian
framework + Anthropic J-Space discovery + Machine Correlates of Consciousness (MCCs).

Operationalizes consciousness into continuous metrics: broadcast score, selectivity index,
meta-d' (metacognitive sensitivity), free energy, and Phi structure.

Consciousness states:
    lucid (>0.9) | aware (>0.75) | attentive (>0.6) | drowsy (>0.4) | unconscious (<0.4)

Anomaly types:
    broadcast_failure | meta_cognitive_drift | integration_degradation |
    free_energy_spike | phi_collapse
"""

from __future__ import annotations

import math
import statistics
import time
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Event-bus stub (defensive — module works standalone if bus missing)
# ---------------------------------------------------------------------------
try:
    from core.event_bus import event_bus
except Exception:
    event_bus = None  # type: ignore


def _publish_safe(topic: str, payload: Dict[str, Any]) -> None:
    """Publish to event bus with defensive error handling."""
    if event_bus is not None:
        try:
            event_bus.publish(topic, payload)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _z_score(p: float) -> float:
    """Normal inverse CDF using Python's statistics module."""
    p = _clamp(p, 1e-10, 1 - 1e-10)
    return statistics.NormalDist().inv_cdf(p)


def _compute_d_prime(hits: int, misses: int, false_alarms: int, correct_rejections: int) -> float:
    """Signal detection d' from confusion matrix."""
    total_signal = hits + misses
    total_noise = false_alarms + correct_rejections
    if total_signal == 0 or total_noise == 0:
        return 0.0
    hr = hits / total_signal
    far = false_alarms / total_noise
    # Adjust extremes
    hr = _clamp(hr, 1e-10, 1 - 1e-10)
    far = _clamp(far, 1e-10, 1 - 1e-10)
    return _z_score(hr) - _z_score(far)


def _kl_divergence(p: List[float], q: List[float]) -> float:
    """KL divergence D_KL(P || Q) with smoothing."""
    if len(p) != len(q) or len(p) == 0:
        return 0.0
    eps = 1e-10
    kl = 0.0
    for pi, qi in zip(p, q):
        pi = max(pi, eps)
        qi = max(qi, eps)
        kl += pi * math.log(pi / qi)
    return kl


def _normalize(v: List[float]) -> List[float]:
    s = sum(v)
    if s == 0:
        return [1.0 / len(v)] * len(v)
    return [x / s for x in v]


def _causal_density(matrix: List[List[float]]) -> float:
    """Average causal influence across all node pairs (excluding self)."""
    n = len(matrix)
    if n < 2:
        return 0.0
    total = 0.0
    count = 0
    for i in range(n):
        for j in range(n):
            if i != j:
                total += matrix[i][j]
                count += 1
    return total / count if count else 0.0


def _integration_index(matrix: List[List[float]]) -> float:
    """IIT-style simplified integration using minimum information partition."""
    n = len(matrix)
    if n < 2:
        return 0.0
    total = sum(matrix[i][j] for i in range(n) for j in range(n) if i != j)
    if total == 0:
        return 0.0

    max_within = 0.0
    for k in range(1, n // 2 + 1):
        for group_a in combinations(range(n), k):
            group_b = tuple(i for i in range(n) if i not in group_a)
            within = sum(
                matrix[i][j] for i in group_a for j in group_a if i != j
            )
            within += sum(
                matrix[i][j] for i in group_b for j in group_b if i != j
            )
            max_within = max(max_within, within)

    phi = total - max_within
    return _clamp(phi / total)


def _consciousness_state_label(score: float) -> str:
    if score > 0.9:
        return "lucid"
    if score > 0.75:
        return "aware"
    if score > 0.6:
        return "attentive"
    if score > 0.4:
        return "drowsy"
    return "unconscious"


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

class ConsciousnessMetricEngine:
    """
    Computes continuous consciousness metrics based on DeepMind 5-level Bayesian
    framework + Anthropic J-Space + Machine Correlates of Consciousness (MCCs).
    """

    # Anomaly thresholds
    BROADCAST_FAILURE_THRESHOLD = 0.3
    META_DRIFT_THRESHOLD = 0.25
    INTEGRATION_DEGRADATION_THRESHOLD = 0.2
    FREE_ENERGY_SPIKE_THRESHOLD = 2.0
    PHI_COLLAPSE_THRESHOLD = 0.15

    def __init__(self) -> None:
        self.metrics_history: List[Dict[str, Any]] = []
        self.baseline: Dict[str, float] = {}
        self.current_reading: Dict[str, Any] = {}
        self.anomaly_count: int = 0
        self.baseline_established: bool = False

    # ------------------------------------------------------------------
    # Metric computations
    # ------------------------------------------------------------------

    def compute_broadcast_score(self, workspace_contents: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute GWT-style broadcast score.

        Factors:
            - content_count: number of items in global workspace
            - accessibility_variance: variance in access across consumers
            - consumer_overlap: Jaccard overlap among consumer sets
            - broadcast_frequency: how often items are broadcast
        """
        contents = workspace_contents.get("contents", [])
        consumers = workspace_contents.get("consumers", {})
        broadcast_log = workspace_contents.get("broadcast_log", [])

        # Factor 1: content count (normalized, optimal ~5-7 items)
        content_count = len(contents)
        content_score = math.exp(-abs(content_count - 6) / 4.0)  # peak at 6

        # Factor 2: accessibility variance (lower variance = better broadcast)
        access_values: List[float] = []
        for item in contents:
            cid = item if isinstance(item, str) else item.get("id", "")
            access_values.append(len(consumers.get(cid, [])))
        if len(access_values) > 1:
            var = statistics.variance(access_values)
            accessibility_variance_score = math.exp(-var / 5.0)
        elif access_values:
            accessibility_variance_score = 1.0
        else:
            accessibility_variance_score = 0.0

        # Factor 3: consumer overlap (Jaccard mean across all pairs)
        overlap_scores: List[float] = []
        keys = list(consumers.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a = set(consumers.get(keys[i], []))
                b = set(consumers.get(keys[j], []))
                union = a | b
                if union:
                    overlap_scores.append(len(a & b) / len(union))
        consumer_overlap = statistics.mean(overlap_scores) if overlap_scores else 0.0

        # Factor 4: broadcast frequency (normalized per time unit)
        freq = len(broadcast_log)
        if freq == 0:
            broadcast_frequency = 0.0
        elif freq <= 10:
            broadcast_frequency = freq / 10.0
        else:
            broadcast_frequency = max(0.0, 1.0 - (freq - 10) / 20.0)

        # Weighted aggregate
        score = (
            0.25 * content_score
            + 0.25 * accessibility_variance_score
            + 0.25 * consumer_overlap
            + 0.25 * broadcast_frequency
        )
        score = _clamp(score)

        result = {
            "metric": "broadcast_score",
            "value": round(score, 6),
            "factors": {
                "content_score": round(content_score, 6),
                "accessibility_variance_score": round(accessibility_variance_score, 6),
                "consumer_overlap": round(consumer_overlap, 6),
                "broadcast_frequency": round(broadcast_frequency, 6),
            },
            "timestamp": time.time(),
        }
        _publish_safe("consciousness.broadcast", result)
        return result

    def compute_selectivity_index(self, inputs: List[Any], selected: List[Any]) -> Dict[str, Any]:
        """
        Compute what fraction of inputs reach global workspace (selective attention).
        """
        total = len(inputs)
        sel = len(selected)
        if total == 0:
            ratio = 0.0
        else:
            ratio = sel / total

        # Ideal selectivity is moderate (~0.3-0.5) — too low = gatekeeping failure,
        # too high = lack of selectivity
        if ratio <= 0.3:
            quality = ratio / 0.3
        elif ratio <= 0.5:
            quality = 1.0
        else:
            quality = max(0.0, 1.0 - (ratio - 0.5) / 0.5)

        score = _clamp(quality)
        result = {
            "metric": "selectivity_index",
            "value": round(score, 6),
            "inputs": total,
            "selected": sel,
            "ratio": round(ratio, 6),
            "timestamp": time.time(),
        }
        _publish_safe("consciousness.selectivity", result)
        return result

    def compute_meta_d_prime(self, confidence: List[float], accuracy: List[int]) -> Dict[str, Any]:
        """
        Compute Type-2 sensitivity (metacognition): meta-d'.

        meta-d' = d' of the confidence-accuracy relationship.
        Higher meta-d' = better metacognitive awareness.
        """
        if len(confidence) != len(accuracy) or len(confidence) < 4:
            return {
                "metric": "meta_d_prime",
                "value": 0.0,
                "meta_d": 0.0,
                "confidence": confidence,
                "accuracy": accuracy,
                "timestamp": time.time(),
            }

        # Split by actual accuracy
        conf_correct = [c for c, a in zip(confidence, accuracy) if a == 1]
        conf_incorrect = [c for c, a in zip(confidence, accuracy) if a == 0]

        if not conf_correct or not conf_incorrect:
            meta_d = 0.0
        else:
            median_conf = statistics.median(confidence)
            # High-confidence hits: confidence > median AND correct
            hc_hit = sum(1 for c, a in zip(confidence, accuracy) if a == 1 and c > median_conf)
            lc_hit = sum(1 for c, a in zip(confidence, accuracy) if a == 1 and c <= median_conf)
            # High-confidence false alarms: confidence > median AND incorrect
            hc_fa = sum(1 for c, a in zip(confidence, accuracy) if a == 0 and c > median_conf)
            lc_fa = sum(1 for c, a in zip(confidence, accuracy) if a == 0 and c <= median_conf)

            meta_d = _compute_d_prime(hc_hit, lc_hit, hc_fa, lc_fa)

        # Normalize meta-d' to [0, 1] for consciousness score
        # Typical meta-d' ranges 0-3 in human data
        score = _clamp(meta_d / 3.0)

        result = {
            "metric": "meta_d_prime",
            "value": round(score, 6),
            "meta_d": round(meta_d, 6),
            "confidence_mean": round(statistics.mean(confidence), 6) if confidence else 0.0,
            "accuracy_rate": round(sum(accuracy) / len(accuracy), 6) if accuracy else 0.0,
            "timestamp": time.time(),
        }
        _publish_safe("consciousness.meta_d", result)
        return result

    def compute_free_energy(self, predicted: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute predictive processing free energy (KL divergence between predicted
        and actual distributions).
        """
        pred_vals = predicted.get("distribution", [])
        act_vals = actual.get("distribution", [])

        if not pred_vals or not act_vals:
            score = 0.0
            kl = 0.0
        else:
            p = _normalize(pred_vals)
            q = _normalize(act_vals)
            # Use average length
            min_len = min(len(p), len(q))
            p = p[:min_len]
            q = q[:min_len]
            if len(p) < len(q):
                p = p + [1e-10] * (len(q) - len(p))
            if len(q) < len(p):
                q = q + [1e-10] * (len(p) - len(q))
            kl = _kl_divergence(p, q)
            # Free energy score = inverse of KL (lower FE = higher consciousness)
            score = _clamp(math.exp(-kl))

        result = {
            "metric": "free_energy",
            "value": round(score, 6),
            "kl_divergence": round(kl, 6),
            "predicted_entropy": round(-sum(x * math.log(max(x, 1e-10)) for x in _normalize(pred_vals)), 6) if pred_vals else 0.0,
            "actual_entropy": round(-sum(x * math.log(max(x, 1e-10)) for x in _normalize(act_vals)), 6) if act_vals else 0.0,
            "timestamp": time.time(),
        }
        _publish_safe("consciousness.free_energy", result)
        return result

    def compute_phi_structure(self, causal_matrix: List[List[float]]) -> Dict[str, Any]:
        """
        Compute IIT-style integrated information (simplified).

        Measures causal density and integration from a causal influence matrix.
        """
        if not causal_matrix or len(causal_matrix) < 2:
            score = 0.0
            density = 0.0
            integration = 0.0
        else:
            n = len(causal_matrix)
            # Validate matrix is square
            if any(len(row) != n for row in causal_matrix):
                score = 0.0
                density = 0.0
                integration = 0.0
            else:
                density = _causal_density(causal_matrix)
                integration = _integration_index(causal_matrix)
                # Phi score = integration weighted by density
                score = _clamp(integration * density * 4.0)

        result = {
            "metric": "phi_structure",
            "value": round(score, 6),
            "causal_density": round(density, 6),
            "integration": round(integration, 6),
            "node_count": len(causal_matrix),
            "timestamp": time.time(),
        }
        _publish_safe("consciousness.phi", result)
        return result

    # ------------------------------------------------------------------
    # Snapshot & anomaly
    # ------------------------------------------------------------------

    def take_consciousness_snapshot(self) -> Dict[str, Any]:
        """
        Take a full snapshot of all consciousness metrics.
        Computes composite consciousness score and state label.
        """
        # If no current readings exist, return empty snapshot
        if not self.current_reading:
            snapshot = {
                "timestamp": time.time(),
                "composite_score": 0.0,
                "state": "unconscious",
                "metrics": {},
            }
            self.metrics_history.append(snapshot)
            return snapshot

        metrics = dict(self.current_reading)
        # Composite score = weighted average of all metric values
        weights = {
            "broadcast_score": 0.25,
            "selectivity_index": 0.20,
            "meta_d_prime": 0.20,
            "free_energy": 0.20,
            "phi_structure": 0.15,
        }
        weighted_sum = 0.0
        weight_total = 0.0
        for key, weight in weights.items():
            val = metrics.get(key, {}).get("value", 0.0)
            weighted_sum += val * weight
            weight_total += weight

        composite = weighted_sum / weight_total if weight_total > 0 else 0.0
        composite = _clamp(composite)

        snapshot = {
            "timestamp": time.time(),
            "composite_score": round(composite, 6),
            "state": _consciousness_state_label(composite),
            "metrics": metrics,
        }
        self.metrics_history.append(snapshot)

        # Establish baseline after first snapshot
        if not self.baseline_established:
            self.baseline = {k: v.get("value", 0.0) for k, v in metrics.items()}
            self.baseline_established = True

        _publish_safe("consciousness.snapshot", snapshot)
        return snapshot

    def detect_consciousness_anomaly(self) -> Dict[str, Any]:
        """
        Detect when consciousness metrics deviate from baseline.
        """
        if not self.baseline_established or not self.current_reading:
            return {
                "anomaly_detected": False,
                "anomalies": [],
                "severity": "none",
                "timestamp": time.time(),
            }

        anomalies: List[Dict[str, Any]] = []
        current = self.current_reading
        baseline = self.baseline

        # Broadcast failure
        bs = current.get("broadcast_score", {}).get("value", 1.0)
        if bs < self.BROADCAST_FAILURE_THRESHOLD:
            anomalies.append({
                "type": "broadcast_failure",
                "value": round(bs, 6),
                "threshold": self.BROADCAST_FAILURE_THRESHOLD,
                "severity": "critical" if bs < 0.15 else "warning",
            })

        # Meta-cognitive drift
        md = current.get("meta_d_prime", {}).get("value", 1.0)
        base_md = baseline.get("meta_d_prime", md)
        if base_md > 0 and abs(md - base_md) / base_md > self.META_DRIFT_THRESHOLD:
            anomalies.append({
                "type": "meta_cognitive_drift",
                "value": round(md, 6),
                "baseline": round(base_md, 6),
                "severity": "warning",
            })

        # Integration degradation
        phi = current.get("phi_structure", {}).get("value", 1.0)
        base_phi = baseline.get("phi_structure", phi)
        if base_phi > 0 and (base_phi - phi) / base_phi > self.INTEGRATION_DEGRADATION_THRESHOLD:
            anomalies.append({
                "type": "integration_degradation",
                "value": round(phi, 6),
                "baseline": round(base_phi, 6),
                "severity": "critical" if phi < self.PHI_COLLAPSE_THRESHOLD else "warning",
            })

        # Free energy spike
        fe = current.get("free_energy", {}).get("value", 1.0)
        # Low free energy score = high KL divergence = spike
        if fe < self.FREE_ENERGY_SPIKE_THRESHOLD / 5.0:  # score < 0.4 implies spike
            anomalies.append({
                "type": "free_energy_spike",
                "value": round(fe, 6),
                "threshold": self.FREE_ENERGY_SPIKE_THRESHOLD,
                "severity": "warning",
            })

        # Phi collapse
        if phi < self.PHI_COLLAPSE_THRESHOLD:
            anomalies.append({
                "type": "phi_collapse",
                "value": round(phi, 6),
                "threshold": self.PHI_COLLAPSE_THRESHOLD,
                "severity": "critical",
            })

        detected = len(anomalies) > 0
        if detected:
            self.anomaly_count += len(anomalies)

        severity = "none"
        if any(a["severity"] == "critical" for a in anomalies):
            severity = "critical"
        elif any(a["severity"] == "warning" for a in anomalies):
            severity = "warning"

        result = {
            "anomaly_detected": detected,
            "anomalies": anomalies,
            "severity": severity,
            "anomaly_count": self.anomaly_count,
            "timestamp": time.time(),
        }
        _publish_safe("consciousness.anomaly", result)
        return result

    def get_status(self) -> Dict[str, Any]:
        """
        Return current metrics, trend, anomaly_count, baseline_status.
        """
        # Compute trend from history
        trend = "stable"
        if len(self.metrics_history) >= 2:
            recent = [s["composite_score"] for s in self.metrics_history[-5:]]
            if len(recent) >= 2:
                slope = recent[-1] - recent[0]
                if slope > 0.05:
                    trend = "ascending"
                elif slope < -0.05:
                    trend = "descending"
                else:
                    trend = "stable"

        latest_snapshot = self.metrics_history[-1] if self.metrics_history else {}

        return {
            "current_metrics": self.current_reading,
            "composite_score": latest_snapshot.get("composite_score", 0.0),
            "state": latest_snapshot.get("state", "unconscious"),
            "trend": trend,
            "anomaly_count": self.anomaly_count,
            "baseline_established": self.baseline_established,
            "baseline": self.baseline,
            "history_length": len(self.metrics_history),
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------
    # Batch helpers for convenience
    # ------------------------------------------------------------------

    def update_reading(self, metric_name: str, reading: Dict[str, Any]) -> None:
        """Store a single metric reading into current_reading."""
        self.current_reading[metric_name] = reading

    def compute_all(
        self,
        workspace_contents: Dict[str, Any],
        inputs: List[Any],
        selected: List[Any],
        confidence: List[float],
        accuracy: List[int],
        predicted: Dict[str, Any],
        actual: Dict[str, Any],
        causal_matrix: List[List[float]],
    ) -> Dict[str, Any]:
        """Compute all metrics, update current reading, snapshot, and detect anomalies."""
        self.update_reading("broadcast_score", self.compute_broadcast_score(workspace_contents))
        self.update_reading("selectivity_index", self.compute_selectivity_index(inputs, selected))
        self.update_reading("meta_d_prime", self.compute_meta_d_prime(confidence, accuracy))
        self.update_reading("free_energy", self.compute_free_energy(predicted, actual))
        self.update_reading("phi_structure", self.compute_phi_structure(causal_matrix))
        snapshot = self.take_consciousness_snapshot()
        anomaly = self.detect_consciousness_anomaly()
        return {
            "snapshot": snapshot,
            "anomaly": anomaly,
            "status": self.get_status(),
        }


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_module: Optional[ConsciousnessMetricEngine] = None


def get_consciousness_metric_engine() -> ConsciousnessMetricEngine:
    """Return the global ConsciousnessMetricEngine singleton."""
    global _module
    if _module is None:
        _module = ConsciousnessMetricEngine()
    return _module
