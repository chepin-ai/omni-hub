
__version__ = "11.0.0"
"""
OMNI-HUB v11.0 — cantus_firmus
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""
"""
OMNI-HUB v4.0 - Cantus Firmus Module
固定旋律（基准线）生成与管理

对位法则：
1. 以级进为主（stepwise motion）
2. 跳进后必须反向级进
3. 没有连续同向跳进
4. 音域限制在一个八度内
5. 最终音必须是主音（解决感）
"""

import numpy as np
from typing import List, Tuple, Optional
import logging


class CantusFirmus:
    """
    固定旋律类 - cisvr作为对位的固定旋律基准
    
    Attributes:
        key_center: 调中心音高 (MIDI note number, default C=60)
        scale_type: 调式类型 ('major', 'minor', 'dorian', etc.)
        melody: 旋律序列 (list of MIDI note numbers)
        rhythm: 节奏序列 (list of durations in beats)
    """
    
    def __init__(self, key_center: int = 60, scale_type: str = 'major', seed: Optional[int] = None):
        """
        Args:
            key_center: 主音MIDI编号 (60=C4)
            scale_type: 调式类型
            seed: 随机种子
        """
        self.key_center = key_center
        self.scale_type = scale_type
        self.melody: List[int] = []
        self.rhythm: List[float] = []
        self._rng = np.random.RandomState(seed)
        
        # 音阶定义（半音间隔）
        self.scales = {
            'major': [0, 2, 4, 5, 7, 9, 11],
            'minor': [0, 2, 3, 5, 7, 8, 10],
            'dorian': [0, 2, 3, 5, 7, 9, 10],
            'phrygian': [0, 1, 3, 5, 7, 8, 10],
            'lydian': [0, 2, 4, 6, 7, 9, 11],
            'mixolydian': [0, 2, 4, 5, 7, 9, 10],
            'locrian': [0, 1, 3, 5, 6, 8, 10],
        }
        
        self.scale = self.scales.get(scale_type, self.scales['major'])
        # 扩展两个八度的音阶
        self.full_scale = sorted(
            [key_center + octave_offset + interval 
             for octave_offset in [-12, 0, 12] 
             for interval in self.scale]
        )
        # 限制在一个八度内的可用音
        self.tessitura = sorted([key_center + i for i in self.scale])
    
    def _get_scale_degree(self, pitch: int) -> int:
        """获取音在音阶中的度数（相对于主音）"""
        rel = (pitch - self.key_center) % 12
        if rel in self.scale:
            return self.scale.index(rel)
        return -1
    
    def _is_step(self, from_pitch: int, to_pitch: int) -> bool:
        """是否为级进（二度）"""
        diff = abs(to_pitch - from_pitch)
        return diff <= 2  # 小二度或大二度
    
    def _is_leap(self, from_pitch: int, to_pitch: int) -> bool:
        """是否为跳进（三度或以上）"""
        diff = abs(to_pitch - from_pitch)
        return diff > 2
    
    def _is_valid_motion(self, prev: int, curr: int, next_pitch: int, 
                         prev_was_leap: bool, prev_direction: int) -> bool:
        """
        检查进行是否合法
        
        规则：
        1. 跳进后必须反向级进
        2. 没有连续同向跳进
        3. 音域在一个八度内
        """
        curr_dir = np.sign(next_pitch - curr)
        leap_size = abs(next_pitch - curr)
        
        # 规则3: 音域限制
        if next_pitch < self.key_center or next_pitch > self.key_center + 12:
            return False
        
        # 规则1: 如果前一个是跳进，当前必须反向级进
        if prev_was_leap:
            prev_dir = np.sign(curr - prev)
            if curr_dir == prev_dir or not self._is_step(curr, next_pitch):
                return False
        
        # 规则2: 没有连续同向跳进
        if prev is not None and prev_direction != 0:
            if curr_dir == prev_direction and self._is_leap(curr, next_pitch):
                if self._is_leap(prev, curr):
                    return False
        
        # 避免超过八度的跳进
        if leap_size > 8:
            return False
        
        return True
    
    def generate(self, length: int = 16, start_on_tonic: bool = True) -> List[int]:
        """
        生成固定旋律
        
        Args:
            length: 旋律长度（拍数）
            start_on_tonic: 是否从主音开始
            
        Returns:
            旋律序列（MIDI note numbers）
        """
        if length < 4:
            raise ValueError("Length must be at least 4")
        
        melody = []
        
        # 起始音：主音或属音
        if start_on_tonic:
            current = self.key_center
        else:
            current = self.key_center + 7  # 属音 (G)
        
        melody.append(current)
        
        prev_was_leap = False
        prev_direction = 0
        
        for i in range(1, length - 1):
            # 候选音：音阶内且在一个八度内的音
            candidates = [n for n in self.tessitura 
                         if n != current and self.key_center <= n <= self.key_center + 12]
            
            valid_candidates = []
            for cand in candidates:
                if len(melody) >= 2:
                    if self._is_valid_motion(melody[-2], current, cand, 
                                            prev_was_leap, prev_direction):
                        valid_candidates.append(cand)
                else:
                    valid_candidates.append(cand)
            
            if not valid_candidates:
                # 如果没有候选，使用级进到最近的音
                scale_idx = self.tessitura.index(current) if current in self.tessitura else 0
                if scale_idx > 0 and scale_idx < len(self.tessitura) - 1:
                    valid_candidates = [self.tessitura[scale_idx - 1], self.tessitura[scale_idx + 1]]
                elif scale_idx == 0:
                    valid_candidates = [self.tessitura[1]]
                else:
                    valid_candidates = [self.tessitura[-2]]
            
            # 级进优先（80%概率）
            step_candidates = [c for c in valid_candidates if self._is_step(current, c)]
            
            if step_candidates and self._rng.random() < 0.8:
                next_pitch = self._rng.choice(step_candidates)
                prev_was_leap = False
            else:
                leap_candidates = [c for c in valid_candidates if self._is_leap(current, c)]
                if leap_candidates:
                    next_pitch = self._rng.choice(leap_candidates)
                    prev_was_leap = True
                else:
                    next_pitch = self._rng.choice(valid_candidates)
                    prev_was_leap = False
            
            prev_direction = np.sign(next_pitch - current)
            melody.append(next_pitch)
            current = next_pitch
        
        # 最终音必须是主音（解决感）
        melody.append(self.key_center)
        
        self.melody = melody
        self.rhythm = [1.0] * len(melody)  # 均匀节奏
        return melody
    
    def get_note(self, t: float) -> int:
        """
        获取t时刻的音符
        
        Args:
            t: 时间（拍）
            
        Returns:
            MIDI note number
        """
        if not self.melody:
            return self.key_center
        
        beat_sum = 0.0
        for i, dur in enumerate(self.rhythm):
            beat_sum += dur
            if t < beat_sum:
                return self.melody[i]
        return self.melody[-1]
    
    def get_notes_at_beat(self, beat: int) -> List[int]:
        """获取特定拍的所有音符（返回单个音符列表）"""
        if 0 <= beat < len(self.melody):
            return [self.melody[beat]]
        return [self.melody[-1]] if self.melody else [self.key_center]
    
    def get_interval(self, t1: int, t2: int) -> int:
        """
        获取两个拍点间的音程（半音数）
        
        Args:
            t1, t2: 拍点索引
            
        Returns:
            音程（半音数，绝对值）
        """
        if not self.melody or t1 >= len(self.melody) or t2 >= len(self.melody):
            return 0
        return abs(self.melody[t2] - self.melody[t1])
    
    def get_melodic_interval_at(self, t: int) -> int:
        """获取t到t+1的音程"""
        if t < 0 or t >= len(self.melody) - 1:
            return 0
        return self.melody[t + 1] - self.melody[t]
    
    def get_direction_at(self, t: int) -> int:
        """获取t到t+1的进行方向（1=上行, -1=下行, 0=保持）"""
        interval = self.get_melodic_interval_at(t)
        return np.sign(interval)
    
    def get_climax(self) -> Tuple[int, int]:
        """
        获取旋律高潮点
        
        Returns:
            (拍点, 音高)
        """
        if not self.melody:
            return (0, self.key_center)
        max_idx = np.argmax(self.melody)
        return (max_idx, self.melody[max_idx])
    
    def get_range(self) -> int:
        """获取旋律音域"""
        if not self.melody:
            return 0
        return max(self.melody) - min(self.melody)
    
    def __len__(self) -> int:
        return len(self.melody)
    
    def __repr__(self) -> str:
        return f"CantusFirmus(key={self.key_center}, scale={self.scale_type}, len={len(self.melody)})"


class CantusFirmusFactory:
    """固定旋律工厂 - 生成多种风格的固定旋律"""
    
    @staticmethod
    def create_ascending(key: int = 60, length: int = 8) -> CantusFirmus:
        """创建上行固定旋律"""
        cf = CantusFirmus(key)
        scale = [key + i for i in [0, 2, 4, 5, 7, 9, 11, 12]]
        cf.melody = scale[:length]
        cf.rhythm = [1.0] * length
        return cf
    
    @staticmethod
    def create_descending(key: int = 60, length: int = 8) -> CantusFirmus:
        """创建下行固定旋律"""
        cf = CantusFirmus(key)
        scale = sorted([key + i for i in [0, 2, 4, 5, 7, 9, 11, 12]], reverse=True)
        cf.melody = scale[:length]
        cf.rhythm = [1.0] * length
        return cf
    
    @staticmethod
    def create_arch(key: int = 60, length: int = 16) -> CantusFirmus:
        """创建拱形固定旋律（上行后下行）"""
        cf = CantusFirmus(key)
        half = length // 2
        ascending = [key + i for i in [0, 2, 4, 5, 7, 9]]
        descending = sorted([key + i for i in [0, 2, 4, 5, 7]], reverse=True)
        cf.melody = ascending[:half] + descending[:length - half]
        cf.rhythm = [1.0] * length
        return cf


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("OMNI-HUB v4.0 - Cantus Firmus Test")
    print("=" * 60)
    
    # 测试1: 基本生成
    cf = CantusFirmus(key_center=60, scale_type='major', seed=42)
    melody = cf.generate(length=16)
    
    print(f"\n固定旋律: {cf}")
    print(f"旋律: {melody}")
    print(f"音域: {cf.get_range()} 半音")
    print(f"高潮点: {cf.get_climax()}")
    
    # 测试2: 进行方向
    print(f"\n进行分析:")
    for t in range(len(melody) - 1):
        interval = cf.get_melodic_interval_at(t)
        direction = "上行" if interval > 0 else "下行" if interval < 0 else "保持"
        leap = "跳进" if abs(interval) > 2 else "级进"
        print(f"  拍{t}->{t+1}: {direction} {abs(interval)}半音 ({leap})")
    
    # 测试3: 不同时刻的音符
    print(f"\n时刻采样:")
    for t in [0, 2.5, 5, 10, 15]:
        print(f"  t={t}: {cf.get_note(t)}")
    
    # 测试4: 工厂方法
    print(f"\n工厂测试:")
    arch = CantusFirmusFactory.create_arch(62, 12)
    print(f"拱形旋律: {arch.melody}")
    
    print("\n" + "=" * 60)
    print("Cantus Firmus 测试完成")
    print("=" * 60)
