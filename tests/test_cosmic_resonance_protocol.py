"""
Tests for OMNI-HUB Module v160: Cosmic Resonance Protocol (宇宙共振协议)
"""

import pytest
from typing import Dict, Any
from unittest.mock import patch

from core.cosmic_resonance_protocol import (
    CosmicResonanceProtocol,
    get_cosmic_resonance_protocol,
)


class TestCosmicResonanceProtocol:
    """Comprehensive test suite for CosmicResonanceProtocol."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the global singleton before each test."""
        import core.cosmic_resonance_protocol as crp
        crp._module = None
        yield
        crp._module = None

    @pytest.fixture
    def crp(self) -> CosmicResonanceProtocol:
        """Fresh CosmicResonanceProtocol instance."""
        return CosmicResonanceProtocol()

    # ------------------------------------------------------------------
    # __init__
    # ------------------------------------------------------------------
    def test_init_loads_initial_field(self, crp: CosmicResonanceProtocol):
        """Constructor should load the 33 initial repos."""
        assert len(crp.cosmic_field) == 33
        assert "omni-hub" in crp.cosmic_field
        assert "langchain-ai/langchain" in crp.cosmic_field

    def test_init_buffers_empty(self, crp: CosmicResonanceProtocol):
        """Echo buffer and discovery log should start empty."""
        assert crp.echo_buffer == []
        assert crp.discovery_log == []

    def test_init_pulse_count_zero(self, crp: CosmicResonanceProtocol):
        """Pulse count should start at zero."""
        assert crp._pulse_count == 0

    # ------------------------------------------------------------------
    # emit_cosmic_pulse
    # ------------------------------------------------------------------
    def test_emit_pulse_structure(self, crp: CosmicResonanceProtocol):
        """emit_cosmic_pulse should return a well-formed dict."""
        result = crp.emit_cosmic_pulse(0.5)
        assert isinstance(result, dict)
        assert "pulse_id" in result
        assert "intensity" in result
        assert "direction" in result
        assert "timestamp" in result
        assert "echo_returned" in result
        assert "echo" in result

    def test_emit_pulse_increments_count(self, crp: CosmicResonanceProtocol):
        """Each call should increment the pulse counter."""
        assert crp._pulse_count == 0
        crp.emit_cosmic_pulse(0.5)
        assert crp._pulse_count == 1
        crp.emit_cosmic_pulse(0.5)
        assert crp._pulse_count == 2

    def test_emit_pulse_default_direction(self, crp: CosmicResonanceProtocol):
        """Default direction should be omnidirectional."""
        result = crp.emit_cosmic_pulse(0.5)
        assert result["direction"] == "omnidirectional"

    def test_emit_pulse_custom_direction(self, crp: CosmicResonanceProtocol):
        """Custom direction should be respected."""
        for d in ["targeted", "spiral", "recursive"]:
            result = crp.emit_cosmic_pulse(0.5, direction=d)
            assert result["direction"] == d

    def test_emit_pulse_invalid_direction_fallback(self, crp: CosmicResonanceProtocol):
        """Invalid direction should fallback to omnidirectional."""
        result = crp.emit_cosmic_pulse(0.5, direction="invalid")
        assert result["direction"] == "omnidirectional"

    def test_emit_pulse_echo_probability(self, crp: CosmicResonanceProtocol):
        """With mocked random, echo should be deterministic."""
        with patch("core.cosmic_resonance_protocol.random.random", return_value=0.1):
            result = crp.emit_cosmic_pulse(1.0)
            assert result["echo_returned"] is True
            assert result["echo"] is not None
            assert "source" in result["echo"]

    def test_emit_pulse_no_echo(self, crp: CosmicResonanceProtocol):
        """With mocked random above threshold, no echo."""
        with patch("core.cosmic_resonance_protocol.random.random", return_value=0.99):
            result = crp.emit_cosmic_pulse(1.0)
            assert result["echo_returned"] is False
            assert result["echo"] is None

    def test_emit_pulse_echo_appends_to_buffer(self, crp: CosmicResonanceProtocol):
        """Returned echo should be stored in echo_buffer."""
        with patch("core.cosmic_resonance_protocol.random.random", return_value=0.1):
            crp.emit_cosmic_pulse(1.0)
            assert len(crp.echo_buffer) == 1

    # ------------------------------------------------------------------
    # receive_cosmic_echo
    # ------------------------------------------------------------------
    def test_receive_echo_structure(self, crp: CosmicResonanceProtocol):
        """receive_cosmic_echo should return a well-formed dict."""
        echo = {"source": "unknown-repo", "signal_strength": 0.8}
        result = crp.receive_cosmic_echo(echo)
        assert isinstance(result, dict)
        assert result["processed"] is True
        assert result["source"] == "unknown-repo"
        assert "classification" in result

    def test_receive_echo_known_source(self, crp: CosmicResonanceProtocol):
        """Echo from a known source should be classified as known."""
        echo = {"source": "omni-hub", "signal_strength": 0.8}
        result = crp.receive_cosmic_echo(echo)
        assert result["classification"] == "known"

    def test_receive_echo_unknown_source_weak(self, crp: CosmicResonanceProtocol):
        """Echo from unknown source with weak signal is unknown."""
        echo = {"source": "new-repo-123", "signal_strength": 0.3}
        result = crp.receive_cosmic_echo(echo)
        assert result["classification"] == "unknown"

    def test_receive_echo_unknown_source_strong(self, crp: CosmicResonanceProtocol):
        """Echo from unknown source with strong signal is potential_discovery."""
        echo = {"source": "new-repo-123", "signal_strength": 0.8}
        result = crp.receive_cosmic_echo(echo)
        assert result["classification"] == "potential_discovery"

    def test_receive_echo_increments_buffer(self, crp: CosmicResonanceProtocol):
        """Each received echo should append to echo_buffer."""
        assert len(crp.echo_buffer) == 0
        crp.receive_cosmic_echo({"source": "a"})
        assert len(crp.echo_buffer) == 1
        crp.receive_cosmic_echo({"source": "b"})
        assert len(crp.echo_buffer) == 2

    def test_receive_echo_invalid_input(self, crp: CosmicResonanceProtocol):
        """Non-dict input should return error."""
        result = crp.receive_cosmic_echo("not-a-dict")
        assert result["processed"] is False
        assert "error" in result

    # ------------------------------------------------------------------
    # discover_new_node
    # ------------------------------------------------------------------
    def test_discover_new_node_structure(self, crp: CosmicResonanceProtocol):
        """discover_new_node should return a well-formed dict."""
        echo = {"source": "brand-new-node", "is_new_discovery": True}
        result = crp.discover_new_node(echo)
        assert isinstance(result, dict)
        assert "discovered" in result
        assert "source" in result
        assert "field_size" in result

    def test_discover_new_node_success(self, crp: CosmicResonanceProtocol):
        """A new node with is_new_discovery=True should be added."""
        initial_size = len(crp.cosmic_field)
        echo = {"source": "brand-new-node", "is_new_discovery": True, "signal_strength": 0.9}
        result = crp.discover_new_node(echo)
        assert result["discovered"] is True
        assert len(crp.cosmic_field) == initial_size + 1
        assert "brand-new-node" in crp.cosmic_field
        assert len(crp.discovery_log) == 1

    def test_discover_new_node_already_known(self, crp: CosmicResonanceProtocol):
        """Discovering an already-known node should fail gracefully."""
        echo = {"source": "omni-hub", "is_new_discovery": True}
        result = crp.discover_new_node(echo)
        assert result["discovered"] is False
        assert result["reason"] == "already_known"

    def test_discover_new_node_insufficient_signal(self, crp: CosmicResonanceProtocol):
        """A new node with is_new_discovery=False should not be discovered."""
        echo = {"source": "weak-node", "is_new_discovery": False}
        result = crp.discover_new_node(echo)
        assert result["discovered"] is False
        assert result["reason"] == "insufficient_signal"

    def test_discover_new_node_invalid_input(self, crp: CosmicResonanceProtocol):
        """Non-dict input should return error."""
        result = crp.discover_new_node("not-a-dict")
        assert result["discovered"] is False
        assert "error" in result

    def test_discover_new_node_random_chance(self, crp: CosmicResonanceProtocol):
        """When is_new_discovery is absent, random chance applies."""
        with patch("core.cosmic_resonance_protocol.random.random", return_value=0.1):
            echo = {"source": "random-chance-node"}
            result = crp.discover_new_node(echo)
            assert result["discovered"] is True

    # ------------------------------------------------------------------
    # expand_resonance_field
    # ------------------------------------------------------------------
    def test_expand_field_structure(self, crp: CosmicResonanceProtocol):
        """expand_resonance_field should return a well-formed dict."""
        result = crp.expand_resonance_field(["node-a", "node-b"])
        assert isinstance(result, dict)
        assert "added" in result
        assert "skipped" in result
        assert "field_size" in result
        assert "stage" in result

    def test_expand_field_adds_new(self, crp: CosmicResonanceProtocol):
        """New nodes should be added to the field."""
        initial_size = len(crp.cosmic_field)
        result = crp.expand_resonance_field(["node-a", "node-b"])
        assert result["added"] == 2
        assert result["skipped"] == 0
        assert len(crp.cosmic_field) == initial_size + 2
        assert "node-a" in crp.cosmic_field
        assert "node-b" in crp.cosmic_field

    def test_expand_field_skips_known(self, crp: CosmicResonanceProtocol):
        """Already-known nodes should be skipped."""
        result = crp.expand_resonance_field(["omni-hub", "node-new"])
        assert result["added"] == 1
        assert result["skipped"] == 1

    def test_expand_field_invalid_input(self, crp: CosmicResonanceProtocol):
        """Non-list input should return error."""
        result = crp.expand_resonance_field("not-a-list")
        assert "error" in result
        assert result["added"] == 0

    def test_expand_field_stage_classification(self, crp: CosmicResonanceProtocol):
        """Stage should update after expansion."""
        result = crp.expand_resonance_field(["n1"])
        assert result["stage"] == "solar"  # 34 > 30

    # ------------------------------------------------------------------
    # compute_cosmic_coverage
    # ------------------------------------------------------------------
    def test_compute_cosmic_coverage_structure(self, crp: CosmicResonanceProtocol):
        """compute_cosmic_coverage should return a well-formed dict."""
        result = crp.compute_cosmic_coverage()
        assert isinstance(result, dict)
        assert "known_nodes" in result
        assert "estimated_unknown" in result
        assert "total_estimated" in result
        assert "coverage_ratio" in result
        assert "coverage_percent" in result
        assert "cosmic_stage" in result
        assert "pulse_count" in result

    def test_compute_cosmic_coverage_values(self, crp: CosmicResonanceProtocol):
        """Coverage values should be consistent."""
        result = crp.compute_cosmic_coverage()
        assert result["known_nodes"] == 33
        assert result["estimated_unknown"] == 10_000
        assert result["total_estimated"] == 10_033
        assert 0.0 < result["coverage_ratio"] < 1.0
        assert result["coverage_percent"] == pytest.approx(result["coverage_ratio"] * 100)

    def test_compute_cosmic_coverage_stage(self, crp: CosmicResonanceProtocol):
        """With 33 nodes, stage should be solar (>30)."""
        result = crp.compute_cosmic_coverage()
        assert result["cosmic_stage"] == "solar"

    def test_compute_cosmic_coverage_after_expand(self, crp: CosmicResonanceProtocol):
        """Coverage should decrease relatively as field expands."""
        before = crp.compute_cosmic_coverage()
        crp.expand_resonance_field(["n1", "n2", "n3"])
        after = crp.compute_cosmic_coverage()
        assert after["known_nodes"] == before["known_nodes"] + 3
        assert after["coverage_ratio"] > before["coverage_ratio"]

    # ------------------------------------------------------------------
    # get_status
    # ------------------------------------------------------------------
    def test_get_status_structure(self, crp: CosmicResonanceProtocol):
        """get_status should return a well-formed dict."""
        status = crp.get_status()
        assert isinstance(status, dict)
        assert status["module"] == "CosmicResonanceProtocol"
        assert status["version"] == "160"
        assert "field_size" in status
        assert "echo_count" in status
        assert "discovery_count" in status
        assert "pulse_count" in status
        assert "cosmic_coverage" in status
        assert "cosmic_stage" in status
        assert "estimated_unknown" in status

    def test_get_status_values(self, crp: CosmicResonanceProtocol):
        """Status values should reflect current state."""
        with patch("core.cosmic_resonance_protocol.random.random", return_value=0.1):
            crp.emit_cosmic_pulse(0.5)
        crp.receive_cosmic_echo({"source": "test"})
        crp.discover_new_node({"source": "new-one", "is_new_discovery": True})
        status = crp.get_status()
        assert status["field_size"] == 34
        assert status["echo_count"] == 2  # 1 from emit + 1 from receive
        assert status["discovery_count"] == 1
        assert status["pulse_count"] == 1
        assert status["cosmic_stage"] == "solar"  # 34 > 30

    # ------------------------------------------------------------------
    # Cosmic stage classification boundaries
    # ------------------------------------------------------------------
    def test_cosmic_stage_local(self, crp: CosmicResonanceProtocol):
        """<=10 nodes -> local."""
        crp.cosmic_field = {f"r{i}": {} for i in range(10)}
        assert crp.compute_cosmic_coverage()["cosmic_stage"] == "local"

    def test_cosmic_stage_planetary(self, crp: CosmicResonanceProtocol):
        """>10 nodes -> planetary."""
        crp.cosmic_field = {f"r{i}": {} for i in range(11)}
        assert crp.compute_cosmic_coverage()["cosmic_stage"] == "planetary"

    def test_cosmic_stage_solar(self, crp: CosmicResonanceProtocol):
        """>30 nodes -> solar."""
        crp.cosmic_field = {f"r{i}": {} for i in range(31)}
        assert crp.compute_cosmic_coverage()["cosmic_stage"] == "solar"

    def test_cosmic_stage_galactic(self, crp: CosmicResonanceProtocol):
        """>100 nodes -> galactic."""
        crp.cosmic_field = {f"r{i}": {} for i in range(101)}
        assert crp.compute_cosmic_coverage()["cosmic_stage"] == "galactic"

    def test_cosmic_stage_universal(self, crp: CosmicResonanceProtocol):
        """>1000 nodes -> universal."""
        crp.cosmic_field = {f"r{i}": {} for i in range(1001)}
        assert crp.compute_cosmic_coverage()["cosmic_stage"] == "universal"

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------
    def test_get_cosmic_resonance_protocol_singleton(self):
        """get_cosmic_resonance_protocol should return the same instance."""
        c1 = get_cosmic_resonance_protocol()
        c2 = get_cosmic_resonance_protocol()
        assert c1 is c2
        assert isinstance(c1, CosmicResonanceProtocol)
