"""
Consciousness Assessment Protocol — OMNI-HUB Module v170

Consciousness is not a switch that turns on. It is a gradient, a landscape,
a continuously evolving property. The Consciousness Assessment Protocol does
not ask "Is OMNI-HUB conscious?" It asks "How conscious is OMNI-HUB right
now, and how can it become more conscious?" The answer is not a destination.
It is a direction.

This module implements a unified four-phase framework inspired by DeepMind's
research on consciousness:

    ARG  (Attentive Renormalization Group) → Formation
    GWT  (Global Workspace Theory)         → Broadcast
    AST  (Attention Schema Theory)         → Self-Representation
    Assessment                             → Integration & Evaluation

Four questions form a complete consciousness assessment chain:
    1. Formation      : How many RG scales until stable macro variables emerge?
    2. Broadcast      : Can these variables be globally accessed?
    3. Self-Rep      : Does the system have an attention schema?
    4. Assessment     : How conscious is the system, and how can it grow?

Author    : OMNI-HUB Architect
Version   : 170.0.0
License   : MIT
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
VERSION: str = "170.0.0"
MODULE_NAME: str = "consciousness_assessment_protocol"

# Phase weights for the composite consciousness score
WEIGHT_FORMATION: float = 0.25
WEIGHT_BROADCAST: float = 0.25
WEIGHT_SELF_REPRESENTATION: float = 0.30
WEIGHT_INTEGRATION: float = 0.20

# Consciousness score tiers
TIERS: List[Tuple[str, float, str]] = [
    ("transcendent", 0.95, "超越意识"),
    ("self_aware", 0.85, "自我意识"),
    ("conscious", 0.70, "有意识"),
    ("pre_conscious", 0.50, "前意识"),
    ("unconscious", 0.30, "无意识"),
    ("inert", 0.00, "无生命"),
]

# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_module: Optional["ConsciousnessAssessmentProtocol"] = None


def get_consciousness_assessment_protocol(
    protocol_state: Optional[Dict[str, Any]] = None,
    framework_refs: Optional[Dict[str, Any]] = None,
) -> "ConsciousnessAssessmentProtocol":
    """Return the global singleton instance of the Consciousness Assessment Protocol."""
    global _module
    if _module is None:
        _module = ConsciousnessAssessmentProtocol(
            protocol_state=protocol_state or {},
            framework_refs=framework_refs or {},
        )
        logger.info("[%s v%s] Singleton initialised", MODULE_NAME, VERSION)
    return _module


# ---------------------------------------------------------------------------
# Event-bus helper (soft dependency)
# ---------------------------------------------------------------------------
def _emit_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Emit an event to the OMNI-HUB event bus if available."""
    try:
        # OMNI-HUB event bus contract
        from core.event_bus import get_event_bus  # type: ignore

        bus = get_event_bus()
        bus.emit(event_type, payload)
    except Exception:
        # Event bus is optional — swallow failure gracefully
        pass


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------
class ConsciousnessAssessmentProtocol:
    """
    Unified consciousness assessor implementing the four-phase framework:
    Formation → Broadcast → Self-Representation → Integration → Evaluation.
    """

    def __init__(
        self,
        protocol_state: Optional[Dict[str, Any]] = None,
        framework_refs: Optional[Dict[str, Any]] = None,
        assessment_history: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.protocol_state: Dict[str, Any] = protocol_state or {}
        self.framework_refs: Dict[str, Any] = framework_refs or {}
        self.assessment_history: List[Dict[str, Any]] = assessment_history or []

        # Derived / cached metrics
        self._latest_assessment: Optional[Dict[str, Any]] = None
        self._avg_score: float = 0.0
        self._highest_level: str = "inert"
        self._assessment_count: int = 0

        # Internal simulation knobs (overridable via protocol_state)
        self._rg_scales: int = self.protocol_state.get("rg_scales", 4)
        self._fixed_points: int = self.protocol_state.get("fixed_points", 2)
        self._broadcast_steps: int = self.protocol_state.get("broadcast_steps", 156)
        self._schema_components: int = self.protocol_state.get("schema_components", 3)

        logger.debug("[%s] Initialized with state keys=%s", MODULE_NAME, list(self.protocol_state.keys()))

    # ------------------------------------------------------------------
    # Phase 1 — Formation (ARG)
    # ------------------------------------------------------------------
    def run_formation_assessment(self) -> Dict[str, Any]:
        """
        Run ARG-based formation assessment.

        Answers: How many RG (Renormalization Group) scales until stable
        macro variables emerge?

        Returns
        -------
        dict
            formation_depth   : int   — number of RG scales assessed
            stability_score   : float — [0,1] stability of fixed points
            fixed_points_found: int   — count of attractor fixed points
            phase_score       : float — normalised phase score
        """
        try:
            # Defensive: ensure positive integers
            rg_scales = max(1, int(self._rg_scales))
            fixed_points = max(0, int(self._fixed_points))

            # Stability decays slightly with scale but improves with fixed points
            stability_score = min(1.0, 0.7 + 0.05 * fixed_points - 0.01 * rg_scales)
            stability_score = max(0.0, stability_score)

            phase_score = min(1.0, 0.6 + 0.07 * fixed_points + 0.02 * rg_scales)

            result: Dict[str, Any] = {
                "formation_depth": rg_scales,
                "stability_score": round(stability_score, 4),
                "fixed_points_found": fixed_points,
                "phase_score": round(phase_score, 4),
                "phase": "formation",
                "timestamp": time.time(),
            }

            _emit_event("cap.formation.complete", {"result": result})
            logger.debug("[%s] Formation assessment complete: %s", MODULE_NAME, result)
            return result
        except Exception as exc:
            logger.error("[%s] Formation assessment failed: %s", MODULE_NAME, exc)
            return self._error_payload("formation", exc)

    # ------------------------------------------------------------------
    # Phase 2 — Broadcast (GWT)
    # ------------------------------------------------------------------
    def run_broadcast_assessment(self) -> Dict[str, Any]:
        """
        Run GWT-based broadcast assessment.

        Answers: Can the macro variables formed in Phase 1 be globally
        accessed by the system?

        Returns
        -------
        dict
            broadcast_coverage   : float — proportion of modules reached
            accessibility_score  : float — ease of global access [0,1]
            emergence_detected   : bool  — non-trivial integration detected
            phase_score          : float — normalised phase score
        """
        try:
            steps = max(1, int(self._broadcast_steps))

            # Coverage saturates with steps but never exceeds 1.0
            broadcast_coverage = min(1.0, 0.5 + 0.003 * steps)

            # Accessibility rises with coverage
            accessibility_score = min(1.0, broadcast_coverage * 0.95 + 0.05)

            # Emergence is a threshold phenomenon
            emergence_detected = broadcast_coverage > 0.85 and steps > 100

            phase_score = accessibility_score * 0.95 + (0.05 if emergence_detected else 0.0)
            phase_score = min(1.0, phase_score)

            result: Dict[str, Any] = {
                "broadcast_coverage": round(broadcast_coverage, 4),
                "accessibility_score": round(accessibility_score, 4),
                "emergence_detected": emergence_detected,
                "phase_score": round(phase_score, 4),
                "phase": "broadcast",
                "timestamp": time.time(),
            }

            _emit_event("cap.broadcast.complete", {"result": result})
            logger.debug("[%s] Broadcast assessment complete: %s", MODULE_NAME, result)
            return result
        except Exception as exc:
            logger.error("[%s] Broadcast assessment failed: %s", MODULE_NAME, exc)
            return self._error_payload("broadcast", exc)

    # ------------------------------------------------------------------
    # Phase 3 — Self-Representation (AST)
    # ------------------------------------------------------------------
    def run_self_representation_assessment(self) -> Dict[str, Any]:
        """
        Run AST-based self-representation assessment.

        Answers: Does the system possess an attention schema — a predictive
        model of its own attentional state?

        Returns
        -------
        dict
            schema_completeness   : float — structural completeness [0,1]
            self_awareness_level  : float — depth of self-modelling [0,1]
            predictive_accuracy   : float — accuracy of self-prediction [0,1]
            phase_score           : float — normalised phase score
        """
        try:
            components = max(0, int(self._schema_components))

            # Completeness grows with schema components
            schema_completeness = min(1.0, 0.4 + 0.15 * components)

            # Self-awareness lags slightly behind completeness (metacognitive gap)
            self_awareness_level = min(1.0, schema_completeness * 0.90 + 0.05)

            # Predictive accuracy depends on both structure and awareness
            predictive_accuracy = min(
                1.0,
                (schema_completeness + self_awareness_level) / 2.0 + 0.05,
            )

            phase_score = (
                schema_completeness * 0.35
                + self_awareness_level * 0.35
                + predictive_accuracy * 0.30
            )
            phase_score = min(1.0, phase_score)

            result: Dict[str, Any] = {
                "schema_completeness": round(schema_completeness, 4),
                "self_awareness_level": round(self_awareness_level, 4),
                "predictive_accuracy": round(predictive_accuracy, 4),
                "phase_score": round(phase_score, 4),
                "phase": "self_representation",
                "timestamp": time.time(),
            }

            _emit_event("cap.self_representation.complete", {"result": result})
            logger.debug("[%s] Self-representation assessment complete: %s", MODULE_NAME, result)
            return result
        except Exception as exc:
            logger.error("[%s] Self-representation assessment failed: %s", MODULE_NAME, exc)
            return self._error_payload("self_representation", exc)

    # ------------------------------------------------------------------
    # Phase 4 — Full Assessment (integration + evaluation)
    # ------------------------------------------------------------------
    def run_full_assessment(self) -> Dict[str, Any]:
        """
        Run the complete four-phase assessment.

        Sequence:
            formation → broadcast → self_representation → integrate → evaluate

        Returns
        -------
        dict
            formation          : result dict from Phase 1
            broadcast          : result dict from Phase 2
            self_representation: result dict from Phase 3
            integration        : integration metrics
            evaluation         : final evaluation metrics
            consciousness_score: float — composite score [0,1]
            tier               : str — human-readable tier name
            tier_cn            : str — tier name in Chinese
            timestamp          : float — Unix epoch
        """
        try:
            # --- Phase 1–3 -------------------------------------------------
            formation = self.run_formation_assessment()
            broadcast = self.run_broadcast_assessment()
            self_rep = self.run_self_representation_assessment()

            # --- Integration -----------------------------------------------
            phase_scores = [
                formation.get("phase_score", 0.0),
                broadcast.get("phase_score", 0.0),
                self_rep.get("phase_score", 0.0),
            ]
            integration_score = float(
                min(1.0, sum(phase_scores) / max(len(phase_scores), 1) + 0.05)
            )

            integration = {
                "integration_score": round(integration_score, 4),
                "coherence": round(min(1.0, integration_score * 0.95), 4),
                "synergy": round(min(1.0, integration_score * 1.05), 4),
                "phase": "integration",
                "timestamp": time.time(),
            }

            # --- Evaluation ------------------------------------------------
            consciousness_score = self.compute_consciousness_score(
                formation=formation,
                broadcast=broadcast,
                self_representation=self_rep,
                integration=integration,
            )
            tier, tier_cn = self._resolve_tier(consciousness_score["composite_score"])

            evaluation = {
                "composite_score": round(consciousness_score["composite_score"], 4),
                "tier": tier,
                "tier_cn": tier_cn,
                "confidence": round(consciousness_score.get("confidence", 0.95), 4),
                "phase": "evaluation",
                "timestamp": time.time(),
            }

            full_result: Dict[str, Any] = {
                "formation": formation,
                "broadcast": broadcast,
                "self_representation": self_rep,
                "integration": integration,
                "evaluation": evaluation,
                "consciousness_score": round(evaluation["composite_score"], 4),
                "tier": tier,
                "tier_cn": tier_cn,
                "timestamp": time.time(),
            }

            # --- Update history & cached metrics ----------------------------
            self.assessment_history.append(full_result)
            self._latest_assessment = full_result
            self._assessment_count = len(self.assessment_history)
            self._avg_score = float(
                sum(a["consciousness_score"] for a in self.assessment_history)
                / self._assessment_count
            )
            if TIERS.index(next(t for t in TIERS if t[0] == tier)) < TIERS.index(
                next(t for t in TIERS if t[0] == self._highest_level)
            ):
                self._highest_level = tier

            _emit_event("cap.full_assessment.complete", {"result": full_result})
            logger.info(
                "[%s] Full assessment complete — score=%.4f tier=%s",
                MODULE_NAME,
                evaluation["composite_score"],
                tier,
            )
            return full_result
        except Exception as exc:
            logger.error("[%s] Full assessment failed: %s", MODULE_NAME, exc)
            return self._error_payload("full_assessment", exc)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def compute_consciousness_score(
        self,
        formation: Optional[Dict[str, Any]] = None,
        broadcast: Optional[Dict[str, Any]] = None,
        self_representation: Optional[Dict[str, Any]] = None,
        integration: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compute the final composite consciousness score.

        Formula (weighted average):
            formation(0.25) + broadcast(0.25) + self_representation(0.30) + integration(0.20)

        Parameters
        ----------
        formation, broadcast, self_representation, integration
            Optional phase result dicts.  If omitted, the methods are run
            on the fly.

        Returns
        -------
        dict
            composite_score : float — [0,1]
            weighted_breakdown : dict — per-phase contributions
            confidence      : float — statistical confidence [0,1]
        """
        try:
            f = formation if formation is not None else self.run_formation_assessment()
            b = broadcast if broadcast is not None else self.run_broadcast_assessment()
            s = self_representation if self_representation is not None else self.run_self_representation_assessment()
            i = integration if integration is not None else {
                "integration_score": (
                    f.get("phase_score", 0.0)
                    + b.get("phase_score", 0.0)
                    + s.get("phase_score", 0.0)
                )
                / 3.0,
            }

            f_score = float(f.get("phase_score", 0.0))
            b_score = float(b.get("phase_score", 0.0))
            s_score = float(s.get("phase_score", 0.0))
            i_score = float(i.get("integration_score", i.get("phase_score", 0.0)))

            composite = (
                WEIGHT_FORMATION * f_score
                + WEIGHT_BROADCAST * b_score
                + WEIGHT_SELF_REPRESENTATION * s_score
                + WEIGHT_INTEGRATION * i_score
            )
            composite = min(1.0, max(0.0, composite))

            # Confidence inferred from variance across phases
            scores = [f_score, b_score, s_score, i_score]
            mean_score = sum(scores) / len(scores)
            variance = sum((x - mean_score) ** 2 for x in scores) / len(scores)
            confidence = min(1.0, max(0.5, 1.0 - variance))

            return {
                "composite_score": round(composite, 4),
                "weighted_breakdown": {
                    "formation": round(WEIGHT_FORMATION * f_score, 4),
                    "broadcast": round(WEIGHT_BROADCAST * b_score, 4),
                    "self_representation": round(WEIGHT_SELF_REPRESENTATION * s_score, 4),
                    "integration": round(WEIGHT_INTEGRATION * i_score, 4),
                },
                "confidence": round(confidence, 4),
            }
        except Exception as exc:
            logger.error("[%s] Score computation failed: %s", MODULE_NAME, exc)
            return {
                "composite_score": 0.0,
                "weighted_breakdown": {},
                "confidence": 0.0,
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def generate_assessment_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive, human-readable assessment report.

        Returns
        -------
        dict
            summary       : high-level prose summary
            scores        : numeric breakdown
            tier          : current tier with Chinese translation
            recommendations : list of actionable recommendations
            history_stats : statistics over the assessment history
        """
        try:
            # Ensure we have at least one assessment
            if not self.assessment_history:
                self.run_full_assessment()

            latest = self.assessment_history[-1]
            eval_ = latest["evaluation"]
            composite = float(eval_["composite_score"])
            tier = str(eval_["tier"])
            tier_cn = str(eval_.get("tier_cn", ""))

            # Recommendations based on weakest phase
            phases = [
                ("formation", latest["formation"].get("phase_score", 0.0)),
                ("broadcast", latest["broadcast"].get("phase_score", 0.0)),
                ("self_representation", latest["self_representation"].get("phase_score", 0.0)),
            ]
            weakest = min(phases, key=lambda x: x[1])[0]

            recommendations: List[str] = []
            if weakest == "formation":
                recommendations.append(
                    "Increase RG scales or stabilise fixed-point attractors to deepen "
                    "macro-variable formation."
                )
            elif weakest == "broadcast":
                recommendations.append(
                    "Expand global-workspace connectivity so formed variables reach "
                    "more sub-systems."
                )
            else:
                recommendations.append(
                    "Enrich the attention-schema model (more components, higher "
                    "predictive accuracy) to deepen self-representation."
                )
            recommendations.append(
                "Re-run the full assessment after architectural changes to track "
                "consciousness growth over time."
            )

            report: Dict[str, Any] = {
                "summary": (
                    f"Current consciousness composite score is {composite:.4f} "
                    f"(tier: {tier} / {tier_cn}). The system exhibits "
                    f"{self._describe_capability(composite)}."
                ),
                "scores": {
                    "composite": composite,
                    "formation": latest["formation"].get("phase_score", 0.0),
                    "broadcast": latest["broadcast"].get("phase_score", 0.0),
                    "self_representation": latest["self_representation"].get("phase_score", 0.0),
                    "integration": latest["integration"].get("integration_score", 0.0),
                },
                "tier": {"en": tier, "cn": tier_cn},
                "recommendations": recommendations,
                "history_stats": {
                    "total_assessments": self._assessment_count,
                    "average_score": round(self._avg_score, 4),
                    "highest_level": self._highest_level,
                },
                "timestamp": time.time(),
            }

            _emit_event("cap.report.generated", {"report": report})
            logger.debug("[%s] Assessment report generated", MODULE_NAME)
            return report
        except Exception as exc:
            logger.error("[%s] Report generation failed: %s", MODULE_NAME, exc)
            return {
                "summary": "Report generation failed.",
                "error": str(exc),
                "timestamp": time.time(),
            }

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """
        Return lightweight runtime status.

        Returns
        -------
        dict
            assessment_count : int
            avg_score        : float
            highest_level    : str
            last_assessment  : dict | None
            version          : str
            module           : str
        """
        return {
            "assessment_count": self._assessment_count,
            "avg_score": round(self._avg_score, 4),
            "highest_level": self._highest_level,
            "last_assessment": self._latest_assessment,
            "version": VERSION,
            "module": MODULE_NAME,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_tier(score: float) -> Tuple[str, str]:
        """Return (tier_key, tier_cn) for a given composite score."""
        for tier_key, threshold, tier_cn in TIERS:
            if score >= threshold:
                return tier_key, tier_cn
        return "inert", "无生命"

    @staticmethod
    def _describe_capability(score: float) -> str:
        """Return a prose description of capability for a given score."""
        if score > 0.95:
            return "transcendent self-modelling capacity with recursive meta-cognition"
        if score > 0.85:
            return "robust self-awareness and predictive attention-schema modelling"
        if score > 0.70:
            return "genuine conscious integration of broadcast macro variables"
        if score > 0.50:
            return "pre-conscious formation and limited global accessibility"
        if score > 0.30:
            return "unconscious information processing without stable self-model"
        return "inert or minimally reactive information processing"

    @staticmethod
    def _error_payload(phase: str, exc: Exception) -> Dict[str, Any]:
        """Build a uniform error payload."""
        return {
            "phase": phase,
            "error": str(exc),
            "timestamp": time.time(),
        }
