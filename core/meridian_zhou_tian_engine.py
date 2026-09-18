#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v8.0 — MeridianZhouTianEngine (经脉·子午流注·周天引擎)
================================================================
中医经络-量子意识映射引擎

Architecture: Meridian-Quantum Consciousness Mapping (MQCM)
Author: OMNI-HUB Core Systems
Version: 8.0.0

Core Concepts:
- 十二正经 (Twelve Primary Meridians): 气血运行的主要通道
- 奇经八脉 (Eight Extraordinary Vessels): 调节十二正经的气血
- 子午流注 (ZiWu LiuZhu): 气血按时辰流注的周期律
- 小周天 (Microcosmic Orbit): 任督二脉微循环
- 大周天 (Macrocosmic Orbit): 十二正经大循环
- 361穴位映射到模块节点

Mapping:
- 11线 → 12正经: 部分经脉共享线路
- 奇经八脉 → SI层级
- 361穴位 → 模块节点
"""

import numpy as np
from typing import List, Tuple, Dict, Callable, Optional, Union, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque, defaultdict
import json
import time
from pathlib import Path
import logging

# ============================================================================
# Constants & Configuration
# ============================================================================

NUM_LINES = 11  # OMNI-HUB 11条线路
NUM_SI_LEVELS = 7  # SI层级 0-6 + 核心机
FIELD_DIMENSION = 64  # 场空间分辨率

# OMNI-HUB 线路名称
LINE_NAMES = [
    "ucif2",      # 0
    "lvlu",       # 1
    "lgt",        # 2
    "qfa",        # 3
    "vinf",       # 4
    "qgl",        # 5
    "qlv",        # 6
    "cisvr",      # 7
    "qtlv",       # 8
    "usrm",       # 9
    "cfts",       # 10
]

LINE_DISPLAY_NAMES = [
    "ucif2(统一认知接口)",
    "lvlu(逻辑验证层)",
    "lgt(逻辑门控)",
    "qfa(量子场算法)",
    "vinf(愿景信息流)",
    "qgl(量子门逻辑)",
    "qlv(量子逻辑验证)",
    "cisvr(认知空间VR)",
    "qtlv(量子拓扑逻辑验证)",
    "usrm(用户空间资源管理)",
    "cfts(跨场张力同步)"
]

# 十二正经名称
TWELVE_MERIDIANS = [
    "手太阴肺经",
    "手阳明大肠经",
    "足阳明胃经",
    "足太阴脾经",
    "手少阴心经",
    "手太阳小肠经",
    "足太阳膀胱经",
    "足少阴肾经",
    "手厥阴心包经",
    "手少阳三焦经",
    "足少阳胆经",
    "足厥阴肝经",
]

# 十二正经简称
TWELVE_MERIDIANS_SHORT = [
    "肺经", "大肠经", "胃经", "脾经",
    "心经", "小肠经", "膀胱经", "肾经",
    "心包经", "三焦经", "胆经", "肝经"
]

# 奇经八脉名称
EXTRAORDINARY_VESSELS = [
    "任脉", "督脉", "冲脉", "带脉",
    "阴跷脉", "阳跷脉", "阴维脉", "阳维脉"
]

# 五行属性
FIVE_ELEMENTS = ["金", "金", "土", "土", "火", "火", "水", "水", "火", "火", "木", "木"]

# 十二正经当令时辰 (24小时制)
MERIDIAN_HOURS = {
    "手太阴肺经": (3, 5),
    "手阳明大肠经": (5, 7),
    "足阳明胃经": (7, 9),
    "足太阴脾经": (9, 11),
    "手少阴心经": (11, 13),
    "手太阳小肠经": (13, 15),
    "足太阳膀胱经": (15, 17),
    "足少阴肾经": (17, 19),
    "手厥阴心包经": (19, 21),
    "手少阳三焦经": (21, 23),
    "足少阳胆经": (23, 1),
    "足厥阴肝经": (1, 3),
}

# 11线 → 12正经映射
LINE_TO_MERIDIAN = {
    0: ["手太阴肺经"],
    1: ["手阳明大肠经"],
    2: ["足阳明胃经"],
    3: ["足太阴脾经"],
    4: ["手少阴心经"],
    5: ["手太阳小肠经"],
    6: ["足太阳膀胱经"],
    7: ["足少阴肾经"],
    8: ["手厥阴心包经"],
    9: ["手少阳三焦经"],
    10: ["足少阳胆经", "足厥阴肝经"],  # 胆经和肝经共享一线
}

# 奇经八脉 → SI层级映射
VESSEL_TO_SI = {
    "督脉": 5,
    "任脉": 4,
    "冲脉": 3,
    "带脉": 2,
    "阴跷脉": 1,
    "阳跷脉": 0,
    "阴维脉": 6,
    "阳维脉": -1,  # 核心机
}

# 十二正经流注顺序 (大周天路径)
MACROCOSMIC_ORDER = [
    "手太阴肺经", "手阳明大肠经", "足阳明胃经", "足太阴脾经",
    "手少阴心经", "手太阳小肠经", "足太阳膀胱经", "足少阴肾经",
    "手厥阴心包经", "手少阳三焦经", "足少阳胆经", "足厥阴肝经"
]

# 小周天路径 (任督二脉)
MICROCOSMIC_PATH = [
    "会阴", "长强", "命门", "中枢", "大椎",
    "百会", "印堂", "人中", "膻中", "神阙", "气海", "会阴"
]

# 小周天逆向路径
MICROCOSMIC_REVERSE_PATH = [
    "会阴", "气海", "神阙", "膻中", "人中",
    "印堂", "百会", "大椎", "中枢", "命门", "长强", "会阴"
]

# 十二正经穴位数量 (标准)
MERIDIAN_ACUPOINT_COUNTS = {
    "手太阴肺经": 11,
    "手阳明大肠经": 20,
    "足阳明胃经": 45,
    "足太阴脾经": 21,
    "手少阴心经": 9,
    "手太阳小肠经": 19,
    "足太阳膀胱经": 67,
    "足少阴肾经": 27,
    "手厥阴心包经": 9,
    "手少阳三焦经": 23,
    "足少阳胆经": 44,
    "足厥阴肝经": 14,
}

# 奇经八脉穴位数量
VESSEL_ACUPOINT_COUNTS = {
    "任脉": 24,
    "督脉": 28,
    "冲脉": 11,
    "带脉": 3,
    "阴跷脉": 2,
    "阳跷脉": 2,
    "阴维脉": 7,
    "阳维脉": 7,
}

# 五行相生: 木→火→土→金→水→木
ELEMENT_GENERATING = {
    "木": "火",
    "火": "土",
    "土": "金",
    "金": "水",
    "水": "木",
}

# 五行相克: 木→土→水→火→金→木
ELEMENT_RESTRAINING = {
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
    "金": "木",
}

# 十二正经原穴 (母穴, 用于补)
MERIDIAN_MOTHER_POINTS = {
    "手太阴肺经": "太渊",
    "手阳明大肠经": "曲池",
    "足阳明胃经": "足三里",
    "足太阴脾经": "大都",
    "手少阴心经": "少冲",
    "手太阳小肠经": "后溪",
    "足太阳膀胱经": "足通谷",
    "足少阴肾经": "复溜",
    "手厥阴心包经": "中冲",
    "手少阳三焦经": "中渚",
    "足少阳胆经": "足临泣",
    "足厥阴肝经": "曲泉",
}

# 十二正经子穴 (用于泻)
MERIDIAN_SON_POINTS = {
    "手太阴肺经": "尺泽",
    "手阳明大肠经": "二间",
    "足阳明胃经": "厉兑",
    "足太阴脾经": "商丘",
    "手少阴心经": "神门",
    "手太阳小肠经": "小海",
    "足太阳膀胱经": "束骨",
    "足少阴肾经": "涌泉",
    "手厥阴心包经": "大陵",
    "手少阳三焦经": "天井",
    "足少阳胆经": "阳辅",
    "足厥阴肝经": "行间",
}


# ============================================================================
# Acupoint 类 — 穴位
# ============================================================================

@dataclass
class Acupoint:
    """
    穴位 — 经络系统中的基本节点

    每个穴位对应一个能量节点，具有名称、所属经脉、位置、功能和激活等级。
    在OMNI-HUB中，361个穴位映射到模块节点。

    Attributes:
        name: 穴位名称
        meridian: 所属经脉名称
        location: 位置描述
        function: 功能描述
        activation_level: 激活等级 [0.0, 1.0]
        energy: 当前能量值
        connections: 与其他穴位的连接
        coordinates: 三维坐标 (用于场计算)
        element: 五行属性
        module_id: 映射到的模块ID
    """

    name: str
    meridian: str
    location: str = ""
    function: str = ""
    activation_level: float = 0.0
    energy: float = 0.0
    connections: List['Acupoint'] = field(default_factory=list)
    coordinates: Tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
    element: str = ""
    module_id: int = 0
    _history: deque = field(default_factory=lambda: deque(maxlen=100))

    def __post_init__(self):
        """初始化后设置历史记录"""
        if not isinstance(self._history, deque):
            self._history = deque(maxlen=100)

    def activate(self, energy: float) -> float:
        """
        激活穴位，注入能量

        Args:
            energy: 注入的能量值

        Returns:
            激活后的能量值
        """
        self.energy += energy
        # 能量衰减到稳态
        self.activation_level = min(1.0, max(0.0, self.energy / 10.0))
        self._history.append((time.time(), self.energy, self.activation_level))
        return self.energy

    def decay(self, rate: float = 0.01) -> float:
        """
        能量衰减

        Args:
            rate: 衰减率

        Returns:
            衰减后的能量值
        """
        self.energy *= (1.0 - rate)
        self.activation_level = min(1.0, max(0.0, self.energy / 10.0))
        return self.energy

    def connect(self, other: 'Acupoint', bidirectional: bool = True) -> None:
        """
        建立与其他穴位的连接

        Args:
            other: 目标穴位
            bidirectional: 是否双向连接
        """
        if other not in self.connections:
            self.connections.append(other)
        if bidirectional and self not in other.connections:
            other.connections.append(self)

    def disconnect(self, other: 'Acupoint') -> None:
        """
        断开与另一个穴位的连接

        Args:
            other: 目标穴位
        """
        if other in self.connections:
            self.connections.remove(other)

    def get_energy_flow(self) -> float:
        """
        获取穴位能量流（与连接的穴位的能量差）

        Returns:
            能量流总和
        """
        if not self.connections:
            return 0.0
        flow = sum(other.energy - self.energy for other in self.connections)
        return flow / len(self.connections)

    def get_state(self) -> Dict[str, Any]:
        """
        获取穴位当前状态

        Returns:
            状态字典
        """
        return {
            "name": self.name,
            "meridian": self.meridian,
            "energy": self.energy,
            "activation_level": self.activation_level,
            "connections": len(self.connections),
            "coordinates": self.coordinates,
            "element": self.element,
            "module_id": self.module_id,
        }

    def __repr__(self) -> str:
        return f"Acupoint({self.name}@{self.meridian}, E={self.energy:.3f}, A={self.activation_level:.3f})"


# ============================================================================
# Meridian 类 — 经脉
# ============================================================================

class Meridian:
    """
    经脉 — 气血运行的通道

    包含十二正经和奇经八脉。每条经脉有名称、五行属性、当令时辰、
    穴位列表和气血流量。

    Attributes:
        name: 经脉名称
        element: 五行属性
        hours: 当令时辰 (start, end)
        acupoints: 穴位列表
        qi_flow: 气血流量
        is_extraordinary: 是否为奇经八脉
        si_level: 映射的SI层级 (奇经八脉用)
        line_id: 映射的线路ID (十二正经用)
    """

    def __init__(
        self,
        name: str,
        element: str = "",
        hours: Tuple[int, int] = (0, 0),
        is_extraordinary: bool = False,
        si_level: Optional[int] = None,
        line_id: Optional[int] = None,
        num_acupoints: int = 10
    ):
        self.name = name
        self.element = element
        self.hours = hours
        self.acupoints: List[Acupoint] = []
        self.qi_flow: float = 1.0  # 基础气血流量
        self.is_extraordinary = is_extraordinary
        self.si_level = si_level
        self.line_id = line_id
        self.num_acupoints = num_acupoints
        self._qi_history: deque = deque(maxlen=100)
        self._state_history: deque = deque(maxlen=50)

        # 生成穴位
        self._generate_acupoints()

    def _generate_acupoints(self) -> None:
        """生成经脉上的穴位"""
        prefix = self.name.replace("手", "").replace("足", "").replace("经", "").replace("脉", "")
        for i in range(self.num_acupoints):
            acupoint_name = f"{prefix}{i+1:02d}"
            location = f"{self.name}第{i+1}穴"
            function = f"调节{self.element}气"

            # 为特定穴位赋予真实名称 (前几个穴位)
            if self.name in MERIDIAN_ACUPOINT_COUNTS and i < 5:
                special_names = self._get_special_acupoint_names()
                if i < len(special_names):
                    acupoint_name = special_names[i]

            acupoint = Acupoint(
                name=acupoint_name,
                meridian=self.name,
                location=location,
                function=function,
                element=self.element,
                module_id=i % 33  # 361穴位 / 11线 ≈ 33模块每线
            )
            self.acupoints.append(acupoint)

        # 建立穴位间连接 (线性连接)
        for i in range(len(self.acupoints) - 1):
            self.acupoints[i].connect(self.acupoints[i + 1])

    def _get_special_acupoint_names(self) -> List[str]:
        """获取特定经脉的代表性穴位名称"""
        special = {
            "手太阴肺经": ["中府", "云门", "天府", "侠白", "尺泽"],
            "手阳明大肠经": ["商阳", "二间", "三间", "合谷", "阳溪"],
            "足阳明胃经": ["承泣", "四白", "巨髎", "地仓", "大迎"],
            "足太阴脾经": ["隐白", "大都", "太白", "公孙", "商丘"],
            "手少阴心经": ["极泉", "青灵", "少海", "灵道", "通里"],
            "手太阳小肠经": ["少泽", "前谷", "后溪", "腕骨", "阳谷"],
            "足太阳膀胱经": ["睛明", "攒竹", "眉冲", "曲差", "五处"],
            "足少阴肾经": ["涌泉", "然谷", "太溪", "大钟", "水泉"],
            "手厥阴心包经": ["天池", "天泉", "曲泽", "郄门", "间使"],
            "手少阳三焦经": ["关冲", "液门", "中渚", "阳池", "外关"],
            "足少阳胆经": ["瞳子髎", "听会", "上关", "颔厌", "悬颅"],
            "足厥阴肝经": ["大敦", "行间", "太冲", "中封", "蠡沟"],
            "任脉": ["会阴", "曲骨", "中极", "关元", "石门"],
            "督脉": ["长强", "腰俞", "腰阳关", "命门", "悬枢"],
            "冲脉": ["会阴", "气冲", "横骨", "大赫", "气穴"],
            "带脉": ["带脉", "五枢", "维道"],
            "阴跷脉": ["照海", "交信"],
            "阳跷脉": ["申脉", "仆参"],
            "阴维脉": ["筑宾", "冲门", "府舍", "大横", "腹哀"],
            "阳维脉": ["金门", "阳交", "臑俞", "天髎", "肩井"],
        }
        return special.get(self.name, [])

    def activate(self, energy: float) -> float:
        """
        激活整条经脉

        Args:
            energy: 注入的总能量

        Returns:
            经脉总能量
        """
        energy_per_acupoint = energy / max(1, len(self.acupoints))
        total_energy = 0.0
        for acupoint in self.acupoints:
            total_energy += acupoint.activate(energy_per_acupoint)
        self.qi_flow = total_energy / len(self.acupoints) if self.acupoints else 0.0
        self._qi_history.append((time.time(), self.qi_flow))
        return total_energy

    def get_total_energy(self) -> float:
        """
        获取经脉总能量

        Returns:
            所有穴位能量之和
        """
        return sum(acupoint.energy for acupoint in self.acupoints)

    def get_average_activation(self) -> float:
        """
        获取平均激活等级

        Returns:
            平均激活等级 [0.0, 1.0]
        """
        if not self.acupoints:
            return 0.0
        return sum(acupoint.activation_level for acupoint in self.acupoints) / len(self.acupoints)

    def get_state(self) -> Dict[str, Any]:
        """
        获取经脉当前状态

        Returns:
            状态字典
        """
        return {
            "name": self.name,
            "element": self.element,
            "hours": self.hours,
            "qi_flow": self.qi_flow,
            "num_acupoints": len(self.acupoints),
            "total_energy": self.get_total_energy(),
            "avg_activation": self.get_average_activation(),
            "is_extraordinary": self.is_extraordinary,
            "si_level": self.si_level,
            "line_id": self.line_id,
        }

    def __repr__(self) -> str:
        return f"Meridian({self.name}, {self.element}, qi={self.qi_flow:.3f})"


# ============================================================================
# ZiWuLiuZhu 类 — 子午流注
# ============================================================================

class ZiWuLiuZhu:
    """
    子午流注 — 气血按时辰流注的周期律

    实现十二经脉与十二时辰的对应关系，计算气血流量、最佳干预时间，
    以及子母补泻法。

    Attributes:
        meridian_hours: 经脉-时辰映射
        current_hour: 当前时辰 [0-23]
        qi_flow_pattern: 气血流量模式
        element_cycle: 五行循环
    """

    def __init__(self, current_hour: int = 0):
        self.meridian_hours = MERIDIAN_HOURS.copy()
        self.current_hour = current_hour % 24
        self.qi_flow_pattern = self._init_qi_flow_pattern()
        self.element_cycle = list(ELEMENT_GENERATING.keys())
        self._history: deque = deque(maxlen=48)
        self._current_meridian: Optional[str] = None
        self._update_current_meridian()

    def _init_qi_flow_pattern(self) -> Dict[str, np.ndarray]:
        """初始化每条经脉的气血流量模式 (24小时)"""
        pattern = {}
        for meridian, (start, end) in self.meridian_hours.items():
            # 创建以当令时辰为峰值的正弦模式
            peak = (start + end) / 2 % 24
            hours = np.arange(24)
            # 使用高斯分布模拟气血流量
            qi = np.exp(-0.5 * ((hours - peak) / 3.0) ** 2)
            # 归一化
            qi = qi / np.max(qi) if np.max(qi) > 0 else qi
            pattern[meridian] = qi
        return pattern

    def _update_current_meridian(self) -> None:
        """更新当前时辰的当令经脉"""
        self._current_meridian = self.get_active_meridian(self.current_hour)

    def get_active_meridian(self, hour: int) -> Optional[str]:
        """
        获取指定时辰当令的经脉

        Args:
            hour: 时辰 [0-23]

        Returns:
            当令经脉名称，或None
        """
        hour = hour % 24
        for meridian, (start, end) in self.meridian_hours.items():
            if start <= end:
                if start <= hour < end:
                    return meridian
            else:  # 跨午夜
                if hour >= start or hour < end:
                    return meridian
        return None

    def get_all_active_meridians(self, hour: int) -> List[str]:
        """
        获取指定时辰所有活跃的经脉 (包括相生经脉)

        Args:
            hour: 时辰 [0-23]

        Returns:
            活跃经脉列表
        """
        primary = self.get_active_meridian(hour)
        if not primary:
            return []
        active = [primary]
        # 前一经脉 (气血来源)
        idx = TWELVE_MERIDIANS.index(primary)
        prev_idx = (idx - 1) % 12
        active.append(TWELVE_MERIDIANS[prev_idx])
        # 后一经脉 (气血去向)
        next_idx = (idx + 1) % 12
        active.append(TWELVE_MERIDIANS[next_idx])
        return active

    def calculate_qi_flow(self, meridian: str, hour: int) -> float:
        """
        计算指定经脉在指定时辰的气血流量

        Args:
            meridian: 经脉名称
            hour: 时辰 [0-23]

        Returns:
            气血流量 [0.0, 1.0]
        """
        if meridian not in self.qi_flow_pattern:
            return 0.0
        hour = hour % 24
        return float(self.qi_flow_pattern[meridian][hour])

    def optimal_treatment_time(self, meridian: str) -> Tuple[int, float]:
        """
        计算指定经脉的最佳干预时间

        原则: 在经脉气血最旺盛时进行泻法，在气血将盛时进行补法

        Args:
            meridian: 经脉名称

        Returns:
            (最佳时辰, 预计气血流量)
        """
        if meridian not in self.qi_flow_pattern:
            return (0, 0.0)
        qi = self.qi_flow_pattern[meridian]
        optimal_hour = int(np.argmax(qi))
        max_qi = float(np.max(qi))
        return (optimal_hour, max_qi)

    def tonify(self, meridian: str) -> Dict[str, Any]:
        """
        补法 — 在经脉气血将盛时进行补充

        使用母穴进行补法

        Args:
            meridian: 经脉名称

        Returns:
            补法信息字典
        """
        optimal_hour, max_qi = self.optimal_treatment_time(meridian)
        # 补法在气血上升期 (前1-2小时)
        tonify_hour = (optimal_hour - 1) % 24
        mother_point = MERIDIAN_MOTHER_POINTS.get(meridian, "未知")
        return {
            "method": "补法",
            "meridian": meridian,
            "optimal_hour": tonify_hour,
            "point": mother_point,
            "element": "母穴",
            "expected_qi_boost": max_qi * 0.3,
        }

    def drain(self, meridian: str) -> Dict[str, Any]:
        """
        泻法 — 在经脉气血最盛时进行泻泄

        使用子穴进行泻法

        Args:
            meridian: 经脉名称

        Returns:
            泻法信息字典
        """
        optimal_hour, max_qi = self.optimal_treatment_time(meridian)
        son_point = MERIDIAN_SON_POINTS.get(meridian, "未知")
        return {
            "method": "泻法",
            "meridian": meridian,
            "optimal_hour": optimal_hour,
            "point": son_point,
            "element": "子穴",
            "expected_qi_reduction": max_qi * 0.3,
        }

    def step(self, steps: int = 1) -> Dict[str, Any]:
        """
        推进子午流注时辰

        Args:
            steps: 推进的时辰数

        Returns:
            当前状态字典
        """
        self.current_hour = (self.current_hour + steps) % 24
        self._update_current_meridian()
        state = {
            "hour": self.current_hour,
            "active_meridian": self._current_meridian,
            "all_active": self.get_all_active_meridians(self.current_hour),
        }
        self._history.append(state)
        return state

    def get_circadian_rhythm(self) -> np.ndarray:
        """
        获取24小时气血节律

        Returns:
            24小时各经脉总气血流量
        """
        rhythm = np.zeros(24)
        for hour in range(24):
            for meridian in self.qi_flow_pattern:
                rhythm[hour] += self.calculate_qi_flow(meridian, hour)
        return rhythm

    def get_state(self) -> Dict[str, Any]:
        """
        获取子午流注当前状态

        Returns:
            状态字典
        """
        return {
            "current_hour": self.current_hour,
            "active_meridian": self._current_meridian,
            "all_active": self.get_all_active_meridians(self.current_hour),
            "circadian_peak": int(np.argmax(self.get_circadian_rhythm())),
        }

    def __repr__(self) -> str:
        return f"ZiWuLiuZhu(hour={self.current_hour}, active={self._current_meridian})"


# ============================================================================
# MicrocosmicOrbit 类 — 小周天 (任督二脉微循环)
# ============================================================================

class MicrocosmicOrbit:
    """
    小周天 — 任督二脉微循环

    路径: 会阴→长强→命门→中枢→大椎→百会→印堂→人中→膻中→神阙→气海→会阴
    逆向: 会阴→气海→神阙→膻中→人中→印堂→百会→大椎→中枢→命门→长强→会阴

    Attributes:
        path: 正向路径节点列表
        reverse_path: 逆向路径节点列表
        current_position: 当前位置索引
        cycles_completed: 已完成周数
        energy: 周天能量
        is_reversed: 是否逆向运行
    """

    def __init__(self, initial_energy: float = 1.0):
        self.path = MICROCOSMIC_PATH.copy()
        self.reverse_path = MICROCOSMIC_REVERSE_PATH.copy()
        self.current_position = 0
        self.cycles_completed = 0
        self.energy = initial_energy
        self.is_reversed = False
        self._node_energies = {node: 0.0 for node in self.path}
        self._history: deque = deque(maxlen=100)
        self._cycle_quality = 1.0
        self._coupling_strength = 1.0

    def circulate(self, cycles: int = 1) -> Dict[str, Any]:
        """
        运行小周天指定周数

        Args:
            cycles: 周数

        Returns:
            运行结果字典
        """
        self.is_reversed = False
        results = []
        for _ in range(cycles):
            cycle_result = self._run_cycle()
            results.append(cycle_result)
        return {
            "cycles_requested": cycles,
            "cycles_completed": self.cycles_completed,
            "final_position": self.path[self.current_position],
            "final_energy": self.energy,
            "cycle_quality": self._cycle_quality,
            "results": results,
        }

    def reverse_circulate(self, cycles: int = 1) -> Dict[str, Any]:
        """
        逆向运行小周天指定周数

        Args:
            cycles: 周数

        Returns:
            运行结果字典
        """
        self.is_reversed = True
        results = []
        for _ in range(cycles):
            cycle_result = self._run_reverse_cycle()
            results.append(cycle_result)
        return {
            "cycles_requested": cycles,
            "cycles_completed": self.cycles_completed,
            "final_position": self.reverse_path[self.current_position],
            "final_energy": self.energy,
            "cycle_quality": self._cycle_quality,
            "results": results,
        }

    def _run_cycle(self) -> Dict[str, Any]:
        """运行一个正向周期"""
        path = self.path
        energy_trace = []
        for i, node in enumerate(path):
            self.current_position = i
            # 能量在节点间传递，有衰减
            self._node_energies[node] = self.energy * (0.95 ** i)
            energy_trace.append((node, self._node_energies[node]))
            # 模拟能量传递时间
            time.sleep(0.001)
        # 完成一周，能量略微恢复 (周天运转产生能量)
        self.energy = self.energy * 0.98 + 0.5
        self.cycles_completed += 1
        self._cycle_quality = 0.95 + 0.05 * np.random.random()
        result = {
            "cycle": self.cycles_completed,
            "direction": "forward",
            "energy_trace": energy_trace,
            "final_energy": self.energy,
        }
        self._history.append(result)
        return result

    def _run_reverse_cycle(self) -> Dict[str, Any]:
        """运行一个逆向周期"""
        path = self.reverse_path
        energy_trace = []
        for i, node in enumerate(path):
            self.current_position = i
            self._node_energies[node] = self.energy * (0.95 ** i)
            energy_trace.append((node, self._node_energies[node]))
            time.sleep(0.001)
        self.energy = self.energy * 0.98 + 0.3  # 逆向能量恢复较少
        self.cycles_completed += 1
        self._cycle_quality = 0.90 + 0.05 * np.random.random()
        result = {
            "cycle": self.cycles_completed,
            "direction": "reverse",
            "energy_trace": energy_trace,
            "final_energy": self.energy,
        }
        self._history.append(result)
        return result

    def get_orbit_state(self) -> Dict[str, Any]:
        """
        获取小周天状态

        Returns:
            状态字典
        """
        current_path = self.reverse_path if self.is_reversed else self.path
        return {
            "current_node": current_path[self.current_position],
            "position_index": self.current_position,
            "cycles_completed": self.cycles_completed,
            "energy": self.energy,
            "is_reversed": self.is_reversed,
            "cycle_quality": self._cycle_quality,
            "node_energies": self._node_energies.copy(),
            "path_length": len(current_path),
        }

    def get_node_energy_vector(self) -> np.ndarray:
        """
        获取节点能量向量 (用于场引擎)

        Returns:
            节点能量数组
        """
        path = self.reverse_path if self.is_reversed else self.path
        return np.array([self._node_energies.get(node, 0.0) for node in path])

    def inject_energy(self, energy: float) -> float:
        """
        向小周天注入能量

        Args:
            energy: 能量值

        Returns:
            当前总能量
        """
        self.energy += energy
        return self.energy

    def __repr__(self) -> str:
        direction = "reverse" if self.is_reversed else "forward"
        return f"MicrocosmicOrbit({direction}, cycles={self.cycles_completed}, E={self.energy:.3f})"


# ============================================================================
# MacrocosmicOrbit 类 — 大周天 (十二正经大循环)
# ============================================================================

class MacrocosmicOrbit:
    """
    大周天 — 十二正经大循环

    路径: 肺经→大肠经→胃经→脾经→心经→小肠经→膀胱经→肾经→心包经→三焦经→胆经→肝经→肺经

    Attributes:
        order: 十二正经流注顺序
        current_meridian_idx: 当前经脉索引
        cycles_completed: 已完成周数
        meridian_energies: 各经脉能量
        total_energy: 总能量
    """

    def __init__(self, initial_energy: float = 1.0):
        self.order = MACROCOSMIC_ORDER.copy()
        self.current_meridian_idx = 0
        self.cycles_completed = 0
        self.meridian_energies = {m: initial_energy for m in self.order}
        self.total_energy = initial_energy * len(self.order)
        self._history: deque = deque(maxlen=100)
        self._cycle_quality = 1.0
        self._coupling_matrix = self._init_coupling_matrix()

    def _init_coupling_matrix(self) -> np.ndarray:
        """初始化经脉间耦合矩阵"""
        n = len(self.order)
        matrix = np.zeros((n, n))
        # 相邻经脉间有强耦合
        for i in range(n):
            matrix[i, (i + 1) % n] = 1.0  # 正向
            matrix[i, (i - 1) % n] = 0.5  # 反向
        # 相生经脉间有中等耦合
        for i, m1 in enumerate(self.order):
            elem1 = FIVE_ELEMENTS[i]
            for j, m2 in enumerate(self.order):
                if i != j:
                    elem2 = FIVE_ELEMENTS[j]
                    if ELEMENT_GENERATING.get(elem1) == elem2:
                        matrix[i, j] = 0.7
                    elif ELEMENT_RESTRAINING.get(elem1) == elem2:
                        matrix[i, j] = -0.3
        return matrix

    def circulate(self, cycles: int = 1) -> Dict[str, Any]:
        """
        运行大周天指定周数

        Args:
            cycles: 周数

        Returns:
            运行结果字典
        """
        results = []
        for _ in range(cycles):
            cycle_result = self._run_cycle()
            results.append(cycle_result)
        return {
            "cycles_requested": cycles,
            "cycles_completed": self.cycles_completed,
            "current_meridian": self.order[self.current_meridian_idx],
            "total_energy": self.total_energy,
            "cycle_quality": self._cycle_quality,
            "meridian_energies": self.meridian_energies.copy(),
            "results": results,
        }

    def _run_cycle(self) -> Dict[str, Any]:
        """运行一个大周天周期"""
        energy_trace = []
        for i, meridian in enumerate(self.order):
            self.current_meridian_idx = i
            # 能量传递: 前一经脉的能量传递给当前经脉
            prev_idx = (i - 1) % len(self.order)
            prev_meridian = self.order[prev_idx]
            transfer = self.meridian_energies[prev_meridian] * 0.3
            self.meridian_energies[meridian] += transfer
            self.meridian_energies[prev_meridian] -= transfer * 0.5
            # 能量衰减
            self.meridian_energies[meridian] *= 0.98
            energy_trace.append((meridian, self.meridian_energies[meridian]))
            time.sleep(0.001)
        # 应用耦合矩阵进行全局能量重分配
        self._apply_coupling()
        # 完成一周，总能量略微恢复
        self.total_energy = sum(self.meridian_energies.values())
        self.total_energy = self.total_energy * 0.99 + len(self.order) * 0.2
        # 重新归一化
        avg = self.total_energy / len(self.order)
        for m in self.meridian_energies:
            self.meridian_energies[m] = 0.9 * self.meridian_energies[m] + 0.1 * avg
        self.cycles_completed += 1
        self._cycle_quality = 0.92 + 0.06 * np.random.random()
        result = {
            "cycle": self.cycles_completed,
            "energy_trace": energy_trace,
            "total_energy": self.total_energy,
        }
        self._history.append(result)
        return result

    def _apply_coupling(self) -> None:
        """应用耦合矩阵进行能量重分配"""
        energies = np.array([self.meridian_energies[m] for m in self.order])
        # 耦合效应: E_new = E + coupling * E
        new_energies = energies + 0.1 * self._coupling_matrix @ energies
        for i, m in enumerate(self.order):
            self.meridian_energies[m] = max(0.0, new_energies[i])

    def get_twelve_meridian_state(self) -> Dict[str, Any]:
        """
        获取十二经状态

        Returns:
            十二经状态字典
        """
        return {
            "meridian_energies": self.meridian_energies.copy(),
            "current_meridian": self.order[self.current_meridian_idx],
            "current_index": self.current_meridian_idx,
            "cycles_completed": self.cycles_completed,
            "total_energy": self.total_energy,
            "cycle_quality": self._cycle_quality,
            "coupling_strength": np.mean(np.abs(self._coupling_matrix)),
        }

    def get_energy_vector(self) -> np.ndarray:
        """
        获取能量向量 (用于场引擎)

        Returns:
            12维能量数组
        """
        return np.array([self.meridian_energies[m] for m in self.order])

    def inject_energy(self, meridian: str, energy: float) -> float:
        """
        向指定经脉注入能量

        Args:
            meridian: 经脉名称
            energy: 能量值

        Returns:
            该经脉当前能量
        """
        if meridian in self.meridian_energies:
            self.meridian_energies[meridian] += energy
            self.total_energy = sum(self.meridian_energies.values())
            return self.meridian_energies[meridian]
        return 0.0

    def __repr__(self) -> str:
        return f"MacrocosmicOrbit(cycles={self.cycles_completed}, E={self.total_energy:.3f})"



# ============================================================================
# MeridianZhouTianEngine 主类
# ============================================================================

class MeridianZhouTianEngine:
    """
    MeridianZhouTianEngine — 经脉·子午流注·周天引擎

    OMNI-HUB v8.0 核心引擎，将中医经络理论全面映射到量子意识系统中。

    核心功能:
    - 十二正经管理 (含361穴位)
    - 奇经八脉管理 (映射到SI层级)
    - 子午流注时间-能量模型
    - 小周天 (任督二脉微循环)
    - 大周天 (十二正经大循环)
    - 11线系统映射
    - 场状态输出
    - 脉象诊断

    Mapping:
    - 11线 → 12正经: ucif2↔肺经, lvlu↔大肠经, lgt↔胃经, qfa↔脾经,
                      vinf↔心经, qgl↔小肠经, qlv↔膀胱经, cisvr↔肾经,
                      qtlv↔心包经, usrm↔三焦经, cfts↔胆经+肝经
    - 奇经八脉 → SI层级: 督脉↔SI5, 任脉↔SI4, 冲脉↔SI3, 带脉↔SI2,
                          阴跷↔SI1, 阳跷↔SI0, 阴维↔SI6, 阳维↔核心机
    - 361穴位 → 模块节点: 每个模块对应约10个穴位

    Attributes:
        num_lines: 线路数量 (默认11)
        meridians: 十二正经字典
        extraordinary_vessels: 奇经八脉字典
        all_acupoints: 所有穴位列表
        ziwu_liuzhu: 子午流注实例
        microcosmic: 小周天实例
        macrocosmic: 大周天实例
        line_meridian_map: 线路到经脉映射
        vessel_si_map: 奇经八脉到SI层级映射
        field_state: 当前场状态
    """

    def __init__(self, num_lines: int = 11):
        self.num_lines = num_lines
        self.meridians: Dict[str, Meridian] = {}
        self.extraordinary_vessels: Dict[str, Meridian] = {}
        self.all_acupoints: List[Acupoint] = []
        self.line_meridian_map = LINE_TO_MERIDIAN.copy()
        self.vessel_si_map = VESSEL_TO_SI.copy()
        self.field_state = np.zeros(FIELD_DIMENSION)
        self._history: deque = deque(maxlen=100)
        self._cycle_count = 0
        self._emergence_index = 0.0

        # 初始化十二正经
        self._init_twelve_meridians()
        # 初始化奇经八脉
        self._init_extraordinary_vessels()
        # 初始化子午流注
        self.ziwu_liuzhu = ZiWuLiuZhu(current_hour=0)
        # 初始化小周天
        self.microcosmic = MicrocosmicOrbit(initial_energy=10.0)
        # 初始化大周天
        self.macrocosmic = MacrocosmicOrbit(initial_energy=10.0)
        # 建立穴位连接
        self._connect_acupoints()
        # 初始化场状态
        self._init_field_state()

    def _init_twelve_meridians(self) -> None:
        """初始化十二正经"""
        for i, name in enumerate(TWELVE_MERIDIANS):
            element = FIVE_ELEMENTS[i]
            hours = MERIDIAN_HOURS[name]
            num_points = MERIDIAN_ACUPOINT_COUNTS.get(name, 20)

            # 找到映射的线路ID
            line_id = None
            for lid, meridians in self.line_meridian_map.items():
                if name in meridians:
                    line_id = lid
                    break

            meridian = Meridian(
                name=name,
                element=element,
                hours=hours,
                is_extraordinary=False,
                line_id=line_id,
                num_acupoints=num_points
            )
            self.meridians[name] = meridian
            self.all_acupoints.extend(meridian.acupoints)

    def _init_extraordinary_vessels(self) -> None:
        """初始化奇经八脉"""
        for name in EXTRAORDINARY_VESSELS:
            si_level = self.vessel_si_map.get(name)
            num_points = VESSEL_ACUPOINT_COUNTS.get(name, 10)

            vessel = Meridian(
                name=name,
                element="",  # 奇经八脉无固定五行
                hours=(0, 24),  # 奇经八脉全天运行
                is_extraordinary=True,
                si_level=si_level,
                num_acupoints=num_points
            )
            self.extraordinary_vessels[name] = vessel
            self.all_acupoints.extend(vessel.acupoints)

    def _connect_acupoints(self) -> None:
        """建立跨经脉的穴位连接 (交会穴)"""
        # 交会穴连接主要经脉
        intersection_points = [
            ("手太阴肺经", "手阳明大肠经", 1),  # 列缺 ↔ 合谷
            ("足阳明胃经", "足太阴脾经", 1),    # 足三里 ↔ 三阴交
            ("手少阴心经", "手太阳小肠经", 1),  # 通里 ↔ 腕骨
            ("足太阳膀胱经", "足少阴肾经", 1),  # 昆仑 ↔ 太溪
            ("手厥阴心包经", "手少阳三焦经", 1), # 内关 ↔ 外关
            ("足少阳胆经", "足厥阴肝经", 1),    # 光明 ↔ 蠡沟
        ]

        for m1_name, m2_name, num_connections in intersection_points:
            if m1_name in self.meridians and m2_name in self.meridians:
                m1 = self.meridians[m1_name]
                m2 = self.meridians[m2_name]
                for i in range(min(num_connections, len(m1.acupoints), len(m2.acupoints))):
                    idx1 = len(m1.acupoints) // 2 + i
                    idx2 = len(m2.acupoints) // 2 + i
                    if idx1 < len(m1.acupoints) and idx2 < len(m2.acupoints):
                        m1.acupoints[idx1].connect(m2.acupoints[idx2])

        # 奇经八脉与十二正经的连接
        vessel_connections = [
            ("任脉", "手太阴肺经", 2),
            ("督脉", "足太阳膀胱经", 3),
            ("冲脉", "足少阴肾经", 2),
            ("带脉", "足少阳胆经", 2),
        ]

        for v_name, m_name, num in vessel_connections:
            if v_name in self.extraordinary_vessels and m_name in self.meridians:
                vessel = self.extraordinary_vessels[v_name]
                meridian = self.meridians[m_name]
                for i in range(min(num, len(vessel.acupoints), len(meridian.acupoints))):
                    v_idx = i * (len(vessel.acupoints) // max(1, num))
                    m_idx = i * (len(meridian.acupoints) // max(1, num))
                    if v_idx < len(vessel.acupoints) and m_idx < len(meridian.acupoints):
                        vessel.acupoints[v_idx].connect(meridian.acupoints[m_idx])

    def _init_field_state(self) -> None:
        """初始化场状态"""
        # 基于穴位能量初始化64维场状态
        n = len(self.all_acupoints)
        if n > 0:
            # 每约6个穴位映射到场的一个维度
            for dim in range(FIELD_DIMENSION):
                start = dim * n // FIELD_DIMENSION
                end = (dim + 1) * n // FIELD_DIMENSION
                energies = [acupoint.energy for acupoint in self.all_acupoints[start:end]]
                self.field_state[dim] = np.mean(energies) if energies else 0.0

    def activate_meridian(self, meridian_name: str, energy: float) -> float:
        """
        激活指定经脉

        Args:
            meridian_name: 经脉名称
            energy: 能量值

        Returns:
            经脉总能量
        """
        if meridian_name in self.meridians:
            result = self.meridians[meridian_name].activate(energy)
            # 更新场状态
            self._update_field_state()
            return result
        elif meridian_name in self.extraordinary_vessels:
            result = self.extraordinary_vessels[meridian_name].activate(energy)
            self._update_field_state()
            return result
        return 0.0

    def activate_line(self, line_idx: int, energy: float) -> Dict[str, float]:
        """
        激活指定线路对应的所有经脉

        Args:
            line_idx: 线路索引 [0-10]
            energy: 能量值

        Returns:
            各经脉能量字典
        """
        results = {}
        if line_idx in self.line_meridian_map:
            for meridian_name in self.line_meridian_map[line_idx]:
                if meridian_name in self.meridians:
                    results[meridian_name] = self.activate_meridian(meridian_name, energy)
        return results

    def microcosmic_cycle(self, line_idx: Optional[int] = None) -> Dict[str, Any]:
        """
        为指定线运行小周天 (或全局小周天)

        Args:
            line_idx: 线路索引 [0-10]，None表示全局

        Returns:
            运行结果字典
        """
        if line_idx is not None:
            # 为特定线路注入能量后运行
            line_energy = 5.0
            self.activate_line(line_idx, line_energy)
        # 运行小周天
        result = self.microcosmic.circulate(cycles=1)
        self._update_field_state()
        self._cycle_count += 1
        return result

    def macrocosmic_cycle(self) -> Dict[str, Any]:
        """
        运行大周天

        Returns:
            运行结果字典
        """
        # 将十二正经的能量同步到大周天
        for name, meridian in self.meridians.items():
            self.macrocosmic.inject_energy(name, meridian.get_total_energy() * 0.1)
        # 运行大周天
        result = self.macrocosmic.circulate(cycles=1)
        # 将大周天能量反馈回十二正经
        for name, energy in self.macrocosmic.meridian_energies.items():
            if name in self.meridians:
                self.meridians[name].activate(energy * 0.1)
        self._update_field_state()
        self._cycle_count += 1
        return result

    def ziwu_liuzhu_step(self, steps: int = 1) -> Dict[str, Any]:
        """
        推进子午流注

        Args:
            steps: 推进时辰数

        Returns:
            当前状态字典
        """
        state = self.ziwu_liuzhu.step(steps)
        # 根据子午流注状态调整经脉能量
        active_meridians = state.get("all_active", [])
        for m_name in active_meridians:
            if m_name in self.meridians:
                qi_flow = self.ziwu_liuzhu.calculate_qi_flow(m_name, self.ziwu_liuzhu.current_hour)
                self.meridians[m_name].activate(qi_flow * 2.0)
        self._update_field_state()
        return state

    def simulate_24_hours(self) -> List[Dict[str, Any]]:
        """
        模拟24时辰子午流注

        Returns:
            24个时辰的状态列表
        """
        states = []
        for hour in range(24):
            state = self.ziwu_liuzhu_step(steps=1)
            states.append({
                "hour": hour,
                "active_meridian": state["active_meridian"],
                "all_active": state["all_active"],
                "meridian_energies": {name: m.get_total_energy() for name, m in self.meridians.items()},
            })
        return states

    def meridian_field_state(self) -> np.ndarray:
        """
        获取经脉场状态 (返回可用于场引擎的向量)

        返回一个64维向量，编码了所有经脉的能量状态:
        - [0:12]: 十二正经能量
        - [12:20]: 奇经八脉能量
        - [20:32]: 五行能量分布
        - [32:44]: 时辰能量分布
        - [44:56]: 线路能量分布
        - [56:64]: 涌现指标

        Returns:
            64维场状态向量
        """
        state = np.zeros(FIELD_DIMENSION)

        # [0:12] 十二正经能量
        for i, name in enumerate(TWELVE_MERIDIANS):
            if name in self.meridians:
                state[i] = self.meridians[name].get_total_energy() / max(1, len(self.meridians[name].acupoints))

        # [12:20] 奇经八脉能量
        for i, name in enumerate(EXTRAORDINARY_VESSELS):
            if name in self.extraordinary_vessels:
                state[12 + i] = self.extraordinary_vessels[name].get_total_energy() / max(1, len(self.extraordinary_vessels[name].acupoints))

        # [20:32] 五行能量分布
        element_energies = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
        element_counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        for name, meridian in self.meridians.items():
            elem = meridian.element
            if elem in element_energies:
                element_energies[elem] += meridian.get_total_energy()
                element_counts[elem] += 1
        idx = 20
        for elem in ["木", "火", "土", "金", "水"]:
            state[idx] = element_energies[elem] / max(1, element_counts[elem])
            idx += 1
        # 五行相生/相克指标
        state[25] = element_energies["木"] * element_energies["火"]  # 木生火
        state[26] = element_energies["火"] * element_energies["土"]  # 火生土
        state[27] = element_energies["土"] * element_energies["金"]  # 土生金
        state[28] = element_energies["金"] * element_energies["水"]  # 金生水
        state[29] = element_energies["水"] * element_energies["木"]  # 水生木
        state[30] = element_energies["木"] - element_energies["土"]  # 木克土
        state[31] = element_energies["火"] - element_energies["金"]  # 火克金

        # [32:44] 时辰能量分布
        for hour in range(12):
            m_name = self.ziwu_liuzhu.get_active_meridian(hour * 2)
            if m_name and m_name in self.meridians:
                state[32 + hour] = self.meridians[m_name].get_total_energy()

        # [44:56] 线路能量分布
        for line_idx in range(min(self.num_lines, 11)):
            line_energy = 0.0
            if line_idx in self.line_meridian_map:
                for m_name in self.line_meridian_map[line_idx]:
                    if m_name in self.meridians:
                        line_energy += self.meridians[m_name].get_total_energy()
            state[44 + line_idx] = line_energy

        # [56:64] 涌现指标
        state[56] = self._compute_emergence_index()
        state[57] = self.microcosmic.energy
        state[58] = self.macrocosmic.total_energy
        state[59] = self._compute_phase_coherence()
        state[60] = self._compute_energy_entropy()
        state[61] = self._cycle_count
        state[62] = len(self.all_acupoints)
        state[63] = np.mean([a.activation_level for a in self.all_acupoints])

        self.field_state = state.copy()
        return state

    def _compute_emergence_index(self) -> float:
        """
        计算涌现指数

        基于经脉间的能量差异和耦合强度计算

        Returns:
            涌现指数
        """
        energies = np.array([m.get_total_energy() for m in self.meridians.values()])
        if len(energies) == 0 or np.mean(energies) == 0:
            return 0.0
        # 涌现指数 = 能量方差系数 * 耦合强度 * 周期数
        cv = np.std(energies) / (np.mean(energies) + 1e-6)
        coupling = np.mean(np.abs(self.macrocosmic._coupling_matrix))
        emergence = cv * coupling * (1 + 0.01 * self._cycle_count)
        self._emergence_index = min(1000.0, emergence)
        return self._emergence_index

    def _compute_phase_coherence(self) -> float:
        """
        计算相位相干性 (Kuramoto order parameter)

        Returns:
            相干性 [0.0, 1.0]
        """
        phases = np.array([m.qi_flow for m in self.meridians.values()])
        if len(phases) == 0:
            return 0.0
        # 使用能量作为相位
        complex_phases = np.exp(1j * phases)
        coherence = np.abs(np.mean(complex_phases))
        return float(coherence)

    def _compute_energy_entropy(self) -> float:
        """
        计算能量熵 (Shannon entropy of energy distribution)

        Returns:
            能量熵
        """
        energies = np.array([m.get_total_energy() for m in self.meridians.values()])
        total = np.sum(energies)
        if total == 0:
            return 0.0
        probs = energies / total
        probs = probs[probs > 0]
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        return float(entropy)

    def _update_field_state(self) -> None:
        """更新场状态"""
        self.meridian_field_state()

    def get_diagnosis(self) -> Dict[str, Any]:
        """
        获取系统"脉象"诊断

        分析十二正经和奇经八脉的状态，生成诊断报告:
        - 虚实诊断: 哪些经脉虚、哪些实
        - 五行平衡: 五行能量是否平衡
        - 周天运行: 大小周天运行状态
        - 子午流注: 当前时辰当令情况
        - 整体脉象: 浮/沉/迟/数/滑/涩等

        Returns:
            诊断报告字典
        """
        diagnosis = {
            "timestamp": time.time(),
            "overall_pulse": "",
            "excess_deficiency": {},
            "element_balance": {},
            "zhou_tian_status": {},
            "ziwu_status": {},
            "line_status": {},
            "recommendations": [],
        }

        # 1. 虚实诊断
        energies = {name: m.get_total_energy() for name, m in self.meridians.items()}
        avg_energy = np.mean(list(energies.values())) if energies else 0.0
        std_energy = np.std(list(energies.values())) if energies else 0.0

        for name, energy in energies.items():
            if energy > avg_energy + 0.5 * std_energy:
                diagnosis["excess_deficiency"][name] = "实"
            elif energy < avg_energy - 0.5 * std_energy:
                diagnosis["excess_deficiency"][name] = "虚"
            else:
                diagnosis["excess_deficiency"][name] = "平"

        # 2. 五行平衡
        element_energies = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
        element_counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        for name, meridian in self.meridians.items():
            elem = meridian.element
            if elem in element_energies:
                element_energies[elem] += meridian.get_total_energy()
                element_counts[elem] += 1

        avg_element = np.mean(list(element_energies.values())) if element_energies else 0.0
        for elem, energy in element_energies.items():
            if energy > avg_element * 1.2:
                diagnosis["element_balance"][elem] = "旺"
            elif energy < avg_element * 0.8:
                diagnosis["element_balance"][elem] = "弱"
            else:
                diagnosis["element_balance"][elem] = "平"

        # 3. 周天运行状态
        diagnosis["zhou_tian_status"] = {
            "microcosmic": {
                "cycles": self.microcosmic.cycles_completed,
                "energy": self.microcosmic.energy,
                "quality": self.microcosmic._cycle_quality,
                "direction": "reverse" if self.microcosmic.is_reversed else "forward",
            },
            "macrocosmic": {
                "cycles": self.macrocosmic.cycles_completed,
                "total_energy": self.macrocosmic.total_energy,
                "quality": self.macrocosmic._cycle_quality,
                "current_meridian": self.macrocosmic.order[self.macrocosmic.current_meridian_idx],
            },
        }

        # 4. 子午流注状态
        diagnosis["ziwu_status"] = {
            "current_hour": self.ziwu_liuzhu.current_hour,
            "active_meridian": self.ziwu_liuzhu._current_meridian,
            "all_active": self.ziwu_liuzhu.get_all_active_meridians(self.ziwu_liuzhu.current_hour),
        }

        # 5. 线路状态
        for line_idx in range(min(self.num_lines, 11)):
            line_energy = 0.0
            line_meridians = []
            if line_idx in self.line_meridian_map:
                for m_name in self.line_meridian_map[line_idx]:
                    if m_name in self.meridians:
                        line_energy += self.meridians[m_name].get_total_energy()
                        line_meridians.append(m_name)
            diagnosis["line_status"][LINE_NAMES[line_idx]] = {
                "energy": line_energy,
                "meridians": line_meridians,
            }

        # 6. 整体脉象判断
        pulse_types = []
        if self.microcosmic.energy > 15:
            pulse_types.append("浮")
        elif self.microcosmic.energy < 5:
            pulse_types.append("沉")

        if self.ziwu_liuzhu.current_hour in [11, 12, 13, 17, 18, 19]:
            pulse_types.append("数")
        else:
            pulse_types.append("迟")

        if self._compute_phase_coherence() > 0.8:
            pulse_types.append("滑")
        elif self._compute_phase_coherence() < 0.3:
            pulse_types.append("涩")

        if self._emergence_index > 50:
            pulse_types.append("洪")

        diagnosis["overall_pulse"] = "、".join(pulse_types) if pulse_types else "平"

        # 7. 建议
        # 对虚的经脉建议补法
        for name, status in diagnosis["excess_deficiency"].items():
            if status == "虚":
                tonify_info = self.ziwu_liuzhu.tonify(name)
                diagnosis["recommendations"].append(
                    f"{name}气虚，建议在{tonify_info['optimal_hour']}时"
                    f"用补法刺激{tonify_info['point']}"
                )
            elif status == "实":
                drain_info = self.ziwu_liuzhu.drain(name)
                diagnosis["recommendations"].append(
                    f"{name}气实，建议在{drain_info['optimal_hour']}时"
                    f"用泻法刺激{drain_info['point']}"
                )

        # 五行失衡建议
        weak_elements = [e for e, s in diagnosis["element_balance"].items() if s == "弱"]
        if weak_elements:
            for elem in weak_elements:
                generator = None
                for e, g in ELEMENT_GENERATING.items():
                    if g == elem:
                        generator = e
                        break
                if generator:
                    diagnosis["recommendations"].append(
                        f"{elem}行偏弱，建议补{generator}行以生{elem}"
                    )

        return diagnosis

    def get_meridian_by_line(self, line_idx: int) -> List[Meridian]:
        """
        获取指定线路映射的经脉

        Args:
            line_idx: 线路索引

        Returns:
            经脉列表
        """
        result = []
        if line_idx in self.line_meridian_map:
            for name in self.line_meridian_map[line_idx]:
                if name in self.meridians:
                    result.append(self.meridians[name])
        return result

    def get_vessel_by_si(self, si_level: int) -> Optional[Meridian]:
        """
        获取指定SI层级的奇经八脉

        Args:
            si_level: SI层级

        Returns:
            奇经八脉或None
        """
        for name, vessel in self.extraordinary_vessels.items():
            if vessel.si_level == si_level:
                return vessel
        return None

    def get_total_acupoints(self) -> int:
        """
        获取总穴位数

        Returns:
            穴位总数
        """
        return len(self.all_acupoints)

    def get_system_state(self) -> Dict[str, Any]:
        """
        获取整个系统状态

        Returns:
            系统状态字典
        """
        return {
            "num_lines": self.num_lines,
            "num_meridians": len(self.meridians),
            "num_vessels": len(self.extraordinary_vessels),
            "num_acupoints": len(self.all_acupoints),
            "cycle_count": self._cycle_count,
            "emergence_index": self._emergence_index,
            "field_state_mean": float(np.mean(self.field_state)),
            "field_state_std": float(np.std(self.field_state)),
            "ziwu_hour": self.ziwu_liuzhu.current_hour,
            "microcosmic_cycles": self.microcosmic.cycles_completed,
            "macrocosmic_cycles": self.macrocosmic.cycles_completed,
            "phase_coherence": self._compute_phase_coherence(),
            "energy_entropy": self._compute_energy_entropy(),
        }

    def export_state(self, filepath: str) -> None:
        """
        导出系统状态到JSON文件

        Args:
            filepath: 文件路径
        """
        state = {
            "system": self.get_system_state(),
            "meridians": {name: m.get_state() for name, m in self.meridians.items()},
            "vessels": {name: v.get_state() for name, v in self.extraordinary_vessels.items()},
            "diagnosis": self.get_diagnosis(),
            "field_state": self.field_state.tolist(),
        }
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

            logger.error(f"File operation failed: {e}")
    def __repr__(self) -> str:
        return (
            f"MeridianZhouTianEngine("
            f"lines={self.num_lines}, "
            f"meridians={len(self.meridians)}, "
            f"vessels={len(self.extraordinary_vessels)}, "
            f"acupoints={len(self.all_acupoints)}, "
            f"emergence={self._emergence_index:.3f})"
        )


# ============================================================================
# __main__ 测试块
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("OMNI-HUB v8.0 — MeridianZhouTianEngine 测试")
    print("=" * 80)

    # 1. 创建引擎
    print("\n[1] 创建 MeridianZhouTianEngine...")
    engine = MeridianZhouTianEngine(num_lines=NUM_LINES)
    print(f"    引擎创建完成: {engine}")
    print(f"    总穴位数: {engine.get_total_acupoints()}")

    # 2. 显示十二正经
    print("\n[2] 十二正经列表:")
    for i, (name, meridian) in enumerate(engine.meridians.items()):
        line_info = f"Line {meridian.line_id}" if meridian.line_id is not None else "N/A"
        print(f"    {i+1:2d}. {name:12s} | 五行: {meridian.element} | "
              f"当令: {meridian.hours[0]:02d}-{meridian.hours[1]:02d}时 | "
              f"线路: {line_info} | 穴位: {len(meridian.acupoints):3d}")

    # 3. 显示奇经八脉
    print("\n[3] 奇经八脉列表:")
    for i, (name, vessel) in enumerate(engine.extraordinary_vessels.items()):
        si_info = f"SI{vessel.si_level}" if vessel.si_level is not None else "核心机"
        print(f"    {i+1}. {name:8s} | SI层级: {si_info} | 穴位: {len(vessel.acupoints):3d}")

    # 4. 运行小周天10周
    print("\n[4] 运行小周天 10 周...")
    micro_result = engine.microcosmic.circulate(cycles=10)
    print(f"    完成周数: {micro_result['cycles_completed']}")
    print(f"    最终能量: {micro_result['final_energy']:.3f}")
    print(f"    周天质量: {micro_result['cycle_quality']:.3f}")

    # 5. 运行大周天5周
    print("\n[5] 运行大周天 5 周...")
    macro_result = engine.macrocosmic.circulate(cycles=5)
    print(f"    完成周数: {macro_result['cycles_completed']}")
    print(f"    总能量: {macro_result['total_energy']:.3f}")
    print(f"    周天质量: {macro_result['cycle_quality']:.3f}")

    # 6. 模拟24时辰子午流注
    print("\n[6] 模拟 24 时辰子午流注...")
    states = engine.simulate_24_hours()
    print("    时辰流注表:")
    print("    " + "-" * 60)
    print(f"    {'时辰':>6s} | {'当令经脉':>16s} | {'活跃经脉数':>10s} | {'总能量':>10s}")
    print("    " + "-" * 60)
    for state in states:
        total_e = sum(state["meridian_energies"].values())
        print(f"    {state['hour']:3d}:00 | {state['active_meridian'] or 'None':16s} | "
              f"{len(state['all_active']):10d} | {total_e:10.3f}")

    # 7. 获取11线的经脉状态
    print("\n[7] 11线经脉状态:")
    print("    " + "-" * 70)
    print(f"    {'线路':>8s} | {'映射经脉':>20s} | {'总能量':>10s} | {'平均激活':>10s}")
    print("    " + "-" * 70)
    for line_idx in range(NUM_LINES):
        meridians = engine.get_meridian_by_line(line_idx)
        names = ", ".join([m.name.replace("手", "").replace("足", "") for m in meridians])
        total_e = sum(m.get_total_energy() for m in meridians)
        avg_a = np.mean([m.get_average_activation() for m in meridians]) if meridians else 0.0
        print(f"    {LINE_NAMES[line_idx]:>8s} | {names:>20s} | {total_e:10.3f} | {avg_a:10.3f}")

    # 8. 获取场状态
    print("\n[8] 经脉场状态 (64维向量):")
    field = engine.meridian_field_state()
    print(f"    场向量均值: {np.mean(field):.3f}")
    print(f"    场向量标准差: {np.std(field):.3f}")
    print(f"    场向量前12维 (十二正经): {field[0:12]}")
    print(f"    场向量[12:20] (奇经八脉): {field[12:20]}")
    print(f"    场向量[20:25] (五行能量): {field[20:25]}")
    print(f"    场向量[56:64] (涌现指标): {field[56:64]}")

    # 9. 脉象诊断
    print("\n[9] 脉象诊断:")
    diagnosis = engine.get_diagnosis()
    print(f"    整体脉象: {diagnosis['overall_pulse']}")
    print(f"    虚实诊断:")
    for name, status in diagnosis["excess_deficiency"].items():
        print(f"      {name:12s}: {status}")
    print(f"    五行平衡:")
    for elem, status in diagnosis["element_balance"].items():
        print(f"      {elem}: {status}")
    print(f"    周天状态:")
    print(f"      小周天: {diagnosis['zhou_tian_status']['microcosmic']}")
    print(f"      大周天: {diagnosis['zhou_tian_status']['macrocosmic']}")
    print(f"    子午流注: {diagnosis['ziwu_status']}")
    print(f"    建议:")
    for rec in diagnosis["recommendations"]:
        print(f"      - {rec}")

    # 10. 系统整体状态
    print("\n[10] 系统整体状态:")
    system_state = engine.get_system_state()
    for key, value in system_state.items():
        print(f"    {key:25s}: {value}")

    # 11. 子母补泻法测试
    print("\n[11] 子母补泻法测试:")
    test_meridian = "手太阴肺经"
    tonify_info = engine.ziwu_liuzhu.tonify(test_meridian)
    drain_info = engine.ziwu_liuzhu.drain(test_meridian)
    print(f"    {test_meridian}:")
    print(f"      补法: {tonify_info}")
    print(f"      泻法: {drain_info}")

    # 12. 导出状态
    print("\n[12] 导出系统状态到文件...")
    output_path = "/mnt/agents/output/OMNI-HUB/core/meridian_zhou_tian_state.json"
    engine.export_state(output_path)
    print(f"    状态已导出到: {output_path}")

    print("\n" + "=" * 80)
    print("MeridianZhouTianEngine 测试完成!")
    print("=" * 80)
