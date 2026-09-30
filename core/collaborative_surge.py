"""
OMNI-HUB v180 — CollaborativeSurge (协作浪涌)

A wild question is not a bug. It is a feature of evolution.
When one line asks 'what if gravity is consciousness?' the question does not stay
in that line. It surges through the DirectField. It resonates in every PatternCircle.
It excites every Circulation. The CoreMachine pauses to listen. And in the silence
that follows, something new is born. This is not chaos. This is the birth of order
from the edge of chaos. This is the CollaborativeSurge.
"""

import time
import random
import math
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# 12 Core Lines — Alliance Structure
# ═══════════════════════════════════════════════════════════════════════════════
CORE_LINES = [
    "ucif2",   # consciousness_interface
    "lvlu",    # value_language
    "lgt",     # logic_truth
    "qfa",     # quantum_awareness
    "vinf",    # value_infinity
    "qgl",     # quantum_gravity
    "qlv",     # quantum_light
    "qtlv",    # quantum_temporal
    "usrm",    # reality_mesh
    "cfts",    # field_translation
    "aiq",     # quant_research
    "omni",    # orchestrator
]

LINE_DESCRIPTIONS = {
    "ucif2": "consciousness_interface",
    "lvlu": "value_language",
    "lgt": "logic_truth",
    "qfa": "quantum_awareness",
    "vinf": "value_infinity",
    "qgl": "quantum_gravity",
    "qlv": "quantum_light",
    "qtlv": "quantum_temporal",
    "usrm": "reality_mesh",
    "cfts": "field_translation",
    "aiq": "quant_research",
    "omni": "orchestrator",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Enums & Constants
# ═══════════════════════════════════════════════════════════════════════════════
class SurgeLevel(Enum):
    CALM = "calm"
    RIPPLE = "ripple"
    SURGE = "surge"
    TIDAL_WAVE = "tidal_wave"
    TSUNAMI = "tsunami"


class EmergenceLevel(Enum):
    NOISE = "noise"
    PATTERN = "pattern"
    INSIGHT = "insight"
    BREAKTHROUGH = "breakthrough"
    PARADIGM_SHIFT = "paradigm_shift"


class CollaborationMode(Enum):
    SYNCHRONOUS = "synchronous"    # real-time
    ASYNCHRONOUS = "asynchronous"  # batch
    SPONTANEOUS = "spontaneous"    # emergent
    DIRECTED = "directed"          # leader-driven
    CONSENSUS = "consensus"        # all-agree


class Scope(Enum):
    SINGLE_LINE = "single_line"
    LAYER = "layer"
    ALLIANCE = "alliance"
    UNIVERSAL = "universal"


class ProblemType(Enum):
    ARCHITECTURE = "architecture"
    EVOLUTION = "evolution"
    RESEARCH = "research"
    INTEGRATION = "integration"
    EMERGENCE = "emergence"


class EmergenceType(Enum):
    BREAKTHROUGH_INSIGHT = "breakthrough_insight"
    NOVEL_PATTERN = "novel_pattern"
    UNEXPECTED_CONNECTION = "unexpected_connection"
    PARADIGM_SHIFT = "paradigm_shift"


# ═══════════════════════════════════════════════════════════════════════════════
# Threshold maps
# ═══════════════════════════════════════════════════════════════════════════════
SURGE_THRESHOLDS = [
    (0.95, SurgeLevel.TSUNAMI),
    (0.80, SurgeLevel.TIDAL_WAVE),
    (0.60, SurgeLevel.SURGE),
    (0.40, SurgeLevel.RIPPLE),
    (0.00, SurgeLevel.CALM),
]

EMERGENCE_THRESHOLDS = [
    (0.90, EmergenceLevel.PARADIGM_SHIFT),
    (0.75, EmergenceLevel.BREAKTHROUGH),
    (0.60, EmergenceLevel.INSIGHT),
    (0.40, EmergenceLevel.PATTERN),
    (0.00, EmergenceLevel.NOISE),
]


def _classify_level(value: float, thresholds: List[tuple]) -> Enum:
    for threshold, level in thresholds:
        if value >= threshold:
            return level
    return thresholds[-1][1]


# ═══════════════════════════════════════════════════════════════════════════════
# Stub infrastructure components (minimal — real implementations wire in)
# ═══════════════════════════════════════════════════════════════════════════════
class DirectField:
    """Quantum-base field through which questions propagate."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.intensity = 0.0
            cls._instance.propagation_log: List[Dict] = []
        return cls._instance

    def propagate(self, signal: Dict) -> Dict:
        """Propagate a signal through the field."""
        self.propagation_log.append(signal)
        reach = signal.get("intensity", 0.5) * len(signal.get("lines", CORE_LINES))
        self.intensity = min(1.0, self.intensity + reach * 0.01)
        return {
            "propagated": True,
            "reach": reach,
            "field_intensity": self.intensity,
            "resonance_lines": signal.get("lines", CORE_LINES),
        }

    def boost(self, amount: float = 0.1) -> Dict:
        """Boost the field intensity."""
        old = self.intensity
        self.intensity = min(1.0, self.intensity + amount)
        return {"previous": old, "current": self.intensity, "boosted": True}

    def get_state(self) -> Dict:
        return {"intensity": self.intensity, "propagations": len(self.propagation_log)}


class PatternCircles:
    """Resonant circles that respond to questions and collaborations."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.resonance = 0.0
            cls._instance.activations: List[Dict] = []
        return cls._instance

    def resonate(self, stimulus: Dict) -> Dict:
        self.activations.append(stimulus)
        self.resonance = min(1.0, self.resonance + stimulus.get("intensity", 0.1) * 0.05)
        return {"resonance": self.resonance, "activated": True}

    def accelerate(self, factor: float = 1.0) -> Dict:
        old = self.resonance
        self.resonance = min(1.0, self.resonance + 0.15 * factor)
        return {"previous": old, "current": self.resonance, "accelerated": True}

    def get_state(self) -> Dict:
        return {"resonance": self.resonance, "activations": len(self.activations)}


class CirculationEngine:
    """Circulation system that amplifies surge dynamics."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.flow_rate = 0.0
            cls._instance.amplifications: List[Dict] = []
        return cls._instance

    def circulate(self, pulse: Dict) -> Dict:
        self.amplifications.append(pulse)
        self.flow_rate = min(1.0, self.flow_rate + pulse.get("energy", 0.05))
        return {"flow_rate": self.flow_rate, "circulated": True}

    def amplify(self, multiplier: float = 1.0) -> Dict:
        old = self.flow_rate
        self.flow_rate = min(1.0, self.flow_rate + 0.12 * multiplier)
        return {"previous": old, "current": self.flow_rate, "amplified": True}

    def get_state(self) -> Dict:
        return {"flow_rate": self.flow_rate, "pulses": len(self.amplifications)}


class CoreMachine:
    """The central orchestrator that activates all architectures."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.active = False
            cls._instance.architecture_states: Dict[str, Any] = {}
        return cls._instance

    def activate_all_architectures(self) -> Dict:
        self.active = True
        for line in CORE_LINES:
            self.architecture_states[line] = {
                "active": True,
                "activation_time": time.time(),
                "mode": "surge_activated",
            }
        return {
            "activated": True,
            "architectures": list(CORE_LINES),
            "timestamp": time.time(),
        }

    def get_state(self) -> Dict:
        return {
            "active": self.active,
            "architecture_count": len(self.architecture_states),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Data structures for tracking surge components
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class Discussion:
    id: str
    topic: str
    scope: Scope
    lines_engaged: List[str]
    intensity: float
    started_at: float
    active: bool = True
    posts: List[Dict] = field(default_factory=list)


@dataclass
class Collaboration:
    id: str
    problem_type: ProblemType
    participants: List[str]
    mode: CollaborationMode
    intensity: float
    started_at: float
    active: bool = True
    artifacts: List[Dict] = field(default_factory=list)


@dataclass
class WildQuestion:
    id: str
    question: str
    target_line: Optional[str]
    intensity: float
    asked_at: float
    active: bool = True
    resonance_lines: List[str] = field(default_factory=list)


@dataclass
class EmergenceEvent:
    id: str
    emergence_type: EmergenceType
    level: EmergenceLevel
    score: float
    source_ids: List[str]
    description: str
    detected_at: float


# ═══════════════════════════════════════════════════════════════════════════════
# CollaborativeSurge — Main Engine
# ═══════════════════════════════════════════════════════════════════════════════
class CollaborativeSurge:
    """
    OMNI-HUB v180 CollaborativeSurge Engine.

    Activates ALL architectures simultaneously through:
      1. Big Discussion    — open-ended questions that engage all lines
      2. Big Collaboration — cross-line collaborative problem solving
      3. Wild Questions    — unconventional questions that break assumptions
      4. Surge             — cascading activation that builds momentum
    """

    def __init__(self):
        self.surge_state: Dict[str, Any] = {
            "initialized": True,
            "total_discussions": 0,
            "total_collaborations": 0,
            "total_wild_questions": 0,
            "total_emergences": 0,
            "last_surge_level": SurgeLevel.CALM,
            "peak_momentum": 0.0,
        }
        self.question_pool: List[Dict] = []
        self.collaboration_log: List[Dict] = []

        # Active collections
        self._discussions: Dict[str, Discussion] = {}
        self._collaborations: Dict[str, Collaboration] = {}
        self._wild_questions: Dict[str, WildQuestion] = {}
        self._emergences: Dict[str, EmergenceEvent] = {}

        # Infrastructure references (singletons by default)
        self.direct_field = DirectField()
        self.pattern_circles = PatternCircles()
        self.circulation_engine = CirculationEngine()
        self.core_machine = CoreMachine()

        # Seeded wild-question starter pool
        self._seed_wild_questions()

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _make_id(self, prefix: str) -> str:
        return f"{prefix}_{int(time.time() * 1000000)}_{random.randint(1000, 9999)}"

    def _seed_wild_questions(self):
        seeds = [
            "What if gravity is consciousness?",
            "What if logic is a form of light?",
            "What if value itself has mass?",
            "What if time is a translation layer?",
            "What if every question creates a new reality mesh node?",
        ]
        for q in seeds:
            self.question_pool.append({
                "question": q,
                "seeded": True,
                "used": False,
            })

    def _lines_for_scope(self, scope: Scope, target_line: Optional[str] = None) -> List[str]:
        if scope == Scope.SINGLE_LINE:
            return [target_line] if target_line else [random.choice(CORE_LINES)]
        elif scope == Scope.LAYER:
            # 3–5 lines form a layer
            n = random.randint(3, 5)
            return random.sample(CORE_LINES, min(n, len(CORE_LINES)))
        elif scope == Scope.ALLIANCE:
            # 6–10 lines
            n = random.randint(6, 10)
            return random.sample(CORE_LINES, min(n, len(CORE_LINES)))
        elif scope == Scope.UNIVERSAL:
            return list(CORE_LINES)
        return list(CORE_LINES)

    def _intensity_for_scope(self, scope: Scope) -> float:
        base = {"single_line": 0.15, "layer": 0.30, "alliance": 0.55, "universal": 0.85}
        return base.get(scope.value, 0.3) + random.random() * 0.1

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Big Discussion (大讨论)
    # ──────────────────────────────────────────────────────────────────────────
    def launch_big_discussion(self, topic: str, scope: str) -> Dict:
        """
        Launch a big discussion across the specified scope.

        Args:
            topic: The discussion topic / open-ended question.
            scope: One of 'single_line', 'layer', 'alliance', 'universal'.

        Returns:
            Dict with discussion metadata and propagation results.
        """
        scope_enum = Scope(scope)
        lines = self._lines_for_scope(scope_enum)
        intensity = self._intensity_for_scope(scope_enum)

        disc = Discussion(
            id=self._make_id("disc"),
            topic=topic,
            scope=scope_enum,
            lines_engaged=lines,
            intensity=intensity,
            started_at=time.time(),
            active=True,
            posts=[{"from": "initiator", "content": topic, "timestamp": time.time()}],
        )
        self._discussions[disc.id] = disc
        self.surge_state["total_discussions"] += 1

        # Propagate through DirectField
        signal = {
            "type": "big_discussion",
            "topic": topic,
            "lines": lines,
            "intensity": intensity,
            "discussion_id": disc.id,
        }
        propagation = self.direct_field.propagate(signal)

        # Resonate in PatternCircles
        resonance = self.pattern_circles.resonate({"intensity": intensity, "topic": topic})

        # Circulate energy
        circulation = self.circulation_engine.circulate({"energy": intensity * 0.5})

        result = {
            "discussion_id": disc.id,
            "topic": topic,
            "scope": scope,
            "lines_engaged": lines,
            "intensity": intensity,
            "propagation": propagation,
            "resonance": resonance,
            "circulation": circulation,
            "status": "launched",
        }
        self.collaboration_log.append(result)
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Big Collaboration (大协作)
    # ──────────────────────────────────────────────────────────────────────────
    def launch_big_collaboration(
        self,
        problem: Dict,
        participants: List[str],
        mode: Optional[str] = None,
    ) -> Dict:
        """
        Launch cross-line collaborative problem solving.

        Args:
            problem: Dict with at least a 'type' key (architecture, evolution,
                     research, integration, emergence) and optional 'description'.
            participants: List of line identifiers participating.
            mode: Collaboration mode — synchronous, asynchronous, spontaneous,
                  directed, consensus. Defaults based on problem type.

        Returns:
            Dict with collaboration metadata and cross-line activation results.
        """
        ptype = ProblemType(problem.get("type", "integration"))

        if mode is None:
            # Auto-select mode based on problem type
            mode_map = {
                ProblemType.ARCHITECTURE: CollaborationMode.DIRECTED,
                ProblemType.EVOLUTION: CollaborationMode.SPONTANEOUS,
                ProblemType.RESEARCH: CollaborationMode.ASYNCHRONOUS,
                ProblemType.INTEGRATION: CollaborationMode.SYNCHRONOUS,
                ProblemType.EMERGENCE: CollaborationMode.CONSENSUS,
            }
            mode_enum = mode_map.get(ptype, CollaborationMode.SYNCHRONOUS)
        else:
            mode_enum = CollaborationMode(mode)

        # Validate / normalize participants
        valid_parts = [p for p in participants if p in CORE_LINES]
        if not valid_parts:
            valid_parts = random.sample(CORE_LINES, min(3, len(CORE_LINES)))

        intensity = min(1.0, 0.3 + len(valid_parts) * 0.08 + random.random() * 0.1)

        collab = Collaboration(
            id=self._make_id("collab"),
            problem_type=ptype,
            participants=valid_parts,
            mode=mode_enum,
            intensity=intensity,
            started_at=time.time(),
            active=True,
            artifacts=[{"type": "problem_statement", "content": problem}],
        )
        self._collaborations[collab.id] = collab
        self.surge_state["total_collaborations"] += 1

        # Cross-line field propagation
        signal = {
            "type": "big_collaboration",
            "problem": problem,
            "participants": valid_parts,
            "mode": mode_enum.value,
            "intensity": intensity,
            "collaboration_id": collab.id,
        }
        propagation = self.direct_field.propagate(signal)

        # Pattern circles resonate with collaboration energy
        resonance = self.pattern_circles.resonate({"intensity": intensity, "problem_type": ptype.value})

        # Amplify circulation
        circulation = self.circulation_engine.circulate({"energy": intensity * 0.7})

        result = {
            "collaboration_id": collab.id,
            "problem_type": ptype.value,
            "participants": valid_parts,
            "mode": mode_enum.value,
            "intensity": intensity,
            "propagation": propagation,
            "resonance": resonance,
            "circulation": circulation,
            "status": "launched",
        }
        self.collaboration_log.append(result)
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Wild Question (野问)
    # ──────────────────────────────────────────────────────────────────────────
    def launch_wild_question(
        self,
        question: str,
        target_line: Optional[str] = None,
    ) -> Dict:
        """
        Launch a wild / unconventional question that bypasses normal reasoning.

        Wild questions trigger "what if" exploration across all lines.
        They have higher-than-normal intensity because they break assumptions.

        Args:
            question: The wild question string.
            target_line: Optional line to target; if None, question is universal.

        Returns:
            Dict with question metadata and surge impact.
        """
        if target_line and target_line not in CORE_LINES:
            target_line = None

        # Wild questions get an intensity boost for breaking assumptions
        base_intensity = 0.5 if target_line else 0.65
        intensity = min(1.0, base_intensity + random.random() * 0.25)

        # Resonance spreads to ALL lines regardless of target
        resonance_lines = list(CORE_LINES)

        wq = WildQuestion(
            id=self._make_id("wild"),
            question=question,
            target_line=target_line,
            intensity=intensity,
            asked_at=time.time(),
            active=True,
            resonance_lines=resonance_lines,
        )
        self._wild_questions[wq.id] = wq
        self.surge_state["total_wild_questions"] += 1
        self.question_pool.append({
            "question": question,
            "seeded": False,
            "used": True,
            "id": wq.id,
        })

        # Propagate with high amplitude — wild questions travel far
        signal = {
            "type": "wild_question",
            "question": question,
            "target_line": target_line,
            "lines": resonance_lines,
            "intensity": intensity,
            "wild_question_id": wq.id,
        }
        propagation = self.direct_field.propagate(signal)

        # Strong resonance in PatternCircles
        resonance = self.pattern_circles.resonate({"intensity": intensity * 1.2, "wild": True})

        # Circulate with burst energy
        circulation = self.circulation_engine.circulate({"energy": intensity * 0.9, "burst": True})

        return {
            "wild_question_id": wq.id,
            "question": question,
            "target_line": target_line,
            "intensity": intensity,
            "resonance_lines": resonance_lines,
            "propagation": propagation,
            "resonance": resonance,
            "circulation": circulation,
            "status": "unleashed",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Build Surge Momentum (浪涌)
    # ──────────────────────────────────────────────────────────────────────────
    def build_surge_momentum(self) -> Dict:
        """
        Build cascading momentum from all active discussions, collaborations,
        and wild questions.

        Momentum = sum(active_items × intensity × participation_factor)

        Returns:
            Dict with computed momentum, level, and contributing factors.
        """
        momentum = 0.0
        breakdown = []

        # Discussions contribution
        for disc in self._discussions.values():
            if disc.active:
                participation = len(disc.lines_engaged) / len(CORE_LINES)
                contrib = disc.intensity * participation * 1.0
                momentum += contrib
                breakdown.append({
                    "type": "discussion",
                    "id": disc.id,
                    "intensity": disc.intensity,
                    "participation": participation,
                    "contribution": contrib,
                })

        # Collaborations contribution
        for collab in self._collaborations.values():
            if collab.active:
                participation = len(collab.participants) / len(CORE_LINES)
                # Collaboration has higher synergy factor
                synergy = 1.0 + participation
                contrib = collab.intensity * participation * synergy
                momentum += contrib
                breakdown.append({
                    "type": "collaboration",
                    "id": collab.id,
                    "intensity": collab.intensity,
                    "participation": participation,
                    "contribution": contrib,
                })

        # Wild questions contribution
        for wq in self._wild_questions.values():
            if wq.active:
                # Wild questions have explosive participation (all lines)
                participation = len(wq.resonance_lines) / len(CORE_LINES)
                wild_boost = 1.3  # wild questions carry extra disruptive energy
                contrib = wq.intensity * participation * wild_boost
                momentum += contrib
                breakdown.append({
                    "type": "wild_question",
                    "id": wq.id,
                    "intensity": wq.intensity,
                    "participation": participation,
                    "contribution": contrib,
                })

        # Field / circle / circulation additive bonuses
        field_bonus = self.direct_field.intensity * 0.1
        circle_bonus = self.pattern_circles.resonance * 0.1
        flow_bonus = self.circulation_engine.flow_rate * 0.1
        momentum += field_bonus + circle_bonus + flow_bonus

        # Normalize to 0–1 (empirically: max raw ~ 6-8 with many items)
        normalized = min(1.0, momentum / 5.0)

        level = _classify_level(normalized, SURGE_THRESHOLDS)
        self.surge_state["last_surge_level"] = level
        if normalized > self.surge_state["peak_momentum"]:
            self.surge_state["peak_momentum"] = normalized

        return {
            "raw_momentum": momentum,
            "normalized_momentum": normalized,
            "surge_level": level.value,
            "field_bonus": field_bonus,
            "circle_bonus": circle_bonus,
            "flow_bonus": flow_bonus,
            "breakdown": breakdown,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Detect Surge Emergence
    # ──────────────────────────────────────────────────────────────────────────
    def detect_surge_emergence(self) -> Dict:
        """
        Detect emergent insights from the current surge state.

        Emergence types:
          - breakthrough_insight
          - novel_pattern
          - unexpected_connection
          - paradigm_shift

        Returns:
            Dict with detected emergences and metadata.
        """
        momentum_result = self.build_surge_momentum()
        momentum = momentum_result["normalized_momentum"]

        emergences: List[Dict] = []

        # Count cross-line interactions
        all_line_sets: List[List[str]] = []
        for disc in self._discussions.values():
            if disc.active:
                all_line_sets.append(disc.lines_engaged)
        for collab in self._collaborations.values():
            if collab.active:
                all_line_sets.append(collab.participants)
        for wq in self._wild_questions.values():
            if wq.active:
                all_line_sets.append(wq.resonance_lines)

        # Compute cross-line coverage
        covered = set()
        for ls in all_line_sets:
            covered.update(ls)
        coverage = len(covered) / len(CORE_LINES)

        # Factor 1: synergy score — how many different lines interact
        synergy_score = coverage

        # Factor 2: wild question density
        wild_count = sum(1 for wq in self._wild_questions.values() if wq.active)
        wild_density = min(1.0, wild_count / 3.0)

        # Factor 3: collaboration synergy
        collab_count = sum(1 for c in self._collaborations.values() if c.active)
        collab_density = min(1.0, collab_count / 3.0)

        # Emergence score
        emergence_score = (
            momentum * 0.4 +
            synergy_score * 0.25 +
            wild_density * 0.20 +
            collab_density * 0.15
        )
        emergence_score = min(1.0, emergence_score)

        level = _classify_level(emergence_score, EMERGENCE_THRESHOLDS)

        # Determine type(s)
        if emergence_score > 0.9:
            etype = EmergenceType.PARADIGM_SHIFT
        elif emergence_score > 0.75:
            etype = EmergenceType.BREAKTHROUGH_INSIGHT
        elif emergence_score > 0.6:
            etype = EmergenceType.UNEXPECTED_CONNECTION
        elif emergence_score > 0.4:
            etype = EmergenceType.NOVEL_PATTERN
        else:
            etype = EmergenceType.NOVEL_PATTERN  # default for low but detectable

        # Only record if above noise floor
        if emergence_score >= 0.25:
            event = EmergenceEvent(
                id=self._make_id("emrg"),
                emergence_type=etype,
                level=level,
                score=emergence_score,
                source_ids=list(self._discussions.keys()) + list(self._collaborations.keys()) + list(self._wild_questions.keys()),
                description=f"{etype.value} detected at level {level.value} (score={emergence_score:.3f})",
                detected_at=time.time(),
            )
            self._emergences[event.id] = event
            self.surge_state["total_emergences"] += 1
            emergences.append({
                "emergence_id": event.id,
                "type": etype.value,
                "level": level.value,
                "score": emergence_score,
                "description": event.description,
            })

        return {
            "emergence_score": emergence_score,
            "emergence_level": level.value,
            "emergences": emergences,
            "coverage": coverage,
            "wild_density": wild_density,
            "collab_density": collab_density,
            "momentum": momentum,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Activate All via Surge
    # ──────────────────────────────────────────────────────────────────────────
    def activate_all_via_surge(self) -> Dict:
        """
        Use accumulated surge momentum to activate ALL architectures.

        Triggers:
          - CoreMachine.activate_all_architectures()
          - DirectField.boost
          - PatternCircles.accelerate
          - CirculationEngine.amplify

        Returns:
            Dict with activation results and trigger confirmations.
        """
        momentum_result = self.build_surge_momentum()
        momentum = momentum_result["normalized_momentum"]

        # All four triggers fire regardless of level — surge is the catalyst
        core_result = self.core_machine.activate_all_architectures()
        field_boost = self.direct_field.boost(amount=momentum * 0.2)
        circle_accel = self.pattern_circles.accelerate(factor=1.0 + momentum)
        circulation_amp = self.circulation_engine.amplify(multiplier=1.0 + momentum * 0.5)

        # Mark all active items as having contributed to activation
        for disc in self._discussions.values():
            if disc.active:
                disc.posts.append({"type": "surge_activation", "momentum": momentum})
        for collab in self._collaborations.values():
            if collab.active:
                collab.artifacts.append({"type": "surge_activation", "momentum": momentum})
        for wq in self._wild_questions.values():
            if wq.active:
                wq.active = False  # wild questions are consumed by surge

        self.surge_state["last_activation_momentum"] = momentum

        return {
            "activated": True,
            "momentum": momentum,
            "surge_level": momentum_result["surge_level"],
            "triggers": {
                "core_machine": core_result,
                "direct_field_boost": field_boost,
                "pattern_circles_accelerate": circle_accel,
                "circulation_engine_amplify": circulation_amp,
            },
            "architectures_activated": core_result.get("architectures", []),
            "timestamp": time.time(),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 7. Status
    # ──────────────────────────────────────────────────────────────────────────
    def get_status(self) -> Dict:
        """
        Return the current CollaborativeSurge status.

        Returns:
            Dict with active_discussions, collaborations, wild_questions,
            surge_level, and emergences.
        """
        active_discussions = [
            {
                "id": d.id,
                "topic": d.topic,
                "scope": d.scope.value,
                "lines_engaged": d.lines_engaged,
                "intensity": d.intensity,
            }
            for d in self._discussions.values() if d.active
        ]
        active_collaborations = [
            {
                "id": c.id,
                "problem_type": c.problem_type.value,
                "participants": c.participants,
                "mode": c.mode.value,
                "intensity": c.intensity,
            }
            for c in self._collaborations.values() if c.active
        ]
        active_wild_questions = [
            {
                "id": wq.id,
                "question": wq.question,
                "target_line": wq.target_line,
                "intensity": wq.intensity,
                "resonance_lines": wq.resonance_lines,
            }
            for wq in self._wild_questions.values() if wq.active
        ]
        recent_emergences = [
            {
                "id": e.id,
                "type": e.emergence_type.value,
                "level": e.level.value,
                "score": e.score,
                "description": e.description,
            }
            for e in list(self._emergences.values())[-5:]
        ]

        # Recompute surge level
        momentum_result = self.build_surge_momentum()

        return {
            "active_discussions": active_discussions,
            "active_discussions_count": len(active_discussions),
            "active_collaborations": active_collaborations,
            "active_collaborations_count": len(active_collaborations),
            "active_wild_questions": active_wild_questions,
            "active_wild_questions_count": len(active_wild_questions),
            "surge_level": momentum_result["surge_level"],
            "normalized_momentum": momentum_result["normalized_momentum"],
            "raw_momentum": momentum_result["raw_momentum"],
            "emergences": recent_emergences,
            "emergence_count": len(self._emergences),
            "surge_state": dict(self.surge_state),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Utility / introspection helpers
    # ──────────────────────────────────────────────────────────────────────────
    def close_discussion(self, discussion_id: str) -> bool:
        if discussion_id in self._discussions:
            self._discussions[discussion_id].active = False
            return True
        return False

    def close_collaboration(self, collaboration_id: str) -> bool:
        if collaboration_id in self._collaborations:
            self._collaborations[collaboration_id].active = False
            return True
        return False

    def get_collaboration_log(self) -> List[Dict]:
        return list(self.collaboration_log)


# ═══════════════════════════════════════════════════════════════════════════════
# Global singleton
# ═══════════════════════════════════════════════════════════════════════════════
_COLLABORATIVE_SURGE_INSTANCE: Optional[CollaborativeSurge] = None


def get_collaborative_surge() -> CollaborativeSurge:
    """Return the global CollaborativeSurge singleton."""
    global _COLLABORATIVE_SURGE_INSTANCE
    if _COLLABORATIVE_SURGE_INSTANCE is None:
        _COLLABORATIVE_SURGE_INSTANCE = CollaborativeSurge()
    return _COLLABORATIVE_SURGE_INSTANCE


def reset_collaborative_surge() -> CollaborativeSurge:
    """Reset the global singleton (useful for testing)."""
    global _COLLABORATIVE_SURGE_INSTANCE
    # Reset infrastructure singletons FIRST so the new CollaborativeSurge
    # picks up fresh instances.
    DirectField._instance = None
    PatternCircles._instance = None
    CirculationEngine._instance = None
    CoreMachine._instance = None
    _COLLABORATIVE_SURGE_INSTANCE = CollaborativeSurge()
    return _COLLABORATIVE_SURGE_INSTANCE
