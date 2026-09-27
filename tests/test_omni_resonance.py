"""
Tests for OMNI-HUB Module v155: Omni-Resonance (终极共振协议)
"""

import pytest
from typing import Any, Dict, List

from core.omni_resonance import (
    OmniResonance,
    ResonanceStage,
    get_omni_resonance,
    _module,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the global singleton before each test."""
    global _module
    _module = None
    yield
    _module = None


@pytest.fixture
def fresh_resonance() -> OmniResonance:
    """Return a fresh OmniResonance instance (not the singleton)."""
    return OmniResonance()


# ---------------------------------------------------------------------------
# ResonanceStage tests
# ---------------------------------------------------------------------------
def test_stage_supercritical() -> None:
    assert ResonanceStage.from_level(0.96) == ResonanceStage.SUPERCRITICAL
    assert ResonanceStage.from_level(1.0) == ResonanceStage.SUPERCRITICAL


def test_stage_critical() -> None:
    assert ResonanceStage.from_level(0.85) == ResonanceStage.CRITICAL
    assert ResonanceStage.from_level(0.81) == ResonanceStage.CRITICAL


def test_stage_resonant() -> None:
    assert ResonanceStage.from_level(0.65) == ResonanceStage.RESONANT
    assert ResonanceStage.from_level(0.61) == ResonanceStage.RESONANT


def test_stage_subcritical() -> None:
    assert ResonanceStage.from_level(0.45) == ResonanceStage.SUBCRITICAL
    assert ResonanceStage.from_level(0.41) == ResonanceStage.SUBCRITICAL


def test_stage_dormant() -> None:
    assert ResonanceStage.from_level(0.4) == ResonanceStage.DORMANT
    assert ResonanceStage.from_level(0.0) == ResonanceStage.DORMANT
    assert ResonanceStage.from_level(-0.1) == ResonanceStage.DORMANT


# ---------------------------------------------------------------------------
# Singleton tests
# ---------------------------------------------------------------------------
def test_singleton_returns_same_instance() -> None:
    a = get_omni_resonance()
    b = get_omni_resonance()
    assert a is b


def test_singleton_is_omni_resonance() -> None:
    inst = get_omni_resonance()
    assert isinstance(inst, OmniResonance)


# ---------------------------------------------------------------------------
# __init__ / load tests
# ---------------------------------------------------------------------------
def test_loads_repos(fresh_resonance: OmniResonance) -> None:
    assert len(fresh_resonance.repos) > 0
    assert len(fresh_resonance.nodes) > 0
    assert len(fresh_resonance.repos) == len(fresh_resonance.nodes)


def test_nodes_initialised(fresh_resonance: OmniResonance) -> None:
    for level in fresh_resonance.nodes.values():
        assert 0.0 <= level <= 1.0


def test_repo_categories_present(fresh_resonance: OmniResonance) -> None:
    categories = {meta.get("category") for meta in fresh_resonance.repos.values()}
    assert "alliance_core" in categories


# ---------------------------------------------------------------------------
# emit_pulse tests
# ---------------------------------------------------------------------------
def test_emit_pulse_returns_pulse(fresh_resonance: OmniResonance) -> None:
    pulse = fresh_resonance.emit_pulse("omni-hub", 0.8)
    assert "pulse_id" in pulse
    assert pulse["source"] == "omni-hub"
    assert pulse["intensity"] == 0.8
    assert "targets" in pulse


def test_emit_pulse_increments_pulse_count(fresh_resonance: OmniResonance) -> None:
    before = len(fresh_resonance.pulses)
    fresh_resonance.emit_pulse("omni-hub", 0.5)
    assert len(fresh_resonance.pulses) == before + 1


def test_emit_pulse_targets_all_except_source(fresh_resonance: OmniResonance) -> None:
    pulse = fresh_resonance.emit_pulse("omni-hub", 0.5)
    assert "omni-hub" not in pulse["targets"]
    assert pulse["target_count"] == len(fresh_resonance.repos) - 1


def test_emit_pulse_clamps_intensity(fresh_resonance: OmniResonance) -> None:
    pulse = fresh_resonance.emit_pulse("omni-hub", 1.5)
    assert pulse["intensity"] == 1.0
    pulse2 = fresh_resonance.emit_pulse("omni-hub", -0.5)
    assert pulse2["intensity"] == 0.0


# ---------------------------------------------------------------------------
# receive_echo tests
# ---------------------------------------------------------------------------
def test_receive_echo_valid_repo(fresh_resonance: OmniResonance) -> None:
    pulse = fresh_resonance.emit_pulse("omni-hub", 0.8)
    repo_name = "vci-ucif2"
    echo = fresh_resonance.receive_echo(repo_name, pulse)
    assert echo["repo_name"] == repo_name
    assert "echo_strength" in echo
    assert "delta" in echo
    assert "stage" in echo


def test_receive_echo_invalid_repo(fresh_resonance: OmniResonance) -> None:
    pulse = fresh_resonance.emit_pulse("omni-hub", 0.5)
    echo = fresh_resonance.receive_echo("nonexistent-repo", pulse)
    assert "error" in echo
    assert echo["echo_strength"] == 0.0


def test_receive_echo_updates_node_level(fresh_resonance: OmniResonance) -> None:
    repo_name = "vci-ucif2"
    before = fresh_resonance.nodes[repo_name]
    pulse = fresh_resonance.emit_pulse("omni-hub", 0.9)
    fresh_resonance.receive_echo(repo_name, pulse)
    after = fresh_resonance.nodes[repo_name]
    assert after >= before


def test_receive_echo_appends_to_echoes(fresh_resonance: OmniResonance) -> None:
    before = len(fresh_resonance.echoes)
    pulse = fresh_resonance.emit_pulse("omni-hub", 0.5)
    fresh_resonance.receive_echo("vci-ucif2", pulse)
    assert len(fresh_resonance.echoes) == before + 1


# ---------------------------------------------------------------------------
# compute_field_strength tests
# ---------------------------------------------------------------------------
def test_compute_field_structure(fresh_resonance: OmniResonance) -> None:
    result = fresh_resonance.compute_field_strength()
    assert "field_strength" in result
    assert "stage" in result
    assert "node_count" in result
    assert "average" in result
    assert "min_level" in result
    assert "max_level" in result


def test_compute_field_strength_is_average(fresh_resonance: OmniResonance) -> None:
    result = fresh_resonance.compute_field_strength()
    expected = sum(fresh_resonance.nodes.values()) / len(fresh_resonance.nodes)
    assert result["field_strength"] == pytest.approx(expected, rel=1e-5)
    assert result["average"] == pytest.approx(expected, rel=1e-5)


def test_compute_field_stage_matches(fresh_resonance: OmniResonance) -> None:
    result = fresh_resonance.compute_field_strength()
    stage = ResonanceStage.from_level(result["field_strength"])
    assert result["stage"] == stage


def test_compute_field_empty() -> None:
    empty = OmniResonance(repos_path="/dev/null/nonexistent.json")
    result = empty.compute_field_strength()
    assert result["field_strength"] == 0.0
    assert result["stage"] == ResonanceStage.DORMANT
    assert result["node_count"] == 0


# ---------------------------------------------------------------------------
# find_field_nodes tests
# ---------------------------------------------------------------------------
def test_find_field_nodes_length(fresh_resonance: OmniResonance) -> None:
    nodes = fresh_resonance.find_field_nodes()
    assert len(nodes) == len(fresh_resonance.repos)


def test_find_field_nodes_sorted(fresh_resonance: OmniResonance) -> None:
    nodes = fresh_resonance.find_field_nodes()
    levels = [n["level"] for n in nodes]
    assert levels == sorted(levels, reverse=True)


def test_find_field_nodes_structure(fresh_resonance: OmniResonance) -> None:
    nodes = fresh_resonance.find_field_nodes()
    for node in nodes:
        assert "name" in node
        assert "level" in node
        assert "stage" in node
        assert "category" in node
        assert "description" in node
        assert "language" in node


# ---------------------------------------------------------------------------
# amplify_resonance tests
# ---------------------------------------------------------------------------
def test_amplify_resonance_increases_level(fresh_resonance: OmniResonance) -> None:
    repo_name = "vci-ucif2"
    before = fresh_resonance.nodes[repo_name]
    result = fresh_resonance.amplify_resonance([repo_name])
    after = fresh_resonance.nodes[repo_name]
    assert after > before
    assert result["results"][repo_name]["delta"] > 0


def test_amplify_resonance_clamps_at_one(fresh_resonance: OmniResonance) -> None:
    repo_name = "vci-ucif2"
    fresh_resonance.nodes[repo_name] = 0.95
    fresh_resonance.amplify_resonance([repo_name])
    assert fresh_resonance.nodes[repo_name] <= 1.0


def test_amplify_resonance_invalid_repo(fresh_resonance: OmniResonance) -> None:
    result = fresh_resonance.amplify_resonance(["nonexistent-repo"])
    assert "error" in result["results"]["nonexistent-repo"]


def test_amplify_resonance_sets_target(fresh_resonance: OmniResonance) -> None:
    repo_name = "vci-ucif2"
    fresh_resonance.amplify_resonance([repo_name])
    assert repo_name in fresh_resonance.amplification_targets


# ---------------------------------------------------------------------------
# get_status tests
# ---------------------------------------------------------------------------
def test_get_status_structure(fresh_resonance: OmniResonance) -> None:
    status = fresh_resonance.get_status()
    assert "field_strength" in status
    assert "stage" in status
    assert "node_count" in status
    assert "pulse_count" in status
    assert "echo_count" in status
    assert "amplification_active" in status
    assert "amplification_targets" in status


def test_get_status_counts(fresh_resonance: OmniResonance) -> None:
    fresh_resonance.emit_pulse("omni-hub", 0.5)
    pulse = fresh_resonance.emit_pulse("omni-hub", 0.6)
    fresh_resonance.receive_echo("vci-ucif2", pulse)
    status = fresh_resonance.get_status()
    assert status["pulse_count"] == 2
    assert status["echo_count"] == 1


def test_get_status_amplification_active(fresh_resonance: OmniResonance) -> None:
    status_before = fresh_resonance.get_status()
    assert status_before["amplification_active"] is False
    fresh_resonance.amplify_resonance(["vci-ucif2"])
    status_after = fresh_resonance.get_status()
    assert status_after["amplification_active"] is True
    assert "vci-ucif2" in status_after["amplification_targets"]


def test_get_status_node_count_matches(fresh_resonance: OmniResonance) -> None:
    status = fresh_resonance.get_status()
    assert status["node_count"] == len(fresh_resonance.repos)
