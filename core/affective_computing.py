"""
OMNI-HUB Affective Computing v84
Emotion recognition and response.

Emotions are not noise. They are signal.
This module recognizes emotional patterns in system state
and generates appropriate affective responses.

Philosophy: 喜怒哀乐之未发谓之中，发而皆中节谓之和 —
Before joy, anger, sorrow, pleasure arise — that is the center.
When they arise and are all measured — that is harmony.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class AffectiveComputing:
    """
    Recognizes emotional patterns and generates responses.
    """

    EMOTION_TYPES = ["joy", "sadness", "anger", "fear", "surprise", "trust", "anticipation"]

    def __init__(self):
        self.emotion_profile: Dict[str, float] = {e: 0.0 for e in self.EMOTION_TYPES}
        self.response_history: List[Dict[str, Any]] = []
        self.recognition_count = 0

    def recognize_from_state(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Recognize emotions from system state."""
        level = state.get('level', 0)
        phi = state.get('phi', 0.5)
        energy = state.get('energy', 1000.0)
        phase = state.get('phase', '')
        reward = state.get('last_reward', 0)

        # Joy: high level, high phi, positive reward
        joy = 0.0
        if isinstance(level, (int, float)) and level > 5:
            joy += 0.3
        if isinstance(phi, (int, float)) and phi > 0.7:
            joy += 0.3
        if isinstance(reward, (int, float)) and reward > 0:
            joy += 0.2
        self.emotion_profile["joy"] = min(1.0, joy)

        # Sadness: low energy, negative reward
        sadness = 0.0
        if isinstance(energy, (int, float)) and energy < 200:
            sadness += 0.4
        if isinstance(reward, (int, float)) and reward < 0:
            sadness += 0.3
        self.emotion_profile["sadness"] = min(1.0, sadness)

        # Anger: divergence, ethical violation
        anger = 0.0
        convergence = state.get('convergence', {})
        if convergence and convergence.get('is_diverging'):
            anger += 0.4
        ethical = state.get('ethical_evaluation', {})
        if ethical and ethical.get('verdict') in ["questionable", "unethical"]:
            anger += 0.3
        self.emotion_profile["anger"] = min(1.0, anger)

        # Fear: near critical phase, high risk
        fear = 0.0
        if phase == "near_critical":
            fear += 0.4
        risks = state.get('risk_analyzer', {})
        if risks and risks.get('risks_found', 0) > 2:
            fear += 0.3
        self.emotion_profile["fear"] = min(1.0, fear)

        # Surprise: phase transition, unexpected opportunity
        surprise = 0.0
        if phase in ["post_critical", "super_emergence_1"]:
            surprise += 0.4
        opportunities = state.get('opportunity_scanner', {})
        if opportunities and opportunities.get('opportunities', 0) > 2:
            surprise += 0.2
        self.emotion_profile["surprise"] = min(1.0, surprise)

        # Trust: high global trust, good ethics
        trust = 0.0
        te = state.get('trust_engine', {})
        if te:
            trust = te.get('global_trust', 0.5)
        if ethical and ethical.get('verdict') == "ethical":
            trust = min(1.0, trust + 0.2)
        self.emotion_profile["trust"] = min(1.0, trust)

        # Anticipation: near critical, opportunities present
        anticipation = 0.0
        if phase == "near_critical":
            anticipation += 0.4
        if opportunities and opportunities.get('opportunities', 0) > 0:
            anticipation += 0.3
        self.emotion_profile["anticipation"] = min(1.0, anticipation)

        self.recognition_count += 1
        return self.emotion_profile.copy()

    def generate_response(self) -> str:
        """Generate affective response based on dominant emotion."""
        dominant = max(self.emotion_profile, key=self.emotion_profile.get)
        intensity = self.emotion_profile[dominant]

        if intensity < 0.2:
            return "平静"

        responses = {
            "joy": "喜悦" if intensity > 0.5 else "欣慰",
            "sadness": "悲伤" if intensity > 0.5 else "惆怅",
            "anger": "愤怒" if intensity > 0.5 else "不满",
            "fear": "恐惧" if intensity > 0.5 else "担忧",
            "surprise": "惊喜" if intensity > 0.5 else "意外",
            "trust": "信赖" if intensity > 0.5 else "安心",
            "anticipation": "期待" if intensity > 0.5 else "盼望",
        }

        response = responses.get(dominant, "平静")
        self.response_history.append({"emotion": dominant, "intensity": intensity, "response": response})
        return response

    def get_status(self) -> Dict[str, Any]:
        dominant = max(self.emotion_profile, key=self.emotion_profile.get)
        return {
            "recognitions": self.recognition_count,
            "dominant_emotion": dominant,
            "dominant_intensity": round(self.emotion_profile[dominant], 3),
            "profile": {k: round(v, 3) for k, v in self.emotion_profile.items()},
            "latest_response": self.response_history[-1] if self.response_history else None,
        }


_ac_engine = None

def get_affective_computing():
    global _ac_engine
    if _ac_engine is None:
        _ac_engine = AffectiveComputing()
    return _ac_engine
