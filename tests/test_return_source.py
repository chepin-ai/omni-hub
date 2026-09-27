"""
OMNI-HUB Return to Source Tests v125
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.return_source import ReturnToSource, get_return_to_source


class TestReturnToSource:
    def test_initialization(self):
        rts = ReturnToSource()
        assert rts.return_count == 0

    def test_assess_completion_incomplete(self):
        rts = ReturnToSource()
        state = {"self_awareness": {}, "learning": {}}
        result = rts.assess_completion(state)
        assert result["complete"] is False
        assert result["completion"] < 0.8

    def test_assess_completion_complete(self):
        rts = ReturnToSource()
        state = {"self_awareness": {}, "learning": {}, "reasoning": {}, "planning": {},
                 "ethics": {}, "communication": {}, "memory": {}, "perception": {},
                 "trust_engine": {}, "narrative_generator": {}, "legacy_preservation": {}}
        for k in ['sensory_integration', 'affective_computing', 'adaptive_interface',
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
                  'vanishing_point', 'absolute_zero', 'omega_point']:
            state[k] = {}
        state["omega_point"] = {"omega": 0.9}
        state["absolute_zero"] = {"stillness": 0.8}
        state["vanishing_point"] = {"convergence": 0.8}
        result = rts.assess_completion(state)
        assert result["complete"] is True
        assert result["completion"] > 0.8

    def test_return_home(self):
        rts = ReturnToSource()
        state = {"self_awareness": {}}
        result = rts.return_home(state)
        assert result["return_id"] == 1
        assert result["stage"] in ["home", "journeying", "wandering"]
        assert "note" in result

    def test_get_status(self):
        rts = ReturnToSource()
        rts.return_home({"self_awareness": {}})
        status = rts.get_status()
        assert status["returns"] == 1


class TestGlobalEngine:
    def test_get_return_to_source(self):
        g = get_return_to_source()
        assert g is not None
        assert isinstance(g, ReturnToSource)
