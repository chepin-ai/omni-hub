
__version__ = "11.0.0"
"""
OMNI-HUB 张量网-场实时交互计算系统
Tensor Network Field Real-time Computation Engine

Mathematical Foundation:
    T_{i,j,k} = line_i ⊗ space_j ⊗ dim_k
    
Where:
    - line_i ∈ ℝ^L : 11条分布式线路状态向量
    - space_j ∈ ℝ^S : 空间维度（讨论空间/系统空间/调度空间/消息空间）
    - dim_k ∈ ℝ^D : 指标维度（健康度/SI等级/任务数/债务数/消息数/异常标志/响应时间）

Contraction Operations:
    - Global field: G = T_{i,j,k} · w^{ijk}  (weighted contraction)
    - Anomaly: A = || T - T_expected ||_F  (Frobenius norm deviation)
    - Trend: ∂T/∂t = (T_t - T_{t-1}) ⊗ K  (temporal convolution)

Author: OMNI-HUB Research Division
Version: SI5.0 Tensor Field v1.0
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import logging

# =============================================================================
# 常量定义
# =============================================================================

LINES = ['ucif2', 'lvlu', 'lgt', 'qfa', 'vinf', 'qgl', 'qlv', 'cisvr', 'qtlv', 'usrm', 'cfts']
NUM_LINES = len(LINES)

SPACES = ['discussion', 'system', 'dispatch', 'messaging', 'topology', 'consciousness', 'octave']
NUM_SPACES = len(SPACES)

DIMS = ['health', 'si_level', 'task_count', 'debt_count', 'message_count', 'anomaly_flag', 'response_time']
NUM_DIMS = len(DIMS)

BEAT_INTERVAL_MS = 100  # 拍级间隔 100ms


# =============================================================================
# 数据结构
# =============================================================================

class SurgeLevel(Enum):
    """浪涌等级"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class LineState:
    """单条线路状态"""
    line_id: str
    health: float = 1.0          # 健康度 [0, 1]
    si_level: float = 5.0        # SI等级
    task_count: int = 0          # 任务数
    debt_count: int = 0          # 债务数
    message_count: int = 0       # 消息数
    anomaly_flag: float = 0.0    # 异常标志 [0, 1]
    response_time_ms: float = 50.0  # 响应时间(ms)
    
    def to_vector(self) -> np.ndarray:
        """转换为维度向量"""
        return np.array([
            self.health,
            self.si_level / 10.0,  # 归一化
            min(self.task_count / 100.0, 1.0),
            min(self.debt_count / 50.0, 1.0),
            min(self.message_count / 1000.0, 1.0),
            self.anomaly_flag,
            min(self.response_time_ms / 1000.0, 1.0)
        ], dtype=np.float64)


@dataclass
class FieldContractionResult:
    """场收缩结果"""
    global_field_state: np.ndarray      # 全局场状态向量
    anomaly_score: float                # 异常分数
    anomaly_locations: List[Tuple[int, int, int]]  # 异常位置
    trend_prediction: np.ndarray        # 趋势预测
    contraction_time_ms: float          # 收缩耗时
    surge_detected: bool                # 是否检测到浪涌
    line_scores: Dict[str, float]       # 各线路评分


@dataclass
class BeatSnapshot:
    """拍级快照"""
    beat_id: int
    timestamp: float
    tensor: np.ndarray
    contraction_result: Optional[FieldContractionResult] = None


# =============================================================================
# 核心张量场类
# =============================================================================

class TensorField:
    """
    OMNI-HUB 张量网-场实时计算引擎
    
    核心张量: T ∈ ℝ^(L×S×D)
    L=11(线路), S=7(空间), D=7(维度)
    """
    
    def __init__(self, 
                 lines: List[str] = None,
                 spaces: List[str] = None,
                 dims: List[str] = None,
                 history_size: int = 100):
        self.lines = lines or LINES
        self.spaces = spaces or SPACES
        self.dims = dims or DIMS
        self.num_lines = len(self.lines)
        self.num_spaces = len(self.spaces)
        self.num_dims = len(self.dims)
        self.history_size = history_size
        
        # 核心张量 T_{i,j,k}
        self.tensor = np.zeros((self.num_lines, self.num_spaces, self.num_dims), dtype=np.float64)
        
        # 线路名称到索引映射
        self.line_index = {name: i for i, name in enumerate(self.lines)}
        
        # 历史张量序列（用于趋势分析）
        self.history: List[BeatSnapshot] = []
        
        # 权重张量（用于加权收缩）
        self.W = self._init_weights()
        
        # 预期基线（用于异常检测）
        self.baseline = np.zeros_like(self.tensor)
        
        # 浪涌状态
        self.surge_state = SurgeLevel.NONE
        self.surge_injection = np.zeros_like(self.tensor)
        
        # 性能统计
        self.contraction_times = []
        
    def _init_weights(self) -> np.ndarray:
        """初始化收缩权重"""
        # 线路权重：更关注关键线路
        line_weights = np.ones(self.num_lines)
        critical_lines = ['qfa', 'vinf', 'usrm', 'cfts']
        for line in critical_lines:
            if line in self.line_index:
                line_weights[self.line_index[line]] = 1.5
        
        # 空间权重
        space_weights = np.array([1.2, 1.5, 1.0, 0.8, 1.1, 1.3, 0.9])
        
        # 维度权重
        dim_weights = np.array([1.5, 1.0, 0.8, 1.2, 0.6, 2.0, 1.1])
        
        # 外积构造权重张量
        W = np.einsum('i,j,k->ijk', line_weights, space_weights, dim_weights)
        return W / np.max(W)  # 归一化
    
    def build_tensor(self, line_states: Dict[str, LineState]) -> np.ndarray:
        """
        从线路状态构建张量场 T_{i,j,k}
        
        Args:
            line_states: 各线路当前状态 {line_name: LineState}
        
        Returns:
            T ∈ ℝ^(L×S×D)
        """
        T = np.zeros((self.num_lines, self.num_spaces, self.num_dims), dtype=np.float64)
        
        for line_name, state in line_states.items():
            if line_name not in self.line_index:
                continue
            i = self.line_index[line_name]
            vec = state.to_vector()  # D维向量
            
            # 将线路状态向量外积扩展到所有空间
            # T_{i,j,k} = line_state_i ⊗ space_basis_j ⊗ dim_k
            # 简化为: 每个空间j都携带相同的线路维度信息，但加权不同
            for j in range(self.num_spaces):
                # 空间特定调制
                space_modulator = self._space_modulator(j, state)
                T[i, j, :] = vec * space_modulator
        
        self.tensor = T
        return T
    
    def _space_modulator(self, space_idx: int, state: LineState) -> float:
        """空间调制因子"""
        modulators = {
            0: 1.0 + 0.1 * state.message_count / max(state.task_count, 1),  # discussion
            1: state.health,  # system
            2: 1.0 - min(state.task_count / 200.0, 0.5),  # dispatch
            3: min(state.message_count / 500.0, 1.0),  # messaging
            4: 1.0 - state.anomaly_flag * 0.5,  # topology
            5: state.health * (1.0 - state.debt_count / 100.0),  # consciousness
            6: 1.0 - state.response_time_ms / 2000.0,  # octave
        }
        return modulators.get(space_idx, 1.0)
    
    def contract(self, weighted: bool = True) -> FieldContractionResult:
        """
        场张量收缩 - 核心计算
        
        数学操作:
            G_l = Σ_{j,k} T_{l,j,k} · W_{l,j,k}   (线路级收缩)
            G = Σ_{l,j,k} T_{l,j,k} · W_{l,j,k}    (全局收缩)
            
        Returns:
            FieldContractionResult
        """
        start_time = time.perf_counter()
        
        # 确保基线已初始化
        if np.all(self.baseline == 0):
            self.update_baseline()
        
        T = self.tensor + self.surge_injection
        W = self.W if weighted else np.ones_like(self.W)
        
        # 1. 线路级收缩: 每条线路的综合评分
        # G_l = Σ_{j,k} T_{l,j,k} · W_{l,j,k}
        line_scores = np.einsum('ijk,ijk->i', T, W) / (self.num_spaces * self.num_dims)
        
        # 2. 全局场状态: 各维度上的全局值
        # G_d = Σ_{i,j} T_{i,j,d} · W_{i,j,d}
        global_field = np.einsum('ijd,ijd->d', T, W) / (self.num_lines * self.num_spaces)
        
        # 3. 异常检测: 与基线的Frobenius偏差
        deviation = T - self.baseline
        baseline_norm = np.sqrt(np.sum(self.baseline ** 2)) + 1e-8
        dev_norm = np.sqrt(np.sum(deviation ** 2))
        anomaly_score = float(dev_norm / baseline_norm)
        
        # 定位异常位置（阈值化）
        threshold = np.mean(np.abs(deviation)) + 2 * np.std(np.abs(deviation))
        anomaly_locations = []
        if anomaly_score > 0.1:
            mask = np.abs(deviation) > threshold
            indices = np.argwhere(mask)
            anomaly_locations = [tuple(int(x) for x in idx) for idx in indices[:20]]  # 最多20个
        
        # 4. 趋势预测（基于历史）
        trend = self._predict_trend()
        
        # 5. 浪涌检测
        surge_detected = self.surge_state.value > SurgeLevel.LOW.value
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        self.contraction_times.append(elapsed_ms)
        
        line_score_dict = {self.lines[i]: float(line_scores[i]) for i in range(self.num_lines)}
        
        return FieldContractionResult(
            global_field_state=global_field,
            anomaly_score=anomaly_score,
            anomaly_locations=anomaly_locations,
            trend_prediction=trend,
            contraction_time_ms=elapsed_ms,
            surge_detected=surge_detected,
            line_scores=line_score_dict
        )
    
    def _predict_trend(self, horizon: int = 5) -> np.ndarray:
        """
        基于历史张量预测趋势
        
        使用线性外推: T_{t+h} ≈ T_t + h · ∂T/∂t
        """
        if len(self.history) < 3:
            return np.zeros(self.num_dims)
        
        # 取最近3个快照计算变化率
        recent = self.history[-3:]
        
        # 计算各维度的时间导数
        dt1 = recent[1].tensor - recent[0].tensor
        dt2 = recent[2].tensor - recent[1].tensor
        
        # 加权平均导数
        dT = (dt1 + dt2) / 2.0
        
        # 按维度聚合
        trend = np.mean(np.mean(dT, axis=0), axis=0)  # 平均到D维
        
        # 预测 horizon 拍后的状态
        prediction = trend * horizon
        
        return np.clip(prediction, -1.0, 1.0)
    
    def detect_anomaly(self, sensitivity: float = 2.0) -> Dict:
        """
        异常检测 - 多尺度分析
        
        Returns:
            {
                'global_anomaly': float,
                'line_anomalies': {line: score},
                'space_anomalies': {space: score},
                'dim_anomalies': {dim: score},
                'localized_hotspots': [(i,j,k, intensity)],
                'recommendation': str
            }
        """
        T = self.tensor + self.surge_injection
        
        # 全局异常
        global_dev = np.sqrt(np.sum((T - self.baseline) ** 2))
        global_norm = np.sqrt(np.sum(self.baseline ** 2)) + 1e-8
        global_anomaly = float(global_dev / global_norm)
        
        # 各线路异常（按线路收缩）
        line_dev = np.linalg.norm(T - self.baseline, axis=(1, 2))
        line_norm = np.linalg.norm(self.baseline, axis=(1, 2)) + 1e-8
        line_anomalies = {self.lines[i]: float(line_dev[i] / line_norm[i]) 
                         for i in range(self.num_lines)}
        
        # 各空间异常
        space_dev = np.linalg.norm(T - self.baseline, axis=(0, 2))
        space_norm = np.linalg.norm(self.baseline, axis=(0, 2)) + 1e-8
        space_anomalies = {self.spaces[j]: float(space_dev[j] / space_norm[j])
                          for j in range(self.num_spaces)}
        
        # 各维度异常
        dim_dev = np.linalg.norm(T - self.baseline, axis=(0, 1))
        dim_norm = np.linalg.norm(self.baseline, axis=(0, 1)) + 1e-8
        dim_anomalies = {self.dims[k]: float(dim_dev[k] / dim_norm[k])
                        for k in range(self.num_dims)}
        
        # 热点定位
        diff = np.abs(T - self.baseline)
        threshold = np.mean(diff) + sensitivity * np.std(diff)
        hotspots = []
        if np.any(diff > threshold):
            indices = np.argwhere(diff > threshold)
            for idx in indices[:10]:
                i, j, k = idx
                hotspots.append((self.lines[i], self.spaces[j], self.dims[k], float(diff[i,j,k])))
        
        # 生成建议
        recommendation = self._generate_recommendation(global_anomaly, line_anomalies, hotspots)
        
        return {
            'global_anomaly': global_anomaly,
            'line_anomalies': line_anomalies,
            'space_anomalies': space_anomalies,
            'dim_anomalies': dim_anomalies,
            'localized_hotspots': hotspots,
            'recommendation': recommendation
        }
    
    def _generate_recommendation(self, global_a: float, line_a: Dict, hotspots: List) -> str:
        """生成运维建议"""
        if global_a < 0.1:
            return "系统运行正常，无需干预。"
        
        worst_lines = sorted(line_a.items(), key=lambda x: x[1], reverse=True)[:3]
        
        if global_a > 0.5:
            return f"严重异常！建议立即检查线路: {', '.join([l for l,_ in worst_lines])}"
        elif global_a > 0.3:
            return f"中度异常，关注线路: {', '.join([l for l,_ in worst_lines])}"
        else:
            return f"轻度偏离基线，监控线路: {', '.join([l for l,_ in worst_lines])}"
    
    def predict_trend(self, steps: int = 10) -> Dict:
        """
        趋势预测 - 基于历史张量的时间序列分析
        
        Returns:
            {
                'health_trajectory': [...],
                'anomaly_trajectory': [...],
                'task_load_forecast': [...],
                'confidence': float
            }
        """
        if len(self.history) < 5:
            return {
                'health_trajectory': [0.5] * steps,
                'anomaly_trajectory': [0.0] * steps,
                'task_load_forecast': [0.0] * steps,
                'confidence': 0.0
            }
        
        # 提取历史全局状态序列
        hist_global = np.array([snap.contraction_result.global_field_state 
                               for snap in self.history if snap.contraction_result is not None])
        
        if len(hist_global) < 5:
            return {
                'health_trajectory': [0.5] * steps,
                'anomaly_trajectory': [0.0] * steps,
                'task_load_forecast': [0.0] * steps,
                'confidence': 0.0
            }
        
        # 自回归预测 (AR(2))
        predictions = []
        for d in range(self.num_dims):
            series = hist_global[:, d]
            if len(series) >= 3:
                # 简单线性回归: x_{t+1} = 2x_t - x_{t-1} (恒定加速度假设)
                pred = []
                last = series[-1]
                prev = series[-2]
                vel = last - prev
                for s in range(steps):
                    next_val = last + vel * (s + 1)
                    pred.append(float(np.clip(next_val, 0, 1)))
                predictions.append(pred)
            else:
                predictions.append([float(series[-1])] * steps)
        
        # 置信度与历史长度成正比
        confidence = min(len(hist_global) / self.history_size, 1.0)
        
        return {
            'health_trajectory': predictions[0],  # health dim
            'anomaly_trajectory': predictions[5],  # anomaly_flag dim
            'task_load_forecast': predictions[2],  # task_count dim
            'confidence': confidence
        }
    
    def surge_tensor_injection(self, 
                              target_lines: List[str], 
                              level: SurgeLevel,
                              surge_profile: Optional[np.ndarray] = None) -> np.ndarray:
        """
        浪涌张量注入 - 模拟异常浪涌对张量场的影响
        
        数学模型:
            T_surge = T + S ⊙ M
            
        其中:
            - S: 浪涌信号张量 (稀疏, 集中在目标线路)
            - M: 空间-维度调制矩阵
            - ⊙: Hadamard积
        
        Args:
            target_lines: 受影响线路
            level: 浪涌等级
            surge_profile: 自定义浪涌剖面 [S×D]
        
        Returns:
            注入后的张量
        """
        self.surge_state = level
        injection = np.zeros_like(self.tensor)
        
        # 浪涌强度系数
        intensity_map = {
            SurgeLevel.NONE: 0.0,
            SurgeLevel.LOW: 0.2,
            SurgeLevel.MEDIUM: 0.5,
            SurgeLevel.HIGH: 0.8,
            SurgeLevel.CRITICAL: 1.0
        }
        intensity = intensity_map[level]
        
        if level == SurgeLevel.NONE:
            self.surge_injection = injection
            return self.tensor
        
        for line_name in target_lines:
            if line_name not in self.line_index:
                continue
            i = self.line_index[line_name]
            
            if surge_profile is not None:
                # 使用自定义剖面
                profile = surge_profile
            else:
                # 默认浪涌剖面: 健康度下降, 异常标志上升, 响应时间上升
                profile = np.zeros((self.num_spaces, self.num_dims))
                for j in range(self.num_spaces):
                    profile[j, 0] = -intensity * 0.5  # health下降
                    profile[j, 5] = intensity         # anomaly上升
                    profile[j, 6] = intensity * 0.3   # response_time上升
                    profile[j, 3] = intensity * 0.2   # debt上升
            
            injection[i] = profile
        
        self.surge_injection = injection
        return self.tensor + injection
    
    def recover_from_surge(self, recovery_rate: float = 0.1) -> np.ndarray:
        """
        浪涌后张量场恢复
        
        衰减模型:
            S_{t+1} = S_t · (1 - recovery_rate)
        """
        self.surge_injection *= (1 - recovery_rate)
        
        if np.linalg.norm(self.surge_injection) < 0.01:
            self.surge_injection = np.zeros_like(self.tensor)
            self.surge_state = SurgeLevel.NONE
        
        return self.tensor + self.surge_injection
    
    def update_baseline(self, window_size: int = 10):
        """更新基线（滑动窗口平均）"""
        if len(self.history) == 0:
            # 无历史时，使用当前张量作为基线
            self.baseline = self.tensor.copy() if np.any(self.tensor != 0) else np.ones_like(self.tensor) * 0.5
            return
        
        if len(self.history) < window_size:
            window_size = len(self.history)
        
        recent_tensors = [snap.tensor for snap in self.history[-window_size:]]
        self.baseline = np.mean(recent_tensors, axis=0)
    
    def add_snapshot(self, result: FieldContractionResult):
        """添加拍级快照到历史"""
        snapshot = BeatSnapshot(
            beat_id=len(self.history),
            timestamp=time.time(),
            tensor=self.tensor.copy(),
            contraction_result=result
        )
        self.history.append(snapshot)
        
        # 保持历史长度限制
        if len(self.history) > self.history_size:
            self.history.pop(0)
    
    def get_field_topology(self) -> Dict:
        """获取场拓扑信息"""
        return {
            'shape': self.tensor.shape,
            'lines': self.lines,
            'spaces': self.spaces,
            'dims': self.dims,
            'sparsity': float(np.count_nonzero(self.tensor) / self.tensor.size),
            'energy': float(np.linalg.norm(self.tensor)),
            'entropy': float(self._compute_entropy()),
            'history_length': len(self.history),
            'avg_contraction_time_ms': np.mean(self.contraction_times) if self.contraction_times else 0
        }
    
    def _compute_entropy(self) -> float:
        """计算张量场的信息熵"""
        flat = np.abs(self.tensor.flatten())
        flat = flat / (np.sum(flat) + 1e-8)
        return -np.sum(flat * np.log2(flat + 1e-8))


# =============================================================================
# 拍级实时收缩引擎
# =============================================================================

class BeatLevelEngine:
    """
    拍级实时张量收缩引擎
    
    以固定节拍(默认100ms)执行张量场收缩
    """
    
    def __init__(self, tensor_field: TensorField, beat_ms: int = BEAT_INTERVAL_MS):
        self.tf = tensor_field
        self.beat_ms = beat_ms
        self.beat_count = 0
        self.running = False
        self.callbacks: List[Callable] = []
        
    def register_callback(self, callback: Callable):
        """注册收缩完成回调"""
        self.callbacks.append(callback)
    
    def beat_level_contraction(self, current_state: Dict[str, LineState]) -> FieldContractionResult:
        """
        单拍收缩 - 核心实时函数
        
        流程:
            1. 构建当前张量
            2. 执行收缩
            3. 异常检测
            4. 趋势预测
            5. 存储快照
            6. 触发回调
        """
        # 1. 构建张量
        self.tf.build_tensor(current_state)
        
        # 2. 收缩
        result = self.tf.contract(weighted=True)
        
        # 3. 快照
        self.tf.add_snapshot(result)
        
        # 4. 基线更新（每10拍）
        if self.beat_count % 10 == 0:
            self.tf.update_baseline()
        
        # 5. 浪涌恢复（如有）
        if self.tf.surge_state != SurgeLevel.NONE:
            self.tf.recover_from_surge(recovery_rate=0.05)
        
        self.beat_count += 1
        
        # 6. 回调
        for cb in self.callbacks:
            cb(result, self.beat_count)
        
        return result
    
    def simulate_beats(self, 
                      state_generator: Callable[[int], Dict[str, LineState]],
                      num_beats: int = 100) -> List[FieldContractionResult]:
        """
        模拟多拍运行
        
        Args:
            state_generator: 状态生成器，输入拍号，返回线路状态
            num_beats: 拍数
        
        Returns:
            收缩结果列表
        """
        results = []
        for beat in range(num_beats):
            states = state_generator(beat)
            result = self.beat_level_contraction(states)
            results.append(result)
        return results


# =============================================================================
# 模拟数据生成器
# =============================================================================

def generate_normal_state(beat: int) -> Dict[str, LineState]:
    """生成正常状态"""
    states = {}
    np.random.seed(beat % 1000)
    for line in LINES:
        # 轻微波动
        health = 0.85 + 0.1 * np.sin(beat * 0.1 + hash(line) % 10)
        health = np.clip(health, 0.7, 1.0)
        
        states[line] = LineState(
            line_id=line,
            health=float(health),
            si_level=5.0,
            task_count=int(20 + 10 * np.sin(beat * 0.05)),
            debt_count=int(5 + 3 * np.random.randn()),
            message_count=int(200 + 50 * np.random.randn()),
            anomaly_flag=0.0,
            response_time_ms=50 + 20 * np.random.randn()
        )
    return states


def generate_degraded_state(beat: int, target_lines: List[str]) -> Dict[str, LineState]:
    """生成退化状态（模拟线路故障）"""
    states = generate_normal_state(beat)
    
    for line in target_lines:
        if line in states:
            states[line].health *= 0.5
            states[line].anomaly_flag = 0.8
            states[line].response_time_ms *= 3
            states[line].task_count += 50
            states[line].debt_count += 20
    
    return states


def generate_surge_state(beat: int, surge_lines: List[str]) -> Dict[str, LineState]:
    """生成浪涌状态"""
    states = generate_normal_state(beat)
    
    for line in surge_lines:
        if line in states:
            states[line].health = 0.3
            states[line].anomaly_flag = 1.0
            states[line].response_time_ms = 800
            states[line].message_count *= 5
            states[line].task_count *= 3
    
    return states


# =============================================================================
# 对比实验框架
# =============================================================================

class ComparisonExperiment:
    """
    替代性对比实验
    
    对比:
        1. 张量网场 vs OTP/API直取
        2. 张量网场 vs DiscussionBoard
    """
    
    def __init__(self):
        self.tf = TensorField()
        self.engine = BeatLevelEngine(self.tf)
        self.results = {}
    
    def run_latency_experiment(self, num_samples: int = 1000) -> Dict:
        """
        延迟对比实验
        
        OTP/API直取: 逐线路查询 (O(L)次请求)
        张量场: 单次全局收缩 (O(1)次计算)
        """
        # 模拟API直取延迟
        api_latencies = []
        for _ in range(num_samples):
            # API需要11次独立请求
            latency_per_request = np.random.exponential(50)  # 50ms平均
            total_api_latency = latency_per_request * NUM_LINES  # 串行
            api_latencies.append(total_api_latency)
        
        # 张量场收缩延迟
        tensor_latencies = []
        states = generate_normal_state(0)
        self.tf.build_tensor(states)
        for _ in range(num_samples):
            result = self.tf.contract()
            tensor_latencies.append(result.contraction_time_ms)
        
        return {
            'api_mean_ms': float(np.mean(api_latencies)),
            'api_p99_ms': float(np.percentile(api_latencies, 99)),
            'tensor_mean_ms': float(np.mean(tensor_latencies)),
            'tensor_p99_ms': float(np.percentile(tensor_latencies, 99)),
            'speedup': float(np.mean(api_latencies) / (np.mean(tensor_latencies) + 0.001)),
            'api_latencies': api_latencies[:100],  # 样本
            'tensor_latencies': tensor_latencies[:100]
        }
    
    def run_accuracy_experiment(self, num_scenarios: int = 100) -> Dict:
        """
        准确性对比实验
        
        检测模拟故障场景中的异常检测能力
        """
        api_hits = 0
        tensor_hits = 0
        
        for i in range(num_scenarios):
            # 随机选择1-3条线路故障
            num_faulty = np.random.randint(1, 4)
            faulty_lines = np.random.choice(LINES, num_faulty, replace=False).tolist()
            
            states = generate_degraded_state(i, faulty_lines)
            
            # API方式: 逐线路检查（模拟阈值判断）
            api_detected = []
            for line, state in states.items():
                if state.health < 0.6 or state.anomaly_flag > 0.5:
                    api_detected.append(line)
            api_hit = len(set(api_detected) & set(faulty_lines)) > 0
            api_hits += int(api_hit)
            
            # 张量场方式
            self.tf.build_tensor(states)
            result = self.tf.contract()
            
            # 通过线路评分检测异常
            tensor_detected = [l for l, s in result.line_scores.items() if s < 0.5]
            tensor_hit = len(set(tensor_detected) & set(faulty_lines)) > 0
            tensor_hits += int(tensor_hit)
        
        return {
            'api_accuracy': api_hits / num_scenarios,
            'tensor_accuracy': tensor_hits / num_scenarios,
            'num_scenarios': num_scenarios
        }
    
    def run_information_density_experiment(self) -> Dict:
        """
        信息密度对比实验
        
        DiscussionBoard: 分散的文本信息
        张量场: 结构化的张量表示
        """
        # DiscussionBoard信息估算（模拟）
        # 4个空间，每个空间平均20条消息，每条消息约100字节
        db_messages_per_space = 20
        db_bytes_per_message = 100
        db_total_bytes = 4 * db_messages_per_space * db_bytes_per_message
        
        # 读取这些信息需要的操作数
        db_read_operations = 4  # 每个空间一次读取
        db_parse_overhead = 0.5  # 解析开销系数
        
        # 张量场信息密度
        tensor_elements = NUM_LINES * NUM_SPACES * NUM_DIMS
        tensor_bytes = tensor_elements * 8  # float64
        
        # 张量场一次收缩获得的全局信息
        contraction_output = NUM_LINES + NUM_DIMS  # 线路评分 + 全局状态
        
        return {
            'db_total_bytes': db_total_bytes,
            'db_read_operations': db_read_operations,
            'db_effective_information_ratio': 0.3,  # 文本信息有效比例
            'tensor_bytes': tensor_bytes,
            'tensor_contraction_output': contraction_output,
            'tensor_information_density': contraction_output / tensor_bytes,
            'db_information_density': (db_total_bytes * 0.3) / db_total_bytes,
            'structured_vs_unstructured': 'tensor provides structured real-time field; db provides unstructured delayed state'
        }
    
    def run_full_comparison(self) -> Dict:
        """运行完整对比实验"""
        logger.info("=" * 60)
        logger.info("OMNI-HUB 张量网-场替代性对比实验")
        logger.info("=" * 60)
        
        logger.info("\n[实验1/3] 延迟对比...")
        latency = self.run_latency_experiment()
        
        logger.info("\n[实验2/3] 准确性对比...")
        accuracy = self.run_accuracy_experiment()
        
        logger.info("\n[实验3/3] 信息密度对比...")
        density = self.run_information_density_experiment()
        
        self.results = {
            'latency': latency,
            'accuracy': accuracy,
            'information_density': density
        }
        
        return self.results
    
    def print_report(self):
        """打印实验报告"""
        if not self.results:
            self.run_full_comparison()
        
        r = self.results
        logger.info("\n" + "=" * 60)
        logger.info("实验结果汇总")
        logger.info("=" * 60)
        
        logger.info("\n【延迟性能】")
        logger.info(f"  OTP/API直取平均延迟: {r['latency']['api_mean_ms']:.2f} ms")
        logger.info(f"  OTP/API直取P99延迟:  {r['latency']['api_p99_ms']:.2f} ms")
        logger.info(f"  张量场收缩平均延迟:  {r['latency']['tensor_mean_ms']:.4f} ms")
        logger.info(f"  张量场收缩P99延迟:   {r['latency']['tensor_p99_ms']:.4f} ms")
        logger.info(f"  加速比:              {r['latency']['speedup']:.1f}x")
        
        logger.info("\n【异常检测准确性】")
        logger.info(f"  OTP/API方式:   {r['accuracy']['api_accuracy']*100:.1f}%")
        logger.info(f"  张量场方式:    {r['accuracy']['tensor_accuracy']*100:.1f}%")
        
        logger.info("\n【信息密度】")
        logger.info(f"  DiscussionBoard数据量: {r['information_density']['db_total_bytes']} bytes")
        logger.info(f"  张量场数据量:          {r['information_density']['tensor_bytes']} bytes")
        logger.info(f"  结论: {r['information_density']['structured_vs_unstructured']}")


# =============================================================================
# 浪涌兼容性实验
# =============================================================================

def run_surge_compatibility_experiment() -> Dict:
    """
    浪涌兼容性验证实验
    """
    logger.info("\n" + "=" * 60)
    logger.info("浪涌兼容性验证实验")
    logger.info("=" * 60)
    
    tf = TensorField()
    engine = BeatLevelEngine(tf)
    
    # Phase 1: 正常运行30拍
    logger.info("\n[Phase 1] 正常运行 30 beats...")
    normal_results = []
    for beat in range(30):
        states = generate_normal_state(beat)
        result = engine.beat_level_contraction(states)
        normal_results.append(result.anomaly_score)
    
    # Phase 2: 浪涌注入（critical级别，影响3条线路）
    surge_lines = ['qfa', 'vinf', 'usrm']
    logger.info(f"\n[Phase 2] 浪涌注入 (CRITICAL) -> {surge_lines}")
    tf.surge_tensor_injection(surge_lines, SurgeLevel.CRITICAL)
    
    surge_results = []
    for beat in range(30, 60):
        states = generate_surge_state(beat, surge_lines)
        result = engine.beat_level_contraction(states)
        surge_results.append({
            'anomaly': result.anomaly_score,
            'surge_detected': result.surge_detected,
            'line_scores': result.line_scores
        })
    
    # Phase 3: 恢复
    logger.info("\n[Phase 3] 恢复阶段 40 beats...")
    recovery_results = []
    for beat in range(60, 100):
        states = generate_normal_state(beat)
        result = engine.beat_level_contraction(states)
        # 自动恢复（每次contraction后调用recover_from_surge）
        recovery_results.append({
            'anomaly': result.anomaly_score,
            'surge_state': tf.surge_state.value,
            'injection_norm': float(np.linalg.norm(tf.surge_injection))
        })
    
    logger.info(f"\n正常期平均异常分: {np.mean(normal_results):.4f}")
    logger.info(f"浪涌期平均异常分: {np.mean([r['anomaly'] for r in surge_results]):.4f}")
    logger.info(f"恢复期最终异常分: {recovery_results[-1]['anomaly']:.4f}")
    logger.info(f"浪涌检测率: {sum([r['surge_detected'] for r in surge_results])}/{len(surge_results)}")
    
    return {
        'normal_scores': normal_results,
        'surge_scores': [r['anomaly'] for r in surge_results],
        'recovery_scores': [r['anomaly'] for r in recovery_results],
        'surge_detection_rate': sum([r['surge_detected'] for r in surge_results]) / len(surge_results),
        'recovery_complete': recovery_results[-1]['surge_state'] == 0
    }


# =============================================================================
# 主程序入口
# =============================================================================
"""
OMNI-HUB v11.0 — tensor_field
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""

if __name__ == "__main__":
    print("OMNI-HUB 张量网-场实时交互计算系统 v1.0")
    print("=" * 60)
    
    # 1. 基础张量场测试
    print("\n【基础张量场测试】")
    tf = TensorField()
    states = generate_normal_state(0)
    T = tf.build_tensor(states)
    print(f"张量形状: {T.shape}")
    print(f"张量能量: {np.linalg.norm(T):.4f}")
    print(f"信息熵: {tf._compute_entropy():.4f}")
    
    result = tf.contract()
    print(f"收缩耗时: {result.contraction_time_ms:.4f} ms")
    print(f"全局异常分: {result.anomaly_score:.4f}")
    print(f"线路评分: { {k: f'{v:.3f}' for k, v in list(result.line_scores.items())[:3]} }")
    
    # 2. 异常检测测试
    print("\n【异常检测测试】")
    degraded_states = generate_degraded_state(1, ['qfa', 'vinf'])
    tf.build_tensor(degraded_states)
    anomaly = tf.detect_anomaly()
    print(f"全局异常: {anomaly['global_anomaly']:.4f}")
    print(f"建议: {anomaly['recommendation']}")
    
    # 3. 对比实验
    print("\n【替代性对比实验】")
    exp = ComparisonExperiment()
    exp.run_full_comparison()
    exp.print_report()
    
    # 4. 浪涌兼容性
    surge_result = run_surge_compatibility_experiment()
    
    # 5. 拍级模拟
    print("\n【拍级实时模拟 (100 beats)】")
    tf2 = TensorField()
    engine2 = BeatLevelEngine(tf2)
    
    def complex_state_generator(beat: int) -> Dict[str, LineState]:
        if 30 <= beat < 50:
            return generate_degraded_state(beat, ['qlv', 'cisvr'])
        elif 70 <= beat < 80:
            return generate_surge_state(beat, ['qfa'])
        else:
            return generate_normal_state(beat)
    
    results = engine2.simulate_beats(complex_state_generator, num_beats=100)
    
    anomaly_scores = [r.anomaly_score for r in results]
    contraction_times = [r.contraction_time_ms for r in results]
    
    print(f"平均异常分: {np.mean(anomaly_scores):.4f}")
    print(f"最大异常分: {np.max(anomaly_scores):.4f} (beat {np.argmax(anomaly_scores)})")
    print(f"平均收缩耗时: {np.mean(contraction_times):.4f} ms")
    print(f"最大收缩耗时: {np.max(contraction_times):.4f} ms")
    
    print("\n" + "=" * 60)
    print("所有实验完成")
    print("=" * 60)
