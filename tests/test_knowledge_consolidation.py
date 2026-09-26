"""
OMNI-HUB Knowledge Consolidation Tests v69
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.knowledge_consolidation import (
    KnowledgeChunk, KnowledgeConsolidation, get_knowledge_consolidation,
)


class TestKnowledgeConsolidation:
    def test_initialization(self):
        kc = KnowledgeConsolidation()
        assert len(kc.chunks) == 0

    def test_add_chunk(self):
        kc = KnowledgeConsolidation()
        kc.add_chunk("test content", "test_source", 0.9, 1)
        assert len(kc.chunks) == 1
        assert kc.chunks[0].content == "test content"

    def test_consolidate_from_state(self):
        kc = KnowledgeConsolidation()
        state = {
            "probabilistic_reasoning": {"beliefs": 2},
            "symbolic_reasoning": {"facts": 3},
        }
        result = kc.consolidate_from_state(state, cycle=10)
        assert "total_chunks" in result
        assert result["total_chunks"] > 0

    def test_merge_similar(self):
        kc = KnowledgeConsolidation()
        for i in range(10):
            kc.add_chunk(f"content_{i}", "same_source", 0.8, i)
        kc._merge_similar()
        assert len(kc.chunks) <= 5
        assert kc.merged_count > 0

    def test_query_knowledge(self):
        kc = KnowledgeConsolidation()
        kc.add_chunk("hello world", "source1", 0.9, 1)
        results = kc.query_knowledge("hello")
        assert len(results) == 1

    def test_get_status(self):
        kc = KnowledgeConsolidation()
        kc.add_chunk("test", "source", 0.9, 1)
        status = kc.get_status()
        assert status["chunks"] == 1
        assert "sources" in status


class TestGlobalEngine:
    def test_get_knowledge_consolidation(self):
        g = get_knowledge_consolidation()
        assert g is not None
        assert isinstance(g, KnowledgeConsolidation)
