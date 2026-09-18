#!/usr/bin/env python3
"""
OMNI-HUB v11.1 三端同步引擎
Sandbox ↔ Github ↔ OS Sync Engine

功能模块:
  - SyncEngine:     主同步引擎，管理三端状态
  - PushQueue:      推送队列，支持优先级和依赖
  - ConflictResolver: 冲突检测与解决
  - SnapshotManager: 版本快照管理
  - SyncState:      文件状态追踪

作者: OMNI-HUB Core Team
版本: v11.1.0
日期: 2026-09-17
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import threading
import queue as thread_queue


# =============================================================================
# 常量与配置
# =============================================================================

VERSION = "11.1.0"
SYNC_DIR = ".sync"
DIRTY_DIR = f"{SYNC_DIR}/dirty"
SNAPSHOT_DIR = f"{SYNC_DIR}/snapshots"
CONFLICT_DIR = f"{SYNC_DIR}/conflicts"
LOG_DIR = f"{SYNC_DIR}/logs"
SYNCED_LOG = f"{SYNC_DIR}/synced"
MANIFEST_FILE = f"{SYNC_DIR}/manifest.json"

DEFAULT_IGNORE_PATTERNS = [
    "__pycache__", "*.pyc", "*.pyo", "*.egg-info",
    ".git", ".gitignore", ".DS_Store", "*.tmp", "*.temp",
    "*.log", "logs/", ".env", ".env.*", ".secrets/",
    "*.png", "*.jpg", "*.jpeg", "*.gif",  # 可视化产物
    "node_modules/", "dist/", "build/",
    "*.tar.gz", "*.tar.zst", "*.zip", "*.bundle",
    ".vscode/", ".idea/", "*.iml",
    ".pytest_cache/", ".ipynb_checkpoints/",
    "1a04*/",  # 临时会话目录
]

PROJECT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "OMNI-HUB": {
        "push": True,
        "targets": ["github", "os"],
        "frequency": "per_session",
        "additional_ignore": ["beat/beat-*.json", "beat/beat-*.md", "snapshots/"],
    },
    "01_Foundation": {
        "push": True,
        "targets": ["github"],
        "frequency": "weekly",
        "additional_ignore": ["*.aux", "*.synctex.gz"],
    },
    "02_Core_Results": {
        "push": True,
        "targets": ["github"],
        "frequency": "weekly",
        "additional_ignore": [],
    },
    "03_Geometric_Realization": {
        "push": True,
        "targets": ["github"],
        "frequency": "weekly",
        "additional_ignore": [],
    },
    "04_Applications": {
        "push": True,
        "targets": ["github"],
        "frequency": "weekly",
        "additional_ignore": [],
    },
    "05_Publications": {
        "push": True,
        "targets": ["github"],
        "frequency": "monthly",
        "additional_ignore": [],
    },
    "06_Code_Tools": {
        "push": True,
        "targets": ["github"],
        "frequency": "weekly",
        "additional_ignore": [],
    },
    "07_Whitepapers": {
        "push": True,
        "targets": ["github"],
        "frequency": "monthly",
        "additional_ignore": [],
    },
    "D4UniversalOptimality": {
        "push": True,
        "targets": ["github"],
        "frequency": "per_commit",
        "additional_ignore": [".lake/"],
    },
    "ucif2-formalization-kernel": {
        "push": True,
        "targets": ["github"],
        "frequency": "per_commit",
        "additional_ignore": [".cfts-state/", ".ci-inbox/", ".ucif2_audit_chain.jsonl"],
    },
    "app": {
        "push": True,
        "targets": ["github"],
        "frequency": "per_commit",
        "additional_ignore": ["dist/"],
    },
    "scratch-ax": {
        "push": "selective",
        "targets": ["github"],
        "frequency": "manual",
        "additional_ignore": ["*.tar.zst", "*.part*", "*.bundle"],
    },
    "formalization": {
        "push": True,
        "targets": ["github"],
        "frequency": "per_session",
        "additional_ignore": ["*.pdf"],
    },
    "UCIF2-OS-Source": {
        "push": True,
        "targets": ["github", "os"],
        "frequency": "per_commit",
        "additional_ignore": [],
    },
    "SI-MAX-01": {
        "push": True,
        "targets": ["github"],
        "frequency": "per_session",
        "additional_ignore": [],
    },
    "shadow-432": {
        "push": False,
        "targets": [],
        "frequency": "never",
        "additional_ignore": [],
    },
    "ucif2-migration-v25": {
        "push": False,
        "targets": [],
        "frequency": "never",
        "additional_ignore": [],
    },
}


# =============================================================================
# 枚举类型
# =============================================================================

class FileStatus(Enum):
    """文件同步状态"""
    CLEAN = auto()      # 已同步
    DIRTY = auto()      # 待同步
    SYNCING = auto()    # 同步中
    CONFLICT = auto()   # 冲突
    ERROR = auto()      # 错误
    FROZEN = auto()     # 冻结（永不推送）


class SyncPriority(Enum):
    """同步优先级"""
    CRITICAL = 1    # 关键配置，立即同步
    HIGH = 2        # 高优先级，30秒内
    NORMAL = 3      # 普通，批量处理
    LOW = 4         # 低优先级，闲时处理


class ConflictResolution(Enum):
    """冲突解决策略"""
    TIMESTAMP_WINS = auto()
    SANDBOX_WINS = auto()
    GITHUB_WINS = auto()
    MERGE = auto()
    MANUAL = auto()


# =============================================================================
# 数据类
# =============================================================================

@dataclass
class FileInfo:
    """文件元数据"""
    path: str
    size: int = 0
    mtime: float = 0.0
    sha256: str = ""
    status: FileStatus = FileStatus.CLEAN
    last_sync: Optional[float] = None
    sync_target: Optional[str] = None
    priority: SyncPriority = SyncPriority.NORMAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "size": self.size,
            "mtime": self.mtime,
            "sha256": self.sha256,
            "status": self.status.name,
            "last_sync": self.last_sync,
            "sync_target": self.sync_target,
            "priority": self.priority.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FileInfo:
        return cls(
            path=data["path"],
            size=data.get("size", 0),
            mtime=data.get("mtime", 0.0),
            sha256=data.get("sha256", ""),
            status=FileStatus[data.get("status", "CLEAN")],
            last_sync=data.get("last_sync"),
            sync_target=data.get("sync_target"),
            priority=SyncPriority[data.get("priority", "NORMAL")],
        )


@dataclass
class SyncEvent:
    """同步事件记录"""
    timestamp: str
    event_type: str
    project: str
    files_changed: int = 0
    files_added: int = 0
    files_removed: int = 0
    conflicts: int = 0
    duration_ms: int = 0
    commit_hash: str = ""
    trigger: str = ""
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConflictRecord:
    """冲突记录"""
    path: str
    detected_at: float
    sandbox_hash: str
    github_hash: str
    sandbox_mtime: float
    github_mtime: float
    resolution: Optional[ConflictResolution] = None
    resolved_at: Optional[float] = None
    resolution_detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "detected_at": self.detected_at,
            "sandbox_hash": self.sandbox_hash,
            "github_hash": self.github_hash,
            "sandbox_mtime": self.sandbox_mtime,
            "github_mtime": self.github_mtime,
            "resolution": self.resolution.name if self.resolution else None,
            "resolved_at": self.resolved_at,
            "resolution_detail": self.resolution_detail,
        }


# =============================================================================
# 工具函数
# =============================================================================

def compute_sha256(filepath: str) -> str:
    """计算文件 SHA256 哈希"""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (IOError, OSError):
        return ""


def get_file_info(filepath: str) -> FileInfo:
    """获取文件信息"""
    st = os.stat(filepath)
    return FileInfo(
        path=filepath,
        size=st.st_size,
        mtime=st.st_mtime,
        sha256=compute_sha256(filepath),
    )


def matches_ignore_patterns(rel_path: str, patterns: List[str]) -> bool:
    """检查路径是否匹配忽略模式"""
    parts = Path(rel_path).parts
    for pattern in patterns:
        # 精确匹配文件名
        if pattern.startswith("*"):
            suffix = pattern.lstrip("*")
            if rel_path.endswith(suffix):
                return True
        # 目录匹配
        if pattern.endswith("/"):
            dir_name = pattern.rstrip("/")
            if dir_name in parts:
                return True
        # 通配符匹配
        if "*" in pattern:
            import fnmatch
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                return True
        # 精确匹配
        if pattern in parts or pattern == os.path.basename(rel_path):
            return True
    return False


def ensure_dir(path: str) -> None:
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def timestamp_now() -> str:
    """获取当前 ISO 时间戳"""
    return datetime.now(timezone.utc).isoformat()


def format_duration_ms(start: float, end: float) -> int:
    """格式化耗时（毫秒）"""
    return int((end - start) * 1000)


# =============================================================================
# SyncState - 文件状态追踪
# =============================================================================

class SyncState:
    """
    文件状态追踪器
    维护沙箱中所有文件的同步状态
    """

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.state_file = self.root_dir / SYNC_DIR / "state.json"
        self.files: Dict[str, FileInfo] = {}
        self._lock = threading.RLock()
        self._load()

    def _load(self) -> None:
        """从磁盘加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for path, info_dict in data.get("files", {}).items():
                    self.files[path] = FileInfo.from_dict(info_dict)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"[SyncState] 警告: 状态文件加载失败: {e}")
                self.files = {}

    def save(self) -> None:
        """保存状态到磁盘"""
        ensure_dir(str(self.state_file.parent))
        with self._lock:
            data = {
                "version": VERSION,
                "updated_at": timestamp_now(),
                "files": {path: info.to_dict() for path, info in self.files.items()},
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def scan(self, project_name: Optional[str] = None) -> List[FileInfo]:
        """
        扫描目录，检测变更
        返回所有脏文件列表
        """
        dirty_files: List[FileInfo] = []
        # 如果 project_name 对应的子目录存在则扫描子目录，否则扫描 root_dir
        if project_name and (self.root_dir / project_name).exists():
            scan_dir = self.root_dir / project_name
        else:
            scan_dir = self.root_dir

        if not scan_dir.exists():
            return dirty_files

        ignore_patterns = DEFAULT_IGNORE_PATTERNS.copy()
        if project_name and project_name in PROJECT_CONFIGS:
            ignore_patterns.extend(PROJECT_CONFIGS[project_name].get("additional_ignore", []))

        # 收集当前所有文件
        current_paths: Set[str] = set()
        for filepath in scan_dir.rglob("*"):
            if not filepath.is_file():
                continue
            rel_path = str(filepath.relative_to(self.root_dir))
            if matches_ignore_patterns(rel_path, ignore_patterns):
                continue
            current_paths.add(rel_path)

            info = get_file_info(str(filepath))
            info.path = rel_path

            with self._lock:
                if rel_path in self.files:
                    old = self.files[rel_path]
                    if old.sha256 != info.sha256 or old.mtime != info.mtime:
                        info.status = FileStatus.DIRTY
                        info.priority = self._infer_priority(rel_path)
                        self.files[rel_path] = info
                        dirty_files.append(info)
                    elif old.status == FileStatus.DIRTY:
                        # 文件未变更但状态仍为 DIRTY（未成功同步），继续加入队列
                        info.status = FileStatus.DIRTY
                        info.priority = self._infer_priority(rel_path)
                        self.files[rel_path] = info
                        dirty_files.append(info)
                    else:
                        info.status = old.status
                        info.last_sync = old.last_sync
                        self.files[rel_path] = info
                else:
                    info.status = FileStatus.DIRTY
                    info.priority = self._infer_priority(rel_path)
                    self.files[rel_path] = info
                    dirty_files.append(info)

        # 检测删除的文件
        with self._lock:
            for path in list(self.files.keys()):
                if path not in current_paths and not matches_ignore_patterns(path, ignore_patterns):
                    if self.files[path].status != FileStatus.FROZEN:
                        self.files[path].status = FileStatus.DIRTY
                        dirty_files.append(self.files[path])

        return dirty_files

    def _infer_priority(self, path: str) -> SyncPriority:
        """根据文件类型推断同步优先级"""
        basename = os.path.basename(path)
        ext = Path(path).suffix.lower()

        # 关键配置文件 -> CRITICAL
        if basename in {"README.md", "ARCHITECTURE.md", "SYNC-STRATEGY.md"}:
            return SyncPriority.CRITICAL
        if ext in {".toml", ".yaml", ".yml", ".json"} and "config" in path.lower():
            return SyncPriority.CRITICAL

        # 源码文件 -> HIGH
        if ext in {".py", ".js", ".ts", ".lean", ".go", ".rs"}:
            return SyncPriority.HIGH

        # 文档 -> NORMAL
        if ext in {".md", ".rst", ".txt"}:
            return SyncPriority.NORMAL

        # 其他 -> LOW
        return SyncPriority.LOW

    def mark_synced(self, path: str, target: str = "github") -> None:
        """标记文件为已同步"""
        with self._lock:
            if path in self.files:
                self.files[path].status = FileStatus.CLEAN
                self.files[path].last_sync = time.time()
                self.files[path].sync_target = target

    def mark_frozen(self, path: str) -> None:
        """标记文件为冻结（永不推送）"""
        with self._lock:
            if path in self.files:
                self.files[path].status = FileStatus.FROZEN

    def get_status(self, path: str) -> Optional[FileStatus]:
        """获取文件状态"""
        with self._lock:
            info = self.files.get(path)
            return info.status if info else None

    def get_dirty_files(self) -> List[FileInfo]:
        """获取所有脏文件"""
        with self._lock:
            return [info for info in self.files.values() if info.status == FileStatus.DIRTY]

    def get_stats(self) -> Dict[str, int]:
        """获取状态统计"""
        with self._lock:
            stats = {s.name: 0 for s in FileStatus}
            for info in self.files.values():
                stats[info.status.name] += 1
            return stats


# =============================================================================
# PushQueue - 推送队列
# =============================================================================

class PushQueue:
    """
    优先级推送队列
    支持依赖关系检测和批量处理
    """

    def __init__(self):
        self._queue: thread_queue.PriorityQueue[Tuple[int, int, FileInfo]] = thread_queue.PriorityQueue()
        self._queued_paths: Set[str] = set()
        self._counter = 0
        self._lock = threading.RLock()
        self._history: List[Dict[str, Any]] = []

    def enqueue(self, file_info: FileInfo) -> bool:
        """将文件加入推送队列"""
        with self._lock:
            if file_info.path in self._queued_paths:
                return False
            self._counter += 1
            self._queue.put((file_info.priority.value, self._counter, file_info))
            self._queued_paths.add(file_info.path)
            return True

    def enqueue_many(self, files: List[FileInfo]) -> int:
        """批量加入队列"""
        count = 0
        for f in files:
            if self.enqueue(f):
                count += 1
        return count

    def dequeue(self) -> Optional[FileInfo]:
        """取出最高优先级文件"""
        try:
            _, _, file_info = self._queue.get(block=False)
            with self._lock:
                self._queued_paths.discard(file_info.path)
            return file_info
        except thread_queue.Empty:
            return None

    def dequeue_batch(self, max_size: int = 100) -> List[FileInfo]:
        """批量取出"""
        batch: List[FileInfo] = []
        for _ in range(max_size):
            item = self.dequeue()
            if item is None:
                break
            batch.append(item)
        return batch

    def is_empty(self) -> bool:
        """队列是否为空"""
        return self._queue.empty()

    def size(self) -> int:
        """队列大小"""
        return self._queue.qsize()

    def clear(self) -> None:
        """清空队列"""
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get(block=False)
                except thread_queue.Empty:
                    break
            self._queued_paths.clear()

    def get_history(self) -> List[Dict[str, Any]]:
        """获取推送历史"""
        return self._history.copy()

    def record_push(self, file_info: FileInfo, success: bool, target: str = "github") -> None:
        """记录推送结果"""
        self._history.append({
            "timestamp": timestamp_now(),
            "path": file_info.path,
            "priority": file_info.priority.name,
            "target": target,
            "success": success,
            "size": file_info.size,
        })


# =============================================================================
# ConflictResolver - 冲突解决
# =============================================================================

class ConflictResolver:
    """
    冲突检测与解决引擎
    实现三级仲裁机制
    """

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.conflicts: Dict[str, ConflictRecord] = {}
        self.conflict_file = self.root_dir / CONFLICT_DIR / "conflicts.json"
        self._load()

    def _load(self) -> None:
        """加载历史冲突记录"""
        if self.conflict_file.exists():
            try:
                with open(self.conflict_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for path, rec in data.get("conflicts", {}).items():
                    self.conflicts[path] = ConflictRecord(
                        path=rec["path"],
                        detected_at=rec["detected_at"],
                        sandbox_hash=rec["sandbox_hash"],
                        github_hash=rec["github_hash"],
                        sandbox_mtime=rec["sandbox_mtime"],
                        github_mtime=rec["github_mtime"],
                        resolution=ConflictResolution[rec["resolution"]] if rec.get("resolution") else None,
                        resolved_at=rec.get("resolved_at"),
                        resolution_detail=rec.get("resolution_detail", ""),
                    )
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[ConflictResolver] 警告: 冲突记录加载失败: {e}")

    def save(self) -> None:
        """保存冲突记录"""
        ensure_dir(str(self.conflict_file.parent))
        data = {
            "version": VERSION,
            "updated_at": timestamp_now(),
            "conflicts": {path: rec.to_dict() for path, rec in self.conflicts.items()},
        }
        with open(self.conflict_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def detect_conflict(self, path: str, sandbox_info: FileInfo, github_info: FileInfo) -> bool:
        """
        检测冲突
        返回 True 表示存在冲突
        """
        # 哈希相同 → 无冲突
        if sandbox_info.sha256 == github_info.sha256:
            return False

        # 时间戳差异在阈值内 → 可能并发修改
        time_diff = abs(sandbox_info.mtime - github_info.mtime)
        if time_diff < 300:  # 5分钟内
            return True

        # 时间戳差异大但内容不同 → 无冲突（按时间戳优先）
        return False

    def resolve(self, path: str, sandbox_info: FileInfo, github_info: FileInfo,
                strategy: ConflictResolution = ConflictResolution.TIMESTAMP_WINS) -> Tuple[bool, str]:
        """
        解决冲突
        返回 (成功, 详情)
        """
        record = ConflictRecord(
            path=path,
            detected_at=time.time(),
            sandbox_hash=sandbox_info.sha256,
            github_hash=github_info.sha256,
            sandbox_mtime=sandbox_info.mtime,
            github_mtime=github_info.mtime,
        )

        if strategy == ConflictResolution.TIMESTAMP_WINS:
            if sandbox_info.mtime >= github_info.mtime:
                record.resolution = ConflictResolution.TIMESTAMP_WINS
                record.resolution_detail = f"沙箱版本较新 (mtime {sandbox_info.mtime} > {github_info.mtime})"
                record.resolved_at = time.time()
                self.conflicts[path] = record
                return True, record.resolution_detail
            else:
                record.resolution = ConflictResolution.TIMESTAMP_WINS
                record.resolution_detail = f"Github版本较新 (mtime {github_info.mtime} > {sandbox_info.mtime})"
                record.resolved_at = time.time()
                self.conflicts[path] = record
                return False, record.resolution_detail  # 不需要推送

        elif strategy == ConflictResolution.SANDBOX_WINS:
            record.resolution = ConflictResolution.SANDBOX_WINS
            record.resolution_detail = "强制使用沙箱版本"
            record.resolved_at = time.time()
            self.conflicts[path] = record
            return True, record.resolution_detail

        elif strategy == ConflictResolution.GITHUB_WINS:
            record.resolution = ConflictResolution.GITHUB_WINS
            record.resolution_detail = "强制使用Github版本"
            record.resolved_at = time.time()
            self.conflicts[path] = record
            return False, record.resolution_detail

        elif strategy == ConflictResolution.MANUAL:
            record.resolution = ConflictResolution.MANUAL
            record.resolution_detail = "等待人工仲裁"
            self.conflicts[path] = record
            self._generate_conflict_report(path, sandbox_info, github_info)
            return False, record.resolution_detail

        return False, "未知策略"

    def _generate_conflict_report(self, path: str, sandbox_info: FileInfo, github_info: FileInfo) -> None:
        """生成冲突报告文件"""
        report_dir = self.root_dir / CONFLICT_DIR
        ensure_dir(str(report_dir))
        report_path = report_dir / f"CONFLICT-{Path(path).name}-{int(time.time())}.md"

        report = f"""# 冲突报告

**文件**: `{path}`
**检测时间**: {timestamp_now()}

## 沙箱版本

- **大小**: {sandbox_info.size} bytes
- **修改时间**: {datetime.fromtimestamp(sandbox_info.mtime, tz=timezone.utc).isoformat()}
- **SHA256**: `{sandbox_info.sha256}`

## Github版本

- **大小**: {github_info.size} bytes
- **修改时间**: {datetime.fromtimestamp(github_info.mtime, tz=timezone.utc).isoformat()}
- **SHA256**: `{github_info.sha256}`

## 解决方式

请运行以下命令之一进行仲裁:

```bash
# 使用沙箱版本
sync resolve --path "{path}" --strategy sandbox-wins

# 使用Github版本
sync resolve --path "{path}" --strategy github-wins

# 手动合并
sync resolve --path "{path}" --strategy manual
```
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

    def get_unresolved(self) -> List[ConflictRecord]:
        """获取未解决的冲突"""
        return [rec for rec in self.conflicts.values() if rec.resolved_at is None]

    def get_stats(self) -> Dict[str, int]:
        """获取冲突统计"""
        total = len(self.conflicts)
        unresolved = len(self.get_unresolved())
        return {
            "total": total,
            "resolved": total - unresolved,
            "unresolved": unresolved,
        }


# =============================================================================
# SnapshotManager - 版本快照
# =============================================================================

class SnapshotManager:
    """
    版本快照管理器
    支持会话/预推送/日/周四级快照
    """

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.snapshot_base = self.root_dir / SNAPSHOT_DIR
        ensure_dir(str(self.snapshot_base))
        self._limits = {
            "session": 10,
            "pre-push": 50,
            "daily": 30,
            "weekly": 12,
        }

    def _snapshot_path(self, kind: str, name: str) -> Path:
        """获取快照路径"""
        snap_dir = self.snapshot_base / kind
        ensure_dir(str(snap_dir))
        return snap_dir / f"{name}.tar.gz"

    def create(self, kind: str, name: Optional[str] = None,
               include_paths: Optional[List[str]] = None) -> str:
        """
        创建快照
        返回快照文件路径
        """
        if name is None:
            name = f"{kind}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}Z"

        snap_path = self._snapshot_path(kind, name)

        # 使用 tarfile 创建快照
        import tarfile
        with tarfile.open(snap_path, "w:gz") as tar:
            if include_paths:
                for p in include_paths:
                    full = self.root_dir / p
                    if full.exists():
                        tar.add(str(full), arcname=p)
            else:
                # 默认快照整个项目（排除 .sync 和忽略模式）
                for item in self.root_dir.rglob("*"):
                    rel = str(item.relative_to(self.root_dir))
                    if matches_ignore_patterns(rel, [SYNC_DIR, ".git"]):
                        continue
                    if item.is_file():
                        tar.add(str(item), arcname=rel)

        # 清理旧快照
        self._cleanup(kind)
        return str(snap_path)

    def _cleanup(self, kind: str) -> None:
        """清理超出限制的旧快照"""
        snap_dir = self.snapshot_base / kind
        if not snap_dir.exists():
            return

        snaps = sorted(snap_dir.glob("*.tar.gz"), key=lambda p: p.stat().st_mtime)
        limit = self._limits.get(kind, 10)
        while len(snaps) > limit:
            old = snaps.pop(0)
            try:
                old.unlink()
            except OSError:
                pass

    def restore(self, kind: str, name: str) -> List[str]:
        """
        恢复快照
        返回恢复的文件列表
        """
        snap_path = self._snapshot_path(kind, name)
        if not snap_path.exists():
            return []

        import tarfile
        restored: List[str] = []
        with tarfile.open(snap_path, "r:gz") as tar:
            for member in tar.getmembers():
                tar.extract(member, str(self.root_dir))
                restored.append(member.name)
        return restored

    def list_snapshots(self, kind: Optional[str] = None) -> Dict[str, List[str]]:
        """列出所有快照"""
        result: Dict[str, List[str]] = {}
        kinds = [kind] if kind else ["session", "pre-push", "daily", "weekly"]
        for k in kinds:
            snap_dir = self.snapshot_base / k
            if snap_dir.exists():
                result[k] = sorted([p.stem for p in snap_dir.glob("*.tar.gz")])
        return result

    def create_session_snapshot(self) -> str:
        """创建会话快照"""
        return self.create("session", f"session-{int(time.time())}")

    def create_pre_push_snapshot(self, project: str) -> str:
        """创建预推送快照"""
        return self.create("pre-push", f"pre-push-{project}-{int(time.time())}")

    def create_daily_snapshot(self) -> str:
        """创建日快照"""
        name = f"daily-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        return self.create("daily", name)


# =============================================================================
# SyncEngine - 主同步引擎
# =============================================================================

class SyncEngine:
    """
    OMNI-HUB 三端同步主引擎

    职责:
      1. 管理三端状态映射
      2. 调度推送队列
      3. 协调冲突解决
      4. 维护版本快照
      5. 生成同步报告
    """

    def __init__(self, root_dir: str, project_name: str = "OMNI-HUB"):
        self.root_dir = Path(root_dir).resolve()
        self.project_name = project_name
        self.state = SyncState(str(self.root_dir))
        self.push_queue = PushQueue()
        self.conflict_resolver = ConflictResolver(str(self.root_dir))
        self.snapshot_mgr = SnapshotManager(str(self.root_dir))
        self.event_log: List[SyncEvent] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._github_mirror: Path = self.root_dir / SYNC_DIR / "mirror_github"
        self._os_mirror: Path = self.root_dir / SYNC_DIR / "mirror_os"
        ensure_dir(str(self._github_mirror))
        ensure_dir(str(self._os_mirror))

    # -------------------------------------------------------------------------
    # 初始化
    # -------------------------------------------------------------------------

    def init(self) -> Dict[str, Any]:
        """
        初始化同步环境
        创建必要的目录结构和配置文件
        """
        dirs = [SYNC_DIR, DIRTY_DIR, SNAPSHOT_DIR, CONFLICT_DIR, LOG_DIR, SYNCED_LOG]
        created = []
        for d in dirs:
            path = self.root_dir / d
            ensure_dir(str(path))
            created.append(str(path))

        # 创建项目清单
        manifest = {
            "version": VERSION,
            "project": self.project_name,
            "created_at": timestamp_now(),
            "root_dir": str(self.root_dir),
            "config": PROJECT_CONFIGS.get(self.project_name, {}),
        }
        manifest_path = self.root_dir / MANIFEST_FILE
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        # 创建全局 .gitignore
        gitignore_path = self.root_dir / SYNC_DIR / "global.gitignore"
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("\n".join(DEFAULT_IGNORE_PATTERNS) + "\n")

        # 创建会话快照
        snap = self.snapshot_mgr.create_session_snapshot()

        return {
            "status": "initialized",
            "directories": created,
            "manifest": str(manifest_path),
            "gitignore": str(gitignore_path),
            "session_snapshot": snap,
        }

    # -------------------------------------------------------------------------
    # 扫描与队列
    # -------------------------------------------------------------------------

    def scan(self) -> Dict[str, Any]:
        """
        扫描项目变更
        返回变更统计
        """
        dirty = self.state.scan(self.project_name)
        enqueued = self.push_queue.enqueue_many(dirty)

        return {
            "scanned": len(dirty),
            "enqueued": enqueued,
            "queue_size": self.push_queue.size(),
            "by_priority": self._count_by_priority(dirty),
        }

    def _count_by_priority(self, files: List[FileInfo]) -> Dict[str, int]:
        """按优先级统计"""
        counts: Dict[str, int] = {}
        for f in files:
            p = f.priority.name
            counts[p] = counts.get(p, 0) + 1
        return counts

    # -------------------------------------------------------------------------
    # 推送
    # -------------------------------------------------------------------------

    def push(self, target: str = "github", dry_run: bool = False,
             batch_size: int = 100) -> Dict[str, Any]:
        """
        执行推送
        target: "github" | "os" | "all"
        """
        start_time = time.time()
        targets = ["github", "os"] if target == "all" else [target]

        # 预推送快照
        pre_push_snap = self.snapshot_mgr.create_pre_push_snapshot(self.project_name)

        results = {"github": [], "os": []}
        conflicts = 0
        success_count = 0
        fail_count = 0

        for tgt in targets:
            mirror = self._github_mirror if tgt == "github" else self._os_mirror
            mirror_project = mirror / self.project_name
            ensure_dir(str(mirror_project))

            batch = self.push_queue.dequeue_batch(batch_size)
            if not batch:
                continue

            for file_info in batch:
                result = self._push_single(file_info, tgt, mirror_project, dry_run)
                if result["status"] == "conflict":
                    conflicts += 1
                elif result["status"] == "success":
                    success_count += 1
                    self.state.mark_synced(file_info.path, tgt)
                    self.push_queue.record_push(file_info, True, tgt)
                elif result["status"] == "dry_run":
                    success_count += 1  # dry_run 视为成功预览
                elif result["status"] in ("deleted", "unchanged"):
                    success_count += 1  # 已删除或无需变更也视为处理成功
                else:
                    fail_count += 1
                    self.push_queue.record_push(file_info, False, tgt)

                results[tgt].append(result)

        duration = format_duration_ms(start_time, time.time())

        # 记录事件
        event = SyncEvent(
            timestamp=timestamp_now(),
            event_type="SYNC_PUSH",
            project=self.project_name,
            files_changed=success_count + fail_count,
            files_added=success_count,
            files_removed=0,
            conflicts=conflicts,
            duration_ms=duration,
            commit_hash="dry-run" if dry_run else self._generate_commit_hash(),
            trigger="manual",
            details=f"target={target}, dry_run={dry_run}",
        )
        self._log_event(event)

        return {
            "targets": targets,
            "dry_run": dry_run,
            "success": success_count,
            "failed": fail_count,
            "conflicts": conflicts,
            "duration_ms": duration,
            "pre_push_snapshot": pre_push_snap,
            "details": results,
        }

    def _push_single(self, file_info: FileInfo, target: str,
                     mirror_project: Path, dry_run: bool) -> Dict[str, Any]:
        """推送单个文件"""
        src = self.root_dir / file_info.path
        dst = mirror_project / file_info.path

        if not src.exists():
            # 文件已被删除
            if not dry_run and dst.exists():
                dst.unlink()
            return {"path": file_info.path, "status": "deleted", "target": target}

        # 检查目标是否已存在且不同
        if dst.exists():
            dst_info = get_file_info(str(dst))
            if dst_info.sha256 == file_info.sha256:
                return {"path": file_info.path, "status": "unchanged", "target": target}

            # 冲突检测
            if dst_info.mtime != file_info.mtime:
                is_conflict = self.conflict_resolver.detect_conflict(
                    file_info.path, file_info, dst_info
                )
                if is_conflict:
                    should_push, detail = self.conflict_resolver.resolve(
                        file_info.path, file_info, dst_info,
                        ConflictResolution.TIMESTAMP_WINS
                    )
                    if not should_push:
                        return {
                            "path": file_info.path,
                            "status": "conflict",
                            "target": target,
                            "detail": detail,
                        }

        # 执行复制
        if not dry_run:
            ensure_dir(str(dst.parent))
            shutil.copy2(str(src), str(dst))
            self.state.mark_synced(file_info.path, target)

        if dry_run:
            return {
                "path": file_info.path,
                "status": "dry_run",
                "target": target,
                "size": file_info.size,
            }

        return {
            "path": file_info.path,
            "status": "success",
            "target": target,
            "size": file_info.size,
        }

    def _generate_commit_hash(self) -> str:
        """生成伪提交哈希"""
        data = f"{self.project_name}:{timestamp_now()}:{time.time()}"
        return hashlib.sha1(data.encode()).hexdigest()[:12]

    # -------------------------------------------------------------------------
    # 回滚
    # -------------------------------------------------------------------------

    def rollback(self, snapshot_kind: str, snapshot_name: str) -> Dict[str, Any]:
        """
        回滚到指定快照
        """
        restored = self.snapshot_mgr.restore(snapshot_kind, snapshot_name)
        return {
            "status": "rolled_back",
            "snapshot_kind": snapshot_kind,
            "snapshot_name": snapshot_name,
            "restored_files": len(restored),
            "restored_paths": restored[:20],  # 只显示前20个
        }

    # -------------------------------------------------------------------------
    # 报告与查询
    # -------------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        """获取同步状态概览"""
        state_stats = self.state.get_stats()
        conflict_stats = self.conflict_resolver.get_stats()
        queue_size = self.push_queue.size()
        snapshots = self.snapshot_mgr.list_snapshots()

        return {
            "project": self.project_name,
            "version": VERSION,
            "timestamp": timestamp_now(),
            "file_states": state_stats,
            "queue_size": queue_size,
            "conflicts": conflict_stats,
            "snapshots": {k: len(v) for k, v in snapshots.items()},
            "root_dir": str(self.root_dir),
        }

    def report(self) -> str:
        """生成文本报告"""
        s = self.status()
        lines = [
            "=" * 60,
            f"OMNI-HUB Sync Report v{VERSION}",
            f"Project: {s['project']}",
            f"Timestamp: {s['timestamp']}",
            "=" * 60,
            "",
            "File States:",
        ]
        for state_name, count in s["file_states"].items():
            lines.append(f"  {state_name:12s}: {count:6d}")

        lines.extend([
            "",
            f"Queue Size: {s['queue_size']}",
            "",
            "Conflicts:",
            f"  Total:      {s['conflicts']['total']}",
            f"  Resolved:   {s['conflicts']['resolved']}",
            f"  Unresolved: {s['conflicts']['unresolved']}",
            "",
            "Snapshots:",
        ])
        for kind, count in s["snapshots"].items():
            lines.append(f"  {kind:12s}: {count:3d}")

        lines.extend(["", "=" * 60])
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # 事件日志
    # -------------------------------------------------------------------------

    def _log_event(self, event: SyncEvent) -> None:
        """记录同步事件"""
        self.event_log.append(event)
        log_file = self.root_dir / LOG_DIR / "sync.log"
        ensure_dir(str(log_file.parent))
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    def get_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近事件"""
        return [e.to_dict() for e in self.event_log[-limit:]]

    # -------------------------------------------------------------------------
    # 自动同步守护
    # -------------------------------------------------------------------------

    def start_daemon(self, interval: int = 300) -> None:
        """
        启动自动同步守护线程
        interval: 扫描间隔（秒）
        """
        self._running = True

        def daemon_loop():
            while self._running:
                try:
                    self.scan()
                    if self.push_queue.size() > 0:
                        self.push(target="github", dry_run=False, batch_size=50)
                    self.state.save()
                    self.conflict_resolver.save()
                except Exception as e:
                    print(f"[Daemon] Error: {e}")
                time.sleep(interval)

        self._thread = threading.Thread(target=daemon_loop, daemon=True)
        self._thread.start()
        print(f"[SyncEngine] Daemon started (interval={interval}s)")

    def stop_daemon(self) -> None:
        """停止守护线程"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[SyncEngine] Daemon stopped")

    # -------------------------------------------------------------------------
    # 清理
    # -------------------------------------------------------------------------

    def cleanup(self) -> Dict[str, Any]:
        """
        清理临时文件和过期快照
        """
        removed = []

        # 清理 dirty 标记
        dirty_dir = self.root_dir / DIRTY_DIR
        if dirty_dir.exists():
            for f in dirty_dir.iterdir():
                f.unlink()
                removed.append(str(f))

        # 清理冲突报告（已解决的）
        for path, rec in list(self.conflict_resolver.conflicts.items()):
            if rec.resolved_at is not None:
                del self.conflict_resolver.conflicts[path]

        self.conflict_resolver.save()

        return {
            "status": "cleaned",
            "removed_items": len(removed),
            "removed_paths": removed[:20],
        }


# =============================================================================
# CLI 接口
# =============================================================================

def run_cli():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="OMNI-HUB v11.1 Sync Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python v11_sync_engine.py init --root /mnt/agents/output/OMNI-HUB
  python v11_sync_engine.py scan --root /mnt/agents/output/OMNI-HUB
  python v11_sync_engine.py push --root /mnt/agents/output/OMNI-HUB --target github
  python v11_sync_engine.py status --root /mnt/agents/output/OMNI-HUB
  python v11_sync_engine.py snapshot --root /mnt/agents/output/OMNI-HUB --kind daily
  python v11_sync_engine.py rollback --root /mnt/agents/output/OMNI-HUB --kind pre-push --name <name>
        """
    )
    parser.add_argument("--root", default="/mnt/agents/output/OMNI-HUB",
                        help="项目根目录")
    parser.add_argument("--project", default="OMNI-HUB",
                        help="项目名称")
    parser.add_argument("--version", action="store_true",
                        help="显示版本")

    subparsers = parser.add_subparsers(dest="command")

    # init
    init_parser = subparsers.add_parser("init", help="初始化同步环境")

    # scan
    scan_parser = subparsers.add_parser("scan", help="扫描变更")

    # push
    push_parser = subparsers.add_parser("push", help="执行推送")
    push_parser.add_argument("--target", default="github", choices=["github", "os", "all"])
    push_parser.add_argument("--dry-run", action="store_true")
    push_parser.add_argument("--batch-size", type=int, default=100)

    # status
    status_parser = subparsers.add_parser("status", help="查看状态")

    # report
    report_parser = subparsers.add_parser("report", help="生成报告")

    # snapshot
    snap_parser = subparsers.add_parser("snapshot", help="创建快照")
    snap_parser.add_argument("--kind", default="session",
                             choices=["session", "pre-push", "daily", "weekly"])
    snap_parser.add_argument("--name", default=None)

    # rollback
    roll_parser = subparsers.add_parser("rollback", help="回滚")
    roll_parser.add_argument("--kind", required=True)
    roll_parser.add_argument("--name", required=True)

    # daemon
    daemon_parser = subparsers.add_parser("daemon", help="启动守护进程")
    daemon_parser.add_argument("--interval", type=int, default=300)
    daemon_parser.add_argument("--stop", action="store_true")

    # cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="清理临时文件")

    args = parser.parse_args()

    if args.version:
        print(f"OMNI-HUB Sync Engine v{VERSION}")
        return

    engine = SyncEngine(args.root, args.project)

    if args.command == "init":
        result = engine.init()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "scan":
        result = engine.scan()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "push":
        result = engine.push(args.target, args.dry_run, args.batch_size)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "status":
        result = engine.status()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "report":
        print(engine.report())

    elif args.command == "snapshot":
        snap = engine.snapshot_mgr.create(args.kind, args.name)
        print(json.dumps({"snapshot": snap}, indent=2))

    elif args.command == "rollback":
        result = engine.rollback(args.kind, args.name)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "daemon":
        if args.stop:
            engine.stop_daemon()
        else:
            engine.start_daemon(args.interval)
            print("按 Ctrl+C 停止...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                engine.stop_daemon()

    elif args.command == "cleanup":
        result = engine.cleanup()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


# =============================================================================
# 测试套件
# =============================================================================

def run_tests():
    """运行内置测试"""
    import tempfile
    import shutil

    print("=" * 60)
    print(f"OMNI-HUB Sync Engine Test Suite v{VERSION}")
    print("=" * 60)

    # 创建临时测试目录
    test_root = tempfile.mkdtemp(prefix="omni_sync_test_")
    print(f"\n[Test] 测试目录: {test_root}")

    try:
        # 创建测试项目结构
        test_project = Path(test_root) / "test_project"
        test_project.mkdir()
        (test_project / "README.md").write_text("# Test Project\n")
        (test_project / "main.py").write_text("print('hello')\n")
        with open(test_project / "config.json", "w") as f:
            json.dump({"key": "value"}, f)
        (test_project / "temp.tmp").write_text("temp data")

        sub = test_project / "src"
        sub.mkdir()
        (sub / "module.py").write_text("def foo(): pass\n")

        # 测试 1: 初始化
        print("\n[Test 1] 初始化同步环境...")
        engine = SyncEngine(str(test_project), "test_project")
        result = engine.init()
        assert result["status"] == "initialized"
        print(f"  PASS: 创建 {len(result['directories'])} 个目录")

        # 测试 2: 扫描
        print("\n[Test 2] 扫描变更...")
        result = engine.scan()  # 不传入 project_name，扫描整个 root_dir
        print(f"  扫描到 {result['scanned']} 个变更文件")
        print(f"  加入队列 {result['enqueued']} 个")
        print(f"  队列大小: {result['queue_size']}")
        assert result["queue_size"] > 0
        print("  PASS")

        # 测试 3: 状态检查
        print("\n[Test 3] 状态检查...")
        status = engine.status()
        print(f"  文件状态: {status['file_states']}")
        assert status["queue_size"] > 0
        print("  PASS")

        # 测试 4: 干运行推送
        print("\n[Test 4] 干运行推送 (github)...")
        result = engine.push(target="github", dry_run=True, batch_size=10)
        print(f"  成功: {result['success']}")
        print(f"  失败: {result['failed']}")
        print(f"  冲突: {result['conflicts']}")
        print(f"  耗时: {result['duration_ms']}ms")
        assert result["dry_run"] is True
        print("  PASS")

        # 测试 5: 实际推送 (需要先重新扫描，因为 dry_run 已清空队列)
        print("\n[Test 5] 实际推送 (github)...")
        engine.scan()  # 重新填充队列
        result = engine.push(target="github", dry_run=False, batch_size=10)
        print(f"  成功: {result['success']}")
        print(f"  预推送快照: {result['pre_push_snapshot']}")
        assert result["success"] > 0
        print("  PASS")

        # 测试 6: 快照
        print("\n[Test 6] 创建快照...")
        snap = engine.snapshot_mgr.create("session", "test-snapshot")
        print(f"  快照路径: {snap}")
        assert os.path.exists(snap)
        print("  PASS")

        # 测试 7: 文件修改后重新扫描
        print("\n[Test 7] 修改文件后扫描...")
        time.sleep(0.1)
        (test_project / "main.py").write_text("print('hello world')\n")
        result = engine.scan()
        print(f"  检测到 {result['scanned']} 个变更")
        assert result["scanned"] >= 1
        print("  PASS")

        # 测试 8: 冲突检测
        print("\n[Test 8] 冲突检测...")
        info1 = FileInfo(path="test.txt", mtime=time.time(), sha256="abc123")
        info2 = FileInfo(path="test.txt", mtime=time.time() - 10, sha256="def456")
        has_conflict = engine.conflict_resolver.detect_conflict("test.txt", info1, info2)
        print(f"  冲突检测: {has_conflict}")
        assert has_conflict is True  # 时间差小于 300s 且哈希不同
        print("  PASS")

        # 测试 9: 冲突解决
        print("\n[Test 9] 冲突解决...")
        should_push, detail = engine.conflict_resolver.resolve(
            "test.txt", info1, info2, ConflictResolution.TIMESTAMP_WINS
        )
        print(f"  解决策略: TIMESTAMP_WINS")
        print(f"  应推送: {should_push}")
        print(f"  详情: {detail}")
        assert should_push is True  # info1 时间戳更新
        print("  PASS")

        # 测试 10: 报告生成
        print("\n[Test 10] 生成报告...")
        report = engine.report()
        print(report)
        assert "OMNI-HUB Sync Report" in report
        print("  PASS")

        # 测试 11: 回滚
        print("\n[Test 11] 回滚...")
        result = engine.rollback("session", "test-snapshot")
        print(f"  恢复文件数: {result['restored_files']}")
        assert result["restored_files"] > 0
        print("  PASS")

        # 测试 12: 清理
        print("\n[Test 12] 清理...")
        result = engine.cleanup()
        print(f"  清理项: {result['removed_items']}")
        print("  PASS")

        # 测试 13: 状态统计
        print("\n[Test 13] 状态统计...")
        stats = engine.state.get_stats()
        print(f"  状态统计: {stats}")
        assert "CLEAN" in stats
        print("  PASS")

        # 测试 14: 队列操作
        print("\n[Test 14] 队列操作...")
        engine.push_queue.clear()
        assert engine.push_queue.is_empty()
        print("  PASS")

        print("\n" + "=" * 60)
        print("所有 14 项测试通过!")
        print("=" * 60)

    finally:
        # 清理测试目录
        shutil.rmtree(test_root, ignore_errors=True)
        print(f"\n[Test] 清理测试目录: {test_root}")


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
    else:
        run_cli()
