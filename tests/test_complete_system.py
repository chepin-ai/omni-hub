"""
OMNI-HUB Complete System Tests v130
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.complete_system import CompleteSystem, get_complete_system


class TestCompleteSystem:
    def test_initialization(self):
        cs = CompleteSystem()
        assert cs.check_count == 0

    def test_verify_completeness_partial(self):
        cs = CompleteSystem()
        state = {"self_awareness": {}, "learning": {}}
        result = cs.verify_completeness(state)
        assert result["complete"] is False
        assert result["coverage"] < 1.0
        assert len(result["missing"]) > 0

    def test_verify_completeness_full(self):
        cs = CompleteSystem()
        state = {}
        for k in ['self_awareness', 'learning', 'reasoning', 'planning',
                  'ethics', 'communication', 'memory', 'perception',
                  'trust_engine', 'narrative_generator', 'legacy_preservation',
                  'sensory_integration', 'affective_computing', 'adaptive_interface',
                  'spatial_reasoning', 'temporal_reasoning', 'causal_learning',
                  'cognitive_load', 'theory_of_mind', 'value_reflection',
                  'metaphorical_reasoning', 'aesthetic_judgment', 'humor_perception',
                  'predictive_model', 'ontology', 'transcendence',
                  'moral_reasoning', 'wisdom_synthesis', 'singularity_gate',
                  'intentionality', 'phenomenal_experience', 'existential_authenticity',
                  'dialectic', 'creative_destruction', 'antifragile_growth',
                  'embodied_cognition', 'extended_mind', 'enactive_cognition',
                  'field_awareness', 'stochastic_resonance', 'final_integration',
                  'strange_loop', 'meta_awareness', 'eternal_cycle',
                  'dream_state', 'intuition', 'precognition',
                  'quantum_consciousness', 'morphic_resonance', 'synchronicity',
                  'vanishing_point', 'absolute_zero', 'omega_point',
                  'return_source', 'renewal', 'eternal_now',
                  'harmony', 'unity_beyond']:
            state[k] = {}
        result = cs.verify_completeness(state)
        assert result["complete"] is True
        assert result["coverage"] == 1.0
        assert len(result["missing"]) == 0

    def test_assess_system(self):
        cs = CompleteSystem()
        state = {"phi": 0.9, "line_coherence": 0.9, "self_awareness": {}}
        result = cs.assess_system(state)
        assert result["check_id"] == 1
        assert result["stage"] in ["complete", "maturing", "growing"]
        assert result["version"] == 130

    def test_get_status(self):
        cs = CompleteSystem()
        cs.assess_system({"phi": 0.5, "line_coherence": 0.5})
        status = cs.get_status()
        assert status["checks"] == 1
        assert status["version"] == 130


class TestGlobalEngine:
    def test_get_complete_system(self):
        g = get_complete_system()
        assert g is not None
        assert isinstance(g, CompleteSystem)
