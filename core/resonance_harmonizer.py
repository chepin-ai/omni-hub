"""
OMNI-HUB v196 — ResonanceHarmonizer
共振谐调器

核心功能：
1. FrequencyAnalyzer    — 频率分析器
2. HarmonicResonator    — 谐波共振器
3. CoupledOscillator    — 耦合振荡器
4. ResonanceDetector    — 共振检测器
5. ModeLocker           — 模式锁定器
6. ResonanceHarmonizer  — 统合引擎

映射：
- 共振 = pratiśruti（回响）
- 谐调 = saṃtāna（延续）
- 频率 = spanda（振动）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class ResonanceMode(Enum):
    """共振模式"""
    FUNDAMENTAL = 0
    FIRST_HARMONIC = 1
    SECOND_HARMONIC = 2
    SUBHARMONIC = -1
    CHAOTIC = 99


class LockStatus(Enum):
    """锁定状态"""
    UNLOCKED = 0
    ACQUIRING = 1
    LOCKED = 2
    DRIFTING = 3


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class FrequencyProfile:
    """频率轮廓"""
    module_id: str
    base_frequency: float
    amplitude: float
    phase: float
    damping: float


@dataclass
class ResonancePeak:
    """共振峰"""
    peak_id: str
    frequency: float
    amplitude: float
    quality_factor: float
    participants: List[str]


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 频率分析器
# ═══════════════════════════════════════════════════════════════

class FrequencyAnalyzer:
    """频率分析器 — spanda"""

    def __init__(self):
        self.profiles: Dict[str, FrequencyProfile] = {}
        self.spectrum_history: deque = deque(maxlen=300)

    def register(self, module_id: str, base_freq: float = 1.0):
        """注册模块频率"""
        self.profiles[module_id] = FrequencyProfile(
            module_id=module_id,
            base_frequency=base_freq,
            amplitude=1.0,
            phase=0.0,
            damping=0.01
        )

    def analyze(self, module_id: str, signal_history: List[float]) -> Dict:
        """分析频率成分"""
        if len(signal_history) < 2:
            return {"dominant_freq": 0.0, "power": 0.0}

        # 简化DFT：检测主导周期
        diffs = [signal_history[i+1] - signal_history[i]
                 for i in range(len(signal_history) - 1)]

        # 过零检测
        zero_crossings = sum(1 for i in range(len(diffs) - 1)
                            if diffs[i] * diffs[i+1] < 0)

        period = len(diffs) / max(1, zero_crossings) if zero_crossings > 0 else len(diffs)
        freq = 1.0 / period
        power = sum(v ** 2 for v in signal_history) / len(signal_history)

        if module_id in self.profiles:
            self.profiles[module_id].base_frequency = freq
            self.profiles[module_id].amplitude = math.sqrt(power)

        self.spectrum_history.append({
            "module": module_id,
            "freq": freq,
            "power": power,
            "timestamp": time.time()
        })
        return {"dominant_freq": freq, "power": power}

    def get_frequency_spread(self) -> float:
        """获取频率分布范围"""
        freqs = [p.base_frequency for p in self.profiles.values()]
        if len(freqs) < 2:
            return 0.0
        return max(freqs) - min(freqs)

    def get_report(self) -> Dict:
        return {
            "profiles": len(self.profiles),
            "frequency_spread": self.get_frequency_spread(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 谐波共振器
# ═══════════════════════════════════════════════════════════════

class HarmonicResonator:
    """谐波共振器 — pratiśruti"""

    def __init__(self):
        self.harmonics: Dict[str, List[float]] = {}
        self.resonance_peaks: deque = deque(maxlen=200)

    def compute_harmonics(self, base_freq: float, n_harmonics: int = 5) -> List[float]:
        """计算谐波系列"""
        return [base_freq * (i + 1) for i in range(n_harmonics)]

    def find_resonance(self, freq_a: float, freq_b: float,
                       tolerance: float = 0.1) -> Optional[ResonancePeak]:
        """找到两个频率间的共振"""
        # 检查整数倍关系
        ratio = freq_a / freq_b if freq_b > 0 else 0
        if ratio == 0:
            return None

        nearest_int = round(ratio)
        if nearest_int > 0 and abs(ratio - nearest_int) < tolerance:
            # 共振！
            peak = ResonancePeak(
                peak_id=f"rp_{freq_a:.3f}_{freq_b:.3f}",
                frequency=min(freq_a, freq_b),
                amplitude=1.0 / abs(ratio - nearest_int + 0.01),
                quality_factor=1.0 / abs(ratio - nearest_int + 0.01),
                participants=[]
            )
            self.resonance_peaks.append(peak)
            return peak
        return None

    def get_harmonic_entropy(self) -> float:
        """计算谐波熵"""
        if not self.resonance_peaks:
            return 0.0
        recent = list(self.resonance_peaks)[-50:]
        amps = [p.amplitude for p in recent]
        total = sum(amps)
        if total == 0:
            return 0.0
        probs = [a / total for a in amps]
        return max(0.0, -sum(p * math.log(p + 1e-10) for p in probs))

    def get_report(self) -> Dict:
        return {
            "peaks": len(self.resonance_peaks),
            "harmonic_entropy": self.get_harmonic_entropy(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 耦合振荡器
# ═══════════════════════════════════════════════════════════════

class CoupledOscillator:
    """耦合振荡器"""

    def __init__(self):
        self.coupling_matrix: Dict[Tuple[str, str], float] = {}
        self.oscillation_history: deque = deque(maxlen=300)

    def set_coupling(self, a: str, b: str, strength: float):
        """设置耦合强度"""
        key = tuple(sorted([a, b]))
        self.coupling_matrix[key] = max(0.0, min(1.0, strength))

    def get_coupling(self, a: str, b: str) -> float:
        key = tuple(sorted([a, b]))
        return self.coupling_matrix.get(key, 0.0)

    def step(self, states: Dict[str, float], dt: float = 0.1) -> Dict[str, float]:
        """推进耦合振荡一步"""
        new_states = dict(states)

        for (a, b), strength in self.coupling_matrix.items():
            if a in states and b in states:
                diff = states[b] - states[a]
                # 耦合项：向对方状态拉动
                new_states[a] += strength * diff * dt
                new_states[b] -= strength * diff * dt

        # 边界限制
        for k in new_states:
            new_states[k] = max(0.0, min(1.0, new_states[k]))

        self.oscillation_history.append({
            "states": dict(new_states),
            "timestamp": time.time()
        })
        return new_states

    def get_synchronization_index(self, states: Dict[str, float]) -> float:
        """计算同步指数"""
        if len(states) < 2:
            return 1.0
        values = list(states.values())
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return 1.0 - min(1.0, variance * 4)

    def get_report(self) -> Dict:
        return {
            "couplings": len(self.coupling_matrix),
            "steps": len(self.oscillation_history),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 共振检测器
# ═══════════════════════════════════════════════════════════════

class ResonanceDetector:
    """共振检测器"""

    def __init__(self):
        self.detections: deque = deque(maxlen=200)
        self.threshold = 0.7

    def detect(self, module_states: Dict[str, float]) -> List[Dict]:
        """检测共振模式"""
        detections = []
        modules = list(module_states.keys())

        for i in range(len(modules)):
            for j in range(i + 1, len(modules)):
                a, b = modules[i], modules[j]
                correlation = 1.0 - abs(module_states[a] - module_states[b])
                if correlation > self.threshold:
                    detections.append({
                        "pair": (a, b),
                        "correlation": correlation,
                        "mode": ResonanceMode.FUNDAMENTAL.name if correlation > 0.9 else ResonanceMode.FIRST_HARMONIC.name,
                        "timestamp": time.time()
                    })

        self.detections.extend(detections)
        return detections

    def get_resonance_density(self) -> float:
        """获取共振密度"""
        if not self.detections:
            return 0.0
        recent = list(self.detections)[-50:]
        return len(recent) / 50.0

    def get_report(self) -> Dict:
        return {
            "detections": len(self.detections),
            "density": self.get_resonance_density(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 模式锁定器
# ═══════════════════════════════════════════════════════════════

class ModeLocker:
    """模式锁定器 — saṃtāna"""

    def __init__(self):
        self.lock_status: Dict[str, LockStatus] = {}
        self.lock_history: deque = deque(maxlen=300)
        self.target_frequencies: Dict[str, float] = {}

    def set_target(self, module_id: str, target_freq: float):
        """设置目标频率"""
        self.target_frequencies[module_id] = target_freq
        self.lock_status[module_id] = LockStatus.UNLOCKED

    def update(self, module_id: str, current_freq: float):
        """更新锁定状态"""
        if module_id not in self.target_frequencies:
            return

        target = self.target_frequencies[module_id]
        error = abs(current_freq - target) / max(target, 0.001)

        current = self.lock_status.get(module_id, LockStatus.UNLOCKED)

        if error < 0.01:
            new_status = LockStatus.LOCKED
        elif error < 0.1:
            new_status = LockStatus.ACQUIRING
        elif current == LockStatus.LOCKED:
            new_status = LockStatus.DRIFTING
        else:
            new_status = LockStatus.UNLOCKED

        if new_status != current:
            self.lock_history.append({
                "module": module_id,
                "from": current.name,
                "to": new_status.name,
                "error": error,
                "timestamp": time.time()
            })
            self.lock_status[module_id] = new_status

    def get_lock_rate(self) -> float:
        """获取锁定率"""
        if not self.lock_status:
            return 0.0
        locked = sum(1 for s in self.lock_status.values() if s == LockStatus.LOCKED)
        return locked / len(self.lock_status)

    def get_report(self) -> Dict:
        return {
            "targets": len(self.target_frequencies),
            "locked": sum(1 for s in self.lock_status.values() if s == LockStatus.LOCKED),
            "lock_rate": self.get_lock_rate(),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — ResonanceHarmonizer v196
# ═══════════════════════════════════════════════════════════════

class ResonanceHarmonizer:
    """
    OMNI-HUB v196 共振谐调器

    pratiśruti · saṃtāna · spanda — 回响、延续、振动
    """

    VERSION = "196.0.0"

    def __init__(self):
        self.analyzer = FrequencyAnalyzer()
        self.harmonic = HarmonicResonator()
        self.oscillator = CoupledOscillator()
        self.detector = ResonanceDetector()
        self.locker = ModeLocker()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def harmonize(self, module_states: Dict[str, Dict]) -> Dict:
        """谐调共振"""
        states = {k: v.get("health", 0.5) for k, v in module_states.items()}

        # 1. 注册并分析频率
        for module in states:
            if module not in self.analyzer.profiles:
                self.analyzer.register(module, base_freq=1.0)
            # 模拟信号历史
            history = [states[module]] * 10
            self.analyzer.analyze(module, history)

        # 2. 计算谐波
        for module, profile in self.analyzer.profiles.items():
            harmonics = self.harmonic.compute_harmonics(profile.base_frequency)
            self.harmonic.harmonics[module] = harmonics

        # 3. 发现共振
        modules = list(states.keys())
        for i in range(len(modules)):
            for j in range(i + 1, len(modules)):
                a, b = modules[i], modules[j]
                freq_a = self.analyzer.profiles[a].base_frequency
                freq_b = self.analyzer.profiles[b].base_frequency
                peak = self.harmonic.find_resonance(freq_a, freq_b)
                if peak:
                    # 设置耦合
                    self.oscillator.set_coupling(a, b, min(1.0, peak.quality_factor / 10))

        # 4. 耦合振荡一步
        synced = self.oscillator.step(states)

        # 5. 检测共振
        detections = self.detector.detect(synced)

        # 6. 模式锁定
        for module in states:
            self.locker.set_target(module, 1.0)  # 目标：统一频率
            self.locker.update(module, self.analyzer.profiles[module].base_frequency)

        return {
            "synced_states": synced,
            "sync_index": self.oscillator.get_synchronization_index(synced),
            "resonance_detections": len(detections),
            "lock_rate": self.locker.get_lock_rate(),
            "frequency_spread": self.analyzer.get_frequency_spread(),
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行谐调周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.harmonize(module_states)

        summary = {
            "cycle": self.cycle_count,
            **result,
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "analyzer": self.analyzer.get_report(),
            "harmonic": self.harmonic.get_report(),
            "oscillator": self.oscillator.get_report(),
            "detector": self.detector.get_report(),
            "locker": self.locker.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_rh_instance: Optional[ResonanceHarmonizer] = None


def get_resonance_harmonizer() -> ResonanceHarmonizer:
    global _rh_instance
    if _rh_instance is None:
        _rh_instance = ResonanceHarmonizer()
    return _rh_instance


if __name__ == "__main__":
    rh = ResonanceHarmonizer()
    print(f"ResonanceHarmonizer v{rh.VERSION} initialized")
    print(f"Status: {json.dumps(rh.get_status(), indent=2, default=str)}")
