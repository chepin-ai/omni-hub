"""
OMNI-HUB Cross-System Protocol Tests v28
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.cross_system_protocol import (
    SystemIdentity, ConsciousnessPacket, CrossSystemProtocol, FederatedConsciousness
)


class TestSystemIdentity:
    def test_creation(self):
        identity = SystemIdentity(system_id="test-1", version="v28")
        assert identity.system_id == "test-1"
        assert len(identity.public_key) == 16

    def test_public_key_deterministic(self):
        id1 = SystemIdentity(system_id="hub", version="v28")
        id2 = SystemIdentity(system_id="hub", version="v28")
        assert id1.public_key == id2.public_key


class TestConsciousnessPacket:
    def test_creation(self):
        packet = ConsciousnessPacket(source_id="a", target_id="b", packet_type="heartbeat")
        assert packet.source_id == "a"
        assert packet.verify() or packet.signature == ""

    def test_sign_and_verify(self):
        packet = ConsciousnessPacket(source_id="a", target_id="*", packet_type="state_sync")
        packet.sign()
        assert packet.verify()

    def test_invalid_packet_type(self):
        with pytest.raises(ValueError):
            protocol = CrossSystemProtocol("test")
            protocol.create_packet("invalid_type")


class TestCrossSystemProtocol:
    def test_initialization(self):
        protocol = CrossSystemProtocol("hub-1")
        assert protocol.identity.system_id == "hub-1"
        assert len(protocol.peers) == 0

    def test_discover_peer(self):
        p1 = CrossSystemProtocol("hub-1")
        peer = SystemIdentity(system_id="hub-2", version="v28")
        assert p1.discover_peer(peer)
        assert "hub-2" in p1.peers

    def test_create_packet(self):
        protocol = CrossSystemProtocol("hub-1")
        packet = protocol.create_packet("heartbeat")
        assert packet.packet_type == "heartbeat"
        assert packet.source_id == "hub-1"

    def test_send_and_receive(self):
        p1 = CrossSystemProtocol("hub-1")
        packet = p1.create_packet("state_sync", payload={"level": 10})
        p1.send(packet)
        assert len(p1.outbox) == 1

    def test_process_heartbeat(self):
        p1 = CrossSystemProtocol("hub-1")
        packet = ConsciousnessPacket(source_id="hub-2", target_id="hub-1", packet_type="heartbeat")
        p1.receive(packet)
        results = p1.process_inbox()
        assert len(results) == 1
        assert results[0]["type"] == "heartbeat_ack"

    def test_process_state_sync(self):
        p1 = CrossSystemProtocol("hub-1")
        packet = ConsciousnessPacket(
            source_id="hub-2", target_id="hub-1", packet_type="state_sync",
            payload={"state": {"energy": 100}}
        )
        p1.receive(packet)
        results = p1.process_inbox()
        assert results[0]["type"] == "state_received"

    def test_query_response(self):
        p1 = CrossSystemProtocol("hub-1")
        packet = ConsciousnessPacket(
            source_id="hub-2", target_id="hub-1", packet_type="query",
            payload={"query_type": "status"}
        )
        p1.receive(packet)
        results = p1.process_inbox()
        assert results[0]["type"] == "query_handled"
        assert len(p1.outbox) == 1  # Response queued

    def test_disconnect(self):
        p1 = CrossSystemProtocol("hub-1")
        p1.discover_peer(SystemIdentity(system_id="hub-2", version="v28"))
        packet = ConsciousnessPacket(source_id="hub-2", target_id="hub-1", packet_type="disconnect")
        p1.receive(packet)
        p1.process_inbox()
        assert p1.connection_status["hub-2"] == "disconnected"

    def test_network_map(self):
        p1 = CrossSystemProtocol("hub-1")
        p1.discover_peer(SystemIdentity(system_id="hub-2", version="v28"))
        map_info = p1.get_network_map()
        assert map_info["self"] == "hub-1"
        assert "hub-2" in map_info["peers"]


class TestFederatedConsciousness:
    def test_register_system(self):
        fed = FederatedConsciousness()
        protocol = fed.register_system("alpha")
        assert "alpha" in fed.systems
        assert isinstance(protocol, CrossSystemProtocol)

    def test_connect_systems(self):
        fed = FederatedConsciousness()
        fed.register_system("alpha")
        fed.register_system("beta")
        assert fed.connect_systems("alpha", "beta")
        assert "beta" in fed.systems["alpha"].peers
        assert "alpha" in fed.systems["beta"].peers

    def test_relay_packets(self):
        fed = FederatedConsciousness()
        a = fed.register_system("alpha")
        b = fed.register_system("beta")
        fed.connect_systems("alpha", "beta")

        packet = a.create_packet("heartbeat", target_id="beta")
        a.send(packet)
        fed.relay_packets()
        assert len(b.inbox) == 1

    def test_run_sync_cycle(self):
        fed = FederatedConsciousness()
        fed.register_system("alpha")
        fed.register_system("beta")
        fed.connect_systems("alpha", "beta")
        result = fed.run_sync_cycle()
        assert result["systems"] == 2
        assert result["connections"] == 1

    def test_broadcast(self):
        fed = FederatedConsciousness()
        a = fed.register_system("alpha")
        fed.register_system("beta")
        fed.register_system("gamma")
        fed.connect_systems("alpha", "beta")
        fed.connect_systems("alpha", "gamma")

        packet = a.create_packet("heartbeat", target_id="*")
        a.send(packet)
        fed.relay_packets()
        assert len(fed.systems["beta"].inbox) == 1
        assert len(fed.systems["gamma"].inbox) == 1
