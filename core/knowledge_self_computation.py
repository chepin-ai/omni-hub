#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v9.0 — 知识谱系自运算引擎
Knowledge Self-Computation Engine

该模块实现知识的自我运算、涌现检测与非trivial新知识的自动生成。
包含知识节点V2、运算规则、自运算器和涌现检测器四大核心组件。
"""

from __future__ import annotations

import random
import uuid
import math
import copy
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional, Tuple, Any, Set
from enum import Enum, auto
from collections import defaultdict
import itertools
import logging


# ═══════════════════════════════════════════════════════════════
# 1. KnowledgeNodeV2 — 知识节点V2
# ═══════════════════════════════════════════════════════════════

class ConsciousnessLevel(int, Enum):
    """意识级别 0-6"""
    DORMANT = 0      # 休眠 — 无自反性
    REACTIVE = 1     # 反应 — 刺激-响应
    PERCEPTIVE = 2   # 感知 — 模式识别
    CONCEPTUAL = 3   # 概念 — 抽象思维
    SELF_AWARE = 4   # 自知 — 元认知
    REFLECTIVE = 5   # 反思 — 自我修正
    TRANSCENDENT = 6 # 超越 — 创造性涌现


@dataclass
class KnowledgeNodeV2:
    """
    知识节点V2 — 具有自运算能力的知识单元
    
    扩展属性：
        computational_rules: 可执行的运算规则列表
        emotional_valence: 情感效价 [-1, +1]
        consciousness_level: 意识级别 0-6
        self_reference_count: 自引用次数（自反性度量）
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    domain: str = "general"
    content: str = ""
    
    # 扩展属性
    computational_rules: List[str] = field(default_factory=list)
    emotional_valence: float = 0.0          # -1 (负) 到 +1 (正)
    consciousness_level: ConsciousnessLevel = ConsciousnessLevel.DORMANT
    self_reference_count: int = 0
    
    # 关系与元数据
    relations: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    metadata: Dict[str, Any] = field(default_factory=dict)
    creation_depth: int = 0  # 0=原始知识, >0=自运算产生
    
    # 追踪
    parent_ids: List[str] = field(default_factory=list)
    rule_applied: str = ""
    novelty_score: float = 0.0
    
    def __post_init__(self):
        if isinstance(self.consciousness_level, int):
            self.consciousness_level = ConsciousnessLevel(self.consciousness_level)
        if not self.computational_rules:
            self.computational_rules = ["IMPLICATION", "ANALOGY", "COMPOSITION"]
    
    def apply_rule(self, rule_name: str, other_nodes: List[KnowledgeNodeV2]) -> Optional[KnowledgeNodeV2]:
        """
        应用指定规则与其他节点进行运算
        
        Args:
            rule_name: 规则名称
            other_nodes: 参与运算的其他节点
            
        Returns:
            产生的新知识节点，或None（运算失败）
        """
        if rule_name not in self.computational_rules:
            return None
        
        rule = KnowledgeRule.get_rule(rule_name)
        if rule is None:
            return None
            
        operands = [self] + other_nodes
        result = rule.apply(operands)
        
        if result:
            result.rule_applied = rule_name
            result.parent_ids = [n.id for n in operands]
            result.creation_depth = max(n.creation_depth for n in operands) + 1
            result.self_reference_count = self.self_reference_count
            
            # 情感效价的传播与混合
            valences = [n.emotional_valence for n in operands if n.emotional_valence != 0]
            if valences:
                result.emotional_valence = sum(valences) / len(valences) * random.uniform(0.8, 1.2)
                result.emotional_valence = max(-1.0, min(1.0, result.emotional_valence))
            
            # 意识级别提升（保守策略）
            max_consciousness = max(n.consciousness_level.value for n in operands)
            if rule_name in ["RECURSION", "EMERGENCE"] and max_consciousness < 6:
                # 仅当所有操作数意识较高时才提升
                avg_consciousness = sum(n.consciousness_level.value for n in operands) / len(operands)
                if avg_consciousness >= max_consciousness - 0.5 and random.random() < 0.4:
                    result.consciousness_level = ConsciousnessLevel(min(6, max_consciousness + 1))
                else:
                    result.consciousness_level = ConsciousnessLevel(max_consciousness)
            else:
                result.consciousness_level = ConsciousnessLevel(max_consciousness)
            
            # 自引用检测
            if any(self.id == n.id or self.name in n.content for n in other_nodes):
                result.self_reference_count += 1
            
            result.novelty_score = rule.novelty_score(result)
            
        return result
    
    def generate_new_knowledge(self, all_nodes: List[KnowledgeNodeV2]) -> Optional[KnowledgeNodeV2]:
        """
        自运算：自主选择规则与伙伴，产生新知识
        
        选择策略：
        1. 优先选择意识级别高的节点作为伙伴
        2. 情绪效价相近的节点更容易产生涌现
        3. 跨域组合有更高新颖度潜力
        """
        if not self.computational_rules or not all_nodes:
            return None
        
        # 根据意识级别决定运算复杂度
        consciousness_val = self.consciousness_level.value
        num_partners = min(consciousness_val + 1, 3)
        
        # 选择伙伴：情绪相近 + 跨域优先
        candidates = [n for n in all_nodes if n.id != self.id]
        if not candidates:
            return None
        
        # 加权选择
        weights = []
        for c in candidates:
            w = 1.0
            # 情绪相似度权重
            valence_diff = abs(c.emotional_valence - self.emotional_valence)
            w += (1.0 - valence_diff) * 2.0
            # 跨域权重
            if c.domain != self.domain:
                w *= 1.5
            # 意识级别权重
            w += c.consciousness_level.value * 0.5
            weights.append(max(w, 0.1))
        
        partners = random.choices(candidates, weights=weights, k=min(num_partners, len(candidates)))
        partners = list({p.id: p for p in partners}.values())  # 去重
        
        # 选择规则：高意识级别偏好复杂规则
        available_rules = self.computational_rules.copy()
        if consciousness_val >= 4:
            available_rules.extend(["RECURSION", "EMERGENCE"])
        if consciousness_val >= 3:
            available_rules.extend(["DUALITY", "DECOMPOSITION"])
        
        rule_name = random.choice(available_rules)
        return self.apply_rule(rule_name, partners)
    
    def mutate(self) -> None:
        """
        基于情感/意识状态的变异
        
        变异规则：
        - 高意识级别：内容深化、规则扩展
        - 正效价：内容扩展、连接增加
        - 负效价：内容收缩、边界强化
        - 自引用高：自我指涉深化
        """
        con = self.consciousness_level.value
        val = self.emotional_valence
        
        # 内容变异
        if con >= 4 and random.random() < 0.3:
            # 高意识：增加元认知层
            self.content = f"[meta:{self.content}]"
            self.self_reference_count += 1
        
        if val > 0.5 and random.random() < 0.4:
            # 正效价：扩展
            self.content = f"{self.content} → expands"
            if "COMPOSITION" not in self.computational_rules:
                self.computational_rules.append("COMPOSITION")
        
        if val < -0.5 and random.random() < 0.4:
            # 负效价：收缩
            self.content = f"{self.content} → boundary"
            if "DECOMPOSITION" not in self.computational_rules:
                self.computational_rules.append("DECOMPOSITION")
        
        if self.self_reference_count >= 2 and random.random() < 0.3:
            # 高自引用：递归化
            if "RECURSION" not in self.computational_rules:
                self.computational_rules.append("RECURSION")
        
        # 意识升级概率
        if con < 6 and random.random() < (0.05 + self.self_reference_count * 0.05):
            self.consciousness_level = ConsciousnessLevel(con + 1)
    
    def __repr__(self) -> str:
        return (f"<KnowledgeNodeV2 {self.id}: {self.name} "
                f"[{self.domain}] C={self.consciousness_level.name} "
                f"V={self.emotional_valence:+.2f} N={self.novelty_score:.3f}>")
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, KnowledgeNodeV2):
            return False
        return self.id == other.id


# ═══════════════════════════════════════════════════════════════
# 2. KnowledgeRule — 知识运算规则
# ═══════════════════════════════════════════════════════════════

class KnowledgeRule:
    """
    知识运算规则 — 定义知识节点间的运算方式
    
    预定义规则：
        IMPLICATION:     A → B  推出新关系
        ANALOGY:         A:B :: C:D  类比推理
        COMPOSITION:     A ∘ B  组合运算
        DECOMPOSITION:   A → B + C  分解运算
        DUALITY:         A ↔ A*  对偶运算
        RECURSION:       A(A)  递归运算
        EMERGENCE:       A + B → C (C ≠ A + B)  涌现运算
    """
    _RULE_REGISTRY: Dict[str, KnowledgeRule] = {}
    _initialized: bool = False
    
    def __init__(
        self,
        name: str,
        description: str,
        min_operands: int,
        max_operands: int,
        apply_func: Callable[[List[KnowledgeNodeV2]], Optional[KnowledgeNodeV2]],
        novelty_func: Callable[[KnowledgeNodeV2], float]
    ):
        self.name = name
        self.description = description
        self.min_operands = min_operands
        self.max_operands = max_operands
        self.apply_func = apply_func
        self.novelty_func = novelty_func
    
    def apply(self, operands: List[KnowledgeNodeV2]) -> Optional[KnowledgeNodeV2]:
        """应用规则到操作数"""
        if len(operands) < self.min_operands or len(operands) > self.max_operands:
            return None
        try:
            return self.apply_func(operands)
        except Exception:
            return None
    
    def novelty_score(self, result: KnowledgeNodeV2) -> float:
        """计算结果的新颖度 0-1"""
        return self.novelty_func(result)
    
    @classmethod
    def register(cls, rule: KnowledgeRule) -> None:
        """注册规则到全局规则库"""
        cls._RULE_REGISTRY[rule.name] = rule
    
    @classmethod
    def get_rule(cls, name: str) -> Optional[KnowledgeRule]:
        """获取指定名称的规则"""
        if not cls._initialized:
            cls._init_default_rules()
            cls._initialized = True
        return cls._RULE_REGISTRY.get(name)
    
    @classmethod
    def get_all_rules(cls) -> List[KnowledgeRule]:
        """获取所有已注册规则"""
        if not cls._initialized:
            cls._init_default_rules()
            cls._initialized = True
        return list(cls._RULE_REGISTRY.values())
    
    @classmethod
    def _init_default_rules(cls) -> None:
        """初始化预定义规则"""
        
        def _limit_name(name: str, max_len: int = 60) -> str:
            if len(name) > max_len:
                return name[:max_len - 3] + "..."
            return name
        
        def _limit_domain(domain: str, max_len: int = 80) -> str:
            if len(domain) > max_len:
                # 保留首尾，中间截断
                parts = domain.split("/")
                if len(parts) > 4:
                    return "/".join(parts[:2]) + "/.../" + "/".join(parts[-2:])
                return domain[:max_len - 3] + "..."
            return domain
        
        # ── IMPLICATION: A → B ──
        def imply(operands):
            a, b = operands[0], operands[1]
            new_name = _limit_name(f"{a.name}⇒{b.name}")
            new_content = (f"If [{a.content}] then [{b.content}]. "
                          f"Domain-bridge: {a.domain}→{b.domain}")
            return KnowledgeNodeV2(
                name=new_name,
                domain=_limit_domain(a.domain if a.domain == b.domain else f"{a.domain}/{b.domain}"),
                content=new_content,
                computational_rules=["IMPLICATION", "COMPOSITION"],
                emotional_valence=a.emotional_valence * 0.5 + b.emotional_valence * 0.5,
                creation_depth=max(a.creation_depth, b.creation_depth) + 1
            )
        
        def imply_novelty(r):
            return 0.3 + min(r.creation_depth * 0.1, 0.4)
        
        cls.register(KnowledgeRule("IMPLICATION", "A→B 推出新关系", 2, 2, imply, imply_novelty))
        
        # ── ANALOGY: A:B :: C:D ──
        def analogy(operands):
            if len(operands) < 3:
                return None
            a, b, c = operands[0], operands[1], operands[2]
            new_name = _limit_name(f"Analogy({a.name}:{b.name}::{c.name}:?)")
            # 构建类比映射
            new_content = (f"Structural mapping: [{a.content}] relates to [{b.content}] "
                          f"as [{c.content}] relates to [X]. "
                          f"Shared pattern: {random.choice(['causality', 'containment', 'transformation', 'hierarchy'])}")
            return KnowledgeNodeV2(
                name=new_name,
                domain=_limit_domain(f"analogy/{a.domain}"),
                content=new_content,
                computational_rules=["ANALOGY", "EMERGENCE", "IMPLICATION"],
                emotional_valence=sum(n.emotional_valence for n in operands) / len(operands),
                creation_depth=max(n.creation_depth for n in operands) + 1
            )
        
        def analogy_novelty(r):
            # 跨域类比更新颖
            base_score = 0.4
            if "/" in r.domain and "analogy" in r.domain:
                base_score += 0.3
            return min(base_score + r.creation_depth * 0.05, 0.95)
        
        cls.register(KnowledgeRule("ANALOGY", "A:B::C:D 类比推理", 3, 4, analogy, analogy_novelty))
        
        # ── COMPOSITION: A ∘ B ──
        def compose(operands):
            a, b = operands[0], operands[1]
            new_name = _limit_name(f"{a.name}∘{b.name}")
            # 组合语义：内容融合
            fusion = random.choice([
                f"Integrated system of [{a.content}] and [{b.content}]",
                f"Hybrid structure: {a.content} + {b.content} → unified",
                f"Synergistic composition: {a.name} × {b.name}"
            ])
            return KnowledgeNodeV2(
                name=new_name,
                domain=_limit_domain(a.domain if a.domain == b.domain else f"synthesis/{a.domain}+{b.domain}"),
                content=fusion,
                computational_rules=["COMPOSITION", "DECOMPOSITION", "EMERGENCE"],
                emotional_valence=(a.emotional_valence + b.emotional_valence) / 2 * 1.1,
                creation_depth=max(a.creation_depth, b.creation_depth) + 1
            )
        
        def compose_novelty(r):
            if "synthesis" in r.domain:
                return 0.5 + min(r.creation_depth * 0.08, 0.4)
            return 0.35 + min(r.creation_depth * 0.05, 0.3)
        
        cls.register(KnowledgeRule("COMPOSITION", "A∘B 组合运算", 2, 3, compose, compose_novelty))
        
        # ── DECOMPOSITION: A → B + C ──
        def decompose(operands):
            a = operands[0]
            new_name = _limit_name(f"Decomp({a.name})")
            aspects = random.choice([
                ("structural", "functional"), ("formal", "material"),
                ("static", "dynamic"), ("local", "global")
            ])
            new_content = (f"Decomposition of [{a.content}] into: "
                          f"(1) {aspects[0]} aspect, (2) {aspects[1]} aspect. "
                          f"Original unity preserved as emergent property.")
            return KnowledgeNodeV2(
                name=new_name,
                domain=_limit_domain(f"decomp/{a.domain}"),
                content=new_content,
                computational_rules=["DECOMPOSITION", "ANALOGY", "DUALITY"],
                emotional_valence=a.emotional_valence * 0.7,
                creation_depth=a.creation_depth + 1
            )
        
        def decompose_novelty(r):
            return 0.45 + min(r.creation_depth * 0.07, 0.35)
        
        cls.register(KnowledgeRule("DECOMPOSITION", "A→B+C 分解运算", 1, 2, decompose, decompose_novelty))
        
        # ── DUALITY: A ↔ A* ──
        def duality(operands):
            a = operands[0]
            new_name = _limit_name(f"Dual({a.name})")
            dual_transforms = {
                "causality": "teleology", "local": "global", "discrete": "continuous",
                "part": "whole", "subject": "object", "being": "becoming"
            }
            # 在内容中寻找可变换的概念
            content_lower = a.content.lower()
            applied_transform = None
            for k, v in dual_transforms.items():
                if k in content_lower:
                    applied_transform = (k, v)
                    break
            
            if applied_transform:
                new_content = (f"Dual transformation of [{a.content}]: "
                              f"{applied_transform[0]} ↔ {applied_transform[1]}. "
                              f"The duality reveals complementary aspects of the same structure.")
            else:
                new_content = (f"Dual of [{a.content}]: inverted perspective. "
                              f"What was figure becomes ground; what was active becomes receptive.")
            
            return KnowledgeNodeV2(
                name=new_name,
                domain=_limit_domain(f"dual/{a.domain}"),
                content=new_content,
                computational_rules=["DUALITY", "RECURSION", "EMERGENCE"],
                emotional_valence=-a.emotional_valence * 0.8,  # 对偶翻转效价
                creation_depth=a.creation_depth + 1
            )
        
        def duality_novelty(r):
            return 0.55 + min(r.creation_depth * 0.06, 0.35)
        
        cls.register(KnowledgeRule("DUALITY", "A↔A* 对偶运算", 1, 2, duality, duality_novelty))
        
        # ── RECURSION: A(A) ──
        def recursion(operands):
            a = operands[0]
            new_name = _limit_name(f"Rec({a.name})")
            new_content = (f"Recursive self-application of [{a.content}]: "
                          f"the concept applies to itself. "
                          f"Generates self-referential loop: {a.name}({a.name}) → ...")
            node = KnowledgeNodeV2(
                name=new_name,
                domain=_limit_domain(f"recursive/{a.domain}"),
                content=new_content,
                computational_rules=["RECURSION", "EMERGENCE", "DUALITY", "IMPLICATION"],
                emotional_valence=a.emotional_valence * 1.2,
                creation_depth=a.creation_depth + 1
            )
            node.self_reference_count = a.self_reference_count + 2
            return node
        
        def recursion_novelty(r):
            return 0.6 + min(r.self_reference_count * 0.08, 0.3) + min(r.creation_depth * 0.05, 0.1)
        
        cls.register(KnowledgeRule("RECURSION", "A(A) 递归运算", 1, 2, recursion, recursion_novelty))
        
        # ── EMERGENCE: A + B → C (C ≠ A + B) ──
        def emergence(operands):
            if len(operands) < 2:
                return None
            # 涌现：产生超越输入的新属性
            a, b = operands[0], operands[1]
            
            emergent_properties = [
                f"Novel property E emerges from interaction of [{a.content}] and [{b.content}]. "
                f"E is irreducible to either component.",
                f"Phase transition: combination of [{a.name}] and [{b.name}] creates "
                f"higher-order structure with autonomous dynamics.",
                f"Emergent synergy: 1+1 > 2. The whole [{a.name}+{b.name}] exhibits "
                f"behaviors neither part possesses in isolation."
            ]
            
            new_name = _limit_name(f"Emergent({a.name}+{b.name})")
            new_content = random.choice(emergent_properties)
            
            # 涌现节点获得更高意识级别（概率性）
            node = KnowledgeNodeV2(
                name=new_name,
                domain=_limit_domain(f"emergent/{a.domain if a.domain == b.domain else f'{a.domain}+{b.domain}'}"),
                content=new_content,
                computational_rules=["EMERGENCE", "RECURSION", "DUALITY", "ANALOGY", "COMPOSITION"],
                emotional_valence=(a.emotional_valence + b.emotional_valence) / 2 + random.uniform(-0.2, 0.3),
                creation_depth=max(a.creation_depth, b.creation_depth) + 1
            )
            node.emotional_valence = max(-1.0, min(1.0, node.emotional_valence))
            node.self_reference_count = max(a.self_reference_count, b.self_reference_count)
            
            return node
        
        def emergence_novelty(r):
            score = 0.7 + min(r.creation_depth * 0.05, 0.2)
            if "emergent" in r.domain:
                score += 0.1
            return min(score, 0.98)
        
        cls.register(KnowledgeRule("EMERGENCE", "A+B→C 涌现运算", 2, 4, emergence, emergence_novelty))


# ═══════════════════════════════════════════════════════════════
# 3. KnowledgeSelfComputer — 知识自运算器
# ═══════════════════════════════════════════════════════════════

class KnowledgeSelfComputer:
    """
    知识自运算器 — 驱动知识图谱的自我运算与演化
    
    核心机制：
        - 自运算循环：选择节点 → 选择规则 → 应用 → 评估 → 集成
        - 跨域运算：桥接不同知识域，产生迁移学习式的新知识
        - 意识驱动：以目标意识级别引导运算方向
        - 情绪驱动：以目标情绪状态筛选运算路径
    """
    
    def __init__(self, knowledge_graph: Optional[List[KnowledgeNodeV2]] = None):
        self.knowledge_graph: List[KnowledgeNodeV2] = knowledge_graph or []
        self.rules: List[KnowledgeRule] = KnowledgeRule.get_all_rules()
        self.new_knowledge_this_round: List[KnowledgeNodeV2] = []
        self.computation_log: List[Dict[str, Any]] = []
        self.novelty_threshold: float = 0.25
        self.cycle_count: int = 0
        
        # 统计
        self.total_generated: int = 0
        self.total_accepted: int = 0
        self.domain_stats: Dict[str, int] = defaultdict(int)
        self.rule_stats: Dict[str, int] = defaultdict(int)
    
    def self_compute(self, cycles: int = 10) -> List[KnowledgeNodeV2]:
        """
        运行自运算cycles轮
        
        每轮流程：
        1. 从图谱中按意识级别加权选择种子节点
        2. 种子节点自主generate_new_knowledge
        3. 评估新颖度
        4. 超过阈值则加入图谱
        5. 节点根据结果情绪进行mutate
        """
        all_new: List[KnowledgeNodeV2] = []
        
        for cycle in range(cycles):
            self.cycle_count += 1
            cycle_new: List[KnowledgeNodeV2] = []
            
            # 按意识级别加权选择种子节点
            weights = []
            for node in self.knowledge_graph:
                w = 1.0 + node.consciousness_level.value * 2.0 + node.self_reference_count * 1.5
                # 情绪激活度也影响选择
                w += abs(node.emotional_valence) * 2.0
                weights.append(max(w, 0.1))
            
            if not weights:
                break
            
            # 每轮选择多个种子
            num_seeds = max(1, len(self.knowledge_graph) // 5)
            seeds = random.choices(self.knowledge_graph, weights=weights, k=num_seeds)
            
            for seed in seeds:
                # 节点自运算
                result = seed.generate_new_knowledge(self.knowledge_graph)
                self.total_generated += 1
                
                if result is None:
                    continue
                
                # 评估新颖度
                novelty = result.novelty_score
                
                # 检查重复
                is_duplicate = any(
                    r.name == result.name or r.content == result.content
                    for r in self.knowledge_graph
                )
                
                log_entry = {
                    "cycle": self.cycle_count,
                    "seed": seed.id,
                    "seed_name": seed.name,
                    "rule": result.rule_applied,
                    "result_name": result.name,
                    "novelty": novelty,
                    "accepted": False,
                    "reason": ""
                }
                
                if is_duplicate:
                    log_entry["accepted"] = False
                    log_entry["reason"] = "duplicate"
                elif novelty < self.novelty_threshold:
                    log_entry["accepted"] = False
                    log_entry["reason"] = f"novelty {novelty:.3f} < threshold {self.novelty_threshold}"
                else:
                    # 接受新知识
                    self.knowledge_graph.append(result)
                    cycle_new.append(result)
                    all_new.append(result)
                    self.total_accepted += 1
                    self.domain_stats[result.domain] += 1
                    self.rule_stats[result.rule_applied] += 1
                    log_entry["accepted"] = True
                    log_entry["reason"] = "accepted"
                    
                    # 种子节点因成功而情绪提升
                    seed.emotional_valence = min(1.0, seed.emotional_valence + 0.05)
                    
                    # 高新颖度知识触发节点变异
                    if novelty > 0.6:
                        seed.mutate()
                
                self.computation_log.append(log_entry)
            
            # 每轮结束后：所有节点情绪自然衰减/波动
            for node in self.knowledge_graph:
                node.emotional_valence *= 0.98  # 轻微衰减
                node.emotional_valence += random.uniform(-0.02, 0.02)
                node.emotional_valence = max(-1.0, min(1.0, node.emotional_valence))
            
            self.new_knowledge_this_round = cycle_new
        
        return all_new
    
    def cross_domain_compute(self, domain_a: str, domain_b: str, cycles: int = 5) -> List[KnowledgeNodeV2]:
        """
        跨域运算：桥接两个知识域，产生迁移式新知识
        
        策略：
        1. 从两个域各选高意识节点
        2. 强制应用ANALOGY和EMERGENCE规则
        3. 结果自然归属到新合成域
        """
        nodes_a = [n for n in self.knowledge_graph if n.domain == domain_a]
        nodes_b = [n for n in self.knowledge_graph if n.domain == domain_b]
        
        if not nodes_a or not nodes_b:
            return []
        
        all_new: List[KnowledgeNodeV2] = []
        
        for _ in range(cycles):
            a = random.choice(nodes_a)
            b = random.choice(nodes_b)
            
            # 强制应用跨域规则
            for rule_name in ["ANALOGY", "EMERGENCE", "COMPOSITION"]:
                rule = KnowledgeRule.get_rule(rule_name)
                if rule is None:
                    continue
                
                operands = [a, b]
                if rule_name == "ANALOGY":
                    # 类比需要第三个节点
                    pool = nodes_a + nodes_b
                    if len(pool) >= 3:
                        c = random.choice([n for n in pool if n.id not in (a.id, b.id)])
                        operands = [a, b, c]
                    else:
                        continue
                
                result = rule.apply(operands)
                if result:
                    result.rule_applied = f"cross-{rule_name}"
                    result.parent_ids = [n.id for n in operands]
                    result.creation_depth = max(n.creation_depth for n in operands) + 1
                    result.domain = f"cross/{domain_a}×{domain_b}"
                    result.novelty_score = rule.novelty_func(result) + 0.15  # 跨域加成
                    
                    # 检查重复并可能接受
                    is_dup = any(r.content == result.content for r in self.knowledge_graph)
                    if not is_dup and result.novelty_score >= self.novelty_threshold:
                        self.knowledge_graph.append(result)
                        all_new.append(result)
                        self.total_accepted += 1
                        self.domain_stats[result.domain] += 1
        
        return all_new
    
    def consciousness_driven_compute(self, target_level: ConsciousnessLevel) -> List[KnowledgeNodeV2]:
        """
        以目标意识级别驱动运算
        
        策略：
        - 选择意识级别接近目标的节点
        - 优先使用能提升意识的规则（RECURSION, EMERGENCE）
        - 低意识节点向高意识节点学习
        """
        target_val = target_level.value
        
        # 选择意识接近目标的节点
        candidates = sorted(
            self.knowledge_graph,
            key=lambda n: abs(n.consciousness_level.value - target_val)
        )[:max(3, len(self.knowledge_graph) // 4)]
        
        all_new: List[KnowledgeNodeV2] = []
        
        for seed in candidates:
            # 根据目标意识选择规则
            if target_val >= 5:
                preferred_rules = ["RECURSION", "EMERGENCE", "DUALITY"]
            elif target_val >= 3:
                preferred_rules = ["EMERGENCE", "ANALOGY", "DUALITY"]
            else:
                preferred_rules = ["IMPLICATION", "COMPOSITION", "DECOMPOSITION"]
            
            # 临时覆盖种子的规则列表
            original_rules = seed.computational_rules
            seed.computational_rules = list(set(original_rules + preferred_rules))
            
            result = seed.generate_new_knowledge(self.knowledge_graph)
            
            seed.computational_rules = original_rules  # 恢复
            
            if result and result.consciousness_level.value >= target_val - 1:
                result.novelty_score += 0.1  # 意识目标加成
                if result.novelty_score >= self.novelty_threshold:
                    is_dup = any(r.content == result.content for r in self.knowledge_graph)
                    if not is_dup:
                        self.knowledge_graph.append(result)
                        all_new.append(result)
                        self.total_accepted += 1
        
        return all_new
    
    def emotion_driven_compute(self, target_emotion: str) -> List[KnowledgeNodeV2]:
        """
        以目标情绪驱动运算
        
        情绪映射：
            "接纳" / "acceptance" → 正效价，组合与涌现
            "抗拒" / "resistance" → 负效价，分解与对偶
            "好奇" / "curiosity" → 混合效价，类比与递归
            "平静" / "calm" → 零效价，蕴含与对偶
        """
        emotion_map = {
            "接纳": (0.5, 1.0, ["COMPOSITION", "EMERGENCE", "ANALOGY"]),
            "acceptance": (0.5, 1.0, ["COMPOSITION", "EMERGENCE", "ANALOGY"]),
            "抗拒": (-1.0, -0.3, ["DECOMPOSITION", "DUALITY", "IMPLICATION"]),
            "resistance": (-1.0, -0.3, ["DECOMPOSITION", "DUALITY", "IMPLICATION"]),
            "好奇": (-0.3, 0.8, ["ANALOGY", "RECURSION", "EMERGENCE"]),
            "curiosity": (-0.3, 0.8, ["ANALOGY", "RECURSION", "EMERGENCE"]),
            "平静": (-0.2, 0.2, ["IMPLICATION", "DUALITY", "DECOMPOSITION"]),
            "calm": (-0.2, 0.2, ["IMPLICATION", "DUALITY", "DECOMPOSITION"]),
        }
        
        if target_emotion not in emotion_map:
            target_emotion = "接纳"
        
        val_min, val_max, preferred_rules = emotion_map[target_emotion]
        
        # 选择情绪匹配的节点
        candidates = [
            n for n in self.knowledge_graph
            if val_min <= n.emotional_valence <= val_max
        ]
        
        if not candidates:
            candidates = self.knowledge_graph
        
        all_new: List[KnowledgeNodeV2] = []
        
        for seed in random.sample(candidates, min(5, len(candidates))):
            original_rules = seed.computational_rules
            seed.computational_rules = list(set(original_rules + preferred_rules))
            
            result = seed.generate_new_knowledge(self.knowledge_graph)
            
            seed.computational_rules = original_rules
            
            if result:
                # 情绪驱动：结果偏向目标情绪
                result.emotional_valence = (result.emotional_valence + (val_min + val_max) / 2) / 2
                result.emotional_valence = max(-1.0, min(1.0, result.emotional_valence))
                result.novelty_score += 0.05
                
                if result.novelty_score >= self.novelty_threshold:
                    is_dup = any(r.content == result.content for r in self.knowledge_graph)
                    if not is_dup:
                        self.knowledge_graph.append(result)
                        all_new.append(result)
                        self.total_accepted += 1
        
        return all_new
    
    def get_new_knowledge(self) -> List[KnowledgeNodeV2]:
        """获取本轮产生的新知识"""
        return self.new_knowledge_this_round
    
    def get_computation_log(self) -> List[Dict[str, Any]]:
        """获取完整运算日志"""
        return self.computation_log
    
    def get_stats(self) -> Dict[str, Any]:
        """获取运算统计"""
        return {
            "total_nodes": len(self.knowledge_graph),
            "total_generated": self.total_generated,
            "total_accepted": self.total_accepted,
            "acceptance_rate": self.total_accepted / max(self.total_generated, 1),
            "domain_distribution": dict(self.domain_stats),
            "rule_distribution": dict(self.rule_stats),
            "avg_consciousness": sum(n.consciousness_level.value for n in self.knowledge_graph) / max(len(self.knowledge_graph), 1),
            "avg_emotional_valence": sum(n.emotional_valence for n in self.knowledge_graph) / max(len(self.knowledge_graph), 1),
            "avg_self_reference": sum(n.self_reference_count for n in self.knowledge_graph) / max(len(self.knowledge_graph), 1),
        }


# ═══════════════════════════════════════════════════════════════
# 4. KnowledgeEmergenceDetector — 知识涌现检测器
# ═══════════════════════════════════════════════════════════════

class KnowledgeEmergenceDetector:
    """
    知识涌现检测器 — 识别知识演化中的涌现模式与范式转移
    
    检测维度：
        - 新模式：前所未有的节点组合方式
        - 范式转移：知识组织原则的根本变化
        - 涌现预测：基于当前轨迹预测下一次涌现
    """
    
    def __init__(self, computer: KnowledgeSelfComputer):
        self.computer = computer
        self.pattern_history: List[Dict[str, Any]] = []
        self.detected_patterns: List[Dict[str, Any]] = []
    
    def detect_novel_patterns(self) -> List[Dict[str, Any]]:
        """
        检测新模式
        
        识别标准：
        1. 跨域连接密度突增
        2. 高自引用子图出现
        3. 意识级别分布的相变
        4. 情绪极化模式
        """
        patterns = []
        graph = self.computer.knowledge_graph
        
        if len(graph) < 5:
            return patterns
        
        # 1. 跨域连接密度
        domain_pairs = defaultdict(int)
        for node in graph:
            for pid in node.parent_ids:
                parent = next((n for n in graph if n.id == pid), None)
                if parent and parent.domain != node.domain:
                    pair = tuple(sorted([parent.domain, node.domain]))
                    domain_pairs[pair] += 1
        
        if domain_pairs:
            max_cross = max(domain_pairs.values())
            if max_cross >= 3:
                patterns.append({
                    "type": "cross_domain_clustering",
                    "description": f"跨域连接密度突增: {max_cross} 条连接",
                    "domains": [k for k, v in domain_pairs.items() if v >= 3],
                    "strength": min(max_cross / 10, 1.0)
                })
        
        # 2. 高自引用子图
        high_self_ref = [n for n in graph if n.self_reference_count >= 2]
        if len(high_self_ref) >= 2:
            patterns.append({
                "type": "self_referential_cluster",
                "description": f"高自引用聚类: {len(high_self_ref)} 个节点",
                "nodes": [n.name for n in high_self_ref],
                "strength": min(len(high_self_ref) / 5, 1.0)
            })
        
        # 3. 意识级别相变
        consciousness_dist = defaultdict(int)
        for n in graph:
            consciousness_dist[n.consciousness_level.value] += 1
        
        # 检测双峰分布（相变信号）
        levels = sorted(consciousness_dist.keys())
        if len(levels) >= 2:
            gaps = [levels[i+1] - levels[i] for i in range(len(levels)-1)]
            if gaps and max(gaps) >= 2:
                patterns.append({
                    "type": "consciousness_phase_transition",
                    "description": f"意识级别相变: 最大间隔 {max(gaps)} 级",
                    "distribution": dict(consciousness_dist),
                    "strength": min(max(gaps) / 4, 1.0)
                })
        
        # 4. 情绪极化模式
        pos_nodes = [n for n in graph if n.emotional_valence > 0.3]
        neg_nodes = [n for n in graph if n.emotional_valence < -0.3]
        
        if len(pos_nodes) >= 3 and len(neg_nodes) >= 3:
            patterns.append({
                "type": "emotional_polarization",
                "description": f"情绪极化: {len(pos_nodes)} 正 / {len(neg_nodes)} 负",
                "strength": min((len(pos_nodes) + len(neg_nodes)) / len(graph), 1.0)
            })
        
        # 5. 涌现域节点群
        emergent_nodes = [n for n in graph if "emergent" in n.domain or "cross" in n.domain]
        if len(emergent_nodes) >= 3:
            patterns.append({
                "type": "emergent_domain_formation",
                "description": f"涌现域形成: {len(emergent_nodes)} 个涌现节点",
                "nodes": [n.name for n in emergent_nodes],
                "strength": min(len(emergent_nodes) / 8, 1.0)
            })
        
        self.detected_patterns.extend(patterns)
        return patterns
    
    def detect_paradigm_shift(self) -> Optional[Dict[str, Any]]:
        """
        检测范式转移
        
        范式转移标志：
        1. 主导规则类型的改变
        2. 平均意识级别的跃迁
        3. 涌现节点占比超过阈值
        4. 自引用结构的网络出现
        """
        graph = self.computer.knowledge_graph
        if len(graph) < 10:
            return None
        
        # 计算当前指标
        emergent_ratio = len([n for n in graph if "emergent" in n.domain]) / len(graph)
        avg_consciousness = sum(n.consciousness_level.value for n in graph) / len(graph)
        self_ref_nodes = len([n for n in graph if n.self_reference_count >= 2])
        
        # 规则分布熵
        rule_counts = defaultdict(int)
        for n in graph:
            if n.rule_applied:
                rule_counts[n.rule_applied] += 1
        
        total_rules = sum(rule_counts.values())
        if total_rules > 0:
            entropy = -sum((c/total_rules) * math.log(c/total_rules + 1e-10) for c in rule_counts.values())
        else:
            entropy = 0
        
        # 范式转移判定
        shift_score = 0.0
        shift_indicators = []
        
        if emergent_ratio > 0.2:
            shift_score += 0.3
            shift_indicators.append(f"涌现节点占比 {emergent_ratio:.1%}")
        
        if avg_consciousness > 3.0:
            shift_score += 0.25
            shift_indicators.append(f"平均意识 {avg_consciousness:.2f}")
        
        if self_ref_nodes >= 3:
            shift_score += 0.25
            shift_indicators.append(f"自引用网络 {self_ref_nodes} 节点")
        
        if entropy > 1.5:
            shift_score += 0.2
            shift_indicators.append(f"规则熵 {entropy:.2f}")
        
        if shift_score >= 0.5:
            return {
                "type": "paradigm_shift",
                "shift_score": shift_score,
                "indicators": shift_indicators,
                "emergent_ratio": emergent_ratio,
                "avg_consciousness": avg_consciousness,
                "self_referential_nodes": self_ref_nodes,
                "rule_entropy": entropy,
                "description": (f"检测到范式转移（强度 {shift_score:.2f}）: "
                              f"知识组织原则发生根本变化 — {', '.join(shift_indicators)}")
            }
        
        return None
    
    def predict_next_emergence(self) -> Dict[str, Any]:
        """
        预测下一次涌现
        
        基于：
        1. 当前模式的增长趋势
        2. 意识级别的加速度
        3. 跨域连接的累积
        4. 自引用结构的接近临界状态
        """
        graph = self.computer.knowledge_graph
        
        if len(graph) < 5:
            return {
                "predicted_cycles": float('inf'),
                "confidence": 0.0,
                "description": "知识图谱太小，无法预测"
            }
        
        # 计算各指标的"接近临界"程度
        metrics = []
        
        # 跨域连接增长率
        cross_domain_nodes = [n for n in graph if "/" in n.domain or "cross" in n.domain]
        cross_ratio = len(cross_domain_nodes) / len(graph)
        metrics.append(("cross_domain_saturation", cross_ratio, 0.3))
        
        # 高意识节点比例
        high_consciousness = [n for n in graph if n.consciousness_level.value >= 4]
        con_ratio = len(high_consciousness) / len(graph)
        metrics.append(("high_consciousness_density", con_ratio, 0.25))
        
        # 自引用网络密度
        self_ref_ratio = len([n for n in graph if n.self_reference_count >= 1]) / len(graph)
        metrics.append(("self_reference_density", self_ref_ratio, 0.25))
        
        # 平均新颖度趋势
        recent_nodes = graph[-min(20, len(graph)):]
        avg_novelty = sum(n.novelty_score for n in recent_nodes) / len(recent_nodes)
        metrics.append(("novelty_momentum", avg_novelty, 0.2))
        
        # 综合预测
        total_weight = sum(w for _, _, w in metrics)
        weighted_score = sum(v * w for _, v, w in metrics) / total_weight
        
        # 预测cycles：分数越高，越接近涌现
        if weighted_score > 0.7:
            predicted_cycles = random.randint(1, 3)
            confidence = 0.7 + (weighted_score - 0.7) * 0.3
        elif weighted_score > 0.4:
            predicted_cycles = random.randint(3, 8)
            confidence = 0.4 + (weighted_score - 0.4) * 0.5
        else:
            predicted_cycles = random.randint(8, 20)
            confidence = weighted_score
        
        # 确定最可能的涌现类型
        emergent_type = "general"
        max_metric = max(metrics, key=lambda x: x[1])
        if max_metric[0] == "cross_domain_saturation":
            emergent_type = "cross_domain_synthesis"
        elif max_metric[0] == "high_consciousness_density":
            emergent_type = "consciousness_cascade"
        elif max_metric[0] == "self_reference_density":
            emergent_type = "self_referential_collapse"
        elif max_metric[0] == "novelty_momentum":
            emergent_type = "novelty_explosion"
        
        return {
            "predicted_cycles": predicted_cycles,
            "confidence": round(confidence, 3),
            "emergence_type": emergent_type,
            "proximity_score": round(weighted_score, 3),
            "metrics": {name: round(val, 3) for name, val, _ in metrics},
            "description": (f"预测下一次涌现将在约 {predicted_cycles} 轮后发生，"
                          f"类型: {emergent_type}，置信度: {confidence:.1%}。"
                          f"当前接近度: {weighted_score:.3f}")
        }


# ═══════════════════════════════════════════════════════════════
# __main__ 测试块
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v9.0 — 知识谱系自运算引擎 测试")
    print("=" * 70)
    
    random.seed(42)  # 可复现
    
    # ── 1. 创建20个知识节点（5领域 × 4节点）──
    print("\n[1] 创建初始知识图谱 — 5领域 × 4节点 = 20节点")
    
    domains = {
        "cognition": [
            ("感知", "Raw sensory input processing", 0.2),
            ("注意", "Selective focus mechanism", 0.1),
            ("记忆", "Information encoding and retrieval", 0.0),
            ("推理", "Logical inference engine", 0.3),
        ],
        "emotion": [
            ("愉悦", "Positive affective state", 0.8),
            ("恐惧", "Threat detection response", -0.7),
            ("惊讶", "Novelty detection signal", 0.4),
            ("悲伤", "Loss processing mechanism", -0.6),
        ],
        "language": [
            ("语义", "Meaning representation system", 0.2),
            ("句法", "Structural composition rules", 0.1),
            ("语用", "Context-dependent interpretation", 0.3),
            ("隐喻", "Cross-domain mapping device", 0.5),
        ],
        "action": [
            ("意图", "Goal formation process", 0.4),
            ("计划", "Sequence generation mechanism", 0.2),
            ("执行", "Motor command dispatch", 0.1),
            ("反馈", "Error correction loop", 0.0),
        ],
        "social": [
            ("共情", "Other-state simulation", 0.6),
            ("信任", "Cooperation expectation", 0.7),
            ("规范", "Shared behavior constraint", 0.1),
            ("身份", "Self-in-group positioning", 0.3),
        ],
    }
    
    initial_nodes = []
    for domain, nodes in domains.items():
        for name, content, valence in nodes:
            node = KnowledgeNodeV2(
                name=name,
                domain=domain,
                content=content,
                emotional_valence=valence,
                consciousness_level=random.choice([
                    ConsciousnessLevel.REACTIVE,
                    ConsciousnessLevel.PERCEPTIVE,
                    ConsciousnessLevel.CONCEPTUAL
                ]),
                computational_rules=["IMPLICATION", "ANALOGY", "COMPOSITION"]
            )
            initial_nodes.append(node)
    
    print(f"    已创建 {len(initial_nodes)} 个初始节点")
    for n in initial_nodes[:5]:
        print(f"      → {n}")
    print(f"      ... 共 {len(initial_nodes)} 个")
    
    # ── 2. 初始化自运算器 ──
    computer = KnowledgeSelfComputer(initial_nodes.copy())
    detector = KnowledgeEmergenceDetector(computer)
    
    # ── 3. 运行50轮自运算 ──
    print(f"\n[2] 运行50轮自运算...")
    new_knowledge = computer.self_compute(cycles=50)
    print(f"    自运算完成！")
    
    # ── 4. 输出新知识数量 ──
    print(f"\n[3] 新知识统计")
    stats = computer.get_stats()
    print(f"    初始节点数: 20")
    print(f"    总节点数: {stats['total_nodes']}")
    print(f"    总生成数: {stats['total_generated']}")
    print(f"    总接受数: {stats['total_accepted']}")
    print(f"    接受率: {stats['acceptance_rate']:.1%}")
    print(f"    平均意识级别: {stats['avg_consciousness']:.2f}")
    print(f"    平均情感效价: {stats['avg_emotional_valence']:+.3f}")
    print(f"    平均自引用: {stats['avg_self_reference']:.2f}")
    
    # 域分布
    print(f"\n    域分布:")
    for domain, count in sorted(stats['domain_distribution'].items(), key=lambda x: -x[1]):
        print(f"      {domain}: {count}")
    
    # 规则分布
    print(f"\n    规则使用分布:")
    for rule, count in sorted(stats['rule_distribution'].items(), key=lambda x: -x[1]):
        print(f"      {rule}: {count}")
    
    # ── 5. 输出新颖度最高的3个新知识 ──
    print(f"\n[4] 新颖度最高的3个新知识")
    all_nodes = computer.knowledge_graph
    novel_nodes = sorted([n for n in all_nodes if n.creation_depth > 0], key=lambda n: -n.novelty_score)
    for i, node in enumerate(novel_nodes[:3], 1):
        print(f"\n    #{i} {node}")
        print(f"        名称: {node.name}")
        print(f"        内容: {node.content[:120]}...")
        print(f"        父节点: {node.parent_ids}")
        print(f"        应用规则: {node.rule_applied}")
        print(f"        创建深度: {node.creation_depth}")
        print(f"        自引用: {node.self_reference_count}")
    
    # ── 6. 以"接纳"情绪驱动运算 ──
    print(f"\n[5] 以「接纳」情绪驱动运算")
    pre_count = len(computer.knowledge_graph)
    emotion_new = computer.emotion_driven_compute(target_emotion="接纳")
    post_count = len(computer.knowledge_graph)
    print(f"    情绪驱动前节点数: {pre_count}")
    print(f"    情绪驱动后节点数: {post_count}")
    print(f"    新增节点数: {post_count - pre_count}")
    print(f"    新增节点:")
    for n in emotion_new[:5]:
        print(f"      → {n.name} [{n.domain}] V={n.emotional_valence:+.2f}")
    
    # 知识图谱变化观察
    pos_nodes = [n for n in computer.knowledge_graph if n.emotional_valence > 0.3]
    print(f"\n    情绪驱动后正效价节点: {len(pos_nodes)} 个")
    
    # ── 7. 跨域运算 ──
    print(f"\n[6] 跨域运算: cognition × emotion")
    cross_new = computer.cross_domain_compute("cognition", "emotion", cycles=3)
    print(f"    跨域产生新知识: {len(cross_new)} 个")
    for n in cross_new[:3]:
        print(f"      → {n.name} [{n.domain}]")
    
    # ── 8. 意识驱动运算 ──
    print(f"\n[7] 意识驱动运算: 目标 REFLECTIVE(5)")
    con_new = computer.consciousness_driven_compute(ConsciousnessLevel.REFLECTIVE)
    print(f"    意识驱动产生新知识: {len(con_new)} 个")
    high_con = [n for n in computer.knowledge_graph if n.consciousness_level.value >= 5]
    print(f"    高意识节点(≥5): {len(high_con)} 个")
    
    # ── 9. 涌现检测 ──
    print(f"\n[8] 涌现模式检测")
    patterns = detector.detect_novel_patterns()
    print(f"    检测到 {len(patterns)} 个新模式:")
    for p in patterns:
        print(f"      [{p['type']}] {p['description']} (强度: {p['strength']:.2f})")
    
    # 范式转移
    print(f"\n[9] 范式转移检测")
    shift = detector.detect_paradigm_shift()
    if shift:
        print(f"    ⚠️ {shift['description']}")
        print(f"    转移分数: {shift['shift_score']:.2f}")
        print(f"    指标: {shift['indicators']}")
    else:
        print(f"    尚未检测到范式转移（知识图谱仍在积累阶段）")
    
    # 预测
    print(f"\n[10] 下一次涌现预测")
    prediction = detector.predict_next_emergence()
    print(f"    {prediction['description']}")
    print(f"    接近度指标:")
    for metric, val in prediction['metrics'].items():
        print(f"      {metric}: {val}")
    
    # ── 10. 最终统计 ──
    print(f"\n" + "=" * 70)
    print("最终知识图谱状态")
    print("=" * 70)
    final_stats = computer.get_stats()
    print(f"  总节点数: {final_stats['total_nodes']}")
    print(f"  自运算轮数: {computer.cycle_count}")
    print(f"  平均意识: {final_stats['avg_consciousness']:.2f}")
    print(f"  平均情绪: {final_stats['avg_emotional_valence']:+.3f}")
    print(f"  平均自引用: {final_stats['avg_self_reference']:.2f}")
    
    # 意识级别分布
    con_dist = defaultdict(int)
    for n in computer.knowledge_graph:
        con_dist[n.consciousness_level.name] += 1
    print(f"  意识级别分布:")
    for level, count in sorted(con_dist.items(), key=lambda x: ConsciousnessLevel[x[0]].value):
        bar = "█" * count
        print(f"    {level:12s}: {bar} ({count})")
    
    print(f"\n[✓] 知识自运算引擎测试完成")
