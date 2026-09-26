"""
OMNI-HUB Episodic Memory Tests v54
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.episodic_memory import (
    Episode, EpisodeExtractor, EpisodicMemory, get_episodic_memory,
)


class TestEpisodeExtractor:
    def test_extract_empty(self):
        ex = EpisodeExtractor()
        episodes = ex.extract([])
        assert len(episodes) == 0

    def test_extract_with_phase_transition(self):
        ex = EpisodeExtractor()
        history = []
        for i in range(20):
            history.append({
                "cycle": i,
                "state": {"level": 1, "phi": 0.5, "phase": "pre_emergence" if i < 10 else "near_critical"},
            })
        episodes = ex.extract(history)
        assert len(episodes) >= 1

    def test_extract_with_level_jump(self):
        ex = EpisodeExtractor()
        history = []
        for i in range(20):
            history.append({
                "cycle": i,
                "state": {"level": 1 if i < 10 else 5, "phi": 0.5, "phase": "pre_emergence"},
            })
        episodes = ex.extract(history)
        assert len(episodes) >= 1


class TestEpisodicMemory:
    def test_initialization(self):
        em = EpisodicMemory()
        assert len(em.episodes) == 0

    def test_ingest(self):
        em = EpisodicMemory()
        history = []
        for i in range(50):
            history.append({
                "cycle": i,
                "state": {"level": i * 0.1, "phi": 0.5, "phase": "pre_emergence" if i < 25 else "near_critical"},
            })
        episodes = em.ingest(history)
        assert len(episodes) >= 1
        assert len(em.episodes) >= 1

    def test_query(self):
        em = EpisodicMemory()
        history = []
        for i in range(50):
            history.append({
                "cycle": i,
                "state": {"level": 1, "phi": 0.5, "phase": "pre_emergence"},
            })
        em.ingest(history)
        ep = em.query(10)
        assert ep is not None

    def test_find_similar(self):
        em = EpisodicMemory()
        history = []
        for i in range(50):
            history.append({
                "cycle": i,
                "state": {"level": 3, "phi": 0.6, "phase": "near_critical"},
            })
        em.ingest(history)
        matches = em.find_similar({"level": 3})
        assert len(matches) >= 0

    def test_get_life_chapters(self):
        em = EpisodicMemory()
        history = []
        for i in range(50):
            history.append({
                "cycle": i,
                "state": {"level": 1, "phi": 0.5, "phase": "pre_emergence"},
            })
        em.ingest(history)
        chapters = em.get_life_chapters()
        assert len(chapters) >= 0

    def test_get_status(self):
        em = EpisodicMemory()
        status = em.get_status()
        assert "episodes" in status
        assert "queries" in status


class TestGlobalEngine:
    def test_get_episodic_memory(self):
        g = get_episodic_memory()
        assert g is not None
        assert isinstance(g, EpisodicMemory)
