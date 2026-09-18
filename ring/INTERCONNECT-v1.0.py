#!/usr/bin/env python3

"""
INTERCONNECT-v1.0.py
SI0~SI5 自联互联/自环互环/自激互激协议实现
ucif2-kernel LOCAL FULL DIMENSION AUTONOMY

执行方式: python3 INTERCONNECT-v1.0.py [command] [args...]
"""

__version__ = "11.0.0"
import os
import sys
import json
import time
import hashlib
import uuid
import fcntl
import shutil
import glob
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading

# =============================================================================
# 全局常量
# =============================================================================

BASE_DIR = Path("/mnt/agents/output/OMNI-HUB")
TOWERS_DIR = BASE_DIR / "towers"
HUB_DIR = BASE_DIR / "hub"
RING_DIR = BASE_DIR / "ring"
QUANTUM_DIR = BASE_DIR / "quantum"
RESONANCE_DIR = BASE_DIR / "resonance"
TENSOR_DIR = BASE_DIR / "tensor"
CIRCLES_DIR = BASE_DIR / "circles"

ALL_LINES = ["ucif2", "lgt", "qfa", "usrm", "vinf", "qgl", "qlv", "lvlu", "cfts"]

# 环拓扑顺序 (顺时针)
RING_ORDER = ["ucif2", "lgt", "qfa", "usrm", "vinf", "qgl", "qlv", "lvlu", "cfts"]

# 圈子分层
CIRCLE_INNER = ["ucif2", "lgt", "qfa"]
CIRCLE_MIDDLE = ["usrm", "vinf", "qgl", "qlv"]
CIRCLE_OUTER = ["lvlu", "cfts"]
CIRCLE_ALL = {"inner": CIRCLE_INNER, "middle": CIRCLE_MIDDLE, "outer": CIRCLE_OUTER}

# SI层级
SI_LEVELS = [0, 1, 2, 3, 4, 5]

# 自激触发阈值
SELF_EXCITE_SILENCE_THRESHOLD = 8.0   # 秒
SELF_EXCITE_ENTROPY_THRESHOLD = 2.5
SELF_EXCITE_HEALTH_THRESHOLD = 0.7
SELF_EXCITE_ORPHAN_THRESHOLD = 3

# 互激阈值
ENTANGLEMENT_THRESHOLD = 0.6
RESONANCE_SIMILARITY_THRESHOLD = 0.75

# ACK超时 (秒)
ACK_TIMEOUTS = {"L0": 5, "L1": 15, "L2": 60, "L3": 300}
MAX_RETRY_ATTEMPTS = 5

# 张量指标
METRICS = ["health", "load", "throughput", "latency", "entropy", "excitation_level"]

# =============================================================================
# 工具函数
# =============================================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    if path.exists():
        h.update(path.read_bytes())
    return h.hexdigest()

def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".tmp.{uuid.uuid4().hex}")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    with tmp.open("rb") as f:
        os.fsync(f.fileno())
    tmp.rename(path)

def read_json(path: Path, default=None) -> dict:
    if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
            return default if default is not None else {}
    return default if default is not None else {}

def line_dir(line: str) -> Path:
    return TOWERS_DIR / line

def inbox_dir(line: str) -> Path:
    return line_dir(line) / "inbox"

def outbox_dir(line: str) -> Path:
    return line_dir(line) / "outbox"

def board_dir(line: str) -> Path:
    return line_dir(line) / "board"

def si_dir(line: str, si: int) -> Path:
    return line_dir(line) / f"si{si}"

# =============================================================================
# SI0: 文件系统互操作
# =============================================================================

class FileLockManager:
    """SI0 文件锁管理器"""
    
    def __init__(self, line: str):
        self.line = line
        self.lock_dir = line_dir(line) / ".locks"
        self.lock_dir.mkdir(parents=True, exist_ok=True)
    
    def acquire_lock(self, filepath: Path, lock_type: str = "exclusive", timeout: float = 30.0) -> Tuple[bool, dict]:
        """获取文件锁，返回 (success, lock_info)"""
        lock_file = self.lock_dir / f"{filepath.name}.{lock_type}.lock"
        start = time.time()
        
        while time.time() - start < timeout:
            if not lock_file.exists():
                lock_info = {
                    "holder": f"{self.line}:SI0",
                    "ts": now_iso(),
                    "pid": os.getpid(),
                    "op": "write" if lock_type == "exclusive" else "read",
                    "type": lock_type
                }
                write_json(lock_file, lock_info)
                return True, lock_info
            
            # 检查现有锁是否超时
            existing = read_json(lock_file, {})
            if existing:
                    lock_ts = datetime.fromisoformat(existing.get("ts", "2000-01-01T00:00:00+00:00"))
                    if (datetime.now(timezone.utc) - lock_ts).total_seconds() > timeout:
                        # 强制抢占
                        lock_info = {
                            "holder": f"{self.line}:SI0",
                            "ts": now_iso(),
                            "pid": os.getpid(),
                            "op": "write" if lock_type == "exclusive" else "read",
                            "type": lock_type,
                            "preempted_from": existing.get("holder")
                        }
                        write_json(lock_file, lock_info)
                        self._audit_log("PREEMPT", existing)
                        return True, lock_info
                    pass
            
            time.sleep(0.1)
        
        return False, {}
    
    def release_lock(self, filepath: Path, lock_type: str = "exclusive"):
        lock_file = self.lock_dir / f"{filepath.name}.{lock_type}.lock"
        if lock_file.exists():
            lock_file.unlink()
    
    def _audit_log(self, event: str, data: dict):
        audit_file = BASE_DIR / "audit" / f"SI0-audit-{self.line}.jsonl"
        audit_file.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event": event, "ts": now_iso(), "data": data}, ensure_ascii=False) + "\n")

class AtomicWriter:
    """SI0 原子写操作"""
    
    VERSION_HEADER = "# SI0-VERSION: {version}\n# SI0-HASH: {hash}\n# SI0-PARENT: {parent}\n# SI0-TIMESTAMP: {ts}\n# SI0-LINE: {line}\n# SI0-LEVEL: {level}\n---\n"
    
    @staticmethod
    def write(filepath: Path, content: str, line: str, si_level: int, version: str = "1.0.0", parent_hash: str = "null"):
        lock_mgr = FileLockManager(line)
        acquired, _ = lock_mgr.acquire_lock(filepath, "exclusive")
        if not acquired:
            raise RuntimeError(f"无法获取文件锁: {filepath}")
        
            content_hash = sha256_str(content)
            header = AtomicWriter.VERSION_HEADER.format(
                version=version,
                hash=content_hash,
                parent=parent_hash,
                ts=now_iso(),
                line=line,
                level=si_level
            )
            full_content = header + content
            
            tmp = filepath.with_suffix(f".tmp.{uuid.uuid4().hex}")
            tmp.write_text(full_content, encoding="utf-8")
            with tmp.open("rb") as f:
                os.fsync(f.fileno())
            tmp.rename(filepath)
            
            # 保留历史版本
            versions_dir = filepath.parent / ".versions"
            versions_dir.mkdir(parents=True, exist_ok=True)
            version_copy = versions_dir / f"{filepath.name}.{content_hash[:16]}"
            if not version_copy.exists():
                version_copy.write_text(full_content, encoding="utf-8")
            
            # 清理旧版本 (保留最近10个)
            old_versions = sorted(versions_dir.glob(f"{filepath.name}.*"), key=lambda p: p.stat().st_mtime)
            for old in old_versions[:-10]:
                old.unlink()
            
            return content_hash
    @staticmethod
    def read(filepath: Path) -> Tuple[dict, str]:
        if not filepath.exists():
            return {}, ""
        content = filepath.read_text(encoding="utf-8")
        # 解析版本头
        header = {}
        body_start = 0
        for i, line in enumerate(content.split("\n")):
            if line.startswith("# SI0-"):
                key_val = line[2:].split(":", 1)
                if len(key_val) == 2:
                    header[key_val[0].strip()] = key_val[1].strip()
            elif line == "---":
                body_start = i + 1
                break
        body = "\n".join(content.split("\n")[body_start:])
        return header, body
    
    @staticmethod
    def verify(filepath: Path) -> bool:
        header, body = AtomicWriter.read(filepath)
        if "SI0-HASH" not in header:
            return False
        expected_hash = sha256_str(body)
        return expected_hash == header["SI0-HASH"]

def si0_self_loop(line: str) -> dict:
    """
    SI0 自环检查
    1. 扫描 line 的 si0/ 目录文件 (排除自身报告)
    2. 检查版本头完整性 (仅对SI0格式文件)
    3. 验证 hash 匹配
    4. 清理过期的 .tmp.* 文件
    5. 若发现孤儿锁（超时>60s），释放并记录
    6. 返回完整性报告
    """
    report = {
        "line": line,
        "ts": now_iso(),
        "total_files": 0,
        "valid_files": 0,
        "invalid_files": [],
        "orphan_locks": [],
        "tmp_cleaned": 0,
        "integrity_score": 1.0
    }
    
    # 扫描 si0 目录 (仅检查SI0格式文件，排除报告文件)
    d = si_dir(line, 0)
    if d.exists():
        for fpath in d.iterdir():
            if fpath.is_file() and not fpath.name.startswith(".") and not fpath.name.startswith("self_loop"):
                report["total_files"] += 1
                # 快速检查: 仅验证有SI0头的文件
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                if content.startswith("# SI0-VERSION"):
                    if AtomicWriter.verify(fpath):
                        report["valid_files"] += 1
                    else:
                        report["invalid_files"].append(str(fpath.relative_to(BASE_DIR)))
                else:
                    # 非SI0格式文件，检查是否为有效JSON
                        json.loads(content)
                        report["valid_files"] += 1
                        report["invalid_files"].append(str(fpath.relative_to(BASE_DIR)))
    
    # 清理临时文件 (所有si级别)
    for si in SI_LEVELS:
        d = si_dir(line, si)
        if d.exists():
            for tmp in d.glob("*.tmp.*"):
                    tmp.unlink()
                    report["tmp_cleaned"] += 1
                    pass
    
    # 检查孤儿锁
    lock_dir = line_dir(line) / ".locks"
    if lock_dir.exists():
        for lock_file in lock_dir.glob("*.lock"):
            lock_data = read_json(lock_file, {})
            if lock_data:
                    lock_ts = datetime.fromisoformat(lock_data.get("ts", "2000-01-01T00:00:00+00:00"))
                    if (datetime.now(timezone.utc) - lock_ts).total_seconds() > 60:
                        report["orphan_locks"].append({
                            "file": lock_file.name,
                            "holder": lock_data.get("holder"),
                            "age_sec": (datetime.now(timezone.utc) - lock_ts).total_seconds()
                        })
                        lock_file.unlink()
                    pass
    
    if report["total_files"] > 0:
        report["integrity_score"] = report["valid_files"] / report["total_files"]
    
    # 写入报告
    report_path = si_dir(line, 0) / f"self_loop_report_{int(time.time())}.json"
    write_json(report_path, report)
    
    return report

def si0_cross_loop(source: str, target: str, file_list: List[str]) -> dict:
    """
    SI0 互环: source -> target 文件同步
    1. source 读取 file_list 中各文件的版本头
    2. 通过原子写将文件复制到 target 的对应目录
    3. 保持版本链连续性
    4. 若 target 已有同名文件，创建 MERGE 分支
    5. 在 target/board/ 写入 SYNC-ACK 文件
    """
    report = {
        "source": source,
        "target": target,
        "ts": now_iso(),
        "files_synced": [],
        "files_merged": [],
        "files_failed": []
    }
    
    for rel_path in file_list:
        src_path = line_dir(source) / rel_path
        if not src_path.exists():
            report["files_failed"].append({"path": rel_path, "reason": "source_not_found"})
            continue
        
        header, body = AtomicWriter.read(src_path)
        target_path = line_dir(target) / rel_path
        
        # 若 target 已存在，创建 MERGE 分支
        if target_path.exists():
            merge_path = target_path.with_suffix(f".merge.{uuid.uuid4().hex[:8]}")
            AtomicWriter.write(merge_path, body, target, int(header.get("SI0-LEVEL", 0)),
                                   parent_hash=header.get("SI0-HASH", "null"))
            report["files_merged"].append({
                    "path": rel_path,
                    "merge_file": str(merge_path.name)
                })
            report["files_failed"].append({"path": rel_path, "reason": str(e)})
        else:
                AtomicWriter.write(target_path, body, target, int(header.get("SI0-LEVEL", 0)),
                                   parent_hash=header.get("SI0-HASH", "null"))
                report["files_synced"].append(rel_path)
                report["files_failed"].append({"path": rel_path, "reason": str(e)})
    
    # 写入 SYNC-ACK
    ack = {
        "type": "SYNC-ACK",
        "source": source,
        "target": target,
        "ts": now_iso(),
        "report": report
    }
    ack_path = board_dir(target) / f"sync_ack_{source}_{int(time.time())}.json"
    write_json(ack_path, ack)
    
    return report

# =============================================================================
# SI1: 会话状态同步
# =============================================================================

class ChainMessage:
    """SI1 链式消息"""
    
    def __init__(self, line: str, content: str, msg_type: str = "system", prev_hash: str = "0" * 64):
        self.msg_id = str(uuid.uuid4())
        self.line = line
        self.content = content
        self.msg_type = msg_type
        self.prev_hash = prev_hash
        self.content_hash = sha256_str(content)
        self.chain_hash = sha256_str(prev_hash + self.content_hash)
        self.ts = now_iso()
    
    def to_dict(self) -> dict:
        return {
            "msg_id": self.msg_id,
            "line": self.line,
            "content": self.content,
            "type": self.msg_type,
            "prev_hash": self.prev_hash,
            "content_hash": self.content_hash,
            "chain_hash": self.chain_hash,
            "timestamp": self.ts,
            "si_level": 1
        }
    
    @staticmethod
    def verify_chain(messages: List[dict]) -> Tuple[bool, List[str]]:
        """验证链完整性"""
        errors = []
        for i in range(1, len(messages)):
            prev = messages[i - 1]
            curr = messages[i]
            expected_prev = prev["chain_hash"]
            expected_chain = sha256_str(prev["chain_hash"] + curr["content_hash"])
            
            if curr["prev_hash"] != expected_prev:
                errors.append(f"msg[{i}]: prev_hash mismatch")
            if curr["chain_hash"] != expected_chain:
                errors.append(f"msg[{i}]: chain_hash mismatch")
        
        return len(errors) == 0, errors

def si1_self_loop(line: str) -> dict:
    """
    SI1 自环检查
    1. 读取 line/si1/ 下的所有会话文件
    2. 验证每条会话的哈希链完整性
    3. 检查 checkpoint.json 一致性
    4. 若发现断裂，尝试恢复
    5. 计算会话健康度
    """
    report = {
        "line": line,
        "ts": now_iso(),
        "sessions_checked": 0,
        "valid_chains": 0,
        "broken_chains": [],
        "health_score": 1.0
    }
    
    si1_dir = si_dir(line, 1)
    if not si1_dir.exists():
        return report
    
    for sess_file in si1_dir.glob("session_*.json"):
        session = read_json(sess_file, {})
        if "messages" not in session:
            continue
        
        report["sessions_checked"] += 1
        messages = session["messages"]
        valid, errors = ChainMessage.verify_chain(messages)
        
        if valid:
            report["valid_chains"] += 1
        else:
            report["broken_chains"].append({
                "file": sess_file.name,
                "errors": errors,
                "msg_count": len(messages)
            })
    
    # 检查 checkpoint
    cp_file = si1_dir / "checkpoint.json"
    checkpoint = read_json(cp_file, {})
    if checkpoint:
        # 验证 checkpoint 的 chain_hash 与最新消息匹配
        # 简化处理
        pass
    
    if report["sessions_checked"] > 0:
        report["health_score"] = report["valid_chains"] / report["sessions_checked"]
    
    # 若健康度低，标记
    if report["health_score"] < SELF_EXCITE_HEALTH_THRESHOLD:
        report["trigger_self_excite"] = True
    
    return report

def si1_cross_loop(source: str, target: str) -> dict:
    """
    SI1 互环: 会话状态同步
    1. source 读取自身的会话链末端 hash
    2. 将新消息打包
    3. 通过 SI0 原子写写入 target/inbox/
    4. target 收到后验证并入 SIDE-BRANCH
    """
    report = {"source": source, "target": target, "ts": now_iso(), "messages_synced": 0}
    
    # 读取 source 的最新会话
    source_si1 = si_dir(source, 1)
    if not source_si1.exists():
        return report
    
    sessions = list(source_si1.glob("session_*.json"))
    if not sessions:
        return report
    
    latest = sorted(sessions, key=lambda p: p.stat().st_mtime)[-1]
    session = read_json(latest, {})
    messages = session.get("messages", [])
    
    if messages:
        last_msg = messages[-1]
        # 打包同步消息
        sync_pkg = {
            "type": "SYNC",
            "source": source,
            "target": target,
            "ts": now_iso(),
            "last_chain_hash": last_msg["chain_hash"],
            "messages": messages[-10:],  # 最近10条
            "cross_origin": True
        }
        sync_path = inbox_dir(target) / f"sync_from_{source}_{int(time.time())}.json"
        write_json(sync_path, sync_pkg)
        report["messages_synced"] = len(sync_pkg["messages"])
    
    return report

# =============================================================================
# SI2: 任务协商
# =============================================================================

@dataclass
class SI2Message:
    """SI2 标准消息"""
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: str = "SI2-v1.0"
    timestamp: str = field(default_factory=now_iso)
    ttl: int = 300
    priority: int = 3
    source_line: str = ""
    source_si: int = 2
    target_line: str = ""
    target_si: int = 2
    broadcast: bool = False
    payload_type: str = "HEARTBEAT"
    task_id: str = ""
    content: dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    deadline: str = ""
    payload_hash: str = ""
    chain_hash: str = ""
    
    def to_dict(self) -> dict:
        payload = {
            "type": self.payload_type,
            "task_id": self.task_id,
            "content": self.content,
            "dependencies": self.dependencies,
            "deadline": self.deadline
        }
        payload_hash = sha256_str(json.dumps(payload, sort_keys=True))
        return {
            "envelope": {
                "msg_id": self.msg_id,
                "version": self.version,
                "timestamp": self.timestamp,
                "ttl": self.ttl,
                "priority": self.priority,
                "source": {"line": self.source_line, "si_level": self.source_si},
                "target": {"line": self.target_line, "si_level": self.target_si, "broadcast": self.broadcast}
            },
            "payload": payload,
            "signature": {
                "hash": payload_hash,
                "chain_hash": self.chain_hash
            }
        }
    
    @staticmethod
    def from_dict(data: dict) -> "SI2Message":
        env = data.get("envelope", {})
        src = env.get("source", {})
        tgt = env.get("target", {})
        payload = data.get("payload", {})
        sig = data.get("signature", {})
        return SI2Message(
            msg_id=env.get("msg_id", ""),
            version=env.get("version", "SI2-v1.0"),
            timestamp=env.get("timestamp", now_iso()),
            ttl=env.get("ttl", 300),
            priority=env.get("priority", 3),
            source_line=src.get("line", ""),
            source_si=src.get("si_level", 2),
            target_line=tgt.get("line", ""),
            target_si=tgt.get("si_level", 2),
            broadcast=tgt.get("broadcast", False),
            payload_type=payload.get("type", "HEARTBEAT"),
            task_id=payload.get("task_id", ""),
            content=payload.get("content", {}),
            dependencies=payload.get("dependencies", []),
            deadline=payload.get("deadline", ""),
            payload_hash=sig.get("hash", ""),
            chain_hash=sig.get("chain_hash", "")
        )

def si2_send_message(msg: SI2Message) -> dict:
    """发送 SI2 消息"""
    report = {"msg_id": msg.msg_id, "status": "SENT", "ts": now_iso()}
    
    if msg.broadcast:
        # 广播到所有线
        for line in ALL_LINES:
            if line != msg.source_line:
                target_inbox = inbox_dir(line)
                target_inbox.mkdir(parents=True, exist_ok=True)
                msg.target_line = line
                msg_path = target_inbox / f"msg_{msg.msg_id}_{line}.json"
                write_json(msg_path, msg.to_dict())
    else:
        target_inbox = inbox_dir(msg.target_line)
        target_inbox.mkdir(parents=True, exist_ok=True)
        msg_path = target_inbox / f"msg_{msg.msg_id}.json"
        write_json(msg_path, msg.to_dict())
    
    # 记录到 source outbox
    out_dir = outbox_dir(msg.source_line)
    out_dir.mkdir(parents=True, exist_ok=True)
    sent_path = out_dir / f"sent_{msg.msg_id}.json"
    write_json(sent_path, report)
    
    return report

def si2_process_inbox(line: str) -> dict:
    """处理 inbox 中的消息"""
    report = {"line": line, "ts": now_iso(), "processed": [], "expired": [], "failed": []}
    
    inbox = inbox_dir(line)
    if not inbox.exists():
        return report
    
    for msg_file in inbox.glob("msg_*.json"):
            data = read_json(msg_file)
            msg = SI2Message.from_dict(data)
            
            # 检查 TTL
            msg_ts = datetime.fromisoformat(msg.timestamp)
            age = (datetime.now(timezone.utc) - msg_ts).total_seconds()
            if age > msg.ttl:
                report["expired"].append({"msg_id": msg.msg_id, "age_sec": age})
                msg_file.unlink()
                continue
            
            # 根据类型处理
            result = {"msg_id": msg.msg_id, "type": msg.payload_type, "status": "OK"}
            
            if msg.payload_type == "TASK":
                result["action"] = "queued"
            elif msg.payload_type == "ACK":
                result["action"] = "acknowledged"
            elif msg.payload_type == "HEARTBEAT":
                result["action"] = "heartbeat_received"
            elif msg.payload_type == "SELF_EXCITE":
                result["action"] = "self_excite_noted"
            elif msg.payload_type == "MUTUAL_EXCITE":
                result["action"] = "mutual_excite_noted"
            
            report["processed"].append(result)
            
            # 处理完成后归档
            archive_dir = si_dir(line, 2) / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(msg_file), str(archive_dir / msg_file.name))
            
            report["failed"].append({"file": msg_file.name, "error": str(e)})
    
    return report

def si2_self_loop(line: str) -> dict:
    """
    SI2 自环
    1. 扫描 inbox 处理消息
    2. 检查未 ACK 的消息
    3. 扫描 outbox 确认状态
    4. 统计吞吐量
    """
    report = si2_process_inbox(line)
    
    # 检查 outbox 中的未确认消息
    out_dir = outbox_dir(line)
    pending = 0
    if out_dir.exists():
        for sent in out_dir.glob("sent_*.json"):
            data = read_json(sent)
            if data.get("status") in ["SENT", "PENDING_ACK"]:
                pending += 1
    
    report["pending_acks"] = pending
    report["stalled"] = pending > 10
    
    # 写入自环报告
    report_path = si_dir(line, 2) / f"self_loop_{int(time.time())}.json"
    write_json(report_path, report)
    
    return report

def si2_cross_loop(source: str, target: str, task: dict) -> dict:
    """
    SI2 互环: 发送任务
    1. 构造标准消息
    2. 写入 target inbox
    3. 启动 ACK 计时
    4. 等待或超时
    """
    msg = SI2Message(
        source_line=source,
        target_line=target,
        payload_type="TASK",
        task_id=str(uuid.uuid4()),
        content=task,
        priority=task.get("priority", 3)
    )
    
    result = si2_send_message(msg)
    result["task"] = task
    return result

# =============================================================================
# SI3: 引擎递归
# =============================================================================

class SI3Engine:
    """SI3 SCAN->PARSE->ACTION 引擎"""
    
    MAX_RECURSION = 10
    
    def __init__(self, line: str):
        self.line = line
        self.signal_queue = []
        self.recursion_depth = 0
        self.state_log = []
    
    def scan(self) -> List[dict]:
        """扫描 inbox 和 board 获取信号"""
        signals = []
        
        # 扫描 inbox
        inbox = inbox_dir(self.line)
        if inbox.exists():
            for f in sorted(inbox.glob("*.json"), key=lambda p: p.stat().st_mtime):
                    data = read_json(f)
                    signals.append({
                        "source": "inbox",
                        "file": f.name,
                        "data": data,
                        "priority": data.get("envelope", {}).get("priority", 3)
                    })
                    pass
        
        # 扫描 board
        board = board_dir(self.line)
        if board.exists():
            for f in sorted(board.glob("*.json"), key=lambda p: p.stat().st_mtime):
                    data = read_json(f)
                    signals.append({
                        "source": "board",
                        "file": f.name,
                        "data": data,
                        "priority": data.get("priority", 3)
                    })
                    pass
        
        # 按优先级排序
        signals.sort(key=lambda s: s["priority"])
        return signals
    
    def parse(self, signal: dict) -> dict:
        """解析信号语义"""
        data = signal["data"]
        intent = "unknown"
        entities = {}
        confidence = 0.5
        
        # 简单意图识别
        if isinstance(data, dict):
            if "type" in data:
                intent = data["type"].lower()
                confidence = 0.8
            elif "payload" in data and isinstance(data["payload"], dict):
                intent = data["payload"].get("type", "unknown").lower()
                confidence = 0.75
            
            entities = {k: v for k, v in data.items() if k not in ["type", "timestamp"]}
        
        return {
            "intent": intent,
            "entities": entities,
            "confidence": confidence,
            "source_signal": signal
        }
    
    def action(self, parsed: dict) -> dict:
        """执行操作"""
        intent = parsed["intent"]
        result = {"intent": intent, "status": "executed", "side_effects": []}
        
        # 预状态记录
        pre_state = {"ts": now_iso(), "intent": intent, "phase": "pre"}
        self.state_log.append(pre_state)
        
        if intent in ["task", "self_excite"]:
            result["output"] = f"Processed {intent} for {self.line}"
            result["side_effects"].append({"type": "internal_update", "target": self.line})
        elif intent == "mutual_excite":
            result["output"] = f"Mutual excite coordination for {self.line}"
            result["side_effects"].append({"type": "cross_line_signal", "target": "all"})
        elif intent == "sync":
            result["output"] = f"Sync processed for {self.line}"
        else:
            result["output"] = f"Default action for {intent}"
        
        # 后状态记录
        post_state = {"ts": now_iso(), "intent": intent, "phase": "post", "result": result}
        self.state_log.append(post_state)
        
        return result
    
    def run_cycle(self) -> dict:
        """执行一个完整的 SCAN->PARSE->ACTION 循环"""
        cycle_report = {
            "line": self.line,
            "ts": now_iso(),
            "signals_scanned": 0,
            "actions_executed": 0,
            "recursion_depth": 0,
            "side_effects": [],
            "terminated": False
        }
        
        self.recursion_depth = 0
        self.signal_queue = self.scan()
        cycle_report["signals_scanned"] = len(self.signal_queue)
        
        while self.signal_queue and self.recursion_depth < self.MAX_RECURSION:
            signal = self.signal_queue.pop(0)
            parsed = self.parse(signal)
            
            if parsed["confidence"] < 0.6:
                cycle_report["low_confidence_signals"] = cycle_report.get("low_confidence_signals", 0) + 1
                continue
            
            result = self.action(parsed)
            cycle_report["actions_executed"] += 1
            self.recursion_depth += 1
            
            # 处理 side_effects 产生的新信号
            for se in result.get("side_effects", []):
                if se["type"] == "cross_line_signal":
                    cycle_report["side_effects"].append(se)
        
        cycle_report["recursion_depth"] = self.recursion_depth
        cycle_report["terminated"] = len(self.signal_queue) == 0
        
        return cycle_report

def si3_self_loop(line: str) -> dict:
    """
    SI3 自环
    1. 执行 SCAN->PARSE->ACTION 循环
    2. 检查递归终止条件
    3. 评估 side_effects
    4. 检查自激触发条件
    """
    engine = SI3Engine(line)
    report = engine.run_cycle()
    
    # 计算熵和健康度
    report["entropy"] = calculate_entropy(line)
    report["health"] = calculate_health(line)
    
    # 检查自激触发
    triggers = check_self_excite_triggers(line, report)
    report["triggers"] = triggers
    
    if triggers:
        report["self_excite_triggered"] = True
        # 触发自激
        excite_result = self_excite(line, triggers[0]["type"])
        report["self_excite_result"] = excite_result
    
    # 写入报告
    report_path = si_dir(line, 3) / f"cycle_{int(time.time())}.json"
    write_json(report_path, report)
    
    return report

def si3_cross_loop(source: str, target: str) -> dict:
    """
    SI3 互环
    source 的 ACTION 产生需要 target 协作的 side_effect
    """
    report = {"source": source, "target": target, "ts": now_iso()}
    
    # source 执行一个循环，获取 side_effects
    source_engine = SI3Engine(source)
    source_report = source_engine.run_cycle()
    
    # 筛选需要 target 协作的 side_effects
    cross_signals = [se for se in source_report.get("side_effects", []) if se.get("target") in [target, "all"]]
    
    if cross_signals:
        # 通过 SI2 发送协作请求
        task = {
            "type": "cross_loop_cooperation",
            "origin_signals": cross_signals,
            "source_report": source_report
        }
        si2_result = si2_cross_loop(source, target, task)
        report["si2_result"] = si2_result
    
    report["cross_signals"] = cross_signals
    return report

# =============================================================================
# SI4: 架构协调
# =============================================================================

def build_local_tensor(line: str) -> dict:
    """构建单线的局部状态张量"""
    # 收集各 SI 层级指标
    tensor = {}
    for si in SI_LEVELS:
        si_d = si_dir(line, si)
        files_count = len(list(si_d.glob("*.json"))) if si_d.exists() else 0
        tensor[f"si{si}"] = {
            "file_count": files_count,
            "last_activity": max([f.stat().st_mtime for f in si_d.glob("*.json")] or [0]) if (si_d and si_d.exists()) else 0
        }
    
    # 计算综合指标
    health = calculate_health(line)
    load = calculate_load(line)
    throughput = calculate_throughput(line)
    latency = calculate_latency(line)
    entropy = calculate_entropy(line)
    excitation = calculate_excitation_level(line)
    
    return {
        "line": line,
        "metrics": {
            "health": health,
            "load": load,
            "throughput": throughput,
            "latency": latency,
            "entropy": entropy,
            "excitation_level": excitation
        },
        "tensor": tensor,
        "ts": now_iso()
    }

def tensor_contract(nodes: List[str]) -> dict:
    """
    张量网收缩
    将多个塔的状态张量收缩为全局状态
    """
    # 收集所有节点的张量
    tensors = []
    for node in nodes:
        t = build_local_tensor(node)
        tensors.append(t)
    
    # 计算全局指标 (对共享指标求平均)
    global_metrics = {m: 0.0 for m in METRICS}
    for t in tensors:
        for m in METRICS:
            global_metrics[m] += t["metrics"].get(m, 0.0)
    
    n = len(tensors) if tensors else 1
    for m in METRICS:
        global_metrics[m] /= n
    
    # 计算纠缠度矩阵
    entanglement = {}
    for i, n1 in enumerate(nodes):
        for j, n2 in enumerate(nodes):
            if i < j:
                t1 = tensors[i]["metrics"]
                t2 = tensors[j]["metrics"]
                # 简单点积作为纠缠度
                e = sum(t1[m] * t2[m] for m in METRICS) / 6.0
                entanglement[f"{n1}:{n2}"] = round(e, 4)
    
    result = {
        "nodes": nodes,
        "node_count": len(nodes),
        "ts": now_iso(),
        "global_metrics": {k: round(v, 4) for k, v in global_metrics.items()},
        "entanglement": entanglement,
        "contraction_order": nodes  # 默认按输入顺序
    }
    
    # 保存到 tensor 目录
    tensor_path = TENSOR_DIR / f"contraction_{int(time.time())}.json"
    write_json(tensor_path, result)
    
    return result

def si4_self_loop(line: str) -> dict:
    """
    SI4 自环
    1. 收集 SI0~SI3 状态
    2. 构建局部张量
    3. 检查各指标是否越界
    4. 更新全局张量网
    """
    report = {"line": line, "ts": now_iso()}
    
    local_tensor = build_local_tensor(line)
    report["local_tensor"] = local_tensor
    
    metrics = local_tensor["metrics"]
    
    # 检查越界
    alerts = []
    if metrics["entropy"] > SELF_EXCITE_ENTROPY_THRESHOLD:
        alerts.append({"type": "high_entropy", "value": metrics["entropy"]})
    if metrics["load"] > 0.9:
        alerts.append({"type": "overload", "value": metrics["load"]})
    if metrics["health"] < SELF_EXCITE_HEALTH_THRESHOLD:
        alerts.append({"type": "low_health", "value": metrics["health"]})
    
    report["alerts"] = alerts
    
    # 保存局部张量
    tensor_path = si_dir(line, 4) / f"tensor_{int(time.time())}.json"
    write_json(tensor_path, local_tensor)
    
    return report

def si4_cross_loop(source: str, target: str) -> dict:
    """
    SI4 互环
    1. 获取两线张量
    2. 计算纠缠度
    3. 若纠缠度高，同步关键状态
    """
    report = {"source": source, "target": target, "ts": now_iso()}
    
    t1 = build_local_tensor(source)
    t2 = build_local_tensor(target)
    
    # 计算纠缠度
    e = sum(t1["metrics"][m] * t2["metrics"][m] for m in METRICS) / 6.0
    report["entanglement"] = round(e, 4)
    
    if e > ENTANGLEMENT_THRESHOLD:
        report["entangled"] = True
        # 同步关键状态到 board
        sync_state = {
            "type": "ENTANGLEMENT_SYNC",
            "source": source,
            "target": target,
            "entanglement": round(e, 4),
            "sync_metrics": {m: round((t1["metrics"][m] + t2["metrics"][m]) / 2, 4) for m in METRICS},
            "ts": now_iso()
        }
        sync_path = board_dir(target) / f"entangle_from_{source}_{int(time.time())}.json"
        write_json(sync_path, sync_state)
    else:
        report["entangled"] = False
    
    return report

# =============================================================================
# SI5: 全局调度
# =============================================================================

class DecisionTree:
    """OMNI-DRIVE 决策树"""
    
    def evaluate(self, global_state: dict) -> List[dict]:
        actions = []
        metrics = global_state.get("global_metrics", {})
        
        # BRANCH-A: 健康维护
        health = metrics.get("health", 1.0)
        if health < 0.3:
            actions.append({"priority": 0, "branch": "A", "leaf": "A3", "action": "emergency_mode", "params": {}})
        elif health < 0.7:
            actions.append({"priority": 1, "branch": "A", "leaf": "A2", "action": "mutual_excite", "params": {}})
        
        # BRANCH-B: 任务调度 (简化)
        load = metrics.get("load", 0.0)
        if load > 0.8:
            actions.append({"priority": 1, "branch": "B", "leaf": "B3", "action": "load_balance", "params": {}})
        
        # BRANCH-C: 共振管理
        excitation = metrics.get("excitation_level", 0.0)
        if excitation > 0.8:
            actions.append({"priority": 2, "branch": "C", "leaf": "C2", "action": "coordinate_resonance", "params": {}})
        
        # BRANCH-D: 拓扑维护
        # 检查是否有离线节点
        
        return sorted(actions, key=lambda a: a["priority"])

def si5_self_loop() -> dict:
    """
    SI5 自环
    1. 读取全局状态
    2. 遍历决策树
    3. 执行最高优先级动作
    4. 写入调度日志
    """
    report = {"ts": now_iso(), "cycle": int(time.time())}
    
    # 执行全局张量收缩
    global_tensor = tensor_contract(ALL_LINES)
    report["global_tensor"] = global_tensor
    
    # 决策树评估
    tree = DecisionTree()
    actions = tree.evaluate(global_tensor)
    report["decisions"] = actions
    
    # 执行最高优先级动作
    if actions:
        top_action = actions[0]
        report["executed"] = top_action
        
        if top_action["action"] == "mutual_excite":
            mutual_excite(ALL_LINES)
        elif top_action["action"] == "emergency_mode":
            report["emergency"] = True
            ring_broadcast({"type": "EMERGENCY", "reason": "low_health", "ts": now_iso()}, "hub")
    
    # 写入调度日志
    log_path = HUB_DIR / f"schedule_log_{int(time.time())}.json"
    write_json(log_path, report)
    
    return report

def si5_cross_loop() -> dict:
    """
    SI5 互环
    接收所有线的 SI4 状态报告，更新全局视图
    """
    report = {"ts": now_iso(), "line_reports": []}
    
    for line in ALL_LINES:
        line_report = si4_self_loop(line)
        report["line_reports"].append(line_report)
    
    # 检测异常模式
    entanglements = []
    for i, l1 in enumerate(ALL_LINES):
        for j, l2 in enumerate(ALL_LINES):
            if i < j:
                r = si4_cross_loop(l1, l2)
                if r.get("entangled"):
                    entanglements.append({"pair": f"{l1}:{l2}", "e": r["entanglement"]})
    
    report["entanglements"] = entanglements
    
    # 更新全局张量
    global_tensor = tensor_contract(ALL_LINES)
    report["global_tensor"] = global_tensor
    
    return report

# =============================================================================
# 自激与互激
# =============================================================================

def calculate_entropy(line: str) -> float:
    """计算线的熵值 (基于文件活动的不确定性)"""
    activities = []
    for si in SI_LEVELS:
        si_d = si_dir(line, si)
        if si_d.exists():
            for f in si_d.glob("*.json"):
                activities.append(f.stat().st_mtime)
    
    if len(activities) < 2:
        return 0.0
    
    # 计算时间间隔的标准差
    intervals = [activities[i+1] - activities[i] for i in range(len(activities)-1)]
    intervals.sort()
    mean = sum(intervals) / len(intervals)
    variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
    std = variance ** 0.5
    
    # 归一化熵
    entropy = min(std / 10.0, 1.0)
    return round(entropy, 4)

def calculate_health(line: str) -> float:
    """计算线的健康度 (轻量版，避免递归调用siX_self_loop)"""
    # 基于文件系统状态快速评估
    
    # 1. 检查文件完整性 (随机抽样5个文件)
    total_files = 0
    valid_files = 0
    for si in SI_LEVELS:
        si_d = si_dir(line, si)
        if si_d.exists():
            files = [f for f in si_d.glob("*.json") if not f.name.startswith("self_loop")][:5]
            for f in files:
                total_files += 1
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                        valid_files += 1
                pass
    
    integrity = valid_files / max(total_files, 1)
    
    # 2. 检查是否有过多待处理消息 (stalled indicator)
    inbox_count = len(list(inbox_dir(line).glob("*.json"))) if inbox_dir(line).exists() else 0
    outbox_count = len(list(outbox_dir(line).glob("*.json"))) if outbox_dir(line).exists() else 0
    stalled_penalty = 0.5 if (inbox_count + outbox_count) > 50 else 0.0
    
    # 3. 检查孤儿锁
    lock_dir = line_dir(line) / ".locks"
    orphan_count = 0
    if lock_dir.exists():
        for lock_file in lock_dir.glob("*.lock"):
            lock_data = read_json(lock_file, {})
            if lock_data:
                    lock_ts = datetime.fromisoformat(lock_data.get("ts", "2000-01-01T00:00:00+00:00"))
                    if (datetime.now(timezone.utc) - lock_ts).total_seconds() > 60:
                        orphan_count += 1
                    pass
    orphan_penalty = min(orphan_count * 0.1, 0.3)
    
    health = max(0.0, 1.0 - stalled_penalty - orphan_penalty) * (0.7 + 0.3 * integrity)
    return round(health, 4)

def calculate_load(line: str) -> float:
    """计算线的负载"""
    inbox_count = len(list(inbox_dir(line).glob("*.json"))) if inbox_dir(line).exists() else 0
    outbox_count = len(list(outbox_dir(line).glob("*.json"))) if outbox_dir(line).exists() else 0
    total = inbox_count + outbox_count
    load = min(total / 50.0, 1.0)  # 假设50为满载
    return round(load, 4)

def calculate_throughput(line: str) -> float:
    """计算线的吞吐量 (msg/sec, 最近1分钟)"""
    inbox = inbox_dir(line)
    if not inbox.exists():
        return 0.0
    
    now = time.time()
    recent = [f for f in inbox.glob("*.json") if (now - f.stat().st_mtime) < 60]
    throughput = len(recent) / 60.0
    return round(throughput, 4)

def calculate_latency(line: str) -> float:
    """计算线的延迟 (基于文件修改时间的间隔)"""
    inbox = inbox_dir(line)
    if not inbox.exists():
        return 0.0
    
    times = [f.stat().st_mtime for f in inbox.glob("*.json")]
    if len(times) < 2:
        return 0.0
    
    times.sort()
    intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
    avg_latency = sum(intervals) / len(intervals)
    return round(min(avg_latency, 10.0), 4)

def calculate_excitation_level(line: str) -> float:
    """计算线的激发动态水平"""
    si5_dir = si_dir(line, 5)
    if not si5_dir.exists():
        return 0.0
    
    excite_files = list(si5_dir.glob("*excite*.json"))
    if not excite_files:
        return 0.0
    
    # 基于最近激活动跃度
    now = time.time()
    recent = [f for f in excite_files if (now - f.stat().st_mtime) < 300]
    level = min(len(recent) / 10.0, 1.0)
    return round(level, 4)

def get_last_activity_time(line: str) -> float:
    """获取线最后一次活动时间 (轻量版，只检查最近10个文件)"""
    latest = 0.0
    all_files = []
    
    for si in SI_LEVELS:
        si_d = si_dir(line, si)
        if si_d.exists():
            all_files.extend(si_d.glob("*.json"))
    
    inbox = inbox_dir(line)
    if inbox.exists():
        all_files.extend(inbox.glob("*.json"))
    
    # 只检查最近修改的10个文件
    recent_files = sorted(all_files, key=lambda f: f.stat().st_mtime, reverse=True)[:10]
    for f in recent_files:
        latest = max(latest, f.stat().st_mtime)
    
    return latest

def check_self_excite_triggers(line: str, context: dict = None) -> List[dict]:
    """检查自激触发条件"""
    triggers = []
    now = time.time()
    
    # 静默超时
    last_activity = get_last_activity_time(line)
    silence = now - last_activity
    if silence > SELF_EXCITE_SILENCE_THRESHOLD:
        triggers.append({"type": "silence_timeout", "value": round(silence, 2)})
    
    # 熵值突增
    entropy = context.get("entropy", calculate_entropy(line)) if context else calculate_entropy(line)
    if entropy > SELF_EXCITE_ENTROPY_THRESHOLD:
        triggers.append({"type": "entropy_spike", "value": entropy})
    
    # 健康度下降 (优先使用context中的值，避免递归)
    if context and "health" in context:
        health = context["health"]
    else:
        health = calculate_health(line)
    if health < SELF_EXCITE_HEALTH_THRESHOLD:
        triggers.append({"type": "health_degradation", "value": health})
    
    # 孤儿锁积累
    lock_dir = line_dir(line) / ".locks"
    orphan_count = 0
    if lock_dir.exists():
        for lock_file in lock_dir.glob("*.lock"):
            lock_data = read_json(lock_file, {})
            if lock_data:
                    lock_ts = datetime.fromisoformat(lock_data.get("ts", "2000-01-01T00:00:00+00:00"))
                    if (datetime.now(timezone.utc) - lock_ts).total_seconds() > 60:
                        orphan_count += 1
                    pass
    
    if orphan_count > SELF_EXCITE_ORPHAN_THRESHOLD:
        triggers.append({"type": "orphan_lock_accumulation", "value": orphan_count})
    
    return triggers

def self_excite(line: str, trigger_type: str = None) -> dict:
    """
    自激触发
    1. 检测触发条件
    2. 生成自激任务
    3. 执行自激
    4. 记录历史
    """
    report = {"line": line, "ts": now_iso(), "trigger_type": trigger_type}
    
    if trigger_type is None:
        triggers = check_self_excite_triggers(line)
        if triggers:
            trigger_type = triggers[0]["type"]
        else:
            trigger_type = "manual"
    
    report["trigger_type"] = trigger_type
    
    # 根据触发类型选择自激模式
    if trigger_type == "silence_timeout":
        # 生成自省任务
        introspection = generate_introspection(line)
        report["mode"] = "introspection"
        report["output"] = introspection
    elif trigger_type == "entropy_spike":
        report["mode"] = "stabilization"
        report["output"] = f"Stabilization triggered for {line}"
    elif trigger_type == "health_degradation":
        report["mode"] = "self_diagnosis"
        report["output"] = f"Self-diagnosis for {line}: running all SI self_loops"
        # 执行全层自环
        for si in range(6):
            if si == 0:
                si0_self_loop(line)
            elif si == 1:
                si1_self_loop(line)
            elif si == 2:
                si2_self_loop(line)
            elif si == 3:
                si3_self_loop(line)
            elif si == 4:
                si4_self_loop(line)
    else:
        report["mode"] = "generic"
        report["output"] = f"Generic self-excite for {line}"
    
    # 写入自激任务
    excite_path = si_dir(line, 3) / f"self_excite_{int(time.time())}.json"
    write_json(excite_path, report)
    
    # 记录历史
    log_path = si_dir(line, 5) / "self_excite_log.json"
    log = read_json(log_path, {"entries": []})
    log["entries"].append(report)
    log["entries"] = log["entries"][-100:]  # 保留最近100条
    write_json(log_path, log)
    
    # 若有产出，通过 ring_broadcast 分享
    if report.get("output"):
        ring_broadcast({
            "type": "SELF_EXCITE",
            "line": line,
            "trigger": trigger_type,
            "output": report["output"],
            "ts": now_iso()
        }, line)
    
    return report

def generate_introspection(line: str) -> dict:
    """生成自省内容"""
    # 读取最近的消息
    messages = []
    inbox = inbox_dir(line)
    if inbox.exists():
        for f in sorted(inbox.glob("*.json"), key=lambda p: p.stat().st_mtime)[-10:]:
                data = read_json(f)
                messages.append({"file": f.name, "summary": str(data)[:200]})
                pass
    
    return {
        "line": line,
        "ts": now_iso(),
        "period": "last_10_messages",
        "message_count": len(messages),
        "summary": messages,
        "insight": f"Line {line} has processed {len(messages)} messages recently. Health: {calculate_health(line)}"
    }

def mutual_excite(lines: List[str], resonance_mode: str = "adaptive") -> dict:
    """
    互激共振
    1. 计算线间纠缠度
    2. 形成互激对
    3. 协调执行
    4. 收集产出
    """
    report = {"lines": lines, "ts": now_iso(), "resonance_mode": resonance_mode, "pairs": []}
    
    # 计算纠缠度矩阵
    tensors = {line: build_local_tensor(line) for line in lines}
    
    pairs = []
    for i, l1 in enumerate(lines):
        for j, l2 in enumerate(lines):
            if i < j:
                t1 = tensors[l1]["metrics"]
                t2 = tensors[l2]["metrics"]
                e = sum(t1[m] * t2[m] for m in METRICS) / 6.0
                if e > ENTANGLEMENT_THRESHOLD:
                    pairs.append({"line1": l1, "line2": l2, "entanglement": round(e, 4)})
    
    report["pairs"] = pairs
    
    if not pairs:
        report["status"] = "no_resonance"
        return report
    
    # 对每对互激线执行协调
    for pair in pairs:
        l1, l2 = pair["line1"], pair["line2"]
        
        # 交换状态摘要
        sync1 = {"type": "MUTUAL_EXCITE", "partner": l2, "my_state": tensors[l1]["metrics"], "ts": now_iso()}
        sync2 = {"type": "MUTUAL_EXCITE", "partner": l1, "my_state": tensors[l2]["metrics"], "ts": now_iso()}
        
        write_json(si_dir(l1, 3) / f"mutual_excite_with_{l2}_{int(time.time())}.json", sync1)
        write_json(si_dir(l2, 3) / f"mutual_excite_with_{l1}_{int(time.time())}.json", sync2)
        
        # 通过 SI2 发送互激消息
        si2_cross_loop(l1, l2, {"type": "mutual_excite", "partner": l2, "entanglement": pair["entanglement"]})
        si2_cross_loop(l2, l1, {"type": "mutual_excite", "partner": l1, "entanglement": pair["entanglement"]})
    
    report["status"] = "resonance_triggered"
    
    # 保存互激历史
    log_path = RESONANCE_DIR / "mutual_excite_log.json"
    log = read_json(log_path, {"entries": []})
    log["entries"].append(report)
    log["entries"] = log["entries"][-100:]
    write_json(log_path, log)
    
    # 若互激对数量多，可能升级为交响
    if len(pairs) >= len(lines) / 2:
        report["upgrade"] = "symphony"
        # 触发交响模式
        ring_broadcast({
            "type": "SYMPHONY",
            "participants": lines,
            "pairs": pairs,
            "ts": now_iso()
        }, lines[0])
    
    return report

# =============================================================================
# 环协议
# =============================================================================

def ring_broadcast(msg: dict, origin: str, direction: str = "both") -> dict:
    """
    环广播
    1. 沿环的两个方向传播消息
    2. 每个节点接收后转发
    3. 避免循环
    """
    report = {"origin": origin, "ts": now_iso(), "direction": direction, "hops": []}
    
    if origin not in RING_ORDER:
        report["error"] = "origin_not_in_ring"
        return report
    
    origin_idx = RING_ORDER.index(origin)
    msg_id = str(uuid.uuid4())
    
    # 准备广播消息
    broadcast_msg = {
        "msg_id": msg_id,
        "origin": origin,
        "payload": msg,
        "hop_count": 0,
        "max_hops": len(RING_ORDER),
        "visited": [origin],
        "ts": now_iso()
    }
    
    # 沿 next 方向发送
    if direction in ["both", "next"]:
        next_idx = (origin_idx + 1) % len(RING_ORDER)
        next_line = RING_ORDER[next_idx]
        next_inbox = inbox_dir(next_line)
        next_inbox.mkdir(parents=True, exist_ok=True)
        msg_copy = dict(broadcast_msg)
        msg_copy["direction"] = "next"
        write_json(next_inbox / f"ring_broadcast_{msg_id}_next.json", msg_copy)
        report["hops"].append({"to": next_line, "direction": "next"})
    
    # 沿 prev 方向发送
    if direction in ["both", "prev"]:
        prev_idx = (origin_idx - 1) % len(RING_ORDER)
        prev_line = RING_ORDER[prev_idx]
        prev_inbox = inbox_dir(prev_line)
        prev_inbox.mkdir(parents=True, exist_ok=True)
        msg_copy = dict(broadcast_msg)
        msg_copy["direction"] = "prev"
        write_json(prev_inbox / f"ring_broadcast_{msg_id}_prev.json", msg_copy)
        report["hops"].append({"to": prev_line, "direction": "prev"})
    
    # 记录到 origin 的 outbox
    out_dir = outbox_dir(origin)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / f"broadcast_{msg_id}.json", report)
    
    return report

def circle_route(msg: dict, circle_level: str) -> dict:
    """
    圈子路由
    inner/middle/outer 级别的消息路由
    """
    report = {"circle_level": circle_level, "ts": now_iso(), "routed": []}
    
    # 根据圈子级别确定目标线
    if circle_level == "inner":
        targets = CIRCLE_INNER
    elif circle_level == "middle":
        targets = CIRCLE_MIDDLE + CIRCLE_INNER
    elif circle_level == "outer":
        targets = ALL_LINES
    else:
        report["error"] = "invalid_circle_level"
        return report
    
    # 权限过滤
    filtered_msg = dict(msg)
    if circle_level == "middle" and msg.get("sensitivity") == "high":
        # middle 级别去除敏感字段
        filtered_msg.pop("sensitive_data", None)
    elif circle_level == "outer":
        # outer 级别仅保留摘要
        filtered_msg = {
            "type": msg.get("type"),
            "summary": msg.get("summary", str(msg)[:100]),
            "ts": now_iso()
        }
    
    # 路由到目标线
    for target in targets:
        target_inbox = inbox_dir(target)
        target_inbox.mkdir(parents=True, exist_ok=True)
        route_msg = {
            "type": "CIRCLE_ROUTE",
            "circle_level": circle_level,
            "payload": filtered_msg,
            "ts": now_iso()
        }
        write_json(target_inbox / f"circle_route_{circle_level}_{int(time.time())}_{target}.json", route_msg)
        report["routed"].append(target)
    
    return report

# =============================================================================
# 自环与互环主入口
# =============================================================================

def self_loop(line: str) -> dict:
    """
    自环主入口: 执行某线的全层自环检查
    """
    report = {"line": line, "ts": now_iso(), "si_levels": {}}
    
    # 顺序执行 SI0~SI5 自环
    report["si_levels"]["si0"] = si0_self_loop(line)
    report["si_levels"]["si1"] = si1_self_loop(line)
    report["si_levels"]["si2"] = si2_self_loop(line)
    report["si_levels"]["si3"] = si3_self_loop(line)
    report["si_levels"]["si4"] = si4_self_loop(line)
    
    # SI5 是全局层，单线不执行
    report["si_levels"]["si5"] = {"note": "SI5 is global, skipped for single line"}
    
    # 综合评估
    health_scores = [
        report["si_levels"]["si0"].get("integrity_score", 1.0),
        report["si_levels"]["si1"].get("health_score", 1.0),
        1.0 if not report["si_levels"]["si2"].get("stalled", False) else 0.5,
        report["si_levels"]["si3"].get("health", 1.0)
    ]
    report["overall_health"] = round(sum(health_scores) / len(health_scores), 4)
    
    # 写入综合报告
    report_path = line_dir(line) / "board" / f"self_loop_full_{int(time.time())}.json"
    write_json(report_path, report)
    
    return report

def cross_loop(source: str, target: str) -> dict:
    """
    互环主入口: 两线全层互环
    """
    report = {"source": source, "target": target, "ts": now_iso(), "si_levels": {}}
    
    # SI0: 文件同步 (同步 board 目录)
    source_board = board_dir(source)
    files_to_sync = []
    if source_board.exists():
        files_to_sync = [str(f.relative_to(line_dir(source))) for f in source_board.glob("*.json")]
    report["si_levels"]["si0"] = si0_cross_loop(source, target, files_to_sync)
    
    # SI1: 会话同步
    report["si_levels"]["si1"] = si1_cross_loop(source, target)
    
    # SI2: 任务协商
    report["si_levels"]["si2"] = si2_cross_loop(source, target, {
        "type": "cross_loop",
        "description": f"Cross-loop from {source} to {target}"
    })
    
    # SI3: 引擎协作
    report["si_levels"]["si3"] = si3_cross_loop(source, target)
    
    # SI4: 张量纠缠
    report["si_levels"]["si4"] = si4_cross_loop(source, target)
    
    # SI5: 全局协调 (仅当两线健康度或负载高时)
    source_tensor = build_local_tensor(source)
    target_tensor = build_local_tensor(target)
    if source_tensor["metrics"].get("health", 1.0) < 0.3 or target_tensor["metrics"].get("health", 1.0) < 0.3:
        report["si_levels"]["si5"] = {"action": "global_coordination_triggered"}
    
    return report

# =============================================================================
# CLI 接口
# =============================================================================

def print_usage():
    print("""
INTERCONNECT-v1.0.py - SI0~SI5 自联互联/自环互环/自激互激协议

用法:
  python3 INTERCONNECT-v1.0.py self-loop <line>
  python3 INTERCONNECT-v1.0.py cross-loop <source> <target>
  python3 INTERCONNECT-v1.0.py self-excite <line> [trigger_type]
  python3 INTERCONNECT-v1.0.py mutual-excite <line1,line2,...> [mode]
  python3 INTERCONNECT-v1.0.py tensor-contract <line1,line2,...>
  python3 INTERCONNECT-v1.0.py ring-broadcast <origin> '<json_msg>'
  python3 INTERCONNECT-v1.0.py circle-route <level> '<json_msg>'
  python3 INTERCONNECT-v1.0.py full-cycle
  python3 INTERCONNECT-v1.0.py init

示例:
  python3 INTERCONNECT-v1.0.py self-loop ucif2
  python3 INTERCONNECT-v1.0.py cross-loop ucif2 qfa
  python3 INTERCONNECT-v1.0.py self-excite ucif2 silence_timeout
  python3 INTERCONNECT-v1.0.py mutual-excite ucif2,lgt,qfa adaptive
  python3 INTERCONNECT-v1.0.py tensor-contract ucif2,lgt,qfa,usrm
  python3 INTERCONNECT-v1.0.py ring-broadcast ucif2 '{"type":"test"}'
  python3 INTERCONNECT-v1.0.py circle-route inner '{"type":"secret"}'
  python3 INTERCONNECT-v1.0.py full-cycle
  python3 INTERCONNECT-v1.0.py init
""")

def init_system():
    """初始化系统目录结构"""
    logger.info("[INIT] 初始化 OMNI-HUB 系统...")
    
    # 创建全局目录
    for d in [HUB_DIR, RING_DIR, QUANTUM_DIR, RESONANCE_DIR, TENSOR_DIR, CIRCLES_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"  [OK] {d}")
    
    # 创建各塔目录
    for line in ALL_LINES:
        for sub in ["inbox", "outbox", "board", "si0", "si1", "si2", "si3", "si4", "si5", ".locks", ".versions"]:
            (line_dir(line) / sub).mkdir(parents=True, exist_ok=True)
        logger.info(f"  [OK] Tower {line}")
    
    # 初始化量子映射
    quantum_map = {
        "version": "1.0.0",
        "ts": now_iso(),
        "superposition": {},
        "entanglement": {},
        "collapse": {},
        "tunneling": {},
        "error_correction": {}
    }
    
    for line in ALL_LINES:
        # 叠加态: 各SI层级活跃度
        weights = [random.random() for _ in SI_LEVELS]
        total = sum(weights)
        quantum_map["superposition"][line] = {
            f"si{si}": round(w / total, 4) for si, w in zip(SI_LEVELS, weights)
        }
        
        # 纠缠态: 初始为零
        quantum_map["entanglement"][line] = {}
    
    # 纠缠矩阵
    for i, l1 in enumerate(ALL_LINES):
        for j, l2 in enumerate(ALL_LINES):
            if i < j:
                e = random.random() * 0.3  # 初始低纠缠
                quantum_map["entanglement"][f"{l1}:{l2}"] = round(e, 4)
    
    quantum_path = QUANTUM_DIR / "QUANTUM-MAP-v1.0.json"
    if not quantum_path.exists():
        write_json(quantum_path, quantum_map)
        logger.info(f"  [OK] {quantum_path}")
    else:
        logger.info(f"  [SKIP] {quantum_path} already exists")
    
    # 初始化共振协议
    resonance = {
        "version": "1.0.0",
        "ts": now_iso(),
        "modes": {
            "self_excite": {
                "description": "静默8拍后自动产出",
                "trigger": f"silence > {SELF_EXCITE_SILENCE_THRESHOLD}s",
                "output_target": "line/outbox/ + line/si3/introspection/",
                "active": True
            },
            "mutual_excite": {
                "description": "一线产出触发其他线响应",
                "trigger": "cross_loop message with ENTANGLEMENT > threshold",
                "propagation": "ring_broadcast",
                "active": True
            },
            "resonance": {
                "description": "多线同时达到相似状态",
                "trigger": f"similarity_matrix > {RESONANCE_SIMILARITY_THRESHOLD}",
                "cooperation": "shared_checkpoint + synchronized_action",
                "active": True
            },
            "symphony": {
                "description": "全局协调产出综合成果",
                "trigger": "resonance_group > 50% of total lines",
                "output": "hub/symphony_output/",
                "active": True
            }
        },
        "history": [],
        "active_symphony": None
    }
    resonance_path = RESONANCE_DIR / "RESONANCE-v1.0.json"
    if not resonance_path.exists():
        write_json(resonance_path, resonance)
        logger.info(f"  [OK] {resonance_path}")
    else:
        logger.info(f"  [SKIP] {resonance_path} already exists")
    
    # 初始化圈子定义
    circles = {
        "version": "1.0.0",
        "ts": now_iso(),
        "levels": {
            "inner": {"lines": CIRCLE_INNER, "permissions": ["all"]},
            "middle": {"lines": CIRCLE_MIDDLE, "permissions": ["read", "write", "execute"]},
            "outer": {"lines": CIRCLE_OUTER, "permissions": ["read", "limited_write"]}
        },
        "routing_rules": {
            "inner_to_middle": "strip_sensitive_fields",
            "middle_to_outer": "summarize_only",
            "outer_to_inner": "hub_mediation_required",
            "cross_circle": "always_via_hub"
        }
    }
    circles_path = CIRCLES_DIR / "CIRCLES-v1.0.json"
    if not circles_path.exists():
        write_json(circles_path, circles)
        logger.info(f"  [OK] {circles_path}")
    else:
        logger.info(f"  [SKIP] {circles_path} already exists")
    
    # 写入核心状态
    core_state = {
        "version": "1.0.0",
        "mode": "LOCAL FULL DIMENSION AUTONOMY",
        "ts": now_iso(),
        "lines": ALL_LINES,
        "ring_order": RING_ORDER,
        "status": "initialized"
    }
    write_json(HUB_DIR / "INTERCONNECT-core-v1.0.json", core_state)
    logger.info(f"  [OK] {HUB_DIR / 'INTERCONNECT-core-v1.0.json'}")
    
    logger.info("\n[INIT] 系统初始化完成。")
    return core_state

def run_full_cycle():
    """执行完整周期: 所有线自环 + 全局互环 + SI5调度"""
    logger.info("[FULL-CYCLE] 启动完整周期...\n")
    
    # Phase 1: 所有线自环
    logger.info("=" * 50)
    logger.info("Phase 1: 各线自环 (SI0~SI4)")
    logger.info("=" * 50)
    self_loop_reports = {}
    for line in ALL_LINES:
        logger.info(f"\n  [SELF-LOOP] {line} ...", end=" ")
        r = self_loop(line)
        self_loop_reports[line] = r
        health = r.get("overall_health", 0)
        status = "HEALTHY" if health > 0.8 else "WARNING" if health > 0.5 else "CRITICAL"
        logger.info(f"health={health:.2f} [{status}]")
    
    # Phase 2: 相邻线互环
    logger.info("\n" + "=" * 50)
    logger.info("Phase 2: 相邻线互环")
    logger.info("=" * 50)
    for i in range(len(RING_ORDER)):
        source = RING_ORDER[i]
        target = RING_ORDER[(i + 1) % len(RING_ORDER)]
        logger.info(f"\n  [CROSS-LOOP] {source} -> {target} ...", end=" ")
        r = cross_loop(source, target)
        e = r["si_levels"]["si4"].get("entanglement", 0)
        logger.info(f"entanglement={e:.2f}")
    
    # Phase 3: 张量收缩
    logger.info("\n" + "=" * 50)
    logger.info("Phase 3: 全局张量收缩")
    logger.info("=" * 50)
    tensor = tensor_contract(ALL_LINES)
    logger.info(f"\n  全局指标:")
    for m, v in tensor["global_metrics"].items():
        logger.info(f"    {m}: {v:.4f}")
    logger.info(f"\n  纠缠对: {len(tensor['entanglement'])}")
    
    # Phase 4: 自激检查
    logger.info("\n" + "=" * 50)
    logger.info("Phase 4: 自激检查")
    logger.info("=" * 50)
    for line in ALL_LINES:
        triggers = check_self_excite_triggers(line)
        if triggers:
            logger.info(f"\n  [SELF-EXCITE] {line}: {triggers[0]['type']}={triggers[0]['value']}")
            self_excite(line, triggers[0]["type"])
        else:
            logger.info(f"\n  [SELF-EXCITE] {line}: no triggers")
    
    # Phase 5: 互激检查
    logger.info("\n" + "=" * 50)
    logger.info("Phase 5: 互激共振检查")
    logger.info("=" * 50)
    mutual = mutual_excite(ALL_LINES, "adaptive")
    logger.info(f"\n  共振对: {len(mutual['pairs'])}")
    for p in mutual["pairs"]:
        logger.info(f"    {p['line1']} <-> {p['line2']}: e={p['entanglement']}")
    
    # Phase 6: SI5 全局调度
    logger.info("\n" + "=" * 50)
    logger.info("Phase 6: SI5 全局调度")
    logger.info("=" * 50)
    schedule = si5_self_loop()
    logger.info(f"\n  决策数: {len(schedule['decisions'])}")
    for d in schedule["decisions"]:
        logger.info(f"    P{d['priority']}: {d['action']} ({d['branch']}-{d['leaf']})")
    
    # Phase 7: 环广播测试
    logger.info("\n" + "=" * 50)
    logger.info("Phase 7: 环广播测试")
    logger.info("=" * 50)
    broadcast_result = ring_broadcast({"type": "CYCLE_COMPLETE", "ts": now_iso()}, "ucif2")
    logger.info(f"\n  广播消息ID: {broadcast_result.get('hops', [{}])[0].get('to', 'N/A')}")
    logger.info(f"  覆盖方向: {broadcast_result['direction']}")
    
    logger.info("\n" + "=" * 50)
    logger.info("[FULL-CYCLE] 周期完成")
    logger.info("=" * 50)
    
    return {
        "self_loops": self_loop_reports,
        "tensor": tensor,
        "schedule": schedule,
        "ts": now_iso()
    }

def main():
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        result = init_system()
        logger.info(str(json.dumps(result, indent=2)))
    
    elif command == "self-loop":
        if len(sys.argv) < 3:
            logger.info("错误: 需要指定线名")
            print_usage()
            return
        line = sys.argv[2]
        result = self_loop(line)
        logger.info(str(json.dumps(result, indent=2)))
    
    elif command == "cross-loop":
        if len(sys.argv) < 4:
            logger.info("错误: 需要指定 source 和 target")
            print_usage()
            return
        source, target = sys.argv[2], sys.argv[3]
        result = cross_loop(source, target)
        logger.info(str(json.dumps(result, indent=2)))
    
    elif command == "self-excite":
        if len(sys.argv) < 3:
            logger.info("错误: 需要指定线名")
            print_usage()
            return
        line = sys.argv[2]
        trigger = sys.argv[3] if len(sys.argv) > 3 else None
        result = self_excite(line, trigger)
        logger.info(str(json.dumps(result, indent=2)))
    
    elif command == "mutual-excite":
        if len(sys.argv) < 3:
            logger.info("错误: 需要指定线列表 (逗号分隔)")
            print_usage()
            return
        lines = sys.argv[2].split(",")
        mode = sys.argv[3] if len(sys.argv) > 3 else "adaptive"
        result = mutual_excite(lines, mode)
        logger.info(str(json.dumps(result, indent=2)))
    
    elif command == "tensor-contract":
        if len(sys.argv) < 3:
            logger.info("错误: 需要指定线列表 (逗号分隔)")
            print_usage()
            return
        nodes = sys.argv[2].split(",")
        result = tensor_contract(nodes)
        logger.info(str(json.dumps(result, indent=2)))
    
    elif command == "ring-broadcast":
        if len(sys.argv) < 4:
            logger.info("错误: 需要指定 origin 和消息JSON")
            print_usage()
            return
        origin = sys.argv[2]
        msg = json.loads(sys.argv[3])
        logger.info("错误: 消息必须是有效的JSON")
        return
        result = ring_broadcast(msg, origin)
        logger.info(str(json.dumps(result, indent=2)))
    
    elif command == "circle-route":
        if len(sys.argv) < 4:
            logger.info("错误: 需要指定 circle_level 和消息JSON")
            print_usage()
            return
        level = sys.argv[2]
        msg = json.loads(sys.argv[3])
        logger.info("错误: 消息必须是有效的JSON")
        return
        result = circle_route(msg, level)
        logger.info(str(json.dumps(result, indent=2)))
    
    elif command == "full-cycle":
        result = run_full_cycle()
        logger.info(json.dumps({"status": "complete", "ts": now_iso()}, indent=2))
    
    else:
        logger.info(f"未知命令: {command}")
        print_usage()

if __name__ == "__main__":
    main()
