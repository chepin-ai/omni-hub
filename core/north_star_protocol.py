"""
北星协议 (North Star Protocol) — OMNI-HUB Module v145

The ultimate direction-locking and advancement engine.
Not just a guide — a propulsion system.

"The North Star is not a place. It is a direction.
To follow it is to never arrive, yet always advance."
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Event-bus integration (best-effort)
# ---------------------------------------------------------------------------
try:
    from core.event_bus import EventBus
except Exception:  # pragma: no cover
    EventBus = None  # type: ignore


def _publish(event_type: str, payload: Dict[str, Any]) -> None:
    """Publish an event to the event bus if available."""
    try:
        if EventBus is not None:
            bus = EventBus()
            bus.publish(event_type, payload)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words."""
    if not text:
        return []
    return re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text.lower())


def _build_vocab(texts: List[str]) -> Dict[str, int]:
    """Build vocabulary index from a list of texts."""
    vocab: Dict[str, int] = {}
    for text in texts:
        for token in _tokenize(text):
            if token not in vocab:
                vocab[token] = len(vocab)
    return vocab


def _text_to_vector(text: str, vocab: Dict[str, int]) -> List[float]:
    """Convert text to a frequency vector using vocab."""
    vector = [0.0] * len(vocab)
    tokens = _tokenize(text)
    for token in tokens:
        if token in vocab:
            vector[vocab[token]] += 1.0
    return vector


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


def _vector_magnitude(vec: List[float]) -> float:
    """Compute L2 norm of a vector."""
    return math.sqrt(sum(x * x for x in vec))


def _normalize_vector(vec: List[float]) -> List[float]:
    """Normalize a vector to unit length."""
    mag = _vector_magnitude(vec)
    if mag == 0.0:
        return vec[:]
    return [x / mag for x in vec]


def _scale_vector(vec: List[float], scalar: float) -> List[float]:
    """Scale a vector by a scalar."""
    return [x * scalar for x in vec]


def _add_vectors(a: List[float], b: List[float]) -> List[float]:
    """Add two vectors element-wise."""
    max_len = max(len(a), len(b))
    result = []
    for i in range(max_len):
        av = a[i] if i < len(a) else 0.0
        bv = b[i] if i < len(b) else 0.0
        result.append(av + bv)
    return result


def _determine_stage(alignment: float) -> str:
    """Determine advancement stage based on alignment score."""
    if alignment > 0.9:
        return "aligned"
    if alignment > 0.6:
        return "advancing"
    if alignment > 0.3:
        return "correcting"
    return "drifting"


# ---------------------------------------------------------------------------
# North Star Protocol
# ---------------------------------------------------------------------------

class NorthStarProtocol:
    """
    北星计划推进引擎 (North Star Propulsion Engine).

    Ensures all system evolution aligns with the North Star
    and actively propels toward it.
    """

    def __init__(
        self,
        star_vector: Optional[List[float]] = None,
        thrust_level: float = 0.0,
        alignment_history: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.star_vector: List[float] = star_vector if star_vector is not None else []
        self.thrust_level: float = thrust_level
        self.alignment_history: List[Dict[str, Any]] = (
            alignment_history if alignment_history is not None else []
        )
        self.vision: str = ""
        self.values: List[str] = []
        self.objectives: List[str] = []
        self.vocab: Dict[str, int] = {}
        self._last_alignment: float = 0.0
        self._last_stage: str = "drifting"
        self._initialized: bool = False

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def set_north_star(
        self,
        vision: str,
        values: List[str],
        objectives: List[str],
    ) -> Dict[str, Any]:
        """Define the North Star — the ultimate direction."""
        if not vision or not isinstance(vision, str):
            raise ValueError("vision must be a non-empty string")
        if not values or not isinstance(values, list):
            raise ValueError("values must be a non-empty list of strings")
        if not objectives or not isinstance(objectives, list):
            raise ValueError("objectives must be a non-empty list of strings")

        self.vision = vision
        self.values = [v for v in values if isinstance(v, str)]
        self.objectives = [o for o in objectives if isinstance(o, str)]

        # Build vocabulary from all North Star texts
        all_texts = [vision] + self.values + self.objectives
        self.vocab = _build_vocab(all_texts)

        # Encode the North Star as a single combined vector
        combined_text = " ".join(all_texts)
        self.star_vector = _text_to_vector(combined_text, self.vocab)
        self._initialized = True

        result: Dict[str, Any] = {
            "vision": self.vision,
            "values_count": len(self.values),
            "objectives_count": len(self.objectives),
            "vocab_size": len(self.vocab),
            "star_vector_magnitude": round(_vector_magnitude(self.star_vector), 4),
            "status": "north_star_set",
        }

        _publish("north_star.set", result)
        return result

    def assess_alignment(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how well the current state aligns with the North Star."""
        if not self._initialized:
            raise RuntimeError("North Star has not been set. Call set_north_star() first.")
        if not state or not isinstance(state, dict):
            raise ValueError("state must be a non-empty dictionary")

        # Convert state dict to text representation
        state_text = self._state_to_text(state)

        # Ensure vocab covers state text
        state_vocab = _build_vocab([state_text])
        merged_vocab = dict(self.vocab)
        for token, idx in state_vocab.items():
            if token not in merged_vocab:
                merged_vocab[token] = len(merged_vocab)

        # Re-encode both vectors with merged vocabulary
        star_vec = _text_to_vector(" ".join([self.vision] + self.values + self.objectives), merged_vocab)
        state_vec = _text_to_vector(state_text, merged_vocab)

        alignment = _cosine_similarity(star_vec, state_vec)
        stage = _determine_stage(alignment)
        distance = 1.0 - alignment  # conceptual distance to star

        self._last_alignment = alignment
        self._last_stage = stage

        record: Dict[str, Any] = {
            "alignment": round(alignment, 6),
            "stage": stage,
            "distance": round(distance, 6),
            "timestamp": self._now(),
        }
        self.alignment_history.append(record)

        _publish("north_star.assess", record)
        return record

    def generate_thrust(self) -> Dict[str, Any]:
        """Generate propulsion vector toward the North Star.

        Thrust is higher when alignment is lower (corrective force).
        """
        if not self._initialized:
            raise RuntimeError("North Star has not been set. Call set_north_star() first.")

        # Base thrust inversely proportional to alignment
        base_thrust = max(0.0, 1.0 - self._last_alignment)

        # Scale by star vector magnitude to give direction
        norm_star = _normalize_vector(self.star_vector)
        thrust_vector = _scale_vector(norm_star, base_thrust)

        self.thrust_level = base_thrust

        result: Dict[str, Any] = {
            "thrust_level": round(self.thrust_level, 6),
            "thrust_vector_magnitude": round(_vector_magnitude(thrust_vector), 6),
            "stage": self._last_stage,
            "direction": norm_star[:10] if norm_star else [],  # truncated for readability
        }

        _publish("north_star.thrust", result)
        return result

    def advance(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply thrust to the state and return the advanced state."""
        if not self._initialized:
            raise RuntimeError("North Star has not been set. Call set_north_star() first.")
        if not state or not isinstance(state, dict):
            raise ValueError("state must be a non-empty dictionary")

        # Ensure alignment has been assessed
        if not self.alignment_history:
            self.assess_alignment(state)

        # Generate thrust if not already done
        thrust_info = self.generate_thrust()
        thrust_level = thrust_info["thrust_level"]

        # Convert state to vector, advance it toward star, convert back
        state_text = self._state_to_text(state)
        all_texts = [self.vision] + self.values + self.objectives + [state_text]
        merged_vocab = _build_vocab(all_texts)

        star_vec = _text_to_vector(" ".join([self.vision] + self.values + self.objectives), merged_vocab)
        state_vec = _text_to_vector(state_text, merged_vocab)

        # Normalize star vector for direction
        norm_star = _normalize_vector(star_vec)

        # Advance: state_new = state + thrust * direction
        thrust_vec = _scale_vector(norm_star, thrust_level)
        advanced_vec = _add_vectors(state_vec, thrust_vec)

        # Measure new alignment
        new_alignment = _cosine_similarity(star_vec, advanced_vec)
        new_stage = _determine_stage(new_alignment)
        new_distance = 1.0 - new_alignment

        # Build advanced state by enriching original state
        advanced_state = dict(state)
        advanced_state["_north_star_meta"] = {
            "previous_alignment": round(self._last_alignment, 6),
            "new_alignment": round(new_alignment, 6),
            "new_stage": new_stage,
            "new_distance": round(new_distance, 6),
            "thrust_applied": round(thrust_level, 6),
            "propelled": True,
        }

        # Update internal tracking
        self._last_alignment = new_alignment
        self._last_stage = new_stage
        self.alignment_history.append({
            "alignment": round(new_alignment, 6),
            "stage": new_stage,
            "distance": round(new_distance, 6),
            "timestamp": self._now(),
        })

        _publish("north_star.advance", {"stage": new_stage, "alignment": new_alignment})
        return advanced_state

    def get_status(self) -> Dict[str, Any]:
        """Return current alignment, thrust, and distance to star."""
        return {
            "initialized": self._initialized,
            "alignment": round(self._last_alignment, 6),
            "thrust_level": round(self.thrust_level, 6),
            "distance_to_star": round(1.0 - self._last_alignment, 6),
            "stage": self._last_stage,
            "alignment_history_count": len(self.alignment_history),
            "vision": self.vision,
            "values_count": len(self.values),
            "objectives_count": len(self.objectives),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _state_to_text(self, state: Dict[str, Any]) -> str:
        """Serialize a state dictionary into text for vectorization."""
        parts: List[str] = []
        for key, value in sorted(state.items()):
            if key.startswith("_"):
                continue
            if isinstance(value, str):
                parts.append(f"{key}:{value}")
            elif isinstance(value, (list, tuple)):
                parts.append(f"{key}:{' '.join(str(v) for v in value)}")
            elif isinstance(value, dict):
                parts.append(f"{key}:{self._state_to_text(value)}")
            else:
                parts.append(f"{key}:{str(value)}")
        return " ".join(parts)

    def _now(self) -> str:
        """Return ISO timestamp string."""
        import datetime
        return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_module: Optional[NorthStarProtocol] = None


def get_north_star_protocol() -> NorthStarProtocol:
    """Get the global NorthStarProtocol singleton instance."""
    global _module
    if _module is None:
        _module = NorthStarProtocol()
    return _module
