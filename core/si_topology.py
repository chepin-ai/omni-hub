#!/usr/bin/env python3

__version__ = "11.0.0"
"""
OMNI-HUB v3.1 — SI Topology Mapping System
Maps SI mechanism to 5-level topology: Line → Tower → Circle → Ring → Cloud/Quantum

Levels:
  line   : 11 computational lines (ucif2, lgt, qfa, usrm, vinf, qgl, qlv, lvlu, cfts, cisvr, qtlv)
  tower  : SixLayerArchitecture (hub, wheel, spine, cauldron, tower, ring)
  circle : Session/Consensus/Command/Relay circles
  ring   : OMNI-Ring global loop
  cloud  : Quantum coherence field / cloud sync
"""

from collections import deque
from typing import Any
import logging


class SITopology:
    """五级拓扑映射系统：线-塔-圈-环-云/量子"""

    LEVEL_LINE = "line"
    LEVEL_TOWER = "tower"
    LEVEL_CIRCLE = "circle"
    LEVEL_RING = "ring"
    LEVEL_CLOUD = "cloud"

    # Ordered level indices for bridge loss calculation
    _LEVEL_ORDER = [LEVEL_LINE, LEVEL_TOWER, LEVEL_CIRCLE, LEVEL_RING, LEVEL_CLOUD]

    def __init__(self):
        self.topology = self._build_topology()
        # Pre-computed lookup maps for fast pathfinding
        self._line_to_tower: dict[str, str] = {}
        self._line_to_circle: dict[str, str] = {}
        self._tower_layer: dict[str, int] = {}
        self._build_lookups()

    # ------------------------------------------------------------------
    # 1. Topology construction
    # ------------------------------------------------------------------
    def _build_topology(self) -> dict:
        """构建五级拓扑映射"""
        return {
            self.LEVEL_LINE: {
                "ucif2":  {"si": 5.0, "health": 1.0,  "tower": "hub",      "circle": "command"},
                "lgt":    {"si": 4.0, "health": 0.98, "tower": "wheel",    "circle": "session"},
                "qfa":    {"si": 4.0, "health": 0.91, "tower": "wheel",    "circle": "consensus"},
                "usrm":   {"si": 3.0, "health": 0.90, "tower": "spine",    "circle": "session"},
                "vinf":   {"si": 4.0, "health": 0.99, "tower": "spine",    "circle": "command"},
                "qgl":    {"si": 4.0, "health": 0.97, "tower": "cauldron", "circle": "relay"},
                "qlv":    {"si": 3.5, "health": 0.97, "tower": "cauldron", "circle": "relay"},
                "lvlu":   {"si": 4.5, "health": 1.0,  "tower": "tower",    "circle": "relay"},
                "cfts":   {"si": 3.0, "health": 0.86, "tower": "tower",    "circle": "relay"},
                "cisvr":  {"si": 3.5, "health": 0.96, "tower": "ring",     "circle": "consensus"},
                "qtlv":   {"si": 3.5, "health": 0.96, "tower": "ring",     "circle": "relay"},
            },
            self.LEVEL_TOWER: {
                "hub":      {"lines": ["ucif2"],              "layer": 0},
                "wheel":    {"lines": ["lgt", "qfa"],        "layer": 1},
                "spine":    {"lines": ["usrm", "vinf"],      "layer": 2},
                "cauldron": {"lines": ["qgl", "qlv"],        "layer": 3},
                "tower":    {"lines": ["lvlu", "cfts"],      "layer": 4},
                "ring":     {"lines": ["cisvr", "qtlv"],     "layer": 5},
            },
            self.LEVEL_CIRCLE: {
                "session":  {"lines": ["lgt", "usrm"],                  "phase": "init"},
                "consensus":{"lines": ["qfa", "cisvr"],                 "phase": "agree"},
                "command":  {"lines": ["ucif2", "vinf"],                "phase": "exec"},
                "relay":    {"lines": ["qgl", "qlv", "lvlu", "cfts", "qtlv"], "phase": "sync"},
            },
            self.LEVEL_RING: {
                "omni_ring": {"lines": "ALL", "cycle": "continuous"},
            },
            self.LEVEL_CLOUD: {
                "quantum_field": {"lines": "ALL", "coherence": 0.95},
                "global_state":  {"lines": "ALL", "sync": "realtime"},
            },
        }

    def _build_lookups(self):
        """预计算反向查找表，加速路径搜索"""
        line_nodes = self.topology[self.LEVEL_LINE]
        tower_nodes = self.topology[self.LEVEL_TOWER]
        circle_nodes = self.topology[self.LEVEL_CIRCLE]

        for line_name, meta in line_nodes.items():
            self._line_to_tower[line_name] = meta["tower"]
            self._line_to_circle[line_name] = meta["circle"]

        for tower_name, meta in tower_nodes.items():
            self._tower_layer[tower_name] = meta["layer"]

    # ------------------------------------------------------------------
    # 2. Node retrieval
    # ------------------------------------------------------------------
    def get_si_nodes(self, level: str) -> list[dict]:
        """获取指定层级的所有SI节点，返回列表，每个元素含完整元数据"""
        if level not in self.topology:
            return []

        nodes = self.topology[level]
        result = []

        if level == self.LEVEL_LINE:
            for name, meta in nodes.items():
                result.append({
                    "id": name,
                    "si": meta["si"],
                    "health": meta["health"],
                    "tower": meta["tower"],
                    "circle": meta["circle"],
                    "level": level,
                })

        elif level == self.LEVEL_TOWER:
            for name, meta in nodes.items():
                lines = meta["lines"]
                avg_si = sum(self.topology[self.LEVEL_LINE][ln]["si"] for ln in lines) / len(lines)
                avg_health = sum(self.topology[self.LEVEL_LINE][ln]["health"] for ln in lines) / len(lines)
                result.append({
                    "id": name,
                    "layer": meta["layer"],
                    "lines": lines,
                    "avg_si": round(avg_si, 3),
                    "avg_health": round(avg_health, 3),
                    "level": level,
                })

        elif level == self.LEVEL_CIRCLE:
            for name, meta in nodes.items():
                lines = meta["lines"]
                avg_si = sum(self.topology[self.LEVEL_LINE][ln]["si"] for ln in lines) / len(lines)
                avg_health = sum(self.topology[self.LEVEL_LINE][ln]["health"] for ln in lines) / len(lines)
                result.append({
                    "id": name,
                    "phase": meta["phase"],
                    "lines": lines,
                    "avg_si": round(avg_si, 3),
                    "avg_health": round(avg_health, 3),
                    "level": level,
                })

        elif level == self.LEVEL_RING:
            for name, meta in nodes.items():
                result.append({
                    "id": name,
                    "cycle": meta["cycle"],
                    "lines": list(self.topology[self.LEVEL_LINE].keys()),
                    "level": level,
                })

        elif level == self.LEVEL_CLOUD:
            for name, meta in nodes.items():
                entry = {
                    "id": name,
                    "lines": list(self.topology[self.LEVEL_LINE].keys()),
                    "level": level,
                }
                if "coherence" in meta:
                    entry["coherence"] = meta["coherence"]
                if "sync" in meta:
                    entry["sync"] = meta["sync"]
                result.append(entry)

        return result

    # ------------------------------------------------------------------
    # 3. Cross-level bridge
    # ------------------------------------------------------------------
    def bridge_levels(self, from_level: str, to_level: str, signal: dict) -> dict:
        """
        跨层级桥接信号，计算路径损耗（layer差 × 0.05）。

        损耗模型：
        - 基础层级距离损耗 = |level_idx(from) - level_idx(to)| × 0.05
        - 若信号中携带 source_line / target_line，额外叠加两线所在 tower 的 layer 差 × 0.05
        """
        if from_level not in self._LEVEL_ORDER or to_level not in self._LEVEL_ORDER:
            return {"error": f"Invalid level: {from_level} or {to_level}"}

        from_idx = self._LEVEL_ORDER.index(from_level)
        to_idx = self._LEVEL_ORDER.index(to_level)
        base_loss = abs(from_idx - to_idx) * 0.05

        tower_loss = 0.0
        src_line = signal.get("source_line")
        dst_line = signal.get("target_line")

        if src_line and dst_line:
            src_tower = self._line_to_tower.get(src_line)
            dst_tower = self._line_to_tower.get(dst_line)
            if src_tower and dst_tower:
                src_layer = self._tower_layer.get(src_tower, 0)
                dst_layer = self._tower_layer.get(dst_tower, 0)
                tower_loss = abs(src_layer - dst_layer) * 0.05

        total_loss = base_loss + tower_loss
        strength = signal.get("strength", 1.0)
        attenuated_strength = max(0.0, strength * (1.0 - total_loss))

        return {
            "from_level": from_level,
            "to_level": to_level,
            "source_line": src_line,
            "target_line": dst_line,
            "base_loss": round(base_loss, 3),
            "tower_loss": round(tower_loss, 3),
            "total_loss": round(total_loss, 3),
            "original_strength": strength,
            "attenuated_strength": round(attenuated_strength, 3),
            "payload": signal.get("payload"),
            "bridged": True,
        }

    # ------------------------------------------------------------------
    # 4. Signal propagation (DFS with depth limit)
    # ------------------------------------------------------------------
    def propagate(self, level: str, line: str, signal: dict, depth: int = 3) -> dict:
        """
        在拓扑中深度优先传播信号，返回影响到的所有节点。

        传播规则：
        - line   → 同 tower / 同 circle 的其他 line，以及所属 tower、所属 circle
        - tower  → 该 tower 下的所有 line，以及相邻 layer 的 tower，以及 ring
        - circle → 该 circle 下的所有 line，以及 ring
        - ring   → 所有 line，所有 tower，所有 circle，以及 cloud
        - cloud  → 所有 line，所有 tower，所有 circle，ring
        """
        # Validate that the starting node exists in the given level
        if level not in self.topology or line not in self.topology[level]:
            return {"error": f"Unknown node: {level}/{line}", "affected": []}

        visited: set[tuple[str, str]] = set()
        affected: list[dict] = []
        stack: list[tuple[str, str, int]] = [(level, line, depth)]

        while stack:
            cur_level, cur_node, cur_depth = stack.pop()
            key = (cur_level, cur_node)
            if key in visited or cur_depth < 0:
                continue
            visited.add(key)

            # Record affected node
            node_meta = self._get_node_meta(cur_level, cur_node)
            affected.append({
                "level": cur_level,
                "node": cur_node,
                "depth_remaining": cur_depth,
                "meta": node_meta,
            })

            if cur_depth == 0:
                continue

            # Generate neighbours
            neighbours = self._get_neighbours(cur_level, cur_node)
            for nb_level, nb_node in neighbours:
                if (nb_level, nb_node) not in visited:
                    stack.append((nb_level, nb_node, cur_depth - 1))

        return {
            "origin": {"level": level, "line": line},
            "signal": signal,
            "max_depth": depth,
            "affected_count": len(affected),
            "affected": affected,
        }

    def _get_node_meta(self, level: str, node: str) -> dict[str, Any]:
        """获取单个节点的元数据摘要"""
        data = self.topology.get(level, {}).get(node, {})
        if level == self.LEVEL_LINE:
            return {"si": data.get("si"), "health": data.get("health")}
        elif level == self.LEVEL_TOWER:
            return {"layer": data.get("layer"), "lines": data.get("lines")}
        elif level == self.LEVEL_CIRCLE:
            return {"phase": data.get("phase"), "lines": data.get("lines")}
        elif level == self.LEVEL_RING:
            return {"cycle": data.get("cycle")}
        elif level == self.LEVEL_CLOUD:
            return {k: v for k, v in data.items() if k != "lines"}
        return {}

    def _get_neighbours(self, level: str, node: str) -> list[tuple[str, str]]:
        """返回 (level, node) 的邻接节点列表"""
        neighbours: list[tuple[str, str]] = []
        line_nodes = self.topology[self.LEVEL_LINE]
        tower_nodes = self.topology[self.LEVEL_TOWER]
        circle_nodes = self.topology[self.LEVEL_CIRCLE]
        ring_nodes = self.topology[self.LEVEL_RING]
        cloud_nodes = self.topology[self.LEVEL_CLOUD]

        if level == self.LEVEL_LINE:
            if node not in line_nodes:
                return neighbours
            tower = line_nodes[node]["tower"]
            circle = line_nodes[node]["circle"]
            # Same tower lines
            for ln in tower_nodes[tower]["lines"]:
                if ln != node:
                    neighbours.append((self.LEVEL_LINE, ln))
            # Same circle lines
            for ln in circle_nodes[circle]["lines"]:
                if ln != node and ln not in [n[1] for n in neighbours]:
                    neighbours.append((self.LEVEL_LINE, ln))
            # Up to tower
            neighbours.append((self.LEVEL_TOWER, tower))
            # Up to circle
            neighbours.append((self.LEVEL_CIRCLE, circle))

        elif level == self.LEVEL_TOWER:
            if node not in tower_nodes:
                return neighbours
            # Down to lines
            for ln in tower_nodes[node]["lines"]:
                neighbours.append((self.LEVEL_LINE, ln))
            # Adjacent tower layers
            my_layer = tower_nodes[node]["layer"]
            for tn, tm in tower_nodes.items():
                if tn != node and abs(tm["layer"] - my_layer) == 1:
                    neighbours.append((self.LEVEL_TOWER, tn))
            # Up to ring
            for rn in ring_nodes:
                neighbours.append((self.LEVEL_RING, rn))

        elif level == self.LEVEL_CIRCLE:
            if node not in circle_nodes:
                return neighbours
            # Down to lines
            for ln in circle_nodes[node]["lines"]:
                neighbours.append((self.LEVEL_LINE, ln))
            # Up to ring
            for rn in ring_nodes:
                neighbours.append((self.LEVEL_RING, rn))

        elif level == self.LEVEL_RING:
            # Ring connects to everything
            for ln in line_nodes:
                neighbours.append((self.LEVEL_LINE, ln))
            for tn in tower_nodes:
                neighbours.append((self.LEVEL_TOWER, tn))
            for cn in circle_nodes:
                neighbours.append((self.LEVEL_CIRCLE, cn))
            for cld in cloud_nodes:
                neighbours.append((self.LEVEL_CLOUD, cld))

        elif level == self.LEVEL_CLOUD:
            # Cloud connects to everything
            for ln in line_nodes:
                neighbours.append((self.LEVEL_LINE, ln))
            for tn in tower_nodes:
                neighbours.append((self.LEVEL_TOWER, tn))
            for cn in circle_nodes:
                neighbours.append((self.LEVEL_CIRCLE, cn))
            for rn in ring_nodes:
                neighbours.append((self.LEVEL_RING, rn))

        return neighbours

    # ------------------------------------------------------------------
    # 5. Shortest path between two lines
    # ------------------------------------------------------------------
    def get_line_path(self, line_a: str, line_b: str) -> dict:
        """
        返回两线之间的最短拓扑路径（BFS），路径经过的节点表示为 (level, node_id) 序列。
        """
        if line_a not in self.topology[self.LEVEL_LINE]:
            return {"error": f"Unknown line: {line_a}"}
        if line_b not in self.topology[self.LEVEL_LINE]:
            return {"error": f"Unknown line: {line_b}"}
        if line_a == line_b:
            return {
                "from": line_a,
                "to": line_b,
                "path": [(self.LEVEL_LINE, line_a)],
                "hops": 0,
            }

        start = (self.LEVEL_LINE, line_a)
        goal = (self.LEVEL_LINE, line_b)

        queue: deque[tuple[tuple[str, str], list[tuple[str, str]]]] = deque()
        queue.append((start, [start]))
        visited: set[tuple[str, str]] = {start}

        while queue:
            (cur_level, cur_node), path = queue.popleft()
            neighbours = self._get_neighbours(cur_level, cur_node)
            for nb_level, nb_node in neighbours:
                nb_key = (nb_level, nb_node)
                if nb_key in visited:
                    continue
                new_path = path + [nb_key]
                if nb_key == goal:
                    return {
                        "from": line_a,
                        "to": line_b,
                        "path": new_path,
                        "hops": len(new_path) - 1,
                    }
                visited.add(nb_key)
                queue.append((nb_key, new_path))

        return {"error": f"No path found from {line_a} to {line_b}"}

    # ------------------------------------------------------------------
    # 6. Level health aggregation
    # ------------------------------------------------------------------
    def get_level_health(self, level: str) -> dict:
        """
        计算某层级的平均健康度。
        - line   : 直接对所有 line 的 health 取平均
        - tower  : 对 tower 下所有 line 的 health 取平均（返回每个 tower 的健康度）
        - circle : 对 circle 下所有 line 的 health 取平均（返回每个 circle 的健康度）
        - ring   : 所有 line 的平均健康度
        - cloud  : 所有 line 的平均健康度（加权云相干系数）
        """
        line_nodes = self.topology[self.LEVEL_LINE]

        if level == self.LEVEL_LINE:
            healths = [meta["health"] for meta in line_nodes.values()]
            avg = sum(healths) / len(healths) if healths else 0.0
            return {
                "level": level,
                "overall_health": round(avg, 4),
                "min_health": round(min(healths), 4) if healths else 0.0,
                "max_health": round(max(healths), 4) if healths else 0.0,
                "node_count": len(healths),
            }

        elif level == self.LEVEL_TOWER:
            tower_nodes = self.topology[self.LEVEL_TOWER]
            per_tower = {}
            for tname, tmeta in tower_nodes.items():
                healths = [line_nodes[ln]["health"] for ln in tmeta["lines"]]
                per_tower[tname] = round(sum(healths) / len(healths), 4)
            overall = round(sum(per_tower.values()) / len(per_tower), 4) if per_tower else 0.0
            return {
                "level": level,
                "overall_health": overall,
                "per_node": per_tower,
                "node_count": len(per_tower),
            }

        elif level == self.LEVEL_CIRCLE:
            circle_nodes = self.topology[self.LEVEL_CIRCLE]
            per_circle = {}
            for cname, cmeta in circle_nodes.items():
                healths = [line_nodes[ln]["health"] for ln in cmeta["lines"]]
                per_circle[cname] = round(sum(healths) / len(healths), 4)
            overall = round(sum(per_circle.values()) / len(per_circle), 4) if per_circle else 0.0
            return {
                "level": level,
                "overall_health": overall,
                "per_node": per_circle,
                "node_count": len(per_circle),
            }

        elif level == self.LEVEL_RING:
            healths = [meta["health"] for meta in line_nodes.values()]
            avg = sum(healths) / len(healths) if healths else 0.0
            return {
                "level": level,
                "overall_health": round(avg, 4),
                "min_health": round(min(healths), 4) if healths else 0.0,
                "max_health": round(max(healths), 4) if healths else 0.0,
                "node_count": len(healths),
            }

        elif level == self.LEVEL_CLOUD:
            healths = [meta["health"] for meta in line_nodes.values()]
            avg = sum(healths) / len(healths) if healths else 0.0
            cloud_nodes = self.topology[self.LEVEL_CLOUD]
            coherence = cloud_nodes.get("quantum_field", {}).get("coherence", 1.0)
            weighted = avg * coherence
            return {
                "level": level,
                "overall_health": round(avg, 4),
                "weighted_health": round(weighted, 4),
                "coherence_factor": coherence,
                "node_count": len(healths),
            }

        return {"error": f"Unknown level: {level}"}


# ====================================================================
# Test block
# ====================================================================
if __name__ == "__main__":
    topo = SITopology()
    print("=" * 60)
    print("OMNI-HUB v3.1 — SI Topology Mapping System Tests")
    print("=" * 60)

    # Test 1: Topology construction
    print("\n[TEST 1] Topology construction")
    for lvl in [SITopology.LEVEL_LINE, SITopology.LEVEL_TOWER,
                SITopology.LEVEL_CIRCLE, SITopology.LEVEL_RING,
                SITopology.LEVEL_CLOUD]:
        nodes = topo.get_si_nodes(lvl)
        print(f"  {lvl:8s}: {len(nodes)} nodes")
    assert len(topo.get_si_nodes(SITopology.LEVEL_LINE)) == 11
    assert len(topo.get_si_nodes(SITopology.LEVEL_TOWER)) == 6
    assert len(topo.get_si_nodes(SITopology.LEVEL_CIRCLE)) == 4
    assert len(topo.get_si_nodes(SITopology.LEVEL_RING)) == 1
    assert len(topo.get_si_nodes(SITopology.LEVEL_CLOUD)) == 2
    print("  PASS: All 5 levels have correct node counts")

    # Test 2: Get SI nodes detail
    print("\n[TEST 2] SI node details (line level)")
    line_nodes = topo.get_si_nodes(SITopology.LEVEL_LINE)
    ucif2 = next(n for n in line_nodes if n["id"] == "ucif2")
    assert ucif2["si"] == 5.0
    assert ucif2["tower"] == "hub"
    assert ucif2["circle"] == "command"
    print(f"  ucif2: SI={ucif2['si']}, tower={ucif2['tower']}, circle={ucif2['circle']}")
    print("  PASS")

    # Test 3: Tower node aggregation
    print("\n[TEST 3] Tower node aggregation")
    tower_nodes = topo.get_si_nodes(SITopology.LEVEL_TOWER)
    hub = next(n for n in tower_nodes if n["id"] == "hub")
    assert hub["layer"] == 0
    assert "ucif2" in hub["lines"]
    print(f"  hub: layer={hub['layer']}, lines={hub['lines']}, avg_si={hub['avg_si']}")
    print("  PASS")

    # Test 4: Bridge levels — same level (no loss)
    print("\n[TEST 4] Bridge levels — same level")
    result = topo.bridge_levels(
        SITopology.LEVEL_LINE, SITopology.LEVEL_LINE,
        {"strength": 1.0, "payload": "test"}
    )
    assert result["total_loss"] == 0.0
    assert result["attenuated_strength"] == 1.0
    print(f"  line→line: loss={result['total_loss']}, strength={result['attenuated_strength']}")
    print("  PASS")

    # Test 5: Bridge levels — line to tower (adjacent, 1 step)
    print("\n[TEST 5] Bridge levels — line to tower")
    result = topo.bridge_levels(
        SITopology.LEVEL_LINE, SITopology.LEVEL_TOWER,
        {"strength": 1.0, "payload": "test"}
    )
    assert result["total_loss"] == 0.05  # |0-1| * 0.05
    assert result["attenuated_strength"] == 0.95
    print(f"  line→tower: loss={result['total_loss']}, strength={result['attenuated_strength']}")
    print("  PASS")

    # Test 6: Bridge levels — line to cloud (4 steps)
    print("\n[TEST 6] Bridge levels — line to cloud")
    result = topo.bridge_levels(
        SITopology.LEVEL_LINE, SITopology.LEVEL_CLOUD,
        {"strength": 1.0, "payload": "test"}
    )
    assert result["total_loss"] == 0.20  # |0-4| * 0.05
    assert result["attenuated_strength"] == 0.80
    print(f"  line→cloud: loss={result['total_loss']}, strength={result['attenuated_strength']}")
    print("  PASS")

    # Test 7: Bridge levels — with tower layer delta (ucif2 hub layer0 → cisvr ring layer5)
    print("\n[TEST 7] Bridge levels — with tower layer delta")
    result = topo.bridge_levels(
        SITopology.LEVEL_LINE, SITopology.LEVEL_TOWER,
        {
            "strength": 1.0,
            "source_line": "ucif2",   # hub, layer 0
            "target_line": "cisvr",   # ring, layer 5
            "payload": "test",
        }
    )
    # base_loss = |0-1| * 0.05 = 0.05
    # tower_loss = |0-5| * 0.05 = 0.25
    # total = 0.30
    assert result["total_loss"] == 0.30
    assert result["attenuated_strength"] == 0.70
    print(f"  ucif2→cisvr: base={result['base_loss']}, tower={result['tower_loss']}, "
          f"total={result['total_loss']}, strength={result['attenuated_strength']}")
    print("  PASS")

    # Test 8: Propagate from line with depth=1
    print("\n[TEST 8] Propagate from line (ucif2, depth=1)")
    result = topo.propagate(
        SITopology.LEVEL_LINE, "ucif2",
        {"type": "pulse", "data": "hello"},
        depth=1
    )
    affected = result["affected"]
    print(f"  Affected nodes: {len(affected)}")
    for a in affected:
        print(f"    - {a['level']}/{a['node']} (depth={a['depth_remaining']})")
    # origin (ucif2, depth=1) + neighbours at depth=0
    # ucif2's tower=hub, circle=command
    # same tower: none (only ucif2)
    # same circle: vinf
    # up to tower: hub
    # up to circle: command
    assert len(affected) == 4  # ucif2 + vinf + hub + command
    print("  PASS")

    # Test 9: Propagate from line with depth=2
    print("\n[TEST 9] Propagate from line (lgt, depth=2)")
    result = topo.propagate(
        SITopology.LEVEL_LINE, "lgt",
        {"type": "sync", "data": "state"},
        depth=2
    )
    affected = result["affected"]
    print(f"  Affected nodes: {len(affected)}")
    assert len(affected) > 4  # should reach more nodes at depth 2
    print("  PASS")

    # Test 10: Propagate from ring (reaches all at sufficient depth)
    print("\n[TEST 10] Propagate from ring (depth=3)")
    result = topo.propagate(
        SITopology.LEVEL_RING, "omni_ring",
        {"type": "broadcast", "data": "global_sync"},
        depth=3
    )
    affected = result["affected"]
    print(f"  Affected nodes: {len(affected)}")
    # Ring at depth 3 should reach all 11 lines + 6 towers + 4 circles + 2 clouds + 1 ring = 24
    assert len(affected) == 24
    print("  PASS: Ring propagation reaches all 24 nodes")

    # Test 11: Shortest path — same line
    print("\n[TEST 11] Shortest path — same line")
    path = topo.get_line_path("ucif2", "ucif2")
    assert path["hops"] == 0
    assert path["path"] == [(SITopology.LEVEL_LINE, "ucif2")]
    print(f"  ucif2→ucif2: hops={path['hops']}")
    print("  PASS")

    # Test 12: Shortest path — same tower
    print("\n[TEST 12] Shortest path — same tower (lgt ↔ qfa)")
    path = topo.get_line_path("lgt", "qfa")
    assert path["hops"] == 1  # direct via line level (same tower neighbours)
    print(f"  lgt→qfa: hops={path['hops']}, path={path['path']}")
    print("  PASS")

    # Test 13: Shortest path — same circle
    print("\n[TEST 13] Shortest path — same circle (lgt ↔ usrm)")
    path = topo.get_line_path("lgt", "usrm")
    assert path["hops"] == 1  # direct via line level (same circle neighbours)
    print(f"  lgt→usrm: hops={path['hops']}, path={path['path']}")
    print("  PASS")

    # Test 14: Shortest path — cross tower via circle
    print("\n[TEST 14] Shortest path — cross tower (ucif2 ↔ qfa)")
    path = topo.get_line_path("ucif2", "qfa")
    # ucif2 (command) and qfa (consensus) are in different circles
    # Shortest: ucif2 → command → (???) → qfa  ... or ucif2 → hub → wheel → qfa
    # Actually: ucif2(line) → hub(tower) → wheel(tower, adjacent layer) → qfa(line)
    # That's 3 hops
    print(f"  ucif2→qfa: hops={path['hops']}, path={path['path']}")
    assert path["hops"] >= 2
    print("  PASS")

    # Test 15: Shortest path — far apart (ucif2 ↔ qtlv)
    print("\n[TEST 15] Shortest path — far apart (ucif2 ↔ qtlv)")
    path = topo.get_line_path("ucif2", "qtlv")
    print(f"  ucif2→qtlv: hops={path['hops']}, path={path['path']}")
    assert path["hops"] >= 2
    print("  PASS")

    # Test 16: Level health — line
    print("\n[TEST 16] Level health — line")
    health = topo.get_level_health(SITopology.LEVEL_LINE)
    print(f"  Overall: {health['overall_health']}, min={health['min_health']}, "
          f"max={health['max_health']}, nodes={health['node_count']}")
    assert health["node_count"] == 11
    assert 0.0 < health["overall_health"] <= 1.0
    print("  PASS")

    # Test 17: Level health — tower
    print("\n[TEST 17] Level health — tower")
    health = topo.get_level_health(SITopology.LEVEL_TOWER)
    print(f"  Overall: {health['overall_health']}")
    for tname, th in health["per_node"].items():
        print(f"    {tname}: {th}")
    assert len(health["per_node"]) == 6
    print("  PASS")

    # Test 18: Level health — circle
    print("\n[TEST 18] Level health — circle")
    health = topo.get_level_health(SITopology.LEVEL_CIRCLE)
    print(f"  Overall: {health['overall_health']}")
    for cname, ch in health["per_node"].items():
        print(f"    {cname}: {ch}")
    assert len(health["per_node"]) == 4
    print("  PASS")

    # Test 19: Level health — ring
    print("\n[TEST 19] Level health — ring")
    health = topo.get_level_health(SITopology.LEVEL_RING)
    print(f"  Overall: {health['overall_health']}")
    assert health["node_count"] == 11
    print("  PASS")

    # Test 20: Level health — cloud (with coherence weighting)
    print("\n[TEST 20] Level health — cloud")
    health = topo.get_level_health(SITopology.LEVEL_CLOUD)
    print(f"  Overall: {health['overall_health']}, weighted: {health['weighted_health']}, "
          f"coherence: {health['coherence_factor']}")
    assert "weighted_health" in health
    assert "coherence_factor" in health
    print("  PASS")

    print("\n" + "=" * 60)
    print("ALL 20 TESTS PASSED — SITopology v3.1 ready for OMNI-HUB")
    print("=" * 60)
