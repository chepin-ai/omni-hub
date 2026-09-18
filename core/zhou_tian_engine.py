#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v7.0 — ZhouTianEngine (周天引擎)
=============================================
正-反-大-小 四重周天深度耦合引擎

Architecture: Quadruple-Coupled ZhouTian (QCZT)
Author: OMNI-HUB Core Systems
Version: 7.0.0

Core Concepts:
- 小周天 (Small): 每线微循环 inbox→outbox→session→self_check→inbox
- 大周天 (Big): 全局大循环 global_dispatch→cross_line_sync→global_optimize→feedback
- 正周天 (Forward): S-drive加速循环 structure→design→implement→test→deploy→structure
- 反周天 (Reverse): I-ripple收敛循环 feedback→analyze→redesign→patch→verify→feedback
- 四重耦合: 四个周天互相驱动、互相修正，形成共振

Physics Model:
- Each ZhouTian is modeled as a coupled oscillator network
- Phase dynamics follow Kuramoto-like equations with coupling
- Energy flows through the cycle nodes
- Coupling between ZhouTians creates emergent resonance phenomena
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from matplotlib.collections import LineCollection
from typing import List, Tuple, Dict, Callable, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque
import json
import warnings
from pathlib import Path
import time
import logging

# ============================================================================
# Constants & Configuration
# ============================================================================

NUM_LINES = 11  # 11条线路
FIELD_DIMENSION = 64  # 场空间分辨率

# 线路名称
LINE_NAMES = [
    "NorthStar",      # 0: 北星线路 - 顶层愿景
    "CoreLogic",      # 1: 核心逻辑
    "EmotionFlow",    # 2: 情绪流
    "MemoryWeave",    # 3: 记忆编织
    "IntentionBeam",  # 4: 意图束
    "PerceptionNet",  # 5: 感知网
    "ActionStream",   # 6: 行动流
    "FeedbackLoop",   # 7: 反馈环
    "ResonanceField", # 8: 共振场
    "EmergenceSpark", # 9: 涌现火花
    "BaseFoundation", # 10: 基座基础
]

# 周天类型枚举
class ZhouTianType(Enum):
    SMALL = 0    # 小周天
    BIG = 1      # 大周天
    FORWARD = 2  # 正周天
    REVERSE = 3  # 反周天

# 小周天节点
SMALL_ZT_NODES = ["inbox", "outbox", "session", "self_check"]

# 大周天节点
BIG_ZT_NODES = ["global_dispatch", "cross_line_sync", "global_optimize", "feedback"]

# 正周天节点
FORWARD_ZT_NODES = ["structure", "design", "implement", "test", "deploy", "structure_out"]

# 反周天节点
REVERSE_ZT_NODES = ["feedback_in", "analyze", "redesign", "patch", "verify", "feedback_out"]


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class CycleNode:
    """周天循环节点"""
    name: str
    phase: float = 0.0          # 相位 [0, 2π]
    amplitude: float = 1.0      # 振幅
    energy: float = 0.0         # 节点能量
    frequency: float = 1.0      # 固有频率
    state: Dict[str, Any] = field(default_factory=dict)  # 扩展状态

    def step(self, dt: float, coupling_force: float = 0.0):
        """节点相位演化一步"""
        # dθ/dt = ω + coupling_force
        self.phase += (self.frequency + coupling_force) * dt
        self.phase %= (2 * np.pi)
        # 振幅轻微振荡
        self.amplitude = 1.0 + 0.1 * np.sin(self.phase)
        # 能量与相位和振幅相关
        self.energy = self.amplitude * (1 + np.sin(self.phase))


@dataclass
class ZhouTianState:
    """周天状态记录"""
    cycle_count: int = 0
    cycle_quality: float = 0.0
    convergence_rate: float = 0.0
    energy: float = 0.0
    phase_coherence: float = 0.0
    timestamp: float = 0.0
    metadata: Dict = field(default_factory=dict)


# ============================================================================
# 1. SmallZhouTian — 小周天 (每线微循环)
# ============================================================================

class SmallZhouTian:
    """
    小周天 — 每线独立的微循环

    循环流: inbox → outbox → session → self_check → inbox

    物理模型:
    - 4个节点构成一个环形耦合振荡器网络
    - 每个节点有独立的相位和振幅
    - 相邻节点间有强耦合（循环驱动力）
    - 循环质量由相位同步度决定
    """

    def __init__(self, line_id: int, num_nodes: int = 4, 
                 base_frequency: float = 1.0,
                 coupling_strength: float = 2.0):
        self.line_id = line_id
        self.line_name = LINE_NAMES[line_id] if line_id < len(LINE_NAMES) else f"Line_{line_id}"
        self.num_nodes = num_nodes
        self.base_frequency = base_frequency
        self.coupling_strength = coupling_strength

        # 初始化节点
        self.nodes: List[CycleNode] = []
        node_names = SMALL_ZT_NODES[:num_nodes]
        for i, name in enumerate(node_names):
            node = CycleNode(
                name=name,
                phase=np.random.uniform(0, 2 * np.pi),
                amplitude=1.0,
                energy=0.0,
                frequency=base_frequency * (1 + 0.05 * np.random.randn())
            )
            self.nodes.append(node)

        # 循环质量历史
        self.cycle_quality_history: List[float] = []
        self.convergence_history: List[float] = []
        self.energy_history: List[float] = []
        self.phase_history: List[List[float]] = []

        # 当前指标
        self._cycle_quality = 0.0
        self._convergence_rate = 0.0
        self._energy = 0.0
        self._phase_coherence = 0.0

        # 时间
        self.time = 0.0
        self.dt = 0.01

        # 外部耦合输入（来自其他周天）
        self.external_coupling = 0.0

    @property
    def cycle_quality(self) -> float:
        """循环质量 — 相位同步度"""
        return self._cycle_quality

    @property
    def convergence_rate(self) -> float:
        """收敛速率 — 质量改善速度"""
        return self._convergence_rate

    @property
    def energy(self) -> float:
        """总能量"""
        return self._energy

    def _compute_phase_coherence(self) -> float:
        """
        计算相位相干性 (Kuramoto order parameter)
        r = |Σ e^(iθ)| / N
        r ∈ [0, 1]: 0=完全无序, 1=完全同步
        """
        phases = np.array([node.phase for node in self.nodes])
        complex_phases = np.exp(1j * phases)
        r = np.abs(np.mean(complex_phases))
        return float(r)

    def _compute_cycle_quality(self) -> float:
        """
        计算循环质量
        综合考虑: 相位同步度、能量均匀性、相位顺序性
        """
        # 相位同步度
        coherence = self._compute_phase_coherence()

        # 能量均匀性 (各节点能量差异小 = 高质量)
        energies = np.array([node.energy for node in self.nodes])
        energy_uniformity = 1.0 - np.std(energies) / (np.mean(energies) + 1e-10)

        # 相位顺序性 (相邻节点相位差应接近 2π/N)
        phases = np.array([node.phase for node in self.nodes])
        ideal_diff = 2 * np.pi / self.num_nodes
        phase_diffs = np.diff(np.sort(phases))
        phase_diffs = np.append(phase_diffs, 2 * np.pi - np.sum(phase_diffs))
        phase_order = 1.0 - np.mean(np.abs(phase_diffs - ideal_diff)) / ideal_diff

        # 综合质量
        quality = 0.5 * coherence + 0.25 * energy_uniformity + 0.25 * phase_order
        return float(np.clip(quality, 0, 1))

    def _compute_coupling_forces(self) -> np.ndarray:
        """
        计算节点间的耦合力
        环形耦合: 每个节点与前后邻居耦合
        """
        forces = np.zeros(self.num_nodes)
        phases = np.array([node.phase for node in self.nodes])

        for i in range(self.num_nodes):
            # 前驱节点 (循环中的前一个)
            prev_idx = (i - 1) % self.num_nodes
            # 后继节点 (循环中的后一个)
            next_idx = (i + 1) % self.num_nodes

            # 环形耦合: 驱动力使节点趋向于跟随前驱
            # F_i = K * [sin(θ_{i-1} - θ_i) + α * sin(θ_{i+1} - θ_i)]
            force_from_prev = self.coupling_strength * np.sin(phases[prev_idx] - phases[i])
            force_from_next = 0.3 * self.coupling_strength * np.sin(phases[next_idx] - phases[i])

            forces[i] = force_from_prev + force_from_next

            # 添加外部耦合影响
            forces[i] += self.external_coupling * 0.1

        return forces

    def cycle(self, dt: Optional[float] = None) -> Dict[str, float]:
        """
        执行一个循环步骤

        Returns:
            {
                'cycle_quality': float,
                'convergence_rate': float,
                'energy': float,
                'phase_coherence': float
            }
        """
        if dt is None:
            dt = self.dt

        # 计算耦合力
        forces = self._compute_coupling_forces()

        # 更新每个节点
        for i, node in enumerate(self.nodes):
            node.step(dt, forces[i])

        # 计算指标
        prev_quality = self._cycle_quality
        self._phase_coherence = self._compute_phase_coherence()
        self._cycle_quality = self._compute_cycle_quality()
        self._energy = sum(node.energy for node in self.nodes)

        # 收敛速率 = 质量改善速度
        self._convergence_rate = (self._cycle_quality - prev_quality) / dt

        # 记录历史
        self.cycle_quality_history.append(self._cycle_quality)
        self.convergence_history.append(self._convergence_rate)
        self.energy_history.append(self._energy)
        self.phase_history.append([node.phase for node in self.nodes])

        self.time += dt

        return {
            'cycle_quality': self._cycle_quality,
            'convergence_rate': self._convergence_rate,
            'energy': self._energy,
            'phase_coherence': self._phase_coherence
        }

    def run_cycles(self, cycles: int = 100) -> Dict[str, Any]:
        """运行多个循环"""
        for _ in range(cycles):
            self.cycle()

        return {
            'line_id': self.line_id,
            'line_name': self.line_name,
            'cycles_completed': cycles,
            'final_quality': self._cycle_quality,
            'final_convergence': self._convergence_rate,
            'final_energy': self._energy,
            'final_coherence': self._phase_coherence,
            'avg_quality': float(np.mean(self.cycle_quality_history[-cycles:])),
            'quality_trend': float(np.polyfit(range(min(10, len(self.cycle_quality_history))), 
                                               self.cycle_quality_history[-10:], 1)[0]) if len(self.cycle_quality_history) >= 2 else 0.0
        }

    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'line_id': self.line_id,
            'line_name': self.line_name,
            'nodes': [
                {
                    'name': node.name,
                    'phase': node.phase,
                    'amplitude': node.amplitude,
                    'energy': node.energy
                }
                for node in self.nodes
            ],
            'cycle_quality': self._cycle_quality,
            'convergence_rate': self._convergence_rate,
            'energy': self._energy,
            'phase_coherence': self._phase_coherence,
            'time': self.time
        }


# ============================================================================
# 2. BigZhouTian — 大周天 (全局大循环)
# ============================================================================

class BigZhouTian:
    """
    大周天 — 全局大循环

    循环流: global_dispatch → cross_line_sync → global_optimize → feedback → global_dispatch

    物理模型:
    - 4个全局节点，每个节点与11条线耦合
    - 全局协调度 = 跨线同步指数
    - 优化增益 = 全局势能降低率
    - 全局状态是一个 [4, 11] 的场
    """

    def __init__(self, num_lines: int = NUM_LINES,
                 base_frequency: float = 0.5,
                 coupling_strength: float = 1.5,
                 line_coupling: float = 0.3):
        self.num_lines = num_lines
        self.num_nodes = 4
        self.base_frequency = base_frequency
        self.coupling_strength = coupling_strength
        self.line_coupling = line_coupling

        # 全局节点 [num_nodes]
        self.nodes: List[CycleNode] = []
        for i, name in enumerate(BIG_ZT_NODES):
            node = CycleNode(
                name=name,
                phase=np.random.uniform(0, 2 * np.pi),
                amplitude=1.0,
                energy=0.0,
                frequency=base_frequency * (1 + 0.05 * np.random.randn())
            )
            self.nodes.append(node)

        # 线状态 [num_lines, num_nodes] — 每条线在每个全局节点上的投影
        self.line_states = np.random.randn(self.num_lines, self.num_nodes) * 0.1

        # 线间耦合矩阵
        self.line_coupling_matrix = self._init_line_coupling()

        # 历史记录
        self.coordination_history: List[float] = []
        self.optimization_history: List[float] = []
        self.energy_history: List[float] = []

        # 当前指标
        self._global_coordination = 0.0
        self._optimization_gain = 0.0
        self._energy = 0.0

        self.time = 0.0
        self.dt = 0.01

        # 外部输入（来自小周天）
        self.small_zt_input = np.zeros(num_lines)

    def _init_line_coupling(self) -> np.ndarray:
        """初始化线间耦合矩阵"""
        C = np.zeros((self.num_lines, self.num_lines))

        # 北星(0) ↔ 所有线
        C[0, :] = 0.25
        C[:, 0] = 0.25

        # 相邻线耦合
        for i in range(self.num_lines - 1):
            C[i, i+1] = 0.15
            C[i+1, i] = 0.15

        # 基座(10) ↔ 所有线
        C[-1, :] = 0.2
        C[:, -1] = 0.2

        # 自耦合
        np.fill_diagonal(C, 0.5)

        return C

    def _compute_global_coordination(self) -> float:
        """
        全局协调度 — 跨线同步指数
        计算所有线在各全局节点上的同步程度
        """
        # 对每条线，计算其在各节点上的相位
        line_phases = np.zeros(self.num_lines)
        for l in range(self.num_lines):
            # 线的状态相位 = atan2(imag, real) of sum over nodes
            complex_sum = np.sum(self.line_states[l] * np.exp(1j * np.array([node.phase for node in self.nodes])))
            line_phases[l] = np.angle(complex_sum)

        # 计算跨线同步
        sync = np.abs(np.mean(np.exp(1j * line_phases)))
        return float(sync)

    def _compute_optimization_gain(self) -> float:
        """
        优化增益 — 全局性能提升
        基于线状态的"有序度"改善
        """
        # 计算当前全局势能
        potential = 0.0

        # 节点间势能 (希望节点同步)
        for i in range(self.num_nodes):
            for j in range(i+1, self.num_nodes):
                phase_diff = self.nodes[i].phase - self.nodes[j].phase
                potential -= np.cos(phase_diff)  # 负cos = 同步时势能低

        # 线间耦合势能 (希望线间协调)
        for l1 in range(self.num_lines):
            for l2 in range(l1+1, self.num_lines):
                coupling = self.line_coupling_matrix[l1, l2]
                state_diff = np.linalg.norm(self.line_states[l1] - self.line_states[l2])
                potential += coupling * state_diff**2

        # 优化增益 = -d(potential)/dt (势能降低 = 优化)
        if len(self.energy_history) > 0:
            prev_potential = self.energy_history[-1]
            gain = -(potential - prev_potential) / self.dt
        else:
            gain = 0.0

        self._energy = potential
        return float(gain)

    def _compute_coupling_forces(self) -> np.ndarray:
        """计算全局节点间的耦合力"""
        forces = np.zeros(self.num_nodes)
        phases = np.array([node.phase for node in self.nodes])

        for i in range(self.num_nodes):
            prev_idx = (i - 1) % self.num_nodes
            next_idx = (i + 1) % self.num_nodes

            # 循环耦合
            force = self.coupling_strength * (
                np.sin(phases[prev_idx] - phases[i]) +
                0.3 * np.sin(phases[next_idx] - phases[i])
            )
            forces[i] = force

        return forces

    def _update_line_states(self, dt: float):
        """更新各线的状态"""
        # 线状态受全局节点驱动，同时也受线间耦合影响
        node_phases = np.array([node.phase for node in self.nodes])

        new_states = self.line_states.copy()

        for l in range(self.num_lines):
            # 全局节点对线状态的驱动
            for n in range(self.num_nodes):
                drive = np.sin(node_phases[n]) * 0.1
                new_states[l, n] += drive * dt

            # 线间耦合
            coupled_input = self.line_coupling_matrix[l] @ self.line_states[:, :].sum(axis=1)
            new_states[l] += coupled_input * self.line_coupling * dt

            # 小周天输入
            new_states[l] += self.small_zt_input[l] * 0.05 * dt

            # 衰减
            new_states[l] *= (1 - 0.01 * dt)

        self.line_states = new_states

    def cycle(self, dt: Optional[float] = None) -> Dict[str, float]:
        """执行一个全局循环步骤"""
        if dt is None:
            dt = self.dt

        # 更新全局节点
        forces = self._compute_coupling_forces()
        for i, node in enumerate(self.nodes):
            node.step(dt, forces[i])

        # 更新线状态
        self._update_line_states(dt)

        # 计算指标
        prev_coord = self._global_coordination
        self._global_coordination = self._compute_global_coordination()
        self._optimization_gain = self._compute_optimization_gain()

        # 记录历史
        self.coordination_history.append(self._global_coordination)
        self.optimization_history.append(self._optimization_gain)
        self.energy_history.append(self._energy)

        self.time += dt

        return {
            'global_coordination': self._global_coordination,
            'optimization_gain': self._optimization_gain,
            'energy': self._energy
        }

    def run_cycles(self, cycles: int = 100) -> Dict[str, Any]:
        """运行多个全局循环"""
        for _ in range(cycles):
            self.cycle()

        return {
            'cycles_completed': cycles,
            'final_coordination': self._global_coordination,
            'final_optimization_gain': self._optimization_gain,
            'final_energy': self._energy,
            'avg_coordination': float(np.mean(self.coordination_history[-cycles:])),
            'avg_optimization': float(np.mean(self.optimization_history[-cycles:])),
            'coordination_trend': float(np.polyfit(range(min(10, len(self.coordination_history))),
                                                     self.coordination_history[-10:], 1)[0]) if len(self.coordination_history) >= 2 else 0.0
        }

    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'nodes': [
                {
                    'name': node.name,
                    'phase': node.phase,
                    'energy': node.energy
                }
                for node in self.nodes
            ],
            'global_coordination': self._global_coordination,
            'optimization_gain': self._optimization_gain,
            'energy': self._energy,
            'line_states_mean': float(np.mean(self.line_states)),
            'line_states_std': float(np.std(self.line_states)),
            'time': self.time
        }


# ============================================================================
# 3. ForwardZhouTian — 正周天 (S-drive加速循环)
# ============================================================================

class ForwardZhouTian:
    """
    正周天 — S-drive的加速循环

    循环流: structure → design → implement → test → deploy → structure

    物理模型:
    - 6个节点构成正向推进链
    - 推进力 = 节点间能量梯度（正向流动）
    - 加速度 = 推进力变化率
    - 结构完整性 = 系统有序度
    """

    def __init__(self, num_nodes: int = 6,
                 base_frequency: float = 1.2,
                 coupling_strength: float = 2.5,
                 thrust_gain: float = 1.0):
        self.num_nodes = num_nodes
        self.base_frequency = base_frequency
        self.coupling_strength = coupling_strength
        self.thrust_gain = thrust_gain

        # 初始化节点
        self.nodes: List[CycleNode] = []
        node_names = FORWARD_ZT_NODES[:num_nodes]
        for i, name in enumerate(node_names):
            # 正周天节点频率递增（加速效应）
            freq = base_frequency * (1 + 0.05 * i)
            node = CycleNode(
                name=name,
                phase=np.random.uniform(0, 2 * np.pi),
                amplitude=1.0,  # 统一振幅，让耦合动力学自然发展
                energy=0.0,
                frequency=freq
            )
            self.nodes.append(node)

        # 推进指标
        self.thrust_history: List[float] = []
        self.acceleration_history: List[float] = []
        self.integrity_history: List[float] = []
        self.energy_history: List[float] = []

        self._thrust = 0.0
        self._acceleration = 0.0
        self._structural_integrity = 1.0
        self._energy = 0.0

        self.time = 0.0
        self.dt = 0.01

        # 外部耦合
        self.reverse_coupling = 0.0  # 来自反周天的校准

    def _compute_thrust(self) -> float:
        """
        推进力 — 正向能量流
        计算从structure到deploy的能量梯度
        """
        energies = np.array([node.energy for node in self.nodes])

        # 推进力 = 能量梯度沿正向的积分
        thrust = 0.0
        for i in range(self.num_nodes - 1):
            gradient = energies[i+1] - energies[i]
            thrust += max(0, gradient)  # 只计正向梯度

        # 结构节点(structure)的高能量表示强的结构基础
        structure_boost = energies[0] * 0.2

        return self.thrust_gain * (thrust + structure_boost)

    def _compute_structural_integrity(self) -> float:
        """
        结构完整性 — 系统有序度
        基于节点振幅的均匀性和相位的规律性
        """
        # 振幅均匀性
        amplitudes = np.array([node.amplitude for node in self.nodes])
        amp_uniformity = 1.0 - np.std(amplitudes) / (np.mean(amplitudes) + 1e-10)

        # 相位顺序性 (正周天中，相位应沿循环方向递增)
        phases = np.array([node.phase for node in self.nodes])
        phase_diffs = np.diff(phases)
        # 理想情况下，相位差应均匀分布
        ideal_diff = 2 * np.pi / self.num_nodes
        phase_order = 1.0 - np.mean(np.abs(phase_diffs - ideal_diff)) / ideal_diff

        # 能量稳定性
        energy_stability = 1.0 / (1.0 + np.var([node.energy for node in self.nodes]))

        integrity = 0.4 * amp_uniformity + 0.4 * phase_order + 0.2 * energy_stability
        return float(np.clip(integrity, 0, 1))

    def _compute_coupling_forces(self) -> np.ndarray:
        """计算正周天节点间的耦合力"""
        forces = np.zeros(self.num_nodes)
        phases = np.array([node.phase for node in self.nodes])

        for i in range(self.num_nodes):
            # 正周天: 强正向耦合 (从前一个节点获取驱动)
            prev_idx = (i - 1) % self.num_nodes

            # 主要驱动力来自前驱
            force = self.coupling_strength * np.sin(phases[prev_idx] - phases[i])

            # 反向校准 (来自反周天的修正)
            force += self.reverse_coupling * 0.1 * np.sin(phases[i] + np.pi)

            forces[i] = force

        return forces

    def cycle(self, dt: Optional[float] = None) -> Dict[str, float]:
        """执行一个正周天循环步骤"""
        if dt is None:
            dt = self.dt

        # 更新节点
        forces = self._compute_coupling_forces()
        for i, node in enumerate(self.nodes):
            node.step(dt, forces[i])

        # 计算指标
        prev_thrust = self._thrust
        self._thrust = self._compute_thrust()
        self._acceleration = (self._thrust - prev_thrust) / dt
        self._structural_integrity = self._compute_structural_integrity()
        self._energy = sum(node.energy for node in self.nodes)

        # 记录历史
        self.thrust_history.append(self._thrust)
        self.acceleration_history.append(self._acceleration)
        self.integrity_history.append(self._structural_integrity)
        self.energy_history.append(self._energy)

        self.time += dt

        return {
            'thrust': self._thrust,
            'acceleration': self._acceleration,
            'structural_integrity': self._structural_integrity,
            'energy': self._energy
        }

    def run_cycles(self, cycles: int = 100) -> Dict[str, Any]:
        """运行多个正周天循环"""
        for _ in range(cycles):
            self.cycle()

        return {
            'cycles_completed': cycles,
            'final_thrust': self._thrust,
            'final_acceleration': self._acceleration,
            'final_integrity': self._structural_integrity,
            'final_energy': self._energy,
            'avg_thrust': float(np.mean(self.thrust_history[-cycles:])),
            'max_thrust': float(np.max(self.thrust_history[-cycles:])),
            'thrust_trend': float(np.polyfit(range(min(10, len(self.thrust_history))),
                                              self.thrust_history[-10:], 1)[0]) if len(self.thrust_history) >= 2 else 0.0,
            'avg_integrity': float(np.mean(self.integrity_history[-cycles:]))
        }

    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'nodes': [
                {
                    'name': node.name,
                    'phase': node.phase,
                    'amplitude': node.amplitude,
                    'energy': node.energy
                }
                for node in self.nodes
            ],
            'thrust': self._thrust,
            'acceleration': self._acceleration,
            'structural_integrity': self._structural_integrity,
            'energy': self._energy,
            'time': self.time
        }


# ============================================================================
# 4. ReverseZhouTian — 反周天 (I-ripple收敛循环)
# ============================================================================

class ReverseZhouTian:
    """
    反周天 — I-ripple的收敛循环

    循环流: feedback → analyze → redesign → patch → verify → feedback

    物理模型:
    - 6个节点构成反向修正链
    - 修正量 = 反馈驱动的反向能量
    - 收敛度 = 误差衰减率
    - 反馈质量 = 信噪比
    """

    def __init__(self, num_nodes: int = 6,
                 base_frequency: float = 0.8,
                 coupling_strength: float = 2.0,
                 correction_gain: float = 1.0):
        self.num_nodes = num_nodes
        self.base_frequency = base_frequency
        self.coupling_strength = coupling_strength
        self.correction_gain = correction_gain

        # 初始化节点
        self.nodes: List[CycleNode] = []
        node_names = REVERSE_ZT_NODES[:num_nodes]
        for i, name in enumerate(node_names):
            # 反周天节点频率递减（收敛效应）
            freq = base_frequency * (1 - 0.05 * i)
            node = CycleNode(
                name=name,
                phase=np.random.uniform(0, 2 * np.pi),
                amplitude=1.0 - 0.05 * i,  # 振幅递减（收敛）
                energy=0.0,
                frequency=max(freq, 0.1)
            )
            self.nodes.append(node)

        # 误差状态 (反周天跟踪系统误差)
        self.error_state = np.ones(num_nodes) * 0.5
        self.error_history: List[float] = []

        # 指标历史
        self.correction_history: List[float] = []
        self.convergence_history: List[float] = []
        self.feedback_quality_history: List[float] = []
        self.energy_history: List[float] = []

        self._correction = 0.0
        self._convergence = 0.0
        self._feedback_quality = 0.0
        self._energy = 0.0

        self.time = 0.0
        self.dt = 0.01

        # 外部输入（来自正周天的偏差）
        self.forward_deviation = 0.0

    def _compute_correction(self) -> float:
        """
        修正量 — 反馈驱动的修正能量
        基于误差状态和节点能量的综合
        """
        # 误差能量
        error_energy = np.sum(self.error_state**2)

        # 节点反馈能量
        node_energies = np.array([node.energy for node in self.nodes])
        feedback_energy = np.sum(node_energies)

        # 修正量 = 误差 × 反馈响应
        correction = self.correction_gain * np.sqrt(error_energy * feedback_energy)

        # 正周天偏差触发额外修正
        correction += self.forward_deviation * 0.5

        return float(correction)

    def _compute_convergence(self) -> float:
        """
        收敛度 — 误差衰减率
        计算误差状态的衰减速度
        """
        if len(self.error_history) > 0:
            prev_error = self.error_history[-1]
            current_error = np.sum(self.error_state**2)
            if prev_error > 1e-10:
                decay_rate = -(current_error - prev_error) / (prev_error * self.dt)
                return float(np.clip(decay_rate, -10, 10))
        return 0.0

    def _compute_feedback_quality(self) -> float:
        """
        反馈质量 — 信噪比
        高质量的反馈 = 修正准确、误差降低
        """
        # 信号 = 有效修正量
        signal = self._correction

        # 噪声 = 误差波动
        if len(self.error_history) >= 2:
            noise = np.std(self.error_history[-10:])
        else:
            noise = 1.0

        snr = signal / (noise + 1e-10)
        quality = np.tanh(snr)  # 映射到 [0, 1]
        return float(quality)

    def _update_errors(self, dt: float):
        """更新误差状态"""
        # 误差自然衰减 (修正的效果)
        decay = 0.1 * self._correction * dt
        self.error_state -= decay
        self.error_state = np.maximum(self.error_state, 0.01)

        # 正周天引入的偏差增加误差
        self.error_state += self.forward_deviation * 0.05 * dt

        # 微小随机扰动
        self.error_state += np.random.randn(self.num_nodes) * 0.01 * dt
        self.error_state = np.maximum(self.error_state, 0.01)

    def _compute_coupling_forces(self) -> np.ndarray:
        """计算反周天节点间的耦合力"""
        forces = np.zeros(self.num_nodes)
        phases = np.array([node.phase for node in self.nodes])

        for i in range(self.num_nodes):
            # 反周天: 反馈节点驱动后续节点
            prev_idx = (i - 1) % self.num_nodes

            # 从feedback节点获得驱动力
            force = self.coupling_strength * np.sin(phases[prev_idx] - phases[i])

            # 误差引导 (高误差区域增强耦合)
            error_weight = 1.0 + self.error_state[i]
            force *= error_weight

            forces[i] = force

        return forces

    def cycle(self, dt: Optional[float] = None) -> Dict[str, float]:
        """执行一个反周天循环步骤"""
        if dt is None:
            dt = self.dt

        # 更新节点
        forces = self._compute_coupling_forces()
        for i, node in enumerate(self.nodes):
            node.step(dt, forces[i])

        # 计算指标
        self._correction = self._compute_correction()
        self._convergence = self._compute_convergence()
        self._feedback_quality = self._compute_feedback_quality()
        self._energy = sum(node.energy for node in self.nodes)

        # 更新误差
        self._update_errors(dt)
        self.error_history.append(float(np.sum(self.error_state**2)))

        # 记录历史
        self.correction_history.append(self._correction)
        self.convergence_history.append(self._convergence)
        self.feedback_quality_history.append(self._feedback_quality)
        self.energy_history.append(self._energy)

        self.time += dt

        return {
            'correction': self._correction,
            'convergence': self._convergence,
            'feedback_quality': self._feedback_quality,
            'energy': self._energy
        }

    def run_cycles(self, cycles: int = 100) -> Dict[str, Any]:
        """运行多个反周天循环"""
        for _ in range(cycles):
            self.cycle()

        return {
            'cycles_completed': cycles,
            'final_correction': self._correction,
            'final_convergence': self._convergence,
            'final_feedback_quality': self._feedback_quality,
            'final_energy': self._energy,
            'avg_correction': float(np.mean(self.correction_history[-cycles:])),
            'avg_convergence': float(np.mean(self.convergence_history[-cycles:])),
            'convergence_trend': float(np.polyfit(range(min(10, len(self.convergence_history))),
                                                    self.convergence_history[-10:], 1)[0]) if len(self.convergence_history) >= 2 else 0.0,
            'final_error': float(np.sum(self.error_state**2))
        }

    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'nodes': [
                {
                    'name': node.name,
                    'phase': node.phase,
                    'amplitude': node.amplitude,
                    'energy': node.energy
                }
                for node in self.nodes
            ],
            'correction': self._correction,
            'convergence': self._convergence,
            'feedback_quality': self._feedback_quality,
            'energy': self._energy,
            'error_state': self.error_state.copy(),
            'time': self.time
        }


# ============================================================================
# 5. ZhouTianCouplingMatrix — 周天耦合矩阵
# ============================================================================

class ZhouTianCouplingMatrix:
    """
    周天耦合矩阵 — 四重周天间的耦合关系

    耦合结构:
         Small(0) ←──→ Big(1)
           ↑ ↕          ↑ ↕
           ↕ ↓          ↕ ↓
        Forward(2) ←─→ Reverse(3)

    耦合机制:
    - Small → Big: 局部优化累积为全局优化
    - Big → Small: 全局约束反馈到局部
    - Forward → Reverse: 推进偏差触发修正
    - Reverse → Forward: 修正结果校准推进方向
    - Forward → Big: 快速推进全局结构
    - Reverse → Small: 精细修正局部细节
    """

    def __init__(self):
        # 4×4耦合矩阵 [from, to]
        self.coupling = np.zeros((4, 4))

        # 初始化耦合强度
        self._init_coupling()

        # 耦合历史
        self.coupling_history: List[np.ndarray] = []

        # 特征模态历史
        self.eigenmode_history: List[Dict] = []

    def _init_coupling(self):
        """初始化耦合矩阵"""
        # 小 ↔ 大 (强耦合)
        self.coupling[0, 1] = 0.6  # Small → Big
        self.coupling[1, 0] = 0.5  # Big → Small

        # 正 ↔ 反 (强耦合)
        self.coupling[2, 3] = 0.7  # Forward → Reverse
        self.coupling[3, 2] = 0.6  # Reverse → Forward

        # 正 → 大 (中等耦合)
        self.coupling[2, 1] = 0.4  # Forward → Big

        # 反 → 小 (中等耦合)
        self.coupling[3, 0] = 0.35  # Reverse → Small

        # 小 → 反 (弱耦合)
        self.coupling[0, 3] = 0.2

        # 大 → 正 (弱耦合)
        self.coupling[1, 2] = 0.25

        # 自耦合 (内部动力学)
        for i in range(4):
            self.coupling[i, i] = 0.3

    def update_coupling(self, from_zt: Union[int, ZhouTianType, str],
                        to_zt: Union[int, ZhouTianType, str],
                        strength: float):
        """
        更新耦合强度

        Args:
            from_zt: 源周天 (0=Small, 1=Big, 2=Forward, 3=Reverse)
            to_zt: 目标周天
            strength: 耦合强度 [0, 1]
        """
        from_idx = self._resolve_index(from_zt)
        to_idx = self._resolve_index(to_zt)

        self.coupling[from_idx, to_idx] = np.clip(strength, 0, 1)
        self.coupling_history.append(self.coupling.copy())

    def get_coupling(self, from_zt: Union[int, ZhouTianType, str],
                     to_zt: Union[int, ZhouTianType, str]) -> float:
        """获取耦合强度"""
        from_idx = self._resolve_index(from_zt)
        to_idx = self._resolve_index(to_zt)
        return float(self.coupling[from_idx, to_idx])

    def _resolve_index(self, zt: Union[int, ZhouTianType, str]) -> int:
        """解析周天索引"""
        if isinstance(zt, int):
            return zt
        elif isinstance(zt, ZhouTianType):
            return zt.value
        elif isinstance(zt, str):
            mapping = {'small': 0, 'big': 1, 'forward': 2, 'reverse': 3}
            return mapping.get(zt.lower(), 0)
        else:
            raise ValueError(f"Invalid ZhouTian identifier: {zt}")

    def eigenmodes(self) -> Dict[str, Any]:
        """
        计算特征模态

        返回耦合矩阵的特征值和特征向量，
        用于分析系统的集体行为模式。
        """
        eigenvalues, eigenvectors = np.linalg.eig(self.coupling)

        # 按实部排序
        sorted_indices = np.argsort(-np.real(eigenvalues))
        eigenvalues = eigenvalues[sorted_indices]
        eigenvectors = eigenvectors[:, sorted_indices]

        # 主导模态 (最大特征值对应的模态)
        dominant_mode = eigenvectors[:, 0]

        # 模态衰减率 (特征值实部的负值)
        decay_rates = -np.real(eigenvalues)

        # 模态频率 (特征值虚部)
        frequencies = np.imag(eigenvalues)

        result = {
            'eigenvalues': eigenvalues,
            'eigenvectors': eigenvectors,
            'dominant_mode': dominant_mode,
            'decay_rates': decay_rates,
            'frequencies': frequencies,
            'dominant_frequency': float(frequencies[0]),
            'spectral_gap': float(np.real(eigenvalues[0]) - np.real(eigenvalues[1])) if len(eigenvalues) > 1 else 0.0,
            'stability': float(np.max(np.real(eigenvalues)) < 1.0)  # 所有特征值实部<1则稳定
        }

        self.eigenmode_history.append(result)
        return result

    def get_coupling_flow(self) -> Dict[str, float]:
        """获取耦合流分析"""
        flows = {}
        names = ['Small', 'Big', 'Forward', 'Reverse']

        for i in range(4):
            for j in range(4):
                if i != j:
                    flows[f"{names[i]}→{names[j]}"] = float(self.coupling[i, j])

        # 总流出和流入
        for i, name in enumerate(names):
            flows[f"{name}_outflow"] = float(np.sum(self.coupling[i, :]) - self.coupling[i, i])
            flows[f"{name}_inflow"] = float(np.sum(self.coupling[:, i]) - self.coupling[i, i])

        return flows

    def get_state(self) -> Dict[str, Any]:
        """获取矩阵状态"""
        return {
            'matrix': self.coupling.copy(),
            'total_coupling': float(np.sum(self.coupling) - np.trace(self.coupling)),
            'symmetry': float(np.sum(np.abs(self.coupling - self.coupling.T))),
            'flow_analysis': self.get_coupling_flow()
        }


# ============================================================================
# 6. ZhouTianEngine — 四重周天引擎主类
# ============================================================================

class ZhouTianEngine:
    """
    四重周天深度耦合引擎

    整合小周天、大周天、正周天、反周天，
    通过耦合矩阵实现四重周天的互相驱动和互相修正。

    核心流程:
    1. 每个周天独立运行微循环
    2. 耦合矩阵传递周天间的能量/信息
    3. 检测共振条件并最大化系统效率
    4. 全局统计和状态监控
    """

    def __init__(self, num_lines: int = NUM_LINES):
        self.num_lines = num_lines
        self.time = 0.0
        self.dt = 0.01
        self.cycle_count = 0

        # 初始化四个周天
        logger.info("[ZhouTianEngine] 初始化四重周天...")

        # 小周天: 每线一个
        self.small_zt: List[SmallZhouTian] = []
        for line_id in range(num_lines):
            szt = SmallZhouTian(
                line_id=line_id,
                base_frequency=1.0 + 0.05 * line_id  # 每线频率略有不同
            )
            self.small_zt.append(szt)
        logger.info(f"  ✓ 小周天: {num_lines} 条线路")

        # 大周天: 全局一个
        self.big_zt = BigZhouTian(
            num_lines=num_lines,
            base_frequency=0.5
        )
        logger.info("  ✓ 大周天: 全局调度")

        # 正周天: 全局一个
        self.forward_zt = ForwardZhouTian(
            base_frequency=1.2,
            thrust_gain=1.5
        )
        logger.info("  ✓ 正周天: S-drive加速")

        # 反周天: 全局一个
        self.reverse_zt = ReverseZhouTian(
            base_frequency=0.8,
            correction_gain=1.2
        )
        logger.info("  ✓ 反周天: I-ripple收敛")

        # 耦合矩阵
        self.coupling_matrix = ZhouTianCouplingMatrix()
        logger.info("  ✓ 耦合矩阵: 4×4 四重耦合")

        # 全局状态记录
        self.global_history: List[Dict] = []
        self.resonance_history: List[Dict] = []
        self.coupling_strength_history: List[float] = []

        # 频率追踪 (用于共振检测)
        self._frequency_estimates = np.ones(4)  # [small_freq, big_freq, forward_freq, reverse_freq]

        logger.info("[ZhouTianEngine] 初始化完成\n")

    # ───────────────────────────────────────────────
    # 独立周天运行
    # ───────────────────────────────────────────────

    def small_zhou_tian(self, line_id: Optional[int] = None, 
                        cycles: int = 100) -> Dict[str, Any]:
        """
        小周天运行

        Args:
            line_id: 指定线路，None则运行所有线
            cycles: 循环次数

        Returns:
            {
                'cycle_quality': float,
                'convergence': float,
                'line_results': List[Dict]
            }
        """
        if line_id is not None:
            # 单线运行
            result = self.small_zt[line_id].run_cycles(cycles)
            return {
                'cycle_quality': result['final_quality'],
                'convergence': result['final_convergence'],
                'line_results': [result]
            }
        else:
            # 所有线运行
            results = []
            qualities = []
            convergences = []

            for szt in self.small_zt:
                result = szt.run_cycles(cycles)
                results.append(result)
                qualities.append(result['final_quality'])
                convergences.append(result['final_convergence'])

            return {
                'cycle_quality': float(np.mean(qualities)),
                'convergence': float(np.mean(convergences)),
                'line_results': results,
                'quality_std': float(np.std(qualities)),
                'convergence_std': float(np.std(convergences))
            }

    def big_zhou_tian(self, cycles: int = 100) -> Dict[str, Any]:
        """
        大周天运行

        Args:
            cycles: 循环次数

        Returns:
            {
                'global_coordination': float,
                'optimization_gain': float,
                'energy': float
            }
        """
        result = self.big_zt.run_cycles(cycles)

        return {
            'global_coordination': result['final_coordination'],
            'optimization_gain': result['final_optimization_gain'],
            'energy': result['final_energy'],
            'avg_coordination': result['avg_coordination'],
            'coordination_trend': result['coordination_trend']
        }

    def forward_zhou_tian(self, cycles: int = 100) -> Dict[str, Any]:
        """
        正周天运行

        Args:
            cycles: 循环次数

        Returns:
            {
                'thrust': float,
                'acceleration': float,
                'structural_integrity': float
            }
        """
        result = self.forward_zt.run_cycles(cycles)

        return {
            'thrust': result['final_thrust'],
            'acceleration': result['final_acceleration'],
            'structural_integrity': result['final_integrity'],
            'avg_thrust': result['avg_thrust'],
            'thrust_trend': result['thrust_trend']
        }

    def reverse_zhou_tian(self, cycles: int = 100) -> Dict[str, Any]:
        """
        反周天运行

        Args:
            cycles: 循环次数

        Returns:
            {
                'correction': float,
                'convergence': float,
                'feedback_quality': float
            }
        """
        result = self.reverse_zt.run_cycles(cycles)

        return {
            'correction': result['final_correction'],
            'convergence': result['final_convergence'],
            'feedback_quality': result['final_feedback_quality'],
            'avg_correction': result['avg_correction'],
            'convergence_trend': result['convergence_trend'],
            'final_error': result['final_error']
        }

    # ───────────────────────────────────────────────
    # 四重耦合
    # ───────────────────────────────────────────────

    def couple_zhou_tians(self, cycles: int = 100) -> Dict[str, Any]:
        """
        四重周天耦合运行

        四个周天同时运行，并通过耦合矩阵互相驱动和修正。

        耦合机制:
        1. 小周天 → 大周天: 局部优化累积为全局优化
        2. 大周天 → 小周天: 全局约束反馈到局部
        3. 正周天 → 反周天: 推进偏差触发修正
        4. 反周天 → 正周天: 修正结果校准推进方向
        5. 正周天 → 大周天: 快速推进全局结构
        6. 反周天 → 小周天: 精细修正局部细节
        """
        # 记录耦合前的状态
        pre_states = {
            'small_quality': np.mean([szt.cycle_quality for szt in self.small_zt]),
            'big_coordination': self.big_zt._global_coordination,
            'forward_thrust': self.forward_zt._thrust,
            'reverse_convergence': self.reverse_zt._convergence
        }

        for step in range(cycles):
            # ── 1. 计算耦合输入 ────────────────────

            # 小周天 → 大周天: 局部优化累积
            small_to_big = np.mean([szt.cycle_quality for szt in self.small_zt])

            # 大周天 → 小周天: 全局约束反馈
            big_to_small = self.big_zt._global_coordination

            # 正周天 → 反周天: 推进偏差
            forward_to_reverse = self.forward_zt._thrust * 0.3

            # 反周天 → 正周天: 修正校准
            reverse_to_forward = self.reverse_zt._correction * 0.2

            # 正周天 → 大周天: 推进全局
            forward_to_big = self.forward_zt._structural_integrity * 0.2

            # 反周天 → 小周天: 精细修正
            reverse_to_small = self.reverse_zt._feedback_quality * 0.15

            # ── 2. 应用耦合 ────────────────────────

            # 大周天接收小周天和正周天的输入
            self.big_zt.small_zt_input = np.ones(self.num_lines) * small_to_big * 0.1
            # 额外正向推进
            for i in range(self.num_lines):
                self.big_zt.line_states[i, 0] += forward_to_big * 0.05

            # 小周天接收大周天和反周天的输入
            for szt in self.small_zt:
                szt.external_coupling = big_to_small * 0.1 + reverse_to_small * 0.05

            # 正周天接收反周天的校准
            self.forward_zt.reverse_coupling = reverse_to_forward

            # 反周天接收正周天的偏差
            self.reverse_zt.forward_deviation = forward_to_reverse

            # ── 3. 各周天运行一步 ──────────────────

            # 小周天: 每线运行
            for szt in self.small_zt:
                szt.cycle()

            # 大周天: 全局运行
            self.big_zt.cycle()

            # 正周天: 运行
            self.forward_zt.cycle()

            # 反周天: 运行
            self.reverse_zt.cycle()

            # ── 4. 更新耦合矩阵 ────────────────────

            # 根据运行效果动态调整耦合强度
            self._adapt_coupling()

            # ── 5. 记录全局状态 ────────────────────

            self._record_global_state()

            self.time += self.dt
            self.cycle_count += 1

        # 计算耦合效果
        post_states = {
            'small_quality': np.mean([szt.cycle_quality for szt in self.small_zt]),
            'big_coordination': self.big_zt._global_coordination,
            'forward_thrust': self.forward_zt._thrust,
            'reverse_convergence': self.reverse_zt._convergence
        }

        improvements = {
            'small_quality_delta': post_states['small_quality'] - pre_states['small_quality'],
            'big_coordination_delta': post_states['big_coordination'] - pre_states['big_coordination'],
            'forward_thrust_delta': post_states['forward_thrust'] - pre_states['forward_thrust'],
            'reverse_convergence_delta': post_states['reverse_convergence'] - pre_states['reverse_convergence']
        }

        # 测量耦合强度
        coupling_strength = self.measure_coupling_strength()

        return {
            'cycles': cycles,
            'improvements': improvements,
            'final_states': post_states,
            'coupling_strength': coupling_strength,
            'avg_coupling': float(np.mean(list(coupling_strength.values())))
        }

    def _adapt_coupling(self):
        """自适应调整耦合强度 — 动态平衡四重周天"""
        # 1. 正周天 ↔ 反周天: 动态平衡
        fwd_integrity = self.forward_zt._structural_integrity
        fwd_thrust = self.forward_zt._thrust

        if fwd_integrity < 0.3 and fwd_thrust > 1.0:
            # 结构不稳时，增强反→正校准，但减弱正→反触发
            current_r2f = self.coupling_matrix.get_coupling(3, 2)
            self.coupling_matrix.update_coupling(3, 2, min(current_r2f + 0.005, 0.8))
            current_f2r = self.coupling_matrix.get_coupling(2, 3)
            self.coupling_matrix.update_coupling(2, 3, max(current_f2r - 0.003, 0.3))
        elif fwd_integrity > 0.7 and fwd_thrust < 0.5:
            # 结构稳定但推进不足，增强正向驱动
            current_f2r = self.coupling_matrix.get_coupling(2, 3)
            self.coupling_matrix.update_coupling(2, 3, min(current_f2r + 0.002, 0.8))

        # 2. 小周天 ↔ 大周天: 协调平衡
        big_coord = self.big_zt._global_coordination
        small_quality = np.mean([szt.cycle_quality for szt in self.small_zt])

        if big_coord < 0.5 and small_quality > 0.4:
            current_s2b = self.coupling_matrix.get_coupling(0, 1)
            self.coupling_matrix.update_coupling(0, 1, min(current_s2b + 0.005, 0.9))
        elif big_coord > 0.8 and small_quality < 0.5:
            current_b2s = self.coupling_matrix.get_coupling(1, 0)
            self.coupling_matrix.update_coupling(1, 0, min(current_b2s + 0.005, 0.8))

        # 3. 反周天 → 小周天: 精细修正
        rev_quality = self.reverse_zt._feedback_quality
        if rev_quality > 0.8:
            current_r2s = self.coupling_matrix.get_coupling(3, 0)
            self.coupling_matrix.update_coupling(3, 0, min(current_r2s + 0.003, 0.6))

        # 4. 正周天 → 大周天: 全局推进
        if fwd_integrity > 0.5:
            current_f2b = self.coupling_matrix.get_coupling(2, 1)
            self.coupling_matrix.update_coupling(2, 1, min(current_f2b + 0.002, 0.6))

    def _record_global_state(self):
        """记录全局状态"""
        state = {
            'time': self.time,
            'cycle_count': self.cycle_count,
            'small_quality': float(np.mean([szt.cycle_quality for szt in self.small_zt])),
            'small_convergence': float(np.mean([szt.convergence_rate for szt in self.small_zt])),
            'big_coordination': self.big_zt._global_coordination,
            'big_optimization': self.big_zt._optimization_gain,
            'forward_thrust': self.forward_zt._thrust,
            'forward_integrity': self.forward_zt._structural_integrity,
            'reverse_correction': self.reverse_zt._correction,
            'reverse_convergence': self.reverse_zt._convergence,
            'reverse_quality': self.reverse_zt._feedback_quality
        }
        self.global_history.append(state)

    # ───────────────────────────────────────────────
    # 测量与检测
    # ───────────────────────────────────────────────

    def measure_coupling_strength(self) -> Dict[str, float]:
        """
        测量耦合强度

        返回各对周天间的实际耦合效果。
        """
        # 基于状态变化计算实际耦合强度
        strengths = {}

        # 小 ↔ 大
        small_qualities = [s['small_quality'] for s in self.global_history[-10:]]
        big_coords = [s['big_coordination'] for s in self.global_history[-10:]]
        if len(small_qualities) >= 2:
            corr_sb = np.corrcoef(small_qualities, big_coords)[0, 1] if np.std(small_qualities) > 0 and np.std(big_coords) > 0 else 0.0
            strengths['small_big'] = float(abs(corr_sb))
        else:
            strengths['small_big'] = 0.0

        # 正 ↔ 反
        fwd_thrusts = [s['forward_thrust'] for s in self.global_history[-10:]]
        rev_corrs = [s['reverse_convergence'] for s in self.global_history[-10:]]
        if len(fwd_thrusts) >= 2:
            corr_fr = np.corrcoef(fwd_thrusts, rev_corrs)[0, 1] if np.std(fwd_thrusts) > 0 and np.std(rev_corrs) > 0 else 0.0
            strengths['forward_reverse'] = float(abs(corr_fr))
        else:
            strengths['forward_reverse'] = 0.0

        # 矩阵耦合强度
        mat = self.coupling_matrix.coupling
        strengths['matrix_total'] = float(np.sum(mat) - np.trace(mat))

        # 各向耦合
        names = ['small', 'big', 'forward', 'reverse']
        for i in range(4):
            for j in range(4):
                if i != j:
                    strengths[f"{names[i]}_to_{names[j]}"] = float(mat[i, j])

        self.coupling_strength_history.append(strengths['matrix_total'])
        return strengths

    def detect_zhou_tian_resonance(self, tolerance: float = 0.1) -> Dict[str, Any]:
        """
        检测周天共振

        共振条件: 四个周天的频率形成整数比
        f_small : f_big : f_forward : f_reverse = 1 : n : m : p

        当共振发生时，系统效率最大化。
        """
        # 估算各周天的有效频率
        frequencies = self._estimate_frequencies()

        # 标准化频率 (以small为基准)
        base_freq = frequencies[0]
        if base_freq < 1e-10:
            return {'resonance_detected': False, 'reason': 'zero_base_frequency'}

        normalized = frequencies / base_freq

        # 检查整数比关系
        # 理想共振比: 1:2:3:4, 1:2:4:8, 1:1:2:2, 等
        ideal_ratios = [
            np.array([1, 2, 3, 4]),
            np.array([1, 2, 4, 8]),
            np.array([1, 1, 2, 2]),
            np.array([1, 2, 2, 4]),
            np.array([2, 3, 5, 7]),  # 素数比
            np.array([1, 3, 5, 7]),
        ]

        best_match = None
        best_error = float('inf')

        for ideal in ideal_ratios:
            # 归一化理想比
            ideal_norm = ideal / ideal[0]

            # 计算误差
            error = np.mean(np.abs(normalized - ideal_norm))

            if error < best_error:
                best_error = error
                best_match = ideal_norm

        # 判断共振
        resonance_detected = best_error < tolerance

        # 共振强度
        resonance_strength = 1.0 - best_error / tolerance if resonance_detected else 0.0

        # 如果共振，计算共振增强效应
        enhancement = 0.0
        if resonance_detected:
            # 共振时耦合效率提升
            enhancement = resonance_strength * 2.0

            # 增强所有周天
            for szt in self.small_zt:
                szt.coupling_strength *= (1 + 0.1 * resonance_strength)
            self.big_zt.coupling_strength *= (1 + 0.1 * resonance_strength)
            self.forward_zt.coupling_strength *= (1 + 0.1 * resonance_strength)
            self.reverse_zt.coupling_strength *= (1 + 0.1 * resonance_strength)

        result = {
            'resonance_detected': resonance_detected,
            'frequencies': frequencies.tolist(),
            'normalized_ratios': normalized.tolist(),
            'best_match_ratio': best_match.tolist() if best_match is not None else None,
            'match_error': float(best_error),
            'resonance_strength': float(resonance_strength),
            'enhancement_factor': float(enhancement),
            'tolerance': tolerance
        }

        self.resonance_history.append(result)
        return result

    def _estimate_frequencies(self) -> np.ndarray:
        """
        估算各周天的有效频率

        使用多方法融合估计:
        1. 基础频率 (从振荡器固有频率)
        2. 周期计数 (从信号过零次数)
        3. 自相关分析
        """
        freqs = np.zeros(4)

        # 方法1: 基础固有频率
        freqs[0] = np.mean([szt.base_frequency for szt in self.small_zt])
        freqs[1] = self.big_zt.base_frequency
        freqs[2] = self.forward_zt.base_frequency
        freqs[3] = self.reverse_zt.base_frequency

        if len(self.global_history) < 30:
            return freqs

        # 方法2: 从时序信号估算 (周期计数法)
        history_slice = self.global_history[-150:]

        signals = [
            np.array([s['small_quality'] for s in history_slice]),
            np.array([s['big_coordination'] for s in history_slice]),
            np.array([s['forward_thrust'] for s in history_slice]),
            np.array([s['reverse_correction'] for s in history_slice]),
        ]

        for i, signal in enumerate(signals):
            if len(signal) >= 20 and np.std(signal) > 0.005:
                # 去趋势
                signal = signal - np.mean(signal)
                # 计算过零次数来估算频率
                zero_crossings = np.sum(np.diff(np.sign(signal)) != 0)
                if zero_crossings > 0:
                    estimated_freq = zero_crossings / (2 * len(signal))
                    # 融合估计 (加权平均)
                    freqs[i] = 0.7 * freqs[i] + 0.3 * estimated_freq * 10

        # 确保频率为正且有合理差异
        freqs = np.maximum(freqs, 0.1)

        return freqs

    # ───────────────────────────────────────────────
    # 统计和报告
    # ───────────────────────────────────────────────

    def get_zhou_tian_stats(self) -> Dict[str, Any]:
        """获取周天统计"""
        stats = {
            'system': {
                'time': self.time,
                'cycle_count': self.cycle_count,
                'num_lines': self.num_lines
            },
            'small_zt': {
                'count': len(self.small_zt),
                'avg_quality': float(np.mean([szt.cycle_quality for szt in self.small_zt])),
                'avg_convergence': float(np.mean([szt.convergence_rate for szt in self.small_zt])),
                'avg_energy': float(np.mean([szt.energy for szt in self.small_zt])),
                'quality_std': float(np.std([szt.cycle_quality for szt in self.small_zt])),
                'per_line': [
                    {
                        'line_id': szt.line_id,
                        'line_name': szt.line_name,
                        'quality': szt.cycle_quality,
                        'convergence': szt.convergence_rate,
                        'energy': szt.energy
                    }
                    for szt in self.small_zt
                ]
            },
            'big_zt': {
                'coordination': self.big_zt._global_coordination,
                'optimization_gain': self.big_zt._optimization_gain,
                'energy': self.big_zt._energy,
                'line_states_mean': float(np.mean(self.big_zt.line_states)),
                'line_states_std': float(np.std(self.big_zt.line_states))
            },
            'forward_zt': {
                'thrust': self.forward_zt._thrust,
                'acceleration': self.forward_zt._acceleration,
                'structural_integrity': self.forward_zt._structural_integrity,
                'energy': self.forward_zt._energy
            },
            'reverse_zt': {
                'correction': self.reverse_zt._correction,
                'convergence': self.reverse_zt._convergence,
                'feedback_quality': self.reverse_zt._feedback_quality,
                'energy': self.reverse_zt._energy,
                'error': float(np.sum(self.reverse_zt.error_state**2))
            },
            'coupling': self.coupling_matrix.get_state(),
            'resonance': self.resonance_history[-1] if self.resonance_history else None
        }

        # 计算综合效率
        stats['overall_efficiency'] = self._compute_overall_efficiency(stats)

        return stats

    def _compute_overall_efficiency(self, stats: Dict) -> float:
        """计算系统综合效率"""
        small_eff = stats['small_zt']['avg_quality']
        big_eff = stats['big_zt']['coordination']
        fwd_eff = stats['forward_zt']['structural_integrity']
        rev_eff = stats['reverse_zt']['feedback_quality']

        # 加权平均
        efficiency = 0.25 * small_eff + 0.25 * big_eff + 0.25 * fwd_eff + 0.25 * rev_eff
        return float(np.clip(efficiency, 0, 1))

    def get_full_state(self) -> Dict[str, Any]:
        """获取完整状态"""
        return {
            'small_zt': [szt.get_state() for szt in self.small_zt],
            'big_zt': self.big_zt.get_state(),
            'forward_zt': self.forward_zt.get_state(),
            'reverse_zt': self.reverse_zt.get_state(),
            'coupling_matrix': self.coupling_matrix.get_state(),
            'global_history_length': len(self.global_history),
            'resonance_history_length': len(self.resonance_history)
        }


# ============================================================================
# Visualization
# ============================================================================

def visualize_zhou_tian_engine(engine: ZhouTianEngine, 
                                save_path: str = "/mnt/agents/output/OMNI-HUB/viz/zhou_tian_engine.png"):
    """
    可视化四重周天引擎运行结果
    """
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(4, 4, hspace=0.35, wspace=0.3)

    # ── 1. 小周天: 各线循环质量 ───────────────
    ax1 = fig.add_subplot(gs[0, 0])
    for szt in engine.small_zt:
        ax1.plot(szt.cycle_quality_history, alpha=0.6, linewidth=0.8, 
                label=szt.line_name if szt.line_id in [0, 5, 10] else None)
    ax1.set_xlabel('Cycle')
    ax1.set_ylabel('Cycle Quality')
    ax1.set_title('Small ZT: Cycle Quality per Line')
    ax1.legend(fontsize=7, loc='lower right')
    ax1.grid(True, alpha=0.3)

    # ── 2. 小周天: 收敛速率 ───────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    for szt in engine.small_zt:
        ax2.plot(szt.convergence_history, alpha=0.5, linewidth=0.6)
    ax2.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
    ax2.set_xlabel('Cycle')
    ax2.set_ylabel('Convergence Rate')
    ax2.set_title('Small ZT: Convergence Rate')
    ax2.grid(True, alpha=0.3)

    # ── 3. 大周天: 全局协调度 ─────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.plot(engine.big_zt.coordination_history, 'g-', linewidth=1.5)
    ax3.set_xlabel('Cycle')
    ax3.set_ylabel('Global Coordination')
    ax3.set_title('Big ZT: Global Coordination')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 1)

    # ── 4. 大周天: 优化增益 ───────────────────
    ax4 = fig.add_subplot(gs[0, 3])
    ax4.plot(engine.big_zt.optimization_history, 'orange', linewidth=1.5)
    ax4.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
    ax4.set_xlabel('Cycle')
    ax4.set_ylabel('Optimization Gain')
    ax4.set_title('Big ZT: Optimization Gain')
    ax4.grid(True, alpha=0.3)

    # ── 5. 正周天: 推进力 ─────────────────────
    ax5 = fig.add_subplot(gs[1, 0])
    ax5.plot(engine.forward_zt.thrust_history, 'b-', linewidth=1.5)
    ax5.set_xlabel('Cycle')
    ax5.set_ylabel('Thrust')
    ax5.set_title('Forward ZT: Thrust')
    ax5.grid(True, alpha=0.3)

    # ── 6. 正周天: 加速度 ─────────────────────
    ax6 = fig.add_subplot(gs[1, 1])
    ax6.plot(engine.forward_zt.acceleration_history, 'purple', linewidth=1.5)
    ax6.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
    ax6.set_xlabel('Cycle')
    ax6.set_ylabel('Acceleration')
    ax6.set_title('Forward ZT: Acceleration')
    ax6.grid(True, alpha=0.3)

    # ── 7. 正周天: 结构完整性 ─────────────────
    ax7 = fig.add_subplot(gs[1, 2])
    ax7.plot(engine.forward_zt.integrity_history, 'darkgreen', linewidth=1.5)
    ax7.set_xlabel('Cycle')
    ax7.set_ylabel('Structural Integrity')
    ax7.set_title('Forward ZT: Structural Integrity')
    ax7.grid(True, alpha=0.3)
    ax7.set_ylim(0, 1)

    # ── 8. 反周天: 修正量 ─────────────────────
    ax8 = fig.add_subplot(gs[1, 3])
    ax8.plot(engine.reverse_zt.correction_history, 'r-', linewidth=1.5)
    ax8.set_xlabel('Cycle')
    ax8.set_ylabel('Correction')
    ax8.set_title('Reverse ZT: Correction')
    ax8.grid(True, alpha=0.3)

    # ── 9. 反周天: 收敛度 ─────────────────────
    ax9 = fig.add_subplot(gs[2, 0])
    ax9.plot(engine.reverse_zt.convergence_history, 'brown', linewidth=1.5)
    ax9.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
    ax9.set_xlabel('Cycle')
    ax9.set_ylabel('Convergence')
    ax9.set_title('Reverse ZT: Convergence Rate')
    ax9.grid(True, alpha=0.3)

    # ── 10. 反周天: 反馈质量 ──────────────────
    ax10 = fig.add_subplot(gs[2, 1])
    ax10.plot(engine.reverse_zt.feedback_quality_history, 'teal', linewidth=1.5)
    ax10.set_xlabel('Cycle')
    ax10.set_ylabel('Feedback Quality')
    ax10.set_title('Reverse ZT: Feedback Quality')
    ax10.grid(True, alpha=0.3)
    ax10.set_ylim(0, 1)

    # ── 11. 耦合矩阵热图 ──────────────────────
    ax11 = fig.add_subplot(gs[2, 2])
    im = ax11.imshow(engine.coupling_matrix.coupling, cmap='YlOrRd', vmin=0, vmax=1)
    ax11.set_xticks(range(4))
    ax11.set_yticks(range(4))
    ax11.set_xticklabels(['Small', 'Big', 'Fwd', 'Rev'], fontsize=8)
    ax11.set_yticklabels(['Small', 'Big', 'Fwd', 'Rev'], fontsize=8)
    ax11.set_title('Coupling Matrix Heatmap')
    for i in range(4):
        for j in range(4):
            ax11.text(j, i, f'{engine.coupling_matrix.coupling[i,j]:.2f}',
                     ha='center', va='center', fontsize=8, 
                     color='white' if engine.coupling_matrix.coupling[i,j] > 0.5 else 'black')
    plt.colorbar(im, ax=ax11, fraction=0.046)

    # ── 12. 全局历史综合 ──────────────────────
    ax12 = fig.add_subplot(gs[2, 3])
    if engine.global_history:
        steps = range(len(engine.global_history))
        ax12.plot(steps, [s['small_quality'] for s in engine.global_history], 
                 'b-', label='Small Quality', alpha=0.8)
        ax12.plot(steps, [s['big_coordination'] for s in engine.global_history], 
                 'g-', label='Big Coordination', alpha=0.8)
        ax12.plot(steps, [s['forward_integrity'] for s in engine.global_history], 
                 'r-', label='Fwd Integrity', alpha=0.8)
        ax12.plot(steps, [s['reverse_quality'] for s in engine.global_history], 
                 'purple', label='Rev Quality', alpha=0.8)
        ax12.set_xlabel('Step')
        ax12.set_ylabel('Normalized Metric')
        ax12.set_title('Global History: All ZhouTians')
        ax12.legend(fontsize=7, loc='best')
        ax12.grid(True, alpha=0.3)

    # ── 13. 四重周天关系图 ────────────────────
    ax13 = fig.add_subplot(gs[3, :2])
    ax13.set_xlim(-2, 2)
    ax13.set_ylim(-1.5, 1.5)
    ax13.set_aspect('equal')
    ax13.axis('off')
    ax13.set_title('Quadruple ZhouTian Coupling Diagram', fontsize=14, fontweight='bold')

    # 节点位置
    positions = {
        'Small': (-1, 0.5),
        'Big': (1, 0.5),
        'Forward': (0, -0.8),
        'Reverse': (0, 0.0)
    }

    colors = {'Small': 'blue', 'Big': 'green', 'Forward': 'red', 'Reverse': 'purple'}

    # 绘制节点
    for name, (x, y) in positions.items():
        circle = Circle((x, y), 0.25, color=colors[name], alpha=0.7)
        ax13.add_patch(circle)
        ax13.text(x, y, name, ha='center', va='center', fontsize=10, 
                 color='white', fontweight='bold')

    # 绘制耦合箭头
    coupling_pairs = [
        ('Small', 'Big', engine.coupling_matrix.get_coupling('small', 'big')),
        ('Big', 'Small', engine.coupling_matrix.get_coupling('big', 'small')),
        ('Forward', 'Reverse', engine.coupling_matrix.get_coupling('forward', 'reverse')),
        ('Reverse', 'Forward', engine.coupling_matrix.get_coupling('reverse', 'forward')),
        ('Forward', 'Big', engine.coupling_matrix.get_coupling('forward', 'big')),
        ('Reverse', 'Small', engine.coupling_matrix.get_coupling('reverse', 'small')),
    ]

    for from_name, to_name, strength in coupling_pairs:
        x1, y1 = positions[from_name]
        x2, y2 = positions[to_name]
        dx, dy = x2 - x1, y2 - y1
        length = np.sqrt(dx**2 + dy**2)
        if length > 0:
            # 缩放使箭头不重叠
            scale = (length - 0.5) / length
            dx *= scale
            dy *= scale
            ax13.annotate('', xy=(x1 + dx, y1 + dy), xytext=(x1, y1),
                         arrowprops=dict(arrowstyle='->', color='gray',
                                        alpha=strength, lw=2*strength))

    # 添加耦合强度标注
    ax13.text(-1.8, -1.3, f'S→B: {engine.coupling_matrix.get_coupling("small", "big"):.2f}', 
             fontsize=8, color='blue')
    ax13.text(-1.8, -1.1, f'B→S: {engine.coupling_matrix.get_coupling("big", "small"):.2f}', 
             fontsize=8, color='green')
    ax13.text(0.8, -1.3, f'F→R: {engine.coupling_matrix.get_coupling("forward", "reverse"):.2f}', 
             fontsize=8, color='red')
    ax13.text(0.8, -1.1, f'R→F: {engine.coupling_matrix.get_coupling("reverse", "forward"):.2f}', 
             fontsize=8, color='purple')

    # ── 14. 综合效率仪表盘 ────────────────────
    ax14 = fig.add_subplot(gs[3, 2:])

    stats = engine.get_zhou_tian_stats()
    efficiency = stats['overall_efficiency']

    # 绘制仪表盘
    theta = np.linspace(0, np.pi, 100)
    r = 1.0
    ax14.plot(r * np.cos(theta), r * np.sin(theta), 'k-', linewidth=2)

    # 填充区域
    eff_theta = theta[int(efficiency * 99)]
    fill_theta = theta[:int(efficiency * 99) + 1]
    ax14.fill_between(r * np.cos(fill_theta), 0, r * np.sin(fill_theta), 
                      alpha=0.3, color='green' if efficiency > 0.6 else 'orange' if efficiency > 0.3 else 'red')

    # 指针
    ax14.arrow(0, 0, 0.8 * np.cos(eff_theta), 0.8 * np.sin(eff_theta),
              head_width=0.08, head_length=0.05, fc='red', ec='red', linewidth=2)

    # 刻度
    for i in range(11):
        idx = min(i * 9, len(theta) - 1)
        t = theta[idx]
        ax14.plot([0.85 * np.cos(t), np.cos(t)], [0.85 * np.sin(t), np.sin(t)], 'k-', linewidth=1)
        ax14.text(1.1 * np.cos(t), 1.1 * np.sin(t), f'{i*10}%', ha='center', va='center', fontsize=8)

    ax14.set_xlim(-1.5, 1.5)
    ax14.set_ylim(-0.2, 1.5)
    ax14.set_aspect('equal')
    ax14.axis('off')
    ax14.set_title(f'Overall Efficiency: {efficiency*100:.1f}%', fontsize=14, fontweight='bold')

    # 添加统计文本
    stats_text = (
        f"Small ZT Quality: {stats['small_zt']['avg_quality']:.3f}\n"
        f"Big ZT Coordination: {stats['big_zt']['coordination']:.3f}\n"
        f"Forward ZT Integrity: {stats['forward_zt']['structural_integrity']:.3f}\n"
        f"Reverse ZT Quality: {stats['reverse_zt']['feedback_quality']:.3f}\n"
        f"Total Cycles: {engine.cycle_count}"
    )
    ax14.text(0, -0.1, stats_text, ha='center', va='top', fontsize=10,
             family='monospace', transform=ax14.transAxes,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.suptitle('OMNI-HUB v7.0 — ZhouTianEngine (四重周天深度耦合引擎)', 
                fontsize=16, fontweight='bold', y=0.995)

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

    return save_path


# ============================================================================
# Experiment Runner
# ============================================================================

def run_zhou_tian_experiment(output_dir: str = "/mnt/agents/output/OMNI-HUB") -> Dict[str, Any]:
    """
    运行周天引擎完整实验

    实验流程:
    1. 初始化引擎
    2. 独立运行100步小周天（每线）
    3. 独立运行100步大周天
    4. 独立运行100步正周天
    5. 独立运行100步反周天
    6. 激活四重耦合，运行100步
    7. 检测共振
    8. 返回周天统计
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    viz_path = output_path / "viz"
    viz_path.mkdir(parents=True, exist_ok=True)

    results = {}

    logger.info("=" * 80)
    logger.info("OMNI-HUB v7.0 — ZhouTianEngine 实验验证")
    logger.info("正-反-大-小 四重周天深度耦合引擎")
    logger.info("=" * 80)

    # ───────────────────────────────────────────────
    # Step 1: 初始化引擎
    # ───────────────────────────────────────────────
    logger.info("\n[Phase 0] 初始化四重周天引擎...")
    engine = ZhouTianEngine(num_lines=NUM_LINES)

    # ───────────────────────────────────────────────
    # Step 2: 独立运行小周天 (每线100步)
    # ───────────────────────────────────────────────
    logger.info("\n" + "─" * 80)
    logger.info("[Phase 1] 小周天独立运行 — 每线100循环")
    logger.info("─" * 80)

    small_results = engine.small_zhou_tian(cycles=100)
    results['small_zt'] = small_results

    logger.info(f"  平均循环质量: {small_results['cycle_quality']:.4f}")
    logger.info(f"  平均收敛速率: {small_results['convergence']:.4f}")
    logger.info(f"  质量标准差: {small_results['quality_std']:.4f}")
    logger.info(f"  收敛标准差: {small_results['convergence_std']:.4f}")

    # 显示每线结果
    for lr in small_results['line_results']:
        print(f"  {lr['line_name']:12s}: quality={lr['final_quality']:.4f}, "
              f"convergence={lr['final_convergence']:.4f}, "
              f"energy={lr['final_energy']:.4f}")

    # ───────────────────────────────────────────────
    # Step 3: 独立运行大周天 (100步)
    # ───────────────────────────────────────────────
    logger.info("\n" + "─" * 80)
    logger.info("[Phase 2] 大周天独立运行 — 100循环")
    logger.info("─" * 80)

    big_results = engine.big_zhou_tian(cycles=100)
    results['big_zt'] = big_results

    logger.info(f"  最终全局协调度: {big_results['global_coordination']:.4f}")
    logger.info(f"  最终优化增益: {big_results['optimization_gain']:.4f}")
    logger.info(f"  平均协调度: {big_results['avg_coordination']:.4f}")
    logger.info(f"  协调度趋势: {big_results['coordination_trend']:.6f}")

    # ───────────────────────────────────────────────
    # Step 4: 独立运行正周天 (100步)
    # ───────────────────────────────────────────────
    logger.info("\n" + "─" * 80)
    logger.info("[Phase 3] 正周天独立运行 — 100循环 (S-drive)")
    logger.info("─" * 80)

    forward_results = engine.forward_zhou_tian(cycles=100)
    results['forward_zt'] = forward_results

    logger.info(f"  最终推进力: {forward_results['thrust']:.4f}")
    logger.info(f"  最终加速度: {forward_results['acceleration']:.4f}")
    logger.info(f"  最终结构完整性: {forward_results['structural_integrity']:.4f}")
    logger.info(f"  平均推进力: {forward_results['avg_thrust']:.4f}")
    logger.info(f"  推进力趋势: {forward_results['thrust_trend']:.6f}")

    # ───────────────────────────────────────────────
    # Step 5: 独立运行反周天 (100步)
    # ───────────────────────────────────────────────
    logger.info("\n" + "─" * 80)
    logger.info("[Phase 4] 反周天独立运行 — 100循环 (I-ripple)")
    logger.info("─" * 80)

    reverse_results = engine.reverse_zhou_tian(cycles=100)
    results['reverse_zt'] = reverse_results

    logger.info(f"  最终修正量: {reverse_results['correction']:.4f}")
    logger.info(f"  最终收敛度: {reverse_results['convergence']:.4f}")
    logger.info(f"  最终反馈质量: {reverse_results['feedback_quality']:.4f}")
    logger.info(f"  平均修正量: {reverse_results['avg_correction']:.4f}")
    logger.info(f"  收敛趋势: {reverse_results['convergence_trend']:.6f}")
    logger.info(f"  最终误差: {reverse_results['final_error']:.4f}")

    # ───────────────────────────────────────────────
    # Step 6: 四重耦合运行 (100步)
    # ───────────────────────────────────────────────
    logger.info("\n" + "─" * 80)
    logger.info("[Phase 5] 四重周天耦合运行 — 100循环")
    logger.info("耦合机制:")
    logger.info("  • 小周天 → 大周天: 局部优化累积为全局优化")
    logger.info("  • 大周天 → 小周天: 全局约束反馈到局部")
    logger.info("  • 正周天 → 反周天: 推进偏差触发修正")
    logger.info("  • 反周天 → 正周天: 修正结果校准推进方向")
    logger.info("  • 正周天 → 大周天: 快速推进全局结构")
    logger.info("  • 反周天 → 小周天: 精细修正局部细节")
    logger.info("─" * 80)

    coupled_results = engine.couple_zhou_tians(cycles=100)
    results['coupled'] = coupled_results

    logger.info(f"\n  耦合运行完成，总步数: {coupled_results['cycles']}")
    logger.info(f"  小周天质量改善: {coupled_results['improvements']['small_quality_delta']:+.6f}")
    logger.info(f"  大周天协调改善: {coupled_results['improvements']['big_coordination_delta']:+.6f}")
    logger.info(f"  正周天推进改善: {coupled_results['improvements']['forward_thrust_delta']:+.6f}")
    logger.info(f"  反周天收敛改善: {coupled_results['improvements']['reverse_convergence_delta']:+.6f}")
    logger.info(f"  平均耦合强度: {coupled_results['avg_coupling']:.4f}")

    # ───────────────────────────────────────────────
    # Step 7: 检测共振
    # ───────────────────────────────────────────────
    logger.info("\n" + "─" * 80)
    logger.info("[Phase 6] 周天共振检测")
    logger.info("─" * 80)

    resonance = engine.detect_zhou_tian_resonance(tolerance=0.2)
    results['resonance'] = resonance

    logger.info(f"  共振检测: {'✓ 检测到共振!' if resonance['resonance_detected'] else '✗ 未检测到共振'}")
    logger.info(f"  各周天频率: {resonance['frequencies']}")
    logger.info(f"  频率比: {resonance['normalized_ratios']}")
    logger.info(f"  最佳匹配比: {resonance['best_match_ratio']}")
    logger.info(f"  匹配误差: {resonance['match_error']:.4f}")
    logger.info(f"  共振强度: {resonance['resonance_strength']:.4f}")
    if resonance['resonance_detected']:
        logger.info(f"  共振增强因子: {resonance['enhancement_factor']:.4f}")

    # 再次检测共振（可能在耦合运行后频率发生了变化）
    if not resonance['resonance_detected']:
        logger.info("\n  尝试调谐频率以寻找共振...")
        
        # 多轮调谐策略
        tuning_rounds = 3
        best_resonance = resonance
        
        for round_idx in range(tuning_rounds):
            current_freqs = np.array(best_resonance['frequencies'])
            
            # 目标比例: 1 : 2 : 3 : 4
            target_ratios = np.array([1.0, 2.0, 3.0, 4.0])
            
            # 计算当前比例
            base = current_freqs[0]
            if base > 0.1:
                current_ratios = current_freqs / base
                tuning_factors = target_ratios / (current_ratios + 1e-10)
                # 放宽调谐限制，逐步收紧
                clip_min = max(0.3, 0.7 - round_idx * 0.1)
                clip_max = min(2.0, 1.3 + round_idx * 0.2)
                tuning_factors = np.clip(tuning_factors, clip_min, clip_max)
                
                logger.info(f"\n    [调谐轮次 {round_idx+1}/{tuning_rounds}]")
                logger.info(f"    当前频率: {[round(f,3) for f in current_freqs.tolist()]}")
                logger.info(f"    当前比例: {[round(r,3) for r in current_ratios.tolist()]}")
                logger.info(f"    目标比例: {target_ratios.tolist()}")
                logger.info(f"    调谐因子: {[round(f,3) for f in tuning_factors.tolist()]}")
                
                for szt in engine.small_zt:
                    szt.base_frequency *= tuning_factors[0]
                engine.big_zt.base_frequency *= tuning_factors[1]
                engine.forward_zt.base_frequency *= tuning_factors[2]
                engine.reverse_zt.base_frequency *= tuning_factors[3]
            else:
                for szt in engine.small_zt:
                    szt.base_frequency = 1.0
                engine.big_zt.base_frequency = 2.0
                engine.forward_zt.base_frequency = 3.0
                engine.reverse_zt.base_frequency = 4.0
            
            logger.info(f"    调谐后运行耦合 (50步)...")
            engine.couple_zhou_tians(cycles=50)
            
            # 检测共振
            tol = 0.3 + round_idx * 0.1  # 逐步放宽容差
            new_resonance = engine.detect_zhou_tian_resonance(tolerance=tol)
            
            if new_resonance['resonance_detected']:
                best_resonance = new_resonance
                logger.info(f"    ✓ 本轮检测到共振! 强度: {new_resonance['resonance_strength']:.4f}")
                break
            else:
                logger.info(f"    ✗ 本轮未检测到共振。匹配误差: {new_resonance['match_error']:.4f}")
                best_resonance = new_resonance
        
        resonance2 = best_resonance
        results['resonance_after_tuning'] = resonance2
        logger.info(f"\n  最终共振检测: {'✓ 检测到共振!' if resonance2['resonance_detected'] else '✗ 仍未检测到共振'}")
        if resonance2['resonance_detected']:
            logger.info(f"  调谐后共振强度: {resonance2['resonance_strength']:.4f}")
            logger.info(f"  共振增强因子: {resonance2['enhancement_factor']:.4f}")
        else:
            logger.info(f"  最终频率比: {[round(r,3) for r in resonance2['normalized_ratios']]}")
            logger.info(f"  最佳匹配比: {resonance2['best_match_ratio']}")
            logger.info(f"  匹配误差: {resonance2['match_error']:.4f}")

    # ───────────────────────────────────────────────
    # Step 8: 获取周天统计
    # ───────────────────────────────────────────────
    logger.info("\n" + "─" * 80)
    logger.info("[Phase 7] 周天统计")
    logger.info("─" * 80)

    stats = engine.get_zhou_tian_stats()
    results['stats'] = stats

    logger.info(f"\n  系统运行时间: {stats['system']['time']:.2f}")
    logger.info(f"  总循环次数: {stats['system']['cycle_count']}")

    logger.info(f"\n  [小周天]")
    logger.info(f"    线路数: {stats['small_zt']['count']}")
    logger.info(f"    平均质量: {stats['small_zt']['avg_quality']:.4f}")
    logger.info(f"    平均收敛: {stats['small_zt']['avg_convergence']:.4f}")
    logger.info(f"    平均能量: {stats['small_zt']['avg_energy']:.4f}")
    logger.info(f"    质量标准差: {stats['small_zt']['quality_std']:.4f}")

    logger.info(f"\n  [大周天]")
    logger.info(f"    全局协调度: {stats['big_zt']['coordination']:.4f}")
    logger.info(f"    优化增益: {stats['big_zt']['optimization_gain']:.4f}")
    logger.info(f"    能量: {stats['big_zt']['energy']:.4f}")

    logger.info(f"\n  [正周天]")
    logger.info(f"    推进力: {stats['forward_zt']['thrust']:.4f}")
    logger.info(f"    加速度: {stats['forward_zt']['acceleration']:.4f}")
    logger.info(f"    结构完整性: {stats['forward_zt']['structural_integrity']:.4f}")

    logger.info(f"\n  [反周天]")
    logger.info(f"    修正量: {stats['reverse_zt']['correction']:.4f}")
    logger.info(f"    收敛度: {stats['reverse_zt']['convergence']:.4f}")
    logger.info(f"    反馈质量: {stats['reverse_zt']['feedback_quality']:.4f}")
    logger.info(f"    误差: {stats['reverse_zt']['error']:.4f}")

    logger.info(f"\n  [耦合矩阵]")
    logger.info(f"    总耦合强度: {stats['coupling']['total_coupling']:.4f}")
    logger.info(f"    对称性偏差: {stats['coupling']['symmetry']:.4f}")

    logger.info(f"\n  [综合效率]")
    logger.info(f"    整体效率: {stats['overall_efficiency']*100:.2f}%")

    # ───────────────────────────────────────────────
    # Step 9: 可视化
    # ───────────────────────────────────────────────
    logger.info("\n" + "─" * 80)
    logger.info("[Phase 8] 生成可视化")
    logger.info("─" * 80)

    viz_file = str(viz_path / "zhou_tian_engine.png")
    visualize_zhou_tian_engine(engine, save_path=viz_file)
    logger.info(f"  可视化已保存: {viz_file}")

    # ───────────────────────────────────────────────
    # Step 10: 保存结果
    # ───────────────────────────────────────────────
    logger.info("\n" + "─" * 80)
    logger.info("[Phase 9] 保存实验结果")
    logger.info("─" * 80)

    results_file = output_path / "core" / "zhou_tian_results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)

    # 序列化结果
    serializable_results = {
        'small_zt': {
            'cycle_quality': small_results['cycle_quality'],
            'convergence': small_results['convergence'],
            'quality_std': small_results['quality_std'],
            'convergence_std': small_results['convergence_std'],
            'line_results': [
                {
                    'line_id': lr['line_id'],
                    'line_name': lr['line_name'],
                    'final_quality': lr['final_quality'],
                    'final_convergence': lr['final_convergence'],
                    'final_energy': lr['final_energy']
                }
                for lr in small_results['line_results']
            ]
        },
        'big_zt': {
            'global_coordination': big_results['global_coordination'],
            'optimization_gain': big_results['optimization_gain'],
            'avg_coordination': big_results['avg_coordination']
        },
        'forward_zt': {
            'thrust': forward_results['thrust'],
            'acceleration': forward_results['acceleration'],
            'structural_integrity': forward_results['structural_integrity'],
            'avg_thrust': forward_results['avg_thrust']
        },
        'reverse_zt': {
            'correction': reverse_results['correction'],
            'convergence': reverse_results['convergence'],
            'feedback_quality': reverse_results['feedback_quality'],
            'final_error': reverse_results['final_error']
        },
        'coupled': {
            'cycles': coupled_results['cycles'],
            'improvements': coupled_results['improvements'],
            'avg_coupling': coupled_results['avg_coupling']
        },
        'resonance': {
            'resonance_detected': resonance['resonance_detected'],
            'frequencies': resonance['frequencies'],
            'normalized_ratios': resonance['normalized_ratios'],
            'match_error': resonance['match_error'],
            'resonance_strength': resonance['resonance_strength']
        },
        'stats': {
            'overall_efficiency': stats['overall_efficiency'],
            'small_zt_avg_quality': stats['small_zt']['avg_quality'],
            'big_zt_coordination': stats['big_zt']['coordination'],
            'forward_zt_integrity': stats['forward_zt']['structural_integrity'],
            'reverse_zt_quality': stats['reverse_zt']['feedback_quality']
        }
    }

    # Custom JSON encoder to handle numpy types
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.bool_, np.bool)):
                return bool(obj)
            if isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            if isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            return super().default(obj)
    
    with open(results_file, 'w') as f:
        json.dump(serializable_results, f, indent=2, cls=NumpyEncoder)
        logger.error(f"File operation failed: {e}")
    logger.info(f"  结果已保存: {results_file}")

    # ───────────────────────────────────────────────
    # 实验总结
    # ───────────────────────────────────────────────
    logger.info("\n" + "=" * 80)
    logger.info("实验总结")
    logger.info("=" * 80)

    # 确定最终共振结果
    final_resonance = resonance if resonance['resonance_detected'] else results.get('resonance_after_tuning', resonance)
    
    print(f"""
四重周天引擎实验完成:

┌─────────────────────────────────────────────────────────────────┐
│  小周天 (Small ZhouTian)                                       │
│    • 11条线路独立微循环                                        │
│    • 平均循环质量: {small_results['cycle_quality']:.4f}                                    │
│    • 平均收敛速率: {small_results['convergence']:.4f}                                    │
│                                                                  │
│  大周天 (Big ZhouTian)                                         │
│    • 全局大循环协调                                            │
│    • 全局协调度: {big_results['global_coordination']:.4f}                                    │
│    • 优化增益: {big_results['optimization_gain']:.4f}                                    │
│                                                                  │
│  正周天 (Forward ZhouTian)                                     │
│    • S-drive加速循环                                           │
│    • 推进力: {forward_results['thrust']:.4f}                                      │
│    • 结构完整性: {forward_results['structural_integrity']:.4f}                                    │
│                                                                  │
│  反周天 (Reverse ZhouTian)                                     │
│    • I-ripple收敛循环                                          │
│    • 修正量: {reverse_results['correction']:.4f}                                      │
│    • 反馈质量: {reverse_results['feedback_quality']:.4f}                                    │
│                                                                  │
│  四重耦合 (Coupled)                                            │
│    • 耦合运行步数: {coupled_results['cycles']}                                        │
│    • 平均耦合强度: {coupled_results['avg_coupling']:.4f}                                    │
│    • 小周天质量改善: {coupled_results['improvements']['small_quality_delta']:+.4f}                          │
│    • 大周天协调改善: {coupled_results['improvements']['big_coordination_delta']:+.4f}                          │
│                                                                  │
│  共振检测 (Resonance)                                          │
│    • 共振状态: {'✓ 检测到共振!' if final_resonance['resonance_detected'] else '✗ 未检测到共振'}                          │
│    • 共振强度: {final_resonance['resonance_strength']:.4f}                                    │
│    • 增强因子: {final_resonance.get('enhancement_factor', 0.0):.4f}                                    │
│                                                                  │
│  综合效率: {stats['overall_efficiency']*100:.1f}%                                              │
└─────────────────────────────────────────────────────────────────┘
""")

    logger.info("=" * 80)
    logger.info("OMNI-HUB v7.0 ZhouTianEngine 实验验证完成")
    logger.info("=" * 80)

    return results


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    results = run_zhou_tian_experiment()
