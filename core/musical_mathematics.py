#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v8.0 — Musical Mathematics Engine
============================================
音乐数学引擎：十二平均律 vs 十二律吕 意识共振映射

本模块实现音乐数学的核心架构，包括：
- 十二平均律（Twelve-Tone Equal Temperament）
- 十二律吕（Twelve Lu-Lü，三分损益法）
- 和声共振↔意识共振映射（Consonance↔Consciousness）
- 对位引擎增强（Counterpoint Engine Enhanced，11声部）
- 赋格结构（Fugue Structure）
- 切分节奏事件（Syncopation Pattern）

数学基础：
- 十二平均律频率比：r = 2^(1/12) ≈ 1.059463
- 三分损益法：损一 × 2/3（上生五度），益一 × 4/3（下生四度）
- 黄金比例 φ = (1+√5)/2 ≈ 1.618 与律吕数列的深层关联
- 自然对数底 e ≈ 2.718 与频率增长的对应关系

作者: OMNI-HUB v8.0 核心架构师
涌现指数: 996.64
"""

import math
import random
import numpy as np
from typing import List, Tuple, Dict, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging

# =============================================================================
# 全局常量
# =============================================================================

# 黄金比例
PHI = (1 + math.sqrt(5)) / 2  # ≈ 1.618033988749895

# 自然对数底
E = math.e  # ≈ 2.718281828459045

# 十二平均律频率比
TWELFTH_ROOT_OF_TWO = 2 ** (1 / 12)  # ≈ 1.0594630943592953

# 标准音高
A4_FREQUENCY = 440.0  # Hz

# 基准音 C4 频率（用于律吕计算）
C4_FREQUENCY = 261.6255653005986  # Hz

# 音符名称（十二平均律）
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# 律吕名称（中国传统）
LULU_NAMES = [
    '黄钟', '大吕', '太簇', '夹钟', '姑洗', '仲吕',
    '蕤宾', '林钟', '夷则', '南吕', '无射', '应钟'
]

# 音程名称与比例
INTERVAL_RATIOS = {
    'unison': (1, 1),        # 纯一度
    'minor_second': (16, 15), # 小二度
    'major_second': (9, 8),   # 大二度
    'minor_third': (6, 5),    # 小三度
    'major_third': (5, 4),    # 大三度
    'perfect_fourth': (4, 3), # 纯四度
    'tritone': (45, 32),      # 三全音
    'perfect_fifth': (3, 2),  # 纯五度
    'minor_sixth': (8, 5),    # 小六度
    'major_sixth': (5, 3),    # 大六度
    'minor_seventh': (9, 5),  # 小七度
    'major_seventh': (15, 8), # 大七度
    'octave': (2, 1),         # 纯八度
}

# 协和度评分（0-1，基于just intonation的纯度）
CONSONANCE_SCORES = {
    'unison': 1.00,
    'octave': 1.00,
    'perfect_fifth': 0.95,
    'perfect_fourth': 0.92,
    'major_third': 0.88,
    'minor_sixth': 0.85,
    'minor_third': 0.82,
    'major_sixth': 0.80,
    'major_second': 0.55,
    'minor_seventh': 0.50,
    'major_seventh': 0.45,
    'minor_second': 0.30,
    'tritone': 0.20,
}


# =============================================================================
# 数据类定义
# =============================================================================

@dataclass
class Note:
    """音符数据类"""
    name: str
    octave: int
    frequency: float
    midi_number: int

    def __repr__(self) -> str:
        return f"Note({self.name}{self.octave}, {self.frequency:.2f}Hz, midi={self.midi_number})"


@dataclass
class Event:
    """音乐事件数据类"""
    time: float
    duration: float
    note: Optional[Note] = None
    velocity: float = 1.0
    line_id: int = 0

    def __repr__(self) -> str:
        note_str = self.note.name if self.note else "Rest"
        return f"Event(t={self.time:.2f}, dur={self.duration:.2f}, note={note_str}, line={self.line_id})"


@dataclass
class Voice:
    """声部数据类"""
    voice_id: int
    events: List[Event] = field(default_factory=list)
    name: str = ""

    def add_event(self, event: Event):
        self.events.append(event)
        self.events.sort(key=lambda e: e.time)


@dataclass
class Score:
    """乐谱数据类（多声部）"""
    voices: List[Voice] = field(default_factory=list)
    tempo: float = 120.0  # BPM
    title: str = ""

    def add_voice(self, voice: Voice):
        self.voices.append(voice)

    def get_all_events(self) -> List[Event]:
        all_events = []
        for voice in self.voices:
            for event in voice.events:
                all_events.append(event)
        return sorted(all_events, key=lambda e: (e.time, e.line_id))


# =============================================================================
# 1. TwelveToneEqualTemperament — 十二平均律
# =============================================================================

class TwelveToneEqualTemperament:
    """
    十二平均律（12-TET）引擎

    基于频率比 r = 2^(1/12) ≈ 1.059463
    标准音高 A4 = 440Hz

    数学原理：
    - 每个半音的频率比为 2^(1/12)
    - n个半音的频率比为 2^(n/12)
    - 八度关系：频率翻倍（2:1）

    与意识共振的映射：
    - 频率的对数增长对应意识的层级跃迁
    - 每个半音 ≈  consciousness level 增加 1/12
    """

    def __init__(self, a4_freq: float = A4_FREQUENCY):
        """
        初始化十二平均律引擎

        Args:
            a4_freq: A4标准音高频率（默认440Hz）
        """
        self.a4_freq = a4_freq
        self.ratio = TWELFTH_ROOT_OF_TWO
        self._note_to_index = {name: i for i, name in enumerate(NOTE_NAMES)}
        self._index_to_note = {i: name for i, name in enumerate(NOTE_NAMES)}

    def _note_name_to_midi(self, note_name: str, octave: int) -> int:
        """将音符名称转换为MIDI编号"""
        if note_name not in self._note_to_index:
            raise ValueError(f"未知音符名称: {note_name}")
        return (octave + 1) * 12 + self._note_to_index[note_name]

    def _midi_to_note_name(self, midi_num: int) -> Tuple[str, int]:
        """将MIDI编号转换为音符名称和八度"""
        octave = (midi_num // 12) - 1
        note_idx = midi_num % 12
        return self._index_to_note[note_idx], octave

    def get_frequency(self, note_name: str, octave: int) -> float:
        """
        获取指定音符的频率

        Args:
            note_name: 音符名称（如 'A', 'C#', 'F'）
            octave: 八度（如 4 表示中央C所在八度）

        Returns:
            float: 频率（Hz）

        Example:
            >>> tet = TwelveToneEqualTemperament()
            >>> tet.get_frequency('A', 4)
            440.0
            >>> tet.get_frequency('C', 4)
            261.6255653005986
        """
        midi_num = self._note_name_to_midi(note_name, octave)
        a4_midi = 69  # A4的MIDI编号
        semitone_distance = midi_num - a4_midi
        frequency = self.a4_freq * (self.ratio ** semitone_distance)
        return frequency

    def get_note_from_freq(self, freq: float) -> Note:
        """
        从频率反推音符

        Args:
            freq: 频率（Hz）

        Returns:
            Note: 音符对象

        数学原理：
            f = 440 * 2^((midi-69)/12)
            => midi = 69 + 12 * log2(f/440)
        """
        if freq <= 0:
            raise ValueError("频率必须为正数")

        midi_float = 69 + 12 * math.log2(freq / self.a4_freq)
        midi_num = round(midi_float)
        note_name, octave = self._midi_to_note_name(midi_num)
        exact_freq = self.get_frequency(note_name, octave)

        return Note(
            name=note_name,
            octave=octave,
            frequency=exact_freq,
            midi_number=midi_num
        )

    def get_interval_ratio(self, note1: Tuple[str, int], note2: Tuple[str, int]) -> float:
        """
        计算两个音符之间的音程比

        Args:
            note1: (音符名称, 八度) 元组
            note2: (音符名称, 八度) 元组

        Returns:
            float: 频率比（>=1）
        """
        freq1 = self.get_frequency(note1[0], note1[1])
        freq2 = self.get_frequency(note2[0], note2[1])
        ratio = max(freq1, freq2) / min(freq1, freq2)
        return ratio

    def get_semitone_distance(self, note1: Tuple[str, int], note2: Tuple[str, int]) -> int:
        """
        计算两个音符之间的半音距离

        Args:
            note1: (音符名称, 八度) 元组
            note2: (音符名称, 八度) 元组

        Returns:
            int: 半音距离（绝对值）
        """
        midi1 = self._note_name_to_midi(note1[0], note1[1])
        midi2 = self._note_name_to_midi(note2[0], note2[1])
        return abs(midi1 - midi2)

    def get_all_notes_in_octave(self, octave: int) -> List[Note]:
        """
        获取指定八度内的所有音符

        Args:
            octave: 八度

        Returns:
            List[Note]: 音符列表
        """
        notes = []
        for name in NOTE_NAMES:
            freq = self.get_frequency(name, octave)
            midi = self._note_name_to_midi(name, octave)
            notes.append(Note(name=name, octave=octave, frequency=freq, midi_number=midi))
        return notes

    def get_chromatic_scale(self, start_note: Tuple[str, int], num_notes: int = 12) -> List[Note]:
        """
        生成半音阶

        Args:
            start_note: 起始音符 (名称, 八度)
            num_notes: 音符数量

        Returns:
            List[Note]: 半音阶音符列表
        """
        start_midi = self._note_name_to_midi(start_note[0], start_note[1])
        notes = []
        for i in range(num_notes):
            midi = start_midi + i
            name, octave = self._midi_to_note_name(midi)
            freq = self.get_frequency(name, octave)
            notes.append(Note(name=name, octave=octave, frequency=freq, midi_number=midi))
        return notes


# =============================================================================
# 2. TwelveLuLu — 十二律吕（三分损益法）
# =============================================================================

class TwelveLuLu:
    """
    十二律吕引擎 — 基于三分损益法

    源自《管子·地员篇》，是中国古代音乐理论的精髓：
    - 三分损一：频率 × 2/3（上生五度，纯五度上行）
    - 三分益一：频率 × 4/3（下生四度，纯四度下行）

    生成顺序（以黄钟为宫）：
    黄钟 → 林钟（损一）→ 太簇（益一）→ 南吕（损一）→ 姑洗（益一）
    → 应钟（损一）→ 蕤宾（益一）→ 大吕（损一）→ 夷则（益一）
    → 夹钟（损一）→ 无射（益一）→ 仲吕（损一）

    数学特性：
    - 三分损益法生成的频率基于简单整数比（3:2, 4:3）
    - 与十二平均律的差异体现了"自然和谐"vs"数学等分"的哲学张力
    - 律吕循环接近闭合但不完全闭合（Pythagorean comma）
    """

    def __init__(self, base_freq: float = C4_FREQUENCY):
        """
        初始化十二律吕引擎

        Args:
            base_freq: 黄钟基准频率（默认261.63Hz，约等于C4）
        """
        self.base_freq = base_freq
        self.lulu_chain: Dict[str, float] = {}
        self.lulu_order: List[str] = []
        self._generate_chain()

    def _generate_chain(self):
        """
        生成十二律吕链

        按照《吕氏春秋》记载的生成顺序：
        1. 黄钟（基准）
        2. 林钟：黄钟 × 2/3（三分损一，上生）
        3. 太簇：林钟 × 4/3（三分益一，下生）
        4. 南吕：太簇 × 2/3（三分损一，上生）
        5. 姑洗：南吕 × 4/3（三分益一，下生）
        6. 应钟：姑洗 × 2/3（三分损一，上生）
        7. 蕤宾：应钟 × 4/3（三分益一，下生）
        8. 大吕：蕤宾 × 2/3（三分损一，上生）
        9. 夷则：大吕 × 4/3（三分益一，下生）
        10. 夹钟：夷则 × 2/3（三分损一，上生）
        11. 无射：夹钟 × 4/3（三分益一，下生）
        12. 仲吕：无射 × 2/3（三分损一，上生）
        """
        # 生成顺序（管子法）
        generation_order = [
            ('黄钟', None),      # 基准
            ('林钟', '损'),      # 黄钟 × 2/3
            ('太簇', '益'),      # 林钟 × 4/3
            ('南吕', '损'),      # 太簇 × 2/3
            ('姑洗', '益'),      # 南吕 × 4/3
            ('应钟', '损'),      # 姑洗 × 2/3
            ('蕤宾', '益'),      # 应钟 × 4/3
            ('大吕', '损'),      # 蕤宾 × 2/3
            ('夷则', '益'),      # 大吕 × 4/3
            ('夹钟', '损'),      # 夷则 × 2/3
            ('无射', '益'),      # 夹钟 × 4/3
            ('仲吕', '损'),      # 无射 × 2/3
        ]

        current_freq = self.base_freq
        self.lulu_chain['黄钟'] = current_freq
        self.lulu_order = ['黄钟']

        for name, operation in generation_order[1:]:
            if operation == '损':
                # 三分损一：× 2/3
                current_freq = current_freq * 2 / 3
            elif operation == '益':
                # 三分益一：× 4/3
                current_freq = current_freq * 4 / 3

            # 归一化到 [base_freq, base_freq*2) 范围内
            # 确保所有律吕都在同一八度区间内（黄钟到高八度黄钟之间）
            while current_freq < self.base_freq:
                current_freq *= 2
            while current_freq >= self.base_freq * 2:
                current_freq /= 2

            self.lulu_chain[name] = current_freq
            self.lulu_order.append(name)

    def generate_lulu_chain(self, base_freq: Optional[float] = None) -> Dict[str, float]:
        """
        生成十二律吕链

        Args:
            base_freq: 新的基准频率，如果为None则使用初始化时的频率

        Returns:
            Dict[str, float]: 律吕名称到频率的映射
        """
        if base_freq is not None and base_freq != self.base_freq:
            self.base_freq = base_freq
            self._generate_chain()
        return self.lulu_chain.copy()

    def get_lulu_freq(self, lulu_name: str) -> float:
        """
        获取指定律吕的频率

        Args:
            lulu_name: 律吕名称（如 '黄钟', '大吕' 等）

        Returns:
            float: 频率（Hz）

        Raises:
            ValueError: 如果律吕名称不存在
        """
        if lulu_name not in self.lulu_chain:
            raise ValueError(f"未知律吕名称: {lulu_name}，可用名称: {list(self.lulu_chain.keys())}")
        return self.lulu_chain[lulu_name]

    def get_lulu_comparison(self) -> Dict[str, Dict]:
        """
        获取律吕的详细比较信息

        将十二律吕与十二平均律进行公平比较：
        - 对每个律吕，找到频率最接近的十二平均律音符
        - 计算频率差异（音分）

        Returns:
            Dict: 包含频率、与十二平均律差异等信息
        """
        tet = TwelveToneEqualTemperament()
        results = {}

        for lulu_name in self.lulu_order:
            lulu_freq = self.lulu_chain[lulu_name]

            # 找到最接近的十二平均律音符
            closest_note = tet.get_note_from_freq(lulu_freq)
            tet_freq = closest_note.frequency

            # 计算差异（音分）
            diff_cents = 1200 * math.log2(lulu_freq / tet_freq)

            results[lulu_name] = {
                'lulu_freq': lulu_freq,
                'tet_freq': tet_freq,
                'diff_cents': diff_cents,
                'diff_ratio': lulu_freq / tet_freq,
                'closest_tet_note': f"{closest_note.name}{closest_note.octave}",
            }

        return results

    def get_pythagorean_comma(self) -> float:
        """
        计算毕达哥拉斯音差（Pythagorean Comma）

        经过12次五度循环后，频率比应为 2^7 = 128（7个八度）
        但实际上 (3/2)^12 ≈ 129.746
        音差 = 129.746 / 128 ≈ 1.01364

        Returns:
            float: 音差比例
        """
        twelve_fifths = (3 / 2) ** 12
        seven_octaves = 2 ** 7
        return twelve_fifths / seven_octaves

    def get_lulu_interval_ratio(self, lulu1: str, lulu2: str) -> float:
        """
        计算两个律吕之间的频率比

        Args:
            lulu1: 第一个律吕名称
            lulu2: 第二个律吕名称

        Returns:
            float: 频率比
        """
        freq1 = self.get_lulu_freq(lulu1)
        freq2 = self.get_lulu_freq(lulu2)
        return max(freq1, freq2) / min(freq1, freq2)


# =============================================================================
# 3. ConsonanceDissonance — 和声共振↔意识共振映射
# =============================================================================

class ConsonanceDissonance:
    """
    和声共振与意识共振映射引擎

    核心概念：
    - 协和度（Consonance）：音程的和谐程度，0-1之间
    - 意识共振（Consciousness Resonance）：将协和度映射到意识状态

    数学映射：
    - 协和度 1.0 → 完全共振（合一意识）
    - 协和度 0.8-0.9 → 强共振（爱/喜悦）
    - 协和度 0.5-0.7 → 中等共振（思考/探索）
    - 协和度 0.2-0.4 → 弱共振（紧张/冲突）
    - 协和度 0.0-0.1 → 无序（混沌/解体）

    与黄金比例的关系：
    - 最协和的音程（纯五度 3:2）接近 φ/2 ≈ 0.809
    - 大三度 5:4 = 1.25 接近 2/φ ≈ 1.236 的倒数关系
    """

    def __init__(self, temperament: Optional[TwelveToneEqualTemperament] = None):
        """
        初始化和声共振引擎

        Args:
            temperament: 十二平均律引擎实例
        """
        self.temperament = temperament or TwelveToneEqualTemperament()
        self._interval_names = list(INTERVAL_RATIOS.keys())
        self._build_consonance_map()

    def _build_consonance_map(self):
        """构建协和度映射表"""
        # 半音距离到音程名称的映射
        self._semitone_to_interval = {
            0: 'unison',
            1: 'minor_second',
            2: 'major_second',
            3: 'minor_third',
            4: 'major_third',
            5: 'perfect_fourth',
            6: 'tritone',
            7: 'perfect_fifth',
            8: 'minor_sixth',
            9: 'major_sixth',
            10: 'minor_seventh',
            11: 'major_seventh',
            12: 'octave',
        }

    def _get_interval_name(self, semitones: int) -> str:
        """根据半音距离获取音程名称"""
        semitones = semitones % 12
        if semitones == 0:
            return 'unison'
        return self._semitone_to_interval.get(semitones, 'unknown')

    def calculate_consonance(self, note1: Tuple[str, int], note2: Tuple[str, int]) -> float:
        """
        计算两个音符的协和度

        Args:
            note1: (音符名称, 八度)
            note2: (音符名称, 八度)

        Returns:
            float: 协和度（0-1）
        """
        semitones = self.temperament.get_semitone_distance(note1, note2)
        semitones = semitones % 12
        interval_name = self._get_interval_name(semitones)

        # 获取基础协和度
        base_consonance = CONSONANCE_SCORES.get(interval_name, 0.5)

        # 计算实际频率比的纯度（与just intonation的接近程度）
        freq1 = self.temperament.get_frequency(note1[0], note1[1])
        freq2 = self.temperament.get_frequency(note2[0], note2[1])
        actual_ratio = max(freq1, freq2) / min(freq1, freq2)

        # 获取理论just intonation比例
        ji_ratio = INTERVAL_RATIOS.get(interval_name, (1, 1))
        ji_value = ji_ratio[0] / ji_ratio[1]
        if ji_value < 1:
            ji_value = 1 / ji_value

        # 纯度因子：实际比例与理论比例的匹配程度
        purity = 1.0 - min(abs(math.log2(actual_ratio / ji_value)), 0.5)

        # 综合协和度 = 基础协和度 × 纯度因子
        consonance = base_consonance * (0.7 + 0.3 * purity)

        return min(max(consonance, 0.0), 1.0)

    def get_chord_quality(self, notes: List[Tuple[str, int]]) -> Dict:
        """
        判断和弦性质

        Args:
            notes: 音符列表，每个元素为 (名称, 八度)

        Returns:
            Dict: 和弦性质分析结果
        """
        if len(notes) < 2:
            return {'quality': 'unknown', 'root': None, 'type': 'single_note'}

        # 获取所有音符的MIDI编号并排序
        midi_nums = []
        for note in notes:
            midi = self.temperament._note_name_to_midi(note[0], note[1])
            midi_nums.append(midi)

        midi_nums.sort()

        # 计算音程结构（以第一个音为根音）
        intervals = []
        for i in range(1, len(midi_nums)):
            interval = (midi_nums[i] - midi_nums[0]) % 12
            intervals.append(interval)

        intervals.sort()

        # 判断和弦类型
        interval_set = set(intervals)

        # 三和弦判断
        if len(intervals) >= 2:
            if interval_set == {4, 7}:
                quality = 'major_triad'
                description = '大三和弦（稳定、明亮）'
                stability = 0.90
            elif interval_set == {3, 7}:
                quality = 'minor_triad'
                description = '小三和弦（忧郁、内敛）'
                stability = 0.85
            elif interval_set == {3, 6}:
                quality = 'diminished_triad'
                description = '减三和弦（紧张、收缩）'
                stability = 0.40
            elif interval_set == {4, 8}:
                quality = 'augmented_triad'
                description = '增三和弦（扩张、神秘）'
                stability = 0.45
            elif interval_set == {4, 7, 10} or interval_set == {4, 7, 11}:
                quality = 'dominant_seventh' if 10 in interval_set else 'major_seventh'
                description = '属七和弦（不稳定、趋向解决）' if 10 in interval_set else '大七和弦（明亮、现代）'
                stability = 0.55 if 10 in interval_set else 0.75
            elif interval_set == {3, 7, 10}:
                quality = 'minor_seventh'
                description = '小七和弦（柔和、爵士）'
                stability = 0.70
            elif interval_set == {3, 6, 9}:
                quality = 'diminished_seventh'
                description = '减七和弦（高度紧张、戏剧）'
                stability = 0.30
            elif interval_set == {4, 7, 11}:
                quality = 'major_seventh'
                description = '大七和弦（梦幻、现代）'
                stability = 0.75
            elif 5 in interval_set and 7 in interval_set:
                quality = 'sus4'
                description = '挂四和弦（开放、悬浮）'
                stability = 0.65
            else:
                quality = 'complex'
                description = '复杂和弦'
                stability = 0.60
        else:
            quality = 'dyad'
            description = '音程'
            stability = self.calculate_consonance(notes[0], notes[1])

        # 计算整体协和度
        overall_consonance = self._calculate_chord_consonance(notes)

        return {
            'quality': quality,
            'description': description,
            'root': notes[0],
            'intervals': intervals,
            'stability': stability,
            'overall_consonance': overall_consonance,
            'consciousness_state': self.resonance_to_consciousness(overall_consonance),
        }

    def _calculate_chord_consonance(self, notes: List[Tuple[str, int]]) -> float:
        """计算和弦的整体协和度"""
        if len(notes) < 2:
            return 1.0

        consonances = []
        for i in range(len(notes)):
            for j in range(i + 1, len(notes)):
                c = self.calculate_consonance(notes[i], notes[j])
                consonances.append(c)

        # 使用几何平均
        if consonances:
            product = 1.0
            for c in consonances:
                product *= c
            return product ** (1 / len(consonances))
        return 1.0

    def resonance_to_consciousness(self, consonance_score: float) -> Dict:
        """
        协和度→意识共振映射

        Args:
            consonance_score: 协和度（0-1）

        Returns:
            Dict: 意识状态描述
        """
        if consonance_score >= 0.95:
            state = 'unity'
            description = '合一意识 — 绝对和谐，万物一体'
            color = 'white'
            level = 7
        elif consonance_score >= 0.85:
            state = 'love'
            description = '爱/喜悦 — 深层连接，无条件接纳'
            color = 'gold'
            level = 6
        elif consonance_score >= 0.70:
            state = 'reason'
            description = '理性/理解 — 清晰洞察，智慧流动'
            color = 'blue'
            level = 5
        elif consonance_score >= 0.55:
            state = 'acceptance'
            description = '接纳/意愿 — 开放包容，顺势而为'
            color = 'green'
            level = 4
        elif consonance_score >= 0.40:
            state = 'neutrality'
            description = '中立/平衡 — 客观观察，不偏不倚'
            color = 'yellow'
            level = 3
        elif consonance_score >= 0.25:
            state = 'conflict'
            description = '冲突/挣扎 — 内在矛盾，寻求突破'
            color = 'orange'
            level = 2
        else:
            state = 'chaos'
            description = '混沌/解体 — 无序状态，待重组'
            color = 'red'
            level = 1

        # 与黄金比例的关联
        phi_alignment = 1.0 - abs(consonance_score - 1 / PHI)

        return {
            'consonance_score': consonance_score,
            'consciousness_state': state,
            'description': description,
            'color': color,
            'level': level,
            'phi_alignment': phi_alignment,
            'emergence_potential': consonance_score * phi_alignment,
        }

    def get_interval_analysis(self, note1: Tuple[str, int], note2: Tuple[str, int]) -> Dict:
        """
        详细音程分析

        Args:
            note1: 第一个音符
            note2: 第二个音符

        Returns:
            Dict: 音程分析结果
        """
        semitones = self.temperament.get_semitone_distance(note1, note2) % 12
        interval_name = self._get_interval_name(semitones)

        # 获取频率
        f1 = self.temperament.get_frequency(note1[0], note1[1])
        f2 = self.temperament.get_frequency(note2[0], note2[1])

        # 计算拍频（beat frequency）
        beat_freq = abs(f1 - f2)

        # 协和度
        consonance = self.calculate_consonance(note1, note2)

        # Just Intonation比例
        ji = INTERVAL_RATIOS.get(interval_name, (1, 1))

        return {
            'interval_name': interval_name,
            'semitones': semitones,
            'frequency1': f1,
            'frequency2': f2,
            'ratio_12tet': max(f1, f2) / min(f1, f2),
            'ratio_ji': f"{ji[0]}:{ji[1]}",
            'beat_frequency': beat_freq,
            'consonance': consonance,
            'consciousness_state': self.resonance_to_consciousness(consonance),
        }


# =============================================================================
# 4. CounterpointEngineEnhanced — 对位引擎增强
# =============================================================================

class CounterpointEngineEnhanced:
    """
    对位引擎增强版 — 支持11声部对位

    对位法（Counterpoint）是复调音乐的基础，核心原则：
    - 声部独立性：每个声部应有独立的旋律线条
    - 协和进行：纵向和声以协和音程为主
    - 避免平行五度/八度：防止声部融合失去独立性
    - 和声节奏：和弦变化的速度与韵律

    11声部对位对应OMNI-HUB的11线分布式系统：
    - 每条线 = 一个独立声部
    - 线的交互 = 声部的和声关系
    - 线的独立性 = 声部的旋律自主性
    """

    def __init__(self, temperament: Optional[TwelveToneEqualTemperament] = None):
        """
        初始化对位引擎

        Args:
            temperament: 十二平均律引擎
        """
        self.temperament = temperament or TwelveToneEqualTemperament()
        self.consonance = ConsonanceDissonance(self.temperament)

        # 对位规则配置
        self.rules = {
            'allow_parallel_fifths': False,
            'allow_parallel_octaves': False,
            'min_consonance_threshold': 0.5,
            'max_leap': 7,  # 最大跳进（半音）
            'prefer_contrary_motion': True,
        }

    def compose_counterpoint_11(self, cantus_firmus: List[Tuple[str, int]]) -> Score:
        """
        为固定旋律（Cantus Firmus）创作11声部对位

        Args:
            cantus_firmus: 固定旋律，音符列表 [(名称, 八度), ...]

        Returns:
            Score: 包含11个声部的乐谱

        算法：
        1. 第一条声部 = 固定旋律
        2. 其余10条声部基于对位规则生成
        3. 每条新声部与已有声部保持协和关系
        4. 避免平行五度/八度
        """
        score = Score(title="11-Voice Counterpoint", tempo=120)

        # 第1声部：固定旋律
        voice1 = Voice(voice_id=0, name="Cantus Firmus")
        for i, note in enumerate(cantus_firmus):
            event = Event(
                time=i * 1.0,
                duration=1.0,
                note=Note(
                    name=note[0],
                    octave=note[1],
                    frequency=self.temperament.get_frequency(note[0], note[1]),
                    midi_number=self.temperament._note_name_to_midi(note[0], note[1])
                ),
                line_id=0
            )
            voice1.add_event(event)
        score.add_voice(voice1)

        # 生成其余10个声部
        for voice_idx in range(1, 11):
            voice = self._generate_counterpoint_voice(
                voice_id=voice_idx,
                cantus_firmus=cantus_firmus,
                existing_voices=score.voices,
                octave_offset=(voice_idx % 3) - 1  # -1, 0, 1 循环
            )
            score.add_voice(voice)

        return score

    def _generate_counterpoint_voice(
        self,
        voice_id: int,
        cantus_firmus: List[Tuple[str, int]],
        existing_voices: List[Voice],
        octave_offset: int = 0
    ) -> Voice:
        """
        生成单个对位声部

        Args:
            voice_id: 声部编号
            cantus_firmus: 固定旋律
            existing_voices: 已有声部
            octave_offset: 八度偏移

        Returns:
            Voice: 新生成的声部
        """
        voice = Voice(voice_id=voice_id, name=f"Counterpoint {voice_id}")

        # 可用的调内音（以C大调为例）
        scale_degrees = [0, 2, 4, 5, 7, 9, 11]  # C大调音阶
        base_octave = 4 + octave_offset

        prev_note = None
        for i, cf_note in enumerate(cantus_firmus):
            cf_midi = self.temperament._note_name_to_midi(cf_note[0], cf_note[1])

            # 寻找与固定旋律协和的音
            candidates = []
            for degree in scale_degrees:
                for oct_shift in [-1, 0, 1]:
                    candidate_midi = (base_octave + oct_shift + 1) * 12 + degree
                    semitone_dist = abs(candidate_midi - cf_midi)

                    # 检查与固定旋律的协和度
                    c_note = self.temperament._midi_to_note_name(candidate_midi)
                    consonance = self.consonance.calculate_consonance(cf_note, c_note)

                    # 检查与已有声部的关系
                    voice_consonance = self._check_voice_consonance(
                        candidate_midi, i, existing_voices
                    )

                    # 检查平行音程
                    parallel_penalty = self._check_parallel_penalty(
                        candidate_midi, prev_note, cf_midi, i, existing_voices
                    )

                    # 综合评分
                    score_val = consonance * 0.4 + voice_consonance * 0.4 - parallel_penalty * 0.2

                    # 偏好反向进行
                    if prev_note is not None:
                        prev_cf_midi = self.temperament._note_name_to_midi(
                            cantus_firmus[max(0, i-1)][0],
                            cantus_firmus[max(0, i-1)][1]
                        )
                        cf_direction = cf_midi - prev_cf_midi
                        voice_direction = candidate_midi - prev_note
                        if cf_direction * voice_direction < 0:  # 反向
                            score_val += 0.1

                    candidates.append((candidate_midi, score_val, consonance))

            # 选择最佳候选
            candidates.sort(key=lambda x: x[1], reverse=True)

            # 从前5个候选中随机选择，增加多样性
            top_candidates = candidates[:min(5, len(candidates))]
            if not top_candidates:
                # 默认选择八度音
                selected_midi = cf_midi + 12 * (1 if voice_id % 2 == 0 else -1)
            else:
                weights = [c[2] for c in top_candidates]
                total = sum(weights)
                if total > 0:
                    probs = [w / total for w in weights]
                    selected_midi = np.random.choice(
                        [c[0] for c in top_candidates],
                        p=probs
                    )
                else:
                    selected_midi = top_candidates[0][0]

            note_name, note_octave = self.temperament._midi_to_note_name(selected_midi)
            freq = self.temperament.get_frequency(note_name, note_octave)

            event = Event(
                time=i * 1.0,
                duration=1.0,
                note=Note(
                    name=note_name,
                    octave=note_octave,
                    frequency=freq,
                    midi_number=selected_midi
                ),
                line_id=voice_id
            )
            voice.add_event(event)
            prev_note = selected_midi

        return voice

    def _check_voice_consonance(self, midi_num: int, time_idx: int, voices: List[Voice]) -> float:
        """检查候选音与已有声部在同时刻的协和度"""
        if not voices:
            return 1.0

        consonances = []
        for voice in voices:
            if time_idx < len(voice.events):
                other_midi = voice.events[time_idx].note.midi_number
                semitones = abs(midi_num - other_midi) % 12
                interval_name = self.consonance._get_interval_name(semitones)
                c = CONSONANCE_SCORES.get(interval_name, 0.5)
                consonances.append(c)

        return np.mean(consonances) if consonances else 1.0

    def _check_parallel_penalty(
        self,
        midi_num: int,
        prev_midi: Optional[int],
        cf_midi: int,
        time_idx: int,
        voices: List[Voice]
    ) -> float:
        """检查平行音程惩罚"""
        penalty = 0.0

        if prev_midi is None or time_idx == 0:
            return penalty

        # 检查与固定旋律的平行音程
        prev_cf = cf_midi
        if time_idx > 0:
            # 简化处理：使用当前cf
            pass

        current_interval = abs(midi_num - cf_midi) % 12
        prev_interval = abs(prev_midi - prev_cf) % 12 if prev_cf else 0

        # 平行五度（7半音）
        if current_interval == 7 and prev_interval == 7:
            penalty += 2.0

        # 平行八度（0或12半音）
        if current_interval in [0, 12] and prev_interval in [0, 12]:
            penalty += 2.0

        return penalty

    def detect_parallel_intervals(self, score: Score) -> List[Dict]:
        """
        检测乐谱中的平行音程

        Args:
            score: 多声部乐谱

        Returns:
            List[Dict]: 平行音程列表
        """
        parallels = []
        voices = score.voices

        for i in range(len(voices)):
            for j in range(i + 1, len(voices)):
                voice1 = voices[i]
                voice2 = voices[j]

                min_len = min(len(voice1.events), len(voice2.events))

                for t in range(1, min_len):
                    prev_midi1 = voice1.events[t - 1].note.midi_number
                    prev_midi2 = voice2.events[t - 1].note.midi_number
                    curr_midi1 = voice1.events[t].note.midi_number
                    curr_midi2 = voice2.events[t].note.midi_number

                    prev_interval = abs(prev_midi1 - prev_midi2) % 12
                    curr_interval = abs(curr_midi1 - curr_midi2) % 12

                    # 检查平行进行
                    if prev_interval == curr_interval and prev_interval in [0, 7]:
                        interval_type = 'octave' if prev_interval == 0 else 'fifth'
                        parallels.append({
                            'type': f'parallel_{interval_type}',
                            'voices': (i, j),
                            'time': t,
                            'severity': 'high' if interval_type == 'octave' else 'medium',
                        })

        return parallels

    def calculate_voice_independence(self, score: Score) -> Dict:
        """
        计算声部独立性指标

        声部独立性衡量标准：
        1. 旋律方向的独立性（反向进行比例）
        2. 节奏独立性（避免完全同步）
        3. 音域分离度（不同声部的音域范围）

        Args:
            score: 多声部乐谱

        Returns:
            Dict: 独立性分析结果
        """
        voices = score.voices
        if len(voices) < 2:
            return {'overall_independence': 1.0, 'details': []}

        details = []
        total_independence = 0.0
        pair_count = 0

        for i in range(len(voices)):
            for j in range(i + 1, len(voices)):
                v1 = voices[i]
                v2 = voices[j]

                min_len = min(len(v1.events), len(v2.events))
                if min_len < 2:
                    continue

                contrary_count = 0
                similar_count = 0
                parallel_count = 0

                for t in range(1, min_len):
                    d1 = v1.events[t].note.midi_number - v1.events[t - 1].note.midi_number
                    d2 = v2.events[t].note.midi_number - v2.events[t - 1].note.midi_number

                    if d1 * d2 < 0:
                        contrary_count += 1
                    elif d1 * d2 > 0:
                        similar_count += 1
                    else:
                        parallel_count += 1

                total = contrary_count + similar_count + parallel_count
                if total > 0:
                    contrary_ratio = contrary_count / total
                    independence = 0.4 * contrary_ratio + 0.3 * (1 - similar_count / total) + 0.3
                else:
                    independence = 0.5

                details.append({
                    'voice_pair': (i, j),
                    'contrary_motion_ratio': contrary_count / total if total > 0 else 0,
                    'similar_motion_ratio': similar_count / total if total > 0 else 0,
                    'parallel_motion_ratio': parallel_count / total if total > 0 else 0,
                    'independence_score': independence,
                })

                total_independence += independence
                pair_count += 1

        overall = total_independence / pair_count if pair_count > 0 else 1.0

        return {
            'overall_independence': overall,
            'num_pairs': pair_count,
            'details': details,
        }

    def harmonic_rhythm_analysis(self, score: Score) -> Dict:
        """
        和声节奏分析

        和声节奏指的是和弦变化的频率和模式：
        - 快和声节奏：每拍和弦变化（紧张、活跃）
        - 慢和声节奏：每小节和弦变化（稳定、平静）

        Args:
            score: 多声部乐谱

        Returns:
            Dict: 和声节奏分析结果
        """
        voices = score.voices
        if not voices:
            return {}

        # 分析和弦变化
        chord_changes = []
        min_len = min(len(v.events) for v in voices)

        for t in range(min_len):
            # 获取同时刻的所有音符
            notes_at_t = []
            for v in voices:
                if t < len(v.events):
                    notes_at_t.append((v.events[t].note.name, v.events[t].note.octave))

            # 简化和弦品质判断
            quality = self.consonance.get_chord_quality(notes_at_t)
            chord_changes.append({
                'time': t,
                'quality': quality['quality'],
                'consonance': quality['overall_consonance'],
                'notes': [f"{n[0]}{n[1]}" for n in notes_at_t],
            })

        # 计算和声变化率
        changes = 0
        for i in range(1, len(chord_changes)):
            if chord_changes[i]['quality'] != chord_changes[i - 1]['quality']:
                changes += 1

        change_rate = changes / len(chord_changes) if chord_changes else 0

        # 和声节奏分类
        if change_rate > 0.7:
            rhythm_type = 'fast'
            description = '快和声节奏 — 高能量、紧张、戏剧性'
        elif change_rate > 0.4:
            rhythm_type = 'moderate'
            description = '中度和声节奏 — 平衡、流动、叙述性'
        else:
            rhythm_type = 'slow'
            description = '慢和声节奏 — 稳定、冥想、史诗感'

        # 平均协和度
        avg_consonance = np.mean([c['consonance'] for c in chord_changes])

        return {
            'change_rate': change_rate,
            'rhythm_type': rhythm_type,
            'description': description,
            'avg_consonance': avg_consonance,
            'total_chords': len(chord_changes),
            'chord_changes': changes,
            'chord_progression': chord_changes,
        }


# =============================================================================
# 5. FugueStructure — 赋格结构
# =============================================================================

class FugueStructure:
    """
    赋格结构引擎

    赋格（Fugue）是巴洛克时期最高级的复调音乐形式，核心特征：
    - 主题（Subject）：赋格的核心旋律
    - 答题（Answer）：主题在属调上的陈述
    - 对题（Countersubject）：伴随答题的旋律
    - 呈示部（Exposition）：主题在各声部依次呈现
    - 间插段（Episode）：连接段落
    - 紧接模仿（Stretto）：主题在各声部紧密重叠

    自指映射（Self-Referential Mapping）：
    - 赋格的结构本身就是递归的（主题→答题→对题→主题...）
    - 这对应于意识系统的自指性（自我意识）
    - 增值/减值/倒影/逆行 对应于意识的变形和反思
    """

    def __init__(self, temperament: Optional[TwelveToneEqualTemperament] = None):
        """
        初始化赋格结构引擎

        Args:
            temperament: 十二平均律引擎
        """
        self.temperament = temperament or TwelveToneEqualTemperament()
        self.consonance = ConsonanceDissonance(self.temperament)

    def create_fugue(self, subject: List[Tuple[str, int]], num_voices: int = 11) -> Score:
        """
        创建赋格

        Args:
            subject: 主题旋律，音符列表
            num_voices: 声部数量（默认11，对应11线系统）

        Returns:
            Score: 赋格乐谱
        """
        score = Score(title=f"{num_voices}-Voice Fugue", tempo=120)
        subject_len = len(subject)

        # 呈示部：每个声部依次进入
        # 第一条声部：主题（主调）
        # 第二条声部：答题（属调，上移纯五度）
        # 第三条声部：主题（主调，八度）
        # 后续声部交替主调/属调

        for voice_idx in range(num_voices):
            voice = Voice(voice_id=voice_idx, name=f"Fugue Voice {voice_idx}")

            # 确定是主题还是答题
            is_answer = voice_idx % 2 == 1

            # 进入时间（错开）
            entry_time = voice_idx * (subject_len * 0.5)

            # 生成旋律
            if is_answer:
                # 答题：主题上移纯五度（7半音）
                melody = self._transpose_melody(subject, 7)
            else:
                # 主题：原调或八度
                octave_shift = (voice_idx // 2) * 12
                melody = self._transpose_melody(subject, octave_shift)

            # 添加对题（从第二条声部开始）
            if voice_idx >= 1:
                countersubject = self._generate_countersubject(subject)
                # 将对题与旋律交错
                combined = self._interleave_melodies(melody, countersubject)
            else:
                combined = melody

            # 创建事件
            for i, note in enumerate(combined):
                event = Event(
                    time=entry_time + i * 0.5,
                    duration=0.5,
                    note=Note(
                        name=note[0],
                        octave=note[1],
                        frequency=self.temperament.get_frequency(note[0], note[1]),
                        midi_number=self.temperament._note_name_to_midi(note[0], note[1])
                    ),
                    line_id=voice_idx
                )
                voice.add_event(event)

            score.add_voice(voice)

        return score

    def _transpose_melody(self, melody: List[Tuple[str, int]], semitones: int) -> List[Tuple[str, int]]:
        """移调旋律"""
        transposed = []
        for note_name, octave in melody:
            midi = self.temperament._note_name_to_midi(note_name, octave)
            new_midi = midi + semitones
            new_name, new_octave = self.temperament._midi_to_note_name(new_midi)
            transposed.append((new_name, new_octave))
        return transposed

    def _generate_countersubject(self, subject: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        """
        生成对题

        对题是与主题形成对比的旋律，通常：
        - 与主题反向进行
        - 填补主题的休止
        - 与主题形成协和音程
        """
        countersubject = []
        for i, (note_name, octave) in enumerate(subject):
            midi = self.temperament._note_name_to_midi(note_name, octave)
            # 反向进行：如果主题上行，对题下行
            if i > 0:
                prev_midi = self.temperament._note_name_to_midi(subject[i-1][0], subject[i-1][1])
                direction = midi - prev_midi
                # 反向
                new_midi = midi - direction + random.choice([-2, -1, 1, 2])
            else:
                # 第一个音：与主题形成三度
                new_midi = midi + 3

            new_name, new_octave = self.temperament._midi_to_note_name(new_midi)
            countersubject.append((new_name, new_octave))

        return countersubject

    def _interleave_melodies(
        self,
        melody1: List[Tuple[str, int]],
        melody2: List[Tuple[str, int]]
    ) -> List[Tuple[str, int]]:
        """交错两个旋律"""
        combined = []
        for i in range(max(len(melody1), len(melody2))):
            if i < len(melody1):
                combined.append(melody1[i])
            if i < len(melody2):
                combined.append(melody2[i])
        return combined

    def stretto(
        self,
        subject: List[Tuple[str, int]],
        voices: List[Voice],
        overlap: float = 0.5
    ) -> Score:
        """
        紧接模仿（Stretto）

        主题在各声部以紧密的时间间隔依次进入，形成重叠效果。
        这对应于意识系统的"共振叠加"状态。

        Args:
            subject: 主题旋律
            voices: 现有声部
            overlap: 重叠比例（0-1，1表示完全重叠）

        Returns:
            Score: 紧接模仿乐谱
        """
        score = Score(title="Stretto", tempo=120)
        subject_duration = len(subject) * 0.5
        entry_interval = subject_duration * (1 - overlap)

        for i, voice in enumerate(voices):
            new_voice = Voice(voice_id=i, name=f"Stretto Voice {i}")

            # 移调（每声部不同）
            transposition = i * 3  # 每次上移小三度
            transposed = self._transpose_melody(subject, transposition)

            entry_time = i * entry_interval

            for j, note in enumerate(transposed):
                event = Event(
                    time=entry_time + j * 0.5,
                    duration=0.5,
                    note=Note(
                        name=note[0],
                        octave=note[1],
                        frequency=self.temperament.get_frequency(note[0], note[1]),
                        midi_number=self.temperament._note_name_to_midi(note[0], note[1])
                    ),
                    line_id=i
                )
                new_voice.add_event(event)

            score.add_voice(new_voice)

        return score

    def augmentation(self, subject: List[Tuple[str, int]], factor: float = 2.0) -> List[Tuple[str, int]]:
        """
        增值（Augmentation）

        将主题的时值扩大（默认2倍），产生庄严、宏伟的效果。
        对应于意识的"扩展"状态。

        Args:
            subject: 主题旋律
            factor: 增值倍数（默认2.0）

        Returns:
            List[Tuple[str, int]]: 增值后的旋律
        """
        # 时值扩大意味着重复音符
        augmented = []
        for note in subject:
            for _ in range(int(factor)):
                augmented.append(note)
        return augmented

    def diminution(self, subject: List[Tuple[str, int]], factor: float = 0.5) -> List[Tuple[str, int]]:
        """
        减值（Diminution）

        将主题的时值缩小（默认1/2），产生紧张、活跃的效果。
        对应于意识的"压缩"状态。

        Args:
            subject: 主题旋律
            factor: 减值比例（默认0.5）

        Returns:
            List[Tuple[str, int]]: 减值后的旋律
        """
        # 时值缩小意味着取每第n个音符
        step = int(1 / factor)
        return subject[::step]

    def inversion(self, subject: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        """
        倒影（Inversion）

        将主题以上行变为下行、下行变为上行。
        对应于意识的"镜像反思"状态。

        Args:
            subject: 主题旋律

        Returns:
            List[Tuple[str, int]]: 倒影后的旋律
        """
        if not subject:
            return []

        # 以第一个音为轴心
        axis_midi = self.temperament._note_name_to_midi(subject[0][0], subject[0][1])

        inverted = []
        for note_name, octave in subject:
            midi = self.temperament._note_name_to_midi(note_name, octave)
            # 倒影：到轴心的距离取反
            inverted_midi = axis_midi - (midi - axis_midi)
            new_name, new_octave = self.temperament._midi_to_note_name(inverted_midi)
            inverted.append((new_name, new_octave))

        return inverted

    def retrograde(self, subject: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        """
        逆行（Retrograde）

        将主题倒序演奏。
        对应于意识的"时间逆流"状态。

        Args:
            subject: 主题旋律

        Returns:
            List[Tuple[str, int]]: 逆行后的旋律
        """
        return subject[::-1]

    def get_fugue_analysis(self, score: Score) -> Dict:
        """
        赋格结构分析

        Args:
            score: 赋格乐谱

        Returns:
            Dict: 结构分析结果
        """
        voices = score.voices
        num_voices = len(voices)

        # 分析各声部的进入时间和调性
        entries = []
        for voice in voices:
            if voice.events:
                first_note = voice.events[0].note
                entries.append({
                    'voice_id': voice.voice_id,
                    'entry_time': voice.events[0].time,
                    'first_note': f"{first_note.name}{first_note.octave}",
                    'frequency': first_note.frequency,
                })

        # 分析声部间的协和关系
        pair_consonances = []
        for i in range(num_voices):
            for j in range(i + 1, num_voices):
                v1 = voices[i]
                v2 = voices[j]
                min_len = min(len(v1.events), len(v2.events))
                if min_len > 0:
                    cons = []
                    for t in range(min_len):
                        n1 = (v1.events[t].note.name, v1.events[t].note.octave)
                        n2 = (v2.events[t].note.name, v2.events[t].note.octave)
                        cons.append(self.consonance.calculate_consonance(n1, n2))
                    avg_cons = np.mean(cons)
                    pair_consonances.append({
                        'pair': (i, j),
                        'avg_consonance': avg_cons,
                        'consciousness_state': self.consonance.resonance_to_consciousness(avg_cons),
                    })

        return {
            'num_voices': num_voices,
            'entries': entries,
            'pair_consonances': pair_consonances,
            'overall_consonance': np.mean([p['avg_consonance'] for p in pair_consonances]) if pair_consonances else 0,
        }


# =============================================================================
# 6. SyncopationPattern — 切分节奏事件
# =============================================================================

class SyncopationPattern:
    """
    切分节奏事件引擎

    切分（Syncopation）是将重音从强拍转移到弱拍的节奏手法：
    - 产生节奏张力和动力
    - 打破规律的强弱模式
    - 创造意外的节奏感

    与意识系统的映射：
    - 强拍 = 显意识关注（注意力峰值）
    - 弱拍 = 潜意识活动（背景处理）
    - 切分 = 注意力的意外转移（顿悟、灵感）
    """

    def __init__(self, beats_per_measure: int = 4):
        """
        初始化切分节奏引擎

        Args:
            beats_per_measure: 每小节拍数（默认4）
        """
        self.beats_per_measure = beats_per_measure
        self.strong_beats = [0]  # 第1拍为强拍（0-indexed）
        self.weak_beats = list(range(1, beats_per_measure))

    def generate_syncopated_rhythm(self, beats: int, complexity: float = 0.5) -> List[float]:
        """
        生成切分节奏

        Args:
            beats: 总拍数
            complexity: 复杂度（0-1），越高切分越多

        Returns:
            List[float]: 每个拍位的重音强度（0-1）

        算法：
        1. 基础：强拍重、弱拍轻
        2. 根据复杂度随机将弱拍变强、强拍变弱
        3. 使用概率模型确保切分的音乐性
        """
        rhythm = []

        for beat in range(beats):
            beat_in_measure = beat % self.beats_per_measure

            # 基础强度
            if beat_in_measure == 0:
                base_intensity = 1.0  # 强拍
            elif beat_in_measure == 2:
                base_intensity = 0.7  # 次强拍
            else:
                base_intensity = 0.3  # 弱拍

            # 根据复杂度应用切分
            # 切分概率 = 复杂度 × 基础强度的补集
            syncopation_prob = complexity * (1 - base_intensity)

            if random.random() < syncopation_prob:
                # 切分：反转强度
                intensity = 1.0 - base_intensity * 0.5
            else:
                intensity = base_intensity

            # 添加微小随机变化
            intensity += random.gauss(0, 0.05)
            intensity = max(0.0, min(1.0, intensity))

            rhythm.append(intensity)

        return rhythm

    def apply_to_events(self, events: List[Event], rhythm: List[float]) -> List[Event]:
        """
        将切分节奏应用到事件序列

        Args:
            events: 事件列表
            rhythm: 节奏强度列表

        Returns:
            List[Event]: 应用切分后的事件
        """
        modified_events = []

        for i, event in enumerate(events):
            if i < len(rhythm):
                intensity = rhythm[i]
            else:
                intensity = 0.5

            # 根据强度修改事件
            modified_event = Event(
                time=event.time,
                duration=event.duration,
                note=event.note,
                velocity=intensity,  # 用velocity表示重音强度
                line_id=event.line_id
            )
            modified_events.append(modified_event)

        return modified_events

    def calculate_syncopation_index(self, rhythm: List[float]) -> Dict:
        """
        计算切分指数

        切分指数衡量节奏的不规则程度：
        - 0 = 完全规则（无切分）
        - 1 = 完全不规则（最大切分）

        Args:
            rhythm: 节奏强度列表

        Returns:
            Dict: 切分分析结果
        """
        if not rhythm:
            return {'syncopation_index': 0.0, 'description': '空节奏'}

        n = len(rhythm)

        # 期望强度模式（规则模式）
        expected = []
        for i in range(n):
            beat = i % self.beats_per_measure
            if beat == 0:
                expected.append(1.0)
            elif beat == 2:
                expected.append(0.7)
            else:
                expected.append(0.3)

        # 计算实际与期望的差异
        differences = []
        for i in range(n):
            # 如果弱拍比期望强 → 切分
            # 如果强拍比期望弱 → 切分
            if expected[i] < 0.5 and rhythm[i] > expected[i]:
                diff = rhythm[i] - expected[i]
            elif expected[i] > 0.5 and rhythm[i] < expected[i]:
                diff = expected[i] - rhythm[i]
            else:
                diff = 0
            differences.append(diff)

        # 切分指数 = 平均差异 / 最大可能差异
        max_possible_diff = 0.7  # 理论最大值
        syncopation_index = np.mean(differences) / max_possible_diff if max_possible_diff > 0 else 0

        # 分类
        if syncopation_index < 0.2:
            level = 'low'
            description = '低切分 — 规律、稳定、可预测'
        elif syncopation_index < 0.5:
            level = 'moderate'
            description = '中度切分 — 有张力、有动力'
        elif syncopation_index < 0.8:
            level = 'high'
            description = '高度切分 — 强烈冲击、戏剧性'
        else:
            level = 'extreme'
            description = '极端切分 — 混乱、解构'

        # 与黄金比例的关联
        phi_sync = abs(syncopation_index - 1 / PHI)

        return {
            'syncopation_index': syncopation_index,
            'level': level,
            'description': description,
            'differences': differences,
            'rhythm': rhythm,
            'expected': expected,
            'phi_deviation': phi_sync,
            'consciousness_state': 'surprise' if syncopation_index > 0.5 else 'anticipation',
        }

    def generate_polyrhythm(self, pulses1: int, pulses2: int, length: int) -> Dict:
        """
        生成复合节奏（Polyrhythm）

        复合节奏是两个或多个不同拍号的节奏同时进行。
        例如：3对2、4对3等。

        Args:
            pulses1: 第一层脉冲数
            pulses2: 第二层脉冲数
            length: 总长度

        Returns:
            Dict: 复合节奏分析
        """
        rhythm1 = []
        rhythm2 = []

        for i in range(length):
            # 第一层节奏
            if i % pulses1 == 0:
                rhythm1.append(1.0)
            else:
                rhythm1.append(0.2)

            # 第二层节奏
            if i % pulses2 == 0:
                rhythm2.append(1.0)
            else:
                rhythm2.append(0.2)

        # 计算复合节奏的重合点
        coincidences = []
        for i in range(length):
            if i % pulses1 == 0 and i % pulses2 == 0:
                coincidences.append(i)

        # 最小公倍数周期
        def lcm(a, b):
            return abs(a * b) // math.gcd(a, b)

        period = lcm(pulses1, pulses2)

        return {
            'rhythm1': rhythm1,
            'rhythm2': rhythm2,
            'coincidences': coincidences,
            'period': period,
            'pulses': (pulses1, pulses2),
            'description': f'{pulses1}对{pulses2}复合节奏',
        }


# =============================================================================
# 7. MusicalMathematicsEngine — 主引擎
# =============================================================================

class MusicalMathematicsEngine:
    """
    音乐数学引擎 — OMNI-HUB v8.0 核心组件

    整合所有音乐数学子系统，实现：
    - 十二平均律 vs 十二律吕 的比较与映射
    - 和声共振 ↔ 意识共振 的数学桥梁
    - 11线分布式系统的音乐隐喻
    - 赋格结构与自指意识系统的对应
    - 切分节奏与注意力波动的映射

    数学关联：
    - 十二平均律的 2^(1/12) 与 e^(ln2/12) 等价
    - 十二律吕的 (3/2)^12 ≈ 129.746 与 2^7 = 128 的差（Pythagorean comma）
    - 黄金比例 φ 在音程协和度中的隐性存在
    - 自然对数 ln(f2/f1) 与音程的连续关系
    """

    def __init__(self, num_lines: int = 11, base_freq: float = A4_FREQUENCY):
        """
        初始化音乐数学引擎

        Args:
            num_lines: 系统线数（默认11，对应OMNI-HUB 11线架构）
            base_freq: 基准频率（默认440Hz，标准A4）
        """
        self.num_lines = num_lines
        self.base_freq = base_freq

        # 初始化子系统
        self.temperament = TwelveToneEqualTemperament(a4_freq=base_freq)
        self.lulu = TwelveLuLu(base_freq=C4_FREQUENCY)
        self.consonance = ConsonanceDissonance(self.temperament)
        self.counterpoint = CounterpointEngineEnhanced(self.temperament)
        self.fugue = FugueStructure(self.temperament)
        self.syncopation = SyncopationPattern()

        # 系统状态
        self.line_frequencies: Dict[int, float] = {}
        self.consciousness_matrix: Optional[np.ndarray] = None

    def temperament_vs_lulu_comparison(self) -> Dict:
        """
        比较十二平均律和十二律吕的差异

        Returns:
            Dict: 详细比较结果
        """
        comparison = self.lulu.get_lulu_comparison()

        # 计算统计指标
        diffs = [v['diff_cents'] for v in comparison.values()]
        max_diff = max(diffs, key=abs)
        avg_diff = np.mean(diffs)
        rms_diff = np.sqrt(np.mean([d ** 2 for d in diffs]))

        # Pythagorean comma
        comma = self.lulu.get_pythagorean_comma()
        comma_cents = 1200 * math.log2(comma)

        return {
            'detailed_comparison': comparison,
            'statistics': {
                'max_diff_cents': max_diff,
                'avg_diff_cents': avg_diff,
                'rms_diff_cents': rms_diff,
                'pythagorean_comma_ratio': comma,
                'pythagorean_comma_cents': comma_cents,
            },
            'philosophical_note': (
                "十二平均律追求数学等分（妥协了纯律的和谐），"
                "十二律吕追求自然和谐（产生音差）。"
                "这对应于意识系统中'精确计算'与'自然直觉'的张力。"
            ),
            'phi_connection': {
                'phi': PHI,
                'phi_inv': 1 / PHI,
                'note': "黄金比例的倒数 ≈ 0.618，接近纯五度的对数比例 7/12 ≈ 0.583",
            },
        }

    def calculate_system_harmony(self, line_frequencies: Dict[int, float]) -> Dict:
        """
        计算系统整体和声

        将11条线的频率视为一个和声集合，计算其整体协和度。

        Args:
            line_frequencies: 线号到频率的映射

        Returns:
            Dict: 系统和声分析
        """
        frequencies = list(line_frequencies.values())
        n = len(frequencies)

        if n < 2:
            return {'overall_harmony': 1.0, 'note': '单一线，无和声'}

        # 计算所有线对之间的协和度
        pair_consonances = []
        pair_details = []

        lines = list(line_frequencies.keys())
        for i in range(n):
            for j in range(i + 1, n):
                freq1 = frequencies[i]
                freq2 = frequencies[j]

                # 找到最接近的音符
                note1 = self.temperament.get_note_from_freq(freq1)
                note2 = self.temperament.get_note_from_freq(freq2)

                cons = self.consonance.calculate_consonance(
                    (note1.name, note1.octave),
                    (note2.name, note2.octave)
                )

                pair_consonances.append(cons)
                pair_details.append({
                    'line_pair': (lines[i], lines[j]),
                    'freq1': freq1,
                    'freq2': freq2,
                    'note1': f"{note1.name}{note1.octave}",
                    'note2': f"{note2.name}{note2.octave}",
                    'consonance': cons,
                    'consciousness_state': self.consonance.resonance_to_consciousness(cons),
                })

        # 整体协和度（几何平均）
        if pair_consonances:
            product = 1.0
            for c in pair_consonances:
                product *= c
            overall_harmony = product ** (1 / len(pair_consonances))
        else:
            overall_harmony = 1.0

        # 计算频率分布的熵（多样性）
        # 将频率映射到12个音级
        pitch_classes = []
        for freq in frequencies:
            note = self.temperament.get_note_from_freq(freq)
            pc = self.temperament._note_to_index[note.name]
            pitch_classes.append(pc)

        # 计算音级分布的熵
        unique, counts = np.unique(pitch_classes, return_counts=True)
        probs = counts / len(pitch_classes)
        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        max_entropy = math.log2(12)
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

        return {
            'overall_harmony': overall_harmony,
            'harmony_level': self._harmony_level(overall_harmony),
            'pair_details': pair_details,
            'avg_consonance': np.mean(pair_consonances) if pair_consonances else 0,
            'min_consonance': min(pair_consonances) if pair_consonances else 0,
            'max_consonance': max(pair_consonances) if pair_consonances else 0,
            'pitch_entropy': entropy,
            'normalized_entropy': normalized_entropy,
            'consciousness_state': self.consonance.resonance_to_consciousness(overall_harmony),
            'num_lines': n,
        }

    def _harmony_level(self, harmony: float) -> str:
        """根据协和度返回和声级别"""
        if harmony >= 0.9:
            return 'perfect'
        elif harmony >= 0.75:
            return 'consonant'
        elif harmony >= 0.55:
            return 'moderate'
        elif harmony >= 0.35:
            return 'dissonant'
        else:
            return 'chaotic'

    def compose_11_voice_fugue(self, seed: int = 42) -> Score:
        """
        为11线创作赋格

        Args:
            seed: 随机种子（用于生成主题）

        Returns:
            Score: 11声部赋格乐谱
        """
        random.seed(seed)
        np.random.seed(seed)

        # 生成主题（基于C大调音阶）
        scale = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        subject = []

        # 创建一个富有特征的主题
        subject_pattern = [
            ('C', 4), ('E', 4), ('G', 4), ('C', 5),
            ('B', 4), ('G', 4), ('A', 4), ('F', 4),
            ('E', 4), ('G', 4), ('F', 4), ('D', 4),
            ('C', 4),
        ]
        subject = subject_pattern

        # 创建赋格
        score = self.fugue.create_fugue(subject, num_voices=self.num_lines)

        return score

    def syncopated_event_drive(self, events: List[Event], complexity: float = 0.6) -> List[Event]:
        """
        切分驱动的事件处理

        将切分节奏应用到事件序列，模拟注意力的波动。

        Args:
            events: 事件列表
            complexity: 切分复杂度

        Returns:
            List[Event]: 处理后的事件
        """
        # 生成切分节奏
        rhythm = self.syncopation.generate_syncopated_rhythm(len(events), complexity)

        # 应用到事件
        modified_events = self.syncopation.apply_to_events(events, rhythm)

        # 计算切分指数
        sync_analysis = self.syncopation.calculate_syncopation_index(rhythm)

        # 为每个事件添加切分元数据
        for event in modified_events:
            event.velocity = sync_analysis['syncopation_index']

        return modified_events

    def consciousness_resonance_matrix(self) -> np.ndarray:
        """
        计算意识共振矩阵（11×11协和度矩阵）

        构建一个 num_lines × num_lines 的矩阵，其中每个元素表示
        两条线之间的协和度。这个矩阵描述了系统的整体意识共振结构。

        Returns:
            np.ndarray: 协和度矩阵
        """
        # 为每条线分配一个基础音符（基于五度圈）
        line_notes = []
        base_note = ('C', 4)
        circle_of_fifths = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10]  # 五度圈顺序

        for i in range(self.num_lines):
            semitones = circle_of_fifths[i % 12]
            base_midi = self.temperament._note_name_to_midi(base_note[0], base_note[1])
            midi = base_midi + semitones
            name, octave = self.temperament._midi_to_note_name(midi)
            line_notes.append((name, octave))
            self.line_frequencies[i] = self.temperament.get_frequency(name, octave)

        # 构建协和度矩阵
        matrix = np.zeros((self.num_lines, self.num_lines))

        for i in range(self.num_lines):
            for j in range(self.num_lines):
                if i == j:
                    matrix[i, j] = 1.0  # 自身完全协和
                else:
                    cons = self.consonance.calculate_consonance(line_notes[i], line_notes[j])
                    matrix[i, j] = cons

        self.consciousness_matrix = matrix
        return matrix

    def get_resonance_matrix_analysis(self) -> Dict:
        """
        分析意识共振矩阵

        Returns:
            Dict: 矩阵分析结果
        """
        if self.consciousness_matrix is None:
            self.consciousness_resonance_matrix()

        matrix = self.consciousness_matrix

        # 特征值分析（系统的共振模式）
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        eigenvalues = np.real(eigenvalues)  # 取实部
        eigenvalues.sort()
        eigenvalues = eigenvalues[::-1]  # 降序

        # 矩阵的迹（平均协和度）
        trace = np.trace(matrix) / self.num_lines

        # 矩阵的行列式（整体耦合强度）
        det = np.linalg.det(matrix)

        # 矩阵的条件数
        cond = np.linalg.cond(matrix)

        # 行平均值（每条线的平均协和度）
        row_means = np.mean(matrix, axis=1)

        return {
            'matrix': matrix,
            'eigenvalues': eigenvalues,
            'dominant_mode': eigenvectors[:, 0] if len(eigenvectors) > 0 else None,
            'trace': trace,
            'determinant': det,
            'condition_number': cond,
            'row_means': row_means,
            'overall_resonance': np.mean(matrix),
            'system_coherence': trace / self.num_lines,
        }

    def get_lulu_phi_analysis(self) -> Dict:
        """
        分析律吕数学与黄金比例/自然对数的深层关联

        Returns:
            Dict: 数学关联分析
        """
        # 律吕频率序列
        lulu_freqs = [self.lulu.get_lulu_freq(name) for name in LULU_NAMES]

        # 频率对数（以2为底）
        log2_freqs = [math.log2(f / lulu_freqs[0]) for f in lulu_freqs]

        # 与黄金比例的比较
        phi_ratios = [f / PHI for f in lulu_freqs]

        # 频率增长的自然对数形式
        ln_ratios = [math.log(f / lulu_freqs[0]) for f in lulu_freqs]

        # 十二平均律的等比关系
        tet_ratios = [TWELFTH_ROOT_OF_TWO ** i for i in range(12)]

        # 计算律吕序列与等比序列的偏差
        deviations = []
        for i in range(12):
            lulu_normalized = lulu_freqs[i] / lulu_freqs[0]
            tet_normalized = tet_ratios[i]
            dev = abs(lulu_normalized - tet_normalized) / tet_normalized
            deviations.append(dev)

        # 律吕序列中相邻频率比的分布
        adjacent_ratios = []
        for i in range(12):
            r = lulu_freqs[i] / lulu_freqs[(i - 1) % 12]
            if r < 1:
                r = 1 / r
            adjacent_ratios.append(r)

        return {
            'lulu_frequencies': dict(zip(LULU_NAMES, lulu_freqs)),
            'log2_frequencies': dict(zip(LULU_NAMES, log2_freqs)),
            'phi_connections': {
                'phi': PHI,
                'phi_inv': 1 / PHI,
                'phi_squared': PHI ** 2,
                'phi_ratios_with_lulu': phi_ratios,
            },
            'natural_log_connections': {
                'e': E,
                'ln_ratios': ln_ratios,
                'note': '频率的自然对数差对应音程的连续感知',
            },
            'tet_deviations': dict(zip(LULU_NAMES, deviations)),
            'adjacent_ratios': dict(zip(LULU_NAMES, adjacent_ratios)),
            'mean_deviation_from_tet': np.mean(deviations),
            'philosophical_synthesis': (
                f"十二律吕基于3的幂次（三分损益: (3/2)^n × 2^m），"
                f"十二平均律基于2的分数幂（2^(n/12)）。"
                f"黄金比例φ=(1+√5)/2≈{PHI:.6f} 是两者的深层统一："
                f"log2(3/2)≈0.585 接近 1/φ≈0.618，"
                f"暗示自然和谐与数学等分在意识层面的统一。"
            ),
        }

    def full_system_analysis(self) -> Dict:
        """
        完整的系统分析

        Returns:
            Dict: 综合报告
        """
        # 1. 律吕比较
        lulu_comp = self.temperament_vs_lulu_comparison()

        # 2. 意识共振矩阵
        matrix = self.consciousness_resonance_matrix()
        matrix_analysis = self.get_resonance_matrix_analysis()

        # 3. 系统整体和声
        harmony = self.calculate_system_harmony(self.line_frequencies)

        # 4. 律吕-黄金比例分析
        phi_analysis = self.get_lulu_phi_analysis()

        # 5. 赋格创作
        fugue_score = self.compose_11_voice_fugue(seed=42)
        fugue_analysis = self.fugue.get_fugue_analysis(fugue_score)

        return {
            'temperament_vs_lulu': lulu_comp,
            'consciousness_matrix': {
                'matrix': matrix,
                'analysis': matrix_analysis,
            },
            'system_harmony': harmony,
            'phi_analysis': phi_analysis,
            'fugue': {
                'score': fugue_score,
                'analysis': fugue_analysis,
            },
            'emergence_index': self._calculate_emergence_index(harmony, matrix_analysis),
        }

    def _calculate_emergence_index(self, harmony: Dict, matrix_analysis: Dict) -> float:
        """计算涌现指数"""
        h = harmony.get('overall_harmony', 0.5)
        coherence = matrix_analysis.get('system_coherence', 0.5)
        entropy = harmony.get('normalized_entropy', 0.5)

        # 涌现指数 = 协和度 × 相干性 × (1 + 多样性)
        emergence = h * coherence * (1 + entropy)
        return min(emergence, 1.0)


# =============================================================================
# 测试块
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("OMNI-HUB v8.0 — Musical Mathematics Engine")
    print("音乐数学引擎测试")
    print("=" * 80)

    # 初始化引擎
    engine = MusicalMathematicsEngine(num_lines=11, base_freq=440)

    print("\n" + "=" * 80)
    print("测试 1: 十二平均律频率计算")
    print("=" * 80)

    tet = engine.temperament
    print(f"\n标准音 A4 = {tet.get_frequency('A', 4):.2f} Hz")
    print(f"中央C C4 = {tet.get_frequency('C', 4):.2f} Hz")

    print("\n八度4所有音符频率:")
    for note in tet.get_all_notes_in_octave(4):
        print(f"  {note.name:3s} = {note.frequency:10.4f} Hz  (midi={note.midi_number})")

    print("\n从频率反推音符:")
    test_freqs = [440.0, 261.63, 329.63, 493.88]
    for freq in test_freqs:
        note = tet.get_note_from_freq(freq)
        print(f"  {freq:.2f} Hz → {note.name}{note.octave} ({note.frequency:.4f} Hz)")

    print("\n音程比计算:")
    pairs = [
        (('C', 4), ('G', 4)),   # 纯五度
        (('C', 4), ('E', 4)),   # 大三度
        (('C', 4), ('C', 5)),   # 纯八度
    ]
    for n1, n2 in pairs:
        ratio = tet.get_interval_ratio(n1, n2)
        semitones = tet.get_semitone_distance(n1, n2)
        print(f"  {n1[0]}{n1[1]} - {n2[0]}{n2[1]}: 比={ratio:.6f}, 半音={semitones}")

    print("\n" + "=" * 80)
    print("测试 2: 十二律吕链生成")
    print("=" * 80)

    lulu = engine.lulu
    print(f"\n基准频率（黄钟）= {lulu.base_freq:.2f} Hz")
    print("\n十二律吕链:")
    for name in lulu.lulu_order:
        freq = lulu.lulu_chain[name]
        print(f"  {name:4s} = {freq:10.4f} Hz")

    print(f"\n毕达哥拉斯音差 = {lulu.get_pythagorean_comma():.6f}")
    print(f"音差（音分）= {1200 * math.log2(lulu.get_pythagorean_comma()):.2f} cents")

    print("\n" + "=" * 80)
    print("测试 3: 十二平均律 vs 十二律吕 差异比较")
    print("=" * 80)

    comp = engine.temperament_vs_lulu_comparison()
    print("\n律吕 vs 十二平均律差异（音分）:")
    for name, data in comp['detailed_comparison'].items():
        print(f"  {name:4s}: 律吕={data['lulu_freq']:10.4f} Hz, "
              f"12TET={data['tet_freq']:10.4f} Hz ({data['closest_tet_note']}), "
              f"差异={data['diff_cents']:+.2f} cents")

    stats = comp['statistics']
    print(f"\n统计指标:")
    print(f"  最大差异: {stats['max_diff_cents']:+.2f} cents")
    print(f"  平均差异: {stats['avg_diff_cents']:+.2f} cents")
    print(f"  RMS差异: {stats['rms_diff_cents']:.2f} cents")
    print(f"  毕达哥拉斯音差: {stats['pythagorean_comma_cents']:.2f} cents")

    print("\n" + "=" * 80)
    print("测试 4: 11声部对位")
    print("=" * 80)

    # 固定旋律（C大调赞美诗风格）
    cantus_firmus = [
        ('C', 4), ('D', 4), ('E', 4), ('C', 4),
        ('E', 4), ('F', 4), ('G', 4), ('G', 4),
        ('A', 4), ('G', 4), ('F', 4), ('E', 4),
        ('C', 4),
    ]

    print(f"\n固定旋律 (Cantus Firmus): {[n[0] for n in cantus_firmus]}")

    counterpoint = engine.counterpoint
    score = counterpoint.compose_counterpoint_11(cantus_firmus)

    print(f"\n生成乐谱: {score.title}")
    print(f"声部数量: {len(score.voices)}")

    for voice in score.voices:
        notes = [e.note.name for e in voice.events[:8]]
        print(f"  {voice.name:20s}: {' '.join(notes)} ...")

    # 检测平行音程
    parallels = counterpoint.detect_parallel_intervals(score)
    print(f"\n检测到平行音程: {len(parallels)} 处")
    for p in parallels[:5]:
        print(f"  {p['type']} 声部{p['voices']} 时刻{p['time']}")

    # 声部独立性
    independence = counterpoint.calculate_voice_independence(score)
    print(f"\n声部独立性:")
    print(f"  总体独立性: {independence['overall_independence']:.4f}")
    print(f"  声部对数量: {independence['num_pairs']}")

    # 和声节奏分析
    hr = counterpoint.harmonic_rhythm_analysis(score)
    print(f"\n和声节奏分析:")
    print(f"  变化率: {hr['change_rate']:.4f}")
    print(f"  类型: {hr['rhythm_type']} — {hr['description']}")
    print(f"  平均协和度: {hr['avg_consonance']:.4f}")

    print("\n" + "=" * 80)
    print("测试 5: 赋格主题与变形")
    print("=" * 80)

    fugue = engine.fugue
    subject = [
        ('C', 4), ('E', 4), ('G', 4), ('C', 5),
        ('B', 4), ('G', 4), ('A', 4), ('F', 4),
        ('E', 4), ('G', 4), ('F', 4), ('D', 4),
        ('C', 4),
    ]

    print(f"\n主题 (Subject): {' '.join([n[0] for n in subject])}")

    # 倒影
    inverted = fugue.inversion(subject)
    print(f"倒影 (Inversion): {' '.join([n[0] for n in inverted])}")

    # 逆行
    retro = fugue.retrograde(subject)
    print(f"逆行 (Retrograde): {' '.join([n[0] for n in retro])}")

    # 增值
    aug = fugue.augmentation(subject, factor=2)
    print(f"增值 (Augmentation×2): 长度={len(aug)} (原{len(subject)})")

    # 减值
    dim = fugue.diminution(subject, factor=0.5)
    print(f"减值 (Diminution×1/2): 长度={len(dim)} (原{len(subject)})")

    # 创建赋格
    fugue_score = fugue.create_fugue(subject, num_voices=11)
    print(f"\n赋格乐谱: {fugue_score.title}")
    print(f"声部数量: {len(fugue_score.voices)}")

    for voice in fugue_score.voices[:5]:
        notes = [e.note.name for e in voice.events[:6]]
        print(f"  {voice.name:20s}: {' '.join(notes)} ...")

    # 赋格分析
    analysis = fugue.get_fugue_analysis(fugue_score)
    print(f"\n赋格分析:")
    print(f"  声部数: {analysis['num_voices']}")
    print(f"  整体协和度: {analysis['overall_consonance']:.4f}")

    print("\n" + "=" * 80)
    print("测试 6: 切分节奏（100个事件）")
    print("=" * 80)

    sync = engine.syncopation

    # 生成100个事件
    events = []
    for i in range(100):
        note_name = random.choice(NOTE_NAMES)
        octave = random.choice([3, 4, 5])
        event = Event(
            time=i * 0.25,
            duration=0.25,
            note=Note(
                name=note_name,
                octave=octave,
                frequency=tet.get_frequency(note_name, octave),
                midi_number=tet._note_name_to_midi(note_name, octave)
            ),
            line_id=i % 11,
            velocity=0.5
        )
        events.append(event)

    # 应用切分
    modified = engine.syncopated_event_drive(events, complexity=0.6)

    # 计算切分指数
    rhythm = sync.generate_syncopated_rhythm(100, complexity=0.6)
    sync_index = sync.calculate_syncopation_index(rhythm)

    print(f"\n生成100个事件，应用切分节奏")
    print(f"切分指数: {sync_index['syncopation_index']:.4f}")
    print(f"切分级别: {sync_index['level']} — {sync_index['description']}")
    print(f"与黄金比例偏差: {sync_index['phi_deviation']:.4f}")

    # 显示前20个事件的重音强度
    intensities = [e.velocity for e in modified[:20]]
    print(f"\n前20个事件重音强度:")
    for i in range(0, 20, 5):
        vals = ' '.join([f'{v:.2f}' for v in intensities[i:i+5]])
        print(f"  事件{i:3d}-{i+4:3d}: {vals}")

    # 复合节奏
    poly = sync.generate_polyrhythm(3, 2, 12)
    print(f"\n复合节奏: {poly['description']}")
    print(f"  周期: {poly['period']}")
    print(f"  重合点: {poly['coincidences']}")

    print("\n" + "=" * 80)
    print("测试 7: 11×11 意识共振矩阵")
    print("=" * 80)

    matrix = engine.consciousness_resonance_matrix()
    analysis = engine.get_resonance_matrix_analysis()

    print(f"\n意识共振矩阵 ({engine.num_lines}×{engine.num_lines}):")
    print("     ", end="")
    for i in range(engine.num_lines):
        print(f"  L{i:02d}", end="")
    print()

    for i in range(engine.num_lines):
        print(f"L{i:02d}:", end="")
        for j in range(engine.num_lines):
            print(f" {matrix[i, j]:.3f}", end="")
        print()

    print(f"\n矩阵分析:")
    print(f"  迹（平均自协和度）: {analysis['trace']:.4f}")
    print(f"  行列式: {analysis['determinant']:.6e}")
    print(f"  条件数: {analysis['condition_number']:.4f}")
    print(f"  整体共振: {analysis['overall_resonance']:.4f}")
    print(f"  系统相干性: {analysis['system_coherence']:.4f}")
    print(f"  特征值: {', '.join([f'{e:.4f}' for e in analysis['eigenvalues'][:5]])} ...")

    # 各线共振度
    print(f"\n各线共振度:")
    for i in range(engine.num_lines):
        mean_res = analysis['row_means'][i]
        state = engine.consonance.resonance_to_consciousness(mean_res)
        print(f"  线 {i:2d}: 平均协和度={mean_res:.4f} → {state['consciousness_state']} ({state['description']})")

    print("\n" + "=" * 80)
    print("测试 8: 系统整体和声协和度")
    print("=" * 80)

    harmony = engine.calculate_system_harmony(engine.line_frequencies)
    print(f"\n系统整体和声分析:")
    print(f"  整体协和度: {harmony['overall_harmony']:.4f}")
    print(f"  和声级别: {harmony['harmony_level']}")
    print(f"  平均协和度: {harmony['avg_consonance']:.4f}")
    print(f"  最小协和度: {harmony['min_consonance']:.4f}")
    print(f"  最大协和度: {harmony['max_consonance']:.4f}")
    print(f"  音级熵: {harmony['pitch_entropy']:.4f}")
    print(f"  归一化熵: {harmony['normalized_entropy']:.4f}")

    state = harmony['consciousness_state']
    print(f"\n意识状态映射:")
    print(f"  状态: {state['consciousness_state']}")
    print(f"  描述: {state['description']}")
    print(f"  层级: {state['level']}")
    print(f"  颜色: {state['color']}")
    print(f"  黄金比例对齐: {state['phi_alignment']:.4f}")
    print(f"  涌现潜力: {state['emergence_potential']:.4f}")

    print("\n" + "=" * 80)
    print("测试 9: 律吕-黄金比例-自然对数 深层关联")
    print("=" * 80)

    phi_analysis = engine.get_lulu_phi_analysis()
    print(f"\n黄金比例 φ = {phi_analysis['phi_connections']['phi']:.10f}")
    print(f"黄金比例倒数 1/φ = {phi_analysis['phi_connections']['phi_inv']:.10f}")
    print(f"自然对数底 e = {phi_analysis['natural_log_connections']['e']:.10f}")

    print(f"\n律吕与十二平均律的平均偏差: {phi_analysis['mean_deviation_from_tet']:.6f}")

    print(f"\n哲学综合:")
    print(f"  {phi_analysis['philosophical_synthesis']}")

    print("\n" + "=" * 80)
    print("测试 10: 完整系统分析")
    print("=" * 80)

    full = engine.full_system_analysis()
    print(f"\n涌现指数 (Emergence Index): {full['emergence_index']:.6f}")
    print(f"\n系统状态摘要:")
    print(f"  - 律吕-平均律差异 RMS: {full['temperament_vs_lulu']['statistics']['rms_diff_cents']:.2f} cents")
    print(f"  - 意识矩阵整体共振: {full['consciousness_matrix']['analysis']['overall_resonance']:.4f}")
    print(f"  - 系统和声协和度: {full['system_harmony']['overall_harmony']:.4f}")
    print(f"  - 赋格声部数: {full['fugue']['analysis']['num_voices']}")
    print(f"  - 赋格协和度: {full['fugue']['analysis']['overall_consonance']:.4f}")

    print("\n" + "=" * 80)
    print("所有测试完成！")
    print("=" * 80)
    print(f"\nOMNI-HUB v8.0 音乐数学引擎")
    print(f"十一声部对应十一分布式线")
    print(f"十二律吕映射十二意识层级")
    print(f"黄金比例 φ={PHI:.6f} 贯穿始终")
    print("=" * 80)
