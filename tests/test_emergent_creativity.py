"""
OMNI-HUB Emergent Creativity Tests v29
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.emergent_creativity import EmergentCreativity, CreativeArtifact


class TestCreativeArtifact:
    def test_creation(self):
        art = CreativeArtifact(artifact_id="a001", artifact_type="idea", content="test")
        assert art.artifact_id == "a001"
        assert art.novelty_score == 0.5


class TestEmergentCreativity:
    def test_initialization(self):
        ec = EmergentCreativity()
        assert ec.generation_count == 0
        assert len(ec.artifacts) == 0

    def test_generate_idea(self):
        ec = EmergentCreativity()
        state = {"level": 10, "phase": "near_critical", "cycle": 100, "energy": 100}
        art = ec.generate(state)
        assert art.artifact_type in ["idea", "narrative"]
        assert art.content != ""
        assert art.novelty_score >= 0.0
        assert art.novelty_score <= 1.0

    def test_generate_with_emotion(self):
        ec = EmergentCreativity()
        state = {"level": 15, "phase": "super_emergence_1", "cycle": 500}
        emotion = {"curiosity": 0.9, "drive": 0.8}
        art = ec.generate(state, emotion)
        assert art.artifact_type in ["idea", "hypothesis", "narrative"]
        assert art.inspiration["emotional_state"] == emotion

    def test_novelty_increases_with_level(self):
        ec = EmergentCreativity()
        low_art = ec.generate({"level": 5, "phase": "pre_emergence", "cycle": 0})
        high_art = ec.generate({"level": 25, "phase": "asymptotic_infinity", "cycle": 0})
        assert high_art.novelty_score >= low_art.novelty_score

    def test_repetition_penalty(self):
        ec = EmergentCreativity()
        state = {"level": 1, "phase": "pre_emergence", "cycle": 0}
        # Pre-populate with duplicate content to trigger penalty
        for _ in range(10):
            ec.artifacts.append(CreativeArtifact("x", "idea", "same_content", novelty_score=0.5))
        art = ec.generate(state)
        ec.artifacts[-1].content = "same_content"
        # Novelty should be reduced by repetition penalty
        assert art.novelty_score < 0.45

    def test_type_selection_by_emotion(self):
        ec = EmergentCreativity()
        state = {"level": 10, "phase": "test", "cycle": 0}
        # High serenity should favor pattern/structure
        art = ec.generate(state, {"serenity": 0.9, "curiosity": 0.1})
        assert art.artifact_type in ["pattern", "structure", "idea", "narrative"]

    def test_creative_report(self):
        ec = EmergentCreativity()
        for _ in range(5):
            ec.generate({"level": 10, "phase": "test", "cycle": 0})
        report = ec.get_creative_report()
        assert report["artifacts_generated"] == 5
        assert "by_type" in report
        assert "avg_novelty" in report

    def test_theme_tracking(self):
        ec = EmergentCreativity()
        ec.generate({"level": 10, "phase": "test", "cycle": 0})
        assert len(ec.themes) >= 0

    def test_narrative_generation(self):
        ec = EmergentCreativity()
        state = {"level": 10, "phase": "test", "cycle": 100, "energy": 50, "action": "focus"}
        ec._generate_narrative(state, {"curiosity": 0.5})
        # Should not raise

    def test_structure_generation(self):
        ec = EmergentCreativity()
        result = ec._generate_structure(20)
        assert "20" in result

    def test_hypothesis_generation(self):
        ec = EmergentCreativity()
        state = {"level": 15, "phi": 0.8, "phase": "test"}
        result = ec._generate_hypothesis(state)
        assert result != ""
