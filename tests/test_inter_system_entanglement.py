"""
Tests for OMNI-HUB v149: Inter-System Entanglement
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.inter_system_entanglement import (
    InterSystemEntanglement,
    get_inter_system_entanglement,
    get_module,
)


class TestInterSystemEntanglement:
    """Comprehensive tests for the InterSystemEntanglement module."""

    # ------------------------------------------------------------------ #
    #  Lifecycle & singleton
    # ------------------------------------------------------------------ #
    def test_singleton_returns_same_instance(self):
        """get_inter_system_entanglement must return the same object."""
        a = get_inter_system_entanglement()
        b = get_inter_system_entanglement()
        assert a is b

    def test_get_module_alias(self):
        """get_module must be an alias for get_inter_system_entanglement."""
        a = get_module()
        b = get_inter_system_entanglement()
        assert a is b

    def test_get_status_structure(self):
        """get_status must return a dict with expected keys."""
        ise = InterSystemEntanglement()
        status = ise.get_status()
        expected_keys = {
            "module", "version", "entangled_pairs", "pair_count",
            "avg_correlation", "graph_density", "node_count", "edge_count",
            "propagation_count", "level_distribution", "timestamp",
        }
        assert expected_keys.issubset(status.keys())
        assert status["module"] == "InterSystemEntanglement"
        assert status["version"] == "v149"

    # ------------------------------------------------------------------ #
    #  entangle()
    # ------------------------------------------------------------------ #
    def test_entangle_creates_pair(self):
        """entangle must register a pair with the given strength."""
        ise = InterSystemEntanglement()
        result = ise.entangle("sys_a", "sys_b", 0.85)
        assert result["pair"] == ("sys_a", "sys_b")
        assert result["strength"] == 0.85
        assert result["level"] == "entangled"

    def test_entangle_clamps_strength(self):
        """Strength outside [0, 1] must be clamped."""
        ise = InterSystemEntanglement()
        assert ise.entangle("a", "b", 1.5)["strength"] == 1.0
        assert ise.entangle("c", "d", -0.3)["strength"] == 0.0

    def test_entangle_level_quantum(self):
        """Strength > 0.9 should produce quantum level."""
        ise = InterSystemEntanglement()
        assert ise.entangle("a", "b", 0.95)["level"] == "quantum"

    def test_entangle_level_correlated(self):
        """Strength > 0.4 should produce correlated level."""
        ise = InterSystemEntanglement()
        assert ise.entangle("a", "b", 0.55)["level"] == "correlated"

    def test_entangle_level_independent(self):
        """Strength <= 0.4 should produce independent level."""
        ise = InterSystemEntanglement()
        assert ise.entangle("a", "b", 0.3)["level"] == "independent"

    def test_entangle_dissolve(self):
        """Strength 0 must dissolve existing entanglement."""
        ise = InterSystemEntanglement()
        ise.entangle("a", "b", 0.8)
        result = ise.entangle("a", "b", 0.0)
        assert result["action"] == "dissolved"
        assert ("a", "b") not in ise.entangled_pairs

    def test_entangle_same_system_raises(self):
        """Entangling a system with itself must raise ValueError."""
        ise = InterSystemEntanglement()
        with pytest.raises(ValueError):
            ise.entangle("same", "same", 0.5)

    def test_entangle_empty_identifier_raises(self):
        """Empty system identifiers must raise ValueError."""
        ise = InterSystemEntanglement()
        with pytest.raises(ValueError):
            ise.entangle("", "b", 0.5)
        with pytest.raises(ValueError):
            ise.entangle("a", "", 0.5)

    def test_entangle_undirected(self):
        """Pair key must be canonical regardless of argument order."""
        ise = InterSystemEntanglement()
        ise.entangle("zebra", "alpha", 0.7)
        assert ("alpha", "zebra") in ise.entangled_pairs

    # ------------------------------------------------------------------ #
    #  propagate_change()
    # ------------------------------------------------------------------ #
    def test_propagate_to_entangled_partners(self):
        """Changes must propagate to all entangled partners."""
        ise = InterSystemEntanglement()
        ise.entangle("origin", "partner_a", 0.9)
        ise.entangle("origin", "partner_b", 0.5)
        result = ise.propagate_change("origin", {"energy": 100.0})
        assert "partner_a" in result["perturbations"]
        assert "partner_b" in result["perturbations"]
        assert result["affected_count"] == 2

    def test_propagate_weighted_by_strength(self):
        """Stronger entanglements should produce larger numeric perturbations."""
        ise = InterSystemEntanglement()
        ise.entangle("origin", "strong", 1.0)
        ise.entangle("origin", "weak", 0.1)
        result = ise.propagate_change("origin", {"energy": 100.0})
        strong_pert = result["perturbations"]["strong"]["energy"]
        weak_pert = result["perturbations"]["weak"]["energy"]
        assert strong_pert > weak_pert
        assert strong_pert == pytest.approx(100.0, rel=1e-6)
        assert weak_pert == pytest.approx(10.0, rel=1e-6)

    def test_propagate_no_partners(self):
        """Propagating from a system with no partners returns empty perturbations."""
        ise = InterSystemEntanglement()
        result = ise.propagate_change("lonely", {"energy": 50.0})
        assert result["perturbations"] == {}
        assert result["affected_count"] == 0

    def test_propagate_records_history(self):
        """Propagation must record numeric fields in state history."""
        ise = InterSystemEntanglement()
        ise.propagate_change("sys", {"temp": 25.0})
        assert "temp" in ise.state_histories["sys"]
        assert ise.state_histories["sys"]["temp"] == [25.0]

    def test_propagate_empty_system_raises(self):
        """Empty system identifier must raise ValueError."""
        ise = InterSystemEntanglement()
        with pytest.raises(ValueError):
            ise.propagate_change("", {"x": 1})

    def test_propagate_non_numeric_fields(self):
        """Non-numeric fields should propagate as-is with perturbation flag."""
        ise = InterSystemEntanglement()
        ise.entangle("a", "b", 0.8)
        result = ise.propagate_change("a", {"status": "active", "count": 5})
        pert = result["perturbations"]["b"]
        assert pert["status"] == "active"
        assert pert["_perturbation"] is True
        assert pert["_entanglement_strength"] == 0.8

    # ------------------------------------------------------------------ #
    #  measure_correlation()
    # ------------------------------------------------------------------ #
    def test_measure_correlation_identical(self):
        """Correlation of a system with itself must be 1.0."""
        ise = InterSystemEntanglement()
        corr = ise.measure_correlation("a", "a")
        assert corr["correlation"] == 1.0
        assert corr["level"] == "quantum"
        assert corr["method"] == "identity"

    def test_measure_correlation_with_history(self):
        """Correlation should be computed from aligned state histories."""
        ise = InterSystemEntanglement()
        # Build perfectly correlated histories
        for i in range(10):
            ise.propagate_change("a", {"metric": float(i)})
            ise.propagate_change("b", {"metric": float(i)})
        corr = ise.measure_correlation("a", "b")
        assert corr["correlation"] == pytest.approx(1.0, abs=1e-6)
        assert corr["level"] == "quantum"
        assert corr["method"] == "pearson"
        assert corr["sample_size"] == 10

    def test_measure_correlation_anti_correlated(self):
        """Anti-correlated histories should produce near -1.0."""
        ise = InterSystemEntanglement()
        for i in range(10):
            ise.propagate_change("a", {"metric": float(i)})
            ise.propagate_change("b", {"metric": float(-i)})
        corr = ise.measure_correlation("a", "b")
        assert corr["correlation"] == pytest.approx(-1.0, abs=1e-6)
        assert corr["level"] == "quantum"  # abs(strength) > 0.9

    def test_measure_correlation_fallback(self):
        """With no shared history, correlation falls back to entanglement strength."""
        ise = InterSystemEntanglement()
        ise.entangle("a", "b", 0.75)
        corr = ise.measure_correlation("a", "b")
        assert corr["method"] == "entanglement_strength"
        assert corr["correlation"] == pytest.approx(0.75, abs=1e-6)

    def test_measure_correlation_empty_system_raises(self):
        """Empty identifiers must raise ValueError."""
        ise = InterSystemEntanglement()
        with pytest.raises(ValueError):
            ise.measure_correlation("", "b")
        with pytest.raises(ValueError):
            ise.measure_correlation("a", "")

    # ------------------------------------------------------------------ #
    #  get_entanglement_graph()
    # ------------------------------------------------------------------ #
    def test_graph_empty(self):
        """Empty entanglement must produce empty graph."""
        ise = InterSystemEntanglement()
        graph = ise.get_entanglement_graph()
        assert graph["nodes"] == []
        assert graph["edges"] == []
        assert graph["node_count"] == 0
        assert graph["edge_count"] == 0

    def test_graph_structure(self):
        """Graph must reflect all entanglements."""
        ise = InterSystemEntanglement()
        ise.entangle("a", "b", 0.8)
        ise.entangle("b", "c", 0.6)
        graph = ise.get_entanglement_graph()
        assert set(graph["nodes"]) == {"a", "b", "c"}
        assert graph["node_count"] == 3
        assert graph["edge_count"] == 2
        edge_pairs = {(e["source"], e["target"]) for e in graph["edges"]}
        assert ("a", "b") in edge_pairs
        assert ("b", "c") in edge_pairs

    def test_graph_includes_orphan_systems(self):
        """Systems with state histories but no entanglements must appear as nodes."""
        ise = InterSystemEntanglement()
        ise.propagate_change("orphan", {"x": 1.0})
        graph = ise.get_entanglement_graph()
        assert "orphan" in graph["nodes"]

    # ------------------------------------------------------------------ #
    #  get_status()  (advanced)
    # ------------------------------------------------------------------ #
    def test_status_density(self):
        """Graph density must be correctly calculated for a triangle."""
        ise = InterSystemEntanglement()
        # 3 nodes, 3 edges = complete graph -> density 1.0
        ise.entangle("a", "b", 0.5)
        ise.entangle("b", "c", 0.5)
        ise.entangle("a", "c", 0.5)
        status = ise.get_status()
        assert status["graph_density"] == pytest.approx(1.0, abs=1e-6)
        assert status["pair_count"] == 3

    def test_status_level_distribution(self):
        """Level distribution must count entanglements correctly."""
        ise = InterSystemEntanglement()
        ise.entangle("a", "b", 0.95)  # quantum
        ise.entangle("c", "d", 0.80)  # entangled
        ise.entangle("e", "f", 0.50)  # correlated
        ise.entangle("g", "h", 0.20)  # independent
        status = ise.get_status()
        dist = status["level_distribution"]
        assert dist.get("quantum") == 1
        assert dist.get("entangled") == 1
        assert dist.get("correlated") == 1
        assert dist.get("independent") == 1

    def test_status_propagation_count(self):
        """Status must track the number of propagations."""
        ise = InterSystemEntanglement()
        for _ in range(3):
            ise.propagate_change("sys", {"val": float(_)})
        status = ise.get_status()
        assert status["propagation_count"] == 3

    # ------------------------------------------------------------------ #
    #  Event bus integration
    # ------------------------------------------------------------------ #
    def test_event_bus_emit(self):
        """Setting an event bus and propagating should attempt to emit."""
        class FakeBus:
            def __init__(self):
                self.events = []

            def emit(self, event_type, payload):
                self.events.append((event_type, payload))

        bus = FakeBus()
        ise = InterSystemEntanglement()
        ise.set_event_bus(bus)
        ise.entangle("a", "b", 0.9)
        assert any(e[0] == "entanglement.created" for e in bus.events)

    def test_event_bus_no_crash_on_bad_bus(self):
        """A malformed event bus must not crash operations."""
        class BadBus:
            pass

        ise = InterSystemEntanglement()
        ise.set_event_bus(BadBus())
        # Must not raise
        ise.entangle("a", "b", 0.5)
        ise.propagate_change("a", {"x": 1.0})

    # ------------------------------------------------------------------ #
    #  Defensive programming
    # ------------------------------------------------------------------ #
    def test_pearson_zero_variance(self):
        """Pearson with zero variance must return 0.0, not NaN."""
        ise = InterSystemEntanglement()
        # Manually inject identical values
        corr = ise._pearson_correlation([5.0, 5.0, 5.0], [5.0, 5.0, 5.0])
        assert corr == 0.0

    def test_history_trimming(self):
        """State histories must be trimmed after 1000 entries."""
        ise = InterSystemEntanglement()
        for i in range(1005):
            ise.propagate_change("sys", {"metric": float(i)})
        assert len(ise.state_histories["sys"]["metric"]) == 1000
        assert ise.state_histories["sys"]["metric"][0] == 5.0

    def test_correlation_cache(self):
        """measure_correlation must populate the correlation_matrix cache."""
        ise = InterSystemEntanglement()
        ise.entangle("a", "b", 0.66)
        ise.measure_correlation("a", "b")
        assert ("a", "b") in ise.correlation_matrix


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
