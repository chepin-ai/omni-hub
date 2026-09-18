
__version__ = "11.0.0"
"""
OMNI-HUB v4.0 — Voice Melody Module
对位席声部旋律实现

11条独立声部的旋律主题，每条线对应一个对位席：
- cisvr: CantusFirmus (固定旋律)
- ucif2: ConjunctiveFormalization (合取形式化)
- lgt: FreeWill (自由意志)
- usrm: CausalSet (因果集与律吕)
- cfts: F4Verification (F4机验)
- qlv: SpectralObservation (谱重合观测)
- vinf: TensorNetwork (张量网联邦)
- qgl: SilentBeat (静默拍度量/休止声部)
- qfa: OrigamiTriangulation (折纸三角剖分)
- lvlu: LayeredRecursion (层叠递归)
- qtlv: QuantumTopology (量子拓扑)

对位法则：
1. 禁止平行五度/八度 → 禁止线间完全同步
2. 反向进行优先 → 线间差异化运动
3. 声部超越 → 高SI线可暂时低于低SI线
4. 协和音程分类 → 完美/不完全/不协和
5. 解决规则 → 张力→松弛趋向
6. 休止的艺术 → qgl的沉默是负空间
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging


class ConsonanceType(Enum):
    """协和度分类 — 从对位法映射到系统架构"""
    PERFECT_CONSONANCE = 3   # 完美协和: 纯一度、纯八度、纯五度 → 系统完全同步（禁止）
    IMPERFECT_CONSONANCE = 2  # 不完全协和: 大三度、小三度、大六度、小六度 → 允许的差异
    DISSONANCE = 1           # 不协和: 大二度、小二度、大七度、小七度、三全音、增减音程 → 必要张力
    REST = 0                 # 休止: qgl的沉默


@dataclass
class NoteEvent:
    """音符事件 — 声部的显化单元"""
    pitch: Optional[int]      # MIDI音高 (0-127), None表示休止
    velocity: int             # 力度 0-127
    duration: float           # 时值 (拍)
    onset: float              # 起始时刻
    line_id: str = ""         # 所属线
    seat_name: str = ""       # 对位席名称
    consonance: ConsonanceType = ConsonanceType.DISSONANCE
    
    def is_rest(self) -> bool:
        return self.pitch is None
    
    def get_pitch_class(self) -> Optional[int]:
        if self.pitch is None:
            return None
        return self.pitch % 12
    
    def get_octave(self) -> Optional[int]:
        if self.pitch is None:
            return None
        return self.pitch // 12


class MelodyTheme(ABC):
    """旋律主题基类 — 对位席的"固定旋律"(cantus firmus)抽象"""
    
    def __init__(self, line_id: str, seat_name: str,
                 pitch_range: Tuple[int, int] = (48, 84),
                 rhythm_density: float = 0.7,
                 rest_probability: float = 0.0):
        self.line_id = line_id
        self.seat_name = seat_name
        self.pitch_range = pitch_range
        self.rhythm_density = rhythm_density
        self.rest_probability = rest_probability
        self.state: Dict[str, Any] = {}
        self.history: List[NoteEvent] = []
        self.rng = np.random.RandomState(hash(line_id) % 2**31)
        
    @abstractmethod
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        """在时刻t生成音符事件"""
        pass
    
    def get_interval(self, note1: NoteEvent, note2: NoteEvent) -> Optional[int]:
        """计算两个音符的音程（半音数）"""
        if note1.is_rest() or note2.is_rest():
            return None
        return abs(note2.pitch - note1.pitch)
    
    def classify_consonance(self, interval: int) -> ConsonanceType:
        """分类协和度"""
        interval_class = interval % 12
        perfect = {0, 7}  # 纯一度/纯八度, 纯五度
        imperfect = {3, 4, 8, 9}  # 小三度, 大三度, 小六度, 大六度
        if interval_class in perfect:
            return ConsonanceType.PERFECT_CONSONANCE
        elif interval_class in imperfect:
            return ConsonanceType.IMPERFECT_CONSONANCE
        else:
            return ConsonanceType.DISSONANCE
    
    def _clamp_pitch(self, pitch: int) -> int:
        return max(self.pitch_range[0], min(self.pitch_range[1], pitch))
    
    def _maybe_rest(self, t: float) -> bool:
        if self.rest_probability <= 0:
            return False
        # qgl在关键拍点（强拍）降低休止概率
        beat_in_bar = t % 4.0
        is_strong_beat = beat_in_bar < 0.5
        effective_prob = self.rest_probability * (0.3 if is_strong_beat else 1.0)
        return self.rng.random() < effective_prob


class CantusFirmusMelody(MelodyTheme):
    """
    cisvr — 固定旋律 (Cantus Firmus)
    对位席基准，全系统的参照基准
    特点: 简单、平稳、全音符为主，极少跳进
    """
    
    def __init__(self):
        super().__init__(
            line_id="cisvr",
            seat_name="对位席基准",
            pitch_range=(55, 72),  # G3-C5
            rhythm_density=0.3,
            rest_probability=0.0
        )
        # 预定义固定旋律 — 格里高利圣咏风格
        self.cantus_notes = [60, 62, 64, 65, 64, 62, 60, 58, 60, 62, 64, 65, 67, 65, 64, 62,
                             60, 62, 64, 60, 58, 57, 55, 57, 58, 60, 62, 60, 58, 60,
                             64, 62, 60, 58, 57, 58, 60, 62, 64, 65, 67, 69, 67, 65, 64, 62, 60]
        self.durations = [2.0, 1.0, 1.0, 2.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0,
                         2.0, 1.0, 2.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 2.0,
                         1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 2.0]
        self._build_schedule()
        
    def _build_schedule(self):
        self.schedule = []
        t = 0.0
        for i, (p, d) in enumerate(zip(self.cantus_notes, self.durations)):
            self.schedule.append((t, p, d))
            t += d
        self.total_length = t
        
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        t_mod = t % self.total_length
        # 找到当前时刻对应的音符
        current = None
        for onset, pitch, dur in self.schedule:
            if onset <= t_mod < onset + dur:
                current = (onset, pitch, dur)
                break
        if current is None:
            current = self.schedule[-1]
        onset, pitch, dur = current
        return NoteEvent(
            pitch=pitch,
            velocity=80,
            duration=dur,
            onset=t,
            line_id=self.line_id,
            seat_name=self.seat_name,
            consonance=ConsonanceType.PERFECT_CONSONANCE
        )


class ConjunctiveFormalizationMelody(MelodyTheme):
    """
    ucif2 — 合取形式化 (Conjunctive Formalization)
    理性声部: 逻辑合取∧、形式化推理、证明生成
    特点: 级进为主（合取的累积性），小跳进，类似古希腊调式(Dorian/Phrygian)
    """
    
    def __init__(self):
        super().__init__(
            line_id="ucif2",
            seat_name="合取形式化",
            pitch_range=(60, 79),  # C4-G5
            rhythm_density=0.6,
            rest_probability=0.05
        )
        # Dorian调式音阶: D-E-F-G-A-B-C (以D为 tonic)
        self.mode = [2, 1, 2, 2, 2, 1, 2]  # 全半音程模式
        self.tonic = 62  # D4
        self._build_scale()
        self.prev_pitch = 64  # E4 - distinct from cantus firmus
        
    def _build_scale(self):
        self.scale = [self.tonic]
        p = self.tonic
        for step in self.mode:
            p += step
            if p <= self.pitch_range[1]:
                self.scale.append(p)
        # 向下扩展
        p = self.tonic
        for step in reversed(self.mode):
            p -= step
            if p >= self.pitch_range[0]:
                self.scale.insert(0, p)
        self.scale = sorted(set(self.scale))
        
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        if self._maybe_rest(t):
            return NoteEvent(None, 0, 1.0, t, self.line_id, self.seat_name, ConsonanceType.REST)
        
        # 合取累积: 以小步级进为主，偶尔三度跳进（合取引入）
        current_idx = self.scale.index(min(self.scale, key=lambda x: abs(x - self.prev_pitch)))
        
        # 逻辑深度影响音高方向
        logic_depth = context.get("logic_depth", 0)
        direction = np.sign(logic_depth - 3) if logic_depth > 0 else self.rng.choice([-1, 0, 1])
        
        step_weights = [0.5, 0.3, 0.15, 0.05]  # 级进, 三度, 四度, 五度+
        step_size = self.rng.choice([1, 2, 3, 4], p=step_weights)
        
        new_idx = self._clamp_index(current_idx + direction * step_size)
        pitch = self.scale[new_idx]
        
        # 节奏: 形式化证明的节奏——严谨但非机械
        dur = self.rng.choice([0.5, 1.0, 1.5, 2.0], p=[0.3, 0.4, 0.2, 0.1])
        vel = int(70 + 20 * np.sin(t * 0.5))
        
        self.prev_pitch = pitch
        interval = abs(pitch - self.prev_pitch) if self.history else 0
        cons = self.classify_consonance(interval) if self.history else ConsonanceType.PERFECT_CONSONANCE
        
        return NoteEvent(pitch, vel, dur, t, self.line_id, self.seat_name, cons)
    
    def _clamp_index(self, idx: int) -> int:
        return max(0, min(len(self.scale) - 1, idx))


class FreeWillMelody(MelodyTheme):
    """
    lgt — 自由意志与商像 (Free Will & Commercial Image)
    意志声部: 自由决策、商业形象、选择分支
    特点: 不可预测性，突然跳进，节奏不规则，体现自由意志的"非决定性"
    """
    
    def __init__(self):
        super().__init__(
            line_id="lgt",
            seat_name="自由意志与商像",
            pitch_range=(64, 88),  # E4-E6
            rhythm_density=0.85,
            rest_probability=0.1
        )
        self.prev_pitch = 67  # G4 - distinct starting point
        self.choice_history = []
        
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        if self._maybe_rest(t):
            return NoteEvent(None, 0, 0.5, t, self.line_id, self.seat_name, ConsonanceType.REST)
        
        # 自由意志: 决策分支模拟
        n_branches = context.get("branches", 3)
        will_strength = context.get("will_strength", 0.5)
        
        # 突然跳进 — 自由意志的不可预测性
        jump_probability = 0.35 * will_strength
        if self.rng.random() < jump_probability:
            # 大跳进: 五度、六度、七度、八度
            jump = self.rng.choice([7, 8, 9, 10, 11, 12]) * self.rng.choice([-1, 1])
        else:
            # 小步或保持
            jump = self.rng.choice([-2, -1, 0, 1, 2])
        
        pitch = self._clamp_pitch(self.prev_pitch + jump)
        
        # 商业形象: 节奏的不规则性——"品牌节奏"
        brand_pulse = context.get("brand_pulse", 0.5)
        dur = self.rng.exponential(0.8) * (1 + brand_pulse)
        dur = max(0.25, min(3.0, dur))
        
        # 力度: 意志的强度
        vel = int(60 + 50 * will_strength + 20 * self.rng.random())
        vel = min(127, vel)
        
        self.prev_pitch = pitch
        interval = abs(jump)
        cons = self.classify_consonance(interval) if interval > 0 else ConsonanceType.PERFECT_CONSONANCE
        
        return NoteEvent(pitch, vel, dur, t, self.line_id, self.seat_name, cons)


class CausalSetMelody(MelodyTheme):
    """
    usrm — 因果集与律吕 (Causal Sets & Musical Temperament)
    因果声部: 因果集合、音律调性(十二律吕)、因果推断
    特点: 基于偏序关系的音高序列，有律吕调性约束
    """
    
    def __init__(self):
        super().__init__(
            line_id="usrm",
            seat_name="因果集与律吕",
            pitch_range=(52, 76),  # E3-E5
            rhythm_density=0.5,
            rest_probability=0.08
        )
        # 十二律吕 — 传统中国音乐律制
        # 黄钟(C), 大吕(C#), 太簇(D), 夹钟(D#), 姑洗(E), 仲吕(F),
        # 蕤宾(F#), 林钟(G), 夷则(G#), 南吕(A), 无射(A#), 应钟(B)
        self.lulv = ["黄钟", "大吕", "太簇", "夹钟", "姑洗", "仲吕",
                     "蕤宾", "林钟", "夷则", "南吕", "无射", "应钟"]
        # 五度相生律的纯五度链
        self.fifth_chain = self._build_fifth_chain()
        self.causal_chain = []
        self.prev_pitch = 55  # G3 - lower register
        
    def _build_fifth_chain(self) -> List[int]:
        """构建五度链: 从C出发，向上/向下纯五度"""
        chain = [60]  # C4
        # 向上五度
        p = 60
        for _ in range(6):
            p = (p + 7) % 12 + 60  # 保持在同一八度附近
            chain.append(p)
        # 向下五度
        p = 60
        for _ in range(6):
            p = (p - 7) % 12 + 60
            chain.insert(0, p)
        return sorted(set(chain))
    
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        if self._maybe_rest(t):
            return NoteEvent(None, 0, 1.0, t, self.line_id, self.seat_name, ConsonanceType.REST)
        
        # 因果推断: 基于历史音符的"因"推"果"
        if len(self.history) >= 2:
            # 检测因果模式: 前一音符对当前的影响
            h1, h2 = self.history[-1], self.history[-2]
            if h1.pitch is not None and h2.pitch is not None:
                prev_interval = h1.pitch - h2.pitch
            else:
                prev_interval = 0
            # 因果传递: 音程的"因果衰减"
            causal_decay = 0.7
            predicted_jump = int(prev_interval * causal_decay + self.rng.normal(0, 2))
        else:
            predicted_jump = self.rng.choice([-2, -1, 0, 1, 2])
        
        # 律吕约束: 倾向于律吕音
        target = self._clamp_pitch(self.prev_pitch + predicted_jump)
        # 找到最近的律吕音
        lulv_pitches = [60 + i for i in range(12)]  # 简化: 十二平均律映射
        nearest_lulv = min(lulv_pitches, key=lambda x: abs(x - target))
        
        # 80%概率遵循律吕，20%偏离（偏音/变化音）
        if self.rng.random() < 0.8:
            pitch = nearest_lulv
        else:
            pitch = target
        
        pitch = self._clamp_pitch(pitch)
        
        # 律吕节奏: 符合自然因果律的时值
        dur = self.rng.choice([1.0, 1.5, 2.0, 3.0], p=[0.3, 0.3, 0.25, 0.15])
        vel = int(65 + 15 * np.sin(t * 0.3))
        
        interval = abs(pitch - self.prev_pitch)
        cons = self.classify_consonance(interval)
        self.prev_pitch = pitch
        
        return NoteEvent(pitch, vel, dur, t, self.line_id, self.seat_name, cons)


class F4VerificationMelody(MelodyTheme):
    """
    cfts — F4机验 (F4 Machine Verification)
    验证声部: F4李代数的根系统、机器验证、一致性检查
    特点: 基于F4根系统的音程，具有高度的对称性和结构性
    """
    
    def __init__(self):
        super().__init__(
            line_id="cfts",
            seat_name="F4机验",
            pitch_range=(48, 74),  # C3-D5
            rhythm_density=0.55,
            rest_probability=0.05
        )
        # F4李代数的根系统 — 48个根
        # 简化: 使用F4的 prominent 音程结构
        # F4的根包含在 D4, D5 等结构中，有特殊的对称性
        self.f4_intervals = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]  # 半音
        # F4特有的长根/短根比例
        self.long_roots = [2, 4, 6, 8, 10]   # 长根对应偶数音程
        self.short_roots = [1, 3, 5, 7, 9, 11]  # 短根对应奇数音程
        self.prev_pitch = 53  # F3 - distinct bass register
        
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        if self._maybe_rest(t):
            return NoteEvent(None, 0, 1.0, t, self.line_id, self.seat_name, ConsonanceType.REST)
        
        # 验证状态影响旋律
        verification_level = context.get("verification_level", 0.5)
        
        # F4结构: 交替使用长根和短根音程
        if int(t) % 2 == 0:
            # 偶数拍: 长根音程（更稳定）
            interval = self.rng.choice(self.long_roots)
        else:
            # 奇数拍: 短根音程（更活跃）
            interval = self.rng.choice(self.short_roots)
        
        direction = self.rng.choice([-1, 1])
        pitch = self._clamp_pitch(self.prev_pitch + direction * interval)
        
        # 一致性检查: 如果与cantus firmus形成不协和，调整
        cf_pitch = context.get("cantus_firmus_pitch")
        if cf_pitch is not None:
            diff = abs(pitch - cf_pitch) % 12
            if diff in {1, 2, 6, 10, 11}:  # 不协和
                # 验证失败修正
                pitch = self._clamp_pitch(pitch + self.rng.choice([-1, 1]))
        
        # F4节奏: 机器验证的精确性
        dur = self.rng.choice([0.5, 1.0, 1.0, 2.0], p=[0.2, 0.4, 0.3, 0.1])
        vel = int(60 + 40 * verification_level)
        
        interval = abs(pitch - self.prev_pitch)
        cons = self.classify_consonance(interval)
        self.prev_pitch = pitch
        
        return NoteEvent(pitch, vel, dur, t, self.line_id, self.seat_name, cons)


class SpectralObservationMelody(MelodyTheme):
    """
    qlv — 谱重合观测量化 (Spectral Overlap Observation Quantization)
    观测声部: 谱分析、观测算符、量子测量
    特点: 基于FFT频谱的音高映射，观测导致的状态坍缩效应
    """
    
    def __init__(self):
        super().__init__(
            line_id="qlv",
            seat_name="谱重合观测",
            pitch_range=(65, 91),  # F4-F6
            rhythm_density=0.75,
            rest_probability=0.08
        )
        self.prev_pitch = 77  # F5 - high register for spectral observation
        self.spectral_buffer = []
        
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        if self._maybe_rest(t):
            return NoteEvent(None, 0, 0.5, t, self.line_id, self.seat_name, ConsonanceType.REST)
        
        # 模拟频谱分析: 生成伪FFT数据
        n_bins = 16
        fft_data = np.abs(np.fft.fft(np.random.randn(n_bins) * 
                                      np.sin(t * np.pi * 0.1) *
                                      np.exp(-t * 0.01)))
        
        # 频谱峰值映射到音高
        peak_idx = np.argmax(fft_data)
        # 将频谱bin映射到MIDI音高范围
        normalized_peak = peak_idx / n_bins
        target_pitch = int(self.pitch_range[0] + normalized_peak * 
                          (self.pitch_range[1] - self.pitch_range[0]))
        
        # 量子测量效应: 观测导致坍缩 — 音高离散化
        quantization_levels = context.get("quantization_levels", 12)
        quantized_pitch = self._quantize_pitch(target_pitch, quantization_levels)
        
        # 谱重合: 与其他声部的谱重叠检测
        other_pitches = context.get("other_pitches", [])
        if other_pitches:
            overlap = self._spectral_overlap(quantized_pitch, other_pitches)
            if overlap > 0.5:
                # 高重合度: 频率避让（量子不相容）
                quantized_pitch = self._clamp_pitch(quantized_pitch + 
                                                    self.rng.choice([-3, 3]))
        
        pitch = self._clamp_pitch(quantized_pitch)
        
        # 观测精度影响时值
        observation_precision = context.get("observation_precision", 0.7)
        dur = 0.5 / observation_precision * self.rng.uniform(0.5, 1.5)
        dur = max(0.25, min(2.0, dur))
        
        vel = int(50 + 40 * (fft_data[peak_idx] / (np.max(fft_data) + 1e-8)))
        
        interval = abs(pitch - self.prev_pitch)
        cons = self.classify_consonance(interval)
        self.prev_pitch = pitch
        
        return NoteEvent(pitch, vel, dur, t, self.line_id, self.seat_name, cons)
    
    def _quantize_pitch(self, pitch: int, levels: int) -> int:
        """将连续音高量子化到离散水平"""
        octave = pitch // 12
        pc = pitch % 12
        quantized_pc = round(pc / (12 / levels)) * (12 / levels)
        return int(octave * 12 + quantized_pc)
    
    def _spectral_overlap(self, pitch: int, other_pitches: List[int]) -> float:
        """计算谱重合度"""
        if not other_pitches:
            return 0.0
        overlaps = []
        for op in other_pitches:
            diff = abs(pitch - op)
            # 谐波重合检测
            if diff == 0:
                overlaps.append(1.0)
            elif diff in {12, 7, 5, 4, 3}:
                overlaps.append(0.5)
            else:
                overlaps.append(0.0)
        return np.mean(overlaps)


class TensorNetworkMelody(MelodyTheme):
    """
    vinf — 张量网联邦图 (Tensor Network Federation Graph)
    网络声部: 张量网络、联邦学习图、分布式拓扑
    特点: 多线程交织，张量收缩的节奏，网络拓扑的音高图
    """
    
    def __init__(self):
        super().__init__(
            line_id="vinf",
            seat_name="张量网联邦图",
            pitch_range=(50, 78),  # D3-F#5
            rhythm_density=0.8,
            rest_probability=0.1
        )
        self.prev_pitch = 50  # D3 - low network register
        self.tensor_dims = [2, 3, 4]  # 张量维度
        self.contraction_history = []
        
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        if self._maybe_rest(t):
            return NoteEvent(None, 0, 0.5, t, self.line_id, self.seat_name, ConsonanceType.REST)
        
        # 联邦节点数影响音高密度
        n_nodes = context.get("federation_nodes", 4)
        
        # 张量收缩: 多个维度同时变化
        # 模拟张量网络的纠缠结构
        contractions = []
        for dim in self.tensor_dims[:n_nodes]:
            # 每个维度产生一个音高偏移
            offset = self.rng.choice([-dim, 0, dim])
            contractions.append(offset)
        
        # 收缩结果: 加权求和
        total_offset = int(np.sum(contractions) * 0.5)
        pitch = self._clamp_pitch(self.prev_pitch + total_offset)
        
        # 网络拓扑: 图结构的音高映射
        topology = context.get("topology", "ring")
        if topology == "ring":
            # 环形: 周期性音高模式
            pitch = self._clamp_pitch(60 + int(12 * np.sin(t * 0.2)))
        elif topology == "star":
            # 星形: 中心-外围跳跃
            if self.rng.random() < 0.3:
                pitch = self._clamp_pitch(60 + self.rng.choice([-12, 0, 12]))
        elif topology == "mesh":
            # 网格: 二维音高平面
            row = int(t / 4) % 4
            col = int(t) % 4
            pitch = self._clamp_pitch(60 + row * 3 + col * 2)
        
        # 联邦学习的异步节奏
        async_delay = self.rng.exponential(0.3)
        dur = max(0.25, 1.0 - async_delay)
        
        vel = int(55 + 30 * (n_nodes / 8))
        
        interval = abs(pitch - self.prev_pitch)
        cons = self.classify_consonance(interval)
        self.prev_pitch = pitch
        
        return NoteEvent(pitch, vel, dur, t, self.line_id, self.seat_name, cons)


class SilentBeatMelody(MelodyTheme):
    """
    qgl — 静默拍度量 (Silent Beat Metrics)
    休止声部: **沉默**、断代检测、拍度量、休止的艺术
    
    核心设计: 不是"不工作"，而是"以沉默工作"。
    在关键拍点（如小节强拍）出现音符，其余时间休止。
    沉默是对位中的负空间。
    """
    
    def __init__(self):
        super().__init__(
            line_id="qgl",
            seat_name="静默拍度量",
            pitch_range=(36, 60),  # C2-C4 低音区，沉默的根基
            rhythm_density=0.1,    # 极低的节奏密度
            rest_probability=0.85  # 85%休止概率 — 最高的休止率
        )
        self.prev_pitch = 36  # C2 - deep silence foundation
        self.silence_count = 0
        self.attack_count = 0
        
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        # 判断是否为关键拍点
        beat_in_bar = t % 4.0
        bar_number = int(t // 4)
        is_strong_beat = beat_in_bar < 0.5
        is_downbeat = abs(beat_in_bar) < 0.1
        
        # 断代检测: 在特定代数边界出现
        generation_boundary = context.get("generation", 0)
        at_boundary = (bar_number % 8 == 0) and is_downbeat
        
        # 休止决策
        should_rest = True
        
        if at_boundary:
            # 代数边界: 必须出现（断代标记）
            should_rest = False
        elif is_strong_beat and self.rng.random() < 0.3:
            # 强拍: 30%概率出现
            should_rest = False
        elif self.silence_count > 12:
            # 长时间沉默后的必然出现（避免永久沉默）
            should_rest = False
        elif self.rng.random() < self.rest_probability:
            # 基础休止概率
            should_rest = True
        else:
            should_rest = False
        
        if should_rest:
            self.silence_count += 1
            # 休止的时值: 沉默的长度
            rest_dur = self.rng.choice([1.0, 1.5, 2.0, 3.0, 4.0],
                                        p=[0.3, 0.25, 0.2, 0.15, 0.1])
            return NoteEvent(None, 0, rest_dur, t, self.line_id, self.seat_name,
                           ConsonanceType.REST)
        
        # 出现: 强音，低音，短促有力
        self.silence_count = 0
        self.attack_count += 1
        
        # 关键拍点的音高: 基于代数递推
        if at_boundary:
            pitch = self._clamp_pitch(36 + (generation_boundary % 3) * 12)
        else:
            pitch = self._clamp_pitch(self.prev_pitch + self.rng.choice([-5, 0, 5]))
        
        dur = self.rng.choice([0.5, 1.0, 1.5], p=[0.5, 0.3, 0.2])
        vel = int(90 + 30 * self.rng.random())  # 强力度
        
        interval = abs(pitch - self.prev_pitch)
        cons = self.classify_consonance(interval)
        self.prev_pitch = pitch
        
        return NoteEvent(pitch, vel, dur, t, self.line_id, self.seat_name, cons)
    
    def get_silence_ratio(self) -> float:
        """计算休止比例 — qgl的核心度量"""
        if not self.history:
            return 1.0
        rests = sum(1 for n in self.history if n.is_rest())
        return rests / len(self.history)


class OrigamiTriangulationMelody(MelodyTheme):
    """
    qfa — 折纸三角剖分 (Origami Triangulation)
    几何声部: 折纸几何、三角剖分、曲面折叠
    特点: 音高路径呈折叠状，三角剖分节奏，"山折"与"谷折"
    """
    
    def __init__(self):
        super().__init__(
            line_id="qfa",
            seat_name="折纸三角剖分",
            pitch_range=(58, 82),  # A#3-A5
            rhythm_density=0.65,
            rest_probability=0.08
        )
        self.prev_pitch = 70  # Bb4 - distinct for origami
        self.fold_state = 1   # 1=山折(向上), -1=谷折(向下)
        self.triangulation = []
        
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        if self._maybe_rest(t):
            return NoteEvent(None, 0, 0.5, t, self.line_id, self.seat_name, ConsonanceType.REST)
        
        # 折纸折叠: 音高路径的"折叠"
        fold_angle = context.get("fold_angle", 45.0)  # 折叠角度
        
        # 三角剖分: 将时间分割为三角形单元
        tri_unit = 3.0  # 三角形单元的时值
        position_in_tri = (t % tri_unit) / tri_unit
        
        if position_in_tri < 0.33:
            # 三角形第一条边: 稳定
            direction = 0
        elif position_in_tri < 0.67:
            # 三角形第二条边: 折叠（方向改变）
            direction = self.fold_state
            # 山折/谷折交替
            self.fold_state *= -1
        else:
            # 三角形第三条边: 回到起点附近
            direction = -self.fold_state * 0.5
        
        # 折叠幅度与角度成正比
        fold_magnitude = max(1, int(fold_angle / 15))
        jump = direction * fold_magnitude
        
        pitch = self._clamp_pitch(self.prev_pitch + jump)
        
        # 曲面曲率影响时值
        curvature = context.get("curvature", 0.0)
        dur = max(0.25, 1.0 - abs(curvature))
        
        vel = int(60 + 20 * abs(direction))
        
        interval = abs(pitch - self.prev_pitch)
        cons = self.classify_consonance(interval)
        self.prev_pitch = pitch
        
        return NoteEvent(pitch, vel, dur, t, self.line_id, self.seat_name, cons)


class LayeredRecursionMelody(MelodyTheme):
    """
    lvlu — 层叠递归与视界 (Layered Recursion & Horizon)
    层级声部: 层级递归、视界边界、自指层级
    特点: 自相似的 fractal 结构，不同递归深度的音高分层
    """
    
    def __init__(self):
        super().__init__(
            line_id="lvlu",
            seat_name="层叠递归与视界",
            pitch_range=(53, 81),  # F3-A5
            rhythm_density=0.7,
            rest_probability=0.06
        )
        self.prev_pitch = 58  # Bb3 - distinct recursive base
        self.recursion_depth = 0
        self.fractal_cache = {}
        
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        if self._maybe_rest(t):
            return NoteEvent(None, 0, 1.0, t, self.line_id, self.seat_name, ConsonanceType.REST)
        
        # 递归深度: 随时间周期性变化
        max_depth = context.get("max_recursion_depth", 4)
        self.recursion_depth = int(t / 8) % (max_depth + 1)
        
        # 自相似旋律: 不同深度的缩放版本
        base_pattern = [0, 2, 4, 2, 0, -1, 0, 2]  # 基础模式
        
        # 根据递归深度缩放
        scale_factor = 2 ** self.recursion_depth
        pattern_idx = int(t * scale_factor) % len(base_pattern)
        jump = base_pattern[pattern_idx]
        
        # 视界边界: 递归深度限制音高范围
        effective_range = (
            self.pitch_range[0],
            min(self.pitch_range[1], 
                self.pitch_range[0] + 12 * (max_depth + 1 - self.recursion_depth))
        )
        
        pitch = self._clamp_pitch(self.prev_pitch + jump)
        pitch = max(effective_range[0], min(effective_range[1], pitch))
        
        # 递归节奏: 深度越深，时值越短（信息密度越高）
        dur = max(0.25, 2.0 / (self.recursion_depth + 1))
        
        # 视界红移: 越深的递归，力度越弱（信息衰减）
        vel = int(80 - 10 * self.recursion_depth)
        
        interval = abs(pitch - self.prev_pitch)
        cons = self.classify_consonance(interval)
        self.prev_pitch = pitch
        
        return NoteEvent(pitch, vel, dur, t, self.line_id, self.seat_name, cons)


class QuantumTopologyMelody(MelodyTheme):
    """
    qtlv — 量子拓扑局部变分 (Quantum Topology Local Variation)
    拓扑声部: 量子拓扑、局部变分、同调群
    特点: 基于同调群的音高类，局部变分的连续性，拓扑不变量
    """
    
    def __init__(self):
        super().__init__(
            line_id="qtlv",
            seat_name="量子拓扑局部变分",
            pitch_range=(61, 87),  # C#4-D#6
            rhythm_density=0.72,
            rest_probability=0.07
        )
        self.prev_pitch = 84  # C6 - high topology register
        # 同调群 H_0, H_1, H_2 对应的音高类
        self.homology_classes = {
            0: [60, 64, 67],   # H_0: 连通分支（大三和弦）
            1: [62, 65, 69],   # H_1: 环路（小三和弦）
            2: [61, 66, 70],   # H_2: 空洞（增三和弦）
        }
        self.current_homology = 0
        
    def generate(self, t: float, context: Dict[str, Any]) -> NoteEvent:
        if self._maybe_rest(t):
            return NoteEvent(None, 0, 0.5, t, self.line_id, self.seat_name, ConsonanceType.REST)
        
        # 局部变分: 连续性约束
        variation = context.get("local_variation", 0.5)
        
        # 同调群切换: 拓扑不变量变化
        if self.rng.random() < 0.1:
            self.current_homology = self.rng.choice(list(self.homology_classes.keys()))
        
        homology_class = self.homology_classes[self.current_homology]
        
        # 在当前的同调类中选择最近的音高
        nearest = min(homology_class, key=lambda x: abs(x - self.prev_pitch))
        
        # 局部变分: 在拓扑不变量约束下的微小变化
        local_shift = int(self.rng.normal(0, variation * 2))
        pitch = self._clamp_pitch(nearest + local_shift)
        
        # 确保仍在某个同调类中（模12等价）
        pitch_class = pitch % 12
        if pitch_class not in {n % 12 for n in homology_class}:
            # 调整到最近的同调类音
            target_classes = [n % 12 for n in homology_class]
            nearest_class = min(target_classes, key=lambda x: min(abs(x - pitch_class), 
                                                                  abs(x - pitch_class + 12)))
            pitch = (pitch // 12) * 12 + nearest_class
        
        pitch = self._clamp_pitch(pitch)
        
        # 拓扑变换的时值: 不变量保持时长，变分时短促
        if pitch % 12 in {n % 12 for n in homology_class}:
            dur = self.rng.choice([1.0, 1.5, 2.0])
        else:
            dur = self.rng.choice([0.25, 0.5])
        
        vel = int(60 + 25 * variation)
        
        interval = abs(pitch - self.prev_pitch)
        cons = self.classify_consonance(interval)
        self.prev_pitch = pitch
        
        return NoteEvent(pitch, vel, dur, t, self.line_id, self.seat_name, cons)


# 旋律工厂
"""
OMNI-HUB v11.0 — voice_melody
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""
MELODY_REGISTRY = {
    "cisvr": CantusFirmusMelody,
    "ucif2": ConjunctiveFormalizationMelody,
    "lgt": FreeWillMelody,
    "usrm": CausalSetMelody,
    "cfts": F4VerificationMelody,
    "qlv": SpectralObservationMelody,
    "vinf": TensorNetworkMelody,
    "qgl": SilentBeatMelody,
    "qfa": OrigamiTriangulationMelody,
    "lvlu": LayeredRecursionMelody,
    "qtlv": QuantumTopologyMelody,
}


def create_melody(line_id: str) -> MelodyTheme:
    """工厂函数: 根据线ID创建对应旋律主题"""
    if line_id not in MELODY_REGISTRY:
        raise ValueError(f"Unknown line_id: {line_id}")
    return MELODY_REGISTRY[line_id]()


def get_all_melodies() -> Dict[str, MelodyTheme]:
    """获取所有11条线的旋律主题实例"""
    return {lid: factory() for lid, factory in MELODY_REGISTRY.items()}
