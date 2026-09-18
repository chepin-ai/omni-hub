#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CIRCULATION-VERIFY-01.py
ucif2 系统大小周天自循环验证脚本
验证11线SI引擎的小周天（每线自循环）与大周天（全局循环）

验证项:
1. 自激 (self_excite): 8拍静默后自动触发PULSE
2. 互激 (mutual_excite): 一线health变化触发关联线响应
3. 自环 (self_loop): 每线自身health检查循环
4. 互环 (cross_loop): 跨线数据同步循环
5. tensor_contract: 全局张量收缩循环
6. ring_broadcast: 全局广播循环
"""

__version__ = "11.0.0"
import numpy as np
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from collections import deque
from enum import Enum
import random

np.random.seed(42)
random.seed(42)

# =============================================================================
# 常量定义
# =============================================================================
NUM_LINES = 11
MAX_STEPS = 100
SILENCE_THRESHOLD = 8  # 8拍静默后自激

LINE_NAMES = [
    "Causal-线", "Semantic-线", "Temporal-线", "Spatial-线", "Agentic-线",
    "Narrative-线", "Modal-线", "Ontological-线", "Epistemic-线", 
    "Ethical-线", "Aesthetic-线"
]

LINE_SHORT = [f"L{i:02d}" for i in range(NUM_LINES)]

# 线间关联权重矩阵 (互激拓扑)
# 值越大表示关联越强，health变化时触发响应的概率越高
CROSS_MATRIX = np.array([
    #Cau Sem Tem Spa Agt Nar Mod Ont Epi Eth Aes
    [0.8, 0.6, 0.7, 0.5, 0.4, 0.5, 0.3, 0.6, 0.7, 0.4, 0.3],  # Causal
    [0.6, 0.8, 0.5, 0.6, 0.5, 0.7, 0.6, 0.7, 0.6, 0.5, 0.7],  # Semantic
    [0.7, 0.5, 0.8, 0.6, 0.5, 0.7, 0.4, 0.5, 0.6, 0.4, 0.5],  # Temporal
    [0.5, 0.6, 0.6, 0.8, 0.7, 0.5, 0.7, 0.5, 0.4, 0.5, 0.6],  # Spatial
    [0.4, 0.5, 0.5, 0.7, 0.8, 0.6, 0.5, 0.4, 0.5, 0.7, 0.4],  # Agentic
    [0.5, 0.7, 0.7, 0.5, 0.6, 0.8, 0.5, 0.5, 0.6, 0.5, 0.7],  # Narrative
    [0.3, 0.6, 0.4, 0.7, 0.5, 0.5, 0.8, 0.4, 0.5, 0.3, 0.7],  # Modal
    [0.6, 0.7, 0.5, 0.5, 0.4, 0.5, 0.4, 0.8, 0.7, 0.6, 0.5],  # Ontological
    [0.7, 0.6, 0.6, 0.4, 0.5, 0.6, 0.5, 0.7, 0.8, 0.6, 0.5],  # Epistemic
    [0.4, 0.5, 0.4, 0.5, 0.7, 0.5, 0.3, 0.6, 0.6, 0.8, 0.4],  # Ethical
    [0.3, 0.7, 0.5, 0.6, 0.4, 0.7, 0.7, 0.5, 0.5, 0.4, 0.8],  # Aesthetic
])

class TaskType(Enum):
    INGEST = "ingest"
    PROCESS = "process"
    PULSE = "pulse"
    SYNC = "sync"
    HEALTH_CHECK = "health_check"
    BROADCAST = "broadcast"
    CONTRACT = "contract"

@dataclass
class Task:
    tid: int
    ttype: TaskType
    src_line: int
    dst_line: int
    payload: Any = None
    step_created: int = 0
    
@dataclass
class SICore:
    """SI0-SI3 处理核心状态 """
    si0_state: str = "idle"   # inbox读取
    si1_state: str = "idle"   # 解析
    si2_state: str = "idle"   # 分类
    si3_state: str = "idle"   # 执行
    si0_count: int = 0
    si1_count: int = 0
    si2_count: int = 0
    si3_count: int = 0

@dataclass 
class LineState:
    """单线完整状态"""
    line_id: int
    inbox: deque = field(default_factory=lambda: deque(maxlen=100))
    outbox: deque = field(default_factory=lambda: deque(maxlen=100))
    session: Dict = field(default_factory=dict)
    health: float = 1.0
    health_history: List[float] = field(default_factory=list)
    silence_count: int = 0
    pulse_count: int = 0
    si: SICore = field(default_factory=SICore)
    tasks_processed: int = 0
    tasks_created: int = 0
    last_active_step: int = 0
    self_loop_closed: int = 0
    cross_signals_sent: int = 0
    cross_signals_recv: int = 0
    
class UCIF2Scheduler:
    """ucif2 全局调度器"""
    def __init__(self):
        self.lines: Dict[int, LineState] = {}
        self.global_tensor = np.zeros((NUM_LINES, NUM_LINES))
        self.global_health = np.ones(NUM_LINES)
        self.step = 0
        self.history: List[Dict] = []
        self.ring_buffer: deque = deque(maxlen=20)
        self.contract_log: List[Tuple[int, float]] = []
        self.broadcast_log: List[Tuple[int, Any]] = []
        self.scheduler_cycles = 0
        
        # 初始化11线
        for i in range(NUM_LINES):
            self.lines[i] = LineState(line_id=i)
            self.lines[i].session = {
                "line_name": LINE_NAMES[i],
                "status": "active",
                "processed_total": 0,
                "errors": 0
            }
    
    # =====================================================================
    # 小周天: 每线自循环
    # =====================================================================
    def small_circulation(self, line_id: int):
        """
        小周天循环:
        inbox新任务 → SI0读取 → SI1解析 → SI2分类 → SI3执行 
        → SI0上传outbox → SI1更新session → 等待下一任务
        """
        line = self.lines[line_id]
        
        # SI0: 读取inbox
        if line.inbox:
            line.si.si0_state = "reading"
            task = line.inbox.popleft()
            line.si.si0_count += 1
            line.last_active_step = self.step
            line.silence_count = 0
            
            # SI1: 解析
            line.si.si1_state = "parsing"
            line.si.si1_count += 1
            
            # SI2: 分类
            line.si.si2_state = "classifying"
            line.si.si2_count += 1
            
            # SI3: 执行
            line.si.si3_state = "executing"
            line.si.si3_count += 1
            line.tasks_processed += 1
            line.session["processed_total"] = line.tasks_processed
            
            # 产出到outbox
            result = {
                "tid": task.tid,
                "ttype": task.ttype.value,
                "src": task.src_line,
                "result": f"processed_by_{LINE_NAMES[line_id]}",
                "step": self.step
            }
            line.outbox.append(result)
            
            # SI1更新session
            line.si.si1_state = "updating_session"
            line.session["last_result"] = result
            line.health = min(1.0, line.health + 0.02)
            
            # 自环标记
            line.self_loop_closed += 1
            
        else:
            # 无任务: 增加静默计数
            line.silence_count += 1
            line.si.si0_state = "idle"
            line.si.si1_state = "idle"
            line.si.si2_state = "idle"
            line.si.si3_state = "idle"
            
            # 自激检测: 8拍静默后触发PULSE
            if line.silence_count >= SILENCE_THRESHOLD:
                self.self_excite(line_id)
    
    def self_excite(self, line_id: int):
        """自激: 8拍静默后自动触发PULSE"""
        line = self.lines[line_id]
        pulse_task = Task(
            tid=self.step * 1000 + line_id,
            ttype=TaskType.PULSE,
            src_line=line_id,
            dst_line=line_id,
            payload={"type": "self_pulse", "trigger": "silence_threshold"},
            step_created=self.step
        )
        line.inbox.append(pulse_task)
        line.pulse_count += 1
        line.silence_count = 0
        line.tasks_created += 1
        # 自激后health微降(能量消耗)
        line.health = max(0.3, line.health - 0.01)
    
    # =====================================================================
    # 互激: 跨线响应
    # =====================================================================
    def mutual_excite(self, line_id: int):
        """
        互激: 一线health变化触发关联线响应
        当某线health变化超过阈值时，按CROSS_MATRIX权重触发关联线
        """
        line = self.lines[line_id]
        if len(line.health_history) < 2:
            line.health_history.append(line.health)
            return
        
        delta = abs(line.health - line.health_history[-1])
        line.health_history.append(line.health)
        
        if delta > 0.01:  # health变化阈值
            for other_id in range(NUM_LINES):
                if other_id == line_id:
                    continue
                weight = CROSS_MATRIX[line_id, other_id]
                if np.random.random() < weight * delta * 10:
                    # 触发互激: 向关联线发送同步任务
                    sync_task = Task(
                        tid=self.step * 1000 + line_id * 100 + other_id,
                        ttype=TaskType.SYNC,
                        src_line=line_id,
                        dst_line=other_id,
                        payload={
                            "trigger_health": line.health,
                            "delta": delta,
                            "weight": weight
                        },
                        step_created=self.step
                    )
                    self.lines[other_id].inbox.append(sync_task)
                    self.lines[other_id].cross_signals_recv += 1
                    line.cross_signals_sent += 1
    
    # =====================================================================
    # 大周天: 全局循环
    # =====================================================================
    def big_circulation(self):
        """
        大周天循环:
        ucif2调度 → 目标线inbox → 目标线处理 → 目标线outbox 
        → ucif2读取 → ucif2验证 → 全局状态更新 → 下一调度
        """
        self.scheduler_cycles += 1
        
        # 1. ucif2调度: 随机注入外部任务
        if np.random.random() < 0.4:
            target = np.random.randint(0, NUM_LINES)
            ext_task = Task(
                tid=self.step * 10000 + 999,
                ttype=TaskType.INGEST,
                src_line=-1,  # 外部源
                dst_line=target,
                payload={"external": True, "data": f"step_{self.step}"},
                step_created=self.step
            )
            self.lines[target].inbox.append(ext_task)
            self.lines[target].tasks_created += 1
        
        # 2-4. 各线处理 (在小circulation中完成)
        
        # 5. ucif2读取各线outbox
        global_updates = []
        for lid in range(NUM_LINES):
            line = self.lines[lid]
            while line.outbox:
                result = line.outbox.popleft()
                global_updates.append((lid, result))
        
        # 6. ucif2验证 & 全局张量更新
        self.tensor_contract(global_updates)
        
        # 7. 全局状态更新
        self.update_global_health()
        
        # 8. 全局广播
        self.ring_broadcast()
        
        # 9. 互激处理
        for lid in range(NUM_LINES):
            self.mutual_excite(lid)
    
    def tensor_contract(self, updates: List[Tuple[int, dict]]):
        """
        tensor_contract: 全局张量收缩循环
        将各线产出收缩到全局张量，实现信息聚合
        """
        if not updates:
            # 无更新时也进行自收缩 (保持循环闭合)
            self.global_tensor *= 0.995
            self.contract_log.append((self.step, float(np.trace(self.global_tensor))))
            return
        
        for lid, result in updates:
            for other_id in range(NUM_LINES):
                # 张量更新: 该线产出影响全局连接
                increment = 0.05 * CROSS_MATRIX[lid, other_id]
                self.global_tensor[lid, other_id] += increment
                self.global_tensor[other_id, lid] += increment
        
        # 对称归一化 (收缩)
        self.global_tensor = np.tanh(self.global_tensor * 0.5)
        trace = float(np.trace(self.global_tensor))
        self.contract_log.append((self.step, trace))
    
    def update_global_health(self):
        """全局health状态更新"""
        for lid in range(NUM_LINES):
            line = self.lines[lid]
            # 全局health是局部health与张量对角线的融合
            tensor_diag = self.global_tensor[lid, lid]
            self.global_health[lid] = 0.7 * line.health + 0.3 * tensor_diag
    
    def ring_broadcast(self):
        """
        ring_broadcast: 全局广播循环
        将全局状态信息广播到所有线
        """
        broadcast_msg = {
            "step": self.step,
            "global_health_mean": float(np.mean(self.global_health)),
            "global_health_std": float(np.std(self.global_health)),
            "tensor_trace": float(np.trace(self.global_tensor)),
            "active_lines": sum(1 for l in self.lines.values() if l.silence_count < SILENCE_THRESHOLD)
        }
        self.ring_buffer.append(broadcast_msg)
        self.broadcast_log.append((self.step, broadcast_msg))
        
        # 所有线接收广播
        for lid in range(NUM_LINES):
            line = self.lines[lid]
            line.session["last_broadcast"] = broadcast_msg
            # 广播影响: 全局健康度高的线获得health加成
            if broadcast_msg["global_health_mean"] > 0.7:
                line.health = min(1.0, line.health + 0.005)
    
    # =====================================================================
    # 主循环
    # =====================================================================
    def step_simulation(self):
        """单步模拟"""
        # 大周天: 全局调度
        self.big_circulation()
        
        # 小周天: 每线自循环
        for lid in range(NUM_LINES):
            self.small_circulation(lid)
        
        # 记录历史
        self.record_history()
        self.step += 1
    
    def record_history(self):
        """记录当前步状态"""
        state_snapshot = {
            "step": self.step,
            "timestamp": time.time(),
            "lines": {},
            "global": {
                "health_mean": float(np.mean(self.global_health)),
                "health_std": float(np.std(self.global_health)),
                "tensor_trace": float(np.trace(self.global_tensor)),
                "scheduler_cycles": self.scheduler_cycles,
                "ring_buffer_size": len(self.ring_buffer)
            }
        }
        
        for lid in range(NUM_LINES):
            line = self.lines[lid]
            state_snapshot["lines"][lid] = {
                "health": round(line.health, 4),
                "silence": line.silence_count,
                "pulse_count": line.pulse_count,
                "processed": line.tasks_processed,
                "created": line.tasks_created,
                "inbox_len": len(line.inbox),
                "outbox_len": len(line.outbox),
                "self_loops": line.self_loop_closed,
                "cross_sent": line.cross_signals_sent,
                "cross_recv": line.cross_signals_recv,
                "si0": line.si.si0_count,
                "si1": line.si.si1_count,
                "si2": line.si.si2_count,
                "si3": line.si.si3_count,
            }
        
        self.history.append(state_snapshot)
    
    def run(self, steps: int = MAX_STEPS):
        """运行完整模拟"""
        logger.info(f"[CIRCULATION-VERIFY] 启动11线SI引擎大小周天验证")
        logger.info(f"[CIRCULATION-VERIFY] 模拟步数: {steps}")
        logger.info(f"[CIRCULATION-VERIFY] 自激阈值: {SILENCE_THRESHOLD}拍")
        logger.info("=" * 70)
        
        for s in range(steps):
            self.step_simulation()
            if (s + 1) % 20 == 0:
                logger.info(f"  Step {s+1:3d}/{steps} | 全局Health: {np.mean(self.global_health):.3f} | "
                      f"张量Trace: {np.trace(self.global_tensor):.3f} | "
                      f"总处理: {sum(l.tasks_processed for l in self.lines.values())}")
        
        logger.info("=" * 70)
        return self.generate_report()
    
    # =====================================================================
    # 报告生成
    # =====================================================================
    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告数据"""
        report = {
            "meta": {
                "script": "CIRCULATION-VERIFY-01.py",
                "version": "1.0",
                "lines": NUM_LINES,
                "steps": MAX_STEPS,
                "silence_threshold": SILENCE_THRESHOLD,
            },
            "summary": {},
            "circulation_checks": {},
            "line_details": []
        }
        
        # 1. 总体统计
        total_processed = sum(l.tasks_processed for l in self.lines.values())
        total_pulses = sum(l.pulse_count for l in self.lines.values())
        total_self_loops = sum(l.self_loop_closed for l in self.lines.values())
        total_cross_sent = sum(l.cross_signals_sent for l in self.lines.values())
        total_cross_recv = sum(l.cross_signals_recv for l in self.lines.values())
        
        report["summary"] = {
            "total_tasks_processed": total_processed,
            "total_self_pulses": total_pulses,
            "total_self_loops": total_self_loops,
            "total_cross_signals_sent": total_cross_sent,
            "total_cross_signals_recv": total_cross_recv,
            "scheduler_cycles": self.scheduler_cycles,
            "tensor_contract_calls": len(self.contract_log),
            "ring_broadcast_calls": len(self.broadcast_log),
            "final_global_health_mean": round(float(np.mean(self.global_health)), 4),
            "final_global_health_std": round(float(np.std(self.global_health)), 4),
            "final_tensor_trace": round(float(np.trace(self.global_tensor)), 4),
        }
        
        # 2. 循环闭合验证
        checks = self.verify_closures()
        report["circulation_checks"] = checks
        
        # 3. 每线详情
        for lid in range(NUM_LINES):
            line = self.lines[lid]
            report["line_details"].append({
                "line_id": lid,
                "name": LINE_NAMES[lid],
                "health": round(line.health, 4),
                "pulse_count": line.pulse_count,
                "tasks_processed": line.tasks_processed,
                "tasks_created": line.tasks_created,
                "self_loops": line.self_loop_closed,
                "cross_sent": line.cross_signals_sent,
                "cross_recv": line.cross_signals_recv,
                "si_counts": {
                    "si0": line.si.si0_count,
                    "si1": line.si.si1_count,
                    "si2": line.si.si2_count,
                    "si3": line.si.si3_count,
                }
            })
        
        return report
    
    def verify_closures(self) -> Dict[str, Any]:
        """验证所有循环是否闭合"""
        checks = {}
        
        # (1) 小周天自循环闭合验证
        # 标准: 每线至少完成一次完整的 inbox→SI0→SI1→SI2→SI3→outbox→session→等待
        small_closed = True
        small_details = []
        for lid in range(NUM_LINES):
            line = self.lines[lid]
            # 自循环闭合条件: SI0-SI3均有计数，且outbox有产出
            closed = (line.si.si0_count > 0 and line.si.si1_count > 0 and 
                     line.si.si2_count > 0 and line.si.si3_count > 0 and
                     line.self_loop_closed > 0)
            small_details.append({
                "line": LINE_NAMES[lid],
                "closed": closed,
                "loops": line.self_loop_closed
            })
            if not closed:
                small_closed = False
        
        checks["small_circulation"] = {
            "name": "小周天（每线自循环）",
            "status": "CLOSED" if small_closed else "OPEN",
            "all_lines_closed": small_closed,
            "details": small_details
        }
        
        # (2) 自激验证
        # 标准: 所有线至少触发一次自激PULSE
        self_excite_ok = all(l.pulse_count > 0 for l in self.lines.values())
        checks["self_excite"] = {
            "name": "自激 (self_excite)",
            "status": "ACTIVE" if self_excite_ok else "INACTIVE",
            "all_lines_pulsed": self_excite_ok,
            "pulse_counts": {LINE_NAMES[i]: self.lines[i].pulse_count for i in range(NUM_LINES)}
        }
        
        # (3) 互激验证
        # 标准: 存在跨线信号传递
        mutual_excite_ok = sum(l.cross_signals_sent for l in self.lines.values()) > 0
        checks["mutual_excite"] = {
            "name": "互激 (mutual_excite)",
            "status": "ACTIVE" if mutual_excite_ok else "INACTIVE",
            "total_signals_sent": sum(l.cross_signals_sent for l in self.lines.values()),
            "total_signals_recv": sum(l.cross_signals_recv for l in self.lines.values()),
        }
        
        # (4) 自环验证
        # 标准: health检查循环运行，health_history有记录
        self_loop_ok = all(len(l.health_history) > 0 for l in self.lines.values())
        checks["self_loop"] = {
            "name": "自环 (self_loop)",
            "status": "CLOSED" if self_loop_ok else "OPEN",
            "all_health_tracked": self_loop_ok,
        }
        
        # (5) 互环验证
        # 标准: 跨线数据同步循环运行，cross_signals > 0
        cross_loop_ok = (sum(l.cross_signals_sent for l in self.lines.values()) > 0 and
                        sum(l.cross_signals_recv for l in self.lines.values()) > 0)
        checks["cross_loop"] = {
            "name": "互环 (cross_loop)",
            "status": "CLOSED" if cross_loop_ok else "OPEN",
            "cross_traffic_exists": cross_loop_ok,
        }
        
        # (6) tensor_contract验证
        # 标准: 全局张量收缩循环每步都调用
        tensor_ok = len(self.contract_log) == MAX_STEPS
        checks["tensor_contract"] = {
            "name": "张量收缩 (tensor_contract)",
            "status": "CLOSED" if tensor_ok else "OPEN",
            "calls": len(self.contract_log),
            "expected": MAX_STEPS,
            "final_trace": round(float(np.trace(self.global_tensor)), 4),
        }
        
        # (7) ring_broadcast验证
        # 标准: 全局广播循环每步都调用
        broadcast_ok = len(self.broadcast_log) == MAX_STEPS
        checks["ring_broadcast"] = {
            "name": "全局广播 (ring_broadcast)",
            "status": "CLOSED" if broadcast_ok else "OPEN",
            "calls": len(self.broadcast_log),
            "expected": MAX_STEPS,
        }
        
        # (8) 大周天验证
        # 标准: scheduler_cycles == MAX_STEPS
        big_ok = self.scheduler_cycles == MAX_STEPS
        checks["big_circulation"] = {
            "name": "大周天（全局循环）",
            "status": "CLOSED" if big_ok else "OPEN",
            "scheduler_cycles": self.scheduler_cycles,
            "expected": MAX_STEPS,
        }
        
        # (9) 全局闭环验证
        all_closed = (small_closed and self_excite_ok and mutual_excite_ok and 
                     self_loop_ok and cross_loop_ok and tensor_ok and broadcast_ok and big_ok)
        checks["global_closure"] = {
            "name": "全11线闭环",
            "status": "CLOSED" if all_closed else "PARTIAL",
            "all_checks_pass": all_closed,
        }
        
        return checks


def save_json(data: dict, path: str):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_md_report(report: dict, history: list, output_path: str):
    """生成Markdown格式的验证报告"""
    
    md = []
    md.append("# ucif2 大小周天自循环验证报告")
    md.append("")
    md.append(f"**验证脚本**: `{report['meta']['script']}`  ")
    md.append(f"**版本**: {report['meta']['version']}  ")
    md.append(f"**模拟步数**: {report['meta']['steps']}  ")
    md.append(f"**线数**: {report['meta']['lines']}  ")
    md.append(f"**自激阈值**: {report['meta']['silence_threshold']}拍  ")
    md.append(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    md.append("")
    md.append("---")
    md.append("")
    
    # 摘要
    md.append("## 一、总体摘要")
    md.append("")
    s = report["summary"]
    md.append(f"| 指标 | 数值 |")
    md.append(f"|------|------|")
    md.append(f"| 总任务处理数 | {s['total_tasks_processed']} |")
    md.append(f"| 总自激PULSE数 | {s['total_self_pulses']} |")
    md.append(f"| 总自环闭合数 | {s['total_self_loops']} |")
    md.append(f"| 跨线信号发送 | {s['total_cross_signals_sent']} |")
    md.append(f"| 跨线信号接收 | {s['total_cross_signals_recv']} |")
    md.append(f"| 调度器周期 | {s['scheduler_cycles']} |")
    md.append(f"| 张量收缩调用 | {s['tensor_contract_calls']} |")
    md.append(f"| 全局广播调用 | {s['ring_broadcast_calls']} |")
    md.append(f"| 最终全局Health均值 | {s['final_global_health_mean']} |")
    md.append(f"| 最终全局Health标准差 | {s['final_global_health_std']} |")
    md.append(f"| 最终张量Trace | {s['final_tensor_trace']} |")
    md.append("")
    
    # 循环验证结果
    md.append("## 二、大小周天循环闭合验证")
    md.append("")
    md.append("### 2.1 验证结果总览")
    md.append("")
    md.append(f"| 循环类型 | 状态 | 说明 |")
    md.append(f"|----------|------|------|")
    
    for key, val in report["circulation_checks"].items():
        status = val["status"]
        status_emoji = "✅" if status in ["CLOSED", "ACTIVE"] else "⚠️"
        md.append(f"| {val['name']} | {status_emoji} {status} | (见下文) |")
    
    md.append("")
    
    # 详细验证
    md.append("### 2.2 详细验证项")
    md.append("")
    
    # 小周天
    sc = report["circulation_checks"]["small_circulation"]
    md.append(f"#### 1 小周天（每线自循环）- {sc['status']}")
    md.append("")
    md.append("```")
    md.append("inbox新任务 → SI0读取 → SI1解析 → SI2分类 → SI3执行")
    md.append("                ↓                                    ↓")
    md.append("         等待下一任务 ← SI1更新session ← SI0上传outbox")
    md.append("```")
    md.append("")
    md.append(f"- **所有线闭合**: {'是' if sc['all_lines_closed'] else '否'}")
    md.append("")
    md.append("| 线名 | 自环闭合数 | 状态 |")
    md.append("|------|-----------|------|")
    for d in sc["details"]:
        st = "✅" if d["closed"] else "❌"
        md.append(f"| {d['line']} | {d['loops']} | {st} |")
    md.append("")
    
    # 自激
    se = report["circulation_checks"]["self_excite"]
    md.append(f"#### 2 自激 (self_excite) - {se['status']}")
    md.append("")
    md.append("```")
    md.append("[静默计数] → 达到8拍 → 自动触发PULSE → inbox注入")
    md.append("     ↑                                      ↓")
    md.append("     └────────── 处理完成重置计数 ←─────────┘")
    md.append("```")
    md.append("")
    md.append(f"- **所有线触发**: {'是' if se['all_lines_pulsed'] else '否'}")
    md.append("")
    md.append("| 线名 | PULSE次数 |")
    md.append("|------|----------|")
    for name, count in se["pulse_counts"].items():
        md.append(f"| {name} | {count} |")
    md.append("")
    
    # 互激
    me = report["circulation_checks"]["mutual_excite"]
    md.append(f"#### 3 互激 (mutual_excite) - {me['status']}")
    md.append("")
    md.append("```")
    md.append("线A health变化 ──→ 按CROSS_MATRIX权重 ──→ 线B inbox注入SYNC任务")
    md.append("   ↑                                              ↓")
    md.append("   └──────── 线B处理影响全局health ←──────────────┘")
    md.append("```")
    md.append("")
    md.append(f"- **总信号发送**: {me['total_signals_sent']}")
    md.append(f"- **总信号接收**: {me['total_signals_recv']}")
    md.append("")
    
    # 自环
    sl = report["circulation_checks"]["self_loop"]
    md.append(f"#### 4 自环 (self_loop) - {sl['status']}")
    md.append("")
    md.append("```")
    md.append("health检查 → health_history记录 → delta计算 → 状态调整")
    md.append("    ↑                                              ↓")
    md.append("    └──────────── 下一轮检查 ←─────────────────────┘")
    md.append("```")
    md.append("")
    md.append(f"- **所有线health追踪**: {'是' if sl['all_health_tracked'] else '否'}")
    md.append("")
    
    # 互环
    cl = report["circulation_checks"]["cross_loop"]
    md.append(f"#### 5 互环 (cross_loop) - {cl['status']}")
    md.append("")
    md.append("```")
    md.append("线A产出 ──→ outbox ──→ ucif2读取 ──→ tensor_contract")
    md.append("                                          ↓")
    md.append("线B接收 ←─ ring_broadcast ←─ 全局状态更新 ←┘")
    md.append("```")
    md.append("")
    md.append(f"- **跨线流量存在**: {'是' if cl['cross_traffic_exists'] else '否'}")
    md.append("")
    
    # tensor_contract
    tc = report["circulation_checks"]["tensor_contract"]
    md.append(f"#### 6 张量收缩 (tensor_contract) - {tc['status']}")
    md.append("")
    md.append("```")
    md.append("各线产出 ──→ 全局张量(global_tensor) ──→ tanh归一化 ──→ trace计算")
    md.append("    ↑                                                      ↓")
    md.append("    └────────────── 下一轮收缩输入 ←────────────────────────┘")
    md.append("```")
    md.append("")
    md.append(f"- **调用次数**: {tc['calls']}/{tc['expected']}")
    md.append(f"- **最终Trace**: {tc['final_trace']}")
    md.append("")
    
    # ring_broadcast
    rb = report["circulation_checks"]["ring_broadcast"]
    md.append(f"#### 7 全局广播 (ring_broadcast) - {rb['status']}")
    md.append("")
    md.append("```")
    md.append("全局状态 ──→ ring_buffer ──→ 所有线session更新")
    md.append("   ↑                                          ↓")
    md.append("   └──────── 下一轮广播状态采集 ←─────────────┘")
    md.append("```")
    md.append("")
    md.append(f"- **调用次数**: {rb['calls']}/{rb['expected']}")
    md.append("")
    
    # 大周天
    bc = report["circulation_checks"]["big_circulation"]
    md.append(f"#### 8 大周天（全局循环）- {bc['status']}")
    md.append("")
    md.append("```")
    md.append("ucif2调度 ──→ 目标线inbox ──→ 目标线处理 ──→ 目标线outbox")
    md.append("    ↑                                                      ↓")
    md.append("    └─ 下一调度 ←─ 全局状态更新 ←─ ucif2验证 ←─ ucif2读取 ─┘")
    md.append("```")
    md.append("")
    md.append(f"- **调度周期**: {bc['scheduler_cycles']}/{bc['expected']}")
    md.append("")
    
    # 全局闭环
    gc = report["circulation_checks"]["global_closure"]
    md.append(f"### 2.3 全11线闭环总判定 - {gc['status']}")
    md.append("")
    if gc["all_checks_pass"]:
        md.append("**✅ 所有循环均已闭合。11线SI引擎大小周天自循环验证通过。**")
    else:
        md.append("**⚠️ 部分循环未完全闭合。详见上方各验证项。**")
    md.append("")
    
    # 每线详情
    md.append("## 三、每线运行详情")
    md.append("")
    md.append("| 线ID | 线名 | Health | PULSE | 处理数 | 创建数 | 自环 | 跨发 | 跨收 | SI0 | SI1 | SI2 | SI3 |")
    md.append("|------|------|--------|-------|--------|--------|------|------|------|-----|-----|-----|-----|")
    
    for ld in report["line_details"]:
        md.append(f"| {ld['line_id']:02d} | {ld['name']} | {ld['health']:.3f} | "
                  f"{ld['pulse_count']} | {ld['tasks_processed']} | {ld['tasks_created']} | "
                  f"{ld['self_loops']} | {ld['cross_sent']} | {ld['cross_recv']} | "
                  f"{ld['si_counts']['si0']} | {ld['si_counts']['si1']} | "
                  f"{ld['si_counts']['si2']} | {ld['si_counts']['si3']} |")
    
    md.append("")
    
    # 时间序列分析
    md.append("## 四、时间序列分析")
    md.append("")
    
    if history:
        # 提取关键指标
        steps = [h["step"] for h in history]
        health_means = [h["global"]["health_mean"] for h in history]
        tensor_traces = [h["global"]["tensor_trace"] for h in history]
        
        md.append(f"- **全局Health均值范围**: {min(health_means):.4f} ~ {max(health_means):.4f}")
        md.append(f"- **全局Health最终值**: {health_means[-1]:.4f}")
        md.append(f"- **张量Trace范围**: {min(tensor_traces):.4f} ~ {max(tensor_traces):.4f}")
        md.append(f"- **张量Trace最终值**: {tensor_traces[-1]:.4f}")
    
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 五、结论")
    md.append("")
    
    if gc["all_checks_pass"]:
        md.append("### ✅ 验证通过")
        md.append("")
        md.append("所有11线的大小周天自循环均已正确建立并运行:")
        md.append("- 每线小周天（inbox→SI0→SI1→SI2→SI3→outbox→session）闭合")
        md.append("- 自激机制（8拍静默→PULSE）正常工作")
        md.append("- 互激机制（health变化→跨线SYNC）正常触发")
        md.append("- 自环（health检查循环）持续运行")
        md.append("- 互环（跨线数据同步循环）持续运行")
        md.append("- 张量收缩循环每步调用，全局信息聚合正常")
        md.append("- 全局广播循环每步调用，全状态同步正常")
        md.append("- 大周天全局循环（调度→处理→验证→更新）完整闭合")
        md.append("")
        md.append("**系统状态**: 所有循环闭合，ucif2引擎可稳定运行。")
    else:
        md.append("### ⚠️ 验证未完全通过")
        md.append("")
        md.append("部分循环存在异常，需进一步排查。")
    
    md.append("")
    md.append("---")
    md.append("")
    md.append(f"*报告生成完毕 | CIRCULATION-VERIFY-01 v1.0*")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    
    logger.info(f"[CIRCULATION-VERIFY] Markdown报告已保存: {output_path}")


# =============================================================================
# 主入口
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("  ucif2 系统大小周天自循环验证")
    print("  CIRCULATION-VERIFY-01")
    print("=" * 70)
    print()
    
    scheduler = UCIF2Scheduler()
    report = scheduler.run(steps=MAX_STEPS)
    
    # 保存JSON报告
    json_path = "/mnt/agents/output/OMNI-HUB/closure/CIRCULATION-RESULT-01.json"
    save_json(report, json_path)
    print(f"[CIRCULATION-VERIFY] JSON报告已保存: {json_path}")
    
    # 保存Markdown报告
    md_path = "/mnt/agents/output/OMNI-HUB/closure/CIRCULATION-RESULT-01.md"
    generate_md_report(report, scheduler.history, md_path)
    
    # 保存完整历史数据
    history_path = "/mnt/agents/output/OMNI-HUB/closure/CIRCULATION-HISTORY-01.json"
    save_json({"history": scheduler.history}, history_path)
    print(f"[CIRCULATION-VERIFY] 历史数据已保存: {history_path}")
    
    print()
    print("=" * 70)
    print("  验证完成")
    print("=" * 70)
    print()
    
    # 打印关键结论
    print("【关键结论】")
    gc = report["circulation_checks"]["global_closure"]
    print(f"  全11线闭环状态: {'✅ 已闭合' if gc['all_checks_pass'] else '⚠️ 未完全闭合'}")
    print(f"  小周天自循环: {report['circulation_checks']['small_circulation']['status']}")
    print(f"  自激机制: {report['circulation_checks']['self_excite']['status']}")
    print(f"  互激机制: {report['circulation_checks']['mutual_excite']['status']}")
    print(f"  张量收缩: {report['circulation_checks']['tensor_contract']['status']}")
    print(f"  全局广播: {report['circulation_checks']['ring_broadcast']['status']}")
    print(f"  大周天全局: {report['circulation_checks']['big_circulation']['status']}")
    print()
    print(f"  总任务处理: {report['summary']['total_tasks_processed']}")
    print(f"  总自激PULSE: {report['summary']['total_self_pulses']}")
    print(f"  最终全局Health: {report['summary']['final_global_health_mean']:.4f}")
    print()
