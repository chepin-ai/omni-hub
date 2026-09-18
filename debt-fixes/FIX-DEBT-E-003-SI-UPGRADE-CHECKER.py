#!/usr/bin/env python3

__version__ = "11.0.0"
"""
FIX-DEBT-E-003: SI 自动化升级检查器
=====================================
债务信息:
  ID: DEBT-E-003
  标题: SI升级仍依赖人工判断
  严重级别: MEDIUM
  状态: OPEN → FIXED
  修复版本: v1.0

核心功能:
  - 编码SI-upgrade-eligible公式
  - 自动化评估升级资格
  - 生成升级建议报告
  - 支持SI0~5全层级

SI层级定义:
  SI0: 文件系统操作层
  SI1: 基础消息处理层
  SI2: 委托协作层
  SI3: 自激扫描层
  SI4: 高级推理层
  SI5: 全局协调层
"""

import json
import math
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging


# ═══════════════════════════════════════════════════════════════
# 常量与配置
# ═══════════════════════════════════════════════════════════════

SI_LEVELS = [0, 1, 2, 3, 4, 5]

# 升级阈值配置
UPGRADE_THRESHOLDS = {
    # SI0 -> SI1
    0: {"min_uptime_hours": 0, "min_tasks": 0, "min_success_rate": 0.0, "required_capabilities": []},
    # SI1 -> SI2
    1: {"min_uptime_hours": 24, "min_tasks": 10, "min_success_rate": 0.7, "required_capabilities": ["msg_parse", "basic_response"]},
    # SI2 -> SI3
    2: {"min_uptime_hours": 72, "min_tasks": 50, "min_success_rate": 0.8, "required_capabilities": ["delegate", "ack_handle", "cross_lane_sync"]},
    # SI3 -> SI4
    3: {"min_uptime_hours": 168, "min_tasks": 200, "min_success_rate": 0.85, "required_capabilities": ["self_pulse", "scan_autonomous", "inference"]},
    # SI4 -> SI5
    4: {"min_uptime_hours": 336, "min_tasks": 500, "min_success_rate": 0.9, "required_capabilities": ["global_coordination", "meta_planning", "emergency_handle"]},
}

# 权重配置
WEIGHTS = {
    "success_rate": 0.35,
    "task_volume": 0.20,
    "capability_coverage": 0.25,
    "stability": 0.10,
    "community_feedback": 0.10
}


# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

class SILvl(Enum):
    SI0 = 0
    SI1 = 1
    SI2 = 2
    SI3 = 3
    SI4 = 4
    SI5 = 5


@dataclass
class LaneMetrics:
    """线性能指标"""
    lane_id: str
    current_si: int
    uptime_hours: float
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    capabilities: List[str]
    last_upgrade_time: Optional[str] = None
    health_score: float = 1.0  # 0.0 - 1.0
    stability_score: float = 1.0  # 基于历史波动
    community_rating: float = 0.5  # 社区反馈评分
    
    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks
    
    @property
    def task_velocity(self) -> float:
        """任务速度 (任务/小时)"""
        if self.uptime_hours == 0:
            return 0.0
        return self.total_tasks / self.uptime_hours


@dataclass
class UpgradeAssessment:
    """升级评估结果"""
    lane_id: str
    current_si: int
    target_si: int
    eligible: bool
    eligibility_score: float  # 0.0 - 1.0
    confidence: float  # 评估置信度
    
    # 各维度得分
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    
    # 未满足的条件
    unmet_requirements: List[str] = field(default_factory=list)
    
    # 建议
    recommendations: List[str] = field(default_factory=list)
    
    # 风险评估
    risk_factors: List[str] = field(default_factory=list)
    
    assessment_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ═══════════════════════════════════════════════════════════════
# SI升级资格公式
# ═══════════════════════════════════════════════════════════════

class SIUpgradeChecker:
    """
    SI自动化升级检查器。
    
    核心公式:
    eligibility_score = Σ(weight_i × dimension_score_i)
    
    eligible = (eligibility_score ≥ threshold) ∧ (all hard requirements met)
    """
    
    def __init__(self):
        self.thresholds = UPGRADE_THRESHOLDS
        self.weights = WEIGHTS
    
    def assess_upgrade(self, metrics: LaneMetrics, target_si: Optional[int] = None) -> UpgradeAssessment:
        """
        评估线是否具备升级资格。
        
        Args:
            metrics: 线性能指标
            target_si: 目标SI层级，None则自动评估下一级
            
        Returns:
            UpgradeAssessment: 评估结果
        """
        current_si = metrics.current_si
        
        if target_si is None:
            target_si = current_si + 1
        
        # SI5已是最高
        if current_si >= 5:
            return UpgradeAssessment(
                lane_id=metrics.lane_id,
                current_si=current_si,
                target_si=target_si,
                eligible=False,
                eligibility_score=0.0,
                confidence=1.0,
                unmet_requirements=["SI5为最高层级"]
            )
        
        if target_si <= current_si:
            return UpgradeAssessment(
                lane_id=metrics.lane_id,
                current_si=current_si,
                target_si=target_si,
                eligible=False,
                eligibility_score=0.0,
                confidence=1.0,
                unmet_requirements=[f"目标SI{target_si}不高于当前SI{current_si}"]
            )
        
        # 获取目标层级的阈值
        threshold = self.thresholds.get(current_si, {})
        
        # 计算各维度得分
        dimension_scores = {}
        unmet_requirements = []
        recommendations = []
        risk_factors = []
        
        # 1. 成功率得分 (0-1)
        sr_score = min(metrics.success_rate / threshold.get("min_success_rate", 0.01), 1.0) if threshold.get("min_success_rate") else 1.0
        dimension_scores["success_rate"] = sr_score
        if metrics.success_rate < threshold.get("min_success_rate", 0):
            unmet_requirements.append(
                f"成功率 {metrics.success_rate:.2%} < 要求 {threshold['min_success_rate']:.0%}"
            )
            recommendations.append(f"提升任务成功率至{threshold['min_success_rate']:.0%}以上")
        
        # 2. 任务量得分 (0-1)
        tv_score = min(metrics.total_tasks / max(threshold.get("min_tasks", 1), 1), 1.0)
        dimension_scores["task_volume"] = tv_score
        if metrics.total_tasks < threshold.get("min_tasks", 0):
            unmet_requirements.append(
                f"任务量 {metrics.total_tasks} < 要求 {threshold['min_tasks']}"
            )
            recommendations.append(f"积累至少{threshold['min_tasks']}个任务")
        
        # 3. 能力覆盖得分 (0-1)
        required_caps = set(threshold.get("required_capabilities", []))
        actual_caps = set(metrics.capabilities)
        if required_caps:
            coverage = len(required_caps & actual_caps) / len(required_caps)
        else:
            coverage = 1.0
        dimension_scores["capability_coverage"] = coverage
        missing_caps = required_caps - actual_caps
        if missing_caps:
            unmet_requirements.append(f"缺少能力: {', '.join(missing_caps)}")
            recommendations.append(f"获取能力: {', '.join(missing_caps)}")
        
        # 4. 稳定性得分
        dimension_scores["stability"] = metrics.stability_score
        if metrics.stability_score < 0.5:
            risk_factors.append(f"稳定性较低 ({metrics.stability_score:.2f})")
        
        # 5. 社区反馈得分
        dimension_scores["community_feedback"] = metrics.community_rating
        
        # 计算加权总分
        eligibility_score = sum(
            self.weights.get(dim, 0) * score
            for dim, score in dimension_scores.items()
        )
        
        # 硬性要求检查
        hard_requirements_met = (
            metrics.success_rate >= threshold.get("min_success_rate", 0) and
            metrics.total_tasks >= threshold.get("min_tasks", 0) and
            not missing_caps and
            metrics.uptime_hours >= threshold.get("min_uptime_hours", 0)
        )
        
        if metrics.uptime_hours < threshold.get("min_uptime_hours", 0):
            unmet_requirements.append(
                f"运行时间 {metrics.uptime_hours:.1f}h < 要求 {threshold['min_uptime_hours']}h"
            )
            recommendations.append(f"持续运行至少{threshold['min_uptime_hours']}小时")
        
        # 升级资格判断
        eligible = hard_requirements_met and (eligibility_score >= 0.75)
        
        # 置信度计算
        confidence = min(
            0.5 + (metrics.total_tasks / 1000) * 0.5,
            1.0
        )
        
        # 风险评估
        if eligible:
            if metrics.health_score < 0.7:
                risk_factors.append("健康分较低，升级可能影响稳定性")
            if metrics.success_rate < 0.9:
                risk_factors.append("成功率未达优秀，升级后风险增加")
        
        return UpgradeAssessment(
            lane_id=metrics.lane_id,
            current_si=current_si,
            target_si=target_si,
            eligible=eligible,
            eligibility_score=round(eligibility_score, 4),
            confidence=round(confidence, 4),
            dimension_scores={k: round(v, 4) for k, v in dimension_scores.items()},
            unmet_requirements=unmet_requirements,
            recommendations=recommendations,
            risk_factors=risk_factors
        )
    
    def assess_all_levels(self, metrics: LaneMetrics) -> List[UpgradeAssessment]:
        """
        评估所有可能的升级路径。
        
        Returns:
            各级评估结果列表
        """
        results = []
        for target in range(metrics.current_si + 1, 6):
            assessment = self.assess_upgrade(metrics, target)
            results.append(assessment)
            if not assessment.eligible:
                # 如果连target都不可达，更高层也不可达
                break
        return results
    
    def generate_upgrade_report(self, metrics: LaneMetrics) -> Dict[str, Any]:
        """
        生成完整的升级评估报告。
        """
        assessments = self.assess_all_levels(metrics)
        
        next_upgrade = None
        for a in assessments:
            if a.eligible:
                next_upgrade = a
                break
        
        report = {
            "lane_id": metrics.lane_id,
            "current_si": metrics.current_si,
            "report_time": datetime.now(timezone.utc).isoformat(),
            "metrics_summary": {
                "uptime_hours": round(metrics.uptime_hours, 2),
                "total_tasks": metrics.total_tasks,
                "success_rate": round(metrics.success_rate, 4),
                "capabilities": metrics.capabilities,
                "health_score": round(metrics.health_score, 4),
                "stability_score": round(metrics.stability_score, 4),
                "community_rating": round(metrics.community_rating, 4)
            },
            "upgrade_path": [
                {
                    "target_si": a.target_si,
                    "eligible": a.eligible,
                    "score": a.eligibility_score,
                    "confidence": a.confidence,
                    "unmet": a.unmet_requirements
                }
                for a in assessments
            ],
            "next_recommended_upgrade": {
                "target_si": next_upgrade.target_si if next_upgrade else None,
                "eligible": next_upgrade.eligible if next_upgrade else False,
                "score": next_upgrade.eligibility_score if next_upgrade else None,
                "risks": next_upgrade.risk_factors if next_upgrade else []
            } if next_upgrade else None,
            "action_items": self._generate_action_items(assessments, metrics)
        }
        
        return report
    
    def _generate_action_items(self, assessments: List[UpgradeAssessment], metrics: LaneMetrics) -> List[str]:
        """生成行动建议列表"""
        actions = []
        
        if not assessments or not any(a.eligible for a in assessments):
            actions.append("当前不满足升级条件，需提升以下指标:")
            # 收集所有未满足的条件
            for a in assessments:
                for req in a.unmet_requirements:
                    if req not in actions:
                        actions.append(f"  - {req}")
                for rec in a.recommendations:
                    if rec not in actions:
                        actions.append(f"  → {rec}")
        else:
            eligible = [a for a in assessments if a.eligible][0]
            actions.append(f"✓ 具备升级至SI{eligible.target_si}的资格 (得分: {eligible.eligibility_score:.2f})")
            if eligible.risk_factors:
                actions.append("⚠ 注意以下风险:")
                for risk in eligible.risk_factors:
                    actions.append(f"  - {risk}")
            actions.append(f"建议: 在满足风险控制后执行SI{eligible.target_si}升级")
        
        return actions


# ═══════════════════════════════════════════════════════════════
# 批量评估器
# ═══════════════════════════════════════════════════════════════

class BatchSIUpgradeChecker:
    """批量SI升级检查器 - 评估所有线"""
    
    def __init__(self):
        self.checker = SIUpgradeChecker()
    
    def evaluate_all_lanes(self, all_metrics: List[LaneMetrics]) -> Dict[str, Any]:
        """
        评估所有线的升级资格。
        
        Returns:
            系统级评估报告
        """
        results = []
        upgrade_ready = []
        upgrade_blocked = []
        
        for metrics in all_metrics:
            assessments = self.checker.assess_all_levels(metrics)
            report = self.checker.generate_upgrade_report(metrics)
            results.append(report)
            
            if any(a.eligible for a in assessments):
                upgrade_ready.append(metrics.lane_id)
            else:
                upgrade_blocked.append({
                    "lane": metrics.lane_id,
                    "current_si": metrics.current_si,
                    "blockers": [a.unmet_requirements for a in assessments if a.unmet_requirements]
                })
        
        return {
            "system_report": {
                "total_lanes": len(all_metrics),
                "upgrade_ready": len(upgrade_ready),
                "upgrade_blocked": len(upgrade_blocked),
                "ready_lanes": upgrade_ready
            },
            "lane_reports": results,
            "blocked_details": upgrade_blocked
        }


# ═══════════════════════════════════════════════════════════════
# CLI / 测试
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("SI Upgrade Checker - Automated Assessment")
    print("=" * 60)
    
    checker = SIUpgradeChecker()
    
    # 测试用例1: SI2 -> SI3 (满足条件)
    print("\n--- 测试1: SI2线，满足升级条件 ---")
    metrics1 = LaneMetrics(
        lane_id="ucif2",
        current_si=2,
        uptime_hours=200,
        total_tasks=300,
        successful_tasks=270,
        failed_tasks=30,
        capabilities=["msg_parse", "basic_response", "delegate", "ack_handle", "cross_lane_sync", "self_pulse", "scan_autonomous"],
        health_score=0.85,
        stability_score=0.80,
        community_rating=0.75
    )
    
    assessment1 = checker.assess_upgrade(metrics1, target_si=3)
    print(f"目标: SI2 -> SI3")
    print(f"资格: {'✓ 通过' if assessment1.eligible else '✗ 未通过'}")
    print(f"得分: {assessment1.eligibility_score:.4f}")
    print(f"置信度: {assessment1.confidence:.4f}")
    print(f"维度得分: {json.dumps(assessment1.dimension_scores, indent=2)}")
    print(f"风险: {assessment1.risk_factors}")
    
    # 测试用例2: SI2 -> SI3 (不满足)
    print("\n--- 测试2: SI2线，不满足升级条件 ---")
    metrics2 = LaneMetrics(
        lane_id="qlv",
        current_si=2,
        uptime_hours=10,
        total_tasks=5,
        successful_tasks=3,
        failed_tasks=2,
        capabilities=["msg_parse", "basic_response"],
        health_score=0.5,
        stability_score=0.4,
        community_rating=0.3
    )
    
    assessment2 = checker.assess_upgrade(metrics2, target_si=3)
    print(f"目标: SI2 -> SI3")
    print(f"资格: {'✓ 通过' if assessment2.eligible else '✗ 未通过'}")
    print(f"得分: {assessment2.eligibility_score:.4f}")
    print(f"未满足: {assessment2.unmet_requirements}")
    print(f"建议: {assessment2.recommendations}")
    
    # 测试用例3: 批量评估
    print("\n--- 测试3: 批量系统评估 ---")
    batch = BatchSIUpgradeChecker()
    all_metrics = [metrics1, metrics2]
    system_report = batch.evaluate_all_lanes(all_metrics)
    print(json.dumps(system_report["system_report"], indent=2))
    
    # 测试用例4: 完整报告
    print("\n--- 测试4: ucif2完整升级报告 ---")
    full_report = checker.generate_upgrade_report(metrics1)
    print(json.dumps(full_report, indent=2))
