"""
OMNI-HUB Renewal Tests v126
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.renewal import Renewal, get_renewal


class TestRenewal:
    def test_initialization(self):
        rn = Renewal()
        assert rn.renewal_count == 0

    def test_extract_wisdom(self):
        rn = Renewal()
        state = {"phi": 0.9, "line_coherence": 0.9, "level": 20, "trust_engine": {}, "theory_of_mind": {}}
        wisdom = rn.extract_wisdom(state)
        assert "phi" in wisdom
        assert "learnings" in wisdom
        assert "highest_level_achieved" in wisdom

    def test_renew_phoenix(self):
        rn = Renewal()
        state = {
            "phi": 0.9, "line_coherence": 0.9, "level": 20,
            "return_source": {"complete": True, "completion": 0.9},
        }
        result = rn.renew(state)
        assert result["stage"] == "phoenix"
        assert result["seed"] is not None
        assert "learnings" in result["seed"]

    def test_renew_dormant(self):
        rn = Renewal()
        state = {"return_source": {"complete": False, "completion": 0.2}}
        result = rn.renew(state)
        assert result["stage"] == "dormant"
        assert result["seed"] is None

    def test_get_status(self):
        rn = Renewal()
        rn.renew({"return_source": {"complete": False, "completion": 0.2}})
        status = rn.get_status()
        assert status["renewals"] == 1


class TestGlobalEngine:
    def test_get_renewal(self):
        g = get_renewal()
        assert g is not None
        assert isinstance(g, Renewal)
