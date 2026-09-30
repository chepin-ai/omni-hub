"""
Tests for OMNI-HUB Module v177: PatternCircles (Pattern-圈)
"""

import pytest
from typing import Dict, Any, List

from core.pattern_circles import (
    PatternCircles,
    get_pattern_circles,
    ALLIANCE_CORE_LINES,
    ALLIANCE_NODES,
    CIRCLE_PATTERNS,
    META_INTERACTIONS,
    DEPTH_LEVELS,
)


class TestPatternCirclesCreation:
    """Test suite for circle and meta-circle creation."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the global singleton before each test."""
        import core.pattern_circles as pc
        pc._module = None
        yield
        pc._module = None

    @pytest.fixture
    def pc(self) -> PatternCircles:
        """Fresh PatternCircles instance."""
        return PatternCircles()

    # ------------------------------------------------------------------
    # create_circle
    # ------------------------------------------------------------------
    def test_create_circle_basic(self, pc: PatternCircles):
        """A newly created circle should have the right shape."""
        result = pc.create_circle("test_circle", ["ucif2", "lvlu"], "resonance")
        assert isinstance(result, dict)
        assert result["name"] == "test_circle"
        assert result["members"] == ["ucif2", "lvlu"]
        assert result["pattern"] == "resonance"
        assert result["level"] == "circle"
        assert "depth" in result

    def test_create_circle_dedupes_members(self, pc: PatternCircles):
        """Duplicate members should be deduplicated while preserving order."""
        result = pc.create_circle("dup", ["a", "a", "b", "c", "b"], "spiral")
        assert result["members"] == ["a", "b", "c"]

    def test_create_circle_invalid_pattern_defaults(self, pc: PatternCircles):
        """Unknown pattern falls back to 'resonance'."""
        result = pc.create_circle("bad", ["x"], "unknown_pattern")
        assert result["pattern"] == "resonance"

    def test_create_circle_all_patterns(self, pc: PatternCircles):
        """All valid patterns should be accepted."""
        for pat in CIRCLE_PATTERNS:
            c = pc.create_circle(f"c_{pat}", ["n1"], pat)
            assert c["pattern"] == pat

    def test_create_circle_stored_in_dict(self, pc: PatternCircles):
        """Created circle should appear in the internal dictionary."""
        pc.create_circle("stored", ["a", "b"], "lattice")
        assert "stored" in pc.circles
        assert pc.circles["stored"]["name"] == "stored"

    # ------------------------------------------------------------------
    # Pre-built circles
    # ------------------------------------------------------------------
    def test_prebuilt_circles_exist(self, pc: PatternCircles):
        """All canonical alliance circles should be bootstrapped."""
        expected = [
            "consciousness_circle",
            "logic_circle",
            "quantum_circle",
            "reality_circle",
            "meta_circle",
            "core_circle",
            "alliance_circle",
        ]
        for name in expected:
            assert name in pc.circles, f"Pre-built circle '{name}' missing"

    def test_prebuilt_consciousness_circle(self, pc: PatternCircles):
        c = pc.circles["consciousness_circle"]
        assert set(c["members"]) == {"ucif2", "lvlu", "qfa"}
        assert c["pattern"] == "resonance"

    def test_prebuilt_logic_circle(self, pc: PatternCircles):
        c = pc.circles["logic_circle"]
        assert set(c["members"]) == {"lgt", "vinf", "qgl"}
        assert c["pattern"] == "rotation"

    def test_prebuilt_quantum_circle(self, pc: PatternCircles):
        c = pc.circles["quantum_circle"]
        assert set(c["members"]) == {"qlv", "qtlv", "cfts"}
        assert c["pattern"] == "pulsation"

    def test_prebuilt_reality_circle(self, pc: PatternCircles):
        c = pc.circles["reality_circle"]
        assert set(c["members"]) == {"usrm", "aiq"}
        assert c["pattern"] == "spiral"

    def test_prebuilt_meta_circle(self, pc: PatternCircles):
        c = pc.circles["meta_circle"]
        assert c["members"] == ["omni"]
        assert c["pattern"] == "lattice"

    def test_prebuilt_core_circle(self, pc: PatternCircles):
        c = pc.circles["core_circle"]
        assert set(c["members"]) == set(ALLIANCE_CORE_LINES)

    def test_prebuilt_alliance_circle(self, pc: PatternCircles):
        c = pc.circles["alliance_circle"]
        assert set(c["members"]) == set(ALLIANCE_NODES)

    # ------------------------------------------------------------------
    # create_meta_circle
    # ------------------------------------------------------------------
    def test_create_meta_circle_basic(self, pc: PatternCircles):
        """Meta-circle should reference existing circles."""
        pc.create_circle("c1", ["a"], "resonance")
        pc.create_circle("c2", ["b"], "rotation")
        result = pc.create_meta_circle("m1", ["c1", "c2"], "nesting")
        assert result["name"] == "m1"
        assert result["circles"] == ["c1", "c2"]
        assert result["interaction"] == "nesting"
        assert result["level"] == "meta"

    def test_create_meta_circle_invalid_interaction_defaults(self, pc: PatternCircles):
        """Unknown interaction falls back to 'nesting'."""
        pc.create_circle("c1", ["a"], "resonance")
        result = pc.create_meta_circle("m1", ["c1"], "bogus")
        assert result["interaction"] == "nesting"

    def test_create_meta_circle_skips_unknown_circles(self, pc: PatternCircles):
        """References to non-existent circles are silently dropped."""
        pc.create_circle("c1", ["a"], "resonance")
        result = pc.create_meta_circle("m1", ["c1", "nonexistent"], "weaving")
        assert result["circles"] == ["c1"]

    def test_create_meta_circle_all_interactions(self, pc: PatternCircles):
        """All valid interactions should be accepted."""
        pc.create_circle("cx", ["a"], "resonance")
        for inter in META_INTERACTIONS:
            m = pc.create_meta_circle(f"m_{inter}", ["cx"], inter)
            assert m["interaction"] == inter


class TestPatternCirclesNet:
    """Test suite for circle-net construction and resonance."""

    @pytest.fixture
    def pc(self) -> PatternCircles:
        return PatternCircles()

    def test_build_circle_net_structure(self, pc: PatternCircles):
        """build_circle_net should return a well-formed dict."""
        net = pc.build_circle_net()
        assert isinstance(net, dict)
        assert "nodes" in net
        assert "edges" in net
        assert "density" in net
        assert "node_count" in net
        assert "edge_count" in net
        assert net["node_count"] == len(net["nodes"])
        assert net["edge_count"] == len(net["edges"])

    def test_build_circle_net_nodes_have_types(self, pc: PatternCircles):
        net = pc.build_circle_net()
        for name, node in net["nodes"].items():
            assert "type" in node
            assert node["type"] in ("circle", "meta_circle")

    def test_build_circle_net_density_in_range(self, pc: PatternCircles):
        net = pc.build_circle_net()
        assert 0.0 <= net["density"] <= 1.0

    # ------------------------------------------------------------------
    # compute_circle_resonance
    # ------------------------------------------------------------------
    def test_resonance_identical_circles(self, pc: PatternCircles):
        """Identical members + same pattern should yield high resonance."""
        pc.create_circle("r1", ["a", "b", "c"], "resonance")
        pc.create_circle("r2", ["a", "b", "c"], "resonance")
        result = pc.compute_circle_resonance("r1", "r2")
        assert result["resonance"] > 0.5
        assert result["member_overlap"] == 1.0
        assert result["pattern_similarity"] == 1.0

    def test_resonance_no_overlap(self, pc: PatternCircles):
        """Disjoint member sets should yield zero resonance."""
        pc.create_circle("r1", ["a", "b"], "resonance")
        pc.create_circle("r2", ["c", "d"], "rotation")
        result = pc.compute_circle_resonance("r1", "r2")
        assert result["resonance"] == 0.0
        assert result["member_overlap"] == 0.0

    def test_resonance_partial_overlap(self, pc: PatternCircles):
        """Partial overlap should yield intermediate resonance."""
        pc.create_circle("r1", ["a", "b", "c"], "resonance")
        pc.create_circle("r2", ["b", "c", "d"], "resonance")
        result = pc.compute_circle_resonance("r1", "r2")
        assert 0.0 < result["resonance"] < 1.0
        assert 0.0 < result["member_overlap"] < 1.0

    def test_resonance_unknown_circle(self, pc: PatternCircles):
        """Resonance with a missing circle should be zero."""
        pc.create_circle("r1", ["a"], "resonance")
        result = pc.compute_circle_resonance("r1", "missing")
        assert result["resonance"] == 0.0

    def test_resonance_formula_sqrt(self, pc: PatternCircles):
        """Resonance should be the square root of the product of factors."""
        pc.create_circle("r1", ["x", "y"], "resonance")
        pc.create_circle("r2", ["x", "y"], "resonance")
        result = pc.compute_circle_resonance("r1", "r2")
        raw = result["member_overlap"] * result["pattern_similarity"] * result["interaction_frequency"]
        import math
        assert abs(result["resonance"] - math.sqrt(raw)) < 1e-6

    def test_resonance_symmetric(self, pc: PatternCircles):
        """Resonance between A and B must equal resonance between B and A."""
        pc.create_circle("r1", ["a", "b", "c"], "resonance")
        pc.create_circle("r2", ["b", "c", "d"], "spiral")
        ab = pc.compute_circle_resonance("r1", "r2")
        ba = pc.compute_circle_resonance("r2", "r1")
        assert ab["resonance"] == ba["resonance"]


class TestPatternCirclesMetaPatterns:
    """Test suite for meta-pattern detection."""

    @pytest.fixture
    def pc(self) -> PatternCircles:
        return PatternCircles()

    def test_detect_meta_patterns_structure(self, pc: PatternCircles):
        """Each detected pattern should have the expected keys."""
        pc.create_meta_circle("meta_a", ["consciousness_circle"], "nesting")
        patterns = pc.detect_meta_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        for p in patterns:
            assert "pattern" in p
            assert "strength" in p
            assert "level" in p
            assert "affected_meta_circles" in p
            assert p["level"] in ["transcendent", "emergent", "complex", "simple", "trivial"]

    def test_detect_meta_patterns_known_patterns(self, pc: PatternCircles):
        """All five meta-patterns should be reported."""
        pc.create_meta_circle("m1", ["consciousness_circle", "logic_circle"], "nesting")
        patterns = pc.detect_meta_patterns()
        names = {p["pattern"] for p in patterns}
        expected = {"self_similarity", "recursivity", "holarchy", "emergence", "symmetry_breaking"}
        assert names == expected

    def test_detect_meta_patterns_holarchy(self, pc: PatternCircles):
        """Holarchy pattern should flag meta-circles with nesting + >1 child."""
        pc.create_meta_circle("m_hol", ["consciousness_circle", "logic_circle"], "nesting")
        patterns = pc.detect_meta_patterns()
        hol = next(p for p in patterns if p["pattern"] == "holarchy")
        assert "m_hol" in hol["affected_meta_circles"]

    def test_detect_meta_patterns_emergence(self, pc: PatternCircles):
        """Emergence pattern should flag meta-circles with diverse child patterns."""
        pc.create_meta_circle("m_em", ["consciousness_circle", "logic_circle"], "weaving")
        patterns = pc.detect_meta_patterns()
        em = next(p for p in patterns if p["pattern"] == "emergence")
        assert "m_em" in em["affected_meta_circles"]

    def test_detect_meta_patterns_empty_meta(self, pc: PatternCircles):
        """With no meta-circles, result should be empty list."""
        pc.meta_circles.clear()
        patterns = pc.detect_meta_patterns()
        assert patterns == []


class TestPatternCirclesDepth:
    """Test suite for fractal depth queries."""

    @pytest.fixture
    def pc(self) -> PatternCircles:
        return PatternCircles()

    def test_depth_structure(self, pc: PatternCircles):
        """get_circle_depth should return a well-formed dict."""
        d = pc.get_circle_depth("consciousness_circle")
        assert isinstance(d, dict)
        assert "name" in d
        assert "depth" in d
        assert "level_name" in d
        assert "max_nesting" in d
        assert "contained_circles" in d

    def test_depth_unknown_circle(self, pc: PatternCircles):
        """Unknown circle should report depth 0 / unknown."""
        d = pc.get_circle_depth("nonexistent")
        assert d["depth"] == 0
        assert d["level_name"] == "unknown"

    def test_depth_alliance_circle_is_cloud(self, pc: PatternCircles):
        """The alliance_circle contains all 33 nodes -> depth 5 (cloud)."""
        d = pc.get_circle_depth("alliance_circle")
        assert d["depth"] == 5
        assert d["level_name"] == "cloud"

    def test_depth_core_circle_is_field(self, pc: PatternCircles):
        """The core_circle contains all 12 core lines -> depth 4 (field)."""
        d = pc.get_circle_depth("core_circle")
        assert d["depth"] == 4
        assert d["level_name"] == "field"

    def test_depth_small_circle_is_meta_or_circle(self, pc: PatternCircles):
        """Small circles (2-3 members) should be depth 2 (meta boundary)."""
        d = pc.get_circle_depth("consciousness_circle")
        assert d["depth"] == 2
        assert d["level_name"] == "meta"

    def test_depth_meta_circle_boosted(self, pc: PatternCircles):
        """Meta-circle depth should be boosted above its deepest child."""
        pc.create_meta_circle("m_deep", ["alliance_circle"], "nesting")
        d = pc.get_circle_depth("m_deep")
        assert d["depth"] == 5  # min(5, max_child+1) where max_child=5

    def test_depth_levels_mapping(self):
        """DEPTH_LEVELS should contain the expected mappings."""
        assert DEPTH_LEVELS[5] == "cloud"
        assert DEPTH_LEVELS[4] == "field"
        assert DEPTH_LEVELS[3] == "net"
        assert DEPTH_LEVELS[2] == "meta"
        assert DEPTH_LEVELS[1] == "circle"


class TestPatternCirclesStatus:
    """Test suite for system status."""

    @pytest.fixture
    def pc(self) -> PatternCircles:
        return PatternCircles()

    def test_get_status_structure(self, pc: PatternCircles):
        """get_status should return the required keys."""
        s = pc.get_status()
        assert isinstance(s, dict)
        assert "circle_count" in s
        assert "meta_count" in s
        assert "net_density" in s
        assert "max_depth" in s

    def test_get_status_counts(self, pc: PatternCircles):
        """Counts should reflect the number of circles and meta-circles."""
        s = pc.get_status()
        assert s["circle_count"] == len(pc.circles)
        assert s["meta_count"] == len(pc.meta_circles)

    def test_get_status_max_depth(self, pc: PatternCircles):
        """max_depth should be the maximum depth across all circles."""
        s = pc.get_status()
        assert s["max_depth"] >= 5  # alliance_circle is cloud(5)

    def test_get_status_density(self, pc: PatternCircles):
        """Density should be a float in [0, 1]."""
        s = pc.get_status()
        assert isinstance(s["net_density"], float)
        assert 0.0 <= s["net_density"] <= 1.0


class TestPatternCirclesSingleton:
    """Test suite for the global singleton."""

    def test_singleton_identity(self):
        """Repeated calls should return the same object."""
        import core.pattern_circles as pc
        pc._module = None
        a = get_pattern_circles()
        b = get_pattern_circles()
        assert a is b
        pc._module = None

    def test_singleton_has_prebuilt_circles(self):
        """The singleton should contain the pre-built circles."""
        import core.pattern_circles as pc
        pc._module = None
        inst = get_pattern_circles()
        assert "consciousness_circle" in inst.circles
        assert "alliance_circle" in inst.circles
        pc._module = None
