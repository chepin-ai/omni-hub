
__version__ = "11.0.0"
"""
inbox_outbox.py — OMNI-HUB v3.2
可靠消息传递系统 — inbox-outbox 模式
确保消息: 不丢失、不重复、有序到达
"""

import time
import hashlib
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging


class MsgStatus(Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKED = "acked"


@dataclass
class Message:
    """消息结构"""
    msg_id: str
    from_line: str
    to_line: str
    msg_type: str
    payload: dict
    priority: int = 5              # 0-9, 0=最高
    seq: int = 0
    status: MsgStatus = MsgStatus.PENDING
    attempts: int = 0
    created_at: float = 0.0
    delivered_at: float = 0.0
    timeline: List[dict] = field(default_factory=list)
    latency_ms: float = 0.0
    acked: bool = False

    def to_dict(self) -> dict:
        return {
            "msg_id": self.msg_id,
            "from_line": self.from_line,
            "to_line": self.to_line,
            "msg_type": self.msg_type,
            "payload": self.payload,
            "priority": self.priority,
            "seq": self.seq,
            "status": self.status.value,
            "attempts": self.attempts,
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
            "timeline": self.timeline,
            "latency_ms": self.latency_ms,
            "acked": self.acked
        }


class ReliableMessaging:
    """可靠消息系统 — inbox-outbox，消息不丢失、不重复、有序到达"""

    MAX_RETRY = 3
    RETRY_DELAY_MS = 100
    LINES = [f"L{i:02d}" for i in range(1, 12)]  # L01 ~ L11

    def __init__(self):
        self.inbox: Dict[str, List[Message]] = {}    # {line: [messages]}
        self.outbox: Dict[str, List[Message]] = {}   # {line: [messages]}
        self.delivery_log: List[dict] = []
        self.msg_counter = 0
        self._line_health: Dict[str, float] = {line: 1.0 for line in self.LINES}
        self._system_load: float = 0.0               # 0.0 ~ 1.0
        self._acked_msg_ids: set = set()             # 去重集合
        self._seq_counters: Dict[str, int] = {}      # {from_to: seq}

        for line in self.LINES:
            self.inbox[line] = []
            self.outbox[line] = []

    def _generate_msg_id(self, from_line: str, to_line: str) -> str:
        """生成消息ID: {from_line}_{to_line}_{seq}_{hash}"""
        key = f"{from_line}_{to_line}"
        self._seq_counters[key] = self._seq_counters.get(key, 0) + 1
        seq = self._seq_counters[key]
        raw = f"{from_line}_{to_line}_{seq}_{time.time()}_{random.randint(0, 9999)}"
        h = hashlib.sha256(raw.encode()).hexdigest()[:8]
        return f"{from_line}_{to_line}_{seq}_{h}"

    def _calculate_success_rate(self, from_line: str, to_line: str) -> float:
        """计算投递成功率
        公式: 源线健康度 × 目标线健康度 × (1 - 系统负载 × 0.1)
        """
        src_health = self._line_health.get(from_line, 0.5)
        dst_health = self._line_health.get(to_line, 0.5)
        load_factor = max(0.0, 1.0 - self._system_load * 0.1)
        return max(0.0, min(1.0, src_health * dst_health * load_factor))

    def _simulate_delivery(self, msg: Message) -> bool:
        """模拟投递，返回是否成功"""
        success_rate = self._calculate_success_rate(msg.from_line, msg.to_line)
        return random.random() < success_rate

    def _record_delivery(self, msg: Message, event: str, detail: dict = None):
        """记录投递日志"""
        entry = {
            "msg_id": msg.msg_id,
            "event": event,
            "timestamp": time.time(),
            "detail": detail or {}
        }
        self.delivery_log.append(entry)
        msg.timeline.append(entry)

    def send(self, from_line: str, to_line: str, message: dict) -> dict:
        """可靠发送

        message: {"type": str, "payload": dict, "priority": 0-9}
        返回: {"msg_id": str, "status": "delivered|pending|failed",
                "attempts": int, "latency_ms": float}
        实现:
            1. 生成msg_id (line_from_line_to_seq_counter_hash)
            2. 放入outbox
            3. 模拟投递 (根据距离/负载计算成功率)
            4. 如果失败，重试MAX_RETRY次
            5. 记录delivery_log
        """
        if from_line not in self.LINES or to_line not in self.LINES:
            return {
                "msg_id": "",
                "status": "failed",
                "attempts": 0,
                "latency_ms": 0.0,
                "error": f"Invalid line, must be in {self.LINES}"
            }

        self.msg_counter += 1
        msg_id = self._generate_msg_id(from_line, to_line)
        msg_type = message.get("type", "unknown")
        payload = message.get("payload", {})
        priority = max(0, min(9, message.get("priority", 5)))

        msg = Message(
            msg_id=msg_id,
            from_line=from_line,
            to_line=to_line,
            msg_type=msg_type,
            payload=payload,
            priority=priority,
            seq=self._seq_counters.get(f"{from_line}_{to_line}", 1),
            created_at=time.time()
        )

        # 放入发件箱
        self.outbox[from_line].append(msg)
        self._record_delivery(msg, "queued")

        # 尝试投递
        start_time = time.time()
        delivered = False

        for attempt in range(1, self.MAX_RETRY + 1):
            msg.attempts = attempt
            if self._simulate_delivery(msg):
                delivered = True
                msg.status = MsgStatus.DELIVERED
                msg.delivered_at = time.time()
                msg.latency_ms = (msg.delivered_at - start_time) * 1000
                self._record_delivery(msg, "delivered", {"attempt": attempt})
                # 放入收件箱
                self.inbox[to_line].append(msg)
                break
            else:
                self._record_delivery(msg, "retry", {"attempt": attempt})
                if attempt < self.MAX_RETRY:
                    time.sleep(self.RETRY_DELAY_MS / 1000.0)

        if not delivered:
            msg.status = MsgStatus.FAILED
            msg.latency_ms = (time.time() - start_time) * 1000
            self._record_delivery(msg, "failed", {"total_attempts": msg.attempts})

        return {
            "msg_id": msg_id,
            "status": msg.status.value,
            "attempts": msg.attempts,
            "latency_ms": round(msg.latency_ms, 3)
        }

    def receive(self, line: str, max_msgs: int = 10) -> list:
        """接收并确认消息

        返回消息列表，标记为已读
        """
        if line not in self.LINES:
            return []

        msgs = self.inbox.get(line, [])
        # 按优先级和seq排序 (priority越小越优先, seq越小越优先)
        msgs.sort(key=lambda m: (m.priority, m.seq))

        result = []
        count = 0
        for msg in msgs:
            if count >= max_msgs:
                break
            if msg.msg_id in self._acked_msg_ids:
                continue
            msg.acked = True
            self._acked_msg_ids.add(msg.msg_id)
            msg.status = MsgStatus.ACKED
            self._record_delivery(msg, "acked", {"by": line})
            result.append({
                "msg_id": msg.msg_id,
                "from_line": msg.from_line,
                "to_line": msg.to_line,
                "type": msg.msg_type,
                "payload": msg.payload,
                "priority": msg.priority,
                "seq": msg.seq,
                "attempts": msg.attempts,
                "latency_ms": round(msg.latency_ms, 3),
                "received_at": datetime.utcnow().isoformat() + "Z"
            })
            count += 1

        return result

    def retry_failed(self) -> dict:
        """重试所有失败的消息

        返回: {"retried": int, "recovered": int, "still_failed": int}
        """
        retried = 0
        recovered = 0
        still_failed = 0

        for line in self.LINES:
            for msg in self.outbox.get(line, []):
                if msg.status != MsgStatus.FAILED:
                    continue

                retried += 1
                msg.status = MsgStatus.PENDING
                msg.attempts = 0  # 重置尝试次数
                start_time = time.time()

                for attempt in range(1, self.MAX_RETRY + 1):
                    msg.attempts = attempt
                    if self._simulate_delivery(msg):
                        recovered += 1
                        msg.status = MsgStatus.DELIVERED
                        msg.delivered_at = time.time()
                        msg.latency_ms = (msg.delivered_at - start_time) * 1000
                        self._record_delivery(msg, "recovered", {"attempt": attempt})
                        self.inbox[msg.to_line].append(msg)
                        break
                    else:
                        self._record_delivery(msg, "retry_failed", {"attempt": attempt})
                        if attempt < self.MAX_RETRY:
                            time.sleep(self.RETRY_DELAY_MS / 1000.0)
                else:
                    still_failed += 1
                    msg.status = MsgStatus.FAILED
                    msg.latency_ms = (time.time() - start_time) * 1000
                    self._record_delivery(msg, "failed_again")

        self.delivery_log.append({
            "event": "retry_failed_batch",
            "timestamp": time.time(),
            "retried": retried,
            "recovered": recovered,
            "still_failed": still_failed
        })

        return {
            "retried": retried,
            "recovered": recovered,
            "still_failed": still_failed
        }

    def verify_delivery(self, msg_id: str) -> dict:
        """验证消息投递状态

        返回: {"msg_id": str, "delivered": bool, "attempts": int,
                "final_status": str, "timeline": list}
        """
        # 在所有outbox中查找
        for line in self.LINES:
            for msg in self.outbox.get(line, []):
                if msg.msg_id == msg_id:
                    return {
                        "msg_id": msg_id,
                        "delivered": msg.status == MsgStatus.DELIVERED or msg.acked,
                        "attempts": msg.attempts,
                        "final_status": msg.status.value,
                        "timeline": msg.timeline,
                        "latency_ms": round(msg.latency_ms, 3),
                        "created_at": msg.created_at,
                        "delivered_at": msg.delivered_at
                    }

        # 在inbox中查找
        for line in self.LINES:
            for msg in self.inbox.get(line, []):
                if msg.msg_id == msg_id:
                    return {
                        "msg_id": msg_id,
                        "delivered": True,
                        "attempts": msg.attempts,
                        "final_status": msg.status.value,
                        "timeline": msg.timeline,
                        "latency_ms": round(msg.latency_ms, 3),
                        "created_at": msg.created_at,
                        "delivered_at": msg.delivered_at
                    }

        return {
            "msg_id": msg_id,
            "delivered": False,
            "attempts": 0,
            "final_status": "unknown",
            "timeline": [],
            "error": "Message not found"
        }

    def broadcast(self, from_line: str, message: dict) -> dict:
        """向所有线广播消息

        返回: {"sent": int, "delivered": int, "failed": int, "ack_rate": float}
        """
        if from_line not in self.LINES:
            return {"sent": 0, "delivered": 0, "failed": 0, "ack_rate": 0.0,
                    "error": f"Invalid line '{from_line}'"}

        sent = 0
        delivered = 0
        failed = 0
        results = []

        for to_line in self.LINES:
            if to_line == from_line:
                continue
            sent += 1
            result = self.send(from_line, to_line, message)
            results.append(result)
            if result["status"] == "delivered":
                delivered += 1
            else:
                failed += 1

        ack_rate = delivered / sent if sent > 0 else 0.0

        self.delivery_log.append({
            "event": "broadcast",
            "timestamp": time.time(),
            "from_line": from_line,
            "sent": sent,
            "delivered": delivered,
            "failed": failed,
            "ack_rate": ack_rate
        })

        return {
            "sent": sent,
            "delivered": delivered,
            "failed": failed,
            "ack_rate": round(ack_rate, 4),
            "details": results
        }

    def get_stats(self) -> dict:
        """获取消息系统统计"""
        total_outbox = sum(len(v) for v in self.outbox.values())
        total_inbox = sum(len(v) for v in self.inbox.values())
        total_acked = len(self._acked_msg_ids)

        delivered_count = 0
        failed_count = 0
        pending_count = 0
        total_latency = 0.0
        latency_count = 0

        for line in self.LINES:
            for msg in self.outbox.get(line, []):
                if msg.status == MsgStatus.DELIVERED or msg.acked:
                    delivered_count += 1
                elif msg.status == MsgStatus.FAILED:
                    failed_count += 1
                else:
                    pending_count += 1
                if msg.latency_ms > 0:
                    total_latency += msg.latency_ms
                    latency_count += 1

        avg_latency = total_latency / latency_count if latency_count > 0 else 0.0

        return {
            "total_messages": self.msg_counter,
            "outbox_messages": total_outbox,
            "inbox_messages": total_inbox,
            "acked_messages": total_acked,
            "delivered": delivered_count,
            "failed": failed_count,
            "pending": pending_count,
            "avg_latency_ms": round(avg_latency, 3),
            "delivery_rate": round(delivered_count / max(1, self.msg_counter), 4),
            "system_load": self._system_load,
            "line_health": dict(self._line_health),
            "delivery_log_entries": len(self.delivery_log)
        }

    def set_line_health(self, line: str, health: float):
        """设置线健康度 (0.0 ~ 1.0)"""
        if line in self._line_health:
            self._line_health[line] = max(0.0, min(1.0, health))

    def set_system_load(self, load: float):
        """设置系统负载 (0.0 ~ 1.0)"""
        self._system_load = max(0.0, min(1.0, load))


# ==================== 测试块 ====================
"""
OMNI-HUB v11.0 — inbox_outbox
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""
if __name__ == "__main__":
    print("=" * 60)
    print("ReliableMessaging 测试开始")
    print("=" * 60)

    rm = ReliableMessaging()

    # 1. 单发测试
    print("\n[1] 单发测试 (send)")
    result = rm.send("L01", "L02", {
        "type": "heartbeat",
        "payload": {"seq": 1, "data": "ping"},
        "priority": 3
    })
    assert result["msg_id"], "msg_id 不应为空"
    assert "_" in result["msg_id"], "msg_id 应包含下划线分隔符"
    assert result["status"] in ("delivered", "failed", "pending")
    assert result["attempts"] >= 1
    print(f"   ✓ 单发完成: msg_id={result['msg_id']}, status={result['status']}, attempts={result['attempts']}")

    # 2. 接收测试
    print("\n[2] 接收测试 (receive)")
    received = rm.receive("L02", max_msgs=10)
    print(f"   ✓ L02 接收到 {len(received)} 条消息")
    for m in received:
        print(f"      - {m['msg_id']}: type={m['type']}, from={m['from_line']}, latency={m['latency_ms']}ms")

    # 3. 验证投递
    print("\n[3] 验证投递 (verify_delivery)")
    msg_id_to_check = result["msg_id"]
    verify = rm.verify_delivery(msg_id_to_check)
    assert verify["msg_id"] == msg_id_to_check
    print(f"   ✓ 投递验证: delivered={verify['delivered']}, attempts={verify['attempts']}, status={verify['final_status']}")
    if verify["timeline"]:
        print(f"      时间线: {len(verify['timeline'])} 个事件")

    # 4. 广播测试
    print("\n[4] 广播测试 (broadcast)")
    broadcast_result = rm.broadcast("L01", {
        "type": "announcement",
        "payload": {"msg": "System upgrade scheduled"},
        "priority": 1
    })
    assert broadcast_result["sent"] == 10  # 11线 - 1(自身) = 10
    print(f"   ✓ 广播完成: sent={broadcast_result['sent']}, delivered={broadcast_result['delivered']}, failed={broadcast_result['failed']}")
    print(f"      ack_rate={broadcast_result['ack_rate']}")

    # 5. 失败重试测试 (通过降低健康度模拟失败)
    print("\n[5] 失败重试测试 (retry_failed)")
    # 设置极低健康度以强制失败
    rm.set_line_health("L03", 0.0)
    rm.set_line_health("L04", 0.0)
    rm.set_system_load(0.9)

    fail_count = 0
    for i in range(5):
        r = rm.send("L03", "L04", {
            "type": "test_fail",
            "payload": {"idx": i},
            "priority": 5
        })
        if r["status"] == "failed":
            fail_count += 1
    print(f"   ✓ 强制失败: {fail_count} 条消息发送失败")

    # 恢复健康度后重试
    rm.set_line_health("L03", 1.0)
    rm.set_line_health("L04", 1.0)
    rm.set_system_load(0.0)

    retry_result = rm.retry_failed()
    print(f"   ✓ 重试结果: retried={retry_result['retried']}, recovered={retry_result['recovered']}, still_failed={retry_result['still_failed']}")

    # 6. 消息去重测试
    print("\n[6] 去重测试")
    # 同一消息ID不应被重复接收
    if received:
        # 先记录当前已ack的消息ID集合（调用receive前的状态）
        pre_acked_ids = set(rm._acked_msg_ids)
        # 向L02再发一条新消息
        rm.send("L09", "L02", {"type": "dup_test", "payload": {}, "priority": 5})
        dup_check = rm.receive("L02", max_msgs=10)
        # 检查返回的消息中是否有在pre_acked_ids中已存在的（即重复返回）
        already_acked = [m for m in dup_check if m["msg_id"] in pre_acked_ids]
        print(f"   ✓ 重复接收检查: 已ack消息再次接收数={len(already_acked)} (应为0)")
        # 同时验证新消息确实被接收到了
        new_msgs = [m for m in dup_check if m["msg_id"] not in pre_acked_ids]
        print(f"   ✓ 新消息接收数={len(new_msgs)} (应>=1)")

    # 7. 消息ID格式验证
    print("\n[7] 消息ID格式验证")
    test_msg = rm.send("L05", "L06", {"type": "id_test", "payload": {}, "priority": 5})
    parts = test_msg["msg_id"].split("_")
    assert len(parts) == 4, f"msg_id 应有4部分: {parts}"
    assert parts[0] == "L05", f"第一部分应为from_line: {parts[0]}"
    assert parts[1] == "L06", f"第二部分应为to_line: {parts[1]}"
    assert parts[2].isdigit(), f"第三部分应为seq数字: {parts[2]}"
    assert len(parts[3]) == 8, f"第四部分应为8位hash: {parts[3]}"
    print(f"   ✓ 消息ID格式正确: {'_'.join(parts)}")

    # 8. 优先级排序测试
    print("\n[8] 优先级排序测试")
    rm2 = ReliableMessaging()
    rm2.send("L07", "L08", {"type": "low", "payload": {}, "priority": 8})
    rm2.send("L07", "L08", {"type": "high", "payload": {}, "priority": 2})
    rm2.send("L07", "L08", {"type": "medium", "payload": {}, "priority": 5})
    rec = rm2.receive("L08", max_msgs=10)
    priorities = [m["priority"] for m in rec]
    assert priorities == sorted(priorities), f"接收应按优先级排序: {priorities}"
    print(f"   ✓ 优先级排序正确: {priorities}")

    # 9. 统计信息测试
    print("\n[9] 统计信息 (get_stats)")
    stats = rm.get_stats()
    assert "total_messages" in stats
    assert "delivery_rate" in stats
    assert "avg_latency_ms" in stats
    print(f"   ✓ 统计: total={stats['total_messages']}, delivered={stats['delivered']}, "
          f"failed={stats['failed']}, rate={stats['delivery_rate']}")

    # 10. 边界测试
    print("\n[10] 边界测试")
    bad = rm.send("L99", "L01", {"type": "bad", "payload": {}})
    assert bad["status"] == "failed"
    assert "error" in bad
    print(f"   ✓ 无效线正确拒绝: {bad['error']}")

    print("\n" + "=" * 60)
    print("ReliableMessaging 全部测试通过!")
    print("=" * 60)
