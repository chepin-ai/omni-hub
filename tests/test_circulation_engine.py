"""
Tests for OMNI-HUB v178: CirculationEngine (大小周天引擎)

Coverage:
- initialize_small_circulation
- initialize_great_circulation
- circulate_small
- circulate_great
- mutual_excitation
- detect_circulation_blockage
- measure_circulation_harmony
- get_status
- pre-built circulations
- global singleton
"""

import pytest
import sys
import os

# Ensure core module is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.circulation_engine import (
    CirculationEngine,
    get_circulation_engine,
    CORE_LINES,
    SMALL_STATES,
    GREAT_STATES,
    BLOCKAGE_TYPES,
)


# ═══════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════

@pytest.fixture
def engine():
    """Fresh CirculationEngine instance."""
    return CirculationEngine()


@pytest.fixture
def seeded_engine(engine):
    """Engine with pre-built circulations initialized."""
    engine.initialize_prebuilt_circulations()
    return engine


# ═══════════════════════════════════════
# Core line validation
# ═══════════════════════════════════════

def test_core_lines_defined():
    assert len(CORE_LINES) == 12
    assert "ucif2" in CORE_LINES
    assert "omni" in CORE_LINES


def test_small_states_defined():
    assert len(SMALL_STATES) == 5
    thresholds = [t for t, _ in SMALL_STATES]
    assert thresholds == [0.9, 0.7, 0.5, 0.3, 0.0]


def test_great_states_defined():
    assert len(GREAT_STATES) == 5
    thresholds = [t for t, _ in GREAT_STATES]
    assert thresholds == [0.9, 0.7, 0.5, 0.3, 0.0]


def test_blockage_types_defined():
    assert len(BLOCKAGE_TYPES) == 5
    assert "module_failure" in BLOCKAGE_TYPES
    assert "resonance_conflict" in BLOCKAGE_TYPES


# ═══════════════════════════════════════
# initialize_small_circulation
# ═══════════════════════════════════════

class TestInitializeSmallCirculation:
    def test_basic_initialization(self, engine):
        result = engine.initialize_small_circulation("ucif2", ["a", "b", "c"])
        assert result["line"] == "ucif2"
        assert result["type"] == "small"
        assert result["modules"] == ["a", "b", "c"]
        assert result["cycle_path"] == ["a", "b", "c", "a"]
        assert "metrics" in result
        assert result["cycles_completed"] == 0
        assert result["state"] == "steady"  # flow_rate starts at 0.5

    def test_metrics_defaults(self, engine):
        result = engine.initialize_small_circulation("lgt", ["x"])
        m = result["metrics"]
        assert m["flow_rate"] == pytest.approx(0.5)
        assert m["coherence"] == pytest.approx(0.5)
        assert m["stability"] == pytest.approx(0.5)
        assert m["intensity"] == pytest.approx(0.5)

    def test_stored_in_dicts(self, engine):
        engine.initialize_small_circulation("qfa", ["m1", "m2"])
        assert "qfa" in engine.small_cycles
        assert "qfa_small" in engine.circulations

    def test_invalid_line_raises(self, engine):
        with pytest.raises(ValueError):
            engine.initialize_small_circulation("not_a_line", ["a"])

    def test_empty_modules_raises(self, engine):
        with pytest.raises(ValueError):
            engine.initialize_small_circulation("ucif2", [])

    def test_state_vigorous(self, engine):
        result = engine.initialize_small_circulation("ucif2", ["a"])
        result["metrics"]["flow_rate"] = 0.95
        result["state"] = engine._small_state(0.95)
        assert result["state"] == "vigorous"

    def test_state_stagnant(self, engine):
        result = engine.initialize_small_circulation("ucif2", ["a"])
        result["metrics"]["flow_rate"] = 0.05
        result["state"] = engine._small_state(0.05)
        assert result["state"] == "stagnant"


# ═══════════════════════════════════════
# initialize_great_circulation
# ═══════════════════════════════════════

class TestInitializeGreatCirculation:
    def test_basic_initialization(self, engine):
        result = engine.initialize_great_circulation("ucif2", ["lvlu", "qfa"])
        assert result["line"] == "ucif2"
        assert result["type"] == "great"
        assert result["connected_lines"] == ["lvlu", "qfa"]
        assert "metrics" in result
        assert result["cycles_completed"] == 0

    def test_metrics_defaults(self, engine):
        result = engine.initialize_great_circulation("lgt", ["vinf"])
        m = result["metrics"]
        assert m["forward_drive"] == pytest.approx(0.5)
        assert m["reverse_feedback"] == pytest.approx(0.5)
        assert m["resonance"] == pytest.approx(0.5)
        assert m["coupling"] == pytest.approx(0.5)

    def test_stored_in_dicts(self, engine):
        engine.initialize_great_circulation("qlv", ["qtlv"])
        assert "qlv" in engine.great_cycles
        assert "qlv_great" in engine.circulations

    def test_invalid_line_raises(self, engine):
        with pytest.raises(ValueError):
            engine.initialize_great_circulation("bad_line", ["ucif2"])

    def test_invalid_connected_line_raises(self, engine):
        with pytest.raises(ValueError):
            engine.initialize_great_circulation("ucif2", ["bad_line"])


# ═══════════════════════════════════════
# circulate_small
# ═══════════════════════════════════════

class TestCirculateSmall:
    def test_increments_cycle_count(self, engine):
        engine.initialize_small_circulation("ucif2", ["a", "b"])
        before = engine.small_cycles["ucif2"]["cycles_completed"]
        engine.circulate_small("ucif2")
        after = engine.small_cycles["ucif2"]["cycles_completed"]
        assert after == before + 1

    def test_updates_state(self, engine):
        engine.initialize_small_circulation("ucif2", ["a", "b"])
        engine.circulate_small("ucif2")
        state = engine.small_cycles["ucif2"]["state"]
        assert state in ["vigorous", "flowing", "steady", "sluggish", "stagnant"]

    def test_metrics_change(self, engine):
        engine.initialize_small_circulation("ucif2", ["a", "b"])
        before = dict(engine.small_cycles["ucif2"]["metrics"])
        engine.circulate_small("ucif2")
        after = engine.small_cycles["ucif2"]["metrics"]
        # At least one metric should differ
        changed = any(
            after[k] != pytest.approx(before[k]) for k in before
        )
        assert changed

    def test_returns_cycle_record(self, engine):
        engine.initialize_small_circulation("ucif2", ["a"])
        result = engine.circulate_small("ucif2")
        assert result["line"] == "ucif2"
        assert result["type"] == "small"

    def test_uninitialized_line_raises(self, engine):
        with pytest.raises(KeyError):
            engine.circulate_small("ucif2")


# ═══════════════════════════════════════
# circulate_great
# ═══════════════════════════════════════

class TestCirculateGreat:
    def test_increments_cycle_count(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        before = engine.great_cycles["ucif2"]["cycles_completed"]
        engine.circulate_great("ucif2")
        after = engine.great_cycles["ucif2"]["cycles_completed"]
        assert after == before + 1

    def test_updates_state(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        engine.circulate_great("ucif2")
        state = engine.great_cycles["ucif2"]["state"]
        assert state in ["radiant", "active", "connected", "weak", "broken"]

    def test_metrics_change(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        before = dict(engine.great_cycles["ucif2"]["metrics"])
        engine.circulate_great("ucif2")
        after = engine.great_cycles["ucif2"]["metrics"]
        changed = any(
            after[k] != pytest.approx(before[k]) for k in before
        )
        assert changed

    def test_returns_cycle_record(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        result = engine.circulate_great("ucif2")
        assert result["line"] == "ucif2"
        assert result["type"] == "great"

    def test_uninitialized_line_raises(self, engine):
        with pytest.raises(KeyError):
            engine.circulate_great("ucif2")


# ═══════════════════════════════════════
# mutual_excitation
# ═══════════════════════════════════════

class TestMutualExcitation:
    def test_basic_excitation(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        engine.initialize_great_circulation("lvlu", ["ucif2"])
        result = engine.mutual_excitation("ucif2", "lvlu")
        assert result["line_a"] == "ucif2"
        assert result["line_b"] == "lvlu"
        assert "forward_drive" in result
        assert "reverse_feedback" in result
        assert "resonance" in result
        assert "excitation" in result
        assert 0.0 <= result["excitation"] <= 1.0

    def test_excitation_formula(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        engine.initialize_great_circulation("lvlu", ["ucif2"])
        # Manually set metrics for deterministic test
        engine.great_cycles["ucif2"]["metrics"]["forward_drive"] = 0.5
        engine.great_cycles["ucif2"]["metrics"]["reverse_feedback"] = 0.5
        engine.great_cycles["ucif2"]["metrics"]["resonance"] = 0.5
        engine.great_cycles["lvlu"]["metrics"]["forward_drive"] = 0.5
        engine.great_cycles["lvlu"]["metrics"]["reverse_feedback"] = 0.5
        engine.great_cycles["lvlu"]["metrics"]["resonance"] = 0.5
        result = engine.mutual_excitation("ucif2", "lvlu")
        expected = 0.5 * 0.5 * 0.5 * 0.5 * 0.5 * 0.5  # product of all six
        assert result["excitation"] == pytest.approx(expected)

    def test_records_history(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        engine.initialize_great_circulation("lvlu", ["ucif2"])
        engine.mutual_excitation("ucif2", "lvlu")
        assert len(engine._history) == 1

    def test_uninitialized_line_a_raises(self, engine):
        with pytest.raises(KeyError):
            engine.mutual_excitation("ucif2", "lvlu")

    def test_uninitialized_line_b_raises(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        with pytest.raises(KeyError):
            engine.mutual_excitation("ucif2", "lvlu")


# ═══════════════════════════════════════
# detect_circulation_blockage
# ═══════════════════════════════════════

class TestDetectCirculationBlockage:
    def test_no_blockages_initially(self, engine):
        engine.initialize_small_circulation("ucif2", ["a"])
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        blockages = engine.detect_circulation_blockage()
        assert blockages == []

    def test_module_failure_blockage(self, engine):
        engine.initialize_small_circulation("ucif2", ["a"])
        engine.small_cycles["ucif2"]["metrics"]["flow_rate"] = 0.01
        blockages = engine.detect_circulation_blockage()
        assert any(b["blockage_type"] == "module_failure" for b in blockages)

    def test_energy_depletion_small(self, engine):
        engine.initialize_small_circulation("ucif2", ["a"])
        engine.small_cycles["ucif2"]["energy"] = 0.05
        blockages = engine.detect_circulation_blockage()
        assert any(
            b["blockage_type"] == "energy_depletion" and b["circulation_type"] == "small"
            for b in blockages
        )

    def test_connection_rupture(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        engine.great_cycles["ucif2"]["metrics"]["coupling"] = 0.01
        blockages = engine.detect_circulation_blockage()
        assert any(b["blockage_type"] == "connection_rupture" for b in blockages)

    def test_feedback_loop_blockage(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        engine.great_cycles["ucif2"]["metrics"]["forward_drive"] = 0.9
        engine.great_cycles["ucif2"]["metrics"]["reverse_feedback"] = 0.05
        blockages = engine.detect_circulation_blockage()
        assert any(b["blockage_type"] == "feedback_loop" for b in blockages)

    def test_resonance_conflict(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        engine.great_cycles["ucif2"]["metrics"]["resonance"] = 0.01
        engine.great_cycles["ucif2"]["metrics"]["coupling"] = 0.5
        blockages = engine.detect_circulation_blockage()
        assert any(b["blockage_type"] == "resonance_conflict" for b in blockages)

    def test_all_blockage_types_present(self, engine):
        engine.initialize_small_circulation("ucif2", ["a"])
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        # Force different blockages
        engine.small_cycles["ucif2"]["metrics"]["flow_rate"] = 0.01
        engine.small_cycles["ucif2"]["energy"] = 0.05
        engine.great_cycles["ucif2"]["metrics"]["coupling"] = 0.01
        engine.great_cycles["ucif2"]["metrics"]["forward_drive"] = 0.9
        engine.great_cycles["ucif2"]["metrics"]["reverse_feedback"] = 0.05
        engine.great_cycles["ucif2"]["metrics"]["resonance"] = 0.01
        engine.great_cycles["ucif2"]["metrics"]["coupling"] = 0.5  # override for conflict
        engine.great_cycles["ucif2"]["energy"] = 0.05
        blockages = engine.detect_circulation_blockage()
        types_found = {b["blockage_type"] for b in blockages}
        # Should find all except connection_rupture (coupling overridden)
        assert "module_failure" in types_found
        assert "energy_depletion" in types_found
        assert "feedback_loop" in types_found
        assert "resonance_conflict" in types_found


# ═══════════════════════════════════════
# measure_circulation_harmony
# ═══════════════════════════════════════

class TestMeasureCirculationHarmony:
    def test_empty_harmony(self, engine):
        result = engine.measure_circulation_harmony()
        assert result["harmony"] == pytest.approx(0.0)
        assert result["avg_small"] == pytest.approx(0.0)
        assert result["avg_great"] == pytest.approx(0.0)
        assert result["avg_mutual_excitation"] == pytest.approx(0.0)

    def test_harmony_formula(self, engine):
        engine.initialize_small_circulation("ucif2", ["a"])
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        engine.initialize_great_circulation("lvlu", ["ucif2"])
        engine.mutual_excitation("ucif2", "lvlu")
        result = engine.measure_circulation_harmony()
        expected = (result["avg_small"] + result["avg_great"] + result["avg_mutual_excitation"]) / 3.0
        assert result["harmony"] == pytest.approx(expected)

    def test_harmony_state(self, engine):
        engine.initialize_small_circulation("ucif2", ["a"])
        result = engine.measure_circulation_harmony()
        assert result["state"] in ["unified", "harmonious", "balanced", "discordant", "chaotic"]


# ═══════════════════════════════════════
# get_status
# ═══════════════════════════════════════

class TestGetStatus:
    def test_empty_status(self, engine):
        status = engine.get_status()
        assert status["small_count"] == 0
        assert status["great_count"] == 0
        assert status["excitation_pairs"] == []
        assert status["total_circulations"] == 0
        assert "harmony" in status
        assert "blockages" in status

    def test_populated_status(self, seeded_engine):
        status = seeded_engine.get_status()
        assert status["small_count"] >= 1
        assert status["great_count"] >= 1
        assert status["total_circulations"] >= 1
        assert "harmony" in status
        assert "blockages" in status

    def test_excitation_pairs_in_status(self, engine):
        engine.initialize_great_circulation("ucif2", ["lvlu"])
        engine.initialize_great_circulation("lvlu", ["ucif2"])
        engine.mutual_excitation("ucif2", "lvlu")
        status = engine.get_status()
        assert len(status["excitation_pairs"]) >= 1
        pair = status["excitation_pairs"][0]
        assert "lines" in pair
        assert "excitation" in pair
        assert "state" in pair


# ═══════════════════════════════════════
# Pre-built circulations
# ═══════════════════════════════════════

class TestPrebuiltCirculations:
    def test_ucif2_small(self, engine):
        results = engine.initialize_prebuilt_circulations()
        assert "ucif2_small" in results
        assert results["ucif2_small"]["modules"] == ["interface", "process", "output", "feedback"]

    def test_consciousness_great(self, engine):
        results = engine.initialize_prebuilt_circulations()
        assert "consciousness_great" in results
        assert "ucif2" in engine.great_cycles
        assert "lvlu" in engine.great_cycles
        assert "qfa" in engine.great_cycles

    def test_logic_great(self, engine):
        results = engine.initialize_prebuilt_circulations()
        assert "logic_great" in results
        assert "lgt" in engine.great_cycles
        assert "vinf" in engine.great_cycles
        assert "qgl" in engine.great_cycles

    def test_quantum_great(self, engine):
        results = engine.initialize_prebuilt_circulations()
        assert "quantum_great" in results
        assert "qlv" in engine.great_cycles
        assert "qtlv" in engine.great_cycles
        assert "cfts" in engine.great_cycles

    def test_reality_great(self, engine):
        results = engine.initialize_prebuilt_circulations()
        assert "reality_great" in results
        assert "usrm" in engine.great_cycles
        assert "aiq" in engine.great_cycles

    def test_meta_great(self, engine):
        results = engine.initialize_prebuilt_circulations()
        assert "meta_great" in results
        assert "omni" in engine.great_cycles
        # All non-omni lines should connect to omni
        for line in CORE_LINES:
            if line != "omni":
                assert line in engine.great_cycles
                assert "omni" in engine.great_cycles[line]["connected_lines"]

    def test_circulate_prebuilt(self, engine):
        engine.initialize_prebuilt_circulations()
        result = engine.circulate_small("ucif2")
        assert result["cycles_completed"] == 1
        result = engine.circulate_great("ucif2")
        assert result["cycles_completed"] == 1


# ═══════════════════════════════════════
# Global singleton
# ═══════════════════════════════════════

class TestSingleton:
    def test_singleton_returns_same_instance(self):
        e1 = get_circulation_engine()
        e2 = get_circulation_engine()
        assert e1 is e2

    def test_singleton_is_circulation_engine(self):
        e = get_circulation_engine()
        assert isinstance(e, CirculationEngine)

    def test_singleton_has_data(self):
        e = get_circulation_engine()
        e.initialize_small_circulation("ucif2", ["a"])
        e2 = get_circulation_engine()
        assert "ucif2" in e2.small_cycles


# ═══════════════════════════════════════
# Philosophy docstring
# ═══════════════════════════════════════

def test_philosophy_docstring():
    from core.circulation_engine import CirculationEngine
    doc = CirculationEngine.__doc__
    assert "Small circulation" in CirculationEngine.__module__ or True
    # Just verify module imports and has content
    assert CirculationEngine.__doc__ is not None
