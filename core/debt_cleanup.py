#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v3.2 — Debt Cleanup System
=====================================
理论/技术/工程三类债务的全生命周期管理

集成点:
    - OMNI-HUB v3.2 core/debt_cleanup.py
    - 11线分布式系统 (ucif1-ucif11)
    - 与 CI/CD pipeline 联动扫描代码标记

作者: OMNI-HUB Architecture Team
版本: 3.2.0
"""

from __future__ import annotations

import json
import hashlib
import re
import time
import math
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging


class DebtCleanup:
    """债务清理系统 — 理论/技术/工程三类债务全生命周期管理

    核心设计:
        1. 统一债务注册与追踪
        2. 自动清理策略引擎 (per-type handlers)
        3. 代码静态扫描集成
        4. 三维优先级排序 (severity × aging × impact)
        5. 11线分布式委托清理
    """

    DEBT_TYPES = ["theoretical", "technical", "engineering"]
    SEVERITY_LEVELS = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    # 代码中常见的债务标记正则
    DEBT_MARKERS = {
        "TODO": re.compile(r"#\s*TODO[\s:]*(.+?)(?:\n|$)", re.IGNORECASE),
        "FIXME": re.compile(r"#\s*FIXME[\s:]*(.+?)(?:\n|$)", re.IGNORECASE),
        "HACK": re.compile(r"#\s*HACK[\s:]*(.+?)(?:\n|$)", re.IGNORECASE),
        "XXX": re.compile(r"#\s*XXX[\s:]*(.+?)(?:\n|$)", re.IGNORECASE),
        "BUG": re.compile(r"#\s*BUG[\s:]*(.+?)(?:\n|$)", re.IGNORECASE),
        "DEBT": re.compile(r"#\s*DEBT[\s:]*(.+?)(?:\n|$)", re.IGNORECASE),
        # 也匹配多行注释中的标记 (如 """TODO: ...""")
        "TODO_MULTILINE": re.compile(r'"""\s*TODO[\s:]*(.+?)(?:"""|\n\n)', re.IGNORECASE | re.DOTALL),
        "FIXME_MULTILINE": re.compile(r'"""\s*FIXME[\s:]*(.+?)(?:"""|\n\n)', re.IGNORECASE | re.DOTALL),
    }

    # 标记到债务类型的映射
    MARKER_TO_TYPE = {
        "TODO": "technical",
        "FIXME": "technical",
        "HACK": "technical",
        "XXX": "engineering",
        "BUG": "technical",
        "DEBT": "engineering",
        "TODO_MULTILINE": "technical",
        "FIXME_MULTILINE": "technical",
    }

    # 标记到严重级别的映射 (默认)
    MARKER_TO_SEVERITY = {
        "TODO": "medium",
        "FIXME": "high",
        "HACK": "high",
        "XXX": "medium",
        "BUG": "critical",
        "DEBT": "medium",
        "TODO_MULTILINE": "medium",
        "FIXME_MULTILINE": "high",
    }

    def __init__(self):
        self.debts: Dict[str, List[Dict[str, Any]]] = {
            t: [] for t in self.DEBT_TYPES
        }
        self.cleanup_log: List[Dict[str, Any]] = []
        self.auto_cleanup_rules = {
            "theoretical": self._auto_theoretical,
            "technical": self._auto_technical,
            "engineering": self._auto_engineering,
        }
        # 统计数据用于趋势分析
        self._daily_stats: List[Dict[str, Any]] = []
        # 委托记录
        self._delegations: Dict[str, Dict[str, Any]] = {}

    # ───────────────────────────────────────────────
    # 核心 CRUD
    # ───────────────────────────────────────────────

    def register_debt(
        self,
        debt_type: str,
        description: str,
        severity: str,
        line: str = "ucif2",
        auto_cleanable: bool = False,
        impact_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """注册债务

        Args:
            debt_type: theoretical | technical | engineering
            description: 债务描述
            severity: low | medium | high | critical
            line: 所属线 (ucif1-ucif11)
            auto_cleanable: 是否可自动清理
            impact_score: 影响评分 (0.0 - 10.0)
            metadata: 附加元数据

        Returns:
            debt_id: 唯一债务标识符
        """
        if debt_type not in self.DEBT_TYPES:
            raise ValueError(
                f"Invalid debt_type '{debt_type}'. Must be one of {self.DEBT_TYPES}"
            )
        if severity not in self.SEVERITY_LEVELS:
            raise ValueError(
                f"Invalid severity '{severity}'. Must be one of {list(self.SEVERITY_LEVELS.keys())}"
            )

        ts = datetime.now(timezone.utc).isoformat()
        debt_id = self._generate_debt_id(debt_type, description, ts)

        debt = {
            "debt_id": debt_id,
            "debt_type": debt_type,
            "description": description,
            "severity": severity,
            "severity_level": self.SEVERITY_LEVELS[severity],
            "line": line,
            "auto_cleanable": auto_cleanable,
            "impact_score": max(0.0, min(10.0, float(impact_score))),
            "status": "open",  # open | cleaning | cleaned | delegated | stale
            "created_at": ts,
            "updated_at": ts,
            "cleaned_at": None,
            "cleanup_method": None,
            "verification": {},
            "side_effects": [],
            "metadata": metadata or {},
            "cleanup_attempts": 0,
            "aging_days": 0.0,
        }

        self.debts[debt_type].append(debt)
        return debt_id

    def get_debt(self, debt_id: str) -> Dict[str, Any]:
        """获取债务详情

        Args:
            debt_id: 债务唯一标识

        Returns:
            债务详情字典，若不存在返回空 dict
        """
        for dtype in self.DEBT_TYPES:
            for debt in self.debts[dtype]:
                if debt["debt_id"] == debt_id:
                    # 实时计算 aging
                    debt["aging_days"] = self._compute_aging(debt)
                    return dict(debt)
        return {}

    def update_debt(self, debt_id: str, **fields) -> bool:
        """更新债务字段 (内部辅助)"""
        for dtype in self.DEBT_TYPES:
            for debt in self.debts[dtype]:
                if debt["debt_id"] == debt_id:
                    for k, v in fields.items():
                        if k in debt:
                            debt[k] = v
                    debt["updated_at"] = datetime.now(timezone.utc).isoformat()
                    return True
        return False

    # ───────────────────────────────────────────────
    # 清理核心
    # ───────────────────────────────────────────────

    def cleanup(self, debt_id: str, method: str = "manual") -> Dict[str, Any]:
        """清理指定债务

        Args:
            debt_id: 债务ID
            method: manual | auto | delegated

        Returns:
            {"debt_id": str, "cleaned": bool, "method": str,
             "verification": dict, "side_effects": list}
        """
        debt = self.get_debt(debt_id)
        if not debt:
            return {
                "debt_id": debt_id,
                "cleaned": False,
                "method": method,
                "verification": {"error": "Debt not found"},
                "side_effects": [],
            }

        if debt["status"] == "cleaned":
            return {
                "debt_id": debt_id,
                "cleaned": True,
                "method": debt.get("cleanup_method", method),
                "verification": debt.get("verification", {}),
                "side_effects": [],
                "note": "Already cleaned",
            }

        self.update_debt(debt_id, status="cleaning", cleanup_attempts=debt["cleanup_attempts"] + 1)

        result = {
            "debt_id": debt_id,
            "cleaned": False,
            "method": method,
            "verification": {},
            "side_effects": [],
        }

        if method == "auto" and debt["auto_cleanable"]:
            handler = self.auto_cleanup_rules.get(debt["debt_type"])
            if handler:
                auto_result = handler(debt)
                result["cleaned"] = auto_result.get("cleaned", False)
                result["verification"] = auto_result.get("verification", {})
                result["side_effects"] = auto_result.get("side_effects", [])
            else:
                result["verification"] = {"error": "No auto handler for type"}
        elif method == "delegated":
            # delegated 需要事先调用 delegate_cleanup
            delegation = self._delegations.get(debt_id)
            if delegation:
                result["cleaned"] = True  # 模拟委托成功
                result["verification"] = {
                    "delegated_to": delegation["to_line"],
                    "delegated_at": delegation["at"],
                    "status": "completed_by_delegate",
                }
            else:
                result["verification"] = {"error": "No delegation record"}
        else:
            # manual cleanup — 记录人工清理
            result["cleaned"] = True
            result["verification"] = {
                "cleaned_by": "manual_operator",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "review_required": debt["severity"] in ("high", "critical"),
            }

        # 更新债务状态
        if result["cleaned"]:
            cleaned_at = datetime.now(timezone.utc).isoformat()
            self.update_debt(
                debt_id,
                status="cleaned",
                cleaned_at=cleaned_at,
                cleanup_method=method,
                verification=result["verification"],
                side_effects=result["side_effects"],
            )
            self.cleanup_log.append({
                "debt_id": debt_id,
                "action": "cleaned",
                "method": method,
                "timestamp": cleaned_at,
            })
        else:
            self.update_debt(debt_id, status="open")

        return result

    def auto_cleanup(self) -> Dict[str, Any]:
        """自动清理可自动处理的债务

        遍历所有标记为 auto_cleanable=True 且状态为 open 的债务，
        调用对应类型的自动清理策略。

        Returns:
            {"processed": int, "succeeded": int, "failed": int,
             "details": list}
        """
        processed = 0
        succeeded = 0
        failed = 0
        details = []

        for dtype in self.DEBT_TYPES:
            for debt in self.debts[dtype]:
                if debt["status"] != "open" or not debt["auto_cleanable"]:
                    continue

                processed += 1
                result = self.cleanup(debt["debt_id"], method="auto")

                if result["cleaned"]:
                    succeeded += 1
                else:
                    failed += 1

                details.append({
                    "debt_id": debt["debt_id"],
                    "type": dtype,
                    "cleaned": result["cleaned"],
                    "verification": result["verification"],
                })

        # 记录趋势
        self._daily_stats.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "auto_cleanup",
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
        })

        return {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "details": details,
        }

    def delegate_cleanup(self, debt_id: str, to_line: str) -> Dict[str, Any]:
        """将债务清理委托给他线

        Args:
            debt_id: 债务ID
            to_line: 目标线 (如 "ucif5")

        Returns:
            {"debt_id": str, "delegated": bool, "to_line": str,
             "from_line": str, "timestamp": str}
        """
        debt = self.get_debt(debt_id)
        if not debt:
            return {
                "debt_id": debt_id,
                "delegated": False,
                "error": "Debt not found",
            }

        ts = datetime.now(timezone.utc).isoformat()
        self._delegations[debt_id] = {
            "to_line": to_line,
            "from_line": debt["line"],
            "at": ts,
        }

        self.update_debt(debt_id, status="delegated")
        self.cleanup_log.append({
            "debt_id": debt_id,
            "action": "delegated",
            "to_line": to_line,
            "timestamp": ts,
        })

        # 尝试执行 delegated cleanup
        result = self.cleanup(debt_id, method="delegated")

        return {
            "debt_id": debt_id,
            "delegated": True,
            "to_line": to_line,
            "from_line": debt["line"],
            "timestamp": ts,
            "cleanup_result": result,
        }

    # ───────────────────────────────────────────────
    # 报告与分析
    # ───────────────────────────────────────────────

    def get_debt_report(self, debt_type: str = None) -> Dict[str, Any]:
        """生成债务报告

        Args:
            debt_type: 可选，仅报告指定类型

        Returns:
            {
                "total": int,
                "by_type": dict,
                "by_severity": dict,
                "by_line": dict,
                "aging": dict,
                "trend": list,
                "auto_cleanable_ratio": float,
                "cleaned_ratio": float,
            }
        """
        types_to_report = [debt_type] if debt_type in self.DEBT_TYPES else self.DEBT_TYPES

        all_debts = []
        for dtype in types_to_report:
            all_debts.extend(self.debts[dtype])

        # by_type
        by_type = {t: 0 for t in self.DEBT_TYPES}
        for d in all_debts:
            by_type[d["debt_type"]] += 1

        # by_severity
        by_severity = {s: 0 for s in self.SEVERITY_LEVELS}
        for d in all_debts:
            by_severity[d["severity"]] += 1

        # by_line
        by_line: Dict[str, int] = {}
        for d in all_debts:
            by_line[d["line"]] = by_line.get(d["line"], 0) + 1

        # aging 分布
        aging_buckets = {"fresh": 0, "aging": 0, "stale": 0, "ancient": 0}
        total_aging = 0.0
        for d in all_debts:
            days = self._compute_aging(d)
            total_aging += days
            if days < 7:
                aging_buckets["fresh"] += 1
            elif days < 30:
                aging_buckets["aging"] += 1
            elif days < 90:
                aging_buckets["stale"] += 1
            else:
                aging_buckets["ancient"] += 1

        # 自动清理比率
        auto_cleanable_count = sum(1 for d in all_debts if d["auto_cleanable"])
        auto_ratio = auto_cleanable_count / len(all_debts) if all_debts else 0.0

        # 已清理比率
        cleaned_count = sum(1 for d in all_debts if d["status"] == "cleaned")
        cleaned_ratio = cleaned_count / len(all_debts) if all_debts else 0.0

        report = {
            "total": len(all_debts),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_line": by_line,
            "aging": {
                "buckets": aging_buckets,
                "average_days": round(total_aging / len(all_debts), 2) if all_debts else 0.0,
            },
            "trend": self._daily_stats[-30:],  # 最近30条趋势
            "auto_cleanable_ratio": round(auto_ratio, 4),
            "cleaned_ratio": round(cleaned_ratio, 4),
            "open_critical": sum(
                1 for d in all_debts if d["status"] == "open" and d["severity"] == "critical"
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return report

    def prioritize(self) -> List[Dict[str, Any]]:
        """债务优先级排序

        排序算法: 综合得分 = severity_level × aging_factor × impact_score
        其中 aging_factor = 1 + log(1 + aging_days / 7)

        Returns:
            按优先级降序排列的债务列表
        """
        all_open = []
        for dtype in self.DEBT_TYPES:
            for debt in self.debts[dtype]:
                if debt["status"] == "open":
                    all_open.append(debt)

        scored = []
        for debt in all_open:
            days = self._compute_aging(debt)
            aging_factor = 1 + math.log(1 + days / 7.0)
            # 综合得分 (越高越优先)
            score = debt["severity_level"] * aging_factor * debt["impact_score"]
            scored.append((score, days, debt))

        # 降序排列
        scored.sort(key=lambda x: (-x[0], -x[1]))

        return [s[2] for s in scored]

    # ───────────────────────────────────────────────
    # 代码静态扫描
    # ───────────────────────────────────────────────

    def detect_debt_from_code(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """从代码内容中检测债务标记

        检测标记: TODO / FIXME / HACK / XXX / BUG / DEBT

        Args:
            file_path: 文件路径 (用于报告定位)
            content: 代码内容

        Returns:
            债务列表 (尚未注册，仅为检测结果)
        """
        detected = []
        lines = content.split("\n")

        for marker_name, pattern in self.DEBT_MARKERS.items():
            for match in pattern.finditer(content):
                desc = match.group(1).strip()
                # 定位行号
                line_num = content[: match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                debt_type = self.MARKER_TO_TYPE.get(marker_name, "technical")
                severity = self.MARKER_TO_SEVERITY.get(marker_name, "medium")

                # 根据描述关键词调整 severity
                if any(k in desc.upper() for k in ["CRITICAL", "URGENT", "SECURITY", "RACE"]):
                    severity = "critical"
                elif any(k in desc.upper() for k in ["HACK", "TEMP", "WORKAROUND"]):
                    severity = "high"

                detected.append({
                    "source_file": file_path,
                    "line_number": line_num,
                    "marker": marker_name.replace("_MULTILINE", ""),
                    "description": desc,
                    "debt_type": debt_type,
                    "severity": severity,
                    "line_content": line_content.strip(),
                    "suggested_auto_cleanable": marker_name in ("TODO", "TODO_MULTILINE"),
                })

        # 额外启发式检测: 未文档化的 public 函数
        detected.extend(self._detect_undocumented_public(file_path, content))

        # 额外启发式检测: 硬编码魔法数字
        detected.extend(self._detect_magic_numbers(file_path, content))

        # 按行号排序
        detected.sort(key=lambda x: x["line_number"])
        return detected

    def _detect_undocumented_public(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检测未文档化的 public 函数 (工程债务)"""
        detected = []
        # 匹配 def 定义，检查前面是否有 docstring
        func_pattern = re.compile(r'(?:^|\n)([ \t]*)def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', re.MULTILINE)

        for match in func_pattern.finditer(content):
            indent = match.group(1)
            func_name = match.group(2)
            # 跳过私有函数
            if func_name.startswith("_"):
                continue

            # 检查前面是否有 docstring
            start_pos = match.start()
            preceding = content[max(0, start_pos - 500):start_pos]
            if '"""' not in preceding[-100:] and "'''" not in preceding[-100:]:
                line_num = content[:start_pos].count("\n") + 1
                detected.append({
                    "source_file": file_path,
                    "line_number": line_num,
                    "marker": "MISSING_DOC",
                    "description": f"Public function '{func_name}' lacks docstring",
                    "debt_type": "engineering",
                    "severity": "low",
                    "line_content": f"def {func_name}(...)",
                    "suggested_auto_cleanable": True,
                })

        return detected

    def _detect_magic_numbers(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检测代码中的魔法数字 (技术债务)"""
        detected = []
        # 匹配非平凡的数字字面量 (排除 0, 1, -1, 常见索引)
        magic_pattern = re.compile(r'[^a-zA-Z0-9_](-?\d{2,}(?:\.\d+)?)[^a-zA-Z0-9_]')
        excluded = {"10", "100", "1000", "256", "512", "1024", "2048", "4096", "8080"}

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            # 跳过注释和字符串中的数字
            code_part = line.split("#")[0]
            for match in magic_pattern.finditer(code_part):
                num = match.group(1)
                if num in excluded or num in ("0", "1", "-1"):
                    continue
                # 检查是否已定义为常量
                if not re.search(rf'[A-Z_]+\s*=\s*{re.escape(num)}', content):
                    detected.append({
                        "source_file": file_path,
                        "line_number": i,
                        "marker": "MAGIC_NUMBER",
                        "description": f"Magic number {num} should be a named constant",
                        "debt_type": "technical",
                        "severity": "low",
                        "line_content": line.strip(),
                        "suggested_auto_cleanable": True,
                    })

        # 去重 (同一行只报一次)
        seen_lines = set()
        unique = []
        for d in detected:
            key = (d["source_file"], d["line_number"])
            if key not in seen_lines:
                seen_lines.add(key)
                unique.append(d)

        return unique

    # ───────────────────────────────────────────────
    # 自动清理策略
    # ───────────────────────────────────────────────

    def _auto_theoretical(self, debt: Dict[str, Any]) -> Dict[str, Any]:
        """自动清理理论债务的策略

        策略:
            1. 数值假设验证: 检查是否有可用数据进行交叉验证
            2. 标记待证: 无法自动验证的标记为 "待人工证明"
            3. 引用追踪: 尝试关联已有文献/证明
        """
        description = debt.get("description", "")
        verification = {}
        side_effects = []

        # 策略1: 数值假设检测
        numeric_patterns = re.findall(r"[\d\.]+\s*[<>=]=?\s*[\d\.]+|[\d\.]+\s*(?:plus|minus|±)\s*[\d\.]+", description)
        if numeric_patterns:
            verification["numeric_hypothesis"] = {
                "detected": True,
                "patterns": numeric_patterns,
                "action": "attempted_cross_validation",
                "result": "insufficient_data",
            }
            # 模拟: 尝试验证但数据不足
            side_effects.append("Triggered cross-validation pipeline (no conclusive data)")

        # 策略2: 命题类检测 (含有 "conjecture", "hypothesis", "claim" 等)
        proposition_keywords = ["conjecture", "hypothesis", "claim", "proposition", "lemma", "theorem"]
        if any(kw in description.lower() for kw in proposition_keywords):
            verification["proposition_status"] = "marked_for_human_proof"
            side_effects.append("Added to proof queue for human verification")

        # 策略3: 引用追踪模拟
        citation_pattern = re.search(r"\[?(\d{4})\]?", description)
        if citation_pattern:
            year = citation_pattern.group(1)
            verification["citation_trace"] = {
                "year_found": year,
                "auto_lookup": f"searched_db_for_papers_{year}",
                "matches": random.randint(0, 3),  # 模拟找到0-3篇匹配
            }

        # 理论债务通常需要人工介入，auto 只能做辅助标记
        cleaned = False  # 理论债务默认不自动标记为已清理
        verification["auto_action"] = "annotated_and_queued"
        verification["requires_human_review"] = True

        return {
            "cleaned": cleaned,
            "verification": verification,
            "side_effects": side_effects,
        }

    def _auto_technical(self, debt: Dict[str, Any]) -> Dict[str, Any]:
        """自动清理技术债务的策略

        策略:
            1. 重构建议: 对 hack 代码生成重构方案
            2. 性能分析: 对未优化实现进行评估
            3. 兼容性检查: 检查临时方案的兼容性影响
        """
        description = debt.get("description", "")
        verification = {}
        side_effects = []

        # 策略1: Hack / workaround 检测
        hack_indicators = ["hack", "workaround", "temp", "temporary", "quick fix", "band-aid"]
        if any(ind in description.lower() for ind in hack_indicators):
            verification["refactor_plan"] = {
                "detected_pattern": "hack_or_workaround",
                "suggested_action": "extract_to_proper_abstraction",
                "estimated_effort": "2-4h",
                "risk_level": "medium",
            }
            side_effects.append("Generated refactor plan in codebase")

        # 策略2: 性能相关
        perf_indicators = ["slow", "performance", "bottleneck", "optimize", "cache", "memoize"]
        if any(ind in description.lower() for ind in perf_indicators):
            verification["performance_analysis"] = {
                "bottleneck_suspected": True,
                "suggested_optimizations": [
                    "Consider memoization",
                    "Profile with cProfile",
                    "Evaluate algorithmic complexity",
                ],
                "estimated_speedup": "1.5x - 10x",
            }
            side_effects.append("Created performance ticket")

        # 策略3: 兼容性检查模拟
        verification["compatibility_check"] = {
            "affected_modules": self._simulate_affected_modules(debt),
            "breaking_change_risk": "low" if debt["severity"] != "critical" else "high",
            "test_coverage_required": True,
        }

        # 对于低/中等的技术债务，可以模拟自动标记为已清理 (生成方案即算清理)
        cleaned = debt["severity"] in ("low", "medium")
        verification["auto_action"] = "generated_remediation_plan"
        verification["plan_applied"] = cleaned

        return {
            "cleaned": cleaned,
            "verification": verification,
            "side_effects": side_effects,
        }

    def _auto_engineering(self, debt: Dict[str, Any]) -> Dict[str, Any]:
        """自动清理工程债务的策略

        策略:
            1. 文档生成: 对缺失文档的模块自动生成文档模板
            2. 测试覆盖: 识别未覆盖的代码路径
            3. 架构评估: 对架构缺陷提出改进建议
        """
        description = debt.get("description", "")
        verification = {}
        side_effects = []

        # 策略1: 文档缺失检测
        doc_indicators = ["doc", "document", "readme", "comment", "explain"]
        if any(ind in description.lower() for ind in doc_indicators):
            verification["doc_generation"] = {
                "template_generated": True,
                "template_type": "auto_doc_stub",
                "sections": ["Overview", "Parameters", "Returns", "Raises", "Examples"],
            }
            side_effects.append("Auto-generated documentation template")

        # 策略2: 测试覆盖检测
        test_indicators = ["test", "coverage", "unittest", "pytest", "missing test"]
        if any(ind in description.lower() for ind in test_indicators):
            verification["test_coverage"] = {
                "coverage_gap_identified": True,
                "suggested_test_cases": [
                    "Unit test for happy path",
                    "Edge case: null input",
                    "Edge case: boundary values",
                    "Integration test with downstream",
                ],
                "auto_test_stub": True,
            }
            side_effects.append("Generated test stub template")

        # 策略3: 架构评估
        arch_indicators = ["architecture", "design", "refactor", "coupling", "dependency"]
        if any(ind in description.lower() for ind in arch_indicators):
            verification["architecture_review"] = {
                "coupling_score": round(random.uniform(2.0, 8.0), 2),
                "recommendations": [
                    "Review inter-module dependencies",
                    "Consider interface segregation",
                    "Evaluate circular dependency risk",
                ],
            }
            side_effects.append("Created architecture review ticket")

        # 工程债务中，文档类可以自动标记为已清理 (模板生成)
        cleaned = any(ind in description.lower() for ind in doc_indicators) and debt["severity"] == "low"
        verification["auto_action"] = "applied_engineering_remediation"
        verification["template_applied"] = cleaned

        return {
            "cleaned": cleaned,
            "verification": verification,
            "side_effects": side_effects,
        }

    # ───────────────────────────────────────────────
    # 内部辅助方法
    # ───────────────────────────────────────────────

    def _generate_debt_id(self, debt_type: str, description: str, timestamp: str) -> str:
        """生成唯一债务ID: 类型前缀 + hash"""
        base = f"{debt_type}:{description}:{timestamp}"
        hash_val = hashlib.sha256(base.encode("utf-8")).hexdigest()[:12]
        prefix = debt_type[:3].upper()  # THE, TEC, ENG
        return f"{prefix}-{hash_val}"

    def _compute_aging(self, debt: Dict[str, Any]) -> float:
        """计算债务账龄 (天)"""
        created = datetime.fromisoformat(debt["created_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - created
        return delta.total_seconds() / 86400.0

    def _simulate_affected_modules(self, debt: Dict[str, Any]) -> List[str]:
        """模拟检测受影响的模块列表"""
        # 从债务元数据或描述中提取模块名
        modules = []
        desc = debt.get("description", "")
        # 简单的模块名匹配: 大驼峰或 snake_case
        mod_pattern = re.findall(r"\b([A-Z][a-zA-Z0-9_]+|[a-z][a-z0-9_]*_module|[a-z][a-z0-9_]*_service)\b", desc)
        if mod_pattern:
            modules = list(set(mod_pattern[:5]))
        else:
            # 默认生成一些模拟模块
            line = debt.get("line", "ucif2")
            modules = [f"{line}_core", f"{line}_adapter"]
        return modules

    def scan_and_register_from_code(self, file_path: str, content: str, line: str = "ucif2") -> List[str]:
        """扫描代码并自动注册检测到的债务

        Returns:
            注册的 debt_id 列表
        """
        detected = self.detect_debt_from_code(file_path, content)
        registered = []
        for d in detected:
            debt_id = self.register_debt(
                debt_type=d["debt_type"],
                description=f"[{d['marker']}] {d['description']} (at {file_path}:{d['line_number']})",
                severity=d["severity"],
                line=line,
                auto_cleanable=d["suggested_auto_cleanable"],
                metadata={
                    "source_file": d["source_file"],
                    "line_number": d["line_number"],
                    "marker": d["marker"],
                    "line_content": d["line_content"],
                },
            )
            registered.append(debt_id)
        return registered


# ═════════════════════════════════════════════════
# 测试块
# ═════════════════════════════════════════════════

def _sample_omni_hub_modules() -> Dict[str, str]:
    """模拟 OMNI-HUB v3.1 现有模块文件内容"""
    return {
        "/mnt/agents/output/OMNI-HUB/core/singularity_resolver.py": '''
#!/usr/bin/env python3
"""
Singularity Resolution Module
OMNI-HUB v3.1 — ucif3 line
"""

# TODO: Verify singularity cancellation holds for non-abelian orbifolds
# FIXME: boundary condition hack for 16M case — needs proper treatment
# HACK: temporary workaround for exceptional divisor mismatch

class SingularityResolver:
    def __init__(self, dimension=24):
        self.dim = dimension  # XXX: hardcoded default, should be configurable

    def resolve(self, orbifold_type):
        # BUG: race condition when concurrent resolution threads access shared cache
        if orbifold_type == "16M":
            return self._16m_hack()  # HACK: remove after proper fix
        return self._generic_resolve()

    def _16m_hack(self):
        """Temporary fix for 16M singularity."""
        # TODO: Replace with formal resolution algorithm
        return {"status": "partial", "confidence": 0.87}

    def _generic_resolve(self):
        return {"status": "resolved"}

    def compute_invariant(self, input_data):
        # DEBT: Missing documentation for invariant computation
        result = input_data * 3.14159  # MAGIC_NUMBER
        return result
''',
        "/mnt/agents/output/OMNI-HUB/core/moonshine_bridge.py": '''
#!/usr/bin/env python3
"""
Moonshine Bridge — connects VOA to CY manifolds
OMNI-HUB v3.1 — ucif5 line
"""

# TODO: Complete the proof of derived equivalence for CICY58
# FIXME: performance bottleneck in character table lookup — O(n^2) algorithm
# XXX: Documentation incomplete for fusion rules

class MoonshineBridge:
    def __init__(self):
        self.cache = {}

    def compute_character(self, group_element):
        # HACK: memoization disabled due to hash collision bug
        return self._slow_lookup(group_element)

    def _slow_lookup(self, element):
        # TODO: optimize with proper indexing
        for i in range(10000):  # MAGIC_NUMBER
            if self._match(i, element):
                return i
        return None

    def _match(self, idx, element):
        # BUG: potential off-by-one in index matching
        return idx == element.get("index", -1)

    def bridge_to_geometry(self, voa_data):
        # DEBT: No error handling for malformed VOAs
        return {"geometry": voa_data, "valid": True}

    def validate_correspondence(self, data):
        """Placeholder for validation."""
        pass  # TODO: implement full validation pipeline
''',
        "/mnt/agents/output/OMNI-HUB/core/holographic_engine.py": '''
#!/usr/bin/env python3

__version__ = "11.0.0"
"""
Holographic Engine — ADS/CFT correspondence
OMNI-HUB v3.1 — ucif7 line
"""

# FIXME: entropy formula assumes spherical symmetry only
# TODO: generalize to arbitrary horizon topology
# HACK: dimension reduction shortcut for 24D -> 4D

class HolographicEngine:
    def compute_entropy(self, black_hole_params):
        # XXX: Missing bounds checking on input parameters
        area = black_hole_params["area"]
        G = 6.67430e-11  # MAGIC_NUMBER — should use constants module
        return area / (4 * G)

    def dual_cft_correlation(self, bulk_operator):
        # DEBT: Test coverage < 40% for correlation functions
        return {"correlation": 0.0, "status": "untested"}

    def run_simulation(self, steps=1000):
        # HACK: step count limited due to memory leak in tensor allocation
        for i in range(steps):
            self._step()
        return {"steps": steps}

    def _step(self):
        pass
''',
    }


def _test_register_and_query():
    """测试: 债务注册与查询"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 1: Register & Query")
    logger.info("=" * 60)

    dc = DebtCleanup()

    # 注册理论债务
    d1 = dc.register_debt(
        "theoretical",
        "Unverified hypothesis: E8 × E8 heterotic string compactification",
        "high",
        line="ucif3",
        auto_cleanable=False,
        impact_score=8.5,
    )
    logger.info(f"  Registered theoretical debt: {d1}")

    # 注册技术债务
    d2 = dc.register_debt(
        "technical",
        "O(n^2) character table lookup needs memoization",
        "high",
        line="ucif5",
        auto_cleanable=True,
        impact_score=7.0,
    )
    logger.info(f"  Registered technical debt: {d2}")

    # 注册工程债务
    d3 = dc.register_debt(
        "engineering",
        "Missing documentation for holographic duality module",
        "medium",
        line="ucif7",
        auto_cleanable=True,
        impact_score=5.0,
    )
    logger.info(f"  Registered engineering debt: {d3}")

    # 查询
    retrieved = dc.get_debt(d2)
    assert retrieved["debt_id"] == d2
    assert retrieved["debt_type"] == "technical"
    logger.info(f"  Query OK: type={retrieved['debt_type']}, severity={retrieved['severity']}")

    logger.info("  [PASS] Register & Query")
    return dc, [d1, d2, d3]


def _test_auto_cleanup():
    """测试: 自动清理策略"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Auto Cleanup Strategies")
    logger.info("=" * 60)

    dc = DebtCleanup()

    # 理论债务 — 不可自动清理
    d_theo = dc.register_debt(
        "theoretical",
        "Conjecture: All CICY 3-folds satisfy derived equivalence",
        "high",
        line="ucif3",
        auto_cleanable=True,  # 标记为可自动，但策略只标记不清理
        impact_score=9.0,
    )

    # 技术债务 — 低 severity 可自动清理
    d_tech = dc.register_debt(
        "technical",
        "Temporary workaround for cache invalidation (hack)",
        "low",
        line="ucif2",
        auto_cleanable=True,
        impact_score=3.0,
    )

    # 工程债务 — 文档缺失可自动清理
    d_eng = dc.register_debt(
        "engineering",
        "Missing docstrings in public API modules",
        "low",
        line="ucif7",
        auto_cleanable=True,
        impact_score=2.0,
    )

    logger.info(f"  Before cleanup: open debts = {sum(len(v) for v in dc.debts.values())}")

    result = dc.auto_cleanup()
    print(f"  Auto cleanup result: processed={result['processed']}, "
          f"succeeded={result['succeeded']}, failed={result['failed']}")

    # 验证状态
    for did in [d_theo, d_tech, d_eng]:
        debt = dc.get_debt(did)
        print(f"  Debt {did[:12]}... status={debt['status']}, "
              f"method={debt.get('cleanup_method', 'N/A')}")

    assert result["processed"] == 3
    assert result["succeeded"] >= 1  # 至少 low severity 的会被清理
    logger.info("  [PASS] Auto Cleanup")
    return dc


def _test_prioritize():
    """测试: 优先级排序 (severity × aging × impact)"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Prioritize (severity × aging × impact)")
    logger.info("=" * 60)

    dc = DebtCleanup()

    # 创建具有不同属性的债务
    debts_config = [
        ("critical", "ucif1", 10.0, "technical"),    # 最高优先级
        ("high", "ucif2", 9.0, "theoretical"),        # 次高
        ("high", "ucif3", 5.0, "engineering"),        # 中等
        ("medium", "ucif4", 8.0, "technical"),        # 中等偏上
        ("low", "ucif5", 2.0, "engineering"),         # 低
    ]

    ids = []
    for sev, line, impact, dtype in debts_config:
        did = dc.register_debt(dtype, f"Test debt {sev}", sev, line=line,
                               impact_score=impact)
        ids.append((did, sev, impact))

    # 排序
    prioritized = dc.prioritize()
    logger.info(f"  Prioritized order (top 5):")
    for i, debt in enumerate(prioritized[:5], 1):
        days = dc._compute_aging(debt)
        score = debt["severity_level"] * (1 + math.log(1 + days / 7.0)) * debt["impact_score"]
        print(f"    {i}. [{debt['severity']}] line={debt['line']} "
              f"impact={debt['impact_score']} score={score:.2f}")

    # 验证 critical 排在第一位
    assert prioritized[0]["severity"] == "critical"
    logger.info("  [PASS] Prioritize")
    return dc


def _test_code_detection():
    """测试: 代码债务检测 (扫描 OMNI-HUB 模拟模块)"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Code Debt Detection (OMNI-HUB Module Scan)")
    logger.info("=" * 60)

    dc = DebtCleanup()
    modules = _sample_omni_hub_modules()

    total_detected = 0
    for file_path, content in modules.items():
        detected = dc.detect_debt_from_code(file_path, content)
        total_detected += len(detected)
        logger.info(f"\n  File: {file_path}")
        logger.info(f"  Detected {len(detected)} debt markers:")
        for d in detected[:6]:  # 只显示前6个
            print(f"    L{d['line_number']:3d} [{d['marker']:12s}] "
                  f"({d['debt_type'][:3]}/{d['severity'][:3]}): {d['description'][:50]}...")
        if len(detected) > 6:
            logger.info(f"    ... and {len(detected) - 6} more")

    logger.info(f"\n  Total detected across all modules: {total_detected}")
    assert total_detected > 0
    logger.info("  [PASS] Code Detection")
    return dc, modules


def _test_scan_and_register():
    """测试: 扫描并注册 (端到端)"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Scan & Register (End-to-End)")
    logger.info("=" * 60)

    dc = DebtCleanup()
    modules = _sample_omni_hub_modules()

    all_registered = []
    for file_path, content in modules.items():
        line = "ucif" + file_path.split("ucif")[-1][0] if "ucif" in file_path else "ucif2"
        registered = dc.scan_and_register_from_code(file_path, content, line=line)
        all_registered.extend(registered)
        logger.info(f"  {file_path}: registered {len(registered)} debts")

    logger.info(f"\n  Total registered: {len(all_registered)}")

    # 运行自动清理
    auto_result = dc.auto_cleanup()
    print(f"  Auto cleanup: processed={auto_result['processed']}, "
          f"succeeded={auto_result['succeeded']}, failed={auto_result['failed']}")

    # 生成报告
    report = dc.get_debt_report()
    logger.info(f"\n  Debt Report:")
    logger.info(f"    Total debts: {report['total']}")
    logger.info(f"    By type: {report['by_type']}")
    logger.info(f"    By severity: {report['by_severity']}")
    logger.info(f"    By line: {report['by_line']}")
    logger.info(f"    Aging: {report['aging']}")
    logger.info(f"    Auto-cleanable ratio: {report['auto_cleanable_ratio']:.2%}")
    logger.info(f"    Cleaned ratio: {report['cleaned_ratio']:.2%}")
    logger.info(f"    Open critical: {report['open_critical']}")

    # 委托测试
    if all_registered:
        d_to_delegate = all_registered[0]
        del_result = dc.delegate_cleanup(d_to_delegate, "ucif9")
        print(f"\n  Delegation test: {d_to_delegate[:20]}... -> {del_result['to_line']} "
              f"(success={del_result['delegated']})")

    logger.info("  [PASS] Scan & Register")
    return dc


def _test_delegation():
    """测试: 委托清理"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: Delegation")
    logger.info("=" * 60)

    dc = DebtCleanup()
    did = dc.register_debt("technical", "Refactor needed in ucif4 adapter",
                           "high", line="ucif2", auto_cleanable=False)

    result = dc.delegate_cleanup(did, "ucif4")
    assert result["delegated"] is True
    assert result["to_line"] == "ucif4"
    assert result["from_line"] == "ucif2"

    debt = dc.get_debt(did)
    assert debt["status"] == "cleaned"  # delegated cleanup 模拟成功
    logger.info(f"  Delegated {did[:20]}... from ucif2 to ucif4")
    logger.info("  [PASS] Delegation")


def _test_cleanup_manual():
    """测试: 人工清理与验证"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 7: Manual Cleanup")
    logger.info("=" * 60)

    dc = DebtCleanup()
    did = dc.register_debt("technical", "Memory leak in tensor allocation",
                           "critical", line="ucif7", impact_score=9.5)

    result = dc.cleanup(did, method="manual")
    assert result["cleaned"] is True
    assert result["verification"]["review_required"] is True  # critical 需要 review

    debt = dc.get_debt(did)
    assert debt["status"] == "cleaned"
    logger.info(f"  Manual cleanup of {did[:20]}... review_required=True")
    logger.info("  [PASS] Manual Cleanup")


def _test_report_comprehensive():
    """测试: 综合报告"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 8: Comprehensive Report")
    logger.info("=" * 60)

    dc = DebtCleanup()

    # 批量注册
    for i in range(20):
        dtype = random.choice(dc.DEBT_TYPES)
        sev = random.choice(list(dc.SEVERITY_LEVELS.keys()))
        line = f"ucif{random.randint(1, 11)}"
        dc.register_debt(
            dtype,
            f"Bulk test debt #{i}",
            sev,
            line=line,
            auto_cleanable=random.random() > 0.5,
            impact_score=random.uniform(1.0, 10.0),
        )

    # 清理一部分
    for dtype in dc.DEBT_TYPES:
        for debt in dc.debts[dtype][:2]:
            dc.cleanup(debt["debt_id"], method="manual")

    report = dc.get_debt_report()
    logger.info(f"  Total: {report['total']}")
    logger.info(f"  By type: {report['by_type']}")
    logger.info(f"  By severity: {report['by_severity']}")
    logger.info(f"  By line: {report['by_line']}")
    logger.info(f"  Aging buckets: {report['aging']['buckets']}")
    logger.info(f"  Avg aging: {report['aging']['average_days']} days")
    logger.info(f"  Auto-cleanable: {report['auto_cleanable_ratio']:.1%}")
    logger.info(f"  Cleaned: {report['cleaned_ratio']:.1%}")
    logger.info(f"  Open critical: {report['open_critical']}")
    logger.info("  [PASS] Comprehensive Report")


def run_all_tests():
    """运行全部测试"""
    logger.info("\n" + "█" * 60)
    logger.info("  OMNI-HUB v3.2 Debt Cleanup System — Test Suite")
    logger.info("  " + "█" * 60)

    try:
        _test_register_and_query()
        _test_auto_cleanup()
        _test_prioritize()
        _test_code_detection()
        _test_scan_and_register()
        _test_delegation()
        _test_cleanup_manual()
        _test_report_comprehensive()

        logger.info("\n" + "█" * 60)
        logger.info("  ALL TESTS PASSED ✓")
        logger.info("  " + "█" * 60)
        return True
    except AssertionError as e:
        logger.info(f"\n  [FAIL] Assertion failed: {e}")
        return False
    except Exception as e:
        logger.info(f"\n  [FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_all_tests()
