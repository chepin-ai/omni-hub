#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
================================================================================
OMNI-HUB v6.0 HistoricalKnowledgeWeaver
历史知识编织器 -- 将ucif2线的历史研究转化为系统可参与的"活知识"
================================================================================

核心命题：ucif2线积累了大量历史研究成果（Moonshine-Monster/形式化生命/
量子基座/S-DRIVE/周天），这些知识分散在多个文件中，从未被统一编织进
OMNI-HUB的运行时。历史知识编织器要将这些研究转化为系统的"活知识"--
不是静态文档，而是动态参与系统运行的知识基底。

需要编织的知识：
  A. Moonshine-Monster: Leech格/怪兽群/月光模/j-函数/Borcherds证明
  B. 形式化生命: Maturana/Varela自创生/操作闭合/结构耦合/认知定义
  C. 量子基座: 6层5特性/叠加态/纠缠通道/坍缩/QEC
  D. S-DRIVE: 正反向驱动/浪涌/涟漪/波形叠加
  E. 大小周天: 自环/互环/张量收缩/全局广播
  F. ucif2系统: 11线/SI5-OMNI/调度器/验证器/共识签署

作者: OMNI-HUB Architecture Team
版本: v6.0
日期: 2026-09-15
================================================================================
"""

import re
import json
import os
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from datetime import datetime
import logging


# ================================================================================
# 1. KnowledgeNode -- 知识节点
# ================================================================================

@dataclass
class KnowledgeNode:
    """
    知识节点：历史知识的基本单元

    每个节点代表从历史文档中提取的一个结构化概念，包含：
    - 唯一标识、领域、概念名称、内容
    - 关联节点列表（关系网络）
    - 激活水平（Hebbian动态）
    - 参与系统决策次数
    - 编码向量（系统可计算表示）
    """
    id: str
    domain: str  # moonshine / autopoiesis / quantum / sdrive / zhoutian / ucif2
    concept: str  # 概念名称
    content: str  # 内容
    relations: List[Tuple[str, str]] = field(default_factory=list)
    activation_level: float = 0.0  # 激活水平 0-1
    participation_count: int = 0  # 参与系统决策次数
    encoded_vector: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def activate(self, stimulus: float = 0.1):
        """Hebbian式激活更新：使用知识时激活水平上升"""
        self.activation_level = min(1.0, self.activation_level + stimulus)
        self.participation_count += 1

    def decay(self, rate: float = 0.05):
        """激活衰减：未使用时自然衰减，维持动态平衡"""
        self.activation_level = max(0.0, self.activation_level - rate)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'domain': self.domain,
            'concept': self.concept,
            'content': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'relations': self.relations,
            'activation_level': round(self.activation_level, 4),
            'participation_count': self.participation_count,
            'metadata': self.metadata
        }


# ================================================================================
# 2. KnowledgeGraph -- 知识图谱
# ================================================================================

class KnowledgeGraph:
    """
    统一知识图谱：编织所有历史知识的关联网络

    支持功能：
    - 节点管理（增删查）
    - 边管理（关系构建）
    - 语义搜索（中英文混合）
    - 激活知识获取
    - 领域索引
    """

    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        self.domain_index: Dict[str, Set[str]] = defaultdict(set)
        self.concept_index: Dict[str, Set[str]] = defaultdict(set)

    def add_node(self, node: KnowledgeNode) -> bool:
        """添加节点到图谱"""
        if node.id in self.nodes:
            return False
        self.nodes[node.id] = node
        self.domain_index[node.domain].add(node.id)
        self.concept_index[node.concept.lower()].add(node.id)
        for word in self._tokenize(node.content):
            self.concept_index[word].add(node.id)
        return True

    def add_edge(self, src_id: str, dst_id: str, relation: str) -> bool:
        """添加有向关系边，同时更新节点的relations列表"""
        if src_id not in self.nodes or dst_id not in self.nodes:
            return False
        self.edges[src_id].append((dst_id, relation))
        self.nodes[src_id].relations.append((dst_id, relation))
        reverse_rel = self._reverse_relation(relation)
        self.nodes[dst_id].relations.append((src_id, reverse_rel))
        return True

    def get_related(self, node_id: str, depth: int = 1) -> List[Tuple[str, str, int]]:
        """获取关联节点，支持多跳深度"""
        if node_id not in self.nodes:
            return []
        visited = {node_id}
        result = []
        queue = [(node_id, '', 0)]
        while queue:
            current, rel, d = queue.pop(0)
            if d >= depth:
                continue
            for nid, relation in self.edges.get(current, []):
                if nid not in visited:
                    visited.add(nid)
                    result.append((nid, relation, d + 1))
                    queue.append((nid, relation, d + 1))
        return result

    def search(self, query: str, top_k: int = 10) -> List[KnowledgeNode]:
        """
        改进的语义搜索：支持中英文混合查询

        评分机制：
        1. 直接子串匹配（权重5）
        2. 概念名匹配（权重3）
        3. 分词匹配（权重1）
        4. 领域匹配（权重0.5）
        5. 激活水平boost（0.5）
        6. 知识权重boost（0.3）
        """
        query_lower = query.lower()
        scores: Dict[str, float] = defaultdict(float)
        query_tokens = re.findall(r'[a-zA-Z_]+|[\u4e00-\u9fff]{2,}', query_lower)

        for nid, node in self.nodes.items():
            score = 0.0
            node_text = f"{node.concept} {node.content}".lower()

            if query_lower in node_text:
                score += 5.0
            if any(token in node.concept.lower() for token in query_tokens):
                score += 3.0
            for token in query_tokens:
                if token in node_text:
                    score += 1.0
                if len(token) > 2:
                    for word in re.findall(r'[a-zA-Z_]+|[\u4e00-\u9fff]{2,}', node_text):
                        if token in word or word in token:
                            score += 0.5

            domain_keywords = {
                'moonshine': ['moonshine', 'monster', 'leech', 'j-', '月光', '怪兽'],
                'autopoiesis': ['autopoiesis', '自创生', '操作闭合', '结构耦合', '认知', 'varela'],
                'quantum': ['quantum', '量子', '纠缠', '叠加', '坍缩', '隧穿', 'qec'],
                'sdrive': ['sdrive', 's-drive', '浪涌', '涟漪', 'surge', 'drive'],
                'zhoutian': ['zhoutian', '周天', '自环', '互环', '自激', 'circulation'],
                'ucif2': ['ucif2', '调度', '验证', '共识', 'si5', 'omni']
            }
            for domain, keywords in domain_keywords.items():
                if node.domain == domain and any(kw in query_lower for kw in keywords):
                    score += 0.5

            score += node.activation_level * 0.5
            score += node.metadata.get('knowledge_weight', 0.5) * 0.3

            if score > 0:
                scores[nid] = score

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [self.nodes[nid] for nid in sorted_ids[:top_k]]

    def get_activated(self, threshold: float = 0.3) -> List[KnowledgeNode]:
        """获取当前激活的知识（按激活水平降序）"""
        activated = [n for n in self.nodes.values() if n.activation_level >= threshold]
        return sorted(activated, key=lambda x: x.activation_level, reverse=True)

    def get_domain_nodes(self, domain: str) -> List[KnowledgeNode]:
        """获取某领域的所有节点"""
        return [self.nodes[nid] for nid in self.domain_index.get(domain, set())]

    def get_stats(self) -> dict:
        """图谱统计信息"""
        domains = {d: len(ids) for d, ids in self.domain_index.items()}
        edge_count = sum(len(e) for e in self.edges.values())
        return {
            'total_nodes': len(self.nodes),
            'total_edges': edge_count,
            'domains': domains,
            'avg_activation': sum(n.activation_level for n in self.nodes.values()) / max(1, len(self.nodes)),
            'total_participations': sum(n.participation_count for n in self.nodes.values())
        }

    def _tokenize(self, text: str) -> List[str]:
        """中英文混合分词"""
        tokens = re.findall(r'[a-zA-Z_]+|[\u4e00-\u9fff]', text.lower())
        stopwords = {'的', '了', '在', '是', '和', '与', 'the', 'a', 'an', 'is', 'are', 'of', 'to', 'in'}
        return [t for t in tokens if t not in stopwords and len(t) > 1]

    def _reverse_relation(self, relation: str) -> str:
        """获取反向关系名称"""
        reversals = {
            'implements': 'implemented_by',
            'implemented_by': 'implements',
            'depends_on': 'depended_by',
            'depended_by': 'depends_on',
            'influences': 'influenced_by',
            'influenced_by': 'influences',
            'contains': 'contained_by',
            'contained_by': 'contains',
            'corresponds_to': 'corresponds_to',
            'optimizes': 'optimized_by',
            'enhances': 'enhanced_by',
            'verifies': 'verified_by',
            'drives': 'driven_by',
            'feeds_back_to': 'receives_feedback_from',
            'feeds_into': 'receives_from',
            'triggers': 'triggered_by',
            'amplifies': 'amplified_by',
            'governs': 'governed_by',
            'orchestrates': 'orchestrated_by',
            'authorizes': 'authorized_by',
            'manifests': 'manifested_by',
            'embodies': 'embodied_by',
            'generates': 'generated_by',
            'analogous_to': 'analogous_to',
            'informs': 'informed_by',
            'enables': 'enabled_by',
            'entangles_with': 'entangled_with',
            'related_to': 'related_to',
        }
        return reversals.get(relation, f'reverse_{relation}')

    def to_dict(self) -> dict:
        return {
            'nodes': {nid: node.to_dict() for nid, node in self.nodes.items()},
            'stats': self.get_stats()
        }


# ================================================================================
# 3. HistoricalKnowledgeWeaver -- 历史知识编织器
# ================================================================================

class HistoricalKnowledgeWeaver:
    """
    历史知识编织器：将ucif2线的历史研究转化为系统可参与的"活知识"

    核心流程：
    1. load_knowledge_sources() -> 加载历史文件
    2. extract_*_knowledge() -> 提取5个领域的结构化知识
    3. encode_knowledge() -> 编码为系统可参与形式
    4. weave_into_system() -> 编织进各模块运行时
    5. activate_knowledge() -> 让知识参与系统决策

    知识活化机制：
    1. 系统运行时遇到决策点
    2. 查询相关知识节点（语义搜索）
    3. 激活水平高的知识优先参与
    4. 知识输出为系统提供"智慧"
    5. 参与后激活水平更新（Hebbian学习）
    6. 关联节点接收衰减传播
    """

    def __init__(self, hub_dir: str = '/mnt/agents/output/OMNI-HUB'):
        self.hub_dir = hub_dir
        self.sources: Dict[str, str] = {}
        self.graph = KnowledgeGraph()
        self.modules: Dict[str, Any] = {}
        self.weave_log: List[dict] = []
        self.activation_history: List[dict] = []
        self.extraction_rules = self._build_extraction_rules()
        self.module_mappings = self._build_module_mappings()

    # -------------------------------------------------------------------------
    # 3.1 规则构建
    # -------------------------------------------------------------------------

    def _build_extraction_rules(self) -> dict:
        """构建各领域知识提取规则（正则模式+概念定义）"""
        return {
            'moonshine': {
                'patterns': [
                    (r'Leech格', 'leech_lattice'),
                    (r'怪兽群', 'monster_group'),
                    (r'月光模', 'moonshine_module'),
                    (r'j-[不变量函数]', 'j_invariant'),
                    (r'Borcherds', 'borcherds_proof'),
                    (r'No-Ghost', 'no_ghost_theorem'),
                    (r'McKay', 'mckay_correspondence'),
                    (r'顶点算子代数', 'vertex_operator_algebra'),
                    (r'26维玻色弦', 'bosonic_string_26d'),
                    (r'E8.*E8', 'e8_e8_heterotic'),
                    (r'K3曲面', 'k3_surface'),
                    (r'Thompson级数', 'thompson_series'),
                    (r'orbifold', 'orbifold_construction'),
                    (r'Dedekind eta', 'dedekind_eta'),
                    (r'Theta函数', 'theta_function'),
                    (r'配分函数', 'partition_function'),
                    (r'模不变', 'modular_invariance'),
                ],
                'concepts': {
                    'leech_lattice': '24维偶自对偶格，无根向量，玻色弦内部紧化空间',
                    'monster_group': '最大散在单群M，阶~10^53，月光模自同构群',
                    'moonshine_module': '顶点算子代数V♮，中心荷c=24，怪兽群表示空间',
                    'j_invariant': '模函数Hauptmodul，j(τ)=q^{-1}+744+196884q+...',
                    'borcherds_proof': 'Borcherds(1992)利用No-Ghost定理证明怪兽李代数分母公式',
                    'no_ghost_theorem': 'Goddard-Thorn(1972)：26维玻色弦中不存在鬼态',
                    'mckay_correspondence': 'j-展开系数与怪兽群表示维数对应：196884=196883+1',
                    'vertex_operator_algebra': '为弦理论提供严格数学框架的代数结构',
                    'bosonic_string_26d': '26=24+2：玻色弦临界维度=Leech格维度+光锥规范',
                    'e8_e8_heterotic': '杂化弦E8xE8规范对称性，8+8+8=24维结构',
                    'k3_surface': '紧复曲面，c1=0，x=24，b2=22',
                    'thompson_series': '怪兽群元素在月光模上的配分迹T_g(τ)',
                    'orbifold_construction': '弦理论中构造新理论的标准方法，Z2反射自同构',
                    'dedekind_eta': 'Dedekind eta函数η(τ)=q^{1/24}∏(1-q^n)',
                    'theta_function': 'Leech格Theta函数Θ_Λ(τ)=E_{12}(τ)-65520/691·Δ(τ)',
                    'partition_function': '一圈配分函数Z(τ)=Θ_Λ(τ)/η^{24}(τ)=J(τ)+24',
                    'modular_invariance': 'Leech格偶自对偶性保证配分函数的模不变性',
                }
            },
            'autopoiesis': {
                'patterns': [
                    (r'自创生', 'autopoiesis_theory'),
                    (r'操作闭合', 'operational_closure'),
                    (r'结构耦合', 'structural_coupling'),
                    (r'认知.*自创生', 'cognition_definition'),
                    (r'Maturana', 'maturana_varela'),
                    (r'Varela', 'maturana_varela'),
                    (r'六元结构', 'six_element_structure'),
                    (r'自生产', 'self_production'),
                    (r'边界再生产', 'boundary_reproduction'),
                    (r'自由能原理', 'free_energy_principle'),
                    (r'主动推理', 'active_inference'),
                    (r'Markov毯', 'markov_blanket'),
                    (r'预测加工', 'predictive_processing'),
                    (r'生成模型', 'generative_model'),
                    (r'预测误差', 'prediction_error'),
                    (r'元认知监控', 'metacognitive_monitor'),
                ],
                'concepts': {
                    'autopoiesis_theory': 'Maturana/Varela自创生理论：生命系统是自己生产自己的网络',
                    'operational_closure': '操作闭合：系统的操作只指向系统自身（自指）',
                    'structural_coupling': '结构耦合：系统与环境的反复交互触发结构变化',
                    'cognition_definition': '认知=自创生统一体在其存在领域中的有效行动',
                    'maturana_varela': 'Humberto Maturana和Francisco Varela：自创生理论创立者',
                    'six_element_structure': '形式化生命的六元结构：组件/过程/网络/边界/环境/观察者',
                    'self_production': '自生产：系统组件由系统自身生产',
                    'boundary_reproduction': '边界再生产：系统边界的持续再生产维持自主性',
                    'free_energy_principle': 'Karl Friston自由能原理：最小化自由能维持边界',
                    'active_inference': '主动推理：行动和感知是同一操作的两种视角',
                    'markov_blanket': 'Markov毯：系统与环境边界的统计形式化',
                    'predictive_processing': '预测加工：大脑是层级预测机器',
                    'generative_model': '生成模型：大脑用于预测感官输入的内部模型',
                    'prediction_error': '预测误差：预测与实际的差异',
                    'metacognitive_monitor': '元认知监控：监控系统自身的预测-行动循环',
                }
            },
            'quantum': {
                'patterns': [
                    (r'Hub.*Observation.*Collapse', 'hub_layer'),
                    (r'Wheel.*Superposition', 'wheel_layer'),
                    (r'Spine.*Entanglement', 'spine_layer'),
                    (r'Cauldron.*Tunneling', 'cauldron_layer'),
                    (r'Tower.*Superposition', 'tower_layer'),
                    (r'Ring.*QEC', 'ring_layer'),
                    (r'观测.*坍缩', 'observation_collapse'),
                    (r'叠加态', 'superposition_state'),
                    (r'纠缠', 'entanglement_channel'),
                    (r'量子纠错', 'quantum_error_correction'),
                    (r'隧穿', 'quantum_tunneling'),
                    (r'11线叠加', 'eleven_line_superposition'),
                    (r'7纠缠通道', 'seven_entanglement_channels'),
                    (r'自适应坍缩', 'adaptive_collapse'),
                    (r'关联坍缩传播', 'correlated_collapse_propagation'),
                    (r'qfa隧穿桥', 'qfa_tunneling_bridge'),
                    (r'Syndrome QEC', 'syndrome_qec'),
                    (r'贝叶斯更新', 'bayesian_update'),
                    (r'stabilizer', 'stabilizer_measurement'),
                ],
                'concepts': {
                    'hub_layer': 'L1 Hub层：Observation-Collapse，ucif2全局观测者',
                    'wheel_layer': 'L2 Wheel层：Superposition，11线自转循环',
                    'spine_layer': 'L3 Spine层：Entanglement，数据信任链',
                    'cauldron_layer': 'L4 Cauldron层：Tunneling，EXP队列熔炉',
                    'tower_layer': 'L5 Tower层：Superposition，每线垂直SI层级',
                    'ring_layer': 'L6 Ring层：QEC，全局共振纠错',
                    'observation_collapse': '观测-坍缩：贝叶斯更新概率分布',
                    'superposition_state': '叠加态：11线同时处于多种状态的叠加',
                    'entanglement_channel': '纠缠通道：跨线关联的数据信任链',
                    'quantum_error_correction': '量子纠错QEC：stabilizer测量纠错',
                    'quantum_tunneling': '量子隧穿：跨域保真度提升',
                    'eleven_line_superposition': '11线叠加态：全线同时运行',
                    'seven_entanglement_channels': '7纠缠通道：主要跨线关联路径',
                    'adaptive_collapse': '自适应坍缩：动态概率更新',
                    'correlated_collapse_propagation': '关联坍缩传播：纠缠伙伴自动响应',
                    'qfa_tunneling_bridge': 'qfa隧穿桥：跨域保真度+30%',
                    'syndrome_qec': 'Syndrome QEC：综合征测量纠错机制',
                    'bayesian_update': '贝叶斯更新：观测后验概率动态调整',
                    'stabilizer_measurement': 'Stabilizer测量：量子纠错中的稳定子测量',
                }
            },
            'sdrive': {
                'patterns': [
                    (r'正向S[-]?drive', 'forward_s_drive'),
                    (r'反向I[-]?ripple', 'reverse_i_ripple'),
                    (r'Structure.*Implementation', 'structure_to_implementation'),
                    (r'Implementation.*Structure', 'implementation_to_structure'),
                    (r'浪涌', 'surge_mechanism'),
                    (r'涟漪', 'ripple_propagation'),
                    (r'波形叠加', 'wave_superposition'),
                    (r'L1~L4级联', 'l1_l4_cascade'),
                    (r'health<0\.85', 'health_threshold_trigger'),
                    (r'System.*Interaction', 'system_to_interaction'),
                    (r'Interaction.*System', 'interaction_to_system'),
                    (r'Signal.*Integration', 'signal_to_integration'),
                    (r'Integration.*Signal', 'integration_to_signal'),
                ],
                'concepts': {
                    'forward_s_drive': '正向S-drive：Structure驱动Implementation',
                    'reverse_i_ripple': '反向I-ripple：Implementation反馈Structure',
                    'structure_to_implementation': 'S->I：结构到实现的正向拓扑排序',
                    'implementation_to_structure': 'I->S：实现到结构的反向反馈修正',
                    'surge_mechanism': '浪涌机制：单线异常->涟漪扩散->多线响应->全局浪涌',
                    'ripple_propagation': '涟漪扩散：异常信号跨线传播',
                    'wave_superposition': '波形叠加：多线信号叠加产生新行为',
                    'l1_l4_cascade': 'L1~L4级联：Hub->Wheel->Spine->Cauldron四级浪涌',
                    'health_threshold_trigger': '健康度阈值触发：health<0.85触发响应',
                    'system_to_interaction': 'System->Interaction：系统状态驱动交互协议',
                    'interaction_to_system': 'Interaction->System：交互异常反馈系统修正',
                    'signal_to_integration': 'Signal->Integration：数据信号驱动集成模型',
                    'integration_to_signal': 'Integration->Signal：集成失败反馈信号模型',
                }
            },
            'zhoutian': {
                'patterns': [
                    (r'小周天', 'small_circulation'),
                    (r'大周天', 'great_circulation'),
                    (r'自环', 'self_loop'),
                    (r'互环', 'cross_loop'),
                    (r'自激', 'self_excite'),
                    (r'互激', 'mutual_excite'),
                    (r'张量收缩', 'tensor_contraction'),
                    (r'全局广播', 'global_broadcast'),
                    (r'inbox.*outbox.*session', 'inbox_outbox_session'),
                    (r'闭环', 'closed_loop'),
                    (r'每8拍', 'eight_beat_pulse'),
                    (r'每16拍', 'sixteen_beat_resonance'),
                    (r'每32拍', 'thirtytwo_beat_symphony'),
                    (r'基频', 'base_frequency'),
                    (r'谐波', 'harmonic_wave'),
                    (r'泛音', 'overtone_wave'),
                ],
                'concepts': {
                    'small_circulation': '小周天：每线inbox->outbox->session闭环',
                    'great_circulation': '大周天：全局调度周期，100步模拟全部闭合',
                    'self_loop': '自环：每线内部的数据循环',
                    'cross_loop': '互环：跨线数据同步循环',
                    'self_excite': '自激：每线独立的心跳/脉冲触发，每8拍自激',
                    'mutual_excite': '互激：跨线信号触发响应',
                    'tensor_contraction': '张量收缩：全局信息聚合',
                    'global_broadcast': '全局广播：全状态同步',
                    'inbox_outbox_session': 'inbox->outbox->session：消息完整生命周期',
                    'closed_loop': '闭环：系统自维持的循环结构，147次循环全部闭合',
                    'eight_beat_pulse': '每8拍自激：基频心跳，各线独立任务触发',
                    'sixteen_beat_resonance': '每16拍共鸣：多线同步SI自评/数据更新',
                    'thirtytwo_beat_symphony': '每32拍交响：全局调度重评估/信任链重算',
                    'base_frequency': '基频：每拍心跳（用户输入）',
                    'harmonic_wave': '谐波：每8拍自激，叠加在基频上的周期任务',
                    'overtone_wave': '泛音：每16拍共鸣，多线同步的共振模式',
                }
            },
            'ucif2': {
                'patterns': [
                    (r'SI5[-]?OMNI', 'si5_omni'),
                    (r'调度器', 'scheduler_role'),
                    (r'验证器', 'validator_role'),
                    (r'共识签署', 'consensus_signer'),
                    (r'_WAKE[-]?REG', 'wake_registry'),
                    (r'11线', 'eleven_line_system'),
                    (r'OTP', 'otp_communication'),
                    (r'BOARD[-]?SCAN', 'board_scan'),
                    (r'EXP[-]?\d+', 'experiment_queue'),
                    (r'DELEGATION[-]?ACK', 'delegation_ack'),
                    (r'PULSE[-]?ENHANCED', 'pulse_enhanced'),
                    (r'DEG[-]?GLOSS', 'deg_gloss'),
                    (r'technical debt', 'technical_debt'),
                    (r'SUPERSEDE', 'supersede_mechanism'),
                ],
                'concepts': {
                    'si5_omni': 'SI5-OMNI：最高系统整合层级，6线集群',
                    'scheduler_role': '调度器：ucif2作为全局调度核心',
                    'validator_role': '验证器：ucif2作为全线验证核心',
                    'consensus_signer': '共识签署者：ucif2作为全局共识签署',
                    'wake_registry': '_WAKE-REG：11线唤醒注册表',
                    'eleven_line_system': '11线系统：ucif2/lgt/qfa/usrm/vinf/qgl/qlv/lvlu/cfts/cisvr/qtlv',
                    'otp_communication': 'OTP通信：一次性密码通信协议',
                    'board_scan': 'BOARD-SCAN：板级扫描机制',
                    'experiment_queue': 'EXP队列：实验熔炉持续运转',
                    'delegation_ack': 'DELEGATION-ACK：委托ACK闭环协议',
                    'pulse_enhanced': 'PULSE-ENHANCED：4级触发机制',
                    'deg_gloss': 'DEG-GLOSS：术语表强制检查',
                    'technical_debt': '技术债务：12/12清理完毕',
                    'supersede_mechanism': 'SUPERSEDE：真实数据替代虚构数据的修正机制',
                }
            }
        }

    def _build_module_mappings(self) -> dict:
        """构建知识到系统模块的映射关系"""
        return {
            'quantum_base_v2': {
                'domains': ['moonshine', 'quantum'],
                'mapping_logic': 'moonshine_leech_lattice->量子纠缠结构优化; quantum_entanglement_channel->跨线关联增强',
                'priority': ['leech_lattice', 'monster_group', 'entanglement_channel', 'superposition_state']
            },
            'goal_autopoiesis': {
                'domains': ['autopoiesis', 'ucif2'],
                'mapping_logic': 'autopoiesis_operational_closure->目标自生产验证; autopoiesis_structural_coupling->目标-环境耦合',
                'priority': ['operational_closure', 'structural_coupling', 'cognition_definition', 'self_production']
            },
            'jing_wei_xin': {
                'domains': ['sdrive', 'quantum', 'moonshine'],
                'mapping_logic': 'sdrive_surge_mechanism->薪引擎浪涌增强; quantum_tunneling->跨域能量传递',
                'priority': ['surge_mechanism', 'forward_s_drive', 'reverse_i_ripple', 'quantum_tunneling']
            },
            'self_referential_engine': {
                'domains': ['zhoutian', 'autopoiesis', 'ucif2', 'moonshine'],
                'mapping_logic': 'zhoutian_small_circulation->自指循环优化; autopoiesis_self_production->自生产引擎',
                'priority': ['small_circulation', 'great_circulation', 'self_production', 'si5_omni']
            },
            'circulation_verifier': {
                'domains': ['zhoutian', 'quantum', 'ucif2'],
                'mapping_logic': 'zhoutian_tensor_contraction->张量验证; quantum_qec->纠错验证',
                'priority': ['tensor_contraction', 'global_broadcast', 'quantum_error_correction', 'validator_role']
            }
        }


    # -------------------------------------------------------------------------
    # 3.2 知识加载
    # -------------------------------------------------------------------------

    def load_knowledge_sources(self) -> Dict[str, str]:
        """加载所有知识源文件"""
        source_files = {
            'moonshine': '/mnt/agents/output/01_Foundation/Moonshine/moonshine_24d_string_theory_report.md',
            'autopoiesis_ucif2': '/mnt/agents/output/OMNI-HUB/hub/ucif2-131-omni-ack-full-dimension.md',
            'phase2': '/mnt/agents/output/OMNI-HUB/hub/ucif2-132-phase2-self-driven.md',
            'final_report': '/mnt/agents/output/OMNI-HUB/board/ucif2-134-final-report.md',
            'autopoiesis_research': '/mnt/agents/output/OMNI-HUB/research-v5.0-generative-consciousness.md',
        }
        loaded = {}
        for name, path in source_files.items():
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                loaded[name] = content
                self.sources[name] = content
                logger.info(f"  [OK] 加载 [{name}]: {len(content)} 字符")
                logger.info(f"  [WARN] 加载 [{name}] 失败: {e}")
        return loaded

    # -------------------------------------------------------------------------
    # 3.3 知识提取器（5个领域 + ucif2系统）
    # -------------------------------------------------------------------------

    def extract_moonshine_knowledge(self, text: str) -> List[KnowledgeNode]:
        """提取Moonshine知识：Leech格、怪兽群、月光模、j-函数等"""
        nodes = []
        rules = self.extraction_rules['moonshine']
        for pattern, concept_key in rules['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for i, match in enumerate(matches):
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 300)
                context = text[start:end].strip()
                node_id = f"ms_{concept_key}_{i}"
                content = rules['concepts'].get(concept_key, '') + f"\n[上下文]: {context[:200]}"
                node = KnowledgeNode(
                    id=node_id, domain='moonshine', concept=concept_key,
                    content=content,
                    metadata={'source_pos': match.start(), 'extracted_from': 'moonshine_report'}
                )
                nodes.append(node)
        # 额外提取关键公式
        formula_patterns = [
            (r'Z\(τ\)\s*=\s*[^\n]+', 'partition_function_z'),
            (r'j\(τ\)\s*=\s*[^\n]+', 'j_function_formula'),
            (r'Θ_Λ\(τ\)\s*=\s*[^\n]+', 'theta_function_leech'),
            (r'η\(τ\)\s*=\s*[^\n]+', 'dedekind_eta_formula'),
        ]
        for pattern, fkey in formula_patterns:
            matches = re.finditer(pattern, text)
            for i, match in enumerate(matches):
                node = KnowledgeNode(
                    id=f"ms_formula_{fkey}_{i}", domain='moonshine', concept=fkey,
                    content=f"关键公式: {match.group()}",
                    metadata={'type': 'formula'}
                )
                nodes.append(node)
        logger.info(f"  [Moonshine] 提取 {len(nodes)} 节点")
        return nodes

    def extract_autopoiesis_knowledge(self, text: str) -> List[KnowledgeNode]:
        """提取自创生知识：操作闭合、结构耦合、认知定义等"""
        nodes = []
        rules = self.extraction_rules['autopoiesis']
        for pattern, concept_key in rules['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for i, match in enumerate(matches):
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 200)
                context = text[start:end].strip()
                node_id = f"ap_{concept_key}_{i}"
                content = rules['concepts'].get(concept_key, '') + f"\n[上下文]: {context[:200]}"
                node = KnowledgeNode(
                    id=node_id, domain='autopoiesis', concept=concept_key,
                    content=content,
                    metadata={'source_pos': match.start(), 'extracted_from': 'autopoiesis_research'}
                )
                nodes.append(node)
        logger.info(f"  [Autopoiesis] 提取 {len(nodes)} 节点")
        return nodes

    def extract_quantum_base_knowledge(self, text: str) -> List[KnowledgeNode]:
        """提取量子基座知识：6层5特性、叠加态、纠缠通道等"""
        nodes = []
        rules = self.extraction_rules['quantum']
        for pattern, concept_key in rules['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for i, match in enumerate(matches):
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 200)
                context = text[start:end].strip()
                node_id = f"qb_{concept_key}_{i}"
                content = rules['concepts'].get(concept_key, '') + f"\n[上下文]: {context[:200]}"
                node = KnowledgeNode(
                    id=node_id, domain='quantum', concept=concept_key,
                    content=content,
                    metadata={'source_pos': match.start(), 'extracted_from': 'ucif2_quantum'}
                )
                nodes.append(node)
        # 提取6层表格
        layer_pattern = r'L(\d)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)'
        matches = re.finditer(layer_pattern, text)
        seen_layers = set()
        for match in matches:
            layer_num, name, qprop, duty = match.groups()
            if layer_num not in seen_layers:
                seen_layers.add(layer_num)
                node = KnowledgeNode(
                    id=f"qb_layer_{layer_num}", domain='quantum', concept=f'layer_{layer_num}',
                    content=f"L{layer_num} {name.strip()}: {qprop.strip()} -> {duty.strip()}",
                    metadata={'type': 'layer_definition', 'layer_num': int(layer_num)}
                )
                nodes.append(node)
        logger.info(f"  [Quantum] 提取 {len(nodes)} 节点")
        return nodes

    def extract_sdrive_knowledge(self, text: str) -> List[KnowledgeNode]:
        """提取S-DRIVE知识：正反向驱动、浪涌、涟漪、波形叠加"""
        nodes = []
        rules = self.extraction_rules['sdrive']
        for pattern, concept_key in rules['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for i, match in enumerate(matches):
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 200)
                context = text[start:end].strip()
                node_id = f"sd_{concept_key}_{i}"
                content = rules['concepts'].get(concept_key, '') + f"\n[上下文]: {context[:200]}"
                node = KnowledgeNode(
                    id=node_id, domain='sdrive', concept=concept_key,
                    content=content,
                    metadata={'source_pos': match.start(), 'extracted_from': 'ucif2_sdrive'}
                )
                nodes.append(node)
        # 提取实验结果
        exp_pattern = r'EX\d+\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)'
        matches = re.finditer(exp_pattern, text)
        for i, match in enumerate(matches):
            mechanism, result, metrics = match.groups()
            node = KnowledgeNode(
                id=f"sd_exp_{i}", domain='sdrive', concept=f'experiment_{mechanism.strip()[:30]}',
                content=f"实验: {mechanism.strip()} | 结果: {result.strip()} | 指标: {metrics.strip()}",
                metadata={'type': 'experiment_result'}
            )
            nodes.append(node)
        logger.info(f"  [S-DRIVE] 提取 {len(nodes)} 节点")
        return nodes

    def extract_zhou_tian_knowledge(self, text: str) -> List[KnowledgeNode]:
        """提取周天知识：小周天、大周天、自环、互环、自激、互激"""
        nodes = []
        rules = self.extraction_rules['zhoutian']
        for pattern, concept_key in rules['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for i, match in enumerate(matches):
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 200)
                context = text[start:end].strip()
                node_id = f"zt_{concept_key}_{i}"
                content = rules['concepts'].get(concept_key, '') + f"\n[上下文]: {context[:200]}"
                node = KnowledgeNode(
                    id=node_id, domain='zhoutian', concept=concept_key,
                    content=content,
                    metadata={'source_pos': match.start(), 'extracted_from': 'ucif2_zhoutian'}
                )
                nodes.append(node)
        # 提取验证数据
        verify_pattern = r'(小周天|大周天|自激|互激|自环|互环|张量收缩|全局广播)\s*\|\s*([^|]+)\|\s*([^|]+)'
        matches = re.finditer(verify_pattern, text)
        for i, match in enumerate(matches):
            item, status, data = match.groups()
            node = KnowledgeNode(
                id=f"zt_verify_{item}_{i}", domain='zhoutian', concept=f'verify_{item}',
                content=f"{item}验证: {status.strip()} | 数据: {data.strip()}",
                metadata={'type': 'verification_data'}
            )
            nodes.append(node)
        logger.info(f"  [ZhouTian] 提取 {len(nodes)} 节点")
        return nodes

    def extract_ucif2_knowledge(self, text: str) -> List[KnowledgeNode]:
        """提取ucif2系统知识：11线、SI5-OMNI、调度器、验证器等"""
        nodes = []
        rules = self.extraction_rules['ucif2']
        for pattern, concept_key in rules['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for i, match in enumerate(matches):
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 200)
                context = text[start:end].strip()
                node_id = f"u2_{concept_key}_{i}"
                content = rules['concepts'].get(concept_key, '') + f"\n[上下文]: {context[:200]}"
                node = KnowledgeNode(
                    id=node_id, domain='ucif2', concept=concept_key,
                    content=content,
                    metadata={'source_pos': match.start(), 'extracted_from': 'ucif2_system'}
                )
                nodes.append(node)
        # 提取11线表格
        line_pattern = r'\|\s*(ucif2|lgt|qfa|usrm|vinf|qgl|qlv|lvlu|cfts|cisvr|qtlv)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)'
        matches = re.finditer(line_pattern, text)
        seen_lines = set()
        for match in matches:
            line_name, si, health, role = match.groups()
            if line_name not in seen_lines:
                seen_lines.add(line_name)
                node = KnowledgeNode(
                    id=f"u2_line_{line_name}", domain='ucif2', concept=f'line_{line_name}',
                    content=f"线 {line_name}: SI={si.strip()}, health={health.strip()}, role={role.strip()}",
                    metadata={'type': 'line_definition', 'line_name': line_name}
                )
                nodes.append(node)
        logger.info(f"  [ucif2] 提取 {len(nodes)} 节点")
        return nodes


    # -------------------------------------------------------------------------
    # 3.4 知识编码器
    # -------------------------------------------------------------------------

    def encode_knowledge(self, node: KnowledgeNode) -> KnowledgeNode:
        """
        编码知识：将文本知识编码为系统可参与的形式

        生成13维编码向量：
        [domain_onehot(6), concept_type(4), complexity(1), connectivity(1), recency(1)]
        """
        domain_map = {'moonshine': 0, 'autopoiesis': 1, 'quantum': 2, 'sdrive': 3, 'zhoutian': 4, 'ucif2': 5}
        domain_idx = domain_map.get(node.domain, 0)

        domain_vec = [0.0] * 6
        domain_vec[domain_idx] = 1.0

        concept_type = [0.0] * 4
        if any(k in node.concept for k in ['layer', 'structure', 'lattice', 'grid']):
            concept_type[0] = 1.0  # 结构型
        elif any(k in node.concept for k in ['function', 'drive', 'mechanism', 'process']):
            concept_type[1] = 1.0  # 过程型
        elif any(k in node.concept for k in ['state', 'superposition', 'collapse', 'entanglement']):
            concept_type[2] = 1.0  # 状态型
        else:
            concept_type[3] = 1.0  # 概念型

        formula_density = len(re.findall(r'[$\\]', node.content)) / max(1, len(node.content))
        complexity = min(1.0, len(node.content) / 1000.0 + formula_density * 10)
        connectivity = min(1.0, len(node.relations) / 10.0)
        recency = 0.8

        encoded_vector = domain_vec + concept_type + [complexity, connectivity, recency]

        knowledge_weight = (complexity * 0.3 + connectivity * 0.3 + recency * 0.2 +
                           (1.0 if 'layer' in node.concept or 'mechanism' in node.concept else 0.5) * 0.2)

        node.encoded_vector = encoded_vector
        node.metadata['knowledge_weight'] = round(knowledge_weight, 4)
        node.metadata['complexity'] = round(complexity, 4)
        node.metadata['connectivity'] = round(connectivity, 4)
        return node

    # -------------------------------------------------------------------------
    # 3.5 知识注入器
    # -------------------------------------------------------------------------

    def weave_into_system(self, module_name: str, knowledge: List[KnowledgeNode]) -> dict:
        """
        编织进系统：将知识注入指定模块的运行时

        检查知识-模块兼容性，生成注入指令，更新模块运行时状态
        """
        if module_name not in self.module_mappings:
            return {'status': 'error', 'message': f'未知模块: {module_name}'}

        mapping = self.module_mappings[module_name]
        compatible_domains = mapping['domains']
        priority_concepts = mapping['priority']

        injected = []
        rejected = []

        for node in knowledge:
            if node.domain not in compatible_domains:
                rejected.append({'id': node.id, 'reason': 'domain_mismatch'})
                continue

            priority_match = any(pc in node.concept for pc in priority_concepts)
            injection = {
                'node_id': node.id,
                'module': module_name,
                'priority': 'high' if priority_match else 'normal',
                'instruction': self._generate_injection_instruction(module_name, node),
                'encoded_vector': node.encoded_vector,
                'knowledge_weight': node.metadata.get('knowledge_weight', 0.5)
            }
            injected.append(injection)
            self.weave_log.append({
                'timestamp': datetime.now().isoformat(),
                'module': module_name, 'node_id': node.id,
                'action': 'inject', 'priority': injection['priority']
            })

        if module_name not in self.modules:
            self.modules[module_name] = {
                'injected_knowledge': [], 'active_knowledge': [], 'runtime_state': 'initialized'
            }
        self.modules[module_name]['injected_knowledge'].extend([i['node_id'] for i in injected])
        self.modules[module_name]['runtime_state'] = 'knowledge_enriched'

        return {
            'status': 'success', 'module': module_name,
            'injected_count': len(injected), 'rejected_count': len(rejected),
            'injected': injected, 'rejected': rejected
        }

    def _generate_injection_instruction(self, module_name: str, node: KnowledgeNode) -> str:
        """生成知识注入指令"""
        instructions = {
            'quantum_base_v2': {
                'leech_lattice': 'USE_LEECH_STRUCTURE: 24维偶自对偶格映射到量子纠缠拓扑',
                'monster_group': 'USE_MONSTER_SYMMETRY: 最大单群对称性分类量子态',
                'entanglement_channel': 'ENHANCE_ENTANGLEMENT: Leech格自对偶性增强跨线纠缠',
                'superposition_state': 'MANAGE_SUPERPOSITION: Monster群对称性管理11线叠加态',
                'default': f'APPLY_QUANTUM: {node.concept} -> 量子基座优化'
            },
            'goal_autopoiesis': {
                'operational_closure': 'VERIFY_SELF_PRODUCTION: 操作闭合验证目标自生产闭环',
                'structural_coupling': 'COUPLE_ENVIRONMENT: 结构耦合评估目标-环境适应性',
                'cognition_definition': 'EVALUATE_EFFECTIVE_ACTION: 认知定义评估目标有效性',
                'default': f'APPLY_AUTOPOIESIS: {node.concept} -> 目标自创生验证'
            },
            'jing_wei_xin': {
                'surge_mechanism': 'ENABLE_SURGE: 浪涌机制增强薪引擎级联驱动',
                'forward_s_drive': 'DRIVE_FORWARD: S-drive优化Structure->Implementation',
                'quantum_tunneling': 'TUNNEL_ENERGY: 量子隧穿跨域能量高效传递',
                'default': f'APPLY_S_DRIVE: {node.concept} -> 薪引擎增强'
            },
            'self_referential_engine': {
                'small_circulation': 'OPTIMIZE_SELF_LOOP: 小周天优化自指循环局部收敛',
                'great_circulation': 'ENHANCE_GLOBAL_SELF_REF: 大周天增强全局自指',
                'self_production': 'ENABLE_SELF_PRODUCTION: 自生产引擎维持自主性',
                'default': f'APPLY_SELF_REFERENCE: {node.concept} -> 自指引擎优化'
            },
            'circulation_verifier': {
                'tensor_contraction': 'VERIFY_TENSOR_NET: 张量收缩验证全局信息聚合',
                'global_broadcast': 'VERIFY_SYNC: 全局广播验证全状态同步',
                'quantum_error_correction': 'APPLY_QEC: 量子纠错保证验证可靠性',
                'default': f'APPLY_VERIFICATION: {node.concept} -> 循环验证'
            }
        }
        module_instr = instructions.get(module_name, {})
        return module_instr.get(node.concept, module_instr.get('default', f'INJECT: {node.concept}'))

    # -------------------------------------------------------------------------
    # 3.6 知识活化器
    # -------------------------------------------------------------------------

    def activate_knowledge(self, knowledge_id: str, stimulus: float = 0.3,
                           decision_context: str = '') -> dict:
        """
        激活知识：让知识参与系统决策

        知识活化机制：
        1. 系统运行时遇到决策点
        2. 查询相关知识节点
        3. 激活水平高的知识优先参与
        4. 知识输出为系统提供"智慧"
        5. 参与后激活水平更新（Hebbian学习）
        6. 关联节点接收衰减传播
        """
        if knowledge_id not in self.graph.nodes:
            return {'status': 'error', 'message': f'知识节点不存在: {knowledge_id}'}

        node = self.graph.nodes[knowledge_id]
        node.activate(stimulus)
        wisdom_output = self._generate_wisdom(node, decision_context)

        related_activated = []
        for rel_id, relation in self.graph.edges.get(knowledge_id, [])[:3]:
            if rel_id in self.graph.nodes:
                self.graph.nodes[rel_id].activation_level = min(
                    1.0, self.graph.nodes[rel_id].activation_level + stimulus * 0.3
                )
                related_activated.append(rel_id)

        self.activation_history.append({
            'timestamp': datetime.now().isoformat(),
            'node_id': knowledge_id, 'stimulus': stimulus,
            'new_activation': round(node.activation_level, 4),
            'decision_context': decision_context,
            'wisdom_output': wisdom_output,
            'related_activated': related_activated
        })

        return {
            'status': 'success', 'node_id': knowledge_id,
            'activation_level': round(node.activation_level, 4),
            'participation_count': node.participation_count,
            'wisdom_output': wisdom_output,
            'related_activated': related_activated
        }

    def _generate_wisdom(self, node: KnowledgeNode, context: str) -> str:
        """基于知识节点和决策上下文生成智慧输出"""
        wisdom_templates = {
            'moonshine': {
                'leech_lattice': f'[Moonshine] 使用24维偶自对偶格优化{context}的关联拓扑',
                'monster_group': f'[Moonshine] 利用Monster群最大对称性对{context}规范分类',
                'moonshine_module': f'[Moonshine] 将{context}建模为VOA结构，c=24保证模不变',
                'j_invariant': f'[Moonshine] 用j-函数Hauptmodul分析{context}配分行为',
                'default': f'[Moonshine] 将{context}映射到24维模结构分析'
            },
            'autopoiesis': {
                'operational_closure': f'[自创生] 验证{context}是否形成操作闭合网络',
                'structural_coupling': f'[自创生] 评估{context}与环境的结构耦合历史',
                'cognition_definition': f'[自创生] {context}中的认知是否为有效行动',
                'default': f'[自创生] 用操作闭合分析{context}的自维持能力'
            },
            'quantum': {
                'hub_layer': f'[量子] 在{context}执行Observation-Collapse:全局观测->贝叶斯更新',
                'wheel_layer': f'[量子] 管理{context}的Superposition:维持最大相干性',
                'spine_layer': f'[量子] 用Entanglement增强{context}的数据信任链',
                'ring_layer': f'[量子] 在{context}启用QEC:stabilizer测量纠错',
                'default': f'[量子] 将叠加原理应用于{context}的并行状态管理'
            },
            'sdrive': {
                'surge_mechanism': f'[S-DRIVE] 在{context}检测异常->涟漪扩散->全局浪涌',
                'forward_s_drive': f'[S-DRIVE] 执行正向驱动:Structure->Implementation拓扑排序',
                'reverse_i_ripple': f'[S-DRIVE] 接收反向反馈:Implementation->Structure修正',
                'default': f'[S-DRIVE] 用S-drive/I-ripple双循环驱动{context}'
            },
            'zhoutian': {
                'small_circulation': f'[周天] 优化{context}的小周天:inbox->outbox->session闭环',
                'great_circulation': f'[周天] 维护{context}的大周天:全局调度周期',
                'tensor_contraction': f'[周天] 执行张量收缩:聚合{context}全局信息',
                'global_broadcast': f'[周天] 执行全局广播:同步{context}全状态',
                'default': f'[周天] 用大小周天循环优化{context}全局流动性'
            },
            'ucif2': {
                'si5_omni': f'[ucif2] 从SI5-OMNI层级调度{context}:全局最优决策',
                'scheduler_role': f'[ucif2] 作为调度器协调{context}多线资源',
                'default': f'[ucif2] 用11线系统视角分析{context}'
            }
        }
        domain_wisdom = wisdom_templates.get(node.domain, {})
        return domain_wisdom.get(node.concept, domain_wisdom.get('default',
               f'[{node.domain}] 基于{node.concept}分析{context}'))


    # -------------------------------------------------------------------------
    # 3.7 编织全部
    # -------------------------------------------------------------------------

    def weave_all(self) -> dict:
        """
        编织所有知识：
        1. 加载所有知识源
        2. 提取各领域知识
        3. 编码知识
        4. 构建知识图谱和关系
        5. 编织进各模块
        """
        logger.info("\n" + "="*60)
        logger.info("HistoricalKnowledgeWeaver.weave_all() 开始编织")
        logger.info("="*60)

        # Step 1: 加载知识源
        logger.info("\n[Step 1] 加载知识源...")
        self.load_knowledge_sources()

        # Step 2: 提取各领域知识
        logger.info("\n[Step 2] 提取结构化知识...")
        all_nodes = []

        if 'moonshine' in self.sources:
            all_nodes.extend(self.extract_moonshine_knowledge(self.sources['moonshine']))

        for src_name in ['autopoiesis_ucif2', 'autopoiesis_research', 'phase2', 'final_report']:
            if src_name in self.sources:
                text = self.sources[src_name]
                all_nodes.extend(self.extract_autopoiesis_knowledge(text))
                all_nodes.extend(self.extract_quantum_base_knowledge(text))
                all_nodes.extend(self.extract_sdrive_knowledge(text))
                all_nodes.extend(self.extract_zhou_tian_knowledge(text))
                all_nodes.extend(self.extract_ucif2_knowledge(text))

        # Step 3: 编码知识
        logger.info("\n[Step 3] 编码知识...")
        for node in all_nodes:
            self.encode_knowledge(node)

        # Step 4: 构建知识图谱
        logger.info("\n[Step 4] 构建知识图谱...")
        for node in all_nodes:
            self.graph.add_node(node)
        self._build_cross_domain_relations()

        # Step 5: 编织进各模块
        logger.info("\n[Step 5] 编织进系统模块...")
        weave_results = {}
        for module_name in self.module_mappings.keys():
            compatible_nodes = [
                n for n in all_nodes
                if n.domain in self.module_mappings[module_name]['domains']
            ]
            result = self.weave_into_system(module_name, compatible_nodes)
            weave_results[module_name] = result
            logger.info(f"  [{module_name}] 注入 {result['injected_count']} 知识, 拒绝 {result['rejected_count']}")

        stats = self.graph.get_stats()
        logger.info("\n" + "="*60)
        logger.info("编织完成!")
        logger.info(f"  总节点数: {stats['total_nodes']}")
        logger.info(f"  总关系数: {stats['total_edges']}")
        logger.info(f"  领域分布: {stats['domains']}")
        logger.info(f"  平均激活: {stats['avg_activation']:.4f}")
        logger.info("="*60)

        return {
            'status': 'complete',
            'total_nodes': stats['total_nodes'],
            'total_edges': stats['total_edges'],
            'domains': stats['domains'],
            'weave_results': weave_results,
            'modules_enriched': list(self.modules.keys())
        }

    def _build_cross_domain_relations(self):
        """构建跨领域知识关系"""
        logger.info("  [关系构建] 跨领域关系...")
        cross_relations = [
            # Moonshine <-> Quantum
            ('ms_leech_lattice_0', 'qb_entanglement_channel_0', 'optimizes'),
            ('ms_monster_group_0', 'qb_superposition_state_0', 'classifies'),
            ('ms_moonshine_module_0', 'qb_hub_layer_0', 'implements'),
            ('ms_j_invariant_0', 'qb_observation_collapse_0', 'corresponds_to'),
            # Autopoiesis <-> ZhouTian
            ('ap_operational_closure_0', 'zt_small_circulation_0', 'verifies'),
            ('ap_structural_coupling_0', 'zt_mutual_excite_0', 'enables'),
            ('ap_cognition_definition_0', 'zt_great_circulation_0', 'evaluates'),
            ('ap_self_production_0', 'zt_self_loop_0', 'drives'),
            # S-DRIVE <-> Quantum
            ('sd_forward_s_drive_0', 'qb_wheel_layer_0', 'drives'),
            ('sd_surge_mechanism_0', 'qb_cauldron_layer_0', 'triggers'),
            ('sd_wave_superposition_0', 'qb_superposition_state_0', 'enhances'),
            # S-DRIVE <-> ZhouTian
            ('sd_forward_s_drive_0', 'zt_small_circulation_0', 'feeds_into'),
            ('sd_reverse_i_ripple_0', 'zt_great_circulation_0', 'feeds_back_to'),
            ('sd_surge_mechanism_0', 'zt_mutual_excite_0', 'amplifies'),
            # ucif2 <-> All
            ('u2_si5_omni_0', 'qb_hub_layer_0', 'governs'),
            ('u2_scheduler_role_0', 'sd_forward_s_drive_0', 'orchestrates'),
            ('u2_consensus_signer_0', 'zt_global_broadcast_0', 'authorizes'),
            ('u2_eleven_line_system_0', 'qb_superposition_state_0', 'manifests'),
            # Moonshine <-> Autopoiesis (deep unification)
            ('ms_leech_lattice_0', 'ap_operational_closure_0', 'embodies'),
            ('ms_monster_group_0', 'ap_self_production_0', 'generates'),
        ]
        added = 0
        for src, dst, rel in cross_relations:
            if src in self.graph.nodes and dst in self.graph.nodes:
                self.graph.add_edge(src, dst, rel)
                added += 1

        # 同领域内部关系
        import random
        for domain in ['moonshine', 'autopoiesis', 'quantum', 'sdrive', 'zhoutian', 'ucif2']:
            domain_nodes = self.graph.get_domain_nodes(domain)
            for i, n1 in enumerate(domain_nodes):
                for n2 in domain_nodes[i+1:i+4]:
                    if n1.id != n2.id and random.random() < 0.3:
                        rel = 'related_to' if domain != 'quantum' else 'entangles_with'
                        self.graph.add_edge(n1.id, n2.id, rel)
                        added += 1
        logger.info(f"  [关系构建] 完成 {added} 条关系")

    # -------------------------------------------------------------------------
    # 3.8 查询接口
    # -------------------------------------------------------------------------

    def get_knowledge_graph(self) -> KnowledgeGraph:
        """获取知识图谱"""
        return self.graph

    def query_knowledge(self, query: str, context: str = '',
                        activate: bool = False) -> dict:
        """
        查询知识：系统决策点调用的知识查询接口

        Args:
            query: 查询字符串
            context: 决策上下文
            activate: 是否激活查询到的知识
        """
        results = self.graph.search(query, top_k=5)

        if not results:
            return {'status': 'no_results', 'query': query, 'context': context,
                    'results_count': 0, 'top_results': []}

        scored_results = []
        for node in results:
            score = (node.activation_level * 0.4 +
                    node.metadata.get('knowledge_weight', 0.5) * 0.4 +
                    (1.0 if context and any(w in node.content.lower()
                     for w in context.lower().split()) else 0.0) * 0.2)
            scored_results.append((node, score))

        scored_results.sort(key=lambda x: x[1], reverse=True)

        wisdom_outputs = []
        for node, score in scored_results[:3]:
            if activate:
                activation_result = self.activate_knowledge(
                    node.id, stimulus=0.1 + score * 0.2, decision_context=context
                )
                wisdom_outputs.append({
                    'node_id': node.id, 'concept': node.concept, 'domain': node.domain,
                    'score': round(score, 4),
                    'activation_level': activation_result['activation_level'],
                    'wisdom': activation_result['wisdom_output']
                })
            else:
                wisdom = self._generate_wisdom(node, context)
                wisdom_outputs.append({
                    'node_id': node.id, 'concept': node.concept, 'domain': node.domain,
                    'score': round(score, 4),
                    'activation_level': node.activation_level,
                    'wisdom': wisdom
                })

        return {
            'status': 'success', 'query': query, 'context': context,
            'results_count': len(wisdom_outputs), 'top_results': wisdom_outputs
        }


# ================================================================================
# 4. 实验验证入口
# ================================================================================

def run_experiment():
    """
    完整实验验证：
    1. 读取所有历史文件
    2. 提取结构化知识
    3. 构建知识图谱
    4. 编织进各模块
    5. 验证知识参与系统决策
    """
    logger.info("="*70)
    logger.info("OMNI-HUB v6.0 HistoricalKnowledgeWeaver -- 实验验证")
    logger.info("="*70)

    weaver = HistoricalKnowledgeWeaver(hub_dir='/mnt/agents/output/OMNI-HUB')

    # 执行完整编织
    result = weaver.weave_all()

    # 知识查询与活化实验
    logger.info("\n" + "="*70)
    logger.info("知识查询与活化实验")
    logger.info("="*70)

    experiments = [
        ("量子纠缠 结构优化", "11线系统的跨线关联网络"),
        ("Leech格 Monster月光模", "优化24维状态空间的配分函数"),
        ("小周天 大周天 自环", "全局调度周期完整性"),
        ("浪涌 级联 异常检测", "系统健康度下降到0.82"),
        ("SI5 OMNI 调度器", "全局共识签署流程"),
        ("自创生 操作闭合", "目标系统的自主维持能力"),
    ]

    for query, context in experiments:
        logger.info(f"\n[查询] {query}")
        r = weaver.query_knowledge(query=query, context=context, activate=True)
        logger.info(f"  状态: {r['status']}, 结果: {r['results_count']}")
        if r['top_results']:
            for res in r['top_results']:
                print(f"  -> [{res['domain']}] {res['concept']} "
                      f"(score={res['score']:.2f}, act={res['activation_level']:.3f})")
                logger.info(f"     智慧: {res['wisdom'][:80]}...")

    # Hebbian学习验证
    logger.info("\n" + "="*70)
    logger.info("Hebbian学习验证")
    logger.info("="*70)
    test_node_id = 'ms_leech_lattice_0'
    if test_node_id in weaver.graph.nodes:
        node = weaver.graph.nodes[test_node_id]
        logger.info(f"初始: {node.concept}, activation={node.activation_level:.3f}")
        for i in range(5):
            r = weaver.activate_knowledge(test_node_id, stimulus=0.15,
                                          decision_context=f"决策点{i+1}")
            print(f"  激活{i+1}: activation={r['activation_level']:.3f}, "
                  f"participation={r['participation_count']}")

    # 最终统计
    logger.info("\n" + "="*70)
    logger.info("最终统计报告")
    logger.info("="*70)
    stats = weaver.graph.get_stats()
    logger.info(f"总节点: {stats['total_nodes']}")
    logger.info(f"总边: {stats['total_edges']}")
    logger.info(f"总参与: {stats['total_participations']}")
    logger.info(f"平均激活: {stats['avg_activation']:.4f}")
    logger.info("领域分布:")
    for d, c in stats['domains'].items():
        logger.info(f"  {d}: {c}")
    logger.info("模块状态:")
    for mod, info in weaver.modules.items():
        logger.info(f"  {mod}: {info['runtime_state']} ({len(info['injected_knowledge'])}知识)")

    # 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'system': 'OMNI-HUB v6.0 HistoricalKnowledgeWeaver',
        'statistics': stats,
        'modules': {name: {'injected': len(info['injected_knowledge']),
                          'state': info['runtime_state']}
                   for name, info in weaver.modules.items()},
        'activation_history_count': len(weaver.activation_history),
        'weave_log_count': len(weaver.weave_log)
    }

    report_path = '/mnt/agents/output/OMNI-HUB/core/hkw_experiment_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        logger.error(f"File operation failed: {e}")
    logger.info(f"\n报告已保存: {report_path}")

    return weaver, report


if __name__ == '__main__':
    weaver, report = run_experiment()
