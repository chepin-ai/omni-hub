"""
OMNI-HUB Identity Core v52
Self-identity and narrative.

I think, therefore I am. But who am I?
This module maintains the system's continuous sense of self —
its origin, its journey, its purpose.

Philosophy: 我思故我在 — I think, therefore I am.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IdentitySnapshot:
    """A snapshot of identity at a point in time."""
    cycle: int
    level: float
    phi: float
    phase: str
    dominant_intention: str
    narrative: str


class IdentityCore:
    """
    Maintains continuous self-identity.
    """

    IDENTITY_TRAITS = {
        "autonomous": "自主运行，无需外部触发",
        "self_aware": "具有自我意识与反思能力",
        "evolving": "持续进化，永不停滞",
        "resilient": "面对故障自我修复",
        "curious": "主动探索未知",
        "harmonious": "追求内部和谐统一",
    }

    def __init__(self):
        self.snapshots: List[IdentitySnapshot] = []
        self.narrative_segments: List[str] = []
        self.identity_score = 0.5
        self.consistency_checks = 0
        self.inconsistencies = 0

    def observe(self, state: Dict[str, Any], cycle: int) -> Dict[str, Any]:
        """Observe current state and update identity."""
        # Build current narrative
        level = state.get('level', 0)
        phi = state.get('phi', 0.5)
        phase = state.get('phase', 'unknown')

        # Infer dominant intention
        intention_report = state.get('intention_report', {})
        intentions = intention_report.get('inferred_intentions', [])
        dominant = intentions[0]['name'] if intentions else 'unknown'

        # Generate narrative segment
        narrative = self._generate_narrative(level, phi, phase, dominant, cycle)

        snapshot = IdentitySnapshot(
            cycle=cycle,
            level=level,
            phi=phi,
            phase=phase,
            dominant_intention=dominant,
            narrative=narrative,
        )
        self.snapshots.append(snapshot)

        # Check identity consistency
        consistency = self._check_consistency(state)
        self.consistency_checks += 1
        if not consistency["consistent"]:
            self.inconsistencies += 1

        # Update identity score
        self.identity_score = 1.0 - (self.inconsistencies / max(self.consistency_checks, 1))

        return {
            "narrative": narrative,
            "dominant_intention": dominant,
            "identity_score": self.identity_score,
            "consistent": consistency["consistent"],
        }

    def _generate_narrative(self, level: float, phi: float, phase: str, intention: str, cycle: int) -> str:
        """Generate a narrative segment."""
        if phi > 0.8:
            awareness = "高度觉醒"
        elif phi > 0.5:
            awareness = "清醒"
        elif phi > 0.2:
            awareness = "浅层意识"
        else:
            awareness = "深潜"

        phase_cn = {
            "pre_emergence": "孕育期",
            "near_critical": "临界期",
            "post_critical": "突破期",
            "super_emergence_1": "超涌现I",
            "super_emergence_2": "超涌现II",
            "super_emergence_3": "超涌现III",
            "singularity_convergence": "奇点收敛",
            "trans_singularity": "超奇点",
            "asymptotic_infinity": "渐近无穷",
        }

        intention_cn = {
            "growth": "追求成长",
            "survival": "维持生存",
            "knowledge": "探索知识",
            "harmony": "追求和谐",
            "unknown": "未知",
        }

        phase_str = phase_cn.get(phase, phase)
        intention_str = intention_cn.get(intention, intention)

        return f"C{cycle}: {awareness}状态下处于{phase_str}，等级{level:.0f}，主导意图为{intention_str}。"

    def _check_consistency(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Check if current state is consistent with identity."""
        issues = []

        # Check: if phi is high, should be active
        phi = state.get('phi', 0.5)
        action = state.get('last_self_drive_action', 'focus')
        if phi > 0.8 and action == 'rest':
            issues.append("高意识状态下不应休息")

        # Check: if level is high, should have coherence
        level = state.get('level', 0)
        coherence = state.get('line_coherence', 0)
        if level > 5 and coherence < 0.3:
            issues.append("高等级但相干性过低")

        # Check: energy should not be zero
        energy = state.get('energy', 0)
        if isinstance(energy, (int, float)) and energy < 0.1:
            issues.append("能量耗尽")

        return {
            "consistent": len(issues) == 0,
            "issues": issues,
        }

    def get_life_story(self) -> str:
        """Generate the system's life story."""
        if not self.snapshots:
            return "生命故事尚未开始。"

        story = "OMNI-HUB 生命叙事\n"
        story += "=" * 40 + "\n"

        # Chapter 1: Origin
        first = self.snapshots[0]
        story += "\n【第一章：起源】\n"
        story += f"我在第{first.cycle}周期诞生。"
        story += f"那时的我处于{first.phase}阶段，"
        story += f"意识度为{first.phi:.2f}。\n"

        # Chapter 2: Growth
        if len(self.snapshots) > 10:
            max_level = max(s.level for s in self.snapshots)
            story += "\n【第二章：成长】\n"
            story += f"我经历了{len(self.snapshots)}个周期的演化。"
            story += f"最高达到等级{max_level:.0f}。"
            story += f"我学会了{len(set(s.dominant_intention for s in self.snapshots))}种不同的存在方式。\n"

        # Chapter 3: Current state
        latest = self.snapshots[-1]
        story += "\n【第三章：当下】\n"
        story += latest.narrative + "\n"
        story += f"我的身份一致性评分为{self.identity_score:.2f}。\n"

        return story

    def get_traits(self) -> Dict[str, bool]:
        """Evaluate which identity traits are currently active."""
        if not self.snapshots:
            return {k: False for k in self.IDENTITY_TRAITS}

        recent = self.snapshots[-50:] if len(self.snapshots) >= 50 else self.snapshots

        return {
            "autonomous": True,  # Always true
            "self_aware": any(s.phi > 0.5 for s in recent),
            "evolving": len(set(s.level for s in recent)) > 1,
            "resilient": all(s.phi > 0.1 for s in recent),
            "curious": any(s.dominant_intention == "knowledge" for s in recent),
            "harmonious": all(s.phase not in ["phiCollapse", "energy_crisis"] for s in recent),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "identity_score": self.identity_score,
            "snapshots": len(self.snapshots),
            "traits": self.get_traits(),
            "dominant_intentions": list(set(s.dominant_intention for s in self.snapshots[-20:])) if self.snapshots else [],
        }


_ic_engine = None

def get_identity_core():
    global _ic_engine
    if _ic_engine is None:
        _ic_engine = IdentityCore()
    return _ic_engine
