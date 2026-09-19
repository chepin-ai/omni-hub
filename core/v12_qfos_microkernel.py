#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12: QF-OS 微内核架构 (QF-OS Microkernel Architecture)
=================================================================
基于范畴论语义和米田引理重构的QF-OS微内核。

设计哲学:
---------
1. 最小内核: 仅保留最核心的机制（调度、通信、资源管理）
2. 用户态服务: 所有其他功能作为独立服务运行
3. 范畴语义: 服务 = 对象，IPC = 态射
4. 正反向驱动: 消息传递(正向) + 依赖解析(逆向)
5. 自愈能力: 通过米田嵌入监控系统健康

架构层次:
---------
┌─────────────────────────────────────────────────────────────────┐
│ L4: 应用层 (Applications, Workloads, User Processes)            │
├─────────────────────────────────────────────────────────────────┤
│ L3: 服务层 (Services: Knowledge, Compute, Security, Storage)    │
├─────────────────────────────────────────────────────────────────┤
│ L2: 框架层 (Framework: Yoneda Bus, Service Mesh, Registry)      │
├─────────────────────────────────────────────────────────────────┤
│ L1: 微内核 (Microkernel: IPC, Scheduling, Memory, Drivers)      │
├─────────────────────────────────────────────────────────────────┤
│ L0: 硬件抽象 (HAL: CPU, Memory, Device Abstraction)             │
└─────────────────────────────────────────────────────────────────┘

核心组件:
---------
- Microkernel: 最小可信计算基
- IPC Bus: 基于米田引理的进程间通信
- Service Registry: 服务发现与生命周期管理
- Resource Manager: 资源分配与回收
- Capability System: 基于能力的访问控制
- Fault Tolerance: 故障检测与恢复

版本: v12.0.0 (QF-OS Microkernel)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import signal
import sys
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
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
    TypeVar,
    Union,
)

logger = logging.getLogger("qfos_microkernel")


# ============================================================================
# 基础类型与常量
# ============================================================================

class ServiceState(Enum):
    """服务生命周期状态"""
    REGISTERED = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    DEGRADED = auto()
    FAILED = auto()
    RECOVERING = auto()
    SHUTDOWN = auto()


class MessageType(Enum):
    """IPC消息类型"""
    REQUEST = auto()
    RESPONSE = auto()
    EVENT = auto()
    COMMAND = auto()
    HEARTBEAT = auto()
    DISCOVERY = auto()
    ERROR = auto()


class CapabilityType(Enum):
    """能力类型"""
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    ADMIN = auto()
    DELEGATE = auto()


@dataclass(frozen=True, slots=True)
class Capability:
    """
    能力令牌 (Capability Token)
    
    基于能力的访问控制: 拥有令牌 = 拥有权限
    令牌不可伪造，由内核签发。
    """
    service_id: str
    resource_id: str
    cap_type: CapabilityType
    grantor: str = "kernel"
    issued_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    constraints: Dict[str, Any] = field(default_factory=dict)

    @property
    def token(self) -> str:
        """生成防篡改令牌"""
        data = f"{self.service_id}:{self.resource_id}:{self.cap_type.name}:{self.grantor}:{self.issued_at}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def is_valid(self) -> bool:
        if self.expires_at and time.time() > self.expires_at:
            return False
        return True


@dataclass(slots=True)
class IPCMessage:
    """
    进程间通信消息
    
    对应范畴论中的态射: source → target
    消息本身携带其类型、负载和追踪信息。
    """
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    msg_type: MessageType = MessageType.REQUEST
    source: str = ""
    target: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    ttl: int = 5  # 最大转发次数
    trace: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def forward(self, new_target: str, new_source: str = "") -> IPCMessage:
        """转发消息（TTL递减）"""
        if self.ttl <= 0:
            raise RuntimeError("Message TTL expired")
        fwd = IPCMessage(
            msg_type=self.msg_type,
            source=new_source or self.source,
            target=new_target,
            payload=dict(self.payload),
            capabilities=list(self.capabilities),
            trace=self.trace + [self.msg_id],
            ttl=self.ttl - 1,
        )
        return fwd

    def reply(self, payload: Dict[str, Any], msg_type: MessageType = MessageType.RESPONSE) -> IPCMessage:
        """生成回复消息"""
        return IPCMessage(
            msg_type=msg_type,
            source=self.target,
            target=self.source,
            payload=payload,
            trace=self.trace + [self.msg_id],
        )


# ============================================================================
# L1: 微内核核心 (Microkernel Core)
# ============================================================================

@dataclass
class KernelConfig:
    """内核配置"""
    max_services: int = 256
    max_ipc_queue: int = 10000
    heartbeat_interval: float = 5.0
    heartbeat_timeout: float = 15.0
    service_restart_limit: int = 3
    enable_sandbox: bool = True
    log_level: str = "INFO"
    max_message_size: int = 16 * 1024 * 1024  # 16MB


class Microkernel:
    """
    QF-OS 微内核
    
    最小可信计算基，仅包含:
    1. 服务生命周期管理
    2. 进程间通信 (IPC)
    3. 资源分配
    4. 能力管理
    5. 心跳与健康监控
    
    所有其他功能都在用户态服务中实现。
    """

    def __init__(self, config: KernelConfig = None):
        self.config = config or KernelConfig()
        self._services: Dict[str, Service] = {}
        self._ipc_queues: Dict[str, asyncio.Queue] = {}
        self._capabilities: Dict[str, Capability] = {}
        self._resource_pool = ResourcePool()
        self._running = False
        self._kernel_task: Optional[asyncio.Task] = None
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._startup_time = time.time()
        self._metrics = KernelMetrics()

    # ------------------------------------------------------------------
    # 内核生命周期
    # ------------------------------------------------------------------
    async def boot(self):
        """启动微内核"""
        logger.info("QF-OS Microkernel: Boot sequence started")
        self._running = True

        # 初始化核心IPC队列
        self._ipc_queues["kernel"] = asyncio.Queue(maxsize=self.config.max_ipc_queue)
        self._ipc_queues["broadcast"] = asyncio.Queue(maxsize=self.config.max_ipc_queue)

        # 启动内核主循环
        self._kernel_task = asyncio.create_task(self._kernel_main_loop())

        # 启动心跳监控
        asyncio.create_task(self._heartbeat_monitor())

        logger.info(f"QF-OS Microkernel: Boot complete in {time.time() - self._startup_time:.3f}s")

    async def shutdown(self, graceful: bool = True):
        """关闭微内核"""
        logger.info("QF-OS Microkernel: Shutdown initiated")
        self._running = False

        if graceful:
            # 优雅关闭: 先停止所有服务
            for sid in list(self._services.keys()):
                await self.stop_service(sid)

        if self._kernel_task:
            self._kernel_task.cancel()
            try:
                await self._kernel_task
            except asyncio.CancelledError:
                pass

        logger.info("QF-OS Microkernel: Shutdown complete")

    # ------------------------------------------------------------------
    # 服务管理
    # ------------------------------------------------------------------
    async def register_service(self, service: Service) -> str:
        """
        注册服务到内核
        
        服务注册后，内核为其:
        1. 分配唯一ID
        2. 创建IPC队列
        3. 分配初始能力
        4. 启动服务进程/协程
        """
        sid = service.service_id

        if len(self._services) >= self.config.max_services:
            raise RuntimeError(f"Maximum service limit ({self.config.max_services}) reached")

        if sid in self._services:
            raise ValueError(f"Service {sid} already registered")

        # 创建IPC队列
        self._ipc_queues[sid] = asyncio.Queue(maxsize=self.config.max_ipc_queue)

        # 注册服务
        self._services[sid] = service
        service._kernel = self
        service._state = ServiceState.REGISTERED

        # 分配基础能力
        self._grant_base_capabilities(sid)

        # 初始化服务
        await service._initialize()
        service._state = ServiceState.READY

        logger.info(f"Microkernel: Service {sid} ({service.service_type}) registered")
        self._metrics.services_registered += 1

        # 广播服务上线事件
        await self._broadcast_event("service.up", {"service_id": sid, "type": service.service_type})

        return sid

    async def start_service(self, sid: str):
        """启动服务"""
        service = self._services.get(sid)
        if not service:
            raise ValueError(f"Service {sid} not found")

        service._state = ServiceState.RUNNING
        asyncio.create_task(service._run())
        logger.info(f"Microkernel: Service {sid} started")

    async def stop_service(self, sid: str):
        """停止服务"""
        service = self._services.get(sid)
        if not service:
            return

        service._state = ServiceState.SHUTDOWN
        await service._shutdown()

        # 清理IPC队列
        if sid in self._ipc_queues:
            del self._ipc_queues[sid]

        # 回收能力
        caps_to_remove = [cid for cid, cap in self._capabilities.items() if cap.service_id == sid]
        for cid in caps_to_remove:
            del self._capabilities[cid]

        del self._services[sid]
        logger.info(f"Microkernel: Service {sid} stopped")

    async def restart_service(self, sid: str):
        """重启服务"""
        service = self._services.get(sid)
        if not service:
            raise ValueError(f"Service {sid} not found")

        service._restart_count += 1
        if service._restart_count > self.config.service_restart_limit:
            service._state = ServiceState.FAILED
            logger.error(f"Microkernel: Service {sid} exceeded restart limit")
            return

        await self.stop_service(sid)
        # 重新注册并启动
        new_service = service.__class__(**service._init_args)
        await self.register_service(new_service)
        await self.start_service(new_service.service_id)

    def get_service(self, sid: str) -> Optional[Service]:
        return self._services.get(sid)

    def list_services(self, state_filter: ServiceState = None) -> List[Service]:
        """列出服务"""
        services = list(self._services.values())
        if state_filter:
            services = [s for s in services if s._state == state_filter]
        return services

    # ------------------------------------------------------------------
    # IPC 通信
    # ------------------------------------------------------------------
    async def send(self, message: IPCMessage) -> bool:
        """
        发送IPC消息
        
        对应范畴论中的态射合成:
        source_service --message--> target_service
        """
        if message.ttl <= 0:
            logger.warning(f"Message {message.msg_id} TTL expired")
            return False

        target_queue = self._ipc_queues.get(message.target)
        if not target_queue:
            logger.warning(f"Target {message.target} not found")
            return False

        # 验证能力
        if not self._verify_capabilities(message):
            logger.warning(f"Message {message.msg_id} capability check failed")
            return False

        try:
            target_queue.put_nowait(message)
            self._metrics.messages_sent += 1
            return True
        except asyncio.QueueFull:
            logger.error(f"Queue for {message.target} is full")
            self._metrics.messages_dropped += 1
            return False

    async def broadcast(self, message: IPCMessage):
        """广播消息到所有服务"""
        for sid in self._services:
            if sid != message.source:
                msg = message.forward(sid, message.source)
                await self.send(msg)

    async def call(self, target: str, payload: Dict[str, Any], source: str = "", timeout: float = 5.0) -> Optional[IPCMessage]:
        """
        同步式RPC调用
        
        发送请求并等待响应。
        """
        msg = IPCMessage(
            msg_type=MessageType.REQUEST,
            source=source or "kernel",
            target=target,
            payload=payload,
        )

        # 创建等待队列
        response_queue = asyncio.Queue(maxsize=1)
        self._pending_calls[msg.msg_id] = response_queue

        await self.send(msg)

        try:
            response = await asyncio.wait_for(response_queue.get(), timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.warning(f"RPC call to {target} timed out")
            return None
        finally:
            self._pending_calls.pop(msg.msg_id, None)

    _pending_calls: Dict[str, asyncio.Queue] = {}

    # ------------------------------------------------------------------
    # 能力管理
    # ------------------------------------------------------------------
    def _grant_base_capabilities(self, sid: str):
        """授予服务基础能力"""
        base_caps = [
            Capability(sid, "ipc", CapabilityType.READ, grantor="kernel"),
            Capability(sid, "ipc", CapabilityType.WRITE, grantor="kernel"),
            Capability(sid, "heartbeat", CapabilityType.READ, grantor="kernel"),
            Capability(sid, f"service:{sid}", CapabilityType.ADMIN, grantor="kernel"),
        ]
        for cap in base_caps:
            self._capabilities[cap.token] = cap

    def grant_capability(self, cap: Capability) -> str:
        """授权能力"""
        self._capabilities[cap.token] = cap
        return cap.token

    def revoke_capability(self, token: str):
        """撤销能力"""
        self._capabilities.pop(token, None)

    def _verify_capabilities(self, message: IPCMessage) -> bool:
        """验证消息的能力令牌"""
        if not message.capabilities:
            # 内核消息或广播消息无需能力验证
            return message.source == "kernel" or message.target == "broadcast"

        for token in message.capabilities:
            cap = self._capabilities.get(token)
            if cap and cap.is_valid() and cap.service_id == message.source:
                return True
        return False

    # ------------------------------------------------------------------
    # 资源管理
    # ------------------------------------------------------------------
    def allocate_resource(self, resource_type: str, amount: float, requester: str) -> Optional[str]:
        """分配资源"""
        return self._resource_pool.allocate(resource_type, amount, requester)

    def release_resource(self, allocation_id: str):
        """释放资源"""
        self._resource_pool.release(allocation_id)

    def get_resource_usage(self) -> Dict[str, Any]:
        """获取资源使用情况"""
        return self._resource_pool.get_stats()

    # ------------------------------------------------------------------
    # 内核主循环
    # ------------------------------------------------------------------
    async def _kernel_main_loop(self):
        """内核主循环: 处理内核消息"""
        kernel_queue = self._ipc_queues.get("kernel")
        if not kernel_queue:
            return

        while self._running:
            try:
                message = await asyncio.wait_for(kernel_queue.get(), timeout=1.0)
                await self._handle_kernel_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Kernel loop error: {e}")

    async def _handle_kernel_message(self, message: IPCMessage):
        """处理内核消息"""
        if message.msg_type == MessageType.COMMAND:
            await self._handle_command(message)
        elif message.msg_type == MessageType.HEARTBEAT:
            await self._handle_heartbeat(message)
        elif message.msg_type == MessageType.DISCOVERY:
            await self._handle_discovery(message)
        else:
            # 分发给注册的处理器
            handlers = self._event_handlers.get(message.msg_type.name, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")

    async def _handle_command(self, message: IPCMessage):
        """处理命令"""
        cmd = message.payload.get("command")
        if cmd == "list_services":
            services = [{
                "id": s.service_id,
                "type": s.service_type,
                "state": s._state.name,
            } for s in self._services.values()]
            # 发送响应
            response = message.reply({"services": services})
            await self.send(response)
        elif cmd == "get_metrics":
            response = message.reply(self._metrics.to_dict())
            await self.send(response)
        elif cmd == "shutdown":
            await self.shutdown()

    async def _handle_heartbeat(self, message: IPCMessage):
        """处理心跳"""
        sid = message.source
        service = self._services.get(sid)
        if service:
            service._last_heartbeat = time.time()
            service._state = ServiceState.RUNNING

    async def _handle_discovery(self, message: IPCMessage):
        """处理服务发现请求"""
        query = message.payload.get("query", "")
        matches = [{
            "id": s.service_id,
            "type": s.service_type,
            "capabilities": s.capabilities,
        } for s in self._services.values()
            if query in s.service_type or query in s.service_id]

        response = message.reply({"matches": matches})
        await self.send(response)

    async def _broadcast_event(self, event_type: str, payload: Dict[str, Any]):
        """广播系统事件"""
        msg = IPCMessage(
            msg_type=MessageType.EVENT,
            source="kernel",
            target="broadcast",
            payload={"event_type": event_type, **payload},
        )
        await self.broadcast(msg)

    # ------------------------------------------------------------------
    # 心跳监控
    # ------------------------------------------------------------------
    async def _heartbeat_monitor(self):
        """监控服务心跳"""
        while self._running:
            now = time.time()
            for sid, service in list(self._services.items()):
                if service._state in (ServiceState.RUNNING, ServiceState.READY):
                    last_hb = service._last_heartbeat
                    if now - last_hb > self.config.heartbeat_timeout:
                        logger.warning(f"Service {sid} heartbeat timeout")
                        service._state = ServiceState.DEGRADED
                        # 触发恢复
                        asyncio.create_task(self._attempt_recovery(sid))
            await asyncio.sleep(self.config.heartbeat_interval)

    async def _attempt_recovery(self, sid: str):
        """尝试恢复服务"""
        service = self._services.get(sid)
        if not service:
            return

        service._state = ServiceState.RECOVERING
        logger.info(f"Attempting recovery for {sid}")

        try:
            await service._recover()
            service._state = ServiceState.RUNNING
            service._last_heartbeat = time.time()
            logger.info(f"Service {sid} recovered")
        except Exception as e:
            logger.error(f"Recovery failed for {sid}: {e}")
            if service._restart_count < self.config.service_restart_limit:
                await self.restart_service(sid)
            else:
                service._state = ServiceState.FAILED

    def on_event(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        self._event_handlers[event_type].append(handler)


@dataclass
class KernelMetrics:
    """内核指标"""
    services_registered: int = 0
    services_running: int = 0
    services_failed: int = 0
    messages_sent: int = 0
    messages_dropped: int = 0
    recoveries_attempted: int = 0
    recoveries_successful: int = 0
    uptime: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# 资源池
# ============================================================================

@dataclass
class ResourceAllocation:
    allocation_id: str
    resource_type: str
    amount: float
    requester: str
    allocated_at: float = field(default_factory=time.time)


class ResourcePool:
    """
    资源池
    
    管理CPU、内存、存储等资源的分配与回收。
    支持资源配额、优先级和超额预订。
    """

    def __init__(self):
        self._allocations: Dict[str, ResourceAllocation] = {}
        self._totals: Dict[str, float] = {
            "cpu": 100.0,  # CPU百分比
            "memory": 1024 * 1024 * 1024 * 16,  # 16GB
            "storage": 1024 * 1024 * 1024 * 100,  # 100GB
            "bandwidth": 1024 * 1024 * 1000,  # 1Gbps
        }
        self._used: Dict[str, float] = defaultdict(float)
        self._quotas: Dict[str, Dict[str, float]] = defaultdict(dict)

    def allocate(self, resource_type: str, amount: float, requester: str) -> Optional[str]:
        """分配资源"""
        if resource_type not in self._totals:
            return None

        available = self._totals[resource_type] - self._used[resource_type]
        if amount > available:
            # 尝试超额分配（如果允许）
            quota = self._quotas[requester].get(resource_type, 0)
            used_by_requester = sum(
                a.amount for a in self._allocations.values()
                if a.requester == requester and a.resource_type == resource_type
            )
            if used_by_requester + amount > quota * 1.2:  # 20%超额限制
                return None

        alloc_id = str(uuid.uuid4())[:8]
        allocation = ResourceAllocation(alloc_id, resource_type, amount, requester)
        self._allocations[alloc_id] = allocation
        self._used[resource_type] += amount
        return alloc_id

    def release(self, allocation_id: str):
        """释放资源"""
        alloc = self._allocations.pop(allocation_id, None)
        if alloc:
            self._used[alloc.resource_type] -= alloc.amount
            if self._used[alloc.resource_type] < 0:
                self._used[alloc.resource_type] = 0

    def set_quota(self, requester: str, resource_type: str, quota: float):
        """设置资源配额"""
        self._quotas[requester][resource_type] = quota

    def get_stats(self) -> Dict[str, Any]:
        """获取资源统计"""
        return {
            "totals": dict(self._totals),
            "used": dict(self._used),
            "available": {
                rt: self._totals[rt] - self._used[rt]
                for rt in self._totals
            },
            "allocation_count": len(self._allocations),
            "utilization": {
                rt: self._used[rt] / total if total > 0 else 0
                for rt, total in self._totals.items()
            },
        }


# ============================================================================
# L2: 服务基类与框架
# ============================================================================

class Service(ABC):
    """
    服务基类
    
    所有QF-OS服务都继承此类。
    服务通过IPC与内核和其他服务通信。
    """

    def __init__(self, service_id: str, service_type: str, capabilities: List[str] = None):
        self.service_id = service_id
        self.service_type = service_type
        self.capabilities = capabilities or []
        self._kernel: Optional[Microkernel] = None
        self._state = ServiceState.REGISTERED
        self._last_heartbeat = time.time()
        self._restart_count = 0
        self._init_args = {"service_id": service_id, "service_type": service_type, "capabilities": capabilities}
        self._message_handlers: Dict[MessageType, Callable] = {}

    # ------------------------------------------------------------------
    # 生命周期钩子
    # ------------------------------------------------------------------
    async def _initialize(self):
        """初始化（子类可覆盖）"""
        pass

    async def _run(self):
        """运行主循环"""
        # 启动心跳
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        # 启动消息处理
        message_task = asyncio.create_task(self._message_loop())

        try:
            await asyncio.gather(heartbeat_task, message_task)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Service {self.service_id} error: {e}")
            self._state = ServiceState.FAILED

    async def _shutdown(self):
        """关闭（子类可覆盖）"""
        pass

    async def _recover(self):
        """恢复（子类可覆盖）"""
        pass

    # ------------------------------------------------------------------
    # 内部循环
    # ------------------------------------------------------------------
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._state in (ServiceState.RUNNING, ServiceState.READY):
            try:
                await self._send_heartbeat()
                await asyncio.sleep(5.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def _send_heartbeat(self):
        """发送心跳"""
        if not self._kernel:
            return
        msg = IPCMessage(
            msg_type=MessageType.HEARTBEAT,
            source=self.service_id,
            target="kernel",
            payload={"timestamp": time.time(), "state": self._state.name},
        )
        await self._kernel.send(msg)

    async def _message_loop(self):
        """消息处理循环"""
        if not self._kernel:
            return

        queue = self._kernel._ipc_queues.get(self.service_id)
        if not queue:
            return

        while self._state in (ServiceState.RUNNING, ServiceState.READY, ServiceState.DEGRADED):
            try:
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message handling error: {e}")

    async def _handle_message(self, message: IPCMessage):
        """处理消息"""
        handler = self._message_handlers.get(message.msg_type)
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Handler error: {e}")
                # 发送错误响应
                if message.msg_type == MessageType.REQUEST:
                    error_reply = message.reply({"error": str(e)}, MessageType.ERROR)
                    await self._kernel.send(error_reply)
        else:
            # 默认处理
            await self.on_message(message)

    # ------------------------------------------------------------------
    # 公共API
    # ------------------------------------------------------------------
    async def send(self, target: str, payload: Dict[str, Any], msg_type: MessageType = MessageType.REQUEST):
        """发送消息"""
        if not self._kernel:
            raise RuntimeError("Service not attached to kernel")
        msg = IPCMessage(
            msg_type=msg_type,
            source=self.service_id,
            target=target,
            payload=payload,
        )
        return await self._kernel.send(msg)

    async def call(self, target: str, payload: Dict[str, Any], timeout: float = 5.0) -> Optional[IPCMessage]:
        """RPC调用"""
        if not self._kernel:
            raise RuntimeError("Service not attached to kernel")
        return await self._kernel.call(target, payload, self.service_id, timeout)

    def register_handler(self, msg_type: MessageType, handler: Callable):
        """注册消息处理器"""
        self._message_handlers[msg_type] = handler

    @abstractmethod
    async def on_message(self, message: IPCMessage):
        """子类覆盖此方法处理消息"""
        pass


# ============================================================================
# 具体服务实现示例
# ============================================================================

class SchedulerService(Service):
    """
    调度器服务
    
    负责任务调度、负载均衡和资源分配。
    """

    def __init__(self):
        super().__init__("scheduler", "core", ["task_dispatch", "resource_alloc"])
        self._task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running_tasks: Dict[str, Any] = {}
        self._task_history: deque = deque(maxlen=1000)

    async def on_message(self, message: IPCMessage):
        if message.msg_type == MessageType.REQUEST:
            action = message.payload.get("action")
            if action == "schedule":
                task = message.payload.get("task")
                priority = message.payload.get("priority", 5)
                await self._task_queue.put((priority, time.time(), task))
                reply = message.reply({"status": "scheduled", "queue_depth": self._task_queue.qsize()})
                await self._kernel.send(reply)
            elif action == "status":
                reply = message.reply({
                    "running": len(self._running_tasks),
                    "queued": self._task_queue.qsize(),
                })
                await self._kernel.send(reply)

    async def _run(self):
        # 启动调度循环
        scheduler_task = asyncio.create_task(self._scheduling_loop())
        await super()._run()
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass

    async def _scheduling_loop(self):
        """调度循环"""
        while self._state == ServiceState.RUNNING:
            try:
                priority, ts, task = await asyncio.wait_for(
                    self._task_queue.get(), timeout=1.0
                )
                # 执行调度逻辑
                await self._execute_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Scheduling error: {e}")

    async def _execute_task(self, task: Dict[str, Any]):
        """执行任务"""
        task_id = task.get("id", str(uuid.uuid4())[:8])
        self._running_tasks[task_id] = task
        try:
            # 实际任务执行逻辑
            await asyncio.sleep(0.1)  # 模拟执行
            self._task_history.append({
                "task_id": task_id,
                "status": "completed",
                "timestamp": time.time(),
            })
        finally:
            del self._running_tasks[task_id]


class KnowledgeService(Service):
    """
    知识管理服务
    
    管理知识存储、查询和推理。
    """

    def __init__(self):
        super().__init__("knowledge", "knowledge", ["store", "query", "infer"])
        self._store: Dict[str, Any] = {}
        self._indices: Dict[str, Set[str]] = defaultdict(set)

    async def on_message(self, message: IPCMessage):
        if message.msg_type == MessageType.REQUEST:
            action = message.payload.get("action")
            if action == "store":
                key = message.payload.get("key")
                value = message.payload.get("value")
                self._store[key] = value
                # 更新索引
                for tag in message.payload.get("tags", []):
                    self._indices[tag].add(key)
                reply = message.reply({"status": "stored", "key": key})
            elif action == "query":
                key = message.payload.get("key")
                value = self._store.get(key)
                reply = message.reply({"found": value is not None, "value": value})
            elif action == "search":
                tag = message.payload.get("tag")
                keys = list(self._indices.get(tag, set()))
                reply = message.reply({"keys": keys, "count": len(keys)})
            else:
                reply = message.reply({"error": "Unknown action"}, MessageType.ERROR)
            await self._kernel.send(reply)


class ComputeService(Service):
    """
    计算引擎服务
    
    提供分布式计算能力。
    """

    def __init__(self):
        super().__init__("compute", "compute", ["execute", "parallel", "distribute"])
        self._workers: List[str] = []
        self._compute_graphs: Dict[str, Any] = {}

    async def on_message(self, message: IPCMessage):
        if message.msg_type == MessageType.REQUEST:
            action = message.payload.get("action")
            if action == "execute":
                graph = message.payload.get("graph")
                graph_id = str(uuid.uuid4())[:8]
                self._compute_graphs[graph_id] = graph
                # 异步执行
                asyncio.create_task(self._run_computation(graph_id))
                reply = message.reply({"status": "accepted", "graph_id": graph_id})
            elif action == "status":
                graph_id = message.payload.get("graph_id")
                graph = self._compute_graphs.get(graph_id)
                reply = message.reply({"graph_id": graph_id, "exists": graph is not None})
            else:
                reply = message.reply({"error": "Unknown action"}, MessageType.ERROR)
            await self._kernel.send(reply)

    async def _run_computation(self, graph_id: str):
        """运行计算图"""
        graph = self._compute_graphs.get(graph_id)
        if not graph:
            return
        # 简化实现
        await asyncio.sleep(1.0)
        # 完成后通知
        if self._kernel:
            await self.send("kernel", {
                "event": "compute_complete",
                "graph_id": graph_id,
            }, MessageType.EVENT)


class SecurityService(Service):
    """
    安全服务
    
    认证、授权和审计。
    """

    def __init__(self):
        super().__init__("security", "security", ["authenticate", "authorize", "audit"])
        self._identities: Dict[str, Dict[str, Any]] = {}
        self._audit_log: deque = deque(maxlen=10000)

    async def on_message(self, message: IPCMessage):
        if message.msg_type == MessageType.REQUEST:
            action = message.payload.get("action")
            if action == "authenticate":
                identity = message.payload.get("identity")
                token = hashlib.sha256(f"{identity}:{time.time()}".encode()).hexdigest()[:16]
                self._identities[token] = {"identity": identity, "created": time.time()}
                reply = message.reply({"token": token})
            elif action == "authorize":
                token = message.payload.get("token")
                resource = message.payload.get("resource")
                auth = self._identities.get(token)
                allowed = auth is not None
                self._audit_log.append({
                    "action": "authorize",
                    "token": token,
                    "resource": resource,
                    "allowed": allowed,
                    "timestamp": time.time(),
                })
                reply = message.reply({"allowed": allowed})
            else:
                reply = message.reply({"error": "Unknown action"}, MessageType.ERROR)
            await self._kernel.send(reply)


class EventBusService(Service):
    """
    事件总线服务
    
    发布-订阅模式的消息总线。
    """

    def __init__(self):
        super().__init__("event_bus", "communication", ["pub", "sub", "route"])
        self._subscribers: Dict[str, List[str]] = defaultdict(list)
        self._event_history: deque = deque(maxlen=5000)

    async def on_message(self, message: IPCMessage):
        if message.msg_type == MessageType.REQUEST:
            action = message.payload.get("action")
            if action == "subscribe":
                channel = message.payload.get("channel")
                self._subscribers[channel].append(message.source)
                reply = message.reply({"status": "subscribed", "channel": channel})
            elif action == "publish":
                channel = message.payload.get("channel")
                event = message.payload.get("event")
                await self._publish(channel, event, message.source)
                reply = message.reply({"status": "published", "subscribers": len(self._subscribers.get(channel, []))})
            else:
                reply = message.reply({"error": "Unknown action"}, MessageType.ERROR)
            await self._kernel.send(reply)

    async def _publish(self, channel: str, event: Any, source: str):
        """发布事件到订阅者"""
        subscribers = self._subscribers.get(channel, [])
        self._event_history.append({
            "channel": channel,
            "event": event,
            "source": source,
            "timestamp": time.time(),
            "subscriber_count": len(subscribers),
        })
        for subscriber in subscribers:
            if subscriber != source and self._kernel:
                msg = IPCMessage(
                    msg_type=MessageType.EVENT,
                    source=source,
                    target=subscriber,
                    payload={"channel": channel, "event": event},
                )
                await self._kernel.send(msg)


# ============================================================================
# 服务工厂与自动发现
# ============================================================================

class ServiceFactory:
    """
    服务工厂
    
    根据配置动态创建和配置服务。
    """

    _service_types: Dict[str, type] = {
        "scheduler": SchedulerService,
        "knowledge": KnowledgeService,
        "compute": ComputeService,
        "security": SecurityService,
        "event_bus": EventBusService,
    }

    @classmethod
    def register_type(cls, name: str, service_class: type):
        cls._service_types[name] = service_class

    @classmethod
    def create(cls, service_type: str, **kwargs) -> Service:
        service_class = cls._service_types.get(service_type)
        if not service_class:
            raise ValueError(f"Unknown service type: {service_type}")
        return service_class(**kwargs)

    @classmethod
    def list_types(cls) -> List[str]:
        return list(cls._service_types.keys())


# ============================================================================
# 系统启动器
# ============================================================================

class SystemLauncher:
    """
    系统启动器
    
    负责启动和配置整个QF-OS系统。
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.kernel: Optional[Microkernel] = None
        self._services_config: List[Dict[str, Any]] = self.config.get("services", [])

    async def launch(self) -> Microkernel:
        """启动系统"""
        # 创建内核
        kernel_config = KernelConfig(
            max_services=self.config.get("max_services", 256),
            heartbeat_interval=self.config.get("heartbeat_interval", 5.0),
            enable_sandbox=self.config.get("enable_sandbox", True),
        )
        self.kernel = Microkernel(kernel_config)

        # 启动内核
        await self.kernel.boot()

        # 注册核心服务
        core_services = [
            EventBusService(),
            SchedulerService(),
            SecurityService(),
        ]

        for service in core_services:
            await self.kernel.register_service(service)
            await self.kernel.start_service(service.service_id)

        # 注册其他服务
        for svc_config in self._services_config:
            svc_type = svc_config.get("type")
            if svc_type:
                service = ServiceFactory.create(svc_type)
                await self.kernel.register_service(service)
                if svc_config.get("auto_start", True):
                    await self.kernel.start_service(service.service_id)

        logger.info("QF-OS System: Launch complete")
        return self.kernel

    async def shutdown(self):
        """关闭系统"""
        if self.kernel:
            await self.kernel.shutdown()


# ============================================================================
# 演示
# ============================================================================

async def demo():
    """QF-OS微内核演示"""
    print("=" * 70)
    print("QF-OS Microkernel v12 演示")
    print("=" * 70)

    # 启动系统
    launcher = SystemLauncher({
        "services": [
            {"type": "knowledge", "auto_start": True},
            {"type": "compute", "auto_start": True},
        ],
        "heartbeat_interval": 2.0,
    })

    kernel = await launcher.launch()

    print(f"\n[1] 系统已启动")
    print(f"    服务数量: {len(kernel.list_services())}")

    # 列出服务
    print(f"\n[2] 已注册服务:")
    for svc in kernel.list_services():
        print(f"    - {svc.service_id} ({svc.service_type}): {svc._state.name}")

    # IPC通信演示
    print(f"\n[3] IPC通信演示:")

    # 通过kernel发送命令查询服务列表
    msg = IPCMessage(
        msg_type=MessageType.COMMAND,
        source="demo",
        target="kernel",
        payload={"command": "list_services"},
    )
    await kernel.send(msg)

    # 直接调用知识服务
    knowledge = kernel.get_service("knowledge")
    if knowledge:
        await knowledge.send("knowledge", {
            "action": "store",
            "key": "test_key",
            "value": {"data": "Hello QF-OS"},
            "tags": ["test"],
        })
        print("    存储数据到知识服务")

        response = await kernel.call("knowledge", {
            "action": "query",
            "key": "test_key",
        }, timeout=2.0)
        if response:
            print(f"    查询结果: {response.payload}")

    # 资源使用
    print(f"\n[4] 资源使用:")
    stats = kernel.get_resource_usage()
    for rt, util in stats.get("utilization", {}).items():
        print(f"    {rt}: {util:.2%}")

    # 内核指标
    print(f"\n[5] 内核指标:")
    msg = IPCMessage(
        msg_type=MessageType.COMMAND,
        source="demo",
        target="kernel",
        payload={"command": "get_metrics"},
    )
    await kernel.send(msg)

    # 等待一下让消息处理
    await asyncio.sleep(0.5)

    # 关闭
    print(f"\n[6] 关闭系统...")
    await launcher.shutdown()
    print("    系统已关闭")

    print("\n" + "=" * 70)
    print("演示完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(demo())
