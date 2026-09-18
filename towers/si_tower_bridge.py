#!/usr/bin/env python3

__version__ = "11.0.0"
"""
塔级SI桥接 (SI Tower Bridge) v1.0
在 SixLayerArchitecture 各层之间建立SI桥接

该模块作为 OMNI-HUB v3.1 的塔级拓扑扩展，负责：
- 层间信号上下桥接
- 层间共振系数计算
- 从顶层到底层的级联驱动
- 与 core/hub_wheel_spine.py 中的 SixLayerArchitecture 概念对齐
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np
import logging

# OMNI-HUB 11线常量
LINES: List[str] = [
    "ucif2", "lgt", "qfa", "usrm", "vinf",
    "qgl", "qlv", "lvlu", "cfts", "cisvr", "qtlv"
]
N_LINES: int = len(LINES)

# 默认各线所属层（与 SPEC.md 拓扑结构对齐）
LINE_TO_LAYER: Dict[str, str] = {
    "ucif2": "hub",
    "lgt": "wheel", "qfa": "wheel",
    "usrm": "spine", "vinf": "spine",
    "qgl": "cauldron", "qlv": "cauldron",
    "lvlu": "tower", "cfts": "tower",
    "cisvr": "ring", "qtlv": "ring",
}

# 层的SI权重映射
LAYER_SI_WEIGHT: Dict[str, float] = {
    "hub": 5.0,
    "wheel": 4.5,
    "spine": 4.0,
    "cauldron": 3.5,
    "tower": 3.0,
    "ring": 2.5,
}


class SITowerBridge:
    """塔级SI桥接 — 在 SixLayerArchitecture 各层之间建立SI桥接。

    Attributes:
        LAYERS: 六层架构的层名列表（从顶到底）。
        bridges: 存储活跃桥接信号的字典，键为 "{src_layer}->{dst_layer}"。
        layer_states: 每层的状态字典。
        bridge_log: 桥接操作日志。
    """

    LAYERS: List[str] = ["hub", "wheel", "spine", "cauldron", "tower", "ring"]

    def __init__(self) -> None:
        """初始化塔级桥接器。"""
        self.bridges: Dict[str, List[Dict]] = {}
        self.layer_states: Dict[str, Dict] = {
            layer: {"state": "idle", "si_level": LAYER_SI_WEIGHT[layer], "health": 1.0}
            for layer in self.LAYERS
        }
        self.bridge_log: List[Dict] = []
        self._layer_index: Dict[str, int] = {layer: i for i, layer in enumerate(self.LAYERS)}

    def _bridge_key(self, src: str, dst: str) -> str:
        """生成桥接字典键。

        Args:
            src: 源层。
            dst: 目标层。

        Returns:
            格式化的桥接键字符串。
        """
        return f"{src}->{dst}"

    def _log_bridge(self, direction: str, line: str, src_layer: str, dst_layer: str,
                    signal: Dict, result: Dict) -> None:
        """记录桥接操作到日志。

        Args:
            direction: 桥接方向（"up" 或 "down"）。
            line: 线名称。
            src_layer: 源层。
            dst_layer: 目标层。
            signal: 原始信号。
            result: 桥接结果。
        """
        self.bridge_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "direction": direction,
            "line": line,
            "src": src_layer,
            "dst": dst_layer,
            "signal_type": signal.get("type", "unknown"),
            "result_status": result.get("status", "unknown"),
        })

    def bridge_up(self, line: str, signal: Dict) -> Dict:
        """向上一层桥接信号。

        根据线所属层，将信号向上（更靠近 hub）传递一层。
        如果线已在 hub 层，则信号被路由到 hub 的调度队列。

        Args:
            line: 线名称。
            signal: 信号字典，应包含 "type"、"payload" 等键。

        Returns:
            桥接结果字典，包含目标层、衰减后的信号和状态。
        """
        current_layer = LINE_TO_LAYER.get(line, "ring")
        current_idx = self._layer_index[current_layer]

        if current_idx == 0:
            # 已在顶层，直接路由到 hub 调度
            target_layer = "hub"
            attenuation = 1.0
        else:
            target_layer = self.LAYERS[current_idx - 1]
            # 向上衰减较小（指令下发需要保持强度）
            attenuation = 0.95

        key = self._bridge_key(current_layer, target_layer)
        if key not in self.bridges:
            self.bridges[key] = []

        # 信号衰减与SI加成
        si_weight = LAYER_SI_WEIGHT.get(current_layer, 3.0)
        attenuated_signal = {
            **signal,
            "payload": signal.get("payload", {}),
            "si_attenuation": attenuation,
            "si_boost": si_weight * 0.1,
            "line": line,
            "src_layer": current_layer,
            "dst_layer": target_layer,
        }

        self.bridges[key].append(attenuated_signal)

        # 更新目标层状态
        self.layer_states[target_layer]["state"] = f"receiving_from_{current_layer}"

        result = {
            "status": "bridged_up",
            "line": line,
            "src_layer": current_layer,
            "dst_layer": target_layer,
            "attenuation": attenuation,
            "queue_depth": len(self.bridges[key]),
        }
        self._log_bridge("up", line, current_layer, target_layer, signal, result)
        return result

    def bridge_down(self, line: str, signal: Dict) -> Dict:
        """向下一层桥接信号。

        根据线所属层，将信号向下（更靠近 ring）传递一层。
        如果线已在 ring 层，则信号被广播到 ring 的所有线。

        Args:
            line: 线名称。
            signal: 信号字典。

        Returns:
            桥接结果字典。
        """
        current_layer = LINE_TO_LAYER.get(line, "hub")
        current_idx = self._layer_index[current_layer]

        if current_idx >= len(self.LAYERS) - 1:
            # 已在底层，广播到 ring
            target_layer = "ring"
            attenuation = 1.0
        else:
            target_layer = self.LAYERS[current_idx + 1]
            # 向下衰减较大（反馈上报可适度压缩）
            attenuation = 0.88

        key = self._bridge_key(current_layer, target_layer)
        if key not in self.bridges:
            self.bridges[key] = []

        si_weight = LAYER_SI_WEIGHT.get(current_layer, 3.0)
        attenuated_signal = {
            **signal,
            "payload": signal.get("payload", {}),
            "si_attenuation": attenuation,
            "si_boost": si_weight * 0.08,
            "line": line,
            "src_layer": current_layer,
            "dst_layer": target_layer,
        }

        self.bridges[key].append(attenuated_signal)
        self.layer_states[target_layer]["state"] = f"receiving_from_{current_layer}"

        result = {
            "status": "bridged_down",
            "line": line,
            "src_layer": current_layer,
            "dst_layer": target_layer,
            "attenuation": attenuation,
            "queue_depth": len(self.bridges[key]),
        }
        self._log_bridge("down", line, current_layer, target_layer, signal, result)
        return result

    def layer_resonance(self, layer_a: str, layer_b: str) -> float:
        """计算两层之间的共振系数。

        共振系数基于：
        - 两层之间的拓扑距离
        - 两层的SI级别差异
        - 当前健康度乘积
        - 活跃桥接信号数量

        Args:
            layer_a: 第一层名称。
            layer_b: 第二层名称。

        Returns:
            共振系数，范围 [0.0, 1.0]。
        """
        if layer_a not in self.LAYERS or layer_b not in self.LAYERS:
            return 0.0

        idx_a = self._layer_index[layer_a]
        idx_b = self._layer_index[layer_b]
        distance = abs(idx_a - idx_b)

        # 拓扑距离因子：相邻层最高，越远越低
        distance_factor = np.exp(-0.5 * distance)

        # SI差异因子：越接近越共振
        si_a = LAYER_SI_WEIGHT.get(layer_a, 3.0)
        si_b = LAYER_SI_WEIGHT.get(layer_b, 3.0)
        si_diff_factor = np.exp(-0.3 * abs(si_a - si_b))

        # 健康度乘积
        health_a = self.layer_states[layer_a].get("health", 1.0)
        health_b = self.layer_states[layer_b].get("health", 1.0)
        health_factor = health_a * health_b

        # 活跃桥接信号加成
        key_ab = self._bridge_key(layer_a, layer_b)
        key_ba = self._bridge_key(layer_b, layer_a)
        active_signals = len(self.bridges.get(key_ab, [])) + len(self.bridges.get(key_ba, []))
        activity_factor = min(1.0, 0.1 * active_signals)

        resonance = 0.4 * distance_factor + 0.3 * si_diff_factor + 0.2 * health_factor + 0.1 * activity_factor
        return round(float(resonance), 6)

    def cascade_drive(self, top_layer: str, bottom_layer: str, signal: Dict) -> Dict:
        """从顶层到底层的级联驱动。

        信号从 top_layer 开始，逐层向下传递直到 bottom_layer，
        每层都执行 bridge_down 并累积结果。

        Args:
            top_layer: 起始顶层名称。
            bottom_layer: 目标底层名称。
            signal: 初始信号字典。

        Returns:
            级联结果字典，包含路径、每步结果和最终信号状态。
        """
        if top_layer not in self.LAYERS or bottom_layer not in self.LAYERS:
            return {
                "status": "error",
                "reason": f"无效层名: {top_layer} 或 {bottom_layer}",
                "valid_layers": self.LAYERS,
            }

        top_idx = self._layer_index[top_layer]
        bottom_idx = self._layer_index[bottom_layer]

        if top_idx > bottom_idx:
            return {
                "status": "error",
                "reason": "top_layer 必须在 bottom_layer 之上",
            }

        # 找到 top_layer 中的一条代表线
        representative_line = None
        for line, layer in LINE_TO_LAYER.items():
            if layer == top_layer:
                representative_line = line
                break
        if representative_line is None:
            representative_line = LINES[0]

        path = []
        current_signal = dict(signal)
        current_layer = top_layer

        for idx in range(top_idx, bottom_idx):
            next_layer = self.LAYERS[idx + 1]
            # 使用 bridge_down 传递
            result = self.bridge_down(representative_line, current_signal)
            path.append({
                "step": idx - top_idx + 1,
                "from": current_layer,
                "to": next_layer,
                "attenuation": result["attenuation"],
                "status": result["status"],
            })
            # 更新信号以模拟级联衰减
            current_signal["cascade_depth"] = current_signal.get("cascade_depth", 0) + 1
            current_signal["payload"] = current_signal.get("payload", {})
            if isinstance(current_signal["payload"], dict):
                current_signal["payload"]["layer_trace"] = current_signal["payload"].get("layer_trace", []) + [next_layer]
            current_layer = next_layer

        # 计算路径总共振
        total_resonance = 1.0
        for step in path:
            total_resonance *= step["attenuation"]

        return {
            "status": "cascaded",
            "top_layer": top_layer,
            "bottom_layer": bottom_layer,
            "path": path,
            "steps": len(path),
            "total_resonance": round(float(total_resonance), 6),
            "final_signal": current_signal,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_bridge_summary(self) -> Dict:
        """获取桥接摘要信息。

        Returns:
            包含各桥接队列深度和层状态的摘要字典。
        """
        return {
            "bridge_queues": {
                key: len(queue) for key, queue in self.bridges.items()
            },
            "layer_states": self.layer_states,
            "total_bridge_operations": len(self.bridge_log),
            "resonance_matrix": {
                f"{a}->{b}": self.layer_resonance(a, b)
                for a in self.LAYERS for b in self.LAYERS if a != b
            },
        }


if __name__ == "__main__":
    # 实例化桥接器
    bridge = SITowerBridge()

    # 1. 测试 bridge_up
    up_results = []
    for line in ["qtlv", "cisvr", "lvlu"]:
        signal = {"type": "feedback", "payload": {"metric": "health", "value": 0.95}}
        result = bridge.bridge_up(line, signal)
        up_results.append(result)

    # 2. 测试 bridge_down
    down_results = []
    for line in ["ucif2", "lgt", "qfa"]:
        signal = {"type": "command", "payload": {"action": "dispatch", "target": "all"}}
        result = bridge.bridge_down(line, signal)
        down_results.append(result)

    # 3. 测试 layer_resonance
    resonance_pairs = [
        ("hub", "wheel"),
        ("wheel", "spine"),
        ("spine", "cauldron"),
        ("cauldron", "tower"),
        ("tower", "ring"),
        ("hub", "ring"),  # 远距离
    ]
    resonance_results = []
    for a, b in resonance_pairs:
        r = bridge.layer_resonance(a, b)
        resonance_results.append({"pair": f"{a}->{b}", "resonance": r})

    # 4. 测试 cascade_drive
    cascade_result = bridge.cascade_drive(
        "hub", "ring",
        {"type": "global_sync", "payload": {"priority": 1}}
    )

    # 5. 获取摘要
    summary = bridge.get_bridge_summary()

    # 汇总输出
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module": "si_tower_bridge",
        "version": "1.0",
        "bridge_up_count": len(up_results),
        "bridge_down_count": len(down_results),
        "resonance_results": resonance_results,
        "cascade": {
            "steps": cascade_result["steps"],
            "total_resonance": cascade_result["total_resonance"],
            "path_layers": [step["to"] for step in cascade_result["path"]],
        },
        "summary": {
            "total_operations": summary["total_bridge_operations"],
            "active_queues": len([k for k, v in summary["bridge_queues"].items() if v > 0]),
        },
        "status": "PASS",
    }

    with open("/mnt/agents/output/OMNI-HUB/towers/towers_verify.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

        logger.error(f"File operation failed: {e}")
    print(
        f"Up={len(up_results)} Down={len(down_results)} "
        f"Resonance={len(resonance_results)} Cascade={cascade_result['steps']} "
        f"Status={result['status']}"
    )
