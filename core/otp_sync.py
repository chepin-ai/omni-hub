
"""
otp_sync.py — OMNI-HUB v3.2
OTP@SI1会话端同步模块
自动在SI1会话端更新OS端会话记录，维护全11线会话状态一致性
"""

__version__ = "11.0.0"
import json
import time
import hashlib
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class SessionState:
    """单线会话状态"""
    line: str
    status: str = "idle"           # idle, active, degraded, offline
    health: float = 1.0            # 0.0 ~ 1.0
    si_level: int = 1              # SI层级 1-5
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class OTPSync:
    """OTP@SI1会话端同步 — 自动在SI1会话端更新OS端会话记录"""

    LINES = [f"L{i:02d}" for i in range(1, 12)]  # L01 ~ L11

    def __init__(self, state_path: str):
        self.state_path = state_path
        self.session_log: List[Dict] = []   # 会话操作日志
        self.sync_counter = 0
        self.os_sessions: Dict[str, SessionState] = {}   # OS端会话状态
        self.si1_sessions: Dict[str, SessionState] = {}  # SI1端会话状态
        self.conflict_log: List[Dict] = []
        self._ensure_state_dir()
        self._load_state()
        self._init_default_sessions()

    def _ensure_state_dir(self):
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)

    def _init_default_sessions(self):
        """初始化11线默认会话状态"""
        for line in self.LINES:
            if line not in self.os_sessions:
                self.os_sessions[line] = SessionState(
                    line=line,
                    status="idle",
                    health=1.0,
                    si_level=1,
                    metadata={"init": True}
                )
            if line not in self.si1_sessions:
                self.si1_sessions[line] = SessionState(
                    line=line,
                    status="idle",
                    health=1.0,
                    si_level=1,
                    metadata={"init": True}
                )

    def _load_state(self):
        """从磁盘加载状态"""
        if os.path.exists(self.state_path):
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for line, state_data in data.get("os_sessions", {}).items():
                    self.os_sessions[line] = SessionState.from_dict(state_data)
                for line, state_data in data.get("si1_sessions", {}).items():
                    self.si1_sessions[line] = SessionState.from_dict(state_data)
                self.sync_counter = data.get("sync_counter", 0)
                self.session_log = data.get("session_log", [])
                # 损坏的状态文件，记录日志后继续
                self._log("load_state_error", {"error": str(e)})

    def _save_state(self):
        """持久化状态到磁盘"""
        data = {
            "os_sessions": {k: v.to_dict() for k, v in self.os_sessions.items()},
            "si1_sessions": {k: v.to_dict() for k, v in self.si1_sessions.items()},
            "sync_counter": self.sync_counter,
            "session_log": self.session_log[-1000:],  # 保留最近1000条
            "saved_at": datetime.utcnow().isoformat() + "Z"
        }
        tmp_path = self.state_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.state_path)

    def _log(self, action: str, detail: dict):
        """记录会话操作日志"""
        entry = {
            "action": action,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "detail": detail
        }
        self.session_log.append(entry)

    def _hash_state(self, state: SessionState) -> str:
        """计算状态哈希，用于快速比较"""
        data = json.dumps(state.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def update_os_session(self, line: str, delta: dict) -> dict:
        """将SI1会话更新同步到OS端

        delta: {"field": str, "old_value": any, "new_value": any, "reason": str}
        返回: {"synced": bool, "line": str, "fields_updated": list, "timestamp": str}
        """
        if line not in self.LINES:
            return {"synced": False, "line": line, "fields_updated": [],
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "error": f"Invalid line '{line}', must be one of {self.LINES}"}

        if line not in self.si1_sessions:
            self.si1_sessions[line] = SessionState(line=line)

        si1 = self.si1_sessions[line]
        field_name = delta.get("field", "")
        new_value = delta.get("new_value")
        reason = delta.get("reason", "unspecified")

        fields_updated = []

        # 使用统一时间戳确保两端一致
        now_ts = datetime.utcnow().isoformat() + "Z"

        # 更新SI1端
        if hasattr(si1, field_name):
            old_val = getattr(si1, field_name)
            setattr(si1, field_name, new_value)
            si1.timestamp = now_ts
            fields_updated.append(field_name)
        elif field_name in si1.metadata:
            si1.metadata[field_name] = new_value
            si1.timestamp = now_ts
            fields_updated.append(field_name)
        else:
            # 作为metadata字段添加
            si1.metadata[field_name] = new_value
            si1.timestamp = now_ts
            fields_updated.append(field_name)

        # 同步到OS端
        if line not in self.os_sessions:
            self.os_sessions[line] = SessionState(line=line)

        os_state = self.os_sessions[line]
        if hasattr(os_state, field_name):
            setattr(os_state, field_name, new_value)
        else:
            os_state.metadata[field_name] = new_value
        os_state.timestamp = now_ts

        # 记录历史
        history_entry = {
            "action": "sync",
            "field": field_name,
            "old_value": delta.get("old_value"),
            "new_value": new_value,
            "reason": reason,
            "timestamp": si1.timestamp
        }
        si1.history.append(history_entry)
        os_state.history.append(history_entry)

        self.sync_counter += 1
        self._log("update_os_session", {
            "line": line,
            "field": field_name,
            "new_value": new_value,
            "reason": reason
        })
        self._save_state()

        return {
            "synced": True,
            "line": line,
            "fields_updated": fields_updated,
            "timestamp": si1.timestamp
        }

    def sync_all_lines(self) -> dict:
        """全11线会话同步

        遍历所有线，检查OS端与SI1端差异，自动同步
        返回: {"total_lines": 11, "synced": int, "conflicts": int, "resolved": int}
        """
        synced = 0
        conflicts = 0
        resolved = 0

        for line in self.LINES:
            os_state = self.os_sessions.get(line)
            si1_state = self.si1_sessions.get(line)

            if os_state is None:
                # OS端缺失，从SI1复制
                if si1_state:
                    self.os_sessions[line] = SessionState.from_dict(si1_state.to_dict())
                    synced += 1
                continue

            if si1_state is None:
                # SI1端缺失，从OS复制
                self.si1_sessions[line] = SessionState.from_dict(os_state.to_dict())
                synced += 1
                continue

            # 比较关键字段
            os_hash = self._hash_state(os_state)
            si1_hash = self._hash_state(si1_state)

            if os_hash == si1_hash:
                continue  # 一致，无需同步

            # 检查是否有冲突
            conflict_fields = self._detect_conflict_fields(os_state, si1_state)
            if conflict_fields:
                conflicts += 1
                result = self.resolve_conflict(line, os_state.to_dict(), si1_state.to_dict())
                if result.get("resolved"):
                    resolved += 1
                    winner = result.get("winner", "os")
                    winner_state = si1_state if winner == "si1" else os_state
                    loser_state = os_state if winner == "si1" else si1_state
                    # 将胜者完整状态复制到败者，确保完全一致
                    winner_dict = winner_state.to_dict()
                    now_ts = datetime.utcnow().isoformat() + "Z"
                    winner_dict["timestamp"] = now_ts
                    # 更新败者为胜者状态
                    for k, v in winner_dict.items():
                        if k != "line" and hasattr(loser_state, k):
                            setattr(loser_state, k, v)
                    # 同时更新胜者的timestamp保持一致
                    winner_state.timestamp = now_ts
                    synced += 1
            else:
                # 无冲突，单向同步（SI1 -> OS）
                self.os_sessions[line] = SessionState.from_dict(si1_state.to_dict())
                synced += 1

        self._log("sync_all_lines", {
            "synced": synced,
            "conflicts": conflicts,
            "resolved": resolved
        })
        self._save_state()

        return {
            "total_lines": 11,
            "synced": synced,
            "conflicts": conflicts,
            "resolved": resolved
        }

    def _detect_conflict_fields(self, os_state: SessionState, si1_state: SessionState) -> List[str]:
        """检测冲突字段（双方都修改过且值不同）"""
        conflicts = []
        for attr in ["status", "health", "si_level"]:
            if getattr(os_state, attr) != getattr(si1_state, attr):
                conflicts.append(attr)
        # 检查metadata
        all_meta_keys = set(os_state.metadata.keys()) | set(si1_state.metadata.keys())
        for key in all_meta_keys:
            if os_state.metadata.get(key) != si1_state.metadata.get(key):
                conflicts.append(key)
        return conflicts

    def resolve_conflict(self, line: str, os_state: dict, si1_state: dict) -> dict:
        """解决OS端与SI1端状态冲突

        策略:
            1) 时间戳新者优先
            2) SI层级高者优先
            3) 健康度高者优先
        返回: {"resolved": bool, "winner": "os|si1", "merged_fields": list}
        """
        os_ts = os_state.get("timestamp", "1970-01-01T00:00:00Z")
        si1_ts = si1_state.get("timestamp", "1970-01-01T00:00:00Z")

        winner = None
        reason = ""

        # 策略1: 时间戳新者优先
        if si1_ts > os_ts:
            winner = "si1"
            reason = "timestamp_newer"
        elif os_ts > si1_ts:
            winner = "os"
            reason = "timestamp_newer"
        else:
            # 策略2: SI层级高者优先
            os_level = os_state.get("si_level", 1)
            si1_level = si1_state.get("si_level", 1)
            if si1_level > os_level:
                winner = "si1"
                reason = "si_level_higher"
            elif os_level > si1_level:
                winner = "os"
                reason = "si_level_higher"
            else:
                # 策略3: 健康度高者优先
                os_health = os_state.get("health", 0.0)
                si1_health = si1_state.get("health", 0.0)
                if si1_health >= os_health:
                    winner = "si1"
                    reason = "health_higher_or_equal"
                else:
                    winner = "os"
                    reason = "health_higher"

        # 合并字段列表（取并集）
        merged_fields = list(set(os_state.keys()) | set(si1_state.keys()))
        # 排除非字段键
        merged_fields = [f for f in merged_fields if f not in ("history", "timestamp", "line")]

        self.conflict_log.append({
            "line": line,
            "winner": winner,
            "reason": reason,
            "os_timestamp": os_ts,
            "si1_timestamp": si1_ts,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

        self._log("resolve_conflict", {
            "line": line,
            "winner": winner,
            "reason": reason
        })

        return {
            "resolved": True,
            "winner": winner,
            "merged_fields": merged_fields,
            "reason": reason
        }

    def get_session_diff(self, line: str) -> dict:
        """获取会话差异报告

        返回OS端与SI1端的所有差异字段
        """
        if line not in self.LINES:
            return {"line": line, "error": f"Invalid line '{line}'",
                    "diff_fields": []}

        os_state = self.os_sessions.get(line)
        si1_state = self.si1_sessions.get(line)

        if os_state is None or si1_state is None:
            return {"line": line, "error": "State missing",
                    "diff_fields": [], "os_exists": os_state is not None,
                    "si1_exists": si1_state is not None}

        diff_fields = []
        for attr in ["status", "health", "si_level", "timestamp"]:
            os_val = getattr(os_state, attr)
            si1_val = getattr(si1_state, attr)
            if os_val != si1_val:
                diff_fields.append({
                    "field": attr,
                    "os_value": os_val,
                    "si1_value": si1_val
                })

        # metadata差异
        all_meta_keys = set(os_state.metadata.keys()) | set(si1_state.metadata.keys())
        for key in all_meta_keys:
            os_val = os_state.metadata.get(key)
            si1_val = si1_state.metadata.get(key)
            if os_val != si1_val:
                diff_fields.append({
                    "field": f"metadata.{key}",
                    "os_value": os_val,
                    "si1_value": si1_val
                })

        return {
            "line": line,
            "diff_count": len(diff_fields),
            "diff_fields": diff_fields,
            "in_sync": len(diff_fields) == 0
        }

    def checkpoint(self) -> dict:
        """创建会话同步检查点"""
        cp_id = hashlib.sha256(
            f"{self.sync_counter}_{time.time()}".encode()
        ).hexdigest()[:12]

        checkpoint_data = {
            "cp_id": cp_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sync_counter": self.sync_counter,
            "lines": {}
        }

        for line in self.LINES:
            os_state = self.os_sessions.get(line)
            si1_state = self.si1_sessions.get(line)
            checkpoint_data["lines"][line] = {
                "os_hash": self._hash_state(os_state) if os_state else None,
                "si1_hash": self._hash_state(si1_state) if si1_state else None,
                "in_sync": (self._hash_state(os_state) == self._hash_state(si1_state))
                            if (os_state and si1_state) else False
            }

        # 保存检查点到独立文件
        cp_path = self.state_path.replace(".json", f"_cp_{cp_id}.json")
    with open(cp_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

        self._log("checkpoint", {"cp_id": cp_id, "path": cp_path})

        return {
            "cp_id": cp_id,
            "timestamp": checkpoint_data["timestamp"],
            "sync_counter": self.sync_counter,
            "lines_checked": 11,
            "in_sync_count": sum(
                1 for v in checkpoint_data["lines"].values() if v["in_sync"]
            ),
            "checkpoint_path": cp_path
        }


# ==================== 测试块 ====================
"""
OMNI-HUB v11.0 — otp_sync
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""
if __name__ == "__main__":
    import tempfile
    import shutil

    # 创建临时目录
    tmpdir = tempfile.mkdtemp(prefix="omni_hub_test_")
    state_path = os.path.join(tmpdir, "otp_state.json")

    print("=" * 60)
    print("OTPSync 测试开始")
    print("=" * 60)

        # 1. 初始化
        print("\n[1] 初始化 OTPSync")
        sync = OTPSync(state_path=state_path)
        assert len(sync.os_sessions) == 11, "OS端应有11线"
        assert len(sync.si1_sessions) == 11, "SI1端应有11线"
        print("   ✓ 11线会话初始化完成")

        # 2. 更新OS会话
        print("\n[2] 测试 update_os_session")
        result = sync.update_os_session("L01", {
            "field": "status",
            "old_value": "idle",
            "new_value": "active",
            "reason": "user_login"
        })
        assert result["synced"] is True
        assert "status" in result["fields_updated"]
        assert sync.os_sessions["L01"].status == "active"
        assert sync.si1_sessions["L01"].status == "active"
        print(f"   ✓ L01 状态同步: idle -> active ({result['timestamp']})")

        # 更新metadata字段
        result = sync.update_os_session("L02", {
            "field": "session_id",
            "old_value": None,
            "new_value": "sess_abc123",
            "reason": "session_created"
        })
        assert result["synced"] is True
        assert sync.os_sessions["L02"].metadata["session_id"] == "sess_abc123"
        print("   ✓ L02 metadata 同步完成")

        # 3. 获取差异报告
        print("\n[3] 测试 get_session_diff"
        # 制造差异
        sync.os_sessions["L03"].health = 0.5
        sync.si1_sessions["L03"].health = 0.9
        diff = sync.get_session_diff("L03")
        assert diff["diff_count"] >= 1
        assert diff["in_sync"] is False
        health_diff = [d for d in diff["diff_fields"] if d["field"] == "health"]
        assert len(health_diff) == 1
        print(f"   ✓ L03 差异检测: health OS={health_diff[0]['os_value']} SI1={health_diff[0]['si1_value']}")

        diff_l01 = sync.get_session_diff("L01")
        assert diff_l01["in_sync"] is True
        print("   ✓ L01 状态一致")

        # 4. 全量同步
        print("\n[4] 测试 sync_all_lines")
        result = sync.sync_all_lines()
        assert result["total_lines"] == 11
        assert result["synced"] >= 1  # L03应被同步
        print(f"   ✓ 全量同步完成: synced={result['synced']}, conflicts={result['conflicts']}, resolved={result['resolved']}")

        # 同步后L03应一致
        diff_after = sync.get_session_diff("L03")
        assert diff_after["in_sync"] is True
        print("   ✓ L03 同步后状态一致")

        # 5. 冲突解决
        print("\n[5] 测试 resolve_conflict")
        # 制造冲突: 相同时间戳、不同值
        now = datetime.utcnow().isoformat() + "Z"
        os_st = {"status": "active", "health": 0.6, "si_level": 2,
                 "timestamp": now, "line": "L05", "metadata": {}}
        si1_st = {"status": "degraded", "health": 0.8, "si_level": 3,
                  "timestamp": now, "line": "L05", "metadata": {}}
        result = sync.resolve_conflict("L05", os_st, si1_st)
        assert result["resolved"] is True
        # 相同时间戳 -> SI层级高者优先 (si1_level=3 > os_level=2)
        assert result["winner"] == "si1"
        assert result["reason"] == "si_level_higher"
        print(f"   ✓ 冲突解决: winner={result['winner']}, reason={result['reason']}")

        # 时间戳不同的情况
        os_st2 = {"status": "active", "health": 0.9, "si_level": 5,
                  "timestamp": "2024-01-01T00:00:00Z", "line": "L06", "metadata": {}}
        si1_st2 = {"status": "degraded", "health": 0.1, "si_level": 1,
                   "timestamp": "2024-06-01T00:00:00Z", "line": "L06", "metadata": {}}
        result2 = sync.resolve_conflict("L06", os_st2, si1_st2)
        assert result2["winner"] == "si1"  # SI1时间戳更新
        assert result2["reason"] == "timestamp_newer"
        print(f"   ✓ 时间戳冲突: winner={result2['winner']}, reason={result2['reason']}")

        # 6. 检查点
        print("\n[6] 测试 checkpoint")
        cp = sync.checkpoint()
        assert cp["cp_id"] is not None
        assert cp["lines_checked"] == 11
        assert os.path.exists(cp["checkpoint_path"])
        print(f"   ✓ 检查点创建: cp_id={cp['cp_id']}, in_sync={cp['in_sync_count']}")

        # 7. 持久化验证
        print("\n[7] 测试 持久化")
        sync2 = OTPSync(state_path=state_path)
        assert sync2.os_sessions["L01"].status == "active"
        assert sync2.si1_sessions["L01"].status == "active"
        print("   ✓ 状态持久化与恢复成功")

        # 8. 无效线处理
        print("\n[8] 测试 边界情况")
        bad_result = sync.update_os_session("L99", {"field": "x", "new_value": 1})
        assert bad_result["synced"] is False
        print("   ✓ 无效线正确拒绝")

        print("\n" + "=" * 60)
        print("OTPSync 全部测试通过!")
        print("=" * 60)
