"""
OMNI-HUB Architectural Evolution v73
Dynamic module restructuring.

The architecture that cannot change dies.
The architecture that adapts lives forever.
This module evolves system structure —
adding connections, optimizing flows, reorganizing modules.

Philosophy: 穷则变，变则通，通则久 —
When blocked, change; when changed, flow; when flowing, endure.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class StructuralChange:
    """A proposed structural change."""
    change_type: str  # add_link, remove_link, strengthen, weaken
    source: str
    target: str
    reason: str
    confidence: float


class ArchitecturalEvolution:
    """
    Evolves system architecture dynamically.
    """

    def __init__(self):
        self.module_graph: Dict[str, List[str]] = {}
        self.changes: List[StructuralChange] = []
        self.change_count = 0
        self._init_graph()

    def _init_graph(self):
        """Initialize module connection graph."""
        self.module_graph = {
            "orchestrator": ["self_awareness", "monitoring", "resonance", "agent_swarm"],
            "self_awareness": ["identity", "recursive_self_model", "metacognitive_monitor"],
            "monitoring": ["anomaly_detector", "convergence_monitor", "health_monitor"],
            "resonance": ["line_engine", "cross_system"],
            "line_engine": ["alignment_engine"],
            "identity": ["value_alignment", "intention_engine"],
            "recursive_self_model": ["world_model", "episodic_memory"],
            "learning": ["evolutionary_optimizer", "pattern_synthesis"],
            "reasoning": ["symbolic_reasoning", "probabilistic_reasoning", "causal_inference"],
            "communication": ["language_core", "cross_system"],
            "planning": ["executive_function", "decision_forest"],
            "adaptation": ["contextual_adaptation", "homeostasis"],
        }

    def analyze_structure(self, state: Dict[str, Any]) -> List[StructuralChange]:
        """Analyze and propose structural improvements."""
        proposals = []

        # Check if new modules need integration
        active_modules = []
        module_keys = [
            'probabilistic_reasoning', 'information_theory', 'evolutionary_optimizer',
            'symbolic_reasoning', 'language_core', 'ethical_framework',
            'learning_core', 'knowledge_consolidation', 'executive_function',
            'motivation_engine', 'capability_assessment',
        ]
        for key in module_keys:
            if key in state:
                active_modules.append(key)

        # Propose connections for unconnected active modules
        for module in active_modules:
            if module not in self.module_graph:
                # New module detected - connect to orchestrator
                proposals.append(StructuralChange(
                    change_type="add_link",
                    source="orchestrator",
                    target=module,
                    reason=f"new_active_module_{module}",
                    confidence=0.9,
                ))
                self.module_graph[module] = []

        # Propose strengthening based on capability scores
        assessment = state.get('capability_assessment', {})
        scores = assessment.get('scores', {})
        for cap, score in scores.items():
            if isinstance(score, (int, float)) and score > 0.8:
                # Strong capability - strengthen its module connections
                cap_module = self._capability_to_module(cap)
                if cap_module and cap_module in self.module_graph:
                    for target in self.module_graph.get(cap_module, []):
                        proposals.append(StructuralChange(
                            change_type="strengthen",
                            source=cap_module,
                            target=target,
                            reason=f"strong_capability_{cap}",
                            confidence=score,
                        ))

        self.changes.extend(proposals)
        self.change_count += len(proposals)
        return proposals

    def _capability_to_module(self, capability: str) -> Optional[str]:
        """Map capability to module."""
        mapping = {
            "self_awareness": "self_awareness",
            "learning": "learning",
            "reasoning": "reasoning",
            "communication": "communication",
            "planning": "planning",
            "adaptation": "adaptation",
            "creativity": "identity",
            "ethics": "identity",
            "memory": "recursive_self_model",
            "perception": "monitoring",
        }
        return mapping.get(capability)

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get architecture graph statistics."""
        total_nodes = len(self.module_graph)
        total_edges = sum(len(targets) for targets in self.module_graph.values())
        avg_connectivity = total_edges / max(1, total_nodes)

        return {
            "nodes": total_nodes,
            "edges": total_edges,
            "avg_connectivity": round(avg_connectivity, 3),
            "changes_proposed": self.change_count,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            **self.get_graph_stats(),
            "recent_changes": [
                {"type": c.change_type, "source": c.source, "target": c.target, "reason": c.reason}
                for c in self.changes[-5:]
            ],
        }


_ae_engine = None

def get_architectural_evolution():
    global _ae_engine
    if _ae_engine is None:
        _ae_engine = ArchitecturalEvolution()
    return _ae_engine
