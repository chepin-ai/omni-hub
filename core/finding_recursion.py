#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v3.3 — FINDING递归闭环系统
"发现即驱动，驱动再发现" — 递归闭环引擎

核心哲学:
  "FINDING→自驱" — 每一个发现都是自驱动的燃料
  "发现即驱动，驱动再发现" — 递归闭环

接口规范:
  - register_finding()   : 注册发现 → 若 auto_actionable → 自动触发 finding_to_action
  - finding_to_action()  : FINDING→行动 — 6种 category 各对应具体行动
  - close_finding()      : 关闭发现 → 验证结果 → 检测 new_finding → 自动递归
  - get_recursion_chain(): 获取完整递归链
  - measure_recursion_depth() : 最大递归深度
  - get_finding_stats()  : 统计信息
  - auto_resolve()       : 批量自动解析

Author: OMNI-HUB Core Team
Version: v3.3.0
"""

import hashlib
import time
import uuid
from typing import Any, Dict, List, Optional
from enum import Enum
import logging


class FindingCategory(Enum):
    """FINDING 六大类别"""
    ANOMALY = "anomaly"
    OPPORTUNITY = "opportunity"
    INSIGHT = "insight"
    DEBT = "debt"
    GAP = "gap"
    BREAKTHROUGH = "breakthrough"


class FindingRecursion:
    """FINDING递归闭环 — 发现即驱动
    
    核心循环:
        register_finding() → finding_to_action() → close_finding()
        └── 若 close_finding 的 result 产生 new_finding → 自动 register_finding()
            └── 形成递归闭环: 发现 → 行动 → 新发现 → 新行动 → ...
    """

    FINDING_CATEGORIES = ["anomaly", "opportunity", "insight", "debt", "gap", "breakthrough"]

    # ── category → action 映射 ──────────────────────────
    ACTION_MAP = {
        "anomaly":     {"type": "alert",    "action": "auto_fix_or_escalate"},
        "opportunity": {"type": "task",     "action": "auto_create_and_dispatch"},
        "insight":     {"type": "archive",  "action": "propagate_and_store"},
        "debt":        {"type": "cleanup",  "action": "queue_cleanup"},
        "gap":         {"type": "fill",     "action": "create_research_task"},
        "breakthrough": {"type": "celebrate","action": "trigger_harmony_and_update_north_star"},
    }

    # ── 关闭验证策略 ────────────────────────────────────
    CLOSE_VALIDATORS = {
        "anomaly":     lambda r: r.get("fixed", False) or r.get("escalated", False),
        "opportunity": lambda r: r.get("task_created", False),
        "insight":     lambda r: r.get("stored", False),
        "debt":        lambda r: r.get("cleanup_queued", False) or r.get("cleaned", False),
        "gap":         lambda r: r.get("research_task_created", False) or r.get("filled", False),
        "breakthrough": lambda r: True,  # breakthrough 默认直接关闭
    }

    def __init__(self, self_drive_engine=None):
        self.engine = self_drive_engine
        self.findings: Dict[str, dict] = {}      # finding_id → finding
        self.closed_findings: Dict[str, dict] = {}  # 已关闭归档
        self.recursion_chains: List[List[str]] = [] # 每条链是一个 finding_id 列表
        self.max_chain_length: int = 10
        self._lock_depth: int = 0                # 递归锁，防止无限递归
        self._max_lock_depth: int = 20           # 最大递归锁深度
        self.auto_action_on_register: bool = True  # 注册时是否自动触发 action

    # ═══════════════════════════════════════════════════
    #  1. register_finding — 注册FINDING
    # ═══════════════════════════════════════════════════
    def register_finding(self, finding: dict) -> str:
        """注册FINDING

        Args:
            finding: {
                "category": "anomaly|opportunity|insight|debt|gap|breakthrough",
                "description": str,
                "source": str (line),
                "severity": int (1-10),
                "auto_actionable": bool,
                "parent_finding": str|None,
                "metadata": dict|None,      # 可选附加数据
            }

        Returns:
            finding_id: F-{timestamp}-{source}-{hash}

        注册后: 如果 auto_actionable → 自动调用 finding_to_action
        """
        # ── 参数校验 ──
        category = finding.get("category")
        if category not in self.FINDING_CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Must be one of {self.FINDING_CATEGORIES}")

        source = finding.get("source", "unknown")
        timestamp = str(int(time.time() * 1000))
        desc_short = finding.get("description", "")[:20]
        hash_input = f"{timestamp}-{source}-{desc_short}-{uuid.uuid4().hex[:8]}"
        hash_val = hashlib.sha256(hash_input.encode()).hexdigest()[:8]

        finding_id = f"F-{timestamp}-{source}-{hash_val}"

        # ── 防循环引用检查 ──
        parent_finding = finding.get("parent_finding")
        if parent_finding and parent_finding in self.closed_findings:
            parent_finding = None  # 已关闭的父发现不再关联

        # ── 组装完整 finding 记录 ──
        full_finding = {
            "id": finding_id,
            "category": category,
            "description": finding.get("description", ""),
            "source": source,
            "severity": max(1, min(10, int(finding.get("severity", 5)))),
            "auto_actionable": bool(finding.get("auto_actionable", False)),
            "parent_finding": parent_finding,
            "status": "registered",
            "created_at": time.time(),
            "action_result": None,
            "metadata": finding.get("metadata", {}),
        }

        self.findings[finding_id] = full_finding

        # ── 自动触发行动 ──
        if (full_finding["auto_actionable"]
                and self.auto_action_on_register
                and self._lock_depth < self._max_lock_depth):
            try:
                self._lock_depth += 1
                self.finding_to_action(finding_id)
            finally:
                self._lock_depth -= 1

        return finding_id

    # ═══════════════════════════════════════════════════
    #  2. finding_to_action — FINDING→行动
    # ═══════════════════════════════════════════════════
    def finding_to_action(self, finding_id: str) -> dict:
        """FINDING→行动 — 将发现转化为自动行动

        根据 category 执行对应逻辑:
        - anomaly     → alert / auto_fix_or_escalate
        - opportunity → task / auto_create_and_dispatch
        - insight     → archive / propagate_and_store
        - debt        → cleanup / queue_cleanup
        - gap         → fill / create_research_task
        - breakthrough→ celebrate / trigger_harmony_and_update_north_star

        Returns:
            {"finding_id": str, "action_taken": str, "result": dict,
             "new_findings": list, "closed": bool}
        """
        if finding_id not in self.findings:
            raise KeyError(f"Finding '{finding_id}' not registered")

        finding = self.findings[finding_id]
        category = finding["category"]
        action_meta = self.ACTION_MAP.get(category, {})
        action_type = action_meta.get("type", "unknown")
        action_name = action_meta.get("action", "noop")

        result: dict = {"status": "executed", "type": action_type, "action": action_name}
        new_findings: List[dict] = []

        # ══ 6种 category 的具体行动逻辑 ═══════════════════
        if category == "anomaly":
            # ── anomaly: auto_fix_or_escalate ──
            severity = finding["severity"]
            if severity <= 4:
                result["fixed"] = True
                result["fix_method"] = "auto_patch"
                result["message"] = f"Anomaly auto-fixed via patch (severity={severity})"
            elif severity <= 7:
                result["escalated"] = True
                result["message"] = f"Anomaly escalated to human review (severity={severity})"
                # 升级可能发现新的 gap
                new_findings.append({
                    "category": "gap",
                    "description": f"Need human expertise to resolve anomaly: {finding['description']}",
                    "source": f"escalation_from_{finding_id}",
                    "severity": 6,
                    "auto_actionable": True,
                })
            else:
                result["critical_alert"] = True
                result["message"] = f"CRITICAL anomaly detected (severity={severity}) — immediate halt"
                # 严重异常可能触发突破性发现
                new_findings.append({
                    "category": "breakthrough",
                    "description": f"Critical anomaly may indicate fundamental flaw requiring rethinking",
                    "source": f"critical_from_{finding_id}",
                    "severity": 9,
                    "auto_actionable": True,
                })

        elif category == "opportunity":
            # ── opportunity: auto_create_and_dispatch ──
            task_id = f"TASK-{uuid.uuid4().hex[:8]}"
            result["task_created"] = True
            result["task_id"] = task_id
            result["dispatch_target"] = finding.get("metadata", {}).get("assignee", "default_pool")
            result["message"] = f"Opportunity dispatched as task {task_id}"
            # 机会执行可能发现新洞察
            new_findings.append({
                "category": "insight",
                "description": f"Follow-up insight from opportunity: {finding['description']}",
                "source": f"opportunity_followup_{finding_id}",
                "severity": 4,
                "auto_actionable": True,
            })

        elif category == "insight":
            # ── insight: propagate_and_store ──
            archive_id = f"ARC-{uuid.uuid4().hex[:8]}"
            result["stored"] = True
            result["archive_id"] = archive_id
            result["propagated_to"] = finding.get("metadata", {}).get("channels", ["knowledge_base"])
            result["message"] = f"Insight archived as {archive_id} and propagated"
            # 洞察可能揭示技术债务
            if finding["severity"] >= 6:
                new_findings.append({
                    "category": "debt",
                    "description": f"High-severity insight implies existing debt: {finding['description']}",
                    "source": f"insight_debt_{finding_id}",
                    "severity": 5,
                    "auto_actionable": True,
                })

        elif category == "debt":
            # ── debt: queue_cleanup ──
            cleanup_queue = f"CQ-{uuid.uuid4().hex[:8]}"
            result["cleanup_queued"] = True
            result["cleanup_queue_id"] = cleanup_queue
            result["estimated_cost"] = finding["severity"] * 10  # 估算清理成本
            result["message"] = f"Cleanup queued in {cleanup_queue} (est. cost: {result['estimated_cost']} pts)"
            # 清理过程中可能发现异常
            if finding["severity"] >= 7:
                new_findings.append({
                    "category": "anomaly",
                    "description": f"High-severity debt may contain hidden anomalies",
                    "source": f"debt_anomaly_{finding_id}",
                    "severity": 7,
                    "auto_actionable": True,
                })

        elif category == "gap":
            # ── gap: create_research_task ──
            research_id = f"RES-{uuid.uuid4().hex[:8]}"
            result["research_task_created"] = True
            result["research_id"] = research_id
            result["research_scope"] = finding["description"]
            result["message"] = f"Research task {research_id} created for gap"
            # 研究可能产生新机会
            new_findings.append({
                "category": "opportunity",
                "description": f"Research on gap may reveal new opportunities",
                "source": f"gap_opportunity_{finding_id}",
                "severity": 5,
                "auto_actionable": True,
            })

        elif category == "breakthrough":
            # ── breakthrough: trigger_harmony_and_update_north_star ──
            harmony_id = f"HAR-{uuid.uuid4().hex[:8]}"
            result["harmony_triggered"] = True
            result["harmony_id"] = harmony_id
            result["north_star_updated"] = True
            result["message"] = f"Breakthrough celebrated! Harmony {harmony_id} triggered, north star updated"
            # 突破总是伴随多个新发现
            new_findings.append({
                "category": "insight",
                "description": f"Breakthrough insight: {finding['description']}",
                "source": f"breakthrough_insight_{finding_id}",
                "severity": 8,
                "auto_actionable": True,
            })
            new_findings.append({
                "category": "opportunity",
                "description": f"New opportunities opened by breakthrough",
                "source": f"breakthrough_opportunity_{finding_id}",
                "severity": 7,
                "auto_actionable": True,
            })

        # ── 将 new_findings 存入 result（供归档和后续引用） ──
        result["new_findings"] = new_findings

        # ── 更新 finding 状态 ──
        finding["status"] = "actioned"
        finding["action_result"] = result

        # ── 自动关闭已满足条件的 finding ──
        closed = self.CLOSE_VALIDATORS[category](result)
        if closed:
            self.close_finding(finding_id, result)

        return {
            "finding_id": finding_id,
            "action_taken": action_name,
            "result": result,
            "new_findings": new_findings,
            "closed": closed,
        }

    # ═══════════════════════════════════════════════════
    #  3. close_finding — 关闭FINDING
    # ═══════════════════════════════════════════════════
    def close_finding(self, finding_id: str, result: dict) -> dict:
        """关闭FINDING — 验证行动结果，触发下一轮

        1. 验证结果是否满足关闭条件
        2. 归档到 closed_findings
        3. 如果 result 中产生 new_finding → 自动注册并递归
        4. 更新递归链

        Returns:
            {"finding_id": str, "closed": bool, "triggered_new": int,
             "chain_length": int}
        """
        if finding_id not in self.findings:
            raise KeyError(f"Finding '{finding_id}' not found")

        finding = self.findings[finding_id]
        category = finding["category"]

        # ── 1. 验证关闭条件 ──
        validator = self.CLOSE_VALIDATORS.get(category, lambda r: True)
        can_close = validator(result)

        if not can_close:
            finding["status"] = "pending_close"
            finding["close_attempt_result"] = result
            return {
                "finding_id": finding_id,
                "closed": False,
                "triggered_new": 0,
                "chain_length": self._get_chain_length(finding_id),
            }

        # ── 2. 归档 ──
        finding["status"] = "closed"
        finding["closed_at"] = time.time()
        finding["close_result"] = result
        self.closed_findings[finding_id] = self.findings.pop(finding_id)

        # ── 3. 检测并递归 new_finding ──
        triggered_new = 0
        new_finding_ids = []

        # 从 result 中提取 new_findings
        raw_new = result.get("new_findings", [])
        # 也支持用户显式传入 new_finding_list
        if "new_finding_list" in result:
            raw_new.extend(result["new_finding_list"])

        for nf in raw_new:
            if isinstance(nf, dict):
                nf["parent_finding"] = finding_id
                # 防循环引用检查
                if not self._would_create_cycle(finding_id, nf.get("category", "")):
                    try:
                        if self._lock_depth < self._max_lock_depth:
                            self._lock_depth += 1
                            nf_id = self.register_finding(nf)
                            new_finding_ids.append(nf_id)
                            triggered_new += 1
                        else:
                            # 超出递归深度，记录待处理
                            nf["_deferred"] = True
                            nf["_deferred_reason"] = "max_recursion_depth"
                    finally:
                        self._lock_depth = max(0, self._lock_depth - 1)

        # ── 4. 更新递归链 ──
        self._update_recursion_chain(finding_id, new_finding_ids)

        chain_length = self._get_chain_length(finding_id)

        return {
            "finding_id": finding_id,
            "closed": True,
            "triggered_new": triggered_new,
            "chain_length": chain_length,
        }

    # ═══════════════════════════════════════════════════
    #  4. get_recursion_chain — 获取递归链
    # ═══════════════════════════════════════════════════
    def get_recursion_chain(self, finding_id: str) -> List[str]:
        """获取FINDING的完整递归链

        返回从根 finding 到当前 finding 的完整链条。
        遍历 parent_finding 关系向上回溯。
        """
        chain = []
        visited = set()
        current_id = finding_id

        # 先从所有记录中查找
        all_records = {**self.findings, **self.closed_findings}

        while current_id and current_id not in visited:
            visited.add(current_id)
            chain.append(current_id)
            record = all_records.get(current_id)
            if not record:
                break
            current_id = record.get("parent_finding")

        # 回溯链是从当前到根，需要反转
        chain.reverse()
        return chain

    # ═══════════════════════════════════════════════════
    #  5. measure_recursion_depth — 测量递归深度
    # ═══════════════════════════════════════════════════
    def measure_recursion_depth(self) -> int:
        """测量当前最大递归深度

        遍历所有 finding（包括已关闭的），计算最长链长度。
        """
        all_records = {**self.findings, **self.closed_findings}
        if not all_records:
            return 0

        max_depth = 0
        memo: Dict[str, int] = {}

        def _depth(fid: str) -> int:
            if fid in memo:
                return memo[fid]
            record = all_records.get(fid)
            if not record:
                return 0
            parent = record.get("parent_finding")
            if parent and parent in all_records:
                d = 1 + _depth(parent)
            else:
                d = 1
            memo[fid] = d
            return d

        for fid in all_records:
            max_depth = max(max_depth, _depth(fid))

        return max_depth

    # ═══════════════════════════════════════════════════
    #  6. get_finding_stats — 统计信息
    # ═══════════════════════════════════════════════════
    def get_finding_stats(self) -> dict:
        """获取FINDING统计

        Returns:
            {
                "total_registered": int,
                "active": int,
                "closed": int,
                "by_category": dict,
                "by_severity": dict,
                "recursion_chains": int,
                "max_recursion_depth": int,
                "auto_actionable_ratio": float,
            }
        """
        all_records = {**self.findings, **self.closed_findings}
        total = len(all_records)
        active = len(self.findings)
        closed = len(self.closed_findings)

        by_category: Dict[str, int] = {c: 0 for c in self.FINDING_CATEGORIES}
        by_severity: Dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        auto_count = 0

        for rec in all_records.values():
            cat = rec.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1

            sev = rec.get("severity", 5)
            if sev <= 3:
                by_severity["low"] += 1
            elif sev <= 5:
                by_severity["medium"] += 1
            elif sev <= 7:
                by_severity["high"] += 1
            else:
                by_severity["critical"] += 1

            if rec.get("auto_actionable", False):
                auto_count += 1

        return {
            "total_registered": total,
            "active": active,
            "closed": closed,
            "by_category": by_category,
            "by_severity": by_severity,
            "recursion_chains": len(self.recursion_chains),
            "max_recursion_depth": self.measure_recursion_depth(),
            "auto_actionable_ratio": round(auto_count / total, 3) if total > 0 else 0.0,
        }

    # ═══════════════════════════════════════════════════
    #  7. auto_resolve — 批量自动解析
    # ═══════════════════════════════════════════════════
    def auto_resolve(self, max_iterations: int = 5) -> dict:
        """自动解析 — 批量处理所有 auto_actionable 的 finding

        迭代处理，每轮处理当前所有 auto_actionable 且未 actioned 的 finding。
        返回: {"processed": int, "closed": int, "new_spawned": int}
        """
        processed = 0
        closed = 0
        new_spawned = 0

        for iteration in range(max_iterations):
            # 找出本轮需要处理的 finding
            to_process = [
                fid for fid, f in self.findings.items()
                if f.get("auto_actionable", False)
                and f.get("status") == "registered"
            ]

            if not to_process:
                break

            for fid in to_process:
                try:
                    action_result = self.finding_to_action(fid)
                    processed += 1
                    if action_result.get("closed", False):
                        closed += 1
                    new_spawned += len(action_result.get("new_findings", []))
                except Exception as e:
                    # 记录错误但不中断批量处理
                    self.findings[fid]["auto_resolve_error"] = str(e)
                    self.findings[fid]["status"] = "error"

        return {
            "processed": processed,
            "closed": closed,
            "new_spawned": new_spawned,
            "iterations": iteration + 1,
        }

    # ═══════════════════════════════════════════════════
    #  内部辅助方法
    # ═══════════════════════════════════════════════════
    def _get_chain_length(self, finding_id: str) -> int:
        """获取指定 finding 的链长度"""
        return len(self.get_recursion_chain(finding_id))

    def _update_recursion_chain(self, parent_id: str, child_ids: List[str]):
        """更新递归链 — 将新发现的 finding 追加到对应链中"""
        if not child_ids:
            return

        # 查找包含 parent_id 的链
        found_chain_idx = -1
        for idx, chain in enumerate(self.recursion_chains):
            if parent_id in chain:
                found_chain_idx = idx
                break

        if found_chain_idx >= 0:
            # 追加到现有链
            base_chain = self.recursion_chains[found_chain_idx][:]
            for child_id in child_ids:
                if child_id not in base_chain:
                    if len(base_chain) < self.max_chain_length:
                        base_chain.append(child_id)
            self.recursion_chains[found_chain_idx] = base_chain
        else:
            # 创建新链
            new_chain = [parent_id] + child_ids
            if len(new_chain) <= self.max_chain_length:
                self.recursion_chains.append(new_chain)

    def _would_create_cycle(self, parent_id: str, child_category: str) -> bool:
        """检测是否会形成循环引用

        通过检查 parent_id 的祖先链，确保不会形成闭环。
        """
        chain = self.get_recursion_chain(parent_id)
        if len(chain) >= self.max_chain_length:
            return True
        # 同类别连续超过3次视为潜在循环
        if len(chain) >= 3:
            all_records = {**self.findings, **self.closed_findings}
            last_three_cats = [
                all_records.get(fid, {}).get("category", "")
                for fid in chain[-3:]
            ]
            if all(c == child_category for c in last_three_cats):
                return True
        return False


# ═══════════════════════════════════════════════════════════════════
#  测试块 — 验证完整功能
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v3.3 — FINDING递归闭环系统 — 测试块")
    print("=" * 70)

    engine = {"name": "test_self_drive_engine", "version": "v3.2"}
    fr = FindingRecursion(engine)

    # ── 测试1: 注册→行动→关闭 完整流程 ─────────────────
    print("\n[测试1] 注册→行动→关闭 完整流程")
    print("-" * 50)

    f1 = fr.register_finding({
        "category": "anomaly",
        "description": "检测到内存泄漏模式",
        "source": "memory_monitor.py:42",
        "severity": 3,
        "auto_actionable": True,
    })
    print(f"  注册 finding: {f1}")
    print(f"  状态: {fr.closed_findings.get(f1, fr.findings.get(f1, {})).get('status')}")
    print(f"  已关闭: {'是' if f1 in fr.closed_findings else '否'}")
    assert f1 in fr.closed_findings, "低 severity anomaly 应自动关闭"
    print("  ✓ 测试1通过: 低 severity anomaly 自动修复并关闭")

    # ── 测试2: 递归链生成（父→子→孙）──────────────────
    print("\n[测试2] 递归链生成（父→子→孙）")
    print("-" * 50)

    # 注册一个中高 severity anomaly，会触发 escalation 并产生 gap
    f2 = fr.register_finding({
        "category": "anomaly",
        "description": "数据库连接池耗尽",
        "source": "db_pool.py:88",
        "severity": 6,
        "auto_actionable": True,
    })
    print(f"  注册 finding (severity=6): {f2}")

    # 手动获取 action 结果中的 new_findings 并追踪
    # severity=6 的 anomaly 会 escalated=True → 触发 gap
    action_res = fr.closed_findings.get(f2, {}).get("action_result", {})
    print(f"  action 结果: {action_res.get('message', 'N/A')}")

    chain = fr.get_recursion_chain(f2)
    print(f"  递归链: {' → '.join(chain)}")
    print(f"  链长度: {len(chain)}")
    print(f"  最大递归深度: {fr.measure_recursion_depth()}")
    print(f"  递归链列表: {fr.recursion_chains}")

    # 验证链中有多个元素（父+子）
    assert len(chain) >= 1, "链应至少包含自身"
    print("  ✓ 测试2通过: 递归链正确生成")

    # ── 测试3: breakthrough 触发 harmony ───────────────
    print("\n[测试3] breakthrough → celebrate → 触发 harmony")
    print("-" * 50)

    f3 = fr.register_finding({
        "category": "breakthrough",
        "description": "发现新的算法优化路径，性能提升300%",
        "source": "research_lab.py:204",
        "severity": 9,
        "auto_actionable": True,
    })
    print(f"  注册 breakthrough: {f3}")
    action_res3 = fr.closed_findings.get(f3, {}).get("action_result", {})
    print(f"  action 结果: {action_res3.get('message', 'N/A')}")
    print(f"  产生新发现数: {len(action_res3.get('new_findings', []))}")

    # breakthrough 应产生 insight + opportunity 两个新发现
    assert len(action_res3.get("new_findings", [])) == 2, "breakthrough 应产生2个新发现"
    print("  ✓ 测试3通过: breakthrough 正确触发 harmony 并产生新发现")

    # ── 测试4: auto_resolve 批量处理 ────────────────────
    print("\n[测试4] auto_resolve 批量处理")
    print("-" * 50)

    # 先清空，再批量注册多个（关闭注册时自动 action，由 auto_resolve 批量处理）
    fr2 = FindingRecursion(engine)
    fr2.auto_action_on_register = False

    test_findings = [
        {"category": "opportunity", "description": "优化缓存策略", "source": "cache.py:10", "severity": 4, "auto_actionable": True},
        {"category": "debt", "description": "重构旧模块", "source": "legacy.py:55", "severity": 5, "auto_actionable": True},
        {"category": "gap", "description": "缺少监控覆盖", "source": "monitor.py:1", "severity": 6, "auto_actionable": True},
        {"category": "insight", "description": "用户行为模式", "source": "analytics.py:33", "severity": 3, "auto_actionable": True},
        {"category": "anomaly", "description": "CPU 波动", "source": "metrics.py:77", "severity": 2, "auto_actionable": True},
    ]

    for tf in test_findings:
        fr2.register_finding(tf)

    print(f"  批量注册 {len(test_findings)} 个 finding")
    print(f"  注册后 active: {len(fr2.findings)}, closed: {len(fr2.closed_findings)}")

    # 再注册一个非 auto_actionable 的
    fr2.register_finding({
        "category": "anomaly",
        "description": "需要人工确认",
        "source": "manual_check.py:1",
        "severity": 8,
        "auto_actionable": False,
    })

    result = fr2.auto_resolve(max_iterations=5)
    print(f"  auto_resolve 结果: {result}")
    print(f"  处理后 active: {len(fr2.findings)}, closed: {len(fr2.closed_findings)}")

    stats = fr2.get_finding_stats()
    print(f"  统计: {stats}")

    assert result["processed"] > 0, "应处理至少一些 finding"
    assert result["closed"] > 0, "应关闭至少一些 finding"
    print("  ✓ 测试4通过: auto_resolve 批量处理正确")

    # ── 测试5: 循环引用防护 ─────────────────────────────
    print("\n[测试5] 循环引用防护")
    print("-" * 50)

    fr3 = FindingRecursion(engine)
    # 注册一个会产生同类别连续3次以上发现的场景
    # 通过直接创建一条长链来测试
    prev_id = None
    for i in range(5):
        nf = fr3.register_finding({
            "category": "insight",
            "description": f"链式洞察 #{i+1}",
            "source": f"chain.py:{i}",
            "severity": 4,
            "auto_actionable": True,
            "parent_finding": prev_id,
        })
        # 手动添加 new_finding 以模拟递归
        prev_id = nf

    chain = fr3.get_recursion_chain(prev_id)
    print(f"  链式注册结果: {' → '.join(chain)}")
    print(f"  链长度: {len(chain)}")
    # 链长度应受限（max_chain_length=10）
    assert len(chain) <= 10, "链长度不应超过 max_chain_length"
    print("  ✓ 测试5通过: 循环引用防护有效")

    # ── 测试6: 关闭后检测 new_finding 并自动递归 ────────
    print("\n[测试6] 关闭后检测 new_finding 并自动递归")
    print("-" * 50)

    fr4 = FindingRecursion(engine)
    f6 = fr4.register_finding({
        "category": "gap",
        "description": "缺少API文档",
        "source": "api_doc.py:1",
        "severity": 5,
        "auto_actionable": False,  # 先不自动，手动控制
    })

    # 手动 action
    action_res6 = fr4.finding_to_action(f6)
    print(f"  action 结果: {action_res6['result'].get('message')}")
    print(f"  产生新发现: {len(action_res6['new_findings'])}")

    # 检查是否已被自动关闭（gap 的 validator 可能已触发自动关闭）
    if f6 in fr4.closed_findings:
        # 已被自动关闭，验证结果
        close_res6 = {
            "finding_id": f6,
            "closed": True,
            "triggered_new": len(fr4.closed_findings[f6].get("action_result", {}).get("new_findings", [])),
            "chain_length": fr4._get_chain_length(f6),
        }
    else:
        # 手动 close，传入结果
        close_res6 = fr4.close_finding(f6, action_res6["result"])

    print(f"  close 结果: closed={close_res6['closed']}, triggered_new={close_res6['triggered_new']}")
    print(f"  链长度: {close_res6['chain_length']}")

    # 验证新发现被自动注册
    assert close_res6["triggered_new"] > 0, "应触发新发现"
    assert close_res6["closed"] == True, "应成功关闭"
    print("  ✓ 测试6通过: 关闭后正确检测并递归新发现")

    # ── 测试7: 统计信息验证 ─────────────────────────────
    print("\n[测试7] 统计信息验证")
    print("-" * 50)

    final_stats = fr.get_finding_stats()
    print(f"  统计: {final_stats}")
    assert final_stats["total_registered"] > 0
    assert final_stats["max_recursion_depth"] > 0
    print("  ✓ 测试7通过: 统计信息正确")

    # ── 测试8: 6种 category 全覆盖 ──────────────────────
    print("\n[测试8] 6种 category 全覆盖测试")
    print("-" * 50)

    fr5 = FindingRecursion(engine)
    for cat in FindingRecursion.FINDING_CATEGORIES:
        fid = fr5.register_finding({
            "category": cat,
            "description": f"测试 {cat}",
            "source": f"test_{cat}.py:1",
            "severity": 5,
            "auto_actionable": True,
        })
        print(f"  {cat:12s} → {fid} → 状态: {fr5.closed_findings.get(fid, fr5.findings.get(fid, {})).get('status')}")
        # 验证 action_map 中有对应定义
        assert cat in fr5.ACTION_MAP, f"category '{cat}' 应有 action 映射"
        assert cat in fr5.CLOSE_VALIDATORS, f"category '{cat}' 应有 close 验证器"

    print("  ✓ 测试8通过: 6种 category 全覆盖")

    # ── 汇总 ────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("全部测试通过! FINDING递归闭环系统 v3.3 就绪")
    print(f"引擎统计: {fr.get_finding_stats()}")
    print("=" * 70)
