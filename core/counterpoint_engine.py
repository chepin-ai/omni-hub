
__version__ = "11.0.0"
"""
OMNI-HUB v4.0 - Counterpoint Engine Module
对位引擎与验证系统

核心命题: 和声不是齐唱，对位即显化

对位法则:
1. 禁止平行五度/八度 → 线间差异化
2. 反向进行优先 → 一进一退
3. 声部超越 → 打破层级固化
4. 协和音程 → 量化线间和谐度
5. 解决规则 → 张力松弛动力学
6. 休止艺术 → qgl沉默的价值
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.collections import LineCollection
import seaborn as sns
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import warnings

# Import CantusFirmus
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from cantus_firmus import CantusFirmus
import logging


# =============================================================================
# 1. CONSONANCE CALCULATOR - 协和度计算
# =============================================================================

@dataclass
class ConsonanceProfile:
    """协和度配置"""
    perfect_consonance: float = 1.0   # 完美协和
    imperfect_consonance: float = 0.7  # 不完全协和
    dissonance: float = 0.3            # 不协和
    perfect_unison_bonus: float = 0.1  # 齐唱惩罚


class ConsonanceCalculator:
    """
    协和度计算器
    
    协和音程分类:
    - 完美协和: 纯一度(0半音)、纯八度(12)、纯五度(7) → 协和度=1.0
    - 不完全协和: 大三度(4)、小三度(3)、大六度(9)、小六度(8) → 协和度=0.7
    - 不协和: 大二度(2)、小二度(1)、大七度(11)、小七度(10)、三全音(6) → 协和度=0.3
    """
    
    # 协和度映射表（基于半音间隔）
    INTERVAL_CONSONANCE = {
        0: 1.0,   # 纯一度 (同音)
        1: 0.3,   # 小二度
        2: 0.3,   # 大二度
        3: 0.7,   # 小三度
        4: 0.7,   # 大三度
        5: 0.5,   # 纯四度 (不完全)
        6: 0.3,   # 三全音 (极不协和)
        7: 1.0,   # 纯五度
        8: 0.7,   # 小六度
        9: 0.7,   # 大六度
        10: 0.3,  # 小七度
        11: 0.3,  # 大七度
        12: 1.0,  # 纯八度
    }
    
    def __init__(self, profile: Optional[ConsonanceProfile] = None):
        self.profile = profile or ConsonanceProfile()
    
    def interval_consonance(self, pitch_a: int, pitch_b: int) -> float:
        """
        计算两音的协和度
        
        Args:
            pitch_a, pitch_b: MIDI note numbers
            
        Returns:
            协和度 [0, 1]
        """
        interval = abs(pitch_a - pitch_b) % 12
        base = self.INTERVAL_CONSONANCE.get(interval, 0.3)
        
        # 同音惩罚（齐唱不应该得高分）
        if interval == 0 and pitch_a == pitch_b:
            return self.profile.perfect_unison_bonus
        
        return base
    
    def chord_consonance(self, pitches: List[int]) -> float:
        """
        多音和弦的协和度
        
        计算所有音对协和度的加权平均
        
        Args:
            pitches: 和弦内所有音高
            
        Returns:
            和弦协和度 [0, 1]
        """
        if len(pitches) < 2:
            return 1.0
        
        pairs = []
        for i in range(len(pitches)):
            for j in range(i + 1, len(pitches)):
                pairs.append((pitches[i], pitches[j]))
        
        if not pairs:
            return 1.0
        
        consonances = [self.interval_consonance(a, b) for a, b in pairs]
        return float(np.mean(consonances))
    
    def matrix_at(self, t: int, all_pitches: List[List[int]]) -> np.ndarray:
        """
        t时刻的协和度矩阵
        
        Args:
            t: 拍点
            all_pitches: 所有声部的音高序列
            
        Returns:
            n×n 协和度矩阵
        """
        n_voices = len(all_pitches)
        matrix = np.zeros((n_voices, n_voices))
        
        for i in range(n_voices):
            for j in range(n_voices):
                if t < len(all_pitches[i]) and t < len(all_pitches[j]):
                    matrix[i, j] = self.interval_consonance(
                        all_pitches[i][t], all_pitches[j][t]
                    )
                else:
                    matrix[i, j] = 0.0
        
        return matrix
    
    def tension_index(self, t: int, all_pitches: List[List[int]]) -> float:
        """
        张力指数（1 - 协和度）
        
        高张力 = 不协和，低张力 = 协和
        
        Args:
            t: 拍点
            all_pitches: 所有声部的音高序列
            
        Returns:
            张力指数 [0, 1]
        """
        chord_pitches = []
        for vp in all_pitches:
            if t < len(vp):
                chord_pitches.append(vp[t])
        
        if len(chord_pitches) < 2:
            return 0.0
        
        cons = self.chord_consonance(chord_pitches)
        return 1.0 - cons
    
    def get_interval_name(self, pitch_a: int, pitch_b: int) -> str:
        """获取音程名称"""
        interval = abs(pitch_a - pitch_b) % 12
        names = {
            0: '纯一度', 1: '小二度', 2: '大二度', 3: '小三度',
            4: '大三度', 5: '纯四度', 6: '三全音', 7: '纯五度',
            8: '小六度', 9: '大六度', 10: '小七度', 11: '大七度',
            12: '纯八度'
        }
        return names.get(interval, f'未知({interval})')


# =============================================================================
# 2. VOICE LEADING - 声部进行规则
# =============================================================================

@dataclass
class VoiceLeadingViolation:
    """声部进行违规记录"""
    type: str          # 'parallel_fifth', 'parallel_octave', 'voice_crossing', 'illegal_leap'
    beat: int          # 发生拍点
    voices: Tuple[int, int]  # 涉及的声部
    description: str   # 描述


class VoiceLeading:
    """
    声部进行规则检查器
    
    核心规则:
    1. 禁止平行五度/八度
    2. 反向进行优先
    3. 声部超越记录
    4. 非法跳进检测
    """
    
    def __init__(self):
        self.violations: List[VoiceLeadingViolation] = []
    
    def _get_interval_class(self, pitch_a: int, pitch_b: int) -> int:
        """获取音程类别（模12）"""
        return abs(pitch_a - pitch_b) % 12
    
    def check_parallel_fifths(self, history: List[List[int]]) -> List[VoiceLeadingViolation]:
        """
        检测平行五度
        
        规则: 连续两拍，两条线同向移动形成纯五度
        """
        violations = []
        if len(history) < 2:
            return violations
        
        n_voices = len(history[0])
        
        for beat in range(len(history) - 1):
            for i in range(n_voices):
                for j in range(i + 1, n_voices):
                    # 当前拍
                    int1 = self._get_interval_class(history[beat][i], history[beat][j])
                    # 下一拍
                    int2 = self._get_interval_class(history[beat + 1][i], history[beat + 1][j])
                    
                    # 方向
                    dir_i = np.sign(history[beat + 1][i] - history[beat][i])
                    dir_j = np.sign(history[beat + 1][j] - history[beat][j])
                    
                    # 平行五度条件: 连续五度 + 同向
                    if int1 == 7 and int2 == 7 and dir_i == dir_j and dir_i != 0:
                        v = VoiceLeadingViolation(
                            type='parallel_fifth',
                            beat=beat,
                            voices=(i, j),
                            description=f'声部{i}与{j}在拍{beat}-{beat+1}平行五度'
                        )
                        violations.append(v)
        
        return violations
    
    def check_parallel_octaves(self, history: List[List[int]]) -> List[VoiceLeadingViolation]:
        """
        检测平行八度
        
        规则: 连续两拍，两条线同向移动形成纯八度
        """
        violations = []
        if len(history) < 2:
            return violations
        
        n_voices = len(history[0])
        
        for beat in range(len(history) - 1):
            for i in range(n_voices):
                for j in range(i + 1, n_voices):
                    int1 = self._get_interval_class(history[beat][i], history[beat][j])
                    int2 = self._get_interval_class(history[beat + 1][i], history[beat + 1][j])
                    
                    dir_i = np.sign(history[beat + 1][i] - history[beat][i])
                    dir_j = np.sign(history[beat + 1][j] - history[beat][j])
                    
                    if int1 == 0 and int2 == 0 and dir_i == dir_j and dir_i != 0:
                        v = VoiceLeadingViolation(
                            type='parallel_octave',
                            beat=beat,
                            voices=(i, j),
                            description=f'声部{i}与{j}在拍{beat}-{beat+1}平行八度'
                        )
                        violations.append(v)
        
        return violations
    
    def check_voice_crossing(self, history: List[List[int]], 
                             voice_order: Optional[List[int]] = None) -> List[VoiceLeadingViolation]:
        """
        检测声部超越
        
        允许，但记录。高SI线暂时低于低SI线是打破层级固化的表现。
        """
        violations = []
        if len(history) < 1:
            return violations
        
        n_voices = len(history[0])
        order = voice_order or list(range(n_voices))
        
        for beat in range(len(history)):
            pitches = history[beat]
            # 检查相邻声部是否交叉
            for idx in range(len(order) - 1):
                higher_voice = order[idx]      # 理论上更高的声部
                lower_voice = order[idx + 1]   # 理论上更低的声部
                
                if pitches[higher_voice] < pitches[lower_voice]:
                    v = VoiceLeadingViolation(
                        type='voice_crossing',
                        beat=beat,
                        voices=(higher_voice, lower_voice),
                        description=f'声部{higher_voice}({pitches[higher_voice]})低于声部{lower_voice}({pitches[lower_voice]})'
                    )
                    violations.append(v)
        
        return violations
    
    def check_illegal_leaps(self, history: List[List[int]], max_leap: int = 12) -> List[VoiceLeadingViolation]:
        """
        检测非法跳进
        
        规则: 单声部跳进超过指定范围
        """
        violations = []
        if len(history) < 2:
            return violations
        
        n_voices = len(history[0])
        
        for beat in range(len(history) - 1):
            for v in range(n_voices):
                leap = abs(history[beat + 1][v] - history[beat][v])
                if leap > max_leap:
                    vio = VoiceLeadingViolation(
                        type='illegal_leap',
                        beat=beat,
                        voices=(v,),
                        description=f'声部{v}在拍{beat}-{beat+1}跳进{leap}半音'
                    )
                    violations.append(vio)
        
        return violations
    
    def leading_score(self, history: List[List[int]]) -> Dict[str, float]:
        """
        声部进行综合评分
        
        Returns:
            各项指标的字典
        """
        if len(history) < 2:
            return {'overall': 0.0}
        
        n_voices = len(history[0])
        n_beats = len(history)
        
        scores = {}
        
        # 1. 反向进行比例（越高越好）
        contrary_count = 0
        total_motion_pairs = 0
        
        for beat in range(n_beats - 1):
            for i in range(n_voices):
                for j in range(i + 1, n_voices):
                    dir_i = np.sign(history[beat + 1][i] - history[beat][i])
                    dir_j = np.sign(history[beat + 1][j] - history[beat][j])
                    
                    if dir_i != 0 and dir_j != 0:
                        total_motion_pairs += 1
                        if dir_i == -dir_j:
                            contrary_count += 1
        
        scores['contrary_ratio'] = contrary_count / max(total_motion_pairs, 1)
        
        # 2. 斜向进行比例（一条保持，另一条移动）
        oblique_count = 0
        for beat in range(n_beats - 1):
            for i in range(n_voices):
                for j in range(i + 1, n_voices):
                    dir_i = np.sign(history[beat + 1][i] - history[beat][i])
                    dir_j = np.sign(history[beat + 1][j] - history[beat][j])
                    
                    if (dir_i == 0 and dir_j != 0) or (dir_i != 0 and dir_j == 0):
                        oblique_count += 1
        
        total_pairs = n_voices * (n_voices - 1) // 2 * (n_beats - 1)
        scores['oblique_ratio'] = oblique_count / max(total_pairs, 1)
        
        # 3. 同向进行比例（越低越好）
        similar_count = 0
        for beat in range(n_beats - 1):
            for i in range(n_voices):
                for j in range(i + 1, n_voices):
                    dir_i = np.sign(history[beat + 1][i] - history[beat][i])
                    dir_j = np.sign(history[beat + 1][j] - history[beat][j])
                    
                    if dir_i != 0 and dir_j != 0 and dir_i == dir_j:
                        similar_count += 1
        
        scores['similar_ratio'] = similar_count / max(total_pairs, 1)
        
        # 4. 平行违规检测
        pf = self.check_parallel_fifths(history)
        po = self.check_parallel_octaves(history)
        scores['parallel_violations'] = len(pf) + len(po)
        
        # 5. 综合评分（归一化）
        max_possible_violations = (n_voices * (n_voices - 1) // 2) * (n_beats - 1)
        violation_penalty = min(1.0, scores['parallel_violations'] / max(max_possible_violations * 0.05, 1))
        
        scores['overall'] = (
            scores['contrary_ratio'] * 0.4 +
            scores['oblique_ratio'] * 0.25 +
            (1 - scores['similar_ratio']) * 0.2 +
            (1 - violation_penalty) * 0.15
        )
        scores['overall'] = max(0.0, min(1.0, scores['overall']))
        
        return scores


# =============================================================================
# 3. COUNTERPOINT ENGINE - 对位引擎
# =============================================================================

class Voice:
    """单个声部"""
    
    def __init__(self, name: str, si_level: float, base_octave: int):
        """
        Args:
            name: 声部名称
            si_level: 系统重要性层级 [0, 1]
            base_octave: 基础八度
        """
        self.name = name
        self.si_level = si_level
        self.base_octave = base_octave
        self.pitches: List[int] = []
        self.active: List[bool] = []  # 是否活跃（非休止）
        self.is_qgl: bool = False     # 是否为qgl声部
    
    def get_pitch_at(self, beat: int) -> Optional[int]:
        if beat < len(self.pitches):
            return self.pitches[beat] if self.active[beat] else None
        return None


class CounterpointEngine:
    """
    对位引擎
    
    生成和管理多声部对位作品
    """
    
    def __init__(self, cantus_firmus: CantusFirmus, n_voices: int = 4, seed: Optional[int] = None):
        """
        Args:
            cantus_firmus: 固定旋律
            n_voices: 声部数量
            seed: 随机种子
        """
        self.cf = cantus_firmus
        self.n_voices = n_voices
        self._rng = np.random.RandomState(seed)
        
        self.consonance_calc = ConsonanceCalculator()
        self.voice_leading = VoiceLeading()
        
        self.voices: List[Voice] = []
        self.composed = False
        self.score_history: List[List[int]] = []
        self.tension_curve: List[float] = []
        
        # qgl相关
        self.qgl_voice_idx: Optional[int] = None
        self.qgl_active_beats: List[int] = []
        
        self._setup_voices()
    
    def _setup_voices(self):
        """初始化声部配置"""
        # 声部配置：名称、SI层级、基础八度
        voice_configs = [
            ('Soprano', 0.95, 5),    # C5区域
            ('Alto', 0.85, 4),       # C4区域
            ('Tenor', 0.75, 3),      # C3区域
            ('Bass', 0.65, 2),       # C2区域
            ('Contrabass', 0.55, 1), # C1区域
            ('Mezzo', 0.80, 4),      # 补充声部
            ('Baritone', 0.70, 3),   # 补充声部
            ('Sub-bass', 0.45, 0),   # 极低音
            ('Descant', 0.90, 6),    # 极高音
            ('Inner1', 0.78, 3),     # 内声部
            ('Inner2', 0.72, 3),     # 内声部
        ]
        
        for i in range(min(self.n_voices, len(voice_configs))):
            name, si, octv = voice_configs[i]
            voice = Voice(name, si, octv)
            
            # 最后一个声部设为qgl
            if i == self.n_voices - 1:
                voice.is_qgl = True
                self.qgl_voice_idx = i
            
            self.voices.append(voice)
    
    def _get_scale_notes(self, octave: int) -> List[int]:
        """获取某八度内的调内音"""
        base = 12 * (octave + 1)  # C=12, C1=24, etc.
        return [base + i for i in self.cf.scale]
    
    def _get_parallel_violations_for_beat(self, beat: int, new_pitch: int, 
                                          voice_idx: int, 
                                          current_pitches: List,
                                          prev_pitches: List) -> int:
        """检查添加新音符会产生多少平行违规"""
        if beat == 0 or prev_pitches is None:
            return 0
        
        violations = 0
        for other_idx in range(len(current_pitches)):
            if other_idx == voice_idx:
                continue
            other_prev = prev_pitches[other_idx]
            other_curr = current_pitches[other_idx]
            
            # 跳过未初始化的声部
            if other_prev is None or other_curr is None or prev_pitches[voice_idx] is None:
                continue
            
            # 前一拍音程
            int1 = abs(other_prev - prev_pitches[voice_idx]) % 12
            # 当前拍音程
            int2 = abs(other_curr - new_pitch) % 12
            
            # 方向
            dir_self = np.sign(new_pitch - prev_pitches[voice_idx])
            dir_other = np.sign(other_curr - other_prev)
            
            # 平行五度
            if int1 == 7 and int2 == 7 and dir_self == dir_other and dir_self != 0:
                violations += 1
            # 平行八度
            if int1 == 0 and int2 == 0 and dir_self == dir_other and dir_self != 0:
                violations += 1
        
        return violations
    
    def _generate_beat_for_voice(self, voice: Voice, voice_idx: int, beat: int,
                                  cf_melody: List[int], prev_pitches: List,
                                  current_pitches: List) -> Tuple[int, bool]:
        """
        为单个声部在单拍生成音符 - 增强版
        
        策略：
        - 严格避免平行五度/八度
        - 强力优先反向进行
        - 各声部有不同的节奏模式
        
        返回: (pitch, is_active)
        """
        cf_note = cf_melody[beat]
        
        # 检查该声部是否应该休止（增加节奏变化）
        # qgl: 大部分休止；其他声部按SI层级决定休止频率
        # 获取前一拍的音高（用于休止时保持）
        prev_pitch_for_voice = prev_pitches[voice_idx] if prev_pitches and voice_idx < len(prev_pitches) and prev_pitches[voice_idx] is not None else cf_note
        
        if voice.is_qgl:
            # qgl在关键拍点出现（每4拍出现1次）
            if beat % 4 == 0 or (beat % 8 == 4):
                pass  # 继续生成
            else:
                return prev_pitch_for_voice, False  # 休止，保持前一音高
        else:
            # 普通声部根据SI层级和拍号决定休止
            # 低SI声部更常休止，增加纹理变化
            # 使用不同的相位使各声部不同步
            phase = int(voice.si_level * 10) % 4
            if beat % 4 == phase and self._rng.random() < 0.15:
                # 偶尔休止一拍，保持前一音高
                return prev_pitch_for_voice, False
            
            rest_prob = (1.0 - voice.si_level) * 0.06
            if beat > 0 and self._rng.random() < rest_prob:
                return prev_pitch_for_voice, False
        
        # qgl声部生成
        if voice.is_qgl:
            candidates = []
            for interval in [3, 4, 7, 8, 9]:  # 不完全协和音程
                candidates.append(cf_note + interval)
                candidates.append(cf_note - interval)
            
            candidates = [c for c in candidates 
                         if 12 * voice.base_octave <= c <= 12 * (voice.base_octave + 2)]
            if candidates:
                # 严格选择无平行违规的
                valid_candidates = []
                for cand in candidates:
                    vios = self._get_parallel_violations_for_beat(
                        beat, cand, voice_idx, current_pitches, prev_pitches
                    )
                    if vios == 0:
                        valid_candidates.append(cand)
                
                if valid_candidates:
                    pitch = self._rng.choice(valid_candidates)
                else:
                    pitch = candidates[0]
            else:
                pitch = cf_note + 12
            
            self.qgl_active_beats.append(beat)
            return pitch, True
        
        # 普通声部生成
        scale_notes = self._get_scale_notes(voice.base_octave)
        scale_notes += [n + 12 for n in scale_notes if n + 12 <= 12 * (voice.base_octave + 3)]
        scale_notes = sorted(set(scale_notes))
        
        prev_pitch = prev_pitches[voice_idx] if prev_pitches and prev_pitches[voice_idx] is not None else scale_notes[len(scale_notes) // 2]
        
        # CF方向
        if beat > 0:
            cf_dir = np.sign(cf_melody[beat] - cf_melody[beat - 1])
        else:
            cf_dir = 0
        
        # 候选音：调内音且与CF形成协和/不完全协和音程
        candidates = []
        for note in scale_notes:
            cons = self.consonance_calc.interval_consonance(note, cf_note)
            if cons >= 0.5:
                candidates.append(note)
        
        if not candidates:
            candidates = scale_notes
        
        # 第一步：过滤掉会产生平行违规的候选
        valid_candidates = []
        violation_counts = {}
        for note in candidates:
            vios = self._get_parallel_violations_for_beat(
                beat, note, voice_idx, current_pitches, prev_pitches
            )
            violation_counts[note] = vios
            if vios == 0:
                valid_candidates.append(note)
        
        # 如果所有候选都有违规，尝试休止来避免
        if not valid_candidates:
            # 检查是否可以通过休止来避免
            if beat > 0 and not voice.is_qgl:
                # 使用前一拍的音（相当于保持/休止）
                held_note = prev_pitches[voice_idx]
                if held_note is not None:
                    vios = self._get_parallel_violations_for_beat(
                        beat, held_note, voice_idx, current_pitches, prev_pitches
                    )
                    if vios == 0:
                        return held_note, False  # 休止但保持音高
            
            # 如果实在无法避免，选择违规最少的
            min_vios = min(violation_counts.values())
            valid_candidates = [n for n, v in violation_counts.items() if v == min_vios]
        
        # 第二步：为有效候选打分
        scored = []
        for note in valid_candidates:
            score = 0.0
            
            # 协和度得分
            cons = self.consonance_calc.interval_consonance(note, cf_note)
            score += cons * 2.0
            
            # 反向进行强力加分
            voice_dir = np.sign(note - prev_pitch)
            if cf_dir != 0 and voice_dir == -cf_dir:
                score += 3.0  # 强力优先反向
            elif voice_dir == 0:
                score += 0.8  # 斜向进行
            else:
                score -= 0.5  # 同向进行惩罚
            
            # 级进强力优先
            step_size = abs(note - prev_pitch)
            if step_size <= 2:
                score += 2.0
            elif step_size <= 4:
                score += 1.2
            elif step_size <= 7:
                score += 0.3
            else:
                score -= 1.0  # 大跳进惩罚
            
            # 避免与已放置声部同音
            for other_idx in range(len(current_pitches)):
                if other_idx != voice_idx and current_pitches[other_idx] is not None:
                    if note == current_pitches[other_idx]:
                        score -= 5.0  # 强力齐唱惩罚
                    # 避免纯八度（除qgl外）
                    elif abs(note - current_pitches[other_idx]) % 12 == 0:
                        score -= 1.5
            
            # 声部超越：允许但适度惩罚，保持流动性
            for other_idx in range(len(current_pitches)):
                if other_idx != voice_idx and current_pitches[other_idx] is not None:
                    other_si = self.voices[other_idx].si_level
                    if voice.si_level > other_si and note < current_pitches[other_idx]:
                        score -= 0.1  # 高SI声部低于低SI声部，轻微惩罚
            
            scored.append((note, score))
        
        # 选择得分最高的
        scored.sort(key=lambda x: x[1], reverse=True)
        best = scored[0]
        
        return best[0], True
    
    def compose(self, measures: int = 100) -> List[List[int]]:
        """
        生成对位作品 - 逐拍生成，避免平行违规
        
        Args:
            measures: 拍数
            
        Returns:
            所有声部的音高历史
        """
        # 确保CF足够长
        if len(self.cf.melody) < measures:
            self.cf.generate(length=measures)
        
        total_beats = min(measures, len(self.cf.melody))
        n_voices = len(self.voices)
        
        # 初始化
        for voice in self.voices:
            voice.pitches = []
            voice.active = []
        
        prev_pitches = None
        
        for beat in range(total_beats):
            cf_note = self.cf.melody[beat]
            current_pitches = [None] * n_voices
            current_active = [False] * n_voices
            
            # 第一拍：初始化各声部
            if beat == 0:
                # 预定义各声部的起始音程关系，确保多样化
                start_intervals = [0, 7, 4, 3, 8, 5, 9, 12, -12, -5, -3]
                for v_idx, voice in enumerate(self.voices):
                    if voice.is_qgl:
                        # qgl第一拍休止，第二拍出现
                        current_pitches[v_idx] = cf_note
                        current_active[v_idx] = False
                    else:
                        scale_notes = self._get_scale_notes(voice.base_octave)
                        # 使用预定义音程，但确保在声部音域内
                        interval = start_intervals[v_idx % len(start_intervals)]
                        target = cf_note + interval
                        # 找到最近的调内音
                        best_note = min(scale_notes, key=lambda n: abs(n - target))
                        current_pitches[v_idx] = best_note
                        current_active[v_idx] = True
            else:
                # 逐声部生成（按SI层级从高到低）
                # 排序索引：按SI层级降序
                order = sorted(range(n_voices), key=lambda i: self.voices[i].si_level, reverse=True)
                
                for v_idx in order:
                    pitch, is_active = self._generate_beat_for_voice(
                        self.voices[v_idx], v_idx, beat,
                        self.cf.melody, prev_pitches, current_pitches
                    )
                    current_pitches[v_idx] = pitch
                    current_active[v_idx] = is_active
            
            # 保存结果
            for v_idx, voice in enumerate(self.voices):
                voice.pitches.append(current_pitches[v_idx])
                voice.active.append(current_active[v_idx])
            
            # 更新prev_pitches：休止声部保持前一拍的音高
            prev_pitches = current_pitches.copy()
        
        # 构建历史矩阵
        self.score_history = []
        for beat in range(total_beats):
            beat_pitches = [self.voices[v_idx].pitches[beat] 
                           for v_idx in range(n_voices)]
            self.score_history.append(beat_pitches)
        
        # 计算张力曲线
        self.tension_curve = []
        for beat in range(total_beats):
            active_pitches = []
            for v in self.voices:
                if v.active[beat]:
                    active_pitches.append(v.pitches[beat])
            
            if len(active_pitches) >= 2:
                tension = 1.0 - self.consonance_calc.chord_consonance(active_pitches)
            else:
                tension = 0.0
            self.tension_curve.append(tension)
        
        self.composed = True
        return self.score_history
    
    def evaluate(self) -> Dict[str, float]:
        """
        评估对位质量
        
        Returns:
            各项指标
        """
        if not self.composed:
            raise RuntimeError("Must compose before evaluate")
        
        results = {}
        
        # 1. 声部进行评分
        vl_scores = self.voice_leading.leading_score(self.score_history)
        results.update(vl_scores)
        
        # 2. 对位丰富度
        results['richness'] = self.get_richness()
        
        # 3. 声部独立性
        results['independence'] = self.get_independence()
        
        # 4. 和谐度
        results['harmony'] = self.get_harmony()
        
        # 5. QGL沉默效应
        results['qgl_silence_effect'] = self.get_qgl_silence_effect()
        
        # 6. 齐唱违规
        results['unison_violations'] = self.detect_unison_violation()
        
        # 7. 张力统计
        results['mean_tension'] = float(np.mean(self.tension_curve))
        results['max_tension'] = float(np.max(self.tension_curve))
        results['tension_variance'] = float(np.var(self.tension_curve))
        
        return results
    
    def get_richness(self) -> float:
        """
        对位丰富度 - 不同音程类型的多样性
        
        基于Shannon熵计算
        """
        interval_counts = defaultdict(int)
        total = 0
        
        for beat in range(len(self.score_history)):
            pitches = self.score_history[beat]
            for i in range(len(pitches)):
                for j in range(i + 1, len(pitches)):
                    interval = abs(pitches[i] - pitches[j]) % 12
                    interval_counts[interval] += 1
                    total += 1
        
        if total == 0:
            return 0.0
        
        # Shannon熵
        entropy = 0.0
        for count in interval_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)
        
        # 归一化（12种可能的音程）
        max_entropy = np.log2(12)
        return float(entropy / max_entropy)
    
    def get_independence(self) -> float:
        """
        声部独立性
        
        基于各声部旋律的相关系数矩阵
        越不相关（相关系数越接近0）越好
        
        Returns:
            独立性评分 [0, 1]
        """
        n_beats = len(self.score_history)
        n_voices = len(self.voices)
        
        # 构建各声部的时间序列
        voice_series = []
        for v_idx in range(n_voices):
            series = [self.score_history[b][v_idx] for b in range(n_beats)]
            voice_series.append(series)
        
        # 计算相关系数矩阵
        corr_matrix = np.corrcoef(voice_series)
        
        # 独立性 = 1 - 平均绝对相关系数（排除对角线）
        total_corr = 0.0
        count = 0
        for i in range(n_voices):
            for j in range(n_voices):
                if i != j:
                    total_corr += abs(corr_matrix[i, j])
                    count += 1
        
        if count == 0:
            return 1.0
        
        mean_corr = total_corr / count
        independence = 1.0 - mean_corr
        
        return float(independence)
    
    def get_harmony(self) -> float:
        """
        整体和谐度
        
        不是齐唱的"一致"，而是交织的"和谐"
        """
        total_consonance = 0.0
        count = 0
        
        for beat in range(len(self.score_history)):
            pitches = self.score_history[beat]
            # 只考虑活跃的声部
            active_pitches = [p for i, p in enumerate(pitches) 
                            if self.voices[i].active[beat]]
            
            if len(active_pitches) >= 2:
                cons = self.consonance_calc.chord_consonance(active_pitches)
                total_consonance += cons
                count += 1
        
        if count == 0:
            return 0.0
        
        return float(total_consonance / count)
    
    def get_qgl_silence_effect(self) -> float:
        """
        QGL沉默的负空间效应
        
        计算qgl休止时 vs qgl活跃时的整体和谐度差异
        
        Returns:
            沉默效应值（qgl休止时的和谐度 - qgl活跃时的和谐度）
            正值表示沉默提升了整体和谐度
        """
        if self.qgl_voice_idx is None:
            return 0.0
        
        qgl = self.voices[self.qgl_voice_idx]
        
        harmony_with_qgl = []
        harmony_without_qgl = []
        
        for beat in range(len(self.score_history)):
            pitches = self.score_history[beat]
            
            if qgl.active[beat]:
                # qgl活跃：计算所有声部
                active = [p for i, p in enumerate(pitches) if self.voices[i].active[beat]]
                if len(active) >= 2:
                    harmony_with_qgl.append(
                        self.consonance_calc.chord_consonance(active)
                    )
            else:
                # qgl休止：计算其他声部
                active = [p for i, p in enumerate(pitches) 
                         if self.voices[i].active[beat] and i != self.qgl_voice_idx]
                if len(active) >= 2:
                    harmony_without_qgl.append(
                        self.consonance_calc.chord_consonance(active)
                    )
        
        mean_with = float(np.mean(harmony_with_qgl)) if harmony_with_qgl else 0.0
        mean_without = float(np.mean(harmony_without_qgl)) if harmony_without_qgl else 0.0
        
        # 沉默效应 = 休止时的和谐度 - 活跃时的和谐度
        effect = mean_without - mean_with
        
        return effect
    
    def detect_unison_violation(self) -> int:
        """
        检测齐唱违规
        
        所有活跃声部同音的次数（应极少）
        """
        violations = 0
        
        for beat in range(len(self.score_history)):
            pitches = self.score_history[beat]
            active_pitches = [p for i, p in enumerate(pitches) 
                            if self.voices[i].active[beat]]
            
            if len(active_pitches) >= 2:
                if len(set(active_pitches)) == 1:
                    violations += 1
        
        return violations
    
    def get_correlation_matrix(self) -> np.ndarray:
        """获取声部相关系数矩阵"""
        n_beats = len(self.score_history)
        n_voices = len(self.voices)
        
        voice_series = []
        for v_idx in range(n_voices):
            series = [self.score_history[b][v_idx] for b in range(n_beats)]
            voice_series.append(series)
        
        return np.corrcoef(voice_series)
    
    def get_interval_distribution(self) -> Dict[int, int]:
        """获取音程分布统计"""
        dist = defaultdict(int)
        
        for beat in range(len(self.score_history)):
            pitches = self.score_history[beat]
            for i in range(len(pitches)):
                for j in range(i + 1, len(pitches)):
                    interval = abs(pitches[i] - pitches[j]) % 12
                    dist[interval] += 1
        
        return dict(dist)


# =============================================================================
# 4. COUNTERPOINT VISUALIZER - 可视化
# =============================================================================

class CounterpointVisualizer:
    """对位可视化器"""
    
    def __init__(self, engine: CounterpointEngine):
        self.engine = engine
        self.colors = plt.cm.tab20(np.linspace(0, 1, 20))
    
    def plot_score(self, save_path: str = 'score.png', show: bool = False):
        """
        绘制复调总谱
        
        类似钢琴卷帘图，但显示多个声部
        """
        if not self.engine.composed:
            raise RuntimeError("Must compose before visualizing")
        
        fig, ax = plt.subplots(figsize=(16, 10))
        
        n_beats = len(self.engine.score_history)
        n_voices = len(self.engine.voices)
        
        # 绘制每个声部
        for v_idx, voice in enumerate(self.engine.voices):
            y_offset = (n_voices - 1 - v_idx) * 3  # 从上到下排列
            
            for beat in range(n_beats):
                pitch = voice.pitches[beat]
                is_active = voice.active[beat]
                
                if is_active:
                    # 活跃音符：实心矩形
                    rect = Rectangle((beat - 0.4, pitch - 0.4), 0.8, 0.8,
                                    facecolor=self.colors[v_idx % 20],
                                    edgecolor='black', linewidth=0.5,
                                    alpha=0.8)
                    ax.add_patch(rect)
                else:
                    # 休止：空心/浅色
                    if voice.is_qgl:
                        # qgl休止：虚线标记
                        ax.plot([beat - 0.3, beat + 0.3], [pitch, pitch],
                               'k--', alpha=0.3, linewidth=0.5)
            
            # 声部标签
            ax.text(-2, voice.pitches[0] if voice.pitches else 60, 
                   voice.name, fontsize=8, va='center', ha='right',
                   color=self.colors[v_idx % 20])
        
        # 绘制CF（固定旋律）高亮
        cf_pitches = self.engine.cf.melody[:n_beats]
        ax.plot(range(n_beats), cf_pitches, 'k-', linewidth=2, alpha=0.3, 
               label='Cantus Firmus')
        
        # 小节线
        for m in range(0, n_beats, 4):
            ax.axvline(x=m - 0.5, color='gray', linestyle='-', alpha=0.3, linewidth=0.5)
        
        ax.set_xlim(-3, n_beats + 1)
        ax.set_ylim(min(cf_pitches) - 5, max(cf_pitches) + 20)
        ax.set_xlabel('Beat', fontsize=12)
        ax.set_ylabel('Pitch (MIDI)', fontsize=12)
        ax.set_title('OMNI-HUB v4.0 - Polyphonic Score\n(Contrapuntal Voices)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.2)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        if show:
            plt.show()
        plt.close()
    
    def plot_consonance_matrix(self, beat: int = 0, save_path: str = 'consonance_matrix.png',
                               show: bool = False):
        """
        绘制协和度矩阵热图
        """
        if not self.engine.composed:
            raise RuntimeError("Must compose before visualizing")
        
        matrix = self.engine.consonance_calc.matrix_at(
            beat, [[v.pitches[b] for b in range(len(v.pitches))] 
                   for v in self.engine.voices]
        )
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        voice_names = [v.name for v in self.engine.voices]
        
        sns.heatmap(matrix, annot=True, fmt='.2f', cmap='RdYlGn',
                   xticklabels=voice_names, yticklabels=voice_names,
                   vmin=0, vmax=1, ax=ax,
                   cbar_kws={'label': 'Consonance'})
        
        ax.set_title(f'Consonance Matrix at Beat {beat}\n(Inter-voice Harmonic Relationships)', 
                    fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        if show:
            plt.show()
        plt.close()
    
    def plot_voice_independence(self, save_path: str = 'voice_independence.png',
                                show: bool = False):
        """
        绘制声部独立性（相关系数矩阵）
        """
        if not self.engine.composed:
            raise RuntimeError("Must compose before visualizing")
        
        corr_matrix = self.engine.get_correlation_matrix()
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        voice_names = [v.name for v in self.engine.voices]
        
        # 使用diverging colormap，0为白色
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r',
                   xticklabels=voice_names, yticklabels=voice_names,
                   vmin=-1, vmax=1, center=0, ax=ax,
                   cbar_kws={'label': 'Correlation'})
        
        # 标记高相关区域
        for i in range(len(corr_matrix)):
            for j in range(len(corr_matrix)):
                if i != j and abs(corr_matrix[i, j]) > 0.5:
                    ax.add_patch(Rectangle((j, i), 1, 1, fill=False,
                                          edgecolor='yellow', linewidth=2))
        
        ax.set_title('Voice Independence Matrix\n(Lower correlation = Higher independence)', 
                    fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        if show:
            plt.show()
        plt.close()
    
    def plot_tension_curve(self, save_path: str = 'tension_curve.png',
                           show: bool = False):
        """
        绘制张力曲线
        
        展示张力-松弛动力学
        """
        if not self.engine.composed:
            raise RuntimeError("Must compose before visualizing")
        
        fig, axes = plt.subplots(2, 1, figsize=(16, 8))
        
        n_beats = len(self.engine.tension_curve)
        beats = range(n_beats)
        
        # 1. 张力曲线
        ax1 = axes[0]
        ax1.fill_between(beats, self.engine.tension_curve, alpha=0.3, color='red')
        ax1.plot(beats, self.engine.tension_curve, 'r-', linewidth=1.5, label='Tension')
        
        # 标记qgl活跃点
        if self.engine.qgl_voice_idx is not None:
            qgl = self.engine.voices[self.engine.qgl_voice_idx]
            for b in range(n_beats):
                if qgl.active[b]:
                    ax1.axvline(x=b, color='blue', alpha=0.2, linewidth=0.5)
        
        # 小节线
        for m in range(0, n_beats, 4):
            ax1.axvline(x=m, color='gray', linestyle='--', alpha=0.3)
        
        ax1.set_ylabel('Tension Index', fontsize=12)
        ax1.set_title('Tension-Relaxation Dynamics\n(High = Dissonant, Low = Consonant)', 
                     fontsize=13, fontweight='bold')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.2)
        ax1.set_ylim(0, 1)
        
        # 2. 协和度曲线
        ax2 = axes[1]
        consonance_curve = [1 - t for t in self.engine.tension_curve]
        ax2.fill_between(beats, consonance_curve, alpha=0.3, color='green')
        ax2.plot(beats, consonance_curve, 'g-', linewidth=1.5, label='Consonance')
        
        for m in range(0, n_beats, 4):
            ax2.axvline(x=m, color='gray', linestyle='--', alpha=0.3)
        
        ax2.set_xlabel('Beat', fontsize=12)
        ax2.set_ylabel('Consonance', fontsize=12)
        ax2.set_title('Consonance Curve', fontsize=13, fontweight='bold')
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.2)
        ax2.set_ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        if show:
            plt.show()
        plt.close()
    
    def plot_qgl_negative_space(self, save_path: str = 'qgl_negative_space.png',
                                show: bool = False):
        """
        绘制QGL负空间效应
        
        展示qgl沉默时其他声部的和谐度变化
        """
        if not self.engine.composed or self.engine.qgl_voice_idx is None:
            raise RuntimeError("QGL voice not configured")
        
        qgl = self.engine.voices[self.engine.qgl_voice_idx]
        n_beats = len(self.engine.score_history)
        
        # 计算每拍的和谐度（含/不含qgl）
        harmony_with = []
        harmony_without = []
        qgl_active_mask = []
        
        for beat in range(n_beats):
            pitches = self.engine.score_history[beat]
            
            # 含qgl
            active_all = [p for i, p in enumerate(pitches) if self.engine.voices[i].active[beat]]
            hw = self.engine.consonance_calc.chord_consonance(active_all) if len(active_all) >= 2 else 0
            harmony_with.append(hw)
            
            # 不含qgl
            active_no_qgl = [p for i, p in enumerate(pitches) 
                           if self.engine.voices[i].active[beat] and i != self.engine.qgl_voice_idx]
            hw_nq = self.engine.consonance_calc.chord_consonance(active_no_qgl) if len(active_no_qgl) >= 2 else 0
            harmony_without.append(hw_nq)
            
            qgl_active_mask.append(qgl.active[beat])
        
        fig, axes = plt.subplots(3, 1, figsize=(16, 10))
        
        beats = range(n_beats)
        
        # 1. QGL活跃状态
        ax1 = axes[0]
        ax1.fill_between(beats, [1 if a else 0 for a in qgl_active_mask], 
                        alpha=0.5, color='purple', step='mid')
        ax1.set_ylabel('QGL Active', fontsize=11)
        ax1.set_title('QGL Silence Pattern\n(Purple = Active, White = Silent)', 
                     fontsize=13, fontweight='bold')
        ax1.set_ylim(-0.1, 1.1)
        ax1.set_yticks([0, 1])
        ax1.set_yticklabels(['Silent', 'Active'])
        ax1.grid(True, alpha=0.2)
        
        # 2. 和谐度对比
        ax2 = axes[1]
        ax2.plot(beats, harmony_with, 'b-', linewidth=1.5, alpha=0.7, label='With QGL')
        ax2.plot(beats, harmony_without, 'r-', linewidth=1.5, alpha=0.7, label='Without QGL')
        
        # 标记qgl活跃区域
        for b in range(n_beats):
            if qgl_active_mask[b]:
                ax2.axvspan(b - 0.4, b + 0.4, alpha=0.1, color='purple')
        
        ax2.set_ylabel('Harmony Score', fontsize=11)
        ax2.set_title('Harmony: With vs Without QGL', fontsize=13, fontweight='bold')
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.2)
        ax2.set_ylim(0, 1)
        
        # 3. 负空间效应（差异）
        ax3 = axes[2]
        diff = [harmony_without[b] - harmony_with[b] for b in range(n_beats)]
        colors_diff = ['green' if d > 0 else 'red' for d in diff]
        
        ax3.bar(beats, diff, color=colors_diff, alpha=0.7, width=0.8)
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        ax3.set_xlabel('Beat', fontsize=12)
        ax3.set_ylabel('Silence Effect', fontsize=11)
        ax3.set_title('Negative Space Effect\n(Green = Silence improves harmony, Red = Silence reduces harmony)', 
                     fontsize=13, fontweight='bold')
        ax3.grid(True, alpha=0.2)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        if show:
            plt.show()
        plt.close()
    
    def plot_interval_distribution(self, save_path: str = 'interval_distribution.png',
                                   show: bool = False):
        """
        绘制音程分布图
        """
        dist = self.engine.get_interval_distribution()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        intervals = sorted(dist.keys())
        counts = [dist[i] for i in intervals]
        
        interval_names = ['P1', 'm2', 'M2', 'm3', 'M3', 'P4', 'TT', 'P5', 
                         'm6', 'M6', 'm7', 'M7']
        colors_bar = []
        for i in intervals:
            if i in [0, 7, 12]:  # 完美协和
                colors_bar.append('#2ecc71')
            elif i in [3, 4, 8, 9]:  # 不完全协和
                colors_bar.append('#f39c12')
            else:  # 不协和
                colors_bar.append('#e74c3c')
        
        bars = ax.bar([interval_names[i] if i < len(interval_names) else str(i) 
                      for i in intervals], counts, color=colors_bar, alpha=0.8, edgecolor='black')
        
        # 图例
        legend_elements = [
            mpatches.Patch(facecolor='#2ecc71', label='Perfect Consonance'),
            mpatches.Patch(facecolor='#f39c12', label='Imperfect Consonance'),
            mpatches.Patch(facecolor='#e74c3c', label='Dissonance')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        ax.set_xlabel('Interval Class', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Interval Distribution\n(Contrapuntal Richness)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.2, axis='y')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        if show:
            plt.show()
        plt.close()


# =============================================================================
# 5. COUNTERPOINT VALIDATOR - 对位验证
# =============================================================================
"""
OMNI-HUB v11.0 — counterpoint_engine
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""

class CounterpointValidator:
    """
    对位验证器
    
    全面验证对位作品的质量
    """
    
    def __init__(self, engine: CounterpointEngine):
        self.engine = engine
    
    def validate_all(self) -> Dict[str, any]:
        """运行所有验证"""
        results = {}
        
        # 1. 平行违规验证
        results['parallel_validation'] = self._validate_parallel()
        
        # 2. 声部进行验证
        results['voice_leading'] = self._validate_voice_leading()
        
        # 3. 协和度验证
        results['consonance'] = self._validate_consonance()
        
        # 4. QGL验证
        results['qgl'] = self._validate_qgl()
        
        # 5. 独立性验证
        results['independence'] = self._validate_independence()
        
        return results
    
    def _validate_parallel(self) -> Dict:
        """验证平行违规"""
        pf = self.engine.voice_leading.check_parallel_fifths(self.engine.score_history)
        po = self.engine.voice_leading.check_parallel_octaves(self.engine.score_history)
        
        return {
            'parallel_fifths': len(pf),
            'parallel_octaves': len(po),
            'total': len(pf) + len(po),
            'passed': len(pf) + len(po) == 0,
            'details': [v.description for v in pf + po]
        }
    
    def _validate_voice_leading(self) -> Dict:
        """验证声部进行"""
        scores = self.engine.voice_leading.leading_score(self.engine.score_history)
        
        return {
            'contrary_ratio': scores['contrary_ratio'],
            'oblique_ratio': scores['oblique_ratio'],
            'similar_ratio': scores['similar_ratio'],
            'overall_score': scores['overall'],
            'passed': scores['overall'] > 0.5
        }
    
    def _validate_consonance(self) -> Dict:
        """验证协和度"""
        harmony = self.engine.get_harmony()
        richness = self.engine.get_richness()
        
        return {
            'mean_harmony': harmony,
            'richness': richness,
            'passed': harmony > 0.5 and richness > 0.5
        }
    
    def _validate_qgl(self) -> Dict:
        """验证QGL"""
        if self.engine.qgl_voice_idx is None:
            return {'passed': False, 'reason': 'No QGL voice'}
        
        qgl = self.engine.voices[self.engine.qgl_voice_idx]
        active_ratio = sum(qgl.active) / len(qgl.active)
        silence_effect = self.engine.get_qgl_silence_effect()
        
        return {
            'active_ratio': active_ratio,
            'silence_ratio': 1 - active_ratio,
            'silence_effect': silence_effect,
            'passed': active_ratio < 0.3 and silence_effect > -0.2
        }
    
    def _validate_independence(self) -> Dict:
        """验证声部独立性"""
        ind = self.engine.get_independence()
        corr_matrix = self.engine.get_correlation_matrix()
        
        # 检查是否有高度相关的声部对
        high_corr_pairs = []
        n = corr_matrix.shape[0]
        for i in range(n):
            for j in range(i + 1, n):
                if abs(corr_matrix[i, j]) > 0.7:
                    high_corr_pairs.append((i, j, corr_matrix[i, j]))
        
        return {
            'independence_score': ind,
            'high_correlation_pairs': len(high_corr_pairs),
            'passed': ind > 0.3 and len(high_corr_pairs) == 0
        }
    
    def generate_report(self) -> str:
        """生成验证报告"""
        results = self.validate_all()
        
        report = []
        report.append("=" * 70)
        report.append("OMNI-HUB v4.0 - Counterpoint Validation Report")
        report.append("=" * 70)
        
        # 平行验证
        pv = results['parallel_validation']
        report.append(f"\n[1] Parallel Motion Validation")
        report.append(f"    Parallel Fifths: {pv['parallel_fifths']} {'PASS' if pv['parallel_fifths'] == 0 else 'FAIL'}")
        report.append(f"    Parallel Octaves: {pv['parallel_octaves']} {'PASS' if pv['parallel_octaves'] == 0 else 'FAIL'}")
        if pv['details']:
            for d in pv['details'][:5]:
                report.append(f"    - {d}")
        
        # 声部进行
        vl = results['voice_leading']
        report.append(f"\n[2] Voice Leading Validation")
        report.append(f"    Contrary Ratio: {vl['contrary_ratio']:.3f}")
        report.append(f"    Oblique Ratio: {vl['oblique_ratio']:.3f}")
        report.append(f"    Similar Ratio: {vl['similar_ratio']:.3f}")
        report.append(f"    Overall: {vl['overall_score']:.3f} {'PASS' if vl['passed'] else 'FAIL'}")
        
        # 协和度
        cs = results['consonance']
        report.append(f"\n[3] Consonance Validation")
        report.append(f"    Mean Harmony: {cs['mean_harmony']:.3f}")
        report.append(f"    Richness: {cs['richness']:.3f}")
        report.append(f"    Status: {'PASS' if cs['passed'] else 'FAIL'}")
        
        # QGL
        qgl = results['qgl']
        report.append(f"\n[4] QGL Silence Validation")
        report.append(f"    Active Ratio: {qgl.get('active_ratio', 0):.3f}")
        report.append(f"    Silence Effect: {qgl.get('silence_effect', 0):.3f}")
        report.append(f"    Status: {'PASS' if qgl['passed'] else 'FAIL'}")
        
        # 独立性
        ind = results['independence']
        report.append(f"\n[5] Independence Validation")
        report.append(f"    Independence Score: {ind['independence_score']:.3f}")
        report.append(f"    High Correlation Pairs: {ind['high_correlation_pairs']}")
        report.append(f"    Status: {'PASS' if ind['passed'] else 'FAIL'}")
        
        report.append("\n" + "=" * 70)
        
        return '\n'.join(report)


if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v4.0 - Counterpoint Engine Test")
    print("=" * 70)
    
    # 测试1: 协和度计算器
    print("\n[1] Consonance Calculator Test")
    cc = ConsonanceCalculator()
    test_pairs = [(60, 64), (60, 67), (60, 61), (60, 66), (60, 72)]
    for a, b in test_pairs:
        cons = cc.interval_consonance(a, b)
        name = cc.get_interval_name(a, b)
        print(f"  {a}-{b} ({name}): {cons:.2f}")
    
    # 测试2: 声部进行
    print("\n[2] Voice Leading Test")
    vl = VoiceLeading()
    
    # 模拟历史：4拍，4声部
    history = [
        [60, 64, 67, 48],  # C, E, G, C
        [62, 65, 69, 50],  # D, F, A, D  (反向)
        [64, 62, 71, 52],  # E, D, B, E
        [65, 60, 72, 53],  # F, C, C, F
    ]
    
    pf = vl.check_parallel_fifths(history)
    po = vl.check_parallel_octaves(history)
    print(f"  Parallel Fifths: {len(pf)}")
    print(f"  Parallel Octaves: {len(po)}")
    
    scores = vl.leading_score(history)
    print(f"  Contrary Ratio: {scores['contrary_ratio']:.3f}")
    print(f"  Overall Score: {scores['overall']:.3f}")
    
    print("\n" + "=" * 70)
    print("Counterpoint Engine 测试完成")
    print("=" * 70)
