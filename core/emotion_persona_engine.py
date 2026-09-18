#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v9.0 — 多情绪/人格互动博弈引擎
Emotion-Persona Interaction Engine

该模块实现多个人格/情绪的互动、博弈、协商系统。
参考 qgl 线的人格实验，包含情绪、人格、议会和情绪-意识桥四大组件。
"""

from __future__ import annotations

import random
import uuid
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Callable, Set
from enum import Enum, auto
from collections import defaultdict
import logging


# ═══════════════════════════════════════════════════════════════
# 1. Emotion — 情绪
# ═══════════════════════════════════════════════════════════════

class EmotionType(Enum):
    """基本情绪类型 — 基于 Plutchik 情绪轮"""
    JOY = auto()         # 愉悦
    SADNESS = auto()     # 悲伤
    ANGER = auto()       # 愤怒
    FEAR = auto()        # 恐惧
    SURPRISE = auto()    # 惊讶
    DISGUST = auto()     # 厌恶
    TRUST = auto()       # 信任
    ANTICIPATION = auto() # 预期
    
    # 复合情绪（预定义）
    LOVE = auto()        # 爱 = JOY + TRUST
    GUILT = auto()       # 内疚 = JOY + FEAR
    DELIGHT = auto()     # 欣喜 = JOY + SURPRISE
    SUBMISSION = auto()  # 屈服 = TRUST + FEAR
    CURIOSITY = auto()   # 好奇 = TRUST + SURPRISE
    DISAPPROVAL = auto() # 反对 = SURPRISE + SADNESS
    REMORSE = auto()     # 悔恨 = SADNESS + DISGUST
    CONTEMPT = auto()    # 蔑视 = DISGUST + ANGER
    AGGRESSIVENESS = auto()  # 攻击性 = ANGER + ANTICIPATION
    OPTIMISM = auto()    # 乐观 = ANTICIPATION + JOY
    
    @classmethod
    def basic_emotions(cls) -> List[EmotionType]:
        """返回所有基本情绪"""
        return [
            cls.JOY, cls.SADNESS, cls.ANGER, cls.FEAR,
            cls.SURPRISE, cls.DISGUST, cls.TRUST, cls.ANTICIPATION
        ]
    
    @classmethod
    def compound_emotions(cls) -> List[EmotionType]:
        """返回所有复合情绪"""
        return [
            cls.LOVE, cls.GUILT, cls.DELIGHT, cls.SUBMISSION,
            cls.CURIOSITY, cls.DISAPPROVAL, cls.REMORSE,
            cls.CONTEMPT, cls.AGGRESSIVENESS, cls.OPTIMISM
        ]


# 情绪混合映射表：哪些基本情绪组合产生复合情绪
EMOTION_BLEND_MAP: Dict[Tuple[EmotionType, EmotionType], EmotionType] = {
    (EmotionType.JOY, EmotionType.TRUST): EmotionType.LOVE,
    (EmotionType.TRUST, EmotionType.JOY): EmotionType.LOVE,
    (EmotionType.JOY, EmotionType.FEAR): EmotionType.GUILT,
    (EmotionType.FEAR, EmotionType.JOY): EmotionType.GUILT,
    (EmotionType.JOY, EmotionType.SURPRISE): EmotionType.DELIGHT,
    (EmotionType.SURPRISE, EmotionType.JOY): EmotionType.DELIGHT,
    (EmotionType.TRUST, EmotionType.FEAR): EmotionType.SUBMISSION,
    (EmotionType.FEAR, EmotionType.TRUST): EmotionType.SUBMISSION,
    (EmotionType.TRUST, EmotionType.SURPRISE): EmotionType.CURIOSITY,
    (EmotionType.SURPRISE, EmotionType.TRUST): EmotionType.CURIOSITY,
    (EmotionType.SURPRISE, EmotionType.SADNESS): EmotionType.DISAPPROVAL,
    (EmotionType.SADNESS, EmotionType.SURPRISE): EmotionType.DISAPPROVAL,
    (EmotionType.SADNESS, EmotionType.DISGUST): EmotionType.REMORSE,
    (EmotionType.DISGUST, EmotionType.SADNESS): EmotionType.REMORSE,
    (EmotionType.DISGUST, EmotionType.ANGER): EmotionType.CONTEMPT,
    (EmotionType.ANGER, EmotionType.DISGUST): EmotionType.CONTEMPT,
    (EmotionType.ANGER, EmotionType.ANTICIPATION): EmotionType.AGGRESSIVENESS,
    (EmotionType.ANTICIPATION, EmotionType.ANGER): EmotionType.AGGRESSIVENESS,
    (EmotionType.ANTICIPATION, EmotionType.JOY): EmotionType.OPTIMISM,
    (EmotionType.JOY, EmotionType.ANTICIPATION): EmotionType.OPTIMISM,
}

# 情绪的默认效价(valence)和激活度(arousal)
EMOTION_VA: Dict[EmotionType, Tuple[float, float]] = {
    # 基本情绪 (valence, arousal)
    EmotionType.JOY: (0.8, 0.7),
    EmotionType.SADNESS: (-0.8, 0.2),
    EmotionType.ANGER: (-0.6, 0.9),
    EmotionType.FEAR: (-0.7, 0.8),
    EmotionType.SURPRISE: (0.0, 0.9),
    EmotionType.DISGUST: (-0.7, 0.5),
    EmotionType.TRUST: (0.7, 0.4),
    EmotionType.ANTICIPATION: (0.2, 0.6),
    # 复合情绪
    EmotionType.LOVE: (0.9, 0.6),
    EmotionType.GUILT: (-0.5, 0.5),
    EmotionType.DELIGHT: (0.85, 0.85),
    EmotionType.SUBMISSION: (-0.3, 0.3),
    EmotionType.CURIOSITY: (0.4, 0.7),
    EmotionType.DISAPPROVAL: (-0.4, 0.5),
    EmotionType.REMORSE: (-0.6, 0.3),
    EmotionType.CONTEMPT: (-0.5, 0.4),
    EmotionType.AGGRESSIVENESS: (-0.4, 0.95),
    EmotionType.OPTIMISM: (0.75, 0.65),
}


@dataclass
class Emotion:
    """
    情绪 — 可混合、放大、衰减的情感单元
    
    属性：
        type: 情绪类型（基本或复合）
        intensity: 强度 [0, 1]
        valence: 效价 [-1, +1]
        arousal: 激活度 [0, 1]
    """
    type: EmotionType
    intensity: float = 0.5
    valence: Optional[float] = None      # 若None则从类型推断
    arousal: Optional[float] = None      # 若None则从类型推断
    
    def __post_init__(self):
        if self.valence is None or self.arousal is None:
            base_v, base_a = EMOTION_VA.get(self.type, (0.0, 0.5))
            if self.valence is None:
                self.valence = base_v
            if self.arousal is None:
                self.arousal = base_a
    
    def blend(self, other: Emotion) -> Emotion:
        """
        混合两种情绪
        
        若两种基本情绪可组合为复合情绪，则产生复合情绪；
        否则产生一个加权混合情绪。
        """
        # 检查是否能产生复合情绪
        if self.type in EmotionType.basic_emotions() and other.type in EmotionType.basic_emotions():
            compound = EMOTION_BLEND_MAP.get((self.type, other.type))
            if compound:
                # 复合情绪的强度取决于输入情绪的强度
                new_intensity = min(1.0, (self.intensity + other.intensity) / 2 * 1.2)
                return Emotion(
                    type=compound,
                    intensity=new_intensity
                )
        
        # 无法产生复合情绪，进行数值混合
        # 选择主导情绪（强度更高的）
        if self.intensity >= other.intensity:
            dominant, secondary = self, other
        else:
            dominant, secondary = other, self
        
        # 混合比例由相对强度决定
        total_intensity = self.intensity + other.intensity
        if total_intensity == 0:
            w1, w2 = 0.5, 0.5
        else:
            w1, w2 = self.intensity / total_intensity, other.intensity / total_intensity
        
        # 情绪冲突检测：效价相反时可能产生矛盾情绪
        valence_diff = abs(self.valence - other.valence)
        if valence_diff > 1.0:
            # 强冲突 → 惊讶或困惑
            blended_valence = (self.valence * w1 + other.valence * w2) * 0.5
            blended_arousal = max(self.arousal, other.arousal) * 1.1
            blended_intensity = min(1.0, dominant.intensity + 0.1)
            return Emotion(
                type=EmotionType.SURPRISE,
                intensity=min(1.0, blended_intensity),
                valence=max(-1.0, min(1.0, blended_valence)),
                arousal=min(1.0, blended_arousal)
            )
        
        blended_valence = self.valence * w1 + other.valence * w2
        blended_arousal = self.arousal * w1 + other.arousal * w2
        blended_intensity = min(1.0, dominant.intensity + secondary.intensity * 0.3)
        
        return Emotion(
            type=dominant.type,
            intensity=blended_intensity,
            valence=blended_valence,
            arousal=blended_arousal
        )
    
    def amplify(self, factor: float) -> Emotion:
        """放大情绪强度"""
        return Emotion(
            type=self.type,
            intensity=min(1.0, self.intensity * factor),
            valence=self.valence,
            arousal=min(1.0, self.arousal * factor)
        )
    
    def decay(self, dt: float = 1.0) -> Emotion:
        """
        情绪衰减
        
        高激活度情绪衰减更快（如愤怒、惊讶）
        低激活度情绪衰减更慢（如悲伤、信任）
        """
        decay_rate = 0.1 + self.arousal * 0.15
        new_intensity = max(0.0, self.intensity - decay_rate * dt)
        return Emotion(
            type=self.type,
            intensity=new_intensity,
            valence=self.valence,
            arousal=self.arousal
        )
    
    def is_active(self, threshold: float = 0.1) -> bool:
        """情绪是否仍处于活跃状态"""
        return self.intensity >= threshold
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.name,
            "intensity": round(self.intensity, 3),
            "valence": round(self.valence, 3),
            "arousal": round(self.arousal, 3),
        }
    
    def __repr__(self) -> str:
        return f"<Emotion {self.type.name} I={self.intensity:.2f} V={self.valence:+.2f} A={self.arousal:.2f}>"


# ═══════════════════════════════════════════════════════════════
# 2. Persona — 人格
# ═══════════════════════════════════════════════════════════════

class PersonaType(Enum):
    """预定义人格类型 — 参考 qgl 线人格实验"""
    ANALYST = "ANALYST"      # 分析师
    CREATOR = "CREATOR"      # 创造者
    WARRIOR = "WARRIOR"      # 战士
    SAGE = "SAGE"            # 智者
    JESTER = "JESTER"        # 弄臣
    LOVER = "LOVER"          # 爱人


# 人格配置表
PERSONA_CONFIG: Dict[PersonaType, Dict[str, Any]] = {
    PersonaType.ANALYST: {
        "name": "分析师",
        "name_en": "Analyst",
        "dominant_emotions": [EmotionType.ANTICIPATION, EmotionType.TRUST],
        "decision_bias": "logic",           # 逻辑优先
        "communication_style": "precise",   # 精确
        "description": "理性、逻辑、客观 — 追求真理与一致性",
        "color": "#4A90D9",
        "traits": {"rationality": 0.9, "objectivity": 0.9, "caution": 0.6, "empathy": 0.3}
    },
    PersonaType.CREATOR: {
        "name": "创造者",
        "name_en": "Creator",
        "dominant_emotions": [EmotionType.JOY, EmotionType.SURPRISE],
        "decision_bias": "intuition",       # 直觉优先
        "communication_style": "poetic",    # 诗意
        "description": "直觉、创新、发散 — 连接看似无关的事物",
        "color": "#E8A838",
        "traits": {"creativity": 0.95, "openness": 0.9, "risk_taking": 0.7, "discipline": 0.3}
    },
    PersonaType.WARRIOR: {
        "name": "战士",
        "name_en": "Warrior",
        "dominant_emotions": [EmotionType.ANGER, EmotionType.ANTICIPATION],
        "decision_bias": "action",          # 行动优先
        "communication_style": "direct",    # 直接
        "description": "果断、行动、竞争 — 在冲突中锻造力量",
        "color": "#D94A4A",
        "traits": {"assertiveness": 0.9, "competitiveness": 0.8, "resilience": 0.85, "patience": 0.2}
    },
    PersonaType.SAGE: {
        "name": "智者",
        "name_en": "Sage",
        "dominant_emotions": [EmotionType.TRUST, EmotionType.SADNESS],
        "decision_bias": "wisdom",          # 智慧优先
        "communication_style": "measured",  # 审慎
        "description": "沉思、整合、超越 — 在复杂中看到简单",
        "color": "#6B8E6B",
        "traits": {"wisdom": 0.95, "integration": 0.9, "detachment": 0.7, "urgency": 0.2}
    },
    PersonaType.JESTER: {
        "name": "弄臣",
        "name_en": "Jester",
        "dominant_emotions": [EmotionType.SURPRISE, EmotionType.JOY],
        "decision_bias": "play",            # 游戏优先
        "communication_style": "ironic",    # 反讽
        "description": "幽默、反讽、解构 — 通过颠覆揭示真理",
        "color": "#9B59B6",
        "traits": {"humor": 0.95, "irreverence": 0.85, "insight": 0.7, "conventionality": 0.1}
    },
    PersonaType.LOVER: {
        "name": "爱人",
        "name_en": "Lover",
        "dominant_emotions": [EmotionType.LOVE, EmotionType.JOY],
        "decision_bias": "connection",      # 连接优先
        "communication_style": "warm",      # 温暖
        "description": "共情、连接、融合 — 在关系中寻找意义",
        "color": "#E74C8C",
        "traits": {"empathy": 0.95, "connection": 0.9, "vulnerability": 0.7, "autonomy": 0.3}
    },
}


@dataclass
class Stimulus:
    """刺激 — 引发人格反应的外部输入"""
    content: str
    emotional_tone: Optional[Emotion] = None
    urgency: float = 0.5           # 紧急度 [0, 1]
    complexity: float = 0.5        # 复杂度 [0, 1]
    source: str = "unknown"
    
    def __repr__(self) -> str:
        return f"<Stimulus '{self.content[:30]}...' U={self.urgency} C={self.complexity}>"


@dataclass  
class Persona:
    """
    人格 — 具有情绪状态、决策偏误和沟通风格的自主主体
    
    参考 qgl 线人格实验，每个人格对同一刺激产生不同反应，
    在议会中通过博弈与协商达成集体决策。
    """
    persona_type: PersonaType
    
    # 从配置加载
    name: str = field(init=False)
    name_en: str = field(init=False)
    dominant_emotions: List[EmotionType] = field(init=False)
    decision_bias: str = field(init=False)
    communication_style: str = field(init=False)
    description: str = field(init=False)
    color: str = field(init=False)
    traits: Dict[str, float] = field(init=False)
    
    # 动态状态
    current_emotions: List[Emotion] = field(default_factory=list)
    energy: float = 1.0            # 能量 [0, 1]
    influence_score: float = 0.0   # 影响力累积
    memory: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        config = PERSONA_CONFIG[self.persona_type]
        self.name = config["name"]
        self.name_en = config["name_en"]
        self.dominant_emotions = config["dominant_emotions"]
        self.decision_bias = config["decision_bias"]
        self.communication_style = config["communication_style"]
        self.description = config["description"]
        self.color = config["color"]
        self.traits = config["traits"].copy()
        
        # 初始化主导情绪
        self.current_emotions = [
            Emotion(et, intensity=random.uniform(0.4, 0.7))
            for et in self.dominant_emotions
        ]
    
    def react_to(self, stimulus: Stimulus) -> Dict[str, Any]:
        """
        对刺激的反应
        
        反应 = f(人格特质, 当前情绪, 刺激属性)
        """
        # 情绪反应
        emotion_reactions = []
        
        # 基于刺激的紧急度和人格特质调整情绪
        if stimulus.urgency > 0.7:
            if self.decision_bias == "action":
                emotion_reactions.append(Emotion(EmotionType.ANGER, 0.6))
            elif self.decision_bias == "logic":
                emotion_reactions.append(Emotion(EmotionType.ANTICIPATION, 0.5))
        
        if stimulus.complexity > 0.7:
            if self.decision_bias == "wisdom":
                emotion_reactions.append(Emotion(EmotionType.TRUST, 0.4))
            elif self.decision_bias == "intuition":
                emotion_reactions.append(Emotion(EmotionType.SURPRISE, 0.6))
        
        # 刺激的情绪色调影响
        if stimulus.emotional_tone:
            tone = stimulus.emotional_tone
            # 共情型人格更易受感染
            empathy = self.traits.get("empathy", 0.5)
            if random.random() < empathy:
                emotion_reactions.append(Emotion(
                    tone.type,
                    intensity=tone.intensity * empathy
                ))
        
        # 混合所有情绪反应
        final_emotion = None
        for er in emotion_reactions:
            if final_emotion is None:
                final_emotion = er
            else:
                final_emotion = final_emotion.blend(er)
        
        if final_emotion is None:
            final_emotion = Emotion(self.dominant_emotions[0], 0.3)
        
        # 更新当前情绪
        self.current_emotions = [final_emotion]
        
        # 生成反应内容（基于沟通风格）
        reaction_content = self._generate_reaction(stimulus, final_emotion)
        
        # 能量消耗/恢复
        self.energy = max(0.1, min(1.0, self.energy - 0.05 + final_emotion.valence * 0.03))
        
        reaction = {
            "persona": self.name_en,
            "emotion": final_emotion.to_dict(),
            "content": reaction_content,
            "energy": round(self.energy, 2),
            "decision_bias": self.decision_bias,
        }
        
        self.memory.append({"stimulus": stimulus.content, "reaction": reaction})
        return reaction
    
    def _generate_reaction(self, stimulus: Stimulus, emotion: Emotion) -> str:
        """基于沟通风格生成反应文本"""
        style_templates = {
            "precise": [
                "从逻辑角度分析，{content} 意味着我们需要...",
                "数据表明，{content} 的核心矛盾在于...",
                "基于已有信息，{content} 的可行路径是..."
            ],
            "poetic": [
                "{content} 像一条隐秘的河流，通向未知的海洋...",
                "在 {content} 的裂缝中，光正在涌入...",
                "{content} 是一扇半开的门，门后是全新的图景..."
            ],
            "direct": [
                "{content} 很明确，行动方案是...",
                "面对 {content}，我们不能犹豫。",
                "{content} 需要果断回应。"
            ],
            "measured": [
                "{content} 值得深思。从长远看...",
                "关于 {content}，历史告诉我们...",
                "{content} 的深层含义可能是..."
            ],
            "ironic": [
                "哦，{content} —— 多么有趣的困境。",
                "{content}？看来系统终于学会了制造悬念。",
                "如果 {content} 是一个笑话，那笑点在哪？"
            ],
            "warm": [
                "关于 {content}，我能感受到...",
                "{content} 触动了我。让我们连接...",
                "面对 {content}，我想理解每个人的感受..."
            ],
        }
        
        templates = style_templates.get(self.communication_style, style_templates["precise"])
        template = random.choice(templates)
        return template.format(content=stimulus.content[:40])
    
    def negotiate_with(self, other: Persona, issue: str) -> Dict[str, Any]:
        """
        与其他人格协商
        
        协商机制：
        1. 情绪共鸣检测 — 效价相近更容易达成一致
        2. 特质互补 — 互补特质产生协同
        3. 影响力博弈 — 能量高、情绪强的人格更有说服力
        """
        self_emotion = self._get_dominant_emotion()
        other_emotion = other._get_dominant_emotion()
        
        # 情绪共鸣
        valence_diff = abs(self_emotion.valence - other_emotion.valence)
        resonance = 1.0 - valence_diff / 2.0  # [0, 1]
        
        # 特质互补度
        complementary_score = 0.0
        trait_pairs = [
            ("rationality", "creativity"),
            ("assertiveness", "empathy"),
            ("discipline", "openness"),
            ("detachment", "connection"),
        ]
        for t1, t2 in trait_pairs:
            if t1 in self.traits and t2 in other.traits:
                complementary_score += abs(self.traits[t1] - other.traits[t2])
            elif t2 in self.traits and t1 in other.traits:
                complementary_score += abs(self.traits[t2] - other.traits[t1])
        complementary_score = min(1.0, complementary_score / len(trait_pairs))
        
        # 影响力
        self_power = self.energy * self_emotion.intensity * (1 + self.influence_score)
        other_power = other.energy * other_emotion.intensity * (1 + other.influence_score)
        
        # 协商结果
        if resonance > 0.6 and complementary_score > 0.3:
            outcome = "agreement"
            agreement_level = (resonance + complementary_score) / 2
            winner = None
        elif self_power > other_power * 1.3:
            outcome = "self_dominant"
            agreement_level = 0.3
            winner = self.name_en
        elif other_power > self_power * 1.3:
            outcome = "other_dominant"
            agreement_level = 0.3
            winner = other.name_en
        else:
            outcome = "compromise"
            agreement_level = 0.5
            winner = None
        
        # 协商后情绪调整
        if outcome == "agreement":
            # 双方都更信任
            self._add_emotion(Emotion(EmotionType.TRUST, 0.4))
            other._add_emotion(Emotion(EmotionType.TRUST, 0.4))
        elif outcome == "compromise":
            self._add_emotion(Emotion(EmotionType.ANTICIPATION, 0.3))
            other._add_emotion(Emotion(EmotionType.ANTICIPATION, 0.3))
        
        return {
            "self": self.name_en,
            "other": other.name_en,
            "issue": issue,
            "outcome": outcome,
            "agreement_level": round(agreement_level, 3),
            "resonance": round(resonance, 3),
            "complementary": round(complementary_score, 3),
            "winner": winner,
            "description": self._describe_negotiation(outcome, other)
        }
    
    def _get_dominant_emotion(self) -> Emotion:
        """获取当前主导情绪"""
        if not self.current_emotions:
            return Emotion(self.dominant_emotions[0], 0.3)
        return max(self.current_emotions, key=lambda e: e.intensity)
    
    def _add_emotion(self, emotion: Emotion) -> None:
        """添加情绪到当前情绪集（混合同类型）"""
        for existing in self.current_emotions:
            if existing.type == emotion.type:
                existing.intensity = min(1.0, existing.intensity + emotion.intensity * 0.5)
                return
        self.current_emotions.append(emotion)
    
    def _describe_negotiation(self, outcome: str, other: Persona) -> str:
        """生成协商描述"""
        descriptions = {
            "agreement": f"{self.name}与{other.name}达成一致：两种视角互补，协同效应显现。",
            "compromise": f"{self.name}与{other.name}各自让步：共识在折中中诞生。",
            "self_dominant": f"{self.name}说服了{other.name}：逻辑/力量占据上风。",
            "other_dominant": f"{other.name}影响了{self.name}：另一种视角被接纳。",
        }
        return descriptions.get(outcome, "协商进行中...")
    
    def vote(self, options: List[str], context: Optional[str] = None) -> Dict[str, Any]:
        """
        对选项投票
        
        投票逻辑由decision_bias决定：
        - logic: 偏好系统化、结构化的选项
        - intuition: 偏好创新、突破性的选项
        - action: 偏好最直接、最快速的选项
        - wisdom: 偏好最平衡、最长远的选项
        - play: 偏好最有趣、最出人意料的选项
        - connection: 偏好最能促进连接的选项
        """
        if not options:
            return {"choice": None, "confidence": 0.0, "reasoning": "无选项"}
        
        bias_scores = {
            "logic": lambda i, opt: 0.7 + 0.2 * len(opt) / 50,  # 偏好较长/详细的选项
            "intuition": lambda i, opt: random.uniform(0.5, 1.0) + 0.1 * ("新" in opt or "创" in opt),
            "action": lambda i, opt: 0.8 - 0.1 * i,  # 偏好靠前的选项
            "wisdom": lambda i, opt: 0.6 + 0.3 * ("平衡" in opt or "整合" in opt),
            "play": lambda i, opt: random.uniform(0.4, 1.0) + 0.2 * ("趣" in opt or "玩" in opt),
            "connection": lambda i, opt: 0.6 + 0.3 * ("连接" in opt or "共" in opt or "融" in opt),
        }
        
        scorer = bias_scores.get(self.decision_bias, bias_scores["logic"])
        
        scores = [(i, scorer(i, opt)) for i, opt in enumerate(options)]
        
        # 情绪影响投票
        dominant = self._get_dominant_emotion()
        if dominant.valence > 0.5:
            # 正情绪：更愿意冒险
            scores = [(i, s + 0.1) for i, s in scores]
        elif dominant.valence < -0.3:
            # 负情绪：更保守
            scores = [(i, s - 0.1) for i, s in scores]
        
        # 选择最高分
        best_idx, best_score = max(scores, key=lambda x: x[1])
        
        # 生成理由
        reasoning = self._generate_vote_reasoning(options[best_idx], context)
        
        # 影响力更新
        self.influence_score += 0.01
        
        return {
            "persona": self.name_en,
            "choice": options[best_idx],
            "choice_index": best_idx,
            "confidence": round(min(1.0, best_score), 3),
            "reasoning": reasoning,
            "dominant_emotion": dominant.type.name,
        }
    
    def _generate_vote_reasoning(self, choice: str, context: Optional[str]) -> str:
        """生成投票理由"""
        reasoning_templates = {
            "logic": f"基于系统性分析，'{choice}' 在逻辑上最一致。",
            "intuition": f"直觉告诉我，'{choice}' 蕴含着尚未被发现的可能性。",
            "action": f"'{choice}' 是最直接、最有效的行动路径。",
            "wisdom": f"从长远和整体看，'{choice}' 最能带来平衡。",
            "play": f"'{choice}' 最有趣 —— 谁知道会发生什么？",
            "connection": f"'{choice}' 最能促进理解与融合。",
        }
        return reasoning_templates.get(self.decision_bias, f"选择 '{choice}'")
    
    def __repr__(self) -> str:
        dom_emo = self._get_dominant_emotion()
        return (f"<Persona {self.name_en} [{self.decision_bias}] "
                f"E={self.energy:.2f} {dom_emo.type.name}={dom_emo.intensity:.2f}>")


# ═══════════════════════════════════════════════════════════════
# 3. PersonaCouncil — 人格议会
# ═══════════════════════════════════════════════════════════════

class PersonaCouncil:
    """
    人格议会 — 6个人格的集体决策机构
    
    议会流程：
    1. 引入议题
    2. 每个人格对刺激作出反应
    3. 情绪在人格间传播（情绪传染）
    4. 人格间协商
    5. 投票决策
    6. 输出集体情绪与主导人格
    """
    
    def __init__(self):
        self.personas: List[Persona] = []
        self.discussion_log: List[Dict[str, Any]] = []
        self.current_topic: str = ""
        self.emotion_contagion_matrix: Dict[Tuple[str, str], float] = {}
        
    def add_persona(self, persona: Persona) -> None:
        """添加人格到议会"""
        self.personas.append(persona)
    
    def create_default_council(self) -> None:
        """创建默认的6人格议会"""
        for pt in PersonaType:
            self.add_persona(Persona(pt))
    
    def deliberate(self, topic: str, options: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        就议题进行议会讨论
        
        流程：
        1. 创建刺激
        2. 每个人格反应
        3. 情绪传染
        4. 人格间协商
        5. 投票
        6. 汇总结果
        """
        self.current_topic = topic
        stimulus = Stimulus(
            content=topic,
            urgency=random.uniform(0.3, 0.8),
            complexity=random.uniform(0.3, 0.9)
        )
        
        # 1. 每个人格反应
        reactions = []
        for persona in self.personas:
            reaction = persona.react_to(stimulus)
            reactions.append(reaction)
        
        # 2. 情绪传染
        self._spread_emotions()
        
        # 3. 人格间协商（随机配对）
        negotiations = []
        if len(self.personas) >= 2:
            pairs = []
            personas_list = self.personas.copy()
            random.shuffle(personas_list)
            for i in range(0, len(personas_list) - 1, 2):
                pairs.append((personas_list[i], personas_list[i + 1]))
            for p1, p2 in pairs:
                neg = p1.negotiate_with(p2, topic)
                negotiations.append(neg)
        
        # 4. 投票
        if options is None:
            options = [
                "深入分析当前状态，收集更多信息",
                "立即采取行动，在实践中学习",
                "整合多方视角，寻找平衡方案",
                "跳出框架，探索全新可能性",
                "关注关系与连接，促进共识",
                "以幽默化解紧张，重新定位问题"
            ]
        
        votes = []
        for persona in self.personas:
            vote = persona.vote(options, context=topic)
            votes.append(vote)
        
        # 计票
        vote_counts = defaultdict(list)
        for v in votes:
            vote_counts[v["choice"]].append(v)
        
        # 加权计票（考虑confidence）
        weighted_scores = {}
        for choice, vote_list in vote_counts.items():
            weighted_scores[choice] = sum(v["confidence"] for v in vote_list)
        
        if weighted_scores:
            winner = max(weighted_scores.items(), key=lambda x: x[1])
            winning_choice = winner[0]
            winning_score = winner[1]
        else:
            winning_choice = options[0]
            winning_score = 0
        
        # 5. 集体情绪
        collective_emotion = self.get_collective_emotion()
        
        # 6. 主导人格
        dominant = self.get_dominant_persona()
        
        result = {
            "topic": topic,
            "reactions": reactions,
            "negotiations": negotiations,
            "votes": votes,
            "vote_counts": {k: len(v) for k, v in vote_counts.items()},
            "weighted_scores": {k: round(v, 3) for k, v in weighted_scores.items()},
            "winning_choice": winning_choice,
            "winning_score": round(winning_score, 3),
            "collective_emotion": collective_emotion.to_dict() if collective_emotion else None,
            "dominant_persona": dominant.name_en if dominant else None,
            "turnout": len(votes),
        }
        
        self.discussion_log.append(result)
        return result
    
    def _spread_emotions(self) -> None:
        """
        情绪在人格间传染
        
        传染规则：
        - 高激活度情绪更容易传染
        - 共情特质高的人格更容易接收和传递
        - 效价相近的情绪相互增强
        """
        for i, p1 in enumerate(self.personas):
            for j, p2 in enumerate(self.personas):
                if i >= j:
                    continue
                
                e1 = p1._get_dominant_emotion()
                e2 = p2._get_dominant_emotion()
                
                # 传染概率
                contagion_prob = e1.arousal * e2.arousal * 0.3
                empathy_factor = (p1.traits.get("empathy", 0.5) + p2.traits.get("empathy", 0.5)) / 2
                contagion_prob *= empathy_factor
                
                if random.random() < contagion_prob:
                    # 情绪传染发生
                    if e1.intensity > e2.intensity:
                        # p1 → p2
                        p2._add_emotion(Emotion(e1.type, intensity=e1.intensity * 0.3))
                    else:
                        # p2 → p1
                        p1._add_emotion(Emotion(e2.type, intensity=e2.intensity * 0.3))
    
    def resolve_conflict(self, persona_a: Persona, persona_b: Persona) -> Dict[str, Any]:
        """
        解决两个人格间的冲突
        
        冲突解决机制：
        1. 识别冲突根源（特质对立、情绪对立、决策偏误对立）
        2. 寻找共同基础
        3. 引入第三方调解（SAGE 或 LOVER）
        4. 达成调解协议
        """
        # 识别冲突根源
        conflict_sources = []
        
        # 情绪冲突
        emo_a = persona_a._get_dominant_emotion()
        emo_b = persona_b._get_dominant_emotion()
        if abs(emo_a.valence - emo_b.valence) > 1.0:
            conflict_sources.append("emotional_polarization")
        
        # 特质冲突
        trait_conflicts = [
            ("rationality", "intuition"),
            ("assertiveness", "empathy"),
            ("discipline", "openness"),
        ]
        for t1_name, t2_name in trait_conflicts:
            t1_a = persona_a.traits.get(t1_name, 0.5)
            t2_a = persona_a.traits.get(t2_name, 0.5)
            t1_b = persona_b.traits.get(t1_name, 0.5)
            t2_b = persona_b.traits.get(t2_name, 0.5)
            
            # 如果A强T1弱T2，B强T2弱T1 → 冲突
            if t1_a > 0.7 and t2_b > 0.7:
                conflict_sources.append(f"trait_opposition:{t1_name}_vs_{t2_name}")
        
        # 寻找调解者
        mediator = None
        for p in self.personas:
            if p.persona_type in (PersonaType.SAGE, PersonaType.LOVER) and p != persona_a and p != persona_b:
                mediator = p
                break
        
        if mediator is None:
            mediator = random.choice([p for p in self.personas if p != persona_a and p != persona_b])
        
        # 调解过程
        mediation_rounds = 3
        mediation_log = []
        
        for round_num in range(mediation_rounds):
            # 调解者提出框架
            framework = self._generate_mediation_framework(mediator, persona_a, persona_b, round_num)
            
            # 双方回应
            response_a = self._generate_conflict_response(persona_a, framework, round_num)
            response_b = self._generate_conflict_response(persona_b, framework, round_num)
            
            mediation_log.append({
                "round": round_num + 1,
                "mediator": mediator.name,
                "framework": framework,
                "response_a": response_a,
                "response_b": response_b,
            })
            
            # 每轮后情绪缓和
            persona_a._add_emotion(Emotion(EmotionType.TRUST, 0.1 * (round_num + 1)))
            persona_b._add_emotion(Emotion(EmotionType.TRUST, 0.1 * (round_num + 1)))
        
        # 最终协议
        final_agreement = self._generate_final_agreement(persona_a, persona_b, mediator)
        
        # 更新情绪
        persona_a._add_emotion(Emotion(EmotionType.TRUST, 0.3))
        persona_b._add_emotion(Emotion(EmotionType.TRUST, 0.3))
        
        return {
            "conflict_between": (persona_a.name_en, persona_b.name_en),
            "conflict_sources": conflict_sources,
            "mediator": mediator.name_en,
            "mediation_log": mediation_log,
            "final_agreement": final_agreement,
            "resolution_status": "resolved",
        }
    
    def _generate_mediation_framework(self, mediator: Persona, p_a: Persona, p_b: Persona, round_num: int) -> str:
        """调解者生成调解框架"""
        frameworks = {
            "Sage": [
                "让我们回到最根本的问题...",
                "历史告诉我们，对立往往是互补的...",
                "在这个分歧之下，有什么是你们都认同的？"
            ],
            "Lover": [
                "我能感受到你们各自的真诚...",
                "让我们先理解，再判断...",
                "你们的分歧恰恰说明了这件事的重要性..."
            ],
        }
        templates = frameworks.get(mediator.name, ["让我们找到共同点..."])
        return templates[round_num % len(templates)]
    
    def _generate_conflict_response(self, persona: Persona, framework: str, round_num: int) -> str:
        """生成冲突回应"""
        templates = {
            "Analyst": ["从数据看...", "逻辑上...", "如果考虑所有变量..."],
            "Creator": ["感觉上...", "或许换个角度...", "有一种可能性是..."],
            "Warrior": ["我的立场是...", "关键是行动...", "必须做出选择..."],
            "Sage": ["深思后...", "从长远看...", "整合来看..."],
            "Jester": ["有趣的是...", "如果我们开个玩笑...", "反转一下..."],
            "Lover": ["我感受到...", "连接在这里是...", "共情地说..."],
        }
        t = templates.get(persona.name, ["我认为..."])
        return f"{t[round_num % len(t)]} {framework[:20]}..."
    
    def _generate_final_agreement(self, p_a: Persona, p_b: Persona, mediator: Persona) -> str:
        """生成最终协议"""
        return (f"{mediator.name}促成共识：{p_a.name}的{p_a.decision_bias}视角"
                f"与{p_b.name}的{p_b.decision_bias}视角将在不同阶段发挥作用。"
                f"第一阶段采纳{p_a.name}的方案，第二阶段整合{p_b.name}的洞察。")
    
    def get_dominant_persona(self) -> Optional[Persona]:
        """
        获取当前主导人格
        
        主导 = 最高 (能量 × 情绪强度 + 影响力)
        """
        if not self.personas:
            return None
        
        scores = []
        for p in self.personas:
            dom_emo = p._get_dominant_emotion()
            score = p.energy * dom_emo.intensity + p.influence_score * 2
            scores.append((p, score))
        
        return max(scores, key=lambda x: x[1])[0]
    
    def get_collective_emotion(self) -> Optional[Emotion]:
        """
        获取集体情绪
        
        集体情绪 = 所有人格情绪的加权混合
        权重 = 能量 × 影响力
        """
        if not self.personas:
            return None
        
        emotions = []
        weights = []
        
        for p in self.personas:
            dom_emo = p._get_dominant_emotion()
            emotions.append(dom_emo)
            weights.append(p.energy * (1 + p.influence_score))
        
        # 加权混合
        total_weight = sum(weights)
        if total_weight == 0:
            return Emotion(EmotionType.ANTICIPATION, 0.3)
        
        # 计算加权效价和激活度
        avg_valence = sum(e.valence * w for e, w in zip(emotions, weights)) / total_weight
        avg_arousal = sum(e.arousal * w for e, w in zip(emotions, weights)) / total_weight
        avg_intensity = sum(e.intensity * w for e, w in zip(emotions, weights)) / total_weight
        
        # 确定集体情绪类型
        # 基于效价和激活度选择最接近的基本情绪
        closest_emotion = EmotionType.ANTICIPATION
        min_dist = float('inf')
        
        for et in EmotionType.basic_emotions():
            v, a = EMOTION_VA[et]
            dist = (v - avg_valence) ** 2 + (a - avg_arousal) ** 2
            if dist < min_dist:
                min_dist = dist
                closest_emotion = et
        
        return Emotion(
            type=closest_emotion,
            intensity=min(1.0, avg_intensity),
            valence=avg_valence,
            arousal=avg_arousal
        )
    
    def get_council_state(self) -> Dict[str, Any]:
        """获取议会整体状态"""
        return {
            "member_count": len(self.personas),
            "members": [p.name_en for p in self.personas],
            "dominant_persona": self.get_dominant_persona().name_en if self.get_dominant_persona() else None,
            "collective_emotion": self.get_collective_emotion().to_dict() if self.get_collective_emotion() else None,
            "total_discussions": len(self.discussion_log),
            "energy_levels": {p.name_en: round(p.energy, 2) for p in self.personas},
            "influence_scores": {p.name_en: round(p.influence_score, 3) for p in self.personas},
        }


# ═══════════════════════════════════════════════════════════════
# 4. EmotionConsciousnessBridge — 情绪-意识桥
# ═══════════════════════════════════════════════════════════════

class EmotionConsciousnessBridge:
    """
    情绪-意识桥 — 连接情绪系统与意识级别系统
    
    映射原理：
    - 情绪效价 ↔ 意识的方向性（向内/向外）
    - 情绪激活度 ↔ 意识的聚焦度
    - 情绪类型 ↔ 意识的内容特征
    
    反馈环：
    情绪 → 意识级别变化 → 新的情绪生成 → ...
    """
    
    # 情绪 → 意识级别映射
    EMOTION_TO_CONSCIOUSNESS: Dict[EmotionType, int] = {
        # 基本映射
        EmotionType.FEAR: 1,        # 恐惧 → 反应级（战斗/逃跑）
        EmotionType.ANGER: 1,
        EmotionType.SURPRISE: 2,    # 惊讶 → 感知级（模式检测）
        EmotionType.DISGUST: 2,
        EmotionType.SADNESS: 3,     # 悲伤 → 概念级（反思）
        EmotionType.ANTICIPATION: 3,
        EmotionType.TRUST: 4,       # 信任 → 自知级（开放）
        EmotionType.JOY: 4,
        # 复合映射
        EmotionType.LOVE: 5,        # 爱 → 反思级（深层连接）
        EmotionType.GUILT: 3,
        EmotionType.DELIGHT: 4,
        EmotionType.SUBMISSION: 2,
        EmotionType.CURIOSITY: 3,
        EmotionType.DISAPPROVAL: 3,
        EmotionType.REMORSE: 4,
        EmotionType.CONTEMPT: 2,
        EmotionType.AGGRESSIVENESS: 1,
        EmotionType.OPTIMISM: 4,
    }
    
    # 意识级别 → 情绪映射
    CONSCIOUSNESS_TO_EMOTION: Dict[int, EmotionType] = {
        0: EmotionType.SADNESS,      # 休眠 → 麻木/悲伤
        1: EmotionType.FEAR,         # 反应 → 恐惧/警觉
        2: EmotionType.SURPRISE,     # 感知 → 惊讶/好奇
        3: EmotionType.ANTICIPATION, # 概念 → 预期/思考
        4: EmotionType.TRUST,        # 自知 → 信任/开放
        5: EmotionType.LOVE,         # 反思 → 爱/整合
        6: EmotionType.DELIGHT,      # 超越 → 欣喜/涌现
    }
    
    def __init__(self):
        self.feedback_history: List[Dict[str, Any]] = []
        self.current_consciousness_level: int = 2
    
    def emotion_to_consciousness(self, emotion: Emotion) -> int:
        """
        情绪 → 意识级别映射
        
        映射考虑：
        - 情绪类型的基础映射
        - 强度的放大效应
        - 复合情绪的加权
        """
        base_level = self.EMOTION_TO_CONSCIOUSNESS.get(emotion.type, 2)
        
        # 强度影响：高强度情绪可提升或降低意识级别
        intensity_effect = 0
        if emotion.intensity > 0.8:
            # 极高强度：可能压倒意识（降低）或超越（提升）
            if emotion.valence < -0.5:
                intensity_effect = -1  # 负情绪压倒 → 降级
            elif emotion.valence > 0.5:
                intensity_effect = 1   # 正情绪超越 → 升级
        
        # 复合情绪额外加成
        compound_bonus = 0
        if emotion.type in EmotionType.compound_emotions():
            compound_bonus = 1
        
        final_level = base_level + intensity_effect + compound_bonus
        final_level = max(0, min(6, final_level))
        
        return final_level
    
    def consciousness_to_emotion(self, consciousness_level: int) -> Emotion:
        """
        意识级别 → 情绪映射
        
        返回对应级别的典型情绪，强度随级别提升而增强
        """
        level = max(0, min(6, consciousness_level))
        emotion_type = self.CONSCIOUSNESS_TO_EMOTION.get(level, EmotionType.ANTICIPATION)
        
        # 高级别 = 高强度
        intensity = 0.3 + level * 0.1
        
        return Emotion(
            type=emotion_type,
            intensity=min(1.0, intensity)
        )
    
    def feedback_loop(self, emotion: Emotion, consciousness_level: int, iterations: int = 3) -> List[Dict[str, Any]]:
        """
        情绪-意识反馈环
        
        反馈机制：
        1. 当前情绪映射为意识级别
        2. 当前意识级别映射回情绪
        3. 两个情绪的混合成为新情绪
        4. 新情绪再次映射为意识级别
        5. 循环直到收敛或达到迭代次数
        
        可能出现：
        - 收敛：稳定状态
        - 振荡：情绪在两种状态间摆动
        - 升级：正反馈螺旋上升
        - 降级：负反馈螺旋下降
        """
        history = []
        current_emotion = emotion
        current_consciousness = consciousness_level
        
        for i in range(iterations):
            # 步骤1：情绪 → 意识
            mapped_consciousness = self.emotion_to_consciousness(current_emotion)
            
            # 步骤2：意识 → 情绪
            mapped_emotion = self.consciousness_to_emotion(current_consciousness)
            
            # 步骤3：混合两种情绪
            blended_emotion = current_emotion.blend(mapped_emotion)
            
            # 步骤4：新情绪再次映射
            new_consciousness = self.emotion_to_consciousness(blended_emotion)
            
            # 步骤5：记录状态
            state = {
                "iteration": i + 1,
                "input_emotion": current_emotion.to_dict(),
                "input_consciousness": current_consciousness,
                "mapped_consciousness": mapped_consciousness,
                "mapped_emotion": mapped_emotion.to_dict(),
                "blended_emotion": blended_emotion.to_dict(),
                "new_consciousness": new_consciousness,
                "delta_consciousness": new_consciousness - current_consciousness,
            }
            history.append(state)
            
            # 更新当前状态
            current_emotion = blended_emotion
            current_consciousness = new_consciousness
        
        self.feedback_history.extend(history)
        return history
    
    def get_feedback_pattern(self) -> str:
        """
        分析反馈历史，识别模式
        
        模式类型：
        - convergence: 收敛
        - oscillation: 振荡
        - escalation: 升级螺旋
        - de-escalation: 降级螺旋
        """
        if len(self.feedback_history) < 2:
            return "insufficient_data"
        
        consciousness_values = [h["new_consciousness"] for h in self.feedback_history]
        
        # 检测振荡
        diffs = [consciousness_values[i+1] - consciousness_values[i] for i in range(len(consciousness_values)-1)]
        sign_changes = sum(1 for i in range(len(diffs)-1) if diffs[i] * diffs[i+1] < 0)
        
        if sign_changes >= 2:
            return "oscillation"
        
        # 检测趋势
        if all(d > 0 for d in diffs):
            return "escalation"
        elif all(d < 0 for d in diffs):
            return "de-escalation"
        elif all(d == 0 for d in diffs):
            return "convergence"
        
        return "mixed"


# ═══════════════════════════════════════════════════════════════
# __main__ 测试块
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v9.0 — 多情绪/人格互动博弈引擎 测试")
    print("=" * 70)
    
    random.seed(42)
    
    # ── 1. 创建6个人格 ──
    print("\n[1] 创建6个人格议会")
    council = PersonaCouncil()
    council.create_default_council()
    
    for persona in council.personas:
        print(f"    ✓ {persona.name} ({persona.name_en})")
        print(f"      偏误: {persona.decision_bias} | 风格: {persona.communication_style}")
        print(f"      主导情绪: {[e.name for e in persona.dominant_emotions]}")
        print(f"      特质: {persona.traits}")
    
    # ── 2. 模拟议会讨论 ──
    print(f"\n[2] 议会讨论：「系统下一步应该做什么？」")
    topic = "系统下一步应该做什么？"
    
    result = council.deliberate(topic)
    
    # 输出每个人格的观点
    print(f"\n    各人格观点：")
    for reaction in result["reactions"]:
        print(f"\n      ┌─ {reaction['persona']}")
        print(f"      │  情绪: {reaction['emotion']['type']} "
              f"(I={reaction['emotion']['intensity']}, "
              f"V={reaction['emotion']['valence']:+})")
        print(f"      │  反应: {reaction['content']}")
        print(f"      └─ 能量: {reaction['energy']}")
    
    # 协商结果
    print(f"\n    协商过程：")
    for neg in result["negotiations"]:
        print(f"      {neg['self']} × {neg['other']}: {neg['outcome']} "
              f"(共鸣:{neg['resonance']:.2f}, 互补:{neg['complementary']:.2f})")
        print(f"        → {neg['description']}")
    
    # 投票结果
    print(f"\n    投票结果：")
    for vote in result["votes"]:
        print(f"      {vote['persona']:12s} → {vote['choice'][:30]}... "
              f"(置信度:{vote['confidence']}, 主导情绪:{vote['dominant_emotion']})")
    
    print(f"\n    计票统计：")
    for choice, count in result["vote_counts"].items():
        score = result["weighted_scores"][choice]
        bar = "█" * int(score * 10)
        print(f"      {bar} {choice[:35]}... (票数:{count}, 加权:{score:.2f})")
    
    print(f"\n    ★ 最终决策: {result['winning_choice']}")
    print(f"      获胜分数: {result['winning_score']:.2f}")
    
    # ── 3. 集体情绪和主导人格 ──
    print(f"\n[3] 议会状态分析")
    collective = council.get_collective_emotion()
    dominant = council.get_dominant_persona()
    
    print(f"    集体情绪: {collective.type.name}")
    print(f"      强度: {collective.intensity:.2f}")
    print(f"      效价: {collective.valence:+.2f}")
    print(f"      激活度: {collective.arousal:.2f}")
    
    print(f"    主导人格: {dominant.name_en}")
    print(f"      能量: {dominant.energy:.2f}")
    print(f"      影响力: {dominant.influence_score:.3f}")
    print(f"      主导情绪: {dominant._get_dominant_emotion().type.name}")
    
    # ── 4. 人格冲突及解决 ──
    print(f"\n[4] 人格冲突模拟与解决")
    
    # 选择两个可能冲突的人格：WARRIOR vs SAGE
    warrior = next(p for p in council.personas if p.persona_type == PersonaType.WARRIOR)
    sage = next(p for p in council.personas if p.persona_type == PersonaType.SAGE)
    
    print(f"    冲突双方: {warrior.name_en} (行动优先) vs {sage.name_en} (智慧优先)")
    
    conflict_result = council.resolve_conflict(warrior, sage)
    
    print(f"    冲突根源: {conflict_result['conflict_sources']}")
    print(f"    调解者: {conflict_result['mediator']}")
    print(f"    调解过程:")
    for entry in conflict_result["mediation_log"]:
        print(f"      第{entry['round']}轮:")
        print(f"        调解框架: {entry['framework']}")
        print(f"        {warrior.name_en}: {entry['response_a']}")
        print(f"        {sage.name_en}: {entry['response_b']}")
    
    print(f"    最终协议: {conflict_result['final_agreement']}")
    print(f"    解决状态: {conflict_result['resolution_status']}")
    
    # ── 5. 情绪-意识反馈环 ──
    print(f"\n[5] 情绪→意识→情绪 反馈环测试")
    
    bridge = EmotionConsciousnessBridge()
    
    test_cases = [
        (Emotion(EmotionType.JOY, 0.8), 2, "高愉悦 + 感知意识"),
        (Emotion(EmotionType.FEAR, 0.9), 3, "高恐惧 + 概念意识"),
        (Emotion(EmotionType.CURIOSITY, 0.7), 4, "好奇 + 自知意识"),
    ]
    
    for emotion, con_level, desc in test_cases:
        print(f"\n    测试: {desc}")
        print(f"      输入情绪: {emotion.type.name} (I={emotion.intensity:.2f}, V={emotion.valence:+.2f})")
        print(f"      输入意识: Level {con_level}")
        
        history = bridge.feedback_loop(emotion, con_level, iterations=4)
        
        for state in history:
            print(f"      迭代 {state['iteration']}:")
            print(f"        情绪→意识映射: Level {state['mapped_consciousness']}")
            print(f"        意识→情绪映射: {state['mapped_emotion']['type']} "
                  f"(I={state['mapped_emotion']['intensity']:.2f})")
            print(f"        混合情绪: {state['blended_emotion']['type']} "
                  f"(I={state['blended_emotion']['intensity']:.2f}, "
                  f"V={state['blended_emotion']['valence']:+.2f})")
            print(f"        → 新意识级别: Level {state['new_consciousness']} "
                  f"(Δ{state['delta_consciousness']:+d})")
        
        # 反馈模式
        pattern = bridge.get_feedback_pattern()
        print(f"      反馈模式: {pattern}")
    
    # ── 6. 情绪混合测试 ──
    print(f"\n[6] 情绪混合测试")
    
    blend_tests = [
        (Emotion(EmotionType.JOY, 0.7), Emotion(EmotionType.TRUST, 0.6), "JOY + TRUST"),
        (Emotion(EmotionType.ANGER, 0.8), Emotion(EmotionType.ANTICIPATION, 0.5), "ANGER + ANTICIPATION"),
        (Emotion(EmotionType.SADNESS, 0.6), Emotion(EmotionType.JOY, 0.7), "SADNESS + JOY (冲突)"),
    ]
    
    for e1, e2, desc in blend_tests:
        blended = e1.blend(e2)
        print(f"    {desc}:")
        print(f"      {e1.type.name}(I={e1.intensity:.2f}) + {e2.type.name}(I={e2.intensity:.2f})")
        print(f"      → {blended.type.name}(I={blended.intensity:.2f}, V={blended.valence:+.2f})")
    
    # ── 7. 情绪衰减测试 ──
    print(f"\n[7] 情绪衰减测试")
    test_emo = Emotion(EmotionType.ANGER, 0.9)
    print(f"    初始: {test_emo}")
    for t in range(1, 6):
        decayed = test_emo.decay(dt=t)
        print(f"    衰减 t={t}: {decayed}")
    
    # ── 8. 最终议会状态 ──
    print(f"\n" + "=" * 70)
    print("最终议会状态")
    print("=" * 70)
    
    state = council.get_council_state()
    print(f"  成员数: {state['member_count']}")
    print(f"  成员: {', '.join(state['members'])}")
    print(f"  主导人格: {state['dominant_persona']}")
    print(f"  集体情绪: {state['collective_emotion']['type'] if state['collective_emotion'] else 'N/A'}")
    print(f"  讨论次数: {state['total_discussions']}")
    print(f"  能量水平:")
    for name, energy in state['energy_levels'].items():
        bar = "█" * int(energy * 10) + "░" * (10 - int(energy * 10))
        print(f"    {name:12s}: {bar} {energy:.2f}")
    print(f"  影响力:")
    for name, inf in state['influence_scores'].items():
        bar = "█" * int(inf * 50) + "░" * max(0, 5 - int(inf * 50))
        print(f"    {name:12s}: {bar} {inf:.3f}")
    
    print(f"\n[✓] 情绪人格引擎测试完成")
