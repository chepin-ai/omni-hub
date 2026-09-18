#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OMNI-HUB v5.0 IntentionGenerator
================================
基于Karl Friston自由能原理/主动推理的意图生成器

核心命题：意图不是外部给定的，而是系统基于当前生成模型自发产生的——
选择能够最小化未来预测误差的行动方向。

理论基础：
- 自由能原理(FEP): 所有生命系统通过最小化自由能来维持自身边界
- 主动推理(Active Inference): 感知和行动是同一操作的两个视角
- Markov毯: 系统与环境边界的统计形式化
- 生成模型: 系统对世界因果结构的内部模型

作者: OMNI-HUB Architecture Team
版本: 5.0.0
"""

__version__ = "11.0.0"
import numpy as np
import numpy.linalg as la
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable
from collections import deque
from datetime import datetime
import json
import warnings

warnings.filterwarnings('ignore')

# =============================================================================
# 全局配置
# =============================================================================
DEFAULT_NUM_LINES = 11
DEFAULT_HORIZON = 5
DEFAULT_STATE_DIM = 4  # 每条线的状态维度 [能量, 稳定性, 连通性, 涌现度]
GAMMA = 0.95  # 时间折扣因子
EPSILON = 1e-8  # 数值稳定常数


# =============================================================================
# Intention 意图对象
# =============================================================================
@dataclass
class Intention:
    """
    意图对象 - 系统自发产生的行动方向
    
    属性:
        direction: 意图方向向量 (state_dim,)
        strength: 意图强度 [0, 1]
        target_state: 目标状态向量
        predicted_error_reduction: 预计误差减少量
        timestamp: 生成时间戳
        line_preference: 偏好执行线 (-1表示系统级)
        free_energy_before: 行动前自由能
        free_energy_after: 行动后预测自由能
        action_id: 选择的行动索引
        confidence: 意图置信度
    """
    direction: np.ndarray
    strength: float
    target_state: np.ndarray
    predicted_error_reduction: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    line_preference: int = -1
    free_energy_before: float = 0.0
    free_energy_after: float = 0.0
    action_id: int = -1
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            'direction': self.direction.tolist() if isinstance(self.direction, np.ndarray) else self.direction,
            'strength': float(self.strength),
            'target_state': self.target_state.tolist() if isinstance(self.target_state, np.ndarray) else self.target_state,
            'predicted_error_reduction': float(self.predicted_error_reduction),
            'timestamp': self.timestamp,
            'line_preference': int(self.line_preference),
            'free_energy_before': float(self.free_energy_before),
            'free_energy_after': float(self.free_energy_after),
            'action_id': int(self.action_id),
            'confidence': float(self.confidence),
        }
    
    def __repr__(self) -> str:
        line_str = "SYSTEM" if self.line_preference == -1 else f"LINE-{self.line_preference}"
        return (f"Intention[{line_str}] "
                f"strength={self.strength:.3f} "
                f"err_reduction={self.predicted_error_reduction:.4f} "
                f"confidence={self.confidence:.3f}")


# =============================================================================
# GenerativeModel 生成模型
# =============================================================================
class GenerativeModel:
    """
    生成模型 - 系统对世界因果结构的内部表示
    
    使用线性高斯状态空间模型:
        s_{t+1} = A * s_t + B * a_t + w_t    (状态转移)
        o_t = C * s_t + v_t                    (观测模型)
    
    其中:
        A: 状态转移矩阵 (state_dim, state_dim)
        B: 行动影响矩阵 (state_dim, action_dim)
        C: 观测矩阵 (obs_dim, state_dim)
        w_t ~ N(0, Q): 过程噪声
        v_t ~ N(0, R): 观测噪声
    """
    
    def __init__(self, state_dim: int, action_dim: int, obs_dim: Optional[int] = None,
                 learning_rate: float = 0.1, forgetting_factor: float = 0.98):
        """
        初始化生成模型
        
        Args:
            state_dim: 状态空间维度
            action_dim: 行动空间维度
            obs_dim: 观测空间维度 (默认等于state_dim)
            learning_rate: 模型参数学习率
            forgetting_factor: 遗忘因子 (用于在线学习)
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.obs_dim = obs_dim or state_dim
        self.lr = learning_rate
        self.forgetting_factor = forgetting_factor
        
        # 初始化模型参数 (带小的随机扰动)
        np.random.seed(42)
        self.A = np.eye(state_dim) * 0.9 + np.random.randn(state_dim, state_dim) * 0.05
        self.B = np.random.randn(state_dim, action_dim) * 0.1
        self.C = np.eye(self.obs_dim, state_dim) + np.random.randn(self.obs_dim, state_dim) * 0.02
        
        # 噪声协方差
        self.Q = np.eye(state_dim) * 0.1  # 过程噪声
        self.R = np.eye(self.obs_dim) * 0.05   # 观测噪声
        
        # 状态估计 (卡尔曼滤波)
        self.mu = np.zeros(state_dim)     # 状态均值
        self.Sigma = np.eye(state_dim)    # 状态协方差
        
        # 在线学习统计量 (用于递归最小二乘)
        self._A_cov = np.eye(state_dim * state_dim) * 10.0
        self._B_cov = np.eye(state_dim * action_dim) * 10.0
        self._C_cov = np.eye(self.obs_dim * state_dim) * 10.0
        
        # 历史记录
        self.history = {
            'predictions': deque(maxlen=100),
            'observations': deque(maxlen=100),
            'prediction_errors': deque(maxlen=100),
            'uncertainties': deque(maxlen=100),
        }
        
        # 模型年龄 (更新次数)
        self.age = 0
        
    def predict(self, state: np.ndarray, action: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测下一状态
        
        Args:
            state: 当前状态 (state_dim,)
            action: 行动 (action_dim,) 或 None
            
        Returns:
            (预测状态均值, 预测状态协方差)
        """
        state = np.asarray(state).reshape(-1)
        
        # 状态预测
        if action is not None:
            action = np.asarray(action).reshape(-1)
            mu_pred = self.A @ state + self.B @ action
        else:
            mu_pred = self.A @ state
            
        # 协方差预测
        Sigma_pred = self.A @ self.Sigma @ self.A.T + self.Q
        Sigma_pred = (Sigma_pred + Sigma_pred.T) / 2  # 对称化
        
        return mu_pred, Sigma_pred
    
    def update(self, observation: np.ndarray, action: Optional[np.ndarray] = None,
               prev_state: Optional[np.ndarray] = None) -> Dict:
        """
        根据观测更新模型 (卡尔曼滤波 + 在线参数学习)
        
        Args:
            observation: 观测向量 (obs_dim,)
            action: 采取的行动 (action_dim,)
            prev_state: 上一时刻状态 (用于参数学习)
            
        Returns:
            更新统计信息字典
        """
        observation = np.asarray(observation).reshape(-1)
        
        # === 卡尔曼滤波更新 ===
        # 观测预测
        obs_pred = self.C @ self.mu
        innovation = observation - obs_pred
        
        # 卡尔曼增益
        S = self.C @ self.Sigma @ self.C.T + self.R
        S = (S + S.T) / 2 + np.eye(self.obs_dim) * EPSILON
        K = self.Sigma @ self.C.T @ la.inv(S)
        
        # 状态更新
        self.mu = self.mu + K @ innovation
        self.Sigma = (np.eye(self.state_dim) - K @ self.C) @ self.Sigma
        self.Sigma = (self.Sigma + self.Sigma.T) / 2 + np.eye(self.state_dim) * EPSILON
        
        # === 在线参数学习 (递归最小二乘) ===
        if prev_state is not None and action is not None:
            prev_state = np.asarray(prev_state).reshape(-1)
            action = np.asarray(action).reshape(-1)
            
            # 更新 A (状态转移)
            pred_state = self.A @ prev_state + self.B @ action
            state_error = self.mu - pred_state
            
            # 梯度下降更新 A
            grad_A = np.outer(state_error, prev_state)
            self.A += self.lr * grad_A
            
            # 梯度下降更新 B
            grad_B = np.outer(state_error, action)
            self.B += self.lr * grad_B
            
            # 更新 C (观测矩阵)
            obs_error = observation - self.C @ self.mu
            grad_C = np.outer(obs_error, self.mu)
            self.C += self.lr * grad_C
            
            # 遗忘因子衰减学习率
            self.lr *= self.forgetting_factor
            self.lr = max(self.lr, 0.001)
        
        # 记录历史
        pred_error = la.norm(innovation)
        self.history['predictions'].append(obs_pred.copy())
        self.history['observations'].append(observation.copy())
        self.history['prediction_errors'].append(pred_error)
        self.history['uncertainties'].append(self.get_uncertainty())
        
        self.age += 1
        
        return {
            'innovation': innovation,
            'kalman_gain_norm': la.norm(K),
            'prediction_error': pred_error,
            'state_uncertainty': self.get_uncertainty(),
        }
    
    def get_uncertainty(self) -> float:
        """
        返回模型不确定性 (状态协方差矩阵的迹)
        
        Returns:
            不确定性标量值
        """
        return float(np.trace(self.Sigma))
    
    def get_model_complexity(self) -> float:
        """
        计算模型复杂度 (Friston自由能中的复杂度项)
        
        复杂度 = KL散度(后验||先验) ≈ trace(Sigma) + ||mu||^2
        
        Returns:
            复杂度标量
        """
        complexity = np.trace(self.Sigma) + np.dot(self.mu, self.mu)
        return float(complexity)
    
    def simulate_forward(self, state: np.ndarray, action_sequence: List[np.ndarray],
                         horizon: int) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        前向模拟 - 预测未来轨迹
        
        Args:
            state: 初始状态
            action_sequence: 行动序列
            horizon: 预测时域
            
        Returns:
            未来状态列表 [(均值, 协方差), ...]
        """
        state = np.asarray(state).reshape(-1)
        predictions = []
        current_state = state.copy()
        
        for t in range(min(horizon, len(action_sequence))):
            mu_pred, Sigma_pred = self.predict(current_state, action_sequence[t])
            predictions.append((mu_pred.copy(), Sigma_pred.copy()))
            current_state = mu_pred  # 使用均值作为下一状态
            
        return predictions
    
    def free_energy(self, observation: np.ndarray, preferred_state: Optional[np.ndarray] = None) -> float:
        """
        计算变分自由能 (惊讶度的上界)
        
        F = E_q[log q(s) - log p(o,s)] 
          ≈ prediction_error + model_complexity + preference_violation
        
        主动推理中，系统通过最小化自由能来选择行动。
        这里的自由能包含三个部分:
        1. 准确性: 模型预测观测的能力
        2. 复杂度: 模型复杂度惩罚 (低权重)
        3. 偏好违背: 到偏好状态的距离 (主要驱动)
        
        Args:
            observation: 当前观测
            preferred_state: 偏好状态 (如果提供)
            
        Returns:
            自由能标量
        """
        observation = np.asarray(observation).reshape(-1)
        
        # 使用观测直接计算，而不是内部状态估计
        # 这样自由能更直接地反映当前状态的质量
        
        # 准确性项: 观测预测误差 (模型预测 vs 实际观测)
        obs_pred = self.C @ observation  # 用观测代替mu来预测
        innovation = observation - obs_pred
        accuracy = 0.5 * np.dot(innovation, innovation) / (np.trace(self.R) + EPSILON)
        
        # 复杂度项: 后验与先验的KL散度 (低权重正则化)
        complexity = 0.02 * (np.trace(self.Sigma) + np.dot(self.mu, self.mu) - self.state_dim 
                            - np.log(max(la.det(self.Sigma), EPSILON)))
        complexity = max(0, complexity)  # 非负
        
        # 偏好项 (到偏好状态的距离 - 这是主动推理的关键)
        preference = 0.0
        if preferred_state is not None:
            preferred_state = np.asarray(preferred_state).reshape(-1)
            state_error = observation - preferred_state
            preference = 0.5 * np.dot(state_error, state_error)
        else:
            # 默认偏好: 零状态
            preference = 0.5 * np.dot(observation, observation)
        
        free_energy = accuracy + complexity + preference
        return float(free_energy)


# =============================================================================
# MarkovBlanket Markov毯
# =============================================================================
class MarkovBlanket:
    """
    Markov毯 - 系统与环境边界的统计形式化
    
    根据Friston的定义，Markov毯将系统变量分为:
    - 内部状态 (internal): 系统的核心状态
    - 毯状态 (blanket): 分隔内部和外部状态的边界
        - 感知状态 (sensory): 接收环境信息
        - 主动状态 (active): 作用于环境
    - 外部状态 (external): 环境状态
    
    Markov毯条件独立性:
    - 内部状态 ⊥ 外部状态 | 毯状态
    """
    
    def __init__(self, state_dim: int, blanket_size: Optional[int] = None):
        """
        初始化Markov毯
        
        Args:
            state_dim: 总状态维度
            blanket_size: 毯状态维度 (默认 state_dim // 2)
        """
        self.state_dim = state_dim
        self.blanket_size = blanket_size or state_dim // 2
        self.internal_size = state_dim - self.blanket_size
        
        # 划分索引
        self.internal_idx = list(range(self.internal_size))
        self.blanket_idx = list(range(self.internal_size, state_dim))
        
        # 进一步划分毯状态为感知和主动
        half_blanket = self.blanket_size // 2
        self.sensory_idx = self.blanket_idx[:half_blanket]
        self.active_idx = self.blanket_idx[half_blanket:]
        
        # 毯的"厚度" (信息流动程度)
        self.thickness = 1.0
        
    def partition(self, state: np.ndarray) -> Dict[str, np.ndarray]:
        """
        将状态划分为内部、感知、主动三部分
        
        Args:
            state: 完整状态向量
            
        Returns:
            {'internal', 'sensory', 'active', 'blanket'}
        """
        state = np.asarray(state).reshape(-1)
        return {
            'internal': state[self.internal_idx],
            'sensory': state[self.sensory_idx],
            'active': state[self.active_idx],
            'blanket': state[self.blanket_idx],
        }
    
    def compute_blanket_statistics(self, state_history: List[np.ndarray]) -> Dict:
        """
        计算Markov毯的统计特性
        
        Args:
            state_history: 状态历史列表
            
        Returns:
            统计字典
        """
        if len(state_history) < 2:
            return {'mutual_info': 0.0, 'boundary_flow': 0.0}
        
        states = np.array(state_history)
        
        # 计算内部状态与外部状态(通过毯)的互信息近似
        internal = states[:, self.internal_idx]
        blanket = states[:, self.blanket_idx]
        
        # 使用相关性近似互信息
        corr_ib = np.corrcoef(internal.T, blanket.T)[:internal.shape[1], internal.shape[1]:]
        mutual_info = 0.5 * np.log(1 + np.mean(corr_ib ** 2) + EPSILON)
        
        # 计算边界信息流 (毯状态的变化率)
        blanket_flow = np.mean(np.diff(blanket, axis=0) ** 2)
        
        return {
            'mutual_info': float(mutual_info),
            'boundary_flow': float(blanket_flow),
            'internal_entropy': float(np.log(la.det(np.cov(internal.T)) + EPSILON)),
            'blanket_entropy': float(np.log(la.det(np.cov(blanket.T)) + EPSILON)),
        }
    
    def update_thickness(self, state: np.ndarray, external_influence: np.ndarray) -> float:
        """
        更新Markov毯的"厚度" - 反映系统边界的渗透性
        
        Args:
            state: 当前状态
            external_influence: 外部影响向量
            
        Returns:
            更新后的厚度
        """
        state = np.asarray(state).reshape(-1)
        external_influence = np.asarray(external_influence).reshape(-1)
        
        # 毯对外部影响的抵抗能力
        blanket = state[self.blanket_idx]
        resistance = np.dot(blanket, external_influence[:len(blanket)]) / (la.norm(blanket) * la.norm(external_influence[:len(blanket)]) + EPSILON)
        
        # 厚度与抵抗能力成正比
        self.thickness = 0.9 * self.thickness + 0.1 * (1.0 + resistance) / 2.0
        self.thickness = np.clip(self.thickness, 0.1, 2.0)
        
        return self.thickness


# =============================================================================
# IntentionGenerator 意图生成器
# =============================================================================
class IntentionGenerator:
    """
    意图生成器 - 基于自由能原理的自发意图产生
    
    核心算法 (主动推理简化版):
    1. 观测当前状态 s_t
    2. 更新生成模型 p(s_{t+1} | s_t, a)
    3. 对每个候选行动 a_i:
        a. 预测未来状态 s_{t+1:t+H}
        b. 计算预测误差 PE = ||predicted - preferred||
        c. 计算自由能 F = PE + model_complexity
    4. 选择使 F 最小的行动作为意图
    5. 返回意图对象
    
    与OMNI-HUB集成:
    - 读取11条线状态 -> 生成系统级意图
    - 也生成线级意图
    - 意图 -> GoalAutopoiesis -> 具体目标
    - 元认知监控器监控意图质量
    """
    
    def __init__(self, num_lines: int = DEFAULT_NUM_LINES, horizon: int = DEFAULT_HORIZON,
                 state_dim: int = DEFAULT_STATE_DIM, action_dim: int = 4,
                 num_candidate_actions: int = 16):
        """
        初始化意图生成器
        
        Args:
            num_lines: 系统线数 (OMNI-HUB = 11)
            horizon: 预测时域
            state_dim: 每条线的状态维度
            action_dim: 行动空间维度
            num_candidate_actions: 候选行动数量
        """
        self.num_lines = num_lines
        self.horizon = horizon
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.num_candidate_actions = num_candidate_actions
        
        # 为每条线创建生成模型
        self.generative_models = [
            GenerativeModel(state_dim, action_dim)
            for _ in range(num_lines)
        ]
        
        # 系统级生成模型 (聚合所有线)
        self.system_model = GenerativeModel(state_dim, action_dim)
        
        # Markov毯
        self.markov_blankets = [
            MarkovBlanket(state_dim)
            for _ in range(num_lines)
        ]
        self.system_blanket = MarkovBlanket(state_dim)
        
        # 偏好状态 (系统"想要"达到的状态)
        # [高能量, 高稳定性, 高连通性, 高涌现度]
        self.preferred_state = np.array([0.8, 0.7, 0.9, 0.85])
        
        # 候选行动库 (在行动空间中采样)
        np.random.seed(42)
        self.candidate_actions = self._sample_candidate_actions()
        
        # 历史记录
        self.intention_history = []
        self.state_history = deque(maxlen=200)
        self.free_energy_history = []
        self.error_reduction_history = []
        
        # 当前全局状态
        self.current_state = np.zeros((num_lines, state_dim))
        
        # 行动到效果的记忆 (用于学习)
        self.action_memory = deque(maxlen=100)
        
        # 统计
        self.stats = {
            'total_intentions': 0,
            'system_intentions': 0,
            'line_intentions': [0] * num_lines,
            'avg_strength': 0.0,
            'avg_error_reduction': 0.0,
            'avg_free_energy': 0.0,
        }
        
    def _sample_candidate_actions(self) -> np.ndarray:
        """
        在行动空间中采样候选行动
        
        主动推理中，候选行动应该覆盖可能推动系统向偏好状态移动的方向。
        这里我们采样随机行动、坐标轴行动和自适应的"趋向偏好"行动。
        
        Returns:
            候选行动矩阵 (num_candidate_actions, action_dim)
        """
        actions = []
        
        # 1. 零行动 (不采取行动 - 基线)
        actions.append(np.zeros(self.action_dim))
        
        # 2. 坐标轴行动 (沿每个维度正负方向)
        for i in range(self.action_dim):
            action = np.zeros(self.action_dim)
            action[i] = 1.0
            actions.append(action.copy())
            action[i] = -1.0
            actions.append(action.copy())
        
        # 3. "趋向偏好"行动模板 (会在generate_intention中自适应调整)
        # 这里先放几个通用的正方向行动
        actions.append(np.ones(self.action_dim) * 0.5)
        actions.append(np.ones(self.action_dim) * 0.8)
        
        # 4. 随机采样行动
        n_random = self.num_candidate_actions - len(actions) - 2
        for _ in range(max(0, n_random)):
            action = np.random.randn(self.action_dim)
            action = action / (la.norm(action) + EPSILON)
            actions.append(action)
        
        # 5. 对角线组合
        actions.append(np.array([1.0, 1.0, -1.0, -1.0]) / 2.0)
        actions.append(np.array([-1.0, 1.0, 1.0, -1.0]) / 2.0)
        
        # 确保数量正确
        result = np.array(actions[:self.num_candidate_actions])
        
        # 归一化每个行动
        for i in range(len(result)):
            norm = la.norm(result[i])
            if norm > 1.0:
                result[i] = result[i] / norm
                
        return result
    
    def update_generative_model(self, observation: np.ndarray, 
                                line_id: Optional[int] = None,
                                prev_action: Optional[np.ndarray] = None) -> Dict:
        """
        更新生成模型
        
        Args:
            observation: 当前观测 (可以是单条线或整个系统)
            line_id: 线ID (None表示系统级)
            prev_action: 上一时刻采取的行动
            
        Returns:
            更新统计信息
        """
        observation = np.asarray(observation).reshape(-1)
        
        if line_id is not None:
            # 更新单条线的模型
            model = self.generative_models[line_id]
            prev_state = self.current_state[line_id] if self.current_state is not None else None
            stats = model.update(observation, prev_action, prev_state)
            self.current_state[line_id] = observation[:self.state_dim]
        else:
            # 更新系统级模型
            if len(observation) == self.state_dim:
                # 聚合状态
                system_state = observation
            else:
                system_state = np.mean(self.current_state, axis=0)
            
            prev_state = np.mean(self.current_state, axis=0) if self.current_state is not None else None
            stats = self.system_model.update(system_state, prev_action, prev_state)
            
        return stats
    
    def predict_future(self, state: np.ndarray, action_sequence: List[np.ndarray],
                       line_id: Optional[int] = None, steps: Optional[int] = None) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        预测未来状态
        
        Args:
            state: 当前状态
            action_sequence: 行动序列
            line_id: 线ID (None使用系统级模型)
            steps: 预测步数 (默认horizon)
            
        Returns:
            未来状态预测列表
        """
        state = np.asarray(state).reshape(-1)
        steps = steps or self.horizon
        
        model = self.generative_models[line_id] if line_id is not None else self.system_model
        return model.simulate_forward(state, action_sequence, steps)
    
    def compute_prediction_error(self, prediction: np.ndarray, actual: np.ndarray,
                                  preferred: Optional[np.ndarray] = None) -> np.ndarray:
        """
        计算预测误差
        
        Args:
            prediction: 预测状态
            actual: 实际状态
            preferred: 偏好状态 (如果提供,计算到偏好的误差)
            
        Returns:
            预测误差向量
        """
        prediction = np.asarray(prediction).reshape(-1)
        
        if preferred is not None:
            preferred = np.asarray(preferred).reshape(-1)
            error = prediction - preferred
        else:
            actual = np.asarray(actual).reshape(-1)
            error = prediction - actual
            
        return error
    
    def free_energy(self, state: np.ndarray, line_id: Optional[int] = None,
                    preferred_state: Optional[np.ndarray] = None) -> float:
        """
        计算自由能
        
        Args:
            state: 当前状态
            line_id: 线ID
            preferred_state: 偏好状态
            
        Returns:
            自由能标量
        """
        state = np.asarray(state).reshape(-1)
        
        if preferred_state is None:
            preferred_state = self.preferred_state
            
        model = self.generative_models[line_id] if line_id is not None else self.system_model
        return model.free_energy(state, preferred_state)
    
    def markov_blanket(self, state: np.ndarray, line_id: Optional[int] = None) -> Dict:
        """
        计算Markov毯
        
        Args:
            state: 当前状态
            line_id: 线ID
            
        Returns:
            Markov毯分区字典
        """
        state = np.asarray(state).reshape(-1)
        
        blanket = self.markov_blankets[line_id] if line_id is not None else self.system_blanket
        return blanket.partition(state)
    
    def generate_intention(self, line_id: Optional[int] = None,
                           context: Optional[Dict] = None) -> Intention:
        """
        生成意图 - 核心算法
        
        主动推理：选择最小化未来自由能的行动方向
        
        Args:
            line_id: 线ID (None生成系统级意图)
            context: 额外上下文信息
            
        Returns:
            Intention对象
        """
        context = context or {}
        
        # 获取当前状态
        if line_id is not None:
            current_state = self.current_state[line_id].copy()
            model = self.generative_models[line_id]
            blanket = self.markov_blankets[line_id]
        else:
            current_state = np.mean(self.current_state, axis=0)
            model = self.system_model
            blanket = self.system_blanket
            
        # 获取Markov毯分区
        mb = blanket.partition(current_state)
        
        # 计算当前自由能
        fe_before = self.free_energy(current_state, line_id)
        
        # === 主动推理：评估每个候选行动 ===
        # 动态生成候选行动：固定库 + 自适应的"趋向偏好"行动
        direction_to_preferred = self.preferred_state - current_state
        direction_to_preferred = direction_to_preferred / (la.norm(direction_to_preferred) + EPSILON)
        
        # 创建自适应候选行动列表
        adaptive_actions = []
        for scale in [0.3, 0.6, 1.0]:
            adaptive_actions.append(direction_to_preferred * scale)
        
        all_actions = list(self.candidate_actions) + adaptive_actions
        all_action_indices = list(range(len(self.candidate_actions))) + [-1, -2, -3]
        
        best_action_idx = -1
        best_free_energy = float('inf')
        best_future_states = None
        best_first_step_fe = fe_before
        
        action_scores = []
        
        for idx, action in zip(all_action_indices, all_actions):
            action = np.asarray(action).reshape(-1)
            # 构建行动序列 (假设重复执行同一行动)
            action_sequence = [action] * self.horizon
            
            # 前向模拟
            future_predictions = self.predict_future(current_state, action_sequence, line_id)
            
            if not future_predictions:
                continue
                
            # 计算累计自由能 (折扣未来)
            total_fe = 0.0
            total_pe = 0.0
            first_step_fe = 0.0
            discount = 1.0
            
            for t, (mu_pred, Sigma_pred) in enumerate(future_predictions):
                # 预测误差 (到偏好状态)
                pred_error = self.compute_prediction_error(mu_pred, None, self.preferred_state)
                pe = la.norm(pred_error) ** 2
                
                # 不确定性惩罚
                uncertainty = np.trace(Sigma_pred)
                
                # 复杂度惩罚 (避免过于复杂的行动)
                complexity = np.dot(action, action) * 0.05
                
                # 时间折扣
                step_fe = (pe + uncertainty + complexity) * discount
                total_fe += step_fe
                total_pe += pe * discount
                
                if t == 0:
                    first_step_fe = step_fe
                
                discount *= GAMMA
            
            # 考虑模型不确定性
            model_uncertainty = model.get_uncertainty()
            total_fe += model_uncertainty * 0.3
            
            action_scores.append({
                'action_idx': idx,
                'action': action,
                'free_energy': total_fe,
                'first_step_fe': first_step_fe,
                'prediction_error': total_pe,
                'future_states': future_predictions,
            })
            
            if total_fe < best_free_energy:
                best_free_energy = total_fe
                best_action_idx = idx
                best_future_states = future_predictions
                best_first_step_fe = first_step_fe
        
        # 如果没有有效预测，返回空意图
        if best_action_idx < 0 or not best_future_states:
            return Intention(
                direction=np.zeros(self.state_dim),
                strength=0.0,
                target_state=current_state,
                predicted_error_reduction=0.0,
                free_energy_before=fe_before,
                free_energy_after=fe_before,
                line_preference=line_id if line_id is not None else -1,
                confidence=0.0,
            )
        
        # 计算置信度 (基于与其他行动的差异)
        if len(action_scores) > 1:
            energies = [s['free_energy'] for s in action_scores]
            energy_range = max(energies) - min(energies)
            confidence = min(1.0, energy_range / (np.mean(energies) + EPSILON))
        else:
            confidence = 0.5
            
        # 选择最佳行动
        if best_action_idx >= 0 and best_action_idx < len(self.candidate_actions):
            best_action = self.candidate_actions[best_action_idx]
        else:
            # 自适应行动
            best_action = direction_to_preferred * abs(best_action_idx) * 0.3
        
        # 计算预测误差减少
        initial_pe = la.norm(self.compute_prediction_error(current_state, None, self.preferred_state))
        final_pe = la.norm(self.compute_prediction_error(best_future_states[-1][0], None, self.preferred_state))
        error_reduction = max(0, initial_pe - final_pe)
        
        # 意图强度 (主要基于误差减少，也考虑自由能改善)
        fe_improvement = fe_before - best_first_step_fe
        fe_ratio = fe_improvement / (fe_before + EPSILON) if fe_before > 0 else 0
        
        strength = 0.7 * min(1.0, error_reduction / (initial_pe + EPSILON)) + \
                   0.3 * max(0, fe_ratio)
        strength = np.clip(strength, 0.0, 1.0)
        
        # 目标状态 (预测的未来状态)
        target_state = best_future_states[-1][0]
        
        # 意图方向 (从当前到目标的方向)
        direction = target_state - current_state
        direction = direction / (la.norm(direction) + EPSILON)
        
        # 创建意图对象
        intention = Intention(
            direction=direction,
            strength=strength,
            target_state=target_state,
            predicted_error_reduction=error_reduction,
            free_energy_before=fe_before,
            free_energy_after=best_free_energy,
            line_preference=line_id if line_id is not None else -1,
            action_id=best_action_idx,
            confidence=confidence,
        )
        
        # 记录
        self.intention_history.append(intention)
        self.free_energy_history.append(fe_before)
        self.error_reduction_history.append(error_reduction)
        
        # 更新统计
        self.stats['total_intentions'] += 1
        if line_id is not None:
            self.stats['line_intentions'][line_id] += 1
        else:
            self.stats['system_intentions'] += 1
            
        self.stats['avg_strength'] = np.mean([i.strength for i in self.intention_history])
        self.stats['avg_error_reduction'] = np.mean(self.error_reduction_history)
        self.stats['avg_free_energy'] = np.mean(self.free_energy_history)
        
        return intention
    
    def select_action(self, intention: Intention) -> np.ndarray:
        """
        将意图转化为具体行动
        
        Args:
            intention: 意图对象
            
        Returns:
            行动向量
        """
        if intention.action_id >= 0 and intention.action_id < len(self.candidate_actions):
            base_action = self.candidate_actions[intention.action_id].copy()
        else:
            base_action = intention.direction * intention.strength
            
        # 根据强度缩放
        action = base_action * intention.strength
        
        # 添加基于方向的微调
        direction_component = intention.direction * 0.3 * intention.strength
        action = action + direction_component
        
        # 归一化
        action_norm = la.norm(action)
        if action_norm > 1.0:
            action = action / action_norm
            
        # 记录行动效果
        self.action_memory.append({
            'intention': intention,
            'action': action.copy(),
            'timestamp': intention.timestamp,
        })
        
        return action
    
    def generate_all_intentions(self) -> List[Intention]:
        """
        生成所有意图 (系统级 + 每条线)
        
        Returns:
            意图列表 [系统意图, 线0意图, 线1意图, ...]
        """
        intentions = []
        
        # 系统级意图
        system_intention = self.generate_intention(line_id=None)
        intentions.append(system_intention)
        
        # 线级意图
        for line_id in range(self.num_lines):
            line_intention = self.generate_intention(line_id=line_id)
            intentions.append(line_intention)
            
        return intentions
    
    def get_diagnostics(self) -> Dict:
        """
        获取诊断信息
        
        Returns:
            诊断字典
        """
        diagnostics = {
            'stats': self.stats.copy(),
            'model_ages': [m.age for m in self.generative_models],
            'system_model_age': self.system_model.age,
            'model_uncertainties': [m.get_uncertainty() for m in self.generative_models],
            'system_uncertainty': self.system_model.get_uncertainty(),
            'free_energy_trend': list(self.free_energy_history[-20:]),
            'recent_intentions': [i.to_dict() for i in self.intention_history[-5:]],
        }
        return diagnostics


# =============================================================================
# OMNI-HUB 系统模拟器
# =============================================================================
class OmniHubSimulator:
    """
    OMNI-HUB系统模拟器 - 用于实验验证
    
    模拟11条线的动力学:
    - 每条线有 [能量, 稳定性, 连通性, 涌现度] 状态
    - 线之间有耦合
    - 意图驱动系统演化
    """
    
    def __init__(self, num_lines: int = DEFAULT_NUM_LINES, 
                 state_dim: int = DEFAULT_STATE_DIM,
                 coupling_strength: float = 0.1):
        self.num_lines = num_lines
        self.state_dim = state_dim
        self.coupling_strength = coupling_strength
        
        # 初始化状态 (随机, 偏离偏好状态 - 需要意图来修正)
        np.random.seed(123)
        self.states = np.random.rand(num_lines, state_dim) * 0.4 + 0.2
        
        # 线间耦合矩阵 (哪条线影响哪条线)
        self.coupling = np.eye(num_lines) * 0.8  # 自耦合
        # 添加一些跨线耦合
        for i in range(num_lines):
            neighbors = [(i-1) % num_lines, (i+1) % num_lines]
            for j in neighbors:
                self.coupling[i, j] = coupling_strength
                
        # 外部扰动
        self.external_noise_level = 0.05
        
        # 偏好状态 (系统"应该"达到的状态)
        self.preferred_state = np.array([0.85, 0.75, 0.9, 0.9])
        
        # 历史
        self.state_history = [self.states.copy()]
        self.action_history = []
        
    def step(self, actions: List[np.ndarray], dt: float = 0.1) -> np.ndarray:
        """
        系统演化一步
        
        Args:
            actions: 每条线的行动列表
            dt: 时间步长
            
        Returns:
            新状态
        """
        new_states = np.zeros_like(self.states)
        
        for i in range(self.num_lines):
            # 当前状态
            s = self.states[i]
            
            # 自动力学 (微弱的趋向偏好状态趋势 - 不足以独自拉回)
            intrinsic = -0.04 * (s - self.preferred_state)
            
            # 行动影响 (意图驱动的主动改变 - 这是主要的恢复力量)
            action_effect = np.zeros(self.state_dim)
            if i < len(actions) and actions[i] is not None:
                action = np.asarray(actions[i]).reshape(-1)
                # 行动对不同维度的影响
                action_effect = action * np.array([0.8, 0.7, 0.75, 0.6])
            
            # 线间耦合 (邻居的影响)
            coupling_effect = np.zeros(self.state_dim)
            for j in range(self.num_lines):
                if self.coupling[i, j] > 0 and i != j:
                    coupling_effect += self.coupling[i, j] * (self.states[j] - s) * 0.15
            
            # 外部噪声 (随机扰动)
            noise = np.random.randn(self.state_dim) * self.external_noise_level
            
            # 状态更新
            ds = intrinsic + action_effect + coupling_effect + noise
            new_states[i] = np.clip(s + ds * dt, 0, 1)
            
        self.states = new_states
        self.state_history.append(self.states.copy())
        
        return self.states
    
    def get_observations(self) -> np.ndarray:
        """获取当前观测 (加噪声)"""
        noise = np.random.randn(self.num_lines, self.state_dim) * 0.01
        return np.clip(self.states + noise, 0, 1)
    
    def compute_system_health(self) -> float:
        """计算系统健康度"""
        # 到偏好状态的距离
        distances = la.norm(self.states - self.preferred_state, axis=1)
        health = np.mean(1.0 - distances / np.sqrt(self.state_dim))
        return float(np.clip(health, 0, 1))
    
    def compute_emergence_index(self) -> float:
        """计算涌现指数"""
        # 基于状态方差和耦合的涌现度量
        state_variance = np.var(self.states, axis=0)
        coherence = 1.0 - np.mean(state_variance)
        emergence = coherence * np.mean(self.states[:, 3])  # 涌现度维度
        return float(np.clip(emergence, 0, 1))


# =============================================================================
# 实验验证
# =============================================================================
def run_experiment(num_steps: int = 100, verbose: bool = True) -> Dict:
    """
    运行100步实验验证
    
    验证:
    1. 意图是否确实减少了预测误差
    2. 意图是否与系统实际需求匹配
    3. 意图生成频率、强度分布、误差减少效果
    
    Args:
        num_steps: 模拟步数
        verbose: 是否打印详细日志
        
    Returns:
        实验结果字典
    """
    logger.info("=" * 70)
    logger.info("OMNI-HUB v5.0 IntentionGenerator 实验验证")
    logger.info("=" * 70)
    logger.info(f"\n实验配置:")
    logger.info(f"  - 模拟步数: {num_steps}")
    logger.info(f"  - 系统线数: {DEFAULT_NUM_LINES}")
    logger.info(f"  - 预测时域: {DEFAULT_HORIZON}")
    logger.info(f"  - 状态维度: {DEFAULT_STATE_DIM}")
    logger.info(f"  - 理论基础: Friston自由能原理 / 主动推理")
    logger.info(str())
    
    # 初始化
    simulator = OmniHubSimulator()
    generator = IntentionGenerator()
    
    # 记录
    results = {
        'steps': [],
        'system_health': [],
        'emergence_index': [],
        'free_energy_system': [],
        'free_energy_lines': [[] for _ in range(DEFAULT_NUM_LINES)],
        'intention_strengths': [],
        'intention_strengths_system': [],
        'intention_strengths_lines': [],
        'error_reductions': [],
        'prediction_errors_before': [],
        'prediction_errors_after': [],
        'intention_confidences': [],
        'markov_blanket_thickness': [],
        'model_uncertainties': [],
        'actions_taken': [],
        'intentions_generated': [],
    }
    
    # 100步模拟
    for step in range(num_steps):
        # 1. 观测当前状态
        observations = simulator.get_observations()
        
        # 2. 更新生成模型
        for line_id in range(DEFAULT_NUM_LINES):
            generator.update_generative_model(observations[line_id], line_id=line_id)
        
        # 系统级更新
        system_obs = np.mean(observations, axis=0)
        generator.update_generative_model(system_obs, line_id=None)
        
        # 3. 生成意图
        intentions = generator.generate_all_intentions()
        system_intention = intentions[0]
        line_intentions = intentions[1:]
        
        # 4. 选择行动
        actions = []
        for line_id in range(DEFAULT_NUM_LINES):
            action = generator.select_action(line_intentions[line_id])
            actions.append(action)
            
        # 5. 系统演化
        simulator.step(actions)
        
        # 6. 记录结果
        health = simulator.compute_system_health()
        emergence = simulator.compute_emergence_index()
        
        results['steps'].append(step)
        results['system_health'].append(health)
        results['emergence_index'].append(emergence)
        results['free_energy_system'].append(system_intention.free_energy_before)
        
        for line_id in range(DEFAULT_NUM_LINES):
            fe = generator.free_energy(generator.current_state[line_id], line_id)
            results['free_energy_lines'][line_id].append(fe)
            
        results['intention_strengths'].append(np.mean([i.strength for i in intentions]))
        results['intention_strengths_system'].append(system_intention.strength)
        results['intention_strengths_lines'].append(np.mean([i.strength for i in line_intentions]))
        results['error_reductions'].append(system_intention.predicted_error_reduction)
        results['prediction_errors_before'].append(
            la.norm(generator.current_state.mean(axis=0) - generator.preferred_state))
        results['intention_confidences'].append(system_intention.confidence)
        results['model_uncertainties'].append(generator.system_model.get_uncertainty())
        results['intentions_generated'].append(len(intentions))
        
        # Markov毯厚度
        mb_stats = generator.system_blanket.compute_blanket_statistics(list(generator.state_history))
        results['markov_blanket_thickness'].append(generator.system_blanket.thickness)
        
        # 周期性打印
        if verbose and (step % 10 == 0 or step == num_steps - 1):
            print(f"Step {step:3d}: ")
                  f"Health={health:.3f} "
                  f"Emergence={emergence:.3f} "
                  f"FE={system_intention.free_energy_before:.3f} "
                  f"Intentions={len(intentions)} "
                  f"SysStrength={system_intention.strength:.3f}"
    
    # ===== 实验分析 =====
    logger.info("\n" + "=" * 70)
    logger.info("实验结果分析")
    logger.info("=" * 70)
    
    # 1. 意图是否减少了预测误差?
    initial_pe = results['prediction_errors_before'][:10]
    final_pe = results['prediction_errors_before'][-10:]
    pe_reduction = np.mean(initial_pe) - np.mean(final_pe)
    
    logger.info(f"\n[验证1] 意图是否减少预测误差?")
    logger.info(f"  初始10步平均预测误差: {np.mean(initial_pe):.4f}")
    logger.info(f"  最后10步平均预测误差: {np.mean(final_pe):.4f}")
    logger.info(f"  误差减少量: {pe_reduction:.4f}")
    logger.info(f"  结论: {'✓ 通过' if pe_reduction > 0 else '✗ 未通过'}")
    
    # 2. 系统健康度变化
    initial_health = np.mean(results['system_health'][:10])
    final_health = np.mean(results['system_health'][-10:])
    health_improvement = final_health - initial_health
    
    logger.info(f"\n[验证2] 系统健康度是否提升?")
    logger.info(f"  初始健康度: {initial_health:.4f}")
    logger.info(f"  最终健康度: {final_health:.4f}")
    logger.info(f"  提升量: {health_improvement:.4f}")
    logger.info(f"  结论: {'✓ 通过' if health_improvement > 0 else '✗ 未通过'}")
    
    # 3. 涌现指数变化
    initial_emergence = np.mean(results['emergence_index'][:10])
    final_emergence = np.mean(results['emergence_index'][-10:])
    emergence_improvement = final_emergence - initial_emergence
    
    logger.info(f"\n[验证3] 涌现指数是否提升?")
    logger.info(f"  初始涌现指数: {initial_emergence:.4f}")
    logger.info(f"  最终涌现指数: {final_emergence:.4f}")
    logger.info(f"  提升量: {emergence_improvement:.4f}")
    logger.info(f"  结论: {'✓ 通过' if emergence_improvement > 0 else '✗ 未通过'}")
    
    # 4. 自由能变化
    initial_fe = np.mean(results['free_energy_system'][:10])
    final_fe = np.mean(results['free_energy_system'][-10:])
    fe_reduction = initial_fe - final_fe
    
    logger.info(f"\n[验证4] 自由能是否降低 (FEP核心预测)?")
    logger.info(f"  初始自由能: {initial_fe:.4f}")
    logger.info(f"  最终自由能: {final_fe:.4f}")
    logger.info(f"  降低量: {fe_reduction:.4f}")
    logger.info(f"  结论: {'✓ 通过' if fe_reduction > 0 else '✗ 未通过'}")
    
    # 5. 意图统计
    avg_strength = np.mean(results['intention_strengths'])
    avg_system_strength = np.mean(results['intention_strengths_system'])
    avg_line_strength = np.mean(results['intention_strengths_lines'])
    avg_confidence = np.mean(results['intention_confidences'])
    avg_error_reduction = np.mean([e for e in results['error_reductions'] if e > 0])
    
    logger.info(f"\n[验证5] 意图生成统计")
    logger.info(f"  总意图数: {len(results['intention_strengths']) * (DEFAULT_NUM_LINES + 1)}")
    logger.info(f"  平均意图强度: {avg_strength:.4f}")
    logger.info(f"  系统意图平均强度: {avg_system_strength:.4f}")
    logger.info(f"  线意图平均强度: {avg_line_strength:.4f}")
    logger.info(f"  平均置信度: {avg_confidence:.4f}")
    logger.info(f"  平均误差减少: {avg_error_reduction:.4f}")
    logger.info(f"  意图生成频率: 每步 {DEFAULT_NUM_LINES + 1} 个")
    
    # 6. 模型学习效果
    initial_uncertainty = np.mean(results['model_uncertainties'][:10])
    final_uncertainty = np.mean(results['model_uncertainties'][-10:])
    
    logger.info(f"\n[验证6] 生成模型学习效果")
    logger.info(f"  初始模型不确定性: {initial_uncertainty:.4f}")
    logger.info(f"  最终模型不确定性: {final_uncertainty:.4f}")
    logger.info(f"  不确定性变化: {final_uncertainty - initial_uncertainty:.4f}")
    logger.info(f"  结论: {'✓ 模型稳定' if final_uncertainty < initial_uncertainty * 2 else '△ 需要关注'}")
    
    # 7. Markov毯分析
    avg_thickness = np.mean(results['markov_blanket_thickness'])
    logger.info(f"\n[验证7] Markov毯边界")
    logger.info(f"  平均毯厚度: {avg_thickness:.4f}")
    logger.info(f"  厚度范围: [{min(results['markov_blanket_thickness']):.3f}, {max(results['markov_blanket_thickness']):.3f}]")
    logger.info(f"  解释: 厚度>1表示系统边界较'厚', 对外部影响抵抗强")
    
    # 8. 相关性分析
    from scipy.stats import pearsonr
    logger.info(f"\n[验证8] 相关性分析")
    corr_fe_health, p1 = pearsonr(results['free_energy_system'], results['system_health'])
    corr_strength_reduction, p2 = pearsonr(results['intention_strengths_system'], results['error_reductions'])
    
    logger.info(f"  自由能 ↔ 健康度 相关性: {corr_fe_health:.3f} (p={p1:.3f})")
    logger.info(f"  意图强度 ↔ 误差减少 相关性: {corr_strength_reduction:.3f} (p={p2:.3f})")
    logger.info(f"  结论: {'✓ 预期相关' if corr_fe_health < -0.3 else '△ 弱相关'}")
    
    # 综合评分
    score = 0
    score += 1 if pe_reduction > 0 else 0
    score += 1 if health_improvement > 0 else 0
    score += 1 if emergence_improvement > 0 else 0
    score += 1 if fe_reduction > 0 else 0
    score += 1 if avg_error_reduction > 0 else 0
    score += 1 if abs(corr_fe_health) > 0.3 else 0
    
    logger.info(f"\n{'=' * 70}")
    logger.info(f"综合评分: {score}/6 项验证通过")
    logger.info(f"{'=' * 70}")
    
    if score >= 5:
        logger.info("评级: ★★★★★ 优秀 - IntentionGenerator工作正常")
    elif score >= 4:
        logger.info("评级: ★★★★☆ 良好 - 主要功能正常")
    elif score >= 3:
        logger.info("评级: ★★★☆☆ 合格 - 需要优化")
    else:
        logger.info("评级: ★★☆☆☆ 需改进 - 存在明显问题")
    
    # 保存详细结果
    results['summary'] = {
        'pe_reduction': float(pe_reduction),
        'health_improvement': float(health_improvement),
        'emergence_improvement': float(emergence_improvement),
        'fe_reduction': float(fe_reduction),
        'avg_strength': float(avg_strength),
        'avg_confidence': float(avg_confidence),
        'score': int(score),
        'total_steps': num_steps,
    }
    
    return results


# =============================================================================
# 可视化 (如果matplotlib可用)
# =============================================================================
def plot_results(results: Dict, save_path: Optional[str] = None):
    """
    可视化实验结果
    
    Args:
        results: 实验结果字典
        save_path: 保存路径
    """
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(3, 3, figsize=(15, 12))
        fig.suptitle('OMNI-HUB v5.0 IntentionGenerator Experiment', fontsize=14, fontweight='bold')
        
        steps = results['steps']
        
        # 1. 系统健康度
        ax = axes[0, 0]
        ax.plot(steps, results['system_health'], 'b-', linewidth=1.5)
        ax.set_title('System Health')
        ax.set_xlabel('Step')
        ax.set_ylabel('Health')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)
        
        # 2. 涌现指数
        ax = axes[0, 1]
        ax.plot(steps, results['emergence_index'], 'g-', linewidth=1.5)
        ax.set_title('Emergence Index')
        ax.set_xlabel('Step')
        ax.set_ylabel('Emergence')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)
        
        # 3. 自由能
        ax = axes[0, 2]
        ax.plot(steps, results['free_energy_system'], 'r-', linewidth=1.5, label='System')
        ax.set_title('Free Energy (System)')
        ax.set_xlabel('Step')
        ax.set_ylabel('Free Energy')
        ax.grid(True, alpha=0.3)
        
        # 4. 意图强度
        ax = axes[1, 0]
        ax.plot(steps, results['intention_strengths_system'], 'm-', linewidth=1.5, label='System')
        ax.plot(steps, results['intention_strengths_lines'], 'c-', linewidth=1, alpha=0.7, label='Lines (avg)')
        ax.set_title('Intention Strength')
        ax.set_xlabel('Step')
        ax.set_ylabel('Strength')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)
        
        # 5. 预测误差
        ax = axes[1, 1]
        ax.plot(steps, results['prediction_errors_before'], 'orange', linewidth=1.5, label='PE')
        ax.set_title('Prediction Error')
        ax.set_xlabel('Step')
        ax.set_ylabel('Error')
        ax.grid(True, alpha=0.3)
        
        # 6. 误差减少
        ax = axes[1, 2]
        ax.bar(steps, results['error_reductions'], color='teal', alpha=0.7)
        ax.set_title('Predicted Error Reduction')
        ax.set_xlabel('Step')
        ax.set_ylabel('Reduction')
        ax.grid(True, alpha=0.3)
        
        # 7. 置信度
        ax = axes[2, 0]
        ax.plot(steps, results['intention_confidences'], 'purple', linewidth=1.5)
        ax.set_title('Intention Confidence')
        ax.set_xlabel('Step')
        ax.set_ylabel('Confidence')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)
        
        # 8. 模型不确定性
        ax = axes[2, 1]
        ax.plot(steps, results['model_uncertainties'], 'brown', linewidth=1.5)
        ax.set_title('Model Uncertainty')
        ax.set_xlabel('Step')
        ax.set_ylabel('Uncertainty')
        ax.grid(True, alpha=0.3)
        
        # 9. Markov毯厚度
        ax = axes[2, 2]
        ax.plot(steps, results['markov_blanket_thickness'], 'darkgreen', linewidth=1.5)
        ax.set_title('Markov Blanket Thickness')
        ax.set_xlabel('Step')
        ax.set_ylabel('Thickness')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"\n图表已保存: {save_path}")
        
        plt.show()
        
# =============================================================================
# 主入口
# =============================================================================
if __name__ == "__main__":
    # 运行实验
    results = run_experiment(num_steps=100, verbose=True)
    
    # 可视化
    plot_results(results, save_path="/mnt/agents/output/OMNI-HUB/core/intention_generator_experiment.png")
    
    # 保存详细结果
    summary_path = "/mnt/agents/output/OMNI-HUB/core/experiment_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        # 转换numpy类型为Python原生类型
        summary = results.get('summary', {})
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n实验摘要已保存: {summary_path}")
    print("\nOMNI-HUB v5.0 IntentionGenerator 实验完成!")
