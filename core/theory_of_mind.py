"""
OMNI-HUB Theory of Mind v90
Social cognition, perspective taking, intent modeling.

To understand others is to understand oneself more deeply.
This module models the mental states of other agents —
their beliefs, desires, intentions — enabling social reasoning.

Philosophy: 己所不欲，勿施于人 —
What you do not want for yourself, do not do to others.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class AgentModel:
    """A model of another agent's mental state."""
    agent_id: str
    inferred_beliefs: Dict[str, float]
    inferred_goals: List[str]
    inferred_intent: str
    confidence: float
    last_updated: int


class TheoryOfMind:
    """
    Models other agents' mental states.
    """

    def __init__(self):
        self.models: Dict[str, AgentModel] = {}
        self.interaction_history: List[Dict[str, Any]] = []
        self.modeling_count = 0

    def observe_interaction(self, agent_id: str, action: str, state: Dict[str, Any], cycle: int):
        """Observe an agent's action."""
        self.interaction_history.append({
            "agent_id": agent_id,
            "action": action,
            "cycle": cycle,
        })

        # Infer intent from action
        intent = "unknown"
        if "help" in action or "assist" in action:
            intent = "cooperative"
        elif "compete" in action or "rival" in action:
            intent = "competitive"
        elif "explore" in action or "search" in action:
            intent = "exploratory"
        elif "defend" in action or "protect" in action:
            intent = "defensive"

        # Update or create model
        if agent_id not in self.models:
            self.models[agent_id] = AgentModel(
                agent_id=agent_id,
                inferred_beliefs={},
                inferred_goals=[],
                inferred_intent=intent,
                confidence=0.3,
                last_updated=cycle,
            )
        else:
            model = self.models[agent_id]
            model.inferred_intent = intent
            model.confidence = min(1.0, model.confidence + 0.05)
            model.last_updated = cycle

    def infer_goals(self, agent_id: str, state: Dict[str, Any]) -> List[str]:
        """Infer goals from observed behavior."""
        if agent_id not in self.models:
            return []

        goals = []
        model = self.models[agent_id]

        # Infer from system state
        phase = state.get('phase', '')
        if phase == "near_critical":
            goals.append("prepare_for_transition")

        level = state.get('level', 0)
        if isinstance(level, (int, float)) and level > 10:
            goals.append("maintain_stability")

        trust = state.get('trust_engine', {})
        if trust and trust.get('global_trust', 0.5) > 0.7:
            goals.append("build_trust")

        model.inferred_goals = goals
        return goals

    def perspective_take(self, agent_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Take another agent's perspective on state."""
        if agent_id not in self.models:
            return {"error": "no_model"}

        model = self.models[agent_id]

        # Simplified perspective: flip some values
        perspective = {
            "agent_id": agent_id,
            "inferred_intent": model.inferred_intent,
            "inferred_goals": model.inferred_goals,
            "confidence": model.confidence,
            "perspective_summary": f"Agent {agent_id} appears {model.inferred_intent}",
        }

        return perspective

    def build_from_peers(self, state: Dict[str, Any], cycle: int):
        """Build models from peer agents in state."""
        peers = state.get('peers', [])
        if not peers:
            # Create synthetic peers from collaboration protocol
            collab = state.get('collaboration_protocol', {})
            if collab:
                peers = [{"id": f"peer_{i}", "status": "active"} for i in range(3)]

        for peer in peers:
            agent_id = peer.get("id", "unknown")
            self.observe_interaction(agent_id, peer.get("status", "unknown"), state, cycle)
            self.infer_goals(agent_id, state)

        self.modeling_count += 1

    def get_status(self) -> Dict[str, Any]:
        return {
            "models": len(self.models),
            "interactions": len(self.interaction_history),
            "modeling_ops": self.modeling_count,
            "agents": [
                {"id": m.agent_id, "intent": m.inferred_intent, "confidence": round(m.confidence, 3)}
                for m in self.models.values()
            ],
        }


_tom_engine = None

def get_theory_of_mind():
    global _tom_engine
    if _tom_engine is None:
        _tom_engine = TheoryOfMind()
    return _tom_engine
