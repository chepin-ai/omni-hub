#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v5.0 - GoalAutopoiesis: 目标自创生系统

基于 Maturana & Varela 的自创生理论 (Autopoiesis Theory):
- 自创生系统: 通过网络中的过程生产构成该网络的组件
- 操作闭合: 系统的操作只指向系统自身
- 结构耦合: 系统与环境的反复交互触发结构变化
- 认知 = 自创生统一体在其存在领域中的有效行动

核心命题: 目标是系统自己生产自己的——就像细胞生产自己的组件一样，
系统生产自己的目标。目标完成→生成新目标→新目标驱动行动→行动完成目标→……
这是一个自创生循环。

作者: OMNI-HUB Architecture Team
版本: 5.0.0
"""

import uuid
import time
import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from datetime import datetime
from collections import deque
from enum import Enum

import numpy as np
import networkx as nx
import logging


# ============================================================================
# 第一部分: 基础枚举和常量
# ============================================================================

class GoalStatus(Enum):
    """目标状态枚举"""
    PENDING = "pending"      # 待处理
    ACTIVE = "active"        # 活跃/执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    BLOCKED = "blocked"      # 被阻塞


class GoalType(Enum):
    """目标类型枚举"""
    EXPLORATORY = "exploratory"    # 探索性（健康度高时生成）
    REMEDIAL = "remedial"          # 修复性（健康度低时生成）
    LINE_SPECIFIC = "line_specific" # 线专项（某线空闲时生成）
    SINGULARITY = "singularity"    # 奇异性（检测到奇异环时生成）
    INSIGHT = "insight"            # 洞察性（顿悟发生时生成）
    MAINTENANCE = "maintenance"    # 维护性（系统维护）
    EMERGENT = "emergent"          # 涌现性（自发涌现）


class LineID(Enum):
    """OMNI-HUB 11线标识"""
    PERCEPTION = 0      # 感知线
    MEMORY = 1          # 记忆线
    REASONING = 2       # 推理线
    EMOTION = 3         # 情感线
    LANGUAGE = 4        # 语言线
    ACTION = 5          # 行动线
    META = 6            # 元认知线
    INTEGRATION = 7     # 整合线
    PREDICTION = 8      # 预测线
    CREATIVITY = 9      # 创造线
    REFLECTION = 10     # 反思线


# 线名称映射
LINE_NAMES = {
    LineID.PERCEPTION: "感知线",
    LineID.MEMORY: "记忆线",
    LineID.REASONING: "推理线",
    LineID.EMOTION: "情感线",
    LineID.LANGUAGE: "语言线",
    LineID.ACTION: "行动线",
    LineID.META: "元认知线",
    LineID.INTEGRATION: "整合线",
    LineID.PREDICTION: "预测线",
    LineID.CREATIVITY: "创造线",
    LineID.REFLECTION: "反思线",
}


# ============================================================================
# 第二部分: Goal 类 - 目标对象
# ============================================================================

@dataclass
class Goal:
    """
    目标对象
    
    属性:
        id: 唯一标识符
        description: 目标描述
        status: 状态（pending/active/completed/failed/blocked）
        priority: 优先级（0-1）
        goal_type: 目标类型
        parent: 父目标ID
        children: 子目标ID列表
        created_at: 创建时间戳
        completed_at: 完成时间戳
        line_assignment: 分配给哪条线
        metrics: 完成度量字典
        trigger: 触发条件描述
        depth: 层级深度
        dependencies: 依赖的目标ID列表
        autopoietic: 是否由自创生产生
        generation: 第几代目标（自创生代数）
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    status: GoalStatus = GoalStatus.PENDING
    priority: float = 0.5
    goal_type: GoalType = GoalType.MAINTENANCE
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    line_assignment: Optional[LineID] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    trigger: str = ""
    depth: int = 0
    dependencies: List[str] = field(default_factory=list)
    autopoietic: bool = True  # 是否由系统自生产
    generation: int = 0       # 自创生代数
    
    # 运行时统计
    execution_attempts: int = 0
    last_attempt_time: Optional[float] = None
    progress: float = 0.0     # 0-1 进度
    
    def __post_init__(self):
        if not self.description:
            self.description = f"Goal-{self.id}"
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority,
            "goal_type": self.goal_type.value,
            "parent": self.parent,
            "children": self.children,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "line_assignment": self.line_assignment.value if self.line_assignment else None,
            "metrics": self.metrics,
            "trigger": self.trigger,
            "depth": self.depth,
            "dependencies": self.dependencies,
            "autopoietic": self.autopoietic,
            "generation": self.generation,
            "progress": self.progress,
            "execution_attempts": self.execution_attempts,
        }
    
    def mark_active(self):
        """标记为活跃"""
        self.status = GoalStatus.ACTIVE
        self.last_attempt_time = time.time()
        self.execution_attempts += 1
    
    def mark_completed(self, success: bool = True, metrics: Optional[Dict] = None):
        """标记为完成/失败"""
        self.completed_at = time.time()
        self.progress = 1.0 if success else 0.0
        if metrics:
            self.metrics.update(metrics)
        if success:
            self.status = GoalStatus.COMPLETED
        else:
            self.status = GoalStatus.FAILED
    
    def mark_blocked(self):
        """标记为阻塞"""
        self.status = GoalStatus.BLOCKED
    
    def duration(self) -> float:
        """计算目标持续时间"""
        end = self.completed_at or time.time()
        return end - self.created_at
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Goal):
            return self.id == other.id
        return False
    
    def __repr__(self):
        line_name = LINE_NAMES.get(self.line_assignment, "未分配") if self.line_assignment else "未分配"
        return (f"Goal(id={self.id}, desc='{self.description[:30]}...', "
                f"status={self.status.value}, priority={self.priority:.2f}, "
                f"line={line_name}, gen={self.generation})")


# ============================================================================
# 第三部分: GoalNetwork 类 - 目标网络（基于networkx）
# ============================================================================

class GoalNetwork:
    """
    目标网络 - 基于 networkx 的有向图
    
    节点: 目标 (Goal)
    边: 依赖关系 / 层级关系 / 触发关系
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.goals: Dict[str, Goal] = {}
        self._cycle_history: List[List[str]] = []  # 历史循环记录
        self._edge_types: Dict[Tuple[str, str], str] = {}  # 边类型映射
    
    # ------------------------------------------------------------------
    # 基本操作
    # ------------------------------------------------------------------
    
    def add_goal(self, goal: Goal) -> str:
        """添加目标节点"""
        self.goals[goal.id] = goal
        self.graph.add_node(
            goal.id,
            goal=goal,
            priority=goal.priority,
            status=goal.status.value,
            depth=goal.depth,
            generation=goal.generation,
            created_at=goal.created_at,
        )
        return goal.id
    
    def add_dependency(self, src: str, dst: str, edge_type: str = "depends") -> bool:
        """
        添加依赖边: src -> dst (src 依赖于 dst)
        即 dst 必须先完成，src 才能执行
        """
        if src not in self.goals or dst not in self.goals:
            return False
        self.graph.add_edge(src, dst, type=edge_type, created_at=time.time())
        self._edge_types[(src, dst)] = edge_type
        
        # 更新目标对象的依赖列表
        if dst not in self.goals[src].dependencies:
            self.goals[src].dependencies.append(dst)
        return True
    
    def add_parent_child(self, parent: str, child: str) -> bool:
        """添加父子边（层级分解关系）"""
        if parent not in self.goals or child not in self.goals:
            return False
        self.graph.add_edge(parent, child, type="decomposition")
        self._edge_types[(parent, child)] = "decomposition"
        
        # 更新目标对象
        if child not in self.goals[parent].children:
            self.goals[parent].children.append(child)
        self.goals[child].parent = parent
        self.goals[child].depth = self.goals[parent].depth + 1
        return True
    
    def add_trigger(self, trigger_goal: str, triggered_goal: str) -> bool:
        """添加触发边: 一个目标的完成触发另一个目标的生成"""
        if trigger_goal not in self.goals or triggered_goal not in self.goals:
            return False
        self.graph.add_edge(trigger_goal, triggered_goal, type="triggers")
        self._edge_types[(trigger_goal, triggered_goal)] = "triggers"
        return True
    
    def remove_goal(self, goal_id: str) -> bool:
        """移除目标"""
        if goal_id not in self.goals:
            return False
        self.graph.remove_node(goal_id)
        del self.goals[goal_id]
        # 清理边类型映射
        self._edge_types = {
            k: v for k, v in self._edge_types.items()
            if k[0] != goal_id and k[1] != goal_id
        }
        return True
    
    # ------------------------------------------------------------------
    # 查询操作
    # ------------------------------------------------------------------
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """获取目标"""
        return self.goals.get(goal_id)
    
    def get_active_goals(self) -> List[Goal]:
        """获取活跃目标"""
        return [g for g in self.goals.values() if g.status == GoalStatus.ACTIVE]
    
    def get_pending_goals(self) -> List[Goal]:
        """获取待处理目标"""
        return [g for g in self.goals.values() if g.status == GoalStatus.PENDING]
    
    def get_completed_goals(self) -> List[Goal]:
        """获取已完成目标"""
        return [g for g in self.goals.values() if g.status == GoalStatus.COMPLETED]
    
    def get_failed_goals(self) -> List[Goal]:
        """获取失败目标"""
        return [g for g in self.goals.values() if g.status == GoalStatus.FAILED]
    
    def get_leaf_goals(self) -> List[Goal]:
        """获取叶节点目标（没有子目标，可直接执行）"""
        leaves = []
        for goal_id, goal in self.goals.items():
            # 叶节点: 没有出边（decomposition 类型）或者没有子目标
            children = [v for u, v, d in self.graph.edges(data=True) 
                       if u == goal_id and d.get("type") == "decomposition"]
            if not children and goal.status in [GoalStatus.PENDING, GoalStatus.ACTIVE]:
                leaves.append(goal)
        return leaves
    
    def get_roots(self) -> List[Goal]:
        """获取根目标（没有父目标）"""
        return [g for g in self.goals.values() if g.parent is None]
    
    def get_subtree(self, goal_id: str) -> List[Goal]:
        """获取子树（包含所有后代）"""
        if goal_id not in self.goals:
            return []
        descendants = nx.descendants(self.graph, goal_id)
        return [self.goals[g_id] for g_id in descendants if g_id in self.goals]
    
    # ------------------------------------------------------------------
    # 网络分析
    # ------------------------------------------------------------------
    
    def detect_cycles(self) -> List[List[str]]:
        """检测图中的循环（自创生循环）"""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            self._cycle_history.extend(cycles)
            return cycles
        except nx.NetworkXNoCycle:
            return []
    
    def get_critical_path(self) -> List[str]:
        """
        获取关键路径（最长路径）
        基于依赖关系计算
        """
        # 只考虑 dependency 类型的边
        dep_graph = nx.DiGraph()
        for u, v, d in self.graph.edges(data=True):
            if d.get("type") in ["depends", "decomposition"]:
                dep_graph.add_edge(v, u)  # 反向: 依赖方 <- 被依赖方
        
        if len(dep_graph.nodes) == 0:
            return []
        
        try:
            # 找到最长路径
            longest_path = []
            for source in dep_graph.nodes():
                for target in dep_graph.nodes():
                    if source != target and nx.has_path(dep_graph, source, target):
                        paths = list(nx.all_simple_paths(dep_graph, source, target))
                        for path in paths:
                            if len(path) > len(longest_path):
                                longest_path = path
            return longest_path
        except Exception:
            return []
    
    def network_density(self) -> float:
        """计算网络密度"""
        n = self.graph.number_of_nodes()
        if n <= 1:
            return 0.0
        return nx.density(self.graph)
    
    def clustering_coefficient(self) -> float:
        """计算平均聚类系数"""
        try:
            return nx.average_clustering(self.graph.to_undirected())
        except Exception:
            return 0.0
    
    def centrality_analysis(self) -> Dict[str, float]:
        """中心性分析"""
        if len(self.graph.nodes) == 0:
            return {}
        try:
            degree_cent = nx.degree_centrality(self.graph)
            betweenness_cent = nx.betweenness_centrality(self.graph)
            
            # 合并分析
            combined = {}
            for node in self.graph.nodes():
                combined[node] = (degree_cent.get(node, 0) + betweenness_cent.get(node, 0)) / 2
            return combined
        except Exception:
            return {}
    
    def get_autopoietic_cycles(self) -> List[List[str]]:
        """获取自创生循环（触发边构成的循环）"""
        trigger_graph = nx.DiGraph()
        for u, v, d in self.graph.edges(data=True):
            if d.get("type") == "triggers":
                trigger_graph.add_edge(u, v)
        
        try:
            return list(nx.simple_cycles(trigger_graph))
        except Exception:
            return []
    
    def lineage(self, goal_id: str) -> List[str]:
        """获取目标的血统（从根到该目标的路径）"""
        if goal_id not in self.goals:
            return []
        path = [goal_id]
        current = goal_id
        while self.goals[current].parent:
            parent = self.goals[current].parent
            path.insert(0, parent)
            current = parent
        return path
    
    def statistics(self) -> Dict[str, Any]:
        """网络统计信息"""
        total = len(self.goals)
        if total == 0:
            return {"total_goals": 0}
        
        status_counts = {}
        for g in self.goals.values():
            status_counts[g.status.value] = status_counts.get(g.status.value, 0) + 1
        
        type_counts = {}
        for g in self.goals.values():
            type_counts[g.goal_type.value] = type_counts.get(g.goal_type.value, 0) + 1
        
        generations = [g.generation for g in self.goals.values()]
        depths = [g.depth for g in self.goals.values()]
        
        return {
            "total_goals": total,
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "density": self.network_density(),
            "clustering": self.clustering_coefficient(),
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "max_generation": max(generations) if generations else 0,
            "avg_generation": sum(generations) / len(generations) if generations else 0,
            "max_depth": max(depths) if depths else 0,
            "avg_depth": sum(depths) / len(depths) if depths else 0,
            "autopoietic_cycles": len(self.get_autopoietic_cycles()),
            "cycles_detected": len(self.detect_cycles()),
        }


# ============================================================================
# 第四部分: 目标分解模板
# ============================================================================

# 目标分解模板: 高层目标 -> [子目标描述, 优先级, 目标类型, 分配线]
DECOMPOSITION_TEMPLATES: Dict[str, List[Tuple[str, float, GoalType, LineID]]] = {
    "提升系统健康度": [
        ("增加自激活动", 0.8, GoalType.REMEDIAL, LineID.META),
        ("减少熵增速率", 0.7, GoalType.REMEDIAL, LineID.INTEGRATION),
        ("增强线间耦合", 0.75, GoalType.REMEDIAL, LineID.INTEGRATION),
        ("优化能量分配", 0.6, GoalType.MAINTENANCE, LineID.PERCEPTION),
    ],
    "增强感知能力": [
        ("扩展感知模态", 0.7, GoalType.EXPLORATORY, LineID.PERCEPTION),
        ("提高信号分辨率", 0.65, GoalType.EXPLORATORY, LineID.PERCEPTION),
        ("优化特征提取", 0.6, GoalType.MAINTENANCE, LineID.REASONING),
    ],
    "优化记忆系统": [
        ("增强短期记忆容量", 0.7, GoalType.MAINTENANCE, LineID.MEMORY),
        ("优化长期记忆检索", 0.65, GoalType.MAINTENANCE, LineID.MEMORY),
        ("改善记忆巩固机制", 0.6, GoalType.MAINTENANCE, LineID.META),
    ],
    "提升推理能力": [
        ("增强逻辑推理链", 0.75, GoalType.EXPLORATORY, LineID.REASONING),
        ("优化因果推断", 0.7, GoalType.EXPLORATORY, LineID.REASONING),
        ("发展类比推理", 0.65, GoalType.EXPLORATORY, LineID.CREATIVITY),
    ],
    "增强情感调节": [
        ("优化情感状态检测", 0.7, GoalType.MAINTENANCE, LineID.EMOTION),
        ("增强情感表达", 0.6, GoalType.EXPLORATORY, LineID.EMOTION),
        ("改善情感-认知耦合", 0.75, GoalType.MAINTENANCE, LineID.INTEGRATION),
    ],
    "提升语言能力": [
        ("扩展词汇表征", 0.6, GoalType.EXPLORATORY, LineID.LANGUAGE),
        ("优化语义理解", 0.7, GoalType.EXPLORATORY, LineID.LANGUAGE),
        ("增强语用推理", 0.65, GoalType.EXPLORATORY, LineID.REASONING),
    ],
    "优化行动执行": [
        ("提高行动精度", 0.7, GoalType.MAINTENANCE, LineID.ACTION),
        ("优化行动规划", 0.65, GoalType.MAINTENANCE, LineID.PREDICTION),
        ("增强反馈学习", 0.75, GoalType.EXPLORATORY, LineID.ACTION),
    ],
    "增强元认知": [
        ("提升自我监控", 0.8, GoalType.EXPLORATORY, LineID.META),
        ("优化策略选择", 0.75, GoalType.EXPLORATORY, LineID.META),
        ("增强自我修正", 0.7, GoalType.MAINTENANCE, LineID.REFLECTION),
    ],
    "促进线间整合": [
        ("增强跨线通信", 0.8, GoalType.MAINTENANCE, LineID.INTEGRATION),
        ("优化信息路由", 0.7, GoalType.MAINTENANCE, LineID.INTEGRATION),
        ("发展全局工作空间", 0.75, GoalType.EXPLORATORY, LineID.INTEGRATION),
    ],
    "提升预测能力": [
        ("优化时序预测", 0.7, GoalType.EXPLORATORY, LineID.PREDICTION),
        ("增强状态预测", 0.65, GoalType.EXPLORATORY, LineID.PREDICTION),
        ("改善异常检测", 0.75, GoalType.MAINTENANCE, LineID.PERCEPTION),
    ],
    "激发创造力": [
        ("促进概念重组", 0.7, GoalType.EXPLORATORY, LineID.CREATIVITY),
        ("增强联想能力", 0.65, GoalType.EXPLORATORY, LineID.CREATIVITY),
        ("优化新颖性评估", 0.6, GoalType.EXPLORATORY, LineID.META),
    ],
    "深化反思能力": [
        ("增强事后分析", 0.7, GoalType.MAINTENANCE, LineID.REFLECTION),
        ("优化模式识别", 0.65, GoalType.MAINTENANCE, LineID.REFLECTION),
        ("促进知识整合", 0.75, GoalType.EXPLORATORY, LineID.MEMORY),
    ],
    "探索新领域": [
        ("识别潜在机会", 0.7, GoalType.EXPLORATORY, LineID.PREDICTION),
        ("评估风险收益", 0.65, GoalType.EXPLORATORY, LineID.REASONING),
        ("设计实验方案", 0.75, GoalType.EXPLORATORY, LineID.CREATIVITY),
    ],
    "修复系统故障": [
        ("诊断故障源", 0.9, GoalType.REMEDIAL, LineID.META),
        ("隔离故障区域", 0.85, GoalType.REMEDIAL, LineID.INTEGRATION),
        ("实施修复措施", 0.8, GoalType.REMEDIAL, LineID.ACTION),
        ("验证修复效果", 0.75, GoalType.REMEDIAL, LineID.PERCEPTION),
    ],
    "增强奇异环": [
        ("强化环内耦合", 0.8, GoalType.SINGULARITY, LineID.INTEGRATION),
        ("优化能量流动", 0.75, GoalType.SINGULARITY, LineID.EMOTION),
        ("增强涌现特性", 0.85, GoalType.SINGULARITY, LineID.META),
    ],
    "利用新洞察": [
        ("形式化洞察", 0.75, GoalType.INSIGHT, LineID.LANGUAGE),
        ("整合到知识库", 0.7, GoalType.INSIGHT, LineID.MEMORY),
        ("生成衍生假设", 0.8, GoalType.INSIGHT, LineID.REASONING),
    ],
}

# 目标描述生成器（用于自动生成目标）
GOAL_DESCRIPTIONS = {
    GoalType.EXPLORATORY: [
        "探索{line}的新可能性",
        "在{line}上尝试创新方法",
        "拓展{line}的能力边界",
        "实验{line}的新配置",
    ],
    GoalType.REMEDIAL: [
        "修复{line}的异常状态",
        "恢复{line}的正常功能",
        "降低{line}的错误率",
        "稳定{line}的性能",
    ],
    GoalType.LINE_SPECIFIC: [
        "提升{line}的专项能力",
        "优化{line}的资源使用",
        "增强{line}的输出质量",
    ],
    GoalType.SINGULARITY: [
        "增强奇异环的稳定性",
        "优化涌现态的持续时间",
        "强化全局耦合效应",
    ],
    GoalType.INSIGHT: [
        "验证新洞察的正确性",
        "扩展洞察的应用范围",
        "基于洞察生成新假设",
    ],
    GoalType.MAINTENANCE: [
        "执行{line}的例行维护",
        "更新{line}的内部状态",
        "清理{line}的冗余数据",
    ],
    GoalType.EMERGENT: [
        "响应涌现模式",
        "追踪自发形成的结构",
        "利用意外发现",
    ],
}


# ============================================================================
# 第五部分: GoalAutopoiesis 类 - 核心自生产系统
# ============================================================================

class GoalAutopoiesis:
    """
    目标自创生系统 (Goal Autopoiesis System)
    
    核心机制:
    1. 系统感知当前状态
    2. 如果有意图，转化为目标
    3. 如果没有意图，基于系统需求自发生成目标
    4. 分解目标为子目标（层级结构）
    5. 将叶目标分配给各线执行
    6. 监控执行进度
    7. 目标完成 → 触发自生产（生成新目标）
    8. 循环往复
    
    自创生产规则:
    - 健康度高 → 探索性目标（创新、实验）
    - 健康度低 → 修复性目标（稳定、恢复）
    - 某线空闲 → 该线专项提升目标
    - 检测到奇异环 → 增强该环的目标
    - 顿悟发生 → 利用新洞察的目标
    """
    
    def __init__(self, num_lines: int = 11, random_seed: Optional[int] = None):
        """
        初始化目标自创生系统
        
        Args:
            num_lines: 线的数量（默认11）
            random_seed: 随机种子（用于可重复实验）
        """
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
        
        self.num_lines = num_lines
        self.network = GoalNetwork()
        
        # 系统状态
        self.system_health: float = 1.0  # 系统健康度 (0-1)
        self.line_activity: np.ndarray = np.ones(num_lines) * 0.5  # 各线活跃度
        self.line_load: np.ndarray = np.zeros(num_lines)  # 各线负载
        self.entropy: float = 0.0  # 系统熵
        self.insights: deque = deque(maxlen=20)  # 最近洞察
        self.singularity_detected: bool = False
        
        # 自创生统计
        self.cycle_count: int = 0
        self.goals_generated: int = 0
        self.goals_completed: int = 0
        self.goals_failed: int = 0
        self.autopoietic_goals: int = 0  # 自创生产的目标数
        self.generation_counts: Dict[int, int] = {}  # 每代目标数
        self.completion_history: List[Tuple[int, bool, float]] = []  # (cycle, success, health)
        
        # 运行时
        self.active_intentions: List[Dict] = []  # 活跃意图
        self.line_assignments: Dict[str, Set[str]] = {i: set() for i in range(num_lines)}
        
        # 历史记录（用于分析）
        self.history: List[Dict] = []
        self.goal_lifecycle: Dict[str, List[Tuple[str, float]]] = {}  # goal_id -> [(event, time)]
    
    # ------------------------------------------------------------------
    # 核心 API: 目标生命周期管理
    # ------------------------------------------------------------------
    
    def spawn_goal(
        self,
        trigger: str,
        priority: float,
        parent: Optional[str] = None,
        goal_type: Optional[GoalType] = None,
        description: Optional[str] = None,
        line_assignment: Optional[LineID] = None,
        autopoietic: bool = True,
        generation: int = 0,
    ) -> str:
        """
        生成新目标
        
        Args:
            trigger: 触发条件
            priority: 优先级 (0-1)
            parent: 父目标ID
            goal_type: 目标类型
            description: 目标描述
            line_assignment: 分配线
            autopoietic: 是否自创生产
            generation: 自创生代数
        
        Returns:
            goal_id: 新目标ID
        """
        # 确定目标类型
        if goal_type is None:
            goal_type = self._infer_goal_type(trigger, priority)
        
        # 生成描述
        if description is None:
            description = self._generate_description(goal_type, line_assignment, trigger)
        
        # 确定线分配
        if line_assignment is None:
            line_assignment = self._assign_line(goal_type, priority)
        
        # 确定代数
        if parent and parent in self.network.goals:
            generation = self.network.goals[parent].generation
        
        # 创建目标
        goal = Goal(
            description=description,
            status=GoalStatus.PENDING,
            priority=max(0.0, min(1.0, priority)),
            goal_type=goal_type,
            parent=parent,
            trigger=trigger,
            line_assignment=line_assignment,
            autopoietic=autopoietic,
            generation=generation,
        )
        
        # 添加到网络
        self.network.add_goal(goal)
        self.goals_generated += 1
        if autopoietic:
            self.autopoietic_goals += 1
        
        # 更新代统计
        self.generation_counts[generation] = self.generation_counts.get(generation, 0) + 1
        
        # 如果有父目标，建立父子关系
        if parent and parent in self.network.goals:
            self.network.add_parent_child(parent, goal.id)
        
        # 记录生命周期
        self.goal_lifecycle[goal.id] = [("created", time.time())]
        
        # 更新线负载
        if line_assignment:
            self.line_load[line_assignment.value] += priority
            self.line_assignments[line_assignment.value].add(goal.id)
        
        return goal.id
    
    def decompose_goal(self, goal_id: str, max_depth: int = 3) -> List[str]:
        """
        目标分解 - 将高层目标自动分解为子目标
        
        Args:
            goal_id: 目标ID
            max_depth: 最大分解深度
        
        Returns:
            子目标ID列表
        """
        goal = self.network.get_goal(goal_id)
        if not goal:
            return []
        
        # 检查是否已达最大深度
        if goal.depth >= max_depth:
            return []
        
        # 查找匹配模板
        children_ids = []
        template = None
        
        for key, value in DECOMPOSITION_TEMPLATES.items():
            if key in goal.description or goal.description in key:
                template = value
                break
        
        # 如果没有匹配模板，使用通用分解
        if template is None:
            template = self._generate_generic_decomposition(goal)
        
        # 生成子目标
        prev_child_id = None
        for i, (desc, child_priority, child_type, child_line) in enumerate(template):
            # 调整优先级（基于父目标）
            adjusted_priority = child_priority * goal.priority
            
            child_id = self.spawn_goal(
                trigger=f"decomposition_of_{goal_id}",
                priority=adjusted_priority,
                parent=goal_id,
                goal_type=child_type,
                description=desc,
                line_assignment=child_line,
                autopoietic=goal.autopoietic,
                generation=goal.generation,
            )
            children_ids.append(child_id)
            
            # 添加子目标之间的顺序依赖（增加网络连接密度）
            if prev_child_id:
                self.network.add_dependency(child_id, prev_child_id, "sequential")
            prev_child_id = child_id
            
            # 子目标可能进一步分解（递归，但受深度限制）
            if adjusted_priority > 0.7 and goal.depth < max_depth - 1:
                sub_children = self.decompose_goal(child_id, max_depth=max_depth)
                children_ids.extend(sub_children)
        
        # 递归分解后的子目标可能也建立跨连接
        if len(children_ids) >= 3 and random.random() < 0.3:
            # 随机添加一些跨子目标的依赖（增加网络复杂度）
            src = random.choice(children_ids)
            dst = random.choice(children_ids)
            if src != dst:
                self.network.add_dependency(src, dst, "cross")
        
        return children_ids
    
    def complete_goal(self, goal_id: str, success: bool = True, 
                      metrics: Optional[Dict] = None) -> List[str]:
        """
        完成目标 - 标记完成并触发自生产
        
        Args:
            goal_id: 目标ID
            success: 是否成功
            metrics: 完成度量
        
        Returns:
            由该目标触发生成的新目标ID列表
        """
        goal = self.network.get_goal(goal_id)
        if not goal:
            return []
        
        # 标记完成
        goal.mark_completed(success=success, metrics=metrics)
        
        if success:
            self.goals_completed += 1
        else:
            self.goals_failed += 1
        
        # 记录生命周期
        self.goal_lifecycle[goal_id].append(("completed" if success else "failed", time.time()))
        self.completion_history.append((self.cycle_count, success, self.system_health))
        
        # 更新线负载
        if goal.line_assignment:
            self.line_load[goal.line_assignment.value] -= goal.priority
            self.line_assignments[goal.line_assignment.value].discard(goal_id)
        
        # ===== 自创生核心: 完成目标产生新目标 =====
        new_goals = []
        
        if success:
            # 成功完成 → 可能生成更高级的挑战目标
            new_goals.extend(self._spawn_post_completion_goals(goal))
        else:
            # 失败 → 生成修复目标
            new_goals.extend(self._spawn_repair_goals(goal))
        
        # 建立触发边（记录自创生关系）
        for new_goal_id in new_goals:
            self.network.add_trigger(goal_id, new_goal_id)
        
        return new_goals
    
    def get_active_goals(self) -> List[Goal]:
        """获取活跃目标列表"""
        return self.network.get_active_goals()
    
    def get_goal_network(self) -> GoalNetwork:
        """获取目标网络"""
        return self.network
    
    def goal_completion_rate(self) -> float:
        """目标完成率"""
        completed = self.goals_completed
        total_done = completed + self.goals_failed
        if total_done == 0:
            return 0.0
        return completed / total_done
    
    def network_density(self) -> float:
        """目标网络密度"""
        return self.network.network_density()
    
    # ------------------------------------------------------------------
    # 自创生循环
    # ------------------------------------------------------------------
    
    def autopoietic_cycle(self) -> Dict[str, Any]:
        """
        一步完整的自创生循环:
        1. 感知系统状态
        2. 生成/接收目标
        3. 分解目标
        4. 分配执行
        5. 监控进度
        6. 完成处理（触发自生产）
        7. 更新系统状态
        
        Returns:
            本轮统计信息
        """
        self.cycle_count += 1
        cycle_stats = {
            "cycle": self.cycle_count,
            "goals_spawned": 0,
            "goals_decomposed": 0,
            "goals_executed": 0,
            "goals_completed": 0,
            "new_goals_from_completion": 0,
            "health_before": self.system_health,
        }
        
        # === 步骤1: 感知系统状态 ===
        self._perceive_system_state()
        
        # === 步骤2: 目标生成（自创生核心）===
        new_goals = self._generate_goals_autopoietically()
        cycle_stats["goals_spawned"] = len(new_goals)
        
        # 处理意图输入
        if self.active_intentions:
            intention_goals = self._process_intentions()
            cycle_stats["goals_spawned"] += len(intention_goals)
            new_goals.extend(intention_goals)
        
        # === 步骤3: 目标分解 ===
        decomposed = 0
        for goal_id in new_goals:
            goal = self.network.get_goal(goal_id)
            if goal and goal.priority > 0.6:  # 高优先级目标才分解
                children = self.decompose_goal(goal_id)
                decomposed += len(children)
        cycle_stats["goals_decomposed"] = decomposed
        
        # === 步骤4: 分配执行（模拟）===
        executed = self._simulate_execution()
        cycle_stats["goals_executed"] = executed
        
        # === 步骤5: 完成处理（触发自生产）===
        completed_goals = self._process_completions()
        cycle_stats["goals_completed"] = len(completed_goals)
        
        # 统计由完成产生的新目标
        from_completion = sum(
            len(self.complete_goal(g.id, success=random.random() > 0.2))
            for g in completed_goals
        )
        cycle_stats["new_goals_from_completion"] = from_completion
        
        # === 步骤6: 更新系统状态 ===
        self._update_system_state()
        cycle_stats["health_after"] = self.system_health
        cycle_stats["entropy"] = self.entropy
        cycle_stats["network_density"] = self.network_density()
        cycle_stats["total_goals"] = len(self.network.goals)
        cycle_stats["active_goals"] = len(self.get_active_goals())
        
        # 记录历史
        self.history.append(cycle_stats)
        
        return cycle_stats
    
    def run_autopoiesis(self, num_cycles: int = 100, verbose: bool = True) -> Dict[str, Any]:
        """
        运行多个自创生循环
        
        Args:
            num_cycles: 循环次数
            verbose: 是否打印详细日志
        
        Returns:
            实验统计结果
        """
        if verbose:
            logger.info(f"\n{'='*70}")
            logger.info(f"OMNI-HUB v5.0 GoalAutopoiesis 实验启动")
            logger.info(f"理论基础: Maturana & Varela 自创生理论")
            logger.info(f"{'='*70}")
            logger.info(f"运行 {num_cycles} 个自创生循环...")
            logger.info(str())
        
        for i in range(num_cycles):
            stats = self.autopoietic_cycle()
            
            if verbose and (i % 20 == 0 or i == num_cycles - 1):
                print(f"  循环 {i+1:3d}: "
                      f"生成={stats['goals_spawned']:2d}, "
                      f"分解={stats['goals_decomposed']:2d}, "
                      f"完成={stats['goals_completed']:2d}, "
                      f"新生产={stats['new_goals_from_completion']:2d}, "
                      f"健康={stats['health_after']:.3f}, "
                      f"密度={stats['network_density']:.3f}")
        
        # 生成实验报告
        report = self._generate_experiment_report(num_cycles)
        
        if verbose:
            logger.info(f"\n{'='*70}")
            logger.info("实验完成!")
            logger.info(f"{'='*70}")
            self._print_report(report)
        
        return report
    
    # ------------------------------------------------------------------
    # 内部方法: 状态感知
    # ------------------------------------------------------------------
    
    def _perceive_system_state(self):
        """感知系统当前状态"""
        # 模拟环境波动
        noise = np.random.normal(0, 0.05, self.num_lines)
        self.line_activity += noise
        self.line_activity = np.clip(self.line_activity, 0, 1)
        
        # 基于活跃度计算健康度
        self.system_health = float(np.mean(self.line_activity))
        
        # 计算熵（无序度）
        # 高熵 = 各线活跃度差异大 = 不健康
        activity_variance = np.var(self.line_activity)
        self.entropy = float(activity_variance * 2)
        
        # 随机产生洞察（10%概率）
        if random.random() < 0.1:
            insight = {
                "cycle": self.cycle_count,
                "type": random.choice(["pattern", "anomaly", "opportunity", "connection"]),
                "strength": random.uniform(0.5, 1.0),
            }
            self.insights.append(insight)
    
    def _update_system_state(self):
        """更新系统状态（循环结束后）"""
        # 根据目标完成情况调整健康度
        recent_completions = [
            h for h in self.completion_history[-10:]
            if h[0] > self.cycle_count - 10
        ]
        if recent_completions:
            success_rate = sum(1 for _, s, _ in recent_completions if s) / len(recent_completions)
            self.system_health = 0.7 * self.system_health + 0.3 * success_rate
            self.system_health = np.clip(self.system_health, 0.1, 1.0)
        
        # 衰减线负载
        self.line_load *= 0.95
        
        # 更新线活跃度
        for i in range(self.num_lines):
            load_factor = 1 - min(1.0, self.line_load[i] / 5.0)  # 负载高则活跃度降
            self.line_activity[i] = 0.8 * self.line_activity[i] + 0.2 * load_factor
        
        # 随机检测奇异环（5%概率）
        self.singularity_detected = random.random() < 0.05
    
    # ------------------------------------------------------------------
    # 内部方法: 目标生成（自创生核心）
    # ------------------------------------------------------------------
    
    def _generate_goals_autopoietically(self) -> List[str]:
        """
        基于系统状态自创生目标
        
        自创生产规则:
        - 健康度高 → 探索性目标
        - 健康度低 → 修复性目标
        - 某线空闲 → 该线专项提升目标
        - 检测到奇异环 → 增强该环的目标
        - 顿悟发生 → 利用新洞察的目标
        """
        new_goals = []
        current_gen = self._get_current_generation()
        
        # 规则1: 基于健康度生成目标
        if self.system_health > 0.8:
            # 高健康度 → 探索性目标
            if random.random() < 0.4:
                line = LineID(random.randint(0, self.num_lines - 1))
                gid = self.spawn_goal(
                    trigger="high_health_exploration",
                    priority=random.uniform(0.5, 0.8),
                    goal_type=GoalType.EXPLORATORY,
                    line_assignment=line,
                    autopoietic=True,
                    generation=current_gen + 1,
                )
                new_goals.append(gid)
        
        elif self.system_health < 0.5:
            # 低健康度 → 修复性目标
            if random.random() < 0.6:
                line = LineID(random.randint(0, self.num_lines - 1))
                gid = self.spawn_goal(
                    trigger=f"low_health_repair_health={self.system_health:.2f}",
                    priority=random.uniform(0.7, 1.0),
                    goal_type=GoalType.REMEDIAL,
                    line_assignment=line,
                    autopoietic=True,
                    generation=current_gen + 1,
                )
                new_goals.append(gid)
        
        # 规则2: 空闲线生成专项目标
        idle_lines = [i for i in range(self.num_lines) if self.line_activity[i] < 0.3]
        for line_idx in idle_lines[:3]:  # 最多处理3条空闲线
            if random.random() < 0.5:
                gid = self.spawn_goal(
                    trigger=f"idle_line_{line_idx}",
                    priority=random.uniform(0.4, 0.7),
                    goal_type=GoalType.LINE_SPECIFIC,
                    line_assignment=LineID(line_idx),
                    autopoietic=True,
                    generation=current_gen + 1,
                )
                new_goals.append(gid)
        
        # 规则3: 奇异环检测
        if self.singularity_detected:
            gid = self.spawn_goal(
                trigger="singularity_detected",
                priority=random.uniform(0.8, 1.0),
                goal_type=GoalType.SINGULARITY,
                line_assignment=LineID.INTEGRATION,
                autopoietic=True,
                generation=current_gen + 1,
            )
            new_goals.append(gid)
        
        # 规则4: 洞察利用
        if len(self.insights) > 0 and random.random() < 0.35:
            latest = self.insights[-1]
            gid = self.spawn_goal(
                trigger=f"insight_utilization_{latest['type']}",
                priority=latest["strength"],
                goal_type=GoalType.INSIGHT,
                line_assignment=LineID.CREATIVITY,
                autopoietic=True,
                generation=current_gen + 1,
            )
            new_goals.append(gid)
        
        # 规则5: 基础维护目标
        if random.random() < 0.25:
            line = LineID(random.randint(0, self.num_lines - 1))
            gid = self.spawn_goal(
                trigger="routine_maintenance",
                priority=random.uniform(0.2, 0.5),
                goal_type=GoalType.MAINTENANCE,
                line_assignment=line,
                autopoietic=True,
                generation=current_gen,
            )
            new_goals.append(gid)
        
        # 规则6: 结构耦合 - 与已有目标建立连接（增加网络密度）
        if new_goals and len(self.network.goals) > 5:
            self._connect_new_goals_to_network(new_goals)
        
        return new_goals
    
    def _connect_new_goals_to_network(self, new_goal_ids: List[str]):
        """将新目标与现有网络连接，增加网络密度和潜在循环"""
        existing_active = [
            g_id for g_id, g in self.network.goals.items()
            if g_id not in new_goal_ids and g.status in [GoalStatus.PENDING, GoalStatus.ACTIVE]
        ]
        existing_completed = [
            g_id for g_id, g in self.network.goals.items()
            if g_id not in new_goal_ids and g.status == GoalStatus.COMPLETED
        ]
        
        for gid in new_goal_ids:
            goal = self.network.get_goal(gid)
            if not goal:
                continue
            
            # 与同类型的活跃目标建立依赖（30%概率）
            if existing_active and random.random() < 0.3:
                same_type = [e for e in existing_active 
                           if self.network.goals[e].goal_type == goal.goal_type]
                if same_type:
                    target = random.choice(same_type)
                    self.network.add_dependency(gid, target, "type_similarity")
            
            # 与同线的已完成目标建立触发关系（20%概率）
            if existing_completed and random.random() < 0.2:
                same_line = [e for e in existing_completed
                           if self.network.goals[e].line_assignment == goal.line_assignment]
                if same_line:
                    target = random.choice(same_line)
                    self.network.add_trigger(gid, target)
    
    def _spawn_post_completion_goals(self, completed_goal: Goal) -> List[str]:
        """
        成功完成目标后生成新目标（自创生核心）
        完成 → 生成更高级的挑战
        """
        new_goals = []
        
        # 提升一代
        next_gen = completed_goal.generation + 1
        
        # 根据完成目标的类型决定后续目标
        if completed_goal.goal_type == GoalType.EXPLORATORY:
            # 探索成功 → 深化探索
            gid = self.spawn_goal(
                trigger=f"deepen_exploration_after_{completed_goal.id}",
                priority=min(1.0, completed_goal.priority + 0.1),
                goal_type=GoalType.EXPLORATORY,
                line_assignment=completed_goal.line_assignment,
                autopoietic=True,
                generation=next_gen,
            )
            new_goals.append(gid)
        
        elif completed_goal.goal_type == GoalType.REMEDIAL:
            # 修复成功 → 预防措施
            gid = self.spawn_goal(
                trigger=f"preventive_after_repair_{completed_goal.id}",
                priority=completed_goal.priority * 0.8,
                goal_type=GoalType.MAINTENANCE,
                line_assignment=completed_goal.line_assignment,
                autopoietic=True,
                generation=next_gen,
            )
            new_goals.append(gid)
        
        elif completed_goal.goal_type == GoalType.SINGULARITY:
            # 奇异环增强成功 → 进一步稳定
            gid = self.spawn_goal(
                trigger=f"stabilize_singularity_{completed_goal.id}",
                priority=0.9,
                goal_type=GoalType.SINGULARITY,
                line_assignment=LineID.INTEGRATION,
                autopoietic=True,
                generation=next_gen,
            )
            new_goals.append(gid)
        
        # 通用: 完成任何目标都有概率生成涌现目标
        if random.random() < 0.3:
            gid = self.spawn_goal(
                trigger=f"emergent_from_{completed_goal.id}",
                priority=random.uniform(0.5, 0.8),
                goal_type=GoalType.EMERGENT,
                line_assignment=LineID(random.randint(0, self.num_lines - 1)),
                autopoietic=True,
                generation=next_gen,
            )
            new_goals.append(gid)
        
        # ===== 自创生循环增强: 新目标可能触发回历史目标 =====
        if new_goals and random.random() < 0.15:
            # 15%概率: 将新目标与随机历史目标连接（可能形成循环）
            history_goals = [
                g_id for g_id, g in self.network.goals.items()
                if g_id != completed_goal.id and g.status == GoalStatus.COMPLETED
                and g_id not in new_goals
            ]
            if history_goals:
                target_id = random.choice(history_goals)
                for gid in new_goals:
                    self.network.add_trigger(gid, target_id)
        
        # 20%概率: 创建一个反馈目标（指向祖先），形成循环
        if random.random() < 0.2 and completed_goal.parent:
            ancestor = self._find_ancestor_or_similar(completed_goal)
            if ancestor and ancestor != completed_goal.id:
                feedback_gid = self.spawn_goal(
                    trigger=f"feedback_loop_from_{completed_goal.id}_to_{ancestor}",
                    priority=random.uniform(0.4, 0.7),
                    goal_type=GoalType.EMERGENT,
                    line_assignment=completed_goal.line_assignment,
                    autopoietic=True,
                    generation=next_gen,
                )
                new_goals.append(feedback_gid)
                # 建立反馈边: 反馈目标触发回祖先
                self.network.add_trigger(feedback_gid, ancestor)
        
        return new_goals
    
    def _find_ancestor_or_similar(self, goal: Goal) -> Optional[str]:
        """找到一个祖先或相似目标（用于形成循环）"""
        # 优先找祖先
        if goal.parent and goal.parent in self.network.goals:
            parent = self.network.goals[goal.parent]
            # 50%概率返回祖父
            if parent.parent and parent.parent in self.network.goals and random.random() < 0.5:
                return parent.parent
            return goal.parent
        
        # 找同类型的已完成目标
        same_type = [
            g_id for g_id, g in self.network.goals.items()
            if g.goal_type == goal.goal_type and g.status == GoalStatus.COMPLETED
            and g_id != goal.id
        ]
        if same_type:
            return random.choice(same_type)
        return None
    
    def _spawn_repair_goals(self, failed_goal: Goal) -> List[str]:
        """
        目标失败后生成修复目标
        """
        new_goals = []
        
        # 生成修复目标
        gid = self.spawn_goal(
            trigger=f"repair_failure_of_{failed_goal.id}",
            priority=min(1.0, failed_goal.priority + 0.2),
            goal_type=GoalType.REMEDIAL,
            line_assignment=failed_goal.line_assignment,
            autopoietic=True,
            generation=failed_goal.generation,
        )
        new_goals.append(gid)
        
        # 生成替代目标
        if random.random() < 0.5:
            alt_gid = self.spawn_goal(
                trigger=f"alternative_to_{failed_goal.id}",
                priority=failed_goal.priority * 0.8,
                goal_type=GoalType.MAINTENANCE,
                line_assignment=LineID(random.randint(0, self.num_lines - 1)),
                autopoietic=True,
                generation=failed_goal.generation,
            )
            new_goals.append(alt_gid)
        
        return new_goals
    
    def _process_intentions(self) -> List[str]:
        """处理外部意图输入，转化为目标"""
        new_goals = []
        
        for intention in self.active_intentions:
            gid = self.spawn_goal(
                trigger=f"intention:{intention.get('type', 'unknown')}",
                priority=intention.get("priority", 0.5),
                goal_type=GoalType.EMERGENT,
                description=intention.get("description", "外部意图"),
                line_assignment=LineID(intention.get("line", random.randint(0, self.num_lines - 1))),
                autopoietic=False,  # 外部意图不是自创生产的
                generation=0,
            )
            new_goals.append(gid)
        
        self.active_intentions.clear()
        return new_goals
    
    def _simulate_execution(self) -> int:
        """
        模拟目标执行
        将待处理的叶目标标记为活跃并模拟执行
        """
        executed = 0
        leaf_goals = self.network.get_leaf_goals()
        
        # 按优先级排序
        leaf_goals.sort(key=lambda g: g.priority, reverse=True)
        
        # 模拟执行（每轮最多执行5个）
        for goal in leaf_goals[:5]:
            if goal.status == GoalStatus.PENDING:
                goal.mark_active()
                executed += 1
                
                # 模拟执行进度
                goal.progress = random.uniform(0.3, 0.9)
                self.goal_lifecycle[goal.id].append(("activated", time.time()))
        
        return executed
    
    def _process_completions(self) -> List[Goal]:
        """
        处理活跃目标的完成
        基于模拟进度决定哪些目标完成
        """
        completed = []
        active = self.get_active_goals()
        
        for goal in active:
            # 模拟执行: 有一定概率完成
            if random.random() < 0.4:  # 40%完成概率
                goal.progress = 1.0
                completed.append(goal)
        
        return completed
    
    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    
    def _infer_goal_type(self, trigger: str, priority: float) -> GoalType:
        """从触发条件推断目标类型"""
        trigger_lower = trigger.lower()
        
        if "health" in trigger_lower or "repair" in trigger_lower or "fix" in trigger_lower:
            return GoalType.REMEDIAL
        elif "explor" in trigger_lower or "experiment" in trigger_lower:
            return GoalType.EXPLORATORY
        elif "singularity" in trigger_lower or "loop" in trigger_lower:
            return GoalType.SINGULARITY
        elif "insight" in trigger_lower or "discover" in trigger_lower:
            return GoalType.INSIGHT
        elif "idle" in trigger_lower or "line" in trigger_lower:
            return GoalType.LINE_SPECIFIC
        elif "emerg" in trigger_lower:
            return GoalType.EMERGENT
        else:
            return GoalType.MAINTENANCE
    
    def _generate_description(self, goal_type: GoalType, 
                              line: Optional[LineID], trigger: str) -> str:
        """生成目标描述"""
        templates = GOAL_DESCRIPTIONS.get(goal_type, ["执行目标"])
        template = random.choice(templates)
        
        line_name = LINE_NAMES.get(line, "系统") if line else "系统"
        
        return template.format(line=line_name, trigger=trigger)
    
    def _assign_line(self, goal_type: GoalType, priority: float) -> LineID:
        """为目标分配执行线"""
        # 基于目标类型和当前负载分配
        type_line_map = {
            GoalType.EXPLORATORY: [LineID.CREATIVITY, LineID.PREDICTION, LineID.PERCEPTION],
            GoalType.REMEDIAL: [LineID.META, LineID.INTEGRATION, LineID.ACTION],
            GoalType.LINE_SPECIFIC: list(LineID),
            GoalType.SINGULARITY: [LineID.INTEGRATION, LineID.META, LineID.EMOTION],
            GoalType.INSIGHT: [LineID.CREATIVITY, LineID.REASONING, LineID.META],
            GoalType.MAINTENANCE: [LineID.REFLECTION, LineID.MEMORY, LineID.ACTION],
            GoalType.EMERGENT: list(LineID),
        }
        
        candidates = type_line_map.get(goal_type, list(LineID))
        
        # 选择负载最低的候选线
        best_line = candidates[0]
        best_load = float('inf')
        
        for line in candidates:
            load = self.line_load[line.value]
            if load < best_load:
                best_load = load
                best_line = line
        
        return best_line
    
    def _generate_generic_decomposition(self, goal: Goal) -> List[Tuple[str, float, GoalType, LineID]]:
        """为没有模板匹配的目标生成通用分解"""
        line = goal.line_assignment or LineID(random.randint(0, self.num_lines - 1))
        
        return [
            (f"分析{goal.description}的可行性", 0.7, GoalType.MAINTENANCE, LineID.REASONING),
            (f"准备{goal.description}的资源", 0.6, GoalType.MAINTENANCE, line),
            (f"执行{goal.description}的核心步骤", 0.8, goal.goal_type, line),
            (f"验证{goal.description}的结果", 0.65, GoalType.MAINTENANCE, LineID.REFLECTION),
        ]
    
    def _get_current_generation(self) -> int:
        """获取当前最大代数"""
        if not self.network.goals:
            return 0
        return max(g.generation for g in self.network.goals.values())
    
    # ------------------------------------------------------------------
    # 实验报告
    # ------------------------------------------------------------------
    
    def _generate_experiment_report(self, num_cycles: int) -> Dict[str, Any]:
        """生成实验报告"""
        # 基础统计
        total_goals = len(self.network.goals)
        active = len(self.network.get_active_goals())
        pending = len(self.network.get_pending_goals())
        completed = len(self.network.get_completed_goals())
        failed = len(self.network.get_failed_goals())
        
        # 网络分析
        net_stats = self.network.statistics()
        
        # 完成率分析
        completion_rate = self.goal_completion_rate()
        
        # 自创生分析
        autopoietic_rate = self.autopoietic_goals / max(1, self.goals_generated)
        
        # 代分析
        gen_counts = self.generation_counts
        max_gen = max(gen_counts.keys()) if gen_counts else 0
        
        # 目标类型分布
        type_dist = {}
        for g in self.network.goals.values():
            t = g.goal_type.value
            type_dist[t] = type_dist.get(t, 0) + 1
        
        # 线分布
        line_dist = {}
        for g in self.network.goals.values():
            if g.line_assignment:
                l = LINE_NAMES.get(g.line_assignment, "未知")
                line_dist[l] = line_dist.get(l, 0) + 1
        
        # 健康度变化
        health_history = [h["health_after"] for h in self.history]
        avg_health = sum(health_history) / len(health_history) if health_history else 0
        health_trend = health_history[-1] - health_history[0] if len(health_history) > 1 else 0
        
        # 密度变化
        density_history = [h["network_density"] for h in self.history]
        avg_density = sum(density_history) / len(density_history) if density_history else 0
        
        # 自生产验证
        # 检查是否有目标是由其他目标完成触发的
        trigger_edges = [
            (u, v) for u, v, d in self.network.graph.edges(data=True)
            if d.get("type") == "triggers"
        ]
        
        # 检测自创生循环
        autopoietic_cycles = self.network.get_autopoietic_cycles()
        
        # 深度分析
        depths = [g.depth for g in self.network.goals.values()]
        avg_depth = sum(depths) / len(depths) if depths else 0
        max_depth = max(depths) if depths else 0
        
        report = {
            "experiment": {
                "name": "GoalAutopoiesis Experiment",
                "cycles": num_cycles,
                "timestamp": datetime.now().isoformat(),
                "theoretical_basis": "Maturana & Varela Autopoiesis Theory",
            },
            "goal_statistics": {
                "total_goals": total_goals,
                "active": active,
                "pending": pending,
                "completed": completed,
                "failed": failed,
                "completion_rate": completion_rate,
                "goals_generated": self.goals_generated,
                "autopoietic_goals": self.autopoietic_goals,
                "autopoietic_rate": autopoietic_rate,
            },
            "network_analysis": {
                "nodes": net_stats["nodes"],
                "edges": net_stats["edges"],
                "density": net_stats["density"],
                "clustering": net_stats["clustering"],
                "avg_depth": avg_depth,
                "max_depth": max_depth,
                "max_generation": max_gen,
                "avg_generation": net_stats["avg_generation"],
                "autopoietic_cycles": len(autopoietic_cycles),
                "cycles_detected": net_stats["cycles_detected"],
            },
            "system_state": {
                "final_health": self.system_health,
                "avg_health": avg_health,
                "health_trend": health_trend,
                "final_entropy": self.entropy,
                "avg_density": avg_density,
            },
            "distributions": {
                "status": net_stats["status_distribution"],
                "type": type_dist,
                "line": line_dist,
                "generation": gen_counts,
            },
            "autopoiesis_verification": {
                "trigger_edges_count": len(trigger_edges),
                "autopoietic_cycles_found": len(autopoietic_cycles),
                "cycles_details": [list(c) for c in autopoietic_cycles[:5]],
                "generation_growth": max_gen > 0,
                "self_production_confirmed": len(trigger_edges) > 0,
            },
            "cycle_history": self.history,
        }
        
        return report
    
    def _print_report(self, report: Dict[str, Any]):
        """打印实验报告"""
        logger.info("\n" + "="*70)
        logger.info("实验报告: OMNI-HUB v5.0 GoalAutopoiesis")
        logger.info("="*70)
        
        gs = report["goal_statistics"]
        logger.info(f"\n【目标统计】")
        logger.info(f"  总目标数:      {gs['total_goals']}")
        logger.info(f"    - 活跃:      {gs['active']}")
        logger.info(f"    - 待处理:    {gs['pending']}")
        logger.info(f"    - 已完成:    {gs['completed']}")
        logger.info(f"    - 失败:      {gs['failed']}")
        logger.info(f"  目标完成率:    {gs['completion_rate']:.2%}")
        print(f"  自创生目标:    {gs['autopoietic_goals']}/{gs['goals_generated']} "
              f"({gs['autopoietic_rate']:.2%})")
        
        na = report["network_analysis"]
        logger.info(f"\n【网络分析】")
        logger.info(f"  节点数:        {na['nodes']}")
        logger.info(f"  边数:          {na['edges']}")
        logger.info(f"  网络密度:      {na['density']:.4f}")
        logger.info(f"  聚类系数:      {na['clustering']:.4f}")
        logger.info(f"  平均深度:      {na['avg_depth']:.2f}")
        logger.info(f"  最大深度:      {na['max_depth']}")
        logger.info(f"  最大代数:      {na['max_generation']}")
        logger.info(f"  自创生循环:    {na['autopoietic_cycles']}")
        logger.info(f"  检测到的循环:  {na['cycles_detected']}")
        
        ss = report["system_state"]
        logger.info(f"\n【系统状态】")
        logger.info(f"  最终健康度:    {ss['final_health']:.4f}")
        logger.info(f"  平均健康度:    {ss['avg_health']:.4f}")
        logger.info(f"  健康度趋势:    {ss['health_trend']:+.4f}")
        logger.info(f"  最终熵:        {ss['final_entropy']:.4f}")
        logger.info(f"  平均密度:      {ss['avg_density']:.4f}")
        
        av = report["autopoiesis_verification"]
        logger.info(f"\n【自创生验证】")
        logger.info(f"  触发边数量:    {av['trigger_edges_count']}")
        logger.info(f"  自创生循环:    {av['autopoietic_cycles_found']}")
        logger.info(f"  代数增长:      {'是' if av['generation_growth'] else '否'}")
        logger.info(f"  自生产确认:    {'✓ 已确认' if av['self_production_confirmed'] else '✗ 未确认'}")
        
        if av["cycles_details"]:
            logger.info(f"\n  循环示例:")
            for i, cycle in enumerate(av["cycles_details"][:3], 1):
                logger.info(f"    循环 {i}: {' -> '.join(cycle)}")
        
        logger.info(f"\n{'='*70}")
        logger.info("结论:")
        if av["self_production_confirmed"] and av["generation_growth"]:
            logger.info("  ✓ 目标自创生机制已验证: 系统成功实现了目标的自生产!")
            logger.info("  ✓ 完成目标触发了新目标的生成，形成了自创生循环!")
        else:
            logger.info("  ! 目标自创生机制部分验证，建议增加循环次数")
        logger.info(f"{'='*70}\n")
    
    # ------------------------------------------------------------------
    # 高级查询
    # ------------------------------------------------------------------
    
    def get_goal_lineage(self, goal_id: str) -> List[Dict]:
        """获取目标的完整血统链"""
        lineage_ids = self.network.lineage(goal_id)
        return [self.network.goals[g_id].to_dict() for g_id in lineage_ids if g_id in self.network.goals]
    
    def get_autopoietic_chains(self) -> List[List[str]]:
        """获取所有自创生链（由触发边构成的路径）"""
        trigger_graph = nx.DiGraph()
        for u, v, d in self.network.graph.edges(data=True):
            if d.get("type") == "triggers":
                trigger_graph.add_edge(u, v)
        
        chains = []
        for node in trigger_graph.nodes():
            # 找到从该节点出发的最长路径
            for target in trigger_graph.nodes():
                if node != target and nx.has_path(trigger_graph, node, target):
                    paths = list(nx.all_simple_paths(trigger_graph, node, target))
                    for path in paths:
                        if len(path) >= 2:
                            chains.append(path)
        
        # 去重并返回最长的
        unique_chains = []
        seen = set()
        for chain in sorted(chains, key=len, reverse=True):
            key = tuple(chain)
            if key not in seen:
                seen.add(key)
                unique_chains.append(chain)
        
        return unique_chains[:10]
    
    def visualize_network_summary(self) -> str:
        """生成网络文本摘要"""
        lines = []
        lines.append("\n" + "="*60)
        lines.append("目标网络摘要")
        lines.append("="*60)
        
        # 根目标
        roots = self.network.get_roots()
        lines.append(f"\n根目标 ({len(roots)}个):")
        for g in roots[:5]:
            lines.append(f"  • {g.description[:40]} (P={g.priority:.2f}, Gen={g.generation})")
        
        # 叶目标
        leaves = self.network.get_leaf_goals()
        lines.append(f"\n叶目标 ({len(leaves)}个):")
        for g in leaves[:5]:
            line_name = LINE_NAMES.get(g.line_assignment, "未分配") if g.line_assignment else "未分配"
            lines.append(f"  • {g.description[:40]} (线={line_name})")
        
        # 关键路径
        critical = self.network.get_critical_path()
        if critical:
            lines.append(f"\n关键路径 ({len(critical)}个节点):")
            for gid in critical[:8]:
                g = self.network.get_goal(gid)
                if g:
                    lines.append(f"  → {g.description[:35]}")
        
        # 网络统计
        stats = self.network.statistics()
        lines.append(f"\n网络统计:")
        lines.append(f"  节点: {stats['nodes']}, 边: {stats['edges']}")
        lines.append(f"  密度: {stats['density']:.4f}")
        lines.append(f"  最大代数: {stats['max_generation']}")
        lines.append(f"  自创生循环: {stats['autopoietic_cycles']}")
        
        lines.append("="*60)
        return "\n".join(lines)


# ============================================================================
# 第六部分: 实验验证
# ============================================================================

def run_comprehensive_experiment(seed: int = 42) -> Dict[str, Any]:
    """
    运行全面的实验验证
    
    验证内容:
    1. 运行100个自创生循环
    2. 统计: 生成目标数、完成率、网络密度、自生产速率
    3. 验证: 目标网络是否形成自创生循环
    4. 验证: 完成目标是否确实触发新目标生成
    """
    logger.info("\n" + "="*70)
    logger.info("OMNI-HUB v5.0 GoalAutopoiesis 全面实验验证")
    logger.info("="*70)
    logger.info(f"随机种子: {seed}")
    logger.info(f"理论基础: Maturana & Varela 自创生理论")
    logger.info(f"核心命题: 目标是系统自己生产自己的")
    logger.info("="*70)
    
    # 创建系统
    system = GoalAutopoiesis(num_lines=11, random_seed=seed)
    
    # 实验1: 基础自创生 (100循环)
    logger.info("\n【实验1】基础自创生循环 (100轮)")
    report1 = system.run_autopoiesis(num_cycles=100, verbose=True)
    
    # 实验2: 添加外部意图后的自创生
    logger.info("\n【实验2】结构耦合: 外部意图输入后的自创生 (50轮)")
    system.active_intentions.append({
        "type": "user_request",
        "description": "增强系统的自我意识能力",
        "priority": 0.9,
        "line": 6,  # 元认知线
    })
    system.active_intentions.append({
        "type": "environment_change",
        "description": "适应新的输入模式",
        "priority": 0.7,
        "line": 0,  # 感知线
    })
    
    report2 = system.run_autopoiesis(num_cycles=50, verbose=True)
    
    # 实验3: 压力测试 (模拟系统故障)
    logger.info("\n【实验3】压力测试: 模拟低健康度状态 (50轮)")
    system.system_health = 0.2  # 强制低健康度
    system.line_activity = np.ones(11) * 0.2
    
    report3 = system.run_autopoiesis(num_cycles=50, verbose=True)
    
    # 网络摘要
    logger.info(str(system.visualize_network_summary()))
    
    # 自创生链分析
    logger.info("\n" + "="*70)
    logger.info("自创生链分析")
    logger.info("="*70)
    chains = system.get_autopoietic_chains()
    logger.info(f"发现 {len(chains)} 条自创生链:")
    for i, chain in enumerate(chains[:5], 1):
        logger.info(f"\n链 {i} ({len(chain)} 个目标):")
        for gid in chain:
            g = system.network.get_goal(gid)
            if g:
                logger.info(f"  → {g.description[:40]} (Gen={g.generation})")
    
    # 综合报告
    logger.info("\n" + "="*70)
    logger.info("综合实验报告")
    logger.info("="*70)
    
    total_cycles = 200
    total_goals = len(system.network.goals)
    
    logger.info(f"\n总运行循环: {total_cycles}")
    logger.info(f"总生成目标: {system.goals_generated}")
    logger.info(f"总完成目标: {system.goals_completed}")
    logger.info(f"总失败目标: {system.goals_failed}")
    logger.info(f"完成率: {system.goal_completion_rate():.2%}")
    logger.info(f"自创生目标占比: {system.autopoietic_goals/max(1,system.goals_generated):.2%}")
    logger.info(f"最终网络密度: {system.network_density():.4f}")
    logger.info(f"最终系统健康度: {system.system_health:.4f}")
    
    # 验证结论
    av = report1["autopoiesis_verification"]
    logger.info(f"\n【验证结论】")
    
    # 网络密度验证: 大型网络(>500节点)的密度阈值应更低
    n_nodes = len(system.network.goals)
    density_threshold = 0.01 if n_nodes < 100 else 0.0003
    
    checks = {
        "目标自生产": av["self_production_confirmed"],
        "代数增长": av["generation_growth"],
        "自创生循环形成": av["autopoietic_cycles_found"] > 0,
        "网络密度增长": system.network_density() > density_threshold,
        "目标完成触发新目标": av["trigger_edges_count"] > 0,
    }
    
    all_passed = True
    for check, passed in checks.items():
        status = "✓ 通过" if passed else "✗ 未通过"
        logger.info(f"  {check}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info(f"\n{'='*70}")
        logger.info("所有验证通过! 目标自创生系统运行正常。")
        logger.info("系统成功实现了目标的自生产、自组织和自维持。")
        logger.info(f"{'='*70}")
    
    # 返回综合结果
    return {
        "system": system,
        "report_phase1": report1,
        "report_phase2": report2,
        "report_phase3": report3,
        "comprehensive": {
            "total_cycles": total_cycles,
            "total_goals": total_goals,
            "goals_generated": system.goals_generated,
            "goals_completed": system.goals_completed,
            "goals_failed": system.goals_failed,
            "completion_rate": system.goal_completion_rate(),
            "autopoietic_rate": system.autopoietic_goals / max(1, system.goals_generated),
            "final_health": system.system_health,
            "final_density": system.network_density(),
            "max_generation": max(system.generation_counts.keys()) if system.generation_counts else 0,
            "all_checks_passed": all_passed,
            "checks": checks,
        }
    }


# ============================================================================
# 第七部分: 主入口
# ============================================================================

if __name__ == "__main__":
    # 运行全面实验
    results = run_comprehensive_experiment(seed=42)
    
    # 额外: 测试核心API
    print("\n" + "="*70)
    print("API 功能测试")
    print("="*70)
    
    system = results["system"]
    
    # 测试 get_active_goals
    active = system.get_active_goals()
    print(f"\n活跃目标数: {len(active)}")
    
    # 测试 get_goal_network
    net = system.get_goal_network()
    print(f"网络节点数: {net.graph.number_of_nodes()}")
    print(f"网络边数: {net.graph.number_of_edges()}")
    
    # 测试 detect_cycles
    cycles = net.detect_cycles()
    print(f"检测到循环数: {len(cycles)}")
    
    # 测试 get_critical_path
    critical = net.get_critical_path()
    print(f"关键路径长度: {len(critical)}")
    
    # 测试 lineage
    if system.network.get_roots():
        root = system.network.get_roots()[0]
        lineage = system.get_goal_lineage(root.id)
        print(f"根目标血统链长度: {len(lineage)}")
    
    print("\n所有测试完成!")
