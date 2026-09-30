"""
Tests for OMNI-HUB v180 — CollaborativeSurge (协作浪涌)

Coverage:
  - launch_big_discussion
  - launch_big_collaboration
  - launch_wild_question
  - build_surge_momentum
  - detect_surge_emergence
  - activate_all_via_surge
  - get_status
  - singleton behaviour
"""

import pytest
import time
from typing import Dict, List

from core.collaborative_surge import (
    CollaborativeSurge,
    get_collaborative_surge,
    reset_collaborative_surge,
    CORE_LINES,
    SurgeLevel,
    EmergenceLevel,
    CollaborationMode,
    Scope,
    ProblemType,
    DirectField,
    PatternCircles,
    CirculationEngine,
    CoreMachine,
)


@pytest.fixture(autouse=True)
def fresh_surge():
    """Provide a clean CollaborativeSurge for every test."""
    yield reset_collaborative_surge()


# ═══════════════════════════════════════════════════════════════════════════════
# launch_big_discussion
# ═══════════════════════════════════════════════════════════════════════════════
class TestLaunchBigDiscussion:
    def test_returns_dict_with_required_keys(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_big_discussion(
            topic="What is the nature of consciousness?",
            scope="universal",
        )
        assert isinstance(result, dict)
        assert "discussion_id" in result
        assert "topic" in result
        assert "scope" in result
        assert "lines_engaged" in result
        assert "intensity" in result
        assert "propagation" in result
        assert "resonance" in result
        assert "circulation" in result
        assert result["status"] == "launched"

    def test_topic_preserved(self, fresh_surge: CollaborativeSurge):
        topic = "Exploring the quantum nature of thought"
        result = fresh_surge.launch_big_discussion(topic=topic, scope="alliance")
        assert result["topic"] == topic

    def test_scope_affects_lines_engaged(self, fresh_surge: CollaborativeSurge):
        # universal should engage all 12 lines
        uni = fresh_surge.launch_big_discussion(topic="Universal Q", scope="universal")
        assert len(uni["lines_engaged"]) == len(CORE_LINES)

        # single_line should engage exactly 1 line
        single = fresh_surge.launch_big_discussion(topic="Single Q", scope="single_line")
        assert len(single["lines_engaged"]) == 1

    def test_intensity_in_valid_range(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_big_discussion(topic="Test", scope="layer")
        assert 0.0 <= result["intensity"] <= 1.0

    def test_propagation_reaches_field(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_big_discussion(topic="Test", scope="universal")
        assert result["propagation"]["propagated"] is True
        assert result["propagation"]["reach"] > 0

    def test_discussion_tracked_in_status(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_big_discussion(topic="Test", scope="universal")
        status = fresh_surge.get_status()
        assert status["active_discussions_count"] >= 1
        ids = [d["id"] for d in status["active_discussions"]]
        assert result["discussion_id"] in ids


# ═══════════════════════════════════════════════════════════════════════════════
# launch_big_collaboration
# ═══════════════════════════════════════════════════════════════════════════════
class TestLaunchBigCollaboration:
    def test_returns_dict_with_required_keys(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_big_collaboration(
            problem={"type": "integration", "description": "Merge two architectures"},
            participants=["ucif2", "lgt", "omni"],
        )
        assert isinstance(result, dict)
        assert "collaboration_id" in result
        assert "problem_type" in result
        assert "participants" in result
        assert "mode" in result
        assert "intensity" in result
        assert "propagation" in result
        assert "resonance" in result
        assert "circulation" in result
        assert result["status"] == "launched"

    def test_problem_type_preserved(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_big_collaboration(
            problem={"type": "research"},
            participants=["aiq", "qfa"],
        )
        assert result["problem_type"] == "research"

    def test_invalid_participants_filtered(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_big_collaboration(
            problem={"type": "architecture"},
            participants=["ucif2", "not_a_line", "omni"],
        )
        assert "not_a_line" not in result["participants"]
        assert "ucif2" in result["participants"]
        assert "omni" in result["participants"]

    def test_empty_participants_falls_back(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_big_collaboration(
            problem={"type": "evolution"},
            participants=[],
        )
        assert len(result["participants"]) >= 1
        for p in result["participants"]:
            assert p in CORE_LINES

    def test_mode_defaults_by_problem_type(self, fresh_surge: CollaborativeSurge):
        type_mode_map = {
            "architecture": "directed",
            "evolution": "spontaneous",
            "research": "asynchronous",
            "integration": "synchronous",
            "emergence": "consensus",
        }
        for ptype, expected_mode in type_mode_map.items():
            result = fresh_surge.launch_big_collaboration(
                problem={"type": ptype},
                participants=["ucif2", "omni"],
            )
            assert result["mode"] == expected_mode

    def test_explicit_mode_override(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_big_collaboration(
            problem={"type": "architecture"},
            participants=["ucif2"],
            mode="consensus",
        )
        assert result["mode"] == "consensus"

    def test_collaboration_tracked_in_status(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_big_collaboration(
            problem={"type": "integration"},
            participants=["usrm", "cfts", "aiq"],
        )
        status = fresh_surge.get_status()
        assert status["active_collaborations_count"] >= 1
        ids = [c["id"] for c in status["active_collaborations"]]
        assert result["collaboration_id"] in ids


# ═══════════════════════════════════════════════════════════════════════════════
# launch_wild_question
# ═══════════════════════════════════════════════════════════════════════════════
class TestLaunchWildQuestion:
    def test_returns_dict_with_required_keys(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_wild_question(
            question="What if gravity is consciousness?",
            target_line="qgl",
        )
        assert isinstance(result, dict)
        assert "wild_question_id" in result
        assert "question" in result
        assert "target_line" in result
        assert "intensity" in result
        assert "resonance_lines" in result
        assert "propagation" in result
        assert "resonance" in result
        assert "circulation" in result
        assert result["status"] == "unleashed"

    def test_question_preserved(self, fresh_surge: CollaborativeSurge):
        q = "What if logic is a form of light?"
        result = fresh_surge.launch_wild_question(question=q)
        assert result["question"] == q

    def test_invalid_target_line_becomes_none(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_wild_question(
            question="Test?",
            target_line="not_a_line",
        )
        assert result["target_line"] is None

    def test_resonance_lines_are_all_core_lines(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_wild_question(question="Universal wild?")
        assert set(result["resonance_lines"]) == set(CORE_LINES)

    def test_intensity_higher_than_normal(self, fresh_surge: CollaborativeSurge):
        # Wild questions should have base intensity >= 0.5 (universal) or >= 0.65 (targeted)
        result_universal = fresh_surge.launch_wild_question(question="Wild?")
        result_targeted = fresh_surge.launch_wild_question(
            question="Wild?", target_line="qgl"
        )
        assert result_universal["intensity"] >= 0.5
        assert result_targeted["intensity"] >= 0.5

    def test_wild_question_tracked_in_status(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.launch_wild_question(question="Tracked?")
        status = fresh_surge.get_status()
        assert status["active_wild_questions_count"] >= 1
        ids = [wq["id"] for wq in status["active_wild_questions"]]
        assert result["wild_question_id"] in ids

    def test_question_pool_updated(self, fresh_surge: CollaborativeSurge):
        before = len(fresh_surge.question_pool)
        fresh_surge.launch_wild_question(question="Pool test?")
        after = len(fresh_surge.question_pool)
        assert after == before + 1


# ═══════════════════════════════════════════════════════════════════════════════
# build_surge_momentum
# ═══════════════════════════════════════════════════════════════════════════════
class TestBuildSurgeMomentum:
    def test_returns_dict_with_required_keys(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.build_surge_momentum()
        assert isinstance(result, dict)
        assert "raw_momentum" in result
        assert "normalized_momentum" in result
        assert "surge_level" in result
        assert "breakdown" in result
        assert "field_bonus" in result
        assert "circle_bonus" in result
        assert "flow_bonus" in result

    def test_empty_momentum_is_calm(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.build_surge_momentum()
        assert result["surge_level"] == SurgeLevel.CALM.value
        assert result["normalized_momentum"] == pytest.approx(0.0, abs=0.01)

    def test_momentum_increases_with_activity(self, fresh_surge: CollaborativeSurge):
        fresh_surge.launch_big_discussion(topic="D1", scope="universal")
        fresh_surge.launch_big_collaboration(
            problem={"type": "integration"},
            participants=CORE_LINES[:6],
        )
        fresh_surge.launch_wild_question(question="W1?")
        result = fresh_surge.build_surge_momentum()
        assert result["normalized_momentum"] > 0.0
        assert result["raw_momentum"] > 0.0

    def test_breakdown_contains_all_active_items(self, fresh_surge: CollaborativeSurge):
        fresh_surge.launch_big_discussion(topic="D1", scope="layer")
        fresh_surge.launch_big_collaboration(
            problem={"type": "research"},
            participants=["aiq", "qfa"],
        )
        fresh_surge.launch_wild_question(question="W1?")
        result = fresh_surge.build_surge_momentum()
        types = [b["type"] for b in result["breakdown"]]
        assert "discussion" in types
        assert "collaboration" in types
        assert "wild_question" in types

    def test_normalized_momentum_within_zero_one(self, fresh_surge: CollaborativeSurge):
        # Launch many activities to try to push momentum high
        for i in range(10):
            fresh_surge.launch_big_discussion(topic=f"D{i}", scope="universal")
            fresh_surge.launch_big_collaboration(
                problem={"type": "integration"},
                participants=CORE_LINES,
            )
            fresh_surge.launch_wild_question(question=f"W{i}?")
        result = fresh_surge.build_surge_momentum()
        assert 0.0 <= result["normalized_momentum"] <= 1.0

    def test_surge_level_classifications(self, fresh_surge: CollaborativeSurge):
        # By launching enough activities we should at least exceed calm
        for i in range(5):
            fresh_surge.launch_big_discussion(topic=f"D{i}", scope="universal")
            fresh_surge.launch_big_collaboration(
                problem={"type": "emergence"},
                participants=CORE_LINES,
            )
            fresh_surge.launch_wild_question(question=f"W{i}?")
        result = fresh_surge.build_surge_momentum()
        level = result["surge_level"]
        assert level in [lvl.value for lvl in SurgeLevel]
        # With this much activity we expect at least ripple
        assert result["normalized_momentum"] > 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# detect_surge_emergence
# ═══════════════════════════════════════════════════════════════════════════════
class TestDetectSurgeEmergence:
    def test_returns_dict_with_required_keys(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.detect_surge_emergence()
        assert isinstance(result, dict)
        assert "emergence_score" in result
        assert "emergence_level" in result
        assert "emergences" in result
        assert "coverage" in result
        assert "momentum" in result

    def test_no_activity_low_score(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.detect_surge_emergence()
        assert result["emergence_score"] < 0.4  # should be low / noise
        assert result["emergence_level"] == EmergenceLevel.NOISE.value

    def test_high_activity_produces_emergence(self, fresh_surge: CollaborativeSurge):
        # Engage all lines through multiple channels
        for line in CORE_LINES:
            fresh_surge.launch_big_discussion(topic=f"Q about {line}", scope="single_line")
        fresh_surge.launch_big_collaboration(
            problem={"type": "emergence"},
            participants=CORE_LINES,
            mode="consensus",
        )
        fresh_surge.launch_wild_question(question="What if everything is one?")
        result = fresh_surge.detect_surge_emergence()
        assert result["emergence_score"] > 0.0
        assert len(result["emergences"]) >= 1

    def test_emergence_types_valid(self, fresh_surge: CollaborativeSurge):
        # Generate enough activity to force detectable emergence
        for i in range(5):
            fresh_surge.launch_big_discussion(topic=f"D{i}", scope="universal")
            fresh_surge.launch_big_collaboration(
                problem={"type": "emergence"},
                participants=CORE_LINES,
            )
            fresh_surge.launch_wild_question(question=f"Wild {i}?")
        result = fresh_surge.detect_surge_emergence()
        for em in result["emergences"]:
            assert em["type"] in [
                "breakthrough_insight",
                "novel_pattern",
                "unexpected_connection",
                "paradigm_shift",
            ]
            assert em["level"] in [lvl.value for lvl in EmergenceLevel]

    def test_coverage_tracked(self, fresh_surge: CollaborativeSurge):
        fresh_surge.launch_big_discussion(topic="All lines", scope="universal")
        result = fresh_surge.detect_surge_emergence()
        assert result["coverage"] == 1.0

    def test_emergence_recorded_in_status(self, fresh_surge: CollaborativeSurge):
        for i in range(4):
            fresh_surge.launch_big_discussion(topic=f"D{i}", scope="universal")
            fresh_surge.launch_wild_question(question=f"W{i}?")
        fresh_surge.detect_surge_emergence()
        status = fresh_surge.get_status()
        assert status["emergence_count"] >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# activate_all_via_surge
# ═══════════════════════════════════════════════════════════════════════════════
class TestActivateAllViaSurge:
    def test_returns_dict_with_required_keys(self, fresh_surge: CollaborativeSurge):
        result = fresh_surge.activate_all_via_surge()
        assert isinstance(result, dict)
        assert "activated" in result
        assert "momentum" in result
        assert "surge_level" in result
        assert "triggers" in result
        assert "architectures_activated" in result
        assert "timestamp" in result

    def test_activates_all_architectures(self, fresh_surge: CollaborativeSurge):
        # Seed some momentum first
        fresh_surge.launch_big_discussion(topic="Activation", scope="universal")
        fresh_surge.launch_wild_question(question="Activate?")
        result = fresh_surge.activate_all_via_surge()
        assert result["activated"] is True
        assert set(result["architectures_activated"]) == set(CORE_LINES)

    def test_triggers_all_four_systems(self, fresh_surge: CollaborativeSurge):
        fresh_surge.launch_big_collaboration(
            problem={"type": "integration"},
            participants=CORE_LINES[:4],
        )
        result = fresh_surge.activate_all_via_surge()
        triggers = result["triggers"]
        assert triggers["core_machine"]["activated"] is True
        assert triggers["direct_field_boost"]["boosted"] is True
        assert triggers["pattern_circles_accelerate"]["accelerated"] is True
        assert triggers["circulation_engine_amplify"]["amplified"] is True

    def test_momentum_recorded(self, fresh_surge: CollaborativeSurge):
        fresh_surge.launch_wild_question(question="Momentum?")
        result = fresh_surge.activate_all_via_surge()
        assert "momentum" in result
        assert 0.0 <= result["momentum"] <= 1.0

    def test_wild_questions_consumed(self, fresh_surge: CollaborativeSurge):
        fresh_surge.launch_wild_question(question="Consume me?")
        before = fresh_surge.get_status()["active_wild_questions_count"]
        assert before >= 1
        fresh_surge.activate_all_via_surge()
        after = fresh_surge.get_status()["active_wild_questions_count"]
        assert after == 0


# ═══════════════════════════════════════════════════════════════════════════════
# get_status
# ═══════════════════════════════════════════════════════════════════════════════
class TestGetStatus:
    def test_returns_dict_with_required_keys(self, fresh_surge: CollaborativeSurge):
        status = fresh_surge.get_status()
        assert isinstance(status, dict)
        assert "active_discussions" in status
        assert "active_discussions_count" in status
        assert "active_collaborations" in status
        assert "active_collaborations_count" in status
        assert "active_wild_questions" in status
        assert "active_wild_questions_count" in status
        assert "surge_level" in status
        assert "normalized_momentum" in status
        assert "raw_momentum" in status
        assert "emergences" in status
        assert "emergence_count" in status
        assert "surge_state" in status

    def test_counts_match_active_items(self, fresh_surge: CollaborativeSurge):
        fresh_surge.launch_big_discussion(topic="D1", scope="layer")
        fresh_surge.launch_big_collaboration(
            problem={"type": "research"},
            participants=["aiq"],
        )
        fresh_surge.launch_wild_question(question="W1?")
        status = fresh_surge.get_status()
        assert status["active_discussions_count"] == len(status["active_discussions"])
        assert status["active_collaborations_count"] == len(status["active_collaborations"])
        assert status["active_wild_questions_count"] == len(status["active_wild_questions"])

    def test_surge_level_one_of_defined_levels(self, fresh_surge: CollaborativeSurge):
        status = fresh_surge.get_status()
        assert status["surge_level"] in [lvl.value for lvl in SurgeLevel]

    def test_surge_state_contains_totals(self, fresh_surge: CollaborativeSurge):
        fresh_surge.launch_big_discussion(topic="D1", scope="universal")
        fresh_surge.launch_big_collaboration(
            problem={"type": "evolution"},
            participants=["ucif2"],
        )
        fresh_surge.launch_wild_question(question="W1?")
        status = fresh_surge.get_status()
        ss = status["surge_state"]
        assert ss["total_discussions"] >= 1
        assert ss["total_collaborations"] >= 1
        assert ss["total_wild_questions"] >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton behaviour
# ═══════════════════════════════════════════════════════════════════════════════
class TestSingleton:
    def test_get_collaborative_surge_returns_same_instance(self):
        a = get_collaborative_surge()
        b = get_collaborative_surge()
        assert a is b

    def test_reset_creates_new_instance(self):
        a = get_collaborative_surge()
        b = reset_collaborative_surge()
        assert a is not b

    def test_infrastructure_singletons_shared(self, fresh_surge: CollaborativeSurge):
        # DirectField should be the same instance across the module
        df1 = fresh_surge.direct_field
        df2 = DirectField()
        assert df1 is df2

        pc1 = fresh_surge.pattern_circles
        pc2 = PatternCircles()
        assert pc1 is pc2

        ce1 = fresh_surge.circulation_engine
        ce2 = CirculationEngine()
        assert ce1 is ce2

        cm1 = fresh_surge.core_machine
        cm2 = CoreMachine()
        assert cm1 is cm2


# ═══════════════════════════════════════════════════════════════════════════════
# Integration / philosophy
# ═══════════════════════════════════════════════════════════════════════════════
class TestIntegration:
    def test_full_surge_pipeline(self, fresh_surge: CollaborativeSurge):
        """End-to-end: discussion → collaboration → wild question → momentum → emergence → activation."""
        # 1. Launch discussions across multiple scopes
        fresh_surge.launch_big_discussion(topic="What is consciousness?", scope="universal")
        fresh_surge.launch_big_discussion(topic="Value of truth", scope="layer")

        # 2. Launch collaborations
        fresh_surge.launch_big_collaboration(
            problem={"type": "integration", "description": "Merge logic and light"},
            participants=["lgt", "qlv", "omni"],
            mode="synchronous",
        )
        fresh_surge.launch_big_collaboration(
            problem={"type": "emergence"},
            participants=CORE_LINES[:6],
            mode="consensus",
        )

        # 3. Launch wild questions
        fresh_surge.launch_wild_question(question="What if gravity is consciousness?", target_line="qgl")
        fresh_surge.launch_wild_question(question="What if time is a translation layer?")

        # 4. Build momentum
        momentum = fresh_surge.build_surge_momentum()
        assert momentum["normalized_momentum"] > 0.0

        # 5. Detect emergence
        emergence = fresh_surge.detect_surge_emergence()
        assert emergence["emergence_score"] > 0.0
        assert len(emergence["emergences"]) >= 1

        # 6. Activate all
        activation = fresh_surge.activate_all_via_surge()
        assert activation["activated"] is True
        assert len(activation["architectures_activated"]) == len(CORE_LINES)

        # 7. Status reflects everything
        status = fresh_surge.get_status()
        assert status["active_discussions_count"] >= 2
        assert status["active_collaborations_count"] >= 2
        assert status["emergence_count"] >= 1

    def test_seed_wild_questions_present(self, fresh_surge: CollaborativeSurge):
        """The 5 seeded wild questions should be in the pool from init."""
        assert len(fresh_surge.question_pool) >= 5
        questions = [q["question"] for q in fresh_surge.question_pool]
        assert "What if gravity is consciousness?" in questions

    def test_collaboration_log_grows(self, fresh_surge: CollaborativeSurge):
        before = len(fresh_surge.get_collaboration_log())
        fresh_surge.launch_big_discussion(topic="Log test", scope="single_line")
        fresh_surge.launch_big_collaboration(
            problem={"type": "research"},
            participants=["aiq"],
        )
        after = len(fresh_surge.get_collaboration_log())
        assert after == before + 2

    def test_close_methods_work(self, fresh_surge: CollaborativeSurge):
        d = fresh_surge.launch_big_discussion(topic="Close me", scope="universal")
        c = fresh_surge.launch_big_collaboration(
            problem={"type": "architecture"},
            participants=["omni"],
        )
        assert fresh_surge.close_discussion(d["discussion_id"]) is True
        assert fresh_surge.close_collaboration(c["collaboration_id"]) is True
        status = fresh_surge.get_status()
        assert status["active_discussions_count"] == 0
        assert status["active_collaborations_count"] == 0
        assert fresh_surge.close_discussion("nonexistent") is False
