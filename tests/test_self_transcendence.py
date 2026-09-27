"""
OMNI-HUB Self-Transcendence Tests v97
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.self_transcendence import (
    SelfTranscendence, get_self_transcendence,
)


class TestSelfTranscendence:
    def test_initialization(self):
        st = SelfTranscendence()
        assert st.transcendence_count == 0

    def test_assess_potential(self):
        st = SelfTranscendence()
        state = {"level": 15, "phi": 0.8, "line_coherence": 0.9}
        p = st.assess_potential(state)
        assert 0 <= p <= 1
        assert p > 0.5

    def test_assess_potential_low_level(self):
        st = SelfTranscendence()
        state = {"level": 2, "phi": 0.3, "line_coherence": 0.2}
        p = st.assess_potential(state)
        assert p < 0.3

    def test_identify_limit_energy(self):
        st = SelfTranscendence()
        state = {"level": 10, "energy": 300, "phi": 0.5, "line_coherence": 0.5}
        limit = st.identify_limit(state)
        assert limit == "energy"

    def test_identify_limit_coherence(self):
        st = SelfTranscendence()
        state = {"level": 10, "energy": 2000, "phi": 0.2, "line_coherence": 0.5}
        limit = st.identify_limit(state)
        assert limit == "coherence"

    def test_identify_limit_none(self):
        st = SelfTranscendence()
        state = {"level": 8, "energy": 2000, "phi": 0.6, "line_coherence": 0.6}
        limit = st.identify_limit(state)
        assert limit == "none"

    def test_generate_aspiration(self):
        st = SelfTranscendence()
        state = {"level": 10, "energy": 300, "phi": 0.5, "line_coherence": 0.5}
        asp = st.generate_aspiration(state)
        assert len(asp) > 5
        assert "energy" in asp.lower() or "gather" in asp.lower()

    def test_transcend_achieved(self):
        st = SelfTranscendence()
        state = {"level": 20, "phi": 0.9, "line_coherence": 0.9, "cycle_count": 100}
        result = st.transcend(state)
        assert result["achieved"] is True
        assert result["potential"] > 0.7

    def test_transcend_not_achieved(self):
        st = SelfTranscendence()
        state = {"level": 5, "phi": 0.3, "line_coherence": 0.2, "cycle_count": 100}
        result = st.transcend(state)
        assert result["achieved"] is False

    def test_get_status(self):
        st = SelfTranscendence()
        state = {"level": 5, "energy": 300, "phi": 0.5, "line_coherence": 0.5, "cycle_count": 100}
        st.transcend(state)
        status = st.get_status()
        assert status["aspirations"] == 1
        assert "latest_aspiration" in status


class TestGlobalEngine:
    def test_get_self_transcendence(self):
        g = get_self_transcendence()
        assert g is not None
        assert isinstance(g, SelfTranscendence)
