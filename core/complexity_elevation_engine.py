
__version__ = "11.0.0"
"""
OMNI-HUB v4.1 ComplexityElevationEngine
========================================
复杂度提升引擎 — 驱动系统从简单到复杂的相变跃迁

核心命题：系统复杂度不是线性增长，而是在临界点附近发生相变/跃迁。

理论支撑：
1. 自组织临界性(SOC) — Bak-Tang-Wiesenfeld 沙堆模型
2. 相变理论 — 序参量、临界指数、标度律
3. 分形几何 — 自相似结构、分形维数
4. 混沌理论 — Lyapunov指数、对初值敏感性
5. 信息论 — Kolmogorov复杂度、Shannon熵

Author: OMNI-HUB Architecture Team
Version: 4.1.0
"""

import numpy as np
import numpy.linalg as la
from typing import List, Tuple, Dict, Optional, Callable
from collections import deque
from dataclasses import dataclass, field
import warnings
import math
from scipy import stats
from scipy.ndimage import gaussian_filter1d
import logging

# ============================================================================
# 数据结构与配置
# ============================================================================

@dataclass
class ComplexityMetrics:
    """复杂度指标容器"""
    kolmogorov: float = 0.0
    network: float = 0.0
    fractal: float = 0.0
    lyapunov: float = 0.0
    entropy: float = 0.0
    composite: float = 0.0  # 综合复杂度
    timestamp: int = 0

@dataclass
class PhaseTransitionEvent:
    """相变事件记录"""
    step: int
    phase_before: str
    phase_after: str
    order_parameter_jump: float
    complexity_jump: float
    critical_exponent: float
    description: str

@dataclass
class ElevationHistory:
    """提升历史记录"""
    steps: List[int] = field(default_factory=list)
    metrics_history: List[ComplexityMetrics] = field(default_factory=list)
    phase_history: List[str] = field(default_factory=list)
    transition_events: List[PhaseTransitionEvent] = field(default_factory=list)
    avalanche_sizes: List[int] = field(default_factory=list)
    order_parameters: List[float] = field(default_factory=list)

# ============================================================================
# 1. SandpileModel — 沙堆模型（自组织临界性）
# ============================================================================

class SandpileModel:
    """
    Bak-Tang-Wiesenfeld 沙堆模型实现
    
    核心机制：
    - 在网格上逐粒添加沙子
    - 当某格沙子数超过阈值时发生崩塌，沙子分配到邻居
    - 崩塌可能引发级联反应（avalanche）
    - 在临界态时，崩塌大小服从幂律分布 P(s) ~ s^(-τ)
    """
    
    def __init__(self, size: int = 50, threshold: int = 4, dimensions: int = 2):
        """
        初始化沙堆模型
        
        Args:
            size: 网格尺寸（一维长度，总格子数为size^dimensions）
            threshold: 崩塌阈值（每格最多容纳的沙子数）
            dimensions: 维度（1, 2, 或 3）
        """
        self.size = size
        self.threshold = threshold
        self.dimensions = dimensions
        
        # 初始化网格
        if dimensions == 1:
            self.grid = np.zeros(size, dtype=np.int32)
        elif dimensions == 2:
            self.grid = np.zeros((size, size), dtype=np.int32)
        elif dimensions == 3:
            self.grid = np.zeros((size, size, size), dtype=np.int32)
        else:
            raise ValueError("dimensions must be 1, 2, or 3")
        
        # 崩塌历史
        self.avalanche_sizes: List[int] = []
        self.avalanche_durations: List[int] = []
        self.total_grains_added: int = 0
        self.total_topplings: int = 0
        
    def add_grain(self, position: Optional[Tuple] = None) -> int:
        """
        在指定位置（或随机位置）添加一粒沙
        
        Returns:
            avalanche_size: 此次添加引发的崩塌大小
        """
        if position is None:
            if self.dimensions == 1:
                position = (np.random.randint(0, self.size),)
            elif self.dimensions == 2:
                position = (np.random.randint(0, self.size), 
                           np.random.randint(0, self.size))
            else:
                position = (np.random.randint(0, self.size),
                           np.random.randint(0, self.size),
                           np.random.randint(0, self.size))
        
        # 添加沙子
        self.grid[position] += 1
        self.total_grains_added += 1
        
        # 处理崩塌
        avalanche_size = self.avalanche()
        self.avalanche_sizes.append(avalanche_size)
        
        return avalanche_size
    
    def avalanche(self) -> int:
        """
        处理所有超过阈值的格子，返回总崩塌大小
        
        崩塌规则：
        - 超过阈值的格子崩塌，沙子数减threshold
        - 每个邻居获得1粒沙
        - 边界处的沙子丢失（开边界条件，驱动系统远离平衡态）
        """
        toppling_count = 0
        duration = 0
        
        if self.dimensions == 2:
            while True:
                # 找到所有超过阈值的格子
                unstable = np.argwhere(self.grid >= self.threshold)
                if len(unstable) == 0:
                    break
                
                duration += 1
                
                # 处理每个不稳定格子
                for (i, j) in unstable:
                    # 计算要分配的沙子数（等于阈值）
                    grains_to_distribute = self.threshold
                    self.grid[i, j] -= grains_to_distribute
                    toppling_count += 1
                    
                    # 分配到4个邻居（上下左右）
                    neighbors = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
                    for ni, nj in neighbors:
                        if 0 <= ni < self.size and 0 <= nj < self.size:
                            self.grid[ni, nj] += 1
        
        elif self.dimensions == 1:
            while True:
                unstable = np.where(self.grid >= self.threshold)[0]
                if len(unstable) == 0:
                    break
                
                duration += 1
                
                for i in unstable:
                    self.grid[i] -= self.threshold
                    toppling_count += 1
                    
                    # 分配到2个邻居
                    if i > 0:
                        self.grid[i-1] += 1
                    if i < self.size - 1:
                        self.grid[i+1] += 1
        
        elif self.dimensions == 3:
            while True:
                unstable = np.argwhere(self.grid >= self.threshold)
                if len(unstable) == 0:
                    break
                
                duration += 1
                
                for (i, j, k) in unstable:
                    self.grid[i, j, k] -= self.threshold
                    toppling_count += 1
                    
                    neighbors = [
                        (i-1, j, k), (i+1, j, k),
                        (i, j-1, k), (i, j+1, k),
                        (i, j, k-1), (i, j, k+1)
                    ]
                    for ni, nj, nk in neighbors:
                        if (0 <= ni < self.size and 0 <= nj < self.size 
                            and 0 <= nk < self.size):
                            self.grid[ni, nj, nk] += 1
        
        if duration > 0:
            self.avalanche_durations.append(duration)
        self.total_topplings += toppling_count
        
        return toppling_count
    
    def get_avalanche_sizes(self) -> np.ndarray:
        """获取崩塌大小分布"""
        return np.array(self.avalanche_sizes)
    
    def get_avalanche_durations(self) -> np.ndarray:
        """获取崩塌持续时间分布"""
        return np.array(self.avalanche_durations)
    
    def power_law_check(self, min_count: int = 100) -> Dict:
        """
        检查崩塌大小是否服从幂律分布
        
        Returns:
            包含幂律检验结果的字典
        """
        if len(self.avalanche_sizes) < min_count:
            return {"status": "insufficient_data", "n_samples": len(self.avalanche_sizes)}
        
        sizes = np.array(self.avalanche_sizes)
        sizes = sizes[sizes > 0]  # 排除0
        
        if len(sizes) < 10:
            return {"status": "no_valid_data"}
        
        # 计算互补累积分布函数 (CCDF)
        unique_sizes = np.unique(sizes)
        ccdf = np.array([np.mean(sizes >= s) for s in unique_sizes])
        
        # 对数-对数线性回归估计幂律指数
        log_sizes = np.log(unique_sizes[ccdf > 0])
        log_ccdf = np.log(ccdf[ccdf > 0])
        
        if len(log_sizes) < 3:
            return {"status": "insufficient_unique"}
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            log_sizes, log_ccdf
        )
        
        # 幂律指数 τ = -slope + 1 (从CCDF转换到PDF)
        tau = -slope + 1
        
        # Kolmogorov-Smirnov检验（简化版）
        # 生成理论幂律分布样本
        if tau > 1:
            theoretical = (np.random.pareto(tau - 1, len(sizes)) + 1) * sizes.min()
            ks_stat, ks_pvalue = stats.ks_2samp(sizes, theoretical)
        else:
            ks_stat, ks_pvalue = None, None
        
        return {
            "status": "success",
            "power_law_exponent_tau": float(tau),
            "ccdf_slope": float(slope),
            "r_squared": float(r_value**2),
            "p_value": float(p_value),
            "ks_statistic": float(ks_stat) if ks_stat else None,
            "ks_pvalue": float(ks_pvalue) if ks_pvalue else None,
            "is_power_law": r_value**2 > 0.8 and tau > 1.0 and tau < 3.5,
            "n_samples": len(sizes),
            "mean_avalanche": float(np.mean(sizes)),
            "max_avalanche": int(np.max(sizes)) if len(sizes) > 0 else 0
        }
    
    def get_criticality_metrics(self) -> Dict:
        """获取临界性指标"""
        if len(self.avalanche_sizes) == 0:
            return {"status": "no_data"}
        
        sizes = np.array(self.avalanche_sizes)
        
        return {
            "mean_avalanche_size": float(np.mean(sizes)),
            "std_avalanche_size": float(np.std(sizes)),
            "max_avalanche": int(np.max(sizes)),
            "total_topplings": self.total_topplings,
            "grains_added": self.total_grains_added,
            "dissipation_rate": self.total_topplings / max(1, self.total_grains_added),
            "grid_mean": float(np.mean(self.grid)),
            "grid_std": float(np.std(self.grid))
        }
    
    def reset(self):
        """重置模型"""
        if self.dimensions == 1:
            self.grid = np.zeros(self.size, dtype=np.int32)
        elif self.dimensions == 2:
            self.grid = np.zeros((self.size, self.size), dtype=np.int32)
        else:
            self.grid = np.zeros((self.size, self.size, self.size), dtype=np.int32)
        
        self.avalanche_sizes = []
        self.avalanche_durations = []
        self.total_grains_added = 0
        self.total_topplings = 0


# ============================================================================
# 2. PhaseTransitionMonitor — 相变监控
# ============================================================================

class PhaseTransitionMonitor:
    """
    相变监控系统
    
    功能：
    1. 监控序参量（order parameter）的演化
    2. 使用CUSUM算法检测突变点（变点检测）
    3. 分类系统相态（有序/临界/混沌）
    4. 估计临界指数
    """
    
    def __init__(self, 
                 window_size: int = 50,
                 cusum_threshold: float = 2.0,
                 min_phase_duration: int = 20):
        """
        初始化相变监控器
        
        Args:
            window_size: 滑动窗口大小
            cusum_threshold: CUSUM检测阈值
            min_phase_duration: 最小相态持续时间
        """
        self.window_size = window_size
        self.cusum_threshold = cusum_threshold
        self.min_phase_duration = min_phase_duration
        self.cusum_cooldown = 0  # CUSUM冷却计时器
        
        # 历史数据
        self.order_parameter_history: List[float] = []
        self.derivative_history: List[float] = []
        self.cusum_history: List[float] = []
        
        # 相态历史
        self.phase_history: List[str] = []
        
        # 检测到的相变事件
        self.detected_transitions: List[Dict] = []
        
        # CUSUM状态
        self.cusum_positive = 0.0
        self.cusum_negative = 0.0
        self.baseline_mean = 0.0
        self.baseline_std = 1.0
        
    def monitor(self, order_parameter: float) -> Dict:
        """
        监控序参量，返回当前状态分析
        
        Args:
            order_parameter: 当前序参量值（如复杂度、能量密度等）
        
        Returns:
            包含监控结果的字典
        """
        self.order_parameter_history.append(order_parameter)
        idx = len(self.order_parameter_history) - 1
        
        # 计算滑动窗口统计量
        if len(self.order_parameter_history) >= self.window_size:
            recent = self.order_parameter_history[-self.window_size:]
            window_mean = np.mean(recent)
            window_std = np.std(recent) + 1e-10
            
            # 更新基线（使用指数移动平均）
            alpha = 0.1
            self.baseline_mean = alpha * window_mean + (1 - alpha) * self.baseline_mean
            self.baseline_std = alpha * window_std + (1 - alpha) * self.baseline_std
        else:
            window_mean = order_parameter
            window_std = 1.0
            self.baseline_mean = order_parameter
            self.baseline_std = 1.0
        
        # 计算导数（变化率）
        if len(self.order_parameter_history) >= 2:
            derivative = order_parameter - self.order_parameter_history[-2]
        else:
            derivative = 0.0
        self.derivative_history.append(derivative)
        
        # CUSUM检测（累积和变点检测）
        normalized = (order_parameter - self.baseline_mean) / (self.baseline_std + 1e-10)
        
        # 自适应CUSUM - 在冷却期间降低敏感度
        if self.cusum_cooldown > 0:
            self.cusum_cooldown -= 1
            drift = 0.8  # 更高的漂移，更快衰减
        else:
            drift = 0.5
            
        self.cusum_positive = max(0, self.cusum_positive + normalized - drift)
        self.cusum_negative = max(0, self.cusum_negative - normalized - drift)
        
        cusum_value = max(self.cusum_positive, self.cusum_negative)
        self.cusum_history.append(cusum_value)
        
        # 检测相变（需要CUSUM超过阈值且不在冷却期）
        is_transition = (cusum_value > self.cusum_threshold) and (self.cusum_cooldown == 0)
        if is_transition:
            self.cusum_cooldown = self.min_phase_duration  # 触发冷却
        
        # 分类相态
        phase = self._classify_phase(order_parameter, derivative, window_std)
        self.phase_history.append(phase)
        
        # 计算"临界距离"（到临界点的距离估计）
        critical_distance = self._estimate_critical_distance()
        
        return {
            "step": idx,
            "order_parameter": float(order_parameter),
            "derivative": float(derivative),
            "window_mean": float(window_mean),
            "window_std": float(window_std),
            "cusum": float(cusum_value),
            "is_transition": is_transition,
            "phase": phase,
            "critical_distance": float(critical_distance)
        }
    
    def _classify_phase(self, 
                       order_parameter: float, 
                       derivative: float,
                       fluctuation: float) -> str:
        """
        分类系统相态
        
        相态分类：
        - ordered: 有序态（低波动、低变化率）
        - critical: 临界态（高波动、中等变化率）
        - chaotic: 混沌态（极高波动、高变化率）
        - transitioning: 跃迁中（检测到CUSUM报警）
        """
        # 使用历史数据归一化
        if len(self.order_parameter_history) > 20:
            all_vals = np.array(self.order_parameter_history)
            hist_std = np.std(all_vals) + 1e-10
            
            normalized_fluct = fluctuation / hist_std
            normalized_deriv = abs(derivative) / hist_std
        else:
            normalized_fluct = 0.5
            normalized_deriv = 0.3
        
        # CUSUM触发跃迁态（但只有在冷却期早期）
        if self.cusum_cooldown > self.min_phase_duration * 0.7:
            return "transitioning"
        
        # 相态判定（基于相对波动和变化率）
        if normalized_fluct > 3.0 and normalized_deriv > 2.5:
            return "chaotic"
        elif normalized_fluct > 1.5 or normalized_deriv > 1.5:
            return "critical"
        elif normalized_fluct < 0.8 and normalized_deriv < 0.5:
            return "ordered"
        else:
            # 根据Lyapunov指数判断
            if len(self.order_parameter_history) > 10:
                recent_lyap = np.mean([self.order_parameter_history[-i] 
                                       for i in range(1, min(6, len(self.order_parameter_history)))])
                if recent_lyap > 0.7:
                    return "chaotic"
            return "critical"
    
    def _estimate_critical_distance(self) -> float:
        """估计到临界点的距离（0表示在临界点，1表示远离）"""
        if len(self.order_parameter_history) < self.window_size * 2:
            return 1.0
        
        # 使用波动率作为临界距离的代理指标
        # 临界点附近波动最大
        recent = self.order_parameter_history[-self.window_size:]
        older = self.order_parameter_history[-2*self.window_size:-self.window_size]
        
        recent_var = np.var(recent)
        older_var = np.var(older) + 1e-10
        
        # 波动率比值 - 临界点附近最大
        var_ratio = recent_var / older_var
        
        # 映射到[0,1]，0表示在临界（最大波动），1表示远离
        critical_distance = 1.0 / (1.0 + var_ratio)
        
        return critical_distance
    
    def detect_critical_point(self, 
                              history: Optional[List[float]] = None) -> Dict:
        """
        从序参量历史中检测临界点
        
        使用有限差分法找到变化率最大的点
        """
        if history is None:
            history = self.order_parameter_history
        
        if len(history) < 10:
            return {"status": "insufficient_data"}
        
        h = np.array(history)
        
        # 平滑处理
        if len(h) > 10:
            h_smooth = gaussian_filter1d(h, sigma=min(3, len(h)//10))
        else:
            h_smooth = h
        
        # 计算一阶导数和二阶导数
        first_deriv = np.gradient(h_smooth)
        second_deriv = np.gradient(first_deriv)
        
        # 临界点候选：二阶导数为零且一阶导数最大的点（拐点）
        # 或者一阶导数最大的点
        critical_candidates = np.argsort(np.abs(first_deriv))[::-1]
        
        # 选择最显著的临界点（排除边界）
        margin = max(5, len(h) // 10)
        valid_candidates = [c for c in critical_candidates 
                          if margin <= c < len(h) - margin]
        
        if not valid_candidates:
            return {"status": "no_critical_point_found"}
        
        critical_idx = valid_candidates[0]
        
        # 计算临界指数（使用有限尺寸标度）
        critical_exponent = self._estimate_critical_exponent(
            h_smooth, critical_idx
        )
        
        return {
            "status": "success",
            "critical_index": int(critical_idx),
            "critical_value": float(h_smooth[critical_idx]),
            "max_derivative": float(first_deriv[critical_idx]),
            "second_derivative": float(second_deriv[critical_idx]),
            "critical_exponent": float(critical_exponent)
        }
    
    def _estimate_critical_exponent(self, 
                                    series: np.ndarray, 
                                    critical_idx: int) -> float:
        """估计临界指数"""
        # 使用幂律拟合：|x - xc|^β
        if critical_idx < 5 or critical_idx > len(series) - 5:
            return 1.0
        
        left = series[:critical_idx]
        right = series[critical_idx:]
        
        if len(left) < 3 or len(right) < 3:
            return 1.0
        
        # 对左侧数据拟合
        x_left = np.arange(len(left))
        y_left = np.abs(left - series[critical_idx]) + 1e-10
        
        try:
            log_x = np.log(x_left + 1)
            log_y = np.log(y_left)
            slope, _, r, _, _ = stats.linregress(log_x, log_y)
            if r**2 > 0.5:
                return float(slope)
        except:
            pass
        
        return 1.0
    
    def get_transition_events(self) -> List[PhaseTransitionEvent]:
        """获取检测到的相变事件列表"""
        events = []
        
        # 从CUSUM历史中提取相变事件
        in_transition = False
        transition_start = 0
        
        for i, cusum in enumerate(self.cusum_history):
            if cusum > self.cusum_threshold and not in_transition:
                in_transition = True
                transition_start = i
            elif cusum <= self.cusum_threshold * 0.5 and in_transition:
                in_transition = False
                # 记录相变事件
                if i - transition_start >= 3:  # 至少持续3步
                    event = PhaseTransitionEvent(
                        step=transition_start,
                        phase_before="ordered" if transition_start > 0 else "unknown",
                        phase_after="critical",
                        order_parameter_jump=(
                            self.order_parameter_history[i] - 
                            self.order_parameter_history[transition_start]
                            if i < len(self.order_parameter_history) and 
                               transition_start < len(self.order_parameter_history)
                            else 0.0
                        ),
                        complexity_jump=0.0,
                        critical_exponent=1.0,
                        description=f"CUSUM-detected transition at step {transition_start}"
                    )
                    events.append(event)
        
        return events
    
    def reset(self):
        """重置监控器"""
        self.order_parameter_history = []
        self.derivative_history = []
        self.cusum_history = []
        self.phase_history = []
        self.detected_transitions = []
        self.cusum_positive = 0.0
        self.cusum_negative = 0.0
        self.baseline_mean = 0.0
        self.baseline_std = 1.0


# ============================================================================
# 3. ComplexityElevationEngine — 复杂度提升引擎
# ============================================================================

class ComplexityElevationEngine:
    """
    OMNI-HUB 复杂度提升引擎
    
    核心功能：
    1. 计算多种复杂度指标（Kolmogorov、网络、分形、Lyapunov、熵）
    2. 驱动系统通过相变临界点
    3. 管理复杂度提升的完整生命周期
    
    提升策略：
    - 驱动期：增加系统能量/信息量（自激、互激）
    - 临界期：系统接近临界点，波动增大
    - 跃迁期：过临界，发生相变，新结构涌现
    - 稳定期：新结构稳定，复杂度提升
    """
    
    def __init__(self, num_lines: int = 11, seed: Optional[int] = None):
        """
        初始化复杂度提升引擎
        
        Args:
            num_lines: OMNI-HUB 线数（默认11线分布式系统）
            seed: 随机种子
        """
        self.num_lines = num_lines
        if seed is not None:
            np.random.seed(seed)
        
        # 系统状态 - Logistic映射范围 [0,1]
        self.system_state = np.random.uniform(0.2, 0.8, num_lines)
        self.coupling_matrix = self._initialize_coupling()
        self.energy_level = 0.0
        self.information_content = 0.0
        
        # 复杂度历史
        self.history = ElevationHistory()
        self.current_step = 0
        
        # 子系统
        self.sandpile = SandpileModel(size=30, threshold=4, dimensions=2)
        self.monitor = PhaseTransitionMonitor(
            window_size=30,
            cusum_threshold=3.0,
            min_phase_duration=15
        )
        
        # 提升参数
        self.drive_strength = 0.1
        self.coupling_strength = 0.05
        self.noise_level = 0.01
        
        # 相变计数
        self.transition_count = 0
        self.phase = "ordered"
        
        # 状态记录
        self.state_history: List[np.ndarray] = []
        self.adjacency_history: List[np.ndarray] = []
        
    def _initialize_coupling(self) -> np.ndarray:
        """初始化耦合矩阵（小世界网络风格）"""
        n = self.num_lines
        # 环形近邻耦合
        coupling = np.zeros((n, n))
        for i in range(n):
            coupling[i, (i+1) % n] = 0.5
            coupling[i, (i-1) % n] = 0.5
            coupling[i, (i+2) % n] = 0.3
            coupling[i, (i-2) % n] = 0.3
        
        # 添加随机长程连接（小世界特性）
        n_random = n // 3
        for _ in range(n_random):
            i, j = np.random.randint(0, n, 2)
            if i != j:
                coupling[i, j] = np.random.uniform(0.1, 0.4)
        
        # 对称化
        coupling = (coupling + coupling.T) / 2
        return coupling
    
    def kolmogorov_complexity(self, state: np.ndarray) -> float:
        """
        估计Kolmogorov复杂度
        
        基于压缩比估计：
        K(x) ≈ 不可压缩部分的比例
        
        使用简化的LZ复杂度 + 状态空间覆盖度
        """
        n = len(state)
        if n == 0:
            return 0.0
        
        # 量化状态为整数序列（更多级别以捕捉细微差异）
        quantized = np.round(state * 1000).astype(np.int32)
        
        # LZ复杂度估计（Lempel-Ziv因子分解）
        def lz_complexity(sequence):
            """计算LZ复杂度"""
            m = len(sequence)
            if m == 0:
                return 0.0
            
            # 使用更高效的字符串匹配
            s = ','.join(map(str, sequence))
            i, c = 0, 1
            factor_count = 1
            
            while i + c <= m:
                current = ','.join(map(str, sequence[i:i+c]))
                # 检查是否在前面出现过
                prefix = ','.join(map(str, sequence[:i+c-1]))
                if ',' + current + ',' in ',' + prefix + ',' or current == prefix:
                    c += 1
                else:
                    i += c
                    c = 1
                    factor_count += 1
            
            # 归一化：高复杂度 = 高不可压缩性
            complexity = factor_count / (m ** 0.5)  # 归一化
            return min(complexity, 1.0)
        
        lz = lz_complexity(quantized)
        
        # 状态空间覆盖度（熵）
        unique_vals = len(np.unique(quantized))
        coverage = unique_vals / min(n, 1001)  # 最多1001个级别
        
        # 状态方差（动态范围）
        variance = np.var(state)
        
        # 综合复杂度
        k_complexity = 0.4 * lz + 0.3 * coverage + 0.3 * min(variance * 4, 1.0)
        
        return float(np.clip(k_complexity, 0, 1))
    
    def network_complexity(self, adjacency: np.ndarray) -> float:
        """
        计算网络复杂度
        
        基于图的谱熵：
        C = -Σ λ_i log(λ_i) / log(N)
        
        其中λ_i是归一化的图拉普拉斯矩阵特征值
        """
        n = adjacency.shape[0]
        if n == 0:
            return 0.0
        
        # 计算度矩阵
        degrees = np.sum(np.abs(adjacency), axis=1)
        D = np.diag(degrees)
        
        # 图拉普拉斯矩阵
        L = D - adjacency
        
        # 计算特征值
        try:
            eigenvalues = la.eigvalsh(L)
            # 归一化（排除零特征值）
            eigenvalues = np.abs(eigenvalues)
            eigenvalues = eigenvalues[eigenvalues > 1e-10]
            
            if len(eigenvalues) == 0:
                return 0.0
            
            # 归一化到概率分布
            ev_sum = np.sum(eigenvalues)
            if ev_sum < 1e-10:
                return 0.0
            
            p = eigenvalues / ev_sum
            
            # 谱熵
            spectral_entropy = -np.sum(p * np.log2(p + 1e-10))
            max_spectral_entropy = np.log2(len(p))
            
            complexity = spectral_entropy / max(max_spectral_entropy, 1e-10)
            
            return float(complexity)
        except:
            return 0.5
    
    def fractal_dimension(self, series: np.ndarray, 
                          k_max: int = 8) -> float:
        """
        使用Higuchi方法计算分形维数
        
        Higuchi方法：
        1. 构造k个新的子序列
        2. 计算每个k对应的曲线长度L(k)
        3. L(k) ~ k^(-D)，D为分形维数
        """
        n = len(series)
        if n < k_max * 2:
            return 1.0
        
        # 归一化序列
        series = np.array(series)
        series = (series - np.mean(series)) / (np.std(series) + 1e-10)
        
        L_values = []
        k_values = []
        
        for k in range(1, k_max + 1):
            # 构造m个子序列
            L_m = []
            for m in range(k):
                # 提取子序列
                indices = np.arange(m, n, k)
                if len(indices) < 2:
                    continue
                
                subseq = series[indices]
                
                # 计算归一化曲线长度
                diff = np.abs(np.diff(subseq))
                L_k_m = np.sum(diff) * (n - 1) / (len(subseq) - 1) / k
                L_m.append(L_k_m)
            
            if L_m:
                L_k = np.mean(L_m)
                L_values.append(L_k)
                k_values.append(k)
        
        if len(k_values) < 3:
            return 1.0
        
        # 对数回归: log(L) ~ -D * log(k)
        log_k = np.log(k_values)
        log_L = np.log(L_values)
        
        try:
            slope, _, r_value, _, _ = stats.linregress(log_k, log_L)
            # D = -slope
            D = -slope
            # 约束到合理范围 [1, 2]
            D = np.clip(D, 1.0, 2.0)
            return float(D)
        except:
            return 1.0
    
    def lyapunov_exponent(self, trajectory: np.ndarray, 
                          dt: float = 1.0) -> float:
        """
        估计最大Lyapunov指数
        
        方法：基于轨迹的分离率
        正值表示混沌（对初值敏感）
        """
        n = len(trajectory)
        if n < 30:
            return 0.0
        
        trajectory = np.array(trajectory)
        
        # 方法：使用轨迹的差分标准差变化率
        # 在混沌系统中，邻近轨迹的分离导致标准差指数增长
        half = n // 2
        first_half = trajectory[:half]
        second_half = trajectory[half:]
        
        var_first = np.var(first_half)
        var_second = np.var(second_half)
        
        if var_first > 1e-10 and var_second > 1e-10:
            # 方差增长率的对数
            lyap = 0.5 * np.log(var_second / var_first) / half
        else:
            lyap = 0.0
        
        # 备选：基于自相关衰减率
        if n > 50:
            # 计算自相关函数
            centered = trajectory - np.mean(trajectory)
            autocorr = np.correlate(centered, centered, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            autocorr = autocorr / autocorr[0]
            
            # 找到自相关降到1/e的时间
            threshold = np.exp(-1)
            decorrelation_idx = np.where(autocorr < threshold)[0]
            if len(decorrelation_idx) > 0:
                decorrelation_time = decorrelation_idx[0]
                if decorrelation_time > 0:
                    lyap_alt = 1.0 / decorrelation_time
                    lyap = max(lyap, lyap_alt)
        
        # 限制到合理范围 [0, 3]
        lyap = np.clip(lyap, 0.0, 3.0)
        
        return float(lyap)
    
    def information_entropy(self, distribution: np.ndarray) -> float:
        """
        计算Shannon信息熵
        
        H = -Σ p_i log(p_i)
        
        归一化到[0,1]范围
        """
        dist = np.array(distribution)
        dist = np.abs(dist)
        
        # 归一化为概率分布
        total = np.sum(dist)
        if total < 1e-10:
            return 0.0
        
        p = dist / total
        p = p[p > 1e-10]
        
        if len(p) == 0:
            return 0.0
        
        entropy = -np.sum(p * np.log2(p))
        max_entropy = np.log2(len(distribution))
        
        normalized = entropy / max(max_entropy, 1e-10)
        return float(normalized)
    
    def phase_transition_detector(self, 
                                  history: Optional[List[float]] = None) -> Dict:
        """
        检测复杂度历史中的相变点
        
        综合使用多种方法：
        1. CUSUM变点检测
        2. 导数峰值检测
        3. 方差突变检测
        """
        if history is None:
            if self.history.metrics_history:
                history = [m.composite for m in self.history.metrics_history]
            else:
                return {"status": "no_history"}
        
        h = np.array(history)
        
        if len(h) < 20:
            return {"status": "insufficient_data"}
        
        # 方法1: 方差突变检测
        window = min(20, len(h) // 4)
        variances = []
        for i in range(window, len(h)):
            variances.append(np.var(h[i-window:i]))
        variances = np.array(variances)
        
        # 找到方差最大的区域（临界区）
        if len(variances) > 0:
            var_peak = np.argmax(variances) + window
        else:
            var_peak = len(h) // 2
        
        # 方法2: 导数峰值
        smooth = gaussian_filter1d(h, sigma=min(2, len(h)//20))
        deriv = np.gradient(smooth)
        deriv2 = np.gradient(deriv)
        
        # 拐点：二阶导数变号
        inflection_candidates = np.where(np.diff(np.sign(deriv2)) != 0)[0]
        
        if len(inflection_candidates) > 0:
            # 选择一阶导数最大的拐点
            inflection = inflection_candidates[np.argmax(np.abs(deriv[inflection_candidates]))]
        else:
            inflection = np.argmax(np.abs(deriv))
        
        # 方法3: CUSUM
        cusum_pos, cusum_neg = 0.0, 0.0
        cusum_max = 0.0
        cusum_step = 0
        mean_h = np.mean(h)
        std_h = np.std(h) + 1e-10
        
        for i, val in enumerate(h):
            normalized = (val - mean_h) / std_h
            cusum_pos = max(0, cusum_pos + normalized - 0.5)
            cusum_neg = max(0, cusum_neg - normalized - 0.5)
            cusum_val = max(cusum_pos, cusum_neg)
            if cusum_val > cusum_max:
                cusum_max = cusum_val
                cusum_step = i
        
        # 综合判断
        transitions = []
        for candidate, method in [(var_peak, "variance_peak"), 
                                   (inflection, "inflection_point"),
                                   (cusum_step, "cusum")]:
            if 5 <= candidate < len(h) - 5:
                transitions.append({
                    "step": int(candidate),
                    "method": method,
                    "complexity_before": float(np.mean(h[max(0, candidate-5):candidate])),
                    "complexity_after": float(np.mean(h[candidate:min(len(h), candidate+5)])),
                    "jump": float(np.mean(h[candidate:min(len(h), candidate+5)]) - 
                                 np.mean(h[max(0, candidate-5):candidate]))
                })
        
        return {
            "status": "success",
            "transitions": transitions,
            "strongest_transition": max(transitions, key=lambda x: abs(x["jump"])) if transitions else None
        }
    
    def self_organized_criticality_step(self) -> Dict:
        """
        执行一步自组织临界性演化
        
        将沙堆模型与系统状态耦合：
        1. 在沙堆中添加沙子
        2. 崩塌影响系统状态
        3. 记录崩塌统计
        """
        # 在沙堆中添加沙子（随机位置或基于系统状态）
        if self.sandpile.dimensions == 2:
            # 使用系统状态决定添加位置（耦合）
            center = self.size // 2 if hasattr(self, 'size') else 15
            pos = (
                int(center + self.system_state[0] * 5) % self.sandpile.size,
                int(center + self.system_state[1] * 5) % self.sandpile.size
            )
        else:
            pos = None
        
        avalanche_size = self.sandpile.add_grain(pos)
        
        # 如果发生大崩塌，扰动系统状态（级联效应）
        if avalanche_size > 5:
            perturbation = np.random.randn(self.num_lines) * 0.1 * np.log1p(avalanche_size)
            self.system_state += perturbation
            self.energy_level += avalanche_size * 0.01
        
        return {
            "avalanche_size": avalanche_size,
            "grid_mean": float(np.mean(self.sandpile.grid)),
            "grid_max": int(np.max(self.sandpile.grid))
        }
    
    def elevate(self, system_state: Optional[np.ndarray] = None) -> Dict:
        """
        提升系统复杂度
        
        策略：
        1. 检测当前复杂度水平
        2. 如果接近临界，推动过临界
        3. 如果远离临界，增加驱动力
        4. 返回提升后的状态
        
        Args:
            system_state: 可选的外部系统状态
        
        Returns:
            提升结果字典
        """
        if system_state is not None:
            self.system_state = system_state.copy()
        
        self.current_step += 1
        
        # 初始化transition_info
        transition_info = {"status": "pending"}
        
        # === 步骤1: 计算当前复杂度指标 ===
        metrics = self._compute_all_metrics()
        self.history.metrics_history.append(metrics)
        self.history.steps.append(self.current_step)
        
        # === 步骤2: 执行SOC步进 ===
        soc_result = self.self_organized_criticality_step()
        self.history.avalanche_sizes.append(soc_result["avalanche_size"])
        
        # === 步骤3: 监控序参量 ===
        order_param = metrics.composite
        monitor_result = self.monitor.monitor(order_param)
        self.history.order_parameters.append(order_param)
        self.history.phase_history.append(monitor_result["phase"])
        
        # === 步骤4: 根据相态调整策略 ===
        self.phase = monitor_result["phase"]
        
        if self.phase == "ordered":
            # 驱动期：增加能量和耦合
            self._drive_phase()
        elif self.phase == "critical":
            # 临界期：适度扰动，等待自发跃迁
            self._critical_phase()
        elif self.phase == "transitioning":
            # 跃迁期：推动系统过临界
            self._transition_phase()
        elif self.phase == "chaotic":
            # 混沌期：引入耗散，稳定系统
            self._dissipate_phase()
        
        # === 步骤5: 系统动力学演化 ===
        self._evolve_system()
        
        # === 步骤6: 检测相变 ===
        # 使用CUSUM检测实时相变
        if monitor_result["is_transition"] and len(self.history.metrics_history) > 20:
            # 计算相变前后的复杂度变化
            recent_metrics = self.history.metrics_history[-10:]
            older_metrics = self.history.metrics_history[-20:-10]
            
            recent_comp = np.mean([m.composite for m in recent_metrics])
            older_comp = np.mean([m.composite for m in older_metrics])
            jump = recent_comp - older_comp
            
            # 只有当复杂度显著变化时才记录
            if abs(jump) > 0.02:
                event = PhaseTransitionEvent(
                    step=self.current_step,
                    phase_before=self.monitor.phase_history[-2] if len(self.monitor.phase_history) > 1 else "ordered",
                    phase_after="critical",
                    order_parameter_jump=jump,
                    complexity_jump=jump,
                    critical_exponent=1.0,
                    description=f"Phase transition at step {self.current_step}, jump={jump:.3f}"
                )
                self.history.transition_events.append(event)
                self.transition_count += 1
        
        # 补充：使用历史分析检测早期相变
        if self.current_step % 50 == 0 and self.current_step > 50:
            transition_info = self.phase_transition_detector()
            if (transition_info.get("status") == "success" and 
                transition_info.get("strongest_transition")):
                st = transition_info["strongest_transition"]
                # 避免重复记录
                already_recorded = any(e.step == st["step"] for e in self.history.transition_events)
                if not already_recorded and abs(st["jump"]) > 0.05:
                    event = PhaseTransitionEvent(
                        step=st["step"],
                        phase_before="ordered",
                        phase_after="critical",
                        order_parameter_jump=st["jump"],
                        complexity_jump=st["jump"],
                        critical_exponent=1.0,
                        description=f"Historical transition at step {st['step']}, jump={st['jump']:.3f}"
                    )
                    self.history.transition_events.append(event)
                    self.transition_count += 1
        
        # 保存状态历史
        self.state_history.append(self.system_state.copy())
        self.adjacency_history.append(self.coupling_matrix.copy())
        
        return {
            "step": self.current_step,
            "metrics": metrics,
            "phase": self.phase,
            "soc_result": soc_result,
            "monitor": monitor_result,
            "transition_detected": transition_info.get("strongest_transition") is not None,
            "system_state": self.system_state.copy(),
            "transition_count": self.transition_count
        }
    
    def _compute_all_metrics(self) -> ComplexityMetrics:
        """计算所有复杂度指标"""
        state = self.system_state
        
        # Kolmogorov复杂度
        k_comp = self.kolmogorov_complexity(state)
        
        # 网络复杂度（基于耦合矩阵）
        net_comp = self.network_complexity(self.coupling_matrix)
        
        # 分形维数（基于状态历史）
        if len(self.state_history) > 10:
            # 使用第一个维度的历史
            series = [s[0] for s in self.state_history[-50:]]
            frac_dim = self.fractal_dimension(np.array(series))
        else:
            frac_dim = 1.0
        
        # Lyapunov指数
        if len(self.state_history) > 10:
            series = [s[0] for s in self.state_history[-100:]]
            lyap = self.lyapunov_exponent(np.array(series))
        else:
            lyap = 0.0
        
        # 信息熵
        entropy = self.information_entropy(np.abs(state))
        
        # 综合复杂度（加权组合）
        # Lyapunov映射到[0,1]后再使用
        lyap_normalized = np.clip(lyap / 2.0, 0, 1)
        composite = (
            0.20 * k_comp +
            0.15 * net_comp +
            0.15 * (frac_dim - 1.0) +  # 分形维数减1，范围[0,1]
            0.30 * lyap_normalized +  # Lyapunov权重增加，混沌=高复杂度
            0.20 * entropy
        )
        
        return ComplexityMetrics(
            kolmogorov=k_comp,
            network=net_comp,
            fractal=frac_dim,
            lyapunov=lyap,
            entropy=entropy,
            composite=composite,
            timestamp=self.current_step
        )
    
    def _drive_phase(self):
        """驱动期：增加系统能量和耦合"""
        # 增加随机扰动（自激）- 适合Logistic范围
        self.system_state += np.random.randn(self.num_lines) * self.drive_strength * 0.3
        self.system_state = np.clip(self.system_state, 0.01, 0.99)
        
        # 增强耦合（互激）
        coupled = self.coupling_strength * self.coupling_matrix @ self.system_state
        self.system_state = np.clip(self.system_state + coupled, 0.01, 0.99)
        
        # 缓慢增加驱动强度
        self.drive_strength = min(0.3, self.drive_strength * 1.005)
        
        # 增加耦合矩阵的随机性
        noise = np.random.randn(self.num_lines, self.num_lines) * 0.005
        noise = (noise + noise.T) / 2
        self.coupling_matrix += noise
        np.fill_diagonal(self.coupling_matrix, 0)
        self.coupling_matrix = np.clip(self.coupling_matrix, -0.5, 0.5)
    
    def _critical_phase(self):
        """临界期：维持系统在高波动状态"""
        # 适度扰动
        perturb = np.random.randn(self.num_lines) * self.drive_strength * 0.4
        self.system_state = np.clip(self.system_state + perturb, 0.01, 0.99)
        
        # 增强耦合，促进协同
        coupled = self.coupling_strength * 2 * self.coupling_matrix @ self.system_state
        self.system_state = np.clip(self.system_state + coupled, 0.01, 0.99)
        
        # 添加非线性项（促进相变）
        self.system_state += 0.02 * np.sin(2 * np.pi * self.system_state)
        self.system_state = np.clip(self.system_state, 0.01, 0.99)
    
    def _transition_phase(self):
        """跃迁期：推动系统过临界"""
        # 强扰动 - 引发状态重组
        perturb = np.random.randn(self.num_lines) * self.drive_strength * 1.5
        self.system_state = np.clip(self.system_state + perturb, 0.01, 0.99)
        
        # 重组耦合矩阵（结构重构）
        n_new = self.num_lines // 2
        for _ in range(n_new):
            i, j = np.random.randint(0, self.num_lines, 2)
            if i != j:
                self.coupling_matrix[i, j] += np.random.uniform(0.1, 0.4)
                self.coupling_matrix[j, i] = self.coupling_matrix[i, j]
        
        # 归一化耦合矩阵
        max_val = np.max(np.abs(self.coupling_matrix))
        if max_val > 1.0:
            self.coupling_matrix /= max_val * 0.8
        
        # 重置驱动强度
        self.drive_strength = 0.05
        
        # 增加能量等级（复杂度跃升标记）
        self.energy_level += 1.0
        
        # 突变：随机改变部分系统状态
        mask = np.random.rand(self.num_lines) < 0.3
        self.system_state[mask] = np.random.uniform(0.1, 0.9, np.sum(mask))
    
    def _dissipate_phase(self):
        """混沌期：引入耗散，稳定系统"""
        # 耗散项 - 向0.5收缩（Logistic映射的不动点附近）
        self.system_state = 0.9 * self.system_state + 0.1 * 0.5
        
        # 减少噪声
        self.drive_strength *= 0.95
        
        # 耦合矩阵衰减但保持结构
        self.coupling_matrix *= 0.99
        np.fill_diagonal(self.coupling_matrix, 0)
        
        # 添加吸引子（稳定到新态）
        attractor = np.random.uniform(0.3, 0.7, self.num_lines)
        self.system_state += 0.03 * (attractor - self.system_state)
        self.system_state = np.clip(self.system_state, 0.01, 0.99)
    
    def _evolve_system(self):
        """系统动力学演化 - 耦合映射格子（CML）
        
        周期性驱动系统通过相变：
        - 有序态（r < 3.0）: 稳定不动点
        - 临界态（r ≈ 3.57）: 周期倍增分岔
        - 混沌态（r > 3.57）: 混沌吸引子
        """
        new_state = self.system_state.copy()
        
        # 周期性淬火：每150步一个完整周期
        cycle_length = 150
        cycle_position = (self.current_step % cycle_length) / cycle_length
        
        # 控制参数 r：正弦调制，周期性地穿越混沌阈值
        # r 在 [2.8, 4.0] 之间振荡
        r_base = 3.4 + 0.6 * np.sin(2 * np.pi * cycle_position)
        
        # 添加随机扰动
        r = r_base + np.random.randn() * 0.02
        r = np.clip(r, 2.5, 4.0)
        
        # 记录当前r值用于分析
        self.current_r = r
        
        for i in range(self.num_lines):
            x = self.system_state[i]
            
            # 局部动力学（Logistic映射）
            local = r * x * (1 - x)
            
            # 耦合项（全局耦合 + 最近邻耦合）
            global_coupling = 0.01 * (np.mean(self.system_state) - x)
            local_coupling = self.coupling_strength * np.sum(
                self.coupling_matrix[i] * (self.system_state - x)
            )
            coupled = global_coupling + local_coupling
            
            # 非线性反馈
            nonlinear = 0.01 * self.energy_level * np.sin(4 * np.pi * x)
            
            # 噪声（相变期间噪声增大）
            phase_noise = 1.0 + 2.0 * abs(r - 3.57)  # 临界点附近噪声增大
            noise = np.random.randn() * self.noise_level * phase_noise
            
            new_val = local + coupled + nonlinear + noise
            new_state_i = np.clip(new_val, 0.001, 0.999)
            
            # 在混沌区使用更强的耦合
            if r > 3.57:
                new_state_i = 0.7 * new_state_i + 0.3 * np.random.uniform(0.1, 0.9)
            
            new_state[i] = new_state_i
        
        self.system_state = new_state
    
    def run_simulation(self, n_steps: int = 1000, 
                       verbose: bool = True) -> Dict:
        """
        运行完整模拟
        
        Args:
            n_steps: 模拟步数
            verbose: 是否打印进度
        
        Returns:
            模拟结果汇总
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"OMNI-HUB v4.1 Complexity Elevation Engine")
        logger.info(f"{'='*60}")
        logger.info(f"Initializing simulation: {n_steps} steps, {self.num_lines} lines")
        logger.info(f"{'='*60}\n")
        
        for step in range(n_steps):
            result = self.elevate()
            
            if verbose and (step + 1) % 100 == 0:
                m = result["metrics"]
                print(f"Step {step+1:4d} | "
                      f"Phase: {result['phase']:12s} | "
                      f"K: {m.kolmogorov:.3f} | "
                      f"N: {m.network:.3f} | "
                      f"F: {m.fractal:.3f} | "
                      f"L: {m.lyapunov:+.3f} | "
                      f"H: {m.entropy:.3f} | "
                      f"C: {m.composite:.3f} | "
                      f"Transitions: {result['transition_count']}")
        
        # 汇总结果
        return self._summarize_simulation()
    
    def _summarize_simulation(self) -> Dict:
        """汇总模拟结果"""
        if not self.history.metrics_history:
            return {"status": "no_data"}
        
        metrics = self.history.metrics_history
        composites = [m.composite for m in metrics]
        
        # 复杂度统计
        complexity_stats = {
            "initial": float(composites[0]),
            "final": float(composites[-1]),
            "mean": float(np.mean(composites)),
            "std": float(np.std(composites)),
            "max": float(np.max(composites)),
            "min": float(np.min(composites)),
            "growth_rate": float((composites[-1] - composites[0]) / max(len(composites), 1))
        }
        
        # 各指标统计
        indicator_stats = {}
        for name in ["kolmogorov", "network", "fractal", "lyapunov", "entropy"]:
            values = [getattr(m, name) for m in metrics]
            indicator_stats[name] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "final": float(values[-1])
            }
        
        # 相态统计
        phase_counts = {}
        for ph in self.history.phase_history:
            phase_counts[ph] = phase_counts.get(ph, 0) + 1
        
        # 相变事件
        transition_summary = []
        for ev in self.history.transition_events:
            transition_summary.append({
                "step": ev.step,
                "jump": float(ev.complexity_jump),
                "description": ev.description
            })
        
        # 沙堆模型幂律检验
        power_law = self.sandpile.power_law_check()
        
        # 临界性指标
        criticality = self.sandpile.get_criticality_metrics()
        
        # 验证：相变后复杂度是否跃升
        transition_verification = self._verify_complexity_jumps()
        
        return {
            "status": "success",
            "n_steps": self.current_step,
            "num_lines": self.num_lines,
            "complexity_stats": complexity_stats,
            "indicator_stats": indicator_stats,
            "phase_distribution": phase_counts,
            "transition_events": transition_summary,
            "transition_count": self.transition_count,
            "power_law_check": power_law,
            "criticality_metrics": criticality,
            "transition_verification": transition_verification
        }
    
    def _verify_complexity_jumps(self) -> Dict:
        """
        验证：每次相变后复杂度是否跃升
        """
        if len(self.history.transition_events) == 0:
            return {"status": "no_transitions"}
        
        verifications = []
        all_passed = True
        
        for ev in self.history.transition_events:
            step = ev.step
            if step < 5 or step >= len(self.history.metrics_history) - 5:
                continue
            
            before = np.mean([m.composite for m in 
                            self.history.metrics_history[max(0, step-5):step]])
            after = np.mean([m.composite for m in 
                           self.history.metrics_history[step:min(len(self.history.metrics_history), step+5)]])
            
            jump = after - before
            passed = jump > 0.01  # 复杂度至少增加0.01
            
            verifications.append({
                "step": step,
                "before": float(before),
                "after": float(after),
                "jump": float(jump),
                "passed": passed
            })
            
            if not passed:
                all_passed = False
        
        return {
            "status": "verified" if all_passed else "partial",
            "all_passed": all_passed,
            "verifications": verifications,
            "pass_rate": sum(1 for v in verifications if v["passed"]) / max(len(verifications), 1)
        }
    
    def get_complexity_trajectory(self) -> Dict:
        """获取复杂度演化轨迹"""
        if not self.history.metrics_history:
            return {"status": "no_data"}
        
        return {
            "steps": self.history.steps,
            "kolmogorov": [m.kolmogorov for m in self.history.metrics_history],
            "network": [m.network for m in self.history.metrics_history],
            "fractal": [m.fractal for m in self.history.metrics_history],
            "lyapunov": [m.lyapunov for m in self.history.metrics_history],
            "entropy": [m.entropy for m in self.history.metrics_history],
            "composite": [m.composite for m in self.history.metrics_history],
            "phases": self.history.phase_history,
            "order_parameters": self.history.order_parameters,
            "avalanche_sizes": self.history.avalanche_sizes
        }


# ============================================================================
# 实验验证脚本
# ============================================================================

def run_experiment(n_steps: int = 1000, 
                   num_lines: int = 11,
                   seed: int = 42,
                   save_results: bool = True) -> Dict:
    """
    运行完整实验验证
    
    实验内容：
    1. 模拟1000步复杂度演化
    2. 计算5种复杂度指标
    3. 检测相变事件
    4. 验证沙堆模型幂律分布
    5. 验证相变后复杂度跃升
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy import stats as scipy_stats
    
    # 创建引擎
    engine = ComplexityElevationEngine(num_lines=num_lines, seed=seed)
    
    # 运行模拟
    summary = engine.run_simulation(n_steps=n_steps, verbose=True)
    
    # 获取轨迹数据
    trajectory = engine.get_complexity_trajectory()
    
    # 生成可视化
    fig = plt.figure(figsize=(20, 24))
    
    # 1. 综合复杂度演化
    ax1 = fig.add_subplot(4, 2, 1)
    ax1.plot(trajectory["steps"], trajectory["composite"], 'b-', linewidth=1.5, label='Composite Complexity')
    # 标记相变事件
    for ev in engine.history.transition_events:
        ax1.axvline(x=ev.step, color='r', linestyle='--', alpha=0.5)
    ax1.set_xlabel('Step')
    ax1.set_ylabel('Complexity')
    ax1.set_title('Composite Complexity Evolution')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 各指标对比
    ax2 = fig.add_subplot(4, 2, 2)
    ax2.plot(trajectory["steps"], trajectory["kolmogorov"], label='Kolmogorov', alpha=0.8)
    ax2.plot(trajectory["steps"], trajectory["network"], label='Network', alpha=0.8)
    ax2.plot(trajectory["steps"], trajectory["entropy"], label='Entropy', alpha=0.8)
    ax2.set_xlabel('Step')
    ax2.set_ylabel('Complexity Index')
    ax2.set_title('Individual Complexity Indices')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 分形维数与Lyapunov指数
    ax3 = fig.add_subplot(4, 2, 3)
    ax3.plot(trajectory["steps"], trajectory["fractal"], 'g-', label='Fractal Dimension')
    ax3_twin = ax3.twinx()
    ax3_twin.plot(trajectory["steps"], trajectory["lyapunov"], 'r-', label='Lyapunov', alpha=0.7)
    ax3.set_xlabel('Step')
    ax3.set_ylabel('Fractal Dimension', color='g')
    ax3_twin.set_ylabel('Lyapunov Exponent', color='r')
    ax3.set_title('Fractal Dimension & Lyapunov Exponent')
    ax3.legend(loc='upper left')
    ax3_twin.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    # 4. 序参量与CUSUM
    ax4 = fig.add_subplot(4, 2, 4)
    ax4.plot(trajectory["steps"], trajectory["order_parameters"], 'b-', label='Order Parameter')
    ax4.set_xlabel('Step')
    ax4.set_ylabel('Order Parameter')
    ax4.set_title('Order Parameter Evolution')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. 沙堆崩塌大小分布（幂律检验）
    ax5 = fig.add_subplot(4, 2, 5)
    avalanche_sizes = np.array(engine.sandpile.avalanche_sizes)
    if len(avalanche_sizes) > 0:
        sizes = avalanche_sizes[avalanche_sizes > 0]
        if len(sizes) > 10:
            # 计算直方图
            hist, bins = np.histogram(sizes, bins=50)
            bin_centers = (bins[:-1] + bins[1:]) / 2
            
            # 只绘制非零部分
            mask = hist > 0
            ax5.loglog(bin_centers[mask], hist[mask], 'bo', markersize=3, alpha=0.6)
            
            # 幂律拟合线
            if len(bin_centers[mask]) > 3:
                log_x = np.log(bin_centers[mask])
                log_y = np.log(hist[mask])
                slope, intercept, r, _, _ = scipy_stats.linregress(log_x, log_y)
                fit_x = np.logspace(np.log10(bin_centers[mask].min()), 
                                   np.log10(bin_centers[mask].max()), 50)
                fit_y = np.exp(intercept) * fit_x ** slope
                ax5.loglog(fit_x, fit_y, 'r--', linewidth=2, 
                          label=f'Power law fit: slope={slope:.2f}, R²={r**2:.3f}')
            
            ax5.set_xlabel('Avalanche Size')
            ax5.set_ylabel('Frequency')
            ax5.set_title(f'Sandpile Avalanche Size Distribution (n={len(sizes)})')
            ax5.legend()
            ax5.grid(True, alpha=0.3, which='both')
    
    # 6. 相态分布饼图
    ax6 = fig.add_subplot(4, 2, 6)
    phase_counts = {}
    for ph in trajectory["phases"]:
        phase_counts[ph] = phase_counts.get(ph, 0) + 1
    colors = {'ordered': '#2ecc71', 'critical': '#f39c12', 
              'chaotic': '#e74c3c', 'transitioning': '#9b59b6'}
    labels = list(phase_counts.keys())
    sizes = list(phase_counts.values())
    pie_colors = [colors.get(l, '#3498db') for l in labels]
    ax6.pie(sizes, labels=labels, colors=pie_colors, autopct='%1.1f%%', startangle=90)
    ax6.set_title('Phase Distribution')
    
    # 7. 相变前后复杂度对比
    ax7 = fig.add_subplot(4, 2, 7)
    if engine.history.transition_events:
        jumps = []
        for ev in engine.history.transition_events:
            step = ev.step
            if step >= 5 and step < len(trajectory["composite"]) - 5:
                before = np.mean(trajectory["composite"][max(0, step-5):step])
                after = np.mean(trajectory["composite"][step:min(len(trajectory["composite"]), step+5)])
                jumps.append((step, after - before))
        
        if jumps:
            steps, jump_vals = zip(*jumps)
            colors_bar = ['green' if j > 0 else 'red' for j in jump_vals]
            ax7.bar(range(len(jumps)), jump_vals, color=colors_bar, alpha=0.7)
            ax7.set_xlabel('Transition Event')
            ax7.set_ylabel('Complexity Jump')
            ax7.set_title('Complexity Jump at Each Transition')
            ax7.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
            ax7.grid(True, alpha=0.3)
    else:
        ax7.text(0.5, 0.5, 'No transitions detected', ha='center', va='center', transform=ax7.transAxes)
        ax7.set_title('Complexity Jump at Each Transition')
    
    # 8. 系统状态热图（最后一步）
    ax8 = fig.add_subplot(4, 2, 8)
    if engine.state_history:
        state_matrix = np.array(engine.state_history[-50:]).T  # 最后50步
        im = ax8.imshow(state_matrix, aspect='auto', cmap='RdBu_r', 
                       interpolation='nearest')
        ax8.set_xlabel('Time Step (last 50)')
        ax8.set_ylabel('System Line')
        ax8.set_title('System State Evolution (Last 50 Steps)')
        plt.colorbar(im, ax=ax8)
    
    plt.tight_layout()
    
    if save_results:
        plt.savefig('/mnt/agents/output/OMNI-HUB/complexity_elevation_results.png', 
                   dpi=150, bbox_inches='tight')
        logger.info("\nVisualization saved to: /mnt/agents/output/OMNI-HUB/complexity_elevation_results.png")
    
    plt.close()
    
    # 打印详细报告
    logger.info(f"\n{'='*60}")
    logger.info("EXPERIMENT SUMMARY REPORT")
    logger.info(f"{'='*60}")
    
    cs = summary["complexity_stats"]
    logger.info(f"\n📊 COMPLEXITY EVOLUTION:")
    logger.info(f"  Initial:     {cs['initial']:.4f}")
    logger.info(f"  Final:       {cs['final']:.4f}")
    print(f"  Growth:      {cs['final'] - cs['initial']:+.4f} "
          f"({(cs['final']/cs['initial']-1)*100:+.1f}%)")
    logger.info(f"  Mean:        {cs['mean']:.4f}")
    logger.info(f"  Max:         {cs['max']:.4f}")
    
    logger.info(f"\n📈 INDICATOR STATISTICS:")
    for name, stats in summary["indicator_stats"].items():
        print(f"  {name:15s}: mean={stats['mean']:.4f}, std={stats['std']:.4f}, "
              f"final={stats['final']:.4f}")
    
    logger.info(f"\n🌀 PHASE DISTRIBUTION:")
    for ph, count in summary["phase_distribution"].items():
        pct = count / n_steps * 100
        logger.info(f"  {ph:15s}: {count:4d} steps ({pct:5.1f}%)")
    
    logger.info(f"\n⚡ TRANSITION EVENTS: {summary['transition_count']}")
    for ev in summary["transition_events"][:10]:  # 最多显示10个
        logger.info(f"  Step {ev['step']:4d}: jump={ev['jump']:+.4f}")
    
    logger.info(f"\n🏔️ SANDPILE POWER-LAW CHECK:")
    pl = summary["power_law_check"]
    if pl.get("status") == "success":
        logger.info(f"  Exponent τ:     {pl['power_law_exponent_tau']:.3f}")
        logger.info(f"  R²:             {pl['r_squared']:.4f}")
        logger.info(f"  Is Power Law:   {pl['is_power_law']}")
        logger.info(f"  Max Avalanche:  {pl['max_avalanche']}")
    else:
        logger.info(f"  Status: {pl.get('status')}")
    
    logger.info(f"\n✅ TRANSITION VERIFICATION:")
    tv = summary["transition_verification"]
    if tv.get("status") in ["verified", "partial"]:
        logger.info(f"  Pass Rate:      {tv['pass_rate']*100:.1f}%")
        logger.info(f"  All Passed:     {tv['all_passed']}")
    else:
        logger.info(f"  Status: {tv.get('status')}")
    
    logger.info(f"\n{'='*60}\n")
    
    return {
        "summary": summary,
        "trajectory": trajectory,
        "engine": engine
    }


# ============================================================================
# 主入口
# ============================================================================
"""
OMNI-HUB v11.0 — complexity_elevation_engine
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""

if __name__ == "__main__":
    # 运行完整实验
    results = run_experiment(n_steps=1000, num_lines=11, seed=42)
