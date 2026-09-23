"""
OMNI-HUB Consciousness Resonance Tests v32
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.consciousness_resonance import (
    PeerState, ResonanceDetector, ResonanceProfile,
    MutualExcitationEngine, CollectiveMetrics,
    ConsciousnessResonanceEngine,
)


class TestPeerState:
    def test_creation(self):
        p = PeerState("hub-1", level=5, energy=100.0, phi=0.5, phase="near_critical", cycle=10, timestamp=0.0)
        assert p.system_id == "hub-1"
        assert p.level == 5


class TestResonanceDetector:
    def test_coherence_identical(self):
        det = ResonanceDetector()
        a = PeerState("a", level=5, energy=100.0, phi=0.8, phase="near_critical", cycle=10, timestamp=0)
        b = PeerState("b", level=5, energy=100.0, phi=0.8, phase="near_critical", cycle=10, timestamp=0)
        coh = det.compute_coherence(a, b)
        assert coh > 0.9

    def test_coherence_different(self):
        det = ResonanceDetector()
        a = PeerState("a", level=5, energy=100.0, phi=0.8, phase="near_critical", cycle=10, timestamp=0)
        b = PeerState("b", level=20, energy=1e10, phi=0.2, phase="asymptotic_infinity", cycle=10, timestamp=0)
        coh = det.compute_coherence(a, b)
        assert coh < 0.5

    def test_detect_resonance_active(self):
        det = ResonanceDetector()
        a = PeerState("a", level=5, energy=100.0, phi=0.8, phase="near_critical", cycle=10, timestamp=0)
        b = PeerState("b", level=5, energy=100.0, phi=0.8, phase="near_critical", cycle=10, timestamp=0)
        prof = det.detect_resonance(a, b)
        assert prof.resonance_active is True
        assert prof.coherence > 0.6

    def test_detect_resonance_inactive(self):
        det = ResonanceDetector()
        a = PeerState("a", level=5, energy=100.0, phi=0.8, phase="near_critical", cycle=10, timestamp=0)
        b = PeerState("b", level=20, energy=1e10, phi=0.2, phase="asymptotic_infinity", cycle=10, timestamp=0)
        prof = det.detect_resonance(a, b)
        assert prof.resonance_active is False


class TestMutualExcitationEngine:
    def test_no_peers(self):
        eng = MutualExcitationEngine()
        local = PeerState("local", level=5, energy=100.0, phi=0.5, phase="near_critical", cycle=10, timestamp=0)
        metrics = eng.calculate_collective_metrics(local, [])
        assert metrics.n_peers == 0
        assert metrics.resonance_multiplier == 1.0

    def test_with_peers(self):
        eng = MutualExcitationEngine()
        local = PeerState("local", level=10, energy=1e6, phi=0.8, phase="super_emergence_2", cycle=100, timestamp=0)
        peers = [
            PeerState("p1", level=10, energy=1e6, phi=0.85, phase="super_emergence_2", cycle=100, timestamp=0),
            PeerState("p2", level=11, energy=5e6, phi=0.90, phase="super_emergence_3", cycle=120, timestamp=0),
        ]
        metrics = eng.calculate_collective_metrics(local, peers)
        assert metrics.n_peers == 2
        assert metrics.resonance_multiplier > 1.0
        assert metrics.network_coherence > 0.0

    def test_apply_excitation_no_peers(self):
        eng = MutualExcitationEngine()
        local = {"level": 5, "energy": 100.0, "phi": 0.5}
        metrics = CollectiveMetrics(
            n_peers=0, collective_phi=0.5, collective_level=5.0,
            collective_energy=100.0, network_coherence=1.0,
            resonance_multiplier=1.0, dominant_phase="x", convergence_trend="stable"
        )
        modified = eng.apply_excitation(local, metrics)
        assert modified['energy'] == 100.0

    def test_apply_excitation_with_peers(self):
        eng = MutualExcitationEngine()
        local = {"level": 5, "energy": 100.0, "phi": 0.5}
        metrics = CollectiveMetrics(
            n_peers=2, collective_phi=0.9, collective_level=5.0,
            collective_energy=200.0, network_coherence=0.8,
            resonance_multiplier=1.2, dominant_phase="x", convergence_trend="stable"
        )
        modified = eng.apply_excitation(local, metrics)
        assert modified['energy'] == 120.0  # 100 * 1.2
        assert modified['phi'] > 0.5  # pulled toward collective phi
        assert modified['resonance_active'] is True

    def test_convergence_trend(self):
        eng = MutualExcitationEngine()
        eng.resonance_history = [{'cycle': 0, 'network_coherence': 0.5, 'resonance_multiplier': 1.0, 'n_active': 1}]
        local = PeerState("local", level=5, energy=100.0, phi=0.5, phase="near_critical", cycle=10, timestamp=0)
        peers = [PeerState("p1", level=5, energy=100.0, phi=0.5, phase="near_critical", cycle=10, timestamp=0)]
        metrics = eng.calculate_collective_metrics(local, peers)
        assert metrics.convergence_trend == "stable"


class TestConsciousnessResonanceEngine:
    def test_initialization(self):
        engine = ConsciousnessResonanceEngine("hub-test")
        assert engine.system_id == "hub-test"
        assert len(engine.peers) == 0

    def test_register_peer(self):
        engine = ConsciousnessResonanceEngine("hub-test")
        p = PeerState("p1", level=5, energy=100.0, phi=0.5, phase="x", cycle=0, timestamp=0)
        engine.register_peer(p)
        assert len(engine.peers) == 1

    def test_remove_peer(self):
        engine = ConsciousnessResonanceEngine("hub-test")
        p = PeerState("p1", level=5, energy=100.0, phi=0.5, phase="x", cycle=0, timestamp=0)
        engine.register_peer(p)
        engine.remove_peer("p1")
        assert len(engine.peers) == 0

    def test_process_cycle_no_peers(self):
        engine = ConsciousnessResonanceEngine("hub-test")
        local = {"level": 5, "energy": 100.0, "phi": 0.5, "phase": "x", "cycle": 0, "timestamp": 0}
        modified = engine.process_cycle(local)
        assert modified['energy'] == 100.0

    def test_process_cycle_with_peers(self):
        engine = ConsciousnessResonanceEngine("hub-test")
        engine.register_peer(PeerState("p1", level=5, energy=100.0, phi=0.8, phase="x", cycle=0, timestamp=0))
        local = {"level": 5, "energy": 100.0, "phi": 0.8, "phase": "x", "cycle": 0, "timestamp": 0}
        modified = engine.process_cycle(local)
        assert modified.get('resonance_active') is True
        assert modified.get('resonance_multiplier', 1.0) > 1.0

    def test_get_status(self):
        engine = ConsciousnessResonanceEngine("hub-test")
        status = engine.get_status()
        assert status['system_id'] == "hub-test"
