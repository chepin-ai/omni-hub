
"""
OMNI-HUB 场熵理论框架 (Field Entropy Framework)
================================================
研究目标：将信息论熵概念引入分布式系统场论框架，建立场熵/层-网-塔的数学模型

核心方程:
  H_field = -Σ_i p_i log(p_i)        [香农场熵]
  H_cross = H_field(debt) + H_field(finding) - I(debt;finding)  [交叉熵]
  dS_total/dt = dS_layer/dt + dS_network/dt + dS_tower/dt + S_gen  [熵平衡方程]

作者: OMNI-HUB 场熵理论研究员
版本: 1.0.0
"""

__version__ = "11.0.0"
import numpy as np
import numpy.typing as npt
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from collections import deque


# ============================================================================
# 1. 基础数据结构与枚举
# ============================================================================

class DimensionType(Enum):
    """场熵维度类型"""
    HEALTH = "health"           # 线路健康度
    QUEUE_DEPTH = "queue_depth" # 任务队列深度
    DEBT = "debt"               # 债务分布
    FINDING = "finding"         # 发现分布
    CONSENSUS = "consensus"     # 共识状态
    FUEL = "fuel"               # 燃料分布
    MESSAGE = "message"         # 消息流量
    TOPOLOGY = "topology"       # 拓扑连接度


@dataclass
class SystemState:
    """OMNI-HUB 系统状态快照"""
    timestamp: float
    line_health: npt.NDArray[np.float64]  # 11线路健康度
    queue_depth: npt.NDArray[np.float64]  # 各线路任务队列深度
    debt_dist: npt.NDArray[np.float64]    # 债务分布
    finding_dist: npt.NDArray[np.float64] # 发现分布
    consensus_vec: npt.NDArray[np.float64] # 共识状态向量
    fuel_level: npt.NDArray[np.float64]   # 燃料水平
    message_flow: npt.NDArray[np.float64] # 消息流量矩阵
    topology_adj: npt.NDArray[np.float64] # 拓扑邻接矩阵

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "line_health": self.line_health.tolist(),
            "queue_depth": self.queue_depth.tolist(),
            "debt_dist": self.debt_dist.tolist(),
            "finding_dist": self.finding_dist.tolist(),
            "consensus_vec": self.consensus_vec.tolist(),
            "fuel_level": self.fuel_level.tolist(),
            "message_flow": self.message_flow.tolist(),
            "topology_adj": self.topology_adj.tolist(),
        }


@dataclass
class EntropyProfile:
    """熵剖面 - 全维度熵快照"""
    timestamp: float
    dimensions: Dict[DimensionType, float]
    total_entropy: float
    cross_entropy_debt_finding: float
    mutual_info_debt_finding: float
    entropy_gradient: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "dimensions": {k.value: v for k, v in self.dimensions.items()},
            "total_entropy": self.total_entropy,
            "cross_entropy_debt_finding": self.cross_entropy_debt_finding,
            "mutual_info_debt_finding": self.mutual_info_debt_finding,
            "entropy_gradient": self.entropy_gradient,
        }


@dataclass
class EntropyFlowResult:
    """熵流分析结果"""
    layer_entropy: float
    network_entropy: float
    tower_entropy: float
    flow_layer_to_network: float
    flow_network_to_tower: float
    entropy_production: float
    is_conserved: bool
    conservation_error: float
    entropy_reduction_detected: bool
    reduction_locations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_entropy": self.layer_entropy,
            "network_entropy": self.network_entropy,
            "tower_entropy": self.tower_entropy,
            "flow_layer_to_network": self.flow_layer_to_network,
            "flow_network_to_tower": self.flow_network_to_tower,
            "entropy_production": self.entropy_production,
            "is_conserved": self.is_conserved,
            "conservation_error": self.conservation_error,
            "entropy_reduction_detected": self.entropy_reduction_detected,
            "reduction_locations": self.reduction_locations,
        }


# ============================================================================
# 2. 核心场熵类
# ============================================================================

class FieldEntropy:
    """
    OMNI-HUB 场熵计算引擎
    
    理论框架:
    -----------
    场熵将香农信息熵扩展到分布式系统的"场"概念中。
    每个维度定义一个概率分布 p_i，场熵衡量该维度上的"不确定性"或"信息丰富度"。
    
    关键洞察:
    - 高熵 = 高不确定性 = 高探索潜力 (FINDING)
    - 低熵 = 低不确定性 = 高执行效率 (DEBT清理)
    - 自驱能力 ∝ 熵梯度 ∝ dH/dt 的调控能力
    """
    
    # OMNI-HUB 11线路定义
    LINES = ['ucif2', 'lvlu', 'lgt', 'qfa', 'vinf', 'qgl', 'qlv', 'cisvr', 'qtlv', 'usrm', 'cfts']
    N_LINES = 11
    
    def __init__(self, epsilon: float = 1e-10, history_size: int = 1000):
        """
        初始化场熵引擎
        
        Args:
            epsilon: 数值稳定性的小常数
            history_size: 历史状态记录大小
        """
        self.epsilon = epsilon
        self.history_size = history_size
        self.state_history: deque[SystemState] = deque(maxlen=history_size)
        self.profile_history: deque[EntropyProfile] = deque(maxlen=history_size)
        self.flow_history: deque[EntropyFlowResult] = deque(maxlen=history_size)
        
        # 维度权重（用于总熵计算）
        self.dimension_weights: Dict[DimensionType, float] = {
            DimensionType.HEALTH: 0.15,
            DimensionType.QUEUE_DEPTH: 0.10,
            DimensionType.DEBT: 0.20,
            DimensionType.FINDING: 0.20,
            DimensionType.CONSENSUS: 0.15,
            DimensionType.FUEL: 0.10,
            DimensionType.MESSAGE: 0.05,
            DimensionType.TOPOLOGY: 0.05,
        }
    
    # ========================================================================
    # 2.1 核心熵计算方法
    # ========================================================================
    
    def _normalize_to_probability(self, data: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """将数据归一化为概率分布"""
        data = np.asarray(data, dtype=np.float64)
        # 处理负值：平移到非负
        if np.any(data < 0):
            data = data - np.min(data)
        total = np.sum(data) + self.epsilon
        p = (data + self.epsilon) / (total + self.epsilon * len(data))
        return p / np.sum(p)  # 确保严格归一化
    
    def _compute_shannon_entropy(self, p: npt.NDArray[np.float64]) -> float:
        """计算香农熵 H = -Σ p_i log(p_i)"""
        p = np.asarray(p, dtype=np.float64)
        p = p[p > self.epsilon]  # 忽略零概率项
        return float(-np.sum(p * np.log2(p)))
    
    def compute_field_entropy(self, dimension_data: npt.NDArray[np.float64], 
                             method: str = "shannon") -> float:
        """
        计算场熵 - 核心方法
        
        数学定义:
            H_field(X) = - Σ_i p(x_i) log_b p(x_i)
            
        其中 p(x_i) 是维度X上第i个状态的概率。
        在OMNI-HUB中，我们通过归一化观测数据来估计概率分布。
        
        Args:
            dimension_data: 某维度上的观测数据（如11线路健康度）
            method: 熵计算方法 ("shannon", "max_entropy", "tsallis")
            
        Returns:
            该维度的场熵值（比特）
            
        Example:
            >>> fe = FieldEntropy()
            >>> health = np.array([0.95, 0.92, 0.88, 0.91, 0.93, 0.90, 0.87, 0.94, 0.89, 0.91, 0.96])
            >>> H = fe.compute_field_entropy(health)
        """
        p = self._normalize_to_probability(dimension_data)
        
        if method == "shannon":
            return self._compute_shannon_entropy(p)
        elif method == "max_entropy":
            n = len(p)
            return np.log2(n)
        elif method == "tsallis":
            q = 1.5  # Tsallis参数
            return float((1 - np.sum(p ** q)) / (q - 1))
        else:
            raise ValueError(f"Unknown entropy method: {method}")
    
    def compute_joint_entropy(self, data_x: npt.NDArray[np.float64], 
                             data_y: npt.NDArray[np.float64]) -> float:
        """
        计算联合熵 H(X,Y) = -Σ_ij p(x_i,y_j) log p(x_i,y_j)
        
        使用直方图估计联合分布。
        """
        # 2D直方图估计联合分布
        hist, _, _ = np.histogram2d(data_x.flatten(), data_y.flatten(), bins=10)
        p_joint = hist / (np.sum(hist) + self.epsilon)
        p_joint = p_joint[p_joint > self.epsilon]
        return float(-np.sum(p_joint * np.log2(p_joint + self.epsilon)))
    
    def compute_mutual_information(self, data_x: npt.NDArray[np.float64], 
                                   data_y: npt.NDArray[np.float64]) -> float:
        """
        计算互信息 I(X;Y) = H(X) + H(Y) - H(X,Y)
        
        互信息衡量两个维度之间的统计依赖性。
        在OMNI-HUB中，I(debt;finding) 是关键指标：
        - 高互信息 = 债务生成与发现强相关
        - 低互信息 = 债务与发现独立（可能表示系统失调）
        """
        H_x = self.compute_field_entropy(data_x)
        H_y = self.compute_field_entropy(data_y)
        H_xy = self.compute_joint_entropy(data_x, data_y)
        return H_x + H_y - H_xy
    
    def compute_cross_entropy(self, data_p: npt.NDArray[np.float64], 
                             data_q: npt.NDArray[np.float64]) -> float:
        """
        计算交叉熵 H(p,q) = -Σ p_i log(q_i)
        
        用于衡量实际分布(p)与目标分布(q)的差异。
        """
        p = self._normalize_to_probability(data_p)
        q = self._normalize_to_probability(data_q)
        return float(-np.sum(p * np.log2(q + self.epsilon)))
    
    def compute_kl_divergence(self, data_p: npt.NDArray[np.float64], 
                             data_q: npt.NDArray[np.float64]) -> float:
        """
        KL散度 D_KL(p||q) = Σ p_i log(p_i/q_i)
        
        衡量两个分布之间的"距离"。非负，当且仅当p=q时为0。
        """
        p = self._normalize_to_probability(data_p)
        q = self._normalize_to_probability(data_q)
        return float(np.sum(p * np.log2((p + self.epsilon) / (q + self.epsilon))))
    
    def compute_conditional_entropy(self, data_x: npt.NDArray[np.float64], 
                                   data_y: npt.NDArray[np.float64]) -> float:
        """
        条件熵 H(X|Y) = H(X,Y) - H(Y)
        
        已知Y时X的剩余不确定性。
        """
        H_xy = self.compute_joint_entropy(data_x, data_y)
        H_y = self.compute_field_entropy(data_y)
        return H_xy - H_y
    
    # ========================================================================
    # 2.2 熵剖面 (Entropy Profile)
    # ========================================================================
    
    def entropy_profile(self, state: SystemState) -> EntropyProfile:
        """
        生成全维度熵剖面 - 核心方法
        
        熵剖面是OMNI-HUB系统状态的"熵签名"，包含所有维度的熵值及其相互关系。
        
        理论框架:
        -----------
        对于系统状态 S，熵剖面定义为:
            Profile(S) = {H_d | d ∈ D} ∪ {H_cross} ∪ {I_mutual} ∪ {∇H}
        
        其中:
        - D = {health, queue, debt, finding, consensus, fuel, message, topology}
        - H_cross = H(debt) + H(finding) - I(debt;finding)  [债务-发现交叉熵]
        - I_mutual = I(debt;finding)  [债务-发现互信息]
        - ∇H = {∂H/∂t}  [熵变率]
        
        Args:
            state: 系统状态快照
            
        Returns:
            EntropyProfile对象
        """
        dims: Dict[DimensionType, float] = {}
        
        # 计算各维度熵
        dims[DimensionType.HEALTH] = self.compute_field_entropy(state.line_health)
        dims[DimensionType.QUEUE_DEPTH] = self.compute_field_entropy(state.queue_depth)
        dims[DimensionType.DEBT] = self.compute_field_entropy(state.debt_dist)
        dims[DimensionType.FINDING] = self.compute_field_entropy(state.finding_dist)
        dims[DimensionType.CONSENSUS] = self.compute_field_entropy(state.consensus_vec)
        dims[DimensionType.FUEL] = self.compute_field_entropy(state.fuel_level)
        dims[DimensionType.MESSAGE] = self.compute_field_entropy(state.message_flow.flatten())
        dims[DimensionType.TOPOLOGY] = self.compute_field_entropy(state.topology_adj.flatten())
        
        # 加权总熵
        total_entropy = sum(
            self.dimension_weights[dim] * val 
            for dim, val in dims.items()
        )
        
        # 债务-发现交叉熵
        mi_debt_finding = self.compute_mutual_information(state.debt_dist, state.finding_dist)
        cross_entropy = dims[DimensionType.DEBT] + dims[DimensionType.FINDING] - mi_debt_finding
        
        # 熵梯度（若存在历史数据）
        entropy_gradient = self._compute_entropy_gradient(dims)
        
        profile = EntropyProfile(
            timestamp=state.timestamp,
            dimensions=dims,
            total_entropy=total_entropy,
            cross_entropy_debt_finding=cross_entropy,
            mutual_info_debt_finding=mi_debt_finding,
            entropy_gradient=entropy_gradient,
        )
        
        self.profile_history.append(profile)
        return profile
    
    def _compute_entropy_gradient(self, current_dims: Dict[DimensionType, float]) -> Dict[str, float]:
        """计算熵变率 dH/dt"""
        gradient: Dict[str, float] = {}
        if len(self.profile_history) < 2:
            return {dim.value: 0.0 for dim in DimensionType}
        
        prev_profile = self.profile_history[-1]
        dt = current_dims[DimensionType.HEALTH] - prev_profile.dimensions.get(DimensionType.HEALTH, 0)
        time_delta = 1.0  # 归一化时间单位
        
        for dim in DimensionType:
            dH = current_dims[dim] - prev_profile.dimensions.get(dim, 0)
            gradient[f"d{dim.value}/dt"] = dH / time_delta if time_delta > 0 else 0.0
        
        return gradient
    
    def compute_debt_finding_entropy_map(self, state: SystemState) -> Dict[str, float]:
        """
        debt_generation ↔ FINDING 的熵映射关系
        
        核心假设:
        ---------
        债务生成 (debt_generation) 与发现 (FINDING) 存在熵层面的对偶关系:
        
        1. 债务熵 H(D) 高 → 系统处于高债务状态，需要清理
        2. 发现熵 H(F) 高 → 系统处于高探索状态，正在发现新路径
        3. 理想状态: H(D) 与 H(F) 保持动态平衡
        4. 危机状态: H(D) >> H(F) 或 H(D) << H(F)（系统失衡）
        
        映射方程:
            Ψ: DebtSpace → FindingSpace
            Ψ(d) = argmin_f { D_KL(P_debt || P_finding) + λ·I(debt;finding) }
        
        Returns:
            熵映射指标字典
        """
        H_debt = self.compute_field_entropy(state.debt_dist)
        H_finding = self.compute_field_entropy(state.finding_dist)
        mi = self.compute_mutual_information(state.debt_dist, state.finding_dist)
        kl_div = self.compute_kl_divergence(state.debt_dist, state.finding_dist)
        
        # 熵差（平衡指标）
        entropy_diff = abs(H_debt - H_finding)
        
        # 熵比（结构指标）
        entropy_ratio = H_debt / (H_finding + self.epsilon)
        
        # 归一化互信息（0-1，1表示完全相关）
        H_joint = self.compute_joint_entropy(state.debt_dist, state.finding_dist)
        nmi = mi / (H_joint + self.epsilon) if H_joint > 0 else 0.0
        
        # 债务-发现耦合度
        coupling = np.exp(-kl_div) * nmi
        
        # 自驱潜力指数 (Self-Drive Potential Index)
        # 高SDPI = 系统有能力将债务转化为发现
        sdpi = (mi * coupling) / (entropy_diff + self.epsilon)
        
        return {
            "H_debt": H_debt,
            "H_finding": H_finding,
            "mutual_information": mi,
            "kl_divergence": kl_div,
            "entropy_diff": entropy_diff,
            "entropy_ratio": entropy_ratio,
            "normalized_mutual_info": nmi,
            "coupling_coefficient": coupling,
            "self_drive_potential_index": sdpi,
            "balance_status": "balanced" if entropy_diff < 0.5 else "imbalanced",
        }
    
    # ========================================================================
    # 2.3 层-网-塔 熵流模型
    # ========================================================================
    
    def entropy_flow(self, layer_state: npt.NDArray[np.float64],
                    network_state: npt.NDArray[np.float64],
                    tower_state: npt.NDArray[np.float64]) -> EntropyFlowResult:
        """
        层-网-塔 熵流分析 - 核心方法
        
        理论模型:
        -----------
        OMNI-HUB的三层架构:
        - 层 (SITopology): 拓扑层，管理节点连接关系
        - 网 (ReliableMessaging): 网络层，管理消息传递
        - 塔 (OctaveScan): 扫描层，管理高维发现
        
        熵流方程:
            dS_layer/dt = -J_layer→network + σ_layer
            dS_network/dt = J_layer→network - J_network→tower + σ_network  
            dS_tower/dt = J_network→tower + σ_tower
        
        其中:
        - J_a→b: 从a到b的熵流（正 = 熵从a流向b）
        - σ_a: 层a的熵产生（≥0，热力学第二定律）
        
        守恒律:
            dS_total/dt = σ_layer + σ_network + σ_tower ≥ 0
        
        熵减可能性:
        -----------
        局部熵减可能存在！当系统通过"自驱引擎"(SelfDriveEngine)进行spin()迭代时，
        可以从环境中引入负熵（信息/秩序），导致某一层暂时熵减。
        但总熵产生 σ_total 必须 ≥ 0。
        
        Args:
            layer_state: 拓扑层状态向量（如节点度分布）
            network_state: 网络层状态向量（如消息队列状态）
            tower_state: 扫描层状态向量（如扫描维度分布）
            
        Returns:
            EntropyFlowResult对象
        """
        # 计算各层熵
        H_layer = self.compute_field_entropy(layer_state)
        H_network = self.compute_field_entropy(network_state)
        H_tower = self.compute_field_entropy(tower_state)
        
        # 计算熵流（使用KL散度作为流强度度量）
        # J_layer→network: 层到网的熵流
        flow_ln = self.compute_kl_divergence(layer_state, network_state)
        
        # J_network→tower: 网到塔的熵流  
        flow_nt = self.compute_kl_divergence(network_state, tower_state)
        
        # 估计熵产生
        # 若总熵增加且流不匹配，则存在熵产生
        total_entropy_current = H_layer + H_network + H_tower
        
        sigma = 0.0
        if len(self.flow_history) > 0:
            prev_total = (self.flow_history[-1].layer_entropy + 
                         self.flow_history[-1].network_entropy +
                         self.flow_history[-1].tower_entropy)
            sigma = max(0.0, total_entropy_current - prev_total - flow_ln - flow_nt)
        else:
            sigma = max(0.0, total_entropy_current - flow_ln - flow_nt)
        
        # 守恒性检验
        # 理想: dS_total = J_in - J_out + σ
        expected_total = flow_ln + flow_nt + sigma
        conservation_error = abs(total_entropy_current - expected_total)
        is_conserved = conservation_error < 0.5
        
        # 检测局部熵减
        reductions = []
        if len(self.flow_history) > 0:
            prev = self.flow_history[-1]
            if H_layer < prev.layer_entropy:
                reductions.append("layer")
            if H_network < prev.network_entropy:
                reductions.append("network")
            if H_tower < prev.tower_entropy:
                reductions.append("tower")
        
        result = EntropyFlowResult(
            layer_entropy=H_layer,
            network_entropy=H_network,
            tower_entropy=H_tower,
            flow_layer_to_network=flow_ln,
            flow_network_to_tower=flow_nt,
            entropy_production=sigma,
            is_conserved=is_conserved,
            conservation_error=conservation_error,
            entropy_reduction_detected=len(reductions) > 0,
            reduction_locations=reductions,
        )
        
        self.flow_history.append(result)
        return result
    
    def compute_entropy_current(self, state_from: SystemState, 
                               state_to: SystemState) -> Dict[str, float]:
        """
        计算两个状态间的熵流（熵电流）
        
        类比电学：
        - 熵 = "电荷"
        - 熵流 = "电流"  
        - 熵产生 = "电阻发热"
        """
        current: Dict[str, float] = {}
        
        dimensions = [
            ("line_health", state_from.line_health, state_to.line_health),
            ("queue_depth", state_from.queue_depth, state_to.queue_depth),
            ("debt_dist", state_from.debt_dist, state_to.debt_dist),
            ("finding_dist", state_from.finding_dist, state_to.finding_dist),
        ]
        
        for name, from_data, to_data in dimensions:
            H_from = self.compute_field_entropy(from_data)
            H_to = self.compute_field_entropy(to_data)
            current[f"J_{name}"] = H_to - H_from
        
        return current
    
    # ========================================================================
    # 2.4 自驱能力量化
    # ========================================================================
    
    def compute_self_drive_index(self, state: SystemState) -> Dict[str, float]:
        """
        计算系统自驱能力指数
        
        理论:
        ------
        自驱能力 = 系统主动降低总熵（增加秩序）的能力
        
        SDI = α·(1/H_total) + β·I(debt;finding) + γ·(1/σ_gen)
        
        其中:
        - 1/H_total: 低总熵 = 高秩序 = 高自驱
        - I(debt;finding): 债务-发现耦合 = 转化能力
        - 1/σ_gen: 低熵产生 = 高效能
        """
        profile = self.entropy_profile(state)
        df_map = self.compute_debt_finding_entropy_map(state)
        
        H_total = profile.total_entropy
        mi = df_map["mutual_information"]
        coupling = df_map["coupling_coefficient"]
        
        # 历史平均熵产生
        sigma_avg = 0.1
        if len(self.flow_history) > 0:
            sigma_avg = np.mean([f.entropy_production for f in self.flow_history])
        
        alpha, beta, gamma = 0.4, 0.4, 0.2
        
        sdi = (alpha * (1.0 / (H_total + self.epsilon)) +
               beta * mi +
               gamma * (1.0 / (sigma_avg + self.epsilon)))
        
        # 归一化到0-1
        sdi_norm = min(1.0, sdi / 5.0)
        
        return {
            "self_drive_index": sdi,
            "self_drive_index_normalized": sdi_norm,
            "total_entropy": H_total,
            "debt_finding_coupling": coupling,
            "entropy_production_avg": sigma_avg,
            "interpretation": (
                "high" if sdi_norm > 0.7 else
                "medium" if sdi_norm > 0.4 else "low"
            ),
        }
    
    def compute_system_temperature(self, state: SystemState) -> float:
        """
        计算系统"温度"（类比热力学温度）
        
        T_system = dE/dS  （能量对熵的导数）
        
        在信息论中，可以用 1/H 作为"秩序温度"的代理:
        - 高H（高熵）= 高温 = 高混乱
        - 低H（低熵）= 低温 = 高秩序
        """
        profile = self.entropy_profile(state)
        # 温度 = 总熵的倒数（归一化）
        T = profile.total_entropy / np.log2(len(self.LINES))
        return float(T)


# ============================================================================
# 3. 系统状态生成器（模拟OMNI-HUB运行）
# ============================================================================

class OMNIHUBSimulator:
    """OMNI-HUB系统模拟器，用于生成实验数据"""
    
    def __init__(self, field_entropy: FieldEntropy, seed: int = 42):
        self.fe = field_entropy
        self.rng = np.random.RandomState(seed)
        self.time = 0.0
        
    def generate_state(self, scenario: str = "normal") -> SystemState:
        """
        生成系统状态
        
        Scenarios:
        - normal: 正常运行
        - high_debt: 高债务状态
        - high_finding: 高发现状态
        - imbalance: 债务-发现失衡
        - consensus: 高共识状态
        """
        n = self.fe.N_LINES
        
        if scenario == "normal":
            health = 0.9 + 0.08 * self.rng.randn(n)
            queue = 5 + 3 * self.rng.randn(n)
            debt = 2 + 2 * self.rng.exponential(1, n)
            finding = 3 + 2 * self.rng.exponential(1, n)
            consensus = 0.8 + 0.15 * self.rng.randn(n)
            fuel = 50 + 20 * self.rng.randn(n)
        elif scenario == "high_debt":
            health = 0.7 + 0.1 * self.rng.randn(n)
            queue = 15 + 5 * self.rng.randn(n)
            debt = 20 + 5 * self.rng.exponential(1, n)
            finding = 1 + self.rng.exponential(0.5, n)
            consensus = 0.5 + 0.2 * self.rng.randn(n)
            fuel = 20 + 10 * self.rng.randn(n)
        elif scenario == "high_finding":
            health = 0.85 + 0.1 * self.rng.randn(n)
            queue = 3 + 2 * self.rng.randn(n)
            debt = 1 + self.rng.exponential(0.5, n)
            finding = 15 + 5 * self.rng.exponential(1, n)
            consensus = 0.6 + 0.15 * self.rng.randn(n)
            fuel = 80 + 15 * self.rng.randn(n)
        elif scenario == "imbalance":
            health = 0.75 + 0.15 * self.rng.randn(n)
            queue = 10 + 4 * self.rng.randn(n)
            debt = 15 + 3 * self.rng.exponential(1, n)
            finding = 2 + self.rng.exponential(0.3, n)
            consensus = 0.4 + 0.2 * self.rng.randn(n)
            fuel = 30 + 15 * self.rng.randn(n)
        elif scenario == "consensus":
            health = 0.95 + 0.03 * self.rng.randn(n)
            queue = 4 + 1.5 * self.rng.randn(n)
            debt = 1 + 0.5 * self.rng.exponential(1, n)
            finding = 4 + 1.5 * self.rng.exponential(1, n)
            consensus = 0.95 + 0.03 * self.rng.randn(n)
            fuel = 90 + 5 * self.rng.randn(n)
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        # 裁剪到合理范围
        health = np.clip(health, 0.0, 1.0)
        queue = np.clip(queue, 0, None)
        debt = np.clip(debt, 0, None)
        finding = np.clip(finding, 0, None)
        consensus = np.clip(consensus, 0.0, 1.0)
        fuel = np.clip(fuel, 0, None)
        
        # 消息流矩阵（11x11）
        message_flow = self.rng.poisson(5, (n, n)).astype(float)
        np.fill_diagonal(message_flow, 0)
        
        # 拓扑邻接矩阵（11x11，对称）
        topology = self.rng.binomial(1, 0.6, (n, n)).astype(float)
        topology = np.maximum(topology, topology.T)  # 对称化
        np.fill_diagonal(topology, 0)
        
        self.time += 1.0
        
        return SystemState(
            timestamp=self.time,
            line_health=health,
            queue_depth=queue,
            debt_dist=debt,
            finding_dist=finding,
            consensus_vec=consensus,
            fuel_level=fuel,
            message_flow=message_flow,
            topology_adj=topology,
        )
    
    def generate_spin_sequence(self, n_steps: int = 50) -> List[SystemState]:
        """生成spin()迭代序列，模拟自驱引擎运行"""
        states = []
        for i in range(n_steps):
            # 模拟自驱过程：债务逐渐清理，发现逐渐增加
            if i == 0:
                state = self.generate_state("high_debt")
            else:
                prev = states[-1]
                # spin()效果：债务减少，发现增加，健康度提升
                new_debt = prev.debt_dist * 0.95 + self.rng.exponential(0.5, self.fe.N_LINES)
                new_finding = prev.finding_dist * 1.02 + self.rng.exponential(0.3, self.fe.N_LINES)
                new_health = np.clip(prev.line_health + 0.005 + 0.01 * self.rng.randn(self.fe.N_LINES), 0, 1)
                new_consensus = np.clip(prev.consensus_vec + 0.002 + 0.005 * self.rng.randn(self.fe.N_LINES), 0, 1)
                
                state = SystemState(
                    timestamp=prev.timestamp + 1.0,
                    line_health=new_health,
                    queue_depth=np.clip(prev.queue_depth + self.rng.poisson(1, self.fe.N_LINES) - 0.5, 0, None),
                    debt_dist=np.clip(new_debt, 0, None),
                    finding_dist=np.clip(new_finding, 0, None),
                    consensus_vec=new_consensus,
                    fuel_level=np.clip(prev.fuel_level + self.rng.randn(self.fe.N_LINES) * 2, 0, None),
                    message_flow=self.rng.poisson(5 + i//10, (self.fe.N_LINES, self.fe.N_LINES)).astype(float),
                    topology_adj=prev.topology_adj,
                )
            states.append(state)
        return states


# ============================================================================
# 4. 实验框架
# ============================================================================

class EntropyExperiment:
    """场熵实验框架"""
    
    def __init__(self):
        self.fe = FieldEntropy()
        self.sim = OMNIHUBSimulator(self.fe)
        self.results: Dict[str, Any] = {}
    
    def run_experiment_1_basic_entropy(self) -> Dict[str, Any]:
        """
        实验1: 基础场熵计算
        验证各维度熵的计算正确性
        """
        logger.info("=" * 70)
        logger.info("实验1: 基础场熵计算")
        logger.info("=" * 70)
        
        results = {}
        scenarios = ["normal", "high_debt", "high_finding", "imbalance", "consensus"]
        
        for scenario in scenarios:
            state = self.sim.generate_state(scenario)
            profile = self.fe.entropy_profile(state)
            
            results[scenario] = {
                "profile": profile.to_dict(),
                "entropy_values": {k.value: v for k, v in profile.dimensions.items()},
            }
            
            logger.info(f"\n场景: {scenario}")
            logger.info(f"  总熵: {profile.total_entropy:.4f}")
            for dim, val in profile.dimensions.items():
                logger.info(f"  {dim.value}: {val:.4f}")
        
        self.results["experiment_1"] = results
        return results
    
    def run_experiment_2_debt_finding_map(self) -> Dict[str, Any]:
        """
        实验2: debt_generation ↔ FINDING 熵映射
        验证债务与发现之间的熵关系
        """
        logger.info("\n" + "=" * 70)
        logger.info("实验2: Debt ↔ Finding 熵映射关系")
        logger.info("=" * 70)
        
        results = {}
        scenarios = ["normal", "high_debt", "high_finding", "imbalance", "consensus"]
        
        for scenario in scenarios:
            state = self.sim.generate_state(scenario)
            df_map = self.fe.compute_debt_finding_entropy_map(state)
            results[scenario] = df_map
            
            logger.info(f"\n场景: {scenario}")
            for k, v in df_map.items():
                if isinstance(v, float):
                    logger.info(f"  {k}: {v:.4f}")
                else:
                    logger.info(f"  {k}: {v}")
        
        self.results["experiment_2"] = results
        return results
    
    def run_experiment_3_entropy_flow(self) -> Dict[str, Any]:
        """
        实验3: 层-网-塔熵流
        验证熵在三层架构中的流动
        """
        logger.info("\n" + "=" * 70)
        logger.info("实验3: 层-网-塔 熵流模型")
        logger.info("=" * 70)
        
        results = []
        
        # 生成10个连续状态，模拟系统运行
        states = [self.sim.generate_state("normal") for _ in range(10)]
        
        for i, state in enumerate(states):
            # 定义三层状态
            # 层(SITopology): 节点度分布
            layer = np.sum(state.topology_adj, axis=1)  # 度分布
            
            # 网(ReliableMessaging): 消息流量分布
            network = np.sum(state.message_flow, axis=1)  # 出流量
            
            # 塔(OctaveScan): 扫描强度分布
            tower = state.finding_dist * state.consensus_vec  # 发现×共识
            
            flow = self.fe.entropy_flow(layer, network, tower)
            results.append(flow.to_dict())
            
            logger.info(f"\n时间步 {i}:")
            logger.info(f"  层熵: {flow.layer_entropy:.4f}")
            logger.info(f"  网熵: {flow.network_entropy:.4f}")
            logger.info(f"  塔熵: {flow.tower_entropy:.4f}")
            logger.info(f"  层→网流: {flow.flow_layer_to_network:.4f}")
            logger.info(f"  网→塔流: {flow.flow_network_to_tower:.4f}")
            logger.info(f"  熵产生: {flow.entropy_production:.4f}")
            logger.info(f"  守恒: {flow.is_conserved}")
            if flow.entropy_reduction_detected:
                logger.info(f"  ⚠ 熵减检测: {flow.reduction_locations}")
        
        self.results["experiment_3"] = results
        return {"flows": results}
    
    def run_experiment_4_spin_dynamics(self) -> Dict[str, Any]:
        """
        实验4: 自驱引擎spin()动态
        验证自驱过程中熵的变化趋势
        """
        logger.info("\n" + "=" * 70)
        logger.info("实验4: 自驱引擎 spin() 动态分析")
        logger.info("=" * 70)
        
        # 重置模拟器
        self.sim = OMNIHUBSimulator(self.fe, seed=123)
        states = self.sim.generate_spin_sequence(n_steps=50)
        
        profiles = []
        df_maps = []
        sdi_values = []
        temperatures = []
        
        for state in states:
            profile = self.fe.entropy_profile(state)
            df_map = self.fe.compute_debt_finding_entropy_map(state)
            sdi = self.fe.compute_self_drive_index(state)
            temp = self.fe.compute_system_temperature(state)
            
            profiles.append(profile.to_dict())
            df_maps.append(df_map)
            sdi_values.append(sdi)
            temperatures.append(temp)
        
        # 分析趋势
        total_entropies = [p["total_entropy"] for p in profiles]
        debt_entropies = [p["dimensions"]["debt"] for p in profiles]
        finding_entropies = [p["dimensions"]["finding"] for p in profiles]
        
        logger.info(f"\n初始总熵: {total_entropies[0]:.4f}")
        logger.info(f"最终总熵: {total_entropies[-1]:.4f}")
        logger.info(f"总熵变化: {total_entropies[-1] - total_entropies[0]:+.4f}")
        logger.info(f"平均总熵: {np.mean(total_entropies):.4f}")
        logger.info(f"总熵标准差: {np.std(total_entropies):.4f}")
        
        logger.info(f"\n初始债务熵: {debt_entropies[0]:.4f}")
        logger.info(f"最终债务熵: {debt_entropies[-1]:.4f}")
        logger.info(f"债务熵变化: {debt_entropies[-1] - debt_entropies[0]:+.4f}")
        
        logger.info(f"\n初始发现熵: {finding_entropies[0]:.4f}")
        logger.info(f"最终发现熵: {finding_entropies[-1]:.4f}")
        logger.info(f"发现熵变化: {finding_entropies[-1] - finding_entropies[0]:+.4f}")
        
        logger.info(f"\n自驱指数变化:")
        logger.info(f"  初始SDI: {sdi_values[0]['self_drive_index_normalized']:.4f}")
        logger.info(f"  最终SDI: {sdi_values[-1]['self_drive_index_normalized']:.4f}")
        logger.info(f"  平均SDI: {np.mean([s['self_drive_index_normalized'] for s in sdi_values]):.4f}")
        
        logger.info(f"\n系统温度变化:")
        logger.info(f"  初始温度: {temperatures[0]:.4f}")
        logger.info(f"  最终温度: {temperatures[-1]:.4f}")
        logger.info(f"  平均温度: {np.mean(temperatures):.4f}")
        
        results = {
            "profiles": profiles,
            "df_maps": df_maps,
            "sdi_values": sdi_values,
            "temperatures": temperatures,
            "trends": {
                "total_entropy_start": total_entropies[0],
                "total_entropy_end": total_entropies[-1],
                "debt_entropy_delta": debt_entropies[-1] - debt_entropies[0],
                "finding_entropy_delta": finding_entropies[-1] - finding_entropies[0],
            }
        }
        
        self.results["experiment_4"] = results
        return results
    
    def run_experiment_5_entropy_law(self) -> Dict[str, Any]:
        """
        实验5: 熵增定律验证
        验证系统运行时总熵的变化趋势
        """
        logger.info("\n" + "=" * 70)
        logger.info("实验5: 熵增定律验证")
        logger.info("=" * 70)
        
        # 运行多轮spin，统计总熵变化
        n_runs = 20
        entropy_changes = []
        
        for run in range(n_runs):
            self.fe = FieldEntropy()  # 重置
            self.sim = OMNIHUBSimulator(self.fe, seed=100 + run)
            states = self.sim.generate_spin_sequence(n_steps=30)
            
            # 计算首尾总熵
            profile_start = self.fe.entropy_profile(states[0])
            self.fe = FieldEntropy()  # 重置避免历史影响
            self.sim = OMNIHUBSimulator(self.fe, seed=100 + run)
            states = self.sim.generate_spin_sequence(n_steps=30)
            profile_end = self.fe.entropy_profile(states[-1])
            
            delta = profile_end.total_entropy - profile_start.total_entropy
            entropy_changes.append(delta)
        
        entropy_changes = np.array(entropy_changes)
        
        logger.info(f"\n运行 {n_runs} 次spin序列（每次30步）:")
        logger.info(f"  平均熵变: {np.mean(entropy_changes):+.4f}")
        logger.info(f"  熵变标准差: {np.std(entropy_changes):.4f}")
        logger.info(f"  熵增次数: {np.sum(entropy_changes > 0)} / {n_runs}")
        logger.info(f"  熵减次数: {np.sum(entropy_changes < 0)} / {n_runs}")
        logger.info(f"  最大熵增: {np.max(entropy_changes):+.4f}")
        logger.info(f"  最大熵减: {np.min(entropy_changes):+.4f}")
        
        results = {
            "entropy_changes": entropy_changes.tolist(),
            "mean_change": float(np.mean(entropy_changes)),
            "std_change": float(np.std(entropy_changes)),
            "increase_count": int(np.sum(entropy_changes > 0)),
            "decrease_count": int(np.sum(entropy_changes < 0)),
            "entropy_law_holds": bool(np.mean(entropy_changes) >= -0.1),
        }
        
        self.results["experiment_5"] = results
        return results
    
    def run_all_experiments(self) -> Dict[str, Any]:
        """运行全部实验"""
        logger.info("\n" + "=" * 70)
        logger.info("OMNI-HUB 场熵框架 实验验证")
        logger.info("=" * 70)
        
        self.run_experiment_1_basic_entropy()
        self.run_experiment_2_debt_finding_map()
        self.run_experiment_3_entropy_flow()
        self.run_experiment_4_spin_dynamics()
        self.run_experiment_5_entropy_law()
        
        return self.results
    
    def save_results(self, filepath: str):
        """保存实验结果到JSON"""
    with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
    logger.info(f"\n实验结果已保存到: {filepath}")


# ============================================================================
# 5. 主入口
# ============================================================================
"""
OMNI-HUB v11.0 — field_entropy
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""

if __name__ == "__main__":
    # 运行完整实验
    experiment = EntropyExperiment()
    results = experiment.run_all_experiments()
    
    # 保存结果
    experiment.save_results("/mnt/agents/output/OMNI-HUB/core/entropy_experiment_results.json")
    
    print("\n" + "=" * 70)
    print("实验完成！")
    print("=" * 70)
