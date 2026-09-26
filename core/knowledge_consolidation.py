"""
OMNI-HUB Knowledge Consolidation v69
Memory consolidation and knowledge merging.

Knowledge scattered is knowledge lost.
Knowledge unified is knowledge powerful.
This module consolidates fragmented memories
into unified, accessible knowledge structures.

Philosophy: 温故知新 — Review the old, know the new.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class KnowledgeChunk:
    """A fragment of knowledge."""
    content: str
    source: str
    confidence: float
    timestamp: int


class KnowledgeConsolidation:
    """
    Consolidates fragmented knowledge into unified structures.
    """

    def __init__(self):
        self.chunks: List[KnowledgeChunk] = []
        self.consolidated: Dict[str, Any] = {}
        self.merged_count = 0

    def add_chunk(self, content: str, source: str, confidence: float, timestamp: int):
        """Add a knowledge chunk."""
        self.chunks.append(KnowledgeChunk(content, source, confidence, timestamp))

    def consolidate_from_state(self, state: Dict[str, Any], cycle: int):
        """Extract and consolidate knowledge from state."""
        # Extract knowledge from various subsystems
        subsystems = {
            "beliefs": state.get('probabilistic_reasoning', {}),
            "facts": state.get('symbolic_reasoning', {}),
            "episodes": state.get('episodic_memory', {}),
            "identity": state.get('identity', {}),
            "values": state.get('value_alignment', {}),
            "intentions": state.get('intention', {}),
        }

        for source, data in subsystems.items():
            if data:
                self.add_chunk(
                    content=str(data),
                    source=source,
                    confidence=0.8,
                    timestamp=cycle,
                )

        # Consolidate: merge similar chunks
        self._merge_similar()

        # Build consolidated knowledge map
        self.consolidated = {
            "total_chunks": len(self.chunks),
            "sources": list(set(c.source for c in self.chunks)),
            "latest_timestamp": cycle,
            "confidence_avg": round(sum(c.confidence for c in self.chunks) / max(1, len(self.chunks)), 3),
        }

        return self.consolidated

    def _merge_similar(self):
        """Merge knowledge chunks from same source."""
        by_source: Dict[str, List[KnowledgeChunk]] = {}
        for chunk in self.chunks:
            by_source.setdefault(chunk.source, []).append(chunk)

        merged = []
        for source, chunks in by_source.items():
            if len(chunks) > 5:
                # Keep most recent and highest confidence
                chunks.sort(key=lambda c: (-c.timestamp, -c.confidence))
                merged.extend(chunks[:5])
                self.merged_count += len(chunks) - 5
            else:
                merged.extend(chunks)

        self.chunks = merged

    def query_knowledge(self, keyword: str) -> List[Dict[str, Any]]:
        """Query consolidated knowledge."""
        results = []
        for chunk in self.chunks:
            if keyword in chunk.content or keyword in chunk.source:
                results.append({
                    "content": chunk.content[:100],
                    "source": chunk.source,
                    "confidence": chunk.confidence,
                })
        return results

    def get_status(self) -> Dict[str, Any]:
        return {
            "chunks": len(self.chunks),
            "consolidated": self.consolidated,
            "merged": self.merged_count,
            "sources": list(set(c.source for c in self.chunks)),
        }


_kc_engine = None

def get_knowledge_consolidation():
    global _kc_engine
    if _kc_engine is None:
        _kc_engine = KnowledgeConsolidation()
    return _kc_engine
