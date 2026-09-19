#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12: QF-OS 核心机制重构 (Core Mechanism Reconstruction)
==================================================================
基于正逆向米田引理对OMNI-HUB四大核心机制进行重构:

1. 统一调度器 (Unified Scheduler)
   - 基于范畴拓扑的任务调度
   - 正向驱动: 因果依赖解析
   - 逆向驱动: 目标导向规划
   - 动态负载均衡

2. 知识管理系统 (Knowledge Management System)
   - 范畴化知识表示
   - 米田嵌入用于知识关联
   - 双向推理: 正向演绎 + 逆向溯因
   - 自组织知识图谱

3. 涌现计算引擎 (Emergence Compute Engine)
   - 循环检测驱动的模式发现
   - 高阶交互分析
   - 预测性涌现模拟
   - 自适应阈值调整

4. 自智循环 (Self-Awareness Loop)
   - 完整的OODA循环: 观察→定向→决策→行动
   - 自模型维护
   - 意图识别与目标管理
   - 元认知监控

重构原则:
---------
- 所有机制共享统一的范畴论语义
- 正反向驱动贯穿所有子系统
- 模块间通过标准IPC通信
- 支持动态重构和自适应

版本: v12.0.0 (Core Reconstruction)
"""

from __future__ import annotations

import asyncio
import heapq
import json
import logging
import math
import random
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    TypeVar,
    Union,
)

logger = logging.getLogger("qfos_rebuild")


# ============================================================================
# 共享类型与工具
# ============================================================================

class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class TaskState(Enum):
    """任务状态"""
    PENDING = auto()
    SCHEDULED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    RETRYING = auto()


@dataclass(slots=True)
class TimestampedValue:
    """带时间戳的值"""
    value: Any
    timestamp: float = field(default_factory=time.time)
    ttl: float = 3600.0  # 默认1小时过期

    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl


# ============================================================================
# 1. 统一调度器重构 (Unified Scheduler)
# ============================================================================

@dataclass
class Task:
    """
    任务定义
    
    任务在范畴论语义下是一个有向图中的节点，
    任务间的依赖关系形成态射。
    
    正向驱动: 任务完成后触发下游任务
    逆向驱动: 任务开始前需确保上游任务完成
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "unnamed"
    priority: TaskPriority = TaskPriority.NORMAL
    state: TaskState = TaskState.PENDING

    # 依赖关系（范畴论语义）
    dependencies: List[str] = field(default_factory=list)  # 入射态射
    dependents: List[str] = field(default_factory=list)    # 出射态射

    # 执行配置
    handler: Optional[Callable] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    max_retries: int = 3
    retry_count: int = 0

    # 资源需求
    cpu_request: float = 0.1
    memory_request: float = 64 * 1024 * 1024  # 64MB

    # 调度信息
    scheduled_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    assigned_worker: Optional[str] = None

    # 结果
    result: Any = None
    error: Optional[str] = None

    def is_ready(self) -> bool:
        """检查任务是否就绪（所有依赖已完成）"""
        return self.state == TaskState.PENDING and len(self.dependencies) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "priority": self.priority.name,
            "state": self.state.name,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "scheduled_at": self.scheduled_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "result": str(self.result) if self.result is not None else None,
            "error": self.error,
        }


@dataclass
class Worker:
    """
    工作节点
    
    执行任务的实体，具有资源容量。
    """
    worker_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    capacity: Dict[str, float] = field(default_factory=lambda: {
        "cpu": 4.0,
        "memory": 1024 * 1024 * 1024 * 8,  # 8GB
    })
    allocated: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    current_tasks: Set[str] = field(default_factory=set)
    health_score: float = 1.0
    last_heartbeat: float = field(default_factory=time.time)

    def available(self, resource_type: str) -> float:
        return self.capacity.get(resource_type, 0) - self.allocated.get(resource_type, 0)

    def can_accept(self, task: Task) -> bool:
        return (
            self.available("cpu") >= task.cpu_request
            and self.available("memory") >= task.memory_request
            and self.health_score > 0.5
        )

    def allocate(self, task: Task):
        self.allocated["cpu"] += task.cpu_request
        self.allocated["memory"] += task.memory_request
        self.current_tasks.add(task.task_id)

    def release(self, task: Task):
        self.allocated["cpu"] -= task.cpu_request
        self.allocated["memory"] -= task.memory_request
        self.current_tasks.discard(task.task_id)


class UnifiedScheduler:
    """
    统一调度器 (重构版)
    
    基于范畴拓扑的任务调度系统。
    
    核心算法:
    1. 拓扑排序: 利用逆向米田引理解析依赖链
    2. 动态规划: 正向传播计算最早开始时间
    3. 负载均衡: 基于工作节点米田签名分配任务
    4. 故障恢复: 逆向追溯重新调度失败任务及其依赖
    
    特性:
    - 支持DAG任务图（无环）
    - 支持动态任务提交
    - 支持优先级抢占
    - 支持资源约束
    - 支持故障恢复
    """

    def __init__(self, max_workers: int = 8):
        self._tasks: Dict[str, Task] = {}
        self._workers: Dict[str, Worker] = {}
        self._ready_queue: List[Tuple[int, float, str]] = []  # (priority, submit_time, task_id)
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._completed_tasks: deque = deque(maxlen=10000)
        self._task_graph: Dict[str, Set[str]] = defaultdict(set)  # task_id -> dependents
        self._reverse_graph: Dict[str, Set[str]] = defaultdict(set)  # task_id -> dependencies

        # 创建默认工作节点
        for i in range(max_workers):
            worker = Worker(worker_id=f"worker-{i}")
            self._workers[worker.worker_id] = worker

        self._running = False
        self._metrics = SchedulerMetrics()

    # ------------------------------------------------------------------
    # 任务管理
    # ------------------------------------------------------------------
    def submit_task(self, task: Task) -> str:
        """
        提交任务到调度器
        
        逆向分析: 解析任务的依赖链，构建入射态射
        正向分析: 注册任务的出射态射（依赖此任务的任务）
        """
        self._tasks[task.task_id] = task

        # 构建依赖图（逆向: 解析入射）
        for dep_id in task.dependencies:
            self._reverse_graph[task.task_id].add(dep_id)
            if dep_id in self._tasks:
                self._tasks[dep_id].dependents.append(task.task_id)
                self._task_graph[dep_id].add(task.task_id)

        # 检查是否就绪
        if task.is_ready():
            self._enqueue_ready(task)

        self._metrics.tasks_submitted += 1
        logger.debug(f"Scheduler: Task {task.task_id} submitted")
        return task.task_id

    def submit_dag(self, tasks: List[Task]) -> List[str]:
        """提交DAG任务图"""
        task_ids = []
        for task in tasks:
            tid = self.submit_task(task)
            task_ids.append(tid)
        return task_ids

    def _enqueue_ready(self, task: Task):
        """将就绪任务加入队列"""
        heapq.heappush(
            self._ready_queue,
            (task.priority.value, time.time(), task.task_id)
        )
        task.state = TaskState.SCHEDULED
        task.scheduled_at = time.time()

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self._tasks.get(task_id)
        if not task or task.state == TaskState.COMPLETED:
            return False

        task.state = TaskState.CANCELLED

        # 取消运行中的任务
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]

        # 级联取消下游任务
        for dependent_id in task.dependents:
            self.cancel_task(dependent_id)

        return True

    # ------------------------------------------------------------------
    # 调度算法
    # ------------------------------------------------------------------
    def _select_worker(self, task: Task) -> Optional[Worker]:
        """
        为任务选择最优工作节点
        
        基于米田引理: 选择其"资源签名"与任务需求最匹配的工作节点
        """
        candidates = []
        for worker in self._workers.values():
            if worker.can_accept(task):
                # 计算匹配度
                cpu_fit = worker.available("cpu") / (task.cpu_request + 0.001)
                mem_fit = worker.available("memory") / (task.memory_request + 1)
                health = worker.health_score
                score = (cpu_fit + mem_fit) * health
                candidates.append((score, worker))

        if not candidates:
            return None

        # 选择得分最高的
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    async def _execute_task(self, task: Task, worker: Worker):
        """执行任务"""
        task.state = TaskState.RUNNING
        task.started_at = time.time()
        task.assigned_worker = worker.worker_id
        worker.allocate(task)

        try:
            if task.handler:
                if asyncio.iscoroutinefunction(task.handler):
                    result = await asyncio.wait_for(
                        task.handler(task.payload),
                        timeout=task.timeout,
                    )
                else:
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, task.handler, task.payload),
                        timeout=task.timeout,
                    )
                task.result = result
                task.state = TaskState.COMPLETED
                self._metrics.tasks_completed += 1
            else:
                task.state = TaskState.COMPLETED
                task.result = None

        except asyncio.TimeoutError:
            task.error = "Timeout"
            task.state = TaskState.FAILED
            self._metrics.tasks_failed += 1
        except Exception as e:
            task.error = str(e)
            task.state = TaskState.FAILED
            self._metrics.tasks_failed += 1

        finally:
            task.completed_at = time.time()
            worker.release(task)
            self._completed_tasks.append(task.to_dict())

            # 触发下游任务
            if task.state == TaskState.COMPLETED:
                await self._trigger_downstream(task)
            elif task.state == TaskState.FAILED and task.retry_count < task.max_retries:
                task.retry_count += 1
                task.state = TaskState.RETRYING
                await asyncio.sleep(1.0 * task.retry_count)
                self._enqueue_ready(task)

    async def _trigger_downstream(self, task: Task):
        """
        触发下游任务（正向驱动）
        
        对应米田引理的正向传播:
        任务完成 → 沿出射态射传播完成事件 → 下游任务变为就绪
        """
        for dependent_id in task.dependents:
            dependent = self._tasks.get(dependent_id)
            if dependent and dependent.state == TaskState.PENDING:
                dependent.dependencies.remove(task.task_id)
                if dependent.is_ready():
                    self._enqueue_ready(dependent)

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------
    async def run(self):
        """运行调度器主循环"""
        self._running = True
        logger.info("UnifiedScheduler: Started")

        while self._running:
            if self._ready_queue:
                _, _, task_id = heapq.heappop(self._ready_queue)
                task = self._tasks.get(task_id)
                if not task or task.state != TaskState.SCHEDULED:
                    continue

                worker = self._select_worker(task)
                if worker:
                    exec_task = asyncio.create_task(self._execute_task(task, worker))
                    self._running_tasks[task_id] = exec_task
                else:
                    # 没有可用工作节点，重新入队
                    heapq.heappush(self._ready_queue, (task.priority.value, time.time(), task_id))
                    await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.1)

            # 清理已完成任务
            done = [tid for tid, t in self._running_tasks.items() if t.done()]
            for tid in done:
                del self._running_tasks[tid]

    def stop(self):
        self._running = False

    # ------------------------------------------------------------------
    # 查询与监控
    # ------------------------------------------------------------------
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self._metrics.to_dict(),
            "pending": len([t for t in self._tasks.values() if t.state == TaskState.PENDING]),
            "running": len(self._running_tasks),
            "completed": len(self._completed_tasks),
            "workers": len(self._workers),
        }

    def get_critical_path(self, target_task_id: str) -> List[str]:
        """
        计算到达目标的关键路径（逆向分析）
        
        利用逆向米田引理，从目标出发追溯所有依赖。
        """
        path = []
        visited: Set[str] = set()

        def dfs(tid: str):
            if tid in visited:
                return
            visited.add(tid)
            task = self._tasks.get(tid)
            if task:
                path.append(tid)
                for dep in task.dependencies:
                    dfs(dep)

        dfs(target_task_id)
        return list(reversed(path))


@dataclass
class SchedulerMetrics:
    """调度器指标"""
    tasks_submitted: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_retried: int = 0
    avg_latency: float = 0.0
    throughput: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# 2. 知识管理系统重构 (Knowledge Management System)
# ============================================================================

@dataclass
class KnowledgeAtom:
    """
    知识原子
    
    范畴化知识表示的基本单元。
    每个知识原子是一个"对象"，与其他原子的关系是"态射"。
    """
    atom_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: Any = None
    atom_type: str = "fact"  # fact, rule, concept, relation, inference
    confidence: float = 1.0
    source: str = "unknown"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 范畴结构
    outgoing_relations: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    incoming_relations: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "atom_type": self.atom_type,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at,
            "outgoing_relations": dict(self.outgoing_relations),
            "incoming_relations": dict(self.incoming_relations),
        }


class KnowledgeGraph:
    """
    范畴化知识图谱
    
    知识图谱在范畴论语义下:
    - 节点 = 知识原子（对象）
    - 边 = 关系（态射）
    - 路径 = 推理链（态射合成）
    
    支持:
    - 正向推理: 从已知事实推导新结论
    - 逆向推理: 从目标反推所需前提
    - 关联发现: 基于米田嵌入的相似性
    """

    def __init__(self):
        self._atoms: Dict[str, KnowledgeAtom] = {}
        self._relations: Dict[str, Dict[str, Any]] = {}
        self._indices: Dict[str, Set[str]] = defaultdict(set)
        self._inference_cache: Dict[str, Any] = {}
        self._version: int = 0

    # ------------------------------------------------------------------
    # CRUD 操作
    # ------------------------------------------------------------------
    def add_atom(self, atom: KnowledgeAtom) -> str:
        """添加知识原子"""
        self._atoms[atom.atom_id] = atom
        self._indices[atom.atom_type].add(atom.atom_id)
        self._version += 1
        return atom.atom_id

    def get_atom(self, atom_id: str) -> Optional[KnowledgeAtom]:
        return self._atoms.get(atom_id)

    def remove_atom(self, atom_id: str) -> bool:
        """移除知识原子及其关联"""
        atom = self._atoms.pop(atom_id, None)
        if not atom:
            return False

        # 清理关系
        for rel_type, targets in atom.outgoing_relations.items():
            for target in targets:
                target_atom = self._atoms.get(target)
                if target_atom and atom_id in target_atom.incoming_relations.get(rel_type, []):
                    target_atom.incoming_relations[rel_type].remove(atom_id)

        for rel_type, sources in atom.incoming_relations.items():
            for source in sources:
                source_atom = self._atoms.get(source)
                if source_atom and atom_id in source_atom.outgoing_relations.get(rel_type, []):
                    source_atom.outgoing_relations[rel_type].remove(atom_id)

        self._indices[atom.atom_type].discard(atom_id)
        self._version += 1
        return True

    def relate(self, source_id: str, target_id: str, relation_type: str, metadata: Dict[str, Any] = None):
        """
        建立关系（态射）
        
        source --[relation_type]--> target
        """
        source = self._atoms.get(source_id)
        target = self._atoms.get(target_id)
        if not source or not target:
            raise ValueError("Source or target atom not found")

        source.outgoing_relations[relation_type].append(target_id)
        target.incoming_relations[relation_type].append(source_id)

        rel_id = f"{source_id}:{relation_type}:{target_id}"
        self._relations[rel_id] = {
            "source": source_id,
            "target": target_id,
            "type": relation_type,
            "metadata": metadata or {},
            "created_at": time.time(),
        }
        self._version += 1

    # ------------------------------------------------------------------
    # 查询与推理
    # ------------------------------------------------------------------
    def query_by_type(self, atom_type: str) -> List[KnowledgeAtom]:
        """按类型查询"""
        return [self._atoms[aid] for aid in self._indices.get(atom_type, set())]

    def query_related(self, atom_id: str, relation_type: str = None, direction: str = "outgoing") -> List[KnowledgeAtom]:
        """
        查询相关知识（米田引理应用）
        
        正向: 查询出射关系 (Hom(A, -))
        逆向: 查询入射关系 (Hom(-, A))
        """
        atom = self._atoms.get(atom_id)
        if not atom:
            return []

        related_ids = []
        if direction in ("outgoing", "both"):
            if relation_type:
                related_ids.extend(atom.outgoing_relations.get(relation_type, []))
            else:
                for ids in atom.outgoing_relations.values():
                    related_ids.extend(ids)

        if direction in ("incoming", "both"):
            if relation_type:
                related_ids.extend(atom.incoming_relations.get(relation_type, []))
            else:
                for ids in atom.incoming_relations.values():
                    related_ids.extend(ids)

        return [self._atoms[aid] for aid in set(related_ids) if aid in self._atoms]

    def find_path(self, source_id: str, target_id: str, max_depth: int = 5) -> List[List[str]]:
        """
        寻找知识路径（推理链）
        
        对应态射的合成序列:
        source --f1--> ... --fn--> target
        """
        paths = []
        visited: Set[str] = set()

        def dfs(current: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            if current == target_id and path:
                paths.append(path[:])
                return

            atom = self._atoms.get(current)
            if not atom:
                return

            for rel_type, targets in atom.outgoing_relations.items():
                for tid in targets:
                    if tid not in visited:
                        visited.add(tid)
                        path.append(f"{rel_type}:{tid}")
                        dfs(tid, path, depth + 1)
                        path.pop()
                        visited.discard(tid)

        visited.add(source_id)
        dfs(source_id, [], 0)
        return paths

    def forward_inference(self, premises: List[str], rule_type: str = "deduction") -> List[KnowledgeAtom]:
        """
        正向推理: 从前提推导结论
        
        对应范畴论中的态射合成:
        premise1 --rule--> conclusion
        """
        conclusions = []

        for premise_id in premises:
            atom = self._atoms.get(premise_id)
            if not atom:
                continue

            # 查找所有从premise出发的推理关系
            for target_id in atom.outgoing_relations.get("implies", []):
                target = self._atoms.get(target_id)
                if target and target_id not in premises:
                    # 生成推理结论
                    inferred = KnowledgeAtom(
                        content=f"Inferred from {premise_id}: {target.content}",
                        atom_type="inference",
                        confidence=atom.confidence * target.confidence * 0.9,
                        source="forward_inference",
                        metadata={
                            "premise": premise_id,
                            "rule": rule_type,
                        },
                    )
                    self.add_atom(inferred)
                    self.relate(premise_id, inferred.atom_id, "inferred")
                    self.relate(inferred.atom_id, target_id, "supports")
                    conclusions.append(inferred)

        return conclusions

    def backward_inference(self, goal_id: str, max_depth: int = 5) -> List[List[str]]:
        """
        逆向推理: 从目标反推所需前提
        
        对应逆向米田引理:
        为了达成goal，需要满足哪些条件？
        """
        proofs = []
        visited: Set[str] = set()

        def prove(target_id: str, path: List[str], depth: int):
            if depth > max_depth:
                return

            target = self._atoms.get(target_id)
            if not target:
                return

            # 如果是基本事实，路径完成
            if target.atom_type == "fact" and not target.incoming_relations.get("implies", []):
                proofs.append(list(reversed(path + [target_id])))
                return

            # 查找支持target的前提
            premises = target.incoming_relations.get("implies", [])
            if not premises:
                proofs.append(list(reversed(path + [target_id])))
                return

            for premise_id in premises:
                if premise_id not in visited:
                    visited.add(premise_id)
                    prove(premise_id, path + [target_id], depth + 1)
                    visited.discard(premise_id)

        visited.add(goal_id)
        prove(goal_id, [], 0)
        return proofs

    def compute_yoneda_similarity(self, atom_id1: str, atom_id2: str) -> float:
        """
        基于米田引理的相似性计算
        
        两个知识原子相似当且仅当它们的米田表示相似。
        """
        a1 = self._atoms.get(atom_id1)
        a2 = self._atoms.get(atom_id2)
        if not a1 or not a2:
            return 0.0

        # 计算出射签名相似度
        out_types = set(a1.outgoing_relations.keys()) | set(a2.outgoing_relations.keys())
        out_sim = 0.0
        for rt in out_types:
            s1 = set(a1.outgoing_relations.get(rt, []))
            s2 = set(a2.outgoing_relations.get(rt, []))
            if s1 or s2:
                jaccard = len(s1 & s2) / len(s1 | s2) if (s1 | s2) else 1.0
                out_sim += jaccard
        out_sim = out_sim / len(out_types) if out_types else 0.0

        # 计算入射签名相似度
        in_types = set(a1.incoming_relations.keys()) | set(a2.incoming_relations.keys())
        in_sim = 0.0
        for rt in in_types:
            s1 = set(a1.incoming_relations.get(rt, []))
            s2 = set(a2.incoming_relations.get(rt, []))
            if s1 or s2:
                jaccard = len(s1 & s2) / len(s1 | s2) if (s1 | s2) else 1.0
                in_sim += jaccard
        in_sim = in_sim / len(in_types) if in_types else 0.0

        return (out_sim + in_sim) / 2

    def get_stats(self) -> Dict[str, Any]:
        return {
            "atoms": len(self._atoms),
            "relations": len(self._relations),
            "types": {t: len(ids) for t, ids in self._indices.items()},
            "version": self._version,
        }


class KnowledgeManagementSystem:
    """
    知识管理系统 (重构版)
    
    整合知识图谱、推理引擎和记忆管理。
    """

    def __init__(self):
        self.graph = KnowledgeGraph()
        self._working_memory: Dict[str, TimestampedValue] = {}
        self._long_term_memory: deque = deque(maxlen=100000)
        self._inference_history: deque = deque(maxlen=5000)
        self._lock = asyncio.Lock()

    async def ingest(self, content: Any, atom_type: str = "fact", metadata: Dict[str, Any] = None) -> str:
        """摄入知识"""
        atom = KnowledgeAtom(
            content=content,
            atom_type=atom_type,
            metadata=metadata or {},
        )
        async with self._lock:
            aid = self.graph.add_atom(atom)
            self._long_term_memory.append({
                "atom_id": aid,
                "content": str(content)[:200],
                "timestamp": time.time(),
            })
        return aid

    async def query(self, query_type: str, **params) -> List[Dict[str, Any]]:
        """查询知识"""
        if query_type == "by_type":
            atoms = self.graph.query_by_type(params.get("atom_type", "fact"))
            return [a.to_dict() for a in atoms]
        elif query_type == "related":
            atoms = self.graph.query_related(
                params.get("atom_id"),
                params.get("relation_type"),
                params.get("direction", "outgoing"),
            )
            return [a.to_dict() for a in atoms]
        elif query_type == "path":
            paths = self.graph.find_path(
                params.get("source"),
                params.get("target"),
                params.get("max_depth", 5),
            )
            return [{"path": p} for p in paths]
        elif query_type == "similar":
            # 查找最相似的知识原子
            target_id = params.get("atom_id")
            similarities = []
            for aid in self.graph._atoms:
                if aid != target_id:
                    sim = self.graph.compute_yoneda_similarity(target_id, aid)
                    if sim > params.get("threshold", 0.5):
                        similarities.append((aid, sim))
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [{"atom_id": aid, "similarity": sim} for aid, sim in similarities[:10]]
        return []

    async def infer(self, mode: str = "forward", **params) -> List[Dict[str, Any]]:
        """推理"""
        if mode == "forward":
            premises = params.get("premises", [])
            conclusions = self.graph.forward_inference(premises)
            result = [c.to_dict() for c in conclusions]
        elif mode == "backward":
            goal = params.get("goal")
            proofs = self.graph.backward_inference(goal)
            result = [{"proof": p} for p in proofs]
        else:
            result = []

        self._inference_history.append({
            "mode": mode,
            "params": params,
            "results": len(result),
            "timestamp": time.time(),
        })
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {
            "graph": self.graph.get_stats(),
            "working_memory": len(self._working_memory),
            "long_term_memory": len(self._long_term_memory),
            "inference_history": len(self._inference_history),
        }


# ============================================================================
# 3. 涌现计算引擎重构 (Emergence Compute Engine)
# ============================================================================

@dataclass
class EmergencePattern:
    """涌现模式"""
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    pattern_type: str = "unknown"
    components: List[str] = field(default_factory=list)
    strength: float = 0.0
    confidence: float = 0.0
    detected_at: float = field(default_factory=time.time)
    lifecycle: str = "emerging"  # emerging, stable, decaying
    predictions: List[Dict[str, Any]] = field(default_factory=list)


class EmergenceComputeEngine:
    """
    涌现计算引擎 (重构版)
    
    通过分析系统范畴结构中的高阶模式检测涌现行为。
    
    核心算法:
    1. 循环检测: 发现反馈回路（振荡、共振）
    2. 社区发现: 识别高耦合模块群
    3. 级联分析: 检测雪崩效应
    4. 熵变监控: 追踪系统无序度变化
    
    米田引理应用:
    - 正向: 从一个组件出发的传播路径预测其影响范围
    - 逆向: 从一个异常状态反推可能的起源
    """

    def __init__(self):
        self._patterns: Dict[str, EmergencePattern] = {}
        self._pattern_history: deque = deque(maxlen=5000)
        self._entropy_history: deque = deque(maxlen=1000)
        self._interaction_matrix: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._detection_threshold: float = 0.7
        self._running = False

    # ------------------------------------------------------------------
    # 模式检测
    # ------------------------------------------------------------------
    async def detect_patterns(self, system_graph: Dict[str, Any]) -> List[EmergencePattern]:
        """
        检测涌现模式
        
        system_graph: 系统的范畴表示
        """
        patterns = []

        # 1. 检测反馈循环
        cycles = self._detect_cycles(system_graph)
        for cycle in cycles:
            strength = self._compute_cycle_strength(cycle, system_graph)
            if strength > self._detection_threshold:
                pattern = EmergencePattern(
                    pattern_type="feedback_loop",
                    components=cycle,
                    strength=strength,
                    confidence=min(1.0, strength * 1.2),
                )
                patterns.append(pattern)

        # 2. 检测社区结构
        communities = self._detect_communities(system_graph)
        for comm in communities:
            if len(comm) >= 3:
                cohesion = self._compute_cohesion(comm, system_graph)
                pattern = EmergencePattern(
                    pattern_type="community",
                    components=comm,
                    strength=cohesion,
                    confidence=cohesion,
                )
                patterns.append(pattern)

        # 3. 检测级联传播
        cascades = self._detect_cascades(system_graph)
        for cascade in cascades:
            pattern = EmergencePattern(
                pattern_type="cascade",
                components=cascade,
                strength=len(cascade) / len(system_graph.get("nodes", [1])),
                confidence=0.8,
            )
            patterns.append(pattern)

        # 4. 检测相变
        phase_transitions = self._detect_phase_transitions(system_graph)
        for pt in phase_transitions:
            patterns.append(EmergencePattern(
                pattern_type="phase_transition",
                components=pt.get("components", []),
                strength=pt.get("magnitude", 0.5),
                confidence=pt.get("confidence", 0.5),
            ))

        # 存储检测到的模式
        for p in patterns:
            self._patterns[p.pattern_id] = p
            self._pattern_history.append(p)

        return patterns

    def _detect_cycles(self, graph: Dict[str, Any]) -> List[List[str]]:
        """检测图中的循环"""
        edges = graph.get("edges", [])
        adj: Dict[str, List[str]] = defaultdict(list)
        for edge in edges:
            adj[edge.get("source")].append(edge.get("target"))

        cycles = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    idx = path.index(neighbor)
                    cycle = path[idx:] + [neighbor]
                    if len(cycle) > 2:  # 忽略自环
                        cycles.append(cycle)
            path.pop()
            rec_stack.discard(node)

        for node in graph.get("nodes", []):
            nid = node.get("id") if isinstance(node, dict) else node
            if nid not in visited:
                dfs(nid)

        # 去重
        unique = []
        seen = set()
        for c in cycles:
            key = tuple(sorted(set(c)))
            if key not in seen:
                seen.add(key)
                unique.append(list(set(c)))
        return unique

    def _detect_communities(self, graph: Dict[str, Any]) -> List[List[str]]:
        """简单社区检测 (基于BFS连通分量)"""
        edges = graph.get("edges", [])
        adj: Dict[str, Set[str]] = defaultdict(set)
        for edge in edges:
            s = edge.get("source")
            t = edge.get("target")
            adj[s].add(t)
            adj[t].add(s)

        visited: Set[str] = set()
        communities = []

        for node in graph.get("nodes", []):
            nid = node.get("id") if isinstance(node, dict) else node
            if nid not in visited:
                community = []
                queue = deque([nid])
                while queue:
                    current = queue.popleft()
                    if current in visited:
                        continue
                    visited.add(current)
                    community.append(current)
                    for neighbor in adj.get(current, set()):
                        if neighbor not in visited:
                            queue.append(neighbor)
                if community:
                    communities.append(community)

        return communities

    def _detect_cascades(self, graph: Dict[str, Any]) -> List[List[str]]:
        """检测级联传播模式"""
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        adj: Dict[str, List[str]] = defaultdict(list)
        for edge in edges:
            adj[edge.get("source")].append(edge.get("target"))

        max_cascade = []

        def bfs_from(start: str) -> List[str]:
            visited = {start}
            queue = deque([start])
            order = [start]
            while queue:
                current = queue.popleft()
                for neighbor in adj.get(current, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
                        order.append(neighbor)
            return order

        for node in nodes:
            nid = node.get("id") if isinstance(node, dict) else node
            cascade = bfs_from(nid)
            if len(cascade) > len(max_cascade):
                max_cascade = cascade

        return [max_cascade] if max_cascade else []

    def _detect_phase_transitions(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测相变信号"""
        # 简化实现: 检测连通度突变
        transitions = []
        # 实际实现需要历史数据对比
        return transitions

    def _compute_cycle_strength(self, cycle: List[str], graph: Dict[str, Any]) -> float:
        """计算循环强度"""
        # 基于循环中边的权重计算
        edges = graph.get("edges", [])
        edge_weights = {}
        for edge in edges:
            key = (edge.get("source"), edge.get("target"))
            edge_weights[key] = edge.get("weight", 1.0)

        total_weight = 0
        count = 0
        for i in range(len(cycle)):
            s = cycle[i]
            t = cycle[(i + 1) % len(cycle)]
            w = edge_weights.get((s, t), 0)
            total_weight += w
            count += 1

        return total_weight / count if count > 0 else 0

    def _compute_cohesion(self, community: List[str], graph: Dict[str, Any]) -> float:
        """计算社区内聚度"""
        if len(community) <= 1:
            return 1.0

        edges = graph.get("edges", [])
        internal_edges = 0
        for edge in edges:
            s = edge.get("source")
            t = edge.get("target")
            if s in community and t in community:
                internal_edges += 1

        n = len(community)
        max_possible = n * (n - 1)
        return internal_edges / max_possible if max_possible > 0 else 0

    # ------------------------------------------------------------------
    # 预测与模拟
    # ------------------------------------------------------------------
    async def simulate_propagation(
        self,
        source: str,
        graph: Dict[str, Any],
        steps: int = 10,
    ) -> Dict[str, Any]:
        """
        模拟传播过程
        
        正向模拟: 从source出发，预测影响范围
        """
        edges = graph.get("edges", [])
        adj: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        for edge in edges:
            adj[edge.get("source")].append((edge.get("target"), edge.get("weight", 1.0)))

        # 传播模拟
        activation = {source: 1.0}
        history = [{source: 1.0}]

        for step in range(steps):
            new_activation = {}
            for node, val in activation.items():
                for target, weight in adj.get(node, []):
                    contrib = val * weight * 0.8  # 衰减因子
                    new_activation[target] = new_activation.get(target, 0) + contrib
            activation = {k: min(1.0, v) for k, v in new_activation.items() if v > 0.01}
            history.append(dict(activation))
            if not activation:
                break

        return {
            "source": source,
            "steps": len(history),
            "final_activation": activation,
            "history": history,
            "total_reach": len(set().union(*[set(h.keys()) for h in history])),
        }

    async def predict_emergence(
        self,
        graph: Dict[str, Any],
        lookahead: int = 5,
    ) -> List[EmergencePattern]:
        """
        预测性涌现检测
        
        基于当前状态和趋势预测未来可能涌现的模式。
        """
        predictions = []

        # 模拟系统演化
        current_patterns = await self.detect_patterns(graph)

        for pattern in current_patterns:
            if pattern.pattern_type == "feedback_loop":
                # 反馈回路可能产生振荡
                predictions.append(EmergencePattern(
                    pattern_type="predicted_oscillation",
                    components=pattern.components,
                    strength=pattern.strength * 1.2,
                    confidence=pattern.confidence * 0.8,
                    predictions=[{
                        "type": "oscillation",
                        "period_estimate": 1.0 / max(pattern.strength, 0.01),
                    }],
                ))
            elif pattern.pattern_type == "community":
                # 社区可能产生集体行为
                predictions.append(EmergencePattern(
                    pattern_type="predicted_collective",
                    components=pattern.components,
                    strength=pattern.strength,
                    confidence=pattern.confidence * 0.9,
                    predictions=[{
                        "type": "collective_behavior",
                        "size_estimate": len(pattern.components),
                    }],
                ))

        return predictions

    def get_stats(self) -> Dict[str, Any]:
        type_counts = defaultdict(int)
        for p in self._patterns.values():
            type_counts[p.pattern_type] += 1

        return {
            "active_patterns": len(self._patterns),
            "pattern_types": dict(type_counts),
            "history_size": len(self._pattern_history),
            "threshold": self._detection_threshold,
        }


# ============================================================================
# 4. 自智循环重构 (Self-Awareness Loop)
# ============================================================================

@dataclass
class SelfModel:
    """
    自模型
    
    系统对自身的范畴论语义表示。
    这是自智的基础: 系统必须能够"看到自己"。
    """
    model_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # 系统结构
    components: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    relationships: List[Dict[str, Any]] = field(default_factory=list)

    # 运行时状态
    health_map: Dict[str, float] = field(default_factory=dict)
    performance_map: Dict[str, float] = field(default_factory=dict)

    # 认知状态
    awareness_level: float = 0.0  # 0-1
    cognitive_load: float = 0.0   # 0-1
    uncertainty: float = 0.0       # 0-1

    # 历史
    adaptation_count: int = 0
    last_adaptation: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "awareness_level": self.awareness_level,
            "cognitive_load": self.cognitive_load,
            "uncertainty": self.uncertainty,
            "components": len(self.components),
            "relationships": len(self.relationships),
            "adaptation_count": self.adaptation_count,
        }


class SelfAwarenessLoop:
    """
    自智循环 (重构版)
    
    完整的OODA循环实现:
    - Observe (观察): 收集系统状态
    - Orient (定向): 构建自模型
    - Decide (决策): 生成适应策略
    - Act (行动): 执行适应
    
    基于米田引理的自观察:
    - 正向: 观察系统对外的影响（Hom(System, -)）
    - 逆向: 观察系统受外界的影响（Hom(-, System)）
    """

    def __init__(self):
        self._self_model = SelfModel()
        self._observation_buffer: deque = deque(maxlen=1000)
        self._decision_history: deque = deque(maxlen=500)
        self._action_history: deque = deque(maxlen=500)
        self._running = False
        self._loop_interval: float = 10.0
        self._observers: List[Callable] = []
        self._adaptation_strategies: Dict[str, Callable] = {}

    # ------------------------------------------------------------------
    # OODA循环
    # ------------------------------------------------------------------
    async def observe(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        观察: 收集系统状态
        
        收集:
        - 组件健康状态
        - 性能指标
        - 连接模式
        - 异常信号
        """
        observation = {
            "timestamp": time.time(),
            "components": system_state.get("components", {}),
            "metrics": system_state.get("metrics", {}),
            "alerts": system_state.get("alerts", []),
        }
        self._observation_buffer.append(observation)

        # 调用外部观察者
        for observer in self._observers:
            try:
                if asyncio.iscoroutinefunction(observer):
                    await observer(observation)
                else:
                    observer(observation)
            except Exception as e:
                logger.error(f"Observer error: {e}")

        return observation

    async def orient(self, observation: Dict[str, Any]) -> SelfModel:
        """
        定向: 构建自模型
        
        将原始观察整合为一致的系统表示。
        """
        self._self_model.updated_at = time.time()

        # 更新组件状态
        components = observation.get("components", {})
        for cid, cstate in components.items():
            self._self_model.components[cid] = cstate
            health = cstate.get("health", 1.0)
            self._self_model.health_map[cid] = health

        # 计算自智水平
        total_health = sum(self._self_model.health_map.values())
        count = len(self._self_model.health_map)
        self._self_model.awareness_level = total_health / count if count > 0 else 0

        # 计算认知负载
        alerts = observation.get("alerts", [])
        self._self_model.cognitive_load = min(1.0, len(alerts) / 10)

        # 计算不确定性
        recent = list(self._observation_buffer)[-10:]
        if len(recent) >= 2:
            variances = []
            for cid in self._self_model.components:
                values = [o["components"].get(cid, {}).get("health", 1.0) for o in recent if cid in o.get("components", {})]
                if len(values) > 1:
                    mean = sum(values) / len(values)
                    var = sum((v - mean) ** 2 for v in values) / len(values)
                    variances.append(var)
            self._self_model.uncertainty = sum(variances) / len(variances) if variances else 0

        return self._self_model

    async def decide(self, model: SelfModel) -> List[Dict[str, Any]]:
        """
        决策: 生成适应策略
        
        基于自模型和当前状态，决定需要采取的行动。
        """
        strategies = []

        # 策略1: 如果有不健康组件，触发修复
        for cid, health in model.health_map.items():
            if health < 0.5:
                strategies.append({
                    "type": "heal",
                    "target": cid,
                    "priority": "critical" if health < 0.2 else "high",
                    "reason": f"Component health: {health:.2f}",
                })

        # 策略2: 如果认知负载过高，触发减负
        if model.cognitive_load > 0.8:
            strategies.append({
                "type": "reduce_load",
                "target": "system",
                "priority": "high",
                "reason": f"Cognitive load: {model.cognitive_load:.2f}",
            })

        # 策略3: 如果不确定性过高，触发探测
        if model.uncertainty > 0.5:
            strategies.append({
                "type": "probe",
                "target": "system",
                "priority": "medium",
                "reason": f"Uncertainty: {model.uncertainty:.2f}",
            })

        # 策略4: 如果自智水平过低，触发重新配置
        if model.awareness_level < 0.3:
            strategies.append({
                "type": "reconfigure",
                "target": "system",
                "priority": "high",
                "reason": f"Awareness level: {model.awareness_level:.2f}",
            })

        # 按优先级排序
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        strategies.sort(key=lambda s: priority_order.get(s["priority"], 4))

        self._decision_history.append({
            "timestamp": time.time(),
            "strategies": strategies,
            "model_state": model.to_dict(),
        })

        return strategies

    async def act(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        行动: 执行适应策略
        """
        results = []

        for strategy in strategies:
            stype = strategy["type"]
            handler = self._adaptation_strategies.get(stype)

            if handler:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(strategy)
                    else:
                        result = handler(strategy)
                    results.append({
                        "strategy": strategy,
                        "success": True,
                        "result": result,
                    })
                    self._self_model.adaptation_count += 1
                    self._self_model.last_adaptation = time.time()
                except Exception as e:
                    results.append({
                        "strategy": strategy,
                        "success": False,
                        "error": str(e),
                    })
            else:
                results.append({
                    "strategy": strategy,
                    "success": False,
                    "error": "No handler registered",
                })

        self._action_history.append({
            "timestamp": time.time(),
            "results": results,
        })

        return results

    # ------------------------------------------------------------------
    # 完整循环
    # ------------------------------------------------------------------
    async def run_cycle(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """运行完整的OODA循环"""
        observation = await self.observe(system_state)
        model = await self.orient(observation)
        strategies = await self.decide(model)
        results = await self.act(strategies)

        return {
            "cycle_timestamp": time.time(),
            "observation": observation["timestamp"],
            "model": model.to_dict(),
            "strategies_count": len(strategies),
            "actions_taken": len([r for r in results if r["success"]]),
            "actions_failed": len([r for r in results if not r["success"]]),
        }

    async def run_continuous(self, state_provider: Callable[[], Dict[str, Any]], interval: float = None):
        """持续运行自智循环"""
        self._running = True
        interval = interval or self._loop_interval

        while self._running:
            try:
                if asyncio.iscoroutinefunction(state_provider):
                    state = await state_provider()
                else:
                    state = state_provider()

                result = await self.run_cycle(state)
                logger.info(f"Self-awareness cycle: {result['actions_taken']} actions taken")

                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Self-awareness loop error: {e}")
                await asyncio.sleep(interval)

    def stop(self):
        self._running = False

    # ------------------------------------------------------------------
    # 配置接口
    # ------------------------------------------------------------------
    def register_observer(self, observer: Callable):
        self._observers.append(observer)

    def register_strategy(self, strategy_type: str, handler: Callable):
        self._adaptation_strategies[strategy_type] = handler

    def get_self_model(self) -> SelfModel:
        return self._self_model

    def get_history(self) -> Dict[str, List]:
        return {
            "observations": list(self._observation_buffer),
            "decisions": list(self._decision_history),
            "actions": list(self._action_history),
        }


# ============================================================================
# 集成与演示
# ============================================================================

class RebuiltCoreSystem:
    """
    重构后的核心系统集成
    
    将四大核心机制整合为统一系统。
    """

    def __init__(self):
        self.scheduler = UnifiedScheduler(max_workers=4)
        self.knowledge = KnowledgeManagementSystem()
        self.emergence = EmergenceComputeEngine()
        self.self_awareness = SelfAwarenessLoop()
        self._running = False

    async def initialize(self):
        """初始化系统"""
        logger.info("RebuiltCoreSystem: Initializing...")

        # 注册自智策略
        self.self_awareness.register_strategy("heal", self._heal_strategy)
        self.self_awareness.register_strategy("reduce_load", self._reduce_load_strategy)
        self.self_awareness.register_strategy("probe", self._probe_strategy)
        self.self_awareness.register_strategy("reconfigure", self._reconfigure_strategy)

        # 启动调度器
        asyncio.create_task(self.scheduler.run())

        logger.info("RebuiltCoreSystem: Initialization complete")

    async def _heal_strategy(self, strategy: Dict[str, Any]):
        """修复策略"""
        target = strategy["target"]
        logger.info(f"Healing strategy: Restarting {target}")
        # 实际实现会重启服务
        return {"action": "restart", "target": target}

    async def _reduce_load_strategy(self, strategy: Dict[str, Any]):
        """减负策略"""
        logger.info("Reducing system load")
        return {"action": "throttle", "target": "non_critical_tasks"}

    async def _probe_strategy(self, strategy: Dict[str, Any]):
        """探测策略"""
        logger.info("Probing system state")
        return {"action": "deep_scan"}

    async def _reconfigure_strategy(self, strategy: Dict[str, Any]):
        """重配置策略"""
        logger.info("Reconfiguring system")
        return {"action": "reconfigure"}

    def get_system_state(self) -> Dict[str, Any]:
        """获取完整系统状态（用于自智循环）"""
        return {
            "components": {
                "scheduler": {"health": 1.0, "status": "running"},
                "knowledge": {"health": 1.0, "status": "running"},
                "emergence": {"health": 1.0, "status": "running"},
                "self_awareness": {"health": 1.0, "status": "running"},
            },
            "metrics": {
                "scheduler": self.scheduler.get_stats(),
                "knowledge": self.knowledge.get_stats(),
                "emergence": self.emergence.get_stats(),
            },
            "alerts": [],
        }

    async def run(self):
        """运行系统"""
        self._running = True
        await self.initialize()

        # 启动自智循环
        asyncio.create_task(
            self.self_awareness.run_continuous(self.get_system_state, interval=15.0)
        )

        logger.info("RebuiltCoreSystem: Running")

    def stop(self):
        self._running = False
        self.scheduler.stop()
        self.self_awareness.stop()


async def demo():
    """核心机制重构演示"""
    print("=" * 70)
    print("QF-OS Core Mechanism Reconstruction v12 演示")
    print("=" * 70)

    system = RebuiltCoreSystem()
    await system.initialize()

    # 1. 调度器演示
    print("\n[1] 统一调度器")

    def sample_task_handler(payload: Dict[str, Any]) -> str:
        return f"Processed: {payload}"

    tasks = [
        Task(name=f"task_{i}", priority=TaskPriority.NORMAL, handler=sample_task_handler, payload={"id": i})
        for i in range(5)
    ]
    # 设置依赖链: task_0 -> task_1 -> task_2
    tasks[1].dependencies = [tasks[0].task_id]
    tasks[2].dependencies = [tasks[1].task_id]
    tasks[0].dependents = [tasks[1].task_id]
    tasks[1].dependents = [tasks[2].task_id]

    task_ids = system.scheduler.submit_dag(tasks)
    print(f"    提交 {len(task_ids)} 个任务（含依赖链）")
    print(f"    关键路径: {' -> '.join(system.scheduler.get_critical_path(tasks[2].task_id))}")

    # 2. 知识管理演示
    print("\n[2] 知识管理系统")

    aid1 = await system.knowledge.ingest("猫是哺乳动物", "fact", {"source": "biology"})
    aid2 = await system.knowledge.ingest("哺乳动物会呼吸", "fact", {"source": "biology"})
    aid3 = await system.knowledge.ingest("猫会呼吸", "inference", {"derived": True})

    # 建立关系
    system.knowledge.graph.relate(aid1, aid3, "implies")
    system.knowledge.graph.relate(aid2, aid3, "supports")

    print(f"    摄入3个知识原子")
    print(f"    图谱统计: {system.knowledge.graph.get_stats()}")

    # 正向推理
    conclusions = system.knowledge.graph.forward_inference([aid1, aid2])
    print(f"    正向推理产生 {len(conclusions)} 个结论")

    # 逆向推理
    proofs = system.knowledge.graph.backward_inference(aid3)
    print(f"    逆向推理找到 {len(proofs)} 条证明路径")

    # 3. 涌现计算演示
    print("\n[3] 涌现计算引擎")

    sample_graph = {
        "nodes": [{"id": f"n{i}"} for i in range(8)],
        "edges": [
            {"source": "n0", "target": "n1", "weight": 0.8},
            {"source": "n1", "target": "n2", "weight": 0.7},
            {"source": "n2", "target": "n0", "weight": 0.6},  # 循环
            {"source": "n2", "target": "n3", "weight": 0.9},
            {"source": "n3", "target": "n4", "weight": 0.5},
            {"source": "n4", "target": "n5", "weight": 0.6},
            {"source": "n5", "target": "n6", "weight": 0.7},
            {"source": "n6", "target": "n7", "weight": 0.8},
            {"source": "n3", "target": "n6", "weight": 0.4},
        ],
    }

    patterns = await system.emergence.detect_patterns(sample_graph)
    print(f"    检测到 {len(patterns)} 个涌现模式:")
    for p in patterns:
        print(f"      - {p.pattern_type}: {p.components} (强度={p.strength:.2f})")

    # 传播模拟
    propagation = await system.emergence.simulate_propagation("n0", sample_graph)
    print(f"    从n0传播: 影响 {propagation['total_reach']} 个节点")

    # 4. 自智循环演示
    print("\n[4] 自智循环")

    state = system.get_system_state()
    cycle_result = await system.self_awareness.run_cycle(state)
    print(f"    OODA循环完成:")
    print(f"      观察到的组件: {len(state['components'])}")
    print(f"      生成的策略: {cycle_result['strategies_count']}")
    print(f"      成功执行: {cycle_result['actions_taken']}")

    self_model = system.self_awareness.get_self_model()
    print(f"      自智水平: {self_model.awareness_level:.2%}")
    print(f"      认知负载: {self_model.cognitive_load:.2%}")

    print("\n[5] 系统统计")
    print(f"    调度器: {system.scheduler.get_stats()}")
    print(f"    知识系统: {system.knowledge.get_stats()}")
    print(f"    涌现引擎: {system.emergence.get_stats()}")

    system.stop()

    print("\n" + "=" * 70)
    print("演示完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(demo())
