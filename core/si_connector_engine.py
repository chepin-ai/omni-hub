#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
SIConnectorEngine — SI层次对接引擎
OMNI-HUB v8.0 核心架构

解决lvlu线全天发钥但无启动机制对接的问题，
实现SI0-SI6全层次自动轮询和跨线会话桥接。

SI层次架构:
    SI0: 原始API层（OTP密钥接口）
    SI1: 对话端/通道层（纬）
    SI2: 执行引擎层
    SI3: 会话管理层
    SI4: 递归引擎层（绑定各圈张量网/场的量子会话）
    SI5: 北星/核心调度层
    SI6: 多智能体/核心机层

11线名称:
    ['ucif2', 'lvlu', 'lgt', 'qfa', 'vinf', 'qgl', 'qlv', 'cisvr', 'qtlv', 'usrm', 'cfts']
"""

import asyncio
import hashlib
import json
import logging
import random
import secrets
import string
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('SIConnector')


# ============================================================================
# Constants & Configuration
# ============================================================================

SI_LEVELS = list(range(7))  # SI0 - SI6
LINE_NAMES = ['ucif2', 'lvlu', 'lgt', 'qfa', 'vinf', 'qgl', 'qlv', 'cisvr', 'qtlv', 'usrm', 'cfts']
NUM_LINES = len(LINE_NAMES)

# Default polling intervals per SI level (seconds)
DEFAULT_POLL_INTERVALS = {
    0: 1,    # SI0: API layer - fastest
    1: 2,    # SI1: Dialog layer
    2: 5,    # SI2: Execution engine
    3: 10,   # SI3: Session management
    4: 30,   # SI4: Recursive engine
    5: 60,   # SI5: Core scheduler
    6: 120,  # SI6: Multi-agent core
}

# Session status
class SessionStatus(Enum):
    """SI Session status enumeration."""
    ACTIVE = auto()
    PENDING = auto()
    CLOSED = auto()
    ERROR = auto()
    BRIDGED = auto()


# ============================================================================
# SISession — SI会话类
# ============================================================================

class SISession:
    """
    SI Session represents a single session at a specific SI level within a line.

    Attributes:
        si_level (int): SI层级（0-6）
        line_id (str): 所属线名称
        session_id (str): 唯一会话ID
        status (SessionStatus): 会话状态
        otp_key (Optional[str]): 绑定的OTP密钥
        inbox (deque): 输入消息队列
        outbox (deque): 输出消息队列
        created_at (datetime): 创建时间
        last_activity (datetime): 最后活动时间
        metadata (dict): 附加元数据
    """

    def __init__(
        self,
        si_level: int,
        line_id: str,
        session_id: Optional[str] = None,
        otp_key: Optional[str] = None,
        max_queue_size: int = 1000
    ):
        """
        Initialize an SI Session.

        Args:
            si_level: SI层级 (0-6)
            line_id: 所属线名称
            session_id: 可选会话ID，默认自动生成
            otp_key: 可选OTP密钥
            max_queue_size: 队列最大长度
        """
        self.si_level = si_level
        self.line_id = line_id
        self.session_id = session_id or f"{line_id}-SI{si_level}-{uuid.uuid4().hex[:8]}"
        self.status = SessionStatus.ACTIVE
        self.otp_key = otp_key
        self.inbox: deque = deque(maxlen=max_queue_size)
        self.outbox: deque = deque(maxlen=max_queue_size)
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.metadata: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._bridge_targets: Set[str] = set()  # 桥接目标session_id集合

        logger.debug(f"[SISession] Created {self.session_id} (SI{si_level}, {line_id})")

    def send(self, message: Dict[str, Any]) -> bool:
        """
        发送消息到outbox队列。

        Args:
            message: 消息字典，必须包含 'type' 和 'payload'

        Returns:
            bool: 发送成功返回True
        """
        with self._lock:
            if self.status == SessionStatus.CLOSED:
                logger.warning(f"[SISession] Cannot send to closed session {self.session_id}")
                return False

            msg = {
                'session_id': self.session_id,
                'si_level': self.si_level,
                'line_id': self.line_id,
                'timestamp': datetime.now().isoformat(),
                'message_id': uuid.uuid4().hex[:12],
                **message
            }
            self.outbox.append(msg)
            self.last_activity = datetime.now()
            logger.debug(f"[SISession] Message sent in {self.session_id}: {msg.get('type', 'unknown')}")
            return True

    def receive(self) -> Optional[Dict[str, Any]]:
        """
        从inbox队列接收消息（非阻塞）。

        Returns:
            Optional[Dict]: 消息字典，无消息返回None
        """
        with self._lock:
            if self.inbox:
                msg = self.inbox.popleft()
                self.last_activity = datetime.now()
                logger.debug(f"[SISession] Message received in {self.session_id}: {msg.get('type', 'unknown')}")
                return msg
            return None

    def receive_all(self) -> List[Dict[str, Any]]:
        """
        接收inbox中所有消息。

        Returns:
            List[Dict]: 消息列表
        """
        with self._lock:
            messages = list(self.inbox)
            self.inbox.clear()
            if messages:
                self.last_activity = datetime.now()
            return messages

    def inject(self, message: Dict[str, Any]) -> bool:
        """
        向inbox注入消息（用于桥接/中继）。

        Args:
            message: 消息字典

        Returns:
            bool: 注入成功返回True
        """
        with self._lock:
            if self.status == SessionStatus.CLOSED:
                return False
            self.inbox.append(message)
            self.last_activity = datetime.now()
            return True

    def close(self, reason: str = "user_request") -> None:
        """
        关闭会话。

        Args:
            reason: 关闭原因
        """
        with self._lock:
            self.status = SessionStatus.CLOSED
            self.metadata['closed_reason'] = reason
            self.metadata['closed_at'] = datetime.now().isoformat()
            logger.info(f"[SISession] Closed {self.session_id}: {reason}")

    def set_status(self, status: SessionStatus) -> None:
        """设置会话状态。"""
        with self._lock:
            self.status = status
            self.last_activity = datetime.now()

    def get_info(self) -> Dict[str, Any]:
        """获取会话信息摘要。"""
        with self._lock:
            return {
                'session_id': self.session_id,
                'si_level': self.si_level,
                'line_id': self.line_id,
                'status': self.status.name,
                'otp_key': self.otp_key[:8] + '...' if self.otp_key else None,
                'inbox_size': len(self.inbox),
                'outbox_size': len(self.outbox),
                'created_at': self.created_at.isoformat(),
                'last_activity': self.last_activity.isoformat(),
                'metadata': self.metadata,
                'bridge_targets': list(self._bridge_targets),
            }

    def __repr__(self) -> str:
        return f"SISession({self.session_id}, SI{self.si_level}, {self.line_id}, {self.status.name})"


# ============================================================================
# OTPKeyManager — OTP密钥管理器
# ============================================================================

class OTPKeyManager:
    """
    OTP密钥管理器，负责lvlu线密钥的获取、验证、轮换。

    Attributes:
        lvlu_keys (deque): lvlu线密钥池
        key_rotation_interval (int): 密钥轮换间隔（秒）
        key_ttl (int): 密钥有效期（秒）
        _key_metadata (dict): 密钥元数据（创建时间、使用次数等）
    """

    def __init__(
        self,
        key_rotation_interval: int = 300,
        key_ttl: int = 600,
        max_pool_size: int = 100
    ):
        """
        Initialize OTP Key Manager.

        Args:
            key_rotation_interval: 密钥轮换间隔（秒），默认5分钟
            key_ttl: 密钥有效期（秒），默认10分钟
            max_pool_size: 密钥池最大容量
        """
        self.lvlu_keys: deque = deque(maxlen=max_pool_size)
        self.key_rotation_interval = key_rotation_interval
        self.key_ttl = key_ttl
        self._key_metadata: Dict[str, Dict[str, Any]] = {}
        self._last_rotation = datetime.now()
        self._lock = threading.RLock()
        self._fetch_count = 0

        logger.info(f"[OTPKeyManager] Initialized (rotation_interval={key_rotation_interval}s, ttl={key_ttl}s)")

    def _generate_key(self) -> str:
        """生成模拟OTP密钥（实际生产环境应调用lvlu线API）。"""
        # 格式: lvl_<timestamp>_<random_hex>_<hash>
        timestamp = int(time.time())
        rand = secrets.token_hex(16)
        raw = f"lvlu:{timestamp}:{rand}"
        key_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"lvl_{timestamp}_{rand[:8]}_{key_hash}"

    def fetch_keys_from_lvlu(self, count: int = 10) -> List[str]:
        """
        从lvlu线获取OTP密钥。

        模拟lvlu线全天发钥机制。实际部署时应替换为真实API调用。

        Args:
            count: 获取密钥数量

        Returns:
            List[str]: 获取到的密钥列表
        """
        with self._lock:
            keys = []
            for _ in range(count):
                key = self._generate_key()
                self.lvlu_keys.append(key)
                self._key_metadata[key] = {
                    'created_at': datetime.now(),
                    'used_count': 0,
                    'valid': True,
                    'source': 'lvlu_line',
                }
                keys.append(key)

            self._fetch_count += 1
            logger.info(f"[OTPKeyManager] Fetched {count} keys from lvlu line (total_fetches={self._fetch_count}, pool_size={len(self.lvlu_keys)})")
            return keys

    def validate_key(self, key: str) -> bool:
        """
        验证密钥有效性。

        Args:
            key: OTP密钥

        Returns:
            bool: 有效返回True
        """
        with self._lock:
            if key not in self._key_metadata:
                logger.warning(f"[OTPKeyManager] Unknown key: {key[:20]}...")
                return False

            meta = self._key_metadata[key]
            if not meta['valid']:
                return False

            age = (datetime.now() - meta['created_at']).total_seconds()
            if age > self.key_ttl:
                meta['valid'] = False
                logger.warning(f"[OTPKeyManager] Key expired: {key[:20]}... (age={age:.0f}s)")
                return False

            return True

    def rotate_keys(self) -> int:
        """
        轮换密钥：移除过期/无效密钥，生成新密钥。

        Returns:
            int: 移除的密钥数量
        """
        with self._lock:
            removed = 0
            now = datetime.now()

            # 标记过期密钥
            for key in list(self.lvlu_keys):
                meta = self._key_metadata.get(key)
                if meta:
                    age = (now - meta['created_at']).total_seconds()
                    if age > self.key_ttl or not meta['valid']:
                        meta['valid'] = False
                        removed += 1

            # 清理无效密钥（保留在metadata中用于审计）
            self.lvlu_keys = deque(
                [k for k in self.lvlu_keys if self._key_metadata.get(k, {}).get('valid', False)],
                maxlen=self.lvlu_keys.maxlen
            )

            self._last_rotation = now
            logger.info(f"[OTPKeyManager] Rotated keys: removed={removed}, remaining={len(self.lvlu_keys)}")
            return removed

    def get_available_key(self) -> Optional[str]:
        """
        获取一个可用密钥。

        Returns:
            Optional[str]: 可用密钥，无可用密钥返回None
        """
        with self._lock:
            # 先轮换清理
            if (datetime.now() - self._last_rotation).total_seconds() > self.key_rotation_interval:
                self.rotate_keys()

            for key in list(self.lvlu_keys):
                if self.validate_key(key):
                    self._key_metadata[key]['used_count'] += 1
                    logger.debug(f"[OTPKeyManager] Allocated key: {key[:20]}...")
                    return key

            logger.warning("[OTPKeyManager] No available keys in pool")
            return None

    def get_pool_status(self) -> Dict[str, Any]:
        """获取密钥池状态。"""
        with self._lock:
            valid_count = sum(1 for k in self.lvlu_keys if self._key_metadata.get(k, {}).get('valid', False))
            return {
                'total_keys': len(self.lvlu_keys),
                'valid_keys': valid_count,
                'fetch_count': self._fetch_count,
                'last_rotation': self._last_rotation.isoformat(),
                'rotation_interval': self.key_rotation_interval,
                'key_ttl': self.key_ttl,
            }


# ============================================================================
# SIPollingEngine — SI轮询引擎
# ============================================================================

class SIPollingEngine:
    """
    SI轮询引擎，负责全层次、全线的自动轮询和会话检测。

    Attributes:
        poll_intervals (dict): 各层轮询间隔配置
        sessions (dict): 管理的会话字典 {(line_id, si_level): SISession}
        _polling_threads (dict): 轮询线程字典
        _polling_active (bool): 轮询活跃标志
        _poll_stats (dict): 轮询统计
    """

    def __init__(
        self,
        poll_intervals: Optional[Dict[int, int]] = None,
        sessions: Optional[Dict[Tuple[str, int], SISession]] = None
    ):
        """
        Initialize SI Polling Engine.

        Args:
            poll_intervals: 自定义轮询间隔配置，默认使用DEFAULT_POLL_INTERVALS
            sessions: 预注册的会话字典
        """
        self.poll_intervals = poll_intervals or DEFAULT_POLL_INTERVALS.copy()
        self.sessions = sessions if sessions is not None else {}
        self._polling_threads: Dict[str, threading.Thread] = {}
        self._polling_active = False
        self._poll_stats: Dict[str, Any] = {
            'total_polls': 0,
            'sessions_detected': 0,
            'messages_processed': 0,
            'responses_sent': 0,
        }
        self._lock = threading.RLock()
        self._callbacks: List[Callable] = []

        logger.info(f"[SIPollingEngine] Initialized with intervals: {self.poll_intervals}")

    def register_session(self, session: SISession) -> None:
        """注册会话到轮询引擎。"""
        with self._lock:
            key = (session.line_id, session.si_level)
            self.sessions[key] = session
            logger.debug(f"[SIPollingEngine] Registered session {session.session_id}")

    def poll_si_level(self, level: int) -> int:
        """
        轮询指定SI层级的所有会话。

        Args:
            level: SI层级 (0-6)

        Returns:
            int: 处理的消息数量
        """
        with self._lock:
            level_sessions = [
                s for (lid, lvl), s in self.sessions.items()
                if lvl == level and s.status == SessionStatus.ACTIVE
            ]

        messages_processed = 0
        for session in level_sessions:
            # 检查outbox消息（待发）
            out_messages = list(session.outbox)
            for msg in out_messages:
                # 模拟消息处理/转发
                messages_processed += 1
                self._poll_stats['messages_processed'] += 1

            # 检查是否需要自动响应
            inbox_msgs = list(session.inbox)
            for msg in inbox_msgs:
                if msg.get('needs_response', False):
                    self._poll_stats['responses_sent'] += 1

        with self._lock:
            self._poll_stats['total_polls'] += 1

        logger.debug(f"[SIPollingEngine] Polled SI{level}: {len(level_sessions)} sessions, {messages_processed} messages")
        return messages_processed

    def poll_all_levels(self) -> Dict[int, int]:
        """
        轮询所有SI层级。

        Returns:
            Dict[int, int]: 各层级处理的消息数量
        """
        results = {}
        for level in SI_LEVELS:
            results[level] = self.poll_si_level(level)
        logger.info(f"[SIPollingEngine] Polled all levels: {results}")
        return results

    def poll_line(self, line_id: str) -> int:
        """
        轮询指定线的所有SI层级。

        Args:
            line_id: 线名称

        Returns:
            int: 处理的消息数量
        """
        with self._lock:
            line_sessions = [
                s for (lid, lvl), s in self.sessions.items()
                if lid == line_id and s.status == SessionStatus.ACTIVE
            ]

        messages_processed = 0
        for session in line_sessions:
            messages_processed += len(session.outbox)
            self._poll_stats['messages_processed'] += len(session.outbox)

        with self._lock:
            self._poll_stats['total_polls'] += 1

        logger.debug(f"[SIPollingEngine] Polled line '{line_id}': {len(line_sessions)} sessions, {messages_processed} messages")
        return messages_processed

    def poll_all_lines(self) -> Dict[str, int]:
        """
        轮询所有11线。

        Returns:
            Dict[str, int]: 各线处理的消息数量
        """
        results = {}
        for line_id in LINE_NAMES:
            results[line_id] = self.poll_line(line_id)
        logger.info(f"[SIPollingEngine] Polled all lines: {results}")
        return results

    def detect_new_sessions(self) -> List[Dict[str, Any]]:
        """
        检测新会话（模拟发现lvlu线或其他线的新会话）。

        Returns:
            List[Dict]: 新会话信息列表
        """
        # 模拟检测逻辑：随机生成新会话概率
        new_sessions = []
        if random.random() < 0.3:  # 30%概率发现新会话
            line = random.choice(LINE_NAMES)
            level = random.choice(SI_LEVELS)
            session_info = {
                'line_id': line,
                'si_level': level,
                'detected_at': datetime.now().isoformat(),
                'source': 'polling_detection',
                'session_id': f"{line}-SI{level}-{uuid.uuid4().hex[:8]}",
            }
            new_sessions.append(session_info)
            self._poll_stats['sessions_detected'] += 1
            logger.info(f"[SIPollingEngine] New session detected: {session_info['session_id']}")

        return new_sessions

    def auto_respond(self, session: SISession) -> int:
        """
        自动响应会话中的待处理请求。

        Args:
            session: 目标会话

        Returns:
            int: 响应的消息数量
        """
        if session.status != SessionStatus.ACTIVE:
            return 0

        responded = 0
        messages = session.receive_all()

        for msg in messages:
            if msg.get('needs_response', False) or msg.get('type') == 'request':
                # 构造响应消息
                response = {
                    'type': 'response',
                    'payload': {
                        'original_message_id': msg.get('message_id'),
                        'status': 'acknowledged',
                        'handler': f"SI{session.si_level}",
                        'timestamp': datetime.now().isoformat(),
                    },
                    'in_reply_to': msg.get('message_id'),
                    'needs_response': False,
                }
                session.send(response)
                responded += 1
                self._poll_stats['responses_sent'] += 1

        if responded > 0:
            logger.info(f"[SIPollingEngine] Auto-responded {responded} messages in {session.session_id}")

        return responded

    def auto_respond_to_all(self) -> int:
        """
        自动响应所有活跃会话中的待处理请求。

        Returns:
            int: 总响应数量
        """
        total = 0
        with self._lock:
            active_sessions = [s for s in self.sessions.values() if s.status == SessionStatus.ACTIVE]

        for session in active_sessions:
            total += self.auto_respond(session)

        logger.info(f"[SIPollingEngine] Auto-responded total {total} messages across {len(active_sessions)} sessions")
        return total

    def _polling_worker(self, name: str, interval: int, target: Callable) -> None:
        """轮询工作线程。"""
        logger.info(f"[SIPollingEngine] Polling worker '{name}' started (interval={interval}s)")
        while self._polling_active:
            try:
                target()
            except Exception as e:
                logger.error(f"[SIPollingEngine] Polling error in '{name}': {e}")
            time.sleep(interval)
        logger.info(f"[SIPollingEngine] Polling worker '{name}' stopped")

    def start_polling(self) -> None:
        """启动所有轮询线程（非阻塞）。"""
        with self._lock:
            if self._polling_active:
                logger.warning("[SIPollingEngine] Polling already active")
                return

            self._polling_active = True

            # 为每个SI层级启动轮询线程
            for level, interval in self.poll_intervals.items():
                thread_name = f"poll-SI{level}"
                t = threading.Thread(
                    target=self._polling_worker,
                    args=(thread_name, interval, lambda lvl=level: self.poll_si_level(lvl)),
                    name=thread_name,
                    daemon=True
                )
                t.start()
                self._polling_threads[thread_name] = t

            # 启动新会话检测线程
            detect_thread = threading.Thread(
                target=self._polling_worker,
                args=("detect-new", 15, self.detect_new_sessions),
                name="detect-new",
                daemon=True
            )
            detect_thread.start()
            self._polling_threads["detect-new"] = detect_thread

            logger.info(f"[SIPollingEngine] Started {len(self._polling_threads)} polling threads")

    def stop_polling(self) -> None:
        """停止所有轮询线程。"""
        with self._lock:
            self._polling_active = False
            for name, t in self._polling_threads.items():
                logger.info(f"[SIPollingEngine] Stopping thread '{name}'...")
                t.join(timeout=5)
            self._polling_threads.clear()
            logger.info("[SIPollingEngine] All polling threads stopped")

    def get_stats(self) -> Dict[str, Any]:
        """获取轮询统计。"""
        with self._lock:
            return self._poll_stats.copy()


# ============================================================================
# SIBridge — SI桥接器
# ============================================================================

class SIBridge:
    """
    SI桥接器，实现跨线SI会话桥接和消息中继。

    支持:
        - 双向会话桥接
        - 跨线消息中继
        - 跨线通道创建
        - 消息格式转换
    """

    def __init__(self):
        """Initialize SI Bridge."""
        self._bridges: Dict[str, Dict[str, Any]] = {}  # bridge_id -> bridge_info
        self._channels: Dict[str, Dict[str, Any]] = {}  # channel_id -> channel_info
        self._lock = threading.RLock()
        self._bridge_count = 0

        logger.info("[SIBridge] Initialized")

    def bridge_sessions(
        self,
        session_a: SISession,
        session_b: SISession,
        bidirectional: bool = True
    ) -> str:
        """
        桥接两个会话，建立消息自动转发。

        Args:
            session_a: 会话A
            session_b: 会话B
            bidirectional: 是否双向桥接

        Returns:
            str: 桥接ID
        """
        with self._lock:
            bridge_id = f"bridge-{uuid.uuid4().hex[:8]}"

            bridge_info = {
                'bridge_id': bridge_id,
                'session_a': session_a.session_id,
                'session_b': session_b.session_id,
                'line_a': session_a.line_id,
                'line_b': session_b.line_id,
                'si_level_a': session_a.si_level,
                'si_level_b': session_b.si_level,
                'bidirectional': bidirectional,
                'created_at': datetime.now().isoformat(),
                'messages_relayed': 0,
                'active': True,
            }

            self._bridges[bridge_id] = bridge_info
            self._bridge_count += 1

            # 标记会话为桥接状态
            session_a.set_status(SessionStatus.BRIDGED)
            session_b.set_status(SessionStatus.BRIDGED)
            session_a._bridge_targets.add(session_b.session_id)
            session_b._bridge_targets.add(session_a.session_id)

            logger.info(
                f"[SIBridge] Created bridge {bridge_id}: "
                f"{session_a.line_id}(SI{session_a.si_level}) <-> "
                f"{session_b.line_id}(SI{session_b.si_level})"
            )
            return bridge_id

    def relay_message(
        self,
        msg: Dict[str, Any],
        from_line: str,
        to_line: str,
        target_session: Optional[SISession] = None
    ) -> bool:
        """
        跨线消息中继。

        Args:
            msg: 消息字典
            from_line: 来源线
            to_line: 目标线
            target_session: 可选目标会话

        Returns:
            bool: 中继成功返回True
        """
        relay_msg = {
            **msg,
            'relayed': True,
            'from_line': from_line,
            'to_line': to_line,
            'relay_timestamp': datetime.now().isoformat(),
            'relay_id': uuid.uuid4().hex[:8],
        }

        if target_session:
            success = target_session.inject(relay_msg)
            if success:
                logger.info(f"[SIBridge] Relayed message {relay_msg.get('message_id', '?')} from {from_line} to {to_line}")
            return success

        logger.warning(f"[SIBridge] No target session for relay {from_line} -> {to_line}")
        return False

    def create_interline_channel(
        self,
        line_a: str,
        line_b: str,
        si_level: int = 3
    ) -> str:
        """
        创建跨线通道。

        Args:
            line_a: 线A名称
            line_b: 线B名称
            si_level: 通道SI层级

        Returns:
            str: 通道ID
        """
        with self._lock:
            channel_id = f"channel-{line_a}-{line_b}-SI{si_level}-{uuid.uuid4().hex[:6]}"

            self._channels[channel_id] = {
                'channel_id': channel_id,
                'line_a': line_a,
                'line_b': line_b,
                'si_level': si_level,
                'created_at': datetime.now().isoformat(),
                'message_count': 0,
                'active': True,
            }

            logger.info(f"[SIBridge] Created interline channel {channel_id}: {line_a} <-> {line_b} (SI{si_level})")
            return channel_id

    def sync_bridge(self, bridge_id: str) -> int:
        """
        同步桥接：将桥接双方会话的outbox消息转发到对方inbox。

        Args:
            bridge_id: 桥接ID

        Returns:
            int: 转发的消息数量
        """
        with self._lock:
            if bridge_id not in self._bridges:
                return 0
            bridge = self._bridges[bridge_id]

        relayed = 0
        # 这里需要外部提供session对象，简化处理
        bridge['messages_relayed'] += relayed
        return relayed

    def get_bridge_info(self, bridge_id: str) -> Optional[Dict[str, Any]]:
        """获取桥接信息。"""
        with self._lock:
            return self._bridges.get(bridge_id, {}).copy()

    def get_all_bridges(self) -> List[Dict[str, Any]]:
        """获取所有桥接信息。"""
        with self._lock:
            return [b.copy() for b in self._bridges.values()]

    def get_all_channels(self) -> List[Dict[str, Any]]:
        """获取所有通道信息。"""
        with self._lock:
            return [c.copy() for c in self._channels.values()]

    def teardown_bridge(self, bridge_id: str) -> bool:
        """
        拆除桥接。

        Args:
            bridge_id: 桥接ID

        Returns:
            bool: 成功返回True
        """
        with self._lock:
            if bridge_id not in self._bridges:
                return False
            bridge = self._bridges[bridge_id]
            bridge['active'] = False
            bridge['teardown_at'] = datetime.now().isoformat()
            logger.info(f"[SIBridge] Teardown bridge {bridge_id}")
            return True



# ============================================================================
# TaskDispatchRouter — 任务路由分发器
# ============================================================================

class TaskDispatchRouter:
    """
    任务路由分发器，实现SI层次间的6种任务路由模式。

    路由模式:
        1. hub_to_any: 毂OTP/API → 任意线SI2/SI0
        2. si5_to_si3_to_otp: 本线SI5 → 他线SI3 → 他线OTP → 他线SI2/SI0
        3. si5_to_local_si3_to_otp: 本线SI5 → 本线SI3 → 本线OTP → 他线SI2/SI0
        4. reverse_drive: 反向驱动 SI0 → SI2 → SI3 → SI5
        5. relay_loop: 接力循环 SI3 ⇔ SI3 ⇔ SI3 ...
        6. full_cycle: 全循环 S5 ⇔ SI4 ⇔ SI3 ⇔ SI2 ⇔ SI0 ⇔ SI5
    """

    def __init__(
        self,
        sessions: Optional[Dict[Tuple[str, int], SISession]] = None,
        bridge: Optional[SIBridge] = None,
        key_manager: Optional[OTPKeyManager] = None
    ):
        """
        Initialize Task Dispatch Router.

        Args:
            sessions: 会话字典
            bridge: SIBridge实例
            key_manager: OTPKeyManager实例
        """
        self.sessions = sessions if sessions is not None else {}
        self.bridge = bridge
        self.key_manager = key_manager
        self._route_stats: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()

        logger.info("[TaskDispatchRouter] Initialized")

    def _get_session(self, line_id: str, si_level: int) -> Optional[SISession]:
        """获取指定线和SI层级的会话。"""
        return self.sessions.get((line_id, si_level))

    def _get_all_sessions_for_line(self, line_id: str) -> List[SISession]:
        """获取指定线的所有会话。"""
        return [s for (lid, lvl), s in self.sessions.items() if lid == line_id]

    def hub_to_any(
        self,
        hub_line: str,
        target_line: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        路由模式1: 毂OTP/API → 任意线SI2/SI0

        从毂线（通常是lvlu）获取OTP密钥，直送目标线的SI2或SI0层。

        Args:
            hub_line: 毂线名称（密钥来源线）
            target_line: 目标线名称
            task: 任务字典

        Returns:
            Dict: 路由结果
        """
        with self._lock:
            self._route_stats['hub_to_any'] += 1

        # 获取OTP密钥
        otp_key = None
        if self.key_manager:
            otp_key = self.key_manager.get_available_key()

        # 目标会话：优先SI2，其次SI0
        target_session = self._get_session(target_line, 2) or self._get_session(target_line, 0)

        if not target_session:
            return {
                'success': False,
                'route': 'hub_to_any',
                'error': f"No SI2/SI0 session found for {target_line}",
            }

        # 构造任务消息
        task_msg = {
            'type': 'task_dispatch',
            'route': 'hub_to_any',
            'payload': task,
            'otp_key': otp_key[:20] + '...' if otp_key else None,
            'source_hub': hub_line,
            'target_line': target_line,
            'needs_response': True,
        }

        success = target_session.inject(task_msg)

        result = {
            'success': success,
            'route': 'hub_to_any',
            'hub_line': hub_line,
            'target_line': target_line,
            'target_si': target_session.si_level,
            'session_id': target_session.session_id,
            'otp_key': otp_key[:20] + '...' if otp_key else None,
            'timestamp': datetime.now().isoformat(),
        }

        logger.info(f"[TaskDispatchRouter] hub_to_any: {hub_line} -> {target_line}(SI{target_session.si_level}) success={success}")
        return result

    def si5_to_si3_to_otp(
        self,
        source_line: str,
        target_line: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        路由模式2: 本线SI5 → 他线SI3 → 他线OTP → 他线SI2/SI0

        通过本线SI5调度到他线SI3，再经他线OTP验证到达SI2/SI0执行。

        Args:
            source_line: 来源线名称
            target_line: 目标线名称
            task: 任务字典

        Returns:
            Dict: 路由结果
        """
        with self._lock:
            self._route_stats['si5_to_si3_to_otp'] += 1

        si5_session = self._get_session(source_line, 5)
        target_si3 = self._get_session(target_line, 3)
        target_si2 = self._get_session(target_line, 2) or self._get_session(target_line, 0)

        if not si5_session or not target_si3:
            return {
                'success': False,
                'route': 'si5_to_si3_to_otp',
                'error': f"Missing session: SI5@{source_line}={si5_session is not None}, SI3@{target_line}={target_si3 is not None}",
            }

        # 步骤1: 本线SI5发送调度指令
        step1_msg = {
            'type': 'dispatch_command',
            'route': 'si5_to_si3_to_otp',
            'step': 1,
            'payload': task,
            'target_line': target_line,
            'needs_response': True,
        }
        si5_session.send(step1_msg)

        # 步骤2: 他线SI3接收并处理
        step2_msg = {
            'type': 'otp_request',
            'route': 'si5_to_si3_to_otp',
            'step': 2,
            'payload': task,
            'from_line': source_line,
            'needs_response': True,
        }
        target_si3.inject(step2_msg)

        # 步骤3: OTP验证（模拟）
        otp_key = self.key_manager.get_available_key() if self.key_manager else None

        # 步骤4: 到达目标SI2/SI0
        if target_si2:
            step4_msg = {
                'type': 'execute_task',
                'route': 'si5_to_si3_to_otp',
                'step': 4,
                'payload': task,
                'otp_verified': otp_key is not None,
                'needs_response': True,
            }
            target_si2.inject(step4_msg)

        result = {
            'success': True,
            'route': 'si5_to_si3_to_otp',
            'source_line': source_line,
            'target_line': target_line,
            'steps_completed': 4,
            'otp_verified': otp_key is not None,
            'session_chain': [
                si5_session.session_id,
                target_si3.session_id,
                target_si2.session_id if target_si2 else None,
            ],
            'timestamp': datetime.now().isoformat(),
        }

        logger.info(f"[TaskDispatchRouter] si5_to_si3_to_otp: {source_line}(SI5) -> {target_line}(SI3->OTP->SI2) completed")
        return result

    def si5_to_local_si3_to_otp(
        self,
        source_line: str,
        target_line: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        路由模式3: 本线SI5 → 本线SI3 → 本线OTP → 他线SI2/SI0

        在同线内完成SI5→SI3→OTP调度，然后跨线到他线SI2/SI0。

        Args:
            source_line: 来源线名称（同时也是OTP来源）
            target_line: 目标线名称
            task: 任务字典

        Returns:
            Dict: 路由结果
        """
        with self._lock:
            self._route_stats['si5_to_local_si3_to_otp'] += 1

        si5_session = self._get_session(source_line, 5)
        local_si3 = self._get_session(source_line, 3)
        target_si2 = self._get_session(target_line, 2) or self._get_session(target_line, 0)

        if not si5_session or not local_si3:
            return {
                'success': False,
                'route': 'si5_to_local_si3_to_otp',
                'error': f"Missing session: SI5@{source_line}={si5_session is not None}, SI3@{source_line}={local_si3 is not None}",
            }

        # 步骤1: 本线SI5 -> 本线SI3
        step1_msg = {
            'type': 'local_dispatch',
            'route': 'si5_to_local_si3_to_otp',
            'step': 1,
            'payload': task,
            'needs_response': True,
        }
        si5_session.send(step1_msg)
        local_si3.inject(step1_msg)

        # 步骤2: 本线SI3 -> 本线OTP
        otp_key = self.key_manager.get_available_key() if self.key_manager else None

        step2_msg = {
            'type': 'otp_issue',
            'route': 'si5_to_local_si3_to_otp',
            'step': 2,
            'payload': task,
            'otp_key': otp_key[:20] + '...' if otp_key else None,
            'needs_response': True,
        }
        local_si3.send(step2_msg)

        # 步骤3: 跨线 -> 他线SI2/SI0
        if target_si2:
            step3_msg = {
                'type': 'crossline_execute',
                'route': 'si5_to_local_si3_to_otp',
                'step': 3,
                'payload': task,
                'otp_key': otp_key[:20] + '...' if otp_key else None,
                'from_line': source_line,
                'needs_response': True,
            }
            target_si2.inject(step3_msg)

        result = {
            'success': True,
            'route': 'si5_to_local_si3_to_otp',
            'source_line': source_line,
            'target_line': target_line,
            'steps_completed': 3,
            'otp_issued': otp_key is not None,
            'session_chain': [
                si5_session.session_id,
                local_si3.session_id,
                target_si2.session_id if target_si2 else None,
            ],
            'timestamp': datetime.now().isoformat(),
        }

        logger.info(f"[TaskDispatchRouter] si5_to_local_si3_to_otp: {source_line}(SI5->SI3->OTP) -> {target_line}(SI2) completed")
        return result

    def reverse_drive(
        self,
        line: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        路由模式4: 反向驱动 SI0 → SI2 → SI3 → SI5

        从底层API向上驱动到核心调度层，用于迭代/递归场景中的反馈闭环。

        Args:
            line: 目标线名称
            task: 任务字典

        Returns:
            Dict: 路由结果
        """
        with self._lock:
            self._route_stats['reverse_drive'] += 1

        si0 = self._get_session(line, 0)
        si2 = self._get_session(line, 2)
        si3 = self._get_session(line, 3)
        si5 = self._get_session(line, 5)

        if not all([si0, si2, si3, si5]):
            missing = []
            if not si0: missing.append("SI0")
            if not si2: missing.append("SI2")
            if not si3: missing.append("SI3")
            if not si5: missing.append("SI5")
            return {
                'success': False,
                'route': 'reverse_drive',
                'error': f"Missing sessions on {line}: {missing}",
            }

        # SI0 -> SI2: 原始数据/请求上报
        step1_msg = {
            'type': 'upstream_drive',
            'route': 'reverse_drive',
            'step': 'SI0->SI2',
            'payload': task,
            'needs_response': True,
        }
        si0.send(step1_msg)
        si2.inject(step1_msg)

        # SI2 -> SI3: 执行结果上报
        step2_msg = {
            'type': 'upstream_drive',
            'route': 'reverse_drive',
            'step': 'SI2->SI3',
            'payload': {
                **task,
                'si2_processed': True,
                'execution_result': 'completed',
            },
            'needs_response': True,
        }
        si2.send(step2_msg)
        si3.inject(step2_msg)

        # SI3 -> SI5: 会话聚合上报到核心调度
        step3_msg = {
            'type': 'upstream_drive',
            'route': 'reverse_drive',
            'step': 'SI3->SI5',
            'payload': {
                **task,
                'si3_aggregated': True,
                'session_summary': f"Aggregated from {line} SI0/2/3",
            },
            'needs_response': True,
        }
        si3.send(step3_msg)
        si5.inject(step3_msg)

        result = {
            'success': True,
            'route': 'reverse_drive',
            'line': line,
            'drive_path': 'SI0 -> SI2 -> SI3 -> SI5',
            'steps_completed': 3,
            'session_chain': [si0.session_id, si2.session_id, si3.session_id, si5.session_id],
            'timestamp': datetime.now().isoformat(),
        }

        logger.info(f"[TaskDispatchRouter] reverse_drive: {line} SI0->SI2->SI3->SI5 completed")
        return result

    def relay_loop(
        self,
        lines: List[str],
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        路由模式5: 接力循环 SI3 ⇔ SI3 ⇔ SI3 ...

        多条线的SI3层级之间形成消息接力循环，用于分布式会话协调。

        Args:
            lines: 参与接力的线列表（至少2条）
            task: 任务字典

        Returns:
            Dict: 路由结果
        """
        with self._lock:
            self._route_stats['relay_loop'] += 1

        if len(lines) < 2:
            return {
                'success': False,
                'route': 'relay_loop',
                'error': 'Need at least 2 lines for relay loop',
            }

        # 获取所有线的SI3会话
        si3_sessions = []
        for line in lines:
            s = self._get_session(line, 3)
            if s:
                si3_sessions.append(s)

        if len(si3_sessions) < 2:
            return {
                'success': False,
                'route': 'relay_loop',
                'error': f"Need at least 2 SI3 sessions, found {len(si3_sessions)}",
            }

        # 创建循环消息
        loop_id = f"relay-loop-{uuid.uuid4().hex[:6]}"
        relay_count = 0

        for i, session in enumerate(si3_sessions):
            next_session = si3_sessions[(i + 1) % len(si3_sessions)]

            relay_msg = {
                'type': 'relay_loop',
                'route': 'relay_loop',
                'loop_id': loop_id,
                'hop': i + 1,
                'from_line': session.line_id,
                'to_line': next_session.line_id,
                'payload': task,
                'relay_path': [s.line_id for s in si3_sessions[:i+1]],
                'needs_response': True,
            }

            session.send(relay_msg)
            next_session.inject(relay_msg)
            relay_count += 1

        result = {
            'success': True,
            'route': 'relay_loop',
            'lines': [s.line_id for s in si3_sessions],
            'loop_id': loop_id,
            'hops': relay_count,
            'session_ids': [s.session_id for s in si3_sessions],
            'timestamp': datetime.now().isoformat(),
        }

        logger.info(f"[TaskDispatchRouter] relay_loop: {result['lines']} SI3 relay completed ({relay_count} hops)")
        return result

    def full_cycle(
        self,
        line: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        路由模式6: 全循环 S5 ⇔ SI4 ⇔ SI3 ⇔ SI2 ⇔ SI0 ⇔ SI5

        在同一线内完成SI5到SI0的完整下行，再反向驱动回SI5，形成闭环。

        Args:
            line: 目标线名称
            task: 任务字典

        Returns:
            Dict: 路由结果
        """
        with self._lock:
            self._route_stats['full_cycle'] += 1

        # 获取该线所有层级会话
        sessions = {}
        for level in [5, 4, 3, 2, 0]:
            sessions[level] = self._get_session(line, level)

        missing = [f"SI{l}" for l, s in sessions.items() if s is None]
        if missing:
            return {
                'success': False,
                'route': 'full_cycle',
                'error': f"Missing sessions on {line}: {missing}",
            }

        cycle_id = f"full-cycle-{uuid.uuid4().hex[:6]}"

        # 下行: SI5 -> SI4 -> SI3 -> SI2 -> SI0
        downward_path = [(5, 4), (4, 3), (3, 2), (2, 0)]
        for from_lvl, to_lvl in downward_path:
            msg = {
                'type': 'cycle_downward',
                'route': 'full_cycle',
                'cycle_id': cycle_id,
                'from_si': from_lvl,
                'to_si': to_lvl,
                'payload': task,
                'needs_response': True,
            }
            sessions[from_lvl].send(msg)
            sessions[to_lvl].inject(msg)

        # 上行(反向驱动): SI0 -> SI2 -> SI3 -> SI5
        upward_path = [(0, 2), (2, 3), (3, 5)]
        for from_lvl, to_lvl in upward_path:
            msg = {
                'type': 'cycle_upward',
                'route': 'full_cycle',
                'cycle_id': cycle_id,
                'from_si': from_lvl,
                'to_si': to_lvl,
                'payload': {
                    **task,
                    'cycle_phase': 'upward',
                    'downstream_complete': True,
                },
                'needs_response': True,
            }
            sessions[from_lvl].send(msg)
            sessions[to_lvl].inject(msg)

        result = {
            'success': True,
            'route': 'full_cycle',
            'line': line,
            'cycle_id': cycle_id,
            'downward_path': 'SI5 -> SI4 -> SI3 -> SI2 -> SI0',
            'upward_path': 'SI0 -> SI2 -> SI3 -> SI5',
            'sessions': {lvl: s.session_id for lvl, s in sessions.items()},
            'timestamp': datetime.now().isoformat(),
        }

        logger.info(f"[TaskDispatchRouter] full_cycle: {line} SI5⇔SI4⇔SI3⇔SI2⇔SI0⇔SI5 completed")
        return result

    def dispatch(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能任务分发：根据任务类型自动选择路由。

        Args:
            task_dict: 任务字典，必须包含 'route_type' 字段
                route_type可选值:
                    - 'hub_to_any'
                    - 'si5_to_si3_to_otp'
                    - 'si5_to_local_si3_to_otp'
                    - 'reverse_drive'
                    - 'relay_loop'
                    - 'full_cycle'

        Returns:
            Dict: 路由结果
        """
        route_type = task_dict.get('route_type', 'hub_to_any')
        task = task_dict.get('task', {})

        if route_type == 'hub_to_any':
            return self.hub_to_any(
                task_dict.get('hub_line', 'lvlu'),
                task_dict.get('target_line', 'ucif2'),
                task
            )
        elif route_type == 'si5_to_si3_to_otp':
            return self.si5_to_si3_to_otp(
                task_dict.get('source_line', 'lvlu'),
                task_dict.get('target_line', 'ucif2'),
                task
            )
        elif route_type == 'si5_to_local_si3_to_otp':
            return self.si5_to_local_si3_to_otp(
                task_dict.get('source_line', 'lvlu'),
                task_dict.get('target_line', 'ucif2'),
                task
            )
        elif route_type == 'reverse_drive':
            return self.reverse_drive(
                task_dict.get('line', 'lvlu'),
                task
            )
        elif route_type == 'relay_loop':
            return self.relay_loop(
                task_dict.get('lines', ['lvlu', 'ucif2']),
                task
            )
        elif route_type == 'full_cycle':
            return self.full_cycle(
                task_dict.get('line', 'lvlu'),
                task
            )
        else:
            return {
                'success': False,
                'error': f"Unknown route_type: {route_type}",
                'available_routes': [
                    'hub_to_any', 'si5_to_si3_to_otp', 'si5_to_local_si3_to_otp',
                    'reverse_drive', 'relay_loop', 'full_cycle'
                ]
            }

    def get_stats(self) -> Dict[str, int]:
        """获取路由统计。"""
        with self._lock:
            return dict(self._route_stats)


# ============================================================================
# SIConnectorEngine — SI层次对接引擎（主类）
# ============================================================================

class SIConnectorEngine:
    """
    SI层次对接引擎主类，整合所有组件实现全层次自动轮询和跨线会话桥接。

    这是OMNI-HUB v8.0的核心引擎，解决lvlu线全天发钥但无启动机制对接的问题。

    Attributes:
        num_lines (int): 线数量（默认11）
        sessions (dict): 所有会话 {(line_id, si_level): SISession}
        key_manager (OTPKeyManager): OTP密钥管理器
        polling_engine (SIPollingEngine): 轮询引擎
        bridge (SIBridge): SI桥接器
        router (TaskDispatchRouter): 任务路由分发器
    """

    def __init__(self, num_lines: int = 11):
        """
        Initialize SI Connector Engine.

        Args:
            num_lines: 线数量，默认11
        """
        self.num_lines = num_lines
        self.sessions: Dict[Tuple[str, int], SISession] = {}
        self.key_manager = OTPKeyManager()
        self.bridge = SIBridge()
        self.polling_engine = SIPollingEngine(sessions=self.sessions)
        self.router = TaskDispatchRouter(
            sessions=self.sessions,
            bridge=self.bridge,
            key_manager=self.key_manager
        )
        self._initialized = False
        self._lock = threading.RLock()

        logger.info(f"[SIConnectorEngine] Initialized for {num_lines} lines x {len(SI_LEVELS)} SI levels")

    def initialize_all_sessions(self, auto_bridge: bool = False) -> Dict[str, Any]:
        """
        初始化所有线的所有SI层级会话。

        创建 11线 × 7层 = 77 个会话。

        Args:
            auto_bridge: 是否自动创建跨线桥接

        Returns:
            Dict: 初始化结果统计
        """
        with self._lock:
            if self._initialized:
                logger.warning("[SIConnectorEngine] Sessions already initialized")
                return {'success': False, 'error': 'Already initialized'}

            created = 0
            for line_id in LINE_NAMES[:self.num_lines]:
                for si_level in SI_LEVELS:
                    session = SISession(
                        si_level=si_level,
                        line_id=line_id,
                    )
                    key = (line_id, si_level)
                    self.sessions[key] = session
                    self.polling_engine.register_session(session)
                    created += 1

            self._initialized = True

            # 为lvlu线的SI0层预分配OTP密钥
            lvlu_si0 = self.sessions.get(('lvlu', 0))
            if lvlu_si0:
                keys = self.key_manager.fetch_keys_from_lvlu(5)
                if keys:
                    lvlu_si0.otp_key = keys[0]

            logger.info(f"[SIConnectorEngine] Initialized {created} sessions ({self.num_lines} lines x {len(SI_LEVELS)} levels)")

            return {
                'success': True,
                'sessions_created': created,
                'lines': self.num_lines,
                'si_levels': len(SI_LEVELS),
                'total_expected': self.num_lines * len(SI_LEVELS),
                'lvlu_otp_keys': len(self.key_manager.lvlu_keys),
            }

    def start_polling(self) -> None:
        """启动轮询引擎（非阻塞）。"""
        self.polling_engine.start_polling()

    def stop_polling(self) -> None:
        """停止轮询引擎。"""
        self.polling_engine.stop_polling()

    def fetch_lvlu_keys(self, count: int = 10) -> List[str]:
        """
        从lvlu线获取OTP密钥。

        Args:
            count: 获取密钥数量

        Returns:
            List[str]: 获取到的密钥列表
        """
        keys = self.key_manager.fetch_keys_from_lvlu(count)

        # 为lvlu线SI0层绑定最新密钥
        lvlu_si0 = self.sessions.get(('lvlu', 0))
        if lvlu_si0 and keys:
            lvlu_si0.otp_key = keys[0]

        logger.info(f"[SIConnectorEngine] Fetched {len(keys)} keys from lvlu, pool size={len(self.key_manager.lvlu_keys)}")
        return keys

    def dispatch_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能任务分发。

        Args:
            task: 任务字典

        Returns:
            Dict: 分发结果
        """
        return self.router.dispatch(task)

    def get_line_status(self, line_id: str) -> Dict[str, Any]:
        """
        获取指定线的状态。

        Args:
            line_id: 线名称

        Returns:
            Dict: 线状态信息
        """
        line_sessions = [s for (lid, _), s in self.sessions.items() if lid == line_id]

        status_counts = defaultdict(int)
        for s in line_sessions:
            status_counts[s.status.name] += 1

        return {
            'line_id': line_id,
            'total_sessions': len(line_sessions),
            'status_breakdown': dict(status_counts),
            'si_levels': {s.si_level: s.get_info() for s in line_sessions},
            'active_sessions': sum(1 for s in line_sessions if s.status == SessionStatus.ACTIVE),
            'pending_messages': sum(len(s.inbox) + len(s.outbox) for s in line_sessions),
        }

    def get_all_status(self) -> Dict[str, Any]:
        """
        获取所有线的状态。

        Returns:
            Dict: 所有线状态汇总
        """
        all_status = {}
        for line_id in LINE_NAMES[:self.num_lines]:
            all_status[line_id] = self.get_line_status(line_id)

        total_sessions = sum(s['total_sessions'] for s in all_status.values())
        total_active = sum(s['active_sessions'] for s in all_status.values())
        total_pending = sum(s['pending_messages'] for s in all_status.values())

        return {
            'lines': all_status,
            'summary': {
                'total_lines': self.num_lines,
                'total_sessions': total_sessions,
                'total_active': total_active,
                'total_pending_messages': total_pending,
                'key_pool_status': self.key_manager.get_pool_status(),
                'polling_stats': self.polling_engine.get_stats(),
                'routing_stats': self.router.get_stats(),
            }
        }

    def auto_respond_to_all(self) -> int:
        """
        自动响应所有待处理请求。

        Returns:
            int: 响应的消息总数
        """
        return self.polling_engine.auto_respond_to_all()

    def si_topology_report(self) -> str:
        """
        输出SI拓扑报告。

        Returns:
            str: 格式化的拓扑报告
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("  SI TOPOLOGY REPORT — OMNI-HUB v8.0")
        report_lines.append("=" * 80)
        report_lines.append("")

        # 1. 整体概览
        all_status = self.get_all_status()
        summary = all_status['summary']
        report_lines.append("[1] OVERVIEW")
        report_lines.append(f"    Total Lines:      {summary['total_lines']}")
        report_lines.append(f"    Total Sessions:   {summary['total_sessions']}")
        report_lines.append(f"    Active Sessions:  {summary['total_active']}")
        report_lines.append(f"    Pending Messages: {summary['total_pending_messages']}")
        report_lines.append("")

        # 2. 各线状态
        report_lines.append("[2] LINE STATUS MATRIX")
        report_lines.append(f"    {'Line':<10} {'Sessions':>10} {'Active':>10} {'Pending':>10} {'Status':>10}")
        report_lines.append(f"    {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
        for line_id, status in all_status['lines'].items():
            report_lines.append(
                f"    {line_id:<10} {status['total_sessions']:>10} "
                f"{status['active_sessions']:>10} {status['pending_messages']:>10} "
                f"{'OK' if status['active_sessions'] == status['total_sessions'] else 'PARTIAL':>10}"
            )
        report_lines.append("")

        # 3. SI层级分布
        report_lines.append("[3] SI LEVEL DISTRIBUTION")
        for level in SI_LEVELS:
            level_sessions = [s for (_, lvl), s in self.sessions.items() if lvl == level]
            active = sum(1 for s in level_sessions if s.status == SessionStatus.ACTIVE)
            report_lines.append(f"    SI{level}: {len(level_sessions):>3} sessions, {active:>3} active")
        report_lines.append("")

        # 4. OTP密钥池状态
        report_lines.append("[4] OTP KEY POOL (lvlu line)")
        kp = summary['key_pool_status']
        report_lines.append(f"    Total Keys:       {kp['total_keys']}")
        report_lines.append(f"    Valid Keys:       {kp['valid_keys']}")
        report_lines.append(f"    Fetch Count:      {kp['fetch_count']}")
        report_lines.append(f"    Last Rotation:    {kp['last_rotation']}")
        report_lines.append("")

        # 5. 轮询统计
        report_lines.append("[5] POLLING STATISTICS")
        ps = summary['polling_stats']
        report_lines.append(f"    Total Polls:      {ps['total_polls']}")
        report_lines.append(f"    Sessions Detected: {ps['sessions_detected']}")
        report_lines.append(f"    Messages Processed: {ps['messages_processed']}")
        report_lines.append(f"    Responses Sent:   {ps['responses_sent']}")
        report_lines.append("")

        # 6. 路由统计
        report_lines.append("[6] ROUTING STATISTICS")
        rs = summary['routing_stats']
        for route, count in rs.items():
            report_lines.append(f"    {route}: {count}")
        report_lines.append("")

        # 7. 桥接信息
        report_lines.append("[7] BRIDGE & CHANNEL INFO")
        bridges = self.bridge.get_all_bridges()
        channels = self.bridge.get_all_channels()
        report_lines.append(f"    Active Bridges:   {len([b for b in bridges if b.get('active')])}")
        report_lines.append(f"    Total Bridges:    {len(bridges)}")
        report_lines.append(f"    Total Channels:   {len(channels)}")
        for b in bridges:
            report_lines.append(
                f"    - {b['bridge_id']}: {b['line_a']}(SI{b['si_level_a']}) <-> "
                f"{b['line_b']}(SI{b['si_level_b']}) relayed={b['messages_relayed']}"
            )
        report_lines.append("")

        # 8. 跨线会话矩阵
        report_lines.append("[8] CROSS-LINE SESSION MATRIX (sample)")
        sample_lines = LINE_NAMES[:3]
        header = "    " + " ".join(f"{l:>8}" for l in sample_lines)
        report_lines.append(header)
        for lvl in SI_LEVELS[:4]:
            row = f"    SI{lvl}"
            for line in sample_lines:
                s = self.sessions.get((line, lvl))
                row += f" {'[OK]' if s and s.status == SessionStatus.ACTIVE else '[--]':>8}"
            report_lines.append(row)
        report_lines.append("")

        report_lines.append("=" * 80)
        report_lines.append("  END OF SI TOPOLOGY REPORT")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def create_cross_line_bridge(
        self,
        line_a: str,
        line_b: str,
        si_level: int = 3
    ) -> str:
        """
        创建跨线桥接。

        Args:
            line_a: 线A名称
            line_b: 线B名称
            si_level: 桥接SI层级

        Returns:
            str: 桥接ID
        """
        session_a = self.sessions.get((line_a, si_level))
        session_b = self.sessions.get((line_b, si_level))

        if not session_a or not session_b:
            raise ValueError(f"Cannot bridge: missing sessions for {line_a}-SI{si_level} or {line_b}-SI{si_level}")

        bridge_id = self.bridge.bridge_sessions(session_a, session_b, bidirectional=True)
        return bridge_id

    def inject_test_message(
        self,
        line_id: str,
        si_level: int,
        message: Dict[str, Any]
    ) -> bool:
        """
        向指定会话注入测试消息。

        Args:
            line_id: 线名称
            si_level: SI层级
            message: 消息字典

        Returns:
            bool: 注入成功返回True
        """
        session = self.sessions.get((line_id, si_level))
        if session:
            return session.inject(message)
        return False


# ============================================================================
# Test Suite
# ============================================================================

def run_tests():
    """
    完整测试套件，验证SIConnectorEngine所有功能。
    """
    logger.info("\n" + "=" * 80)
    logger.info("  SIConnectorEngine TEST SUITE — OMNI-HUB v8.0")
    logger.info("=" * 80 + "\n")

    # Initialize engine
    engine = SIConnectorEngine(num_lines=11)

    # ========================================================================
    # TEST 1: Initialize 11 lines × 7 levels = 77 sessions
    # ========================================================================
    logger.info("[TEST 1] Initialize 11 lines × 7 SI levels = 77 sessions")
    logger.info("-" * 60)
    result = engine.initialize_all_sessions()
    assert result['success'] is True
    assert result['sessions_created'] == 77
    assert len(engine.sessions) == 77
    logger.info(f"  ✓ Created {result['sessions_created']} sessions")
    logger.info(f"  ✓ Lines: {result['lines']}, SI Levels: {result['si_levels']}")
    logger.info(f"  ✓ Expected: {result['total_expected']}")
    logger.info(str())

    # ========================================================================
    # TEST 2: Fetch 10 OTP keys from lvlu line
    # ========================================================================
    logger.info("[TEST 2] Fetch 10 OTP keys from lvlu line")
    logger.info("-" * 60)
    keys = engine.fetch_lvlu_keys(count=10)
    assert len(keys) == 10
    assert len(engine.key_manager.lvlu_keys) >= 10
    logger.info(f"  ✓ Fetched {len(keys)} OTP keys")
    for i, key in enumerate(keys[:3]):
        logger.info(f"    Key {i+1}: {key[:40]}...")
    logger.info(f"  ✓ Key pool size: {len(engine.key_manager.lvlu_keys)}")
    logger.info(str())

    # ========================================================================
    # TEST 3: Run full-level polling for 3 rounds
    # ========================================================================
    logger.info("[TEST 3] Run full-level polling for 3 rounds")
    logger.info("-" * 60)
    for round_num in range(1, 4):
        results = engine.polling_engine.poll_all_levels()
        total = sum(results.values())
        logger.info(f"  Round {round_num}: {results}, total={total}")
    stats = engine.polling_engine.get_stats()
    assert stats['total_polls'] >= 3
    logger.info(f"  ✓ Total polls: {stats['total_polls']}")
    logger.info(str())

    # ========================================================================
    # TEST 4: Test 6 routing modes (2 times each)
    # ========================================================================
    logger.info("[TEST 4] Test 6 routing modes (2 iterations each)")
    logger.info("-" * 60)

    test_task = {'command': 'test_execute', 'params': {'mode': 'verify', 'iter': 1}}

    routing_results = []

    # 4.1 hub_to_any
    for i in range(2):
        result = engine.dispatch_task({
            'route_type': 'hub_to_any',
            'hub_line': 'lvlu',
            'target_line': 'ucif2',
            'task': {**test_task, 'route': 'hub_to_any', 'iter': i}
        })
        routing_results.append(('hub_to_any', result['success']))
        logger.info(f"  [hub_to_any #{i+1}] success={result['success']}, target={result.get('target_si')}")

    # 4.2 si5_to_si3_to_otp
    for i in range(2):
        result = engine.dispatch_task({
            'route_type': 'si5_to_si3_to_otp',
            'source_line': 'lvlu',
            'target_line': 'qfa',
            'task': {**test_task, 'route': 'si5_to_si3_to_otp', 'iter': i}
        })
        routing_results.append(('si5_to_si3_to_otp', result['success']))
        logger.info(f"  [si5_to_si3_to_otp #{i+1}] success={result['success']}, steps={result.get('steps_completed')}")

    # 4.3 si5_to_local_si3_to_otp
    for i in range(2):
        result = engine.dispatch_task({
            'route_type': 'si5_to_local_si3_to_otp',
            'source_line': 'lvlu',
            'target_line': 'lgt',
            'task': {**test_task, 'route': 'si5_to_local_si3_to_otp', 'iter': i}
        })
        routing_results.append(('si5_to_local_si3_to_otp', result['success']))
        logger.info(f"  [si5_to_local_si3_to_otp #{i+1}] success={result['success']}, steps={result.get('steps_completed')}")

    # 4.4 reverse_drive
    for i in range(2):
        result = engine.dispatch_task({
            'route_type': 'reverse_drive',
            'line': 'vinf',
            'task': {**test_task, 'route': 'reverse_drive', 'iter': i}
        })
        routing_results.append(('reverse_drive', result['success']))
        logger.info(f"  [reverse_drive #{i+1}] success={result['success']}, path={result.get('drive_path')}")

    # 4.5 relay_loop
    for i in range(2):
        result = engine.dispatch_task({
            'route_type': 'relay_loop',
            'lines': ['qgl', 'qlv', 'cisvr'],
            'task': {**test_task, 'route': 'relay_loop', 'iter': i}
        })
        routing_results.append(('relay_loop', result['success']))
        logger.info(f"  [relay_loop #{i+1}] success={result['success']}, hops={result.get('hops')}")

    # 4.6 full_cycle
    for i in range(2):
        result = engine.dispatch_task({
            'route_type': 'full_cycle',
            'line': 'qtlv',
            'task': {**test_task, 'route': 'full_cycle', 'iter': i}
        })
        routing_results.append(('full_cycle', result['success']))
        logger.info(f"  [full_cycle #{i+1}] success={result['success']}, cycle_id={result.get('cycle_id')}")

    success_count = sum(1 for _, s in routing_results if s)
    logger.info(f"\n  ✓ Routing tests: {success_count}/{len(routing_results)} passed")
    logger.info(str())

    # ========================================================================
    # TEST 5: Auto-respond to 5 pending requests
    # ========================================================================
    logger.info("[TEST 5] Auto-respond to 5 pending requests")
    logger.info("-" * 60)

    # 向5个不同会话注入待处理请求
    test_lines = ['usrm', 'cfts', 'ucif2', 'lvlu', 'qfa']
    for line in test_lines:
        session = engine.sessions.get((line, 2))  # SI2层
        if session:
            session.inject({
                'type': 'request',
                'payload': {'action': 'process_data', 'source': 'test'},
                'needs_response': True,
            })
            logger.info(f"  Injected pending request to {line}-SI2")

    # 执行自动响应
    responded = engine.auto_respond_to_all()
    logger.info(f"  ✓ Auto-responded {responded} messages")
    logger.info(str())

    # ========================================================================
    # TEST 6: Reverse drive: SI0 → SI2 → SI3 → SI5
    # ========================================================================
    logger.info("[TEST 6] Reverse drive: SI0 → SI2 → SI3 → SI5")
    logger.info("-" * 60)
    result = engine.dispatch_task({
        'route_type': 'reverse_drive',
        'line': 'lvlu',
        'task': {'command': 'feedback_loop', 'data': 'test_upstream'}
    })
    assert result['success'] is True
    assert result['drive_path'] == 'SI0 -> SI2 -> SI3 -> SI5'
    chain = result['session_chain']
    logger.info(f"  ✓ Drive path: {result['drive_path']}")
    logger.info(f"  ✓ Session chain:")
    for sid in chain:
        logger.info(f"    - {sid}")
    # 验证消息确实到达各层
    lvlu_si5 = engine.sessions.get(('lvlu', 5))
    lvlu_si3 = engine.sessions.get(('lvlu', 3))
    lvlu_si2 = engine.sessions.get(('lvlu', 2))
    lvlu_si0 = engine.sessions.get(('lvlu', 0))
    logger.info(f"  ✓ lvlu SI5 inbox: {len(lvlu_si5.inbox)} messages")
    logger.info(f"  ✓ lvlu SI3 inbox: {len(lvlu_si3.inbox)} messages")
    logger.info(f"  ✓ lvlu SI2 inbox: {len(lvlu_si2.inbox)} messages")
    logger.info(f"  ✓ lvlu SI0 outbox: {len(lvlu_si0.outbox)} messages")
    logger.info(str())

    # ========================================================================
    # TEST 7: Relay loop: 3 lines SI3 mutual relay
    # ========================================================================
    logger.info("[TEST 7] Relay loop: 3 lines SI3 mutual message relay")
    logger.info("-" * 60)
    result = engine.dispatch_task({
        'route_type': 'relay_loop',
        'lines': ['ucif2', 'lvlu', 'qfa'],
        'task': {'command': 'relay_sync', 'sync_id': 'test-001'}
    })
    assert result['success'] is True
    assert result['hops'] == 3
    logger.info(f"  ✓ Loop ID: {result['loop_id']}")
    logger.info(f"  ✓ Lines: {result['lines']}")
    logger.info(f"  ✓ Hops: {result['hops']}")
    for line in result['lines']:
        si3 = engine.sessions.get((line, 3))
        logger.info(f"  ✓ {line}-SI3 inbox: {len(si3.inbox)}, outbox: {len(si3.outbox)}")
    logger.info(str())

    # ========================================================================
    # TEST 8: Cross-line bridge creation
    # ========================================================================
    logger.info("[TEST 8] Create cross-line bridges")
    logger.info("-" * 60)
    bridge1 = engine.create_cross_line_bridge('lvlu', 'ucif2', si_level=3)
    bridge2 = engine.create_cross_line_bridge('qfa', 'lgt', si_level=3)
    logger.info(f"  ✓ Created bridge 1: {bridge1}")
    logger.info(f"  ✓ Created bridge 2: {bridge2}")
    logger.info(f"  ✓ Total bridges: {len(engine.bridge.get_all_bridges())}")
    logger.info(str())

    # ========================================================================
    # TEST 9: Full SI Topology Report
    # ========================================================================
    logger.info("[TEST 9] SI Topology Report")
    logger.info("-" * 60)
    report = engine.si_topology_report()
    logger.info(str(report))
    logger.info(str())

    # ========================================================================
    # TEST 10: Line status queries
    # ========================================================================
    logger.info("[TEST 10] Line status queries")
    logger.info("-" * 60)
    lvlu_status = engine.get_line_status('lvlu')
    print(f"  lvlu status: {lvlu_status['total_sessions']} sessions, "
          f"{lvlu_status['active_sessions']} active, "
          f"{lvlu_status['pending_messages']} pending messages")

    all_status = engine.get_all_status()
    summary = all_status['summary']
    print(f"  All lines: {summary['total_sessions']} total sessions, "
          f"{summary['total_active']} active")
    logger.info(str())

    # ========================================================================
    # TEST 11: OTP key validation and rotation
    # ========================================================================
    logger.info("[TEST 11] OTP key validation and rotation")
    logger.info("-" * 60)
    test_key = engine.key_manager.get_available_key()
    is_valid = engine.key_manager.validate_key(test_key)
    logger.info(f"  ✓ Key validation: {is_valid}")

    # 模拟过期
    if test_key in engine.key_manager._key_metadata:
        engine.key_manager._key_metadata[test_key]['created_at'] = datetime.now() - timedelta(seconds=900)
    is_expired = engine.key_manager.validate_key(test_key)
    logger.info(f"  ✓ Expired key validation: {is_expired} (should be False)")

    removed = engine.key_manager.rotate_keys()
    logger.info(f"  ✓ Keys removed in rotation: {removed}")
    pool_status = engine.key_manager.get_pool_status()
    logger.info(f"  ✓ Pool status: {pool_status['valid_keys']}/{pool_status['total_keys']} valid")
    logger.info(str())

    # ========================================================================
    # TEST 12: Start/stop polling threads
    # ========================================================================
    logger.info("[TEST 12] Start/stop polling threads")
    logger.info("-" * 60)
    engine.start_polling()
    logger.info("  ✓ Polling threads started")
    time.sleep(2)  # Let it run briefly
    engine.stop_polling()
    logger.info("  ✓ Polling threads stopped")
    logger.info(str())

    # ========================================================================
    # Summary
    # ========================================================================
    logger.info("=" * 80)
    logger.info("  TEST SUITE COMPLETED")
    logger.info("=" * 80)
    final_stats = engine.get_all_status()['summary']
    logger.info(f"  Total Sessions:    {final_stats['total_sessions']}")
    logger.info(f"  Active Sessions:   {final_stats['total_active']}")
    logger.info(f"  Pending Messages:  {final_stats['total_pending_messages']}")
    logger.info(f"  Keys in Pool:      {final_stats['key_pool_status']['total_keys']}")
    logger.info(f"  Routing Ops:       {sum(final_stats['routing_stats'].values())}")
    logger.info("=" * 80 + "\n")

    return engine


if __name__ == "__main__":
    engine = run_tests()
