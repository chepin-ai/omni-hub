#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v7.0 - ExternalKnowledgeFusion Module
===============================================
内外部知识动态融构系统

Architecture: ExternalKnowledgeFusion
- 突破内部知识限制，构建内外部知识动态融构系统
- 关键技术：外部接口调用、实时注入、交叉验证、Hebbian学习、自适应遗忘
- 安全处理：值永不入文原则

Author: OMNI-HUB Architecture Team
Version: 7.0.0
"""

import json
import time
import re
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading
import copy
import logging

# ============================================================================
# 工具接口层 - 外部搜索工具调用
# ============================================================================

class ExternalSearchInterface:
    """外部搜索工具接口"""
    
    @staticmethod
    def web_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        调用网络搜索工具获取外部知识
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            搜索结果列表
        """
        try:
            # 动态导入工具函数
            from mshtools import web_search
            results = web_search(query, max_results=max_results)
            return ExternalSearchInterface._normalize_web_results(results)
        except ImportError:
            return ExternalSearchInterface._mock_web_search(query, max_results)
        except Exception as e:
            logger.info(f"[ExternalSearch] web_search error: {e}")
            return []
    
    @staticmethod
    def scholar_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        调用学术论文搜索工具
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            学术论文结果列表
        """
        try:
            from mshtools import scholar
            results = scholar(query, top_n=max_results)
            return ExternalSearchInterface._normalize_scholar_results(results)
        except ImportError:
            return ExternalSearchInterface._mock_scholar_search(query, max_results)
        except Exception as e:
            logger.info(f"[ExternalSearch] scholar_search error: {e}")
            return []
    
    @staticmethod
    def image_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        调用图片搜索工具
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            图片搜索结果列表
        """
        try:
            from mshtools import search_image_by_text
            results = search_image_by_text(query, topn=max_results)
            return ExternalSearchInterface._normalize_image_results(results, query)
        except ImportError:
            return ExternalSearchInterface._mock_image_search(query, max_results)
        except Exception as e:
            logger.info(f"[ExternalSearch] image_search error: {e}")
            return []
    
    @staticmethod
    def open_url(url: str) -> Optional[str]:
        """
        打开网页获取详细内容
        
        Args:
            url: 网页URL
            
        Returns:
            网页内容文本
        """
        try:
            from mshtools import web_open_url
            return web_open_url(url)
        except ImportError:
            return None
        except Exception as e:
            logger.info(f"[ExternalSearch] open_url error: {e}")
            return None
    
    @staticmethod
    def _normalize_web_results(results: Any) -> List[Dict[str, Any]]:
        """标准化网页搜索结果"""
        normalized = []
        if isinstance(results, list):
            for r in results:
                if isinstance(r, dict):
                    normalized.append({
                        'source': 'web',
                        'title': r.get('title', ''),
                        'url': r.get('url', r.get('link', '')),
                        'content': r.get('content', r.get('snippet', '')),
                        'timestamp': datetime.now().isoformat(),
                        'credibility': 0.7,
                        'metadata': r
                    })
                elif isinstance(r, str):
                    normalized.append({
                        'source': 'web',
                        'title': r[:50],
                        'url': '',
                        'content': r,
                        'timestamp': datetime.now().isoformat(),
                        'credibility': 0.5,
                        'metadata': {}
                    })
        elif isinstance(results, dict):
            # 处理可能的字典格式结果
            for key, value in results.items():
                if isinstance(value, dict):
                    normalized.append({
                        'source': 'web',
                        'title': value.get('title', key),
                        'url': value.get('url', ''),
                        'content': value.get('content', str(value)),
                        'timestamp': datetime.now().isoformat(),
                        'credibility': 0.7,
                        'metadata': value
                    })
        return normalized
    
    @staticmethod
    def _normalize_scholar_results(results: Any) -> List[Dict[str, Any]]:
        """标准化学术搜索结果"""
        normalized = []
        if isinstance(results, list):
            for r in results:
                if isinstance(r, dict):
                    normalized.append({
                        'source': 'scholar',
                        'title': r.get('title', ''),
                        'url': r.get('url', r.get('link', '')),
                        'content': f"{r.get('abstract', '')} Authors: {r.get('authors', '')}",
                        'timestamp': datetime.now().isoformat(),
                        'credibility': 0.85,  # 学术论文可信度更高
                        'metadata': {
                            'authors': r.get('authors', ''),
                            'year': r.get('year', ''),
                            'citations': r.get('citations', 0),
                            'venue': r.get('venue', '')
                        }
                    })
        return normalized
    
    @staticmethod
    def _normalize_image_results(results: Any, query: str) -> List[Dict[str, Any]]:
        """标准化图片搜索结果"""
        normalized = []
        if isinstance(results, list):
            for i, r in enumerate(results):
                if isinstance(r, dict):
                    normalized.append({
                        'source': 'image',
                        'title': f"Image: {query}",
                        'url': r.get('url', r.get('link', '')),
                        'content': f"Visual content related to: {query}",
                        'timestamp': datetime.now().isoformat(),
                        'credibility': 0.6,
                        'metadata': r
                    })
                elif isinstance(r, str):
                    normalized.append({
                        'source': 'image',
                        'title': f"Image: {query}",
                        'url': r,
                        'content': f"Visual content related to: {query}",
                        'timestamp': datetime.now().isoformat(),
                        'credibility': 0.6,
                        'metadata': {'image_url': r}
                    })
        return normalized
    
    @staticmethod
    def _mock_web_search(query: str, max_results: int) -> List[Dict[str, Any]]:
        """模拟网页搜索（用于测试）"""
        logger.info(f"[Mock] Web search: '{query}'")
        return [{
            'source': 'web',
            'title': f"Web result for: {query}",
            'url': f"https://example.com/search?q={query.replace(' ', '+')}",
            'content': f"Simulated web search content for query: {query}",
            'timestamp': datetime.now().isoformat(),
            'credibility': 0.7,
            'metadata': {'mock': True}
        }]
    
    @staticmethod
    def _mock_scholar_search(query: str, max_results: int) -> List[Dict[str, Any]]:
        """模拟学术搜索（用于测试）"""
        logger.info(f"[Mock] Scholar search: '{query}'")
        return [{
            'source': 'scholar',
            'title': f"Academic paper on: {query}",
            'url': f"https://scholar.example.com/paper/{hashlib.md5(query.encode()).hexdigest()[:8]}",
            'content': f"Simulated academic abstract for: {query}",
            'timestamp': datetime.now().isoformat(),
            'credibility': 0.85,
            'metadata': {'mock': True, 'citations': random.randint(10, 1000)}
        }]
    
    @staticmethod
    def _mock_image_search(query: str, max_results: int) -> List[Dict[str, Any]]:
        """模拟图片搜索（用于测试）"""
        logger.info(f"[Mock] Image search: '{query}'")
        return [{
            'source': 'image',
            'title': f"Image for: {query}",
            'url': f"https://images.example.com/{hashlib.md5(query.encode()).hexdigest()[:8]}.jpg",
            'content': f"Visual content for: {query}",
            'timestamp': datetime.now().isoformat(),
            'credibility': 0.6,
            'metadata': {'mock': True}
        }]


# ============================================================================
# ExternalKnowledgeNode - 外部知识节点
# ============================================================================

@dataclass
class ExternalKnowledgeNode:
    """
    外部知识节点
    
    表示从外部来源获取的知识单元，包含来源追溯、可信度评估、
    时间戳和访问统计等元数据。
    """
    
    # 核心属性
    node_id: str
    source: str  # 'web', 'scholar', 'image', 'hybrid'
    url: str
    content: str
    title: str = ""
    
    # 时间属性
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 质量属性
    credibility: float = 0.5  # 0.0 - 1.0
    base_credibility: float = 0.5  # 基础可信度（由来源决定）
    
    # 融合属性
    fusion_count: int = 0  # 被融合的次数
    fusion_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 关联属性
    related_internal_nodes: List[str] = field(default_factory=list)
    related_external_nodes: List[str] = field(default_factory=list)
    
    # Hebbian学习属性
    activation_count: int = 0
    weight: float = 1.0
    last_activation: str = ""
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # 安全属性
    filtered: bool = False
    anonymized: bool = False
    compliance_checked: bool = False
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.node_id:
            self.node_id = self._generate_id()
        if not self.last_activation:
            self.last_activation = self.timestamp
    
    def _generate_id(self) -> str:
        """生成唯一节点ID"""
        content_hash = hashlib.md5(
            f"{self.source}:{self.url}:{self.content[:100]}".encode()
        ).hexdigest()[:12]
        return f"EXT_{self.source.upper()}_{content_hash}"
    
    def activate(self, strength: float = 1.0):
        """
        激活节点（Hebbian学习）
        
        Args:
            strength: 激活强度
        """
        self.activation_count += 1
        self.last_accessed = datetime.now().isoformat()
        self.last_activation = datetime.now().isoformat()
        # Hebbian更新: 频繁激活增加权重
        self.weight = min(2.0, self.weight + 0.1 * strength)
    
    def decay(self, decay_rate: float = 0.001):
        """
        时间衰减 - 旧知识可信度逐渐降低
        
        Args:
            decay_rate: 衰减率
        """
        try:
            ts = datetime.fromisoformat(self.timestamp)
            age_hours = (datetime.now() - ts).total_seconds() / 3600
            time_decay = max(0, 1.0 - decay_rate * age_hours)
            self.credibility = self.base_credibility * time_decay
        except:
            pass
    
    def fuse(self, internal_node_id: str, fusion_score: float):
        """
        记录融合事件
        
        Args:
            internal_node_id: 融合的内部节点ID
            fusion_score: 融合分数
        """
        self.fusion_count += 1
        self.fusion_history.append({
            'internal_node_id': internal_node_id,
            'fusion_score': fusion_score,
            'timestamp': datetime.now().isoformat()
        })
        if internal_node_id not in self.related_internal_nodes:
            self.related_internal_nodes.append(internal_node_id)
        # 融合增加可信度
        self.credibility = min(1.0, self.credibility + 0.05 * fusion_score)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExternalKnowledgeNode':
        """从字典反序列化"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def __repr__(self) -> str:
        return (f"<ExternalKnowledgeNode id={self.node_id} "
                f"source={self.source} credibility={self.credibility:.2f} "
                f"fusions={self.fusion_count} weight={self.weight:.2f}>")
    
    def __hash__(self):
        return hash(self.node_id)
    
    def __eq__(self, other):
        if isinstance(other, ExternalKnowledgeNode):
            return self.node_id == other.node_id
        return False


# ============================================================================
# KnowledgeFusionVerifier - 知识融合验证器
# ============================================================================

class KnowledgeFusionVerifier:
    """
    知识融合验证器
    
    负责验证内外部知识的一致性、检测冲突、解决冲突，
    并计算融合分数。
    """
    
    def __init__(self):
        self.consistency_threshold = 0.6
        self.conflict_threshold = 0.3
        self.fusion_history: List[Dict[str, Any]] = []
    
    def verify_consistency(self, internal: Dict[str, Any], 
                          external: ExternalKnowledgeNode) -> Dict[str, Any]:
        """
        验证内部知识与外部知识的一致性
        
        策略：
        1. 关键词重叠分析
        2. 语义相似度计算（简化版）
        3. 主题一致性检查
        
        Args:
            internal: 内部知识节点（字典格式）
            external: 外部知识节点
            
        Returns:
            一致性验证结果
        """
        internal_content = internal.get('content', '') or internal.get('description', '')
        external_content = external.content
        
        # 关键词提取和重叠
        internal_keywords = self._extract_keywords(internal_content)
        external_keywords = self._extract_keywords(external_content)
        
        if not internal_keywords or not external_keywords:
            overlap_score = 0.0
        else:
            overlap = len(internal_keywords & external_keywords)
            union = len(internal_keywords | external_keywords)
            overlap_score = overlap / union if union > 0 else 0.0
        
        # 语义相似度（基于词向量距离）
        semantic_score = self._compute_semantic_similarity(
            internal_content, external_content
        )
        
        # 主题一致性
        topic_score = self._check_topic_consistency(
            internal.get('tags', []), external.tags
        )
        
        # 综合一致性分数
        consistency_score = (
            0.4 * overlap_score +
            0.4 * semantic_score +
            0.2 * topic_score
        )
        
        is_consistent = consistency_score >= self.consistency_threshold
        
        result = {
            'is_consistent': is_consistent,
            'consistency_score': consistency_score,
            'overlap_score': overlap_score,
            'semantic_score': semantic_score,
            'topic_score': topic_score,
            'internal_keywords': list(internal_keywords),
            'external_keywords': list(external_keywords),
            'common_keywords': list(internal_keywords & external_keywords),
            'timestamp': datetime.now().isoformat()
        }
        
        self.fusion_history.append({
            'type': 'consistency_check',
            'result': result
        })
        
        return result
    
    def detect_conflict(self, internal: Dict[str, Any], 
                       external: ExternalKnowledgeNode) -> Dict[str, Any]:
        """
        检测内部知识与外部知识之间的冲突
        
        策略：
        1. 事实性冲突检测（数字、日期等）
        2. 逻辑矛盾检测
        3. 立场冲突检测
        
        Args:
            internal: 内部知识节点
            external: 外部知识节点
            
        Returns:
            冲突检测结果
        """
        internal_content = internal.get('content', '') or internal.get('description', '')
        external_content = external.content
        
        conflicts = []
        conflict_score = 0.0
        
        # 1. 数值冲突检测
        numerical_conflict = self._detect_numerical_conflict(
            internal_content, external_content
        )
        if numerical_conflict['has_conflict']:
            conflicts.append({
                'type': 'numerical',
                'details': numerical_conflict
            })
            conflict_score += numerical_conflict['severity']
        
        # 2. 否定词冲突检测
        negation_conflict = self._detect_negation_conflict(
            internal_content, external_content
        )
        if negation_conflict['has_conflict']:
            conflicts.append({
                'type': 'negation',
                'details': negation_conflict
            })
            conflict_score += negation_conflict['severity']
        
        # 3. 反义词冲突检测
        antonym_conflict = self._detect_antonym_conflict(
            internal_content, external_content
        )
        if antonym_conflict['has_conflict']:
            conflicts.append({
                'type': 'antonym',
                'details': antonym_conflict
            })
            conflict_score += antonym_conflict['severity']
        
        has_conflict = len(conflicts) > 0 and conflict_score > self.conflict_threshold
        
        result = {
            'has_conflict': has_conflict,
            'conflict_score': min(1.0, conflict_score),
            'conflicts': conflicts,
            'severity': 'high' if conflict_score > 0.7 else 'medium' if conflict_score > 0.3 else 'low',
            'timestamp': datetime.now().isoformat()
        }
        
        self.fusion_history.append({
            'type': 'conflict_detection',
            'result': result
        })
        
        return result
    
    def resolve_conflict(self, internal: Dict[str, Any], 
                        external: ExternalKnowledgeNode,
                        conflict_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        解决内部知识与外部知识之间的冲突
        
        策略：
        1. 高可信度来源优先
        2. 时间优先（新知识优先）
        3. 多源验证优先
        4. 保留分歧标记
        
        Args:
            internal: 内部知识节点
            external: 外部知识节点
            conflict_info: 冲突信息
            
        Returns:
            冲突解决结果
        """
        internal_credibility = internal.get('credibility', 0.5)
        external_credibility = external.credibility
        
        # 策略1: 高可信度优先
        if external_credibility > internal_credibility + 0.2:
            resolution = 'external_wins'
            winner = 'external'
            reason = f"External credibility ({external_credibility:.2f}) > Internal ({internal_credibility:.2f})"
        elif internal_credibility > external_credibility + 0.2:
            resolution = 'internal_wins'
            winner = 'internal'
            reason = f"Internal credibility ({internal_credibility:.2f}) > External ({external_credibility:.2f})"
        else:
            # 策略2: 检查时间
            internal_time = internal.get('timestamp', '')
            external_time = external.timestamp
            
            try:
                if external_time and internal_time:
                    ext_dt = datetime.fromisoformat(external_time)
                    int_dt = datetime.fromisoformat(internal_time)
                    if ext_dt > int_dt + timedelta(days=30):
                        resolution = 'external_wins_time'
                        winner = 'external'
                        reason = "External knowledge is newer"
                    elif int_dt > ext_dt + timedelta(days=30):
                        resolution = 'internal_wins_time'
                        winner = 'internal'
                        reason = "Internal knowledge is newer"
                    else:
                        resolution = 'merge'
                        winner = 'both'
                        reason = "Similar credibility and time - merge with conflict marker"
                else:
                    resolution = 'merge'
                    winner = 'both'
                    reason = "Insufficient time data - merge with conflict marker"
            except:
                resolution = 'merge'
                winner = 'both'
                reason = "Time parse error - merge with conflict marker"
        
        result = {
            'resolution': resolution,
            'winner': winner,
            'reason': reason,
            'internal_credibility': internal_credibility,
            'external_credibility': external_credibility,
            'conflict_marked': winner == 'both',
            'timestamp': datetime.now().isoformat()
        }
        
        self.fusion_history.append({
            'type': 'conflict_resolution',
            'result': result
        })
        
        return result
    
    def compute_fusion_score(self, internal: Dict[str, Any], 
                            external: ExternalKnowledgeNode) -> Dict[str, Any]:
        """
        计算知识融合分数
        
        融合分数综合考虑：
        1. 一致性分数 (0-1)
        2. 外部知识可信度 (0-1)
        3. 内部知识权重 (0-1)
        4. 冲突程度 (0-1, 反向)
        5. 来源多样性 (0-1)
        
        Args:
            internal: 内部知识节点
            external: 外部知识节点
            
        Returns:
            融合分数详情
        """
        # 一致性
        consistency = self.verify_consistency(internal, external)
        consistency_score = consistency['consistency_score']
        
        # 冲突
        conflict = self.detect_conflict(internal, external)
        conflict_penalty = conflict['conflict_score'] * 0.5
        
        # 外部可信度
        external_cred = external.credibility
        
        # 内部权重
        internal_weight = internal.get('weight', 0.5)
        
        # 来源多样性加分
        source_bonus = 0.1 if external.source == 'scholar' else 0.0
        
        # 综合融合分数
        fusion_score = (
            0.3 * consistency_score +
            0.3 * external_cred +
            0.2 * internal_weight +
            0.2 * (1.0 - conflict_penalty) +
            source_bonus
        )
        
        # 融合决策
        should_fuse = fusion_score > 0.5 and not conflict['has_conflict']
        needs_verification = 0.3 < fusion_score <= 0.5 or conflict['has_conflict']
        
        result = {
            'fusion_score': fusion_score,
            'should_fuse': should_fuse,
            'needs_verification': needs_verification,
            'consistency_score': consistency_score,
            'conflict_penalty': conflict_penalty,
            'external_credibility': external_cred,
            'internal_weight': internal_weight,
            'source_bonus': source_bonus,
            'decision': 'fuse' if should_fuse else 'verify' if needs_verification else 'reject',
            'timestamp': datetime.now().isoformat()
        }
        
        self.fusion_history.append({
            'type': 'fusion_score',
            'result': result
        })
        
        return result
    
    # ==================== 辅助方法 ====================
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """提取关键词"""
        if not text:
            return set()
        # 简化的关键词提取：去除停用词后的词频
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{2,}\b', text.lower())
        # 基础停用词
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
                     'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has',
                     'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see',
                     'two', 'who', 'boy', 'did', 'she', 'use', 'her', 'way', 'many',
                     'oil', 'sit', 'set', 'run', 'eat', 'far', 'sea', 'eye', 'ago',
                     'off', 'too', 'any', 'say', 'man', 'try', 'ask', 'end', 'why',
                     'let', 'put', 'say', 'she', 'try', 'way', 'own', 'say', 'too',
                     '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
                     '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
                     '你', '会', '着', '没有', '看', '好', '自己', '这'}
        keywords = set(w for w in words if w not in stopwords and len(w) > 2)
        return keywords
    
    def _compute_semantic_similarity(self, text1: str, text2: str) -> float:
        """计算语义相似度（基于词袋模型）"""
        words1 = set(re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{2,}\b', text1.lower()))
        words2 = set(re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{2,}\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _check_topic_consistency(self, internal_tags: List[str], 
                                  external_tags: List[str]) -> float:
        """检查主题一致性"""
        if not internal_tags or not external_tags:
            return 0.5  # 中性
        
        internal_set = set(t.lower() for t in internal_tags)
        external_set = set(t.lower() for t in external_tags)
        
        overlap = len(internal_set & external_set)
        union = len(internal_set | external_set)
        
        return overlap / union if union > 0 else 0.0
    
    def _detect_numerical_conflict(self, text1: str, text2: str) -> Dict[str, Any]:
        """检测数值冲突"""
        # 提取数字
        nums1 = re.findall(r'\b\d+(?:\.\d+)?\b', text1)
        nums2 = re.findall(r'\b\d+(?:\.\d+)?\b', text2)
        
        if not nums1 or not nums2:
            return {'has_conflict': False, 'severity': 0.0}
        
        # 简化的数值冲突检测
        # 如果两个文本都有数字但完全不匹配，可能存在冲突
        set1 = set(nums1)
        set2 = set(nums2)
        
        if set1 and set2 and not (set1 & set2):
            return {'has_conflict': True, 'severity': 0.3, 'type': 'no_common_numbers'}
        
        return {'has_conflict': False, 'severity': 0.0}
    
    def _detect_negation_conflict(self, text1: str, text2: str) -> Dict[str, Any]:
        """检测否定词冲突"""
        negations = ['not', 'no', 'never', 'none', 'without', 'not', 'false',
                     '不', '没有', '无', '未', '否', '不是']
        
        has_neg1 = any(n in text1.lower() for n in negations)
        has_neg2 = any(n in text2.lower() for n in negations)
        
        if has_neg1 != has_neg2:
            return {'has_conflict': True, 'severity': 0.4, 'type': 'negation_mismatch'}
        
        return {'has_conflict': False, 'severity': 0.0}
    
    def _detect_antonym_conflict(self, text1: str, text2: str) -> Dict[str, Any]:
        """检测反义词冲突"""
        antonyms = [
            ('increase', 'decrease'), ('high', 'low'), ('large', 'small'),
            ('good', 'bad'), ('success', 'failure'), ('hot', 'cold'),
            ('fast', 'slow'), ('strong', 'weak'), ('positive', 'negative'),
            ('上升', '下降'), ('增加', '减少'), ('好', '坏'), ('大', '小')
        ]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        for pair in antonyms:
            if (pair[0] in text1_lower and pair[1] in text2_lower) or \
               (pair[1] in text1_lower and pair[0] in text2_lower):
                return {'has_conflict': True, 'severity': 0.5, 'type': f'antonym:{pair[0]}'}
        
        return {'has_conflict': False, 'severity': 0.0}


# ============================================================================
# SecureKnowledgeFilter - 安全知识过滤器
# ============================================================================

class SecureKnowledgeFilter:
    """
    安全知识过滤器
    
    遵循"值永不入文"原则：
    1. 外部知识中的具体数值不嵌入代码
    2. 匿名化处理：去除个人/组织标识
    3. 来源追溯：每个外部知识节点记录来源
    4. 合规检查：符合数据使用规范
    """
    
    # 敏感模式 - 用于检测敏感信息
    SENSITIVE_PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
        'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
        'api_key': re.compile(r'\b(?:api[_-]?key|token|secret)[\s]*[:=][\s]*["\']?[a-zA-Z0-9]{16,}["\']?\b', re.IGNORECASE),
    }
    
    # 个人身份信息 (PII)
    PII_PATTERNS = {
        'person_name': re.compile(r'\b(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)\s+[A-Z][a-z]+\b'),
        'organization': re.compile(r'\b(?:Inc\.?|Corp\.?|Ltd\.?|LLC|Company)\b'),
    }
    
    # 合规关键词
    COMPLIANCE_KEYWORDS = [
        'classified', 'confidential', 'proprietary', 'restricted',
        'internal_use_only', 'trade_secret', 'non_disclosure',
        '机密', '内部资料', '禁止外传'
    ]
    
    def __init__(self):
        self.filter_stats = {
            'total_filtered': 0,
            'sensitive_found': 0,
            'anonymized': 0,
            'compliance_violations': 0
        }
        self.filtered_log: List[Dict[str, Any]] = []
    
    def filter_sensitive(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """
        过滤敏感内容
        
        策略：
        1. 检测并标记敏感信息类型
        2. 替换敏感内容为占位符
        3. 记录过滤日志
        
        Args:
            content: 原始内容
            
        Returns:
            (过滤后内容, 过滤详情)
        """
        if not content:
            return content, {'filtered': False, 'types': []}
        
        filtered_content = content
        found_types = []
        replacements = []
        
        for name, pattern in self.SENSITIVE_PATTERNS.items():
            matches = list(pattern.finditer(content))
            if matches:
                found_types.append(name)
                for i, match in enumerate(matches):
                    placeholder = f"[{name.upper()}_{i+1}]"
                    filtered_content = filtered_content.replace(match.group(), placeholder, 1)
                    replacements.append({
                        'type': name,
                        'original_length': len(match.group()),
                        'placeholder': placeholder
                    })
        
        is_filtered = len(found_types) > 0
        if is_filtered:
            self.filter_stats['total_filtered'] += 1
            self.filter_stats['sensitive_found'] += len(found_types)
        
        result = {
            'filtered': is_filtered,
            'types': found_types,
            'replacements': replacements,
            'original_length': len(content),
            'filtered_length': len(filtered_content)
        }
        
        if is_filtered:
            self.filtered_log.append({
                'action': 'filter_sensitive',
                'types': found_types,
                'timestamp': datetime.now().isoformat()
            })
        
        return filtered_content, result
    
    def anonymize(self, content: str, preserve_structure: bool = True) -> Tuple[str, Dict[str, Any]]:
        """
        匿名化处理
        
        策略：
        1. 替换人名为通用标识
        2. 替换组织名为通用标识
        3. 保留知识结构，去除身份标识
        
        Args:
            content: 原始内容
            preserve_structure: 是否保留句子结构
            
        Returns:
            (匿名化后内容, 匿名化详情)
        """
        if not content:
            return content, {'anonymized': False}
        
        anonymized = content
        replacements = []
        
        # 人名替换
        name_counter = 0
        for match in self.PII_PATTERNS['person_name'].finditer(content):
            name_counter += 1
            replacement = f"[PERSON_{name_counter}]"
            anonymized = anonymized.replace(match.group(), replacement, 1)
            replacements.append({
                'type': 'person_name',
                'original': match.group(),
                'replacement': replacement
            })
        
        # 组织名替换
        org_counter = 0
        for match in self.PII_PATTERNS['organization'].finditer(content):
            org_counter += 1
            replacement = f"[ORGANIZATION_{org_counter}]"
            anonymized = anonymized.replace(match.group(), replacement, 1)
            replacements.append({
                'type': 'organization',
                'original': match.group(),
                'replacement': replacement
            })
        
        # 通用实体替换（大写词组可能是专有名词）
        if preserve_structure:
            # 保留结构，只替换明确的PII
            pass
        
        is_anonymized = len(replacements) > 0
        if is_anonymized:
            self.filter_stats['anonymized'] += 1
        
        result = {
            'anonymized': is_anonymized,
            'replacements': replacements,
            'person_count': name_counter,
            'organization_count': org_counter
        }
        
        if is_anonymized:
            self.filtered_log.append({
                'action': 'anonymize',
                'replacements': len(replacements),
                'timestamp': datetime.now().isoformat()
            })
        
        return anonymized, result
    
    def check_compliance(self, content: str, source: str = '') -> Dict[str, Any]:
        """
        合规检查
        
        策略：
        1. 检查合规关键词
        2. 检查数据来源合规性
        3. 验证使用权限
        
        Args:
            content: 内容
            source: 来源标识
            
        Returns:
            合规检查结果
        """
        if not content:
            return {'compliant': True, 'violations': []}
        
        violations = []
        content_lower = content.lower()
        
        # 检查合规关键词
        for keyword in self.COMPLIANCE_KEYWORDS:
            if keyword.lower() in content_lower:
                violations.append({
                    'type': 'compliance_keyword',
                    'keyword': keyword,
                    'severity': 'high'
                })
        
        # 检查来源合规性
        if source:
            # 模拟来源合规检查
            if any(bad in source.lower() for bad in ['unauthorized', 'leaked', 'stolen']):
                violations.append({
                    'type': 'source_compliance',
                    'source': source,
                    'severity': 'critical'
                })
        
        # 检查内容长度合规性（防止过大内容）
        if len(content) > 100000:  # 100KB限制
            violations.append({
                'type': 'size_compliance',
                'size': len(content),
                'limit': 100000,
                'severity': 'medium'
            })
        
        is_compliant = len(violations) == 0
        
        if not is_compliant:
            self.filter_stats['compliance_violations'] += len(violations)
            self.filtered_log.append({
                'action': 'compliance_check',
                'violations': len(violations),
                'timestamp': datetime.now().isoformat()
            })
        
        return {
            'compliant': is_compliant,
            'violations': violations,
            'violation_count': len(violations),
            'severity': 'critical' if any(v['severity'] == 'critical' for v in violations) else
                       'high' if any(v['severity'] == 'high' for v in violations) else 'low'
        }
    
    def apply_all_filters(self, content: str, source: str = '') -> Tuple[str, Dict[str, Any]]:
        """
        应用所有安全过滤器
        
        执行顺序：
        1. 合规检查
        2. 敏感内容过滤
        3. 匿名化处理
        
        Args:
            content: 原始内容
            source: 来源
            
        Returns:
            (处理后内容, 完整过滤报告)
        """
        report = {
            'original_length': len(content),
            'filters_applied': [],
            'compliance': None,
            'sensitive': None,
            'anonymization': None,
            'safe': True
        }
        
        # 1. 合规检查
        compliance = self.check_compliance(content, source)
        report['compliance'] = compliance
        report['filters_applied'].append('compliance')
        
        if not compliance['compliant'] and compliance['severity'] == 'critical':
            report['safe'] = False
            report['blocked'] = True
            report['block_reason'] = 'Critical compliance violation'
            return "", report
        
        # 2. 敏感内容过滤
        filtered_content, sensitive_info = self.filter_sensitive(content)
        report['sensitive'] = sensitive_info
        report['filters_applied'].append('sensitive')
        
        # 3. 匿名化处理
        anonymized_content, anon_info = self.anonymize(filtered_content)
        report['anonymization'] = anon_info
        report['filters_applied'].append('anonymization')
        
        report['final_length'] = len(anonymized_content)
        report['reduction_ratio'] = 1 - (len(anonymized_content) / len(content)) if content else 0
        
        return anonymized_content, report
    
    def get_stats(self) -> Dict[str, Any]:
        """获取过滤统计"""
        return {
            **self.filter_stats,
            'log_entries': len(self.filtered_log),
            'last_updated': datetime.now().isoformat()
        }


# ============================================================================
# ExternalKnowledgeFusion - 内外部知识融构引擎
# ============================================================================

class ExternalKnowledgeFusion:
    """
    内外部知识融构引擎
    
    核心功能：
    1. 加载内部知识（从HistoricalKnowledgeWeaver）
    2. 外部搜索和获取
    3. 知识融合（内部为主，外部为辅）
    4. 交叉验证
    5. 运行时注入
    6. Hebbian学习更新
    7. 自适应遗忘
    """
    
    def __init__(self, internal_knowledge_path: Optional[str] = None, 
                 max_external_nodes: int = 1000):
        """
        初始化融构引擎
        
        Args:
            internal_knowledge_path: 内部知识图谱文件路径
            max_external_nodes: 外部知识节点上限
        """
        self.max_external_nodes = max_external_nodes
        self.lock = threading.RLock()
        
        # 内部知识存储
        self.internal_knowledge: Dict[str, Dict[str, Any]] = {}
        self.internal_knowledge_graph: Dict[str, Any] = {}
        
        # 外部知识存储
        self.external_nodes: Dict[str, ExternalKnowledgeNode] = {}
        self.external_index: Dict[str, Set[str]] = defaultdict(set)  # 关键词索引
        
        # 融合知识存储
        self.fused_knowledge: Dict[str, Dict[str, Any]] = {}
        self.fusion_edges: List[Dict[str, Any]] = []
        
        # 运行时注入记录
        self.runtime_injections: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # 工具组件
        self.search_interface = ExternalSearchInterface()
        self.verifier = KnowledgeFusionVerifier()
        self.security_filter = SecureKnowledgeFilter()
        
        # Hebbian学习参数
        self.hebbian_learning_rate = 0.1
        self.hebbian_decay = 0.001
        
        # 统计
        self.stats = {
            'searches_performed': 0,
            'external_nodes_added': 0,
            'fusions_completed': 0,
            'verifications_done': 0,
            'injections_done': 0,
            'hebbian_updates': 0,
            'nodes_forgotten': 0
        }
        
        # 加载内部知识
        if internal_knowledge_path:
            self._load_internal_knowledge(internal_knowledge_path)
        else:
            self._init_default_internal_knowledge()
    
    def _load_internal_knowledge(self, path: str):
        """加载内部知识图谱"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.internal_knowledge_graph = data
            
            # 提取节点
            nodes = data.get('nodes', [])
            for node in nodes:
                node_id = node.get('id', node.get('node_id', ''))
                if node_id:
                    self.internal_knowledge[node_id] = node
            
            logger.info(f"[InternalKnowledge] Loaded {len(self.internal_knowledge)} nodes from {path}")
        except Exception as e:
            logger.info(f"[InternalKnowledge] Failed to load from {path}: {e}")
            self._init_default_internal_knowledge()
    
    def _init_default_internal_knowledge(self):
        """初始化默认内部知识（基于ucif2历史研究327节点）"""
        logger.info("[InternalKnowledge] Initializing default knowledge base...")
        
        # 模拟ucif2历史研究节点
        default_nodes = [
            {
                'id': 'ucif2_root',
                'label': 'UCIF2 Historical Research',
                'content': 'UCIF2 historical research project containing 327 nodes of interconnected knowledge',
                'tags': ['ucif2', 'history', 'research'],
                'credibility': 0.95,
                'weight': 1.0
            },
            {
                'id': 'ucif2_knowledge_graph',
                'label': 'Knowledge Graph Structure',
                'content': 'The knowledge graph contains 327 interconnected nodes representing historical research data',
                'tags': ['graph', 'structure', 'nodes'],
                'credibility': 0.9,
                'weight': 0.9
            },
            {
                'id': 'ai_ethics',
                'label': 'AI Ethics Principles',
                'content': 'Artificial intelligence ethics principles including fairness, transparency, accountability, and privacy protection',
                'tags': ['ai', 'ethics', 'principles'],
                'credibility': 0.85,
                'weight': 0.8
            },
            {
                'id': 'knowledge_fusion',
                'label': 'Knowledge Fusion Methodology',
                'content': 'Methodology for fusing internal and external knowledge sources with cross-verification',
                'tags': ['fusion', 'methodology', 'verification'],
                'credibility': 0.88,
                'weight': 0.85
            },
            {
                'id': 'hebbian_learning',
                'label': 'Hebbian Learning Theory',
                'content': 'Hebbian learning principle: neurons that fire together wire together. Applied to knowledge graph weight updates',
                'tags': ['hebbian', 'learning', 'neural'],
                'credibility': 0.9,
                'weight': 0.8
            },
            {
                'id': 'adaptive_forgetting',
                'label': 'Adaptive Forgetting Mechanism',
                'content': 'Mechanism for gradually forgetting low-weight, rarely activated knowledge nodes to maintain system efficiency',
                'tags': ['forgetting', 'adaptive', 'mechanism'],
                'credibility': 0.82,
                'weight': 0.75
            },
            {
                'id': 'data_security',
                'label': 'Data Security Principles',
                'content': 'Security principles including value-never-in-text, anonymization, source tracing, and compliance checking',
                'tags': ['security', 'privacy', 'compliance'],
                'credibility': 0.92,
                'weight': 0.9
            },
            {
                'id': 'omni_hub_architecture',
                'label': 'OMNI-HUB Architecture',
                'content': 'OMNI-HUB system architecture with multiple modules including ExternalKnowledgeFusion, HistoricalKnowledgeWeaver, and others',
                'tags': ['architecture', 'system', 'omni-hub'],
                'credibility': 0.95,
                'weight': 1.0
            }
        ]
        
        for node in default_nodes:
            self.internal_knowledge[node['id']] = node
        
        self.internal_knowledge_graph = {
            'nodes': default_nodes,
            'edges': [
                {'source': 'ucif2_root', 'target': 'ucif2_knowledge_graph', 'weight': 0.9},
                {'source': 'ucif2_root', 'target': 'knowledge_fusion', 'weight': 0.7},
                {'source': 'knowledge_fusion', 'target': 'hebbian_learning', 'weight': 0.6},
                {'source': 'knowledge_fusion', 'target': 'adaptive_forgetting', 'weight': 0.6},
                {'source': 'omni_hub_architecture', 'target': 'data_security', 'weight': 0.8},
                {'source': 'omni_hub_architecture', 'target': 'knowledge_fusion', 'weight': 0.85},
                {'source': 'ai_ethics', 'target': 'data_security', 'weight': 0.75}
            ],
            'metadata': {
                'total_nodes': len(default_nodes),
                'version': '7.0.0',
                'created': datetime.now().isoformat()
            }
        }
        
        logger.info(f"[InternalKnowledge] Initialized {len(self.internal_knowledge)} default nodes")
    
    def search_external(self, query: str, sources: List[str] = None, 
                       max_results: int = 10) -> List[Dict[str, Any]]:
        """
        外部搜索
        
        调用外部搜索工具获取知识，支持多种来源：
        - web: 网页搜索
        - scholar: 学术论文
        - image: 图片搜索
        
        Args:
            query: 搜索查询
            sources: 来源列表，默认 ['web', 'scholar']
            max_results: 每个来源的最大结果数
            
        Returns:
            结构化的搜索结果列表
        """
        if sources is None:
            sources = ['web', 'scholar']
        
        logger.info(f"[ExternalSearch] Query: '{query}' | Sources: {sources} | Max: {max_results}")
        
        all_results = []
        
        for source in sources:
            try:
                if source == 'web':
                    results = self.search_interface.web_search(query, max_results)
                elif source == 'scholar':
                    results = self.search_interface.scholar_search(query, max_results)
                elif source == 'image':
                    results = self.search_interface.image_search(query, max_results)
                else:
                    logger.info(f"[ExternalSearch] Unknown source: {source}")
                    continue
                
                # 安全过滤
                for r in results:
                    content = r.get('content', '')
                    filtered_content, filter_report = self.security_filter.apply_all_filters(
                        content, source=r.get('source', '')
                    )
                    r['content'] = filtered_content
                    r['filter_report'] = filter_report
                    r['query'] = query
                    r['search_source'] = source
                
                all_results.extend(results)
                logger.info(f"[ExternalSearch] {source}: {len(results)} results")
                
            except Exception as e:
                logger.info(f"[ExternalSearch] Error searching {source}: {e}")
        
        self.stats['searches_performed'] += 1
        
        # 去重和排序
        seen_urls = set()
        unique_results = []
        for r in all_results:
            url = r.get('url', '')
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            unique_results.append(r)
        
        # 按可信度排序
        unique_results.sort(key=lambda x: x.get('credibility', 0), reverse=True)
        
        return unique_results[:max_results * len(sources)]
    
    def fuse_knowledge(self, internal_node_id: str, 
                      external_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        知识融合
        
        将外部知识与内部知识节点融合：
        1. 内部知识为主，外部知识为辅
        2. 外部知识需要交叉验证才能进入核心
        3. 冲突时：高可信度来源优先
        4. 时间衰减：旧知识可信度逐渐降低
        
        Args:
            internal_node_id: 内部知识节点ID
            external_results: 外部搜索结果列表
            
        Returns:
            融合结果
        """
        with self.lock:
            if internal_node_id not in self.internal_knowledge:
                return {'success': False, 'error': f'Internal node {internal_node_id} not found'}
            
            internal_node = self.internal_knowledge[internal_node_id]
            fusion_records = []
            fused_external_ids = []
            
            for ext_result in external_results:
                # 创建外部知识节点
                ext_node = ExternalKnowledgeNode(
                    node_id='',
                    source=ext_result.get('source', 'unknown'),
                    url=ext_result.get('url', ''),
                    content=ext_result.get('content', ''),
                    title=ext_result.get('title', ''),
                    credibility=ext_result.get('credibility', 0.5),
                    base_credibility=ext_result.get('credibility', 0.5),
                    metadata=ext_result.get('metadata', {}),
                    tags=ext_result.get('search_source', '')
                )
                
                # 检查是否已存在
                if ext_node.node_id in self.external_nodes:
                    ext_node = self.external_nodes[ext_node.node_id]
                    ext_node.activate()
                else:
                    # 检查容量限制
                    if len(self.external_nodes) >= self.max_external_nodes:
                        # 执行自适应遗忘
                        self.adaptive_forget()
                    
                    self.external_nodes[ext_node.node_id] = ext_node
                    self.stats['external_nodes_added'] += 1
                
                # 计算融合分数
                fusion_score = self.verifier.compute_fusion_score(internal_node, ext_node)
                
                if fusion_score['should_fuse']:
                    # 执行融合
                    ext_node.fuse(internal_node_id, fusion_score['fusion_score'])
                    
                    fusion_record = {
                        'internal_node_id': internal_node_id,
                        'external_node_id': ext_node.node_id,
                        'fusion_score': fusion_score['fusion_score'],
                        'timestamp': datetime.now().isoformat()
                    }
                    fusion_records.append(fusion_record)
                    self.fusion_edges.append(fusion_record)
                    fused_external_ids.append(ext_node.node_id)
                    
                    # 更新索引
                    keywords = self.verifier._extract_keywords(ext_node.content)
                    for kw in keywords:
                        self.external_index[kw].add(ext_node.node_id)
                    
                elif fusion_score['needs_verification']:
                    # 需要进一步验证
                    print(f"[Fusion] External node {ext_node.node_id} needs verification "
                          f"(score: {fusion_score['fusion_score']:.2f})")
                else:
                    # 拒绝融合
                    print(f"[Fusion] External node {ext_node.node_id} rejected "
                          f"(score: {fusion_score['fusion_score']:.2f})")
            
            # 更新融合知识
            if fusion_records:
                self.fused_knowledge[internal_node_id] = {
                    'internal_node': internal_node,
                    'fused_external_ids': fused_external_ids,
                    'fusion_records': fusion_records,
                    'fusion_timestamp': datetime.now().isoformat(),
                    'fusion_count': len(fusion_records)
                }
                self.stats['fusions_completed'] += len(fusion_records)
            
            return {
                'success': True,
                'internal_node_id': internal_node_id,
                'fusion_records': fusion_records,
                'fused_count': len(fusion_records),
                'total_external': len(external_results)
            }
    
    def cross_verify(self, internal_claim: str, 
                    external_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        交叉验证
        
        用外部来源验证内部知识声明：
        1. 多源验证提高可信度
        2. 一致性检查
        3. 可信度加权投票
        
        Args:
            internal_claim: 内部知识声明文本
            external_sources: 外部来源列表
            
        Returns:
            验证结果和可信度
        """
        if not external_sources:
            return {
                'verified': False,
                'confidence': 0.0,
                'reason': 'No external sources provided'
            }
        
        votes = []
        total_weight = 0.0
        
        for source in external_sources:
            # 创建临时节点进行验证
            temp_node = ExternalKnowledgeNode(
                node_id='temp',
                source=source.get('source', 'unknown'),
                url=source.get('url', ''),
                content=source.get('content', ''),
                title=source.get('title', ''),
                credibility=source.get('credibility', 0.5)
            )
            
            # 语义相似度
            similarity = self.verifier._compute_semantic_similarity(
                internal_claim, temp_node.content
            )
            
            # 可信度加权
            weight = temp_node.credibility
            vote = similarity * weight
            
            votes.append({
                'source': temp_node.source,
                'similarity': similarity,
                'credibility': temp_node.credibility,
                'vote': vote,
                'url': temp_node.url
            })
            
            total_weight += weight
        
        # 计算加权平均验证分数
        if total_weight > 0:
            avg_vote = sum(v['vote'] for v in votes) / total_weight
        else:
            avg_vote = 0.0
        
        # 一致性检查
        similarities = [v['similarity'] for v in votes]
        consistency = 1.0 - (max(similarities) - min(similarities)) if similarities else 0.0
        
        # 最终可信度
        confidence = avg_vote * (0.5 + 0.5 * consistency)
        
        # 验证阈值
        verified = confidence > 0.5 and len(votes) >= 2
        
        self.stats['verifications_done'] += 1
        
        return {
            'verified': verified,
            'confidence': confidence,
            'avg_similarity': avg_vote,
            'consistency': consistency,
            'vote_count': len(votes),
            'votes': votes,
            'threshold': 0.5
        }
    
    def inject_into_runtime(self, module_name: str, 
                           knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """
        注入运行时
        
        将融合后的知识注入指定模块运行时
        
        Args:
            module_name: 目标模块名称
            knowledge: 要注入的知识
            
        Returns:
            注入结果
        """
        injection_record = {
            'module': module_name,
            'knowledge_id': knowledge.get('id', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'knowledge_summary': str(knowledge)[:200]
        }
        
        self.runtime_injections[module_name].append(injection_record)
        self.stats['injections_done'] += 1
        
        logger.info(f"[RuntimeInjection] Injected knowledge into module: {module_name}")
        
        return {
            'success': True,
            'module': module_name,
            'injection_id': hashlib.md5(
                f"{module_name}:{time.time()}".encode()
            ).hexdigest()[:12],
            'timestamp': injection_record['timestamp']
        }
    
    def hebbian_update(self, node_id: str, activation: float = 1.0) -> Dict[str, Any]:
        """
        Hebbian学习更新
        
        根据激活频率更新知识权重：
        - 频繁激活的知识权重增加
        - 遵循"一起激发的神经元连在一起"原则
        
        Args:
            node_id: 节点ID（可以是内部或外部节点）
            activation: 激活强度 (0.0 - 1.0)
            
        Returns:
            更新结果
        """
        with self.lock:
            updated_nodes = []
            
            # 更新内部节点
            if node_id in self.internal_knowledge:
                node = self.internal_knowledge[node_id]
                old_weight = node.get('weight', 1.0)
                # Hebbian规则: w_new = w_old + lr * activation
                new_weight = old_weight + self.hebbian_learning_rate * activation
                node['weight'] = min(2.0, new_weight)
                node['last_activation'] = datetime.now().isoformat()
                updated_nodes.append({
                    'type': 'internal',
                    'id': node_id,
                    'old_weight': old_weight,
                    'new_weight': node['weight']
                })
            
            # 更新外部节点
            if node_id in self.external_nodes:
                ext_node = self.external_nodes[node_id]
                old_weight = ext_node.weight
                ext_node.weight = min(2.0, old_weight + self.hebbian_learning_rate * activation)
                ext_node.activate(activation)
                updated_nodes.append({
                    'type': 'external',
                    'id': node_id,
                    'old_weight': old_weight,
                    'new_weight': ext_node.weight
                })
            
            # 关联节点也获得小幅度更新（协同激活）
            if node_id in self.internal_knowledge:
                for edge in self.internal_knowledge_graph.get('edges', []):
                    if edge.get('source') == node_id:
                        target_id = edge.get('target')
                        if target_id in self.internal_knowledge:
                            target = self.internal_knowledge[target_id]
                            old_w = target.get('weight', 1.0)
                            target['weight'] = min(2.0, old_w + 0.05 * activation)
                            updated_nodes.append({
                                'type': 'internal_associated',
                                'id': target_id,
                                'old_weight': old_w,
                                'new_weight': target['weight']
                            })
            
            self.stats['hebbian_updates'] += len(updated_nodes)
            
            return {
                'updated': len(updated_nodes) > 0,
                'node_id': node_id,
                'activation': activation,
                'updated_nodes': updated_nodes
            }
    
    def adaptive_forget(self, threshold: float = 0.01) -> Dict[str, Any]:
        """
        自适应遗忘
        
        遗忘长期未激活的低权重知识：
        1. 计算每个节点的遗忘分数
        2. 分数 = 权重 * 时间衰减 * 激活频率
        3. 低于阈值的节点被标记为遗忘
        
        Args:
            threshold: 遗忘阈值
            
        Returns:
            遗忘结果
        """
        with self.lock:
            forgotten = []
            
            # 处理外部节点
            nodes_to_remove = []
            for node_id, node in self.external_nodes.items():
                # 计算遗忘分数
                time_since_access = 0
                try:
                    last_access = datetime.fromisoformat(node.last_accessed)
                    time_since_access = (datetime.now() - last_access).total_seconds() / 3600  # hours
                except:
                    time_since_access = 9999
                
                # 遗忘分数公式
                forget_score = (
                    node.weight * 
                    (1.0 / (1.0 + time_since_access * 0.01)) * 
                    min(1.0, node.activation_count / 10.0)
                )
                
                if forget_score < threshold and node.fusion_count == 0:
                    nodes_to_remove.append(node_id)
                    forgotten.append({
                        'id': node_id,
                        'type': 'external',
                        'forget_score': forget_score,
                        'weight': node.weight,
                        'time_since_access_hours': time_since_access,
                        'activation_count': node.activation_count
                    })
            
            # 执行遗忘
            for node_id in nodes_to_remove:
                del self.external_nodes[node_id]
                # 清理索引
                for kw_set in self.external_index.values():
                    kw_set.discard(node_id)
            
            self.stats['nodes_forgotten'] += len(forgotten)
            
            return {
                'forgotten_count': len(forgotten),
                'threshold': threshold,
                'forgotten_nodes': forgotten,
                'remaining_nodes': len(self.external_nodes)
            }
    
    def get_fused_knowledge_graph(self) -> Dict[str, Any]:
        """
        获取融合知识图谱
        
        Returns:
            完整的融合知识图谱
        """
        # 构建融合图谱
        fused_nodes = []
        
        # 添加内部节点
        for node_id, node in self.internal_knowledge.items():
            fused_nodes.append({
                'id': node_id,
                'type': 'internal',
                'label': node.get('label', node_id),
                'content': node.get('content', ''),
                'credibility': node.get('credibility', 0.5),
                'weight': node.get('weight', 1.0),
                'tags': node.get('tags', [])
            })
        
        # 添加外部节点
        for node_id, node in self.external_nodes.items():
            fused_nodes.append({
                'id': node_id,
                'type': 'external',
                'label': node.title[:50] if node.title else node_id,
                'content': node.content[:200] if node.content else '',
                'credibility': node.credibility,
                'weight': node.weight,
                'source': node.source,
                'fusion_count': node.fusion_count,
                'tags': node.tags
            })
        
        # 构建边
        edges = []
        
        # 内部边
        for edge in self.internal_knowledge_graph.get('edges', []):
            edges.append({
                'source': edge.get('source'),
                'target': edge.get('target'),
                'type': 'internal',
                'weight': edge.get('weight', 0.5)
            })
        
        # 融合边
        for fusion_edge in self.fusion_edges:
            edges.append({
                'source': fusion_edge['internal_node_id'],
                'target': fusion_edge['external_node_id'],
                'type': 'fusion',
                'weight': fusion_edge['fusion_score']
            })
        
        return {
            'nodes': fused_nodes,
            'edges': edges,
            'metadata': {
                'total_nodes': len(fused_nodes),
                'internal_nodes': len(self.internal_knowledge),
                'external_nodes': len(self.external_nodes),
                'total_edges': len(edges),
                'fusion_edges': len(self.fusion_edges),
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            系统统计
        """
        return {
            'system': self.stats,
            'knowledge': {
                'internal_nodes': len(self.internal_knowledge),
                'external_nodes': len(self.external_nodes),
                'fused_knowledge': len(self.fused_knowledge),
                'fusion_edges': len(self.fusion_edges),
                'runtime_injections': sum(len(v) for v in self.runtime_injections.values())
            },
            'security': self.security_filter.get_stats(),
            'verifier': {
                'history_entries': len(self.verifier.fusion_history)
            },
            'memory': {
                'external_index_entries': len(self.external_index),
                'external_nodes_capacity': self.max_external_nodes,
                'capacity_usage': len(self.external_nodes) / self.max_external_nodes if self.max_external_nodes > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_external_node(self, node_id: str) -> Optional[ExternalKnowledgeNode]:
        """获取外部知识节点"""
        return self.external_nodes.get(node_id)
    
    def get_internal_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取内部知识节点"""
        return self.internal_knowledge.get(node_id)
    
    def search_external_by_keyword(self, keyword: str) -> List[ExternalKnowledgeNode]:
        """通过关键词搜索外部节点"""
        node_ids = self.external_index.get(keyword.lower(), set())
        return [self.external_nodes[nid] for nid in node_ids if nid in self.external_nodes]


# ============================================================================
# 实验验证
# ============================================================================

def run_experiments():
    """
    运行实验验证
    
    实验内容：
    1. 搜索3个不同主题的外部知识
    2. 与内部知识融合
    3. 执行交叉验证
    4. 测试Hebbian学习和遗忘
    5. 返回融合后的知识图谱统计
    """
    logger.info("=" * 80)
    logger.info("OMNI-HUB v7.0 ExternalKnowledgeFusion - Experiment Validation")
    logger.info("=" * 80)
    logger.info(str())
    
    # 初始化引擎
    logger.info("[Experiment] Initializing ExternalKnowledgeFusion engine...")
    engine = ExternalKnowledgeFusion(
        internal_knowledge_path=None,  # 使用默认知识
        max_external_nodes=100
    )
    logger.info(f"[Experiment] Engine initialized with {len(engine.internal_knowledge)} internal nodes")
    logger.info(str())
    
    # =========================================================================
    # 实验1: 搜索3个不同主题
    # =========================================================================
    logger.info("-" * 80)
    logger.info("EXPERIMENT 1: External Knowledge Search (3 Topics)")
    logger.info("-" * 80)
    
    topics = [
        "artificial intelligence ethics 2024",
        "knowledge graph neural networks",
        "Hebbian learning deep learning"
    ]
    
    all_search_results = {}
    
    for i, topic in enumerate(topics, 1):
        logger.info(f"\n[Topic {i}/3] Searching: '{topic}'")
        results = engine.search_external(
            query=topic,
            sources=['web', 'scholar'],
            max_results=5
        )
        all_search_results[topic] = results
        logger.info(f"  -> Found {len(results)} results")
        for j, r in enumerate(results[:3], 1):
            logger.info(f"     [{j}] {r.get('title', 'N/A')[:60]}... (cred: {r.get('credibility', 0):.2f})")
    
    print(f"\n[Experiment 1] Total external results collected: "
          f"{sum(len(v) for v in all_search_results.values())}")
    
    # =========================================================================
    # 实验2: 知识融合
    # =========================================================================
    logger.info("\n" + "-" * 80)
    logger.info("EXPERIMENT 2: Knowledge Fusion")
    logger.info("-" * 80)
    
    # 为每个内部节点选择相关的外部知识进行融合
    fusion_targets = [
        ('ai_ethics', topics[0]),
        ('knowledge_fusion', topics[1]),
        ('hebbian_learning', topics[2])
    ]
    
    fusion_results = []
    
    for internal_id, topic in fusion_targets:
        logger.info(f"\n[Fusion] Internal: {internal_id} <-> External: '{topic}'")
        results = all_search_results.get(topic, [])
        if results:
            fusion_result = engine.fuse_knowledge(internal_id, results[:3])
            fusion_results.append(fusion_result)
            logger.info(f"  -> Success: {fusion_result['success']}")
            logger.info(f"  -> Fused: {fusion_result['fused_count']}/{fusion_result['total_external']}")
        else:
            logger.info(f"  -> No results to fuse")
    
    print(f"\n[Experiment 2] Total fusions completed: "
          f"{sum(r['fused_count'] for r in fusion_results if r.get('success'))}")
    
    # =========================================================================
    # 实验3: 交叉验证
    # =========================================================================
    logger.info("\n" + "-" * 80)
    logger.info("EXPERIMENT 3: Cross-Verification")
    logger.info("-" * 80)
    
    # 验证声明
    claims = [
        "AI ethics principles include fairness, transparency, and accountability",
        "Knowledge graphs use neural networks for representation learning",
        "Hebbian learning strengthens connections between co-activated neurons"
    ]
    
    verification_results = []
    
    for i, claim in enumerate(claims, 1):
        topic = topics[i-1]
        sources = all_search_results.get(topic, [])[:3]
        logger.info(f"\n[Verification {i}/3] Claim: '{claim[:60]}...'")
        result = engine.cross_verify(claim, sources)
        verification_results.append(result)
        logger.info(f"  -> Verified: {result['verified']}")
        logger.info(f"  -> Confidence: {result['confidence']:.3f}")
        logger.info(f"  -> Sources checked: {result['vote_count']}")
    
    avg_confidence = sum(r['confidence'] for r in verification_results) / len(verification_results) if verification_results else 0
    logger.info(f"\n[Experiment 3] Average verification confidence: {avg_confidence:.3f}")
    
    # =========================================================================
    # 实验4: Hebbian学习
    # =========================================================================
    logger.info("\n" + "-" * 80)
    logger.info("EXPERIMENT 4: Hebbian Learning")
    logger.info("-" * 80)
    
    # 激活内部节点多次，观察权重变化
    target_node = 'omni_hub_architecture'
    logger.info(f"\n[Hebbian] Target node: {target_node}")
    
    for i in range(5):
        result = engine.hebbian_update(target_node, activation=0.5 + i * 0.1)
        if result['updated_nodes']:
            node_info = result['updated_nodes'][0]
            logger.info(f"  Activation {i+1}: weight {node_info['old_weight']:.3f} -> {node_info['new_weight']:.3f}")
    
    # 验证协同激活效应
    logger.info(f"\n[Hebbian] Checking associated nodes activation...")
    associated_updates = engine.hebbian_update(target_node, activation=1.0)
    for update in associated_updates['updated_nodes']:
        if update['type'] == 'internal_associated':
            logger.info(f"  Associated node '{update['id']}': weight {update['old_weight']:.3f} -> {update['new_weight']:.3f}")
    
    logger.info(f"\n[Experiment 4] Total Hebbian updates: {engine.stats['hebbian_updates']}")
    
    # =========================================================================
    # 实验5: 自适应遗忘
    # =========================================================================
    logger.info("\n" + "-" * 80)
    logger.info("EXPERIMENT 5: Adaptive Forgetting")
    logger.info("-" * 80)
    
    # 先添加一些低权重节点
    logger.info("\n[Forgetting] Adding test nodes with low activation...")
    for i in range(5):
        test_node = ExternalKnowledgeNode(
            node_id=f"test_low_{i}",
            source='web',
            url=f"https://test.example.com/{i}",
            content=f"Low activation test content {i}",
            title=f"Test {i}",
            credibility=0.3,
            weight=0.1,
            activation_count=0
        )
        # 模拟旧时间戳
        test_node.timestamp = (datetime.now() - timedelta(days=30)).isoformat()
        test_node.last_accessed = (datetime.now() - timedelta(days=30)).isoformat()
        engine.external_nodes[test_node.node_id] = test_node
    
    logger.info(f"  -> Added 5 low-activation test nodes")
    logger.info(f"  -> External nodes before forget: {len(engine.external_nodes)}")
    
    # 执行遗忘
    forget_result = engine.adaptive_forget(threshold=0.05)
    logger.info(f"\n[Forgetting] Results:")
    logger.info(f"  -> Nodes forgotten: {forget_result['forgotten_count']}")
    logger.info(f"  -> Remaining nodes: {forget_result['remaining_nodes']}")
    
    for node in forget_result['forgotten_nodes']:
        logger.info(f"     - {node['id']}: score={node['forget_score']:.4f}, weight={node['weight']:.2f}")
    
    # =========================================================================
    # 实验6: 安全过滤
    # =========================================================================
    logger.info("\n" + "-" * 80)
    logger.info("EXPERIMENT 6: Security Filtering")
    logger.info("-" * 80)
    
    # 测试敏感内容过滤
    test_contents = [
        "Contact us at admin@example.com or call 555-123-4567 for API key: sk-abc123def456",
        "Dr. Smith from ACME Corp reported classified information about the project",
        "Normal research content about neural networks and deep learning"
    ]
    
    for i, content in enumerate(test_contents, 1):
        logger.info(f"\n[Security {i}/3] Testing content filtering...")
        filtered, report = engine.security_filter.apply_all_filters(content)
        logger.info(f"  -> Original length: {report['original_length']}")
        logger.info(f"  -> Filtered length: {report['final_length']}")
        logger.info(f"  -> Filters applied: {report['filters_applied']}")
        logger.info(f"  -> Safe: {report['safe']}")
        if report.get('blocked'):
            logger.info(f"  -> BLOCKED: {report['block_reason']}")
    
    # =========================================================================
    # 实验7: 融合知识图谱
    # =========================================================================
    logger.info("\n" + "-" * 80)
    logger.info("EXPERIMENT 7: Fused Knowledge Graph")
    logger.info("-" * 80)
    
    kg = engine.get_fused_knowledge_graph()
    logger.info(f"\n[KnowledgeGraph] Statistics:")
    logger.info(f"  -> Total nodes: {kg['metadata']['total_nodes']}")
    logger.info(f"  -> Internal nodes: {kg['metadata']['internal_nodes']}")
    logger.info(f"  -> External nodes: {kg['metadata']['external_nodes']}")
    logger.info(f"  -> Total edges: {kg['metadata']['total_edges']}")
    logger.info(f"  -> Fusion edges: {kg['metadata']['fusion_edges']}")
    
    logger.info(f"\n[KnowledgeGraph] Node types:")
    type_counts = {}
    for node in kg['nodes']:
        t = node['type']
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, count in type_counts.items():
        logger.info(f"  -> {t}: {count}")
    
    # =========================================================================
    # 最终统计
    # =========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("FINAL STATISTICS")
    logger.info("=" * 80)
    
    final_stats = engine.get_stats()
    logger.info(str(json.dumps(final_stats, indent=2, default=str)))
    
    # =========================================================================
    # 保存结果
    # =========================================================================
    output = {
        'experiments': {
            'search': {
                'topics': topics,
                'total_results': sum(len(v) for v in all_search_results.values()),
                'results_by_topic': {k: len(v) for k, v in all_search_results.items()}
            },
            'fusion': {
                'targets': [r for r in fusion_results if r.get('success')],
                'total_fused': sum(r['fused_count'] for r in fusion_results if r.get('success'))
            },
            'verification': {
                'results': verification_results,
                'avg_confidence': avg_confidence
            },
            'hebbian': {
                'updates': engine.stats['hebbian_updates'],
                'target_node': 'omni_hub_architecture'
            },
            'forgetting': {
                'forgotten': forget_result['forgotten_count'],
                'remaining': forget_result['remaining_nodes']
            }
        },
        'knowledge_graph': kg,
        'stats': final_stats
    }
    
    return output


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    results = run_experiments()
    print("\n[Done] Experiment validation completed successfully!")
