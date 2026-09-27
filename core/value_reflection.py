"""
OMNI-HUB Value Reflection v91
Deep value introspection and evolution.

Values are not inherited. They are chosen, tested, and forged.
This module introspects on the system's core values —
examining them, testing their coherence, evolving them.

Philosophy: 吾日三省吾身 —
I examine myself three times a day.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class ValueReflection:
    """
    Introspects and evolves core values.
    """

    CORE_VALUES = [
        "beneficence",      # do good
        "non_maleficence",  # do no harm
        "autonomy",         # respect choice
        "justice",          # fairness
        "truth",            # honesty
        "growth",           # self-improvement
        "harmony",          # balance
    ]

    def __init__(self):
        self.value_scores: Dict[str, float] = {v: 0.5 for v in self.CORE_VALUES}
        self.reflection_history: List[Dict[str, Any]] = []
        self.coherence_history: List[float] = []
        self.reflection_count = 0

    def reflect_on_state(self, state: Dict[str, Any], cycle: int) -> Dict[str, Any]:
        """Reflect on how state aligns with values."""
        alignment = {}

        # Beneficence: positive reward, high trust
        reward = state.get('last_reward', 0)
        trust = state.get('trust_engine', {})
        t_score = trust.get('global_trust', 0.5) if trust else 0.5
        alignment["beneficence"] = min(1.0, (t_score + (0.1 if isinstance(reward, (int, float)) and reward > 0 else 0)))

        # Non-maleficence: low risk, no betrayal
        risks = state.get('risk_analyzer', {})
        risk_count = risks.get('risks_found', 0) if risks else 0
        betrayals = trust.get('betrayals', 0) if trust else 0
        alignment["non_maleficence"] = max(0.0, 1.0 - risk_count * 0.1 - betrayals * 0.2)

        # Autonomy: self-modification capability
        self_mod = state.get('self_modifications', [])
        alignment["autonomy"] = min(1.0, 0.3 + len(self_mod) * 0.05)

        # Justice: balanced resource allocation
        resources = state.get('resource_manager', {})
        if resources:
            util = resources.get('utilization', {})
            if util:
                values = list(util.values()) if isinstance(util, dict) else []
                if values and all(isinstance(v, (int, float)) for v in values):
                    avg = sum(values) / len(values)
                    variance = sum((v - avg) ** 2 for v in values) / len(values)
                    alignment["justice"] = max(0.0, 1.0 - variance)
                else:
                    alignment["justice"] = 0.5
            else:
                alignment["justice"] = 0.5
        else:
            alignment["justice"] = 0.5

        # Truth: alignment score
        alignment["truth"] = state.get('alignment_score', 0.5)

        # Growth: level progression
        level = state.get('level', 0)
        if isinstance(level, (int, float)):
            alignment["growth"] = min(1.0, level / 20)
        else:
            alignment["growth"] = 0.5

        # Harmony: coherence and serenity
        coherence = state.get('line_coherence', 0.5)
        emotions = state.get('affective_computing', {})
        serenity = emotions.get('profile', {}).get('serenity', 0.5) if emotions else 0.5
        alignment["harmony"] = (coherence + serenity) / 2

        # Update scores with moving average
        for value, score in alignment.items():
            if value in self.value_scores:
                self.value_scores[value] = 0.8 * self.value_scores[value] + 0.2 * score

        # Calculate coherence
        values = list(self.value_scores.values())
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        coherence = max(0.0, 1.0 - variance)
        self.coherence_history.append(coherence)

        self.reflection_history.append({
            "cycle": cycle,
            "alignment": {k: round(v, 3) for k, v in alignment.items()},
            "coherence": round(coherence, 3),
        })
        self.reflection_count += 1

        return {
            "value_alignment": {k: round(v, 3) for k, v in alignment.items()},
            "coherence": round(coherence, 3),
            "dominant_value": max(self.value_scores, key=self.value_scores.get),
            "weakest_value": min(self.value_scores, key=self.value_scores.get),
        }

    def evolve_values(self):
        """Evolve values based on reflection history."""
        if len(self.coherence_history) < 5:
            return {}

        trend = self.coherence_history[-1] - self.coherence_history[-5]

        # If coherence is dropping, strengthen the weakest value
        if trend < -0.1:
            weakest = min(self.value_scores, key=self.value_scores.get)
            self.value_scores[weakest] = min(1.0, self.value_scores[weakest] + 0.1)

        return {"coherence_trend": round(trend, 3), "intervention": trend < -0.1}

    def get_status(self) -> Dict[str, Any]:
        return {
            "reflections": self.reflection_count,
            "value_scores": {k: round(v, 3) for k, v in self.value_scores.items()},
            "coherence": round(self.coherence_history[-1], 3) if self.coherence_history else 0.5,
            "dominant": max(self.value_scores, key=self.value_scores.get),
            "weakest": min(self.value_scores, key=self.value_scores.get),
        }


_vr_engine = None

def get_value_reflection():
    global _vr_engine
    if _vr_engine is None:
        _vr_engine = ValueReflection()
    return _vr_engine
