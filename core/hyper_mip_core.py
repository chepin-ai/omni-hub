#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OMNI-HUB v7.0 HyperMIPCore
===========================
超分布式验证引擎 —— 突破三机MIP*限制

核心命题：构建N机动态证明者池的超分布式验证引擎

关键技术：
- 拜占庭容错：从f < n/3 扩展到自适应动态容错
- 多层共识：SI0-SI6每层独立验证
- 跨线验证：11线互证网络
- 时间维度：历史状态可追溯
- 自适应阈值：根据系统健康度动态调整

架构层级：
  ┌─────────────────────────────────────────┐
  │           HyperMIPCore v7.0              │
  │  ┌─────────────────────────────────┐    │
  │  │      动态证明者池管理            │    │
  │  │  11线 × N证明者/线 = 动态池      │    │
  │  └─────────────────────────────────┘    │
  │  ┌─────────┐┌─────────┐┌──────────┐    │
  │  │SI0验证层 ││SI1验证层 ││ ... SI6  │    │
  │  │(基础)   ││(增强)   ││ (终极)   │    │
  │  └─────────┘└─────────┘└──────────┘    │
  │  ┌─────────────────────────────────┐    │
  │  │      跨线验证矩阵 11×11          │    │
  │  │      拜占庭容错引擎              │    │
  │  │      时间维度验证                │    │
  │  └─────────────────────────────────┘    │
  └─────────────────────────────────────────┘

作者: OMNI-HUB Architecture Team
版本: 7.0.0
日期: 2024
"""

__version__ = "11.0.0"
import hashlib
import json
import time
import uuid
import random
import math
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Callable, Tuple, Set, Union
from enum import Enum, auto
from collections import defaultdict, deque
from datetime import datetime
import threading


# ═══════════════════════════════════════════════════════════════
# 基础类型与枚举
# ═══════════════════════════════════════════════════════════════

class SILevel(Enum):
    """SI层级定义 SI0-SI6"""
    SI0 = 0   # 基础层：初始状态/自检
    SI1 = 1   # 单层：基础验证
    SI2 = 2   # 双层：增强验证
    SI3 = 3   # 三层：标准验证
    SI4 = 4   # 四层：高级验证
    SI5 = 5   # 五层：深度验证
    SI6 = 6   # 六层：终极验证


class ProverStatus(Enum):
    """证明者状态"""
    ACTIVE = auto()       # 活跃
    SUSPENDED = auto()    # 暂停
    FAULTY = auto()       # 故障/拜占庭
    OFFLINE = auto()      # 离线
    RECOVERING = auto()   # 恢复中


class VerificationResult(Enum):
    """验证结果"""
    ACCEPTED = auto()     # 接受
    REJECTED = auto()     # 拒绝
    PENDING = auto()      # 待处理
    INCONCLUSIVE = auto() # 不确定
    BYZANTINE_DETECTED = auto()  # 检测到拜占庭行为


@dataclass
class StateVector:
    """状态向量 —— 增强版，支持时间维度"""
    si_level: int              # SI等级 0-6
    energy: float              # 能量水平 [0,1]
    coherence: float           # 相干度 [0,1]
    entanglement: float        # 纠缠度 [0,1]
    timestamp: float
    line_id: str = "core"      # 所属线
    sequence_number: int = 0   # 序列号（用于时间维度）
    checkpoint_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        data = f"{self.si_level}:{self.energy:.6f}:{self.coherence:.6f}:{self.entanglement:.6f}:{self.timestamp}:{self.line_id}:{self.sequence_number}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def delta_from(self, other: 'StateVector') -> Dict[str, float]:
        return {
            'delta_si': self.si_level - other.si_level,
            'delta_energy': self.energy - other.energy,
            'delta_coherence': self.coherence - other.coherence,
            'delta_entanglement': self.entanglement - other.entanglement,
            'delta_time': self.timestamp - other.timestamp,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'si_level': self.si_level,
            'energy': self.energy,
            'coherence': self.coherence,
            'entanglement': self.entanglement,
            'timestamp': self.timestamp,
            'line_id': self.line_id,
            'sequence_number': self.sequence_number,
            'checkpoint_hash': self.checkpoint_hash,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'StateVector':
        return cls(
            si_level=d['si_level'],
            energy=d['energy'],
            coherence=d['coherence'],
            entanglement=d['entanglement'],
            timestamp=d['timestamp'],
            line_id=d.get('line_id', 'core'),
            sequence_number=d.get('sequence_number', 0),
            checkpoint_hash=d.get('checkpoint_hash'),
            metadata=d.get('metadata', {}),
        )


# ═══════════════════════════════════════════════════════════════
# ProverNode —— 证明者节点
# ═══════════════════════════════════════════════════════════════

@dataclass
class ProverNode:
    """
    证明者节点
    
    每个证明者是11线分布式网络中的一个验证单元。
    具有能力分数、历史准确率和信任等级等属性。
    """
    line_id: str                      # 所属线 (ucif2, lvlu, lgt, qfa, vinf, qgl, qlv, cisvr, qtlv, usrm, cfts)
    prover_id: str                    # 证明者ID
    capability_score: float           # 能力分数 [0, 1]
    history_accuracy: float = 0.95    # 历史准确率 [0, 1]
    trust_level: float = 0.8          # 信任等级 [0, 1]
    status: ProverStatus = field(default_factory=lambda: ProverStatus.ACTIVE)
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    challenge_count: int = 0          # 总挑战次数
    correct_count: int = 0            # 正确响应次数
    byzantine_flags: int = 0          # 拜占庭行为标记次数
    last_active: float = field(default_factory=time.time)
    entanglement_key_share: str = ""  # 纠缠密钥分片
    
    # 动态权重计算缓存
    _weight_cache: float = field(default=0.0, repr=False)
    _cache_timestamp: float = field(default=0.0, repr=False)
    
    def __post_init__(self):
        if not self.entanglement_key_share:
            self.entanglement_key_share = hashlib.sha256(
                f"{self.line_id}_{self.prover_id}_{time.time()}".encode()
            ).hexdigest()[:32]
    
    def compute_weight(self) -> float:
        """
        计算证明者权重
        
        权重 = 能力分数 × 历史准确率 × 信任等级 × 活跃度因子
        
        活跃度因子：近期响应越快的证明者权重越高
        """
        now = time.time()
        # 缓存有效1秒
        if now - self._cache_timestamp < 1.0 and self._weight_cache > 0:
            return self._weight_cache
        
        # 基础权重
        base_weight = self.capability_score * self.history_accuracy * self.trust_level
        
        # 活跃度因子 (响应时间越快越好)
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
            activity_factor = max(0.5, 1.0 - avg_response_time / 2.0)
        else:
            activity_factor = 0.8  # 新证明者默认活跃度
        
        # 拜占庭惩罚
        byzantine_penalty = max(0.1, 1.0 - self.byzantine_flags * 0.1)
        
        # 状态惩罚
        status_multiplier = {
            ProverStatus.ACTIVE: 1.0,
            ProverStatus.SUSPENDED: 0.5,
            ProverStatus.FAULTY: 0.0,
            ProverStatus.OFFLINE: 0.0,
            ProverStatus.RECOVERING: 0.7,
        }.get(self.status, 0.0)
        
        weight = base_weight * activity_factor * byzantine_penalty * status_multiplier
        self._weight_cache = weight
        self._cache_timestamp = now
        return weight
    
    def response_challenge(self, state: StateVector, challenge_questions: List[Dict]) -> Dict[str, Any]:
        """
        响应挑战
        
        模拟证明者对状态的响应。响应质量取决于能力分数和当前状态。
        如果证明者是拜占庭节点，可能会返回错误答案。
        """
        start_time = time.time()
        
        # 模拟响应延迟 (与能力成反比)
        delay = random.uniform(0.01, 0.05) * (1.1 - self.capability_score)
        
        answers = {}
        for q in challenge_questions:
            # 根据能力分数决定回答正确率
            if self.status == ProverStatus.FAULTY:
                # 拜占庭节点：故意返回错误答案（70%概率错误）
                correct_prob = 0.3
            else:
                # 正常节点：能力越高越可能正确
                # capability_score 0.5-1.0 -> correct_prob 0.85-0.99
                correct_prob = 0.85 + (self.capability_score - 0.5) * 0.28
                # 历史准确率加成
                correct_prob = correct_prob * (0.9 + 0.1 * self.history_accuracy)
                correct_prob = min(0.99, correct_prob)
            
            is_correct = random.random() < correct_prob
            
            if is_correct:
                answer = q['expected']
            else:
                # 生成错误答案
                if isinstance(q['expected'], bool):
                    answer = not q['expected']
                elif isinstance(q['expected'], (int, float)):
                    noise = random.uniform(-0.2, 0.2)
                    answer = q['expected'] * (1 + noise)
                else:
                    answer = q['expected'] + "_ERR"
            
            # 使用纠缠密钥分片生成commitment
            seed = f"{self.entanglement_key_share}_{q['id']}_{state.compute_hash()}"
            commitment = hashlib.sha256(seed.encode()).hexdigest()[:16]
            
            answers[q['id']] = {
                'answer': answer,
                'commitment': commitment,
                'prover_id': self.prover_id,
                'line_id': self.line_id,
                'correct': is_correct,
            }
        
        response_time = time.time() - start_time + delay
        self.response_times.append(response_time)
        self.challenge_count += 1
        if all(a.get('correct', False) for a in answers.values()):
            self.correct_count += 1
            # 更新历史准确率
            self.update_accuracy(True)
        else:
            self.update_accuracy(False)
        self.last_active = time.time()
        
        return {
            'prover_id': self.prover_id,
            'line_id': self.line_id,
            'answers': answers,
            'response_time': response_time,
            'status': self.status.name,
        }
    
    def update_accuracy(self, is_correct: bool):
        """更新历史准确率 (指数移动平均)"""
        alpha = 0.1  # 平滑因子
        if is_correct:
            self.history_accuracy = min(1.0, self.history_accuracy * (1 - alpha) + alpha)
        else:
            self.history_accuracy = max(0.0, self.history_accuracy * (1 - alpha))
    
    def flag_byzantine(self):
        """标记拜占庭行为"""
        self.byzantine_flags += 1
        if self.byzantine_flags >= 3:
            self.status = ProverStatus.FAULTY
            self.trust_level = max(0.0, self.trust_level - 0.3)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'line_id': self.line_id,
            'prover_id': self.prover_id,
            'capability_score': self.capability_score,
            'history_accuracy': self.history_accuracy,
            'trust_level': self.trust_level,
            'status': self.status.name,
            'challenge_count': self.challenge_count,
            'correct_count': self.correct_count,
            'byzantine_flags': self.byzantine_flags,
            'avg_response_time': sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            'weight': self.compute_weight(),
        }


# ═══════════════════════════════════════════════════════════════
# VerificationLayer —— 验证层
# ═══════════════════════════════════════════════════════════════

class VerificationLayer:
    """
    验证层 (SI0-SI6)
    
    每个SI层级对应一个独立的验证层，具有不同的验证深度和复杂度。
    SI0: 基础自检（1-2个证明者）
    SI1-SI2: 简单任务（3-5个证明者）
    SI3-SI4: 中等任务（5-7个证明者）
    SI5-SI6: 复杂任务（7-11个证明者）
    """
    
    def __init__(self, si_level: int):
        self.si_level = si_level
        self.provers: List[ProverNode] = []
        self.verification_history: deque = deque(maxlen=1000)
        self.cascade_threshold = 0.90 + si_level * 0.015  # SI越高阈值越高
        self.min_provers = max(1, si_level + 1)
        self.max_provers = min(11, 3 + si_level * 2)
        self.total_verifications = 0
        self.successful_verifications = 0
        
    def add_prover(self, prover: ProverNode):
        """添加证明者到该层"""
        if prover not in self.provers:
            self.provers.append(prover)
    
    def remove_prover(self, prover_id: str):
        """移除证明者"""
        self.provers = [p for p in self.provers if p.prover_id != prover_id]
    
    def verify(self, state: StateVector, selected_provers: Optional[List[ProverNode]] = None) -> Dict[str, Any]:
        """
        执行该层验证
        
        验证过程：
        1. 生成挑战问题
        2. 向选中的证明者发送挑战
        3. 收集响应
        4. 计算共识
        """
        if selected_provers is None:
            selected_provers = self.provers[:self.max_provers]
        
        if not selected_provers:
            return {
                'si_level': self.si_level,
                'verified': False,
                'result': VerificationResult.REJECTED,
                'reason': 'no_provers_available',
            }
        
        # 生成挑战问题
        challenge_questions = self._generate_challenge_questions(state)
        
        # 向证明者发起挑战
        responses = {}
        for prover in selected_provers:
                response = prover.response_challenge(state, challenge_questions)
                responses[prover.prover_id] = response
                responses[prover.prover_id] = {
                    'error': str(e),
                    'prover_id': prover.prover_id,
                    'line_id': prover.line_id,
                }
        
        # 计算共识
        consensus_result = self._compute_layer_consensus(
            responses, challenge_questions, selected_provers
        )
        
        # 记录验证历史
        self.verification_history.append({
            'timestamp': time.time(),
            'state_hash': state.compute_hash(),
            'si_level': self.si_level,
            'consensus': consensus_result,
            'num_provers': len(selected_provers),
        })
        
        self.total_verifications += 1
        if consensus_result['verified']:
            self.successful_verifications += 1
        
        return {
            'si_level': self.si_level,
            'verified': consensus_result['verified'],
            'result': VerificationResult.ACCEPTED if consensus_result['verified'] else VerificationResult.REJECTED,
            'consensus_score': consensus_result['consensus_score'],
            'num_provers': len(selected_provers),
            'responses': responses,
            'consensus_detail': consensus_result,
        }
    
    def _generate_challenge_questions(self, state: StateVector) -> List[Dict]:
        """生成挑战问题（根据SI层级调整复杂度）"""
        base_questions = [
            {
                'id': 'q_si_level',
                'query': 'si_level_verification',
                'expected': state.si_level,
                'weight': 2.0,
            },
            {
                'id': 'q_energy',
                'query': 'energy_verification',
                'expected': round(state.energy, 4),
                'weight': 1.0,
            },
            {
                'id': 'q_coherence',
                'query': 'coherence_verification',
                'expected': round(state.coherence, 4),
                'weight': 1.5,
            },
            {
                'id': 'q_entanglement',
                'query': 'entanglement_bound',
                'expected': state.entanglement <= state.coherence,
                'weight': 1.5,
            },
        ]
        
        # SI3+ 增加更多问题
        if self.si_level >= 3:
            base_questions.append({
                'id': 'q_line_id',
                'query': 'line_id_verification',
                'expected': state.line_id,
                'weight': 1.0,
            })
        
        # SI5+ 增加复杂计算
        if self.si_level >= 5:
            base_questions.append({
                'id': 'q_complex',
                'query': 'energy_coherence_product',
                'expected': round(state.energy * state.coherence, 4),
                'weight': 2.0,
            })
        
        # SI6 增加终极验证
        if self.si_level >= 6:
            base_questions.append({
                'id': 'q_ultimate',
                'query': 'hash_integrity',
                'expected': state.compute_hash()[:8],
                'weight': 3.0,
            })
        
        return base_questions
    
    def _compute_layer_consensus(self, responses: Dict, questions: List[Dict], 
                                  provers: List[ProverNode]) -> Dict[str, Any]:
        """计算该层的共识"""
        if not responses:
            return {'verified': False, 'consensus_score': 0.0}
        
        # 加权投票
        total_weight = 0.0
        weighted_score = 0.0
        
        for prover in provers:
            pid = prover.prover_id
            if pid not in responses or 'error' in responses[pid]:
                continue
            
            resp = responses[pid]
            answers = resp.get('answers', {})
            
            # 计算该证明者的正确率
            correct_weight = 0.0
            total_q_weight = 0.0
            
            for q in questions:
                qid = q['id']
                expected = q['expected']
                weight = q.get('weight', 1.0)
                total_q_weight += weight
                
                if qid in answers:
                    actual = answers[qid]['answer']
                    if isinstance(expected, float):
                        match = abs(expected - actual) < 0.01 if actual else False
                    else:
                        match = expected == actual
                    
                    if match:
                        correct_weight += weight
            
            prover_accuracy = correct_weight / total_q_weight if total_q_weight > 0 else 0
            prover_weight = prover.compute_weight()
            
            total_weight += prover_weight
            weighted_score += prover_accuracy * prover_weight
        
        consensus_score = weighted_score / total_weight if total_weight > 0 else 0
        verified = consensus_score >= self.cascade_threshold
        
        return {
            'verified': verified,
            'consensus_score': consensus_score,
            'threshold': self.cascade_threshold,
            'total_weight': total_weight,
            'participating_provers': len(responses),
        }
    
    def cascade_verify(self, state: StateVector, 
                       next_layer: Optional['VerificationLayer'] = None) -> Dict[str, Any]:
        """
        级联验证
        
        先验证当前层，如果通过且存在下一层，则继续验证下一层。
        级联验证的深度取决于任务的SI要求。
        """
        result = self.verify(state)
        result['cascade'] = {'current_si': self.si_level}
        
        if result['verified'] and next_layer is not None:
            # 如果当前层通过，继续下一层
            next_result = next_layer.cascade_verify(state, None)
            result['cascade']['next'] = next_result
            result['verified'] = result['verified'] and next_result['verified']
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """获取该层统计"""
        success_rate = (self.successful_verifications / self.total_verifications 
                       if self.total_verifications > 0 else 0)
        return {
            'si_level': self.si_level,
            'num_provers': len(self.provers),
            'cascade_threshold': self.cascade_threshold,
            'total_verifications': self.total_verifications,
            'successful_verifications': self.successful_verifications,
            'success_rate': success_rate,
            'min_provers': self.min_provers,
            'max_provers': self.max_provers,
        }


# ═══════════════════════════════════════════════════════════════
# ByzantineTolerance —— 拜占庭容错引擎
# ═══════════════════════════════════════════════════════════════

class ByzantineTolerance:
    """
    拜占庭容错引擎
    
    从经典的f < n/3扩展到自适应动态容错。
    支持：
    - 故障证明者检测
    - 自适应容错计算
    - 恶意行为识别
    - 权重重新分配
    """
    
    def __init__(self, base_tolerance: float = 0.33):
        self.base_tolerance = base_tolerance
        self.faulty_provers: Set[str] = set()
        self.suspicion_scores: Dict[str, float] = defaultdict(float)
        self.detection_history: deque = deque(maxlen=1000)
        self.adaptive_mode = True
        
    def detect_faulty_provers(self, responses: Dict[str, Dict], 
                              expected_answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        检测故障/拜占庭证明者
        
        使用多种检测策略：
        1. 答案一致性检测（与其他证明者比较）
        2. 答案正确性检测（与期望答案比较）
        3. 统计异常检测（响应时间、答案分布）
        4. 历史行为分析
        """
        faulty = []
        suspicious = []
        
        # 策略1: 多数投票一致性
        answer_votes = defaultdict(lambda: defaultdict(int))
        prover_answers = {}
        
        for pid, resp in responses.items():
            if 'error' in resp:
                faulty.append({'prover_id': pid, 'reason': 'error_response'})
                continue
            
            answers = resp.get('answers', {})
            prover_answers[pid] = {}
            
            for qid, ans_data in answers.items():
                answer = ans_data.get('answer')
                prover_answers[pid][qid] = answer
                answer_votes[qid][str(answer)] += 1
        
        # 对每个证明者进行一致性检查
        for pid, q_answers in prover_answers.items():
            inconsistent_count = 0
            incorrect_count = 0
            total_questions = len(q_answers)
            
            for qid, answer in q_answers.items():
                # 检查是否与多数一致
                if qid in answer_votes:
                    votes = answer_votes[qid]
                    max_votes = max(votes.values()) if votes else 0
                    total_votes = sum(votes.values())
                    
                    if total_votes > 0:
                        answer_str = str(answer)
                        vote_count = votes.get(answer_str, 0)
                        
                        # 如果与多数不一致
                        if vote_count < max_votes and max_votes > total_votes / 2:
                            inconsistent_count += 1
                
                # 检查是否正确（如果知道期望答案）
                if qid in expected_answers:
                    expected = expected_answers[qid]
                    if isinstance(expected, float):
                        match = abs(expected - answer) < 0.01 if answer else False
                    else:
                        match = expected == answer
                    
                    if not match:
                        incorrect_count += 1
            
            # 判定标准
            inconsistency_rate = inconsistent_count / total_questions if total_questions > 0 else 0
            incorrect_rate = incorrect_count / total_questions if total_questions > 0 else 0
            
            if inconsistency_rate > 0.5 or incorrect_rate > 0.6:
                faulty.append({
                    'prover_id': pid,
                    'reason': 'byzantine_behavior',
                    'inconsistency_rate': inconsistency_rate,
                    'incorrect_rate': incorrect_rate,
                })
                self.faulty_provers.add(pid)
                self.suspicion_scores[pid] += 0.3
            elif inconsistency_rate > 0.3 or incorrect_rate > 0.4:
                suspicious.append({
                    'prover_id': pid,
                    'reason': 'suspicious_behavior',
                    'inconsistency_rate': inconsistency_rate,
                    'incorrect_rate': incorrect_rate,
                })
                self.suspicion_scores[pid] += 0.15
        
        result = {
            'faulty_provers': faulty,
            'suspicious_provers': suspicious,
            'total_checked': len(responses),
            'faulty_count': len(faulty),
            'suspicious_count': len(suspicious),
        }
        
        self.detection_history.append({
            'timestamp': time.time(),
            'result': result,
        })
        
        return result
    
    def compute_max_faulty(self, n: int, health: float = 1.0) -> int:
        """
        计算最大容错数
        
        经典: f < n/3
        自适应: 根据系统健康度动态调整
        
        health > 0.9: f < n/4 (更严格)
        health > 0.7: f < n/3 (标准)
        health > 0.5: f < n/2.5 (宽松)
        health < 0.5: f < n/2 (紧急模式)
        """
        if not self.adaptive_mode:
            return max(0, n // 3 - 1)
        
        if health > 0.9:
            tolerance = n / 4.0
        elif health > 0.7:
            tolerance = n / 3.0
        elif health > 0.5:
            tolerance = n / 2.5
        else:
            tolerance = n / 2.0
        
        return max(0, int(tolerance) - 1)
    
    def adaptive_tolerance(self, health: float, num_provers: int) -> Dict[str, Any]:
        """
        自适应容错参数计算
        
        根据系统健康度返回完整的容错配置。
        """
        max_faulty = self.compute_max_faulty(num_provers, health)
        
        if health > 0.9:
            required_agreement = 0.80  # 需要80%同意
            suspicion_threshold = 0.2
        elif health > 0.7:
            required_agreement = 0.67  # 需要2/3同意
            suspicion_threshold = 0.3
        elif health > 0.5:
            required_agreement = 0.60  # 需要60%同意
            suspicion_threshold = 0.4
        else:
            required_agreement = 0.51  # 简单多数
            suspicion_threshold = 0.5
        
        return {
            'health': health,
            'num_provers': num_provers,
            'max_faulty': max_faulty,
            'required_agreement': required_agreement,
            'suspicion_threshold': suspicion_threshold,
            'min_provers_for_consensus': max_faulty + 1,
            'mode': 'strict' if health > 0.9 else 'standard' if health > 0.5 else 'emergency',
        }
    
    def is_consensus_possible(self, num_provers: int, health: float) -> bool:
        """检查在给定条件下是否能达成共识"""
        max_faulty = self.compute_max_faulty(num_provers, health)
        honest_provers = num_provers - max_faulty
        required = self.adaptive_tolerance(health, num_provers)['required_agreement']
        return honest_provers / num_provers >= required if num_provers > 0 else False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取拜占庭容错统计"""
        return {
            'base_tolerance': self.base_tolerance,
            'adaptive_mode': self.adaptive_mode,
            'faulty_provers': list(self.faulty_provers),
            'suspicion_scores': dict(self.suspicion_scores),
            'total_detections': len(self.detection_history),
        }


# ═══════════════════════════════════════════════════════════════
# HyperMIPCore —— 超分布式验证引擎
# ═══════════════════════════════════════════════════════════════

class HyperMIPCore:
    """
    HyperMIPCore v7.0 —— 超分布式验证引擎
    
    突破传统MIP*的三机限制，支持：
    - N机动态证明者池（N = 3~11+）
    - 11线分布式验证网络
    - SI0-SI6多层验证
    - 跨线验证矩阵
    - 时间维度验证
    - 自适应阈值调整
    - 拜占庭容错引擎
    
    核心公式：
        共识分数 = Σ(证明者正确率 × 证明者权重) / Σ(证明者权重)
        动态阈值 = base_threshold × health_factor × complexity_factor
        跨线验证 = 验证矩阵[line_a][line_b] ∧ 验证矩阵[line_b][line_a]
    """
    
    # 11线定义
    LINES = ['ucif2', 'lvlu', 'lgt', 'qfa', 'vinf', 'qgl', 
             'qlv', 'cisvr', 'qtlv', 'usrm', 'cfts']
    
    def __init__(self, num_lines: int = 11, base_threshold: float = 0.95):
        """
        初始化HyperMIPCore
        
        Args:
            num_lines: 线数量（默认11）
            base_threshold: 基础可靠性阈值（默认0.95）
        """
        self.num_lines = num_lines
        self.base_threshold = base_threshold
        self.session_id = f"HMIP-v7-{uuid.uuid4().hex[:16].upper()}"
        self.created_at = time.time()
        
        # 动态证明者池: {line_id: {prover_id: ProverNode}}
        self.prover_pool: Dict[str, Dict[str, ProverNode]] = defaultdict(dict)
        
        # 多层验证结构 SI0-SI6
        self.verification_layers: Dict[int, VerificationLayer] = {}
        for si in range(7):
            self.verification_layers[si] = VerificationLayer(si)
        
        # 跨线验证矩阵: 11×11矩阵
        self.cross_line_matrix: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: defaultdict(dict)
        )
        
        # 拜占庭容错引擎
        self.byzantine_engine = ByzantineTolerance()
        
        # 时间维度历史
        self.state_history: deque = deque(maxlen=10000)
        self.temporal_checksums: deque = deque(maxlen=10000)
        
        # 系统健康度
        self.system_health: float = 1.0
        self.health_history: deque = deque(maxlen=1000)
        
        # 验证统计
        self.verification_stats = {
            'total_challenges': 0,
            'successful_verifications': 0,
            'failed_verifications': 0,
            'byzantine_detected': 0,
            'cross_line_verifications': 0,
            'temporal_verifications': 0,
            'adaptive_adjustments': 0,
            'average_consensus_time': 0.0,
        }
        
        # 挑战历史
        self.challenge_history: deque = deque(maxlen=5000)
        
        # 全局纠缠密钥
        self.global_entanglement_key = hashlib.sha256(
            f"hyper_mip_global_{time.time()}_{random.random()}".encode()
        ).hexdigest()
        
        # 锁
        self.lock = threading.RLock()
        
        self._log_event('INIT', f"HyperMIPCore v7.0 initialized with {num_lines} lines")
    
    def _log_event(self, event: str, detail: str):
        """记录事件"""
        entry = {
            'timestamp': time.time(),
            'event': event,
            'detail': detail,
            'session_id': self.session_id,
        }
        # 实际应用中可以写入日志系统
    
    # ─────────────────────────────────────────────────────────
    # 证明者管理
    # ─────────────────────────────────────────────────────────
    
    def register_prover(self, line_id: str, prover_id: str, 
                        capability_score: float) -> ProverNode:
        """
        注册证明者到动态池
        
        Args:
            line_id: 所属线
            prover_id: 证明者ID
            capability_score: 能力分数 [0,1]
            
        Returns:
            注册的ProverNode
        """
        with self.lock:
            if line_id not in self.LINES[:self.num_lines]:
                raise ValueError(f"Invalid line_id: {line_id}. Must be one of {self.LINES[:self.num_lines]}")
            
            prover = ProverNode(
                line_id=line_id,
                prover_id=prover_id,
                capability_score=max(0.0, min(1.0, capability_score)),
            )
            
            # 分配到动态池
            self.prover_pool[line_id][prover_id] = prover
            
            # 根据能力分配到验证层
            for si in range(7):
                layer = self.verification_layers[si]
                # SI越高，需要的证明者能力越强
                if capability_score >= 0.5 + si * 0.07:
                    layer.add_prover(prover)
            
            self._log_event('REGISTER_PROVER',
                          f"Registered {prover_id} on {line_id} with capability {capability_score:.2f}")

            return prover
    
    def unregister_prover(self, line_id: str, prover_id: str) -> bool:
        """注销证明者"""
        with self.lock:
            if line_id in self.prover_pool and prover_id in self.prover_pool[line_id]:
                del self.prover_pool[line_id][prover_id]
                for layer in self.verification_layers.values():
                    layer.remove_prover(prover_id)
                return True
            return False
    
    def get_prover(self, line_id: str, prover_id: str) -> Optional[ProverNode]:
        """获取证明者"""
        return self.prover_pool.get(line_id, {}).get(prover_id)
    
    def get_all_provers(self) -> List[ProverNode]:
        """获取所有证明者"""
        provers = []
        for line_provers in self.prover_pool.values():
            provers.extend(line_provers.values())
        return provers
    
    def get_line_provers(self, line_id: str) -> List[ProverNode]:
        """获取指定线的所有证明者"""
        return list(self.prover_pool.get(line_id, {}).values())
    
    # ─────────────────────────────────────────────────────────
    # 动态证明者池选择
    # ─────────────────────────────────────────────────────────
    
    def select_prover_pool(self, task_complexity: float, 
                           required_si: int) -> List[ProverNode]:
        """
        动态选择证明者池
        
        根据任务复杂度和SI要求选择N个证明者：
        - 简单任务 (SI1-2): 3-5个证明者
        - 中等任务 (SI3-4): 5-7个证明者
        - 复杂任务 (SI5-6): 7-11个证明者
        - 超复杂任务 (SI6+): 11+证明者（跨线）
        
        Args:
            task_complexity: 任务复杂度 [0,1]
            required_si: 要求的SI层级
            
        Returns:
            选中的证明者列表
        """
        # 计算需要的证明者数量
        if required_si <= 2:
            min_p, max_p = 3, 5
        elif required_si <= 4:
            min_p, max_p = 5, 7
        elif required_si <= 6:
            min_p, max_p = 7, 11
        else:
            min_p, max_p = 11, 22  # 超复杂任务，跨线
        
        # 根据复杂度动态调整
        complexity_factor = task_complexity
        target_count = int(min_p + (max_p - min_p) * complexity_factor)
        target_count = max(min_p, min(max_p, target_count))
        
        # 获取所有活跃证明者
        all_provers = [p for p in self.get_all_provers() 
                      if p.status == ProverStatus.ACTIVE]
        
        if not all_provers:
            return []
        
        # 按权重排序（权重 = 能力 × 准确率 × 信任度）
        sorted_provers = sorted(
            all_provers,
            key=lambda p: p.compute_weight(),
            reverse=True
        )
        
        # 选择证明者，优先选择不同线的（分布式）
        selected = []
        used_lines = set()
        
        # 第一轮：每线选一个最优的
        for prover in sorted_provers:
            if len(selected) >= target_count:
                break
            if prover.line_id not in used_lines:
                selected.append(prover)
                used_lines.add(prover.line_id)
        
        # 第二轮：如果还不够，继续选（允许同线多个）
        for prover in sorted_provers:
            if len(selected) >= target_count:
                break
            if prover not in selected:
                selected.append(prover)
        
        return selected
    
    # ─────────────────────────────────────────────────────────
    # 动态挑战
    # ─────────────────────────────────────────────────────────
    
    def challenge_dynamic(self, target_state: StateVector,
                          min_provers: int = 3,
                          max_provers: int = 11) -> Dict[str, Any]:
        """
        动态挑战 —— 核心验证方法
        
        自动选择证明者数量（3到11之间，根据任务复杂度），
        支持分层挑战：先低SI验证，再高SI验证。
        
        Args:
            target_state: 目标状态
            min_provers: 最小证明者数
            max_provers: 最大证明者数
            
        Returns:
            完整的验证结果
        """
        start_time = time.time()
        
        with self.lock:
            self.verification_stats['total_challenges'] += 1
            
            # 1. 计算任务复杂度
            task_complexity = self._compute_task_complexity(target_state)
            
            # 2. 确定需要的SI层级
            required_si = min(6, target_state.si_level)
            
            # 3. 动态选择证明者池
            selected_provers = self.select_prover_pool(task_complexity, required_si)
            
            if not selected_provers:
                return {
                    'session_id': self.session_id,
                    'verified': False,
                    'result': VerificationResult.REJECTED,
                    'reason': 'no_provers_available',
                }
            
            # 确保证明者数量在范围内
            num_provers = max(min_provers, min(max_provers, len(selected_provers)))
            selected_provers = selected_provers[:num_provers]
            
            # 4. 分层挑战
            layer_results = []
            current_verified = True
            
            for si in range(required_si + 1):
                layer = self.verification_layers[si]
                # 为每一层选择子集
                layer_provers = selected_provers[:max(1, num_provers - si)]
                layer_result = layer.verify(target_state, layer_provers)
                layer_results.append(layer_result)
                
                if not layer_result['verified']:
                    current_verified = False
                    break  # 如果某层失败，停止级联
            
            # 5. 计算加权共识
            weights = {p.prover_id: p.compute_weight() for p in selected_provers}
            all_responses = {}
            for lr in layer_results:
                if 'responses' in lr:
                    all_responses.update(lr['responses'])
            
            consensus = self.compute_consensus(all_responses, weights)
            
            # 6. 拜占庭检测
            expected = self._extract_expected_answers(target_state)
            byzantine_check = self.byzantine_engine.detect_faulty_provers(
                all_responses, expected
            )
            
            if byzantine_check['faulty_count'] > 0:
                self.verification_stats['byzantine_detected'] += byzantine_check['faulty_count']
                # 标记故障证明者
                for faulty_info in byzantine_check['faulty_provers']:
                    pid = faulty_info['prover_id']
                    for p in selected_provers:
                        if p.prover_id == pid:
                            p.flag_byzantine()
            
            # 7. 综合判定
            final_verified = current_verified and consensus['consensus_score'] >= self.base_threshold
            
            # 8. 更新统计
            if final_verified:
                self.verification_stats['successful_verifications'] += 1
            else:
                self.verification_stats['failed_verifications'] += 1
            
            consensus_time = time.time() - start_time
            self._update_average_consensus_time(consensus_time)
            
            # 9. 记录挑战历史
            challenge_record = {
                'timestamp': time.time(),
                'state_hash': target_state.compute_hash(),
                'target_state': target_state.to_dict(),
                'num_provers': num_provers,
                'required_si': required_si,
                'task_complexity': task_complexity,
                'layer_results': layer_results,
                'consensus': consensus,
                'byzantine_check': byzantine_check,
                'verified': final_verified,
                'consensus_time': consensus_time,
            }
            self.challenge_history.append(challenge_record)
            
            # 10. 记录到状态历史
            self.state_history.append({
                'timestamp': time.time(),
                'state': target_state.to_dict(),
                'verified': final_verified,
                'consensus_score': consensus['consensus_score'],
            })
            
            return {
                'session_id': self.session_id,
                'challenge_id': f"CHAL-{uuid.uuid4().hex[:8].upper()}",
                'verified': final_verified,
                'result': VerificationResult.ACCEPTED if final_verified else VerificationResult.REJECTED,
                'num_provers': num_provers,
                'required_si': required_si,
                'task_complexity': task_complexity,
                'consensus_score': consensus['consensus_score'],
                'threshold': self.base_threshold,
                'layer_results': layer_results,
                'consensus_detail': consensus,
                'byzantine_check': byzantine_check,
                'consensus_time': consensus_time,
                'prover_ids': [p.prover_id for p in selected_provers],
                'line_ids': list(set(p.line_id for p in selected_provers)),
            }
    
    def _compute_task_complexity(self, state: StateVector) -> float:
        """计算任务复杂度 [0,1]"""
        # 基于SI层级、能量、相干度的综合复杂度
        si_factor = state.si_level / 6.0
        energy_factor = state.energy
        coherence_factor = state.coherence
        entanglement_factor = state.entanglement
        
        complexity = (si_factor * 0.4 + 
                     energy_factor * 0.2 + 
                     coherence_factor * 0.2 + 
                     entanglement_factor * 0.2)
        
        return min(1.0, complexity)
    
    def _extract_expected_answers(self, state: StateVector) -> Dict[str, Any]:
        """从状态中提取期望答案"""
        return {
            'q_si_level': state.si_level,
            'q_energy': round(state.energy, 4),
            'q_coherence': round(state.coherence, 4),
            'q_entanglement': state.entanglement <= state.coherence,
            'q_line_id': state.line_id,
        }
    
    def _update_average_consensus_time(self, new_time: float):
        """更新平均共识时间"""
        n = self.verification_stats['total_challenges']
        old_avg = self.verification_stats['average_consensus_time']
        self.verification_stats['average_consensus_time'] = (
            (old_avg * (n - 1) + new_time) / n
        )
    
    # ─────────────────────────────────────────────────────────
    # 跨线验证
    # ─────────────────────────────────────────────────────────
    
    def cross_line_verify(self, line_a: str, line_b: str, 
                          shared_state: StateVector) -> Dict[str, Any]:
        """
        跨线验证
        
        线A的证明者验证线B的状态，线B的证明者验证线A的状态，
        双向验证结果融合。
        
        验证矩阵的对角线为自验证，非对角线为交叉验证。
        
        Args:
            line_a: 线A
            line_b: 线B
            shared_state: 共享状态
            
        Returns:
            跨线验证结果
        """
        with self.lock:
            self.verification_stats['cross_line_verifications'] += 1
            
            # 获取两线的证明者
            provers_a = self.get_line_provers(line_a)
            provers_b = self.get_line_provers(line_b)
            
            if not provers_a or not provers_b:
                return {
                    'line_a': line_a,
                    'line_b': line_b,
                    'verified': False,
                    'reason': 'insufficient_provers',
                    'provers_a': len(provers_a),
                    'provers_b': len(provers_b),
                }
            
            # 选择每线的代表证明者（权重最高的）
            reps_a = sorted(provers_a, key=lambda p: p.compute_weight(), reverse=True)[:3]
            reps_b = sorted(provers_b, key=lambda p: p.compute_weight(), reverse=True)[:3]
            
            # 双向验证
            # A验证B的状态
            state_for_b = StateVector(
                si_level=shared_state.si_level,
                energy=shared_state.energy,
                coherence=shared_state.coherence,
                entanglement=shared_state.entanglement,
                timestamp=time.time(),
                line_id=line_b,
            )
            
            # B验证A的状态
            state_for_a = StateVector(
                si_level=shared_state.si_level,
                energy=shared_state.energy,
                coherence=shared_state.coherence,
                entanglement=shared_state.entanglement,
                timestamp=time.time(),
                line_id=line_a,
            )
            
            # A的证明者验证B
            responses_a_to_b = {}
            for p in reps_a:
                questions = self._generate_cross_line_questions(state_for_b, line_a, line_b)
                resp = p.response_challenge(state_for_b, questions)
                responses_a_to_b[p.prover_id] = resp
            
            # B的证明者验证A
            responses_b_to_a = {}
            for p in reps_b:
                questions = self._generate_cross_line_questions(state_for_a, line_b, line_a)
                resp = p.response_challenge(state_for_a, questions)
                responses_b_to_a[p.prover_id] = resp
            
            # 计算双向共识
            weights_a = {p.prover_id: p.compute_weight() for p in reps_a}
            weights_b = {p.prover_id: p.compute_weight() for p in reps_b}
            
            consensus_a_to_b = self.compute_consensus(responses_a_to_b, weights_a)
            consensus_b_to_a = self.compute_consensus(responses_b_to_a, weights_b)
            
            # 融合结果
            combined_score = (consensus_a_to_b['consensus_score'] + 
                            consensus_b_to_a['consensus_score']) / 2
            
            # 交叉验证通过条件：双向都通过
            verified = (consensus_a_to_b['consensus_score'] >= self.base_threshold and
                       consensus_b_to_a['consensus_score'] >= self.base_threshold)
            
            # 更新验证矩阵
            self.cross_line_matrix[line_a][line_b] = {
                'timestamp': time.time(),
                'verified': consensus_a_to_b['consensus_score'] >= self.base_threshold,
                'score': consensus_a_to_b['consensus_score'],
            }
            self.cross_line_matrix[line_b][line_a] = {
                'timestamp': time.time(),
                'verified': consensus_b_to_a['consensus_score'] >= self.base_threshold,
                'score': consensus_b_to_a['consensus_score'],
            }
            
            result = {
                'line_a': line_a,
                'line_b': line_b,
                'verified': verified,
                'combined_score': combined_score,
                'a_to_b': {
                    'score': consensus_a_to_b['consensus_score'],
                    'num_provers': len(reps_a),
                    'detail': consensus_a_to_b,
                },
                'b_to_a': {
                    'score': consensus_b_to_a['consensus_score'],
                    'num_provers': len(reps_b),
                    'detail': consensus_b_to_a,
                },
                'timestamp': time.time(),
            }
            
            self._log_event('CROSS_LINE_VERIFY', 
                          f"{line_a} <-> {line_b}: score={combined_score:.3f}, verified={verified}"
            
            return result
    
    def _generate_cross_line_questions(self, state: StateVector, 
                                       from_line: str, to_line: str) -> List[Dict]:
        """生成跨线验证问题"""
        return [
            {
                'id': 'q_cross_line_id',
                'query': f'verify_line_identity_{from_line}_to_{to_line}',
                'expected': to_line,
                'weight': 2.0,
            },
            {
                'id': 'q_cross_si',
                'query': 'cross_line_si_verification',
                'expected': state.si_level,
                'weight': 1.5,
            },
            {
                'id': 'q_cross_coherence',
                'query': 'cross_line_coherence_check',
                'expected': round(state.coherence, 4),
                'weight': 1.5,
            },
            {
                'id': 'q_cross_shared_state',
                'query': 'shared_state_integrity',
                'expected': state.compute_hash()[:8],
                'weight': 3.0,
            },
        ]
    
    def verify_cross_line_matrix(self) -> Dict[str, Any]:
        """
        验证整个跨线矩阵
        
        检查11×11验证矩阵的完整性。
        """
        matrix = {}
        verified_pairs = 0
        total_pairs = 0
        
        for line_a in self.LINES[:self.num_lines]:
            matrix[line_a] = {}
            for line_b in self.LINES[:self.num_lines]:
                if line_a == line_b:
                    continue
                total_pairs += 1
                
                entry = self.cross_line_matrix.get(line_a, {}).get(line_b, {})
                if entry:
                    matrix[line_a][line_b] = entry
                    if entry.get('verified', False):
                        verified_pairs += 1
                else:
                    matrix[line_a][line_b] = {'verified': False, 'score': 0.0}
        
        coverage = verified_pairs / total_pairs if total_pairs > 0 else 0
        
        return {
            'matrix': matrix,
            'verified_pairs': verified_pairs,
            'total_pairs': total_pairs,
            'coverage': coverage,
            'fully_connected': coverage >= 0.8,
        }
    
    # ─────────────────────────────────────────────────────────
    # 时间维度验证
    # ─────────────────────────────────────────────────────────
    
    def temporal_verify(self, state: StateVector, 
                        history_depth: int = 10) -> Dict[str, Any]:
        """
        时间维度验证
        
        验证当前状态与历史状态的一致性，检测时间线上的异常。
        
        Args:
            state: 当前状态
            history_depth: 检查历史深度
            
        Returns:
            时间验证结果
        """
        with self.lock:
            self.verification_stats['temporal_verifications'] += 1
            
            if len(self.state_history) < 2:
                return {
                    'verified': True,
                    'reason': 'insufficient_history',
                    'anomaly_detected': False,
                }
            
            # 获取历史状态
            history = list(self.state_history)[-history_depth:]
            
            anomalies = []
            temporal_scores = []
            
            # 检查状态连续性
            current_hash = state.compute_hash()
            
            for i, record in enumerate(history):
                hist_state = StateVector.from_dict(record['state'])
                
                # 计算delta
                delta = state.delta_from(hist_state)
                
                # 检查异常
                checks = self._check_temporal_consistency(delta, state, hist_state)
                temporal_scores.append(checks['score'])
                
                if not checks['consistent']:
                    anomalies.append({
                        'index': i,
                        'historical_state': hist_state.to_dict(),
                        'delta': delta,
                        'reasons': checks['reasons'],
                    })
            
            # 计算时间一致性分数
            avg_temporal_score = sum(temporal_scores) / len(temporal_scores) if temporal_scores else 1.0
            
            # 异常检测阈值
            anomaly_threshold = 0.3
            anomaly_rate = len(anomalies) / len(history) if history else 0
            
            verified = avg_temporal_score >= anomaly_threshold and anomaly_rate < 0.5
            
            # 更新时间维度校验和
            self._update_temporal_checksum(state)
            
            return {
                'verified': verified,
                'anomaly_detected': len(anomalies) > 0,
                'anomaly_count': len(anomalies),
                'anomaly_rate': anomaly_rate,
                'temporal_score': avg_temporal_score,
                'history_depth': len(history),
                'anomalies': anomalies[:5],  # 只返回前5个异常
                'temporal_checksum': self._get_temporal_checksum(),
            }
    
    def _check_temporal_consistency(self, delta: Dict[str, float], 
                                    current: StateVector, 
                                    historical: StateVector) -> Dict[str, Any]:
        """检查时间一致性"""
        reasons = []
        score = 1.0
        
        # 检查能量突变
        if abs(delta['delta_energy']) > 0.5:
            reasons.append(f"energy_spike: {delta['delta_energy']:.3f}")
            score -= 0.3
        
        # 检查相干度异常下降
        if delta['delta_coherence'] < -0.3:
            reasons.append(f"coherence_drop: {delta['delta_coherence']:.3f}")
            score -= 0.25
        
        # 检查纠缠度异常
        if current.entanglement > current.coherence + 0.1:
            reasons.append("entanglement_exceeds_coherence")
            score -= 0.2
        
        # 检查时间倒流
        if delta['delta_time'] < 0:
            reasons.append("negative_time_delta")
            score -= 0.5
        
        # 检查SI层级跳变
        if abs(delta['delta_si']) > 2:
            reasons.append(f"si_level_jump: {delta['delta_si']}")
            score -= 0.15
        
        return {
            'consistent': len(reasons) == 0,
            'score': max(0.0, score),
            'reasons': reasons,
        }
    
    def _update_temporal_checksum(self, state: StateVector):
        """更新时间维度校验和"""
        checksum = hashlib.sha256(
            f"{state.compute_hash()}_{time.time()}".encode()
        ).hexdigest()[:16]
        self.temporal_checksums.append({
            'timestamp': time.time(),
            'checksum': checksum,
            'state_hash': state.compute_hash(),
        })
    
    def _get_temporal_checksum(self) -> str:
        """获取当前时间校验和"""
        if self.temporal_checksums:
            return self.temporal_checksums[-1]['checksum']
        return ""
    
    # ─────────────────────────────────────────────────────────
    # 自适应阈值调整
    # ─────────────────────────────────────────────────────────
    
    def adaptive_threshold_adjust(self) -> Dict[str, Any]:
        """
        自适应阈值调整
        
        根据系统健康度动态调整soundness_threshold：
        - health > 0.9: threshold = 0.99 (极严格)
        - health > 0.7: threshold = 0.95 (严格)
        - health > 0.5: threshold = 0.90 (标准)
        - health < 0.5: threshold = 0.85 (宽松，容错)
        
        Returns:
            调整结果
        """
        with self.lock:
            self.verification_stats['adaptive_adjustments'] += 1
            
            # 计算系统健康度
            health = self._compute_system_health()
            self.system_health = health
            self.health_history.append({
                'timestamp': time.time(),
                'health': health,
            })
            
            # 根据健康度调整阈值
            if health > 0.9:
                new_threshold = 0.99
                mode = 'ultra_strict'
            elif health > 0.7:
                new_threshold = 0.95
                mode = 'strict'
            elif health > 0.5:
                new_threshold = 0.90
                mode = 'standard'
            else:
                new_threshold = 0.85
                mode = 'lenient'
            
            old_threshold = self.base_threshold
            self.base_threshold = new_threshold
            
            # 同时调整各层的级联阈值
            for si, layer in self.verification_layers.items():
                layer.cascade_threshold = new_threshold + si * 0.005
            
            self._log_event('ADAPTIVE_ADJUST',
                          f"Health={health:.3f}, Threshold: {old_threshold:.2f} -> {new_threshold:.2f} ({mode}"))
            
            return {
                'health': health,
                'old_threshold': old_threshold,
                'new_threshold': new_threshold,
                'mode': mode,
                'adjustment_reason': self._get_health_reason(health),
            }
    
    def _compute_system_health(self) -> float:
        """
        计算系统健康度 [0,1]
        
        基于：
        - 验证成功率
        - 活跃证明者比例
        - 拜占庭节点比例
        - 平均共识时间
        """
        stats = self.verification_stats
        
        # 验证成功率
        total = stats['total_challenges']
        if total > 0:
            success_rate = stats['successful_verifications'] / total
        else:
            success_rate = 1.0
        
        # 活跃证明者比例
        total_provers = sum(len(p) for p in self.prover_pool.values())
        active_provers = sum(
            1 for line in self.prover_pool.values()
            for p in line.values() if p.status == ProverStatus.ACTIVE
        )
        active_ratio = active_provers / total_provers if total_provers > 0 else 0
        
        # 拜占庭节点比例
        byzantine_count = stats['byzantine_detected']
        byzantine_ratio = byzantine_count / total if total > 0 else 0
        
        # 共识时间因子 (越短越好)
        avg_time = stats['average_consensus_time']
        time_factor = max(0, 1.0 - avg_time / 5.0)  # 5秒为基准
        
        # 综合健康度
        health = (success_rate * 0.35 + 
                 active_ratio * 0.25 + 
                 (1 - byzantine_ratio) * 0.25 + 
                 time_factor * 0.15)
        
        return max(0.0, min(1.0, health))
    
    def _get_health_reason(self, health: float) -> str:
        """获取健康度原因描述"""
        if health > 0.9:
            return "System operating optimally"
        elif health > 0.7:
            return "System operating normally"
        elif health > 0.5:
            return "System showing signs of stress"
        else:
            return "System under duress - reducing thresholds for continuity"
    
    # ─────────────────────────────────────────────────────────
    # 加权共识计算
    # ─────────────────────────────────────────────────────────
    
    def compute_consensus(self, responses: Dict[str, Dict], 
                          weights: Dict[str, float]) -> Dict[str, Any]:
        """
        加权共识计算
        
        考虑证明者的能力分数和历史准确率，
        支持拜占庭容错（识别并排除恶意/故障证明者）。
        
        共识公式：
            score = Σ(w_i × c_i) / Σ(w_i)
            其中 w_i 是证明者权重，c_i 是正确率
        
        Args:
            responses: 证明者响应
            weights: 证明者权重
            
        Returns:
            共识结果
        """
        if not responses:
            return {
                'consensus_score': 0.0,
                'verified': False,
                'participating_provers': 0,
                'byzantine_excluded': 0,
            }
        
        # 排除已知的拜占庭节点和错误响应
        filtered_responses = {}
        filtered_weights = {}
        byzantine_excluded = 0
        
        for pid, resp in responses.items():
            if pid in self.byzantine_engine.faulty_provers:
                byzantine_excluded += 1
                continue
            if 'error' not in resp and 'answers' in resp:
                filtered_responses[pid] = resp
                filtered_weights[pid] = weights.get(pid, 0.5)
        
        if not filtered_responses:
            return {
                'consensus_score': 0.0,
                'verified': False,
                'participating_provers': 0,
                'byzantine_excluded': byzantine_excluded,
                'reason': 'all_provers_byzantine_or_error',
            }
        
        # 计算每个证明者的个体正确率
        prover_correct_rates = {}
        for pid, resp in filtered_responses.items():
            answers = resp.get('answers', {})
            correct_count = sum(1 for a in answers.values() if a.get('correct', False))
            total_count = len(answers)
            prover_correct_rates[pid] = correct_count / total_count if total_count > 0 else 0
        
        # 加权共识 = Σ(w_i × c_i) / Σ(w_i)
        total_weight = sum(filtered_weights.values())
        weighted_score = sum(
            filtered_weights[pid] * prover_correct_rates[pid]
            for pid in filtered_responses
        )
        
        consensus_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # 同时计算答案一致性（多数投票）
        answer_votes = defaultdict(lambda: defaultdict(float))
        for pid, resp in filtered_responses.items():
            weight = filtered_weights.get(pid, 0.5)
            for qid, ans_data in resp.get('answers', {}).items():
                answer = str(ans_data.get('answer', ''))
                answer_votes[qid][answer] += weight
        
        question_consensus_scores = []
        for qid, votes in answer_votes.items():
            if votes:
                max_votes = max(votes.values())
                total_votes = sum(votes.values())
                qc = max_votes / total_votes if total_votes > 0 else 0
                question_consensus_scores.append(qc)
        
        avg_question_consensus = (
            sum(question_consensus_scores) / len(question_consensus_scores)
            if question_consensus_scores else 0
        )
        
        # 最终共识分数：个体正确率 + 一致性（加权平均）
        final_consensus = 0.6 * consensus_score + 0.4 * avg_question_consensus
        
        # 自适应判定
        tolerance_config = self.byzantine_engine.adaptive_tolerance(
            self.system_health, len(filtered_responses)
        )
        required_agreement = tolerance_config['required_agreement']
        
        # 使用当前阈值进行判定
        effective_threshold = self.base_threshold
        verified = final_consensus >= effective_threshold
        
        return {
            'consensus_score': final_consensus,
            'individual_score': consensus_score,
            'consistency_score': avg_question_consensus,
            'verified': verified,
            'participating_provers': len(filtered_responses),
            'total_weight': total_weight,
            'byzantine_excluded': byzantine_excluded,
            'required_agreement': required_agreement,
            'effective_threshold': effective_threshold,
            'tolerance_mode': tolerance_config['mode'],
            'question_scores': question_consensus_scores,
        }
    
    # ─────────────────────────────────────────────────────────
    # 验证统计
    # ─────────────────────────────────────────────────────────
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """
        获取完整的验证统计
        
        Returns:
            验证统计数据
        """
        total = self.verification_stats['total_challenges']
        success = self.verification_stats['successful_verifications']
        failed = self.verification_stats['failed_verifications']
        
        success_rate = success / total if total > 0 else 0
        failure_rate = failed / total if total > 0 else 0
        
        # 各线证明者统计
        line_stats = {}
        for line_id in self.LINES[:self.num_lines]:
            provers = self.get_line_provers(line_id)
            line_stats[line_id] = {
                'total_provers': len(provers),
                'active_provers': sum(1 for p in provers if p.status == ProverStatus.ACTIVE),
                'faulty_provers': sum(1 for p in provers if p.status == ProverStatus.FAULTY),
                'avg_capability': sum(p.capability_score for p in provers) / len(provers) if provers else 0,
                'avg_accuracy': sum(p.history_accuracy for p in provers) / len(provers) if provers else 0,
            }
        
        # 各层统计
        layer_stats = {si: layer.get_stats() for si, layer in self.verification_layers.items()}
        
        # 拜占庭容错统计
        byzantine_stats = self.byzantine_engine.get_stats()
        
        # 跨线矩阵统计
        cross_line_stats = self.verify_cross_line_matrix()
        
        return {
            'session_id': self.session_id,
            'system_health': self.system_health,
            'current_threshold': self.base_threshold,
            'total_challenges': total,
            'successful_verifications': success,
            'failed_verifications': failed,
            'success_rate': success_rate,
            'failure_rate': failure_rate,
            'byzantine_detected': self.verification_stats['byzantine_detected'],
            'cross_line_verifications': self.verification_stats['cross_line_verifications'],
            'temporal_verifications': self.verification_stats['temporal_verifications'],
            'adaptive_adjustments': self.verification_stats['adaptive_adjustments'],
            'average_consensus_time': self.verification_stats['average_consensus_time'],
            'total_provers': sum(len(p) for p in self.prover_pool.values()),
            'active_provers': sum(
                1 for line in self.prover_pool.values()
                for p in line.values() if p.status == ProverStatus.ACTIVE
            ),
            'line_stats': line_stats,
            'layer_stats': layer_stats,
            'byzantine_stats': byzantine_stats,
            'cross_line_stats': cross_line_stats,
            'health_history': list(self.health_history)[-20:],
        }


# ═══════════════════════════════════════════════════════════════
# 实验验证
# ═══════════════════════════════════════════════════════════════

def run_experiments():
    """
    运行完整实验验证
    
    1. 注册55个证明者（11线×5证明者/线）
    2. 执行10次不同复杂度的挑战
    3. 执行跨线验证
    4. 执行时间维度验证
    5. 验证自适应阈值调整
    6. 返回完整验证统计
    """
    logger.info("=" * 80)
    logger.info("OMNI-HUB v7.0 HyperMIPCore 实验验证")
    logger.info("=" * 80)
    
    # 1. 初始化HyperMIPCore
    logger.info("\n[1/6] 初始化 HyperMIPCore...")
    core = HyperMIPCore(num_lines=11, base_threshold=0.95)
    logger.info(f"      Session ID: {core.session_id}")
    logger.info(f"      Base Threshold: {core.base_threshold}")
    
    # 2. 注册55个证明者（11线×5证明者/线）
    logger.info("\n[2/6] 注册55个证明者（11线 × 5证明者/线）...")
    
    lines = HyperMIPCore.LINES
    prover_id_counter = 0
    
    # 为每条线注册5个证明者，能力分布多样化
    for line in lines:
        for i in range(5):
            prover_id = f"{line}_prover_{i}"
            # 能力分数多样化：0.6-1.0，部分高能力节点
            if i < 2:
                capability = 0.85 + random.random() * 0.15  # 高能力
            elif i < 4:
                capability = 0.70 + random.random() * 0.15  # 中等能力
            else:
                capability = 0.60 + random.random() * 0.15  # 基础能力
            
            prover = core.register_prover(line, prover_id, capability)
            
            # 随机设置一些证明者为故障状态（约8%）
            if random.random() < 0.08:
                prover.status = ProverStatus.FAULTY
                prover.byzantine_flags = 3
                prover.trust_level = 0.2
                logger.info(f"        [!] {prover_id} on {line} marked as BYZANTINE")
            
            prover_id_counter += 1
    
    logger.info(f"      已注册 {prover_id_counter} 个证明者")
    
    # 统计各线证明者
    for line in lines:
        provers = core.get_line_provers(line)
        active = sum(1 for p in provers if p.status == ProverStatus.ACTIVE)
        faulty = sum(1 for p in provers if p.status == ProverStatus.FAULTY)
        avg_cap = sum(p.capability_score for p in provers) / len(provers) if provers else 0
        logger.info(f"        {line:8s}: {len(provers)} provers (active={active}, faulty={faulty}, avg_cap={avg_cap:.2f})")
    
    # 3. 执行10次不同复杂度的挑战
    logger.info("\n[3/6] 执行10次不同复杂度的动态挑战...")
    challenge_results = []
    
    for i in range(10):
        # 创建不同复杂度的状态
        si_level = random.randint(0, 6)
        energy = random.random()
        coherence = 0.6 + random.random() * 0.4  # 确保较高相干度
        entanglement = random.random() * coherence * 0.8  # 纠缠度不超过相干度
        
        state = StateVector(
            si_level=si_level,
            energy=energy,
            coherence=coherence,
            entanglement=entanglement,
            timestamp=time.time(),
            line_id=random.choice(lines),
            sequence_number=i,
        )
        
        # 动态挑战
        result = core.challenge_dynamic(state, min_provers=3, max_provers=11)
        challenge_results.append(result)
        
        status_icon = "[PASS]" if result['verified'] else "[FAIL]"
        print(f"      Challenge {i+1:2d}: SI={si_level} | ")
              f"Complexity={result['task_complexity']:.2f} | "
              f"Provers={result['num_provers']:2d} | "
              f"Score={result['consensus_score']:.3f} | "
              f"Threshold={result.get('threshold', core.base_threshold):.2f} | "
              f"{status_icon}"
    
    # 4. 执行跨线验证
    logger.info("\n[4/6] 执行跨线验证（11×11矩阵）...")
    cross_results = []
    
    # 选择10对线进行验证
    cross_pairs = [
        ('ucif2', 'lvlu'),
        ('lgt', 'qfa'),
        ('vinf', 'qgl'),
        ('qlv', 'cisvr'),
        ('qtlv', 'usrm'),
        ('usrm', 'cfts'),
        ('ucif2', 'cfts'),
        ('lvlu', 'qtlv'),
        ('lgt', 'vinf'),
        ('qfa', 'qlv'),
    ]
    
    for line_a, line_b in cross_pairs:
        shared_state = StateVector(
            si_level=random.randint(2, 5),
            energy=random.random() * 0.8 + 0.2,
            coherence=random.random() * 0.3 + 0.7,
            entanglement=random.random() * 0.3,
            timestamp=time.time(),
            line_id='cross_line',
        )
        
        result = core.cross_line_verify(line_a, line_b, shared_state)
        cross_results.append(result)
        
        status_icon = "[PASS]" if result['verified'] else "[FAIL]"
        print(f"      {line_a:6s} <-> {line_b:6s}: ")
              f"Combined={result['combined_score']:.3f} | "
              f"A→B={result['a_to_b']['score']:.3f} | "
              f"B→A={result['b_to_a']['score']:.3f} | "
              f"{status_icon}"
    
    # 验证整个矩阵
    matrix_stats = core.verify_cross_line_matrix()
    logger.info(f"\n      跨线矩阵统计:")
    logger.info(f"        验证对数: {matrix_stats['verified_pairs']}/{matrix_stats['total_pairs']}")
    logger.info(f"        覆盖率: {matrix_stats['coverage']:.1%}")
    logger.info(f"        完全连接: {matrix_stats['fully_connected']}")
    
    # 5. 执行时间维度验证
    logger.info("\n[5/6] 执行时间维度验证...")
    
    # 先生成一些历史状态（模拟正常运行的历史）
    for i in range(15):
        hist_state = StateVector(
            si_level=random.randint(1, 4),
            energy=0.3 + random.random() * 0.4,
            coherence=0.6 + random.random() * 0.3,
            entanglement=random.random() * 0.2,
            timestamp=time.time() - (15 - i) * 10,  # 每10秒一个历史状态
            line_id=random.choice(lines),
            sequence_number=i,
        )
        core.state_history.append({
            'timestamp': hist_state.timestamp,
            'state': hist_state.to_dict(),
            'verified': True,
            'consensus_score': 0.9 + random.random() * 0.1,
        })
    
    # 验证当前状态（正常状态）
    current_state = StateVector(
        si_level=3,
        energy=0.6,
        coherence=0.8,
        entanglement=0.2,
        timestamp=time.time(),
        line_id='ucif2',
        sequence_number=100,
    )
    
    temporal_result = core.temporal_verify(current_state, history_depth=10)
    logger.info(f"      正常状态时间验证:")
    logger.info(f"        验证通过: {temporal_result['verified']}")
    logger.info(f"        异常检测: {temporal_result['anomaly_detected']}")
    logger.info(f"        异常数量: {temporal_result['anomaly_count']}")
    logger.info(f"        时间一致性分数: {temporal_result['temporal_score']:.3f}")
    
    # 验证异常状态（能量突变）
    anomalous_state = StateVector(
        si_level=3,
        energy=0.95,  # 能量突变
        coherence=0.8,
        entanglement=0.2,
        timestamp=time.time(),
        line_id='ucif2',
        sequence_number=101,
    )
    
    temporal_result2 = core.temporal_verify(anomalous_state, history_depth=10)
    logger.info(f"\n      异常状态时间验证（能量突变）:")
    logger.info(f"        验证通过: {temporal_result2['verified']}")
    logger.info(f"        异常检测: {temporal_result2['anomaly_detected']}")
    logger.info(f"        异常数量: {temporal_result2['anomaly_count']}")
    logger.info(f"        时间一致性分数: {temporal_result2['temporal_score']:.3f}")
    
    # 6. 自适应阈值调整
    logger.info("\n[6/6] 验证自适应阈值调整...")
    
    # 模拟不同健康度下的阈值调整
    health_scenarios = [
        (0.95, "Optimal"),
        (0.80, "Normal"),
        (0.60, "Stressed"),
        (0.40, "Emergency"),
    ]
    
    # 先重置阈值
    core.base_threshold = 0.95
    
    for health, label in health_scenarios:
        # 先调整系统健康度（通过修改内部状态模拟）
        core.system_health = health
        result = core.adaptive_threshold_adjust()
        logger.info(f"      Health={health:.2f} ({label:10s})
              f"Threshold {result['old_threshold']:.2f} → {result['new_threshold']:.2f} "
              f"[{result['mode']:12s}] - {result['adjustment_reason']}"
    
    # 7. 拜占庭容错演示
    logger.info("\n[7/6] 拜占庭容错演示...")
    
    # 创建一个包含拜占庭节点的场景
    byzantine_state = StateVector(
        si_level=4,
        energy=0.7,
        coherence=0.85,
        entanglement=0.3,
        timestamp=time.time(),
        line_id='test_line',
        sequence_number=200,
    )
    
    # 将部分证明者设为拜占庭并发起挑战
    test_provers = core.select_prover_pool(0.8, 4)
    logger.info(f"      选择 {len(test_provers)} 个证明者进行拜占庭容错测试")
    
    # 模拟其中2个为拜占庭
    byzantine_count = 0
    for p in test_provers[:2]:
        if p.status != ProverStatus.FAULTY:
            p.status = ProverStatus.FAULTY
            byzantine_count += 1
    
    if byzantine_count > 0:
        logger.info(f"      模拟 {byzantine_count} 个拜占庭节点")
    
    result = core.challenge_dynamic(byzantine_state, min_provers=5, max_provers=11)
    
    if 'byzantine_check' in result:
        bc = result['byzantine_check']
        logger.info(f"      检测到故障证明者: {bc['faulty_count']}")
        logger.info(f"      可疑证明者: {bc['suspicious_count']}")
        logger.info(f"      共识分数: {result['consensus_score']:.3f}")
        logger.info(f"      验证结果: {'通过' if result['verified'] else '未通过'}")
    
    # 8. 获取完整验证统计
    logger.info("\n" + "=" * 80)
    logger.info("验证统计报告")
    logger.info("=" * 80)
    
    stats = core.get_verification_stats()
    
    logger.info(f"\n  会话ID: {stats['session_id']}")
    logger.info(f"  系统健康度: {stats['system_health']:.3f}")
    logger.info(f"  当前阈值: {stats['current_threshold']:.3f}")
    
    logger.info(f"\n  [挑战统计]")
    logger.info(f"    总挑战次数: {stats['total_challenges']}")
    logger.info(f"    成功验证: {stats['successful_verifications']}")
    logger.info(f"    失败验证: {stats['failed_verifications']}")
    logger.info(f"    成功率: {stats['success_rate']:.1%}")
    logger.info(f"    平均共识时间: {stats['average_consensus_time']*1000:.2f}ms")
    
    logger.info(f"\n  [证明者统计]")
    logger.info(f"    总证明者: {stats['total_provers']}")
    logger.info(f"    活跃证明者: {stats['active_provers']}")
    logger.info(f"    拜占庭检测: {stats['byzantine_detected']}")
    
    logger.info(f"\n  [各线统计]")
    for line, lstats in stats['line_stats'].items():
        print(f"    {line:8s}: {lstats['total_provers']} provers, ")
              f"avg_cap={lstats['avg_capability']:.2f}, "
              f"avg_acc={lstats['avg_accuracy']:.2f}"
    
    logger.info(f"\n  [各层统计]")
    for si, lstats in stats['layer_stats'].items():
        print(f"    SI{si}: {lstats['num_provers']:2d} provers, ")
              f"threshold={lstats['cascade_threshold']:.3f}, "
              f"success_rate={lstats['success_rate']:.1%}, "
              f"total={lstats['total_verifications']}"
    
    logger.info(f"\n  [拜占庭容错]")
    bstats = stats['byzantine_stats']
    logger.info(f"    基础容错率: {bstats['base_tolerance']:.1%}")
    logger.info(f"    自适应模式: {bstats['adaptive_mode']}")
    logger.info(f"    故障证明者: {bstats['faulty_provers']}")
    logger.info(f"    总检测次数: {bstats['total_detections']}")
    
    logger.info(f"\n  [跨线验证]")
    cstats = stats['cross_line_stats']
    logger.info(f"    验证对数: {cstats['verified_pairs']}/{cstats['total_pairs']}")
    logger.info(f"    覆盖率: {cstats['coverage']:.1%}")
    logger.info(f"    完全连接: {cstats['fully_connected']}")
    
    logger.info("\n" + "=" * 80)
    logger.info("实验验证完成!")
    logger.info("=" * 80)
    
    return {
        'core': core,
        'challenge_results': challenge_results,
        'cross_results': cross_results,
        'temporal_result': temporal_result,
        'stats': stats,
    }


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    results = run_experiments()
