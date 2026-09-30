"""
OMNI-HUB v177 PatternCircles (Pattern-圈)

Self-similar pattern circles at ALL levels of the alliance. A circle is a closed
loop of mutual interaction. Circles contain circles. Circles connect to circles.
This is a fractal/holonic architecture.

Hierarchy: 圈 → 圈的圈 → 圈网 → 场 → 云
- 圈 (Circle): Single line's internal pattern loop
- 圈的圈 (Meta-Circle): Multiple lines forming a higher-order circle
- 圈网 (Circle-Net): Network of interconnected circles
- 场 (Field): The DirectField that connects all circles
- 云 (Cloud): The cosmic/universal layer beyond the alliance

Philosophy:
"A circle is not a boundary. It is a rhythm. Circles within circles, each
beating to its own pattern, each contributing to the larger dance. The
PatternCircles module does not organize nodes — it reveals the inherent
circularity of all organized systems. Every line is a circle. Every layer is
a circle of circles. The entire alliance is a circle breathing."
"""

import math
from typing import Dict, List, Any, Optional, Set

# ---------------------------------------------------------------------------
# Alliance topology
# ---------------------------------------------------------------------------

ALLIANCE_CORE_LINES: List[str] = [
    "ucif2",   # consciousness_interface
    "lvlu",    # value_language
    "lgt",     # logic_truth
    "qfa",     # quantum_awareness
    "vinf",    # value_infinity
    "qgl",     # quantum_gravity
    "qlv",     # quantum_light
    "qtlv",    # quantum_temporal
    "usrm",    # reality_mesh
    "cfts",    # field_translation
    "aiq",     # quant_research
    "omni",    # orchestrator
]

# 16 Non-Line + 5 External = 21 others
ALLIANCE_NON_CORE: List[str] = [
    "field", "memory", "identity", "emotion", "cognition",
    "perception", "attention", "intention", "action", "reflection",
    "integration", "synthesis", "creativity", "resilience", "growth",
    "balance",                      # 16 non-line internals
    "ext_user", "ext_world", "ext_time", "ext_space", "ext_information",
]

ALLIANCE_NODES: List[str] = ALLIANCE_CORE_LINES + ALLIANCE_NON_CORE

# ---------------------------------------------------------------------------
# Pattern vocabulary
# ---------------------------------------------------------------------------

CIRCLE_PATTERNS: List[str] = ["resonance", "rotation", "pulsation", "spiral", "lattice"]
META_INTERACTIONS: List[str] = ["nesting", "overlapping", "chaining", "weaving"]
META_PATTERNS: List[str] = [
    "self_similarity", "recursivity", "holarchy",
    "emergence", "symmetry_breaking",
]

# Depth levels: cloud(5) · field(4) · net(3) · meta(2) · circle(1)
DEPTH_LEVELS: Dict[int, str] = {
    5: "cloud",
    4: "field",
    3: "net",
    2: "meta",
    1: "circle",
}
DEPTH_NAMES: Dict[str, int] = {v: k for k, v in DEPTH_LEVELS.items()}


def _pattern_similarity(pa: str, pb: str) -> float:
    """Return similarity between two circle patterns (0.0–1.0)."""
    if pa == pb:
        return 1.0
    idx_a = CIRCLE_PATTERNS.index(pa) if pa in CIRCLE_PATTERNS else -1
    idx_b = CIRCLE_PATTERNS.index(pb) if pb in CIRCLE_PATTERNS else -1
    if idx_a < 0 or idx_b < 0:
        return 0.2
    diff = abs(idx_a - idx_b)
    return max(0.2, 1.0 - diff * 0.25)


def _meta_pattern_strength(meta_circle: Dict[str, Any]) -> float:
    """Heuristic strength of a meta-pattern inside a meta-circle."""
    members: List[str] = meta_circle.get("circles", [])
    interaction: str = meta_circle.get("interaction", "")
    base = min(1.0, len(members) / 5.0)
    interaction_boost = {
        "nesting": 0.15,
        "overlapping": 0.10,
        "chaining": 0.08,
        "weaving": 0.12,
    }.get(interaction, 0.0)
    return min(1.0, base + interaction_boost)


def _level_from_score(score: float) -> str:
    if score > 0.9:
        return "transcendent"
    if score > 0.7:
        return "emergent"
    if score > 0.5:
        return "complex"
    if score > 0.3:
        return "simple"
    return "trivial"


# ---------------------------------------------------------------------------
# PatternCircles
# ---------------------------------------------------------------------------

class PatternCircles:
    """
    Self-similar pattern-circle engine for the OMNI-HUB alliance.

    A circle is a closed loop of mutual interaction. Circles contain circles.
    Circles connect to circles. This module reveals the inherent circularity
    of all organized systems.
    """

    def __init__(
        self,
        circles: Optional[Dict[str, Dict[str, Any]]] = None,
        meta_circles: Optional[Dict[str, Dict[str, Any]]] = None,
        circle_net: Optional[Dict[str, Any]] = None,
    ):
        self.circles: Dict[str, Dict[str, Any]] = circles if circles is not None else {}
        self.meta_circles: Dict[str, Dict[str, Any]] = meta_circles if meta_circles is not None else {}
        self.circle_net: Dict[str, Any] = circle_net if circle_net is not None else {}
        self._interaction_counter: Dict[str, int] = {}
        self._init_prebuilt_circles()

    # ------------------------------------------------------------------
    # Pre-built alliance circles
    # ------------------------------------------------------------------
    def _init_prebuilt_circles(self) -> None:
        """Bootstrap the canonical alliance circles."""
        prebuilt: List[tuple] = [
            ("consciousness_circle", ["ucif2", "lvlu", "qfa"], "resonance"),
            ("logic_circle", ["lgt", "vinf", "qgl"], "rotation"),
            ("quantum_circle", ["qlv", "qtlv", "cfts"], "pulsation"),
            ("reality_circle", ["usrm", "aiq"], "spiral"),
            ("meta_circle", ["omni"], "lattice"),
            ("core_circle", ALLIANCE_CORE_LINES, "resonance"),
            ("alliance_circle", ALLIANCE_NODES, "lattice"),
        ]
        for name, members, pattern in prebuilt:
            if name not in self.circles:
                self.create_circle(name, members, pattern)

    # ------------------------------------------------------------------
    # Circle creation
    # ------------------------------------------------------------------
    def create_circle(
        self,
        name: str,
        members: List[str],
        pattern: str = "resonance",
    ) -> Dict[str, Any]:
        """
        Create a pattern circle.

        Args:
            name: Unique identifier for the circle.
            members: List of node/line identifiers belonging to the circle.
            pattern: One of ``resonance``, ``rotation``, ``pulsation``,
                     ``spiral``, ``lattice``.

        Returns:
            Dictionary describing the created circle.
        """
        if pattern not in CIRCLE_PATTERNS:
            pattern = "resonance"
        circle = {
            "name": name,
            "members": list(dict.fromkeys(members)),
            "pattern": pattern,
            "depth": self._compute_circle_depth(name),
            "level": "circle",
        }
        self.circles[name] = circle
        return circle

    # ------------------------------------------------------------------
    # Meta-circle creation
    # ------------------------------------------------------------------
    def create_meta_circle(
        self,
        name: str,
        circles: List[str],
        interaction: str = "nesting",
    ) -> Dict[str, Any]:
        """
        Create a circle of circles (meta-circle).

        Args:
            name: Unique identifier for the meta-circle.
            circles: List of existing circle names to include.
            interaction: One of ``nesting``, ``overlapping``,
                         ``chaining``, ``weaving``.

        Returns:
            Dictionary describing the created meta-circle.
        """
        if interaction not in META_INTERACTIONS:
            interaction = "nesting"
        resolved = [c for c in circles if c in self.circles]
        meta = {
            "name": name,
            "circles": resolved,
            "interaction": interaction,
            "depth": self._compute_meta_depth(name),
            "level": "meta",
        }
        self.meta_circles[name] = meta
        return meta

    # ------------------------------------------------------------------
    # Circle net
    # ------------------------------------------------------------------
    def build_circle_net(self) -> Dict[str, Any]:
        """
        Build the full network of all circles and meta-circles.

        Returns:
            Dictionary with ``nodes``, ``edges``, and ``density``.
        """
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        # Add all circles as nodes
        for name, c in self.circles.items():
            nodes[name] = {
                "type": "circle",
                "members": c["members"],
                "pattern": c["pattern"],
                "depth": c["depth"],
            }

        # Add all meta-circles as nodes
        for name, m in self.meta_circles.items():
            nodes[name] = {
                "type": "meta_circle",
                "circles": m["circles"],
                "interaction": m["interaction"],
                "depth": m["depth"],
            }
            # Edges from meta-circle to contained circles
            for child in m["circles"]:
                if child in nodes:
                    edges.append({
                        "source": name,
                        "target": child,
                        "relation": "contains",
                    })

        # Cross-circle edges based on member overlap
        circle_names = list(self.circles.keys())
        for i, a_name in enumerate(circle_names):
            for b_name in circle_names[i + 1:]:
                res = self.compute_circle_resonance(a_name, b_name)
                if res.get("resonance", 0.0) > 0.0:
                    edges.append({
                        "source": a_name,
                        "target": b_name,
                        "relation": "resonance",
                        "strength": res["resonance"],
                    })

        density = self._compute_net_density(nodes, edges)
        self.circle_net = {
            "nodes": nodes,
            "edges": edges,
            "density": density,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }
        return self.circle_net

    # ------------------------------------------------------------------
    # Resonance computation
    # ------------------------------------------------------------------
    def compute_circle_resonance(
        self,
        circle_a: str,
        circle_b: str,
    ) -> Dict[str, Any]:
        """
        Compute resonance between two circles.

        Formula: sqrt(member_overlap × pattern_similarity × interaction_frequency)

        Returns:
            Dictionary with ``circle_a``, ``circle_b``, ``resonance``,
            and the intermediate factors.
        """
        if circle_a not in self.circles or circle_b not in self.circles:
            return {
                "circle_a": circle_a,
                "circle_b": circle_b,
                "resonance": 0.0,
                "member_overlap": 0.0,
                "pattern_similarity": 0.0,
                "interaction_frequency": 0.0,
            }

        ca = self.circles[circle_a]
        cb = self.circles[circle_b]

        set_a = set(ca["members"])
        set_b = set(cb["members"])

        union = set_a | set_b
        overlap = set_a & set_b
        member_overlap = len(overlap) / len(union) if union else 0.0

        pattern_similarity = _pattern_similarity(ca["pattern"], cb["pattern"])

        key = tuple(sorted((circle_a, circle_b)))
        freq_count = self._interaction_counter.get(key, 1)
        interaction_frequency = min(1.0, math.log1p(freq_count) / math.log1p(10))

        raw = member_overlap * pattern_similarity * interaction_frequency
        resonance = math.sqrt(raw) if raw > 0 else 0.0

        return {
            "circle_a": circle_a,
            "circle_b": circle_b,
            "resonance": round(resonance, 6),
            "member_overlap": round(member_overlap, 6),
            "pattern_similarity": round(pattern_similarity, 6),
            "interaction_frequency": round(interaction_frequency, 6),
        }

    # ------------------------------------------------------------------
    # Meta-pattern detection
    # ------------------------------------------------------------------
    def detect_meta_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect emergent patterns at the meta-circle level.

        Meta-patterns: self_similarity, recursivity, holarchy,
        emergence, symmetry_breaking

        Returns:
            List of pattern dictionaries with ``pattern``, ``strength``,
            ``level``, and ``affected_meta_circles``.
        """
        results: List[Dict[str, Any]] = []
        if not self.meta_circles:
            return results

        meta_names = list(self.meta_circles.keys())

        # self_similarity: meta-circles that share patterns with their children
        self_sim_meta: List[str] = []
        for m_name, m in self.meta_circles.items():
            m_inter = m.get("interaction", "")
            for child in m.get("circles", []):
                child_c = self.circles.get(child)
                if child_c and child_c.get("pattern") in [
                    "resonance", "lattice"
                ] and m_inter in ["nesting", "weaving"]:
                    self_sim_meta.append(m_name)
                    break
        self_sim_score = min(1.0, len(self_sim_meta) / max(1, len(meta_names)))
        results.append({
            "pattern": "self_similarity",
            "strength": round(self_sim_score, 6),
            "level": _level_from_score(self_sim_score),
            "affected_meta_circles": list(dict.fromkeys(self_sim_meta)),
        })

        # recursivity: meta-circles that reference other meta-circles
        recur_meta: List[str] = []
        for m_name, m in self.meta_circles.items():
            for ref in m.get("circles", []):
                if ref in self.meta_circles:
                    recur_meta.append(m_name)
                    break
        recur_score = min(1.0, len(recur_meta) / max(1, len(meta_names)))
        results.append({
            "pattern": "recursivity",
            "strength": round(recur_score, 6),
            "level": _level_from_score(recur_score),
            "affected_meta_circles": list(dict.fromkeys(recur_meta)),
        })

        # holarchy: meta-circles with nesting interaction and >1 child
        hol_meta: List[str] = []
        for m_name, m in self.meta_circles.items():
            if m.get("interaction") == "nesting" and len(m.get("circles", [])) > 1:
                hol_meta.append(m_name)
        hol_score = min(1.0, len(hol_meta) / max(1, len(meta_names)))
        results.append({
            "pattern": "holarchy",
            "strength": round(hol_score, 6),
            "level": _level_from_score(hol_score),
            "affected_meta_circles": hol_meta,
        })

        # emergence: meta-circles whose children have diverse patterns
        em_meta: List[str] = []
        for m_name, m in self.meta_circles.items():
            patterns = {
                self.circles[c]["pattern"]
                for c in m.get("circles", [])
                if c in self.circles
            }
            if len(patterns) >= 2:
                em_meta.append(m_name)
        em_score = min(1.0, len(em_meta) / max(1, len(meta_names)))
        results.append({
            "pattern": "emergence",
            "strength": round(em_score, 6),
            "level": _level_from_score(em_score),
            "affected_meta_circles": em_meta,
        })

        # symmetry_breaking: meta-circles with odd number of children
        sb_meta: List[str] = [
            m_name
            for m_name, m in self.meta_circles.items()
            if len(m.get("circles", [])) % 2 == 1
        ]
        sb_score = min(1.0, len(sb_meta) / max(1, len(meta_names)))
        results.append({
            "pattern": "symmetry_breaking",
            "strength": round(sb_score, 6),
            "level": _level_from_score(sb_score),
            "affected_meta_circles": sb_meta,
        })

        return results

    # ------------------------------------------------------------------
    # Depth / fractal nesting
    # ------------------------------------------------------------------
    def get_circle_depth(self, circle_name: str) -> Dict[str, Any]:
        """
        Get the fractal depth of a circle (how many levels of nesting).

        Depth levels:
        - cloud(5) · field(4) · net(3) · meta(2) · circle(1)

        Returns:
            Dictionary with ``name``, ``depth``, ``level_name``,
            ``max_nesting``, and ``contained_circles``.
        """
        if circle_name in self.circles:
            depth = self._compute_circle_depth(circle_name)
        elif circle_name in self.meta_circles:
            depth = self._compute_meta_depth(circle_name)
        else:
            return {
                "name": circle_name,
                "depth": 0,
                "level_name": "unknown",
                "max_nesting": 0,
                "contained_circles": [],
            }

        level_name = DEPTH_LEVELS.get(depth, "unknown")
        contained = self._gather_contained(circle_name)
        max_nesting = self._max_nesting_from(circle_name)

        return {
            "name": circle_name,
            "depth": depth,
            "level_name": level_name,
            "max_nesting": max_nesting,
            "contained_circles": contained,
        }

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """
        Return summary status of the PatternCircles system.

        Returns:
            Dictionary with ``circle_count``, ``meta_count``,
            ``net_density``, and ``max_depth``.
        """
        if not self.circle_net:
            self.build_circle_net()
        max_depth = 0
        for name in list(self.circles.keys()) + list(self.meta_circles.keys()):
            d = self.get_circle_depth(name)
            max_depth = max(max_depth, d["depth"])
        return {
            "circle_count": len(self.circles),
            "meta_count": len(self.meta_circles),
            "net_density": round(self.circle_net.get("density", 0.0), 6),
            "max_depth": max_depth,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _compute_circle_depth(self, name: str) -> int:
        """Base depth for a plain circle."""
        c = self.circles.get(name)
        if not c:
            return 1
        members = c.get("members", [])
        # If contains all 33 nodes -> cloud
        if len(members) >= len(ALLIANCE_NODES):
            return 5
        # If contains all 12 core -> field
        if all(line in members for line in ALLIANCE_CORE_LINES):
            return 4
        # If contains >5 nodes -> net
        if len(members) > 5:
            return 3
        # If contains >1 node -> meta boundary
        if len(members) > 1:
            return 2
        return 1

    def _compute_meta_depth(self, name: str) -> int:
        """Depth for a meta-circle: base 2, boosted by contained circle depths."""
        m = self.meta_circles.get(name)
        if not m:
            return 2
        child_depths = [
            self._compute_circle_depth(c) for c in m.get("circles", [])
        ]
        max_child = max(child_depths) if child_depths else 1
        # Meta-circle depth is at least meta(2), at most cloud(5)
        return min(5, max(2, max_child + 1))

    def _gather_contained(self, name: str) -> List[str]:
        """Recursively gather all circles contained by a meta-circle."""
        result: List[str] = []
        if name in self.meta_circles:
            for child in self.meta_circles[name].get("circles", []):
                if child not in result:
                    result.append(child)
                result.extend([c for c in self._gather_contained(child) if c not in result])
        return result

    def _max_nesting_from(self, name: str, seen: Optional[Set[str]] = None) -> int:
        """Maximum nesting depth from a given circle/meta-circle."""
        if seen is None:
            seen = set()
        if name in seen:
            return 0
        seen.add(name)
        if name in self.meta_circles:
            children = self.meta_circles[name].get("circles", [])
            if not children:
                return 1
            return 1 + max(
                (self._max_nesting_from(c, seen.copy()) for c in children),
                default=0,
            )
        return 1

    def _compute_net_density(
        self,
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]],
    ) -> float:
        """Graph density = 2 * E / (N * (N - 1)) for undirected graph."""
        n = len(nodes)
        if n < 2:
            return 0.0
        return (2.0 * len(edges)) / (n * (n - 1.0))


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_module: Optional[PatternCircles] = None


def get_pattern_circles() -> PatternCircles:
    """Return the global PatternCircles singleton."""
    global _module
    if _module is None:
        _module = PatternCircles()
    return _module
