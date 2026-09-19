#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12 - 周天循环系统 (Zhou Tian / Cosmic Cycle)
本线及各线大小周天关系

概念框架:
    小周天 (Small Heavenly Circuit):
        - 单线内部的自循环
        - 周期短、频率高、相位自锁
        - 如: Lean→证明→债务→Lean
        
    大周天 (Great Heavenly Circuit):
        - 跨线的大循环
        - 周期长、频率低、相位漂移
        - 如: 场→圈→环→层→网→塔→云→场
        
    周天关系:
        - 谐波关系: 大周天频率是小周天的整数分之一
        - 相位锁定: 小周天相位与大周天相位保持固定关系
        - 能量交换: 小周天向大周天输送能量，大周天向小周天提供结构

数学模型:
    小周天: y_small = A_small * sin(ω_small * t + φ_small)
    大周天: y_great = A_great * sin(ω_great * t + φ_great)
    谐波条件: ω_small = n * ω_great (n为正整数)
    相位锁定: φ_small = k * φ_great + δ (k为谐波次数, δ为固定偏移)
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Set, Tuple, Optional, Callable, Any
from collections import defaultdict
import json


# ═══════════════════════════════════════════════════════════════
# 基础定义
# ═══════════════════════════════════════════════════════════════

class CircuitType(Enum):
    """周天类型"""
    SMALL = "small"          # 小周天 (单线自循环)
    GREAT = "great"          # 大周天 (跨线大循环)
    MICRO = "micro"          # 微周天 (子循环/子循环)
    NANO = "nano"            # 纳周天 (原子级循环)


class CircuitPhase(Enum):
    """周天相位 - 八卦对应"""
    QIAN = ("乾", 0, "☰")           # 天 - 开始/创造
    DUI = ("兑", 1, "☱")            # 泽 - 愉悦/开放
    LI = ("离", 2, "☲")             # 火 - 光明/依附
    ZHEN = ("震", 3, "☳")           # 雷 - 震动/行动
    XUN = ("巽", 4, "☴")            # 风 - 渗透/入
    KAN = ("坎", 5, "☵")            # 水 - 危险/陷
    GEN = ("艮", 6, "☶")            # 山 - 静止/止
    KUN = ("坤", 7, "☷")            # 地 - 承载/顺
    
    def __init__(self, cn_name, index, symbol):
        self.cn_name = cn_name
        self.index = index
        self.symbol = symbol


# 11条线定义
ELEVEN_LINES = [
    "ucif2",      # 0: Lean/证明/数学
    "sib0",       # 1: SI循环/涌现
    "fctn",       # 2: 函数式/桥接
    "weave",      # 3: 知识编织
    "consensus",  # 4: 共识/协议
    "surge",      # 5: 浪涌/峰值
    "debt",       # 6: 债务/欠条
    "bridge",     # 7: 桥接/翻译
    "reflect",    # 8: 反思/元认知
    "wildq",      # 9: 野问/开放问题
    "omni",       # 10: OMNI-HUB本体
]


# ═══════════════════════════════════════════════════════════════
# 周天节点 - 循环中的关键位置
# ═══════════════════════════════════════════════════════════════

@dataclass
class CircuitNode:
    """
    周天节点 - 循环中的一个状态/位置
    
    节点属性:
        - id: 唯一标识
        - name: 节点名称
        - phase_angle: 相位角 (0-2π)
        - energy_level: 能量水平
        - line_affinity: 所属线亲和度
        - transitions: 可转移到的下一节点
    """
    id: str = field(default_factory=lambda: "CN-" + str(uuid.uuid4())[:6])
    name: str = ""
    phase_angle: float = 0.0          # 相位角 (0-2π)
    energy_level: float = 0.5          # 能量水平 (0-1)
    entropy: float = 0.5               # 熵 (混乱度)
    line_affinity: Dict[str, float] = field(default_factory=dict)  # 对各线的亲和度
    
    # 动态属性
    occupancy: float = 0.0             # 当前占用率
    resonance_history: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.line_affinity:
            # 默认对所有线有中等亲和度
            self.line_affinity = {line: 0.5 for line in ELEVEN_LINES}
    
    def get_gua(self) -> CircuitPhase:
        """获取当前节点对应的八卦相位"""
        index = int((self.phase_angle % (2 * math.pi)) / (math.pi / 4)) % 8
        return list(CircuitPhase)[index]


# ═══════════════════════════════════════════════════════════════
# 小周天 - 单线内部自循环
# ═══════════════════════════════════════════════════════════════

@dataclass
class SmallZhouTian:
    """
    小周天 - 单线内部的自循环
    
    小周天模型:
        - 属于某一条特定线
        - 周期: T_small (相对短)
        - 频率: ω_small = 2π/T_small
        - 节点: 线内的关键状态
        - 循环: 节点间按固定顺序流转
    
    示例 - ucif2线的小周天:
        Lean声明 → 类型检查 → 证明搜索 → 证明发现 → 债务生成 → 债务清偿 → Lean声明
    
    谐波结构:
        小周天本身可以包含更小的微周天
        形成谐波级数: ω_micro = n * ω_small
    """
    id: str = field(default_factory=lambda: "SZT-" + str(uuid.uuid4())[:6])
    line_name: str = ""
    name: str = ""
    
    # 循环参数
    period: float = 1.0                # 周期 (相对时间单位)
    frequency: float = 1.0             # 频率
    phase: float = 0.0                 # 当前相位
    amplitude: float = 1.0             # 振幅
    
    # 节点
    nodes: Dict[str, CircuitNode] = field(default_factory=dict)
    node_order: List[str] = field(default_factory=list)  # 节点流转顺序
    
    # 当前状态
    current_node_id: Optional[str] = None
    cycle_count: int = 0               # 已完成循环数
    
    # 谐波
    harmonics: List[SmallZhouTian] = field(default_factory=list)  # 子谐波
    parent_harmonic: Optional[SmallZhouTian] = None
    harmonic_number: int = 1           # 谐波次数 (1=基波)
    
    # 统计
    node_visit_counts: Dict[str, int] = field(default_factory=dict)
    transition_counts: Dict[Tuple[str, str], int] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.name:
            self.name = f"{self.line_name}-small-zhou"
        self.frequency = 2 * math.pi / self.period if self.period > 0 else 1.0
    
    def add_node(self, node: CircuitNode, position: Optional[int] = None) -> str:
        """添加节点到循环"""
        self.nodes[node.id] = node
        if position is not None:
            self.node_order.insert(position, node.id)
        else:
            self.node_order.append(node.id)
        
        if self.current_node_id is None:
            self.current_node_id = node.id
        
        return node.id
    
    def tick(self, dt: float = 0.1) -> Dict[str, Any]:
        """
        小周天推进一个时间步
        
        Args:
            dt: 时间增量
            
        Returns:
            本次tick的事件记录
        """
        events = {
            "phase_before": self.phase,
            "phase_after": 0,
            "node_before": self.current_node_id,
            "node_after": None,
            "cycle_completed": False,
            "harmonic_events": []
        }
        
        # 更新相位
        self.phase += self.frequency * dt
        if self.phase >= 2 * math.pi:
            self.phase -= 2 * math.pi
            self.cycle_count += 1
            events["cycle_completed"] = True
        
        events["phase_after"] = self.phase
        
        # 确定当前节点
        if self.node_order:
            node_index = int((self.phase / (2 * math.pi)) * len(self.node_order)) % len(self.node_order)
            new_node_id = self.node_order[node_index]
            
            if new_node_id != self.current_node_id:
                # 节点转移
                if self.current_node_id and new_node_id:
                    transition = (self.current_node_id, new_node_id)
                    self.transition_counts[transition] = self.transition_counts.get(transition, 0) + 1
                
                self.current_node_id = new_node_id
            
            events["node_after"] = self.current_node_id
            
            # 更新节点访问计数
            if self.current_node_id:
                self.node_visit_counts[self.current_node_id] = \
                    self.node_visit_counts.get(self.current_node_id, 0) + 1
                
                node = self.nodes.get(self.current_node_id)
                if node:
                    node.occupancy += 0.1
        
        # 推进谐波
        for harmonic in self.harmonics:
            h_events = harmonic.tick(dt)
            if h_events["cycle_completed"]:
                events["harmonic_events"].append({
                    "harmonic_number": harmonic.harmonic_number,
                    "event": "cycle_completed"
                })
        
        return events
    
    def add_harmonic(self, n: int) -> SmallZhouTian:
        """
        添加第n次谐波
        谐波频率 = n * 基频
        """
        harmonic = SmallZhouTian(
            line_name=self.line_name,
            name=f"{self.name}-H{n}",
            period=self.period / n,
            amplitude=self.amplitude / n,
            parent_harmonic=self,
            harmonic_number=n
        )
        
        # 复制节点但调整相位
        for i, node_id in enumerate(self.node_order):
            orig_node = self.nodes[node_id]
            new_phase = (orig_node.phase_angle * n) % (2 * math.pi)
            new_node = CircuitNode(
                name=f"{orig_node.name}-H{n}",
                phase_angle=new_phase,
                energy_level=orig_node.energy_level / n,
                line_affinity=orig_node.line_affinity.copy()
            )
            harmonic.add_node(new_node)
        
        self.harmonics.append(harmonic)
        return harmonic
    
    def get_current_gua(self) -> CircuitPhase:
        """获取当前八卦相位"""
        if self.current_node_id and self.current_node_id in self.nodes:
            return self.nodes[self.current_node_id].get_gua()
        return CircuitPhase.QIAN
    
    def get_cycle_efficiency(self) -> float:
        """计算循环效率"""
        if not self.node_visit_counts:
            return 0.0
        
        # 理想情况下各节点访问均匀
        total_visits = sum(self.node_visit_counts.values())
        num_nodes = len(self.node_order)
        
        if num_nodes == 0 or total_visits == 0:
            return 0.0
        
        ideal_per_node = total_visits / num_nodes
        variance = sum(
            (self.node_visit_counts.get(nid, 0) - ideal_per_node) ** 2
            for nid in self.node_order
        ) / num_nodes
        
        # 效率 = 1 - 归一化方差
        efficiency = max(0, 1 - variance / (ideal_per_node ** 2 + 1e-10))
        return efficiency
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "line": self.line_name,
            "name": self.name,
            "period": self.period,
            "frequency": self.frequency,
            "phase": self.phase,
            "cycle_count": self.cycle_count,
            "node_count": len(self.nodes),
            "harmonics": [h.harmonic_number for h in self.harmonics],
            "efficiency": self.get_cycle_efficiency(),
            "current_gua": self.get_current_gua().cn_name if self.get_current_gua() else None
        }


# ═══════════════════════════════════════════════════════════════
# 大周天 - 跨线大循环
# ═══════════════════════════════════════════════════════════════

@dataclass
class GreatZhouTian:
    """
    大周天 - 跨线的大循环
    
    大周天模型:
        - 跨越所有11条线
        - 周期: T_great >> T_small
        - 频率: ω_great = 2π/T_great
        - 结构: 场→圈→环→层→网→塔→云→场
    
    大周天阶段:
        1. 场 (Field):    分布式存在，无中心
        2. 圈 (Ring):     自组织环，局部结构
        3. 环 (Loop):     闭合循环，能量守恒
        4. 层 (Layer):    分层结构，同频聚集
        5. 网 (Web):      网络连接，跨层关联
        6. 塔 (Tower):    层级涌现，向上构建
        7. 云 (Cloud):    分布式场，超越中心
        8. → 回到场 (完成循环)
    
    与小周天的关系:
        - 能量关系: 小周天向大周天输送能量
        - 结构关系: 大周天为小周天提供框架
        - 谐波关系: ω_small = n * ω_great
    """
    id: str = field(default_factory=lambda: "GZT-" + str(uuid.uuid4())[:6])
    name: str = "OMNI-Great-ZhouTian"
    
    # 循环参数
    period: float = 11.0               # 周期 = 11 (对应11条线)
    frequency: float = 1.0             # 基频
    phase: float = 0.0                 # 当前相位
    amplitude: float = 1.0             # 振幅
    
    # 大周天阶段 (八卦对应)
    stages: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"name": "场", "symbol": "☰", "gua": CircuitPhase.QIAN, "line_focus": "omni", 
         "description": "分布式存在，无中心"},
        {"name": "圈", "symbol": "☱", "gua": CircuitPhase.DUI, "line_focus": "consensus",
         "description": "自组织环，局部结构"},
        {"name": "环", "symbol": "☲", "gua": CircuitPhase.LI, "line_focus": "sib0",
         "description": "闭合循环，能量守恒"},
        {"name": "层", "symbol": "☳", "gua": CircuitPhase.ZHEN, "line_focus": "reflect",
         "description": "分层结构，同频聚集"},
        {"name": "网", "symbol": "☴", "gua": CircuitPhase.XUN, "line_focus": "weave",
         "description": "网络连接，跨层关联"},
        {"name": "塔", "symbol": "☵", "gua": CircuitPhase.KAN, "line_focus": "fctn",
         "description": "层级涌现，向上构建"},
        {"name": "云", "symbol": "☶", "gua": CircuitPhase.GEN, "line_focus": "surge",
         "description": "分布式场，超越中心"},
        {"name": "归", "symbol": "☷", "gua": CircuitPhase.KUN, "line_focus": "ucif2",
         "description": "回归本源，承载一切"},
    ])
    
    # 子周天注册表
    small_zhou_tians: Dict[str, SmallZhouTian] = field(default_factory=dict)
    
    # 线能量分布
    line_energies: Dict[str, float] = field(default_factory=lambda: {line: 0.5 for line in ELEVEN_LINES})
    
    # 当前状态
    current_stage_index: int = 0
    cycle_count: int = 0
    
    # 统计
    stage_durations: Dict[int, List[float]] = field(default_factory=lambda: defaultdict(list))
    energy_flows: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        self.frequency = 2 * math.pi / self.period if self.period > 0 else 1.0
    
    def register_small_zhou(self, szt: SmallZhouTian) -> bool:
        """注册一个小周天"""
        if szt.line_name not in ELEVEN_LINES:
            return False
        
        self.small_zhou_tians[szt.line_name] = szt
        
        # 设置谐波关系: 小周天频率 = n * 大周天频率
        # n 根据线在周期中的位置确定
        line_index = ELEVEN_LINES.index(szt.line_name)
        harmonic_n = line_index + 1
        szt.frequency = self.frequency * harmonic_n
        szt.period = self.period / harmonic_n
        
        return True
    
    def tick(self, dt: float = 0.1) -> Dict[str, Any]:
        """
        大周天推进一个时间步
        """
        events = {
            "stage_before": self.current_stage_index,
            "stage_after": self.current_stage_index,
            "cycle_completed": False,
            "energy_flows": [],
            "small_zhou_updates": []
        }
        
        # 更新相位
        self.phase += self.frequency * dt
        if self.phase >= 2 * math.pi:
            self.phase -= 2 * math.pi
            self.cycle_count += 1
            events["cycle_completed"] = True
        
        # 确定当前阶段
        new_stage = int((self.phase / (2 * math.pi)) * len(self.stages)) % len(self.stages)
        
        if new_stage != self.current_stage_index:
            # 阶段转移 - 能量重新分配
            old_stage = self.current_stage_index
            self.current_stage_index = new_stage
            events["stage_after"] = new_stage
            
            # 能量从旧阶段流向新阶段
            flow = self._transfer_energy(old_stage, new_stage)
            events["energy_flows"].append(flow)
        
        # 更新各线能量
        self._update_line_energies()
        
        # 推进各小周天
        for line_name, szt in self.small_zhou_tians.items():
            szt_events = szt.tick(dt)
            
            # 小周天完成循环时向大周天贡献能量
            if szt_events["cycle_completed"]:
                contribution = szt.amplitude * 0.1
                self.amplitude = min(2.0, self.amplitude + contribution)
                events["small_zhou_updates"].append({
                    "line": line_name,
                    "contribution": contribution,
                    "szt_cycles": szt.cycle_count
                })
        
        # 大周天向小周天提供结构反馈
        self._feedback_to_small()
        
        return events
    
    def _transfer_energy(self, from_stage: int, to_stage: int) -> Dict[str, Any]:
        """阶段间能量转移"""
        transfer_amount = self.amplitude * 0.2
        
        # 从旧阶段关联的线抽取
        from_line = self.stages[from_stage]["line_focus"]
        self.line_energies[from_line] = max(0, self.line_energies[from_line] - transfer_amount * 0.5)
        
        # 向新阶段关联的线注入
        to_line = self.stages[to_stage]["line_focus"]
        self.line_energies[to_line] = min(2.0, self.line_energies[to_line] + transfer_amount)
        
        return {
            "from_stage": self.stages[from_stage]["name"],
            "to_stage": self.stages[to_stage]["name"],
            "from_line": from_line,
            "to_line": to_line,
            "amount": transfer_amount
        }
    
    def _update_line_energies(self):
        """更新各线能量分布"""
        # 根据大周天相位计算各线的"照射"能量
        for i, line in enumerate(ELEVEN_LINES):
            # 该线在当前相位的能量 = 振幅 * cos(相位差)
            line_phase = (2 * math.pi * i / len(ELEVEN_LINES))
            phase_diff = abs(self.phase - line_phase)
            illumination = self.amplitude * math.cos(phase_diff / 2)
            
            # 平滑更新
            self.line_energies[line] = 0.9 * self.line_energies[line] + 0.1 * (0.5 + illumination)
    
    def _feedback_to_small(self):
        """大周天向小周天的结构反馈"""
        current_stage = self.stages[self.current_stage_index]
        focus_line = current_stage["line_focus"]
        
        # 当前聚焦的线获得结构支持
        if focus_line in self.small_zhou_tians:
            szt = self.small_zhou_tians[focus_line]
            szt.amplitude = min(1.5, szt.amplitude + 0.05)
    
    def get_harmonic_relationship(self, line_name: str) -> Dict[str, Any]:
        """
        获取某条线与大周天的谐波关系
        """
        if line_name not in ELEVEN_LINES:
            return {}
        
        line_index = ELEVEN_LINES.index(line_name)
        harmonic_n = line_index + 1
        
        # 理论频率比
        frequency_ratio = harmonic_n
        
        # 实际频率比 (如果有注册的小周天)
        actual_ratio = None
        if line_name in self.small_zhou_tians:
            szt = self.small_zhou_tians[line_name]
            actual_ratio = szt.frequency / self.frequency if self.frequency > 0 else None
        
        # 相位关系
        line_phase = (2 * math.pi * line_index / len(ELEVEN_LINES))
        phase_diff = (self.phase - line_phase) % (2 * math.pi)
        
        return {
            "line": line_name,
            "line_index": line_index,
            "harmonic_number": harmonic_n,
            "frequency_ratio_theory": frequency_ratio,
            "frequency_ratio_actual": actual_ratio,
            "phase_difference": phase_diff,
            "is_phase_locked": abs(phase_diff - 0) < 0.5 or abs(phase_diff - 2 * math.pi) < 0.5,
            "energy": self.line_energies.get(line_name, 0)
        }
    
    def get_all_harmonics(self) -> List[Dict[str, Any]]:
        """获取所有线的谐波关系"""
        return [self.get_harmonic_relationship(line) for line in ELEVEN_LINES]
    
    def get_resonance_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        获取11×11的共振矩阵
        矩阵元素 M[i][j] = 线i与线j的共振强度
        """
        matrix = {}
        for line_i in ELEVEN_LINES:
            matrix[line_i] = {}
            info_i = self.get_harmonic_relationship(line_i)
            
            for line_j in ELEVEN_LINES:
                info_j = self.get_harmonic_relationship(line_j)
                
                # 共振强度 = 能量乘积 * 相位相干
                energy_product = info_i["energy"] * info_j["energy"]
                phase_coherence = math.cos(abs(info_i["phase_difference"] - info_j["phase_difference"]) / 2)
                
                # 谐波关系增强共振
                h_ratio = info_i["harmonic_number"] / info_j["harmonic_number"] if info_j["harmonic_number"] > 0 else 1
                is_harmonic = abs(h_ratio - round(h_ratio)) < 0.1
                harmonic_bonus = 1.5 if is_harmonic else 1.0
                
                matrix[line_i][line_j] = energy_product * phase_coherence * harmonic_bonus
        
        return matrix
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "period": self.period,
            "frequency": self.frequency,
            "phase": self.phase,
            "cycle_count": self.cycle_count,
            "current_stage": self.stages[self.current_stage_index]["name"] if self.stages else None,
            "current_gua": self.stages[self.current_stage_index]["gua"].cn_name if self.stages else None,
            "registered_small_zhous": list(self.small_zhou_tians.keys()),
            "line_energies": self.line_energies,
            "total_small_cycles": sum(szt.cycle_count for szt in self.small_zhou_tians.values())
        }


# ═══════════════════════════════════════════════════════════════
# 周天协调器 - 管理所有周天
# ═══════════════════════════════════════════════════════════════

@dataclass
class ZhouTianCoordinator:
    """
    周天协调器
    
    管理:
        - 11条线的11个小周天
        - 1个大周天
        - 各周天间的谐波关系
        - 能量流动与平衡
    """
    id: str = field(default_factory=lambda: "ZTC-" + str(uuid.uuid4())[:6])
    
    # 大周天
    great_zhou: GreatZhouTian = field(default_factory=GreatZhouTian)
    
    # 小周天 (按线名索引)
    small_zhous: Dict[str, SmallZhouTian] = field(default_factory=dict)
    
    # 运行状态
    is_running: bool = False
    global_time: float = 0.0
    tick_count: int = 0
    
    # 观察记录
    observation_log: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        self._init_default_small_zhous()
    
    def _init_default_small_zhous(self):
        """初始化各线的默认小周天"""
        # ucif2: Lean→证明→债务→Lean
        ucif2_szt = SmallZhouTian(
            line_name="ucif2",
            name="ucif2-proof-debt-cycle",
            period=4.0
        )
        ucif2_szt.add_node(CircuitNode(name="Lean声明", phase_angle=0, energy_level=0.8, 
                                       line_affinity={"ucif2": 1.0}))
        ucif2_szt.add_node(CircuitNode(name="类型检查", phase_angle=math.pi/2, energy_level=0.6,
                                       line_affinity={"ucif2": 0.9}))
        ucif2_szt.add_node(CircuitNode(name="证明搜索", phase_angle=math.pi, energy_level=0.4,
                                       line_affinity={"ucif2": 0.8}))
        ucif2_szt.add_node(CircuitNode(name="债务生成", phase_angle=3*math.pi/2, energy_level=0.5,
                                       line_affinity={"ucif2": 0.7, "debt": 0.5}))
        self.small_zhous["ucif2"] = ucif2_szt
        self.great_zhou.register_small_zhou(ucif2_szt)
        
        # sib0: Sensation→Integration→Action→Reflection→Sensation
        sib0_szt = SmallZhouTian(
            line_name="sib0",
            name="sib0-SI-cycle",
            period=4.0
        )
        sib0_szt.add_node(CircuitNode(name="Sensation", phase_angle=0, energy_level=0.7,
                                      line_affinity={"sib0": 1.0}))
        sib0_szt.add_node(CircuitNode(name="Integration", phase_angle=math.pi/2, energy_level=0.8,
                                      line_affinity={"sib0": 0.95}))
        sib0_szt.add_node(CircuitNode(name="Action", phase_angle=math.pi, energy_level=0.6,
                                      line_affinity={"sib0": 0.9}))
        sib0_szt.add_node(CircuitNode(name="Reflection", phase_angle=3*math.pi/2, energy_level=0.5,
                                      line_affinity={"sib0": 0.85, "reflect": 0.4}))
        self.small_zhous["sib0"] = sib0_szt
        self.great_zhou.register_small_zhou(sib0_szt)
        
        # weave: 收集→编织→验证→发布→收集
        weave_szt = SmallZhouTian(
            line_name="weave",
            name="weave-knowledge-cycle",
            period=5.0
        )
        weave_szt.add_node(CircuitNode(name="收集", phase_angle=0, energy_level=0.6))
        weave_szt.add_node(CircuitNode(name="编织", phase_angle=2*math.pi/5, energy_level=0.8))
        weave_szt.add_node(CircuitNode(name="验证", phase_angle=4*math.pi/5, energy_level=0.5))
        weave_szt.add_node(CircuitNode(name="发布", phase_angle=6*math.pi/5, energy_level=0.7))
        weave_szt.add_node(CircuitNode(name="反馈", phase_angle=8*math.pi/5, energy_level=0.4))
        self.small_zhous["weave"] = weave_szt
        self.great_zhou.register_small_zhou(weave_szt)
        
        # fctn: 输入→转换→输出→桥接→输入
        fctn_szt = SmallZhouTian(
            line_name="fctn",
            name="fctn-bridge-cycle",
            period=4.0
        )
        fctn_szt.add_node(CircuitNode(name="输入", phase_angle=0, energy_level=0.6))
        fctn_szt.add_node(CircuitNode(name="转换", phase_angle=math.pi/2, energy_level=0.7))
        fctn_szt.add_node(CircuitNode(name="输出", phase_angle=math.pi, energy_level=0.6))
        fctn_szt.add_node(CircuitNode(name="桥接", phase_angle=3*math.pi/2, energy_level=0.8))
        self.small_zhous["fctn"] = fctn_szt
        self.great_zhou.register_small_zhou(fctn_szt)
        
        # consensus: 提议→讨论→投票→共识→执行→提议
        consensus_szt = SmallZhouTian(
            line_name="consensus",
            name="consensus-protocol-cycle",
            period=5.0
        )
        consensus_szt.add_node(CircuitNode(name="提议", phase_angle=0, energy_level=0.7))
        consensus_szt.add_node(CircuitNode(name="讨论", phase_angle=2*math.pi/5, energy_level=0.8))
        consensus_szt.add_node(CircuitNode(name="投票", phase_angle=4*math.pi/5, energy_level=0.6))
        consensus_szt.add_node(CircuitNode(name="共识", phase_angle=6*math.pi/5, energy_level=0.9))
        consensus_szt.add_node(CircuitNode(name="执行", phase_angle=8*math.pi/5, energy_level=0.5))
        self.small_zhous["consensus"] = consensus_szt
        self.great_zhou.register_small_zhou(consensus_szt)
        
        # surge: 平静→积累→爆发→衰减→平静
        surge_szt = SmallZhouTian(
            line_name="surge",
            name="surge-wave-cycle",
            period=4.0
        )
        surge_szt.add_node(CircuitNode(name="平静", phase_angle=0, energy_level=0.3))
        surge_szt.add_node(CircuitNode(name="积累", phase_angle=math.pi/2, energy_level=0.6))
        surge_szt.add_node(CircuitNode(name="爆发", phase_angle=math.pi, energy_level=1.0))
        surge_szt.add_node(CircuitNode(name="衰减", phase_angle=3*math.pi/2, energy_level=0.5))
        self.small_zhous["surge"] = surge_szt
        self.great_zhou.register_small_zhou(surge_szt)
        
        # debt: 借贷→使用→偿还→清零→借贷
        debt_szt = SmallZhouTian(
            line_name="debt",
            name="debt-obligation-cycle",
            period=4.0
        )
        debt_szt.add_node(CircuitNode(name="借贷", phase_angle=0, energy_level=0.7))
        debt_szt.add_node(CircuitNode(name="使用", phase_angle=math.pi/2, energy_level=0.5))
        debt_szt.add_node(CircuitNode(name="偿还", phase_angle=math.pi, energy_level=0.6))
        debt_szt.add_node(CircuitNode(name="清零", phase_angle=3*math.pi/2, energy_level=0.4))
        self.small_zhous["debt"] = debt_szt
        self.great_zhou.register_small_zhou(debt_szt)
        
        # bridge: 识别→翻译→验证→连接→识别
        bridge_szt = SmallZhouTian(
            line_name="bridge",
            name="bridge-translation-cycle",
            period=4.0
        )
        bridge_szt.add_node(CircuitNode(name="识别", phase_angle=0, energy_level=0.7))
        bridge_szt.add_node(CircuitNode(name="翻译", phase_angle=math.pi/2, energy_level=0.8))
        bridge_szt.add_node(CircuitNode(name="验证", phase_angle=math.pi, energy_level=0.5))
        bridge_szt.add_node(CircuitNode(name="连接", phase_angle=3*math.pi/2, energy_level=0.9))
        self.small_zhous["bridge"] = bridge_szt
        self.great_zhou.register_small_zhou(bridge_szt)
        
        # reflect: 观察→分析→判断→调整→观察
        reflect_szt = SmallZhouTian(
            line_name="reflect",
            name="reflect-meta-cycle",
            period=4.0
        )
        reflect_szt.add_node(CircuitNode(name="观察", phase_angle=0, energy_level=0.6))
        reflect_szt.add_node(CircuitNode(name="分析", phase_angle=math.pi/2, energy_level=0.7))
        reflect_szt.add_node(CircuitNode(name="判断", phase_angle=math.pi, energy_level=0.5))
        reflect_szt.add_node(CircuitNode(name="调整", phase_angle=3*math.pi/2, energy_level=0.6))
        self.small_zhous["reflect"] = reflect_szt
        self.great_zhou.register_small_zhou(reflect_szt)
        
        # wildq: 提问→探索→发现→深化→提问
        wildq_szt = SmallZhouTian(
            line_name="wildq",
            name="wildq-inquiry-cycle",
            period=5.0
        )
        wildq_szt.add_node(CircuitNode(name="提问", phase_angle=0, energy_level=0.9))
        wildq_szt.add_node(CircuitNode(name="探索", phase_angle=2*math.pi/5, energy_level=0.7))
        wildq_szt.add_node(CircuitNode(name="发现", phase_angle=4*math.pi/5, energy_level=0.8))
        wildq_szt.add_node(CircuitNode(name="深化", phase_angle=6*math.pi/5, energy_level=0.5))
        wildq_szt.add_node(CircuitNode(name="新问题", phase_angle=8*math.pi/5, energy_level=0.6))
        self.small_zhous["wildq"] = wildq_szt
        self.great_zhou.register_small_zhou(wildq_szt)
        
        # omni: 感知→编排→执行→同步→感知
        omni_szt = SmallZhouTian(
            line_name="omni",
            name="omni-hub-cycle",
            period=4.0
        )
        omni_szt.add_node(CircuitNode(name="感知", phase_angle=0, energy_level=0.8))
        omni_szt.add_node(CircuitNode(name="编排", phase_angle=math.pi/2, energy_level=0.9))
        omni_szt.add_node(CircuitNode(name="执行", phase_angle=math.pi, energy_level=0.7))
        omni_szt.add_node(CircuitNode(name="同步", phase_angle=3*math.pi/2, energy_level=0.8))
        self.small_zhous["omni"] = omni_szt
        self.great_zhou.register_small_zhou(omni_szt)
    
    def tick(self, dt: float = 0.1) -> Dict[str, Any]:
        """全局tick"""
        self.global_time += dt
        self.tick_count += 1
        
        # 推进大周天
        great_events = self.great_zhou.tick(dt)
        
        # 推进各小周天 (已由大周天在推进时调用)
        # 但我们需要确保所有小周天都被推进
        for line, szt in self.small_zhous.items():
            if line not in self.great_zhou.small_zhou_tians:
                szt.tick(dt)
        
        # 记录观察
        if self.tick_count % 10 == 0:
            self.observation_log.append({
                "tick": self.tick_count,
                "time": self.global_time,
                "great_stage": self.great_zhou.stages[self.great_zhou.current_stage_index]["name"],
                "line_energies": self.great_zhou.line_energies.copy(),
                "great_amplitude": self.great_zhou.amplitude
            })
        
        return {
            "tick": self.tick_count,
            "time": self.global_time,
            "great_events": great_events,
            "great_stage": self.great_zhou.stages[self.great_zhou.current_stage_index]["name"]
        }
    
    def run_cycles(self, n: int, dt: float = 0.1) -> List[Dict[str, Any]]:
        """运行n个周期"""
        results = []
        for _ in range(n):
            result = self.tick(dt)
            results.append(result)
        return results
    
    def get_harmonic_table(self) -> Dict[str, Any]:
        """
        获取谐波关系表
        """
        return {
            "great_zhou": {
                "period": self.great_zhou.period,
                "frequency": self.great_zhou.frequency,
                "phase": self.great_zhou.phase
            },
            "harmonics": {
                line: self.great_zhou.get_harmonic_relationship(line)
                for line in ELEVEN_LINES
            }
        }
    
    def get_energy_flow_report(self) -> Dict[str, Any]:
        """获取能量流动报告"""
        return {
            "global_time": self.global_time,
            "tick_count": self.tick_count,
            "line_energies": self.great_zhou.line_energies,
            "great_amplitude": self.great_zhou.amplitude,
            "great_cycle_count": self.great_zhou.cycle_count,
            "small_cycle_counts": {
                line: szt.cycle_count for line, szt in self.small_zhous.items()
            },
            "resonance_matrix": self.great_zhou.get_resonance_matrix()
        }
    
    def get_synchronization_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        locked_count = 0
        statuses = {}
        
        for line in ELEVEN_LINES:
            rel = self.great_zhou.get_harmonic_relationship(line)
            is_locked = rel.get("is_phase_locked", False)
            if is_locked:
                locked_count += 1
            statuses[line] = {
                "phase_locked": is_locked,
                "phase_diff": rel.get("phase_difference", 0),
                "energy": rel.get("energy", 0)
            }
        
        return {
            "total_lines": len(ELEVEN_LINES),
            "locked_lines": locked_count,
            "sync_ratio": locked_count / len(ELEVEN_LINES),
            "statuses": statuses
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "global_time": self.global_time,
            "tick_count": self.tick_count,
            "great_zhou": self.great_zhou.to_dict(),
            "small_zhous": {line: szt.to_dict() for line, szt in self.small_zhous.items()},
            "sync_status": self.get_synchronization_status()
        }


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def create_coordinator() -> ZhouTianCoordinator:
    """创建默认协调器"""
    return ZhouTianCoordinator()


def analyze_harmonics(coordinator: ZhouTianCoordinator) -> str:
    """分析谐波关系，返回可读报告"""
    report = []
    report.append("=" * 60)
    report.append("周天谐波分析报告")
    report.append("=" * 60)
    
    gz = coordinator.great_zhou
    report.append(f"\n大周天: 周期={gz.period:.2f}, 频率={gz.frequency:.4f}, 相位={gz.phase:.4f}")
    report.append(f"当前阶段: {gz.stages[gz.current_stage_index]['name']}")
    
    report.append("\n各线小周天谐波关系:")
    report.append("-" * 60)
    report.append(f"{'线名':<12} {'谐波次数':<8} {'周期':<8} {'频率比':<8} {'相位差':<8} {'能量':<8} {'锁定':<6}")
    report.append("-" * 60)
    
    for line in ELEVEN_LINES:
        rel = gz.get_harmonic_relationship(line)
        szt = coordinator.small_zhous.get(line)
        report.append(
            f"{line:<12} {rel['harmonic_number']:<8} "
            f"{szt.period if szt else 'N/A':<8.2f} "
            f"{rel['frequency_ratio_theory']:<8.1f} "
            f"{rel['phase_difference']:<8.4f} "
            f"{rel['energy']:<8.4f} "
            f"{'✓' if rel['is_phase_locked'] else '✗':<6}"
        )
    
    report.append("\n" + "=" * 60)
    return "\n".join(report)


# ═══════════════════════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v12 - 周天循环系统")
    print("=" * 70)
    
    # 创建协调器
    ztc = create_coordinator()
    print(f"\n[1] 创建周天协调器: {ztc.id}")
    print(f"    已注册小周天: {list(ztc.small_zhous.keys())}")
    
    # 打印谐波分析
    print("\n[2] 初始谐波分析:")
    print(analyze_harmonics(ztc))
    
    # 运行多个周期
    print("\n[3] 运行100个tick...")
    for i in range(100):
        ztc.tick(dt=0.1)
    
    print(f"    全局时间: {ztc.global_time:.1f}")
    print(f"    大周天周期: {ztc.great_zhou.cycle_count}")
    print(f"    当前阶段: {ztc.great_zhou.stages[ztc.great_zhou.current_stage_index]['name']}")
    
    # 同步状态
    print("\n[4] 同步状态:")
    sync = ztc.get_synchronization_status()
    print(f"    锁定线数: {sync['locked_lines']}/{sync['total_lines']}")
    print(f"    同步率: {sync['sync_ratio']:.1%}")
    
    # 能量流动报告
    print("\n[5] 能量分布:")
    energies = ztc.great_zhou.line_energies
    for line, energy in sorted(energies.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(energy * 20)
        print(f"    {line:<12} {energy:.4f} {bar}")
    
    # 共振矩阵 (简化)
    print("\n[6] 共振矩阵 (前3条线):")
    matrix = ztc.great_zhou.get_resonance_matrix()
    top3 = ELEVEN_LINES[:3]
    for li in top3:
        row = [f"{matrix[li][lj]:.2f}" for lj in top3]
        print(f"    {li}: {row}")
    
    print("\n" + "=" * 70)
    print("周天循环系统演示完成")
    print("=" * 70)
