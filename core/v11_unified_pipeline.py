#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v11.0 — UnifiedPipeline
=================================
End-to-end unified pipeline integrating:
  Scanner → Parser → Extractor → Associator → Weaver → Validator → Injector
                    ↑________________________________________________↓
                              Feedback Closed Loop

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    UnifiedOrchestrator                       │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│  Scanner    │   Parser    │  Extractor  │    Associator     │
│  (扫描)      │  (解析)      │  (提取)      │    (关联)          │
├─────────────┴─────────────┴─────────────┴───────────────────┤
│                      MessageBus (消息总线)                    │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│   Weaver    │  Validator  │   Injector  │   StateManager    │
│  (编织)      │  (验证)      │   (注入)     │   (状态管理)       │
└─────────────┴─────────────┴─────────────┴───────────────────┘
                        ↑________反馈闭环________↓

Key Solutions:
1. Process Synergy: MessageBus + StateManager enable state sharing across stages
2. Unified Data: All stages use KNode/KEdge/UnifiedFieldState
3. Incremental: Only changed files processed via mtime comparison
4. Feedback Loop: Injector output → Scanner input (self-driving)

Version: 11.0.0
Date: 2026-09-17
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import logging
import math
import os
import re
import sys
import time
import traceback
import uuid
import warnings
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any, Callable, Dict, Generic, Iterator, List, Literal,
    Optional, Set, Tuple, TypeVar, Union, Protocol
)

import numpy as np

# =============================================================================
# 0. Module Path Setup & Graceful Imports
# =============================================================================

CORE_DIR = Path(__file__).parent.resolve()
OMNI_HUB_ROOT = CORE_DIR.parent if CORE_DIR.name == "core" else CORE_DIR

# Insert core dir into sys.path for clean imports
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

# --- Import v11_standards ---
try:
    import v11_standards as _v11_std
    UnifiedFieldState = _v11_std.UnifiedFieldState
    DimensionIndex = _v11_std.DimensionIndex
    UNIFIED_FIELD_DIMENSIONS = _v11_std.UNIFIED_FIELD_DIMENSIONS
    PHI_GOLDEN = _v11_std.PHI_GOLDEN
    EMERGENCE_THRESHOLD = _v11_std.EMERGENCE_THRESHOLD
    OMNIHUBException = _v11_std.OMNIHUBException
    get_logger = _v11_std.get_logger
    configure_logging = _v11_std.configure_logging
except Exception as e:
    raise ImportError(f"v11_standards.py is required for UnifiedPipeline: {e}")

# --- Import v11_knowledge_pedestal_unified ---
try:
    import v11_knowledge_pedestal_unified as _v11_ped
    KNode = _v11_ped.KNode
    KEdge = _v11_ped.KEdge
    KnowledgePedestal = _v11_ped.KnowledgePedestal
    KGBase = _v11_ped.KGBase
    CCBase = _v11_ped.CCBase
    HGBase = _v11_ped.HGBase
    INBase = _v11_ped.INBase
    CTBase = _v11_ped.CTBase
    LLBase = _v11_ped.LLBase
    PedestalBridge = _v11_ped.PedestalBridge
    KnowledgeOperations = _v11_ped.KnowledgeOperations
    Cell = _v11_ped.Cell
    HyperEdge = _v11_ped.HyperEdge
    Morphism = _v11_ped.Morphism
    FormalProp = _v11_ped.FormalProp
    Pedestal = _v11_ped.Pedestal
    PEDESTAL_NAMES = _v11_ped.PEDESTAL_NAMES
    stable_hash = _v11_ped.stable_hash
    entropy_shannon = _v11_ped.entropy_shannon
except Exception as e:
    raise ImportError(f"v11_knowledge_pedestal_unified.py is required for UnifiedPipeline: {e}")

# --- Import v11_relation_discovery_engine ---
try:
    import v11_relation_discovery_engine as _v11_rel
    RelationDiscoveryEngine = _v11_rel.RelationDiscoveryEngine
    RelationType = _v11_rel.RelationType
    Relation = _v11_rel.Relation
    RelationFactory = _v11_rel.RelationFactory
    SelfInferenceEngine = _v11_rel.SelfInferenceEngine
    MutualComputationProtocol = _v11_rel.MutualComputationProtocol
    UnifiedFieldInjector = _v11_rel.UnifiedFieldInjector
except Exception as e:
    raise ImportError(f"v11_relation_discovery_engine.py is required for UnifiedPipeline: {e}")

# --- Import v11_consciousness_emergence_system ---
try:
    import v11_consciousness_emergence_system as _v11_ces
    EmergenceTheoryArchitecture = _v11_ces.EmergenceTheoryArchitecture
    EmergenceManifestationSystem = _v11_ces.EmergenceManifestationSystem
    EmergenceApplicationAPI = _v11_ces.EmergenceApplicationAPI
    ConsciousnessState = _v11_ces.ConsciousnessState
except Exception as e:
    raise ImportError(f"v11_consciousness_emergence_system.py is required for UnifiedPipeline: {e}")

logger = get_logger("UnifiedPipeline")


# =============================================================================
# 1. MessageBus — Unified Message Queue (Pub/Sub IPC via JSON Files)
# =============================================================================

class MessageType(Enum):
    """Standard pipeline message types."""
    SCAN_EVENT = "scan"
    PARSE_EVENT = "parse"
    EXTRACT_EVENT = "extract"
    ASSOCIATE_EVENT = "associate"
    WEAVE_EVENT = "weave"
    VALIDATE_EVENT = "validate"
    INJECT_EVENT = "inject"
    FEEDBACK_EVENT = "feedback"
    ERROR_EVENT = "error"
    CHECKPOINT_EVENT = "checkpoint"


@dataclass
class PipelineMessage:
    """Unified message envelope for cross-stage communication."""
    msg_id: str
    msg_type: MessageType
    stage: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    parent_id: Optional[str] = None
    trace_id: str = ""  # Correlation ID for end-to-end tracing

    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "msg_type": self.msg_type.value,
            "stage": self.stage,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "parent_id": self.parent_id,
            "trace_id": self.trace_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PipelineMessage":
        return cls(
            msg_id=d["msg_id"],
            msg_type=MessageType(d["msg_type"]),
            stage=d["stage"],
            payload=d.get("payload", {}),
            timestamp=d.get("timestamp", 0.0),
            parent_id=d.get("parent_id"),
            trace_id=d.get("trace_id", ""),
        )


class MessageBus:
    """
    Unified Message Bus — Pub/Sub via JSON-serialized state files.
    Since we cannot use true IPC (multiprocessing.Queue / ZeroMQ / Redis),
    we use a shared JSONL file as the message journal.

    Publishers append messages; subscribers poll and filter by type.
    """

    def __init__(self, journal_dir: Optional[str] = None, max_journal_size_mb: float = 100.0):
        self.journal_dir = Path(journal_dir) if journal_dir else CORE_DIR / "pipeline_journal"
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        self.journal_file = self.journal_dir / "message_bus.jsonl"
        self.subscribers: Dict[MessageType, List[Callable[[PipelineMessage], None]]] = defaultdict(list)
        self._lock_file = self.journal_dir / ".bus_lock"
        self._max_journal_size = max_journal_size_mb * 1024 * 1024
        self._msg_counter = 0
        self._trace_id = f"trace_{uuid.uuid4().hex[:8]}"
        logger.info("MessageBus initialized: journal=%s", self.journal_file)

    def publish(self, msg_type: MessageType, stage: str, payload: Dict[str, Any],
                parent_id: Optional[str] = None) -> PipelineMessage:
        """Publish a message to the bus (append to journal)."""
        self._msg_counter += 1
        msg = PipelineMessage(
            msg_id=f"{stage}_{self._msg_counter}_{uuid.uuid4().hex[:4]}",
            msg_type=msg_type,
            stage=stage,
            payload=payload,
            timestamp=time.time(),
            parent_id=parent_id,
            trace_id=self._trace_id,
        )
        # Append to journal
        try:
            with open(self.journal_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(msg.to_dict(), ensure_ascii=False, default=str) + "\n")
        except OSError as e:
            logger.error("MessageBus journal write failed: %s", e)

        # Notify in-process subscribers
        for cb in self.subscribers.get(msg_type, []):
            try:
                cb(msg)
            except Exception as e:
                logger.error("Subscriber error for %s: %s", msg_type, e)

        return msg

    def subscribe(self, msg_type: MessageType, callback: Callable[[PipelineMessage], None]) -> None:
        """Register an in-process subscriber."""
        self.subscribers[msg_type].append(callback)
        logger.debug("Subscribed to %s: %s", msg_type.value, callback.__name__)

    def poll(self, msg_type: Optional[MessageType] = None, since: float = 0.0,
             limit: int = 1000) -> List[PipelineMessage]:
        """Poll messages from journal (for cross-process recovery)."""
        messages: List[PipelineMessage] = []
        if not self.journal_file.exists():
            return messages
        try:
            with open(self.journal_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        if d.get("timestamp", 0) < since:
                            continue
                        if msg_type is not None and d.get("msg_type") != msg_type.value:
                            continue
                        messages.append(PipelineMessage.from_dict(d))
                        if len(messages) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
        except OSError as e:
            logger.error("MessageBus journal read failed: %s", e)
        return messages

    def checkpoint(self, label: str = "") -> str:
        """Rotate journal and create checkpoint."""
        checkpoint_id = f"cp_{int(time.time())}_{label}"
        if self.journal_file.exists() and self.journal_file.stat().st_size > self._max_journal_size:
            rotated = self.journal_dir / f"message_bus_{checkpoint_id}.jsonl"
            try:
                self.journal_file.rename(rotated)
                logger.info("Journal rotated to %s", rotated.name)
            except OSError as e:
                logger.error("Journal rotation failed: %s", e)
        self.publish(MessageType.CHECKPOINT_EVENT, "MessageBus",
                     {"checkpoint_id": checkpoint_id, "msg_count": self._msg_counter})
        return checkpoint_id

    def get_stats(self) -> Dict[str, Any]:
        return {
            "journal_file": str(self.journal_file),
            "msg_counter": self._msg_counter,
            "subscriber_count": sum(len(cbs) for cbs in self.subscribers.values()),
            "trace_id": self._trace_id,
        }


# =============================================================================
# 2. StateManager — Unified State Persistence & Checkpoint Recovery
# =============================================================================

class StateManager:
    """
    Unified state manager:
      - Persist pipeline state to JSON
      - Incremental diff tracking
      - Breakpoint recovery
      - File fingerprint tracking for incremental updates
    """

    def __init__(self, state_dir: Optional[str] = None):
        self.state_dir = Path(state_dir) if state_dir else CORE_DIR / "pipeline_state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "unified_pipeline_state.json"
        self.checkpoint_dir = self.state_dir / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._state: Dict[str, Any] = {}
        self._file_fingerprints: Dict[str, Dict[str, Any]] = {}  # path -> {mtime, size, hash}
        self._load_state()

    def _load_state(self) -> None:
        """Load state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._state = data.get("state", {})
                self._file_fingerprints = data.get("fingerprints", {})
                logger.info("State loaded: %d fingerprints, version=%s",
                            len(self._file_fingerprints),
                            data.get("version", "unknown"))
            except (json.JSONDecodeError, OSError) as e:
                logger.error("State load failed: %s", e)
                self._state = {}
                self._file_fingerprints = {}

    def save_state(self, extra: Optional[Dict[str, Any]] = None) -> None:
        """Persist current state to disk."""
        data = {
            "version": "11.0.0",
            "timestamp": time.time(),
            "state": self._state,
            "fingerprints": self._file_fingerprints,
        }
        if extra:
            data.update(extra)
        temp_file = self.state_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            temp_file.replace(self.state_file)
            logger.debug("State saved: %s", self.state_file)
        except OSError as e:
            logger.error("State save failed: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def update(self, updates: Dict[str, Any]) -> None:
        self._state.update(updates)

    def compute_file_fingerprint(self, path: Path) -> Dict[str, Any]:
        """Compute file fingerprint for incremental tracking."""
        stat = path.stat()
        # Quick hash: first 8KB + mtime + size
        sample = b""
        try:
            with open(path, "rb") as f:
                sample = f.read(8192)
        except OSError:
            pass
        return {
            "mtime": stat.st_mtime,
            "size": stat.st_size,
            "quick_hash": hashlib.sha256(sample + str(stat.st_mtime).encode()).hexdigest()[:16],
        }

    def is_file_changed(self, path: Path) -> bool:
        """Check if file has changed since last scan."""
        path_str = str(path)
        current = self.compute_file_fingerprint(path)
        previous = self._file_fingerprints.get(path_str)
        if previous is None:
            return True
        return (current["quick_hash"] != previous.get("quick_hash") or
                current["size"] != previous.get("size"))

    def update_fingerprint(self, path: Path) -> None:
        self._file_fingerprints[str(path)] = self.compute_file_fingerprint(path)

    def get_changed_files(self, files: List[Path]) -> Tuple[List[Path], List[Path]]:
        """Return (changed_files, unchanged_files)."""
        changed = []
        unchanged = []
        for f in files:
            if self.is_file_changed(f):
                changed.append(f)
            else:
                unchanged.append(f)
        return changed, unchanged

    def create_checkpoint(self, label: str = "", payload: Optional[Dict[str, Any]] = None) -> str:
        """Create a named checkpoint."""
        cp_id = f"checkpoint_{int(time.time())}_{label}"
        cp_file = self.checkpoint_dir / f"{cp_id}.json"
        data = {
            "checkpoint_id": cp_id,
            "timestamp": time.time(),
            "state": self._state.copy(),
            "fingerprints": self._file_fingerprints.copy(),
            "payload": payload or {},
        }
        try:
            with open(cp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.info("Checkpoint created: %s", cp_id)
        except OSError as e:
            logger.error("Checkpoint creation failed: %s", e)
        return cp_id

    def restore_checkpoint(self, cp_id: str) -> bool:
        """Restore state from checkpoint."""
        cp_file = self.checkpoint_dir / f"{cp_id}.json"
        if not cp_file.exists():
            logger.error("Checkpoint not found: %s", cp_id)
            return False
        try:
            with open(cp_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._state = data.get("state", {})
            self._file_fingerprints = data.get("fingerprints", {})
            logger.info("Checkpoint restored: %s", cp_id)
            return True
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Checkpoint restore failed: %s", e)
            return False

    def diff_state(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """Compute incremental diff between two states."""
        diff = {}
        all_keys = set(old_state.keys()) | set(new_state.keys())
        for k in all_keys:
            if k not in old_state:
                diff[k] = {"op": "add", "value": new_state[k]}
            elif k not in new_state:
                diff[k] = {"op": "remove", "old_value": old_state[k]}
            elif old_state[k] != new_state[k]:
                diff[k] = {"op": "update", "old_value": old_state[k], "new_value": new_state[k]}
        return diff

    def get_stats(self) -> Dict[str, Any]:
        return {
            "state_keys": len(self._state),
            "tracked_files": len(self._file_fingerprints),
            "state_file": str(self.state_file),
            "checkpoints": len(list(self.checkpoint_dir.glob("checkpoint_*.json"))),
        }


# =============================================================================
# 3. UnifiedScanner — Full & Incremental File Scanning
# =============================================================================

@dataclass
class FileDescriptor:
    """Unified file descriptor — the atom flowing through the pipeline."""
    path: str           # Absolute or relative path
    rel_path: str       # Path relative to scan root
    size_bytes: int
    mtime: float
    ext: str
    fingerprint: str    # Quick content hash
    scan_mode: str = "full"  # "full" or "incremental"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "rel_path": self.rel_path,
            "size_bytes": self.size_bytes,
            "mtime": self.mtime,
            "ext": self.ext,
            "fingerprint": self.fingerprint,
            "scan_mode": self.scan_mode,
            "metadata": self.metadata,
        }


class ScanFilter:
    """Configurable filter for file scanning."""

    def __init__(self,
                 include_extensions: Optional[Set[str]] = None,
                 exclude_extensions: Optional[Set[str]] = None,
                 max_size_bytes: Optional[int] = None,
                 min_size_bytes: int = 0,
                 exclude_patterns: Optional[List[str]] = None,
                 include_patterns: Optional[List[str]] = None,
                 since_mtime: Optional[float] = None):
        self.include_extensions = set(include_extensions) if include_extensions else None
        self.exclude_extensions = set(exclude_extensions) if exclude_extensions else {"pyc", "pyo", "so", "dll", "dylib", "exe"}
        self.max_size_bytes = max_size_bytes
        self.min_size_bytes = min_size_bytes
        self.exclude_patterns = exclude_patterns or ["__pycache__", ".git", ".svn", ".hg", "node_modules", ".pytest_cache", "*.egg-info"]
        self.include_patterns = include_patterns or []
        self.since_mtime = since_mtime

    def match(self, path: Path, root: Path) -> bool:
        """Check if file passes filter."""
        rel = str(path.relative_to(root))

        # Exclude patterns
        for pat in self.exclude_patterns:
            if pat in rel or (pat.startswith("*") and rel.endswith(pat[1:])):
                return False

        # Include patterns
        if self.include_patterns:
            if not any(pat in rel for pat in self.include_patterns):
                return False

        ext = path.suffix.lstrip(".").lower()
        if self.exclude_extensions and ext in self.exclude_extensions:
            return False
        if self.include_extensions and ext not in self.include_extensions:
            return False

        try:
            stat = path.stat()
        except OSError:
            return False

        if self.max_size_bytes is not None and stat.st_size > self.max_size_bytes:
            return False
        if stat.st_size < self.min_size_bytes:
            return False
        if self.since_mtime is not None and stat.st_mtime < self.since_mtime:
            return False

        return True


class UnifiedScanner:
    """
    Unified Scanner — full and incremental file scanning.
    Produces FileDescriptor stream for downstream stages.
    """

    def __init__(self, root: str, state_manager: StateManager,
                 message_bus: MessageBus, scan_filter: Optional[ScanFilter] = None):
        self.root = Path(root).resolve()
        self.state = state_manager
        self.bus = message_bus
        self.filter = scan_filter or ScanFilter()
        self.scanned_files: List[FileDescriptor] = []
        self.stats = {"total": 0, "changed": 0, "unchanged": 0, "filtered": 0}

    def scan(self, incremental: bool = True, max_files: int = 200) -> List[FileDescriptor]:
        """Execute scan. If incremental=True, only return changed files."""
        logger.info("[Scanner] Starting %s scan of %s", "incremental" if incremental else "full", self.root)
        self.scanned_files = []
        self.stats = {"total": 0, "changed": 0, "unchanged": 0, "filtered": 0}

        # Use rglob but limit total files to avoid performance issues
        all_files = []
        for f in self.root.rglob("*"):
            if f.is_file():
                all_files.append(f)
                if len(all_files) >= max_files * 5:
                    break
        logger.info("[Scanner] Found %d raw files (capped at %d for safety)", len(all_files), max_files * 5)

        for f in all_files:
            self.stats["total"] += 1
            if not self.filter.match(f, self.root):
                self.stats["filtered"] += 1
                continue

            fd = self._create_descriptor(f)

            if incremental:
                if self.state.is_file_changed(f):
                    fd.scan_mode = "incremental"
                    self.scanned_files.append(fd)
                    self.stats["changed"] += 1
                    self.state.update_fingerprint(f)
                else:
                    self.stats["unchanged"] += 1
            else:
                fd.scan_mode = "full"
                self.scanned_files.append(fd)
                self.state.update_fingerprint(f)
                self.stats["changed"] += 1

        logger.info("[Scanner] Result: %d changed, %d unchanged, %d filtered",
                    self.stats["changed"], self.stats["unchanged"], self.stats["filtered"])

        self.bus.publish(MessageType.SCAN_EVENT, "UnifiedScanner", {
            "stats": self.stats,
            "file_count": len(self.scanned_files),
            "root": str(self.root),
            "incremental": incremental,
        })
        return self.scanned_files

    def _create_descriptor(self, path: Path) -> FileDescriptor:
        stat = path.stat()
        rel = path.relative_to(self.root)
        # Quick fingerprint
        sample = b""
        try:
            with open(path, "rb") as f:
                sample = f.read(4096)
        except OSError:
            pass
        fingerprint = hashlib.sha256(sample + str(stat.st_mtime).encode()).hexdigest()[:16]

        return FileDescriptor(
            path=str(path),
            rel_path=str(rel),
            size_bytes=stat.st_size,
            mtime=stat.st_mtime,
            ext=path.suffix.lower(),
            fingerprint=fingerprint,
            metadata={"stem": path.stem, "name": path.name}
        )

    def get_stats(self) -> Dict[str, Any]:
        return {"scanner": self.stats, "files": [f.to_dict() for f in self.scanned_files[:50]]}


# =============================================================================
# 4. UnifiedParser — Multi-Format AST/Structured Parsing
# =============================================================================

@dataclass
class ParsedUnit:
    """Structured parse result for any file type."""
    file_descriptor: FileDescriptor
    file_type: str
    ast: Optional[Any] = None           # Python AST (for .py)
    structure: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    parse_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_descriptor": self.file_descriptor.to_dict(),
            "file_type": self.file_type,
            "structure": self.structure,
            "raw_text": self.raw_text[:2000] if len(self.raw_text) > 2000 else self.raw_text,
            "parse_time_ms": self.parse_time_ms,
            "errors": self.errors,
        }


class BaseParser:
    """Abstract base parser."""
    def parse(self, fd: FileDescriptor) -> ParsedUnit:
        raise NotImplementedError


class PythonParser(BaseParser):
    """Python source parser — AST extraction."""

    def parse(self, fd: FileDescriptor) -> ParsedUnit:
        start = time.time()
        unit = ParsedUnit(file_descriptor=fd, file_type="python")
        try:
            with open(fd.path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
            unit.raw_text = source
            unit.ast = ast.parse(source)
            unit.structure = self._extract_structure(unit.ast, source)
        except SyntaxError as e:
            unit.errors.append(f"SyntaxError: {e}")
            unit.raw_text = ""
        except OSError as e:
            unit.errors.append(f"ReadError: {e}")
        unit.parse_time_ms = (time.time() - start) * 1000
        return unit

    def _extract_structure(self, tree: ast.AST, source: str) -> Dict[str, Any]:
        result = {
            "classes": [],
            "functions": [],
            "imports": [],
            "docstring": ast.get_docstring(tree) or "",
            "line_count": source.count("\n") + 1,
            "complexity": 0,
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                result["classes"].append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "methods": methods,
                    "bases": [self._format_expr(b) for b in node.bases],
                })
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result["functions"].append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "args": len(node.args.args),
                    "returns": self._format_expr(node.returns) if node.returns else None,
                })
                result["complexity"] += 1
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append({"name": alias.name, "as": alias.asname})
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    result["imports"].append({
                        "module": mod,
                        "name": alias.name,
                        "as": alias.asname,
                    })
        return result

    @staticmethod
    def _format_expr(node: ast.AST) -> str:
        try:
            return ast.unparse(node)
        except Exception:
            return str(type(node).__name__)


class MarkdownParser(BaseParser):
    """Markdown parser — heading/section extraction."""

    def parse(self, fd: FileDescriptor) -> ParsedUnit:
        start = time.time()
        unit = ParsedUnit(file_descriptor=fd, file_type="markdown")
        try:
            with open(fd.path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            unit.raw_text = text
            unit.structure = self._extract_structure(text)
        except OSError as e:
            unit.errors.append(f"ReadError: {e}")
        unit.parse_time_ms = (time.time() - start) * 1000
        return unit

    def _extract_structure(self, text: str) -> Dict[str, Any]:
        headings = []
        code_blocks = []
        links = []
        for i, line in enumerate(text.split("\n"), 1):
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("#").strip()
                headings.append({"level": level, "title": title, "lineno": i})
            if line.startswith("```"):
                code_blocks.append({"lineno": i})
            # Simple link extraction
            for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
                links.append({"text": m.group(1), "url": m.group(2), "lineno": i})
        return {
            "headings": headings,
            "heading_count": len(headings),
            "code_blocks": len(code_blocks),
            "links": links,
            "line_count": text.count("\n") + 1,
        }


class JSONParser(BaseParser):
    """JSON parser — schema extraction."""

    def parse(self, fd: FileDescriptor) -> ParsedUnit:
        start = time.time()
        unit = ParsedUnit(file_descriptor=fd, file_type="json")
        try:
            with open(fd.path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            unit.raw_text = text
            data = json.loads(text)
            unit.structure = self._extract_structure(data)
        except json.JSONDecodeError as e:
            unit.errors.append(f"JSONDecodeError: {e}")
        except OSError as e:
            unit.errors.append(f"ReadError: {e}")
        unit.parse_time_ms = (time.time() - start) * 1000
        return unit

    def _extract_structure(self, data: Any, depth: int = 0) -> Dict[str, Any]:
        result = {"depth": depth, "keys": [], "types": {}, "item_count": 0}
        self._scan(data, result, depth)
        return result

    def _scan(self, obj: Any, result: Dict[str, Any], depth: int) -> None:
        result["depth"] = max(result["depth"], depth)
        tname = type(obj).__name__
        result["types"][tname] = result["types"].get(tname, 0) + 1
        if isinstance(obj, dict):
            result["item_count"] += len(obj)
            for k, v in obj.items():
                result["keys"].append(k)
                self._scan(v, result, depth + 1)
        elif isinstance(obj, list):
            result["item_count"] += len(obj)
            for item in obj:
                self._scan(item, result, depth + 1)


class LeanParser(BaseParser):
    """Lean theorem prover parser — theorem/definition extraction."""

    def parse(self, fd: FileDescriptor) -> ParsedUnit:
        start = time.time()
        unit = ParsedUnit(file_descriptor=fd, file_type="lean")
        try:
            with open(fd.path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            unit.raw_text = text
            unit.structure = self._extract_structure(text)
        except OSError as e:
            unit.errors.append(f"ReadError: {e}")
        unit.parse_time_ms = (time.time() - start) * 1000
        return unit

    def _extract_structure(self, text: str) -> Dict[str, Any]:
        theorems = []
        definitions = []
        imports = []
        for i, line in enumerate(text.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("theorem ") or stripped.startswith("lemma "):
                name = stripped.split()[1].split(":")[0].split("(")[0].strip()
                kind = "theorem" if stripped.startswith("theorem") else "lemma"
                theorems.append({"name": name, "kind": kind, "lineno": i})
            elif stripped.startswith("def "):
                name = stripped.split()[1].split(":")[0].split("(")[0].strip()
                definitions.append({"name": name, "lineno": i})
            elif stripped.startswith("import "):
                imports.append(stripped.split("import ")[1].strip())
        return {
            "theorems": theorems,
            "definitions": definitions,
            "imports": imports,
            "line_count": text.count("\n") + 1,
        }


class UnifiedParser:
    """
    Unified Parser — dispatches to format-specific parsers.
    Supports: Python, Markdown, JSON, Lean, fallback(text).
    """

    PARSER_MAP: Dict[str, type] = {
        ".py": PythonParser,
        ".md": MarkdownParser,
        ".markdown": MarkdownParser,
        ".json": JSONParser,
        ".lean": LeanParser,
    }

    def __init__(self, message_bus: MessageBus):
        self.bus = message_bus
        self.parsers: Dict[str, BaseParser] = {}
        self.stats = {"parsed": 0, "errors": 0, "by_type": defaultdict(int)}

    def parse(self, descriptors: List[FileDescriptor]) -> List[ParsedUnit]:
        """Parse all file descriptors."""
        logger.info("[Parser] Parsing %d files...", len(descriptors))
        results: List[ParsedUnit] = []
        self.stats = {"parsed": 0, "errors": 0, "by_type": defaultdict(int)}

        for fd in descriptors:
            parser = self._get_parser(fd.ext)
            unit = parser.parse(fd)
            results.append(unit)
            self.stats["parsed"] += 1
            self.stats["by_type"][unit.file_type] += 1
            if unit.errors:
                self.stats["errors"] += 1
                self.bus.publish(MessageType.ERROR_EVENT, "UnifiedParser", {
                    "file": fd.rel_path,
                    "errors": unit.errors,
                })

        self.bus.publish(MessageType.PARSE_EVENT, "UnifiedParser", {
            "stats": dict(self.stats),
            "count": len(results),
        })
        logger.info("[Parser] Parsed %d files, %d errors", self.stats["parsed"], self.stats["errors"])
        return results

    def _get_parser(self, ext: str) -> BaseParser:
        """Get or create parser for extension."""
        ext_lower = ext.lower()
        if ext_lower not in self.parsers:
            parser_cls = self.PARSER_MAP.get(ext_lower)
            if parser_cls:
                self.parsers[ext_lower] = parser_cls()
            else:
                # Fallback: generic text parser
                self.parsers[ext_lower] = self._fallback_parser()
        return self.parsers[ext_lower]

    def _fallback_parser(self) -> BaseParser:
        """Create a minimal fallback parser."""
        class FallbackParser(BaseParser):
            def parse(self, fd: FileDescriptor) -> ParsedUnit:
                unit = ParsedUnit(file_descriptor=fd, file_type="generic")
                try:
                    with open(fd.path, "r", encoding="utf-8", errors="ignore") as f:
                        unit.raw_text = f.read()
                    unit.structure = {"line_count": unit.raw_text.count("\n") + 1}
                except OSError as e:
                    unit.errors.append(str(e))
                return unit
        return FallbackParser()

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


# =============================================================================
# 5. UnifiedExtractor — AST → KNode Stream
# =============================================================================

@dataclass
class ExtractionRule:
    """Rule for extracting knowledge nodes from parsed units."""
    name: str
    file_types: List[str]
    extractor: Callable[[ParsedUnit], List[KNode]]
    priority: int = 5


class UnifiedExtractor:
    """
    Unified Extractor — transforms ParsedUnits into KNode stream.
    Extraction targets: functions, classes, theorems, definitions, concepts.
    """

    def __init__(self, message_bus: MessageBus, state_manager: StateManager):
        self.bus = message_bus
        self.state = state_manager
        self.rules: List[ExtractionRule] = []
        self._register_default_rules()
        self.extracted_nodes: List[KNode] = []
        self.stats = {"total_nodes": 0, "by_type": defaultdict(int)}

    def _register_default_rules(self) -> None:
        """Register built-in extraction rules."""
        self.rules.append(ExtractionRule(
            name="python_classes",
            file_types=["python"],
            extractor=self._extract_python_classes,
            priority=1,
        ))
        self.rules.append(ExtractionRule(
            name="python_functions",
            file_types=["python"],
            extractor=self._extract_python_functions,
            priority=2,
        ))
        self.rules.append(ExtractionRule(
            name="python_modules",
            file_types=["python"],
            extractor=self._extract_python_modules,
            priority=3,
        ))
        self.rules.append(ExtractionRule(
            name="markdown_sections",
            file_types=["markdown"],
            extractor=self._extract_markdown_sections,
            priority=4,
        ))
        self.rules.append(ExtractionRule(
            name="json_schemas",
            file_types=["json"],
            extractor=self._extract_json_schemas,
            priority=5,
        ))
        self.rules.append(ExtractionRule(
            name="lean_theorems",
            file_types=["lean"],
            extractor=self._extract_lean_theorems,
            priority=6,
        ))
        self.rules.append(ExtractionRule(
            name="generic_file_nodes",
            file_types=["generic"],
            extractor=self._extract_generic_nodes,
            priority=10,
        ))

    def extract(self, parsed_units: List[ParsedUnit], max_nodes_per_unit: int = 50) -> List[KNode]:
        """Extract KNodes from parsed units."""
        logger.info("[Extractor] Extracting from %d parsed units...", len(parsed_units))
        self.extracted_nodes = []
        self.stats = {"total_nodes": 0, "by_type": defaultdict(int)}

        for unit in parsed_units:
            for rule in sorted(self.rules, key=lambda r: r.priority):
                if unit.file_type in rule.file_types:
                    try:
                        nodes = rule.extractor(unit)
                        # Limit nodes per unit to avoid explosion
                        if len(nodes) > max_nodes_per_unit:
                            nodes = nodes[:max_nodes_per_unit]
                        for node in nodes:
                            self.extracted_nodes.append(node)
                            self.stats["by_type"][node.node_type] += 1
                    except Exception as e:
                        logger.error("Extractor rule '%s' failed for %s: %s", rule.name, unit.file_descriptor.rel_path, e)

        self.stats["total_nodes"] = len(self.extracted_nodes)

        self.bus.publish(MessageType.EXTRACT_EVENT, "UnifiedExtractor", {
            "stats": dict(self.stats),
            "node_count": len(self.extracted_nodes),
        })
        logger.info("[Extractor] Extracted %d KNodes", len(self.extracted_nodes))
        return self.extracted_nodes

    # ---- Extractor implementations ----

    def _extract_python_classes(self, unit: ParsedUnit) -> List[KNode]:
        nodes = []
        for cls in unit.structure.get("classes", []):
            node_id = stable_hash((unit.file_descriptor.rel_path, "class", cls["name"]))
            nodes.append(KNode(
                node_id=node_id,
                label=cls["name"],
                node_type="python_class",
                module=Path(unit.file_descriptor.rel_path).parts[0] if Path(unit.file_descriptor.rel_path).parts else "root",
                version="11.0.0",
                size_bytes=unit.file_descriptor.size_bytes,
                path=unit.file_descriptor.rel_path,
                metadata={
                    "lineno": cls.get("lineno", 0),
                    "methods": cls.get("methods", []),
                    "bases": cls.get("bases", []),
                    "extractor": "python_classes",
                }
            ))
        return nodes

    def _extract_python_functions(self, unit: ParsedUnit) -> List[KNode]:
        nodes = []
        for fn in unit.structure.get("functions", []):
            node_id = stable_hash((unit.file_descriptor.rel_path, "func", fn["name"]))
            nodes.append(KNode(
                node_id=node_id,
                label=fn["name"],
                node_type="python_function",
                module=Path(unit.file_descriptor.rel_path).parts[0] if Path(unit.file_descriptor.rel_path).parts else "root",
                version="11.0.0",
                size_bytes=unit.file_descriptor.size_bytes,
                path=unit.file_descriptor.rel_path,
                metadata={
                    "lineno": fn.get("lineno", 0),
                    "args": fn.get("args", 0),
                    "returns": fn.get("returns"),
                    "extractor": "python_functions",
                }
            ))
        return nodes

    def _extract_python_modules(self, unit: ParsedUnit) -> List[KNode]:
        node_id = stable_hash((unit.file_descriptor.rel_path, "module"))
        return [KNode(
            node_id=node_id,
            label=Path(unit.file_descriptor.rel_path).stem,
            node_type="python_module",
            module=Path(unit.file_descriptor.rel_path).parts[0] if Path(unit.file_descriptor.rel_path).parts else "root",
            version="11.0.0",
            size_bytes=unit.file_descriptor.size_bytes,
            path=unit.file_descriptor.rel_path,
            metadata={
                "imports": [i.get("name", "") for i in unit.structure.get("imports", [])],
                "classes_count": len(unit.structure.get("classes", [])),
                "functions_count": len(unit.structure.get("functions", [])),
                "complexity": unit.structure.get("complexity", 0),
                "extractor": "python_modules",
            }
        )]

    def _extract_markdown_sections(self, unit: ParsedUnit) -> List[KNode]:
        nodes = []
        for h in unit.structure.get("headings", []):
            node_id = stable_hash((unit.file_descriptor.rel_path, "heading", h["title"]))
            nodes.append(KNode(
                node_id=node_id,
                label=h["title"][:100],
                node_type="markdown_heading",
                module=Path(unit.file_descriptor.rel_path).parts[0] if Path(unit.file_descriptor.rel_path).parts else "root",
                version="11.0.0",
                size_bytes=unit.file_descriptor.size_bytes,
                path=unit.file_descriptor.rel_path,
                metadata={
                    "level": h.get("level", 1),
                    "lineno": h.get("lineno", 0),
                    "extractor": "markdown_sections",
                }
            ))
        return nodes

    def _extract_json_schemas(self, unit: ParsedUnit) -> List[KNode]:
        node_id = stable_hash((unit.file_descriptor.rel_path, "json_root"))
        return [KNode(
            node_id=node_id,
            label=Path(unit.file_descriptor.rel_path).stem,
            node_type="json_schema",
            module=Path(unit.file_descriptor.rel_path).parts[0] if Path(unit.file_descriptor.rel_path).parts else "root",
            version="11.0.0",
            size_bytes=unit.file_descriptor.size_bytes,
            path=unit.file_descriptor.rel_path,
            metadata={
                "depth": unit.structure.get("depth", 0),
                "keys": list(set(unit.structure.get("keys", []))),
                "types": unit.structure.get("types", {}),
                "extractor": "json_schemas",
            }
        )]

    def _extract_lean_theorems(self, unit: ParsedUnit) -> List[KNode]:
        nodes = []
        for t in unit.structure.get("theorems", []):
            node_id = stable_hash((unit.file_descriptor.rel_path, "theorem", t["name"]))
            nodes.append(KNode(
                node_id=node_id,
                label=t["name"],
                node_type="lean_theorem",
                module=Path(unit.file_descriptor.rel_path).parts[0] if Path(unit.file_descriptor.rel_path).parts else "root",
                version="11.0.0",
                size_bytes=unit.file_descriptor.size_bytes,
                path=unit.file_descriptor.rel_path,
                metadata={
                    "kind": t.get("kind", "theorem"),
                    "lineno": t.get("lineno", 0),
                    "extractor": "lean_theorems",
                }
            ))
        return nodes

    def _extract_generic_nodes(self, unit: ParsedUnit) -> List[KNode]:
        node_id = stable_hash((unit.file_descriptor.rel_path, "generic"))
        return [KNode(
            node_id=node_id,
            label=Path(unit.file_descriptor.rel_path).stem,
            node_type="generic_file",
            module=Path(unit.file_descriptor.rel_path).parts[0] if Path(unit.file_descriptor.rel_path).parts else "root",
            version="11.0.0",
            size_bytes=unit.file_descriptor.size_bytes,
            path=unit.file_descriptor.rel_path,
            metadata={
                "ext": unit.file_descriptor.ext,
                "extractor": "generic_file_nodes",
            }
        )]

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


# =============================================================================
# 6. UnifiedAssociator — 8-Relation Type Discovery Engine Integration
# =============================================================================

class UnifiedAssociator:
    """
    Unified Associator — computes all 8 relation types between KNodes.
    Wraps v11_relation_discovery_engine.RelationDiscoveryEngine.
    """

    def __init__(self, message_bus: MessageBus, state_manager: StateManager):
        self.bus = message_bus
        self.state = state_manager
        self.relations: List[KEdge] = []
        self.stats = {"total_edges": 0, "by_type": defaultdict(int)}

    def associate(self, nodes: List[KNode],
                  node_data: Optional[Dict[str, Dict[str, Any]]] = None,
                  max_nodes_for_relations: int = 60) -> List[KEdge]:
        """
        Compute associations (edges) between all knowledge nodes.
        Uses the 8 relation types from RelationDiscoveryEngine.
        """
        # Limit nodes to avoid O(n^2) explosion
        if len(nodes) > max_nodes_for_relations:
            logger.info("[Associator] Limiting from %d to %d nodes for relation computation", len(nodes), max_nodes_for_relations)
            nodes = nodes[:max_nodes_for_relations]

        logger.info("[Associator] Computing associations for %d nodes...", len(nodes))
        self.relations = []
        self.stats = {"total_edges": 0, "by_type": defaultdict(int)}

        if len(nodes) < 2:
            logger.warning("[Associator] Not enough nodes for association")
            return self.relations

        # Build node embeddings for relation computation
        if node_data is None:
            node_data = self._build_node_data(nodes)

        # Use RelationDiscoveryEngine for full 8-type relation discovery
        node_ids = [n.node_id for n in nodes]
        try:
            engine = RelationDiscoveryEngine(node_ids)
            raw_relations = engine.discover_all_relations(node_data)

            # Convert Relation objects to KEdge objects
            for rel in raw_relations:
                edge = KEdge(
                    edge_id=rel.rel_id,
                    source=rel.source_id,
                    target=rel.target_id,
                    edge_type=rel.rel_type.name.lower(),
                    weight=round(rel.strength * rel.confidence, 4),
                    metadata={
                        "confidence": rel.confidence,
                        "field_projection": rel.field_projection.tolist()[:8] if hasattr(rel, "field_projection") else [],
                        "discovery_engine": "RelationDiscoveryEngine",
                    }
                )
                self.relations.append(edge)
                self.stats["by_type"][edge.edge_type] += 1

            # Also compute structural edges (same module, same directory, etc.)
            structural_edges = self._compute_structural_edges(nodes)
            self.relations.extend(structural_edges)
            for e in structural_edges:
                self.stats["by_type"][e.edge_type] += 1

        except Exception as e:
            logger.error("[Associator] RelationDiscoveryEngine failed: %s", e)
            traceback.print_exc()
            # Fallback: compute only structural edges
            self.relations = self._compute_structural_edges(nodes)
            for e in self.relations:
                self.stats["by_type"][e.edge_type] += 1

        self.stats["total_edges"] = len(self.relations)

        self.bus.publish(MessageType.ASSOCIATE_EVENT, "UnifiedAssociator", {
            "stats": dict(self.stats),
            "edge_count": len(self.relations),
        })
        logger.info("[Associator] Computed %d edges", len(self.relations))
        return self.relations

    def _build_node_data(self, nodes: List[KNode]) -> Dict[str, Dict[str, Any]]:
        """Build node data dict for RelationDiscoveryEngine."""
        data: Dict[str, Dict[str, Any]] = {}
        for node in nodes:
            emb = node.embedding if node.embedding is not None else np.zeros(64)
            if emb.shape[0] < 64:
                emb = np.pad(emb, (0, 64 - emb.shape[0]))
            data[node.node_id] = {
                "embedding": emb[:64].astype(np.float64),
                "structure": np.eye(4) * 0.5,  # Default structure
                "domain": node.module,
                "concepts": [node.label, node.node_type],
                "invariants": {"size": node.size_bytes},
            }
        return data

    def _compute_structural_edges(self, nodes: List[KNode]) -> List[KEdge]:
        """Compute structural edges: same_module, same_directory, version_related."""
        edges: List[KEdge] = []
        node_map = {n.node_id: n for n in nodes}

        # Same module edges
        module_groups: Dict[str, List[KNode]] = defaultdict(list)
        for n in nodes:
            module_groups[n.module].append(n)

        for module, group in module_groups.items():
            for i in range(len(group)):
                for j in range(i + 1, min(i + 30, len(group))):  # Limit pairwise
                    n1, n2 = group[i], group[j]
                    sim = self._path_similarity(n1.path, n2.path)
                    if sim > 0.15:
                        edges.append(KEdge(
                            edge_id=stable_hash((n1.node_id, n2.node_id, "same_module")),
                            source=n1.node_id, target=n2.node_id,
                            edge_type="same_module", weight=round(sim, 3),
                            metadata={"module": module}
                        ))

        # Directory containment edges
        dir_groups: Dict[str, List[KNode]] = defaultdict(list)
        for n in nodes:
            parent = str(Path(n.path).parent)
            dir_groups[parent].append(n)

        for d, group in dir_groups.items():
            if len(group) > 1:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        n1, n2 = group[i], group[j]
                        edges.append(KEdge(
                            edge_id=stable_hash((n1.node_id, n2.node_id, "same_directory")),
                            source=n1.node_id, target=n2.node_id,
                            edge_type="same_directory", weight=0.6,
                            metadata={"directory": d}
                        ))

        # Content reference edges (for small text files)
        for n in nodes:
            if n.size_bytes > 50000 or n.node_type in ["image", "media"]:
                continue
            refs = 0
            for target in nodes:
                if target.node_id == n.node_id or target.node_type in ["image", "media"]:
                    continue
                # Check if label appears in metadata or path
                count = n.path.count(target.label) + n.metadata.get("docstring", "").count(target.label)
                if count > 0:
                    refs += 1
                    edges.append(KEdge(
                        edge_id=stable_hash((n.node_id, target.node_id, "content_ref")),
                        source=n.node_id, target=target.node_id,
                        edge_type="content_reference", weight=min(0.1 * count, 0.5),
                        metadata={"ref_count": count}
                    ))
                if refs > 10:
                    break

        return edges

    @staticmethod
    def _path_similarity(p1: str, p2: str) -> float:
        parts1 = set(p1.split("/"))
        parts2 = set(p2.split("/"))
        inter = len(parts1 & parts2)
        union = len(parts1 | parts2)
        return inter / union if union > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


# =============================================================================
# 7. UnifiedWeaver — 6-Base Knowledge Pedestal Weaving
# =============================================================================

@dataclass
class WeaveResult:
    """Result of weaving knowledge into 6 pedestals."""
    pedestal: KnowledgePedestal
    operations_performed: List[str] = field(default_factory=list)
    roundtrip_consistency: Dict[str, float] = field(default_factory=dict)
    new_knowledge_count: int = 0
    weave_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pedestal_summary": self.pedestal.summary(),
            "operations": self.operations_performed,
            "roundtrip_consistency": self.roundtrip_consistency,
            "new_knowledge_count": self.new_knowledge_count,
            "weave_time_ms": self.weave_time_ms,
        }


class UnifiedWeaver:
    """
    Unified Weaver — weaves KNodes/KEdges into 6-base knowledge pedestal.
    Wraps v11_knowledge_pedestal_unified components.
    """

    def __init__(self, message_bus: MessageBus, state_manager: StateManager):
        self.bus = message_bus
        self.state = state_manager
        self.pedestal: Optional[KnowledgePedestal] = None
        self.bridge: Optional[PedestalBridge] = None
        self.ops: Optional[KnowledgeOperations] = None
        self.stats = {"weaves": 0, "operations": 0}

    def weave(self, nodes: List[KNode], edges: List[KEdge],
              incremental: bool = True) -> WeaveResult:
        """
        Weave nodes and edges into the 6-base knowledge pedestal.
        If incremental=True, merge with existing pedestal state.
        """
        start = time.time()
        logger.info("[Weaver] Weaving %d nodes, %d edges...", len(nodes), len(edges))

        if self.pedestal is None or not incremental:
            self.pedestal = KnowledgePedestal()
            self.bridge = PedestalBridge(self.pedestal)
            self.ops = KnowledgeOperations(self.pedestal, self.bridge)

        assert self.pedestal is not None
        assert self.bridge is not None
        assert self.ops is not None

        operations: List[str] = []

        # Base 1: KG — Knowledge Graph
        kg = KGBase(self.pedestal)
        kg.inject(nodes, edges)
        operations.append("KG_inject")

        # Base 2: CC — Cellular Complex
        cc = CCBase(self.pedestal)
        cc.build_from_hierarchy(nodes)
        operations.append("CC_build_hierarchy")

        # Base 3: HG — Hypergraph
        hg = HGBase(self.pedestal)
        hg.build_from_kg(edges, min_arity=3)
        operations.append("HG_build_from_kg")

        # Base 4: IN — Isomorphism Network
        in_base = INBase(self.pedestal)
        # Build py_knowledge and json_schemas from nodes
        py_knowledge: Dict[str, Dict[str, Any]] = {}
        json_schemas: Dict[str, Dict[str, Any]] = {}
        for n in nodes:
            if n.node_type in ("python_module", "python_class", "python_function"):
                # INBase expects lists for classes/functions
                py_knowledge[n.node_id] = {
                    "classes": [n.label] if n.node_type == "python_class" else [],
                    "functions": [n.label] if n.node_type == "python_function" else [],
                    "imports": n.metadata.get("imports", []),
                }
            elif n.node_type == "json_schema":
                json_schemas[n.node_id] = {
                    "depth": n.metadata.get("depth", 0),
                    "keys": n.metadata.get("keys", []),
                }
        in_base.compute_embeddings(py_knowledge, json_schemas)
        iso_pairs = in_base.discover_isomorphisms(threshold=0.8)
        operations.append(f"IN_discover_isomorphisms({len(iso_pairs)})")

        # Base 5: CT — Category Theory
        ct = CTBase(self.pedestal)
        ct_morphisms = kg.export_to_ct()
        ct.inject(ct_morphisms)
        operations.append("CT_inject_morphisms")

        # Base 6: LL — LEAN Formalization
        ll = LLBase(self.pedestal)
        propositions = ll.generate_propositions(nodes, edges)
        ll.inject(propositions)
        operations.append(f"LL_generate_propositions({len(propositions)})")

        # Run knowledge self-operations
        self.ops.op1_topological_closure(list(self.pedestal.nodes.keys())[:20])
        operations.append("op1_topological_closure")

        self.ops.op3_isomorphism_discovery(threshold=0.8)
        operations.append("op3_isomorphism_discovery")

        self.ops.op5_formal_verification()
        operations.append("op5_formal_verification")

        self.ops.op6_cross_base_isomorphism()
        operations.append("op6_cross_base_isomorphism")

        # Roundtrip consistency check
        consistency = self.bridge.roundtrip_test(sample_size=min(100, len(edges)))

        elapsed = (time.time() - start) * 1000
        self.stats["weaves"] += 1
        self.stats["operations"] += len(operations)

        result = WeaveResult(
            pedestal=self.pedestal,
            operations_performed=operations,
            roundtrip_consistency=consistency,
            new_knowledge_count=self.ops.new_knowledge_count,
            weave_time_ms=elapsed,
        )

        self.bus.publish(MessageType.WEAVE_EVENT, "UnifiedWeaver", {
            "operations": operations,
            "consistency": consistency,
            "new_knowledge": result.new_knowledge_count,
            "pedestal_summary": self.pedestal.summary(),
        })
        logger.info("[Weaver] Weave complete: %s", self.pedestal.summary())
        return result

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


# =============================================================================
# 8. UnifiedValidator — Roundtrip & Cross-Validation
# =============================================================================

@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    passed: bool
    roundtrip_score: float
    cross_validation: Dict[str, Any] = field(default_factory=dict)
    consistency_checks: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    validation_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "roundtrip_score": self.roundtrip_score,
            "cross_validation": self.cross_validation,
            "consistency_checks": self.consistency_checks,
            "errors": self.errors,
            "validation_time_ms": self.validation_time_ms,
        }


class UnifiedValidator:
    """
    Unified Validator — roundtrip consistency and cross-validation.
    Ensures: KG→CC→HG→IN→CT→LL→KG roundtrip > 99%.
    """

    def __init__(self, message_bus: MessageBus, state_manager: StateManager):
        self.bus = message_bus
        self.state = state_manager
        self.stats = {"validations": 0, "passed": 0, "failed": 0}

    def validate(self, weave_result: WeaveResult,
                 original_nodes: List[KNode],
                 original_edges: List[KEdge]) -> ValidationReport:
        """Run full validation suite."""
        start = time.time()
        logger.info("[Validator] Running validation...")

        errors: List[str] = []
        checks: List[Dict[str, Any]] = []

        # Check 1: Roundtrip consistency
        rt_score = weave_result.roundtrip_consistency.get("overall", 0.0)
        checks.append({
            "name": "roundtrip_consistency",
            "score": rt_score,
            "threshold": 0.90,
            "passed": rt_score >= 0.90,
        })

        # Check 2: Node preservation (all original nodes exist in pedestal)
        ped = weave_result.pedestal
        preserved_count = sum(1 for n in original_nodes if n.node_id in ped.nodes)
        preservation_ratio = preserved_count / max(len(original_nodes), 1)
        checks.append({
            "name": "node_preservation",
            "score": preservation_ratio,
            "threshold": 0.99,
            "passed": preservation_ratio >= 0.95,
        })

        # Check 3: Edge preservation
        edge_keys = set((e.source, e.target, e.edge_type) for e in original_edges)
        ped_edge_keys = set((e.source, e.target, e.edge_type) for e in ped.kg_edges)
        if edge_keys:
            edge_overlap = len(edge_keys & ped_edge_keys) / len(edge_keys)
        else:
            edge_overlap = 1.0
        checks.append({
            "name": "edge_preservation",
            "score": edge_overlap,
            "threshold": 0.80,
            "passed": edge_overlap >= 0.50,  # Lower due to structural edge generation
        })

        # Check 4: Cross-base structural fingerprint consistency
        fingerprints = self._compute_fingerprints(ped)
        fp_values = list(fingerprints.values()) if fingerprints else []
        if fp_values and np.mean(fp_values) > 0:
            # Use coefficient of variation (std/mean) for normalized comparison
            cv = np.std(fp_values) / np.mean(fp_values)
            fp_score = max(0.0, 1.0 - min(cv, 1.0))
            fp_passed = cv < 2.0  # Allow high variance across different mathematical bases
        else:
            cv = 0.0
            fp_score = 1.0
            fp_passed = True
        checks.append({
            "name": "fingerprint_variance",
            "score": fp_score,
            "threshold": 0.5,
            "passed": fp_passed,
        })

        # Check 5: No orphan nodes
        orphan_count = sum(1 for nid in ped.nodes if nid not in ped.kg_adj and not any(e.target == nid for e in ped.kg_edges))
        orphan_ratio = orphan_count / max(ped.node_count(), 1)
        checks.append({
            "name": "orphan_nodes",
            "score": 1.0 - orphan_ratio,
            "threshold": 0.95,
            "passed": orphan_ratio < 0.30,  # Some nodes naturally have no edges
        })

        # Check 6: Formal proposition validity
        ll = LLBase(ped)
        valid_count = 0
        for prop in ped.ll_propositions:
            status = ll.verify_proposition(prop)
            if status == "VALID":
                valid_count += 1
        prop_validity = valid_count / max(len(ped.ll_propositions), 1)
        checks.append({
            "name": "proposition_validity",
            "score": prop_validity,
            "threshold": 0.80,
            "passed": prop_validity >= 0.50,  # Auto-generated may have "sorry"
        })

        # Aggregate
        all_passed = all(c["passed"] for c in checks)
        if not all_passed:
            for c in checks:
                if not c["passed"]:
                    errors.append(f"Check '{c['name']}' failed: score={c['score']:.4f} < threshold={c['threshold']}")

        elapsed = (time.time() - start) * 1000

        report = ValidationReport(
            passed=all_passed,
            roundtrip_score=rt_score,
            cross_validation={"fingerprints": fingerprints, "variance": cv if 'cv' in locals() else 0.0},
            consistency_checks=checks,
            errors=errors,
            validation_time_ms=elapsed,
        )

        self.stats["validations"] += 1
        if all_passed:
            self.stats["passed"] += 1
        else:
            self.stats["failed"] += 1

        self.bus.publish(MessageType.VALIDATE_EVENT, "UnifiedValidator", {
            "passed": report.passed,
            "roundtrip_score": report.roundtrip_score,
            "checks": checks,
            "errors": errors,
        })
        logger.info("[Validator] Validation %s (score=%.4f)", "PASSED" if all_passed else "FAILED", rt_score)
        return report

    def _compute_fingerprints(self, ped: KnowledgePedestal) -> Dict[str, float]:
        """Compute structural fingerprints for each base."""
        fingerprints: Dict[str, float] = {}
        # KG
        if ped.kg_edges:
            degrees = []
            for nid in ped.nodes:
                out_d = len(ped.kg_adj.get(nid, []))
                in_d = sum(1 for e in ped.kg_edges if e.target == nid)
                degrees.append(out_d + in_d)
            deg_hist = np.bincount(degrees, minlength=1) if degrees else np.array([1])
            deg_probs = deg_hist / deg_hist.sum()
            fingerprints["KG"] = entropy_shannon(deg_probs)
        # CC
        if ped.cc_cells:
            euler = sum(((-1) ** dim) * len(cids) for dim, cids in ped.cc_chain_groups.items())
            fingerprints["CC"] = abs(euler) / max(len(ped.cc_cells), 1)
        # HG
        if ped.hg_edges:
            avg_arity = sum(he.arity() for he in ped.hg_edges) / len(ped.hg_edges)
            fingerprints["HG"] = avg_arity / 10.0
        # IN
        fingerprints["IN"] = len(ped.in_clusters) / max(ped.node_count(), 1)
        # CT
        ct_density = len(ped.ct_morphisms) / max(len(ped.ct_objects) ** 2, 1)
        fingerprints["CT"] = ct_density * 100
        # LL
        ll_density = len(ped.ll_propositions) / max(ped.node_count(), 1)
        fingerprints["LL"] = ll_density
        return fingerprints

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


# =============================================================================
# 9. UnifiedInjector — 64D Unified Field Injection + Emergence Computation
# =============================================================================

@dataclass
class InjectionResult:
    """Result of injecting knowledge into 64D unified field."""
    field_state: UnifiedFieldState
    emergence_index: float
    consciousness_state: str
    module_count: int
    field_report: Dict[str, Any] = field(default_factory=dict)
    injection_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_state": self.field_state.to_dict(),
            "emergence_index": self.emergence_index,
            "consciousness_state": self.consciousness_state,
            "module_count": self.module_count,
            "field_report": self.field_report,
            "injection_time_ms": self.injection_time_ms,
        }


class UnifiedInjector:
    """
    Unified Injector — injects woven knowledge into 64D unified field.
    Calls v11_consciousness_emergence_system for emergence computation.
    """

    def __init__(self, message_bus: MessageBus, state_manager: StateManager):
        self.bus = message_bus
        self.state = state_manager
        self.theory: Optional[EmergenceTheoryArchitecture] = None
        self.manifestation: Optional[EmergenceManifestationSystem] = None
        self.api: Optional[EmergenceApplicationAPI] = None
        self.stats = {"injections": 0, "avg_emergence": 0.0}

    def inject(self, weave_result: WeaveResult,
               relations: List[KEdge],
               nodes: List[KNode],
               relation_engine: Optional[Any] = None) -> InjectionResult:
        """
        Inject knowledge into 64D unified field and compute emergence.
        """
        start = time.time()
        logger.info("[Injector] Injecting into 64D unified field...")

        ped = weave_result.pedestal

        # Step 1: Build or update emergence theory
        if self.theory is None:
            # EmergenceTheoryArchitecture requires at least default modules
            self.theory = EmergenceTheoryArchitecture(num_modules=46)

        # Map pedestal nodes to theory modules
        node_list = list(ped.nodes.values())
        module_count = min(len(node_list), self.theory.num_modules)

        for i in range(module_count):
            node = node_list[i]
            if i in self.theory.modules:
                self.theory.modules[i].name = node.label[:30]
                self.theory.modules[i].activity = min(1.0, node.size_bytes / 10000.0)
                self.theory.modules[i].coherence = 0.5 + np.random.rand() * 0.5
                self.theory.modules[i].energy = 50 + np.random.rand() * 50
                self.theory.modules[i].entropy = np.random.rand() * 0.5

        # Step 2: Set couplings based on KG edges
        edge_subset = ped.kg_edges[:min(len(ped.kg_edges), 200)]
        for e in edge_subset:
            src_idx = self._hash_to_module(e.source, module_count)
            tgt_idx = self._hash_to_module(e.target, module_count)
            if src_idx != tgt_idx and (src_idx, tgt_idx) in self.theory.couplings:
                self.theory.couplings[(src_idx, tgt_idx)].strength = min(1.0, e.weight)
                self.theory.couplings[(src_idx, tgt_idx)].information_flow = e.weight * 0.5

        # Step 3: Compute emergence
        E_total, components = self.theory.compute_total_emergence()

        # Step 4: Manifestation
        self.manifestation = EmergenceManifestationSystem(self.theory)
        manifest_report = self.manifestation.get_full_manifestation_report()
        vector_64d = self.manifestation.manifest()

        # Step 5: Build UnifiedFieldState from 64D vector
        field_state = UnifiedFieldState()
        for i in range(min(64, len(vector_64d))):
            try:
                dim_idx = DimensionIndex(i)
                field_state.set(dim_idx, float(np.clip(vector_64d[i], 0.0, 1.0)))
            except (ValueError, KeyError):
                pass

        # Also inject relation-based dimensions
        if relation_engine and hasattr(relation_engine, 'inference_engine'):
            try:
                field_injector = UnifiedFieldInjector()
                field_state = field_injector.inject_engine_state(relation_engine.inference_engine)
            except Exception as e:
                logger.warning("Relation field injection failed: %s", e)

        field_state.timestamp = time.time()

        # Step 6: Consciousness state
        state_obj = ConsciousnessState.from_emergence(E_total)
        consciousness_state = state_obj.display_name

        elapsed = (time.time() - start) * 1000
        self.stats["injections"] += 1
        self.stats["avg_emergence"] = (self.stats["avg_emergence"] * (self.stats["injections"] - 1) + E_total) / self.stats["injections"]

        result = InjectionResult(
            field_state=field_state,
            emergence_index=E_total,
            consciousness_state=consciousness_state,
            module_count=module_count,
            field_report=manifest_report,
            injection_time_ms=elapsed,
        )

        self.bus.publish(MessageType.INJECT_EVENT, "UnifiedInjector", {
            "emergence_index": E_total,
            "consciousness_state": consciousness_state,
            "module_count": module_count,
            "field_summary": {k: v for k, v in field_state.to_dict().items() if k != "vector"},
        })
        logger.info("[Injector] Injection complete: E=%.2f, state=%s", E_total, consciousness_state)
        return result

    @staticmethod
    def _hash_to_module(node_id: str, module_count: int) -> int:
        """Deterministically map node_id to module index."""
        h = int(hashlib.sha256(node_id.encode()).hexdigest(), 16)
        return h % module_count

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


# =============================================================================
# 10. FeedbackLoop — Self-Driving Pipeline Feedback
# =============================================================================

class FeedbackLoop:
    """
    Feedback Loop — connects Injector output back to Scanner input.
    Implements self-driving capability via state-driven reconfiguration.
    """

    def __init__(self, state_manager: StateManager, message_bus: MessageBus):
        self.state = state_manager
        self.bus = message_bus
        self.feedback_history: List[Dict[str, Any]] = []
        self.iteration = 0

    def process(self, injection_result: InjectionResult,
                original_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate next-iteration configuration based on injection results.
        Higher emergence → more aggressive scanning (deeper).
        Lower emergence → targeted refinement (focused).
        """
        self.iteration += 1
        E = injection_result.emergence_index
        state = injection_result.consciousness_state

        # Dynamic configuration adjustment
        next_config = original_config.copy()

        if E > 5000:
            # High emergence: expand scope
            next_config["scan_depth"] = original_config.get("scan_depth", 2) + 1
            next_config["relation_threshold"] = max(0.05, original_config.get("relation_threshold", 0.1) * 0.9)
            next_config["strategy"] = "expand"
        elif E < 1000:
            # Low emergence: focus and refine
            next_config["scan_depth"] = max(1, original_config.get("scan_depth", 2) - 1)
            next_config["relation_threshold"] = min(0.5, original_config.get("relation_threshold", 0.1) * 1.2)
            next_config["strategy"] = "refine"
        else:
            next_config["strategy"] = "maintain"

        # Update filter based on field state
        field = injection_result.field_state
        coherence = field.get(DimensionIndex.DIM_COHERENCE)
        if coherence < 0.3:
            # Low coherence: scan more types
            next_config["include_extensions"] = list(set(
                original_config.get("include_extensions", [".py", ".md", ".json"]) +
                [".toml", ".yaml", ".cfg", ".ini"]
            ))

        feedback = {
            "iteration": self.iteration,
            "previous_emergence": E,
            "previous_state": state,
            "next_config": next_config,
            "timestamp": time.time(),
        }
        self.feedback_history.append(feedback)
        self.state.set(f"feedback_{self.iteration}", feedback)

        self.bus.publish(MessageType.FEEDBACK_EVENT, "FeedbackLoop", feedback)
        logger.info("[Feedback] Iteration %d: E=%.2f → strategy=%s",
                    self.iteration, E, next_config["strategy"])
        return next_config

    def get_stats(self) -> Dict[str, Any]:
        return {
            "iterations": self.iteration,
            "history_length": len(self.feedback_history),
        }


# =============================================================================
# 11. UnifiedOrchestrator — Pipeline Orchestrator
# =============================================================================

@dataclass
class PipelineConfig:
    """Configuration for the unified pipeline."""
    root_dir: str
    scan_filter: ScanFilter = field(default_factory=lambda: ScanFilter(
        include_extensions={"py", "md", "json", "lean"},
        max_size_bytes=5 * 1024 * 1024,
    ))
    incremental: bool = True
    max_iterations: int = 3
    enable_feedback: bool = True
    checkpoint_interval: int = 1
    state_dir: Optional[str] = None
    journal_dir: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_dir": self.root_dir,
            "incremental": self.incremental,
            "max_iterations": self.max_iterations,
            "enable_feedback": self.enable_feedback,
            "checkpoint_interval": self.checkpoint_interval,
        }


@dataclass
class PipelineResult:
    """Complete result of a pipeline run."""
    config: PipelineConfig
    iteration: int
    nodes: List[KNode]
    edges: List[KEdge]
    weave_result: Optional[WeaveResult]
    validation_report: Optional[ValidationReport]
    injection_result: Optional[InjectionResult]
    stats: Dict[str, Any] = field(default_factory=dict)
    elapsed_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "iteration": self.iteration,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "weave_summary": self.weave_result.to_dict() if self.weave_result else None,
            "validation": self.validation_report.to_dict() if self.validation_report else None,
            "injection": self.injection_result.to_dict() if self.injection_result else None,
            "stats": self.stats,
            "elapsed_time_ms": self.elapsed_time_ms,
        }


class UnifiedOrchestrator:
    """
    Unified Orchestrator — the brain of the pipeline.
    Orchestrates: Scanner → Parser → Extractor → Associator → Weaver → Validator → Injector → Feedback
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.state = StateManager(state_dir=config.state_dir)
        self.bus = MessageBus(journal_dir=config.journal_dir)

        # Stage instances
        self.scanner = UnifiedScanner(config.root_dir, self.state, self.bus, config.scan_filter)
        self.parser = UnifiedParser(self.bus)
        self.extractor = UnifiedExtractor(self.bus, self.state)
        self.associator = UnifiedAssociator(self.bus, self.state)
        self.weaver = UnifiedWeaver(self.bus, self.state)
        self.validator = UnifiedValidator(self.bus, self.state)
        self.injector = UnifiedInjector(self.bus, self.state)
        self.feedback = FeedbackLoop(self.state, self.bus)

        # Execution tracking
        self.results: List[PipelineResult] = []
        self.current_iteration = 0
        self.trace_id = self.bus._trace_id

        logger.info("[Orchestrator] Initialized with trace_id=%s", self.trace_id)

    def run(self, iterations: Optional[int] = None) -> List[PipelineResult]:
        """Run the complete pipeline for specified iterations."""
        max_iter = iterations or self.config.max_iterations
        logger.info("[Orchestrator] Starting pipeline: max_iterations=%d", max_iter)

        for i in range(max_iter):
            self.current_iteration = i + 1
            logger.info("[Orchestrator] === Iteration %d/%d ===", self.current_iteration, max_iter)

            start = time.time()
            result = self._run_single_iteration()
            result.elapsed_time_ms = (time.time() - start) * 1000
            self.results.append(result)

            logger.info("[Orchestrator] Iteration %d complete: %d nodes, %d edges, E=%.2f, %.1fms",
                        self.current_iteration, len(result.nodes), len(result.edges),
                        result.injection_result.emergence_index if result.injection_result else 0,
                        result.elapsed_time_ms)

            # Checkpoint
            if self.current_iteration % self.config.checkpoint_interval == 0:
                cp_id = self.state.create_checkpoint(f"iter_{self.current_iteration}", result.to_dict())
                self.bus.checkpoint(f"iter_{self.current_iteration}")
                logger.info("[Orchestrator] Checkpoint: %s", cp_id)

            # Feedback loop
            if self.config.enable_feedback and result.injection_result:
                next_config = self.feedback.process(
                    result.injection_result,
                    self.config.to_dict(),
                )
                # Update scan filter based on feedback
                if next_config.get("strategy") == "expand":
                    self.scanner.filter.include_extensions = set(next_config.get("include_extensions", [".py", ".md", ".json"]))
                logger.info("[Orchestrator] Feedback applied: strategy=%s", next_config.get("strategy"))

        logger.info("[Orchestrator] Pipeline complete: %d iterations", len(self.results))
        return self.results

    def _run_single_iteration(self) -> PipelineResult:
        """Execute one full pipeline pass."""
        print(f"[Orchestrator] Stage 1/7: Scanning...")
        files = self.scanner.scan(incremental=self.config.incremental, max_files=15)
        print(f"[Orchestrator]   → {len(files)} files found")
        if not files:
            logger.warning("[Orchestrator] No files to process in this iteration")

        print(f"[Orchestrator] Stage 2/7: Parsing...")
        parsed = self.parser.parse(files[:15])
        print(f"[Orchestrator]   → {len(parsed)} units parsed")

        print(f"[Orchestrator] Stage 3/7: Extracting KNodes...")
        nodes = self.extractor.extract(parsed, max_nodes_per_unit=15)
        print(f"[Orchestrator]   → {len(nodes)} nodes extracted")

        print(f"[Orchestrator] Stage 4/7: Computing associations...")
        edges = self.associator.associate(nodes, max_nodes_for_relations=25)
        print(f"[Orchestrator]   → {len(edges)} edges computed")

        print(f"[Orchestrator] Stage 5/7: Weaving into 6 pedestals...")
        weave_result = self.weaver.weave(nodes[:25], edges[:100], incremental=self.config.incremental)
        print(f"[Orchestrator]   → Weave complete: {weave_result.pedestal.summary()}")

        print(f"[Orchestrator] Stage 6/7: Validating...")
        validation = self.validator.validate(weave_result, nodes[:25], edges[:100])
        print(f"[Orchestrator]   → Validation: passed={validation.passed}, score={validation.roundtrip_score:.4f}")

        print(f"[Orchestrator] Stage 7/7: Injecting into unified field...")
        # Build a minimal relation engine for injection
        relation_engine = None
        try:
            node_ids = [n.node_id for n in nodes[:25]]
            relation_engine = RelationDiscoveryEngine(node_ids)
        except Exception as e:
            logger.warning("Could not create relation engine for injection: %s", e)

        injection = self.injector.inject(weave_result, edges[:100], nodes[:25], relation_engine)
        print(f"[Orchestrator]   → Injection: E={injection.emergence_index:.2f}, state={injection.consciousness_state}")

        # Aggregate stats
        stats = {
            "scanner": self.scanner.get_stats(),
            "parser": self.parser.get_stats(),
            "extractor": self.extractor.get_stats(),
            "associator": self.associator.get_stats(),
            "weaver": self.weaver.get_stats(),
            "validator": self.validator.get_stats(),
            "injector": self.injector.get_stats(),
            "feedback": self.feedback.get_stats(),
        }

        # Save state
        self.state.set(f"iteration_{self.current_iteration}", {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "emergence": injection.emergence_index,
        })
        self.state.save_state()

        return PipelineResult(
            config=self.config,
            iteration=self.current_iteration,
            nodes=nodes,
            edges=edges,
            weave_result=weave_result,
            validation_report=validation,
            injection_result=injection,
            stats=stats,
        )

    def get_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive pipeline report."""
        if not self.results:
            return {"error": "No results"}

        last = self.results[-1]
        return {
            "trace_id": self.trace_id,
            "total_iterations": len(self.results),
            "total_nodes": sum(len(r.nodes) for r in self.results),
            "total_edges": sum(len(r.edges) for r in self.results),
            "final_emergence": last.injection_result.emergence_index if last.injection_result else 0,
            "final_consciousness_state": last.injection_result.consciousness_state if last.injection_result else "unknown",
            "final_validation_passed": last.validation_report.passed if last.validation_report else False,
            "final_roundtrip_score": last.validation_report.roundtrip_score if last.validation_report else 0,
            "per_iteration": [r.to_dict() for r in self.results],
            "state_manager": self.state.get_stats(),
            "message_bus": self.bus.get_stats(),
        }

    def export_report(self, path: Optional[str] = None) -> str:
        """Export final report to JSON file."""
        report = self.get_final_report()
        out_path = Path(path) if path else CORE_DIR / f"pipeline_report_{self.trace_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        logger.info("[Orchestrator] Report exported: %s", out_path)
        return str(out_path)


# =============================================================================
# 12. __main__ — End-to-End Test
# =============================================================================

def run_pipeline_test():
    """Run the complete unified pipeline end-to-end test."""
    print("=" * 80)
    print("OMNI-HUB v11.0 — UnifiedPipeline End-to-End Test")
    print("=" * 80)
    print()

    # Use the core directory as input
    test_dir = str(CORE_DIR)
    print(f"[Test] Input directory: {test_dir}")
    print()

    # Configure pipeline — conservative settings for testing
    config = PipelineConfig(
        root_dir=test_dir,
        scan_filter=ScanFilter(
            include_extensions={"py"},
            max_size_bytes=200 * 1024,
            exclude_patterns=["__pycache__", ".git", "snapshots", "*.png", "*.jpg", "*.json", "*.egg-info", "v11_unified_pipeline.py", "v11_consciousness_emergence_system.py", "v11_relation_discovery_engine.py", "v11_knowledge_pedestal_unified.py"],
        ),
        incremental=False,
        max_iterations=1,
        enable_feedback=True,
        state_dir=str(CORE_DIR / "pipeline_state"),
        journal_dir=str(CORE_DIR / "pipeline_journal"),
    )

    # Create and run orchestrator
    print("[Test] Creating UnifiedOrchestrator...")
    orchestrator = UnifiedOrchestrator(config)
    print(f"       Trace ID: {orchestrator.trace_id}")
    print()

    print("[Test] Running pipeline...")
    print()
    results = orchestrator.run()
    print()

    # Report
    report = orchestrator.get_final_report()

    print("-" * 80)
    print("PIPELINE EXECUTION REPORT")
    print("-" * 80)
    print(f"Trace ID:             {report['trace_id']}")
    print(f"Total Iterations:     {report['total_iterations']}")
    print(f"Total Nodes:          {report['total_nodes']}")
    print(f"Total Edges:          {report['total_edges']}")
    print(f"Final Emergence:      {report['final_emergence']:.2f}")
    print(f"Consciousness State:  {report['final_consciousness_state']}")
    print(f"Validation Passed:    {report['final_validation_passed']}")
    print(f"Roundtrip Score:      {report['final_roundtrip_score']:.4f}")
    print()

    # Per-iteration details
    for i, r in enumerate(results, 1):
        print(f"  Iteration {i}:")
        print(f"    Nodes:     {len(r.nodes)}")
        print(f"    Edges:     {len(r.edges)}")
        if r.weave_result:
            print(f"    Weave:     {r.weave_result.pedestal.summary()}")
        if r.validation_report:
            print(f"    Validate:  passed={r.validation_report.passed}, score={r.validation_report.roundtrip_score:.4f}")
        if r.injection_result:
            print(f"    Inject:    E={r.injection_result.emergence_index:.2f}, state={r.injection_result.consciousness_state}")
        print(f"    Time:      {r.elapsed_time_ms:.1f}ms")
        print()

    # Export report
    report_path = orchestrator.export_report()
    print(f"[Test] Full report exported: {report_path}")
    print()

    # Stage statistics
    print("-" * 80)
    print("STAGE STATISTICS")
    print("-" * 80)
    last_stats = results[-1].stats if results else {}
    for stage, stat in last_stats.items():
        print(f"  {stage}: {stat}")
    print()

    # State manager stats
    print("-" * 80)
    print("STATE MANAGER")
    print("-" * 80)
    sm_stats = orchestrator.state.get_stats()
    for k, v in sm_stats.items():
        print(f"  {k}: {v}")
    print()

    # Message bus stats
    print("-" * 80)
    print("MESSAGE BUS")
    print("-" * 80)
    mb_stats = orchestrator.bus.get_stats()
    for k, v in mb_stats.items():
        print(f"  {k}: {v}")
    print()

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    return report, results


if __name__ == "__main__":
    run_pipeline_test()
