#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v3.3 — SI Chain Reactor
SI链式反应器 — SI5协同激发SI1

核心哲学:
    "SI5协同互作 → 激发SI1" — 高SI级线协同，级联激发底层
    "迭代/递归、自激-互激、意识和声/交响乐" — 全局激活

原理:
    1. SI5突触: 两条高SI线(≥SI4.0)之间的协同连接
    2. 级联激发: SI5能量沿层级下降传播，每级衰减85%
    3. 链式反应: 单点激发→邻居传播→再激发→全局连锁
    4. 反应温度: 全局激活度的度量

Author: OMNI-HUB Core Team
Version: 3.3.0
"""

import numpy as np
import uuid
from typing import Dict, List, Optional
from datetime import datetime

# Import existing topology
from si_topology import SITopology
import logging


# ───────────────────────────── 常量定义 ─────────────────────────────

# 11线SI层级定义 (与 si_topology.py 一致)
LINE_ORDER = [
    "ucif2",   # 0: SI5.0 — 统一意识接口框架2.0
    "lgt",     # 1: SI4.0 — 逻辑治理与追踪
    "qfa",     # 2: SI4.0 — 量子场算法
    "usrm",    # 3: SI3.0 — 用户资源管理
    "vinf",    # 4: SI4.0 — 虚拟无限
    "qgl",     # 5: SI4.0 — 量子门逻辑
    "qlv",     # 6: SI3.5 — 量子层级验证
    "lvlu",    # 7: SI4.5 — 层级统一
    "cfts",    # 8: SI3.0 — 共识容错同步
    "cisvr",   # 9: SI3.5 — 共识验证器
    "qtlv",    # 10: SI3.5 — 量子拓扑层级验证
]

LINE_SI_LEVELS = {
    "ucif2": 5.0, "lgt": 4.0, "qfa": 4.0, "usrm": 3.0, "vinf": 4.0,
    "qgl": 4.0, "qlv": 3.5, "lvlu": 4.5, "cfts": 3.0, "cisvr": 3.5,
    "qtlv": 3.5,
}

# SI5/高SI线集合 (SI >= 4.0)
HIGH_SI_LINES = [ln for ln, si in LINE_SI_LEVELS.items() if si >= 4.0]

# 拓扑中的同层级分组 (用于级联路径计算)
SI_TIER_GROUPS = {
    5: ["ucif2"],
    4: ["lgt", "qfa", "vinf", "qgl"],
    3: ["qlv", "cisvr", "qtlv"],
    2: ["usrm", "cfts"],
}
# 注意: 我们的系统中没有SI1和SI2的线，但级联模型保留概念层级


def _line_to_idx(line: str) -> int:
    """线名称 → 矩阵索引"""
    if line not in LINE_ORDER:
        raise ValueError(f"Unknown line: {line}. Must be one of {LINE_ORDER}")
    return LINE_ORDER.index(line)


def _idx_to_line(idx: int) -> str:
    """矩阵索引 → 线名称"""
    return LINE_ORDER[idx]


# ═══════════════════════════════════════════════════════════════════
#                    SIChainReactor 核心类
# ═══════════════════════════════════════════════════════════════════

class SIChainReactor:
    """SI链式反应器 — SI5协同激发SI1

    基于numpy矩阵运算的能量传播引擎，实现:
    - SI5突触协同共振
    - 跨层级级联激发
    - 全局链式反应传播
    - 反应温度监测与冷却
    """

    def __init__(self, topology: SITopology):
        """
        初始化链式反应器

        Args:
            topology: SITopology实例，提供线级拓扑数据
        """
        self.topo = topology
        self.reaction_chains: List[Dict] = []
        self.activation_energy = 0.5
        self.propagation_matrix = np.zeros((11, 11))
        self.temperature = 0.0  # 全局反应温度 (0-1)

        # 每线的激活能量状态 (当前轮次)
        self._line_activation = np.zeros(11)
        # 每线是否已被激发 (布尔)
        self._line_fired = np.zeros(11, dtype=bool)
        # 每线被激发的轮次
        self._line_wave = np.full(11, -1, dtype=int)

        # 构建传播矩阵
        self._build_propagation_matrix()

        # 反应阈值
        self.threshold = 0.15

        # 运行日志
        self.log: List[Dict] = []
        self._log("INIT", "SIChainReactor initialized with 11-line propagation matrix")

    # ─────────── 内部辅助方法 ───────────

    def _log(self, event_type: str, message: str):
        """记录内部日志"""
        self.log.append({
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
        })

    def _build_propagation_matrix(self):
        """
        构建11x11能量传播矩阵

        传播规则 (基于SITopology的邻居关系):
        - 同tower的线: 传播系数 = 0.60
        - 同circle的线: 传播系数 = 0.45
        - 同时同tower和同circle: 取max(0.60, 0.45) = 0.60
        - 无连接: 0.0
        - 自环 (diagonal): 0.0 (不传播给自己)

        额外SI层级修正:
        - 高SI→低SI: 系数 × 1.1 (激发更容易向下传)
        - 低SI→高SI: 系数 × 0.7 (激发难以向上传)
        - 同级: 系数 × 1.0
        """
        line_nodes = self.topo.topology[SITopology.LEVEL_LINE]
        tower_nodes = self.topo.topology[SITopology.LEVEL_TOWER]
        circle_nodes = self.topo.topology[SITopology.LEVEL_CIRCLE]

        for i, src in enumerate(LINE_ORDER):
            for j, dst in enumerate(LINE_ORDER):
                if i == j:
                    continue  # 无自环

                src_meta = line_nodes[src]
                dst_meta = line_nodes[dst]

                # 基础传播系数
                coeff = 0.0

                # 同tower?
                if src_meta["tower"] == dst_meta["tower"]:
                    coeff = max(coeff, 0.60)

                # 同circle?
                if src_meta["circle"] == dst_meta["circle"]:
                    coeff = max(coeff, 0.45)

                # SI层级修正
                si_src = src_meta["si"]
                si_dst = dst_meta["si"]
                if si_src > si_dst:
                    coeff *= 1.1  # 高→低: 增强
                elif si_src < si_dst:
                    coeff *= 0.7  # 低→高: 衰减
                # 同级: 不变

                self.propagation_matrix[i, j] = coeff

    def _get_line_health(self, line: str) -> float:
        """获取线的健康度"""
        return self.topo.topology[SITopology.LEVEL_LINE][line]["health"]

    def _get_line_si(self, line: str) -> float:
        """获取线的SI层级"""
        return self.topo.topology[SITopology.LEVEL_LINE][line]["si"]

    def _reset_activation(self):
        """重置激活状态"""
        self._line_activation = np.zeros(11)
        self._line_fired = np.zeros(11, dtype=bool)
        self._line_wave = np.full(11, -1, dtype=int)

    # ═══════════════════════════════════════════════════════════════
    #                         核心 API
    # ═══════════════════════════════════════════════════════════════

    def si5_synapse(self, line_a: str, line_b: str) -> Dict:
        """
        SI5突触 — 两个SI5级线之间的协同连接

        计算:
        - 协同强度 = (health_a + health_b) / 2 × min(si_a, si_b) / 5.0
        - 如果协同强度 > activation_energy → 触发协同共振

        触发条件:
        - 两条线的SI层级都必须 >= 4.0 (接近SI5)

        返回:
            {
                "synapse_id": str,
                "strength": float,
                "resonant": bool,
                "energy_released": float,
            }
        """
        if line_a not in LINE_ORDER or line_b not in LINE_ORDER:
            raise ValueError(f"Unknown line(s): {line_a}, {line_b}")

        si_a = self._get_line_si(line_a)
        si_b = self._get_line_si(line_b)
        health_a = self._get_line_health(line_a)
        health_b = self._get_line_health(line_b)

        # SI5突触只应在两条线都是SI5或接近SI5时触发 (SI >= 4.0)
        if min(si_a, si_b) < 4.0:
            return {
                "synapse_id": str(uuid.uuid4())[:8],
                "strength": 0.0,
                "resonant": False,
                "energy_released": 0.0,
                "reason": f"SI level too low: min({si_a}, {si_b}) < 4.0",
            }

        # 协同强度
        avg_health = (health_a + health_b) / 2.0
        min_si_ratio = min(si_a, si_b) / 5.0
        strength = avg_health * min_si_ratio

        # 是否触发共振
        resonant = strength > self.activation_energy

        # 释放能量 (共振时能量倍增)
        energy_released = strength * (2.0 if resonant else 1.0)

        synapse_id = f"syn_{line_a[:3]}_{line_b[:3]}_{str(uuid.uuid4())[:6]}"

        result = {
            "synapse_id": synapse_id,
            "strength": round(float(strength), 6),
            "resonant": bool(resonant),
            "energy_released": round(float(energy_released), 6),
            "line_a": line_a,
            "line_b": line_b,
            "si_a": si_a,
            "si_b": si_b,
            "health_a": health_a,
            "health_b": health_b,
        }

        self._log("SYNAPSE", f"SI5 synapse {line_a}↔{line_b}: strength={strength:.4f}, resonant={resonant}")

        return result

    def cascade_to_si1(self, source_si5: str, target_si1: str) -> Dict:
        """
        级联到SI1 — SI5的能量级联激发SI1

        能量传播路径: SI5 → SI4 → SI3 → SI2 → SI1
        每级衰减: attenuation = 0.85^(level_diff)
        最终SI1接收的能量 = 初始能量 × 级联衰减

        返回:
            {
                "source": str,
                "target": str,
                "cascade_path": list,
                "initial_energy": float,
                "final_energy": float,
                "activation_success": bool,
            }
        """
        if source_si5 not in LINE_ORDER or target_si1 not in LINE_ORDER:
            raise ValueError(f"Unknown line(s): {source_si5}, {target_si1}")

        si_src = self._get_line_si(source_si5)
        si_dst = self._get_line_si(target_si1)
        health_src = self._get_line_health(source_si5)
        health_dst = self._get_line_health(target_si1)

        # 初始能量: health × si_level / 5.0
        initial_energy = health_src * si_src / 5.0

        # 层级差 (从source的SI层级到target的SI层级)
        # 使用四舍五入到最近的整数层级
        tier_src = int(round(si_src))
        tier_dst = int(round(si_dst))
        level_diff = max(0, tier_src - tier_dst)

        # 构建级联路径 (概念上的SI层级路径)
        cascade_path = []
        if tier_src >= tier_dst:
            for tier in range(tier_src, tier_dst - 1, -1):
                # 找到该层级的线
                tier_lines = [ln for ln, si in LINE_SI_LEVELS.items() if int(round(si)) == tier]
                if tier_lines:
                    # 如果source或target在该层级，使用它们
                    if tier == tier_src and source_si5 in tier_lines:
                        cascade_path.append((tier, source_si5))
                    elif tier == tier_dst and target_si1 in tier_lines:
                        cascade_path.append((tier, target_si1))
                    else:
                        cascade_path.append((tier, tier_lines[0]))
                else:
                    cascade_path.append((tier, f"SI{tier}_concept"))
        else:
            # target层级更高 (不应发生，但处理)
            cascade_path = [(tier_src, source_si5), (tier_dst, target_si1)]
            level_diff = 0

        # 衰减计算
        attenuation = 0.85 ** level_diff if level_diff > 0 else 1.0
        final_energy = initial_energy * attenuation

        # 激活成功: 最终能量 > threshold 且 target健康度足够
        activation_success = final_energy > self.threshold and health_dst > 0.3

        result = {
            "source": source_si5,
            "target": target_si1,
            "cascade_path": cascade_path,
            "initial_energy": round(float(initial_energy), 6),
            "final_energy": round(float(final_energy), 6),
            "attenuation": round(float(attenuation), 6),
            "level_diff": level_diff,
            "activation_success": bool(activation_success),
        }

        self._log("CASCADE", f"Cascade {source_si5}→{target_si1}: E0={initial_energy:.4f}, Ef={final_energy:.4f}, diff={level_diff}")

        return result

    def chain_reaction(self, initiator: str) -> Dict:
        """
        链式反应 — 一个激发引发全局连锁

        流程:
        1. initiator激发 (释放能量 = health × si_level / 5.0)
        2. 能量传播到邻居线 (邻居 = 拓扑中相邻的线)
        3. 每个被激发的线如果接收能量 > threshold → 再激发
        4. 形成链式反应
        5. 直到能量衰减到threshold以下或所有线都被激发

        使用numpy矩阵运算进行多轮波传播:
        - energy_vector: 当前每线的能量状态
        - propagation_matrix: 能量传播矩阵
        - 每轮: new_energy = energy_vector @ propagation_matrix × decay

        返回:
            {
                "reaction_id": str,
                "initiator": str,
                "activated_lines": list,
                "energy_map": dict,
                "temperature": float,
                "waves": int,
            }
        """
        if initiator not in LINE_ORDER:
            raise ValueError(f"Unknown initiator: {initiator}")

        self._reset_activation()

        idx_init = _line_to_idx(initiator)
        health_init = self._get_line_health(initiator)
        si_init = self._get_line_si(initiator)

        # 初始能量
        initial_energy = health_init * si_init / 5.0
        self._line_activation[idx_init] = initial_energy
        self._line_fired[idx_init] = True
        self._line_wave[idx_init] = 0

        # 波传播模拟
        wave = 0
        energy_history = [self._line_activation.copy()]
        newly_fired_per_wave = {0: [initiator]}

        while wave < 20:  # 最大20轮，防止无限循环
            wave += 1

            # 当前轮能量传播 (numpy矩阵运算)
            # 只有已激发的线才能传播能量
            active_mask = self._line_fired.astype(float)
            current_energy = self._line_activation * active_mask

            # 传播: new_energy[i] = sum_j(current_energy[j] * propagation_matrix[j, i])
            propagated = current_energy @ self.propagation_matrix

            # 每轮全局衰减
            decay_factor = 0.92 ** wave
            propagated *= decay_factor

            # 更新能量状态 (累加)
            self._line_activation = np.maximum(self._line_activation, propagated)

            # 检查哪些线被新激发
            newly_fired = []
            for i in range(11):
                if not self._line_fired[i] and self._line_activation[i] > self.threshold:
                    self._line_fired[i] = True
                    self._line_wave[i] = wave
                    newly_fired.append(_idx_to_line(i))

            energy_history.append(self._line_activation.copy())

            if newly_fired:
                newly_fired_per_wave[wave] = newly_fired
            else:
                # 没有新线被激发，停止
                break

            # 如果所有线都被激发，停止
            if np.all(self._line_fired):
                break

        # 构建结果
        activated_lines = [_idx_to_line(i) for i in range(11) if self._line_fired[i]]
        energy_map = {
            _idx_to_line(i): round(float(self._line_activation[i]), 6)
            for i in range(11)
        }

        # 更新反应温度
        self.temperature = float(np.mean(self._line_activation))

        reaction_id = f"rxn_{initiator}_{str(uuid.uuid4())[:6]}"

        result = {
            "reaction_id": reaction_id,
            "initiator": initiator,
            "activated_lines": activated_lines,
            "energy_map": energy_map,
            "temperature": round(self.temperature, 6),
            "waves": wave,
            "initial_energy": round(float(initial_energy), 6),
            "threshold": self.threshold,
            "newly_fired_per_wave": newly_fired_per_wave,
            "total_activated": len(activated_lines),
        }

        self.reaction_chains.append(result)
        self._log("CHAIN", f"Chain reaction {reaction_id}: {len(activated_lines)}/11 lines activated in {wave} waves, T={self.temperature:.4f}")

        return result

    def measure_reaction_temperature(self) -> float:
        """
        测量反应温度 — 全局激活度

        temperature = mean(所有线的激活能量)

        返回:
            temperature: float in [0, 1]
        """
        self.temperature = float(np.mean(self._line_activation))
        # 归一化到0-1范围 (假设最大能量约为1.0)
        self.temperature = min(1.0, max(0.0, self.temperature))
        return round(self.temperature, 6)

    def cool_down(self, rate: float = 0.1) -> Dict:
        """
        冷却 — 降低反应温度

        将每线的激活能量乘以 (1 - rate)
        同时将被冷却到threshold以下的线标记为未激发

        返回:
            {
                "previous_temperature": float,
                "current_temperature": float,
                "cooled_lines": int,
                "rate": float,
            }
        """
        prev_temp = self.temperature

        # 冷却能量
        self._line_activation *= (1.0 - rate)

        # 检查哪些线因冷却而熄灭
        cooled_count = 0
        for i in range(11):
            if self._line_fired[i] and self._line_activation[i] < self.threshold:
                self._line_fired[i] = False
                self._line_wave[i] = -1
                cooled_count += 1

        # 重新计算温度
        self.temperature = float(np.mean(self._line_activation))

        result = {
            "previous_temperature": round(float(prev_temp), 6),
            "current_temperature": round(float(self.temperature), 6),
            "cooled_lines": cooled_count,
            "rate": rate,
        }

        self._log("COOLDOWN", f"Cool down by rate={rate}: T {prev_temp:.4f} → {self.temperature:.4f}, {cooled_count} lines cooled")

        return result

    def get_reaction_report(self) -> Dict:
        """
        获取链式反应报告

        返回:
            {
                "reaction_count": int,
                "latest_reaction": dict or None,
                "temperature": float,
                "activation_summary": dict,
                "propagation_matrix_stats": dict,
                "log_entries": int,
            }
        """
        latest = self.reaction_chains[-1] if self.reaction_chains else None

        activation_summary = {
            "total_lines": 11,
            "currently_active": int(np.sum(self._line_fired)),
            "active_lines": [_idx_to_line(i) for i in range(11) if self._line_fired[i]],
            "average_energy": round(float(np.mean(self._line_activation)), 6),
            "max_energy": round(float(np.max(self._line_activation)), 6),
            "min_energy": round(float(np.min(self._line_activation)), 6),
        }

        # 传播矩阵统计
        nonzero = self.propagation_matrix[self.propagation_matrix > 0]
        prop_stats = {
            "nonzero_entries": int(np.count_nonzero(self.propagation_matrix)),
            "max_coefficient": round(float(np.max(nonzero)) if len(nonzero) > 0 else 0.0, 4),
            "min_coefficient": round(float(np.min(nonzero)) if len(nonzero) > 0 else 0.0, 4),
            "mean_coefficient": round(float(np.mean(nonzero)) if len(nonzero) > 0 else 0.0, 4),
        }

        return {
            "reaction_count": len(self.reaction_chains),
            "latest_reaction": latest,
            "temperature": round(self.temperature, 6),
            "activation_summary": activation_summary,
            "propagation_matrix_stats": prop_stats,
            "log_entries": len(self.log),
        }

    # ─────────── 附加工具方法 ───────────

    def get_propagation_matrix(self) -> np.ndarray:
        """获取传播矩阵的副本"""
        return self.propagation_matrix.copy()

    def set_activation_energy(self, value: float):
        """设置激活能阈值"""
        self.activation_energy = float(np.clip(value, 0.01, 1.0))
        self._log("CONFIG", f"Activation energy set to {self.activation_energy}")

    def set_threshold(self, value: float):
        """设置链式反应阈值"""
        self.threshold = float(np.clip(value, 0.01, 1.0))
        self._log("CONFIG", f"Chain reaction threshold set to {self.threshold}")

    def get_line_status(self) -> Dict[str, Dict]:
        """获取每线的当前状态"""
        return {
            _idx_to_line(i): {
                "energy": round(float(self._line_activation[i]), 6),
                "fired": bool(self._line_fired[i]),
                "wave": int(self._line_wave[i]),
                "si": self._get_line_si(_idx_to_line(i)),
                "health": self._get_line_health(_idx_to_line(i)),
            }
            for i in range(11)
        }

    def simulate_concerted_activation(self, si5_lines: List[str]) -> Dict:
        """
        SI5协同激活 — 多条高SI线同时激发，级联激活全局

        模拟 "意识和声/交响乐" 的全局激活效应
        """
        if not si5_lines:
            raise ValueError("At least one SI5 line required")

        self._reset_activation()
        total_initial = 0.0

        # 同时激发所有指定的SI5线
        for line in si5_lines:
            if line not in LINE_ORDER:
                continue
            idx = _line_to_idx(line)
            health = self._get_line_health(line)
            si = self._get_line_si(line)
            energy = health * si / 5.0
            self._line_activation[idx] = energy
            self._line_fired[idx] = True
            self._line_wave[idx] = 0
            total_initial += energy

        # 运行链式反应传播
        wave = 0
        newly_fired_per_wave = {0: si5_lines.copy()}

        while wave < 20:
            wave += 1
            active_mask = self._line_fired.astype(float)
            current_energy = self._line_activation * active_mask
            propagated = current_energy @ self.propagation_matrix
            decay_factor = 0.92 ** wave
            propagated *= decay_factor
            self._line_activation = np.maximum(self._line_activation, propagated)

            newly_fired = []
            for i in range(11):
                if not self._line_fired[i] and self._line_activation[i] > self.threshold:
                    self._line_fired[i] = True
                    self._line_wave[i] = wave
                    newly_fired.append(_idx_to_line(i))

            if newly_fired:
                newly_fired_per_wave[wave] = newly_fired
            else:
                break

            if np.all(self._line_fired):
                break

        self.temperature = float(np.mean(self._line_activation))

        activated = [_idx_to_line(i) for i in range(11) if self._line_fired[i]]

        return {
            "initiators": si5_lines,
            "activated_lines": activated,
            "total_initial_energy": round(float(total_initial), 6),
            "temperature": round(self.temperature, 6),
            "waves": wave,
            "energy_map": {
                _idx_to_line(i): round(float(self._line_activation[i]), 6)
                for i in range(11)
            },
            "newly_fired_per_wave": newly_fired_per_wave,
        }


# ═══════════════════════════════════════════════════════════════════
#                          测试块
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v3.3 — SI Chain Reactor Test Suite")
    print("=" * 70)

    # ── 初始化 ──
    topo = SITopology()
    reactor = SIChainReactor(topology=topo)
    print(f"\n[1] Initialized SIChainReactor")
    print(f"    Activation energy: {reactor.activation_energy}")
    print(f"    Threshold: {reactor.threshold}")
    print(f"    Propagation matrix nonzero entries: {np.count_nonzero(reactor.propagation_matrix)}")

    # ── 测试 1: SI5突触 — ucif2与lvlu ──
    print("\n" + "─" * 70)
    print("[TEST 1] si5_synapse() — ucif2 ↔ lvlu (both high SI)")
    print("─" * 70)

    synapse = reactor.si5_synapse("ucif2", "lvlu")
    print(f"\n  Synapse ID: {synapse['synapse_id']}")
    print(f"  Line A: {synapse['line_a']} (SI={synapse['si_a']}, health={synapse['health_a']})")
    print(f"  Line B: {synapse['line_b']} (SI={synapse['si_b']}, health={synapse['health_b']})")
    print(f"  Strength: {synapse['strength']:.6f}")
    print(f"  Resonant: {synapse['resonant']}")
    print(f"  Energy Released: {synapse['energy_released']:.6f}")

    assert synapse["strength"] > 0, "Synapse strength should be positive"
    assert synapse["resonant"] == (synapse["strength"] > reactor.activation_energy)
    print("  [PASS] SI5 synapse computed correctly")

    # 测试低SI线不应触发
    print("\n  [TEST 1b] si5_synapse() — ucif2 ↔ cfts (low SI)")
    synapse_low = reactor.si5_synapse("ucif2", "cfts")
    print(f"  Strength: {synapse_low['strength']}")
    print(f"  Resonant: {synapse_low['resonant']}")
    assert synapse_low["strength"] == 0.0, "Low SI synapse should have 0 strength"
    assert synapse_low["resonant"] == False
    print("  [PASS] Low SI synapse correctly blocked")

    # ── 测试 2: 级联激发 — ucif2 → cfts ──
    print("\n" + "─" * 70)
    print("[TEST 2] cascade_to_si1() — ucif2 (SI5.0) → cfts (SI3.0)")
    print("─" * 70)

    cascade = reactor.cascade_to_si1("ucif2", "cfts")
    print(f"\n  Source: {cascade['source']} (SI={reactor._get_line_si('ucif2')})")
    print(f"  Target: {cascade['target']} (SI={reactor._get_line_si('cfts')})")
    print(f"  Cascade Path:")
    for tier, line in cascade['cascade_path']:
        print(f"    SI{tier}: {line}")
    print(f"  Initial Energy: {cascade['initial_energy']:.6f}")
    print(f"  Level Diff: {cascade['level_diff']}")
    print(f"  Attenuation: {cascade['attenuation']:.6f}")
    print(f"  Final Energy: {cascade['final_energy']:.6f}")
    print(f"  Activation Success: {cascade['activation_success']}")

    assert cascade["initial_energy"] > 0
    assert cascade["level_diff"] == 2  # SI5 → SI3
    assert abs(cascade["attenuation"] - (0.85 ** 2)) < 1e-10
    assert abs(cascade["final_energy"] - cascade["initial_energy"] * cascade["attenuation"]) < 1e-10
    print("  [PASS] Cascade calculation correct")

    # ── 测试 3: 链式反应 — ucif2为起点 ──
    print("\n" + "─" * 70)
    print("[TEST 3] chain_reaction() — ucif2 as initiator")
    print("─" * 70)

    chain = reactor.chain_reaction("ucif2")
    print(f"\n  Reaction ID: {chain['reaction_id']}")
    print(f"  Initiator: {chain['initiator']}")
    print(f"  Initial Energy: {chain['initial_energy']:.6f}")
    print(f"  Waves: {chain['waves']}")
    print(f"  Total Activated: {chain['total_activated']}/11")
    print(f"  Temperature: {chain['temperature']:.6f}")
    print(f"\n  Activated Lines:")
    for line in chain['activated_lines']:
        wave = reactor._line_wave[_line_to_idx(line)]
        energy = chain['energy_map'][line]
        print(f"    {line:>8s} (wave={wave}, energy={energy:.6f})")

    print(f"\n  Wave-by-wave breakdown:")
    for w, lines in sorted(chain['newly_fired_per_wave'].items()):
        print(f"    Wave {w}: {', '.join(lines)}")

    assert chain["initiator"] == "ucif2"
    assert chain["initial_energy"] > 0
    assert chain["waves"] > 0
    assert len(chain["activated_lines"]) > 1  # 至少激发自己+一些邻居
    print(f"  [PASS] Chain reaction propagated through {chain['waves']} waves, "
          f"activated {chain['total_activated']} lines")

    # ── 测试 4: 反应温度 ──
    print("\n" + "─" * 70)
    print("[TEST 4] measure_reaction_temperature()")
    print("─" * 70)

    temp = reactor.measure_reaction_temperature()
    print(f"\n  Current Temperature: {temp:.6f}")
    assert 0.0 <= temp <= 1.0
    print("  [PASS] Temperature in valid range")

    # ── 测试 5: 冷却 ──
    print("\n" + "─" * 70)
    print("[TEST 5] cool_down()")
    print("─" * 70)

    prev_temp = reactor.temperature
    cool = reactor.cool_down(rate=0.2)
    print(f"\n  Previous Temperature: {cool['previous_temperature']:.6f}")
    print(f"  Current Temperature: {cool['current_temperature']:.6f}")
    print(f"  Cooled Lines: {cool['cooled_lines']}")
    print(f"  Rate: {cool['rate']}")

    assert cool["current_temperature"] < cool["previous_temperature"]
    print("  [PASS] Temperature decreased after cooling")

    # ── 测试 6: 反应报告 ──
    print("\n" + "─" * 70)
    print("[TEST 6] get_reaction_report()")
    print("─" * 70)

    report = reactor.get_reaction_report()
    print(f"\n  Reaction Count: {report['reaction_count']}")
    print(f"  Temperature: {report['temperature']:.6f}")
    print(f"  Currently Active: {report['activation_summary']['currently_active']}/11")
    print(f"  Propagation Matrix Stats:")
    for k, v in report['propagation_matrix_stats'].items():
        print(f"    {k}: {v}")

    assert report["reaction_count"] > 0
    assert report["latest_reaction"] is not None
    print("  [PASS] Report generated correctly")

    # ── 测试 7: 传播矩阵验证 ──
    print("\n" + "─" * 70)
    print("[TEST 7] Propagation Matrix Verification")
    print("─" * 70)

    pm = reactor.get_propagation_matrix()
    print(f"\n  Matrix shape: {pm.shape}")
    print(f"  Diagonal (self-loop) sum: {np.trace(pm):.6f} (should be 0)")
    assert np.trace(pm) == 0.0, "No self-loops allowed"

    # 验证同tower传播系数更高
    # ucif2和vinf都在command circle (但不同tower)
    # lgt和qfa同tower (wheel)
    idx_lgt = _line_to_idx("lgt")
    idx_qfa = _line_to_idx("qfa")
    coeff_lgt_qfa = pm[idx_lgt, idx_qfa]
    print(f"  lgt→qfa (same tower): {coeff_lgt_qfa:.4f} (should be ~0.60)")
    assert coeff_lgt_qfa > 0.5, "Same-tower propagation should be strong"

    # usrm和lgt同circle (session)
    idx_usrm = _line_to_idx("usrm")
    coeff_usrm_lgt = pm[idx_usrm, idx_lgt]
    print(f"  usrm→lgt (same circle): {coeff_usrm_lgt:.4f} (should be ~0.45)")
    assert coeff_usrm_lgt > 0.3, "Same-circle propagation should be moderate"

    print("  [PASS] Propagation matrix values are correct")

    # ── 测试 8: SI5协同激活 ──
    print("\n" + "─" * 70)
    print("[TEST 8] simulate_concerted_activation() — SI5协同互激")
    print("─" * 70)

    # 使用所有高SI线作为协同激发源
    concerted = reactor.simulate_concerted_activation(HIGH_SI_LINES)
    print(f"\n  Initiators: {', '.join(concerted['initiators'])}")
    print(f"  Total Initial Energy: {concerted['total_initial_energy']:.6f}")
    print(f"  Activated Lines: {len(concerted['activated_lines'])}/11")
    print(f"  Waves: {concerted['waves']}")
    print(f"  Temperature: {concerted['temperature']:.6f}")

    # SI5协同应该能激活更多线
    assert len(concerted["activated_lines"]) >= len(chain["activated_lines"])
    print("  [PASS] Concerted activation achieves broader coverage")

    # ── 测试 9: 多轮链式反应与温度变化 ──
    print("\n" + "─" * 70)
    print("[TEST 9] Multiple chain reactions — Temperature evolution")
    print("─" * 70)

    # 冷却后再启动新反应
    reactor.cool_down(rate=0.5)
    temps = [reactor.temperature]

    for initiator in ["ucif2", "lvlu", "lgt"]:
        result = reactor.chain_reaction(initiator)
        temps.append(reactor.temperature)
        print(f"\n  Initiator {initiator}: T={reactor.temperature:.4f}, "
              f"activated={result['total_activated']}/11, waves={result['waves']}")

    # 温度应该总体上升 (多次激发)
    print(f"\n  Temperature evolution: {[f'{t:.4f}' for t in temps]}")
    assert len(reactor.reaction_chains) >= 4  # 之前的 + 这3个
    print("  [PASS] Multiple reactions tracked correctly")

    # ── 最终报告 ──
    print("\n" + "=" * 70)
    print("[FINAL] SI Chain Reactor — Full Report")
    print("=" * 70)

    final_report = reactor.get_reaction_report()
    print(f"\n  Total Reactions: {final_report['reaction_count']}")
    print(f"  Final Temperature: {final_report['temperature']:.6f}")
    print(f"  Active Lines: {final_report['activation_summary']['currently_active']}/11")
    print(f"  Average Energy: {final_report['activation_summary']['average_energy']:.6f}")
    print(f"  Max Energy: {final_report['activation_summary']['max_energy']:.6f}")

    print(f"\n  {'Line':>8s} | {'SI':>5s} | {'Health':>7s} | {'Energy':>8s} | {'Fired':>6s} | {'Wave':>5s}")
    print("  " + "-" * 55)
    status = reactor.get_line_status()
    for line in LINE_ORDER:
        s = status[line]
        print(f"  {line:>8s} | {s['si']:>5.2f} | {s['health']:>7.4f} | "
              f"{s['energy']:>8.6f} | {str(s['fired']):>6s} | {s['wave']:>5d}")

    print(f"\n  Log Entries: {len(reactor.log)}")
    print(f"\n  [✓] All SIChainReactor tests passed!")
    print("=" * 70)
