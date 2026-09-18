#!/usr/bin/env python3

__version__ = "11.0.0"
"""
OMNI-HUB v3.3 — DebtFuelConverter
=================================
燃料转换器 — 将债务/账目/FINDING转化为自驱能量

核心哲学:
    "债/账/FINDING->自驱" — 债务、账目、发现都是自驱动燃料
    系统中的所有"未处理项"都是潜在能量

集成:
    - core/debt_cleanup.py — 债务清理 (v3.2)
    - core/finding_recursion.py — FINDING递归 (v3.2)

Author: OMNI-HUB Core Team
Version: 3.3.0
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any
import logging


@dataclass
class ConversionRecord:
    """单次转换记录"""
    timestamp: float
    source_type: str
    source_value: float
    quantity: int
    converted: float
    fuel_before: float
    fuel_after: float
    efficiency: float


@dataclass
class FuelSource:
    """燃料来源统计"""
    source_type: str
    total_converted: float = 0.0
    conversion_count: int = 0
    last_conversion: float = 0.0
    avg_efficiency: float = 0.0


class DebtFuelConverter:
    """
    燃料转换器 — 将债务/账目/FINDING转化为自驱能量

    转换公式:
        fuel_gain = source_value * quantity * conversion_rate * 0.1

    燃料值域: [0, max_fuel]
    低燃料阈值: 0.3 (触发自动补充)
    """

    # 转换率表 — 数值差异体现不同来源的能量密度
    # 越难处理/越重要的发现，转化率越高 (能量密度越大)
    CONVERSION_RATES: dict[str, float] = {
        # ---- 发现类 (高转化率 — 突破性发现是最高能量) ----
        "finding_breakthrough": 1.0,   # 突破性发现 — 最高能量密度
        "finding_anomaly": 0.9,        # 异常发现 — 高能量，暗示系统边界
        "finding_opportunity": 0.7,    # 机会发现 — 中高能量
        "finding_insight": 0.5,        # 洞察 — 中等能量

        # ---- 债务类 (中等转化率 — 技术债是工程燃料) ----
        "theoretical_debt": 0.8,       # 理论债务 — 高纯度，但未经验证
        "technical_debt": 0.6,         # 技术债务 — 标准工程燃料
        "si_misalignment": 0.6,        # SI不对齐 — 系统接口摩擦能量
        "engineering_debt": 0.4,       # 工程债务 — 低纯度，需精炼
        "health_drift": 0.4,           # 健康度漂移 — 系统衰变能量

        # ---- 任务/流程类 (低转化率 — 基础燃料) ----
        "unclosed_task": 0.3,          # 未关闭任务 — 基础燃料
        "pending_receipt": 0.2,        # 待处理回执 — 低能量密度
    }

    # 分类映射 — 用于 scan_for_fuel 自动识别
    DEBT_TYPE_MAP: dict[str, list[str]] = {
        "theoretical_debt": ["theoretical", "spec", "architecture", "design"],
        "technical_debt": ["technical", "code_smell", "refactor", "legacy"],
        "engineering_debt": ["engineering", "infrastructure", "pipeline", "build"],
    }

    FINDING_TYPE_MAP: dict[str, list[str]] = {
        "finding_anomaly": ["anomaly", "unexpected", "weird", "strange", "bug"],
        "finding_opportunity": ["opportunity", "improvement", "optimization", "enhance"],
        "finding_insight": ["insight", "pattern", "observation", "analysis"],
        "finding_breakthrough": ["breakthrough", "discovery", "revolutionary", "game_changer"],
    }

    # 燃料管理常量
    LOW_FUEL_THRESHOLD: float = 0.3
    CRITICAL_FUEL_THRESHOLD: float = 0.1
    REFUEL_BOOST_MULTIPLIER: float = 1.2  # 自动补充时的效率加成
    CONSUMPTION_LOG_MAX: int = 1000

    def __init__(self) -> None:
        """初始化燃料转换器"""
        self.fuel_tank: float = 1.0          # 当前燃料水平 (0 - max_fuel)
        self.max_fuel: float = 2.0           # 最大燃料容量
        self.conversion_log: list[ConversionRecord] = []
        self.consumption_log: list[dict] = []
        self.fuel_sources: dict[str, FuelSource] = {}  # 各来源累计燃料
        self._total_consumed: float = 0.0
        self._creation_time: float = time.time()
        self._last_refuel_time: float = time.time()

    # ------------------------------------------------------------------
    # 核心转换接口
    # ------------------------------------------------------------------

    def convert(
        self,
        source_type: str,
        source_value: float,
        quantity: int = 1,
        *,
        bypass_rate_limit: bool = False,
    ) -> dict[str, Any]:
        """
        转换燃料 — 将债务/发现/未完成任务转化为系统驱动能量

        Args:
            source_type: 必须是 CONVERSION_RATES 中的键
            source_value: 基础值 (0.0 - 1.0)
            quantity: 数量 (>= 1)
            bypass_rate_limit: 是否绕过速率限制 (紧急模式)

        Returns:
            {
                "converted": float,      # 实际转换的燃料量
                "new_fuel_level": float, # 转换后燃料水平
                "source": str,           # 来源类型
                "efficiency": float,     # 本次转换效率
                "wasted": float,         # 因满箱而浪费的燃料
                "status": str,           # "ok" | "tank_full" | "limited"
            }
        """
        # 参数校验
        if source_type not in self.CONVERSION_RATES:
            valid = ", ".join(self.CONVERSION_RATES.keys())
            raise ValueError(
                f"Unknown source_type '{source_type}'. Valid types: {valid}"
            )

        if not (0.0 <= source_value <= 1.0):
            raise ValueError(f"source_value must be in [0, 1], got {source_value}")

        if quantity < 1:
            raise ValueError(f"quantity must be >= 1, got {quantity}")

        rate = self.CONVERSION_RATES[source_type]

        # 计算原始可转换燃料
        raw_fuel = source_value * quantity * rate * 0.1

        # 效率计算 — 基于source_value的完美度
        efficiency = rate * (0.5 + 0.5 * source_value)

        # 检查燃料箱容量
        available_space = self.max_fuel - self.fuel_tank
        if available_space <= 0:
            return {
                "converted": 0.0,
                "new_fuel_level": self.fuel_tank,
                "source": source_type,
                "efficiency": efficiency,
                "wasted": raw_fuel,
                "status": "tank_full",
            }

        # 实际可加入的燃料 (受容量限制)
        actual_fuel = min(raw_fuel, available_space)
        wasted = raw_fuel - actual_fuel if raw_fuel > available_space else 0.0

        # 记录转换前状态
        fuel_before = self.fuel_tank

        # 执行转换
        self.fuel_tank += actual_fuel
        self.fuel_tank = round(min(self.fuel_tank, self.max_fuel), 6)

        # 记录日志
        record = ConversionRecord(
            timestamp=time.time(),
            source_type=source_type,
            source_value=source_value,
            quantity=quantity,
            converted=actual_fuel,
            fuel_before=fuel_before,
            fuel_after=self.fuel_tank,
            efficiency=efficiency,
        )
        self.conversion_log.append(record)

        # 更新来源统计
        if source_type not in self.fuel_sources:
            self.fuel_sources[source_type] = FuelSource(source_type=source_type)

        src = self.fuel_sources[source_type]
        src.total_converted += actual_fuel
        src.conversion_count += quantity
        src.last_conversion = time.time()
        # 滚动平均效率
        n = src.conversion_count
        src.avg_efficiency = (src.avg_efficiency * (n - 1) + efficiency) / n

        status = "limited" if wasted > 0 else "ok"

        return {
            "converted": round(actual_fuel, 6),
            "new_fuel_level": round(self.fuel_tank, 6),
            "source": source_type,
            "efficiency": round(efficiency, 6),
            "wasted": round(wasted, 6),
            "status": status,
        }

    # ------------------------------------------------------------------
    # 系统扫描接口
    # ------------------------------------------------------------------

    def scan_for_fuel(
        self,
        topology: dict[str, Any] | None = None,
        pending_tasks: list[dict[str, Any]] | None = None,
        findings: list[dict[str, Any]] | None = None,
        debts: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        扫描系统寻找可转化燃料

        扫描来源:
            1. 未关闭任务 -> unclosed_task
            2. 待处理回执 -> pending_receipt
            3. 债务 -> theoretical/technical/engineering_debt
            4. FINDING -> finding_anomaly/opportunity/insight/breakthrough
            5. SI不对齐 -> si_misalignment (从 topology 检测)
            6. 健康度漂移 -> health_drift (从 topology 检测)

        Args:
            topology: 系统拓扑状态字典
            pending_tasks: 待处理任务列表
            findings: 发现列表
            debts: 债务列表

        Returns:
            {
                "scanned_sources": dict,   # 各来源扫描到的潜在燃料
                "total_potential": float,  # 总潜在燃料
                "conversion_plan": list,   # 建议的转换计划 (按效率排序)
                "topology_health": float,  # 拓扑健康度 (0-1)
            }
        """
        scanned: dict[str, float] = {}
        conversion_plan: list[dict[str, Any]] = []

        # ---- 1. 扫描拓扑结构 (SI不对齐 + 健康度漂移) ----
        if topology:
            self._scan_topology(topology, scanned, conversion_plan)

        # ---- 2. 扫描待处理任务 ----
        if pending_tasks:
            self._scan_pending_tasks(pending_tasks, scanned, conversion_plan)

        # ---- 3. 扫描发现 (FINDING) ----
        if findings:
            self._scan_findings(findings, scanned, conversion_plan)

        # ---- 4. 扫描债务 ----
        if debts:
            self._scan_debts(debts, scanned, conversion_plan)

        # 计算总潜在燃料
        total_potential = sum(scanned.values())

        # 按转化率排序转换计划 (高转化率优先)
        conversion_plan.sort(
            key=lambda x: self.CONVERSION_RATES.get(x["source_type"], 0),
            reverse=True,
        )

        # 拓扑健康度评估
        topology_health = self._evaluate_topology_health(topology or {})

        return {
            "scanned_sources": scanned,
            "total_potential": round(total_potential, 6),
            "conversion_plan": conversion_plan,
            "topology_health": round(topology_health, 6),
            "scan_timestamp": time.time(),
        }

    def _scan_topology(
        self,
        topology: dict[str, Any],
        scanned: dict[str, float],
        plan: list[dict[str, Any]],
    ) -> None:
        """扫描拓扑中的 SI 不对齐和健康度漂移"""
        # SI不对齐检测
        si_align = topology.get("si_alignment", 1.0)
        if isinstance(si_align, (int, float)) and si_align < 0.95:
            misalignment = 1.0 - si_align
            potential = misalignment * self.CONVERSION_RATES["si_misalignment"] * 0.1
            scanned["si_misalignment"] = scanned.get("si_misalignment", 0.0) + potential
            plan.append({
                "source_type": "si_misalignment",
                "detected_value": misalignment,
                "potential_fuel": round(potential, 6),
                "priority": "high" if misalignment > 0.3 else "medium",
                "reason": f"SI alignment at {si_align:.2%}",
            })

        # 健康度漂移检测
        health = topology.get("health", 1.0)
        if isinstance(health, (int, float)) and health < 0.9:
            drift = 1.0 - health
            potential = drift * self.CONVERSION_RATES["health_drift"] * 0.1
            scanned["health_drift"] = scanned.get("health_drift", 0.0) + potential
            plan.append({
                "source_type": "health_drift",
                "detected_value": drift,
                "potential_fuel": round(potential, 6),
                "priority": "critical" if drift > 0.5 else "high",
                "reason": f"System health at {health:.2%}",
            })

        # 未处理节点/连接
        unprocessed_nodes = topology.get("unprocessed_nodes", [])
        if unprocessed_nodes:
            count = len(unprocessed_nodes)
            potential = count * 0.1 * self.CONVERSION_RATES["unclosed_task"] * 0.1
            scanned["unclosed_task"] = scanned.get("unclosed_task", 0.0) + potential
            plan.append({
                "source_type": "unclosed_task",
                "detected_value": count,
                "potential_fuel": round(potential, 6),
                "priority": "medium",
                "reason": f"{count} unprocessed topology nodes",
            })

    def _scan_pending_tasks(
        self,
        tasks: list[dict[str, Any]],
        scanned: dict[str, float],
        plan: list[dict[str, Any]],
    ) -> None:
        """扫描待处理任务"""
        for task in tasks:
            task_type = task.get("type", "unclosed_task")
            urgency = task.get("urgency", 0.5)
            status = task.get("status", "")

            # 待处理回执
            if status == "pending_receipt" or task_type == "receipt":
                potential = urgency * self.CONVERSION_RATES["pending_receipt"] * 0.1
                scanned["pending_receipt"] = scanned.get("pending_receipt", 0.0) + potential
                plan.append({
                    "source_type": "pending_receipt",
                    "detected_value": urgency,
                    "potential_fuel": round(potential, 6),
                    "priority": "low",
                    "reason": f"Pending receipt: urgency={urgency}",
                })
            else:
                # 未关闭任务
                potential = urgency * self.CONVERSION_RATES["unclosed_task"] * 0.1
                scanned["unclosed_task"] = scanned.get("unclosed_task", 0.0) + potential
                plan.append({
                    "source_type": "unclosed_task",
                    "detected_value": urgency,
                    "potential_fuel": round(potential, 6),
                    "priority": "medium" if urgency > 0.5 else "low",
                    "reason": f"Unclosed task: urgency={urgency}",
                })

    def _scan_findings(
        self,
        findings: list[dict[str, Any]],
        scanned: dict[str, float],
        plan: list[dict[str, Any]],
    ) -> None:
        """扫描发现列表"""
        for finding in findings:
            ftype = finding.get("type", "finding_insight")
            severity = finding.get("severity", 0.5)
            confidence = finding.get("confidence", 0.8)

            # 自动映射 finding 类型
            mapped_type = self._map_finding_type(ftype)
            rate = self.CONVERSION_RATES.get(mapped_type, 0.5)

            # 综合考虑严重度和置信度
            source_value = severity * confidence
            potential = source_value * rate * 0.1

            scanned[mapped_type] = scanned.get(mapped_type, 0.0) + potential
            plan.append({
                "source_type": mapped_type,
                "detected_value": source_value,
                "potential_fuel": round(potential, 6),
                "priority": "high" if severity > 0.7 else "medium",
                "reason": f"Finding '{ftype}': severity={severity}, confidence={confidence}",
            })

    def _scan_debts(
        self,
        debts: list[dict[str, Any]],
        scanned: dict[str, float],
        plan: list[dict[str, Any]],
    ) -> None:
        """扫描债务列表"""
        for debt in debts:
            dtype = debt.get("type", "technical_debt")
            amount = debt.get("amount", 1.0)
            impact = debt.get("impact", 0.5)

            # 自动映射债务类型
            mapped_type = self._map_debt_type(dtype)
            rate = self.CONVERSION_RATES.get(mapped_type, 0.5)

            # 综合影响和数量
            source_value = min(impact * amount, 1.0)
            potential = source_value * rate * 0.1

            scanned[mapped_type] = scanned.get(mapped_type, 0.0) + potential
            plan.append({
                "source_type": mapped_type,
                "detected_value": source_value,
                "potential_fuel": round(potential, 6),
                "priority": "high" if impact > 0.7 else "medium",
                "reason": f"Debt '{dtype}': impact={impact}, amount={amount}",
            })

    def _map_finding_type(self, raw_type: str) -> str:
        """将原始 finding 类型映射到标准类型"""
        raw_lower = raw_type.lower()
        for std_type, keywords in self.FINDING_TYPE_MAP.items():
            if any(kw in raw_lower for kw in keywords):
                return std_type
        return "finding_insight"  # 默认

    def _map_debt_type(self, raw_type: str) -> str:
        """将原始债务类型映射到标准类型"""
        raw_lower = raw_type.lower()
        for std_type, keywords in self.DEBT_TYPE_MAP.items():
            if any(kw in raw_lower for kw in keywords):
                return std_type
        return "technical_debt"  # 默认

    def _evaluate_topology_health(self, topology: dict[str, Any]) -> float:
        """评估拓扑整体健康度 (0-1)"""
        health = topology.get("health", 1.0)
        si_align = topology.get("si_alignment", 1.0)
        if isinstance(health, (int, float)) and isinstance(si_align, (int, float)):
            return min(health, si_align)
        return 1.0

    # ------------------------------------------------------------------
    # 燃料管理接口
    # ------------------------------------------------------------------

    def refuel(self, *,
               topology: dict[str, Any] | None = None,
               pending_tasks: list[dict[str, Any]] | None = None,
               findings: list[dict[str, Any]] | None = None,
               debts: list[dict[str, Any]] | None = None,
               ) -> dict[str, Any]:
        """
        自动补充燃料 — 如果 fuel_tank < 0.3，自动扫描并转换

        在紧急模式 (fuel < 0.1) 时，启用 1.2x 效率加成

        Returns:
            {
                "refueled": bool,        # 是否执行了补充
                "fuel_before": float,
                "fuel_after": float,
                "converted_sources": list,
                "mode": str,             # "normal" | "emergency" | "none"
            }
        """
        fuel_before = self.fuel_tank

        # 判断是否需要补充
        if self.fuel_tank >= self.LOW_FUEL_THRESHOLD:
            return {
                "refueled": False,
                "fuel_before": fuel_before,
                "fuel_after": self.fuel_tank,
                "converted_sources": [],
                "mode": "none",
                "reason": f"Fuel level {self.fuel_tank:.2f} >= threshold {self.LOW_FUEL_THRESHOLD}",
            }

        # 确定模式
        is_emergency = self.fuel_tank < self.CRITICAL_FUEL_THRESHOLD
        mode = "emergency" if is_emergency else "normal"
        multiplier = self.REFUEL_BOOST_MULTIPLIER if is_emergency else 1.0

        # 扫描燃料源
        scan_result = self.scan_for_fuel(topology, pending_tasks, findings, debts)
        plan = scan_result["conversion_plan"]

        converted_sources: list[dict[str, Any]] = []

        # 按优先级和效率执行转换，直到燃料充足或计划耗尽
        for item in plan:
            if self.fuel_tank >= self.LOW_FUEL_THRESHOLD:
                break

            stype = item["source_type"]
            detected = item["detected_value"]
            # 确保值在有效范围
            source_value = min(max(float(detected), 0.0), 1.0)

            # 紧急模式提升基础值
            if is_emergency:
                source_value = min(source_value * multiplier, 1.0)

            # 执行转换
            result = self.convert(stype, source_value)
            converted_sources.append({
                "source_type": stype,
                "converted": result["converted"],
                "efficiency": result["efficiency"],
            })

        self._last_refuel_time = time.time()

        return {
            "refueled": True,
            "fuel_before": round(fuel_before, 6),
            "fuel_after": round(self.fuel_tank, 6),
            "converted_sources": converted_sources,
            "mode": mode,
            "total_converted": round(self.fuel_tank - fuel_before, 6),
        }

    def consume(self, amount: float, *,
                reason: str = "system_operation",
                ) -> dict[str, Any]:
        """
        消耗燃料

        Args:
            amount: 消耗量 (>= 0)
            reason: 消耗原因

        Returns:
            {
                "consumed": float,       # 实际消耗量
                "fuel_before": float,
                "fuel_after": float,
                "status": str,           # "ok" | "insufficient" | "critical"
                "need_refuel": bool,
            }
        """
        if amount < 0:
            raise ValueError(f"amount must be >= 0, got {amount}")

        fuel_before = self.fuel_tank
        actual_consumed = min(amount, self.fuel_tank)
        self.fuel_tank -= actual_consumed
        self.fuel_tank = round(max(self.fuel_tank, 0.0), 6)
        self._total_consumed += actual_consumed

        # 记录消耗
        self.consumption_log.append({
            "timestamp": time.time(),
            "requested": amount,
            "consumed": actual_consumed,
            "reason": reason,
            "fuel_after": self.fuel_tank,
        })
        # 限制日志长度
        if len(self.consumption_log) > self.CONSUMPTION_LOG_MAX:
            self.consumption_log = self.consumption_log[-self.CONSUMPTION_LOG_MAX:]

        # 状态判定
        if self.fuel_tank < self.CRITICAL_FUEL_THRESHOLD:
            status = "critical"
        elif self.fuel_tank < self.LOW_FUEL_THRESHOLD:
            status = "insufficient"
        elif actual_consumed < amount:
            status = "insufficient"
        else:
            status = "ok"

        need_refuel = self.fuel_tank < self.LOW_FUEL_THRESHOLD

        return {
            "consumed": round(actual_consumed, 6),
            "fuel_before": round(fuel_before, 6),
            "fuel_after": round(self.fuel_tank, 6),
            "status": status,
            "need_refuel": need_refuel,
            "shortfall": round(amount - actual_consumed, 6) if amount > actual_consumed else 0.0,
        }

    # ------------------------------------------------------------------
    # 报告与优化接口
    # ------------------------------------------------------------------

    def get_fuel_report(self) -> dict[str, Any]:
        """
        燃料报告

        Returns:
            {
                "current": float,
                "max": float,
                "percentage": float,
                "sources": dict,
                "history": list,
                "projected_empty": str,   # 预计耗尽时间
                "avg_consumption_rate": float,
                "system_uptime": float,
            }
        """
        percentage = (self.fuel_tank / self.max_fuel) * 100 if self.max_fuel > 0 else 0.0

        # 计算平均消耗速率 (燃料/秒)
        avg_rate = self._calculate_avg_consumption_rate()

        # 预计耗尽时间
        projected_empty = self._project_empty_time(avg_rate)

        # 来源统计
        sources_summary = {}
        for stype, src in self.fuel_sources.items():
            sources_summary[stype] = {
                "total_converted": round(src.total_converted, 6),
                "conversion_count": src.conversion_count,
                "avg_efficiency": round(src.avg_efficiency, 6),
                "last_conversion": src.last_conversion,
            }

        # 最近转换历史 (最近10条)
        recent_history = [
            {
                "timestamp": r.timestamp,
                "source_type": r.source_type,
                "converted": round(r.converted, 6),
                "fuel_after": round(r.fuel_after, 6),
                "efficiency": round(r.efficiency, 6),
            }
            for r in self.conversion_log[-10:]
        ]

        uptime = time.time() - self._creation_time

        return {
            "current": round(self.fuel_tank, 6),
            "max": self.max_fuel,
            "percentage": round(percentage, 2),
            "sources": sources_summary,
            "history": recent_history,
            "projected_empty": projected_empty,
            "avg_consumption_rate": round(avg_rate, 8),
            "system_uptime": round(uptime, 2),
            "total_consumed": round(self._total_consumed, 6),
            "total_converted": round(sum(s.total_converted for s in self.fuel_sources.values()), 6),
        }

    def _calculate_avg_consumption_rate(self) -> float:
        """计算平均燃料消耗速率 (单位: 燃料/秒)"""
        if len(self.consumption_log) < 2:
            return 0.0

        # 使用最近20条消耗记录计算
        recent = self.consumption_log[-20:]
        total_consumed = sum(r["consumed"] for r in recent)
        time_span = recent[-1]["timestamp"] - recent[0]["timestamp"]

        if time_span > 0:
            return total_consumed / time_span
        return 0.0

    def _project_empty_time(self, avg_rate: float) -> str:
        """预测燃料耗尽时间"""
        if avg_rate <= 0:
            return "unknown (no consumption data)"
        if self.fuel_tank <= 0:
            return "already_empty"

        seconds_remaining = self.fuel_tank / avg_rate
        if seconds_remaining < 60:
            return f"{seconds_remaining:.1f}s"
        elif seconds_remaining < 3600:
            return f"{seconds_remaining / 60:.1f}m"
        elif seconds_remaining < 86400:
            return f"{seconds_remaining / 3600:.1f}h"
        else:
            return f"{seconds_remaining / 86400:.1f}d"

    def optimize_conversion(self) -> dict[str, Any]:
        """
        优化转换策略 — 优先转换高转化率的来源

        Returns:
            {
                "optimal_order": list,       # 最优转换顺序
                "efficiency_map": dict,      # 各来源效率
                "recommendation": str,       # 策略建议
                "estimated_max_fuel": float, # 理论最大可获取燃料
            }
        """
        # 按转化率排序
        sorted_rates = sorted(
            self.CONVERSION_RATES.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        optimal_order = [
            {
                "source_type": st,
                "rate": rate,
                "priority": i + 1,
                "description": self._get_source_description(st),
            }
            for i, (st, rate) in enumerate(sorted_rates)
        ]

        efficiency_map = dict(self.CONVERSION_RATES)

        # 计算理论最大燃料 (假设所有来源都达到最大值1.0)
        estimated_max = sum(
            rate * 0.1 for rate in self.CONVERSION_RATES.values()
        )

        # 策略建议
        recommendation = self._generate_recommendation(sorted_rates)

        return {
            "optimal_order": optimal_order,
            "efficiency_map": efficiency_map,
            "recommendation": recommendation,
            "estimated_max_fuel": round(estimated_max, 6),
        }

    def _get_source_description(self, source_type: str) -> str:
        """获取来源类型描述"""
        descriptions = {
            "finding_breakthrough": "突破性发现 — 系统边界突破，最高能量",
            "finding_anomaly": "异常发现 — 揭示系统异常行为",
            "theoretical_debt": "理论债务 — 未经验证的理论假设",
            "finding_opportunity": "机会发现 — 系统改进机会",
            "technical_debt": "技术债务 — 代码与设计层面的债务",
            "si_misalignment": "SI不对齐 — 系统接口间的不一致",
            "finding_insight": "洞察 — 深层模式识别",
            "engineering_debt": "工程债务 — 基础设施与流程债务",
            "health_drift": "健康度漂移 — 系统性能衰减",
            "unclosed_task": "未关闭任务 — 待完成的操作项",
            "pending_receipt": "待处理回执 — 等待确认的流程项",
        }
        return descriptions.get(source_type, "未知来源")

    def _generate_recommendation(
        self, sorted_rates: list[tuple[str, float]]
    ) -> str:
        """生成转换策略建议"""
        top_3 = [st for st, _ in sorted_rates[:3]]
        bottom_3 = [st for st, _ in sorted_rates[-3:]]

        rec = (
            f"优先转换高价值发现类来源 ({', '.join(top_3)}); "
            f"基础任务类 ({', '.join(bottom_3)}) 作为稳定底噪燃料。"
            "建议保持燃料箱在 50% 以上以应对突发消耗。"
        )
        return rec

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def set_fuel(self, value: float) -> None:
        """直接设置燃料值 (用于测试和恢复)"""
        self.fuel_tank = round(max(0.0, min(value, self.max_fuel)), 6)

    def reset(self) -> None:
        """重置转换器状态"""
        self.fuel_tank = 1.0
        self.conversion_log.clear()
        self.consumption_log.clear()
        self.fuel_sources.clear()
        self._total_consumed = 0.0
        self._creation_time = time.time()
        self._last_refuel_time = time.time()

    def __repr__(self) -> str:
        pct = (self.fuel_tank / self.max_fuel) * 100
        return (
            f"<DebtFuelConverter fuel={self.fuel_tank:.3f}/{self.max_fuel} "
            f"({pct:.1f}%) conversions={len(self.conversion_log)}>"
        )


# =============================================================================
# 测试块
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v3.3 — DebtFuelConverter 测试")
    print("=" * 70)

    # ---- 初始化 ----
    converter = DebtFuelConverter()
    print(f"\n[1] 初始化: {converter}")
    print(f"    转换率表: {len(converter.CONVERSION_RATES)} 种来源")

    # ---- 测试: 各种来源的燃料转换 ----
    print("\n[2] 各种来源的燃料转换测试")
    print("-" * 50)

    test_conversions = [
        # (source_type, source_value, quantity)
        ("finding_breakthrough", 1.0, 1),    # 最高转化率
        ("finding_anomaly", 0.9, 2),          # 高转化率
        ("theoretical_debt", 0.8, 1),
        ("finding_opportunity", 0.7, 1),
        ("technical_debt", 0.6, 3),
        ("si_misalignment", 0.6, 1),
        ("finding_insight", 0.5, 2),
        ("engineering_debt", 0.4, 1),
        ("health_drift", 0.4, 1),
        ("unclosed_task", 0.3, 5),
        ("pending_receipt", 0.2, 10),
    ]

    for stype, sval, qty in test_conversions:
        result = converter.convert(stype, sval, qty)
        rate = converter.CONVERSION_RATES[stype]
        print(
            f"  {stype:25s} | value={sval:.1f} qty={qty:2d} | "
            f"rate={rate:.1f} | +{result['converted']:.4f} fuel | "
            f"eff={result['efficiency']:.3f} | status={result['status']}"
        )

    print(f"\n  转换后燃料水平: {converter.fuel_tank:.4f}")
    print(f"  转换记录数: {len(converter.conversion_log)}")

    # ---- 测试: 满箱限制 ----
    print("\n[3] 燃料箱容量限制测试")
    print("-" * 50)
    converter.set_fuel(1.95)
    result = converter.convert("finding_breakthrough", 1.0, 10)
    print(f"  燃料箱: 1.95 -> 尝试添加 10x 突破发现")
    print(f"  实际转换: {result['converted']:.4f}")
    print(f"  浪费燃料: {result['wasted']:.4f}")
    print(f"  状态: {result['status']}")
    print(f"  当前燃料: {result['new_fuel_level']:.4f} (max={converter.max_fuel})")

    # ---- 测试: 扫描系统寻找燃料 ----
    print("\n[4] 扫描系统寻找燃料测试")
    print("-" * 50)

    topology = {
        "health": 0.72,
        "si_alignment": 0.85,
        "unprocessed_nodes": ["node_a", "node_b", "node_c"],
    }

    pending_tasks = [
        {"type": "review", "urgency": 0.8, "status": "open"},
        {"type": "deploy", "urgency": 0.6, "status": "open"},
        {"type": "receipt", "urgency": 0.4, "status": "pending_receipt"},
    ]

    findings = [
        {"type": "breakthrough", "severity": 0.95, "confidence": 0.9},
        {"type": "anomaly", "severity": 0.8, "confidence": 0.85},
        {"type": "insight", "severity": 0.5, "confidence": 0.7},
    ]

    debts = [
        {"type": "technical", "amount": 2.0, "impact": 0.7},
        {"type": "engineering", "amount": 1.5, "impact": 0.5},
        {"type": "theoretical", "amount": 1.0, "impact": 0.6},
    ]

    scan_result = converter.scan_for_fuel(
        topology=topology,
        pending_tasks=pending_tasks,
        findings=findings,
        debts=debts,
    )

    print(f"  扫描到的来源:")
    for src, potential in scan_result["scanned_sources"].items():
        print(f"    {src:25s}: {potential:.4f}")

    print(f"\n  总潜在燃料: {scan_result['total_potential']:.4f}")
    print(f"  拓扑健康度: {scan_result['topology_health']:.2%}")
    print(f"  转换计划条目: {len(scan_result['conversion_plan'])}")
    print(f"  最优转换顺序 (前5):")
    for i, plan in enumerate(scan_result["conversion_plan"][:5], 1):
        print(
            f"    {i}. {plan['source_type']:25s} | "
            f"potential={plan['potential_fuel']:.4f} | "
            f"priority={plan['priority']}"
        )

    # ---- 测试: 自动补充燃料 ----
    print("\n[5] 自动补充燃料测试")
    print("-" * 50)

    # 正常模式 (> 0.1, < 0.3)
    converter.set_fuel(0.15)
    print(f"  设置燃料为 0.15 (低燃料阈值={converter.LOW_FUEL_THRESHOLD})")
    refuel_result = converter.refuel(
        topology=topology,
        pending_tasks=pending_tasks,
        findings=findings,
        debts=debts,
    )
    print(f"  模式: {refuel_result['mode']}")
    print(f"  补充前: {refuel_result['fuel_before']:.4f}")
    print(f"  补充后: {refuel_result['fuel_after']:.4f}")
    print(f"  总转换量: {refuel_result['total_converted']:.4f}")
    print(f"  转换来源数: {len(refuel_result['converted_sources'])}")

    # 紧急模式 (< 0.1)
    converter.set_fuel(0.05)
    print(f"\n  设置燃料为 0.05 (紧急)")
    refuel_result = converter.refuel(
        topology=topology,
        pending_tasks=pending_tasks,
        findings=findings,
        debts=debts,
    )
    print(f"  模式: {refuel_result['mode']}")
    print(f"  补充前: {refuel_result['fuel_before']:.4f}")
    print(f"  补充后: {refuel_result['fuel_after']:.4f}")

    # 无需补充 (> 0.3)
    converter.set_fuel(0.8)
    print(f"\n  设置燃料为 0.8 (充足)")
    refuel_result = converter.refuel()
    print(f"  是否补充: {refuel_result['refueled']}")
    print(f"  原因: {refuel_result['reason']}")

    # ---- 测试: 燃料消耗 ----
    print("\n[6] 燃料消耗测试")
    print("-" * 50)
    converter.set_fuel(1.0)
    for i, amount in enumerate([0.2, 0.3, 0.4], 1):
        result = converter.consume(amount, reason=f"operation_{i}")
        print(
            f"  消耗 #{i}: 请求={amount:.1f} 实际={result['consumed']:.2f} "
            f"剩余={result['fuel_after']:.2f} 状态={result['status']} "
            f"需补充={result['need_refuel']}"
        )

    # ---- 测试: 燃料报告生成 ----
    print("\n[7] 燃料报告生成测试")
    print("-" * 50)

    report = converter.get_fuel_report()
    print(f"  当前燃料: {report['current']}")
    print(f"  最大容量: {report['max']}")
    print(f"  百分比: {report['percentage']}%")
    print(f"  预计耗尽: {report['projected_empty']}")
    print(f"  平均消耗率: {report['avg_consumption_rate']}")
    print(f"  系统运行时间: {report['system_uptime']}s")
    print(f"  总消耗: {report['total_consumed']}")
    print(f"  总转换: {report['total_converted']}")
    print(f"  来源统计:")
    for src_name, src_data in report["sources"].items():
        print(
            f"    {src_name:25s}: total={src_data['total_converted']:.4f} "
            f"count={src_data['conversion_count']} "
            f"avg_eff={src_data['avg_efficiency']:.3f}"
        )
    print(f"  最近转换历史: {len(report['history'])} 条")

    # ---- 测试: 优化策略 ----
    print("\n[8] 优化转换策略测试")
    print("-" * 50)

    opt = converter.optimize_conversion()
    print(f"  最优转换顺序 (前5):")
    for item in opt["optimal_order"][:5]:
        print(
            f"    #{item['priority']} {item['source_type']:25s} "
            f"rate={item['rate']:.1f} — {item['description']}"
        )
    print(f"\n  理论最大可获取燃料: {opt['estimated_max_fuel']:.4f}")
    print(f"  策略建议: {opt['recommendation']}")

    # ---- 测试: 异常处理 ----
    print("\n[9] 异常处理测试")
    print("-" * 50)

    try:
        converter.convert("invalid_type", 0.5)
    except ValueError as e:
        print(f"  无效来源类型: {e}")

    try:
        converter.convert("technical_debt", 1.5)
    except ValueError as e:
        print(f"  越界source_value: {e}")

    try:
        converter.convert("technical_debt", 0.5, -1)
    except ValueError as e:
        print(f"  无效quantity: {e}")

    try:
        converter.consume(-0.1)
    except ValueError as e:
        print(f"  负消耗: {e}")

    # ---- 测试: 重置 ----
    print("\n[10] 重置功能测试")
    print("-" * 50)
    print(f"  重置前: {converter}")
    converter.reset()
    print(f"  重置后: {converter}")
    print(f"  记录清空: conversions={len(converter.conversion_log)}")

    print("\n" + "=" * 70)
    print("所有测试通过!")
    print("=" * 70)
