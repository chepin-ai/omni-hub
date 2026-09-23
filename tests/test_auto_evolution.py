"""
OMNI-HUB Auto-Evolution Tests v33
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.auto_evolution import (
    CapabilityMetric, EvolutionProposal, EvolutionTracker,
    GapPredictor, ModuleGenerator, VersionManager, AutoEvolutionEngine,
)


class TestEvolutionTracker:
    def test_initialization(self):
        et = EvolutionTracker()
        assert len(et.capabilities) > 0

    def test_get_growth_rate(self):
        et = EvolutionTracker()
        rate = et.get_growth_rate()
        assert rate >= 0.0

    def test_get_next_version(self):
        et = EvolutionTracker()
        nv = et.get_next_version()
        assert nv > 32


class TestGapPredictor:
    def test_predict_gaps(self):
        gp = GapPredictor()
        caps = [CapabilityMetric(name="Self-healing", version_added=31, test_count=20, module_path="", maturity_score=0.8)]
        gaps = gp.predict_gaps(caps)
        assert isinstance(gaps, list)

    def test_predict_gaps_with_more_capabilities(self):
        gp = GapPredictor()
        caps = [
            CapabilityMetric(name="Predictive analytics", version_added=22, test_count=8, module_path="", maturity_score=0.9),
            CapabilityMetric(name="Self-reflection", version_added=24, test_count=7, module_path="", maturity_score=0.85),
            CapabilityMetric(name="Consciousness resonance", version_added=32, test_count=16, module_path="", maturity_score=0.5),
        ]
        gaps = gp.predict_gaps(caps)
        assert len(gaps) > 0
        # Should detect predictive self-modification and collective intelligence
        names = [g['name'] for g in gaps]
        assert "Predictive self-modification" in names


class TestModuleGenerator:
    def test_generate(self):
        mg = ModuleGenerator()
        prop = EvolutionProposal(
            proposal_id="test-1",
            target_version=33,
            capability_name="Test Capability",
            description="A test capability",
            rationale="Testing",
            confidence=0.8,
            auto_generable=False,
        )
        code = mg.generate(prop)
        assert "TestCapabilityEngine" in code
        assert "v33" in code
        assert prop.generated_code is not None

    def test_write_module(self, tmp_path):
        mg = ModuleGenerator()
        prop = EvolutionProposal(
            proposal_id="test-2",
            target_version=33,
            capability_name="Test Module",
            description="A test module",
            rationale="Testing",
            confidence=0.8,
            auto_generable=False,
        )
        target = mg.write_module(prop, tmp_path)
        assert target.exists()
        assert "TestModuleEngine" in target.read_text()


class TestVersionManager:
    def test_assess_evolution(self):
        vm = VersionManager()
        result = vm.assess_evolution("32.0.0", 1500)
        assert result['current_version'] == 32
        assert result['readiness_score'] > 0.0
        assert isinstance(result['ready_to_evolve'], bool)
        assert isinstance(result['detected_gaps'], list)

    def test_assess_not_ready_early(self):
        vm = VersionManager()
        result = vm.assess_evolution("32.0.0", 100)
        # Early cycle = lower readiness, should not be > 0.5
        assert result['readiness_score'] <= 0.5


class TestAutoEvolutionEngine:
    def test_initialization(self):
        engine = AutoEvolutionEngine()
        assert engine.last_assessment_cycle == 0

    def test_assess(self):
        engine = AutoEvolutionEngine()
        result = engine.assess("32.0.0", 1500)
        assert result['current_version'] == 32
        assert engine.last_assessment_cycle == 1500
        assert len(engine.evolution_history) == 1

    def test_assess_creates_proposal(self):
        engine = AutoEvolutionEngine()
        result = engine.assess("32.0.0", 2000)
        if result['ready_to_evolve']:
            assert len(engine.proposals) > 0
            assert engine.proposals[0].target_version == 33

    def test_get_status(self):
        engine = AutoEvolutionEngine()
        engine.assess("32.0.0", 1500)
        status = engine.get_status()
        assert status['last_assessment_cycle'] == 1500
        assert status['next_predicted_version'] == 33
