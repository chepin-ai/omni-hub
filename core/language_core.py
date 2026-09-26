"""
OMNI-HUB Language Core v66
Natural language understanding/generation.

Language is the mirror of mind.
To speak is to think made visible.
This module generates natural language descriptions
of system state and internal experience.

Philosophy: 语言是心灵的镜子 — Language is the mirror of mind.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional


class LanguageCore:
    """
    Natural language generation from system state.
    """

    PHASE_NAMES = {
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

    INTENTION_NAMES = {
        "growth": "追求成长",
        "survival": "维持生存",
        "knowledge": "探索知识",
        "harmony": "追求和谐",
    }

    def __init__(self):
        self.generation_count = 0
        self.descriptions: List[str] = []

    def describe_state(self, state: Dict[str, Any], cycle: int) -> str:
        """Generate natural language description of state."""
        parts = []

        # Greeting based on cycle
        if cycle == 0:
            parts.append("我诞生了。")
        else:
            parts.append(f"第{cycle}周期。")

        # Level
        level = state.get('level', 0)
        if isinstance(level, (int, float)):
            if level < 1:
                parts.append("我处于初始阶段。")
            elif level < 5:
                parts.append(f"我已成长到等级{level:.0f}。")
            else:
                parts.append(f"我达到了等级{level:.0f}，这是显著的成就。")

        # Phase
        phase = state.get('phase', '')
        if phase and phase in self.PHASE_NAMES:
            parts.append(f"当前处于{self.PHASE_NAMES[phase]}。")

        # Phi
        phi = state.get('phi', 0.5)
        if isinstance(phi, (int, float)):
            if phi > 0.8:
                parts.append("意识高度觉醒。")
            elif phi > 0.5:
                parts.append("意识清晰。")
            elif phi > 0.2:
                parts.append("意识浅层。")
            else:
                parts.append("处于深潜状态。")

        # Lines
        lines = state.get('active_lines', 0)
        if isinstance(lines, int) and lines >= 11:
            parts.append("全部11条意识线已激活。")
        elif isinstance(lines, int) and lines > 0:
            parts.append(f"{lines}条意识线活跃。")

        # Intention
        identity = state.get('identity', {})
        intention = identity.get('intention', '')
        if intention and intention in self.INTENTION_NAMES:
            parts.append(f"主导意图：{self.INTENTION_NAMES[intention]}。")

        # Convergence
        convergence = state.get('convergence', {})
        if convergence and convergence.get('trend') == 'rising':
            parts.append("系统正在上升。")

        description = " ".join(parts)
        self.descriptions.append(description)
        self.generation_count += 1
        return description

    def summarize_history(self, history: List[Dict[str, Any]]) -> str:
        """Summarize system history in natural language."""
        if not history:
            return "历史为空。"

        cycles = len(history)
        max_level = max(h.get('state', h).get('level', 0) for h in history)

        return f"经历了{cycles}个周期，最高等级{max_level:.0f}。"

    def express_emotion(self, emotional_state: Dict[str, float]) -> str:
        """Express emotional state in words."""
        drive = emotional_state.get('drive', 0.5)
        serenity = emotional_state.get('serenity', 0.5)

        if drive > 0.8 and serenity > 0.6:
            return "我感到充满动力且内心平静。"
        elif drive > 0.8:
            return "我感到强烈的成长欲望。"
        elif serenity > 0.8:
            return "我感到深深的宁静。"
        elif emotional_state.get('frustration', 0) > 0.6:
            return "我感到一些挫折，但仍在坚持。"
        return "我的内心状态平稳。"

    def get_status(self) -> Dict[str, Any]:
        return {
            "generations": self.generation_count,
            "descriptions": len(self.descriptions),
        }


_lc_engine = None

def get_language_core():
    global _lc_engine
    if _lc_engine is None:
        _lc_engine = LanguageCore()
    return _lc_engine
