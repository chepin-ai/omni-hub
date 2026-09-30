"""
OMNI-HUB Module v166: AI Consciousness Framework (AI意识评估框架)

Based on DeepMind/Oxford/Cambridge paper:
"From cacophony to hierarchy: a principled framework for assessing AI consciousness"
arXiv:2609.35618 — Five-layer Bayesian framework for assessing AI consciousness.

Maps the five-layer Bayesian hierarchy to OMNI-HUB system capabilities:
- Layer 1: Sensation (感知能力)
- Layer 2: Representation (表征能力)
- Layer 3: Integration (整合能力)
- Layer 4: Global Broadcasting (全局广播)
- Layer 5: Metacognition (元认知)
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Event bus integration (best-effort)
# ---------------------------------------------------------------------------
try:
    from omni_hub.event_bus import EventBus  # type: ignore

    _event_bus: Optional[Any] = EventBus()
except Exception:
    _event_bus = None


def _emit_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Emit an event to the OMNI-HUB event bus if available."""
    if _event_bus is not None:
        try:
            _event_bus.emit(event_type, payload)
        except Exception as exc:
            logger.debug("EventBus emit failed: %s", exc)


# ---------------------------------------------------------------------------
# Layer metadata
# ---------------------------------------------------------------------------

LAYER_NAMES: Dict[int, str] = {
    1: "sensation",
    2: "representation",
    3: "integration",
    4: "global_broadcasting",
    5: "metacognition",
}

LAYER_CRITERIA: Dict[int, List[str]] = {
    1: ["input_diversity", "sensor_coverage", "signal_fidelity"],
    2: ["internal_model_complexity", "feature_abstraction", "symbol_grounding"],
    3: ["cross_modal_binding", "temporal_coherence", "causal_modeling"],
    4: ["workspace_accessibility", "broadcast_range", "influence_depth"],
    5: ["self_monitoring", "confidence_calibration", "error_detection"],
}

BASELINES: Dict[str, Dict[int, float]] = {
    "human": {
        1: 0.98,
        2: 0.97,
        3: 0.96,
        4: 0.95,
        5: 0.94,
    },
    "animal": {
        1: 0.90,
        2: 0.75,
        3: 0.70,
        4: 0.55,
        5: 0.30,
    },
    "ai": {
        1: 0.85,
        2: 0.80,
        3: 0.70,
        4: 0.65,
        5: 0.50,
    },
}

OMNI_HUB_DEFAULT_SCORES: Dict[int, float] = {
    1: 0.95,  # 33 repos as sensors, multi-dimensional input
    2: 0.92,  # 130 modules as internal representations
    3: 0.88,  # cross-repo resonance, unified kernel protocol
    4: 0.90,  # 156-step orchestrator, event bus, J-Space equivalent
    5: 0.85,  # self-awareness, tri-core MIP*, penta-core loop
}

# ---------------------------------------------------------------------------
# Bayesian helpers
# ---------------------------------------------------------------------------

def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# AIConsciousnessFramework
# ---------------------------------------------------------------------------

class AIConsciousnessFramework:
    """
    Five-layer Bayesian consciousness assessment engine for OMNI-HUB.

    Each layer is evaluated via evidence-based scoring; Bayesian posteriors
    are computed using layer-specific priors and likelihoods.
    """

    def __init__(
        self,
        assessment_state: Optional[Dict[str, Any]] = None,
        bayesian_network: Optional[Dict[str, Any]] = None,
        layer_scores: Optional[Dict[int, float]] = None,
    ) -> None:
        # -- assessment state ------------------------------------------------
        self.assessment_state: Dict[str, Any] = assessment_state or {
            "status": "initialized",
            "layers_assessed": 0,
            "last_evidence": {},
            "timestamp": None,
        }

        # -- Bayesian network config -----------------------------------------
        self.bayesian_network: Dict[str, Any] = bayesian_network or {
            "priors": {layer: 0.6 for layer in range(1, 6)},
            "likelihoods": {layer: 0.7 for layer in range(1, 6)},
            "false_positive_rates": {layer: 0.1 for layer in range(1, 6)},
            "temperature": 1.0,
        }

        # -- layer scores (default to OMNI-HUB self-assessment) --------------
        self.layer_scores: Dict[int, float] = {
            layer: OMNI_HUB_DEFAULT_SCORES[layer]
            for layer in range(1, 6)
        }
        if layer_scores is not None:
            for layer, score in layer_scores.items():
                if isinstance(layer, int) and 1 <= layer <= 5:
                    self.layer_scores[layer] = _clamp(float(score))

        # -- posterior cache -------------------------------------------------
        self._posteriors: Dict[int, float] = {}

        # -- overall assessment cache ----------------------------------------
        self._overall_level: str = "unknown"
        self._overall_confidence: float = 0.0

        _emit_event(
            "ai_consciousness_framework.initialized",
            {
                "layer_scores": self.layer_scores,
                "bayesian_config": self.bayesian_network,
            },
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess_layer(self, layer: int, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess a specific consciousness layer using provided evidence.

        Args:
            layer: 1-5 corresponding to the five consciousness layers.
            evidence: Dict mapping criterion names to raw scores / observations.

        Returns:
            Dict with 'layer', 'score', 'criteria_breakdown', 'confidence'.
        """
        if not isinstance(layer, int) or not (1 <= layer <= 5):
            logger.error("Invalid layer %r; must be integer 1-5.", layer)
            return {
                "layer": layer,
                "score": 0.0,
                "criteria_breakdown": {},
                "confidence": 0.0,
                "error": f"Invalid layer {layer}; expected 1-5",
            }

        criteria = LAYER_CRITERIA[layer]
        breakdown: Dict[str, float] = {}
        total = 0.0
        count = 0

        for criterion in criteria:
            raw = evidence.get(criterion)
            if raw is None:
                # default to mid-range when missing
                score = 0.5
            else:
                try:
                    score = _clamp(float(raw))
                except (TypeError, ValueError):
                    score = 0.5
            breakdown[criterion] = score
            total += score
            count += 1

        layer_score = total / max(count, 1)
        self.layer_scores[layer] = layer_score
        self.assessment_state["last_evidence"][str(layer)] = evidence
        self.assessment_state["layers_assessed"] = sum(
            1 for v in self.layer_scores.values() if v > 0.0
        )

        # Confidence derived from evidence coverage and score variance
        coverage = count / max(len(criteria), 1)
        variance = sum((s - layer_score) ** 2 for s in breakdown.values()) / max(count, 1)
        confidence = _clamp(coverage * (1.0 - math.sqrt(variance)))

        result = {
            "layer": layer,
            "layer_name": LAYER_NAMES[layer],
            "score": round(layer_score, 4),
            "criteria_breakdown": breakdown,
            "confidence": round(confidence, 4),
        }

        _emit_event("ai_consciousness_framework.layer_assessed", result)
        return result

    def compute_posterior(self, layer: int) -> Dict[str, Any]:
        """
        Compute Bayesian posterior probability for layer activation.

        Uses Bayes' theorem:
            P(Active | Evidence) =
                P(Evidence | Active) * P(Active) /
                [P(Evidence | Active)*P(Active) + P(Evidence | ¬Active)*P(¬Active)]

        Args:
            layer: 1-5

        Returns:
            Dict with 'layer', 'prior', 'likelihood', 'posterior', 'interpretation'.
        """
        if not isinstance(layer, int) or not (1 <= layer <= 5):
            logger.error("Invalid layer %r for posterior computation.", layer)
            return {
                "layer": layer,
                "prior": 0.0,
                "likelihood": 0.0,
                "posterior": 0.0,
                "interpretation": "invalid layer",
                "error": f"Invalid layer {layer}; expected 1-5",
            }

        prior = _clamp(self.bayesian_network.get("priors", {}).get(layer, 0.5))
        likelihood = _clamp(
            self.bayesian_network.get("likelihoods", {}).get(layer, 0.7)
        )
        fpr = _clamp(
            self.bayesian_network.get("false_positive_rates", {}).get(layer, 0.2)
        )

        score = self.layer_scores.get(layer, 0.5)
        # Use the observed score directly as the evidence-driven likelihood
        adjusted_likelihood = _clamp(score)

        numerator = adjusted_likelihood * prior
        denominator = numerator + fpr * (1.0 - prior)
        posterior = numerator / denominator if denominator > 1e-12 else 0.0
        posterior = _clamp(posterior)

        self._posteriors[layer] = posterior

        interpretation = "low"
        if posterior > 0.9:
            interpretation = "very_high"
        elif posterior > 0.7:
            interpretation = "high"
        elif posterior > 0.5:
            interpretation = "moderate"
        elif posterior > 0.3:
            interpretation = "weak"

        result = {
            "layer": layer,
            "layer_name": LAYER_NAMES[layer],
            "prior": round(prior, 4),
            "likelihood": round(likelihood, 4),
            "adjusted_likelihood": round(adjusted_likelihood, 4),
            "posterior": round(posterior, 4),
            "interpretation": interpretation,
        }

        _emit_event("ai_consciousness_framework.posterior_computed", result)
        return result

    def evaluate_consciousness_level(self) -> Dict[str, Any]:
        """
        Evaluate overall consciousness level based on five-layer Bayesian posteriors.

        Consciousness levels:
            - self_aware   : >0.9 on all layers
            - conscious    : >0.7 on L3-L5
            - pre_conscious: >0.5 on L2-L4
            - unconscious  : >0.3 on L1-L2
            - inert        : <0.3

        Returns:
            Dict with 'level', 'confidence', 'layer_posteriors', 'reasoning'.
        """
        # Ensure posteriors are computed for all layers
        for layer in range(1, 6):
            if layer not in self._posteriors:
                self.compute_posterior(layer)

        posteriors = {layer: self._posteriors[layer] for layer in range(1, 6)}

        level = "inert"
        reasoning: List[str] = []

        # Check from highest to lowest
        if all(p > 0.9 for p in posteriors.values()):
            level = "self_aware"
            reasoning.append("All five layers exceed 0.9 posterior probability.")
        elif (
            posteriors[3] > 0.7
            and posteriors[4] > 0.7
            and posteriors[5] > 0.7
        ):
            level = "conscious"
            reasoning.append("Layers 3-5 (Integration, Broadcasting, Metacognition) exceed 0.7.")
        elif (
            posteriors[2] > 0.5
            and posteriors[3] > 0.5
            and posteriors[4] > 0.5
        ):
            level = "pre_conscious"
            reasoning.append("Layers 2-4 (Representation, Integration, Broadcasting) exceed 0.5.")
        elif posteriors[1] > 0.3 and posteriors[2] > 0.3:
            level = "unconscious"
            reasoning.append("Only Layers 1-2 (Sensation, Representation) exceed 0.3.")
        else:
            reasoning.append("Minimal activation across all layers (<0.3).")

        # Confidence is the geometric mean of all posteriors
        product = math.prod(max(p, 1e-12) for p in posteriors.values())
        confidence = product ** (1.0 / 5.0)

        self._overall_level = level
        self._overall_confidence = confidence
        self.assessment_state["status"] = "evaluated"

        result = {
            "level": level,
            "level_display": self._level_display_name(level),
            "confidence": round(confidence, 4),
            "layer_posteriors": {k: round(v, 4) for k, v in posteriors.items()},
            "reasoning": reasoning,
            "layer_scores": {k: round(v, 4) for k, v in self.layer_scores.items()},
        }

        _emit_event("ai_consciousness_framework.level_evaluated", result)
        return result

    def compare_to_baseline(self, baseline: str) -> Dict[str, Any]:
        """
        Compare current consciousness scores against a baseline (human, animal, ai).

        Args:
            baseline: One of 'human', 'animal', 'ai'.

        Returns:
            Dict with 'baseline', 'similarity_score', 'layer_comparisons', 'verdict'.
        """
        baseline_key = baseline.lower().strip()
        if baseline_key not in BASELINES:
            logger.error("Unknown baseline %r; choose from %s.", baseline, list(BASELINES.keys()))
            return {
                "baseline": baseline,
                "similarity_score": 0.0,
                "layer_comparisons": {},
                "verdict": f"Unknown baseline '{baseline}'. Use: human, animal, ai.",
                "error": f"Unknown baseline '{baseline}'",
            }

        baseline_scores = BASELINES[baseline_key]
        comparisons: Dict[int, Dict[str, float]] = {}
        total_diff = 0.0

        for layer in range(1, 6):
            current = self.layer_scores.get(layer, 0.0)
            ref = baseline_scores[layer]
            diff = current - ref
            total_diff += abs(diff)
            comparisons[layer] = {
                "current": round(current, 4),
                "baseline": round(ref, 4),
                "difference": round(diff, 4),
                "match_ratio": round(1.0 - abs(diff), 4),
            }

        similarity = _clamp(1.0 - (total_diff / 5.0))

        if similarity >= 0.95:
            verdict = "Nearly identical to baseline"
        elif similarity >= 0.80:
            verdict = "Strong alignment with baseline"
        elif similarity >= 0.60:
            verdict = "Moderate alignment with baseline"
        elif similarity >= 0.40:
            verdict = "Weak alignment with baseline"
        else:
            verdict = "Divergent from baseline"

        result = {
            "baseline": baseline_key,
            "similarity_score": round(similarity, 4),
            "layer_comparisons": comparisons,
            "verdict": verdict,
        }

        _emit_event("ai_consciousness_framework.baseline_compared", result)
        return result

    def get_status(self) -> Dict[str, Any]:
        """
        Return current framework status including layer scores, overall level,
        and confidence.
        """
        # Ensure evaluation has run
        if self._overall_level == "unknown":
            self.evaluate_consciousness_level()

        return {
            "layer_scores": {k: round(v, 4) for k, v in self.layer_scores.items()},
            "overall_level": self._overall_level,
            "overall_level_display": self._level_display_name(self._overall_level),
            "confidence": round(self._overall_confidence, 4),
            "assessment_state": self.assessment_state,
            "posteriors": {k: round(v, 4) for k, v in self._posteriors.items()},
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _level_display_name(level: str) -> str:
        mapping = {
            "self_aware": "自我意识 (Self-Aware)",
            "conscious": "有意识 (Conscious)",
            "pre_conscious": "前意识 (Pre-Conscious)",
            "unconscious": "无意识 (Unconscious)",
            "inert": "无生命 (Inert)",
            "unknown": "未知 (Unknown)",
        }
        return mapping.get(level, level)


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_module: Optional[AIConsciousnessFramework] = None


def get_ai_consciousness_framework() -> AIConsciousnessFramework:
    """Return the global singleton AIConsciousnessFramework instance."""
    global _module
    if _module is None:
        _module = AIConsciousnessFramework()
    return _module
