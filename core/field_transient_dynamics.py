
__version__ = "11.0.0"
"""
OMNI-HUB v3.9 - Field-Transient-Ripple Dynamics Architecture
场-瞬态-涟漪动力学架构 + 正反向驱动V2

Author: OMNI-HUB Core Systems
Version: 3.9.0
Architecture: Field-Transient-Ripple-BidirectionalDrive

Core Concepts:
- Field: 全局态势的连续场表示（11线 × 多维）
- Transient: 场的瞬时扰动/能量脉冲
- Ripple: 瞬态的扩散传播与干涉
- BidirectionalDrive: 正反向驱动耦合
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
from matplotlib.collections import LineCollection
from typing import List, Tuple, Dict, Callable, Optional, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import json
import warnings
from pathlib import Path
import logging

# ============================================================================
# Constants & Configuration
# ============================================================================

NUM_LINES = 11  # 11条线路 (北星/核心线路)
FIELD_DIMENSION = 64  # 场空间分辨率
DEFAULT_DT = 0.01
DAMPING_COEFF = 0.05
WAVE_SPEED = 2.0
DECAY_RATE = 0.1

# 线路语义定义
LINE_NAMES = [
    "NorthStar",      # 北星线路 - 顶层愿景
    "CoreLogic",      # 核心逻辑
    "EmotionFlow",    # 情绪流
    "MemoryWeave",    # 记忆编织
    "IntentionBeam",  # 意图束
    "PerceptionNet",  # 感知网
    "ActionStream",   # 行动流
    "FeedbackLoop",   # 反馈环
    "ResonanceField", # 共振场
    "EmergenceSpark", # 涌现火花
    "BaseFoundation", # 基座基础
]


# ============================================================================
# Data Structures
# ============================================================================

class PulseShape(Enum):
    GAUSSIAN = auto()
    EXPONENTIAL = auto()
    DELTA = auto()
    SINC = auto()
    LORENTZIAN = auto()


class DecayModel(Enum):
    EXPONENTIAL = auto()
    POWER_LAW = auto()
    OSCILLATORY = auto()
    CRITICAL = auto()


@dataclass
class FieldState:
    """场状态表示 - 全局态势的瞬时快照"""
    amplitude: np.ndarray      # 振幅场 [NUM_LINES, FIELD_DIMENSION]
    velocity: np.ndarray       # 速度场 [NUM_LINES, FIELD_DIMENSION]
    phase: np.ndarray          # 相位场 [NUM_LINES, FIELD_DIMENSION]
    timestamp: float = 0.0
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.amplitude.shape != (NUM_LINES, FIELD_DIMENSION):
            raise ValueError(f"振幅场维度错误: {self.amplitude.shape}")
        if self.velocity.shape != (NUM_LINES, FIELD_DIMENSION):
            raise ValueError(f"速度场维度错误: {self.velocity.shape}")
    
    def copy(self) -> 'FieldState':
        return FieldState(
            amplitude=self.amplitude.copy(),
            velocity=self.velocity.copy(),
            phase=self.phase.copy(),
            timestamp=self.timestamp,
            metadata=self.metadata.copy()
        )
    
    def to_dict(self) -> Dict:
        return {
            'amplitude': self.amplitude.tolist(),
            'velocity': self.velocity.tolist(),
            'phase': self.phase.tolist(),
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


@dataclass
class TransientPulse:
    """瞬态脉冲数据结构"""
    position: Tuple[int, int]  # (line_idx, spatial_idx)
    amplitude: float
    width: float
    shape: PulseShape
    energy: float
    birth_time: float
    decay_model: DecayModel
    decay_rate: float
    frequency: float = 0.0
    phase: float = 0.0


@dataclass
class Ripple:
    """涟漪数据结构"""
    origin: Tuple[int, int]    # 起源位置
    amplitude: float           # 当前振幅
    initial_amplitude: float   # 初始振幅
    wavelength: float          # 波长
    wave_number: float         # 波数
    frequency: float           # 频率
    phase: float               # 相位
    velocity: float            # 传播速度
    damping_coeff: float       # 阻尼系数
    birth_time: float          # 诞生时间
    generation: int = 0        # 递归代际
    children: List['Ripple'] = field(default_factory=list)
    
    def age(self, current_time: float) -> float:
        return current_time - self.birth_time


# ============================================================================
# 1. FieldDynamics - 场动力学核心
# ============================================================================

class FieldDynamics:
    """
    场动力学核心类
    
    管理全局场的演化、能量、梯度与平衡点。
    场是所有线路的叠加态，势能与动能的统一场。
    """
    
    def __init__(self, 
                 num_lines: int = NUM_LINES,
                 field_dim: int = FIELD_DIMENSION,
                 dt: float = DEFAULT_DT,
                 damping: float = DAMPING_COEFF,
                 coupling_matrix: Optional[np.ndarray] = None):
        self.num_lines = num_lines
        self.field_dim = field_dim
        self.dt = dt
        self.damping = damping
        self.time = 0.0
        self.history: List[FieldState] = []
        self.energy_history: List[Dict[str, float]] = []
        
        # 线路间耦合矩阵 [num_lines, num_lines]
        if coupling_matrix is None:
            self.coupling = self._init_coupling_matrix()
        else:
            self.coupling = coupling_matrix
        
        # 空间拉普拉斯算子核
        self.laplacian_kernel = np.array([1, -2, 1], dtype=np.float64)
        
        # 初始化场状态
        self.state = self._init_field_state()
        self._record_state()
    
    def _init_coupling_matrix(self) -> np.ndarray:
        """初始化线路间耦合矩阵 - 层次化耦合结构"""
        C = np.zeros((self.num_lines, self.num_lines))
        
        # 北星→所有线路 (强耦合)
        C[0, :] = 0.3
        C[:, 0] = 0.3
        
        # 相邻线路耦合 (带状结构)
        for i in range(self.num_lines - 1):
            C[i, i+1] = 0.2
            C[i+1, i] = 0.2
        
        # 基座←所有线路 (反馈耦合)
        C[-1, :] = 0.25
        C[:, -1] = 0.25
        
        # 自耦合 (内部动力学)
        np.fill_diagonal(C, 0.5)
        
        return C
    
    def _init_field_state(self) -> FieldState:
        """初始化场状态 - 微小随机扰动"""
        np.random.seed(42)
        amp = np.random.randn(self.num_lines, self.field_dim) * 0.1
        vel = np.zeros((self.num_lines, self.field_dim))
        phase = np.random.uniform(0, 2*np.pi, (self.num_lines, self.field_dim))
        
        return FieldState(
            amplitude=amp,
            velocity=vel,
            phase=phase,
            timestamp=0.0,
            metadata={'init_type': 'random_small'}
        )
    
    def _laplacian_1d(self, arr: np.ndarray) -> np.ndarray:
        """一维离散拉普拉斯算子 (周期性边界)"""
        result = np.zeros_like(arr)
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                jm = (j - 1) % self.field_dim
                jp = (j + 1) % self.field_dim
                result[i, j] = arr[i, jm] - 2*arr[i, j] + arr[i, jp]
        return result
    
    def evolve(self, dt: Optional[float] = None, 
               external_force: Optional[np.ndarray] = None,
               num_steps: int = 1) -> FieldState:
        """
        场演化 - 基于波动方程的离散化
        
        ∂²ψ/∂t² = c²∇²ψ - γ∂ψ/∂t + F_ext + coupling
        
        使用Verlet积分保持能量守恒性质
        """
        if dt is None:
            dt = self.dt
        
        for _ in range(num_steps):
            amp = self.state.amplitude
            vel = self.state.velocity
            
            # 空间拉普拉斯 (扩散项)
            laplacian = self._laplacian_1d(amp)
            
            # 线路间耦合
            coupled = self.coupling @ amp
            
            # 加速度 = c²∇²ψ - γv + coupling + external
            acceleration = (WAVE_SPEED**2 * laplacian 
                          - self.damping * vel 
                          + 0.1 * coupled)
            
            if external_force is not None:
                acceleration += external_force
            
            # Verlet积分更新
            new_amp = amp + vel * dt + 0.5 * acceleration * dt**2
            
            # 计算新加速度用于速度更新
            new_laplacian = self._laplacian_1d(new_amp)
            new_coupled = self.coupling @ new_amp
            new_acceleration = (WAVE_SPEED**2 * new_laplacian 
                               - self.damping * vel 
                               + 0.1 * new_coupled)
            if external_force is not None:
                new_acceleration += external_force
            
            new_vel = vel + 0.5 * (acceleration + new_acceleration) * dt
            
            # 相位演化
            new_phase = (self.state.phase + WAVE_SPEED * dt) % (2 * np.pi)
            
            # 更新状态
            self.state = FieldState(
                amplitude=new_amp,
                velocity=new_vel,
                phase=new_phase,
                timestamp=self.time + dt,
                metadata=self.state.metadata.copy()
            )
            
            self.time += dt
            self._record_state()
        
        return self.state
    
    def _record_state(self):
        """记录当前状态到历史"""
        self.history.append(self.state.copy())
        self.energy_history.append({
            'time': self.time,
            'potential': self.potential_energy(),
            'kinetic': self.kinetic_energy(),
            'total': self.total_energy()
        })
    
    def potential_energy(self) -> float:
        """势能: U = ½∫|∇ψ|²dx + ½∫|ψ|²dx (弹性势能 + 自能)"""
        amp = self.state.amplitude
        grad = np.gradient(amp, axis=1)
        elastic = 0.5 * np.sum(grad**2)
        self_energy = 0.5 * np.sum(amp**2)
        coupling_energy = 0.0
        for i in range(self.num_lines):
            for j in range(i+1, self.num_lines):
                coupling_energy += self.coupling[i,j] * np.sum(amp[i] * amp[j])
        return elastic + self_energy + 0.1 * coupling_energy
    
    def kinetic_energy(self) -> float:
        """动能: K = ½∫|∂ψ/∂t|²dx"""
        return 0.5 * np.sum(self.state.velocity**2)
    
    def total_energy(self) -> float:
        """总能量 = 势能 + 动能"""
        return self.potential_energy() + self.kinetic_energy()
    
    def field_gradient(self) -> np.ndarray:
        """场梯度 - 各方向变化率"""
        grad_spatial = np.gradient(self.state.amplitude, axis=1)
        grad_temporal = self.state.velocity
        # 线路间梯度
        grad_line = np.zeros_like(self.state.amplitude)
        for i in range(self.num_lines):
            for j in range(self.num_lines):
                if i != j:
                    grad_line[i] += self.coupling[i,j] * (
                        self.state.amplitude[j] - self.state.amplitude[i]
                    )
        return grad_spatial + 0.1 * grad_temporal + 0.05 * grad_line
    
    def equilibrium_point(self) -> Tuple[np.ndarray, float]:
        """
        平衡点计算 - 寻找场的稳态配置
        返回: (平衡位置, 稳定性指标)
        """
        # 简单平衡点: 振幅最小处
        flat_idx = np.argmin(np.abs(self.state.amplitude).sum(axis=1))
        equilibrium_pos = self.state.amplitude[flat_idx]
        
        # 稳定性 = -λ_max (Hessian最大特征值)
        hessian_approx = np.zeros((self.num_lines, self.num_lines))
        for i in range(self.num_lines):
            for j in range(self.num_lines):
                hessian_approx[i,j] = np.mean(
                    self.state.amplitude[i] * self.state.amplitude[j]
                )
        eigenvalues = np.linalg.eigvalsh(hessian_approx)
        stability = -np.max(eigenvalues)
        
        return equilibrium_pos, stability
    
    def field_coherence(self) -> float:
        """场相干性 - 各线路间的同步程度"""
        coherence_matrix = np.corrcoef(self.state.amplitude)
        # 提取上三角非对角元素
        triu_idx = np.triu_indices(self.num_lines, k=1)
        return np.mean(np.abs(coherence_matrix[triu_idx]))
    
    def get_state(self) -> FieldState:
        return self.state.copy()
    
    def set_state(self, state: FieldState):
        self.state = state.copy()
        self._record_state()


# ============================================================================
# 2. TransientInjector - 瞬态注入器
# ============================================================================

class TransientInjector:
    """
    瞬态注入器
    
    向场中注入能量脉冲，支持多种脉冲形状和衰减模型。
    瞬态是场的局部瞬时扰动，快速衰减/快速响应。
    """
    
    def __init__(self, field_dynamics: FieldDynamics):
        self.fd = field_dynamics
        self.pulses: List[TransientPulse] = []
        self.pulse_history: List[Dict] = []
        self.time = 0.0
    
    def inject(self, 
               position: Tuple[int, int],
               energy: float,
               width: float = 3.0,
               shape: PulseShape = PulseShape.GAUSSIAN,
               decay_model: DecayModel = DecayModel.EXPONENTIAL,
               decay_rate: float = DECAY_RATE,
               frequency: float = 1.0) -> TransientPulse:
        """
        注入能量脉冲到指定位置
        
        Args:
            position: (线路索引, 空间位置)
            energy: 脉冲能量
            width: 脉冲宽度
            shape: 脉冲形状
            decay_model: 衰减模型
            decay_rate: 衰减率
            frequency: 振荡频率
        """
        line_idx, spatial_idx = position
        
        # 生成脉冲形状
        pulse_field = self._generate_pulse(
            shape, spatial_idx, width, energy, frequency
        )
        
        # 注入到场中
        current_amp = self.fd.state.amplitude[line_idx].copy()
        current_vel = self.fd.state.velocity[line_idx].copy()
        
        self.fd.state.amplitude[line_idx] += pulse_field
        self.fd.state.velocity[line_idx] += pulse_field * frequency * 0.5
        
        pulse = TransientPulse(
            position=position,
            amplitude=energy,
            width=width,
            shape=shape,
            energy=energy,
            birth_time=self.time,
            decay_model=decay_model,
            decay_rate=decay_rate,
            frequency=frequency
        )
        
        self.pulses.append(pulse)
        self.pulse_history.append({
            'time': self.time,
            'pulse': pulse,
            'pre_injection_energy': self.fd.total_energy() - np.sum(pulse_field**2)
        })
        
        return pulse
    
    def _generate_pulse(self, shape: PulseShape, center: int, 
                        width: float, amplitude: float, 
                        frequency: float) -> np.ndarray:
        """生成脉冲形状"""
        x = np.arange(self.fd.field_dim)
        dx = np.minimum(np.abs(x - center), 
                        self.fd.field_dim - np.abs(x - center))  # 周期性距离
        
        if shape == PulseShape.GAUSSIAN:
            envelope = amplitude * np.exp(-(dx**2) / (2 * width**2))
        elif shape == PulseShape.EXPONENTIAL:
            envelope = amplitude * np.exp(-np.abs(dx) / width)
        elif shape == PulseShape.DELTA:
            envelope = np.zeros(self.fd.field_dim)
            envelope[center] = amplitude
        elif shape == PulseShape.SINC:
            envelope = amplitude * np.sinc(dx / width)
        elif shape == PulseShape.LORENTZIAN:
            envelope = amplitude * width**2 / (dx**2 + width**2)
        else:
            envelope = amplitude * np.exp(-(dx**2) / (2 * width**2))
        
        # 添加振荡载波
        carrier = np.cos(2 * np.pi * frequency * dx / self.fd.field_dim)
        return envelope * carrier
    
    def pulse_shape(self, pulse: TransientPulse, 
                    spatial_points: Optional[np.ndarray] = None) -> np.ndarray:
        """获取脉冲在任意空间点的形状值"""
        if spatial_points is None:
            spatial_points = np.arange(self.fd.field_dim)
        
        center = pulse.position[1]
        dx = np.minimum(np.abs(spatial_points - center),
                        self.fd.field_dim - np.abs(spatial_points - center))
        
        if pulse.shape == PulseShape.GAUSSIAN:
            return pulse.amplitude * np.exp(-(dx**2) / (2 * pulse.width**2))
        elif pulse.shape == PulseShape.EXPONENTIAL:
            return pulse.amplitude * np.exp(-np.abs(dx) / pulse.width)
        elif pulse.shape == PulseShape.SINC:
            return pulse.amplitude * np.sinc(dx / pulse.width)
        else:
            return pulse.amplitude * np.exp(-(dx**2) / (2 * pulse.width**2))
    
    def decay_model(self, pulse: TransientPulse, 
                    current_time: float) -> float:
        """计算脉冲当前衰减后的振幅"""
        age = current_time - pulse.birth_time
        
        if pulse.decay_model == DecayModel.EXPONENTIAL:
            return pulse.amplitude * np.exp(-pulse.decay_rate * age)
        elif pulse.decay_model == DecayModel.POWER_LAW:
            return pulse.amplitude / (1 + pulse.decay_rate * age)**2
        elif pulse.decay_model == DecayModel.OSCILLATORY:
            return pulse.amplitude * np.exp(-pulse.decay_rate * age) * \
                   np.cos(pulse.frequency * age)
        elif pulse.decay_model == DecayModel.CRITICAL:
            return pulse.amplitude * (1 + pulse.decay_rate * age) * \
                   np.exp(-pulse.decay_rate * age)
        else:
            return pulse.amplitude * np.exp(-pulse.decay_rate * age)
    
    def superpose(self, pulses: List[TransientPulse],
                  line_idx: int = 0) -> np.ndarray:
        """多脉冲叠加 - 瞬态的干涉效应"""
        result = np.zeros(self.fd.field_dim)
        for p in pulses:
            if p.position[0] == line_idx:
                shape = self.pulse_shape(p)
                decay_factor = self.decay_model(p, self.time)
                result += shape * (decay_factor / p.amplitude)
        return result
    
    def measure_transient_lifetime(self, pulse: TransientPulse,
                                    threshold: float = 0.01) -> float:
        """
        测量瞬态寿命 - 振幅衰减到阈值的时间
        
        解析解:
        - 指数衰减: τ = -ln(threshold)/decay_rate
        - 幂律衰减: τ = (1/sqrt(threshold) - 1)/decay_rate
        - 振荡衰减: 包络寿命
        """
        if pulse.decay_model == DecayModel.EXPONENTIAL:
            return -np.log(threshold) / pulse.decay_rate
        elif pulse.decay_model == DecayModel.POWER_LAW:
            return (1/np.sqrt(threshold) - 1) / pulse.decay_rate
        elif pulse.decay_model == DecayModel.OSCILLATORY:
            return -np.log(threshold) / pulse.decay_rate  # 包络寿命
        elif pulse.decay_model == DecayModel.CRITICAL:
            # 临界衰减: (1+λτ)exp(-λτ) = threshold
            # 近似解
            return 2.0 / pulse.decay_rate
        else:
            return -np.log(threshold) / pulse.decay_rate
    
    def update_time(self, dt: float):
        self.time += dt
    
    def get_active_pulses(self, threshold: float = 0.01) -> List[TransientPulse]:
        """获取当前仍活跃的脉冲"""
        active = []
        for p in self.pulses:
            current_amp = self.decay_model(p, self.time)
            if abs(current_amp) > threshold * p.amplitude:
                active.append(p)
        return active


# ============================================================================
# 3. RipplePropagator - 涟漪传播器
# ============================================================================

class RipplePropagator:
    """
    涟漪传播器
    
    瞬态的扩散传播:
    - 单源涟漪向外扩散
    - 多源涟漪干涉相长/相消
    - 递归涟漪（涟漪激发新涟漪）
    """
    
    def __init__(self, field_dynamics: FieldDynamics):
        self.fd = field_dynamics
        self.ripples: List[Ripple] = []
        self.ripple_history: List[Dict] = []
        self.time = 0.0
        self.generation_limit = 3  # 最大递归代际
        self.interference_threshold = 0.5  # 干涉激发阈值
    
    def create_ripple(self,
                      origin: Tuple[int, int],
                      amplitude: float,
                      wavelength: float = 8.0,
                      velocity: float = WAVE_SPEED,
                      damping: float = DAMPING_COEFF,
                      generation: int = 0) -> Ripple:
        """创建新涟漪"""
        ripple = Ripple(
            origin=origin,
            amplitude=amplitude,
            initial_amplitude=amplitude,
            wavelength=wavelength,
            wave_number=2 * np.pi / wavelength,
            frequency=velocity / wavelength,
            phase=0.0,
            velocity=velocity,
            damping_coeff=damping,
            birth_time=self.time,
            generation=generation
        )
        self.ripples.append(ripple)
        return ripple
    
    def propagate_step(self, dt: Optional[float] = None) -> List[Ripple]:
        """
        单步传播所有涟漪
        
        每个涟漪产生扩散场，叠加到场中
        """
        if dt is None:
            dt = self.fd.dt
        
        self.time += dt
        
        # 构建涟漪叠加场
        ripple_field = np.zeros((self.fd.num_lines, self.fd.field_dim))
        
        for ripple in self.ripples:
            field = self._ripple_field(ripple)
            line_idx = ripple.origin[0]
            # 允许涟漪跨线路传播 (简化模型)
            for l in range(self.fd.num_lines):
                coupling = self.fd.coupling[line_idx, l]
                ripple_field[l] += coupling * field
        
        # 将涟漪场作为外力注入场演化
        self.fd.evolve(dt=dt, external_force=ripple_field, num_steps=1)
        
        # 衰减所有涟漪
        active_ripples = []
        for ripple in self.ripples:
            ripple.amplitude = self.damping(ripple)
            if abs(ripple.amplitude) > 0.01 * ripple.initial_amplitude:
                active_ripples.append(ripple)
        
        self.ripples = active_ripples
        
        # 递归涟漪生成
        self.recursive_ripple()
        
        self.ripple_history.append({
            'time': self.time,
            'num_ripples': len(self.ripples),
            'total_amplitude': sum(r.amplitude for r in self.ripples)
        })
        
        return self.ripples
    
    def _ripple_field(self, ripple: Ripple) -> np.ndarray:
        """计算涟漪在当前时刻的场分布"""
        origin_line, origin_pos = ripple.origin
        x = np.arange(self.fd.field_dim)
        
        # 计算到涟漪中心的周期性距离
        dx = np.minimum(np.abs(x - origin_pos),
                        self.fd.field_dim - np.abs(x - origin_pos))
        
        # 涟漪传播距离
        distance = ripple.velocity * (self.time - ripple.birth_time)
        
        # 球面波近似 (一维)
        wave_front = np.exp(-((dx - distance)**2) / (2 * ripple.wavelength**2))
        wave_tail = np.exp(-((dx + distance)**2) / (2 * ripple.wavelength**2))
        
        # 振荡
        oscillation = np.cos(ripple.wave_number * dx - ripple.frequency * 
                            (self.time - ripple.birth_time) + ripple.phase)
        
        # 振幅衰减
        amplitude = ripple.amplitude
        
        field = amplitude * (wave_front + wave_tail) * oscillation
        return field
    
    def damping(self, ripple: Ripple) -> float:
        """涟漪阻尼衰减"""
        age = self.time - ripple.birth_time
        return ripple.amplitude * np.exp(-ripple.damping_coeff * age)
    
    def interference(self, ripples: List[Ripple]) -> np.ndarray:
        """
        多涟漪干涉计算
        
        返回干涉场和干涉统计
        """
        if len(ripples) < 2:
            return np.zeros((self.fd.num_lines, self.fd.field_dim))
        
        # 在第一条线路上计算干涉
        fields = [self._ripple_field(r) for r in ripples]
        
        # 直接叠加 (干涉)
        interference_field = np.zeros(self.fd.field_dim)
        for f in fields:
            interference_field += f
        
        # 计算相长和相消区域
        constructive = np.sum(interference_field > max(np.max(f) for f in fields))
        destructive = np.sum(interference_field < min(np.min(f) for f in fields))
        
        self.interference_stats = {
            'constructive_regions': constructive,
            'destructive_regions': destructive,
            'max_interference': np.max(interference_field),
            'min_interference': np.min(interference_field),
            'std_interference': np.std(interference_field)
        }
        
        return interference_field
    
    def recursive_ripple(self):
        """
        递归涟漪 - 当涟漪振幅足够大时，激发新涟漪
        
        涟漪产生涟漪: 能量在局部集中时产生次级涟漪
        """
        new_ripples = []
        
        for ripple in self.ripples:
            # 检查是否满足激发条件
            if (ripple.generation < self.generation_limit and
                abs(ripple.amplitude) > self.interference_threshold * 
                ripple.initial_amplitude):
                
                # 在涟漪传播前沿激发新涟漪
                distance = ripple.velocity * (self.time - ripple.birth_time)
                new_origin_pos = int((ripple.origin[1] + distance) % 
                                     self.fd.field_dim)
                
                # 新涟漪参数
                new_amplitude = ripple.amplitude * 0.3  # 能量传递效率
                new_wavelength = ripple.wavelength * 0.8
                
                if abs(new_amplitude) > 0.05:
                    child = Ripple(
                        origin=(ripple.origin[0], new_origin_pos),
                        amplitude=new_amplitude,
                        initial_amplitude=new_amplitude,
                        wavelength=new_wavelength,
                        wave_number=2 * np.pi / new_wavelength,
                        frequency=ripple.velocity / new_wavelength,
                        phase=ripple.phase + np.pi,  # 相位反转
                        velocity=ripple.velocity * 0.9,
                        damping_coeff=ripple.damping_coeff * 1.1,
                        birth_time=self.time,
                        generation=ripple.generation + 1
                    )
                    new_ripples.append(child)
                    ripple.children.append(child)
        
        self.ripples.extend(new_ripples)
    
    def measure_ripple_amplitude(self, ripple: Ripple) -> Dict[str, float]:
        """测量涟漪振幅统计"""
        field = self._ripple_field(ripple)
        return {
            'peak_amplitude': np.max(np.abs(field)),
            'rms_amplitude': np.sqrt(np.mean(field**2)),
            'current_theoretical': abs(ripple.amplitude),
            'age': ripple.age(self.time),
            'generation': ripple.generation
        }
    
    def visualize(self, save_path: Optional[str] = None,
                  show_interference: bool = True) -> plt.Figure:
        """可视化涟漪传播"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. 当前场状态热图
        ax1 = axes[0, 0]
        im = ax1.imshow(self.fd.state.amplitude, aspect='auto', 
                        cmap='RdBu_r', interpolation='bilinear')
        ax1.set_yticks(range(len(LINE_NAMES)))
        ax1.set_yticklabels(LINE_NAMES, fontsize=7)
        ax1.set_xlabel('Spatial Position')
        ax1.set_title(f'Field State (t={self.time:.2f})')
        plt.colorbar(im, ax=ax1)
        
        # 2. 各线路振幅剖面
        ax2 = axes[0, 1]
        x = np.arange(self.fd.field_dim)
        for i, name in enumerate(LINE_NAMES):
            alpha = 1.0 if i in [0, 5, 10] else 0.3
            lw = 2 if i in [0, 5, 10] else 1
            ax2.plot(x, self.fd.state.amplitude[i], 
                    label=name if i in [0, 5, 10] else None,
                    alpha=alpha, linewidth=lw)
        ax2.set_xlabel('Spatial Position')
        ax2.set_ylabel('Amplitude')
        ax2.set_title('Line Amplitude Profiles')
        ax2.legend(loc='upper right', fontsize=8)
        ax2.grid(True, alpha=0.3)
        
        # 3. 涟漪树状结构
        ax3 = axes[1, 0]
        self._draw_ripple_tree(ax3)
        ax3.set_title('Recursive Ripple Tree')
        
        # 4. 干涉模式
        ax4 = axes[1, 1]
        if len(self.ripples) >= 2 and show_interference:
            intf = self.interference(self.ripples)
            ax4.fill_between(x, intf, alpha=0.5, color='purple')
            ax4.plot(x, intf, 'purple', linewidth=1.5)
            ax4.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
            ax4.set_xlabel('Spatial Position')
            ax4.set_ylabel('Interference Amplitude')
            ax4.set_title('Multi-Ripple Interference')
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'Need ≥2 ripples\nfor interference',
                    ha='center', va='center', transform=ax4.transAxes,
                    fontsize=12)
            ax4.set_title('Interference Pattern')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        return fig
    
    def _draw_ripple_tree(self, ax):
        """绘制涟漪递归树"""
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, len(self.ripples) + 1)
        ax.axis('off')
        
        if not self.ripples:
            ax.text(0, 0, 'No active ripples', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
            return
        
        # 按代际分组
        gen_groups: Dict[int, List[Ripple]] = {}
        for r in self.ripples:
            gen_groups.setdefault(r.generation, []).append(r)
        
        colors = plt.cm.viridis(np.linspace(0, 1, self.generation_limit + 1))
        
        y_pos = 0
        for gen in sorted(gen_groups.keys()):
            ripples = gen_groups[gen]
            n = len(ripples)
            x_positions = np.linspace(-0.8, 0.8, max(n, 1))
            
            for i, ripple in enumerate(ripples):
                x = x_positions[i] if n > 1 else 0
                size = 100 * abs(ripple.amplitude) / max(abs(r.amplitude) 
                                                          for r in self.ripples)
                ax.scatter(x, y_pos, s=max(size, 20), 
                          color=colors[gen], alpha=0.7, edgecolors='black')
                ax.text(x, y_pos, f'G{gen}\nA:{ripple.amplitude:.2f}',
                       ha='center', va='bottom', fontsize=6)
                
                # 绘制父子连线
                for child in ripple.children:
                    if child in self.ripples:
                        child_idx = self.ripples.index(child)
                        child_gen = child.generation
                        child_y = y_pos + 1.5
                        # 简化的连接线
                        ax.annotate('', xy=(x + 0.1, child_y - 0.3),
                                   xytext=(x, y_pos + 0.1),
                                   arrowprops=dict(arrowstyle='->', 
                                                  color=colors[gen],
                                                  alpha=0.5))
            
            y_pos += 1.5


# ============================================================================
# 4. BidirectionalDriveV2 - 正反向驱动引擎V2
# ============================================================================

class BidirectionalDriveV2:
    """
    正反向驱动引擎V2
    
    - 正向驱动: 北星→基座 (Top-down, 指令/愿景驱动)
    - 反向驱动: 基座→北星 (Bottom-up, 涌现/数据驱动)
    - 双向耦合: 正反向同时作用，形成共振
    """
    
    def __init__(self, field_dynamics: FieldDynamics):
        self.fd = field_dynamics
        self.forward_history: List[Dict] = []
        self.reverse_history: List[Dict] = []
        self.coupled_history: List[Dict] = []
        self.time = 0.0
        
        # 驱动参数
        self.forward_gain = 1.0
        self.reverse_gain = 1.0
        self.coupling_strength = 0.3
        self.resonance_frequency = 1.0
    
    def forward_drive(self, signal: Union[np.ndarray, Callable],
                      line_weights: Optional[np.ndarray] = None) -> np.ndarray:
        """
        正向驱动 - 北星→基座
        
        从顶层线路向下传播信号，权重递减
        """
        if callable(signal):
            sig = signal(self.time)
        else:
            sig = signal
        
        if isinstance(sig, (int, float)):
            sig = np.full(self.fd.field_dim, sig)
        
        if line_weights is None:
            # 默认: 北星最强，向下递减
            line_weights = np.exp(-0.3 * np.arange(self.fd.num_lines))
        
        # 构建正向驱动场
        drive_field = np.zeros((self.fd.num_lines, self.fd.field_dim))
        
        for i in range(self.fd.num_lines):
            # 正向传播: 上层信号衰减后影响下层
            attenuated_signal = sig * line_weights[i]
            # 添加传播延迟 (空间相位)
            phase_shift = np.exp(-1j * 2 * np.pi * i / self.fd.num_lines)
            drive_field[i] = attenuated_signal * np.real(phase_shift)
        
        # 应用驱动
        self.fd.state.amplitude += self.forward_gain * drive_field * self.fd.dt
        
        self.forward_history.append({
            'time': self.time,
            'signal_power': np.sum(sig**2),
            'drive_energy': np.sum(drive_field**2),
            'direction': 'forward'
        })
        
        return drive_field
    
    def reverse_drive(self, signal: Union[np.ndarray, Callable],
                      line_weights: Optional[np.ndarray] = None) -> np.ndarray:
        """
        反向驱动 - 基座→北星
        
        从基座线路向上传播信号，反映涌现信息
        """
        if callable(signal):
            sig = signal(self.time)
        else:
            sig = signal
        
        if isinstance(sig, (int, float)):
            sig = np.full(self.fd.field_dim, sig)
        
        if line_weights is None:
            # 默认: 基座最强，向上递减
            line_weights = np.exp(-0.3 * np.arange(self.fd.num_lines)[::-1])
        
        # 构建反向驱动场
        drive_field = np.zeros((self.fd.num_lines, self.fd.field_dim))
        
        for i in range(self.fd.num_lines):
            # 反向传播: 下层信号影响上层
            attenuated_signal = sig * line_weights[i]
            # 反向相位
            phase_shift = np.exp(1j * 2 * np.pi * i / self.fd.num_lines)
            drive_field[i] = attenuated_signal * np.real(phase_shift)
        
        # 应用驱动
        self.fd.state.amplitude += self.reverse_gain * drive_field * self.fd.dt
        
        self.reverse_history.append({
            'time': self.time,
            'signal_power': np.sum(sig**2),
            'drive_energy': np.sum(drive_field**2),
            'direction': 'reverse'
        })
        
        return drive_field
    
    def couple_drives(self, forward_signal: Union[np.ndarray, Callable],
                      reverse_signal: Union[np.ndarray, Callable]) -> Dict:
        """
        双向耦合 - 正反向驱动同时作用
        
        耦合机制:
        - 正向和反向信号在中间层交互
        - 产生干涉和共振效应
        - 能量在双向之间交换
        """
        # 分别计算两个驱动
        f_drive = self.forward_drive(forward_signal)
        r_drive = self.reverse_drive(reverse_signal)
        
        # 耦合场 - 在中间线路产生交互
        mid_line = self.fd.num_lines // 2
        coupling_field = np.zeros((self.fd.num_lines, self.fd.field_dim))
        
        for i in range(self.fd.num_lines):
            # 耦合强度随距离中间层变化
            distance_from_mid = abs(i - mid_line)
            coupling_weight = np.exp(-distance_from_mid / 3.0)
            
            # 正反向干涉
            interference = f_drive[i] * r_drive[i]
            coupling_field[i] = self.coupling_strength * coupling_weight * interference
        
        # 应用耦合
        self.fd.state.amplitude += coupling_field * self.fd.dt
        
        # 计算耦合指标
        forward_energy = np.sum(f_drive**2)
        reverse_energy = np.sum(r_drive**2)
        coupling_energy = np.sum(coupling_field**2)
        
        # 能量交换效率
        if forward_energy + reverse_energy > 0:
            exchange_efficiency = coupling_energy / (forward_energy + reverse_energy)
        else:
            exchange_efficiency = 0.0
        
        result = {
            'time': self.time,
            'forward_energy': forward_energy,
            'reverse_energy': reverse_energy,
            'coupling_energy': coupling_energy,
            'exchange_efficiency': exchange_efficiency,
            'net_direction': 'forward' if forward_energy > reverse_energy else 'reverse'
        }
        
        self.coupled_history.append(result)
        return result
    
    def drive_resonance(self, frequency: float, 
                        amplitude: float = 1.0,
                        num_cycles: int = 5) -> List[Dict]:
        """
        驱动共振实验
        
        以特定频率驱动，观察共振响应
        """
        results = []
        period = 2 * np.pi / frequency
        dt = self.fd.dt
        steps_per_period = int(period / dt)
        total_steps = steps_per_period * num_cycles
        
        for step in range(total_steps):
            t = step * dt
            # 正向驱动: 正弦信号
            f_signal = amplitude * np.sin(frequency * t)
            # 反向驱动: 相位差
            r_signal = amplitude * np.sin(frequency * t + np.pi/4)
            
            result = self.couple_drives(f_signal, r_signal)
            result['step'] = step
            result['drive_phase'] = (frequency * t) % (2 * np.pi)
            results.append(result)
            self.time += dt
        
        return results
    
    def measure_drive_efficiency(self) -> Dict[str, float]:
        """测量驱动效率"""
        if not self.coupled_history:
            return {'efficiency': 0.0, 'forward_ratio': 0.5}
        
        recent = self.coupled_history[-10:] if len(self.coupled_history) >= 10 \
                 else self.coupled_history
        
        avg_forward = np.mean([r['forward_energy'] for r in recent])
        avg_reverse = np.mean([r['reverse_energy'] for r in recent])
        avg_coupling = np.mean([r['coupling_energy'] for r in recent])
        avg_efficiency = np.mean([r['exchange_efficiency'] for r in recent])
        
        total = avg_forward + avg_reverse
        forward_ratio = avg_forward / total if total > 0 else 0.5
        
        return {
            'efficiency': avg_efficiency,
            'forward_ratio': forward_ratio,
            'reverse_ratio': 1 - forward_ratio,
            'coupling_strength': avg_coupling,
            'balance': 1 - abs(2 * forward_ratio - 1)  # 1=完美平衡
        }


# ============================================================================
# 5. FieldAwareness - 场感知
# ============================================================================

class FieldAwareness:
    """
    场感知类
    
    模拟场的感知、记忆、意图和情绪。
    这些是场的高阶属性，从场的动态模式中涌现。
    """
    
    def __init__(self, field_dynamics: FieldDynamics):
        self.fd = field_dynamics
        self.memory_buffer: List[FieldState] = []
        self.memory_capacity = 100
        self.intention_field = np.zeros((self.fd.num_lines, self.fd.field_dim))
        self.emotion_state = {
            'arousal': 0.0,      # 唤醒度
            'valence': 0.0,      # 效价
            'coherence': 0.0,    # 一致性
            'complexity': 0.0    # 复杂度
        }
        self.emotion_history: List[Dict] = []
    
    def field_perception(self) -> Dict[str, float]:
        """
        场的感知能力 - 从场中提取信息
        
        感知维度:
        - 空间分辨率: 场能分辨的最小尺度
        - 时间灵敏度: 对变化的响应速度
        - 信息容量: 场携带的信息量
        """
        amp = self.fd.state.amplitude
        
        # 空间分辨率 (高频成分)
        fft_amp = np.fft.fft(amp, axis=1)
        high_freq_ratio = np.sum(np.abs(fft_amp[:, self.fd.field_dim//4:])) / \
                          np.sum(np.abs(fft_amp))
        
        # 时间灵敏度 (速度场能量)
        temporal_sensitivity = np.mean(self.fd.state.velocity**2)
        
        # 信息容量 (熵近似)
        prob_dist = np.abs(amp) / (np.sum(np.abs(amp)) + 1e-10)
        entropy = -np.sum(prob_dist * np.log(prob_dist + 1e-10))
        
        # 跨线路信息整合
        cross_line_info = self.fd.field_coherence()
        
        return {
            'spatial_resolution': float(high_freq_ratio),
            'temporal_sensitivity': float(temporal_sensitivity),
            'information_capacity': float(entropy),
            'cross_line_integration': float(cross_line_info),
            'perception_score': float((high_freq_ratio + cross_line_info + 
                                       entropy / self.fd.field_dim) / 3)
        }
    
    def field_memory(self, state: Optional[FieldState] = None) -> Dict:
        """
        场记忆 - 存储和回忆场状态
        
        记忆机制:
        - 短期记忆: 最近的场状态
        - 长期记忆: 重要的场模式
        - 联想记忆: 相似状态的关联
        """
        if state is None:
            state = self.fd.state
        
        # 存入记忆缓冲区
        self.memory_buffer.append(state.copy())
        if len(self.memory_buffer) > self.memory_capacity:
            self.memory_buffer.pop(0)
        
        # 计算记忆统计
        if len(self.memory_buffer) >= 2:
            recent = self.memory_buffer[-10:]
            # 记忆变化率
            changes = [np.mean(np.abs(recent[i].amplitude - recent[i-1].amplitude))
                      for i in range(1, len(recent))]
            avg_change = np.mean(changes) if changes else 0.0
            
            # 记忆稳定性
            stability = 1.0 / (1.0 + avg_change)
            
            # 记忆深度 (时间跨度)
            if len(self.memory_buffer) >= 2:
                memory_depth = self.memory_buffer[-1].timestamp - \
                              self.memory_buffer[0].timestamp
            else:
                memory_depth = 0.0
        else:
            avg_change = 0.0
            stability = 1.0
            memory_depth = 0.0
        
        return {
            'memory_size': len(self.memory_buffer),
            'avg_change_rate': float(avg_change),
            'stability': float(stability),
            'depth': float(memory_depth),
            'recall_quality': float(stability * min(len(self.memory_buffer) / 10, 1.0))
        }
    
    def field_intention(self, target_state: Optional[np.ndarray] = None) -> np.ndarray:
        """
        场意图 - 场的目标导向性
        
        意图场表示场"想要"趋向的状态。
        从当前状态到目标状态的梯度方向。
        """
        current = self.fd.state.amplitude
        
        if target_state is None:
            # 默认意图: 向平滑、有序状态演化
            # 计算局部平滑目标
            target_state = np.zeros_like(current)
            for i in range(self.fd.num_lines):
                target_state[i] = np.convolve(current[i], 
                                              np.ones(5)/5, 
                                              mode='same')
        
        # 意图 = 目标 - 当前 (梯度上升方向)
        intention = target_state - current
        
        # 归一化
        norm = np.linalg.norm(intention)
        if norm > 0:
            intention = intention / norm
        
        self.intention_field = intention
        
        # 计算意图强度
        intention_strength = np.mean(np.abs(intention))
        
        # 意图方向一致性
        direction_consistency = np.corrcoef(
            intention.flatten(), 
            self.fd.state.velocity.flatten()
        )[0, 1] if np.std(intention) > 0 and np.std(self.fd.state.velocity) > 0 else 0.0
        
        return intention
    
    def field_emotion(self) -> Dict[str, float]:
        """
        场情绪 - 从场动态中涌现的情绪状态
        
        情绪维度:
        - Arousal (唤醒): 场的总能量和活动水平
        - Valence (效价): 场的有序/无序程度
        - Coherence (一致性): 各线路的同步程度
        - Complexity (复杂度): 场的结构复杂度
        """
        amp = self.fd.state.amplitude
        vel = self.fd.state.velocity
        
        # Arousal: 总能量
        total_energy = np.mean(amp**2) + np.mean(vel**2)
        arousal = np.tanh(total_energy * 2)
        
        # Valence: 有序度 (负=混沌, 正=有序)
        # 用熵的补数
        flat_amp = np.abs(amp.flatten())
        prob = flat_amp / (np.sum(flat_amp) + 1e-10)
        entropy = -np.sum(prob * np.log(prob + 1e-10))
        max_entropy = np.log(len(prob))
        valence = 2 * (1 - entropy / max_entropy) - 1
        
        # Coherence: 线路间相关
        coherence = self.fd.field_coherence()
        
        # Complexity: 梯度复杂度
        grad = np.gradient(amp)
        complexity = np.mean([np.std(g) for g in grad])
        
        self.emotion_state = {
            'arousal': float(arousal),
            'valence': float(valence),
            'coherence': float(coherence),
            'complexity': float(complexity)
        }
        
        self.emotion_history.append({
            'time': self.fd.time,
            **self.emotion_state
        })
        
        return self.emotion_state


# ============================================================================
# Experiment Runner - 实验运行器
# ============================================================================

class ExperimentRunner:
    """实验运行器 - 执行所有关键实验"""
    
    def __init__(self, output_dir: str = "/mnt/agents/output/OMNI-HUB/viz"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, Dict] = {}
    
    def run_all(self) -> Dict[str, Dict]:
        """运行所有实验"""
        logger.info("=" * 70)
        logger.info("OMNI-HUB v3.9 - Field-Transient-Ripple Dynamics Experiments")
        logger.info("=" * 70)
        
        self.experiment_1_field_evolution()
        self.experiment_2_transient_injection()
        self.experiment_3_ripple_propagation()
        self.experiment_4_bidirectional_drive()
        self.experiment_5_energy_conservation()
        self.experiment_6_coverage_validation()
        
        return self.results
    
    def experiment_1_field_evolution(self):
        """实验1: 场演化 - 从初始态到稳态"""
        logger.info("\n[实验1] 场演化: 初始态 → 稳态")
        
        fd = FieldDynamics()
        awareness = FieldAwareness(fd)
        
        # 演化
        times = []
        energies = []
        coherences = []
        
        for step in range(500):
            fd.evolve(num_steps=1)
            times.append(fd.time)
            energies.append(fd.total_energy())
            coherences.append(fd.field_coherence())
            awareness.field_memory()
            awareness.field_emotion()
        
        # 可视化
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 能量演化
        ax1 = axes[0, 0]
        ax1.plot(times, energies, 'b-', linewidth=1)
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Total Energy')
        ax1.set_title('E1: Field Energy Evolution')
        ax1.grid(True, alpha=0.3)
        
        # 相干性演化
        ax2 = axes[0, 1]
        ax2.plot(times, coherences, 'g-', linewidth=1)
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Field Coherence')
        ax2.set_title('E1: Field Coherence Evolution')
        ax2.grid(True, alpha=0.3)
        
        # 初始态 vs 稳态
        ax3 = axes[1, 0]
        im1 = ax3.imshow(fd.history[0].amplitude, aspect='auto', 
                         cmap='RdBu_r')
        ax3.set_title('E1: Initial State')
        plt.colorbar(im1, ax=ax3)
        
        ax4 = axes[1, 1]
        im2 = ax4.imshow(fd.state.amplitude, aspect='auto', 
                         cmap='RdBu_r')
        ax4.set_title('E1: Steady State')
        plt.colorbar(im2, ax=ax4)
        
        plt.tight_layout()
        save_path = self.output_dir / 'exp1_field_evolution.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        # 记录结果
        self.results['exp1'] = {
            'name': 'Field Evolution',
            'final_energy': float(energies[-1]),
            'energy_variance': float(np.var(energies[-100:])),
            'final_coherence': float(coherences[-1]),
            'convergence_steps': int(np.argmax(np.array(energies) > 0.95 * energies[-1])),
            'plot': str(save_path)
        }
        logger.info(f"  ✓ 能量收敛至: {energies[-1]:.4f}")
        logger.info(f"  ✓ 最终相干性: {coherences[-1]:.4f}")
        logger.info(f"  ✓ 图表: {save_path}")
    
    def experiment_2_transient_injection(self):
        """实验2: 瞬态注入 - 单脉冲→响应→衰减"""
        logger.info("\n[实验2] 瞬态注入: 单脉冲 → 响应 → 衰减")
        
        fd = FieldDynamics()
        injector = TransientInjector(fd)
        
        # 注入脉冲
        pulse = injector.inject(
            position=(5, 32),  # 中间线路，中间位置
            energy=5.0,
            width=4.0,
            shape=PulseShape.GAUSSIAN,
            decay_model=DecayModel.EXPONENTIAL,
            decay_rate=0.5,
            frequency=2.0
        )
        
        # 演化并记录
        times = []
        amplitudes = []
        energies = []
        decay_theoretical = []
        
        for step in range(300):
            fd.evolve(num_steps=1)
            injector.update_time(fd.dt)
            times.append(fd.time)
            
            # 测量中心点振幅
            center_amp = fd.state.amplitude[5, 32]
            amplitudes.append(center_amp)
            energies.append(fd.total_energy())
            
            # 理论衰减
            decay_theoretical.append(
                injector.decay_model(pulse, fd.time)
            )
        
        # 可视化
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 脉冲衰减曲线
        ax1 = axes[0, 0]
        ax1.plot(times, amplitudes, 'b-', label='Actual', linewidth=1.5)
        ax1.plot(times, decay_theoretical, 'r--', label='Theoretical', linewidth=1.5)
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Amplitude at Injection Point')
        ax1.set_title('E2: Transient Decay')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 能量变化
        ax2 = axes[0, 1]
        ax2.plot(times, energies, 'g-', linewidth=1)
        ax2.axvline(x=0, color='r', linestyle='--', label='Injection')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Total Energy')
        ax2.set_title('E2: Energy Response')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 空间传播快照
        ax3 = axes[1, 0]
        for t_idx in [0, 50, 100, 200]:
            if t_idx < len(fd.history):
                ax3.plot(fd.history[t_idx].amplitude[5], 
                        label=f't={fd.history[t_idx].timestamp:.2f}')
        ax3.set_xlabel('Spatial Position')
        ax3.set_ylabel('Amplitude')
        ax3.set_title('E2: Spatial Propagation')
        ax3.legend(fontsize=8)
        ax3.grid(True, alpha=0.3)
        
        # 瞬态寿命分析
        ax4 = axes[1, 1]
        shapes = [PulseShape.GAUSSIAN, PulseShape.EXPONENTIAL, 
                  PulseShape.SINC, PulseShape.LORENTZIAN]
        decays = [DecayModel.EXPONENTIAL, DecayModel.POWER_LAW,
                  DecayModel.OSCILLATORY, DecayModel.CRITICAL]
        lifetimes = []
        labels = []
        for s, d in zip(shapes, decays):
            p = TransientPulse(
                position=(0, 0), amplitude=1.0, width=3.0,
                shape=s, energy=1.0, birth_time=0.0,
                decay_model=d, decay_rate=0.3
            )
            lt = injector.measure_transient_lifetime(p)
            lifetimes.append(lt)
            labels.append(f'{s.name}-{d.name}')
        
        ax4.bar(range(len(lifetimes)), lifetimes, color='skyblue', edgecolor='navy')
        ax4.set_xticks(range(len(labels)))
        ax4.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)
        ax4.set_ylabel('Lifetime')
        ax4.set_title('E2: Transient Lifetime by Type')
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        save_path = self.output_dir / 'exp2_transient_injection.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        self.results['exp2'] = {
            'name': 'Transient Injection',
            'pulse_lifetime': float(injector.measure_transient_lifetime(pulse)),
            'peak_response': float(max(amplitudes)),
            'energy_dissipation': float(energies[0] - energies[-1]),
            'plot': str(save_path)
        }
        logger.info(f"  ✓ 脉冲寿命: {injector.measure_transient_lifetime(pulse):.4f}")
        logger.info(f"  ✓ 峰值响应: {max(amplitudes):.4f}")
        logger.info(f"  ✓ 能量耗散: {energies[0] - energies[-1]:.4f}")
        logger.info(f"  ✓ 图表: {save_path}")
    
    def experiment_3_ripple_propagation(self):
        """实验3: 涟漪传播 - 单源→多源干涉→递归"""
        logger.info("\n[实验3] 涟漪传播: 单源 → 多源干涉 → 递归")
        
        fd = FieldDynamics()
        propagator = RipplePropagator(fd)
        
        # 创建多个涟漪源
        ripples = []
        
        # 源1: 北星线路
        r1 = propagator.create_ripple(
            origin=(0, 16), amplitude=3.0, wavelength=8.0
        )
        ripples.append(r1)
        
        # 源2: 中间线路
        r2 = propagator.create_ripple(
            origin=(5, 32), amplitude=2.5, wavelength=6.0
        )
        ripples.append(r2)
        
        # 源3: 基座线路
        r3 = propagator.create_ripple(
            origin=(10, 48), amplitude=2.0, wavelength=10.0
        )
        ripples.append(r3)
        
        # 演化
        snapshots = []
        all_ripples_count = []
        
        for step in range(200):
            propagator.propagate_step()
            all_ripples_count.append(len(propagator.ripples))
            if step in [0, 50, 100, 150, 199]:
                snapshots.append(fd.state.amplitude.copy())
        
        # 可视化
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 涟漪传播动画帧
        for idx, (snap, step) in enumerate(zip(snapshots, [0, 50, 100, 150, 199])):
            ax = fig.add_subplot(gs[idx // 3, idx % 3])
            im = ax.imshow(snap, aspect='auto', cmap='RdBu_r',
                          vmin=-2, vmax=2, interpolation='bilinear')
            ax.set_title(f't={step*fd.dt:.2f}')
            ax.set_yticks(range(0, len(LINE_NAMES), 2))
            ax.set_yticklabels([LINE_NAMES[i] for i in range(0, len(LINE_NAMES), 2)], 
                              fontsize=6)
            plt.colorbar(im, ax=ax, fraction=0.046)
        
        # 涟漪数量演化
        ax_ripple = fig.add_subplot(gs[1, 2])
        ax_ripple.plot(all_ripples_count, 'purple', linewidth=1.5)
        ax_ripple.set_xlabel('Step')
        ax_ripple.set_ylabel('Active Ripples')
        ax_ripple.set_title('Recursive Ripple Count')
        ax_ripple.grid(True, alpha=0.3)
        
        # 干涉模式
        ax_intf = fig.add_subplot(gs[2, 0])
        if len(propagator.ripples) >= 2:
            intf = propagator.interference(propagator.ripples)
            ax_intf.plot(intf, 'purple', linewidth=1.5)
            ax_intf.fill_between(range(len(intf)), intf, alpha=0.3, color='purple')
            ax_intf.axhline(y=0, color='k', linewidth=0.5)
            ax_intf.set_xlabel('Position')
            ax_intf.set_ylabel('Interference')
            ax_intf.set_title('Interference Pattern')
            ax_intf.grid(True, alpha=0.3)
        
        # 振幅统计
        ax_stats = fig.add_subplot(gs[2, 1])
        if propagator.ripples:
            gens = [r.generation for r in propagator.ripples]
            amps = [r.amplitude for r in propagator.ripples]
            colors = plt.cm.viridis(np.linspace(0, 1, max(gens)+1))
            for g in set(gens):
                mask = [i for i, gen in enumerate(gens) if gen == g]
                ax_stats.scatter([gens[i] for i in mask], 
                               [amps[i] for i in mask],
                               color=colors[g], label=f'Gen {g}', s=50)
            ax_stats.set_xlabel('Generation')
            ax_stats.set_ylabel('Amplitude')
            ax_stats.set_title('Ripple Amplitude by Generation')
            ax_stats.legend(fontsize=8)
            ax_stats.grid(True, alpha=0.3)
        
        # 场状态热图最终
        ax_final = fig.add_subplot(gs[2, 2])
        im_final = ax_final.imshow(fd.state.amplitude, aspect='auto',
                                   cmap='RdBu_r', interpolation='bilinear')
        ax_final.set_title('Final Field State')
        plt.colorbar(im_final, ax=ax_final, fraction=0.046)
        
        save_path = self.output_dir / 'exp3_ripple_propagation.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        self.results['exp3'] = {
            'name': 'Ripple Propagation',
            'initial_ripples': 3,
            'final_ripples': len(propagator.ripples),
            'max_generation': max((r.generation for r in propagator.ripples), default=0),
            'total_recursive_created': sum(1 for r in propagator.ripples if r.generation > 0),
            'plot': str(save_path)
        }
        logger.info(f"  ✓ 初始涟漪: 3")
        logger.info(f"  ✓ 最终涟漪: {len(propagator.ripples)}")
        logger.info(f"  ✓ 最大递归代际: {self.results['exp3']['max_generation']}")
        logger.info(f"  ✓ 图表: {save_path}")
    
    def experiment_4_bidirectional_drive(self):
        """实验4: 正反向驱动对比"""
        logger.info("\n[实验4] 正反向驱动: 正向指令 vs 反向涌现")
        
        # 正向驱动实验
        fd_fwd = FieldDynamics()
        drive_fwd = BidirectionalDriveV2(fd_fwd)
        
        fwd_energies = []
        for step in range(200):
            signal = np.sin(2 * np.pi * 0.5 * fd_fwd.time)
            drive_fwd.forward_drive(signal)
            fd_fwd.evolve(num_steps=1)
            drive_fwd.time += fd_fwd.dt
            fwd_energies.append(fd_fwd.total_energy())
        
        # 反向驱动实验
        fd_rev = FieldDynamics()
        drive_rev = BidirectionalDriveV2(fd_rev)
        
        rev_energies = []
        for step in range(200):
            # 反向信号: 从基座涌现的随机模式
            signal = np.random.randn(fd_rev.field_dim) * 0.5
            drive_rev.reverse_drive(signal)
            fd_rev.evolve(num_steps=1)
            drive_rev.time += fd_rev.dt
            rev_energies.append(fd_rev.total_energy())
        
        # 双向耦合实验
        fd_coupled = FieldDynamics()
        drive_coupled = BidirectionalDriveV2(fd_coupled)
        
        coupled_results = []
        for step in range(200):
            f_sig = np.sin(2 * np.pi * 0.5 * fd_coupled.time)
            r_sig = np.random.randn(fd_coupled.field_dim) * 0.3
            result = drive_coupled.couple_drives(f_sig, r_sig)
            fd_coupled.evolve(num_steps=1)
            drive_coupled.time += fd_coupled.dt
            coupled_results.append(result)
        
        # 可视化
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        times = np.arange(200) * fd_fwd.dt
        
        # 能量对比
        ax1 = axes[0, 0]
        ax1.plot(times, fwd_energies, 'b-', label='Forward Drive', linewidth=1.5)
        ax1.plot(times, rev_energies, 'r-', label='Reverse Drive', linewidth=1.5)
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Total Energy')
        ax1.set_title('E4: Forward vs Reverse Drive')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 耦合效率
        ax2 = axes[0, 1]
        efficiencies = [r['exchange_efficiency'] for r in coupled_results]
        fwd_e = [r['forward_energy'] for r in coupled_results]
        rev_e = [r['reverse_energy'] for r in coupled_results]
        ax2.plot(times, efficiencies, 'purple', label='Efficiency', linewidth=1.5)
        ax2_twin = ax2.twinx()
        ax2_twin.plot(times, fwd_e, 'b--', alpha=0.5, label='Forward Energy')
        ax2_twin.plot(times, rev_e, 'r--', alpha=0.5, label='Reverse Energy')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Coupling Efficiency', color='purple')
        ax2_twin.set_ylabel('Drive Energy')
        ax2.set_title('E4: Bidirectional Coupling')
        ax2.legend(loc='upper left')
        ax2_twin.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)
        
        # 场状态对比
        ax3 = axes[1, 0]
        im1 = ax3.imshow(fd_fwd.state.amplitude, aspect='auto', cmap='RdBu_r')
        ax3.set_title('Forward Drive Final State')
        plt.colorbar(im1, ax=ax3)
        
        ax4 = axes[1, 1]
        im2 = ax4.imshow(fd_rev.state.amplitude, aspect='auto', cmap='RdBu_r')
        ax4.set_title('Reverse Drive Final State')
        plt.colorbar(im2, ax=ax4)
        
        plt.tight_layout()
        save_path = self.output_dir / 'exp4_bidirectional_drive.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        self.results['exp4'] = {
            'name': 'Bidirectional Drive',
            'forward_final_energy': float(fwd_energies[-1]),
            'reverse_final_energy': float(rev_energies[-1]),
            'coupled_efficiency': float(np.mean(efficiencies)),
            'drive_balance': float(drive_coupled.measure_drive_efficiency()['balance']),
            'plot': str(save_path)
        }
        logger.info(f"  ✓ 正向终能: {fwd_energies[-1]:.4f}")
        logger.info(f"  ✓ 反向终能: {rev_energies[-1]:.4f}")
        logger.info(f"  ✓ 耦合效率: {np.mean(efficiencies):.4f}")
        logger.info(f"  ✓ 图表: {save_path}")
    
    def experiment_5_energy_conservation(self):
        """实验5: 能量守恒验证"""
        logger.info("\n[实验5] 能量守恒验证")
        
        # 无外力情况下的能量守恒
        fd = FieldDynamics(damping=0.0)  # 关闭阻尼
        
        times = []
        potentials = []
        kinetics = []
        totals = []
        
        for step in range(500):
            fd.evolve(num_steps=1)
            times.append(fd.time)
            potentials.append(fd.potential_energy())
            kinetics.append(fd.kinetic_energy())
            totals.append(fd.total_energy())
        
        # 有阻尼情况
        fd_damp = FieldDynamics(damping=0.1)
        totals_damp = []
        for step in range(500):
            fd_damp.evolve(num_steps=1)
            totals_damp.append(fd_damp.total_energy())
        
        # 可视化
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 无阻尼能量
        ax1 = axes[0, 0]
        ax1.plot(times, potentials, 'b-', label='Potential', linewidth=1)
        ax1.plot(times, kinetics, 'r-', label='Kinetic', linewidth=1)
        ax1.plot(times, totals, 'g--', label='Total', linewidth=2)
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Energy')
        ax1.set_title('E5: Energy Conservation (No Damping)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 总能量漂移
        ax2 = axes[0, 1]
        energy_drift = np.array(totals) - totals[0]
        ax2.plot(times, energy_drift, 'purple', linewidth=1)
        ax2.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Energy Drift')
        ax2.set_title(f'E5: Energy Drift (max={np.max(np.abs(energy_drift)):.6f})')
        ax2.grid(True, alpha=0.3)
        
        # 阻尼能量衰减
        ax3 = axes[1, 0]
        ax3.plot(times, totals_damp, 'orange', linewidth=1.5)
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Total Energy')
        ax3.set_title('E5: Energy with Damping')
        ax3.grid(True, alpha=0.3)
        
        # 能量分布直方图
        ax4 = axes[1, 1]
        ax4.hist(totals, bins=30, alpha=0.7, color='green', edgecolor='black')
        ax4.axvline(x=np.mean(totals), color='red', linestyle='--', 
                   label=f'Mean={np.mean(totals):.4f}')
        ax4.set_xlabel('Total Energy')
        ax4.set_ylabel('Frequency')
        ax4.set_title('E5: Energy Distribution')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_path = self.output_dir / 'exp5_energy_conservation.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        self.results['exp5'] = {
            'name': 'Energy Conservation',
            'initial_energy': float(totals[0]),
            'final_energy': float(totals[-1]),
            'max_drift': float(np.max(np.abs(energy_drift))),
            'relative_drift': float(np.max(np.abs(energy_drift)) / totals[0]),
            'damping_halflife': float(times[np.argmin(np.abs(np.array(totals_damp) - 0.5*totals_damp[0]))]) if any(np.array(totals_damp) < 0.5*totals_damp[0]) else None,
            'plot': str(save_path)
        }
        logger.info(f"  ✓ 初始能量: {totals[0]:.4f}")
        logger.info(f"  ✓ 最终能量: {totals[-1]:.4f}")
        logger.info(f"  ✓ 最大漂移: {np.max(np.abs(energy_drift)):.6f}")
        logger.info(f"  ✓ 相对漂移: {self.results['exp5']['relative_drift']:.6f}")
        logger.info(f"  ✓ 图表: {save_path}")
    
    def experiment_6_coverage_validation(self):
        """实验6: 覆盖验证 - 场-瞬态-涟漪能否替代大讨论大协作"""
        logger.info("\n[实验6] 覆盖验证: 场-瞬态-涟漪 vs 大讨论大协作")
        
        # 模拟场景: 多智能体通过场进行"讨论"和"协作"
        fd = FieldDynamics()
        injector = TransientInjector(fd)
        propagator = RipplePropagator(fd)
        drive = BidirectionalDriveV2(fd)
        awareness = FieldAwareness(fd)
        
        # 指标记录
        discussion_coverage = []  # 讨论覆盖度
        collaboration_sync = []   # 协作同步度
        emergence_score = []      # 涌现分数
        
        # 模拟"讨论": 多个瞬态注入 (模拟不同观点)
        num_agents = 5
        for round_idx in range(10):
            # 每个"回合"，多个agent注入观点
            for agent in range(num_agents):
                pos = (np.random.randint(0, NUM_LINES), 
                       np.random.randint(0, FIELD_DIMENSION))
                energy = np.random.uniform(1, 3)
                injector.inject(pos, energy, 
                               shape=np.random.choice(list(PulseShape)),
                               decay_model=DecayModel.EXPONENTIAL)
            
            # 演化: 观点传播 (涟漪)
            for _ in range(20):
                propagator.propagate_step()
                
                # 正向驱动: 顶层决策
                drive.forward_drive(np.sin(fd.time))
                
                # 反向驱动: 底层反馈
                drive.reverse_drive(np.random.randn(FIELD_DIMENSION) * 0.2)
                
                # 记录指标
                cov = fd.field_coherence()
                sync = np.std(fd.state.amplitude) / (np.mean(np.abs(fd.state.amplitude)) + 1e-10)
                
                # 涌现: 检测高阶模式
                fft = np.fft.fft2(fd.state.amplitude)
                emergence = np.sum(np.abs(fft)**2) / (NUM_LINES * FIELD_DIMENSION)
                
                discussion_coverage.append(cov)
                collaboration_sync.append(1.0 / (1.0 + sync))
                emergence_score.append(emergence)
                
                awareness.field_emotion()
                awareness.field_memory()
        
        # 可视化
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        steps = range(len(discussion_coverage))
        
        # 讨论覆盖度
        ax1 = axes[0, 0]
        ax1.plot(steps, discussion_coverage, 'b-', linewidth=1)
        ax1.set_xlabel('Simulation Step')
        ax1.set_ylabel('Coverage (Coherence)')
        ax1.set_title('E6: Discussion Coverage')
        ax1.grid(True, alpha=0.3)
        
        # 协作同步度
        ax2 = axes[0, 1]
        ax2.plot(steps, collaboration_sync, 'g-', linewidth=1)
        ax2.set_xlabel('Simulation Step')
        ax2.set_ylabel('Collaboration Sync')
        ax2.set_title('E6: Collaboration Synchronization')
        ax2.grid(True, alpha=0.3)
        
        # 涌现分数
        ax3 = axes[1, 0]
        ax3.plot(steps, emergence_score, 'purple', linewidth=1)
        ax3.set_xlabel('Simulation Step')
        ax3.set_ylabel('Emergence Score')
        ax3.set_title('E6: Emergence Score')
        ax3.grid(True, alpha=0.3)
        
        # 综合对比雷达图
        ax4 = axes[1, 1]
        
        # 计算各维度平均值
        metrics = {
            'Coverage': np.mean(discussion_coverage),
            'Sync': np.mean(collaboration_sync),
            'Emergence': np.mean(emergence_score) / max(emergence_score) if max(emergence_score) > 0 else 0,
            'Energy': np.mean([e['total'] for e in fd.energy_history[-50:]]) / 10 if fd.energy_history else 0,
            'Coherence': fd.field_coherence()
        }
        
        categories = list(metrics.keys())
        values = list(metrics.values())
        values += values[:1]  # 闭合
        
        angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))
        
        ax4 = plt.subplot(2, 2, 4, polar=True)
        ax4.plot(angles, values, 'o-', linewidth=2, color='navy')
        ax4.fill(angles, values, alpha=0.25, color='skyblue')
        ax4.set_xticks(angles[:-1])
        ax4.set_xticklabels(categories)
        ax4.set_title('E6: Coverage Metrics Radar', pad=20)
        ax4.set_ylim(0, 1)
        
        plt.tight_layout()
        save_path = self.output_dir / 'exp6_coverage_validation.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        self.results['exp6'] = {
            'name': 'Coverage Validation',
            'avg_coverage': float(np.mean(discussion_coverage)),
            'avg_sync': float(np.mean(collaboration_sync)),
            'avg_emergence': float(np.mean(emergence_score)),
            'final_coherence': float(fd.field_coherence()),
            'metrics': {k: float(v) for k, v in metrics.items()},
            'plot': str(save_path)
        }
        logger.info(f"  ✓ 平均覆盖度: {np.mean(discussion_coverage):.4f}")
        logger.info(f"  ✓ 平均同步度: {np.mean(collaboration_sync):.4f}")
        logger.info(f"  ✓ 平均涌现分: {np.mean(emergence_score):.4f}")
        logger.info(f"  ✓ 最终相干性: {fd.field_coherence():.4f}")
        logger.info(f"  ✓ 图表: {save_path}")


# ============================================================================
# Main Entry Point
# ============================================================================
"""
OMNI-HUB v11.0 — field_transient_dynamics
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""

def main():
    """主入口 - 运行所有实验"""
    runner = ExperimentRunner()
    results = runner.run_all()
    
    logger.info("\n" + "=" * 70)
    logger.info("实验完成 - 结果摘要")
    logger.info("=" * 70)
    
    for exp_id, result in results.items():
        logger.info(f"\n[{exp_id}] {result['name']}")
        for key, value in result.items():
            if key != 'plot' and key != 'metrics':
                logger.info(f"  {key}: {value}")
    
    # 保存结果到JSON
    results_path = Path("/mnt/agents/output/OMNI-HUB/core") / 'experiment_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
        logger.error(f"File operation failed: {e}")
    logger.info(f"\n结果已保存至: {results_path}")
    
    return results


if __name__ == "__main__":
    main()
