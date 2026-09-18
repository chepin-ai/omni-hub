#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v3.1 — Bidirectional Drive Engine
============================================

双向驱动引擎负责管理11条计算线之间的正反向信号传输：

- **正向驱动 (forward_drive)**: 高 SI → 低 SI，用于指令下发、参数同步、调度分派
- **反向反馈 (reverse_feedback)**: 低 SI → 高 SI，用于状态上报、健康度回流、结果回传
- **双向脉冲 (bidirectional_pulse)**: 同时触发正向+反向通道，实现一次往返握手
- **互激耦合 (update_coupling)**: 基于健康度差异动态调整11×11耦合矩阵

11 线配置:
    ucif2 (SI 5.0) — 核心调度器
    lgt   (SI 4.0), qfa (SI 4.0), vinf (SI 4.0), qgl (SI 4.0)
    qlv   (SI 3.5), cisvr (SI 3.5), qtlv (SI 3.5)
    usrm  (SI 3.0), cfts (SI 3.0)
    lvlu  (SI 4.5) — 观察中，SI5-OMNI ELIGIBLE

版本: 3.1.0
作者: OMNI-HUB Architecture Team
"""

from __future__ import annotations

import json
import os
import time
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import logging


# =============================================================================
# 常量定义
# =============================================================================

# 11条计算线的默认 SI 等级与健康度
DEFAULT_LINE_CONFIG: Dict[str, Dict[str, Any]] = {
    "ucif2": {"si": 5.0, "health": 1.00, "tower": "hub",     "circle": "command", "layer": 0},
    "lgt":   {"si": 4.0, "health": 0.98, "tower": "wheel",   "circle": "session",  "layer": 1},
    "qfa":   {"si": 4.0, "health": 0.97, "tower": "wheel",   "circle": "consensus","layer": 1},
    "vinf":  {"si": 4.0, "health": 0.96, "tower": "spine",   "circle": "command",  "layer": 2},
    "qgl":   {"si": 4.0, "health": 0.95, "tower": "cauldron","circle": "relay",    "layer": 3},
    "lvlu":  {"si": 4.5, "health": 0.94, "tower": "tower",   "circle": "relay",    "layer": 4},
    "qlv":   {"si": 3.5, "health": 0.93, "tower": "cauldron","circle": "relay",    "layer": 3},
    "cisvr": {"si": 3.5, "health": 0.92, "tower": "ring",    "circle": "consensus","layer": 5},
    "qtlv":  {"si": 3.5, "health": 0.91, "tower": "ring",    "circle": "relay",    "layer": 5},
    "usrm":  {"si": 3.0, "health": 0.90, "tower": "spine",   "circle": "session",  "layer": 2},
    "cfts":  {"si": 3.0, "health": 0.89, "tower": "tower",   "circle": "relay",    "layer": 4},
}

LINE_NAMES: List[str] = list(DEFAULT_LINE_CONFIG.keys())
NUM_LINES: int = len(LINE_NAMES)

# SI 阈值
SI_THRESHOLD_OMNI: float = 5.0      # SI5 核心调度器
SI_THRESHOLD_HIGH: float = 4.0      # SI4 高等级线
SI_THRESHOLD_MID: float = 3.5       # SI3.5 中等等级线
SI_THRESHOLD_LOW: float = 3.0       # SI3 基础等级线

# 驱动权限矩阵阈值 — 正向要求 source_si >= target_si + 0.1
MIN_SI_GAP_FORWARD: float = 0.1

# 耦合系数计算参数
COUPLING_SCALE: float = 0.001       # mutual = 0.001 * (avg_other - self)
COUPLING_CLIP_MIN: float = -0.5     # 耦合矩阵下限
COUPLING_CLIP_MAX: float = 0.5      # 耦合矩阵上限

# 健康度回流参数
HEALTH_REFLUX_DECAY: float = 0.95   # 健康度衰减系数
HEALTH_REFLUX_BOOST: float = 0.02   # 成功反馈的健康度增益
HEALTH_REFLUX_PENALTY: float = 0.05 # 失败反馈的健康度惩罚

# 通道统计滑动窗口大小
STATS_WINDOW_SIZE: int = 1000


# =============================================================================
# 类型别名
# =============================================================================

DriveSignal = Dict[str, Any]
FeedbackPacket = Dict[str, Any]
LineConfig = Dict[str, Dict[str, Any]]


# =============================================================================
# 辅助函数
# =============================================================================

def _generate_seq_id() -> str:
    """生成全局唯一的序列标识符 (UUID4)."""
    return str(uuid.uuid4())


def _iso_timestamp() -> str:
    """返回当前 UTC 时间的 ISO 8601 格式字符串."""
    return datetime.now(timezone.utc).isoformat()


def _si_level_to_index(si: float) -> int:
    """将 SI 等级映射到离散索引 (0-4)."""
    if si >= SI_THRESHOLD_OMNI:
        return 4
    elif si >= SI_THRESHOLD_HIGH:
        return 3
    elif si >= SI_THRESHOLD_MID:
        return 2
    elif si >= SI_THRESHOLD_LOW:
        return 1
    else:
        return 0


def _default_hub_state() -> Dict[str, Any]:
    """构造默认的 Hub 状态字典."""
    return {
        "version": "3.1.0",
        "lines": deepcopy(DEFAULT_LINE_CONFIG),
        "global_health": 0.95,
        "coupling_matrix": np.zeros((NUM_LINES, NUM_LINES)).tolist(),
        "last_updated": _iso_timestamp(),
        "pulse_count": 0,
        "forward_count": 0,
        "reverse_count": 0,
    }


# =============================================================================
# 核心类: BidirectionalDrive
# =============================================================================

class BidirectionalDrive:
    """
    OMNI-HUB v3.1 双向驱动引擎.

    管理11条计算线之间的高保真双向信号传输，包括：
    - 正向驱动通道 (forward_channels): SI5 → SI1 指令下发
    - 反向反馈通道 (reverse_channels): SI1 → SI5 状态上报
    - 互激耦合矩阵 (coupling_matrix): 11×11 动态耦合系数

    Attributes:
        hub_state_path (str): Hub 状态持久化文件路径.
        hub_state (dict): 当前内存中的 Hub 状态.
        forward_channels (dict): 正向通道状态与历史.
        reverse_channels (dict): 反向通道状态与历史.
        coupling_matrix (np.ndarray): 11×11 互激耦合矩阵.
        _line_index (dict): 线名到矩阵索引的映射.
    """

    def __init__(self, hub_state_path: str) -> None:
        """
        初始化双向驱动引擎.

        Args:
            hub_state_path: Hub 状态 JSON 文件的绝对或相对路径.
                            若文件不存在，将自动创建默认状态.
        """
        self.hub_state_path: str = hub_state_path
        self.hub_state: Dict[str, Any] = self.load_state(hub_state_path)

        # 通道状态: 每对线维护一个状态对象
        self.forward_channels: Dict[str, Dict[str, Any]] = {}
        self.reverse_channels: Dict[str, Dict[str, Any]] = {}

        # 初始化耦合矩阵
        self.coupling_matrix: np.ndarray = np.zeros((NUM_LINES, NUM_LINES), dtype=np.float64)
        loaded_matrix = self.hub_state.get("coupling_matrix")
        if loaded_matrix is not None:
            try:
                self.coupling_matrix = np.array(loaded_matrix, dtype=np.float64)
            except (ValueError, TypeError):
                self.coupling_matrix = np.zeros((NUM_LINES, NUM_LINES), dtype=np.float64)

        # 线名到索引的映射
        self._line_index: Dict[str, int] = {name: idx for idx, name in enumerate(LINE_NAMES)}

        # 初始化通道历史
        self._init_channel_histories()

    # -------------------------------------------------------------------------
    # 状态管理
    # -------------------------------------------------------------------------

    def load_state(self, path: str) -> Dict[str, Any]:
        """
        从 JSON 文件加载 Hub 状态.

        若文件不存在或解析失败，返回默认状态并持久化.

        Args:
            path: 状态文件路径.

        Returns:
            Hub 状态字典.
        """
        state_path = Path(path)
        if state_path.exists():
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # 确保关键字段存在
                if "lines" not in loaded:
                    loaded["lines"] = deepcopy(DEFAULT_LINE_CONFIG)
                if "version" not in loaded:
                    loaded["version"] = "3.1.0"
                return loaded
            except (json.JSONDecodeError, OSError, PermissionError) as exc:
                # 日志记录并回退到默认状态
                logger.info(f"[BidirectionalDrive] 状态加载失败 ({exc}), 使用默认状态.")
                default = _default_hub_state()
                self.save_state(path, default)
                return default
        else:
            default = _default_hub_state()
            self.save_state(path, default)
            return default

    def save_state(self, path: Optional[str] = None,
                   state: Optional[Dict[str, Any]] = None) -> None:
        """
        将 Hub 状态持久化到 JSON 文件.

        Args:
            path: 目标文件路径; 若为 None 则使用 self.hub_state_path.
            state: 要保存的状态字典; 若为 None 则使用 self.hub_state.
        """
        target_path = Path(path) if path else Path(self.hub_state_path)
        target_state = state if state is not None else self.hub_state

        # 确保目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 深拷贝并序列化 numpy 数组
        serializable = deepcopy(target_state)
        if isinstance(serializable.get("coupling_matrix"), np.ndarray):
            serializable["coupling_matrix"] = serializable["coupling_matrix"].tolist()

        serializable["last_updated"] = _iso_timestamp()

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
        except (OSError, PermissionError) as exc:
            raise RuntimeError(f"状态保存失败: {exc}") from exc

    # -------------------------------------------------------------------------
    # 通道初始化与统计
    # -------------------------------------------------------------------------

    def _init_channel_histories(self) -> None:
        """初始化所有线对的正向/反向通道状态."""
        for src in LINE_NAMES:
            for dst in LINE_NAMES:
                if src == dst:
                    continue
                key = f"{src}→{dst}"
                self.forward_channels[key] = {
                    "packets": 0,
                    "acked": 0,
                    "failed": 0,
                    "latency_sum_ms": 0.0,
                    "last_pulse": None,
                    "history": [],  # 最近 N 条记录
                }
                self.reverse_channels[key] = {
                    "packets": 0,
                    "acked": 0,
                    "failed": 0,
                    "latency_sum_ms": 0.0,
                    "last_pulse": None,
                    "history": [],
                }

    def get_channel_stats(self, direction: str = "all") -> Dict[str, Any]:
        """
        获取通道统计信息.

        Args:
            direction: "forward" | "reverse" | "all".

        Returns:
            包含各通道统计数据的字典.
        """
        stats: Dict[str, Any] = {
            "timestamp": _iso_timestamp(),
            "direction": direction,
        }

        def _summarize(channels: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
            total_packets = sum(c["packets"] for c in channels.values())
            total_acked = sum(c["acked"] for c in channels.values())
            total_failed = sum(c["failed"] for c in channels.values())
            ack_rate = total_acked / total_packets if total_packets > 0 else 0.0
            avg_latency = (
                sum(c["latency_sum_ms"] for c in channels.values()) / total_packets
                if total_packets > 0 else 0.0
            )
            return {
                "total_packets": total_packets,
                "total_acked": total_acked,
                "total_failed": total_failed,
                "ack_rate": round(ack_rate, 4),
                "avg_latency_ms": round(avg_latency, 2),
                "active_channels": sum(1 for c in channels.values() if c["packets"] > 0),
            }

        if direction in ("forward", "all"):
            stats["forward"] = _summarize(self.forward_channels)
        if direction in ("reverse", "all"):
            stats["reverse"] = _summarize(self.reverse_channels)

        # 全局聚合
        stats["global"] = {
            "pulse_count": self.hub_state.get("pulse_count", 0),
            "forward_count": self.hub_state.get("forward_count", 0),
            "reverse_count": self.hub_state.get("reverse_count", 0),
            "global_health": self.hub_state.get("global_health", 0.0),
        }

        return stats

    # -------------------------------------------------------------------------
    # 正向驱动
    # -------------------------------------------------------------------------

    def forward_drive(self, source_si: float, target_si: float,
                      signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        正向驱动: 高 SI → 低 SI (指令下发 / 参数同步).

        权限校验规则:
            1. source_si 必须严格大于 target_si + MIN_SI_GAP_FORWARD (默认 0.1).
            2. 源线必须在 hub_state["lines"] 中已注册.
            3. 信号必须包含有效的 payload 字段.

        驱动成功后，更新目标线的接收计数与源线的下发计数.

        Args:
            source_si: 源线的 SI 等级.
            target_si: 目标线的 SI 等级.
            signal: 驱动信号字典，必须包含以下键:
                - "source_line" (str): 源线名称.
                - "target_line" (str): 目标线名称.
                - "payload" (dict): 载荷数据，需含 "type" 和 "data".
                可选键:
                - "priority" (int): 优先级 0-9，0 为最高.

        Returns:
            驱动结果字典，包含 ack、latency_ms、status、channel 等字段.
        """
        t_start = time.perf_counter()
        result: Dict[str, Any] = {
            "ack": False,
            "direction": "forward",
            "status": "failed",
            "error": None,
            "latency_ms": 0.0,
            "seq_id": _generate_seq_id(),
        }

        # --- 参数提取与校验 ---
        src_line = signal.get("source_line", "")
        dst_line = signal.get("target_line", "")
        payload = signal.get("payload", {})
        priority = signal.get("priority", 5)

        # 线名校验
        if src_line not in self.hub_state.get("lines", {}):
            result["error"] = f"源线 '{src_line}' 未注册."
            result["latency_ms"] = (time.perf_counter() - t_start) * 1000
            return result
        if dst_line not in self.hub_state.get("lines", {}):
            result["error"] = f"目标线 '{dst_line}' 未注册."
            result["latency_ms"] = (time.perf_counter() - t_start) * 1000
            return result

        # SI 权限校验: 高 SI → 低 SI
        if source_si < target_si + MIN_SI_GAP_FORWARD:
            result["error"] = (
                f"正向驱动权限不足: source_si({source_si}) 必须 >= "
                f"target_si({target_si}) + {MIN_SI_GAP_FORWARD}"
            )
            result["latency_ms"] = (time.perf_counter() - t_start) * 1000
            return result

        # payload 校验
        if not isinstance(payload, dict) or "type" not in payload:
            result["error"] = "信号 payload 无效，缺少 'type' 字段."
            result["latency_ms"] = (time.perf_counter() - t_start) * 1000
            return result

        # --- 构建标准化 DriveSignal ---
        drive_signal: DriveSignal = {
            "direction": "forward",
            "source": {"line": src_line, "si_level": source_si},
            "target": {"line": dst_line, "si_level": target_si},
            "payload": payload,
            "timestamp": _iso_timestamp(),
            "seq_id": result["seq_id"],
            "priority": max(0, min(9, int(priority))),
        }

        # --- 执行驱动逻辑 ---
        channel_key = f"{src_line}→{dst_line}"
        ch = self.forward_channels.setdefault(channel_key, {
            "packets": 0, "acked": 0, "failed": 0,
            "latency_sum_ms": 0.0, "last_pulse": None, "history": [],
        })

        # 模拟通道时延 (与 SI 差距成反比，差距越大时延越低)
        si_gap = max(0.0, source_si - target_si)
        simulated_latency = max(1.0, 50.0 / (1.0 + si_gap * 10))

        # 更新状态
        ch["packets"] += 1
        ch["acked"] += 1
        ch["last_pulse"] = drive_signal["timestamp"]
        ch["latency_sum_ms"] += simulated_latency
        ch["history"].append({
            "seq_id": drive_signal["seq_id"],
            "timestamp": drive_signal["timestamp"],
            "latency_ms": simulated_latency,
            "status": "completed",
        })
        # 滑动窗口截断
        if len(ch["history"]) > STATS_WINDOW_SIZE:
            ch["history"] = ch["history"][-STATS_WINDOW_SIZE:]

        # 更新 hub_state 计数
        self.hub_state["forward_count"] = self.hub_state.get("forward_count", 0) + 1

        # 更新目标线的接收状态
        lines = self.hub_state.setdefault("lines", {})
        dst_info = lines.setdefault(dst_line, deepcopy(DEFAULT_LINE_CONFIG.get(dst_line, {})))
        dst_info["last_forward_recv"] = drive_signal["timestamp"]
        dst_info["forward_recv_count"] = dst_info.get("forward_recv_count", 0) + 1

        # 构建成功结果
        result["ack"] = True
        result["status"] = "completed"
        result["latency_ms"] = round(simulated_latency, 2)
        result["channel"] = channel_key
        result["drive_signal"] = drive_signal
        result["si_gap"] = round(si_gap, 2)

        # 自动保存状态
        self.save_state()

        return result

    # -------------------------------------------------------------------------
    # 反向反馈
    # -------------------------------------------------------------------------

    def reverse_feedback(self, source_si: float, target_si: float,
                         feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        反向反馈: 低 SI → 高 SI (状态上报 / 健康度回流).

        权限校验规则:
            1. source_si 必须严格小于 target_si (低 SI 向高 SI 上报).
            2. 源线、目标线必须在 hub_state["lines"] 中已注册.
            3. feedback 必须包含有效的 health_delta 字段.

        健康度回流计算:
            - 成功反馈: target_health += health_delta * HEALTH_REFLUX_BOOST
            - 失败反馈: target_health -= HEALTH_REFLUX_PENALTY
            - 全局健康度同步更新.

        Args:
            source_si: 源线 (低 SI) 的 SI 等级.
            target_si: 目标线 (高 SI) 的 SI 等级.
            feedback: 反馈数据字典，必须包含:
                - "source_line" (str): 源线名称.
                - "target_line" (str): 目标线名称.
                - "health_delta" (float): 健康度变化量 (-1.0 ~ 1.0).
                可选:
                - "si_proposal" (float): 源线请求的 SI 调整建议.
                - "status" (str): "completed" | "pending" | "failed".

        Returns:
            反馈处理结果字典，包含 ack、health_adjusted、new_health 等字段.
        """
        t_start = time.perf_counter()
        result: Dict[str, Any] = {
            "ack": False,
            "direction": "reverse",
            "status": "failed",
            "error": None,
            "latency_ms": 0.0,
            "health_adjusted": 0.0,
            "new_health": 0.0,
            "seq_id": _generate_seq_id(),
        }

        # --- 参数提取与校验 ---
        src_line = feedback.get("source_line", "")
        dst_line = feedback.get("target_line", "")
        health_delta = feedback.get("health_delta", 0.0)
        si_proposal = feedback.get("si_proposal", None)
        fb_status = feedback.get("status", "completed")

        # 线名校验
        if src_line not in self.hub_state.get("lines", {}):
            result["error"] = f"源线 '{src_line}' 未注册."
            result["latency_ms"] = (time.perf_counter() - t_start) * 1000
            return result
        if dst_line not in self.hub_state.get("lines", {}):
            result["error"] = f"目标线 '{dst_line}' 未注册."
            result["latency_ms"] = (time.perf_counter() - t_start) * 1000
            return result

        # SI 权限校验: 低 SI → 高 SI
        if source_si >= target_si:
            result["error"] = (
                f"反向反馈权限不足: source_si({source_si}) 必须 < "
                f"target_si({target_si})"
            )
            result["latency_ms"] = (time.perf_counter() - t_start) * 1000
            return result

        # health_delta 范围校验
        if not isinstance(health_delta, (int, float)):
            result["error"] = "health_delta 必须是数值."
            result["latency_ms"] = (time.perf_counter() - t_start) * 1000
            return result
        health_delta = float(np.clip(health_delta, -1.0, 1.0))

        # --- 构建标准化 FeedbackPacket ---
        fb_packet: FeedbackPacket = {
            "ack": False,
            "line": src_line,
            "health_delta": health_delta,
            "si_proposal": si_proposal if si_proposal is not None else source_si,
            "status": fb_status if fb_status in ("completed", "pending", "failed") else "completed",
            "latency_ms": 0.0,
        }

        # --- 执行反馈逻辑 ---
        channel_key = f"{src_line}→{dst_line}"
        ch = self.reverse_channels.setdefault(channel_key, {
            "packets": 0, "acked": 0, "failed": 0,
            "latency_sum_ms": 0.0, "last_pulse": None, "history": [],
        })

        # 模拟通道时延 (与 SI 差距成反比)
        si_gap = max(0.0, target_si - source_si)
        simulated_latency = max(1.0, 60.0 / (1.0 + si_gap * 10))

        # 健康度回流计算
        lines = self.hub_state.setdefault("lines", {})
        dst_info = lines.setdefault(dst_line, deepcopy(DEFAULT_LINE_CONFIG.get(dst_line, {})))
        current_health = dst_info.get("health", 0.95)

        if fb_packet["status"] == "completed":
            health_adjustment = health_delta * HEALTH_REFLUX_BOOST
            new_health = min(1.0, current_health + health_adjustment)
            ch["acked"] += 1
            fb_packet["ack"] = True
        elif fb_packet["status"] == "failed":
            health_adjustment = -HEALTH_REFLUX_PENALTY
            new_health = max(0.0, current_health + health_adjustment)
            ch["failed"] += 1
            fb_packet["ack"] = False
        else:  # pending
            health_adjustment = 0.0
            new_health = current_health * HEALTH_REFLUX_DECAY
            fb_packet["ack"] = False

        dst_info["health"] = round(new_health, 4)
        fb_packet["latency_ms"] = round(simulated_latency, 2)

        # 更新源线状态
        src_info = lines.setdefault(src_line, deepcopy(DEFAULT_LINE_CONFIG.get(src_line, {})))
        src_info["last_reverse_sent"] = _iso_timestamp()
        src_info["reverse_sent_count"] = src_info.get("reverse_sent_count", 0) + 1
        if si_proposal is not None:
            src_info["si_proposal"] = round(si_proposal, 2)

        # 更新全局健康度
        all_healths = [ln.get("health", 0.95) for ln in lines.values()]
        self.hub_state["global_health"] = round(float(np.mean(all_healths)), 4)

        # 更新通道统计
        ch["packets"] += 1
        ch["last_pulse"] = _iso_timestamp()
        ch["latency_sum_ms"] += simulated_latency
        ch["history"].append({
            "seq_id": result["seq_id"],
            "timestamp": _iso_timestamp(),
            "latency_ms": simulated_latency,
            "status": fb_packet["status"],
            "health_adjusted": round(health_adjustment, 4),
        })
        if len(ch["history"]) > STATS_WINDOW_SIZE:
            ch["history"] = ch["history"][-STATS_WINDOW_SIZE:]

        # 更新 hub_state 计数
        self.hub_state["reverse_count"] = self.hub_state.get("reverse_count", 0) + 1

        # 构建结果
        result["ack"] = fb_packet["ack"]
        result["status"] = fb_packet["status"]
        result["latency_ms"] = round(simulated_latency, 2)
        result["health_adjusted"] = round(health_adjustment, 4)
        result["new_health"] = round(new_health, 4)
        result["channel"] = channel_key
        result["feedback_packet"] = fb_packet
        result["global_health"] = self.hub_state["global_health"]
        result["si_gap"] = round(si_gap, 2)

        # 自动保存状态
        self.save_state()

        return result

    # -------------------------------------------------------------------------
    # 双向脉冲
    # -------------------------------------------------------------------------

    def bidirectional_pulse(self, line_a: str, line_b: str,
                           payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        双向脉冲: 同时触发正向驱动 + 反向反馈.

        根据 line_a 和 line_b 的 SI 等级自动判定方向：
            - SI 高的一方作为正向源 (指令下发)
            - SI 低的一方作为反向源 (状态上报)

        若 SI 相等，则交换进行一次往返握手.

        Args:
            line_a: 第一条线名称.
            line_b: 第二条线名称.
            payload: 双向载荷字典，格式:
                {
                    "forward": {"type": str, "data": any},
                    "reverse": {"type": str, "data": any},
                    "priority": int (可选),
                }
                或简写为单个 payload 自动复制到两个方向.

        Returns:
            包含正向结果 (forward_result) 和反向结果 (reverse_result) 的字典.
        """
        t_start = time.perf_counter()
        result: Dict[str, Any] = {
            "ack": False,
            "direction": "bidirectional",
            "status": "failed",
            "error": None,
            "latency_ms": 0.0,
            "seq_id": _generate_seq_id(),
            "forward_result": None,
            "reverse_result": None,
        }

        lines = self.hub_state.get("lines", {})

        # 线名校验
        if line_a not in lines:
            result["error"] = f"线 '{line_a}' 未注册."
            result["latency_ms"] = (time.perf_counter() - t_start) * 1000
            return result
        if line_b not in lines:
            result["error"] = f"线 '{line_b}' 未注册."
            result["latency_ms"] = (time.perf_counter() - t_start) * 1000
            return result

        si_a = float(lines[line_a].get("si", 0.0))
        si_b = float(lines[line_b].get("si", 0.0))

        # 自动解析 payload
        forward_payload = payload.get("forward", payload) if isinstance(payload, dict) else payload
        reverse_payload = payload.get("reverse", payload) if isinstance(payload, dict) else payload
        priority = payload.get("priority", 5) if isinstance(payload, dict) else 5

        # 判定方向: 高 SI → 低 SI 为正向; 低 SI → 高 SI 为反向
        if si_a > si_b:
            high_line, low_line = line_a, line_b
            high_si, low_si = si_a, si_b
        elif si_b > si_a:
            high_line, low_line = line_b, line_a
            high_si, low_si = si_b, si_a
        else:
            # SI 相等时，先 a→b 正向，再 b→a 反向
            high_line, low_line = line_a, line_b
            high_si, low_si = si_a, si_b

        # --- 正向驱动: 高 SI → 低 SI ---
        forward_signal = {
            "source_line": high_line,
            "target_line": low_line,
            "payload": forward_payload,
            "priority": priority,
        }
        forward_result = self.forward_drive(high_si, low_si, forward_signal)
        result["forward_result"] = forward_result

        # --- 反向反馈: 低 SI → 高 SI ---
        # 计算 health_delta: 基于低线当前健康度与全局平均的差异
        low_health = float(lines[low_line].get("health", 0.95))
        all_healths = [ln.get("health", 0.95) for ln in lines.values()]
        avg_health = float(np.mean(all_healths))
        health_delta = float(np.clip(low_health - avg_health, -1.0, 1.0))

        reverse_feedback_packet = {
            "source_line": low_line,
            "target_line": high_line,
            "health_delta": health_delta,
            "si_proposal": low_si,  # 默认维持当前 SI
            "status": "completed" if forward_result.get("ack") else "failed",
        }
        reverse_result = self.reverse_feedback(low_si, high_si, reverse_feedback_packet)
        result["reverse_result"] = reverse_result

        # --- 汇总结果 ---
        latency_total = (time.perf_counter() - t_start) * 1000
        result["latency_ms"] = round(latency_total, 2)
        result["channel"] = f"{high_line}↔{low_line}"

        if forward_result.get("ack") and reverse_result.get("ack"):
            result["ack"] = True
            result["status"] = "completed"
        elif forward_result.get("ack") or reverse_result.get("ack"):
            result["ack"] = True
            result["status"] = "partial"
        else:
            result["ack"] = False
            result["status"] = "failed"
            result["error"] = (
                f"Forward: {forward_result.get('error', 'OK')}; "
                f"Reverse: {reverse_result.get('error', 'OK')}"
            )

        # 更新脉冲计数
        self.hub_state["pulse_count"] = self.hub_state.get("pulse_count", 0) + 1

        # 自动保存状态
        self.save_state()

        return result

    # -------------------------------------------------------------------------
    # 互激耦合矩阵
    # -------------------------------------------------------------------------

    def update_coupling(self) -> np.ndarray:
        """
        基于健康度差异更新互激耦合矩阵.

        耦合系数计算规则:
            mutual[i][j] = COUPLING_SCALE * (avg_health_others[j] - health[i])

        其中:
            - health[i]: 第 i 条线的当前健康度.
            - avg_health_others[j]: 除第 j 条线外其余线的平均健康度.
            - COUPLING_SCALE: 全局缩放因子 (默认 0.001).

        矩阵将被裁剪到 [COUPLING_CLIP_MIN, COUPLING_CLIP_MAX] 范围.

        Returns:
            更新后的 11×11 耦合矩阵 (numpy ndarray).
        """
        lines = self.hub_state.get("lines", {})
        healths = np.zeros(NUM_LINES, dtype=np.float64)

        for idx, line_name in enumerate(LINE_NAMES):
            line_info = lines.get(line_name, {})
            healths[idx] = float(line_info.get("health", 0.95))

        # 计算互激耦合系数
        new_matrix = np.zeros((NUM_LINES, NUM_LINES), dtype=np.float64)

        for i in range(NUM_LINES):
            for j in range(NUM_LINES):
                if i == j:
                    new_matrix[i][j] = 0.0
                    continue

                # 除 j 外其余线的平均健康度
                others_mask = np.ones(NUM_LINES, dtype=bool)
                others_mask[j] = False
                avg_health_others = float(np.mean(healths[others_mask]))

                # 互激耦合公式
                coupling = COUPLING_SCALE * (avg_health_others - healths[i])
                new_matrix[i][j] = coupling

        # 裁剪到合理范围
        new_matrix = np.clip(new_matrix, COUPLING_CLIP_MIN, COUPLING_CLIP_MAX)

        self.coupling_matrix = new_matrix
        self.hub_state["coupling_matrix"] = new_matrix.tolist()
        self.hub_state["last_coupling_update"] = _iso_timestamp()

        # 自动保存状态
        self.save_state()

        return self.coupling_matrix

    def get_coupling_summary(self) -> Dict[str, Any]:
        """
        获取耦合矩阵的统计摘要.

        Returns:
            包含矩阵统计信息的字典.
        """
        mat = self.coupling_matrix
        return {
            "timestamp": _iso_timestamp(),
            "shape": mat.shape,
            "max": float(np.max(mat)),
            "min": float(np.min(mat)),
            "mean": float(np.mean(mat)),
            "std": float(np.std(mat)),
            "diagonal_sum": float(np.trace(mat)),
            "strongest_pair": self._get_strongest_coupling_pair(),
        }

    def _get_strongest_coupling_pair(self) -> Optional[Dict[str, Any]]:
        """返回耦合矩阵中绝对值最大的非对角线元素及其对应线对."""
        mat = self.coupling_matrix.copy()
        np.fill_diagonal(mat, 0.0)
        max_idx = np.unravel_index(np.argmax(np.abs(mat)), mat.shape)
        i, j = max_idx
        return {
            "from": LINE_NAMES[i],
            "to": LINE_NAMES[j],
            "value": round(float(mat[i, j]), 6),
        }

    # -------------------------------------------------------------------------
    # 便捷查询方法
    # -------------------------------------------------------------------------

    def get_line_health(self, line_name: str) -> float:
        """
        获取指定线的当前健康度.

        Args:
            line_name: 线名称.

        Returns:
            健康度值 (0.0 ~ 1.0).
        """
        lines = self.hub_state.get("lines", {})
        if line_name not in lines:
            raise ValueError(f"线 '{line_name}' 未注册.")
        return float(lines[line_name].get("health", 0.95))

    def get_line_si(self, line_name: str) -> float:
        """
        获取指定线的当前 SI 等级.

        Args:
            line_name: 线名称.

        Returns:
            SI 等级值.
        """
        lines = self.hub_state.get("lines", {})
        if line_name not in lines:
            raise ValueError(f"线 '{line_name}' 未注册.")
        return float(lines[line_name].get("si", 0.0))

    def set_line_health(self, line_name: str, health: float) -> None:
        """
        手动设置指定线的健康度.

        Args:
            line_name: 线名称.
            health: 新的健康度值 (0.0 ~ 1.0).
        """
        lines = self.hub_state.setdefault("lines", {})
        if line_name not in lines:
            lines[line_name] = deepcopy(DEFAULT_LINE_CONFIG.get(line_name, {}))
        lines[line_name]["health"] = float(np.clip(health, 0.0, 1.0))
        self.save_state()

    def list_lines(self) -> List[str]:
        """返回所有已注册线的名称列表."""
        return list(self.hub_state.get("lines", {}).keys())


# =============================================================================
# 测试块
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v3.1 — Bidirectional Drive Engine 自检测试")
    print("=" * 70)

    # 初始化状态文件路径
    state_path = "/mnt/agents/output/OMNI-HUB/core/hub_state.json"
    if os.path.exists(state_path):
        os.remove(state_path)

    # 实例化引擎
    engine = BidirectionalDrive(state_path)
    print(f"\n[1] 引擎初始化完成 — 状态文件: {state_path}")
    print(f"    注册线数: {len(engine.list_lines())}")
    print(f"    全局健康度: {engine.hub_state.get('global_health', 0.0)}")

    # -----------------------------------------------------------------------
    # 测试 1: ucif2 (SI 5.0) → lgt (SI 4.0) 正向驱动
    # -----------------------------------------------------------------------
    print("\n[2] 测试正向驱动: ucif2 (SI 5.0) → lgt (SI 4.0)")
    forward_signal = {
        "source_line": "ucif2",
        "target_line": "lgt",
        "payload": {"type": "SCHEDULE", "data": {"task_id": "T-001", "priority": 0}},
        "priority": 0,
    }
    fwd_result = engine.forward_drive(5.0, 4.0, forward_signal)
    print(f"    ack={fwd_result['ack']}, status={fwd_result['status']}, "
          f"latency={fwd_result['latency_ms']}ms, si_gap={fwd_result.get('si_gap')}")
    assert fwd_result["ack"] is True, "正向驱动应成功"
    assert fwd_result["status"] == "completed", "正向驱动状态应为 completed"

    # -----------------------------------------------------------------------
    # 测试 2: lgt (SI 4.0) → ucif2 (SI 5.0) 反向反馈
    # -----------------------------------------------------------------------
    print("\n[3] 测试反向反馈: lgt (SI 4.0) → ucif2 (SI 5.0)")
    fb_packet = {
        "source_line": "lgt",
        "target_line": "ucif2",
        "health_delta": 0.05,
        "si_proposal": 4.2,
        "status": "completed",
    }
    rev_result = engine.reverse_feedback(4.0, 5.0, fb_packet)
    print(f"    ack={rev_result['ack']}, status={rev_result['status']}, "
          f"latency={rev_result['latency_ms']}ms, "
          f"health_adjusted={rev_result.get('health_adjusted')}, "
          f"new_health={rev_result.get('new_health')}, "
          f"global_health={rev_result.get('global_health')}")
    assert rev_result["ack"] is True, "反向反馈应成功"
    assert rev_result["status"] == "completed", "反向反馈状态应为 completed"

    # -----------------------------------------------------------------------
    # 测试 3: ucif2 ⇔ lgt 双向脉冲
    # -----------------------------------------------------------------------
    print("\n[4] 测试双向脉冲: ucif2 ⇔ lgt")
    pulse_payload = {
        "forward": {"type": "EXECUTE", "data": {"command": "sync_config", "args": ["--force"]}},
        "reverse": {"type": "HEALTH_REPORT", "data": {"cpu": 0.75, "mem": 0.60}},
        "priority": 1,
    }
    pulse_result = engine.bidirectional_pulse("ucif2", "lgt", pulse_payload)
    print(f"    ack={pulse_result['ack']}, status={pulse_result['status']}, "
          f"latency={pulse_result['latency_ms']}ms, channel={pulse_result.get('channel')}")
    print(f"    Forward: ack={pulse_result['forward_result']['ack']}, "
          f"status={pulse_result['forward_result']['status']}")
    print(f"    Reverse: ack={pulse_result['reverse_result']['ack']}, "
          f"status={pulse_result['reverse_result']['status']}, "
          f"new_health={pulse_result['reverse_result'].get('new_health')}")
    assert pulse_result["ack"] is True, "双向脉冲应成功"
    assert pulse_result["forward_result"]["ack"] is True, "正向脉冲应成功"
    assert pulse_result["reverse_result"]["ack"] is True, "反向脉冲应成功"

    # -----------------------------------------------------------------------
    # 测试 4: 权限校验 — 低 SI 不应能正向驱动高 SI
    # -----------------------------------------------------------------------
    print("\n[5] 测试权限校验: lgt (SI 4.0) → ucif2 (SI 5.0) 正向驱动 (应失败)")
    bad_signal = {
        "source_line": "lgt",
        "target_line": "ucif2",
        "payload": {"type": "HACK", "data": {}},
        "priority": 9,
    }
    bad_fwd = engine.forward_drive(4.0, 5.0, bad_signal)
    print(f"    ack={bad_fwd['ack']}, status={bad_fwd['status']}, error='{bad_fwd.get('error')}'")
    assert bad_fwd["ack"] is False, "低 SI 向高 SI 正向驱动应失败"
    assert "权限不足" in bad_fwd.get("error", ""), "错误信息应包含权限不足"

    # -----------------------------------------------------------------------
    # 测试 5: 反向权限校验 — 高 SI 不应能反向反馈低 SI
    # -----------------------------------------------------------------------
    print("\n[6] 测试权限校验: ucif2 (SI 5.0) → lgt (SI 4.0) 反向反馈 (应失败)")
    bad_fb = {
        "source_line": "ucif2",
        "target_line": "lgt",
        "health_delta": 0.1,
        "status": "completed",
    }
    bad_rev = engine.reverse_feedback(5.0, 4.0, bad_fb)
    print(f"    ack={bad_rev['ack']}, status={bad_rev['status']}, error='{bad_rev.get('error')}'")
    assert bad_rev["ack"] is False, "高 SI 向低 SI 反向反馈应失败"
    assert "权限不足" in bad_rev.get("error", ""), "错误信息应包含权限不足"

    # -----------------------------------------------------------------------
    # 测试 6: 互激耦合矩阵更新
    # -----------------------------------------------------------------------
    print("\n[7] 测试互激耦合矩阵更新")
    coupling = engine.update_coupling()
    summary = engine.get_coupling_summary()
    print(f"    矩阵形状: {summary['shape']}")
    print(f"    最大值: {summary['max']}, 最小值: {summary['min']}")
    print(f"    均值: {summary['mean']:.6f}, 标准差: {summary['std']:.6f}")
    print(f"    最强耦合对: {summary['strongest_pair']}")
    assert coupling.shape == (NUM_LINES, NUM_LINES), "耦合矩阵应为 11×11"
    assert np.allclose(np.diag(coupling), 0.0), "对角线应为 0"

    # -----------------------------------------------------------------------
    # 测试 7: 通道统计
    # -----------------------------------------------------------------------
    print("\n[8] 测试通道统计")
    stats = engine.get_channel_stats("all")
    print(f"    正向: packets={stats['forward']['total_packets']}, "
          f"acked={stats['forward']['total_acked']}, "
          f"ack_rate={stats['forward']['ack_rate']}, "
          f"avg_latency={stats['forward']['avg_latency_ms']}ms")
    print(f"    反向: packets={stats['reverse']['total_packets']}, "
          f"acked={stats['reverse']['total_acked']}, "
          f"ack_rate={stats['reverse']['ack_rate']}, "
          f"avg_latency={stats['reverse']['avg_latency_ms']}ms")
    print(f"    全局: pulses={stats['global']['pulse_count']}, "
          f"forward={stats['global']['forward_count']}, "
          f"reverse={stats['global']['reverse_count']}")
    assert stats["forward"]["total_packets"] > 0, "应有正向数据包"
    assert stats["reverse"]["total_packets"] > 0, "应有反向数据包"

    # -----------------------------------------------------------------------
    # 测试 8: 多条线级联脉冲
    # -----------------------------------------------------------------------
    print("\n[9] 测试多条线级联脉冲")
    cascade_lines = [("ucif2", "qfa"), ("ucif2", "vinf"), ("lvlu", "qlv")]
    for src, dst in cascade_lines:
        payload = {"type": "CASCADE", "data": {"from": src, "to": dst}}
        res = engine.bidirectional_pulse(src, dst, payload)
        print(f"    {src}⇔{dst}: ack={res['ack']}, status={res['status']}, "
              f"latency={res['latency_ms']}ms")
        assert res["ack"] is True, f"{src}⇔{dst} 脉冲应成功"

    # -----------------------------------------------------------------------
    # 测试 9: lvlu (SI 4.5) 观察中状态验证
    # -----------------------------------------------------------------------
    print("\n[10] 验证 lvlu (SI 4.5) 观察中状态")
    lvlu_si = engine.get_line_si("lvlu")
    lvlu_health = engine.get_line_health("lvlu")
    print(f"    lvlu SI={lvlu_si}, health={lvlu_health}")
    assert lvlu_si == 4.5, "lvlu SI 应为 4.5"
    assert lvlu_health > 0.9, "lvlu 健康度应大于 0.9"

    # -----------------------------------------------------------------------
    # 最终保存与清理
    # -----------------------------------------------------------------------
    engine.save_state()
    print("\n" + "=" * 70)
    print("所有自检测试通过! OMNI-HUB v3.1 双向驱动引擎就绪.")
    print(f"状态文件: {state_path}")
    print(f"耦合矩阵摘要: {engine.get_coupling_summary()}")
    print("=" * 70)
