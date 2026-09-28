"""
Tests for Alliance Collective Intelligence Module (v159)
"""

import pytest
from core.alliance_collective_intelligence import (
    AllianceCollectiveIntelligence,
    _connectivity_density,
    _collective_iq,
    _information_flow_rate,
    _iq_level,
    _load_repos,
    _repo_capability,
    get_alliance_collective_intelligence,
)


class TestAllianceCollectiveIntelligence:
    """Comprehensive tests for the ACI module."""

    @pytest.fixture
    def aci(self) -> AllianceCollectiveIntelligence:
        return AllianceCollectiveIntelligence()

    # ------------------------------------------------------------------
    # Constructor / data loading
    # ------------------------------------------------------------------

    def test_loads_33_repos(self, aci: AllianceCollectiveIntelligence) -> None:
        assert len(aci.repos) == 33, f"Expected 33 repos, got {len(aci.repos)}"

    def test_collective_memory_initially_empty(self, aci: AllianceCollectiveIntelligence) -> None:
        assert aci.collective_memory == {}

    def test_insight_history_initially_empty(self, aci: AllianceCollectiveIntelligence) -> None:
        assert aci.insight_history == []

    def test_repo_capabilities_populated(self, aci: AllianceCollectiveIntelligence) -> None:
        assert len(aci._repo_capabilities) == 33
        for cap in aci._repo_capabilities.values():
            assert 50.0 <= cap <= 120.0

    def test_metrics_computed(self, aci: AllianceCollectiveIntelligence) -> None:
        assert aci._avg_capability > 0
        assert 0.0 <= aci._density <= 1.0
        assert aci._flow_rate > 0
        assert aci._collective_iq > 0

    # ------------------------------------------------------------------
    # aggregate_perspectives
    # ------------------------------------------------------------------

    def test_aggregate_returns_dict(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.aggregate_perspectives("quantum")
        assert isinstance(result, dict)

    def test_aggregate_has_expected_keys(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.aggregate_perspectives("ai")
        assert "topic" in result
        assert "repo_count" in result
        assert "perspectives" in result
        assert "total_contribution" in result
        assert "top_contributor" in result
        assert "timestamp" in result

    def test_aggregate_repo_count_matches(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.aggregate_perspectives("scaling")
        assert result["repo_count"] == 33

    def test_aggregate_perspectives_list_length(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.aggregate_perspectives("value")
        assert len(result["perspectives"]) == 33

    def test_aggregate_top_contributor_not_none(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.aggregate_perspectives("consciousness")
        assert result["top_contributor"] is not None

    def test_aggregate_total_contribution_positive(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.aggregate_perspectives("logic")
        assert result["total_contribution"] > 0

    def test_aggregate_insight_stored(self, aci: AllianceCollectiveIntelligence) -> None:
        aci.aggregate_perspectives("integration")
        assert "integration" in aci._aggregate_insights

    def test_aggregate_insight_history_updated(self, aci: AllianceCollectiveIntelligence) -> None:
        aci.aggregate_perspectives("performance")
        assert any(i["type"] == "aggregate" for i in aci.insight_history)

    def test_aggregate_generic_topic(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.aggregate_perspectives("something random")
        assert result["repo_count"] == 33
        assert len(result["perspectives"]) == 33

    # ------------------------------------------------------------------
    # detect_emergent_patterns
    # ------------------------------------------------------------------

    def test_detect_returns_list(self, aci: AllianceCollectiveIntelligence) -> None:
        patterns = aci.detect_emergent_patterns()
        assert isinstance(patterns, list)

    def test_detect_patterns_have_required_fields(self, aci: AllianceCollectiveIntelligence) -> None:
        patterns = aci.detect_emergent_patterns()
        for p in patterns:
            assert "type" in p
            assert "description" in p
            assert "repos" in p
            assert "strength" in p
            assert p["type"] in [
                "convergent_evolution",
                "complementary_capabilities",
                "shared_challenges",
                "synergistic_opportunities",
            ]

    def test_detect_has_convergent_evolution(self, aci: AllianceCollectiveIntelligence) -> None:
        patterns = aci.detect_emergent_patterns()
        types = [p["type"] for p in patterns]
        assert "convergent_evolution" in types

    def test_detect_has_complementary_capabilities(self, aci: AllianceCollectiveIntelligence) -> None:
        patterns = aci.detect_emergent_patterns()
        types = [p["type"] for p in patterns]
        assert "complementary_capabilities" in types

    def test_detect_patterns_stored(self, aci: AllianceCollectiveIntelligence) -> None:
        patterns = aci.detect_emergent_patterns()
        assert aci._detected_patterns == patterns

    def test_detect_insight_history_updated(self, aci: AllianceCollectiveIntelligence) -> None:
        aci.detect_emergent_patterns()
        assert any(i["type"] == "detect_patterns" for i in aci.insight_history)

    # ------------------------------------------------------------------
    # solve_collective_problem
    # ------------------------------------------------------------------

    def test_solve_returns_dict(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.solve_collective_problem({
            "type": "architecture_decision",
            "description": "Which message bus to adopt?",
        })
        assert isinstance(result, dict)

    def test_solve_has_expected_keys(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.solve_collective_problem({
            "type": "scaling_challenge",
            "description": "Handle 10x traffic",
        })
        assert "problem_type" in result
        assert "relevant_repos" in result
        assert "repo_count" in result
        assert "avg_expertise" in result
        assert "solution_quality" in result
        assert "collective_iq_boost" in result
        assert "effective_quality" in result
        assert "recommended_action" in result

    def test_solve_quality_in_range(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.solve_collective_problem({
            "type": "integration_issue",
            "description": "Fix API mismatch",
        })
        assert 0.0 <= result["solution_quality"] <= 1.0
        assert 0.0 <= result["effective_quality"] <= 1.0

    def test_solve_relevant_repos_non_empty(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.solve_collective_problem({
            "type": "performance_bottleneck",
            "description": "Slow inference",
        })
        assert result["repo_count"] > 0
        assert len(result["relevant_repos"]) > 0

    def test_solve_stores_in_memory(self, aci: AllianceCollectiveIntelligence) -> None:
        problem = {"type": "architecture_decision", "description": "Pick DB"}
        aci.solve_collective_problem(problem)
        assert "Pick DB" in aci.collective_memory

    def test_solve_invalid_type_defaults(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.solve_collective_problem({"type": "unknown_type"})
        assert result["problem_type"] == "architecture_decision"

    def test_solve_insight_history_updated(self, aci: AllianceCollectiveIntelligence) -> None:
        aci.solve_collective_problem({"type": "scaling_challenge"})
        assert any(i["type"] == "solve" for i in aci.insight_history)

    # ------------------------------------------------------------------
    # forecast_collective_trajectory
    # ------------------------------------------------------------------

    def test_forecast_returns_dict(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.forecast_collective_trajectory()
        assert isinstance(result, dict)

    def test_forecast_has_expected_keys(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.forecast_collective_trajectory()
        assert "current_iq" in result
        assert "current_level" in result
        assert "projected_iq_6m" in result
        assert "projected_level" in result
        assert "growth_rate" in result
        assert "capability_trend" in result
        assert "phase" in result
        assert "key_drivers" in result
        assert "recommendation" in result

    def test_forecast_iq_positive(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.forecast_collective_trajectory()
        assert result["current_iq"] > 0
        assert result["projected_iq_6m"] > 0

    def test_forecast_level_valid(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.forecast_collective_trajectory()
        valid_levels = {"superintelligence", "genius", "gifted", "bright", "average", "below_average"}
        assert result["current_level"] in valid_levels
        assert result["projected_level"] in valid_levels

    def test_forecast_key_drivers_non_empty(self, aci: AllianceCollectiveIntelligence) -> None:
        result = aci.forecast_collective_trajectory()
        assert len(result["key_drivers"]) > 0

    def test_forecast_insight_history_updated(self, aci: AllianceCollectiveIntelligence) -> None:
        aci.forecast_collective_trajectory()
        assert any(i["type"] == "forecast" for i in aci.insight_history)

    # ------------------------------------------------------------------
    # get_status
    # ------------------------------------------------------------------

    def test_status_returns_dict(self, aci: AllianceCollectiveIntelligence) -> None:
        status = aci.get_status()
        assert isinstance(status, dict)

    def test_status_has_expected_keys(self, aci: AllianceCollectiveIntelligence) -> None:
        status = aci.get_status()
        assert "collective_iq" in status
        assert "iq_level" in status
        assert "repo_count" in status
        assert "avg_capability" in status
        assert "connectivity_density" in status
        assert "information_flow_rate" in status
        assert "aggregate_insights" in status
        assert "detected_patterns" in status
        assert "insight_history_count" in status
        assert "collective_memory_keys" in status

    def test_status_repo_count(self, aci: AllianceCollectiveIntelligence) -> None:
        status = aci.get_status()
        assert status["repo_count"] == 33

    def test_status_iq_level_valid(self, aci: AllianceCollectiveIntelligence) -> None:
        status = aci.get_status()
        valid_levels = {"superintelligence", "genius", "gifted", "bright", "average", "below_average"}
        assert status["iq_level"] in valid_levels

    # ------------------------------------------------------------------
    # Global singleton
    # ------------------------------------------------------------------

    def test_singleton_returns_instance(self) -> None:
        inst1 = get_alliance_collective_intelligence()
        inst2 = get_alliance_collective_intelligence()
        assert isinstance(inst1, AllianceCollectiveIntelligence)
        assert inst1 is inst2


class TestHelperFunctions:
    """Unit tests for pure helper functions."""

    def test_connectivity_density_full(self) -> None:
        # 4 nodes, 6 edges = complete graph
        assert _connectivity_density(4, 6) == 1.0

    def test_connectivity_density_zero(self) -> None:
        assert _connectivity_density(4, 0) == 0.0

    def test_connectivity_density_half(self) -> None:
        # 4 nodes, 3 edges
        assert _connectivity_density(4, 3) == 0.5

    def test_information_flow_rate_positive(self) -> None:
        rate = _information_flow_rate(80.0, 0.5)
        assert rate > 0

    def test_collective_iq_formula(self) -> None:
        iq = _collective_iq(80.0, 0.5, 7.0)
        assert iq == round(80.0 * 0.5 * 7.0, 2)

    def test_iq_level_superintelligence(self) -> None:
        assert _iq_level(250) == "superintelligence"

    def test_iq_level_genius(self) -> None:
        assert _iq_level(160) == "genius"

    def test_iq_level_gifted(self) -> None:
        assert _iq_level(130) == "gifted"

    def test_iq_level_bright(self) -> None:
        assert _iq_level(110) == "bright"

    def test_iq_level_average(self) -> None:
        assert _iq_level(90) == "average"

    def test_iq_level_below_average(self) -> None:
        assert _iq_level(50) == "below_average"

    def test_load_repos_returns_33(self) -> None:
        repos = _load_repos()
        assert len(repos) == 33

    def test_repo_capability_in_range(self) -> None:
        repos = _load_repos()
        for name, meta in repos.items():
            cap = _repo_capability(meta)
            assert 50.0 <= cap <= 120.0, f"Repo {name} capability {cap} out of range"
