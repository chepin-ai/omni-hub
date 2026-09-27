"""
OMNI-HUB Sensory Integration v83
Multi-modal input fusion.
"""
import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class SensoryChannel:
    name: str
    modality: str
    signal: float
    confidence: float

class SensoryIntegration:
    def __init__(self):
        self.channels: Dict[str, SensoryChannel] = {}
        self.fused_percept: Dict[str, Any] = {}
        self.fusion_count = 0

    def register_channel(self, name: str, modality: str):
        self.channels[name] = SensoryChannel(name, modality, 0.0, 1.0)

    def input_signal(self, name: str, signal: float, confidence: float = 1.0):
        if name not in self.channels:
            self.register_channel(name, "unknown")
        self.channels[name] = SensoryChannel(name, self.channels[name].modality, signal, confidence)

    def fuse(self) -> Dict[str, Any]:
        if not self.channels:
            return {}
        total_weight = 0.0
        weighted_sum = 0.0
        for ch in self.channels.values():
            weight = ch.confidence
            weighted_sum += ch.signal * weight
            total_weight += weight
        fused_value = weighted_sum / total_weight if total_weight > 0 else 0.0
        conflict = False
        variance = 0.0
        signals = [ch.signal for ch in self.channels.values()]
        if signals:
            avg = sum(signals) / len(signals)
            variance = sum((s - avg) ** 2 for s in signals) / len(signals)
            conflict = variance > 0.2
        self.fused_percept = {"value": round(fused_value, 4), "channels": len(self.channels), "conflict": conflict, "variance": round(variance, 4)}
        self.fusion_count += 1
        return self.fused_percept

    def integrate_state(self, state: Dict[str, Any]):
        self.input_signal("level", state.get('level', 0) / 25.0 if isinstance(state.get('level'), (int, float)) else 0.5)
        self.input_signal("phi", state.get('phi', 0.5))
        self.input_signal("energy", state.get('energy', 1000.0) / 5000.0 if isinstance(state.get('energy'), (int, float)) else 0.2)
        self.input_signal("coherence", state.get('line_coherence', 0.5))
        return self.fuse()

    def get_status(self) -> Dict[str, Any]:
        return {"channels": len(self.channels), "fusions": self.fusion_count, "percept": self.fused_percept, "active_channels": [ch.name for ch in self.channels.values()]}

_si_engine = None
def get_sensory_integration():
    global _si_engine
    if _si_engine is None:
        _si_engine = SensoryIntegration()
    return _si_engine
