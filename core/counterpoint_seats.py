
"""
OMNI-HUB v4.0 — Counterpoint Seats Module
对位席架构实现

核心命题: "和声不是齐唱，对位即显化"

11条独立声部作为11个对位席，遵循音乐对位法则映射到系统架构：
1. 禁止平行五度/八度 → 禁止线间完全同步
2. 反向进行优先 → 线间差异化运动
3. 声部超越 → 高SI线可暂时低于低SI线
4. 协和音程分类 → 完美/不完全/不协和
5. 解决规则 → 张力→松弛趋向
6. 休止的艺术 → qgl的沉默是负空间
"""

__version__ = "11.0.0"
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
import warnings

from voice_melody import (
    MelodyTheme, NoteEvent, ConsonanceType,
    create_melody, get_all_melodies, MELODY_REGISTRY,
    CantusFirmusMelody, SilentBeatMelody
)


@dataclass
class CounterpointSeat:
    """
    单条线的对位席 — 一个独立声部
    
    对位席是OMNI-HUB中的"显化单元"，每条线对应一个声部，
    各自独立运动，相互形成对位关系。
    """
    line_id: str
    seat_name: str
    voice_type: str  # soprano/alto/tenor/bass/cantus_firmus/rest
    melody_theme: MelodyTheme
    interval_range: Tuple[int, int] = (0, 12)  # 音程运动范围（半音）
    rhythm_pattern: str = "common_time"  # 节奏型
    rest_probability: float = 0.0
    priority: int = 5  # 声部优先级 (1-10)
    
    # 运行时状态
    current_note: Optional[NoteEvent] = None
    note_history: List[NoteEvent] = field(default_factory=list)
    direction_history: List[int] = field(default_factory=list)  # 运动方向记录
    
    def __post_init__(self):
        if self.melody_theme is None:
            self.melody_theme = create_melody(self.line_id)
    
    def play_note(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        """在时刻t演奏音符"""
        note = self.melody_theme.generate(t, context)
        note.line_id = self.line_id
        note.seat_name = self.seat_name
        
        # 记录运动方向
        if self.current_note and not self.current_note.is_rest() and not note.is_rest():
            direction = np.sign(note.pitch - self.current_note.pitch)
            self.direction_history.append(int(direction))
        
        self.current_note = note
        self.note_history.append(note)
        self.melody_theme.history.append(note)
        
        return note
    
    def get_average_direction(self, window: int = 4) -> float:
        """获取最近window个音符的平均运动方向"""
        if len(self.direction_history) < window:
            return 0.0
        recent = self.direction_history[-window:]
        return np.mean(recent)
    
    def get_pitch_range_used(self) -> Tuple[Optional[int], Optional[int]]:
        """获取实际使用的音高范围"""
        pitches = [n.pitch for n in self.note_history if not n.is_rest()]
        if not pitches:
            return None, None
        return min(pitches), max(pitches)
    
    def get_rest_ratio(self) -> float:
        """获取休止比例"""
        if not self.note_history:
            return 0.0
        rests = sum(1 for n in self.note_history if n.is_rest())
        return rests / len(self.note_history)
    
    def get_melodic_intervals(self) -> List[int]:
        """获取旋律音程序列"""
        intervals = []
        for i in range(1, len(self.note_history)):
            n1, n2 = self.note_history[i-1], self.note_history[i]
            if not n1.is_rest() and not n2.is_rest():
                intervals.append(abs(n2.pitch - n1.pitch))
        return intervals
    
    def __repr__(self):
        return f"CounterpointSeat({self.line_id}: {self.seat_name}, {self.voice_type})"


class CounterpointOrchestra:
    """
    全席管弦乐团 — 11个对位席的复调交织
    
    指挥全席演奏，检测对位违规，计算协和度与独立性。
    """
    
    # 声部类型对应的默认音域
    VOICE_RANGES = {
        "cantus_firmus": (55, 72),
        "soprano": (64, 91),
        "alto": (55, 79),
        "tenor": (48, 72),
        "bass": (36, 60),
        "rest": (36, 60),
    }
    
    # 对位违规的严重程度
    VIOLATION_WEIGHTS = {
        "parallel_fifth": 1.0,
        "parallel_octave": 1.0,
        "direct_fifth": 0.5,
        "direct_octave": 0.5,
        "unison": 0.8,
        "voice_crossing": 0.3,
    }
    
    def __init__(self, seats: Optional[List[CounterpointSeat]] = None):
        self.seats: Dict[str, CounterpointSeat] = {}
        self.cantus_firmus: Optional[CounterpointSeat] = None
        self.time: float = 0.0
        self.violations: List[Dict[str, Any]] = []
        self.harmony_history: List[Dict[str, Any]] = []
        
        if seats:
            for seat in seats:
                self.add_seat(seat)
        else:
            self._create_default_seats()
    
    def _create_default_seats(self):
        """创建默认的11个对位席"""
        registry = SeatRegistry()
        for line_id in MELODY_REGISTRY.keys():
            config = registry.get_seat(line_id)
            melody = create_melody(line_id)
            seat = CounterpointSeat(
                line_id=line_id,
                seat_name=config["seat_name"],
                voice_type=config["voice_type"],
                melody_theme=melody,
                interval_range=config["interval_range"],
                rhythm_pattern=config["rhythm_pattern"],
                rest_probability=config["rest_probability"],
                priority=config["priority"]
            )
            self.add_seat(seat)
    
    def add_seat(self, seat: CounterpointSeat):
        """添加对位席"""
        self.seats[seat.line_id] = seat
        if seat.voice_type == "cantus_firmus":
            self.cantus_firmus = seat
    
    def conduct(self, t: float, context: Optional[Dict[str, Any]] = None) -> Dict[str, NoteEvent]:
        """
        在时刻t指挥全席演奏
        
        返回每个对位席在当前时刻的音符。
        """
        if context is None:
            context = {}
        
        context["time"] = t
        context["orchestra"] = self
        
        results = {}
        
        # 1. 先演奏固定旋律 (Cantus Firmus) — 基准声部
        if self.cantus_firmus:
            cf_note = self.cantus_firmus.play_note(t, context)
            context["cantus_firmus_pitch"] = cf_note.pitch if not cf_note.is_rest() else None
            results[self.cantus_firmus.line_id] = cf_note
        
        # 2. 其他声部围绕固定旋律运动
        for line_id, seat in self.seats.items():
            if seat == self.cantus_firmus:
                continue
            
            # 构建声部特定的上下文
            seat_context = context.copy()
            seat_context["other_pitches"] = [
                n.pitch for n in results.values() 
                if n.pitch is not None
            ]
            seat_context["logic_depth"] = len(seat.note_history) % 7
            seat_context["branches"] = 2 + (hash(line_id) % 4)
            seat_context["will_strength"] = 0.3 + 0.5 * np.sin(t * 0.1)
            seat_context["verification_level"] = 0.5 + 0.3 * np.cos(t * 0.15)
            seat_context["quantization_levels"] = 12
            seat_context["observation_precision"] = 0.6 + 0.3 * np.sin(t * 0.2)
            seat_context["federation_nodes"] = 3 + (int(t) % 5)
            seat_context["topology"] = ["ring", "star", "mesh"][int(t / 10) % 3]
            seat_context["fold_angle"] = 30 + 45 * np.sin(t * 0.1)
            seat_context["curvature"] = 0.5 * np.sin(t * 0.15)
            seat_context["max_recursion_depth"] = 3 + (int(t / 8) % 3)
            seat_context["local_variation"] = 0.3 + 0.4 * np.abs(np.sin(t * 0.2))
            seat_context["generation"] = int(t // 16)
            seat_context["brand_pulse"] = 0.5 + 0.3 * np.sin(t * 0.25)
            
            note = seat.play_note(t, seat_context)
            
            # 音高碰撞避免: 如果与其他活跃声部同度，轻微偏移
            if not note.is_rest():
                for other_id, other_note in results.items():
                    if other_note.is_rest():
                        continue
                    if note.pitch == other_note.pitch:
                        # 检测到同度碰撞，轻微偏移
                        offset = seat.melody_theme.rng.choice([-1, 1])
                        new_pitch = note.pitch + offset
                        # 确保在音域内
                        pr = seat.melody_theme.pitch_range
                        new_pitch = max(pr[0], min(pr[1], new_pitch))
                        note.pitch = new_pitch
                        seat.melody_theme.prev_pitch = new_pitch
            
            results[line_id] = note
        
        # 3. 检测对位违规
        self._detect_violations(t, results)
        
        # 4. 记录和声
        harmony = self._analyze_harmony(t, results)
        self.harmony_history.append(harmony)
        
        self.time = t
        return results
    
    def _detect_violations(self, t: float, results: Dict[str, NoteEvent]):
        """检测对位违规"""
        active_notes = {lid: n for lid, n in results.items() if not n.is_rest()}
        line_ids = list(active_notes.keys())
        
        for i in range(len(line_ids)):
            for j in range(i + 1, len(line_ids)):
                lid1, lid2 = line_ids[i], line_ids[j]
                n1, n2 = active_notes[lid1], active_notes[lid2]
                
                interval = abs(n1.pitch - n2.pitch) % 12
                
                # 检测齐唱 (同度) — 不同声部不能在同一音高
                if n1.pitch == n2.pitch:
                    self.violations.append({
                        "time": t,
                        "type": "unison",
                        "lines": (lid1, lid2),
                        "pitches": (n1.pitch, n2.pitch),
                        "severity": self.VIOLATION_WEIGHTS["unison"]
                    })
                
                # 检测平行五度/八度需要历史信息
                if len(self.seats[lid1].note_history) >= 2 and \
                   len(self.seats[lid2].note_history) >= 2:
                    
                    prev_n1 = self.seats[lid1].note_history[-2]
                    prev_n2 = self.seats[lid2].note_history[-2]
                    
                    if not prev_n1.is_rest() and not prev_n2.is_rest():
                        prev_interval = abs(prev_n1.pitch - prev_n2.pitch) % 12
                        
                        # 平行五度: 两个声部都保持纯五度关系同向运动
                        if interval == 7 and prev_interval == 7:
                            dir1 = np.sign(n1.pitch - prev_n1.pitch)
                            dir2 = np.sign(n2.pitch - prev_n2.pitch)
                            if dir1 == dir2 and dir1 != 0:
                                self.violations.append({
                                    "time": t,
                                    "type": "parallel_fifth",
                                    "lines": (lid1, lid2),
                                    "pitches": (n1.pitch, n2.pitch),
                                    "severity": self.VIOLATION_WEIGHTS["parallel_fifth"]
                                })
                        
                        # 平行八度
                        if interval == 0 and prev_interval == 0 and n1.pitch != prev_n1.pitch:
                            dir1 = np.sign(n1.pitch - prev_n1.pitch)
                            dir2 = np.sign(n2.pitch - prev_n2.pitch)
                            if dir1 == dir2 and dir1 != 0:
                                self.violations.append({
                                    "time": t,
                                    "type": "parallel_octave",
                                    "lines": (lid1, lid2),
                                    "pitches": (n1.pitch, n2.pitch),
                                    "severity": self.VIOLATION_WEIGHTS["parallel_octave"]
                                })
    
    def _analyze_harmony(self, t: float, results: Dict[str, NoteEvent]) -> Dict[str, Any]:
        """分析和声结构"""
        active_notes = [n for n in results.values() if not n.is_rest()]
        pitches = [n.pitch for n in active_notes]
        
        if not pitches:
            return {"time": t, "pitches": [], "intervals": [], "consonance_score": 0}
        
        # 计算所有声部间的音程
        intervals = []
        consonance_scores = []
        for i in range(len(pitches)):
            for j in range(i + 1, len(pitches)):
                interval = abs(pitches[i] - pitches[j])
                intervals.append(interval)
                
                interval_class = interval % 12
                if interval_class in {0, 7}:
                    consonance_scores.append(3.0)  # 完美协和
                elif interval_class in {3, 4, 8, 9}:
                    consonance_scores.append(2.0)  # 不完全协和
                else:
                    consonance_scores.append(1.0)  # 不协和
        
        avg_consonance = np.mean(consonance_scores) if consonance_scores else 0
        
        return {
            "time": t,
            "pitches": pitches,
            "intervals": intervals,
            "consonance_score": avg_consonance,
            "n_active": len(active_notes)
        }
    
    def get_harmony(self, t: float) -> Dict[str, Any]:
        """获取t时刻的和声"""
        for h in self.harmony_history:
            if abs(h["time"] - t) < 0.01:
                return h
        return {}
    
    def get_consonance_matrix(self, t: float) -> Optional[np.ndarray]:
        """
        获取t时刻的协和度矩阵
        
        返回11x11矩阵，元素(i,j)表示声部i和j的协和度
        """
        results = {lid: seat.current_note for lid, seat in self.seats.items()}
        line_ids = sorted(results.keys())
        n = len(line_ids)
        matrix = np.zeros((n, n))
        
        for i, lid1 in enumerate(line_ids):
            for j, lid2 in enumerate(line_ids):
                if i == j:
                    matrix[i, j] = 3.0  # 自身完美协和
                    continue
                
                n1, n2 = results[lid1], results[lid2]
                if n1.is_rest() or n2.is_rest():
                    matrix[i, j] = 0.0  # 休止
                    continue
                
                interval = abs(n1.pitch - n2.pitch) % 12
                if interval in {0, 7}:
                    matrix[i, j] = 3.0
                elif interval in {3, 4, 8, 9}:
                    matrix[i, j] = 2.0
                else:
                    matrix[i, j] = 1.0
        
        return matrix, line_ids
    
    def detect_parallel_fifths(self) -> List[Dict[str, Any]]:
        """检测所有平行五度违规"""
        return [v for v in self.violations if v["type"] == "parallel_fifth"]
    
    def detect_unison(self) -> List[Dict[str, Any]]:
        """检测所有齐唱违规"""
        return [v for v in self.violations if v["type"] == "unison"]
    
    def detect_parallel_octaves(self) -> List[Dict[str, Any]]:
        """检测所有平行八度违规"""
        return [v for v in self.violations if v["type"] == "parallel_octave"]
    
    def get_all_violations(self) -> List[Dict[str, Any]]:
        """获取所有违规"""
        return self.violations
    
    def voice_independence_score(self) -> float:
        """
        计算声部独立性评分
        
        基于:
        1. 各声部运动方向的差异性（反向运动比例）
        2. 节奏密度的差异
        3. 音域重叠度（越低越好）
        4. 违规数量
        
        返回0-1分数，1表示完全独立。
        """
        scores = []
        
        # 1. 运动方向差异性
        directions = {}
        for lid, seat in self.seats.items():
            if seat.direction_history:
                directions[lid] = seat.get_average_direction(window=8)
        
        if len(directions) >= 2:
            dir_values = list(directions.values())
            dir_variance = np.var(dir_values)
            # 方向差异越大，独立性越高
            direction_score = min(1.0, dir_variance * 4)
            scores.append(direction_score)
        
        # 2. 节奏密度差异
        densities = []
        for lid, seat in self.seats.items():
            if seat.note_history:
                # 计算平均时值（越短密度越高）
                avg_dur = np.mean([n.duration for n in seat.note_history[-20:]])
                density = 1.0 / (avg_dur + 0.1)
                densities.append(density)
        
        if densities:
            density_variance = np.var(densities) / (np.mean(densities) ** 2 + 0.01)
            rhythm_score = min(1.0, density_variance * 2)
            scores.append(rhythm_score)
        
        # 3. 音域分离度
        ranges = []
        for lid, seat in self.seats.items():
            low, high = seat.get_pitch_range_used()
            if low is not None and high is not None:
                ranges.append((low, high))
        
        if len(ranges) >= 2:
            # 计算音域重叠
            overlaps = []
            for i in range(len(ranges)):
                for j in range(i + 1, len(ranges)):
                    r1, r2 = ranges[i], ranges[j]
                    overlap = max(0, min(r1[1], r2[1]) - max(r1[0], r2[0]))
                    total_range = max(r1[1], r2[1]) - min(r1[0], r2[0])
                    if total_range > 0:
                        overlaps.append(1 - overlap / total_range)
            if overlaps:
                range_score = np.mean(overlaps)
                scores.append(range_score)
        
        # 4. 违规惩罚
        if self.violations:
            total_severity = sum(v["severity"] for v in self.violations)
            violation_penalty = min(0.5, total_severity / 20)
            scores.append(1.0 - violation_penalty)
        
        if not scores:
            return 0.5
        
        return float(np.mean(scores))
    
    def get_counterpoint_richness(self) -> Dict[str, float]:
        """
        计算对位丰富度指标
        
        返回多个维度的丰富度评分。
        """
        # 1. 音程多样性
        all_intervals = []
        for seat in self.seats.values():
            all_intervals.extend(seat.get_melodic_intervals())
        
        if all_intervals:
            unique_intervals = len(set(int(i) % 12 for i in all_intervals))
            interval_richness = min(1.0, unique_intervals / 12.0)
        else:
            interval_richness = 0.0
        
        # 2. 协和度变化
        if self.harmony_history:
            consonance_values = [h["consonance_score"] for h in self.harmony_history]
            consonance_variance = np.var(consonance_values) / 4.0
        else:
            consonance_variance = 0.0
        
        # 3. 声部活跃数变化
        if self.harmony_history:
            active_counts = [h["n_active"] for h in self.harmony_history]
            activity_variance = np.var(active_counts) / 11.0
        else:
            activity_variance = 0.0
        
        # 4. 休止的艺术 (qgl的贡献)
        qgl_seat = self.seats.get("qgl")
        if qgl_seat:
            rest_ratio = qgl_seat.get_rest_ratio()
            silence_art = rest_ratio * 0.5  # 休止也是对位的贡献
        else:
            silence_art = 0.0
        
        return {
            "interval_richness": float(interval_richness),
            "consonance_variance": float(min(1.0, consonance_variance)),
            "activity_variance": float(min(1.0, activity_variance)),
            "silence_art": float(silence_art),
            "overall": float(np.mean([
                interval_richness, 
                min(1.0, consonance_variance),
                min(1.0, activity_variance),
                silence_art
            ]))
        }
    
    def get_seat_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取每个对位席的统计信息"""
        stats = {}
        for lid, seat in self.seats.items():
            intervals = seat.get_melodic_intervals()
            low, high = seat.get_pitch_range_used()
            stats[lid] = {
                "seat_name": seat.seat_name,
                "voice_type": seat.voice_type,
                "n_notes": len(seat.note_history),
                "n_rests": sum(1 for n in seat.note_history if n.is_rest()),
                "rest_ratio": seat.get_rest_ratio(),
                "pitch_low": low,
                "pitch_high": high,
                "avg_interval": float(np.mean(intervals)) if intervals else 0,
                "max_interval": max(intervals) if intervals else 0,
                "direction_changes": sum(1 for i in range(1, len(seat.direction_history))
                                          if seat.direction_history[i] != seat.direction_history[i-1])
                                      if len(seat.direction_history) > 1 else 0,
            }
        return stats
    
    def get_summary(self) -> Dict[str, Any]:
        """获取全席总结"""
        return {
            "n_seats": len(self.seats),
            "total_violations": len(self.violations),
            "parallel_fifths": len(self.detect_parallel_fifths()),
            "parallel_octaves": len(self.detect_parallel_octaves()),
            "unisons": len(self.detect_unison()),
            "independence_score": self.voice_independence_score(),
            "richness": self.get_counterpoint_richness(),
            "seat_stats": self.get_seat_statistics(),
            "total_time": self.time,
        }


class SeatRegistry:
    """
    对位席注册表 — 预定义11条线的配置
    
    每条线的配置包含声部类型、音域、节奏型、休止概率等。
    """
    
    _SEAT_CONFIGS = {
        "cisvr": {
            "seat_name": "对位席基准",
            "voice_type": "cantus_firmus",
            "interval_range": (0, 4),
            "rhythm_pattern": "gregorian",
            "rest_probability": 0.0,
            "priority": 10,
            "description": "固定旋律，全系统的参照基准。格里高利圣咏风格，全音符为主。"
        },
        "ucif2": {
            "seat_name": "合取形式化",
            "voice_type": "alto",
            "interval_range": (0, 5),
            "rhythm_pattern": "dorian_mode",
            "rest_probability": 0.05,
            "priority": 7,
            "description": "理性声部。逻辑合取∧的累积性体现为级进，Dorian调式。"
        },
        "lgt": {
            "seat_name": "自由意志与商像",
            "voice_type": "soprano",
            "interval_range": (0, 12),
            "rhythm_pattern": "irregular",
            "rest_probability": 0.10,
            "priority": 8,
            "description": "意志声部。不可预测性，突然跳进，自由决策的非决定性。"
        },
        "usrm": {
            "seat_name": "因果集与律吕",
            "voice_type": "tenor",
            "interval_range": (0, 7),
            "rhythm_pattern": "causal_temporal",
            "rest_probability": 0.08,
            "priority": 6,
            "description": "因果声部。偏序关系音高序列，十二律吕调性约束，五度相生。"
        },
        "cfts": {
            "seat_name": "F4机验",
            "voice_type": "tenor",
            "interval_range": (0, 8),
            "rhythm_pattern": "f4_symmetric",
            "rest_probability": 0.05,
            "priority": 7,
            "description": "验证声部。F4李代数根系统音程，高度对称，一致性检查修正。"
        },
        "qlv": {
            "seat_name": "谱重合观测量化",
            "voice_type": "alto",
            "interval_range": (0, 10),
            "rhythm_pattern": "spectral_quantized",
            "rest_probability": 0.08,
            "priority": 6,
            "description": "观测声部。FFT频谱映射，量子测量坍缩效应，频率避让。"
        },
        "vinf": {
            "seat_name": "张量网联邦图",
            "voice_type": "bass",
            "interval_range": (0, 9),
            "rhythm_pattern": "tensor_async",
            "rest_probability": 0.10,
            "priority": 5,
            "description": "网络声部。多线程交织，张量收缩节奏，联邦异步。"
        },
        "qgl": {
            "seat_name": "静默拍度量",
            "voice_type": "rest",
            "interval_range": (0, 12),
            "rhythm_pattern": "silent_beat",
            "rest_probability": 0.85,
            "priority": 4,
            "description": "休止声部。以沉默工作，关键拍点强音，断代检测，负空间艺术。"
        },
        "qfa": {
            "seat_name": "折纸三角剖分",
            "voice_type": "alto",
            "interval_range": (0, 6),
            "rhythm_pattern": "origami_fold",
            "rest_probability": 0.08,
            "priority": 5,
            "description": "几何声部。音高路径折叠，三角剖分节奏，山折谷折交替。"
        },
        "lvlu": {
            "seat_name": "层叠递归与视界",
            "voice_type": "tenor",
            "interval_range": (0, 8),
            "rhythm_pattern": "fractal_recursive",
            "rest_probability": 0.06,
            "priority": 6,
            "description": "层级声部。自相似fractal结构，递归深度音高分层，视界红移。"
        },
        "qtlv": {
            "seat_name": "量子拓扑局部变分",
            "voice_type": "soprano",
            "interval_range": (0, 7),
            "rhythm_pattern": "homology_class",
            "rest_probability": 0.07,
            "priority": 7,
            "description": "拓扑声部。同调群音高类，局部变分连续性，拓扑不变量。"
        },
    }
    
    @classmethod
    def get_seat(cls, line_id: str) -> Dict[str, Any]:
        """获取对位席配置"""
        if line_id not in cls._SEAT_CONFIGS:
            raise ValueError(f"Unknown line_id: {line_id}")
        return cls._SEAT_CONFIGS[line_id]
    
    @classmethod
    def get_voice_type(cls, line_id: str) -> str:
        """获取声部类型"""
        return cls.get_seat(line_id)["voice_type"]
    
    @classmethod
    def get_melody_theme(cls, line_id: str) -> MelodyTheme:
        """获取旋律主题实例"""
        return create_melody(line_id)
    
    @classmethod
    def get_all_configs(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有配置"""
        return cls._SEAT_CONFIGS.copy()
    
    @classmethod
    def get_line_ids(cls) -> List[str]:
        """获取所有线ID"""
        return list(cls._SEAT_CONFIGS.keys())


# ============================================================
# 实验验证函数
# ============================================================
"""
OMNI-HUB v11.0 — counterpoint_seats
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""

def run_counterpoint_experiment(n_beats: int = 100, 
                                 beat_resolution: float = 0.5) -> Dict[str, Any]:
    """
    运行对位实验
    
    生成n_beats拍的复调进行，收集所有数据。
    """
    logger.info("=" * 70)
    logger.info("OMNI-HUB v4.0 — 对位席架构实验")
    logger.info("核心命题: '和声不是齐唱，对位即显化'")
    logger.info("=" * 70)
    
    # 创建乐团
    orchestra = CounterpointOrchestra()
    
    logger.info(f"\n[初始化] 创建11个对位席:")
    for lid, seat in orchestra.seats.items():
        config = SeatRegistry.get_seat(lid)
        logger.info(f"  {lid}: {seat.seat_name} ({seat.voice_type}) — {config['description'][:40]}...")
    
    # 生成复调进行
    logger.info(f"\n[演奏] 生成 {n_beats} 拍复调进行 (分辨率: {beat_resolution}拍)")
    
    for beat in np.arange(0, n_beats, beat_resolution):
        orchestra.conduct(beat)
        
        if int(beat * 2) % 20 == 0:
            logger.info(f"  进度: {beat:.1f}/{n_beats} 拍", end="\r")
    
    logger.info(f"\n[完成] 生成完毕")
    
    # 收集结果
    summary = orchestra.get_summary()
    
    # 协和度矩阵
    mid_time = n_beats / 2
    matrix, line_ids = orchestra.get_consonance_matrix(mid_time)
    
    # 时间序列数据
    times = [h["time"] for h in orchestra.harmony_history]
    consonance_scores = [h["consonance_score"] for h in orchestra.harmony_history]
    active_counts = [h["n_active"] for h in orchestra.harmony_history]
    
    # qgl休止分析
    qgl_seat = orchestra.seats.get("qgl")
    qgl_rests = qgl_seat.get_rest_ratio() if qgl_seat else 0
    
    # 各声部音高时间序列
    pitch_tracks = {}
    for lid, seat in orchestra.seats.items():
        pitch_tracks[lid] = [
            n.pitch if not n.is_rest() else None 
            for n in seat.note_history
        ]
    
    return {
        "orchestra": orchestra,
        "summary": summary,
        "consonance_matrix": matrix,
        "line_ids": line_ids,
        "times": times,
        "consonance_scores": consonance_scores,
        "active_counts": active_counts,
        "qgl_rest_ratio": qgl_rests,
        "pitch_tracks": pitch_tracks,
        "violations": orchestra.violations,
        "n_beats": n_beats,
        "beat_resolution": beat_resolution,
    }


if __name__ == "__main__":
    results = run_counterpoint_experiment(n_beats=100, beat_resolution=0.5)
    print("\n" + "=" * 70)
    print("实验结果摘要")
    print("=" * 70)
    print(f"总违规数: {results['summary']['total_violations']}")
    print(f"  - 平行五度: {results['summary']['parallel_fifths']}")
    print(f"  - 平行八度: {results['summary']['parallel_octaves']}")
    print(f"  - 齐唱: {results['summary']['unisons']}")
    print(f"声部独立性评分: {results['summary']['independence_score']:.3f}")
    print(f"对位丰富度: {results['summary']['richness']['overall']:.3f}")
    print(f"qgl休止比例: {results['qgl_rest_ratio']:.3f}")
