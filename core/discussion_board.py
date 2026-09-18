#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
discussion_board.py — OMNI-HUB v3.2 讨论室系统
4空间无死角可见管理系统

空间总览:
  1. discussion_room — 讨论型空间，线程可长，支持多轮深度讨论
  2. bulletin_board  — 公告型空间，只读+确认，重要信息广播
  3. hall            — 大厅型空间，开放讨论，自由发言
  4. wild_ask        — 野问型空间，无序但需全部应答，不允许遗漏
"""

__version__ = "11.0.0"
from __future__ import annotations

import copy
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class Thread:
    """讨论线程"""
    thread_id: str
    space: str
    author: str
    title: str
    body: str
    tags: List[str] = field(default_factory=list)
    priority: int = 0  # 0-9, 越高越紧急
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    responses: List[dict] = field(default_factory=list)
    confirmed_by: List[str] = field(default_factory=list)  # bulletin_board 用
    status: str = "open"  # open | closed | escalated | answered
    visibility: float = 1.0  # 0.0~1.0
    auto_escalated: bool = False
    required_responders: List[str] = field(default_factory=list)  # wild_ask 用

    def to_dict(self) -> dict:
        return {
            "thread_id": self.thread_id,
            "space": self.space,
            "author": self.author,
            "title": self.title,
            "body": self.body,
            "tags": self.tags,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "responses": self.responses,
            "confirmed_by": self.confirmed_by,
            "status": self.status,
            "visibility": self.visibility,
            "auto_escalated": self.auto_escalated,
            "required_responders": self.required_responders,
            "response_count": len(self.responses),
            "last_response_at": self.responses[-1]["timestamp"] if self.responses else None,
            "age_hours": round((time.time() - self.created_at) / 3600, 2),
        }


class DiscussionBoard:
    """讨论室/公告板/大厅/野问册 — 无死角可见管理系统"""

    SPACES = ["discussion_room", "bulletin_board", "hall", "wild_ask"]

    # 各空间的行为特征配置
    SPACE_CONFIG = {
        "discussion_room": {
            "description": "讨论型空间，线程可长，支持多轮深度讨论",
            "max_threads": 200,
            "allow_multiple_responses": True,
            "require_confirmation": False,
            "auto_close_after_hours": 168,  # 7天后自动关闭
            "response_types": ["answer", "followup", "question", "debate"],
            "visibility_decay": 0.01,  # 每小时衰减
            "escalation_threshold_hours": 48,
        },
        "bulletin_board": {
            "description": "公告型空间，只读+确认，重要信息广播",
            "max_threads": 50,
            "allow_multiple_responses": False,
            "require_confirmation": True,
            "auto_close_after_hours": 720,  # 30天后自动关闭
            "response_types": ["confirm"],
            "visibility_decay": 0.0,
            "escalation_threshold_hours": 24,
        },
        "hall": {
            "description": "大厅型空间，开放讨论，自由发言",
            "max_threads": 500,
            "allow_multiple_responses": True,
            "require_confirmation": False,
            "auto_close_after_hours": 72,  # 3天后自动关闭
            "response_types": ["answer", "followup", "question", "chat", "announcement"],
            "visibility_decay": 0.05,
            "escalation_threshold_hours": None,  # 大厅不升级
        },
        "wild_ask": {
            "description": "野问型空间，无序但需全部应答，不允许遗漏",
            "max_threads": 300,
            "allow_multiple_responses": True,
            "require_confirmation": False,
            "auto_close_after_hours": 48,
            "response_types": ["answer", "clarification"],
            "visibility_decay": 0.0,
            "escalation_threshold_hours": 12,
            "require_all_answered": True,
        },
    }

    def __init__(self, state_path: str = "/tmp/omni_hub_board_state"):
        self.rooms: Dict[str, dict] = {
            s: {"threads": [], "visibility": 1.0, "last_update": None}
            for s in self.SPACES
        }
        self.response_deadline_hours = 24
        self.state_path = Path(state_path)
        self.state_path.mkdir(parents=True, exist_ok=True)
        self._lines = ["alpha", "beta", "gamma", "delta", "epsilon",
                       "zeta", "eta", "theta", "iota", "kappa", "lambda"]
        self._load_state()

    # ------------------------------------------------------------------ #
    #  发帖
    # ------------------------------------------------------------------ #
    def post(self, space: str, content: dict) -> dict:
        """发布公告/讨论

        content: {
            "author": str,
            "title": str,
            "body": str,
            "tags": list,
            "priority": 0-9
        }

        返回: {
            "thread_id": str,
            "space": str,
            "posted": bool,
            "visibility": float,
            "message": str
        }
        """
        if space not in self.SPACES:
            return {
                "thread_id": None,
                "space": space,
                "posted": False,
                "visibility": 0.0,
                "message": f"未知空间: {space}",
            }

        config = self.SPACE_CONFIG[space]
        room = self.rooms[space]

        # 检查空间容量
        if len(room["threads"]) >= config["max_threads"]:
            # 自动归档最旧的线程
            self._archive_oldest(space)

        # 生成线程ID
        thread_id = self._generate_thread_id(space, content)

        # 创建线程
        thread = Thread(
            thread_id=thread_id,
            space=space,
            author=content.get("author", "anonymous"),
            title=content.get("title", "无标题"),
            body=content.get("body", ""),
            tags=content.get("tags", []),
            priority=min(9, max(0, content.get("priority", 0))),
            visibility=1.0,
            required_responders=content.get("required_responders", []),
        )

        # 空间特殊处理
        if space == "bulletin_board":
            # 公告型：所有线必须确认
            thread.required_responders = self._lines.copy()
            thread.status = "open"
        elif space == "wild_ask":
            # 野问型：如未指定回应者，默认为全部
            if not thread.required_responders:
                thread.required_responders = self._lines.copy()

        room["threads"].append(thread)
        room["last_update"] = time.time()
        self._persist_state()

        return {
            "thread_id": thread_id,
            "space": space,
            "posted": True,
            "visibility": thread.visibility,
            "message": f"成功发布到 {space}",
            "thread": thread.to_dict(),
        }

    # ------------------------------------------------------------------ #
    #  回应
    # ------------------------------------------------------------------ #
    def respond(self, space: str, thread_id: str, response: dict) -> dict:
        """回应线程

        response: {
            "author": str,
            "body": str,
            "type": "answer|followup|question|confirm|..."
        }
        """
        if space not in self.SPACES:
            return {
                "responded": False,
                "message": f"未知空间: {space}",
            }

        config = self.SPACE_CONFIG[space]
        room = self.rooms[space]

        # 查找线程
        thread = None
        for t in room["threads"]:
            if t.thread_id == thread_id:
                thread = t
                break

        if thread is None:
            return {
                "responded": False,
                "message": f"线程未找到: {thread_id}",
            }

        resp_type = response.get("type", "answer")
        author = response.get("author", "anonymous")

        # 检查回应类型是否允许
        if resp_type not in config["response_types"]:
            return {
                "responded": False,
                "message": f"空间 '{space}' 不允许回应类型 '{resp_type}'",
                "allowed_types": config["response_types"],
            }

        # 检查是否允许多次回应
        if not config["allow_multiple_responses"]:
            existing = [r for r in thread.responses if r.get("author") == author]
            if existing:
                return {
                    "responded": False,
                    "message": f"空间 '{space}' 不允许同一人多次回应",
                }

        # 构建回应记录
        resp_record = {
            "response_id": str(uuid.uuid4())[:8],
            "author": author,
            "body": response.get("body", ""),
            "type": resp_type,
            "timestamp": time.time(),
        }

        thread.responses.append(resp_record)
        thread.updated_at = time.time()

        # 空间特殊处理
        if space == "bulletin_board" and resp_type == "confirm":
            if author not in thread.confirmed_by:
                thread.confirmed_by.append(author)
            # 检查是否全部确认
            if set(thread.confirmed_by) >= set(thread.required_responders):
                thread.status = "closed"

        elif space == "wild_ask" and resp_type == "answer":
            # 检查是否所有required_responders都已回答
            answered_by = set(r["author"] for r in thread.responses if r["type"] == "answer")
            if answered_by >= set(thread.required_responders):
                thread.status = "answered"

        elif space == "discussion_room":
            # 讨论型：有新回应即刷新活跃度
            thread.visibility = min(1.0, thread.visibility + 0.1)

        room["last_update"] = time.time()
        self._persist_state()

        return {
            "responded": True,
            "response_id": resp_record["response_id"],
            "thread_id": thread_id,
            "space": space,
            "thread_status": thread.status,
            "response_count": len(thread.responses),
            "message": f"成功回应线程 {thread_id}",
        }

    # ------------------------------------------------------------------ #
    #  扫描未应答
    # ------------------------------------------------------------------ #
    def scan_unanswered(self, space: Optional[str] = None) -> List[dict]:
        """扫描未应答条目

        返回超过 response_deadline_hours 未响应的线程
        """
        now = time.time()
        deadline_seconds = self.response_deadline_hours * 3600
        results = []

        spaces_to_check = [space] if space else self.SPACES

        for sp in spaces_to_check:
            if sp not in self.SPACES:
                continue
            config = self.SPACE_CONFIG[sp]
            room = self.rooms[sp]

            for thread in room["threads"]:
                if thread.status in ("closed", "answered"):
                    continue

                # 计算最后活跃时间
                last_active = thread.updated_at
                elapsed = now - last_active

                if elapsed > deadline_seconds:
                    # 计算逾期时长
                    overdue_hours = round(elapsed / 3600, 2)

                    # 确定还需要谁回应
                    if sp == "bulletin_board":
                        pending = list(set(thread.required_responders) - set(thread.confirmed_by))
                    elif sp == "wild_ask":
                        answered = set(r["author"] for r in thread.responses if r["type"] == "answer")
                        pending = list(set(thread.required_responders) - answered)
                    else:
                        pending = []

                    results.append({
                        "thread_id": thread.thread_id,
                        "space": sp,
                        "title": thread.title,
                        "author": thread.author,
                        "priority": thread.priority,
                        "created_at": thread.created_at,
                        "last_active": last_active,
                        "overdue_hours": overdue_hours,
                        "status": thread.status,
                        "pending_responders": pending,
                        "response_count": len(thread.responses),
                    })

        # 按优先级和逾期时长排序
        results.sort(key=lambda x: (-x["priority"], -x["overdue_hours"]))
        return results

    # ------------------------------------------------------------------ #
    #  覆盖率检查
    # ------------------------------------------------------------------ #
    def ensure_coverage(self) -> dict:
        """确保所有空间全覆盖，无盲点

        检查4个空间的可见性、更新频率、响应率

        返回: {
            "coverage_rate": float,
            "blind_spots": list,
            "actions": list
        }
        """
        now = time.time()
        blind_spots = []
        actions = []
        total_score = 0.0
        max_score = len(self.SPACES) * 3  # 每个空间3分：可见性/更新/响应

        for sp in self.SPACES:
            config = self.SPACE_CONFIG[sp]
            room = self.rooms[sp]
            threads = room["threads"]
            space_score = 0

            # 1. 可见性检查
            avg_visibility = sum(t.visibility for t in threads) / len(threads) if threads else 1.0
            if avg_visibility < 0.5:
                blind_spots.append({
                    "space": sp,
                    "type": "low_visibility",
                    "value": round(avg_visibility, 2),
                    "threshold": 0.5,
                })
                actions.append(f"提升 {sp} 的可见性: 当前 {avg_visibility:.2f}")
            else:
                space_score += 1

            # 2. 更新频率检查
            if room["last_update"]:
                hours_since_update = (now - room["last_update"]) / 3600
                if hours_since_update > 24:
                    blind_spots.append({
                        "space": sp,
                        "type": "stale",
                        "hours_since_update": round(hours_since_update, 2),
                    })
                    actions.append(f"{sp} 超过24小时未更新，建议检查数据源")
                else:
                    space_score += 1
            else:
                blind_spots.append({
                    "space": sp,
                    "type": "never_updated",
                })
                actions.append(f"{sp} 从未被更新，建议初始化数据")

            # 3. 响应率检查
            if threads:
                if sp == "bulletin_board":
                    # 公告型：检查确认率
                    unconfirmed = [t for t in threads if t.status != "closed"]
                    confirm_rate = 1.0 - (len(unconfirmed) / len(threads))
                elif sp == "wild_ask":
                    # 野问型：检查回答率
                    unanswered = [t for t in threads if t.status != "answered"]
                    confirm_rate = 1.0 - (len(unanswered) / len(threads))
                else:
                    # 讨论型/大厅：检查有回应的比例
                    responded = [t for t in threads if t.responses]
                    confirm_rate = len(responded) / len(threads)

                if confirm_rate < 0.5:
                    blind_spots.append({
                        "space": sp,
                        "type": "low_response_rate",
                        "rate": round(confirm_rate, 2),
                    })
                    actions.append(f"{sp} 响应率过低 ({confirm_rate:.2%})，建议推送提醒")
                else:
                    space_score += 1
            else:
                # 无线程，不算响应问题
                space_score += 1

            total_score += space_score

        coverage_rate = round(total_score / max_score, 4) if max_score else 1.0

        return {
            "coverage_rate": coverage_rate,
            "blind_spots": blind_spots,
            "actions": actions,
            "spaces_checked": len(self.SPACES),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        }

    # ------------------------------------------------------------------ #
    #  自动跟进
    # ------------------------------------------------------------------ #
    def auto_follow_up(self) -> dict:
        """自动跟进超时未响应项

        对超时的线程自动发送提醒/升级
        """
        now = time.time()
        follow_ups = []

        for sp in self.SPACES:
            config = self.SPACE_CONFIG[sp]
            room = self.rooms[sp]
            threshold = config.get("escalation_threshold_hours")

            if threshold is None:
                continue

            for thread in room["threads"]:
                if thread.status in ("closed", "answered"):
                    continue

                elapsed_hours = (now - thread.updated_at) / 3600

                if elapsed_hours > threshold and not thread.auto_escalated:
                    # 自动升级
                    thread.status = "escalated"
                    thread.auto_escalated = True
                    thread.priority = min(9, thread.priority + 2)

                    follow_ups.append({
                        "thread_id": thread.thread_id,
                        "space": sp,
                        "action": "escalated",
                        "previous_status": "open",
                        "new_status": "escalated",
                        "elapsed_hours": round(elapsed_hours, 2),
                        "new_priority": thread.priority,
                    })

                elif elapsed_hours > self.response_deadline_hours:
                    # 发送提醒
                    follow_ups.append({
                        "thread_id": thread.thread_id,
                        "space": sp,
                        "action": "reminder",
                        "elapsed_hours": round(elapsed_hours, 2),
                        "message": f"线程 '{thread.title}' 已超时 {elapsed_hours:.1f} 小时未响应",
                    })

        self._persist_state()

        return {
            "follow_up_count": len(follow_ups),
            "actions": follow_ups,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        }

    # ------------------------------------------------------------------ #
    #  空间统计
    # ------------------------------------------------------------------ #
    def get_space_stats(self, space: str) -> dict:
        """获取指定空间的统计"""
        if space not in self.SPACES:
            return {
                "space": space,
                "error": f"未知空间: {space}",
            }

        config = self.SPACE_CONFIG[space]
        room = self.rooms[space]
        threads = room["threads"]
        now = time.time()

        if not threads:
            return {
                "space": space,
                "thread_count": 0,
                "response_count": 0,
                "avg_visibility": 1.0,
                "status_breakdown": {},
                "last_update": room["last_update"],
            }

        status_breakdown = {}
        for t in threads:
            status_breakdown[t.status] = status_breakdown.get(t.status, 0) + 1

        total_responses = sum(len(t.responses) for t in threads)
        avg_visibility = sum(t.visibility for t in threads) / len(threads)
        avg_age_hours = sum((now - t.created_at) / 3600 for t in threads) / len(threads)

        # 空间特有指标
        extra = {}
        if space == "bulletin_board":
            total_confirmations = sum(len(t.confirmed_by) for t in threads)
            required_confirmations = sum(len(t.required_responders) for t in threads)
            extra["confirmation_rate"] = round(total_confirmations / required_confirmations, 4) if required_confirmations else 1.0
        elif space == "wild_ask":
            answered = sum(1 for t in threads if t.status == "answered")
            extra["answer_rate"] = round(answered / len(threads), 4)
        elif space == "discussion_room":
            avg_thread_length = sum(len(t.responses) for t in threads) / len(threads)
            extra["avg_thread_length"] = round(avg_thread_length, 2)

        return {
            "space": space,
            "description": config["description"],
            "thread_count": len(threads),
            "response_count": total_responses,
            "avg_visibility": round(avg_visibility, 4),
            "avg_age_hours": round(avg_age_hours, 2),
            "status_breakdown": status_breakdown,
            "last_update": room["last_update"],
            "hours_since_update": round((now - room["last_update"]) / 3600, 2) if room["last_update"] else None,
            **extra,
        }

    # ------------------------------------------------------------------ #
    #  跨空间搜索
    # ------------------------------------------------------------------ #
    def cross_reference(self, query: str) -> List[dict]:
        """跨空间交叉引用搜索"""
        query_lower = query.lower()
        results = []

        for sp in self.SPACES:
            room = self.rooms[sp]
            for thread in room["threads"]:
                score = 0
                match_fields = []

                if query_lower in thread.title.lower():
                    score += 10
                    match_fields.append("title")
                if query_lower in thread.body.lower():
                    score += 5
                    match_fields.append("body")
                if any(query_lower in tag.lower() for tag in thread.tags):
                    score += 8
                    match_fields.append("tags")
                for resp in thread.responses:
                    if query_lower in resp.get("body", "").lower():
                        score += 3
                        match_fields.append("response")
                        break

                if score > 0:
                    results.append({
                        "thread_id": thread.thread_id,
                        "space": sp,
                        "title": thread.title,
                        "author": thread.author,
                        "score": score,
                        "match_fields": list(set(match_fields)),
                        "priority": thread.priority,
                        "status": thread.status,
                    })

        # 按相关度排序
        results.sort(key=lambda x: (-x["score"], -x["priority"]))
        return results

    # ------------------------------------------------------------------ #
    #  可见性检查
    # ------------------------------------------------------------------ #
    def visibility_check(self) -> dict:
        """可见性检查 — 确保所有内容对所有线可见"""
        now = time.time()
        issues = []
        visibility_scores = {}

        for sp in self.SPACES:
            config = self.SPACE_CONFIG[sp]
            room = self.rooms[sp]
            threads = room["threads"]

            if not threads:
                visibility_scores[sp] = 1.0
                continue

            low_vis_threads = []
            for thread in threads:
                # 应用可见性衰减
                if config.get("visibility_decay", 0) > 0:
                    hours_old = (now - thread.updated_at) / 3600
                    decay = hours_old * config["visibility_decay"]
                    thread.visibility = max(0.1, thread.visibility - decay)

                if thread.visibility < 0.3:
                    low_vis_threads.append({
                        "thread_id": thread.thread_id,
                        "title": thread.title,
                        "visibility": round(thread.visibility, 4),
                    })

            avg_vis = sum(t.visibility for t in threads) / len(threads)
            visibility_scores[sp] = round(avg_vis, 4)

            if low_vis_threads:
                issues.append({
                    "space": sp,
                    "type": "low_visibility_threads",
                    "count": len(low_vis_threads),
                    "threads": low_vis_threads,
                })

            if avg_vis < 0.5:
                issues.append({
                    "space": sp,
                    "type": "low_average_visibility",
                    "average": round(avg_vis, 4),
                })

        overall_visibility = sum(visibility_scores.values()) / len(visibility_scores) if visibility_scores else 1.0

        return {
            "overall_visibility": round(overall_visibility, 4),
            "space_visibility": visibility_scores,
            "issues": issues,
            "all_visible": len(issues) == 0,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        }

    # ------------------------------------------------------------------ #
    #  内部辅助方法
    # ------------------------------------------------------------------ #
    def _generate_thread_id(self, space: str, content: dict) -> str:
        """生成线程唯一ID"""
        base = f"{space}:{content.get('author')}:{content.get('title')}:{time.time()}"
        return f"{space[:3]}_{hashlib.sha256(base.encode()).hexdigest()[:12]}"

    def _archive_oldest(self, space: str):
        """归档最旧的线程"""
        room = self.rooms[space]
        if not room["threads"]:
            return
        # 按更新时间排序，移除最旧的一个
        room["threads"].sort(key=lambda t: t.updated_at)
        archived = room["threads"].pop(0)
        archived.status = "archived"
        # 持久化归档（简化实现）
        archive_path = self.state_path / "archive"
        archive_path.mkdir(exist_ok=True)
        with open(archive_path / f"{archived.thread_id}.json", "w", encoding="utf-8") as f:
                json.dump(archived.to_dict(), f, ensure_ascii=False, indent=2, default=str)
        pass

    def _persist_state(self):
        """持久化状态"""
        state = {}
        for sp in self.SPACES:
                room = self.rooms[sp]
                state[sp] = {
                    "threads": [t.to_dict() for t in room["threads"]],
                    "visibility": room["visibility"],
                    "last_update": room["last_update"],
                }
    with open(self.state_path / "board_state.json", "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2, default=str)
    pass

    def _load_state(self):
        """加载状态"""
        state_file = self.state_path / "board_state.json"
        if not state_file.exists():
            return
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            for sp in self.SPACES:
                if sp in state:
                    room_data = state[sp]
                    self.rooms[sp]["visibility"] = room_data.get("visibility", 1.0)
                    self.rooms[sp]["last_update"] = room_data.get("last_update")
                    for t_data in room_data.get("threads", []):
                        thread = Thread(
                            thread_id=t_data["thread_id"],
                            space=sp,
                            author=t_data["author"],
                            title=t_data["title"],
                            body=t_data["body"],
                            tags=t_data.get("tags", []),
                            priority=t_data.get("priority", 0),
                            created_at=t_data.get("created_at", time.time()),
                            updated_at=t_data.get("updated_at", time.time()),
                            responses=t_data.get("responses", []),
                            confirmed_by=t_data.get("confirmed_by", []),
                            status=t_data.get("status", "open"),
                            visibility=t_data.get("visibility", 1.0),
                            auto_escalated=t_data.get("auto_escalated", False),
                            required_responders=t_data.get("required_responders", []),
                        )
                        self.rooms[sp]["threads"].append(thread)
            pass

    # ------------------------------------------------------------------ #
    #  便捷方法
    # ------------------------------------------------------------------ #
    def get_thread(self, space: str, thread_id: str) -> Optional[Thread]:
        """获取指定线程"""
        if space not in self.SPACES:
            return None
        for t in self.rooms[space]["threads"]:
            if t.thread_id == thread_id:
                return t
        return None

    def list_threads(self, space: str, status: Optional[str] = None) -> List[dict]:
        """列出空间中的线程"""
        if space not in self.SPACES:
            return []
        threads = self.rooms[space]["threads"]
        if status:
            threads = [t for t in threads if t.status == status]
        return [t.to_dict() for t in threads]

    def close_thread(self, space: str, thread_id: str, closer: str = "system") -> dict:
        """关闭线程"""
        thread = self.get_thread(space, thread_id)
        if not thread:
            return {"closed": False, "message": "线程未找到"}
        thread.status = "closed"
        thread.updated_at = time.time()
        self._persist_state()
        return {"closed": True, "thread_id": thread_id, "closer": closer}


# =====================================================================
#  测试块
# =====================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v3.2 讨论室系统 — 测试")
    print("=" * 70)

    # 初始化
    board = DiscussionBoard(state_path="/tmp/omni_hub_board_test")

    # ---- 测试1: 发帖到4个不同空间 ----
    print("\n【测试1】发帖到4个空间")
    print("-" * 40)

    # discussion_room: 讨论型
    r1 = board.post("discussion_room", {
        "author": "user_alpha",
        "title": "关于board_diff算法的优化讨论",
        "body": "建议引入增量hash来降低差异计算开销...",
        "tags": ["algo", "optimization", "board"],
        "priority": 5,
    })
    print(f"  ✓ discussion_room | ID: {r1['thread_id'][:20]}... | 可见度: {r1['visibility']}")

    # bulletin_board: 公告型
    r2 = board.post("bulletin_board", {
        "author": "admin",
        "title": "【重要】OMNI-HUB v3.2 发布通知",
        "body": "新版本已上线，所有线请在24小时内确认阅读。",
        "tags": ["release", "important"],
        "priority": 9,
    })
    print(f"  ✓ bulletin_board  | ID: {r2['thread_id'][:20]}... | 确认要求: 全部11线")

    # hall: 大厅型
    r3 = board.post("hall", {
        "author": "user_gamma",
        "title": "今天大家状态如何？",
        "body": "大厅自由讨论，欢迎分享进展。",
        "tags": ["chat", "daily"],
        "priority": 1,
    })
    print(f"  ✓ hall            | ID: {r3['thread_id'][:20]}... | 开放讨论")

    # wild_ask: 野问型
    r4 = board.post("wild_ask", {
        "author": "user_delta",
        "title": "W12t进程偶发崩溃排查",
        "body": "观察到w12t_worker_2在过去一小时内崩溃3次，需要各线协助排查。",
        "tags": ["bug", "w12t", "urgent"],
        "priority": 8,
        "required_responders": ["alpha", "beta", "gamma", "delta"],
    })
    print(f"  ✓ wild_ask        | ID: {r4['thread_id'][:20]}... | 需全部应答")

    thread_ids = {
        "discussion_room": r1["thread_id"],
        "bulletin_board": r2["thread_id"],
        "hall": r3["thread_id"],
        "wild_ask": r4["thread_id"],
    }

    # ---- 测试2: 回应 ----
    print("\n【测试2】回应线程")
    print("-" * 40)

    # discussion_room: 多轮讨论
    resp1 = board.respond("discussion_room", thread_ids["discussion_room"], {
        "author": "user_beta",
        "body": "同意，增量hash可以将复杂度从O(n)降到O(delta)。",
        "type": "followup",
    })
    print(f"  ✓ discussion_room 回应 | type=followup | 线程状态: {resp1['thread_status']}")

    resp2 = board.respond("discussion_room", thread_ids["discussion_room"], {
        "author": "user_alpha",
        "body": "我来负责实现这个优化。",
        "type": "answer",
    })
    print(f"  ✓ discussion_room 回应 | type=answer   | 总回应数: {resp2['response_count']}")

    # bulletin_board: 确认（模拟多线确认）
    for line in ["alpha", "beta", "gamma", "delta", "epsilon"]:
        board.respond("bulletin_board", thread_ids["bulletin_board"], {
            "author": line,
            "body": "已确认阅读",
            "type": "confirm",
        })
    bb_thread = board.get_thread("bulletin_board", thread_ids["bulletin_board"])
    print(f"  ✓ bulletin_board 确认  | 已确认: {len(bb_thread.confirmed_by)}/11 | 状态: {bb_thread.status}")

    # hall: 自由聊天
    board.respond("hall", thread_ids["hall"], {
        "author": "user_zeta",
        "body": "今天eta线的水位监控出了点问题，已修复。",
        "type": "chat",
    })
    print(f"  ✓ hall 回应           | type=chat     | 自由发言")

    # wild_ask: 必须全部回答
    for line in ["alpha", "beta", "gamma"]:
        board.respond("wild_ask", thread_ids["wild_ask"], {
            "author": line,
            "body": f"{line}线排查中，未发现异常日志。",
            "type": "answer",
        })
    wa_thread = board.get_thread("wild_ask", thread_ids["wild_ask"])
    print(f"  ✓ wild_ask 回答       | 已回答: 3/4 | 状态: {wa_thread.status}")

    # 最后一人回答，触发全部应答
    board.respond("wild_ask", thread_ids["wild_ask"], {
        "author": "delta",
        "body": "delta线排查完成，发现是内存泄漏，已提交修复。",
        "type": "answer",
    })
    wa_thread = board.get_thread("wild_ask", thread_ids["wild_ask"])
    print(f"  ✓ wild_ask 最终回答   | 全部应答完成 | 状态: {wa_thread.status}")

    # ---- 测试3: 扫描未应答 ----
    print("\n【测试3】扫描未应答 (scan_unanswered)")
    print("-" * 40)

    # 创建一个超时的线程用于测试
    old_thread = board.post("discussion_room", {
        "author": "user_old",
        "title": "遗留问题：nonce清理策略",
        "body": "需要讨论nonce过期后的清理策略。",
        "priority": 3,
    })
    # 手动修改时间为25小时前
    t = board.get_thread("discussion_room", old_thread["thread_id"])
    t.created_at = time.time() - 25 * 3600
    t.updated_at = time.time() - 25 * 3600

    unanswered = board.scan_unanswered()
    print(f"  发现未应答条目: {len(unanswered)}")
    for item in unanswered:
        print(f"    ⚠ [{item['space']}] '{item['title']}' | 逾期: {item['overdue_hours']}h | 优先级: {item['priority']}")

    # ---- 测试4: 覆盖率检查 ----
    print("\n【测试4】覆盖率检查 (ensure_coverage)")
    print("-" * 40)
    coverage = board.ensure_coverage()
    print(f"  覆盖率: {coverage['coverage_rate']:.2%}")
    print(f"  盲点数: {len(coverage['blind_spots'])}")
    if coverage['blind_spots']:
        for bs in coverage['blind_spots']:
            print(f"    ⚠ {bs['space']} | 类型: {bs['type']}")
    if coverage['actions']:
        for act in coverage['actions']:
            print(f"    → {act}")

    # ---- 测试5: 空间统计 ----
    print("\n【测试5】空间统计 (get_space_stats)")
    print("-" * 40)
    for sp in board.SPACES:
        stats = board.get_space_stats(sp)
        print(f"  {sp:18s} | 线程: {stats['thread_count']:3d} | 回应: {stats['response_count']:3d} | 可见度: {stats['avg_visibility']:.2f}")
        if "confirmation_rate" in stats:
            print(f"                     | 确认率: {stats['confirmation_rate']:.2%}")
        if "answer_rate" in stats:
            print(f"                     | 回答率: {stats['answer_rate']:.2%}")
        if "avg_thread_length" in stats:
            print(f"                     | 平均长度: {stats['avg_thread_length']:.1f}")

    # ---- 测试6: 跨空间搜索 ----
    print("\n【测试6】跨空间搜索 (cross_reference)")
    print("-" * 40)
    search_results = board.cross_reference("w12t")
    print(f"  查询 'w12t' | 命中: {len(search_results)}")
    for r in search_results:
        print(f"    → [{r['space']}] '{r['title']}' | 匹配分: {r['score']} | 字段: {r['match_fields']}")

    search_results2 = board.cross_reference("优化")
    print(f"  查询 '优化' | 命中: {len(search_results2)}")
    for r in search_results2:
        print(f"    → [{r['space']}] '{r['title']}' | 匹配分: {r['score']}")

    # ---- 测试7: 可见性检查 ----
    print("\n【测试7】可见性检查 (visibility_check)")
    print("-" * 40)
    vis = board.visibility_check()
    print(f"  整体可见度: {vis['overall_visibility']:.2%}")
    print(f"  全部可见: {'是' if vis['all_visible'] else '否'}")
    for sp, score in vis['space_visibility'].items():
        status = "✓" if score >= 0.5 else "⚠"
        print(f"    {status} {sp:18s} | 可见度: {score:.2%}")
    if vis['issues']:
        for issue in vis['issues']:
            print(f"    ⚠ {issue['space']} | {issue['type']} | 数量: {issue.get('count', 'N/A')}")

    # ---- 测试8: 自动跟进 ----
    print("\n【测试8】自动跟进 (auto_follow_up)")
    print("-" * 40)
    # 创建一个足够老的线程触发升级
    very_old = board.post("wild_ask", {
        "author": "user_ancient",
        "title": "历史遗留：水位校准",
        "body": "需要重新校准双系统水位。",
        "priority": 2,
    })
    vt = board.get_thread("wild_ask", very_old["thread_id"])
    vt.created_at = time.time() - 48 * 3600
    vt.updated_at = time.time() - 48 * 3600

    follow_up = board.auto_follow_up()
    print(f"  跟进动作数: {follow_up['follow_up_count']}")
    for action in follow_up['actions']:
        print(f"    → [{action['action']}] {action.get('message', '')}")
        if 'new_priority' in action:
            print(f"       升级后优先级: {action['new_priority']} | 新状态: {action['new_status']}")

    # ---- 测试9: 持久化验证 ----
    print("\n【测试9】状态持久化验证")
    print("-" * 40)
    state_file = board.state_path / "board_state.json"
    print(f"  状态文件存在: {'是' if state_file.exists() else '否'}")
    if state_file.exists():
        import os
        size = os.path.getsize(state_file)
        print(f"  状态文件大小: {size} bytes")

    # 重新加载验证
    board2 = DiscussionBoard(state_path="/tmp/omni_hub_board_test")
    total_threads = sum(len(board2.rooms[sp]["threads"]) for sp in board2.SPACES)
    print(f"  重新加载后线程总数: {total_threads}")

    print("\n" + "=" * 70)
    print("讨论室系统测试完成")
    print("=" * 70)
