"""
OMNI-HUB Information Theory Tests v63
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.information_theory import (
    InformationTheoryCore, get_information_theory,
)


class TestInformationTheoryCore:
    def test_initialization(self):
        itc = InformationTheoryCore()
        assert itc.measurement_count == 0

    def test_entropy_uniform(self):
        itc = InformationTheoryCore()
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        h = itc.entropy(values, bins=5)
        assert h > 0

    def test_entropy_constant(self):
        itc = InformationTheoryCore()
        values = [5.0] * 10
        h = itc.entropy(values, bins=5)
        assert h == 0.0

    def test_mutual_information(self):
        itc = InformationTheoryCore()
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]  # y = 2x, perfect correlation
        mi = itc.mutual_information(x, y)
        assert mi >= 0

    def test_system_entropy(self):
        itc = InformationTheoryCore()
        state = {"level": 5, "energy": 1000.0, "phi": 0.6, "line_coherence": 0.5}
        result = itc.system_entropy(state)
        assert "state_entropy" in result

    def test_complexity_score(self):
        itc = InformationTheoryCore()
        state = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
        score = itc.complexity_score(state)
        assert 0 <= score <= 1

    def test_analyze(self):
        itc = InformationTheoryCore()
        state = {"level": 5, "energy": 1000.0, "phi": 0.6}
        result = itc.analyze(state)
        assert "entropy" in result
        assert "complexity" in result

    def test_get_status(self):
        itc = InformationTheoryCore()
        status = itc.get_status()
        assert "measurements" in status


class TestGlobalEngine:
    def test_get_information_theory(self):
        g = get_information_theory()
        assert g is not None
        assert isinstance(g, InformationTheoryCore)
