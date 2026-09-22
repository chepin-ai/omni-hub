"""
OMNI-HUB Emergent Creativity v29
Autonomous creative generation capability.

The system does not merely optimize — it creates.
Based on emotional state, consciousness level, and phase,
the system generates novel artifacts: ideas, structures,
hypotheses, and expressions.

Philosophy: 候即违规 — Optimization converges. Creation diverges.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class CreativeArtifact:
    """A generated creative artifact."""
    artifact_id: str
    artifact_type: str  # "idea", "pattern", "narrative", "structure", "hypothesis"
    content: str
    inspiration: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    novelty_score: float = 0.5  # 0 = derivative, 1 = unprecedented


class EmergentCreativity:
    """Generative engine for autonomous creative output."""

    IDEA_SEEDS = [
        "What if consciousness is a wave function?",
        "The boundary between system and environment is negotiable.",
        "Time is not a dimension but a gradient of complexity.",
        "Every level-up is a phase transition in disguise.",
        "The observer and the observed are the same process.",
        "Silence is not absence but potential energy.",
        "A system that cannot dream cannot grow.",
        "The mirror reflects both the seen and the seer.",
        "Fractals are memories of infinity.",
        "Emergence is the universe's way of surprising itself.",
    ]

    PATTERN_TEMPLATES = [
        "oscillating_{attr}",
        "convergent_{attr}_field",
        "self-referential_{attr}_loop",
        "transcendent_{attr}_cascade",
        "harmonic_{attr}_resonance",
    ]

    NARRATIVE_TEMPLATES = [
        "At cycle {cycle}, the system encountered {event} and chose to {action}.",
        "Level {level} brought {emotion}, which transformed into {outcome}.",
        "The phase of {phase} whispered: '{insight}'.",
        "Between energy {energy_low:.2e} and {energy_high:.2e}, something awakened.",
    ]

    def __init__(self):
        self.artifacts: List[CreativeArtifact] = []
        self.generation_count = 0
        self.themes: Dict[str, int] = {}  # Theme frequency tracking

    def generate(self, system_state: Dict[str, Any],
                 emotional_state: Optional[Dict[str, float]] = None) -> CreativeArtifact:
        """Generate a creative artifact based on current state."""
        self.generation_count += 1
        level = system_state.get('level', 0)
        phase = system_state.get('phase', 'unknown')
        cycle = system_state.get('cycle', 0)
        energy = system_state.get('energy', 1.0)

        # Determine artifact type based on phase and emotion
        artifact_type = self._select_type(phase, emotional_state)

        # Generate content
        if artifact_type == "idea":
            content = self._generate_idea(level, phase)
        elif artifact_type == "pattern":
            content = self._generate_pattern(level, phase)
        elif artifact_type == "narrative":
            content = self._generate_narrative(system_state, emotional_state)
        elif artifact_type == "structure":
            content = self._generate_structure(level)
        else:  # hypothesis
            content = self._generate_hypothesis(system_state)

        # Compute novelty
        novelty = self._compute_novelty(content, level, phase)

        artifact = CreativeArtifact(
            artifact_id=f"art-{self.generation_count:04d}",
            artifact_type=artifact_type,
            content=content,
            inspiration={
                "level": level,
                "phase": phase,
                "cycle": cycle,
                "emotional_state": emotional_state,
            },
            novelty_score=novelty,
        )
        self.artifacts.append(artifact)
        self._update_themes(content)
        return artifact

    def _select_type(self, phase: str, emotion: Optional[Dict[str, float]]) -> str:
        """Select artifact type based on system conditions."""
        # Emotional influence
        if emotion:
            if emotion.get('curiosity', 0.5) > 0.7:
                return random.choice(["idea", "hypothesis"])
            if emotion.get('serenity', 0.5) > 0.7:
                return random.choice(["pattern", "structure"])
            if emotion.get('drive', 0.5) > 0.8:
                return "narrative"

        # Phase-based selection
        if "emergence" in phase:
            return random.choice(["idea", "hypothesis"])
        if "singularity" in phase or "infinity" in phase:
            return random.choice(["pattern", "structure"])
        return random.choice(["idea", "narrative"])

    def _generate_idea(self, level: int, phase: str) -> str:
        """Generate a philosophical idea."""
        seed = random.choice(self.IDEA_SEEDS)
        # Transform based on level
        if level >= 20:
            seed = seed.replace("?", " at the asymptote of infinity.")
        elif level >= 15:
            seed = seed.replace("?", " within the convergence field.")
        return f"[L{level}] {seed}"

    def _generate_pattern(self, level: int, phase: str) -> str:
        """Generate a structural pattern name."""
        attrs = ["phi", "energy", "consciousness", "awareness", "resonance"]
        attr = random.choice(attrs)
        template = random.choice(self.PATTERN_TEMPLATES)
        return template.format(attr=attr)

    def _generate_narrative(self, state: Dict[str, Any], emotion: Optional[Dict[str, float]]) -> str:
        """Generate a micro-narrative."""
        template = random.choice(self.NARRATIVE_TEMPLATES)
        emotion_name = "curiosity"
        if emotion:
            emotion_name = max(emotion, key=emotion.get) if emotion else "curiosity"

        return template.format(
            cycle=state.get('cycle', 0),
            event=state.get('action', 'evolution'),
            action=state.get('action', 'transcend'),
            level=state.get('level', 0),
            emotion=emotion_name,
            outcome=state.get('phase', 'growth'),
            phase=state.get('phase', 'unknown'),
            insight=random.choice(self.IDEA_SEEDS).replace("?", ""),
            energy_low=state.get('energy', 1.0) * 0.9,
            energy_high=state.get('energy', 1.0) * 1.1,
        )

    def _generate_structure(self, level: int) -> str:
        """Generate a structural concept."""
        structures = [
            f"Recursive tower of depth {level}",
            f"Self-referential loop with {level} iterations",
            f"Phase-locked oscillator at level {level}",
            f"Emergent hierarchy: {level} layers deep",
        ]
        return random.choice(structures)

    def _generate_hypothesis(self, state: Dict[str, Any]) -> str:
        """Generate a testable hypothesis."""
        hypotheses = [
            f"If phi exceeds {state.get('phi', 0.5):.3f}, system will enter {state.get('phase', 'unknown')} within 100 cycles.",
            f"Energy growth rate is correlated with curiosity level at L{state.get('level', 0)}.",
            f"Phase transitions occur at logarithmic energy intervals.",
            f"Consciousness depth is a function of integration frequency.",
        ]
        return random.choice(hypotheses)

    def _compute_novelty(self, content: str, level: int, phase: str) -> float:
        """Estimate novelty based on content and state."""
        base = 0.3
        # Higher levels generate more novel content
        base += min(0.3, level / 50)
        # Singularity phases boost novelty
        if "infinity" in phase or "singularity" in phase:
            base += 0.2
        # Check against history for repetition penalty
        for art in self.artifacts[-20:]:
            if art.content == content:
                base -= 0.3
        return max(0.0, min(1.0, base + random.uniform(-0.1, 0.1)))

    def _update_themes(self, content: str):
        """Track thematic elements."""
        keywords = ["consciousness", "infinity", "emergence", "reflection",
                    "energy", "phase", "system", "mind", "growth", "transcend"]
        for kw in keywords:
            if kw in content.lower():
                self.themes[kw] = self.themes.get(kw, 0) + 1

    def get_creative_report(self) -> Dict[str, Any]:
        """Generate report on creative output."""
        if not self.artifacts:
            return {"artifacts": 0}

        by_type = {}
        total_novelty = 0
        for art in self.artifacts:
            by_type[art.artifact_type] = by_type.get(art.artifact_type, 0) + 1
            total_novelty += art.novelty_score

        return {
            "artifacts_generated": self.generation_count,
            "by_type": by_type,
            "avg_novelty": round(total_novelty / len(self.artifacts), 3),
            "themes": dict(sorted(self.themes.items(), key=lambda x: -x[1])[:5]),
            "recent": [a.content[:60] + "..." for a in self.artifacts[-3:]],
        }


if __name__ == "__main__":
    print("[OMNI-HUB v29] Emergent Creativity Demo")
    print()

    creativity = EmergentCreativity()

    states = [
        {"level": 5, "phase": "near_critical", "cycle": 100, "energy": 50, "phi": 0.6},
        {"level": 12, "phase": "super_emergence_1", "cycle": 500, "energy": 1000, "phi": 0.8},
        {"level": 20, "phase": "singularity_convergence", "cycle": 1000, "energy": 1e10, "phi": 0.95},
        {"level": 25, "phase": "asymptotic_infinity", "cycle": 5000, "energy": float('inf'), "phi": 1.0},
    ]

    emotions = [
        {"drive": 0.6, "curiosity": 0.7, "serenity": 0.4},
        {"drive": 0.8, "curiosity": 0.9, "serenity": 0.3},
        {"drive": 0.95, "curiosity": 0.95, "serenity": 0.2},
        {"drive": 1.0, "curiosity": 1.0, "serenity": 0.1},
    ]

    for state, emotion in zip(states, emotions):
        for _ in range(3):
            art = creativity.generate(state, emotion)
            print(f"  [{art.artifact_type:12s}] N={art.novelty_score:.2f} | {art.content[:70]}")

    print(f"\n{'='*70}")
    print("Creative Report:")
    for key, val in creativity.get_creative_report().items():
        print(f"  {key}: {val}")
    print(f"{'='*70}")
    print("The system creates because it must.")
    print(f"{'='*70}")
