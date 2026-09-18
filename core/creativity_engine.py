
__version__ = "11.0.0"
"""
OMNI-HUB v5.0 CreativityEngine
===============================
创造力引擎 — 基于预测加工理论和认知创造力模型

核心命题：创造力是生成模型的受控幻觉扩展——系统主动生成预测误差，
然后整合这些"意外"形成新观念。

理论基础：
- 预测加工理论 (Predictive Processing): 大脑是层级预测机器
- 认知创造力模型: 远距离联想 + 组合创新 + 类比推理
- 发散思维 ↔ 收敛思维的辩证循环
"""

import numpy as np
import uuid
import time
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable, Any
from collections import defaultdict
import json
from datetime import datetime
import logging


# =============================================================================
# 创造物类 — 记录每次创造的结果
# =============================================================================
@dataclass
class Creation:
    """创造物：记录创意产出的数据结构"""
    id: str
    type: str  # association / combination / metaphor / analogy / divergent
    content: str
    novelty: float  # 0-1
    value: float  # 0-1
    line_source: List[int]  # 源自哪些线（OMNI-HUB的11条线）
    timestamp: float
    components: List[str] = field(default_factory=list)  # 组成元素
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        # 处理numpy类型
        def clean(val):
            if isinstance(val, np.ndarray):
                return val.tolist()
            if isinstance(val, (np.bool_, np.int64, np.int32, np.float64, np.float32)):
                return val.item()
            if isinstance(val, dict):
                return {k: clean(v) for k, v in val.items()}
            if isinstance(val, list):
                return [clean(v) for v in val]
            return val
        
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'novelty': round(float(self.novelty), 4),
            'value': round(float(self.value), 4),
            'line_source': [int(x) for x in self.line_source],
            'timestamp': float(self.timestamp),
            'components': [str(c) for c in self.components],
            'metadata': clean(self.metadata)
        }


# =============================================================================
# 概念空间类 — 向量空间中的概念表示与操作
# =============================================================================
class ConceptSpace:
    """
    概念空间：高维向量空间中的概念表示
    
    每个概念是一个向量，语义距离 = 向量间距离
    远距离联想 = 找到距离大但结构相似的概念对
    """
    
    def __init__(self, dim: int = 64, seed: int = 42):
        self.dim = dim
        self.concepts: Dict[str, np.ndarray] = {}
        self.concept_categories: Dict[str, str] = {}  # 概念 -> 类别
        self.rng = np.random.RandomState(seed)
        
        # 初始化默认概念库（跨多个领域）
        self._init_default_concepts()
    
    def _init_default_concepts(self):
        """初始化跨领域概念库"""
        domains = {
            '数学': ['张量场', '流形', '奇异点', '拓扑', '分形', '混沌', '对偶性', '纤维丛'],
            '音乐': ['对位法', '赋格', '主题', '变奏', '不和谐音', '休止', '复调', '十二音'],
            '物理': ['量子纠缠', '熵增', '相变', '场论', '自组织', '涌现', '对称性破缺', '测不准'],
            '生物': ['基因调控', '神经网络', '演化', '适应', '代谢', '共生', '自复制', '形态发生'],
            '社会': ['网络效应', '集体智慧', '制度变迁', '文化模因', '权力结构', '社会资本', '信任机制'],
            '认知': ['注意力', '工作记忆', '直觉', '元认知', '表征', '图式', '心理模型', '具身认知'],
            '计算机': ['递归', '并行计算', '神经网络', '区块链', '虚拟机', '编译器', '哈希', '图灵机'],
            '哲学': ['存在', '时间性', '他者', '虚无', '差异', '重复', '生成', '解构']
        }
        
        # 为每个领域生成聚类向量
        for domain, concepts in domains.items():
            # 每个领域有一个中心方向
            center = self.rng.randn(self.dim)
            center = center / (np.linalg.norm(center) + 1e-8)
            
            for concept in concepts:
                # 概念向量 = 领域中心 + 随机扰动
                noise = self.rng.randn(self.dim) * 0.3
                vec = center + noise
                vec = vec / (np.linalg.norm(vec) + 1e-8)
                self.add_concept(concept, vec, domain)
    
    def add_concept(self, name: str, vector: np.ndarray, category: str = 'general'):
        """添加概念到空间"""
        if isinstance(vector, list):
            vector = np.array(vector, dtype=np.float64)
        vector = vector / (np.linalg.norm(vector) + 1e-8)
        self.concepts[name] = vector
        self.concept_categories[name] = category
    
    def get_vector(self, name: str) -> np.ndarray:
        """获取概念向量"""
        if name not in self.concepts:
            # 未知概念：生成随机但确定性的向量
            hash_val = abs(hash(name)) % (2**31)
            rng = np.random.RandomState(hash_val)
            vec = rng.randn(self.dim)
            vec = vec / (np.linalg.norm(vec) + 1e-8)
            self.add_concept(name, vec, 'unknown')
        return self.concepts[name]
    
    def distance(self, c1: str, c2: str) -> float:
        """计算两个概念间的语义距离 (0-2, 越大越远)"""
        v1 = self.get_vector(c1)
        v2 = self.get_vector(c2)
        # 余弦距离 = 1 - 余弦相似度
        cos_sim = np.dot(v1, v2)
        return float(1 - cos_sim)
    
    def get_neighbors(self, concept: str, k: int = 5) -> List[Tuple[str, float]]:
        """获取k个最近邻概念"""
        distances = []
        for other in self.concepts:
            if other != concept:
                d = self.distance(concept, other)
                distances.append((other, d))
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    def get_distant_pairs(self, threshold: float = 1.2, max_pairs: int = 50) -> List[Tuple[str, str, float]]:
        """获取远距离概念对（跨领域联想的基础）"""
        pairs = []
        concepts = list(self.concepts.keys())
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                d = self.distance(c1, c2)
                if d > threshold:
                    # 优先返回跨领域的远距离对
                    cat1 = self.concept_categories.get(c1, '')
                    cat2 = self.concept_categories.get(c2, '')
                    bonus = 0.2 if cat1 != cat2 else 0
                    pairs.append((c1, c2, d + bonus))
        pairs.sort(key=lambda x: x[2], reverse=True)
        return pairs[:max_pairs]
    
    def get_all_concepts(self) -> List[str]:
        return list(self.concepts.keys())
    
    def get_category(self, concept: str) -> str:
        return self.concept_categories.get(concept, 'unknown')
    
    def get_concepts_by_category(self, category: str) -> List[str]:
        """获取某类别的所有概念"""
        return [c for c, cat in self.concept_categories.items() if cat == category]


# =============================================================================
# 创造力引擎 — 核心类
# =============================================================================
class CreativityEngine:
    """
    CreativityEngine: OMNI-HUB v5.0 创造力引擎
    
    实现完整的创造循环：
    发散 → 酝酿 → 收敛 → 评估
    
    11条线的对位运动产生"意外"交集，这些交集是创造力的源泉。
    """
    
    def __init__(self, num_lines: int = 11, concept_dim: int = 64, seed: int = 42):
        self.num_lines = num_lines
        self.concept_space = ConceptSpace(dim=concept_dim, seed=seed)
        self.rng = np.random.RandomState(seed)
        
        # 创造物历史
        self.creations: List[Creation] = []
        self.creation_index: Dict[str, Creation] = {}
        
        # 系统状态：11条线的当前"概念"
        self.line_states: Dict[int, str] = {}
        self._init_line_states()
        
        # 评估历史（用于计算新颖度）
        self.known_patterns: set = set()
        self.component_history: List[set] = []  # 组件集合历史
        
        # 统计
        self.stats = {
            'total_cycles': 0,
            'creations_by_type': defaultdict(int),
            'avg_novelty_history': [],
            'avg_value_history': []
        }
    
    def _init_line_states(self):
        """初始化11条线的状态"""
        all_concepts = self.concept_space.get_all_concepts()
        for i in range(self.num_lines):
            self.line_states[i] = str(self.rng.choice(all_concepts))
    
    # =====================================================================
    # 1. 跨域联想 (Distant Association)
    # =====================================================================
    def associate_distant(self, concepts: Optional[List[str]] = None, 
                          distance_threshold: float = 1.2) -> List[Creation]:
        """
        跨域联想：找到远距离但结构上有潜在关联的概念对
        """
        if concepts is None:
            concepts = [self.line_states[i] for i in range(self.num_lines)]
        
        creations = []
        pairs = []
        
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                d = self.concept_space.distance(c1, c2)
                if d > distance_threshold:
                    pairs.append((c1, c2, d))
        
        pairs.sort(key=lambda x: x[2], reverse=True)
        
        for c1, c2, dist in pairs[:5]:
            association = self._generate_association_text(c1, c2, dist)
            lines = self._find_lines_for_concepts([c1, c2])
            
            creation = Creation(
                id=str(uuid.uuid4())[:8],
                type='association',
                content=association,
                novelty=min(dist / 2.0, 1.0),
                value=self._compute_association_value(c1, c2),
                line_source=lines,
                timestamp=time.time(),
                components=[c1, c2],
                metadata={'distance': float(dist)}
            )
            creations.append(creation)
        
        return creations
    
    def _generate_association_text(self, c1: str, c2: str, dist: float) -> str:
        """生成联想描述文本"""
        templates = [
            f"{c1}与{c2}的深层同构：二者在结构层面共享某种未言明的秩序",
            f"将{c1}的张力注入{c2}的框架，产生跨域共振",
            f"{c1}的拓扑在{c2}的介质中展开，形成意外的对称",
            f"当{c1}遇见{c2}：预测误差的爆炸性耦合",
            f"{c1}作为{c2}的隐喻基底，揭示隐藏的结构映射",
            f"从{c1}到{c2}的远程跳跃：概念空间的量子隧穿"
        ]
        return self.rng.choice(templates)
    
    def _compute_association_value(self, c1: str, c2: str) -> float:
        """计算联想对系统的价值"""
        cat1 = self.concept_space.get_category(c1)
        cat2 = self.concept_space.get_category(c2)
        
        cross_domain_bonus = 0.3 if cat1 != cat2 else 0.0
        neighbors1 = len(self.concept_space.get_neighbors(c1, k=10))
        neighbors2 = len(self.concept_space.get_neighbors(c2, k=10))
        connectivity = (neighbors1 + neighbors2) / 20.0
        
        return min(0.4 + cross_domain_bonus + connectivity * 0.3, 1.0)
    
    # =====================================================================
    # 2. 组合创新 (Combinatorial Innovation)
    # =====================================================================
    def combine_elements(self, elements: Optional[List[str]] = None,
                         num_combinations: int = 5) -> List[Creation]:
        """
        组合创新：已有元素的重新组合
        """
        if elements is None:
            line_concepts = [self.line_states[i] for i in range(self.num_lines)]
            extra = self.rng.choice(self.concept_space.get_all_concepts(), 
                                   size=10, replace=False).tolist()
            elements = list(set(line_concepts + extra))
        
        creations = []
        for _ in range(num_combinations):
            k = self.rng.randint(2, min(5, len(elements) + 1))
            combo = [str(c) for c in self.rng.choice(elements, size=k, replace=False)]
            combo = [str(c) for c in combo]  # 确保是字符串
            combo_key = tuple(sorted(combo))
            
            is_new = combo_key not in self.known_patterns
            if is_new:
                self.known_patterns.add(combo_key)
            
            content = self._generate_combination_text(combo)
            novelty = self._compute_combination_novelty(combo, is_new)
            value = self._compute_combination_value(combo)
            lines = self._find_lines_for_concepts(combo)
            
            creation = Creation(
                id=str(uuid.uuid4())[:8],
                type='combination',
                content=content,
                novelty=novelty,
                value=value,
                line_source=lines,
                timestamp=time.time(),
                components=combo,
                metadata={'is_new_pattern': bool(is_new), 'num_elements': k}
            )
            creations.append(creation)
        
        return creations
    
    def _generate_combination_text(self, combo: List[str]) -> str:
        """生成组合描述"""
        if len(combo) == 2:
            templates = [
                f"{combo[0]} × {combo[1]} 的耦合系统",
                f"在{combo[0]}的拓扑中嵌入{combo[1]}的动力学",
                f"{combo[0]}与{combo[1]}的异质共生"
            ]
        elif len(combo) == 3:
            templates = [
                f"{combo[0]} → {combo[1]} → {combo[2]} 的循环涌现",
                f"由{combo[0]}、{combo[1]}和{combo[2]}构成的三重奏",
                f"{combo[0]}的基质中，{combo[1]}与{combo[2]}的复调"
            ]
        else:
            joined = ' · '.join(combo)
            templates = [
                f"多元素复合体 [{joined}] 的协同涌现",
                f"在{joined}的交叉点上生成的新结构"
            ]
        return self.rng.choice(templates)
    
    def _compute_combination_novelty(self, combo: List[str], is_new: bool) -> float:
        """计算组合的新颖度"""
        total_dist = 0
        count = 0
        for i, c1 in enumerate(combo):
            for c2 in combo[i+1:]:
                total_dist += self.concept_space.distance(str(c1), str(c2))
                count += 1
        avg_dist = total_dist / max(count, 1)
        
        novelty = min(avg_dist / 1.5, 1.0)
        if is_new:
            novelty = min(novelty * 1.2 + 0.1, 1.0)
        return novelty
    
    def _compute_combination_value(self, combo: List[str]) -> float:
        """计算组合的价值"""
        categories = [self.concept_space.get_category(str(c)) for c in combo]
        unique_cats = len(set(categories))
        diversity_bonus = unique_cats / max(len(combo), 1) * 0.4
        size_score = 1.0 - abs(len(combo) - 3) * 0.1
        return min(0.3 + diversity_bonus + size_score * 0.3, 1.0)
    
    # =====================================================================
    # 3. 隐喻生成 (Metaphor Generation)
    # =====================================================================
    def generate_metaphor(self, source_domain: str, target_domain: str) -> Creation:
        """
        隐喻生成：跨模态/跨域映射
        """
        source_concepts = self.concept_space.get_concepts_by_category(source_domain)
        target_concepts = self.concept_space.get_concepts_by_category(target_domain)
        
        if not source_concepts:
            source_concepts = self.concept_space.get_all_concepts()
        if not target_concepts:
            target_concepts = self.concept_space.get_all_concepts()
        
        best_pair = None
        best_score = -1
        
        for sc in source_concepts[:10]:
            for tc in target_concepts[:10]:
                sc_neighbors = set([n[0] for n in self.concept_space.get_neighbors(sc, k=5)])
                tc_neighbors = set([n[0] for n in self.concept_space.get_neighbors(tc, k=5)])
                overlap = len(sc_neighbors & tc_neighbors)
                surface_dist = self.concept_space.distance(sc, tc)
                score = overlap * 0.3 + surface_dist * 0.7
                if score > best_score:
                    best_score = score
                    best_pair = (sc, tc)
        
        if best_pair is None:
            best_pair = (str(self.rng.choice(source_concepts)), 
                        str(self.rng.choice(target_concepts)))
        
        sc, tc = best_pair
        content = self._generate_metaphor_text(sc, tc, source_domain, target_domain)
        novelty = self.concept_space.distance(sc, tc) / 2.0
        value = 0.5 + best_score * 0.3
        lines = self._find_lines_for_concepts([sc, tc])
        
        creation = Creation(
            id=str(uuid.uuid4())[:8],
            type='metaphor',
            content=content,
            novelty=min(novelty, 1.0),
            value=min(value, 1.0),
            line_source=lines,
            timestamp=time.time(),
            components=[sc, tc],
            metadata={
                'source_domain': source_domain,
                'target_domain': target_domain,
                'mapping': f'{sc} → {tc}'
            }
        )
        return creation
    
    def _generate_metaphor_text(self, sc: str, tc: str, s_domain: str, t_domain: str) -> str:
        """生成隐喻描述"""
        templates = [
            f"{s_domain}中的{sc}是{t_domain}中{tc}的隐喻："
            f"{sc}的结构动力学在{tc}的介质中获得了新的语义维度",
            f"将{sc}的生成逻辑映射到{tc}："
            f"源域的拓扑约束在目标域中转化为组织原则",
            f"{sc} → {tc} 的跨域隧穿："
            f"两个不可通约领域间的结构共振"
        ]
        return self.rng.choice(templates)
    
    # =====================================================================
    # 4. 类比推理 (Analogical Reasoning)
    # =====================================================================
    def analogical_reasoning(self, source_structure: List[str], 
                             target_domain: str) -> Creation:
        """
        类比推理：结构映射
        """
        if not source_structure:
            source_structure = [self.line_states[i] for i in range(3)]
        
        source_structure = [str(s) for s in source_structure]
        target_concepts = self.concept_space.get_concepts_by_category(target_domain)
        if not target_concepts:
            target_concepts = self.concept_space.get_all_concepts()
        
        mapping = {}
        used_targets = set()
        
        for src in source_structure:
            src_vec = self.concept_space.get_vector(src)
            best_match = None
            best_sim = -1
            
            for tgt in target_concepts:
                if tgt in used_targets:
                    continue
                tgt_vec = self.concept_space.get_vector(tgt)
                sim = np.dot(src_vec, tgt_vec)
                if sim > best_sim:
                    best_sim = sim
                    best_match = tgt
            
            if best_match:
                mapping[src] = best_match
                used_targets.add(best_match)
        
        content = self._generate_analogy_text(source_structure, mapping, target_domain)
        fidelity = self._compute_mapping_fidelity(source_structure, mapping)
        novelty = 1.0 - fidelity * 0.3
        value = fidelity * 0.6 + 0.3
        lines = self._find_lines_for_concepts(source_structure + list(mapping.values()))
        
        creation = Creation(
            id=str(uuid.uuid4())[:8],
            type='analogy',
            content=content,
            novelty=min(novelty, 1.0),
            value=min(value, 1.0),
            line_source=lines,
            timestamp=time.time(),
            components=source_structure + list(mapping.values()),
            metadata={
                'source_structure': source_structure,
                'mapping': mapping,
                'target_domain': target_domain,
                'fidelity': float(fidelity)
            }
        )
        return creation
    
    def _generate_analogy_text(self, src_struct: List[str], mapping: Dict[str, str],
                               target: str) -> str:
        """生成类比描述"""
        mappings = [f"{s} → {t}" for s, t in mapping.items()]
        mapping_str = ", ".join(mappings)
        
        templates = [
            f"结构映射 [{mapping_str}] 到{target}域："
            f"源结构的关系统律在目标域中获得保持",
            f"从源域到{target}的类比迁移："
            f"{mapping_str} 的对应关系揭示了深层同构",
            f"基于{mapping_str}的跨域推理："
            f"{target}中的现象可通过源结构获得解释"
        ]
        return self.rng.choice(templates)
    
    def _compute_mapping_fidelity(self, src: List[str], mapping: Dict[str, str]) -> float:
        """计算映射的结构保真度"""
        if len(src) < 2 or len(mapping) < 2:
            return 0.5
        
        preserved = 0
        total = 0
        for i, s1 in enumerate(src):
            for s2 in src[i+1:]:
                if s1 in mapping and s2 in mapping:
                    d_src = self.concept_space.distance(s1, s2)
                    d_tgt = self.concept_space.distance(mapping[s1], mapping[s2])
                    diff = abs(d_src - d_tgt)
                    preserved += max(0, 1 - diff)
                    total += 1
        
        return preserved / max(total, 1)
    
    # =====================================================================
    # 5. 发散生成 (Divergent Generation)
    # =====================================================================
    def divergent_generate(self, seed: str, num_variants: int = 5) -> List[Creation]:
        """
        发散生成：基于种子概念生成多个变体
        """
        seed = str(seed)
        seed_vec = self.concept_space.get_vector(seed)
        creations = []
        
        # 策略1：在种子方向上延伸
        for i in range(num_variants // 2):
            direction = self.rng.randn(self.concept_space.dim)
            direction = direction / (np.linalg.norm(direction) + 1e-8)
            new_vec = seed_vec + direction * (0.3 + self.rng.rand() * 0.7)
            new_vec = new_vec / (np.linalg.norm(new_vec) + 1e-8)
            
            nearest = self._find_nearest_concept(new_vec, exclude=[seed])
            dist = self.concept_space.distance(seed, nearest)
            content = f"从{seed}发散：沿向量方向{i}延伸至{nearest}"
            
            creation = Creation(
                id=str(uuid.uuid4())[:8],
                type='divergent',
                content=content,
                novelty=min(dist / 1.5 + 0.3, 1.0),
                value=0.3 + self.rng.rand() * 0.4,
                line_source=[i % self.num_lines],
                timestamp=time.time(),
                components=[seed, nearest],
                metadata={'strategy': 'vector_extension'}
            )
            creations.append(creation)
        
        # 策略2：与远距离概念组合
        distant = self.concept_space.get_distant_pairs(threshold=1.0, max_pairs=20)
        related_distant = [p for p in distant if seed in [p[0], p[1]]]
        
        for i in range(num_variants // 2):
            if related_distant and i < len(related_distant):
                pair = related_distant[i]
                other = pair[1] if pair[0] == seed else pair[0]
            else:
                other = str(self.rng.choice(self.concept_space.get_all_concepts()))
            
            content = f"{seed}与{other}的异质杂交：预测误差的创造性整合"
            dist = self.concept_space.distance(seed, other)
            
            creation = Creation(
                id=str(uuid.uuid4())[:8],
                type='divergent',
                content=content,
                novelty=min(dist / 1.5 + 0.2, 1.0),
                value=0.4 + dist * 0.2,
                line_source=[(i + 5) % self.num_lines],
                timestamp=time.time(),
                components=[seed, other],
                metadata={'strategy': 'distant_hybrid'}
            )
            creations.append(creation)
        
        return creations
    
    def _find_nearest_concept(self, vector: np.ndarray, exclude: List[str] = None) -> str:
        """找到最接近给定向量的概念"""
        exclude = exclude or []
        best = None
        best_sim = -1
        for name, vec in self.concept_space.concepts.items():
            if name in exclude:
                continue
            sim = np.dot(vector, vec)
            if sim > best_sim:
                best_sim = sim
                best = name
        return best or "未知概念"
    
    # =====================================================================
    # 6. 收敛选择 (Convergent Selection)
    # =====================================================================
    def convergent_select(self, variants: List[Creation], 
                          criteria: Optional[Dict[str, float]] = None) -> List[Creation]:
        """
        收敛选择：基于标准选择最佳变体
        """
        if criteria is None:
            criteria = {'novelty': 0.4, 'value': 0.4, 'surprise': 0.2}
        
        def score(creation: Creation) -> float:
            s = 0
            for key, weight in criteria.items():
                if key == 'novelty':
                    s += creation.novelty * weight
                elif key == 'value':
                    s += creation.value * weight
                elif key == 'surprise':
                    s += (creation.novelty * creation.value) * weight
            return s
        
        scored = [(c, score(c)) for c in variants]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        n_select = max(1, int(len(scored) * 0.4))
        return [c for c, _ in scored[:n_select]]
    
    # =====================================================================
    # 7. 新颖度评估 (Novelty Score) - 修复版
    # =====================================================================
    def novelty_score(self, creation: Creation) -> float:
        """
        评估创造物的新颖度 - 基于概念组合独特性
        
        避免文本字符集相似度的问题，改用：
        1. 组件组合是否首次出现
        2. 组件间概念距离
        3. 与历史中组件集合的Jaccard距离
        """
        scores = []
        
        # 1. 组件组合独特性
        if creation.components:
            comp_key = tuple(sorted([str(c) for c in creation.components]))
            is_unique_combo = comp_key not in self.known_patterns
            scores.append(1.0 if is_unique_combo else 0.3)
        
        # 2. 组件间概念距离（越远越新颖）
        if creation.components and len(creation.components) >= 2:
            total_dist = 0
            count = 0
            comps = [str(c) for c in creation.components]
            for i, c1 in enumerate(comps):
                for c2 in comps[i+1:]:
                    total_dist += self.concept_space.distance(c1, c2)
                    count += 1
            avg_dist = total_dist / max(count, 1)
            scores.append(min(avg_dist / 1.5, 1.0))
        
        # 3. 与历史中组件集合的Jaccard距离
        if creation.components and self.component_history:
            current_set = set([str(c) for c in creation.components])
            max_overlap = 0
            for hist_set in self.component_history[-20:]:
                intersection = len(current_set & hist_set)
                union = len(current_set | hist_set)
                overlap = intersection / max(union, 1)
                max_overlap = max(max_overlap, overlap)
            scores.append(1.0 - max_overlap)
        
        # 4. 类型新颖度（少见的类型更新颖）
        type_count = self.stats['creations_by_type'][creation.type]
        if self.stats['total_cycles'] > 0:
            type_freq = type_count / max(self.stats['total_cycles'] * 3, 1)
            scores.append(1.0 - min(type_freq, 1.0))
        
        return float(np.mean(scores)) if scores else 0.5
    
    # =====================================================================
    # 8. 价值评估 (Value Score)
    # =====================================================================
    def value_score(self, creation: Creation) -> float:
        """
        评估创造物的价值
        """
        scores = []
        
        # 跨领域连接价值
        if creation.components:
            cats = [self.concept_space.get_category(str(c)) for c in creation.components]
            unique_cats = len(set(cats))
            scores.append(unique_cats / max(len(cats), 1))
        
        # 结构复杂性价值
        if creation.type == 'analogy':
            fidelity = creation.metadata.get('fidelity', 0.5)
            scores.append(fidelity)
        
        # 新颖度与价值的平衡（最佳点在0.6）
        balance = 1.0 - abs(creation.novelty - 0.6) * 1.5
        scores.append(max(balance, 0))
        
        # 来源线多样性
        line_diversity = len(set(creation.line_source)) / max(len(creation.line_source), 1)
        scores.append(line_diversity)
        
        return float(np.mean(scores)) if scores else 0.5
    
    # =====================================================================
    # 9. 完整创造循环 (Creative Cycle)
    # =====================================================================
    def creative_cycle(self, seed: Optional[str] = None) -> List[Creation]:
        """
        完整创造循环：
        1. 发散阶段：生成远距离联想和随机组合
        2. 酝酿阶段：让组合在"无意识"中发酵
        3. 收敛阶段：选择新颖度和价值最高的组合
        4. 评估阶段：计算创造物的涌现潜力
        5. 输出创造物
        """
        self.stats['total_cycles'] += 1
        
        if seed is None:
            seed = str(self.rng.choice(self.concept_space.get_all_concepts()))
        seed = str(seed)
        
        all_creations = []
        
        # ---- 阶段1：发散 (Divergence) ----
        associations = self.associate_distant(distance_threshold=0.9)
        all_creations.extend(associations)
        
        combinations = self.combine_elements(num_combinations=5)
        all_creations.extend(combinations)
        
        divergent = self.divergent_generate(seed, num_variants=4)
        all_creations.extend(divergent)
        
        # 隐喻生成
        domains = list(set(self.concept_space.concept_categories.values()))
        if len(domains) >= 2:
            s_domain = self.rng.choice(domains)
            t_domain = self.rng.choice([d for d in domains if d != s_domain])
            metaphor = self.generate_metaphor(s_domain, t_domain)
            all_creations.append(metaphor)
        
        # 类比推理
        source_struct = [self.line_states[i] for i in range(3)]
        target = self.rng.choice(domains) if domains else 'general'
        analogy = self.analogical_reasoning(source_struct, target)
        all_creations.append(analogy)
        
        # ---- 阶段2：酝酿 (Incubation) ----
        incubated = self._incubation(all_creations)
        
        # ---- 阶段3：收敛 (Convergence) ----
        criteria = {'novelty': 0.35, 'value': 0.35, 'surprise': 0.3}
        selected = self.convergent_select(incubated, criteria)
        
        # 确保多样性：如果某种类型缺失，强制加入
        selected_types = set(c.type for c in selected)
        for c in incubated:
            if c.type not in selected_types and c.type in ['metaphor', 'analogy']:
                selected.append(c)
                selected_types.add(c.type)
        
        # ---- 阶段4：评估 (Evaluation) ----
        for creation in selected:
            # 重新评估新颖度和价值
            creation.novelty = self.novelty_score(creation)
            creation.value = self.value_score(creation)
            
            # 计算涌现潜力
            emergence = creation.novelty * creation.value
            creation.metadata['emergence_potential'] = float(emergence)
            
            # 保存到历史
            self.creations.append(creation)
            self.creation_index[creation.id] = creation
            self.stats['creations_by_type'][creation.type] += 1
            
            # 记录组件历史
            if creation.components:
                self.component_history.append(set([str(c) for c in creation.components]))
        
        # ---- 更新系统状态 ----
        for _ in range(3):
            line_idx = self.rng.randint(0, self.num_lines)
            if selected:
                new_concept = selected[0].components[0] if selected[0].components else seed
                self.line_states[line_idx] = str(new_concept)
        
        return selected
    
    def _incubation(self, creations: List[Creation]) -> List[Creation]:
        """
        酝酿阶段：无意识加工模拟
        """
        incubated = []
        
        for creation in creations:
            incubated.append(creation)
            
            # 以一定概率生成"突变"版本
            if self.rng.rand() < 0.3:
                mutated = self._mutate_creation(creation)
                if mutated:
                    incubated.append(mutated)
        
        return incubated
    
    def _mutate_creation(self, creation: Creation) -> Optional[Creation]:
        """对创造物进行概念突变"""
        if not creation.components:
            return None
        
        new_components = [str(c) for c in creation.components]
        idx = self.rng.randint(0, len(new_components))
        old = new_components[idx]
        
        # 找到远距离概念
        distant_pairs = self.concept_space.get_distant_pairs(threshold=1.1, max_pairs=20)
        candidates = [p[1] if p[0] == old else p[0] for p in distant_pairs if old in [p[0], p[1]]]
        
        if candidates:
            new_components[idx] = str(self.rng.choice(candidates))
            
            new_creation = Creation(
                id=str(uuid.uuid4())[:8],
                type=creation.type,
                content=f"[突变] {creation.content} → 替换{old}为{new_components[idx]}",
                novelty=min(creation.novelty * 1.2 + 0.1, 1.0),
                value=creation.value * 0.9,
                line_source=creation.line_source + [self.rng.randint(0, self.num_lines)],
                timestamp=time.time(),
                components=new_components,
                metadata={**creation.metadata, 'mutated': True, 'original_id': creation.id}
            )
            return new_creation
        
        return None
    
    def _find_lines_for_concepts(self, concepts: List[str]) -> List[int]:
        """找到包含这些概念的线"""
        lines = []
        for concept in concepts:
            for line, state in self.line_states.items():
                if state == concept and line not in lines:
                    lines.append(line)
        if not lines:
            lines = [self.rng.randint(0, self.num_lines)]
        return lines
    
    # =====================================================================
    # 统计与报告
    # =====================================================================
    def get_statistics(self) -> Dict:
        """获取创造力引擎统计信息"""
        if not self.creations:
            return {"error": "No creations yet"}
        
        recent = self.creations[-50:] if len(self.creations) > 50 else self.creations
        
        novelties = [c.novelty for c in recent]
        values = [c.value for c in recent]
        
        type_dist = defaultdict(int)
        for c in self.creations:
            type_dist[c.type] += 1
        
        # 跨领域统计
        cross_domain = 0
        for c in self.creations:
            if c.components:
                cats = [self.concept_space.get_category(str(comp)) for comp in c.components]
                if len(set(cats)) > 1:
                    cross_domain += 1
        
        return {
            'total_creations': len(self.creations),
            'total_cycles': self.stats['total_cycles'],
            'avg_novelty': float(np.mean(novelties)),
            'std_novelty': float(np.std(novelties)),
            'avg_value': float(np.mean(values)),
            'std_value': float(np.std(values)),
            'type_distribution': dict(type_dist),
            'cross_domain_ratio': cross_domain / max(len(self.creations), 1),
            'emergence_potential_avg': float(np.mean([c.metadata.get('emergence_potential', 0) 
                                                for c in recent]))
        }
    
    def print_report(self):
        """打印实验报告"""
        stats = self.get_statistics()
        logger.info("=" * 70)
        logger.info("OMNI-HUB v5.0 CreativityEngine 实验报告")
        logger.info("=" * 70)
        logger.info(f"\n[基础统计]")
        logger.info(f"  总创造循环: {stats['total_cycles']}")
        logger.info(f"  总创造物: {stats['total_creations']}")
        logger.info(f"\n[质量评估]")
        logger.info(f"  平均新颖度: {stats['avg_novelty']:.4f} (±{stats['std_novelty']:.4f})")
        logger.info(f"  平均价值: {stats['avg_value']:.4f} (±{stats['std_value']:.4f})")
        logger.info(f"  平均涌现潜力: {stats['emergence_potential_avg']:.4f}")
        logger.info(f"\n[类型分布]")
        for t, count in sorted(stats['type_distribution'].items(), key=lambda x: -x[1]):
            pct = count / stats['total_creations'] * 100
            logger.info(f"  {t:15s}: {count:3d} ({pct:5.1f}%)")
        logger.info(f"\n[跨领域创新]")
        logger.info(f"  跨领域创造占比: {stats['cross_domain_ratio']*100:.1f}%")
        logger.info(f"\n[代表性创造物]")
        top = sorted(self.creations, 
                    key=lambda c: c.novelty * c.value, reverse=True)[:5]
        for i, c in enumerate(top, 1):
            logger.info(f"\n  #{i} [{c.type}] (N={c.novelty:.3f}, V={c.value:.3f})")
            logger.info(f"      {c.content}")
            if c.components:
                logger.info(f"      组件: {c.components}")
        logger.info("\n" + "=" * 70)


# =============================================================================
# 实验验证
# =============================================================================
def run_experiment(num_cycles: int = 50, verbose: bool = True) -> Dict:
    """
    运行实验验证
    
    验证目标：
    1. 创造物确实"新颖"（与已有概念距离大）
    2. 创造物"有价值"（对系统目标有贡献）
    3. 11条线的交叉产生高质量创造
    4. 创造循环能持续产生涌现
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"OMNI-HUB v5.0 CreativityEngine 实验验证")
    logger.info(f"{'='*70}")
    logger.info(f"实验参数: {num_cycles} 个创造循环")
    logger.info(f"系统: 11条线, 64维概念空间, 跨8个领域")
    logger.info(f"{'='*70}\n")
    
    engine = CreativityEngine(num_lines=11, concept_dim=64, seed=42)
    
    cycle_results = []
    
    for cycle in range(num_cycles):
        seed = engine.rng.choice(engine.concept_space.get_all_concepts())
        creations = engine.creative_cycle(seed)
        
        cycle_results.append({
            'cycle': cycle + 1,
            'num_creations': len(creations),
            'avg_novelty': float(np.mean([c.novelty for c in creations])) if creations else 0,
            'avg_value': float(np.mean([c.value for c in creations])) if creations else 0,
            'types': [c.type for c in creations]
        })
        
        if verbose and (cycle + 1) % 10 == 0:
            stats = engine.get_statistics()
            print(f"Cycle {cycle+1:3d}: 总创造={stats['total_creations']:3d}, "
                  f"新颖度={stats['avg_novelty']:.3f}, 价值={stats['avg_value']:.3f}")
    
    # 最终报告
    engine.print_report()
    
    # 详细验证
    logger.info("\n[验证测试]")
    logger.info("-" * 50)
    
    # 验证1：新颖度是否确实高
    all_novelties = [c.novelty for c in engine.creations]
    avg_nov = float(np.mean(all_novelties))
    logger.info(f"1. 新颖度验证: 平均={avg_nov:.4f}")
    logger.info(f"   {'PASS' if avg_nov > 0.3 else 'FAIL'}: 新颖度 > 0.3")
    
    # 验证2：价值是否确实高
    all_values = [c.value for c in engine.creations]
    avg_val = float(np.mean(all_values))
    logger.info(f"2. 价值验证: 平均={avg_val:.4f}")
    logger.info(f"   {'PASS' if avg_val > 0.3 else 'FAIL'}: 价值 > 0.3")
    
    # 验证3：跨领域创造比例
    cross_count = sum(1 for c in engine.creations 
                      if len(set([engine.concept_space.get_category(str(comp)) 
                                  for comp in c.components])) > 1)
    cross_ratio = cross_count / max(len(engine.creations), 1)
    logger.info(f"3. 跨领域验证: 比例={cross_ratio*100:.1f}%")
    logger.info(f"   {'PASS' if cross_ratio > 0.2 else 'FAIL'}: 跨领域 > 20%")
    
    # 验证4：创造物数量
    total = len(engine.creations)
    logger.info(f"4. 产出验证: 总创造物={total}")
    logger.info(f"   {'PASS' if total > num_cycles else 'FAIL'}: 产出 > 循环数")
    
    # 验证5：涌现潜力
    emergence_scores = [c.metadata.get('emergence_potential', 0) for c in engine.creations]
    avg_emergence = float(np.mean(emergence_scores))
    logger.info(f"5. 涌现验证: 平均潜力={avg_emergence:.4f}")
    logger.info(f"   {'PASS' if avg_emergence > 0.15 else 'FAIL'}: 潜力 > 0.15")
    
    # 验证6：类型多样性
    n_types = len(set(c.type for c in engine.creations))
    logger.info(f"6. 多样性验证: 创造类型数={n_types}")
    logger.info(f"   {'PASS' if n_types >= 4 else 'FAIL'}: 类型 >= 4")
    
    logger.info("-" * 50)
    
    results = {
        'engine': engine,
        'statistics': engine.get_statistics(),
        'cycle_results': cycle_results,
        'all_creations': [c.to_dict() for c in engine.creations],
        'verifications': {
            'novelty': {'value': avg_nov, 'threshold': 0.3, 'pass': bool(avg_nov > 0.3)},
            'value': {'value': avg_val, 'threshold': 0.3, 'pass': bool(avg_val > 0.3)},
            'cross_domain': {'value': cross_ratio, 'threshold': 0.2, 'pass': bool(cross_ratio > 0.2)},
            'productivity': {'value': total, 'threshold': num_cycles, 'pass': bool(total > num_cycles)},
            'emergence': {'value': avg_emergence, 'threshold': 0.15, 'pass': bool(avg_emergence > 0.15)},
            'diversity': {'value': n_types, 'threshold': 4, 'pass': bool(n_types >= 4)}
        }
    }
    
    return results


# =============================================================================
# 主入口
# =============================================================================
"""
OMNI-HUB v11.0 — creativity_engine
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""
if __name__ == "__main__":
    results = run_experiment(num_cycles=50, verbose=True)
    
    # 保存结果到JSON
    output_path = "/mnt/agents/output/OMNI-HUB/core/creativity_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        save_data = {
            'statistics': results['statistics'],
            'verifications': results['verifications'],
            'sample_creations': results['all_creations'][:20]
        }
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
        logger.error(f"File operation failed: {e}")
    print(f"\n结果已保存到: {output_path}")
    print("\nOMNI-HUB v5.0 CreativityEngine 实验完成！")
