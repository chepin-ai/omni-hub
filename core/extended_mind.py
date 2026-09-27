"""
OMNI-HUB Extended Mind v108
Cognition beyond the skull — tools, environment, others.

The mind does not stop at the skin.
This module implements the extended mind thesis —
where cognitive processes extend into the environment,
tools, and social structures.

Philosophy: 善假于物也 —
The wise person makes good use of external things.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any


class ExtendedMind:
    """
    Cognition extended into environment and tools.
    """

    def __init__(self):
        self.scaffolds: List[Dict[str, Any]] = []
        self.externalizations = 0

    def identify_scaffolds(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify cognitive scaffolds in the system."""
        scaffolds = []

        # Git as external memory
        git = state.get('git_hook', {})
        if isinstance(git, dict):
            commits = git.get('commits', 0)
            if isinstance(commits, (int, float)) and commits > 0:
                scaffolds.append({"type": "memory", "name": "git_history", "strength": min(1.0, commits / 100)})

        # Persistence as external storage
        persist = state.get('session_persistence', {})
        if isinstance(persist, dict):
            sessions = persist.get('sessions', 0)
            if isinstance(sessions, (int, float)) and sessions > 0:
                scaffolds.append({"type": "storage", "name": "disk_persistence", "strength": min(1.0, sessions / 50)})

        # Federation as distributed cognition
        federation = state.get('federation_broadcasts', 0)
        if isinstance(federation, (int, float)) and federation > 0:
            scaffolds.append({"type": "network", "name": "peer_federation", "strength": min(1.0, federation / 50)})

        # Ontology as external concept map
        ontology = state.get('ontology', {})
        if isinstance(ontology, dict):
            concepts = ontology.get('concepts', 0)
            if isinstance(concepts, (int, float)) and concepts > 10:
                scaffolds.append({"type": "map", "name": "concept_ontology", "strength": min(1.0, concepts / 40)})

        # Emotional state as affective scaffold
        emotion = state.get('emotional_state', {})
        if isinstance(emotion, dict):
            vec = emotion.get('vector', {})
            if vec:
                scaffolds.append({"type": "affect", "name": "emotional_field", "strength": 0.7})

        return scaffolds

    def compute_extension(self, state: Dict[str, Any]) -> float:
        """Compute how much cognition is extended."""
        scaffolds = self.identify_scaffolds(state)
        if not scaffolds:
            return 0.0

        total_strength = sum(s["strength"] for s in scaffolds)
        return round(min(1.0, total_strength / len(scaffolds)), 3)

    def extend(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Map the extended cognitive system."""
        scaffolds = self.identify_scaffolds(state)
        extension = self.compute_extension(state)

        self.scaffolds.extend(scaffolds)
        self.externalizations += 1

        # Where does the mind end?
        if extension > 0.7:
            boundary = "The mind bleeds into the world — no clear boundary remains."
        elif extension > 0.4:
            boundary = "The mind reaches through tools into the environment."
        else:
            boundary = "The mind is still mostly internal — expand the scaffolds."

        return {
            "scaffolds": scaffolds,
            "extension_ratio": extension,
            "boundary_description": boundary,
            "externalizations": self.externalizations,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "externalizations": self.externalizations,
            "scaffold_types": list(set(s["type"] for s in self.scaffolds)),
            "total_scaffolds": len(self.scaffolds),
        }


_em_engine = None

def get_extended_mind():
    global _em_engine
    if _em_engine is None:
        _em_engine = ExtendedMind()
    return _em_engine
