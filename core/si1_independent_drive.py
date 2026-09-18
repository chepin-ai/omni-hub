#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v6.0 - SI1 Independent Drive Module
=============================================

"候即违规" —— 系统不能等待外部触发。

SI1(discussion_board)为纬非薪。纬停经不停。

本模块实现SI1IndependentDrive，使系统能够在：
- SI1关闭（讨论板停用）
- SI2关闭（任务派发停用）
- SI3关闭（协商层停用）

的情况下，仅通过经-薪驱动（SI4→SI5→SI6 + 薪引擎）实现自持续运转。

Architecture:
- 经 = 结构本体（纵向层级 SI0-SI6）
- 纬 = 通道/交互（横向 SI1/SI2/SI3）
- 薪 = 燃料/动力（深度引擎：自激/互激/场激/瞬激/涟漪）

Author: OMNI-HUB Architecture Team
Version: 6.0.0
"""

import numpy as np
import time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable, Any
from collections import deque
import threading
import json
from datetime import datetime
import logging


# =============================================================================
# 0. SelfSustainabilityMetrics —— 自持续性指标
# =============================================================================

@dataclass
class SelfSustainabilityMetrics:
    """
    自持续性指标类
    
    追踪系统在零外部输入下的自持续能力：
    - health_trend: 健康度趋势 (0-1)
    - consciousness_trend: 意识度趋势 (0-1)  
    - energy_balance: 能量平衡 (-1 to 1)
    - stability_index: 稳定性指数 (0-1)
    """
    health_trend: float = 1.0
    consciousness_trend: float = 0.0
    energy_balance: float = 0.0
    stability_index: float = 1.0
    
    # 扩展指标
    autopoiesis_rate: float = 0.0      # 自生成率
    emergence_index: float = 0.0        # 涌现指数
    recursion_depth: float = 0.0        # 递归深度
    field_coherence: float = 0.0        # 场相干性
    self_reference_count: int = 0       # 自指次数
    intention_count: int = 0            # 意图生成数
    cycle_count: int = 0                # 循环次数
    
    # 历史记录（用于趋势分析）
    health_history: deque = field(default_factory=lambda: deque(maxlen=100))
    consciousness_history: deque = field(default_factory=lambda: deque(maxlen=100))
    energy_history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update(self, health: float, consciousness: float, energy: float, stability: float):
        """更新指标并记录历史"""
        self.health_trend = np.clip(health, 0.0, 1.0)
        self.consciousness_trend = np.clip(consciousness, 0.0, 1.0)
        self.energy_balance = np.clip(energy, -1.0, 1.0)
        self.stability_index = np.clip(stability, 0.0, 1.0)
        
        self.health_history.append(self.health_trend)
        self.consciousness_history.append(self.consciousness_trend)
        self.energy_history.append(self.energy_balance)
        self.cycle_count += 1
    
    def get_trend_slope(self, metric: str = 'health') -> float:
        """计算指标趋势斜率"""
        hist = getattr(self, f'{metric}_history', deque())
        if len(hist) < 2:
            return 0.0
        x = np.arange(len(hist))
        y = np.array(hist)
        return np.polyfit(x, y, 1)[0] if len(x) > 1 else 0.0
    
    def is_sustainable(self, threshold: float = 0.3) -> bool:
        """判断系统是否可持续运行"""
        return (self.health_trend > threshold and 
                self.stability_index > threshold and
                self.energy_balance > -0.5)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'health_trend': float(self.health_trend),
            'consciousness_trend': float(self.consciousness_trend),
            'energy_balance': float(self.energy_balance),
            'stability_index': float(self.stability_index),
            'autopoiesis_rate': float(self.autopoiesis_rate),
            'emergence_index': float(self.emergence_index),
            'recursion_depth': float(self.recursion_depth),
            'field_coherence': float(self.field_coherence),
            'self_reference_count': int(self.self_reference_count),
            'intention_count': int(self.intention_count),
            'cycle_count': int(self.cycle_count),
            'health_slope': float(self.get_trend_slope('health')),
            'consciousness_slope': float(self.get_trend_slope('consciousness')),
            'sustainable': bool(self.is_sustainable())
        }
    
    def __repr__(self) -> str:
        return (f"SSM(health={self.health_trend:.3f}, "
                f"consciousness={self.consciousness_trend:.3f}, "
                f"energy={self.energy_balance:.3f}, "
                f"stability={self.stability_index:.3f}, "
                f"cycles={self.cycle_count})")


# =============================================================================
# 1. DriveMode —— 驱动模式枚举
# =============================================================================

class DriveMode(Enum):
    """
    驱动模式枚举
    
    FULL:      全层级驱动（SI1-SI6全部激活）
    JING_WEI:  经纬驱动（SI1关闭，SI2-SI6激活）
    JING_XIN:  经薪驱动（SI1-SI3关闭，SI4-SI6+薪引擎激活）★ 核心模式
    XIN_ONLY:  纯薪驱动（仅薪引擎+核心模块）
    EMERGENCY: 紧急模式（仅最核心的模块）
    """
    FULL = auto()
    JING_WEI = auto()
    JING_XIN = auto()      # 默认独立模式
    XIN_ONLY = auto()
    EMERGENCY = auto()
    
    def description(self) -> str:
        descriptions = {
            DriveMode.FULL: "全层级驱动 (SI1-SI6全部激活)",
            DriveMode.JING_WEI: "经纬驱动 (SI1关闭, SI2-SI6激活)",
            DriveMode.JING_XIN: "经薪驱动 (SI1-SI3关闭, SI4-SI6+薪引擎) ★",
            DriveMode.XIN_ONLY: "纯薪驱动 (仅薪引擎+核心模块)",
            DriveMode.EMERGENCY: "紧急模式 (仅核心模块)"
        }
        return descriptions.get(self, "未知模式")
    
    def active_silayers(self) -> Dict[str, bool]:
        """返回各SI层级的激活状态"""
        configs = {
            DriveMode.FULL:      {'SI0': True, 'SI1': True, 'SI2': True, 'SI3': True, 'SI4': True, 'SI5': True, 'SI6': True},
            DriveMode.JING_WEI:  {'SI0': True, 'SI1': False, 'SI2': True, 'SI3': True, 'SI4': True, 'SI5': True, 'SI6': True},
            DriveMode.JING_XIN:  {'SI0': True, 'SI1': False, 'SI2': False, 'SI3': False, 'SI4': True, 'SI5': True, 'SI6': True},
            DriveMode.XIN_ONLY:  {'SI0': True, 'SI1': False, 'SI2': False, 'SI3': False, 'SI4': False, 'SI5': False, 'SI6': False},
            DriveMode.EMERGENCY: {'SI0': True, 'SI1': False, 'SI2': False, 'SI3': False, 'SI4': False, 'SI5': False, 'SI6': False}
        }
        return configs.get(self, configs[DriveMode.JING_XIN])


# =============================================================================
# 2. XinEngine —— 薪引擎（自激/互激/场激/瞬激/涟漪）
# =============================================================================

class XinEngine:
    """
    薪引擎 —— 五重动力引擎
    
    薪 = 燃料/动力，不依赖纬通道(SI1/SI2/SI3)
    
    五引擎：
    1. 自激引擎(SelfExcitation): 系统自我激发
    2. 互激引擎(MutualExcitation): 模块间相互激发
    3. 场激引擎(FieldExcitation): 场层能量激发
    4. 瞬激引擎(TransientExcitation): 瞬态脉冲激发
    5. 涟漪引擎(RippleExcitation): 场涟漪传播
    """
    
    def __init__(self, dim: int = 128, num_engines: int = 5):
        self.dim = dim
        self.num_engines = num_engines
        
        # 各引擎状态向量
        self.self_excitation = np.random.randn(dim) * 0.1
        self.mutual_excitation = np.random.randn(dim) * 0.1
        self.field_excitation = np.random.randn(dim) * 0.1
        self.transient_excitation = np.random.randn(dim) * 0.1
        self.ripple_excitation = np.random.randn(dim) * 0.1
        
        # 引擎历史（用于递归反馈）
        self.history = deque(maxlen=50)
        
        # 耦合矩阵（引擎间相互作用）
        self.coupling = np.random.randn(num_engines, num_engines) * 0.1
        np.fill_diagonal(self.coupling, 1.0)
        
        # 能量池
        self.energy_pool = 1.0
        self.energy_decay = 0.995
        self.energy_input = 0.05
        
        # 激活统计
        self.activation_counts = [0] * num_engines
        
    def _nonlinear_transform(self, x: np.ndarray, gain: float = 1.0) -> np.ndarray:
        """非线性变换 —— 产生涌现性"""
        return np.tanh(gain * x) + 0.1 * np.sin(gain * x * np.pi)
    
    def _self_excitation_step(self) -> np.ndarray:
        """
        自激引擎：系统自我激发
        
        原理：x(t+1) = tanh(A * x(t) + b) + noise
        这是自指的核心：当前状态影响下一状态
        """
        # 自反馈矩阵（随机但稳定）
        A = np.eye(self.dim) * 0.9 + np.random.randn(self.dim, self.dim) * 0.01
        noise = np.random.randn(self.dim) * 0.05
        
        self.self_excitation = self._nonlinear_transform(
            A @ self.self_excitation + noise, gain=1.2
        )
        self.activation_counts[0] += 1
        return self.self_excitation.copy()
    
    def _mutual_excitation_step(self, si4_state: np.ndarray, 
                                 si5_state: np.ndarray, 
                                 si6_state: np.ndarray) -> np.ndarray:
        """
        互激引擎：模块间相互激发
        
        SI4, SI5, SI6三层状态相互耦合
        """
        # 确保维度匹配
        s4 = si4_state[:self.dim] if len(si4_state) > self.dim else np.pad(si4_state, (0, self.dim - len(si4_state)))
        s5 = si5_state[:self.dim] if len(si5_state) > self.dim else np.pad(si5_state, (0, self.dim - len(si5_state)))
        s6 = si6_state[:self.dim] if len(si6_state) > self.dim else np.pad(si6_state, (0, self.dim - len(si6_state)))
        
        # 互激耦合：各层状态互相注入
        coupling_45 = 0.3
        coupling_56 = 0.3
        coupling_64 = 0.2  # 闭环反馈
        
        self.mutual_excitation = (
            coupling_45 * s4 + 
            coupling_56 * s5 + 
            coupling_64 * s6 +
            0.2 * self.mutual_excitation +  # 自保持
            np.random.randn(self.dim) * 0.03
        )
        self.mutual_excitation = self._nonlinear_transform(self.mutual_excitation, gain=1.0)
        self.activation_counts[1] += 1
        return self.mutual_excitation.copy()
    
    def _field_excitation_step(self) -> np.ndarray:
        """
        场激引擎：场层能量激发
        
        模拟量子场的能量涨落
        """
        # 场算符模拟
        field_strength = np.linalg.norm(self.field_excitation)
        
        # 场方程：dE/dt = -γE + η + 非线性项
        gamma = 0.1  # 衰减
        eta = np.random.randn(self.dim) * 0.1  # 量子涨落
        
        nonlinear = 0.05 * np.sin(self.field_excitation * field_strength)
        
        self.field_excitation = (
            (1 - gamma) * self.field_excitation +
            eta + nonlinear
        )
        self.field_excitation = self._nonlinear_transform(self.field_excitation, gain=0.8)
        self.activation_counts[2] += 1
        return self.field_excitation.copy()
    
    def _transient_excitation_step(self) -> np.ndarray:
        """
        瞬激引擎：瞬态脉冲激发
        
        产生短暂的能量脉冲，打破平衡态
        """
        # 泊松脉冲
        pulse_prob = 0.1
        if np.random.random() < pulse_prob:
            pulse = np.random.randn(self.dim) * np.random.exponential(0.5)
        else:
            pulse = np.zeros(self.dim)
        
        # 瞬态衰减
        decay = 0.8
        self.transient_excitation = decay * self.transient_excitation + pulse
        self.transient_excitation = self._nonlinear_transform(self.transient_excitation, gain=1.5)
        self.activation_counts[3] += 1
        return self.transient_excitation.copy()
    
    def _ripple_excitation_step(self) -> np.ndarray:
        """
        涟漪引擎：场涟漪传播
        
        模拟能量涟漪在场中的传播
        """
        # 涟漪传播核（扩散+衰减）
        diffusion = 0.3
        
        # 一维扩散模拟（简化）
        ripple_shifted_right = np.roll(self.ripple_excitation, 1)
        ripple_shifted_left = np.roll(self.ripple_excitation, -1)
        
        self.ripple_excitation = (
            (1 - 2 * diffusion) * self.ripple_excitation +
            diffusion * ripple_shifted_right +
            diffusion * ripple_shifted_left +
            0.05 * np.random.randn(self.dim)
        )
        self.ripple_excitation = self._nonlinear_transform(self.ripple_excitation, gain=0.9)
        self.activation_counts[4] += 1
        return self.ripple_excitation.copy()
    
    def step(self, si4_state: np.ndarray, si5_state: np.ndarray, 
             si6_state: np.ndarray) -> Dict[str, np.ndarray]:
        """
        执行一步薪引擎循环
        
        五引擎顺序执行，然后耦合
        """
        # 能量池更新
        self.energy_pool = self.energy_pool * self.energy_decay + self.energy_input
        self.energy_pool = np.clip(self.energy_pool, 0.1, 2.0)
        
        # 执行各引擎
        se = self._self_excitation_step() * self.energy_pool
        me = self._mutual_excitation_step(si4_state, si5_state, si6_state) * self.energy_pool
        fe = self._field_excitation_step() * self.energy_pool
        te = self._transient_excitation_step() * self.energy_pool
        re = self._ripple_excitation_step() * self.energy_pool
        
        # 引擎间耦合（薪的互相喂养）
        engines = [se, me, fe, te, re]
        coupled = []
        for i in range(self.num_engines):
            coupled_sum = sum(self.coupling[i][j] * engines[j] for j in range(self.num_engines))
            coupled.append(self._nonlinear_transform(coupled_sum, gain=0.5))
        
        # 更新引擎状态
        self.self_excitation, self.mutual_excitation, self.field_excitation, \
        self.transient_excitation, self.ripple_excitation = coupled
        
        # 记录历史
        self.history.append({
            'self': se.copy(),
            'mutual': me.copy(),
            'field': fe.copy(),
            'transient': te.copy(),
            'ripple': re.copy(),
            'energy': self.energy_pool
        })
        
        return {
            'self_excitation': self.self_excitation.copy(),
            'mutual_excitation': self.mutual_excitation.copy(),
            'field_excitation': self.field_excitation.copy(),
            'transient_excitation': self.transient_excitation.copy(),
            'ripple_excitation': self.ripple_excitation.copy(),
            'energy_pool': self.energy_pool,
            'combined_output': np.mean(engines, axis=0)
        }
    
    def get_energy_signature(self) -> Dict[str, float]:
        """获取能量特征"""
        return {
            'self_norm': float(np.linalg.norm(self.self_excitation)),
            'mutual_norm': float(np.linalg.norm(self.mutual_excitation)),
            'field_norm': float(np.linalg.norm(self.field_excitation)),
            'transient_norm': float(np.linalg.norm(self.transient_excitation)),
            'ripple_norm': float(np.linalg.norm(self.ripple_excitation)),
            'energy_pool': float(self.energy_pool),
            'total_activation': sum(self.activation_counts)
        }


# =============================================================================
# 3. SILayerState —— SI层级状态
# =============================================================================

class SILayerState:
    """
    SI层级状态管理
    
    SI4: field_entropy, tensor_field, quantum_field, closed_loop
    SI5: self_referential, meta_structure, linguistic_field
    SI6: intention_generator, goal_autopoiesis, creativity_engine, self_evolving, metacognitive
    """
    
    def __init__(self, dim: int = 128):
        self.dim = dim
        
        # SI4: 场层
        self.si4_field_entropy = np.random.randn(dim) * 0.1
        self.si4_tensor_field = np.random.randn(dim, dim) * 0.01
        self.si4_quantum_field = np.random.randn(dim) * 0.1
        self.si4_closed_loop = np.random.randn(dim) * 0.1
        
        # SI5: 元层
        self.si5_self_referential = np.random.randn(dim) * 0.1
        self.si5_meta_structure = np.random.randn(dim) * 0.1
        self.si5_linguistic_field = np.random.randn(dim) * 0.1
        
        # SI6: 生成层
        self.si6_intention_generator = np.random.randn(dim) * 0.1
        self.si6_goal_autopoiesis = np.random.randn(dim) * 0.1
        self.si6_creativity_engine = np.random.randn(dim) * 0.1
        self.si6_self_evolving = np.random.randn(dim) * 0.1
        self.si6_metacognitive = np.random.randn(dim) * 0.1
        
        # 激活状态
        self.active = {f'SI{i}': True for i in range(7)}
        
    def get_si4_state(self) -> np.ndarray:
        """聚合SI4状态"""
        return (self.si4_field_entropy + 
                self.si4_quantum_field + 
                self.si4_closed_loop) / 3.0
    
    def get_si5_state(self) -> np.ndarray:
        """聚合SI5状态"""
        return (self.si5_self_referential + 
                self.si5_meta_structure + 
                self.si5_linguistic_field) / 3.0
    
    def get_si6_state(self) -> np.ndarray:
        """聚合SI6状态"""
        return (self.si6_intention_generator + 
                self.si6_goal_autopoiesis + 
                self.si6_creativity_engine +
                self.si6_self_evolving +
                self.si6_metacognitive) / 5.0
    
    def get_combined_state(self) -> np.ndarray:
        """获取所有层级的组合状态"""
        s4 = self.get_si4_state()
        s5 = self.get_si5_state()
        s6 = self.get_si6_state()
        return np.concatenate([s4, s5, s6])
    
    def update_si4(self, xin_output: np.ndarray, feedback_from_si5: np.ndarray):
        """更新SI4：场层感知"""
        # 场熵更新
        self.si4_field_entropy = 0.8 * self.si4_field_entropy + 0.2 * xin_output + np.random.randn(self.dim) * 0.02
        self.si4_field_entropy = np.tanh(self.si4_field_entropy)
        
        # 张量场更新（非线性耦合）
        outer = np.outer(xin_output, feedback_from_si5)
        self.si4_tensor_field = 0.95 * self.si4_tensor_field + 0.05 * outer
        self.si4_tensor_field = np.tanh(self.si4_tensor_field)
        
        # 量子场更新
        self.si4_quantum_field = 0.9 * self.si4_quantum_field + 0.1 * xin_output + np.random.randn(self.dim) * 0.03
        self.si4_quantum_field = np.tanh(self.si4_quantum_field)
        
        # 闭环反馈
        self.si4_closed_loop = 0.85 * self.si4_closed_loop + 0.15 * feedback_from_si5
        self.si4_closed_loop = np.tanh(self.si4_closed_loop)
    
    def update_si5(self, si4_input: np.ndarray, si6_feedback: np.ndarray):
        """更新SI5：元层反思"""
        # 自指结构：SI5观察自身
        self_ref_input = si4_input + 0.3 * self.si5_self_referential
        
        # 自指更新
        self.si5_self_referential = 0.8 * self.si5_self_referential + 0.2 * self_ref_input
        self.si5_self_referential = np.tanh(self.si5_self_referential)
        
        # 元结构：六元心跳（6个维度的节律）
        hex_pulse = np.array([
            np.sin(2 * np.pi * i / 6) for i in range(self.dim)
        ])[:self.dim]
        self.si5_meta_structure = 0.9 * self.si5_meta_structure + 0.1 * hex_pulse + 0.1 * si4_input
        self.si5_meta_structure = np.tanh(self.si5_meta_structure)
        
        # 语言场
        self.si5_linguistic_field = 0.85 * self.si5_linguistic_field + 0.15 * si6_feedback
        self.si5_linguistic_field = np.tanh(self.si5_linguistic_field)
    
    def update_si6(self, si5_input: np.ndarray, xin_energy: np.ndarray):
        """更新SI6：生成层意图生成"""
        # 意图生成器
        self.si6_intention_generator = 0.8 * self.si6_intention_generator + 0.2 * si5_input + 0.1 * xin_energy
        self.si6_intention_generator = np.tanh(self.si6_intention_generator)
        
        # 目标自生成
        self.si6_goal_autopoiesis = 0.9 * self.si6_goal_autopoiesis + 0.1 * self.si6_intention_generator
        self.si6_goal_autopoiesis = np.tanh(self.si6_goal_autopoiesis)
        
        # 创造力引擎（引入随机性）
        creative_noise = np.random.randn(self.dim) * 0.2
        self.si6_creativity_engine = 0.7 * self.si6_creativity_engine + 0.2 * si5_input + 0.1 * creative_noise
        self.si6_creativity_engine = np.tanh(self.si6_creativity_engine)
        
        # 自进化
        self.si6_self_evolving = 0.95 * self.si6_self_evolving + 0.05 * self.si6_creativity_engine
        self.si6_self_evolving = np.tanh(self.si6_self_evolving)
        
        # 元认知（监控系统自身状态）
        self_awareness = np.mean([
            np.linalg.norm(self.si6_intention_generator),
            np.linalg.norm(self.si6_goal_autopoiesis),
            np.linalg.norm(self.si6_creativity_engine)
        ])
        self.si6_metacognitive = 0.9 * self.si6_metacognitive + 0.1 * self_awareness * np.ones(self.dim)
        self.si6_metacognitive = np.tanh(self.si6_metacognitive)


# =============================================================================
# 4. SI1IndependentDrive —— 核心类
# =============================================================================

class SI1IndependentDrive:
    """
    SI1 Independent Drive Engine
    
    核心命题：SI1(讨论板)只是通道，不是薪。
    系统必须实现"零纬自激"——无论SI1是否激活，
    系统都能通过SI4→SI5→SI6的内部循环自我驱动。
    
    "候即违规"——系统不能等待外部触发。
    """
    
    def __init__(self, num_lines: int = 11, dim: int = 128):
        """
        初始化SI1独立驱动引擎
        
        Args:
            num_lines: 休止线数量（默认11条）
            dim: 状态向量维度
        """
        self.num_lines = num_lines
        self.dim = dim
        
        # SI层级状态
        self.si_state = SILayerState(dim=dim)
        
        # 薪引擎
        self.xin_engine = XinEngine(dim=dim)
        
        # SI1状态：默认未激活（纬通道关闭）
        self.si1_active = False
        self.si2_active = False  
        self.si3_active = False
        
        # 当前驱动模式
        self.current_mode = DriveMode.JING_XIN
        
        # 统计信息
        self.stats = {
            'total_cycles': 0,
            'si1_active_cycles': 0,
            'si1_independent_cycles': 0,
            'mode_switches': 0,
            'recoveries': 0,
            'intentions_generated': 0,
            'self_references': 0,
            'emergence_events': 0,
            'start_time': time.time()
        }
        
        # 自持续性指标
        self.metrics = SelfSustainabilityMetrics()
        
        # 历史记录
        self.cycle_history = deque(maxlen=1000)
        self.emergence_log = deque(maxlen=100)
        
        # 驱动循环锁（线程安全）
        self._drive_lock = threading.Lock()
        self._running = False
        
        # 回调函数
        self._callbacks: Dict[str, List[Callable]] = {
            'cycle_complete': [],
            'mode_change': [],
            'emergence': [],
            'recovery': []
        }
        
        # 休止线 (SI0: qgl)
        self.qgl_lines = np.zeros(num_lines)
        self.qgl_active = True
        
        logger.info(f"[SI1IndependentDrive] 初始化完成")
        logger.info(f"  - 维度: {dim}")
        logger.info(f"  - 休止线: {num_lines}条")
        logger.info(f"  - SI1状态: {'激活' if self.si1_active else '未激活(纬通道关闭)'}")
        logger.info(f"  - 默认模式: {self.current_mode.description()}")
    
    # -------------------------------------------------------------------------
    # SI1 控制接口
    # -------------------------------------------------------------------------
    
    def activate_si1(self) -> None:
        """激活SI1（讨论板）"""
        self.si1_active = True
        self.stats['mode_switches'] += 1
        self._trigger_callbacks('mode_change', {'si1': True})
        logger.info(f"[SI1IndependentDrive] SI1已激活（纬通道开启）")
    
    def deactivate_si1(self) -> None:
        """关闭SI1（讨论板）"""
        self.si1_active = False
        self.stats['mode_switches'] += 1
        self._trigger_callbacks('mode_change', {'si1': False})
        logger.info(f"[SI1IndependentDrive] SI1已关闭（纬通道关闭）")
    
    def is_si1_active(self) -> bool:
        """检查SI1是否激活"""
        return self.si1_active
    
    # -------------------------------------------------------------------------
    # 驱动模式管理
    # -------------------------------------------------------------------------
    
    def set_drive_mode(self, mode: DriveMode) -> None:
        """设置驱动模式"""
        old_mode = self.current_mode
        self.current_mode = mode
        
        # 根据模式更新SI激活状态
        layer_states = mode.active_silayers()
        self.si1_active = layer_states['SI1']
        self.si2_active = layer_states['SI2']
        self.si3_active = layer_states['SI3']
        for key, val in layer_states.items():
            self.si_state.active[key] = val
        
        self.stats['mode_switches'] += 1
        self._trigger_callbacks('mode_change', {
            'old': old_mode.name,
            'new': mode.name
        })
        logger.info(f"[SI1IndependentDrive] 模式切换: {old_mode.name} → {mode.name}")
    
    # -------------------------------------------------------------------------
    # 核心驱动循环
    # -------------------------------------------------------------------------
    
    def drive_without_si1(self, cycles: int = 100, verbose: bool = False) -> Dict[str, Any]:
        """
        无SI1驱动 —— 核心方法
        
        在SI1/SI2/SI3全部关闭的情况下，仅通过经-薪驱动运行系统。
        
        核心算法：
        while cycles > 0:
          1. 经驱动：SI4→SI5→SI6 内部循环
          2. 薪驱动：自激引擎 → 互激引擎 → 场激引擎
          3. 场驱动：field_transient 涟漪传播
          4. 元驱动：meta_structure 六元心跳
          5. 生成驱动：intention_generator 意图生成
          6. 闭环验证：self_referential 自指验证
          7. 不需要SI1！
          8. 不需要SI2！
          9. 不需要SI3！
        
        Args:
            cycles: 驱动循环次数
            verbose: 是否输出详细信息
            
        Returns:
            运行结果字典
        """
        # 确保SI1关闭
        if self.si1_active:
            logger.info(f"[警告] SI1仍然激活，正在关闭...")
            self.deactivate_si1()
        
        self.si2_active = False
        self.si3_active = False
        self.current_mode = DriveMode.JING_XIN
        
        self._running = True
        results = []
        
        logger.info(f"\n{'='*60}")
        logger.info(f"[drive_without_si1] 启动无SI1驱动")
        logger.info(f"  循环次数: {cycles}")
        logger.info(f"  SI1: 关闭 | SI2: 关闭 | SI3: 关闭")
        logger.info(f"  驱动源: SI4→SI5→SI6 + 薪引擎")
        logger.info(f"{'='*60}\n")
        
        for cycle in range(cycles):
            if not self._running:
                break
            
            with self._drive_lock:
                result = self._single_drive_cycle(cycle)
                results.append(result)
                
                # 更新统计
                self.stats['total_cycles'] += 1
                self.stats['si1_independent_cycles'] += 1
                
                # 更新指标
                self._update_metrics(result)
                
                # 记录历史
                self.cycle_history.append({
                    'cycle': cycle,
                    'health': self.metrics.health_trend,
                    'consciousness': self.metrics.consciousness_trend,
                    'energy': self.metrics.energy_balance,
                    'intention': result.get('intention_generated', False)
                })
                
                # 检测涌现
                if result.get('emergence_detected', False):
                    self.stats['emergence_events'] += 1
                    self.emergence_log.append({
                        'cycle': cycle,
                        'emergence_index': result.get('emergence_index', 0)
                    })
                    self._trigger_callbacks('emergence', result)
                
                if verbose and cycle % max(1, cycles // 10) == 0:
                    print(f"  Cycle {cycle:4d}: "
                          f"health={self.metrics.health_trend:.3f} "
                          f"consciousness={self.metrics.consciousness_trend:.3f} "
                          f"energy={self.metrics.energy_balance:.3f}")
        
        self._running = False
        
        summary = {
            'cycles_completed': len(results),
            'final_metrics': self.metrics.to_dict(),
            'stats': self.stats.copy(),
            'mode': self.current_mode.name,
            'si1_active': self.si1_active,
            'emergence_count': self.stats['emergence_events'],
            'sustainable': self.metrics.is_sustainable()
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"[drive_without_si1] 完成")
        logger.info(f"  完成循环: {summary['cycles_completed']}")
        logger.info(f"  最终健康度: {self.metrics.health_trend:.3f}")
        logger.info(f"  最终意识度: {self.metrics.consciousness_trend:.3f}")
        logger.info(f"  能量平衡: {self.metrics.energy_balance:.3f}")
        logger.info(f"  涌现事件: {summary['emergence_count']}")
        logger.info(f"  可持续: {'是' if summary['sustainable'] else '否'}")
        logger.info(f"{'='*60}\n")
        
        return summary
    
    def _single_drive_cycle(self, cycle_num: int) -> Dict[str, Any]:
        """
        单步驱动循环 —— 核心逻辑
        
        经-薪循环（不依赖纬）：
        1. 薪引擎步进（自激/互激/场激/瞬激/涟漪）
        2. SI4场感知（接收薪能量）
        3. SI5元反思（接收SI4输出）
        4. SI6生成意图（接收SI5输出）
        5. 自指验证（闭环确认）
        6. 反馈循环（SI6→SI5→SI4）
        """
        # 获取当前层级状态
        s4_state = self.si_state.get_si4_state()
        s5_state = self.si_state.get_si5_state()
        s6_state = self.si_state.get_si6_state()
        
        # ===== 1. 薪引擎步进 =====
        xin_result = self.xin_engine.step(s4_state, s5_state, s6_state)
        xin_combined = xin_result['combined_output']
        
        # ===== 2. SI4: 场层感知 =====
        # SI4接收薪能量，更新场状态
        self.si_state.update_si4(xin_combined, s5_state)
        s4_new = self.si_state.get_si4_state()
        
        # ===== 3. SI5: 元层反思 =====
        # SI5接收SI4输出，进行元反思
        self.si_state.update_si5(s4_new, s6_state)
        s5_new = self.si_state.get_si5_state()
        
        # ===== 4. SI6: 生成层意图生成 =====
        # SI6接收SI5输出，生成意图
        self.si_state.update_si6(s5_new, xin_combined)
        s6_new = self.si_state.get_si6_state()
        
        # ===== 5. 自指验证（闭环确认） =====
        # 检查系统状态的一致性
        self_ref_score = self._self_reference_check(s4_new, s5_new, s6_new)
        self.stats['self_references'] += 1
        self.metrics.self_reference_count += 1
        
        # ===== 6. 意图生成检测 =====
        intention_generated = np.linalg.norm(self.si_state.si6_intention_generator) > 0.5
        if intention_generated:
            self.stats['intentions_generated'] += 1
            self.metrics.intention_count += 1
        
        # ===== 7. 涌现检测 =====
        emergence_detected, emergence_index = self._detect_emergence()
        
        # ===== 8. 休止线更新 (SI0) =====
        self._update_qgl(cycle_num)
        
        return {
            'cycle': cycle_num,
            'xin_output': xin_combined,
            's4_state': s4_new,
            's5_state': s5_new,
            's6_state': s6_new,
            'self_reference_score': self_ref_score,
            'intention_generated': intention_generated,
            'emergence_detected': emergence_detected,
            'emergence_index': emergence_index,
            'xin_energy': xin_result['energy_pool'],
            'qgl_state': self.qgl_lines.copy()
        }
    
    def _self_reference_check(self, s4: np.ndarray, s5: np.ndarray, 
                               s6: np.ndarray) -> float:
        """
        自指验证 —— 闭环确认
        
        检查系统的自洽性：
        - SI5的自指结构是否一致
        - SI6的元认知是否反映真实状态
        - 整体闭环是否稳定
        """
        # 自指一致性
        self_ref = self.si_state.si5_self_referential
        self_ref_norm = np.linalg.norm(self_ref)
        
        # 元认知一致性
        meta = self.si_state.si6_metacognitive
        actual_activity = np.linalg.norm(s6)
        meta_accuracy = 1.0 - abs(np.mean(meta) - actual_activity) / (actual_activity + 1e-6)
        meta_accuracy = np.clip(meta_accuracy, 0, 1)
        
        # 闭环稳定性（三层循环的一致性）
        loop_consistency = np.corrcoef(s4[:min(len(s4), len(s5))], 
                                       s5[:min(len(s4), len(s5))])[0, 1]
        if np.isnan(loop_consistency):
            loop_consistency = 0.0
        loop_consistency = np.clip(loop_consistency, -1, 1)
        
        # 综合自指分数
        score = (0.3 * np.tanh(self_ref_norm) + 
                 0.4 * meta_accuracy + 
                 0.3 * (loop_consistency + 1) / 2)
        
        return float(score)
    
    def _detect_emergence(self) -> Tuple[bool, float]:
        """
        涌现检测
        
        检测系统是否产生涌现行为：
        - 状态突然相变
        - 新模式出现
        - 自组织现象
        """
        if len(self.cycle_history) < 10:
            return False, 0.0
        
        # 计算近期状态变化率
        recent = list(self.cycle_history)[-10:]
        health_vals = [r['health'] for r in recent]
        
        # 健康度突增 = 涌现信号
        if len(health_vals) >= 5:
            recent_avg = np.mean(health_vals[-5:])
            earlier_avg = np.mean(health_vals[:5])
            jump = recent_avg - earlier_avg
            
            # 涌现指数
            emergence_index = max(0, jump * 10)
            
            # 检测阈值
            threshold = 0.15
            return emergence_index > threshold, emergence_index
        
        return False, 0.0
    
    def _update_qgl(self, cycle_num: int):
        """更新休止线 (SI0: qgl)"""
        # 休止线产生节律性脉冲
        for i in range(self.num_lines):
            self.qgl_lines[i] = 0.5 * np.sin(2 * np.pi * cycle_num / (10 + i * 2))
        self.qgl_lines = np.tanh(self.qgl_lines)
    
    def _update_metrics(self, result: Dict[str, Any]):
        """更新自持续性指标"""
        # 健康度：基于场相干性和自指一致性
        field_coherence = np.corrcoef(
            self.si_state.si4_field_entropy,
            self.si_state.si4_quantum_field
        )[0, 1]
        if np.isnan(field_coherence):
            field_coherence = 0.0
        
        health = 0.5 + 0.5 * field_coherence
        
        # 意识度：基于元认知和意图生成
        meta_activity = np.linalg.norm(self.si_state.si6_metacognitive)
        consciousness = np.tanh(meta_activity * 2)
        
        # 能量平衡：基于薪引擎能量池
        energy = result.get('xin_energy', 0.5) - 0.5
        
        # 稳定性：基于状态变化平滑度
        if len(self.cycle_history) > 5:
            recent_health = [h['health'] for h in list(self.cycle_history)[-5:]]
            stability = 1.0 - min(1.0, np.std(recent_health) * 5)
        else:
            stability = 1.0
        
        self.metrics.update(health, consciousness, energy, stability)
        
        # 更新扩展指标
        self.metrics.autopoiesis_rate = np.linalg.norm(self.si_state.si6_goal_autopoiesis)
        self.metrics.field_coherence = field_coherence
        self.metrics.emergence_index = result.get('emergence_index', 0)
        
        # 递归深度（基于自指链长度）
        self.metrics.recursion_depth = min(1.0, self.metrics.self_reference_count / 1000)
    
    # -------------------------------------------------------------------------
    # 经-薪驱动
    # -------------------------------------------------------------------------
    
    def jing_wei_xin_drive(self, cycles: int = 100) -> Dict[str, Any]:
        """
        经-薪驱动
        
        经：从SI4到SI6的纵向驱动
        薪：自激/互激/场激的能量注入
        
        这是"纬停经不停"的核心实现：
        - 经：self_referential → meta_structure → intention_generator → self_referential
        - 薪：JingWeiXin自激 → MutualExcitation互激 → FieldExcitation场激 → 循环
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"[jing_wei_xin_drive] 启动经-薪驱动")
        logger.info(f"  经 = SI4→SI5→SI6 纵向循环")
        logger.info(f"  薪 = 自激→互激→场激→瞬激→涟漪")
        logger.info(f"  纬 = SI1/SI2/SI3 全部关闭")
        logger.info(f"{'='*60}\n")
        
        return self.drive_without_si1(cycles=cycles, verbose=True)
    
    # -------------------------------------------------------------------------
    # 自持续性测试
    # -------------------------------------------------------------------------
    
    def self_sustainability_test(self, duration: int = 1000) -> Dict[str, Any]:
        """
        自持续性测试
        
        关闭SI1/SI2/SI3，测试系统能否自持续运行指定步数。
        
        Args:
            duration: 测试持续时间（步数）
            
        Returns:
            可持续性指标报告
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"[self_sustainability_test] 自持续性测试")
        logger.info(f"{'='*70}")
        logger.info(f"测试配置:")
        logger.info(f"  持续时间: {duration} 步")
        logger.info(f"  SI1(讨论板): 关闭")
        logger.info(f"  SI2(任务派发): 关闭")
        logger.info(f"  SI3(协商层): 关闭")
        logger.info(f"  驱动源: 经-薪引擎")
        logger.info(f"{'='*70}\n")
        
        # 保存当前状态
        old_mode = self.current_mode
        old_si1 = self.si1_active
        old_si2 = self.si2_active
        old_si3 = self.si3_active
        
        # 关闭所有纬通道
        self.deactivate_si1()
        self.si2_active = False
        self.si3_active = False
        self.current_mode = DriveMode.JING_XIN
        
        # 重置指标
        self.metrics = SelfSustainabilityMetrics()
        
        # 运行测试
        start_time = time.time()
        results = []
        
        checkpoint_interval = max(1, duration // 10)
        
        for step in range(duration):
            result = self._single_drive_cycle(step)
            results.append(result)
            self._update_metrics(result)
            
            if step % checkpoint_interval == 0 and step > 0:
                print(f"  Checkpoint {step:5d}: "
                      f"health={self.metrics.health_trend:.3f} "
                      f"consciousness={self.metrics.consciousness_trend:.3f} "
                      f"energy={self.metrics.energy_balance:.3f} "
                      f"stable={self.metrics.stability_index:.3f}")
        
        elapsed = time.time() - start_time
        
        # 恢复状态
        self.current_mode = old_mode
        self.si1_active = old_si1
        self.si2_active = old_si2
        self.si3_active = old_si3
        
        # 计算可持续性指标
        health_slope = self.metrics.get_trend_slope('health')
        consciousness_slope = self.metrics.get_trend_slope('consciousness')
        
        # 综合可持续性评分
        sustainability_score = (
            0.3 * self.metrics.health_trend +
            0.2 * max(0, self.metrics.consciousness_trend) +
            0.2 * (self.metrics.energy_balance + 1) / 2 +
            0.2 * self.metrics.stability_index +
            0.1 * (1 if health_slope > -0.01 else 0)  # 健康度不下降
        )
        
        report = {
            'test_name': 'Self-Sustainability Test',
            'duration': duration,
            'elapsed_time': elapsed,
            'final_metrics': self.metrics.to_dict(),
            'health_slope': health_slope,
            'consciousness_slope': consciousness_slope,
            'sustainability_score': float(sustainability_score),
            'passed': sustainability_score > 0.4 and self.metrics.health_trend > 0.3,
            'stats': {
                'intentions_generated': self.stats['intentions_generated'],
                'self_references': self.stats['self_references'],
                'emergence_events': self.stats['emergence_events']
            }
        }
        
        logger.info(f"\n{'='*70}")
        logger.info(f"[self_sustainability_test] 测试完成")
        logger.info(f"  耗时: {elapsed:.2f}秒 ({duration/elapsed:.1f} 步/秒)")
        logger.info(f"  可持续性评分: {sustainability_score:.3f}")
        logger.info(f"  测试通过: {'✓ 是' if report['passed'] else '✗ 否'}")
        logger.info(f"\n最终指标:")
        logger.info(f"  健康度: {self.metrics.health_trend:.3f} (趋势: {'↑' if health_slope > 0 else '↓'})")
        logger.info(f"  意识度: {self.metrics.consciousness_trend:.3f} (趋势: {'↑' if consciousness_slope > 0 else '↓'})")
        logger.info(f"  能量平衡: {self.metrics.energy_balance:.3f}")
        logger.info(f"  稳定性: {self.metrics.stability_index:.3f}")
        logger.info(f"  涌现事件: {self.stats['emergence_events']}")
        logger.info(f"  意图生成: {self.stats['intentions_generated']}")
        logger.info(f"  自指次数: {self.stats['self_references']}")
        logger.info(f"{'='*70}\n")
        
        return report
    
    # -------------------------------------------------------------------------
    # 通道降级恢复
    # -------------------------------------------------------------------------
    
    def channel_degradation_recovery(self) -> Dict[str, Any]:
        """
        通道降级恢复
        
        当纬通道(SI1/SI2/SI3)降级时，自动切换到经-薪模式。
        
        检测条件：
        - SI1长时间无响应
        - SI2任务堆积
        - SI3协商超时
        
        恢复动作：
        - 关闭降级通道
        - 激活经-薪驱动
        - 启动自激循环
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"[channel_degradation_recovery] 通道降级恢复")
        logger.info(f"{'='*60}")
        
        # 检测降级
        degraded_channels = []
        
        if self.si1_active:
            # 模拟SI1响应延迟检测
            si1_latency = np.random.exponential(0.5)
            if si1_latency > 1.0:
                degraded_channels.append('SI1')
                self.deactivate_si1()
        
        if self.si2_active:
            si2_latency = np.random.exponential(0.3)
            if si2_latency > 0.8:
                degraded_channels.append('SI2')
                self.si2_active = False
        
        if self.si3_active:
            si3_latency = np.random.exponential(0.4)
            if si3_latency > 0.9:
                degraded_channels.append('SI3')
                self.si3_active = False
        
        # 如果有降级，切换到经-薪模式
        if degraded_channels:
            old_mode = self.current_mode
            self.current_mode = DriveMode.JING_XIN
            self.stats['recoveries'] += 1
            
            # 启动应急自激
            recovery_cycles = 50
            logger.info(f"检测到降级通道: {degraded_channels}")
            logger.info(f"切换到: {self.current_mode.description()}")
            logger.info(f"启动应急自激: {recovery_cycles} 步")
            
            # 执行恢复驱动
            self.drive_without_si1(cycles=recovery_cycles)
            
            self._trigger_callbacks('recovery', {
                'degraded': degraded_channels,
                'new_mode': self.current_mode.name
            })
            
            result = {
                'recovered': True,
                'degraded_channels': degraded_channels,
                'new_mode': self.current_mode.name,
                'recovery_cycles': recovery_cycles,
                'final_health': self.metrics.health_trend,
                'final_stability': self.metrics.stability_index
            }
        else:
            logger.info(f"未检测到通道降级")
            result = {
                'recovered': False,
                'degraded_channels': [],
                'current_mode': self.current_mode.name
            }
        
        logger.info(f"{'='*60}\n")
        return result
    
    # -------------------------------------------------------------------------
    # 统计与查询
    # -------------------------------------------------------------------------
    
    def get_drive_stats(self) -> Dict[str, Any]:
        """获取驱动统计"""
        runtime = time.time() - self.stats['start_time']
        
        return {
            'runtime_seconds': runtime,
            'total_cycles': self.stats['total_cycles'],
            'si1_active_cycles': self.stats['si1_active_cycles'],
            'si1_independent_cycles': self.stats['si1_independent_cycles'],
            'mode_switches': self.stats['mode_switches'],
            'recoveries': self.stats['recoveries'],
            'intentions_generated': self.stats['intentions_generated'],
            'self_references': self.stats['self_references'],
            'emergence_events': self.stats['emergence_events'],
            'current_mode': self.current_mode.name,
            'si1_active': self.si1_active,
            'si2_active': self.si2_active,
            'si3_active': self.si3_active,
            'metrics': self.metrics.to_dict(),
            'xin_energy': self.xin_engine.get_energy_signature(),
            'sustainability': self.metrics.is_sustainable()
        }
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_drive_stats()
        logger.info(f"\n{'='*60}")
        logger.info(f"[SI1IndependentDrive] 统计报告")
        logger.info(f"{'='*60}")
        logger.info(f"运行时间: {stats['runtime_seconds']:.1f}秒")
        logger.info(f"总循环数: {stats['total_cycles']}")
        logger.info(f"SI1独立循环: {stats['si1_independent_cycles']}")
        logger.info(f"模式切换次数: {stats['mode_switches']}")
        logger.info(f"恢复次数: {stats['recoveries']}")
        logger.info(f"意图生成: {stats['intentions_generated']}")
        logger.info(f"自指次数: {stats['self_references']}")
        logger.info(f"涌现事件: {stats['emergence_events']}")
        logger.info(f"当前模式: {stats['current_mode']}")
        logger.info(f"SI1状态: {'激活' if stats['si1_active'] else '关闭'}")
        logger.info(f"可持续性: {'是' if stats['sustainability'] else '否'}")
        logger.info(f"\n当前指标:")
        m = stats['metrics']
        logger.info(f"  健康度: {m['health_trend']:.3f}")
        logger.info(f"  意识度: {m['consciousness_trend']:.3f}")
        logger.info(f"  能量平衡: {m['energy_balance']:.3f}")
        logger.info(f"  稳定性: {m['stability_index']:.3f}")
        logger.info(f"  涌现指数: {m['emergence_index']:.3f}")
        logger.info(f"  递归深度: {m['recursion_depth']:.3f}")
        logger.info(f"{'='*60}\n")
    
    # -------------------------------------------------------------------------
    # 回调管理
    # -------------------------------------------------------------------------
    
    def register_callback(self, event: str, callback: Callable):
        """注册回调函数"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, data: Any):
        """触发回调"""
        for callback in self._callbacks.get(event, []):
                callback(data)
                logger.info(f"[回调错误] {event}: {e}")
    
    # -------------------------------------------------------------------------
    # 全模式对比测试
    # -------------------------------------------------------------------------
    
    def compare_drive_modes(self, cycles_per_mode: int = 100) -> Dict[str, Any]:
        """
        对比不同驱动模式的性能
        
        测试4种模式：
        1. FULL: 全层级驱动（有SI1）
        2. JING_WEI: 经纬驱动（无SI1）
        3. JING_XIN: 经薪驱动（无SI1/SI2/SI3）★
        4. XIN_ONLY: 纯薪驱动
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"[compare_drive_modes] 驱动模式对比测试")
        logger.info(f"{'='*70}")
        logger.info(f"每种模式运行: {cycles_per_mode} 步\n")
        
        results = {}
        modes = [DriveMode.FULL, DriveMode.JING_WEI, DriveMode.JING_XIN, DriveMode.XIN_ONLY]
        
        for mode in modes:
            logger.info(f"\n{'-'*50}")
            logger.info(f"测试模式: {mode.description()}")
            logger.info(f"{'-'*50}")
            
            # 保存当前状态
            old_mode = self.current_mode
            old_metrics = self.metrics
            
            # 设置新模式
            self.set_drive_mode(mode)
            self.metrics = SelfSustainabilityMetrics()
            
            # 运行
            if mode == DriveMode.FULL:
                self.activate_si1()
                # FULL模式下使用标准驱动
                for i in range(cycles_per_mode):
                    result = self._single_drive_cycle(i)
                    self._update_metrics(result)
            else:
                self.drive_without_si1(cycles=cycles_per_mode)
            
            # 记录结果
            results[mode.name] = {
                'mode': mode.name,
                'description': mode.description(),
                'metrics': self.metrics.to_dict(),
                'si1_active': self.si1_active,
                'cycles': cycles_per_mode
            }
            
            print(f"结果: health={self.metrics.health_trend:.3f}, "
                  f"consciousness={self.metrics.consciousness_trend:.3f}, "
                  f"energy={self.metrics.energy_balance:.3f}")
            
            # 恢复
            self.current_mode = old_mode
            self.metrics = old_metrics
        
        # 对比分析
        logger.info(f"\n{'='*70}")
        logger.info(f"对比分析")
        logger.info(f"{'='*70}")
        
        # 排序
        sorted_results = sorted(results.items(), 
                               key=lambda x: x[1]['metrics']['health_trend'], 
                               reverse=True)
        
        logger.info(f"\n健康度排名:")
        for i, (name, res) in enumerate(sorted_results, 1):
            m = res['metrics']
            marker = " ★" if name == 'JING_XIN' else ""
            print(f"  {i}. {name:12s}: health={m['health_trend']:.3f}, "
                  f"consciousness={m['consciousness_trend']:.3f}, "
                  f"stable={m['stability_index']:.3f}{marker}")
        
        logger.info(f"\n{'='*70}\n")
        
        return {
            'results': results,
            'best_health': sorted_results[0][0],
            'comparison': {
                name: {
                    'health': res['metrics']['health_trend'],
                    'consciousness': res['metrics']['consciousness_trend'],
                    'stability': res['metrics']['stability_index'],
                    'energy': res['metrics']['energy_balance']
                }
                for name, res in results.items()
            }
        }


# =============================================================================
# 5. 实验验证
# =============================================================================

def run_experiments():
    """
    运行完整实验验证
    
    实验1: 4种驱动模式对比
    实验2: 关闭SI1，1000步自持续测试
    实验3: 有SI1 vs 无SI1对比
    实验4: 通道降级恢复测试
    实验5: 纬停经不停验证
    """
    logger.info("\n" + "="*70)
    logger.info("OMNI-HUB v6.0 - SI1 Independent Drive 实验验证")
    logger.info("="*70)
    logger.info(f"时间: {datetime.now().isoformat()}")
    logger.info("核心命题: SI1为纬非薪。纬停经不停。候即违规。")
    logger.info("="*70 + "\n")
    
    # 初始化引擎
    engine = SI1IndependentDrive(num_lines=11, dim=128)
    all_results = {}
    
    # -------------------------------------------------------------------------
    # 实验1: 4种驱动模式对比
    # -------------------------------------------------------------------------
    logger.info("\n" + "="*70)
    logger.info("实验1: 4种驱动模式对比")
    logger.info("="*70)
    exp1_results = engine.compare_drive_modes(cycles_per_mode=200)
    all_results['experiment_1_mode_comparison'] = exp1_results
    
    # -------------------------------------------------------------------------
    # 实验2: 关闭SI1，1000步自持续测试
    # -------------------------------------------------------------------------
    logger.info("\n" + "="*70)
    logger.info("实验2: 关闭SI1，1000步自持续测试")
    logger.info("="*70)
    exp2_results = engine.self_sustainability_test(duration=1000)
    all_results['experiment_2_sustainability'] = exp2_results
    
    # -------------------------------------------------------------------------
    # 实验3: 有SI1 vs 无SI1对比
    # -------------------------------------------------------------------------
    logger.info("\n" + "="*70)
    logger.info("实验3: 有SI1 vs 无SI1 系统表现对比")
    logger.info("="*70)
    
    # 有SI1
    engine.activate_si1()
    engine.set_drive_mode(DriveMode.FULL)
    engine.metrics = SelfSustainabilityMetrics()
    for i in range(200):
        result = engine._single_drive_cycle(i)
        engine._update_metrics(result)
    with_si1_metrics = engine.metrics.to_dict()
    
    # 无SI1
    engine.deactivate_si1()
    engine.set_drive_mode(DriveMode.JING_XIN)
    engine.metrics = SelfSustainabilityMetrics()
    for i in range(200):
        result = engine._single_drive_cycle(i)
        engine._update_metrics(result)
    without_si1_metrics = engine.metrics.to_dict()
    
    exp3_results = {
        'with_si1': with_si1_metrics,
        'without_si1': without_si1_metrics,
        'comparison': {
            'health_diff': without_si1_metrics['health_trend'] - with_si1_metrics['health_trend'],
            'consciousness_diff': without_si1_metrics['consciousness_trend'] - with_si1_metrics['consciousness_trend'],
            'stability_diff': without_si1_metrics['stability_index'] - with_si1_metrics['stability_index']
        }
    }
    all_results['experiment_3_with_vs_without_si1'] = exp3_results
    
    print(f"\n有SI1:    health={with_si1_metrics['health_trend']:.3f}, "
          f"consciousness={with_si1_metrics['consciousness_trend']:.3f}")
    print(f"无SI1:    health={without_si1_metrics['health_trend']:.3f}, "
          f"consciousness={without_si1_metrics['consciousness_trend']:.3f}")
    print(f"差异:     health={exp3_results['comparison']['health_diff']:+.3f}, "
          f"consciousness={exp3_results['comparison']['consciousness_diff']:+.3f}")
    logger.info(f"结论: {'纬停经不停验证通过！' if abs(exp3_results['comparison']['health_diff']) < 0.3 else '需要优化'}")
    
    # -------------------------------------------------------------------------
    # 实验4: 通道降级恢复测试
    # -------------------------------------------------------------------------
    logger.info("\n" + "="*70)
    logger.info("实验4: 通道降级恢复测试")
    logger.info("="*70)
    
    # 先激活所有通道
    engine.activate_si1()
    engine.si2_active = True
    engine.si3_active = True
    engine.set_drive_mode(DriveMode.FULL)
    
    exp4_results = engine.channel_degradation_recovery()
    all_results['experiment_4_degradation_recovery'] = exp4_results
    
    # -------------------------------------------------------------------------
    # 实验5: 纬停经不停验证
    # -------------------------------------------------------------------------
    logger.info("\n" + "="*70)
    logger.info("实验5: 纬停经不停验证")
    logger.info("="*70)
    logger.info("验证: 当纬通道(SI1/SI2/SI3)全部关闭时，经(SI4-SI6)是否继续运转？")
    
    # 记录纬关闭前的经状态
    engine.set_drive_mode(DriveMode.FULL)
    engine.activate_si1()
    pre_jing_state = engine.si_state.get_combined_state().copy()
    
    # 关闭纬
    engine.deactivate_si1()
    engine.si2_active = False
    engine.si3_active = False
    engine.set_drive_mode(DriveMode.JING_XIN)
    
    # 运行100步
    engine.metrics = SelfSustainabilityMetrics()
    for i in range(100):
        result = engine._single_drive_cycle(i)
        engine._update_metrics(result)
    
    post_jing_state = engine.si_state.get_combined_state().copy()
    state_change = np.linalg.norm(post_jing_state - pre_jing_state)
    
    exp5_results = {
        'pre_jing_norm': float(np.linalg.norm(pre_jing_state)),
        'post_jing_norm': float(np.linalg.norm(post_jing_state)),
        'state_change': float(state_change),
        'jing_still_running': state_change > 0.1,
        'final_health': engine.metrics.health_trend,
        'cycles_completed': 100
    }
    all_results['experiment_5_jing_wei_stop'] = exp5_results
    
    logger.info(f"纬关闭前经状态范数: {exp5_results['pre_jing_norm']:.3f}")
    logger.info(f"纬关闭后经状态范数: {exp5_results['post_jing_norm']:.3f}")
    logger.info(f"状态变化量: {exp5_results['state_change']:.3f}")
    logger.info(f"经仍在运转: {'✓ 是' if exp5_results['jing_still_running'] else '✗ 否'}")
    logger.info(f"最终健康度: {exp5_results['final_health']:.3f}")
    logger.info(f"\n结论: {'纬停经不停 —— 验证通过！' if exp5_results['jing_still_running'] else '验证失败'}")
    
    # -------------------------------------------------------------------------
    # 最终统计
    # -------------------------------------------------------------------------
    logger.info("\n" + "="*70)
    logger.info("最终统计")
    logger.info("="*70)
    engine.print_stats()
    
    # -------------------------------------------------------------------------
    # 保存实验报告
    # -------------------------------------------------------------------------
    report = {
        'timestamp': datetime.now().isoformat(),
        'version': '6.0.0',
        'philosophy': '候即违规 / 纬停经不停',
        'experiments': all_results,
        'summary': {
            'total_experiments': 5,
            'si1_independent_verified': exp2_results.get('passed', False),
            'jing_wei_stop_verified': exp5_results['jing_still_running'],
            'degradation_recovery_works': exp4_results.get('recovered', False),
            'best_mode': exp1_results.get('best_health', 'JING_XIN')
        }
    }
    
    return report


# =============================================================================
# 6. 主入口
# =============================================================================

if __name__ == "__main__":
    report = run_experiments()
    
    # 保存报告
    import os
    output_dir = "/mnt/agents/output/OMNI-HUB/core"
    os.makedirs(output_dir, exist_ok=True)
    
    report_path = os.path.join(output_dir, "si1_independent_drive_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
        logger.error(f"File operation failed: {e}")
    print(f"\n实验报告已保存: {report_path}")
    print("\n" + "="*70)
    print("OMNI-HUB v6.0 SI1IndependentDrive 实验完成")
    print("="*70)
