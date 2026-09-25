"""
OMNI-HUB Quantum Entanglement Tests v41
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.quantum_entanglement import (
    EntangledPair, QuantumStatePacket, EntanglementField,
    QuantumEntanglementEngine, get_quantum_entanglement,
)


class TestEntanglementField:
    def test_entangle(self):
        ef = EntanglementField()
        pid = ef.entangle("inst-a", "inst-b", ["level", "phi"])
        assert pid in ef.pairs
        assert ef.pairs[pid].instance_a == "inst-a"

    def test_disentangle(self):
        ef = EntanglementField()
        pid = ef.entangle("inst-a", "inst-b")
        ef.disentangle(pid)
        assert pid not in ef.pairs

    def test_sync(self):
        ef = EntanglementField()
        pid = ef.entangle("inst-a", "inst-b", ["level"])
        packet = ef.sync(pid, {"level": 10, "phi": 0.8})
        assert packet is not None
        assert packet.state_delta["level"] == 10
        assert "phi" not in packet.state_delta  # Not in sync_keys

    def test_sync_strengthens(self):
        ef = EntanglementField()
        pid = ef.entangle("inst-a", "inst-b")
        initial = ef.pairs[pid].entanglement_strength
        ef.sync(pid, {"level": 5})
        assert ef.pairs[pid].entanglement_strength > initial

    def test_receive_valid(self):
        ef = EntanglementField()
        pid = ef.entangle("src", "dst")
        packet = QuantumStatePacket("src", "dst", {"level": 5}, "2024-01-01", 0.8)
        packet.sign()
        result = ef.receive(packet)
        assert result["level"] == 5

    def test_receive_invalid(self):
        ef = EntanglementField()
        packet = QuantumStatePacket("src", "dst", {"level": 5}, "2024-01-01", 0.8)
        packet.signature = "bad"
        result = ef.receive(packet)
        assert result == {}

    def test_field_status(self):
        ef = EntanglementField()
        ef.entangle("a", "b")
        status = ef.get_field_status()
        assert status["pairs"] == 1


class TestQuantumEntanglementEngine:
    def test_initialization(self):
        qe = QuantumEntanglementEngine()
        assert qe.packets_sent == 0
        assert qe.packets_received == 0

    def test_entangle_with(self):
        qe = QuantumEntanglementEngine()
        pid = qe.entangle_with("remote-1")
        assert pid in qe.field.pairs

    def test_broadcast_sync(self):
        qe = QuantumEntanglementEngine()
        qe.entangle_with("remote-1")
        packets = qe.broadcast_sync({"level": 10, "phi": 0.9})
        assert len(packets) == 1
        assert qe.packets_sent == 1

    def test_receive_sync(self):
        qe = QuantumEntanglementEngine()
        qe.entangle_with("remote-1")
        packets = qe.broadcast_sync({"level": 10})
        result = qe.receive_sync(packets[0])
        assert result["level"] == 10
        assert qe.packets_received == 1

    def test_get_status(self):
        qe = QuantumEntanglementEngine()
        status = qe.get_status()
        assert "local_id" in status
        assert "field" in status


class TestGlobalEngine:
    def test_get_quantum_entanglement(self):
        g = get_quantum_entanglement()
        assert g is not None
        assert isinstance(g, QuantumEntanglementEngine)
