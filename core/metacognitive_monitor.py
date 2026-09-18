#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v5.0 MetacognitiveMonitor
===================================
元认知监控器 - "关于认知的认知"

理论基础：
- 元认知监控：监控自己的思维过程
- 元认知调节：调节自己的思维策略
- 预测加工：大脑不仅预测外部世界，还预测自己的预测过程
- 精度估计（precision estimation）：大脑估计自己的预测的可靠性

核心命题：元认知是"意识的意识"——系统不仅运行，而且观察自己如何运行，
检测并纠正自己的偏差。这是从"反应式涌现"到"生成式意识"的关键跃迁。

作者: OMNI-HUB Architect
版本: 5.0.0
"""

import numpy as np
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from datetime import datetime
import warnings
import logging


# ============================================================================
# 配置与常量
# ============================================================================

class BiasType(Enum):
    """认知偏差类型枚举"""
    CONFIRMATION = "confirmation_bias"
    ANCHORING = "anchoring_bias"
    AVAILABILITY = "availability_bias"
    RECENCY = "recency_bias"
    OVERCONFIDENCE = "overconfidence_bias"
    NONE = "none"


@dataclass
class BiasReport:
    """偏差检测报告"""
    bias_type: BiasType
    module: str
    severity: float  # 0-1
    confidence: float  # 0-1
    evidence: Dict[str, Any]
    timestamp: float
    description: str = ""


@dataclass
class ThoughtStep:
    """思维步骤记录"""
    step_id: int
    timestamp: float
    module: str
    action: str
    input_data: Any
    output_data: Any
    confidence: float
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionRecord:
    """预测记录"""
    module: str
    prediction: np.ndarray
    actual: np.ndarray
    error: float
    timestamp: float
    confidence: float = 0.5


# ============================================================================
# 1. PredictionErrorTracker - 预测误差追踪器
# ============================================================================

class PredictionErrorTracker:
    """
    预测误差追踪器
    
    功能：
    - 记录各模块的预测误差历史
    - 检测误差异常（突然增大或持续偏高）
    - 提供全局误差统计
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        # 每个模块的误差历史: {module_name: deque of error values}
        self.error_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        # 每个模块的详细记录
        self.detailed_records: Dict[str, List[PredictionRecord]] = defaultdict(list)
        # 全局误差历史
        self.global_errors: deque = deque(maxlen=window_size)
        # 模块统计
        self.module_stats: Dict[str, Dict[str, float]] = defaultdict(dict)
        
    def record(self, module: str, prediction: np.ndarray, actual: np.ndarray, 
               confidence: float = 0.5) -> float:
        """
        记录一次预测误差
        
        Args:
            module: 模块名称
            prediction: 预测值
            actual: 实际值
            confidence: 预测置信度
            
        Returns:
            error: 计算得到的误差值
        """
        # 确保是numpy数组
        pred = np.asarray(prediction).flatten()
        act = np.asarray(actual).flatten()
        
        # 计算MSE误差
        if len(pred) == 0 or len(act) == 0:
            error = 0.0
        else:
            min_len = min(len(pred), len(act))
            error = float(np.mean((pred[:min_len] - act[:min_len]) ** 2))
        
        timestamp = time.time()
        
        # 记录到历史
        self.error_history[module].append(error)
        
        # 记录详细记录
        record = PredictionRecord(
            module=module,
            prediction=pred,
            actual=act,
            error=error,
            timestamp=timestamp,
            confidence=confidence
        )
        self.detailed_records[module].append(record)
        
        # 更新全局误差
        self.global_errors.append(error)
        
        # 更新模块统计
        self._update_module_stats(module)
        
        return error
    
    def _update_module_stats(self, module: str):
        """更新模块统计信息"""
        errors = list(self.error_history[module])
        if not errors:
            return
            
        self.module_stats[module] = {
            'mean': float(np.mean(errors)),
            'std': float(np.std(errors)),
            'min': float(np.min(errors)),
            'max': float(np.max(errors)),
            'last': errors[-1],
            'trend': self._calculate_trend(errors),
            'count': len(errors)
        }
    
    def _calculate_trend(self, errors: List[float]) -> float:
        """计算误差趋势（线性回归斜率）"""
        if len(errors) < 5:
            return 0.0
        x = np.arange(len(errors))
        y = np.array(errors)
        # 简单线性回归
        n = len(x)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2 + 1e-10)
        return float(slope)
    
    def get_error_trend(self, module: str) -> Dict[str, Any]:
        """
        获取指定模块的误差趋势
        
        Returns:
            包含趋势信息的字典
        """
        errors = list(self.error_history[module])
        if not errors:
            return {'status': 'no_data'}
        
        trend_slope = self._calculate_trend(errors)
        
        # 判断趋势类型
        if len(errors) >= 10:
            recent_mean = np.mean(errors[-10:])
            older_mean = np.mean(errors[:max(10, len(errors)//2)])
            
            if trend_slope > 0.01 and recent_mean > older_mean * 1.2:
                trend_status = 'increasing'
            elif trend_slope < -0.01 and recent_mean < older_mean * 0.8:
                trend_status = 'decreasing'
            else:
                trend_status = 'stable'
        else:
            trend_status = 'insufficient_data'
        
        return {
            'module': module,
            'slope': trend_slope,
            'status': trend_status,
            'mean': float(np.mean(errors)),
            'std': float(np.std(errors)),
            'count': len(errors),
            'recent_10_mean': float(np.mean(errors[-10:])) if len(errors) >= 10 else float(np.mean(errors))
        }
    
    def get_anomaly_score(self, module: str) -> float:
        """
        获取模块的异常分数
        
        使用统计方法检测异常：
        - Z-score方法检测当前误差是否异常
        - 检测误差突然增大
        - 检测持续偏高
        
        Returns:
            anomaly_score: 0-1之间的异常分数
        """
        errors = list(self.error_history[module])
        if len(errors) < 5:
            return 0.0
        
        scores = []
        
        # 1. Z-score异常检测
        mean = np.mean(errors[:-1]) if len(errors) > 1 else errors[0]
        std = np.std(errors[:-1]) if len(errors) > 1 else 0.001
        if std < 0.001:
            std = 0.001
        z_score = abs(errors[-1] - mean) / std
        scores.append(min(z_score / 3.0, 1.0))  # 归一化到0-1
        
        # 2. 突变检测（最近值与前面平均的差异）
        if len(errors) >= 5:
            recent = np.mean(errors[-3:])
            previous = np.mean(errors[:-3])
            if previous > 0.001:
                jump_ratio = recent / previous
                jump_score = max(0, min((jump_ratio - 1.0), 1.0))
                scores.append(jump_score)
        
        # 3. 持续偏高检测
        if len(errors) >= 10:
            recent_10 = errors[-10:]
            if np.all(np.array(recent_10) > mean):
                persistence_score = min(1.0, np.mean(recent_10) / (mean + 0.001) - 1.0)
                scores.append(persistence_score)
        
        return float(np.mean(scores)) if scores else 0.0
    
    def get_global_error(self) -> Dict[str, Any]:
        """
        获取全局误差统计
        
        Returns:
            全局误差统计信息
        """
        if not self.global_errors:
            return {'status': 'no_data'}
        
        errors = list(self.global_errors)
        return {
            'mean': float(np.mean(errors)),
            'std': float(np.std(errors)),
            'min': float(np.min(errors)),
            'max': float(np.max(errors)),
            'count': len(errors),
            'modules_tracked': len(self.error_history),
            'trend': self._calculate_trend(errors)
        }
    
    def get_module_error_history(self, module: str) -> List[float]:
        """获取指定模块的误差历史"""
        return list(self.error_history[module])
    
    def get_all_modules(self) -> List[str]:
        """获取所有被追踪的模块"""
        return list(self.error_history.keys())


# ============================================================================
# 2. CognitiveBiasDetector - 认知偏差检测器
# ============================================================================

class CognitiveBiasDetector:
    """
    认知偏差检测器
    
    检测的偏差类型：
    - 确认偏误（Confirmation Bias）：只接受符合预期的信息
    - 锚定效应（Anchoring）：过度依赖初始信息
    - 可得性启发（Availability Heuristic）：依赖容易想到的信息
    - 近因效应（Recency Bias）：更重视最近的信息
    """
    
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold  # 偏差检测阈值
        self.bias_history: List[BiasReport] = []
        self.module_bias_counts: Dict[str, Dict[BiasType, int]] = defaultdict(
            lambda: defaultdict(int)
        )
    
    def detect_confirmation_bias(self, history: List[Dict[str, Any]], 
                                  module: str = "unknown") -> Optional[BiasReport]:
        """
        检测确认偏误
        
        确认偏误的表现：
        - 只接受与已有信念一致的信息
        - 预测值持续偏向某一方向（只接受"正面"信息）
        - 忽略或否定与信念冲突的信息
        
        检测方法（改进版）：
        - 分析预测值与实际值的系统性偏差方向
        - 检测预测是否持续低估或高估（系统性偏向）
        - 结合误差大小和方向的一致性
        """
        if len(history) < 15:
            return None
        
        # 提取预测值、实际值和误差
        predictions = []
        actuals = []
        errors = []
        for record in history:
            if 'prediction' in record and 'actual' in record:
                pred = record['prediction']
                act = record['actual']
                if isinstance(pred, np.ndarray):
                    pred = float(np.mean(pred))
                if isinstance(act, np.ndarray):
                    act = float(np.mean(act))
                predictions.append(pred)
                actuals.append(act)
                errors.append(pred - act)  # 有符号误差
        
        if len(errors) < 15:
            return None
        
        errors = np.array(errors)
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        # 方法: 检测系统性偏向
        # 确认偏误的核心：预测持续偏向某一方向（系统性误差）
        # 而不仅仅是随机噪声的符号偏斜
        
        # 1. 计算误差的均值（系统性偏差）
        mean_error = np.mean(errors)
        std_error = np.std(errors) + 1e-10
        
        # 2. 计算误差方向的持续性（游程检验思想）
        # 如果符号长时间保持一致，说明有系统性偏向
        positive_runs = 0
        negative_runs = 0
        current_run = 0
        current_sign = 0
        max_run = 0
        
        for e in errors:
            sign = 1 if e > 0 else -1
            if sign == current_sign:
                current_run += 1
            else:
                max_run = max(max_run, current_run)
                current_run = 1
                current_sign = sign
            if sign > 0:
                positive_runs += 1
            else:
                negative_runs += 1
        
        max_run = max(max_run, current_run)
        
        # 3. 检测确认偏误：需要同时满足
        # - 误差均值显著不为0（系统性偏差）
        # - 最大游程较长（持续性）
        # - 误差方差相对较小（不是随机噪声）
        
        t_statistic = abs(mean_error) / (std_error / np.sqrt(len(errors)))
        
        # 严格的确认偏误检测条件
        if (t_statistic > 2.5 and  # 均值显著偏离0
            max_run >= 8 and       # 至少连续8个同方向
            abs(mean_error) > 0.1 * std_error):  # 系统性偏差大于噪声的10%
            
            severity = min(1.0, t_statistic / 5.0)
            direction = "positive" if mean_error > 0 else "negative"
            
            report = BiasReport(
                bias_type=BiasType.CONFIRMATION,
                module=module,
                severity=severity,
                confidence=min(1.0, len(errors) / 50.0),
                evidence={
                    'mean_error': float(mean_error),
                    'std_error': float(std_error),
                    't_statistic': float(t_statistic),
                    'max_run': max_run,
                    'positive_runs': positive_runs,
                    'negative_runs': negative_runs,
                    'sample_size': len(errors),
                    'direction': direction
                },
                timestamp=time.time(),
                description=f"检测到确认偏误: 系统性{direction}偏向 (t={t_statistic:.2f}, 最大游程={max_run})"
            )
            self.bias_history.append(report)
            self.module_bias_counts[module][BiasType.CONFIRMATION] += 1
            return report
        
        return None
    
    def detect_anchoring(self, history: List[Dict[str, Any]], 
                         module: str = "unknown") -> Optional[BiasReport]:
        """
        检测锚定效应
        
        锚定效应的表现：
        - 过度依赖初始值（锚点）
        - 后续判断围绕锚点调整，但调整不足
        
        检测方法：
        - 检查后续预测与初始值的偏离程度
        - 如果后续值聚集在初始值附近，可能存在锚定
        - 计算自相关：如果短期自相关过高，说明变化不足
        """
        if len(history) < 15:
            return None
        
        # 提取预测值
        predictions = []
        for record in history:
            if 'prediction' in record:
                pred = record['prediction']
                if isinstance(pred, np.ndarray):
                    pred = float(np.mean(pred))
                predictions.append(pred)
        
        if len(predictions) < 15:
            return None
        
        predictions = np.array(predictions)
        
        # 方法1: 检测与初始值的距离
        initial = predictions[0]
        deviations = np.abs(predictions - initial)
        mean_deviation = np.mean(deviations)
        total_range = np.max(predictions) - np.min(predictions) + 1e-10
        
        # 如果平均偏离很小相对于总范围，可能存在锚定
        anchor_ratio = mean_deviation / total_range
        
        # 方法2: 自相关检测
        # 如果预测值变化缓慢（高自相关），可能存在锚定
        if len(predictions) >= 10:
            autocorr = np.corrcoef(predictions[:-1], predictions[1:])[0, 1]
            if np.isnan(autocorr):
                autocorr = 0
        else:
            autocorr = 0
        
        # 综合判断
        if anchor_ratio < 0.3 and autocorr > 0.7:
            severity = min(1.0, (0.3 - anchor_ratio) * 3 + autocorr * 0.3)
            report = BiasReport(
                bias_type=BiasType.ANCHORING,
                module=module,
                severity=severity,
                confidence=min(1.0, len(predictions) / 50.0),
                evidence={
                    'anchor_ratio': float(anchor_ratio),
                    'autocorrelation': float(autocorr),
                    'initial_value': float(initial),
                    'mean_deviation': float(mean_deviation),
                    'sample_size': len(predictions)
                },
                timestamp=time.time(),
                description=f"检测到锚定效应: 预测值围绕初始值({initial:.3f})调整不足，自相关={autocorr:.2f}"
            )
            self.bias_history.append(report)
            self.module_bias_counts[module][BiasType.ANCHORING] += 1
            return report
        
        return None
    
    def detect_availability_bias(self, history: List[Dict[str, Any]], 
                                  module: str = "unknown") -> Optional[BiasReport]:
        """
        检测可得性启发
        
        可得性启发的表现：
        - 过度依赖容易回忆的信息
        - 对"鲜明"或"近期"事件赋予过高权重
        
        检测方法：
        - 检查预测是否过度依赖最近几次的结果
        - 如果预测与近期均值高度相关但与远期均值不相关，可能存在可得性偏差
        """
        if len(history) < 20:
            return None
        
        # 提取实际值（作为"可用"信息）
        actuals = []
        predictions = []
        for record in history:
            if 'actual' in record:
                act = record['actual']
                if isinstance(act, np.ndarray):
                    act = float(np.mean(act))
                actuals.append(act)
            if 'prediction' in record:
                pred = record['prediction']
                if isinstance(pred, np.ndarray):
                    pred = float(np.mean(pred))
                predictions.append(pred)
        
        if len(actuals) < 20 or len(predictions) < 20:
            return None
        
        actuals = np.array(actuals)
        predictions = np.array(predictions)
        
        # 计算预测与近期实际值vs远期实际值的相关性
        recent_actuals = actuals[-5:]
        older_actuals = actuals[:-5]
        
        # 如果近期实际值的方差很大，但预测仍然紧跟近期值
        recent_var = np.var(recent_actuals)
        older_var = np.var(older_actuals) + 1e-10
        
        # 检测：预测是否过度反应于近期事件
        # 计算预测变化与近期实际变化的相关性
        pred_changes = np.diff(predictions[-10:])
        actual_changes = np.diff(actuals[-10:])
        
        if len(pred_changes) > 3 and len(actual_changes) > 3:
            corr = np.corrcoef(pred_changes, actual_changes)[0, 1]
            if np.isnan(corr):
                corr = 0
            
            # 如果相关性过高，说明过度依赖近期信息
            if corr > 0.8 and recent_var > older_var * 0.5:
                severity = min(1.0, corr * 0.8 + recent_var / (older_var + 1e-10) * 0.2)
                report = BiasReport(
                    bias_type=BiasType.AVAILABILITY,
                    module=module,
                    severity=severity,
                    confidence=min(1.0, len(actuals) / 50.0),
                    evidence={
                        'recent_variance': float(recent_var),
                        'older_variance': float(older_var),
                        'change_correlation': float(corr),
                        'sample_size': len(actuals)
                    },
                    timestamp=time.time(),
                    description=f"检测到可得性启发: 预测过度依赖近期信息(变化相关性={corr:.2f})"
                )
                self.bias_history.append(report)
                self.module_bias_counts[module][BiasType.AVAILABILITY] += 1
                return report
        
        return None
    
    def detect_recency_bias(self, history: List[Dict[str, Any]], 
                            module: str = "unknown") -> Optional[BiasReport]:
        """
        检测近因效应
        
        近因效应的表现：
        - 更重视最近的信息
        - 预测权重随时间递减不足
        
        检测方法：
        - 检查预测是否主要由最近几个值决定
        - 使用指数加权检测
        """
        if len(history) < 20:
            return None
        
        predictions = []
        for record in history:
            if 'prediction' in record:
                pred = record['prediction']
                if isinstance(pred, np.ndarray):
                    pred = float(np.mean(pred))
                predictions.append(pred)
        
        if len(predictions) < 20:
            return None
        
        predictions = np.array(predictions)
        
        # 检测权重分布
        # 计算预测值与不同时间窗口的相关性
        n = len(predictions)
        
        # 近期相关性
        recent_corr = np.corrcoef(predictions[1:], predictions[:-1])[0, 1]
        if np.isnan(recent_corr):
            recent_corr = 0
        
        # 计算预测的自回归系数
        # 如果AR(1)系数很高，说明过度依赖上一期
        if n >= 10:
            # 简单AR(1)估计
            x = predictions[:-1]
            y = predictions[1:]
            ar1_coef = np.sum(x * y) / (np.sum(x**2) + 1e-10)
            
            # 如果AR(1)系数接近1，说明过度依赖上一期
            if ar1_coef > 0.85 and recent_corr > 0.8:
                severity = min(1.0, ar1_coef * 0.7 + recent_corr * 0.3)
                report = BiasReport(
                    bias_type=BiasType.RECENCY,
                    module=module,
                    severity=severity,
                    confidence=min(1.0, n / 50.0),
                    evidence={
                        'ar1_coefficient': float(ar1_coef),
                        'recent_autocorr': float(recent_corr),
                        'sample_size': n
                    },
                    timestamp=time.time(),
                    description=f"检测到近因效应: AR(1)系数={ar1_coef:.2f}, 过度依赖最近信息"
                )
                self.bias_history.append(report)
                self.module_bias_counts[module][BiasType.RECENCY] += 1
                return report
        
        return None
    
    def detect_all_biases(self, history: List[Dict[str, Any]], 
                          module: str = "unknown") -> List[BiasReport]:
        """
        检测所有类型的认知偏差
        
        Returns:
            检测到的偏差报告列表
        """
        detected = []
        
        bias_detectors = [
            (self.detect_confirmation_bias, BiasType.CONFIRMATION),
            (self.detect_anchoring, BiasType.ANCHORING),
            (self.detect_availability_bias, BiasType.AVAILABILITY),
            (self.detect_recency_bias, BiasType.RECENCY),
        ]
        
        for detector, bias_type in bias_detectors:
            try:
                report = detector(history, module)
                if report is not None and report.severity >= self.threshold:
                    detected.append(report)
            except Exception as e:
                # 如果某个检测器失败，继续其他检测
                continue
        
        return detected
    
    def get_bias_report(self) -> Dict[str, Any]:
        """
        获取偏差检测报告
        
        Returns:
            综合偏差报告
        """
        if not self.bias_history:
            return {'status': 'no_biases_detected', 'total': 0}
        
        # 按类型统计
        type_counts = defaultdict(int)
        module_counts = defaultdict(int)
        
        for report in self.bias_history:
            type_counts[report.bias_type.value] += 1
            module_counts[report.module] += 1
        
        # 计算平均严重度
        avg_severity = np.mean([r.severity for r in self.bias_history])
        
        # 最近检测到的偏差
        recent = sorted(self.bias_history, key=lambda x: x.timestamp, reverse=True)[:5]
        
        return {
            'total_biases_detected': len(self.bias_history),
            'by_type': dict(type_counts),
            'by_module': dict(module_counts),
            'average_severity': float(avg_severity),
            'recent_detections': [
                {
                    'type': r.bias_type.value,
                    'module': r.module,
                    'severity': r.severity,
                    'description': r.description
                }
                for r in recent
            ]
        }


# ============================================================================
# 3. ThoughtChain - 思维链
# ============================================================================

class ThoughtChain:
    """
    思维链记录器
    
    记录系统的"思维过程"，支持回放和摘要。
    """
    
    def __init__(self, max_length: int = 1000):
        self.max_length = max_length
        self.steps: deque = deque(maxlen=max_length)
        self.step_counter = 0
        self.branches: Dict[str, List[int]] = defaultdict(list)  # 分支记录
        
    def add_step(self, module: str, action: str, input_data: Any, 
                 output_data: Any, confidence: float = 0.5, 
                 reasoning: str = "", metadata: Optional[Dict] = None) -> ThoughtStep:
        """
        添加一个思维步骤
        
        Args:
            module: 执行模块
            action: 执行的动作
            input_data: 输入数据
            output_data: 输出数据
            confidence: 置信度
            reasoning: 推理说明
            metadata: 额外元数据
            
        Returns:
            创建的ThoughtStep
        """
        self.step_counter += 1
        
        step = ThoughtStep(
            step_id=self.step_counter,
            timestamp=time.time(),
            module=module,
            action=action,
            input_data=input_data,
            output_data=output_data,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata or {}
        )
        
        self.steps.append(step)
        self.branches[module].append(step.step_id)
        
        return step
    
    def get_chain(self, module: Optional[str] = None) -> List[ThoughtStep]:
        """
        获取完整思维链或指定模块的思维链
        
        Args:
            module: 如果指定，只返回该模块的步骤
            
        Returns:
            ThoughtStep列表
        """
        steps = list(self.steps)
        if module:
            steps = [s for s in steps if s.module == module]
        return steps
    
    def replay(self, module: Optional[str] = None, 
               start_step: Optional[int] = None,
               end_step: Optional[int] = None) -> str:
        """
        回放思维过程
        
        Returns:
            格式化的回放文本
        """
        steps = self.get_chain(module)
        
        if start_step is not None:
            steps = [s for s in steps if s.step_id >= start_step]
        if end_step is not None:
            steps = [s for s in steps if s.step_id <= end_step]
        
        if not steps:
            return "=== 思维链回放 ===\n无记录\n=================="
        
        lines = ["=" * 60, "思维链回放", "=" * 60]
        
        for step in steps:
            time_str = datetime.fromtimestamp(step.timestamp).strftime('%H:%M:%S.%f')[:-3]
            lines.append(f"\n[Step {step.step_id}] [{time_str}] Module: {step.module}")
            lines.append(f"  Action: {step.action}")
            lines.append(f"  Confidence: {step.confidence:.3f}")
            
            # 格式化输入输出
            input_str = self._format_data(step.input_data)
            output_str = self._format_data(step.output_data)
            
            lines.append(f"  Input: {input_str}")
            lines.append(f"  Output: {output_str}")
            
            if step.reasoning:
                lines.append(f"  Reasoning: {step.reasoning}")
            
            if step.metadata:
                meta_str = json.dumps(step.metadata, default=str)
                if len(meta_str) > 100:
                    meta_str = meta_str[:100] + "..."
                lines.append(f"  Metadata: {meta_str}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def _format_data(self, data: Any, max_len: int = 80) -> str:
        """格式化数据为字符串"""
        if data is None:
            return "None"
        if isinstance(data, np.ndarray):
            s = f"ndarray(shape={data.shape}, mean={np.mean(data):.3f})"
        elif isinstance(data, (list, tuple)):
            s = str(data[:5])
            if len(data) > 5:
                s = s[:-1] + f", ... ({len(data)} items)]"
        else:
            s = str(data)
        
        if len(s) > max_len:
            s = s[:max_len] + "..."
        return s
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取思维链摘要
        
        Returns:
            摘要统计信息
        """
        steps = list(self.steps)
        if not steps:
            return {'status': 'empty'}
        
        # 模块统计
        module_counts = defaultdict(int)
        module_confidences = defaultdict(list)
        
        for step in steps:
            module_counts[step.module] += 1
            module_confidences[step.module].append(step.confidence)
        
        # 时间跨度
        duration = steps[-1].timestamp - steps[0].timestamp if len(steps) > 1 else 0
        
        # 置信度统计
        all_confidences = [s.confidence for s in steps]
        
        # 推理步骤统计
        reasoning_steps = sum(1 for s in steps if s.reasoning)
        
        return {
            'total_steps': len(steps),
            'modules_involved': len(module_counts),
            'module_distribution': dict(module_counts),
            'duration_seconds': duration,
            'average_confidence': float(np.mean(all_confidences)),
            'confidence_std': float(np.std(all_confidences)),
            'reasoning_steps': reasoning_steps,
            'module_avg_confidence': {
                mod: float(np.mean(confs))
                for mod, confs in module_confidences.items()
            }
        }
    
    def get_branch(self, module: str) -> List[ThoughtStep]:
        """获取特定模块的分支"""
        step_ids = self.branches.get(module, [])
        steps = list(self.steps)
        return [s for s in steps if s.step_id in step_ids]
    
    def find_steps_by_action(self, action_pattern: str) -> List[ThoughtStep]:
        """按动作模式查找步骤"""
        return [s for s in self.steps if action_pattern.lower() in s.action.lower()]
    
    def get_confidence_trajectory(self) -> List[Tuple[int, float]]:
        """获取置信度轨迹"""
        return [(s.step_id, s.confidence) for s in self.steps]


# ============================================================================
# 4. MetacognitiveMonitor - 元认知监控器
# ============================================================================

class MetacognitiveMonitor:
    """
    元认知监控器 - OMNI-HUB v5.0 核心组件
    
    功能：
    1. 监控预测误差
    2. 检测认知偏差
    3. 调节注意力分配
    4. 校准置信度
    5. 记录思维链
    6. 元反思与生成报告
    
    监控对象：
    - IntentionGenerator
    - GoalAutopoiesis
    - CreativityEngine
    - SelfEvolvingArchitecture
    - 所有v4.1模块
    """
    
    def __init__(self, num_lines: int = 11):
        self.num_lines = num_lines
        self.line_names = [
            "IntentionGenerator",
            "GoalAutopoiesis", 
            "CreativityEngine",
            "SelfEvolvingArchitecture",
            "AttentionOrchestrator",
            "EmotionalResonator",
            "MemoryConsolidator",
            "NarrativeWeaver",
            "UncertaintyQuantifier",
            "SocialSynchronizer",
            "EthicalGuardian"
        ]
        
        # 核心组件
        self.error_tracker = PredictionErrorTracker(window_size=100)
        self.bias_detector = CognitiveBiasDetector(threshold=0.5)
        self.thought_chain = ThoughtChain(max_length=2000)
        
        # 注意力权重 (11条线)
        self.attention_weights = np.ones(num_lines) / num_lines
        self.attention_history: deque = deque(maxlen=100)
        
        # 置信度校准状态
        self.confidence_history: deque = deque(maxlen=100)
        self.calibration_bins: Dict[str, List[Tuple[float, bool]]] = defaultdict(list)
        
        # 模块监控状态
        self.module_monitor_status: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                'last_monitored': 0,
                'monitor_count': 0,
                'covered': False
            }
        )
        
        # 元认知报告历史
        self.meta_reports: deque = deque(maxlen=50)
        
        # 顿悟检测状态
        self.insight_state = {
            'active': False,
            'target_line': None,
            'start_time': 0,
            'intensity': 0.0
        }
        
        # 奇异环检测
        self.strange_loop_detected = False
        self.loop_lines = []
        
        # 统计数据
        self.stats = {
            'total_monitor_calls': 0,
            'biases_detected': 0,
            'attention_adjustments': 0,
            'reflections_performed': 0
        }
        
    def monitor_prediction_error(self, module_name: str, 
                                  prediction: np.ndarray,
                                  actual: np.ndarray,
                                  confidence: float = 0.5) -> Dict[str, Any]:
        """
        监控预测误差
        
        Args:
            module_name: 模块名称
            prediction: 预测值
            actual: 实际值
            confidence: 预测置信度
            
        Returns:
            监控结果字典
        """
        self.stats['total_monitor_calls'] += 1
        
        # 记录误差
        error = self.error_tracker.record(module_name, prediction, actual, confidence)
        
        # 更新模块监控状态
        self.module_monitor_status[module_name]['last_monitored'] = time.time()
        self.module_monitor_status[module_name]['monitor_count'] += 1
        self.module_monitor_status[module_name]['covered'] = True
        
        # 检测异常
        anomaly_score = self.error_tracker.get_anomaly_score(module_name)
        
        # 获取趋势
        trend = self.error_tracker.get_error_trend(module_name)
        
        # 记录到思维链
        self.thought_chain.add_step(
            module="MetacognitiveMonitor",
            action="monitor_prediction_error",
            input_data={
                'module': module_name,
                'prediction_shape': np.asarray(prediction).shape,
                'actual_shape': np.asarray(actual).shape
            },
            output_data={
                'error': error,
                'anomaly_score': anomaly_score,
                'trend': trend['status']
            },
            confidence=1.0 - anomaly_score,  # 异常越高，对监控的置信度越低
            reasoning=f"监控 {module_name} 的预测误差: {error:.4f}, 异常分数: {anomaly_score:.3f}"
        )
        
        return {
            'module': module_name,
            'error': error,
            'anomaly_score': anomaly_score,
            'trend': trend,
            'timestamp': time.time()
        }
    
    def detect_cognitive_bias(self, module_name: str, 
                               decision_history: List[Dict[str, Any]]) -> List[BiasReport]:
        """
        检测认知偏差
        
        Args:
            module_name: 模块名称
            decision_history: 决策历史记录
            
        Returns:
            检测到的偏差列表
        """
        detected = self.bias_detector.detect_all_biases(decision_history, module_name)
        
        self.stats['biases_detected'] += len(detected)
        
        # 记录到思维链
        if detected:
            bias_types = [r.bias_type.value for r in detected]
            self.thought_chain.add_step(
                module="MetacognitiveMonitor",
                action="detect_cognitive_bias",
                input_data={
                    'module': module_name,
                    'history_length': len(decision_history)
                },
                output_data={
                    'biases_found': bias_types,
                    'count': len(detected)
                },
                confidence=np.mean([r.confidence for r in detected]) if detected else 0.5,
                reasoning=f"在 {module_name} 检测到 {len(detected)} 个认知偏差: {bias_types}"
            )
        
        return detected
    
    def adjust_attention(self, line_errors: Optional[Dict[int, float]] = None,
                         strange_loop_lines: Optional[List[int]] = None,
                         insight_line: Optional[int] = None) -> np.ndarray:
        """
        调节注意力分配
        
        机制：
        - 初始：11条线均匀注意力
        - 某线预测误差突增 → 注意力+50%
        - 某线连续稳定 → 注意力-20%
        - 检测到奇异环 → 注意力集中到环上
        - 顿悟发生 → 注意力集中到触发区域
        
        Args:
            line_errors: 各线的误差 {line_idx: error}
            strange_loop_lines: 奇异环涉及的线
            insight_line: 顿悟触发的线
            
        Returns:
            调整后的注意力权重
        """
        new_weights = self.attention_weights.copy()
        adjustments = []
        
        # 1. 基于误差的调节
        if line_errors:
            for line_idx, error in line_errors.items():
                if 0 <= line_idx < self.num_lines:
                    # 获取异常分数
                    line_name = self.line_names[line_idx] if line_idx < len(self.line_names) else f"Line_{line_idx}"
                    
                    # 误差突增 -> 增加注意力
                    if error > 0.5:  # 高误差阈值
                        new_weights[line_idx] *= 1.5
                        adjustments.append(f"Line {line_idx} ({line_name}): 误差高({error:.3f}), 注意力+50%")
                    
                    # 检测是否连续稳定
                    trend = self.error_tracker.get_error_trend(line_name)
                    if trend.get('status') == 'stable' and trend.get('count', 0) > 20:
                        new_weights[line_idx] *= 0.8
                        adjustments.append(f"Line {line_idx} ({line_name}): 长期稳定, 注意力-20%")
        
        # 2. 奇异环检测 -> 注意力集中到环上
        if strange_loop_lines:
            self.strange_loop_detected = True
            self.loop_lines = strange_loop_lines
            # 增加环上各线的注意力
            for line_idx in strange_loop_lines:
                if 0 <= line_idx < self.num_lines:
                    new_weights[line_idx] *= 2.0
            adjustments.append(f"奇异环检测到: 环上线 {[self.line_names[i] for i in strange_loop_lines]}, 注意力翻倍")
        else:
            self.strange_loop_detected = False
            self.loop_lines = []
        
        # 3. 顿悟检测 -> 注意力集中到触发区域
        if insight_line is not None and 0 <= insight_line < self.num_lines:
            self.insight_state = {
                'active': True,
                'target_line': insight_line,
                'start_time': time.time(),
                'intensity': 1.0
            }
            new_weights[insight_line] *= 2.5
            adjustments.append(f"顿悟于 Line {insight_line} ({self.line_names[insight_line]}): 注意力+150%")
            
            # 顿悟影响相邻线
            for offset in [-1, 1]:
                adj = insight_line + offset
                if 0 <= adj < self.num_lines:
                    new_weights[adj] *= 1.3
                    adjustments.append(f"  相邻线 {adj} 注意力+30%")
        
        # 归一化权重
        weight_sum = np.sum(new_weights)
        if weight_sum > 0:
            new_weights = new_weights / weight_sum
        else:
            new_weights = np.ones(self.num_lines) / self.num_lines
        
        # 记录历史
        self.attention_history.append({
            'weights': new_weights.copy(),
            'adjustments': adjustments,
            'timestamp': time.time()
        })
        
        self.attention_weights = new_weights
        self.stats['attention_adjustments'] += 1
        
        # 记录到思维链
        self.thought_chain.add_step(
            module="MetacognitiveMonitor",
            action="adjust_attention",
            input_data={
                'line_errors': line_errors,
                'strange_loop': strange_loop_lines,
                'insight_line': insight_line
            },
            output_data={
                'new_weights': new_weights.tolist(),
                'adjustments': adjustments
            },
            confidence=0.8,
            reasoning=f"注意力调节: 执行了 {len(adjustments)} 项调整"
        )
        
        return new_weights
    
    def calibrate_confidence(self, predictions: List[Tuple[np.ndarray, float]], 
                             outcomes: List[np.ndarray]) -> Dict[str, Any]:
        """
        校准置信度
        
        比较预测置信度与实际结果，检测过度自信或自信不足。
        
        Args:
            predictions: [(prediction, confidence), ...]
            outcomes: [actual, ...]
            
        Returns:
            校准报告
        """
        if len(predictions) != len(outcomes) or len(predictions) == 0:
            return {'status': 'insufficient_data'}
        
        # 按置信度分桶
        bins = defaultdict(list)
        
        for (pred, conf), actual in zip(predictions, outcomes):
            pred_arr = np.asarray(pred).flatten()
            actual_arr = np.asarray(actual).flatten()
            
            min_len = min(len(pred_arr), len(actual_arr))
            if min_len == 0:
                continue
                
            accuracy = 1.0 - float(np.mean(np.abs(pred_arr[:min_len] - actual_arr[:min_len])))
            
            # 将置信度分配到10个桶
            bin_idx = min(int(conf * 10), 9)
            bins[bin_idx].append((conf, accuracy))
        
        # 计算校准曲线
        calibration_curve = []
        
        for bin_idx in range(10):
            bin_data = bins[bin_idx]
            if bin_data:
                avg_confidence = np.mean([d[0] for d in bin_data])
                avg_accuracy = np.mean([d[1] for d in bin_data])
                calibration_curve.append({
                    'bin': bin_idx,
                    'confidence_range': f"{bin_idx * 0.1:.1f}-{(bin_idx + 1) * 0.1:.1f}",
                    'avg_confidence': float(avg_confidence),
                    'avg_accuracy': float(avg_accuracy),
                    'sample_count': len(bin_data),
                    'calibration_gap': float(avg_confidence - avg_accuracy)
                })
        
        # 检测过度自信/自信不足
        if calibration_curve:
            gaps = [c['calibration_gap'] for c in calibration_curve if c['sample_count'] >= 5]
            if gaps:
                avg_gap = np.mean(gaps)
                
                if avg_gap > 0.15:
                    calibration_status = 'overconfident'
                    status_desc = "系统过度自信"
                elif avg_gap < -0.15:
                    calibration_status = 'underconfident'
                    status_desc = "系统自信不足"
                else:
                    calibration_status = 'well_calibrated'
                    status_desc = "置信度校准良好"
            else:
                avg_gap = 0
                calibration_status = 'insufficient_data'
                status_desc = "数据不足"
        else:
            avg_gap = 0
            calibration_status = 'insufficient_data'
            status_desc = "数据不足"
        
        # 记录校准历史
        self.confidence_history.append({
            'calibration_curve': calibration_curve,
            'status': calibration_status,
            'avg_gap': avg_gap,
            'timestamp': time.time()
        })
        
        result = {
            'calibration_curve': calibration_curve,
            'status': calibration_status,
            'description': status_desc,
            'average_gap': float(avg_gap),
            'total_samples': len(predictions),
            'timestamp': time.time()
        }
        
        # 记录到思维链
        self.thought_chain.add_step(
            module="MetacognitiveMonitor",
            action="calibrate_confidence",
            input_data={'num_predictions': len(predictions)},
            output_data=result,
            confidence=0.9 if calibration_status == 'well_calibrated' else 0.6,
            reasoning=f"置信度校准: {status_desc}, 平均差距={avg_gap:.3f}"
        )
        
        return result
    
    def record_thought_chain(self, decision_steps: List[Dict[str, Any]]) -> List[ThoughtStep]:
        """
        记录思维链
        
        Args:
            decision_steps: 决策步骤列表
            
        Returns:
            记录的步骤列表
        """
        recorded = []
        for step in decision_steps:
            thought_step = self.thought_chain.add_step(
                module=step.get('module', 'unknown'),
                action=step.get('action', 'unknown'),
                input_data=step.get('input'),
                output_data=step.get('output'),
                confidence=step.get('confidence', 0.5),
                reasoning=step.get('reasoning', ''),
                metadata=step.get('metadata', {})
            )
            recorded.append(thought_step)
        
        return recorded
    
    def meta_reflection(self) -> Dict[str, Any]:
        """
        元反思 - 对系统整体思维模式进行反思
        
        生成"元认知报告"，包含：
        1. 全局预测误差趋势
        2. 各模块认知偏差检测
        3. 注意力分配建议
        4. 置信度校准状态
        5. 思维链摘要
        6. 系统"自我评价"
        
        Returns:
            元认知报告
        """
        self.stats['reflections_performed'] += 1
        
        report = {
            'timestamp': time.time(),
            'reflection_id': self.stats['reflections_performed'],
            'sections': {}
        }
        
        # 1. 全局预测误差趋势
        global_error = self.error_tracker.get_global_error()
        report['sections']['global_error_trend'] = global_error
        
        # 2. 各模块认知偏差检测
        bias_report = self.bias_detector.get_bias_report()
        report['sections']['cognitive_bias_detection'] = bias_report
        
        # 3. 注意力分配建议
        attention_advice = self._generate_attention_advice()
        report['sections']['attention_allocation'] = {
            'current_weights': self.attention_weights.tolist(),
            'line_names': self.line_names,
            'advice': attention_advice,
            'strange_loop_active': self.strange_loop_detected,
            'insight_active': self.insight_state['active']
        }
        
        # 4. 置信度校准状态
        if self.confidence_history:
            last_calibration = list(self.confidence_history)[-1]
            report['sections']['confidence_calibration'] = last_calibration
        else:
            report['sections']['confidence_calibration'] = {'status': 'no_calibration_yet'}
        
        # 5. 思维链摘要
        thought_summary = self.thought_chain.get_summary()
        report['sections']['thought_chain_summary'] = thought_summary
        
        # 6. 系统"自我评价"
        self_evaluation = self._generate_self_evaluation()
        report['sections']['self_evaluation'] = self_evaluation
        
        # 7. 监控覆盖率
        coverage = self.get_coverage()
        report['sections']['monitor_coverage'] = coverage
        
        # 保存报告
        self.meta_reports.append(report)
        
        # 记录到思维链
        self.thought_chain.add_step(
            module="MetacognitiveMonitor",
            action="meta_reflection",
            input_data={'modules_tracked': len(self.error_tracker.get_all_modules())},
            output_data={'report_id': report['reflection_id']},
            confidence=0.85,
            reasoning=f"执行第 {report['reflection_id']} 次元反思，监控了 {len(self.error_tracker.get_all_modules())} 个模块"
        )
        
        return report
    
    def _generate_attention_advice(self) -> List[str]:
        """生成注意力分配建议"""
        advice = []
        
        # 检查各模块的异常状态
        for i, line_name in enumerate(self.line_names):
            anomaly = self.error_tracker.get_anomaly_score(line_name)
            if anomaly > 0.5:
                advice.append(f"建议增加对 {line_name} 的监控（异常分数: {anomaly:.2f}）")
        
        # 检查是否有未充分监控的模块
        for line_name in self.line_names:
            status = self.module_monitor_status[line_name]
            if not status['covered']:
                advice.append(f"{line_name} 尚未被充分监控，建议增加采样")
        
        # 检查注意力分布是否过于集中
        max_weight = np.max(self.attention_weights)
        if max_weight > 0.3:
            dominant = self.line_names[np.argmax(self.attention_weights)]
            advice.append(f"注意力过于集中在 {dominant}，建议分散注意力以避免盲区")
        
        if not advice:
            advice.append("当前注意力分配合理，继续保持")
        
        return advice
    
    def _generate_self_evaluation(self) -> Dict[str, Any]:
        """生成系统自我评价"""
        total_calls = self.stats['total_monitor_calls']
        biases = self.stats['biases_detected']
        reflections = self.stats['reflections_performed']
        
        # 计算"健康度"
        coverage = self.get_coverage()
        coverage_score = coverage['overall_coverage_ratio']
        
        # 基于误差趋势评估
        global_error = self.error_tracker.get_global_error()
        if global_error.get('status') != 'no_data':
            error_score = max(0, 1.0 - global_error['mean'])
            error_trend = global_error.get('trend', 0)
        else:
            error_score = 0.5
            error_trend = 0
        
        # 健康度综合评分
        health_score = (coverage_score * 0.3 + error_score * 0.4 + 
                       (1.0 if not self.strange_loop_detected else 0.7) * 0.3)
        
        # 生成"自我意识"文本
        if health_score > 0.8:
            self_awareness = "系统运行良好，元认知监控有效"
        elif health_score > 0.6:
            self_awareness = "系统运行正常，但存在改进空间"
        elif health_score > 0.4:
            self_awareness = "系统需要注意：监控覆盖或预测精度有待提高"
        else:
            self_awareness = "系统警告：元认知监控检测到显著问题，建议人工审查"
        
        return {
            'health_score': float(health_score),
            'coverage_score': float(coverage_score),
            'error_score': float(error_score),
            'self_awareness_level': self_awareness,
            'monitor_calls': total_calls,
            'biases_detected': biases,
            'reflections': reflections,
            'attention_distribution_entropy': float(
                -np.sum(self.attention_weights * np.log(self.attention_weights + 1e-10))
            ),
            'strange_loop_active': self.strange_loop_detected,
            'insight_active': self.insight_state['active']
        }
    
    def get_coverage(self) -> Dict[str, Any]:
        """
        获取监控覆盖率
        
        Returns:
            覆盖率报告
        """
        all_modules = self.line_names
        covered = []
        uncovered = []
        
        for module in all_modules:
            status = self.module_monitor_status[module]
            if status['covered']:
                covered.append({
                    'name': module,
                    'monitor_count': status['monitor_count'],
                    'last_monitored': status['last_monitored']
                })
            else:
                uncovered.append(module)
        
        coverage_ratio = len(covered) / len(all_modules) if all_modules else 0
        
        return {
            'total_modules': len(all_modules),
            'covered_modules': len(covered),
            'uncovered_modules': uncovered,
            'overall_coverage_ratio': float(coverage_ratio),
            'module_details': covered,
            'status': 'complete' if coverage_ratio >= 0.9 else 'partial' if coverage_ratio >= 0.5 else 'insufficient'
        }
    
    def get_meta_report(self, report_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """获取指定的元认知报告"""
        if report_id is None:
            return list(self.meta_reports)[-1] if self.meta_reports else None
        
        for report in self.meta_reports:
            if report['reflection_id'] == report_id:
                return report
        return None
    
    def format_meta_report(self, report: Optional[Dict[str, Any]] = None) -> str:
        """格式化元认知报告为可读文本"""
        if report is None:
            report = self.get_meta_report()
        
        if report is None:
            return "暂无元认知报告"
        
        lines = []
        lines.append("=" * 70)
        lines.append("OMNI-HUB v5.0 元认知报告")
        lines.append("=" * 70)
        lines.append(f"报告ID: {report['reflection_id']} | 时间: {datetime.fromtimestamp(report['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 全局误差
        error_section = report['sections']['global_error_trend']
        lines.append("【全局预测误差趋势】")
        if error_section.get('status') != 'no_data':
            lines.append(f"  平均误差: {error_section['mean']:.4f}")
            lines.append(f"  误差标准差: {error_section['std']:.4f}")
            lines.append(f"  趋势: {error_section['trend']:.6f}")
            lines.append(f"  追踪模块数: {error_section['modules_tracked']}")
        else:
            lines.append("  暂无数据")
        lines.append("")
        
        # 偏差检测
        bias_section = report['sections']['cognitive_bias_detection']
        lines.append("【认知偏差检测】")
        lines.append(f"  检测到的偏差总数: {bias_section.get('total_biases_detected', 0)}")
        if bias_section.get('by_type'):
            lines.append("  按类型分布:")
            for bias_type, count in bias_section['by_type'].items():
                lines.append(f"    - {bias_type}: {count}")
        lines.append("")
        
        # 注意力分配
        att_section = report['sections']['attention_allocation']
        lines.append("【注意力分配】")
        lines.append("  当前权重分布:")
        for i, (name, weight) in enumerate(zip(att_section['line_names'], att_section['current_weights'])):
            bar = "█" * int(weight * 30)
            lines.append(f"    {name:30s} {weight:.3f} {bar}")
        lines.append("  建议:")
        for advice in att_section['advice'][:3]:
            lines.append(f"    • {advice}")
        lines.append("")
        
        # 置信度校准
        conf_section = report['sections']['confidence_calibration']
        lines.append("【置信度校准】")
        if conf_section.get('status') != 'no_calibration_yet':
            lines.append(f"  状态: {conf_section.get('description', 'N/A')}")
            lines.append(f"  平均差距: {conf_section.get('average_gap', 0):.3f}")
        else:
            lines.append("  尚未进行校准")
        lines.append("")
        
        # 思维链摘要
        thought_section = report['sections']['thought_chain_summary']
        lines.append("【思维链摘要】")
        if thought_section.get('status') != 'empty':
            lines.append(f"  总步骤: {thought_section['total_steps']}")
            lines.append(f"  涉及模块: {thought_section['modules_involved']}")
            lines.append(f"  平均置信度: {thought_section['average_confidence']:.3f}")
            lines.append(f"  推理步骤: {thought_section['reasoning_steps']}")
        else:
            lines.append("  思维链为空")
        lines.append("")
        
        # 自我评价
        eval_section = report['sections']['self_evaluation']
        lines.append("【系统自我评价】")
        lines.append(f"  健康度评分: {eval_section['health_score']:.2f}/1.00")
        lines.append(f"  覆盖率评分: {eval_section['coverage_score']:.2f}")
        lines.append(f"  误差评分: {eval_section['error_score']:.2f}")
        lines.append(f"  自我意识: {eval_section['self_awareness_level']}")
        lines.append(f"  监控调用: {eval_section['monitor_calls']}")
        lines.append(f"  偏差检测: {eval_section['biases_detected']}")
        lines.append(f"  元反思次数: {eval_section['reflections']}")
        lines.append(f"  注意力熵: {eval_section['attention_distribution_entropy']:.3f}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


# ============================================================================
# 5. 实验验证
# ============================================================================

def run_experiment(num_steps: int = 100, seed: int = 42) -> Dict[str, Any]:
    """
    运行元认知监控器实验
    
    实验设计：
    1. 模拟100步系统运行
    2. 注入已知偏差（确认偏误、锚定效应等）
    3. 验证监控器是否能检测到偏差
    4. 验证注意力调节是否有效
    5. 统计：监控覆盖率、偏差检测率、误报率
    
    Args:
        num_steps: 模拟步数
        seed: 随机种子
        
    Returns:
        实验结果
    """
    np.random.seed(seed)
    
    logger.info("=" * 70)
    logger.info("OMNI-HUB v5.0 MetacognitiveMonitor 实验验证")
    logger.info("=" * 70)
    logger.info(f"\n实验参数: 步数={num_steps}, 随机种子={seed}")
    logger.info(str())
    
    # 初始化监控器
    monitor = MetacognitiveMonitor(num_lines=11)
    
    # 跟踪实验状态
    injected_bias_windows = []  # 注入的偏差窗口: [(module, bias_type, start_step, end_step), ...]
    detected_bias_events = []   # 检测到的偏差事件: [(step, module, bias_type), ...]
    
    # 为每个模块创建决策历史
    module_decision_histories = defaultdict(list)
    
    # 用于置信度校准的数据
    calibration_predictions = []
    calibration_outcomes = []
    
    # 用于注意力调节的各线误差
    line_errors = {}
    
    # 标记当前哪些模块正在被注入偏差
    active_injections = {}  # {module: (bias_type, start_step)}
    
    logger.info("开始模拟运行...")
    logger.info("-" * 70)
    
    for step in range(num_steps):
        # 1. 模拟各模块的预测与实际值
        for line_idx, line_name in enumerate(monitor.line_names):
            # 基础预测：带噪声的正弦信号
            t = step / 20.0
            base_signal = np.sin(t) + 0.5 * np.cos(2 * t)
            
            # 预测值（带噪声）
            prediction = base_signal + np.random.normal(0, 0.1)
            
            # 实际值（带不同噪声）
            actual = base_signal + np.random.normal(0, 0.15)
            
            # 注入偏差（在特定步骤）
            bias_injected_now = False
            bias_type = None
            
            # 步骤20-40: 在IntentionGenerator注入确认偏误
            if line_name == "IntentionGenerator" and 20 <= step < 40:
                # 确认偏误：系统性地只接受正面信息
                # 实际值总是高于预测值（预测持续低估）
                actual = prediction + 0.4 + abs(np.random.normal(0, 0.05))
                bias_injected_now = True
                bias_type = BiasType.CONFIRMATION
            
            # 步骤50-70: 在GoalAutopoiesis注入锚定效应
            elif line_name == "GoalAutopoiesis" and 50 <= step < 70:
                # 锚定效应：预测值围绕固定锚点，不随实际信号变化
                anchor = 0.5  # 锚点
                prediction = anchor + np.random.normal(0, 0.02)
                actual = base_signal + np.random.normal(0, 0.1)
                bias_injected_now = True
                bias_type = BiasType.ANCHORING
            
            # 步骤80-95: 在CreativityEngine注入近因效应
            elif line_name == "CreativityEngine" and 80 <= step < 95:
                # 近因效应：预测值几乎等于上一期实际值
                if step > 0 and module_decision_histories[line_name]:
                    last_actual = module_decision_histories[line_name][-1].get('actual', base_signal)
                    prediction = float(last_actual) + np.random.normal(0, 0.01)
                actual = base_signal + np.random.normal(0, 0.2)
                bias_injected_now = True
                bias_type = BiasType.RECENCY
            
            # 步骤30-50: 在MemoryConsolidator注入可得性启发
            elif line_name == "MemoryConsolidator" and 30 <= step < 50:
                # 可得性启发：预测过度反应于近期的大噪声
                if step > 3:
                    # 取最近3个实际值计算过度反应
                    recent = [module_decision_histories[line_name][-i]['actual'] 
                             for i in range(1, min(4, len(module_decision_histories[line_name])+1))]
                    recent_mean = np.mean(recent)
                    prediction = recent_mean + np.random.normal(0, 0.1)
                actual = base_signal + np.random.normal(0, 0.15)
                bias_injected_now = True
                bias_type = BiasType.AVAILABILITY
            
            # 记录偏差注入窗口
            if bias_injected_now:
                if line_name not in active_injections:
                    active_injections[line_name] = (bias_type, step)
            else:
                if line_name in active_injections:
                    # 偏差注入结束，记录窗口
                    btype, start = active_injections[line_name]
                    injected_bias_windows.append((line_name, btype, start, step - 1))
                    del active_injections[line_name]
            
            # 记录预测误差
            pred_arr = np.array([prediction])
            actual_arr = np.array([actual])
            
            monitor.monitor_prediction_error(line_name, pred_arr, actual_arr, 
                                              confidence=0.5 + np.random.random() * 0.5)
            
            # 记录决策历史（用于偏差检测）
            error = float(np.mean((pred_arr - actual_arr) ** 2))
            record = {
                'prediction': prediction,
                'actual': actual,
                'error': error,
                'confidence': 0.5 + np.random.random() * 0.5,
                'step': step
            }
            module_decision_histories[line_name].append(record)
            
            # 记录置信度校准数据
            calibration_predictions.append((pred_arr, record['confidence']))
            calibration_outcomes.append(actual_arr)
            
            # 更新线误差
            line_errors[line_idx] = error
        
        # 处理剩余的活跃注入
        for line_name in list(active_injections.keys()):
            btype, start = active_injections[line_name]
            if step == num_steps - 1:
                injected_bias_windows.append((line_name, btype, start, step))
        
        # 2. 定期检测认知偏差（每10步）
        if step % 10 == 0 and step > 0:
            for line_name, history in module_decision_histories.items():
                if len(history) >= 15:
                    biases = monitor.detect_cognitive_bias(line_name, history[-35:])
                    if biases:
                        for bias in biases:
                            detected_bias_events.append((
                                step, line_name, bias.bias_type,
                                bias.severity, bias.confidence, bias.description
                            ))
        
        # 3. 定期调节注意力（每15步）
        if step % 15 == 0 and step > 0:
            # 随机触发奇异环（步骤45）
            strange_loop = [2, 5, 8] if step == 45 else None
            
            # 随机触发顿悟（步骤75）
            insight = 3 if step == 75 else None
            
            monitor.adjust_attention(
                line_errors=line_errors.copy(),
                strange_loop_lines=strange_loop,
                insight_line=insight
            )
        
        # 4. 定期置信度校准（每25步）
        if step % 25 == 0 and step > 0 and len(calibration_predictions) > 20:
            monitor.calibrate_confidence(calibration_predictions[-100:], 
                                          calibration_outcomes[-100:])
        
        # 5. 定期元反思（每20步）
        if step % 20 == 0 and step > 0:
            monitor.meta_reflection()
        
        # 进度输出
        if step % 20 == 0:
            logger.info(f"  Step {step:3d}/{num_steps} | 注入窗口: {len(injected_bias_windows)} | 检测到: {len(detected_bias_events)}")
    
    logger.info("-" * 70)
    logger.info("模拟完成，生成最终报告...")
    logger.info(str())
    
    # 最终元反思
    final_report = monitor.meta_reflection()
    
    # 打印元认知报告
    logger.info(str(monitor.format_meta_report(final_report)))
    
    # 计算实验统计
    # 1. 监控覆盖率
    coverage = monitor.get_coverage()
    coverage_rate = coverage['overall_coverage_ratio']
    
    # 2. 偏差检测率 - 基于偏差窗口的检测
    # 对于每个注入窗口，检查是否在对应模块检测到了对应类型的偏差
    # 改进：每个窗口可以有多个检测事件，我们计算窗口级别的匹配
    matched_windows = set()
    matched_detections = set()
    
    for win_idx, (inj_module, inj_type, inj_start, inj_end) in enumerate(injected_bias_windows):
        # 查找是否在注入期间或之后检测到了对应偏差
        for det_idx, (det_step, det_module, det_type, _, _, _) in enumerate(detected_bias_events):
            if det_module == inj_module and det_type == inj_type:
                # 检测时间应在注入窗口内或稍后(允许10步延迟)
                if inj_start <= det_step <= inj_end + 10:
                    matched_windows.add(win_idx)
                    matched_detections.add(det_idx)
    
    true_positives = len(matched_windows)
    false_negatives = len(injected_bias_windows) - true_positives
    false_positives = len(detected_bias_events) - len(matched_detections)
    
    recall = true_positives / len(injected_bias_windows) if injected_bias_windows else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # 统计按类型
    injected_by_type = defaultdict(int)
    for _, btype, _, _ in injected_bias_windows:
        injected_by_type[btype.value] += 1
    
    detected_by_type = defaultdict(int)
    for _, _, det_type, _, _, _ in detected_bias_events:
        detected_by_type[det_type.value] += 1
    
    # 打印思维链回放片段
    logger.info("\n" + "=" * 70)
    logger.info("思维链回放片段（最近10步）")
    logger.info("=" * 70)
    steps = monitor.thought_chain.get_chain()
    recent_steps = steps[-10:] if len(steps) >= 10 else steps
    for s in recent_steps:
        logger.info(f"  [{s.step_id:3d}] {s.module:25s} | {s.action:25s} | conf={s.confidence:.2f}")
        if s.reasoning:
            logger.info(f"         └─> {s.reasoning[:80]}")
    
    # 打印偏差检测详情
    logger.info("\n" + "=" * 70)
    logger.info("偏差检测详情")
    logger.info("=" * 70)
    
    logger.info("\n注入的偏差窗口:")
    for module, btype, start, end in injected_bias_windows:
        logger.info(f"  {module:25s} | {btype.value:20s} | Steps {start:3d}-{end:3d}")
    
    logger.info("\n检测到的偏差事件:")
    for step, module, btype, severity, conf, desc in detected_bias_events[:15]:
        logger.info(f"  Step {step:3d} | {module:25s} | {btype.value:20s} | sev={severity:.2f}")
    if len(detected_bias_events) > 15:
        logger.info(f"  ... 还有 {len(detected_bias_events) - 15} 个")
    
    # 汇总统计
    logger.info("\n" + "=" * 70)
    logger.info("实验统计汇总")
    logger.info("=" * 70)
    
    results = {
        'experiment_config': {
            'num_steps': num_steps,
            'seed': seed,
            'num_lines': monitor.num_lines
        },
        'coverage': {
            'overall_rate': float(coverage_rate),
            'covered_modules': coverage['covered_modules'],
            'total_modules': coverage['total_modules'],
            'status': coverage['status']
        },
        'bias_detection': {
            'injected_windows': len(injected_bias_windows),
            'detected_events': len(detected_bias_events),
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'injected_by_type': dict(injected_by_type),
            'detected_by_type': dict(detected_by_type),
            'detection_rate_recall': float(recall),
            'precision': float(precision),
            'f1_score': float(f1_score)
        },
        'attention': {
            'final_weights': monitor.attention_weights.tolist(),
            'weight_entropy': float(-np.sum(monitor.attention_weights * 
                                           np.log(monitor.attention_weights + 1e-10))),
            'adjustments_count': monitor.stats['attention_adjustments']
        },
        'monitor_stats': {
            'total_monitor_calls': monitor.stats['total_monitor_calls'],
            'biases_detected_total': monitor.stats['biases_detected'],
            'reflections_performed': monitor.stats['reflections_performed'],
            'thought_steps': len(monitor.thought_chain.get_chain())
        },
        'self_evaluation': final_report['sections']['self_evaluation'],
        'global_error': monitor.error_tracker.get_global_error(),
        'error_trends': {
            name: monitor.error_tracker.get_error_trend(name)
            for name in monitor.line_names
        }
    }
    
    logger.info(f"\n监控覆盖率: {coverage_rate*100:.1f}% ({coverage['covered_modules']}/{coverage['total_modules']})")
    logger.info(f"偏差注入窗口: {len(injected_bias_windows)}")
    logger.info(f"偏差检测事件: {len(detected_bias_events)}")
    logger.info(f"真阳性(TP): {true_positives}")
    logger.info(f"假阳性(FP): {false_positives}")
    logger.info(f"假阴性(FN): {false_negatives}")
    logger.info(f"召回率(Recall): {recall*100:.1f}%")
    logger.info(f"精确率(Precision): {precision*100:.1f}%")
    logger.info(f"F1分数: {f1_score:.3f}")
    logger.info(f"监控调用: {monitor.stats['total_monitor_calls']}")
    logger.info(f"元反思: {monitor.stats['reflections_performed']}")
    logger.info(f"思维步骤: {len(monitor.thought_chain.get_chain())}")
    logger.info(f"系统健康度: {results['self_evaluation']['health_score']:.2f}")
    
    logger.info("\n" + "=" * 70)
    logger.info("实验验证完成")
    logger.info("=" * 70)
    
    return results


def run_extended_experiments():
    """运行扩展实验，测试不同参数配置"""
    logger.info("\n" + "=" * 70)
    logger.info("扩展实验: 多配置验证")
    logger.info("=" * 70)
    
    configs = [
        {'num_steps': 100, 'seed': 42, 'name': '标准配置'},
        {'num_steps': 200, 'seed': 123, 'name': '长序列'},
        {'num_steps': 50, 'seed': 999, 'name': '短序列'},
    ]
    
    all_results = []
    for config in configs:
        logger.info(f"\n运行: {config['name']} (steps={config['num_steps']}, seed={config['seed']})")
        results = run_experiment(**{k: v for k, v in config.items() if k != 'name'})
        all_results.append({
            'config_name': config['name'],
            'results': results
        })
    
    # 汇总比较
    logger.info("\n" + "=" * 70)
    logger.info("多配置比较汇总")
    logger.info("=" * 70)
    logger.info(f"{'配置':<15s} {'覆盖率':>8s} {'召回率':>8s} {'精确率':>8s} {'F1':>8s} {'健康度':>8s}")
    logger.info("-" * 65)
    for r in all_results:
        name = r['config_name']
        cov = r['results']['coverage']['overall_rate'] * 100
        rec = r['results']['bias_detection']['detection_rate_recall'] * 100
        prec = r['results']['bias_detection']['precision'] * 100
        f1 = r['results']['bias_detection']['f1_score'] * 100
        health = r['results']['self_evaluation']['health_score'] * 100
        logger.info(f"{name:<15s} {cov:>7.1f}% {rec:>7.1f}% {prec:>7.1f}% {f1:>7.1f}% {health:>7.1f}%")
    
    return all_results


# ============================================================================
# 6. 主入口
# ============================================================================

if __name__ == "__main__":
    # 运行标准实验
    results = run_experiment(num_steps=100, seed=42)
    
    # 运行扩展实验
    extended_results = run_extended_experiments()
    
    # 保存实验结果
    output_dir = "/mnt/agents/output/OMNI-HUB/core"
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存JSON结果
    try:
        with open(f"{output_dir}/experiment_results.json", "w", encoding="utf-8") as f:
            # 将numpy类型转换为普通类型
            def convert(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, (np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, BiasType):
                    return obj.value
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            json.dump({
                'standard': results,
                'extended': extended_results
            }, f, indent=2, default=convert, ensure_ascii=False)
        
        print(f"\n实验结果已保存到: {output_dir}/experiment_results.json")
    except Exception as e:
        print(f"\n保存结果时出错: {e}")
    
    print("\n" + "=" * 70)
    print("OMNI-HUB v5.0 MetacognitiveMonitor 全部实验完成")
    print("=" * 70)
