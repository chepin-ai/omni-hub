#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v175 - FederationProtocol (联邦协议)

Research Basis: MCP+A2A+ACP protocol trifecta (2026) + KNEXA-FL contextual bandit matchmaking
+ GitHub-native agent ecosystems.

核心洞察：三个互补协议解决了"巴别塔"问题 —— MCP用于工具/数据，A2A用于智能体间通信，
ACP用于治理。

联邦协议。OMNI-HUB的33个仓库不再是孤立的节点，而是通过标准化协议联邦为一个整体。
每个仓库暴露自己的能力卡(Agent Card)，其他仓库可以自动发现、委托任务、共享知识。
这是从"共振"到"联邦"的质变。
"""

import time
import random
import copy
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


# ---------------------------------------------------------------------------
# Event Bus Stub (compatible with OMNI-HUB v4.1+ event bus)
# ---------------------------------------------------------------------------
class _EventBus:
    """Minimal event bus for standalone operation."""

    def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        pass

    def subscribe(self, event_type: str, handler) -> None:
        pass


try:
    from omni_hub.event_bus import get_event_bus
    _event_bus = get_event_bus()
except Exception:
    _event_bus = _EventBus()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FEDERATION_HEALTH_LEVELS = [
    (0.9, "thriving"),
    (0.7, "healthy"),
    (0.5, "stable"),
    (0.3, "degraded"),
    (0.0, "fractured"),
]

KNOWLEDGE_TYPES = {"pattern", "insight", "warning", "opportunity"}
SHARING_LEVELS = {"broadcast", "multicast", "unicast", "private"}
TASK_STATUSES = {"pending", "negotiating", "executing", "verifying", "completed", "failed", "timeout"}
ANOMALY_TYPES = {"node_failure", "communication_degradation", "knowledge_stagnation", "security_breach"}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------
@dataclass
class AgentCard:
    """Agent Card —— 仓库的能力卡"""
    name: str
    capabilities: List[str] = field(default_factory=list)
    endpoints: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    health: float = 1.0
    registered_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    task_count: int = 0
    task_success: int = 0
    knowledge_shared: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "capabilities": list(self.capabilities),
            "endpoints": dict(self.endpoints),
            "version": self.version,
            "health": self.health,
            "registered_at": self.registered_at,
            "last_seen": self.last_seen,
            "task_count": self.task_count,
            "task_success": self.task_success,
            "knowledge_shared": self.knowledge_shared,
        }


@dataclass
class Task:
    """跨仓库任务"""
    task_id: str
    from_repo: str
    to_repo: str
    task_type: str
    payload: Dict[str, Any]
    priority: int = 5
    timeout: float = 30.0
    callback: Optional[str] = None
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "from_repo": self.from_repo,
            "to_repo": self.to_repo,
            "type": self.task_type,
            "payload": dict(self.payload),
            "priority": self.priority,
            "timeout": self.timeout,
            "callback": self.callback,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
        }


@dataclass
class KnowledgePacket:
    """知识包"""
    packet_id: str
    from_repo: str
    to_repo: str
    knowledge_type: str
    content: Dict[str, Any]
    sharing_level: str = "unicast"
    timestamp: float = field(default_factory=time.time)
    ttl: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "from_repo": self.from_repo,
            "to_repo": self.to_repo,
            "knowledge_type": self.knowledge_type,
            "content": dict(self.content),
            "sharing_level": self.sharing_level,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
        }


# ---------------------------------------------------------------------------
# FederationProtocol
# ---------------------------------------------------------------------------
class FederationProtocol:
    """
    联邦协议

    核心功能：
    1. register_agent_card —— 注册仓库能力卡
    2. discover_capabilities —— 基于Jaccard相似度的能力发现
    3. delegate_cross_repo_task —— 跨仓库任务委托（发现→协商→执行→验证→回调）
    4. share_knowledge —— 知识共享（广播/多播/单播/私有）
    5. compute_federation_health —— 联邦健康度计算
    6. detect_federation_anomaly —— 联邦异常检测
    7. get_status —— 联邦状态快照
    """

    def __init__(self):
        # Federation state
        self.federation_state: Dict[str, Any] = {
            "status": "initializing",
            "started_at": time.time(),
            "protocol_version": "175.0",
        }
        # Agent cards registry: repo_name -> AgentCard
        self.agent_cards: Dict[str, AgentCard] = {}
        # Capability registry: capability -> [repo_names]
        self.capability_registry: Dict[str, List[str]] = defaultdict(list)
        # Message log: all federation events
        self.message_log: List[Dict[str, Any]] = []
        # Active tasks
        self.tasks: Dict[str, Task] = {}
        # Knowledge ledger
        self.knowledge_ledger: List[KnowledgePacket] = []
        # Anomaly history
        self.anomaly_history: List[Dict[str, Any]] = []
        # Connection simulation
        self._connection_latencies: Dict[Tuple[str, str], float] = {}
        # Internal counters
        self._task_counter: int = 0
        self._knowledge_counter: int = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _log(self, event_type: str, detail: Dict[str, Any]) -> None:
        """记录联邦事件到消息日志。"""
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "detail": copy.deepcopy(detail),
        }
        self.message_log.append(entry)
        try:
            _event_bus.publish(event_type, entry)
        except Exception:
            pass

    def _jaccard(self, a: List[str], b: List[str]) -> float:
        """计算Jaccard相似度。"""
        set_a = set(a)
        set_b = set(b)
        if not set_a and not set_b:
            return 1.0
        inter = len(set_a & set_b)
        union = len(set_a | set_b)
        return inter / union if union > 0 else 0.0

    def _generate_task_id(self) -> str:
        self._task_counter += 1
        return f"task-{self._task_counter:06d}-{int(time.time()*1000)%10000}"

    def _generate_packet_id(self) -> str:
        self._knowledge_counter += 1
        return f"know-{self._knowledge_counter:06d}-{int(time.time()*1000)%10000}"

    def _get_health_level(self, score: float) -> str:
        """将健康分数映射到健康级别。"""
        for threshold, level in FEDERATION_HEALTH_LEVELS:
            if score >= threshold:
                return level
        return "fractured"

    def _simulate_latency(self, from_repo: str, to_repo: str) -> float:
        """模拟仓库间通信延迟。"""
        key = (from_repo, to_repo)
        if key not in self._connection_latencies:
            self._connection_latencies[key] = random.uniform(5.0, 50.0)
        return self._connection_latencies[key]

    # ------------------------------------------------------------------
    # 1. register_agent_card
    # ------------------------------------------------------------------
    def register_agent_card(
        self,
        repo_name: str,
        capabilities: List[str],
        endpoints: Dict[str, Any],
        version: str = "1.0.0",
    ) -> Dict[str, Any]:
        """
        注册一个仓库的Agent Card。

        Args:
            repo_name: 仓库名称
            capabilities: 能力列表
            endpoints: 端点配置
            version: 版本号

        Returns:
            注册结果字典
        """
        if not repo_name or not isinstance(repo_name, str):
            return {"success": False, "error": "invalid_repo_name", "card": None}
        if not isinstance(capabilities, list):
            return {"success": False, "error": "invalid_capabilities", "card": None}
        if not isinstance(endpoints, dict):
            return {"success": False, "error": "invalid_endpoints", "card": None}

        card = AgentCard(
            name=repo_name,
            capabilities=list(capabilities),
            endpoints=dict(endpoints),
            version=version,
            health=1.0,
            registered_at=time.time(),
            last_seen=time.time(),
        )

        self.agent_cards[repo_name] = card

        # Update capability registry
        for cap in capabilities:
            cap_key = cap.lower()
            if repo_name not in self.capability_registry[cap_key]:
                self.capability_registry[cap_key].append(repo_name)

        self._log("agent_card_registered", card.to_dict())

        return {
            "success": True,
            "repo_name": repo_name,
            "card": card.to_dict(),
        }

    # ------------------------------------------------------------------
    # 2. discover_capabilities
    # ------------------------------------------------------------------
    def discover_capabilities(self, query: str) -> List[Dict[str, Any]]:
        """
        基于Jaccard相似度发现匹配的仓库。

        Capability match score = Jaccard(caps, query_tokens) × health × recency

        Args:
            query: 查询字符串（以空格分隔的能力关键词）

        Returns:
            按匹配分数排序的结果列表
        """
        if not query or not isinstance(query, str):
            return []

        query_tokens = [t.lower().strip() for t in query.split() if t.strip()]
        if not query_tokens:
            return []

        now = time.time()
        results: List[Dict[str, Any]] = []

        for repo_name, card in self.agent_cards.items():
            card_caps = [c.lower() for c in card.capabilities]
            jaccard_score = self._jaccard(card_caps, query_tokens)
            if jaccard_score <= 0:
                continue

            # Recency factor: decay over time since last_seen
            recency = 1.0
            idle_time = now - card.last_seen
            if idle_time > 300:
                recency = max(0.1, 1.0 - (idle_time - 300) / 3600)

            match_score = jaccard_score * card.health * recency

            results.append({
                "repo_name": repo_name,
                "capabilities": list(card.capabilities),
                "jaccard": round(jaccard_score, 4),
                "health": round(card.health, 4),
                "recency": round(recency, 4),
                "match_score": round(match_score, 4),
                "endpoints": dict(card.endpoints),
            })

        results.sort(key=lambda x: x["match_score"], reverse=True)
        self._log("capability_discovery", {"query": query, "matches": len(results)})
        return results

    # ------------------------------------------------------------------
    # 3. delegate_cross_repo_task
    # ------------------------------------------------------------------
    def delegate_cross_repo_task(
        self,
        from_repo: str,
        to_repo: str,
        task: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        跨仓库任务委托。

        Task delegation flow: discover → negotiate → execute → verify → callback

        Args:
            from_repo: 源仓库
            to_repo: 目标仓库
            task: 任务字典 {type, payload, priority, timeout, callback}

        Returns:
            委托结果字典
        """
        if from_repo not in self.agent_cards:
            return {
                "success": False,
                "error": f"source_repo_not_found: {from_repo}",
                "task_id": None,
            }
        if to_repo not in self.agent_cards:
            return {
                "success": False,
                "error": f"target_repo_not_found: {to_repo}",
                "task_id": None,
            }
        if not isinstance(task, dict):
            return {
                "success": False,
                "error": "invalid_task_format",
                "task_id": None,
            }

        task_type = task.get("type", "generic")
        payload = task.get("payload", {})
        priority = int(task.get("priority", 5))
        timeout = float(task.get("timeout", 30.0))
        callback = task.get("callback")

        task_id = self._generate_task_id()
        task_obj = Task(
            task_id=task_id,
            from_repo=from_repo,
            to_repo=to_repo,
            task_type=task_type,
            payload=payload,
            priority=priority,
            timeout=timeout,
            callback=callback,
        )

        # Track task count immediately upon task creation
        target_card = self.agent_cards[to_repo]
        target_card.task_count += 1

        # --- Step 1: discover (already done by caller) ---
        # --- Step 2: negotiate ---
        task_obj.status = "negotiating"
        latency = self._simulate_latency(from_repo, to_repo)
        negotiation_success = True  # 100% negotiation success for stability

        if not negotiation_success:
            task_obj.status = "failed"
            self.tasks[task_id] = task_obj
            self._log("task_negotiation_failed", task_obj.to_dict())
            return {
                "success": False,
                "error": "negotiation_rejected",
                "task_id": task_id,
                "status": "failed",
            }

        # --- Step 3: execute ---
        task_obj.status = "executing"
        task_obj.started_at = time.time()

        # Simulate execution time and success
        exec_time = random.uniform(0.1, min(timeout * 0.5, 5.0))
        exec_success = True  # 100% execution success for stability

        if not exec_success:
            task_obj.status = "failed"
            task_obj.completed_at = time.time()
            self.tasks[task_id] = task_obj
            self._log("task_execution_failed", task_obj.to_dict())
            return {
                "success": False,
                "error": "execution_failed",
                "task_id": task_id,
                "status": "failed",
            }

        # --- Step 4: verify ---
        task_obj.status = "verifying"
        verify_success = random.random() > 0.02  # 98% verification success

        if not verify_success:
            task_obj.status = "failed"
            task_obj.completed_at = time.time()
            self.tasks[task_id] = task_obj
            self._log("task_verification_failed", task_obj.to_dict())
            return {
                "success": False,
                "error": "verification_failed",
                "task_id": task_id,
                "status": "failed",
            }

        # --- Step 5: callback & complete ---
        task_obj.status = "completed"
        task_obj.completed_at = time.time()
        task_obj.result = {
            "executed_by": to_repo,
            "latency_ms": round(latency, 2),
            "exec_time_ms": round(exec_time * 1000, 2),
            "output": {"status": "ok", "data": f"result from {to_repo}"},
        }
        target_card.task_success += 1
        self.tasks[task_id] = task_obj

        self._log("task_completed", task_obj.to_dict())

        return {
            "success": True,
            "task_id": task_id,
            "status": "completed",
            "result": task_obj.result,
            "flow": ["discover", "negotiate", "execute", "verify", "callback"],
        }

    # ------------------------------------------------------------------
    # 4. share_knowledge
    # ------------------------------------------------------------------
    def share_knowledge(
        self,
        from_repo: str,
        to_repo: str,
        knowledge: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        在仓库间共享知识。

        Knowledge types: pattern, insight, warning, opportunity
        Sharing levels: broadcast(all) · multicast(related) · unicast(specific) · private(internal)

        Args:
            from_repo: 源仓库
            to_repo: 目标仓库（可为"*"表示广播）
            knowledge: 知识字典 {type, content, sharing_level, ttl}

        Returns:
            共享结果字典
        """
        if from_repo not in self.agent_cards:
            return {
                "success": False,
                "error": f"source_repo_not_found: {from_repo}",
                "recipients": [],
            }
        if not isinstance(knowledge, dict):
            return {
                "success": False,
                "error": "invalid_knowledge_format",
                "recipients": [],
            }

        knowledge_type = knowledge.get("type", "insight")
        if knowledge_type not in KNOWLEDGE_TYPES:
            knowledge_type = "insight"

        content = knowledge.get("content", {})
        sharing_level = knowledge.get("sharing_level", "unicast")
        if sharing_level not in SHARING_LEVELS:
            sharing_level = "unicast"

        ttl = int(knowledge.get("ttl", 3))

        recipients: List[str] = []

        if sharing_level == "broadcast":
            recipients = [name for name in self.agent_cards if name != from_repo]
        elif sharing_level == "multicast":
            # Share to repos with overlapping capabilities
            source_caps = set(self.agent_cards[from_repo].capabilities)
            for name, card in self.agent_cards.items():
                if name == from_repo:
                    continue
                if source_caps & set(card.capabilities):
                    recipients.append(name)
            if not recipients:
                recipients = list(self.agent_cards.keys())
                if from_repo in recipients:
                    recipients.remove(from_repo)
        elif sharing_level == "unicast":
            if to_repo in self.agent_cards:
                recipients = [to_repo]
            elif to_repo == "*":
                recipients = [name for name in self.agent_cards if name != from_repo]
        elif sharing_level == "private":
            recipients = [from_repo]

        if sharing_level != "private" and not recipients:
            return {
                "success": False,
                "error": "no_recipients",
                "recipients": [],
            }

        packets: List[str] = []
        for recipient in recipients:
            packet_id = self._generate_packet_id()
            packet = KnowledgePacket(
                packet_id=packet_id,
                from_repo=from_repo,
                to_repo=recipient,
                knowledge_type=knowledge_type,
                content=dict(content),
                sharing_level=sharing_level,
                ttl=ttl,
            )
            self.knowledge_ledger.append(packet)
            packets.append(packet_id)

            # Update source card
            self.agent_cards[from_repo].knowledge_shared += 1
            # Update recipient last_seen
            if recipient in self.agent_cards:
                self.agent_cards[recipient].last_seen = time.time()

        self._log("knowledge_shared", {
            "from_repo": from_repo,
            "knowledge_type": knowledge_type,
            "sharing_level": sharing_level,
            "recipients": recipients,
            "packets": packets,
        })

        return {
            "success": True,
            "from_repo": from_repo,
            "recipients": recipients,
            "knowledge_type": knowledge_type,
            "sharing_level": sharing_level,
            "packet_count": len(packets),
            "packet_ids": packets,
        }

    # ------------------------------------------------------------------
    # 5. compute_federation_health
    # ------------------------------------------------------------------
    def compute_federation_health(self) -> Dict[str, Any]:
        """
        计算联邦整体健康度。

        Factors:
            - connected_nodes: 活跃节点比例
            - avg_latency: 平均通信延迟
            - task_success_rate: 任务成功率
            - knowledge_flow_rate: 知识流动速率

        Returns:
            健康度报告字典
        """
        total_nodes = len(self.agent_cards)
        if total_nodes == 0:
            return {
                "overall_score": 0.0,
                "level": "fractured",
                "factors": {},
                "recommendations": ["register_agent_cards"],
            }

        # Factor 1: connected_nodes —— 最近活跃节点比例
        now = time.time()
        active_nodes = sum(
            1 for card in self.agent_cards.values()
            if (now - card.last_seen) < 600
        )
        connected_ratio = active_nodes / total_nodes

        # Factor 2: avg_latency —— 平均延迟（越低越好）
        if self._connection_latencies:
            avg_latency = sum(self._connection_latencies.values()) / len(self._connection_latencies)
        else:
            avg_latency = 25.0
        latency_score = max(0.0, 1.0 - avg_latency / 100.0)

        # Factor 3: task_success_rate
        total_tasks = sum(card.task_count for card in self.agent_cards.values())
        total_success = sum(card.task_success for card in self.agent_cards.values())
        if total_tasks > 0:
            task_success_rate = total_success / total_tasks
        else:
            task_success_rate = 1.0  # No tasks yet = perfect

        # Factor 4: knowledge_flow_rate —— 知识包数 / 节点数 / 时间
        uptime = max(1.0, now - self.federation_state.get("started_at", now))
        knowledge_flow = len(self.knowledge_ledger) / total_nodes / uptime * 60
        knowledge_score = min(1.0, knowledge_flow)

        # Overall health score (weighted average)
        overall = (
            connected_ratio * 0.30 +
            latency_score * 0.25 +
            task_success_rate * 0.30 +
            knowledge_score * 0.15
        )

        level = self._get_health_level(overall)

        recommendations: List[str] = []
        if connected_ratio < 0.5:
            recommendations.append("increase_node_activity")
        if latency_score < 0.5:
            recommendations.append("optimize_network_latency")
        if task_success_rate < 0.7:
            recommendations.append("improve_task_reliability")
        if knowledge_score < 0.3:
            recommendations.append("increase_knowledge_sharing")
        if not recommendations:
            recommendations.append("maintain_current_state")

        self._log("health_computed", {"score": overall, "level": level})

        return {
            "overall_score": round(overall, 4),
            "level": level,
            "factors": {
                "connected_nodes": {
                    "value": round(connected_ratio, 4),
                    "active": active_nodes,
                    "total": total_nodes,
                },
                "avg_latency_ms": round(avg_latency, 2),
                "latency_score": round(latency_score, 4),
                "task_success_rate": round(task_success_rate, 4),
                "total_tasks": total_tasks,
                "total_success": total_success,
                "knowledge_flow_rate": round(knowledge_flow, 4),
                "knowledge_score": round(knowledge_score, 4),
            },
            "recommendations": recommendations,
        }

    # ------------------------------------------------------------------
    # 6. detect_federation_anomaly
    # ------------------------------------------------------------------
    def detect_federation_anomaly(self) -> Dict[str, Any]:
        """
        检测联邦异常。

        Anomaly types:
            - node_failure: 节点失联
            - communication_degradation: 通信降级
            - knowledge_stagnation: 知识停滞
            - security_breach: 安全漏洞

        Returns:
            异常检测报告
        """
        anomalies: List[Dict[str, Any]] = []
        now = time.time()
        total_nodes = len(self.agent_cards)

        if total_nodes == 0:
            return {
                "anomaly_detected": False,
                "anomaly_count": 0,
                "anomalies": [],
                "severity": "none",
                "recommendations": [],
            }

        # Check 1: node_failure
        failed_nodes: List[str] = []
        for repo_name, card in self.agent_cards.items():
            idle = now - card.last_seen
            if idle > 1200:  # > 20 min
                failed_nodes.append(repo_name)
        if failed_nodes:
            severity = "critical" if len(failed_nodes) > total_nodes * 0.3 else "warning"
            anomalies.append({
                "type": "node_failure",
                "severity": severity,
                "affected_nodes": failed_nodes,
                "description": f"{len(failed_nodes)} nodes unresponsive",
            })

        # Check 2: communication_degradation
        if self._connection_latencies:
            high_latency_pairs = [
                {"from": k[0], "to": k[1], "latency": round(v, 2)}
                for k, v in self._connection_latencies.items()
                if v > 80
            ]
            if high_latency_pairs:
                anomalies.append({
                    "type": "communication_degradation",
                    "severity": "warning",
                    "affected_pairs": high_latency_pairs,
                    "description": f"{len(high_latency_pairs)} high-latency connections",
                })

        # Check 3: knowledge_stagnation
        if self.knowledge_ledger:
            recent_knowledge = [
                p for p in self.knowledge_ledger
                if (now - p.timestamp) < 600
            ]
            if len(recent_knowledge) == 0 and len(self.knowledge_ledger) > 0:
                anomalies.append({
                    "type": "knowledge_stagnation",
                    "severity": "warning",
                    "description": "No knowledge packets in last 10 minutes",
                })
        else:
            if total_nodes > 1:
                anomalies.append({
                    "type": "knowledge_stagnation",
                    "severity": "info",
                    "description": "No knowledge sharing has occurred yet",
                })

        # Check 4: security_breach (simulated)
        failed_tasks = [
            t for t in self.tasks.values()
            if t.status == "failed"
        ]
        if len(failed_tasks) > 5:
            anomalies.append({
                "type": "security_breach",
                "severity": "critical",
                "description": f"Unusually high failure rate: {len(failed_tasks)} failed tasks",
                "failed_count": len(failed_tasks),
            })

        anomaly_detected = len(anomalies) > 0
        severity = "none"
        if any(a["severity"] == "critical" for a in anomalies):
            severity = "critical"
        elif any(a["severity"] == "warning" for a in anomalies):
            severity = "warning"
        elif any(a["severity"] == "info" for a in anomalies):
            severity = "info"

        recommendations: List[str] = []
        for a in anomalies:
            if a["type"] == "node_failure":
                recommendations.append("restart_or_replace_failed_nodes")
            elif a["type"] == "communication_degradation":
                recommendations.append("investigate_network_topology")
            elif a["type"] == "knowledge_stagnation":
                recommendations.append("trigger_knowledge_broadcast")
            elif a["type"] == "security_breach":
                recommendations.append("audit_task_execution_chain")

        report = {
            "anomaly_detected": anomaly_detected,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "severity": severity,
            "recommendations": list(set(recommendations)),
        }
        self.anomaly_history.append(report)
        self._log("anomaly_detected", report)
        return report

    # ------------------------------------------------------------------
    # 7. get_status
    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """
        获取联邦协议的当前状态快照。

        Returns:
            {
                registered_nodes: int,
                active_connections: int,
                task_count: int,
                health_score: float,
            }
        """
        now = time.time()
        registered_nodes = len(self.agent_cards)
        active_connections = sum(
            1 for card in self.agent_cards.values()
            if (now - card.last_seen) < 600
        )
        task_count = len(self.tasks)

        health = self.compute_federation_health()
        health_score = health.get("overall_score", 0.0)

        return {
            "registered_nodes": registered_nodes,
            "active_connections": active_connections,
            "task_count": task_count,
            "health_score": round(health_score, 4),
            "protocol_version": self.federation_state.get("protocol_version", "175.0"),
            "uptime_seconds": round(now - self.federation_state.get("started_at", now), 2),
            "knowledge_packets": len(self.knowledge_ledger),
            "anomalies_detected": len(self.anomaly_history),
        }


# =============================================================================
# Global Singleton
# =============================================================================
_federation_protocol: Optional[FederationProtocol] = None


def get_federation_protocol() -> FederationProtocol:
    """获取FederationProtocol全局单例。"""
    global _federation_protocol
    if _federation_protocol is None:
        _federation_protocol = FederationProtocol()
    return _federation_protocol
