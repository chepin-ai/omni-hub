
"""
OMNI-HUB v4.1 InsightDetector - 顿悟检测器架构
================================================
基于认知科学中的顿悟理论实现：
- 僵局(Impasse) -> 无意识加工 -> 突然解决(Sudden Insight)
- 正免疫函数：距离突然缩短
- 认知联结：远距离元素突然关联
- 表征变化：问题表征的突然重组

Author: OMNI-HUB Architecture Team
Version: 4.1.0
"""

__version__ = "11.0.0"
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import deque
import warnings
from scipy.spatial.distance import cosine, euclidean
from scipy.stats import entropy
import json

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# 顿悟事件数据结构
# ---------------------------------------------------------------------------

@dataclass
class InsightEvent:
    """顿悟事件记录"""
    timestamp: int
    impasse_start: int
    impasse_duration: int
    jump_magnitude: float
    post_performance: float
    pre_performance: float
    strength: float = 0.0
    restructuring_degree: float = 0.0
    phi_surge: float = 0.0
    dimension_change: int = 0
    lines_involved: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'impasse_start': self.impasse_start,
            'impasse_duration': self.impasse_duration,
            'jump_magnitude': round(self.jump_magnitude, 4),
            'post_performance': round(self.post_performance, 4),
            'pre_performance': round(self.pre_performance, 4),
            'strength': round(self.strength, 4),
            'restructuring_degree': round(self.restructuring_degree, 4),
            'phi_surge': round(self.phi_surge, 4),
            'dimension_change': self.dimension_change,
            'lines_involved': self.lines_involved
        }


@dataclass
class ImpasseRecord:
    """僵局记录"""
    start_time: int
    end_time: int
    duration: int
    intensity: float
    avg_change_rate: float
    lines_affected: List[int]


# ---------------------------------------------------------------------------
# 表征空间 (Representation Space)
# ---------------------------------------------------------------------------

class RepresentationSpace:
    """
    表征空间：将高维系统状态映射到低维表征空间
    """

    def __init__(self, n_components: int = 8, history_window: int = 100):
        self.n_components = n_components
        self.history_window = history_window
        self.state_history: deque = deque(maxlen=history_window)
        self.representation_history: deque = deque(maxlen=history_window)
        self.pca_basis: Optional[np.ndarray] = None
        self.mean_vec: Optional[np.ndarray] = None
        self.active_dimensions: int = n_components

    def encode(self, state: np.ndarray, method: str = 'adaptive_pca') -> np.ndarray:
        state = np.asarray(state).flatten()
        self.state_history.append(state)

        if method == 'direct':
            rep = state[:self.n_components] if len(state) >= self.n_components else \
                  np.pad(state, (0, self.n_components - len(state)))
            self.representation_history.append(rep)
            return rep

        elif method == 'pca':
            if len(self.state_history) < self.n_components * 2:
                rep = state[:self.n_components] if len(state) >= self.n_components else \
                      np.pad(state, (0, self.n_components - len(state)))
            else:
                rep = self._pca_transform(state)
            self.representation_history.append(rep)
            return rep

        elif method == 'adaptive_pca':
            if len(self.state_history) < self.n_components * 2:
                rep = state[:self.n_components] if len(state) >= self.n_components else \
                      np.pad(state, (0, self.n_components - len(state)))
            else:
                rep = self._adaptive_pca_transform(state)
            self.representation_history.append(rep)
            return rep

        elif method == 'random_projection':
            if not hasattr(self, '_rp_matrix'):
                np.random.seed(42)
                self._rp_matrix = np.random.randn(len(state), self.n_components) / np.sqrt(len(state))
            rep = state @ self._rp_matrix
            self.representation_history.append(rep)
            return rep
        else:
            raise ValueError(f"Unknown encoding method: {method}")

    def _pca_transform(self, state: np.ndarray) -> np.ndarray:
        if self.pca_basis is None or len(self.state_history) % 50 == 0:
            data = np.array(list(self.state_history))
            self.mean_vec = np.mean(data, axis=0)
            centered = data - self.mean_vec
            cov = centered.T @ centered / (len(data) - 1)
            eigvals, eigvecs = np.linalg.eigh(cov)
            idx = np.argsort(eigvals)[::-1]
            self.pca_basis = eigvecs[:, idx[:self.n_components]]

        centered_state = state - self.mean_vec
        return centered_state @ self.pca_basis

    def _adaptive_pca_transform(self, state: np.ndarray) -> np.ndarray:
        data = np.array(list(self.state_history))
        self.mean_vec = np.mean(data, axis=0)
        centered = data - self.mean_vec
        cov = centered.T @ centered / (len(data) - 1)
        eigvals, eigvecs = np.linalg.eigh(cov)
        idx = np.argsort(eigvals)[::-1]

        threshold = np.mean(eigvals) * 0.1
        effective_dims = np.sum(eigvals > threshold)
        self.active_dimensions = min(effective_dims, self.n_components)

        basis = eigvecs[:, idx[:self.active_dimensions]]
        centered_state = state - self.mean_vec
        rep = centered_state @ basis

        if len(rep) < self.n_components:
            rep = np.pad(rep, (0, self.n_components - len(rep)))
        return rep

    def distance(self, state_a: np.ndarray, state_b: np.ndarray,
                 metric: str = 'combined') -> float:
        rep_a = self.encode(state_a)
        rep_b = self.encode(state_b)

        if metric == 'euclidean':
            return float(euclidean(rep_a, rep_b))
        elif metric == 'cosine':
            sim = 1 - cosine(rep_a, rep_b)
            return float(np.arccos(np.clip(sim, -1, 1)))
        elif metric == 'manhattan':
            return float(np.sum(np.abs(rep_a - rep_b)))
        elif metric == 'combined':
            eucl = euclidean(rep_a, rep_b)
            sim = 1 - cosine(rep_a, rep_b)
            angle = np.arccos(np.clip(sim, -1, 1))
            eucl_norm = eucl / (np.linalg.norm(rep_a) + np.linalg.norm(rep_b) + 1e-8)
            return float(eucl_norm + angle / np.pi)
        else:
            raise ValueError(f"Unknown distance metric: {metric}")

    def trajectory(self, states: List[np.ndarray]) -> Dict[str, float]:
        if len(states) < 3:
            return {'path_length': 0, 'curvature': 0, 'tortuosity': 1, 'exploration_volume': 0}

        reps = [self.encode(s) for s in states]
        reps = np.array(reps)

        path_length = sum(euclidean(reps[i], reps[i+1]) for i in range(len(reps)-1))
        endpoint_dist = euclidean(reps[0], reps[-1])
        tortuosity = path_length / (endpoint_dist + 1e-8)

        curvatures = []
        for i in range(1, len(reps)-1):
            v1 = reps[i] - reps[i-1]
            v2 = reps[i+1] - reps[i]
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 > 1e-8 and norm2 > 1e-8:
                cos_angle = np.dot(v1, v2) / (norm1 * norm2)
                cos_angle = np.clip(cos_angle, -1, 1)
                curvatures.append(np.arccos(cos_angle))
        avg_curvature = np.mean(curvatures) if curvatures else 0

        ranges = np.ptp(reps, axis=0)
        exploration_volume = np.prod(ranges[ranges > 0]) if np.any(ranges > 0) else 0

        return {
            'path_length': float(path_length),
            'curvature': float(avg_curvature),
            'tortuosity': float(tortuosity),
            'exploration_volume': float(exploration_volume)
        }

    def dimension_change(self, window_size: int = 20) -> int:
        if len(self.representation_history) < window_size * 2:
            return 0

        hist = list(self.representation_history)
        recent = hist[-window_size:]
        previous = hist[-2*window_size:-window_size]

        recent_var = np.var(recent, axis=0)
        prev_var = np.var(previous, axis=0)

        threshold = np.mean(prev_var) * 0.5
        new_dims = np.sum(recent_var > threshold)
        old_dims = np.sum(prev_var > threshold)

        return int(new_dims - old_dims)


# ---------------------------------------------------------------------------
# 认知僵局 (Cognitive Impasse)
# ---------------------------------------------------------------------------

class CognitiveImpasse:
    """
    认知僵局检测器
    """

    def __init__(self,
                 change_rate_threshold: float = 0.05,
                 min_impasse_duration: int = 10,
                 flow_threshold: float = 0.1):
        self.change_rate_threshold = change_rate_threshold
        self.min_impasse_duration = min_impasse_duration
        self.flow_threshold = flow_threshold
        self.impasse_history: List[ImpasseRecord] = []
        self.current_impasse: Optional[ImpasseRecord] = None
        self._last_detect_time: int = -1

    def measure_stuckness(self, history: List[np.ndarray],
                          flow_history: Optional[List[float]] = None) -> Dict[str, float]:
        if len(history) < 5:
            return {'change_rate': 1.0, 'change_trend': 0, 'flow_rate': 1.0, 'stuckness_score': 0}

        diffs = [np.linalg.norm(history[i] - history[i-1]) for i in range(1, len(history))]
        change_rate = np.mean(diffs[-5:]) if len(diffs) >= 5 else np.mean(diffs)

        if len(diffs) >= 5:
            x = np.arange(len(diffs))
            slope = np.polyfit(x, diffs, 1)[0]
            change_trend = slope / (np.mean(diffs) + 1e-8)
        else:
            change_trend = 0

        if flow_history and len(flow_history) > 0:
            flow_rate = np.mean(flow_history[-5:])
        else:
            recent = np.array(history[-10:])
            flow_rate = float(np.mean(np.std(recent, axis=0)))

        # 卡住度计算：基于绝对阈值
        # 僵局的核心特征：变化率极低 + 流量极低
        
        # 绝对阈值（基于OMNI-HUB系统特性校准）
        ABS_CHANGE_THRESHOLD = 0.002  # 绝对变化率阈值
        ABS_FLOW_THRESHOLD = 0.001    # 绝对流量阈值
        
        # 变化率评估
        is_low_change = change_rate < ABS_CHANGE_THRESHOLD
        change_severity = max(0, 1 - change_rate / ABS_CHANGE_THRESHOLD)
        
        # 流量评估
        is_low_flow = flow_rate < ABS_FLOW_THRESHOLD
        flow_severity = max(0, 1 - flow_rate / ABS_FLOW_THRESHOLD)
        
        # 趋势评估（下降趋势加剧卡住）
        trend_severity = max(0, min(1, -change_trend / 0.1))
        
        # 综合卡住分数（加权组合）
        stuckness_score = (
            change_severity * 0.45 +
            flow_severity * 0.35 +
            trend_severity * 0.20
        )
        
        stuckness_score = min(1.0, max(0.0, stuckness_score))

        return {
            'change_rate': float(change_rate),
            'change_trend': float(change_trend),
            'flow_rate': float(flow_rate),
            'stuckness_score': float(stuckness_score)
        }

    def measure_restructuring(self, history: List[np.ndarray],
                              rep_space: RepresentationSpace) -> Dict[str, float]:
        if len(history) < 10:
            return {'distance_jump': 0, 'dimension_shift': 0, 'novelty_score': 0, 'restructuring_degree': 0}

        recent_states = history[-5:]
        previous_states = history[-15:-5] if len(history) >= 15 else history[:5]

        prev_centroid = np.mean(previous_states, axis=0)
        recent_centroid = np.mean(recent_states, axis=0)

        distance_jump = rep_space.distance(prev_centroid, recent_centroid)
        dimension_shift = rep_space.dimension_change()

        prev_std = np.std(previous_states, axis=0) + 1e-8
        z_scores = np.abs((recent_centroid - prev_centroid) / prev_std)
        novelty_score = float(np.mean(z_scores))

        restructuring_degree = (
            min(distance_jump, 5.0) / 5.0 * 0.5 +
            abs(dimension_shift) / 5.0 * 0.3 +
            min(novelty_score, 10.0) / 10.0 * 0.2
        )

        return {
            'distance_jump': float(distance_jump),
            'dimension_shift': int(dimension_shift),
            'novelty_score': float(novelty_score),
            'restructuring_degree': float(restructuring_degree)
        }

    def detect(self, timestamp: int, stuckness: Dict[str, float],
               restructuring: Dict[str, float]) -> Optional[ImpasseRecord]:
        """检测僵局，返回刚结束的僵局记录（如果有）"""
        # 防止同一时刻重复检测
        if timestamp <= self._last_detect_time:
            return None
        self._last_detect_time = timestamp

        is_impasse = (
            stuckness['stuckness_score'] > 0.7
        )

        if is_impasse:
            if self.current_impasse is None:
                self.current_impasse = ImpasseRecord(
                    start_time=timestamp,
                    end_time=-1,
                    duration=1,
                    intensity=stuckness['stuckness_score'],
                    avg_change_rate=stuckness['change_rate'],
                    lines_affected=[]
                )
            else:
                self.current_impasse.duration = timestamp - self.current_impasse.start_time + 1
                self.current_impasse.intensity = max(
                    self.current_impasse.intensity,
                    stuckness['stuckness_score']
                )
            return None
        else:
            if self.current_impasse is not None:
                if self.current_impasse.duration >= self.min_impasse_duration:
                    self.current_impasse.end_time = timestamp
                    record = self.current_impasse
                    self.impasse_history.append(record)
                    self.current_impasse = None
                    return record
                self.current_impasse = None
            return None

    def get_active_impasse(self) -> Optional[ImpasseRecord]:
        return self.current_impasse

    def has_recent_impasse(self, timestamp: int, window: int = 20) -> Tuple[bool, Optional[ImpasseRecord]]:
        """检查最近窗口内是否有已结束的僵局"""
        for record in reversed(self.impasse_history):
            if timestamp - record.end_time <= window:
                return True, record
        if self.current_impasse is not None:
            return True, self.current_impasse
        return False, None


# ---------------------------------------------------------------------------
# 顿悟检测器 (Insight Detector)
# ---------------------------------------------------------------------------

class InsightDetector:
    """
    OMNI-HUB顿悟检测器

    Insight = Impasse + Restructuring + Performance_Jump
    Strength = Impasse_Duration x Jump_Magnitude x Post_Improvement
    """

    def __init__(self,
                 history_size: int = 200,
                 n_components: int = 8,
                 impasse_threshold: float = 0.05,
                 jump_threshold: float = 0.3,
                 performance_window: int = 15,
                 warmup_steps: int = 100):

        self.history_size = history_size
        self.jump_threshold = jump_threshold
        self.performance_window = performance_window
        self.warmup_steps = warmup_steps

        self.rep_space = RepresentationSpace(n_components=n_components,
                                              history_window=history_size)
        self.impasse_detector = CognitiveImpasse(
            change_rate_threshold=impasse_threshold,
            min_impasse_duration=20,
            flow_threshold=0.1
        )

        self.state_history: deque = deque(maxlen=history_size)
        self.time_history: deque = deque(maxlen=history_size)
        self.performance_history: deque = deque(maxlen=history_size)
        self.flow_history: deque = deque(maxlen=history_size)

        self.insight_events: List[InsightEvent] = []
        self.current_time: int = 0

        # 僵局跟踪状态
        self.in_impasse: bool = False
        self.impasse_start: int = -1
        self.impasse_duration: int = 0

        # 缓存上一次的检测结果，避免重复计算
        self._last_impasse_result: Optional[Dict] = None
        self._last_restruct_result: Optional[Dict] = None

    def track_state_history(self, state: np.ndarray,
                           performance: float = 0.0,
                           flow: float = 0.0) -> None:
        state = np.asarray(state).flatten()
        self.state_history.append(state)
        self.time_history.append(self.current_time)
        self.performance_history.append(performance)
        self.flow_history.append(flow)
        self.rep_space.encode(state)
        self.current_time += 1

    def detect_impasse(self) -> Dict[str, Any]:
        if len(self.state_history) < 10:
            return {'is_impasse': False, 'stuckness': {}, 'impasse_record': None}

        stuckness = self.impasse_detector.measure_stuckness(
            list(self.state_history),
            list(self.flow_history)
        )
        restructuring = self.impasse_detector.measure_restructuring(
            list(self.state_history),
            self.rep_space
        )

        impasse_record = self.impasse_detector.detect(
            self.current_time, stuckness, restructuring
        )

        is_impasse = stuckness['stuckness_score'] > 0.6

        if is_impasse and not self.in_impasse:
            self.in_impasse = True
            self.impasse_start = self.current_time
            self.impasse_duration = 1
        elif is_impasse and self.in_impasse:
            self.impasse_duration = self.current_time - self.impasse_start + 1
        elif not is_impasse and self.in_impasse:
            self.in_impasse = False

        self._last_impasse_result = {
            'is_impasse': is_impasse,
            'stuckness': stuckness,
            'impasse_record': impasse_record,
            'impasse_duration': self.impasse_duration if is_impasse else 0
        }
        return self._last_impasse_result

    def detect_restructuring(self) -> Dict[str, Any]:
        if len(self.state_history) < 20:
            return {'is_restructuring': False, 'metrics': {}}

        metrics = self.impasse_detector.measure_restructuring(
            list(self.state_history),
            self.rep_space
        )

        is_restructuring = (
            metrics['distance_jump'] > self.jump_threshold or
            abs(metrics['dimension_shift']) >= 2 or
            metrics['restructuring_degree'] > 0.5
        )

        self._last_restruct_result = {
            'is_restructuring': is_restructuring,
            'metrics': metrics
        }
        return self._last_restruct_result

    def detect_insight(self) -> Optional[InsightEvent]:
        if len(self.state_history) < 25 or self.current_time < self.warmup_steps:
            return None

        # 使用缓存或重新检测
        impasse_info = self._last_impasse_result or self.detect_impasse()
        restructuring_info = self._last_restruct_result or self.detect_restructuring()

        # 检查最近是否有僵局（已结束的）
        has_recent, recent_impasse = self.impasse_detector.has_recent_impasse(
            self.current_time, window=30
        )

        # 检查当前是否刚从僵局恢复
        just_recovered = False
        impasse_duration = 0
        impasse_start = -1

        if has_recent and recent_impasse is not None:
            if recent_impasse.end_time > 0:
                # 僵局已结束
                just_recovered = (self.current_time - recent_impasse.end_time) <= 15
                impasse_duration = recent_impasse.duration
                impasse_start = recent_impasse.start_time
            else:
                # 当前仍在僵局中
                pass

        # 顿悟条件：刚从僵局恢复 + 表征重组
        if not just_recovered:
            return None

        is_restructuring = restructuring_info['is_restructuring']
        metrics = restructuring_info['metrics']

        if not is_restructuring:
            return None

        # 性能对比
        if len(self.performance_history) < self.performance_window * 2:
            return None

        perf_list = list(self.performance_history)
        pre_perf = np.mean(perf_list[-self.performance_window*2:-self.performance_window])
        post_perf = np.mean(perf_list[-self.performance_window:])

        # 计算Phi值突增
        phi_surge = self._calculate_phi_surge()

        # 创建顿悟事件
        event = InsightEvent(
            timestamp=self.current_time,
            impasse_start=impasse_start,
            impasse_duration=impasse_duration,
            jump_magnitude=metrics['distance_jump'],
            post_performance=post_perf,
            pre_performance=pre_perf,
            phi_surge=phi_surge,
            dimension_change=metrics['dimension_shift'],
            lines_involved=[]
        )

        event.strength = self.insight_strength(event)
        event.restructuring_degree = metrics['restructuring_degree']

        # 防止重复检测
        if self.insight_events:
            last_event = self.insight_events[-1]
            if self.current_time - last_event.timestamp < 20:
                return None

        self.insight_events.append(event)
        return event

    def _calculate_phi_surge(self) -> float:
        if len(self.state_history) < 20:
            return 0.0

        recent = np.array(list(self.state_history)[-10:])
        previous = np.array(list(self.state_history)[-20:-10])

        recent_cov = np.cov(recent.T)
        prev_cov = np.cov(previous.T)

        recent_det = np.linalg.det(recent_cov + np.eye(recent_cov.shape[0]) * 1e-6)
        prev_det = np.linalg.det(prev_cov + np.eye(prev_cov.shape[0]) * 1e-6)

        phi = float(np.log(max(recent_det, 1e-10) / max(prev_det, 1e-10)))
        return phi

    def insight_strength(self, event: InsightEvent) -> float:
        norm_duration = min(event.impasse_duration / 50.0, 1.0)
        norm_jump = min(event.jump_magnitude / 5.0, 1.0)
        perf_improvement = max(0, event.post_performance - event.pre_performance)
        norm_perf = min(perf_improvement / 2.0, 1.0)

        strength = (norm_duration * norm_jump * (1 + norm_perf)) ** (1/3)
        return float(min(strength, 1.0))

    def aha_frequency(self, window_size: int = 100) -> float:
        if not self.insight_events:
            return 0.0

        recent_events = [
            e for e in self.insight_events
            if self.current_time - e.timestamp <= window_size
        ]

        return round(len(recent_events) / window_size, 4)

    def get_insight_summary(self) -> Dict[str, Any]:
        if not self.insight_events:
            return {
                'total_insights': 0,
                'avg_strength': 0.0,
                'max_strength': 0.0,
                'avg_duration': 0.0,
                'avg_jump': 0.0,
                'frequency': 0.0,
                'events': []
            }

        strengths = [e.strength for e in self.insight_events]
        durations = [e.impasse_duration for e in self.insight_events]
        jumps = [e.jump_magnitude for e in self.insight_events]

        return {
            'total_insights': len(self.insight_events),
            'avg_strength': round(float(np.mean(strengths)), 4),
            'max_strength': round(float(np.max(strengths)), 4),
            'avg_duration': round(float(np.mean(durations)), 2),
            'avg_jump': round(float(np.mean(jumps)), 4),
            'frequency': round(self.aha_frequency(1000), 4),
            'events': [e.to_dict() for e in self.insight_events]
        }


# ---------------------------------------------------------------------------
# OMNI-HUB 11线模拟系统
# ---------------------------------------------------------------------------

class OMNIHUBSimulator:
    """
    OMNI-HUB 11线分布式系统模拟器
    
    设计用于模拟认知僵局和顿悟突破：
    - 僵局期：系统变化极小，低复杂度
    - 突破期：状态大幅跃迁，复杂度提升
    """

    def __init__(self, n_lines: int = 11, state_dim: int = 16, seed: int = 42):
        np.random.seed(seed)
        self.n_lines = n_lines
        self.state_dim = state_dim
        self.total_dim = n_lines * state_dim

        self.states = np.random.randn(n_lines, state_dim) * 0.3

        # 引擎参数
        self.self_excitation = np.ones(n_lines) * 0.6
        self.mutual_coupling = np.random.randn(n_lines, n_lines) * 0.15
        np.fill_diagonal(self.mutual_coupling, 0)
        self.field_strength = 0.4
        self.transient_pulse = 0.0
        
        # 僵局控制
        self._frozen_lines: set = set()
        self._damping_factor: float = 1.0  # 1.0=正常, <1=僵局
        self._in_impasse: bool = False

        self.complexity = 0.0
        self.entropy = 0.0
        self.integration = 0.0
        self.performance = 0.0
        self.time = 0

        self.state_history = []
        self.complexity_history = []
        self.performance_history = []

    def _update_self_excitation(self) -> np.ndarray:
        noise = np.random.randn(self.n_lines, self.state_dim) * 0.03
        self_exc = np.zeros_like(self.states)
        for i in range(self.n_lines):
            self_exc[i] = np.tanh(self.states[i] * self.self_excitation[i]) + noise[i]
        return self_exc

    def _update_mutual_excitation(self) -> np.ndarray:
        mutual = np.zeros_like(self.states)
        for i in range(self.n_lines):
            for j in range(self.n_lines):
                if i != j:
                    mutual[i] += self.mutual_coupling[i, j] * self.states[j] * 0.15
        return np.tanh(mutual)

    def _update_field_excitation(self) -> np.ndarray:
        field = np.mean(self.states, axis=0)
        field_effect = np.ones((self.n_lines, 1)) * field * self.field_strength
        return np.tanh(field_effect)

    def _update_transient(self) -> np.ndarray:
        if self.transient_pulse > 0:
            pulse = np.random.randn(self.n_lines, self.state_dim) * self.transient_pulse
            self.transient_pulse *= 0.7
            return pulse
        return np.zeros_like(self.states)

    def _update_ripple(self) -> np.ndarray:
        activation = np.linalg.norm(self.states, axis=1)
        strongest = np.argmax(activation)
        ripple = np.zeros_like(self.states)
        for i in range(max(0, strongest-1), min(self.n_lines, strongest+2)):
            if i != strongest:
                ripple[i] = self.states[strongest] * 0.15 * activation[strongest]
        return np.tanh(ripple)

    def step(self) -> np.ndarray:
        # 计算各引擎贡献
        self_exc = self._update_self_excitation()
        mutual = self._update_mutual_excitation()
        field = self._update_field_excitation()
        transient = self._update_transient()
        ripple = self._update_ripple()

        # 综合更新（带僵局阻尼）
        delta = (
            self_exc * 0.3 +
            mutual * 0.25 +
            field * 0.25 +
            transient * 0.1 +
            ripple * 0.1
        ) * self._damping_factor

        # 更新状态
        if self._in_impasse:
            # 僵局期：强衰减，极小变化
            self.states = 0.97 * self.states + 0.03 * delta
        else:
            self.states = 0.92 * self.states + 0.08 * delta

        self._compute_metrics()
        self.time += 1

        self.state_history.append(self.states.copy())
        self.complexity_history.append(self.complexity)
        self.performance_history.append(self.performance)

        return self.states.flatten()

    def _compute_metrics(self) -> None:
        flat_state = self.states.flatten()
        hist, _ = np.histogram(flat_state, bins=20, density=True)
        hist = hist[hist > 0]
        self.entropy = float(entropy(hist))

        corr_matrix = np.corrcoef(self.states)
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        self.integration = float(np.mean(np.abs(corr_matrix[mask])))

        self.complexity = self.entropy * self.integration

        activity = np.mean(np.abs(self.states))
        self.performance = self.complexity * activity * 2.5

    def inject_impasse(self, target_lines: Optional[List[int]] = None,
                       strength: float = 0.9) -> None:
        """注入僵局：冻结系统动态"""
        if target_lines is None:
            target_lines = list(range(self.n_lines))

        self._in_impasse = True
        self._damping_factor = 0.02  # 大幅抑制更新

        for line in target_lines:
            self._frozen_lines.add(line)
            self.self_excitation[line] *= 0.05
            self.mutual_coupling[line, :] *= 0.005
            self.states[line] *= 0.15

        self.field_strength *= 0.1

    def inject_breakthrough(self, target_lines: Optional[List[int]] = None,
                           field_boost: float = 3.0,
                           transient_boost: float = 2.0) -> None:
        """注入突破：打破僵局，产生状态跃迁"""
        self._in_impasse = False
        self._damping_factor = 2.0  # 暂时增强更新
        self._frozen_lines.clear()

        # 恢复自激
        self.self_excitation[:] = np.clip(self.self_excitation * 5, 0.4, 1.0)
        
        # 增强场激
        self.field_strength = 0.5 * field_boost
        
        # 强瞬激脉冲
        self.transient_pulse = transient_boost
        
        # 重新随机化互激耦合
        self.mutual_coupling = np.random.randn(self.n_lines, self.n_lines) * 0.25
        np.fill_diagonal(self.mutual_coupling, 0)
        
        # 强状态扰动（产生大距离跃迁）
        if target_lines:
            for line in target_lines:
                self.states[line] = np.random.randn(self.state_dim) * 2.0
        else:
            self.states = np.random.randn(self.n_lines, self.state_dim) * 1.5

    def get_full_state(self) -> np.ndarray:
        return self.states.flatten()

    def get_metrics(self) -> Dict[str, float]:
        return {
            'complexity': round(self.complexity, 4),
            'entropy': round(self.entropy, 4),
            'integration': round(self.integration, 4),
            'performance': round(self.performance, 4),
            'activity': round(float(np.mean(np.abs(self.states))), 4),
            'self_excitation': round(float(np.mean(self.self_excitation)), 4),
            'field_strength': round(self.field_strength, 4),
            'damping': round(self._damping_factor, 4)
        }


# ---------------------------------------------------------------------------
# 实验验证
# ---------------------------------------------------------------------------

def run_insight_experiment(n_steps: int = 1000,
                           n_lines: int = 11,
                           state_dim: int = 16,
                           seed: int = 42,
                           verbose: bool = True) -> Dict[str, Any]:
    """
    运行顿悟检测实验

    实验阶段:
    1. 正常演化 0-200步 (基线)
    2. 注入僵局 200-400步 (降低自激率)
    3. 注入突破 400步 (增强场激) -> 预期顿悟
    4. 正常演化 400-650步
    5. 第二次僵局 650-850步
    6. 第二次突破 850步 -> 预期顿悟
    7. 最终演化 850-1000步
    """

    sim = OMNIHUBSimulator(n_lines=n_lines, state_dim=state_dim, seed=seed)
    detector = InsightDetector(
        history_size=200,
        n_components=8,
        impasse_threshold=0.05,
        jump_threshold=0.2,
        performance_window=15
    )

    experiment_log = {
        'steps': [],
        'states': [],
        'metrics': [],
        'impasse_states': [],
        'restructuring_states': [],
        'insight_events': [],
        'complexity_trajectory': [],
        'performance_trajectory': [],
        'stuckness_trajectory': [],
        'distance_jumps': [],
        'phase_markers': []
    }

    if verbose:
        logger.info("=" * 70)
        logger.info("OMNI-HUB v4.1 InsightDetector 实验验证")
        logger.info("=" * 70)
        logger.info(f"\n实验配置:")
        logger.info(f"  总步数: {n_steps}")
        logger.info(f"  线数: {n_lines}")
        logger.info(f"  状态维度: {state_dim}")
        logger.info(f"  总维度: {n_lines * state_dim}")
        logger.info(f"\n实验阶段:")
        logger.info(f"  0-200:    正常演化 (基线)")
        logger.info(f"  200-400:  注入僵局 (降低自激率85%)")
        logger.info(f"  400:      注入突破 (场激增强3x) -> 预期顿悟")
        logger.info(f"  400-650:  恢复演化")
        logger.info(f"  650-850:  第二次僵局")
        logger.info(f"  850:      第二次突破 -> 预期顿悟")
        logger.info(f"  850-1000: 最终演化")
        logger.info("=" * 70)

    for step in range(n_steps):
        phase = ""

        # 阶段控制
        if step == 200:
            sim.inject_impasse(strength=0.85)
            phase = "IMPASSE_1"
            if verbose:
                logger.info(f"\n[步 {step}] >>> 僵局注入: 自激率降低85%")

        elif step == 400:
            sim.inject_breakthrough(field_boost=3.0, transient_boost=1.5)
            phase = "BREAKTHROUGH_1"
            if verbose:
                logger.info(f"[步 {step}] >>> 突破注入: 场激增强3x, 瞬激脉冲")

        elif step == 650:
            sim.inject_impasse(strength=0.75)
            phase = "IMPASSE_2"
            if verbose:
                logger.info(f"\n[步 {step}] >>> 第二次僵局注入")

        elif step == 850:
            sim.inject_breakthrough(field_boost=2.5, transient_boost=1.0)
            phase = "BREAKTHROUGH_2"
            if verbose:
                logger.info(f"[步 {step}] >>> 第二次突破注入")

        # 系统演化
        state = sim.step()
        metrics = sim.get_metrics()

        # 追踪到检测器
        detector.track_state_history(
            state=state,
            performance=metrics['performance'],
            flow=metrics['activity']
        )

        # 检测（先检测僵局，再检测顿悟）
        impasse_info = detector.detect_impasse()
        restructuring_info = detector.detect_restructuring()
        insight = detector.detect_insight()

        # 记录距离跳跃
        distance_jump = restructuring_info['metrics'].get('distance_jump', 0)

        experiment_log['steps'].append(step)
        experiment_log['states'].append(state.copy())
        experiment_log['metrics'].append(metrics)
        experiment_log['complexity_trajectory'].append(metrics['complexity'])
        experiment_log['performance_trajectory'].append(metrics['performance'])
        experiment_log['stuckness_trajectory'].append(
            impasse_info['stuckness'].get('stuckness_score', 0)
        )
        experiment_log['distance_jumps'].append(distance_jump)

        if impasse_info['is_impasse']:
            experiment_log['impasse_states'].append(step)

        if restructuring_info['is_restructuring']:
            experiment_log['restructuring_states'].append(step)

        if insight:
            experiment_log['insight_events'].append(insight.to_dict())
            if verbose:
                logger.info(f"\n{'='*55}")
                logger.info(f"  顿悟事件检测到!  [步 {step}]  #{len(experiment_log['insight_events'])}")
                logger.info(f"  {'='*55}")
                logger.info(f"  僵局持续时间: {insight.impasse_duration} 步")
                logger.info(f"  跃迁幅度:     {insight.jump_magnitude:.4f}")
                logger.info(f"  顿悟强度:     {insight.strength:.4f}")
                logger.info(f"  性能提升:     {insight.post_performance - insight.pre_performance:+.4f}")
                logger.info(f"  维度变化:     {insight.dimension_change:+d}")
                logger.info(f"  Phi值突增:    {insight.phi_surge:+.6f}")
                logger.info(f"{'='*55}")

        if phase:
            experiment_log['phase_markers'].append({'step': step, 'phase': phase})

    # 实验总结
    summary = detector.get_insight_summary()

    if verbose:
        logger.info("\n" + "=" * 70)
        logger.info("实验结果摘要")
        logger.info("=" * 70)
        logger.info(f"\n顿悟统计:")
        logger.info(f"  总顿悟次数:       {summary['total_insights']}")
        logger.info(f"  平均顿悟强度:     {summary['avg_strength']:.4f}")
        logger.info(f"  最大顿悟强度:     {summary['max_strength']:.4f}")
        logger.info(f"  平均僵局持续时间: {summary['avg_duration']:.2f} 步")
        logger.info(f"  平均跃迁幅度:     {summary['avg_jump']:.4f}")
        logger.info(f"  顿悟频率:         {summary['frequency']:.4f} /步")

        complexity_data = experiment_log['complexity_trajectory']
        pre_insight = np.mean(complexity_data[:200])
        post_insight1 = np.mean(complexity_data[450:650])
        post_insight2 = np.mean(complexity_data[900:1000])

        logger.info(f"\n复杂度变化:")
        logger.info(f"  基线 (0-200步):       {pre_insight:.4f}")
        logger.info(f"  第一次顿悟后(450-650):  {post_insight1:.4f}")
        logger.info(f"  第二次顿悟后(900-1000): {post_insight2:.4f}")
        if pre_insight > 0:
            logger.info(f"  总提升比例:           {((post_insight2 - pre_insight) / pre_insight * 100):+.1f}%")

        logger.info(f"\n僵局记录:")
        logger.info(f"  检测到的僵局数: {len(detector.impasse_detector.impasse_history)}")
        for i, imp in enumerate(detector.impasse_detector.impasse_history):
            print(f"    僵局{i+1}: 步{imp.start_time}-{imp.end_time}, "
                  f"持续{imp.duration}步, 强度{imp.intensity:.4f}")

        logger.info("\n" + "=" * 70)

    return {
        'summary': summary,
        'experiment_log': experiment_log,
        'detector': detector,
        'simulator': sim
    }


# ---------------------------------------------------------------------------
# 可视化
# ---------------------------------------------------------------------------

def generate_experiment_plots(result: Dict[str, Any],
                               output_dir: str = "/mnt/agents/output/OMNI-HUB/core") -> str:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
    log = result['experiment_log']
    steps = log['steps']

    fig, axes = plt.subplots(4, 1, figsize=(14, 12))

    # 图1: 复杂度和性能轨迹
    ax1 = axes[0]
    ax1.plot(steps, log['complexity_trajectory'], 'b-', label='Complexity', linewidth=1.2)
    ax1_twin = ax1.twinx()
    ax1_twin.plot(steps, log['performance_trajectory'], 'r--', label='Performance', linewidth=1, alpha=0.7)

    for marker in log['phase_markers']:
        ax1.axvline(x=marker['step'], color='gray', linestyle=':', alpha=0.4)

    for event in log['insight_events']:
        ax1.axvline(x=event['timestamp'], color='gold', linewidth=2.5, alpha=0.9)
        ax1.scatter([event['timestamp']], [max(log['complexity_trajectory'])*0.95],
                   color='gold', s=150, marker='*', zorder=5, edgecolors='darkorange', linewidths=1.5)

    ax1.set_ylabel('Complexity', color='b')
    ax1_twin.set_ylabel('Performance', color='r')
    ax1.set_title('OMNI-HUB v4.1: Complexity & Performance Trajectory (★ = Insight)', 
                  fontsize=12, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)

    # 图2: 卡住度轨迹
    ax2 = axes[1]
    ax2.fill_between(steps, log['stuckness_trajectory'], alpha=0.3, color='green')
    ax2.plot(steps, log['stuckness_trajectory'], 'g-', label='Stuckness Score', linewidth=1)
    ax2.axhline(y=0.6, color='r', linestyle='--', alpha=0.5, label='Impasse Threshold')

    for marker in log['phase_markers']:
        if 'IMPASSE' in marker['phase']:
            ax2.axvline(x=marker['step'], color='purple', linestyle=':', alpha=0.4)

    for event in log['insight_events']:
        ax2.axvline(x=event['timestamp'], color='gold', linewidth=2.5, alpha=0.9)

    ax2.set_ylabel('Stuckness Score')
    ax2.set_title('Cognitive Impasse Detection', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 图3: 表征距离跳跃
    ax3 = axes[2]
    ax3.plot(steps, log['distance_jumps'], 'm-', linewidth=0.8, alpha=0.8)
    ax3.axhline(y=0.2, color='orange', linestyle='--', alpha=0.5, label='Restructuring Threshold')

    for event in log['insight_events']:
        ax3.axvline(x=event['timestamp'], color='gold', linewidth=2.5, alpha=0.9)
        ax3.scatter([event['timestamp']], [event['jump_magnitude']],
                   color='gold', s=100, marker='*', zorder=5)

    ax3.set_ylabel('Representation Distance Jump')
    ax3.set_title('State Transition Distance (Representation Jump)', fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 图4: 顿悟强度
    ax4 = axes[3]
    if log['insight_events']:
        event_times = [e['timestamp'] for e in log['insight_events']]
        event_strengths = [e['strength'] for e in log['insight_events']]
        colors = plt.cm.plasma(np.array(event_strengths) / max(event_strengths))
        bars = ax4.bar(event_times, event_strengths, color=colors, width=12, alpha=0.85, edgecolor='black')
        ax4.set_ylabel('Insight Strength')
        ax4.set_xlabel('Time Step')
        ax4.set_title('Detected Insight Events (Strength Distribution)', fontsize=12, fontweight='bold')

        for i, (t, s) in enumerate(zip(event_times, event_strengths)):
            ax4.text(t, s + 0.01, f'#{i+1}\n{s:.3f}', ha='center', fontsize=9, fontweight='bold')
    else:
        ax4.text(0.5, 0.5, 'No Insight Events Detected', ha='center', va='center',
                transform=ax4.transAxes, fontsize=14)

    ax4.set_ylim(0, max(event_strengths) * 1.3 if event_strengths else 1)
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = f"{output_dir}/insight_experiment_results.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()

    return plot_path


def generate_representation_plot(result: Dict[str, Any],
                                  output_dir: str = "/mnt/agents/output/OMNI-HUB/core") -> str:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from sklearn.decomposition import PCA
# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------
"""
OMNI-HUB v11.0 — insight_detector
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""

if __name__ == "__main__":
    result = run_insight_experiment(n_steps=1000, verbose=True)

    print("\n正在生成可视化图表...")
    plot1 = generate_experiment_plots(result)
    plot2 = generate_representation_plot(result)
    print(f"图表已保存: {plot1}")
    print(f"图表已保存: {plot2}")

    output_path = "/mnt/agents/output/OMNI-HUB/core/insight_experiment_results.json"
    with open(output_path, 'w') as f:
        serializable = {
            'summary': result['summary'],
            'phase_markers': result['experiment_log']['phase_markers'],
            'insight_events': result['experiment_log']['insight_events'],
            'complexity_trajectory': [float(x) for x in result['experiment_log']['complexity_trajectory']],
            'performance_trajectory': [float(x) for x in result['experiment_log']['performance_trajectory']],
            'stuckness_trajectory': [float(x) for x in result['experiment_log']['stuckness_trajectory']],
            'distance_jumps': [float(x) for x in result['experiment_log']['distance_jumps']]
        }
        json.dump(serializable, f, indent=2)

    print(f"\n实验结果已保存: {output_path}")
    print("\nOMNI-HUB v4.1 InsightDetector 实验完成!")
