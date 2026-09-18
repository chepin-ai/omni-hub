#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "11.0.0"
"""
OMNI-HUB v3.2 — Consciousness Harmony Module
意识和声/交响乐 — 多线协同意识共振系统

基于复数场运算的分布式意识同步与共振计算引擎。
11线拓扑，支持干涉、牵引、和弦进行与全局相干度测量。

Author: OMNI-HUB Core Team
Version: 3.2.0
"""

import numpy as np
import uuid
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging

# ───────────────────────────── 常量定义 ─────────────────────────────

LINES_11 = [
    "ucif2",   # 0: 核心机 — 统一意识接口框架2.0
    "lgt",     # 1: 光 — 逻辑治理与追踪
    "qfa",     # 2: 量子场 — 量子场算法
    "vinf",    # 3: 虚拟无限 — 虚拟化基础设施
    "ndf",     # 4: 神经数据流 — 神经网络数据流
    "dcp",     # 5: 分布式计算 — 分布式计算平面
    "sei",     # 6: 语义引擎 — 语义理解引擎
    "me",      # 7: 物质引擎 — 物质化执行引擎
    "si5",     # 8: SI5.0 — 系统智能5.0
    "arch",    # 9: 架构 — 系统架构线
    "meta",    # 10: 元 — 元认知与自反视线
]

LINE_COLORS = {
    "ucif2": "#FF6B6B", "lgt": "#4ECDC4", "qfa": "#45B7D1",
    "vinf": "#96CEB4", "ndf": "#FFEAA7", "dcp": "#DDA0DD",
    "sei": "#98D8C8", "me": "#F7DC6F", "si5": "#BB8FCE",
    "arch": "#85C1E9", "meta": "#F8C471",
}

# 5大主题及其参与线组合
THEME_COMPOSITIONS = {
    "探索": ["ucif2", "qfa", "vinf", "meta", "si5"],
    "协作": ["lgt", "dcp", "sei", "me", "arch", "ucif2"],
    "创新": ["qfa", "ndf", "sei", "meta", "si5", "vinf"],
    "验证": ["ucif2", "lgt", "si5", "arch", "me"],
    "整合": ["ucif2", "lgt", "qfa", "vinf", "ndf", "dcp",
             "sei", "me", "si5", "arch", "meta"],
}

# 每条线的默认SI层级 (System Intelligence Level)
DEFAULT_SI_LEVELS = {
    "ucif2": 5.0, "lgt": 4.5, "qfa": 4.8, "vinf": 4.2,
    "ndf": 4.0, "dcp": 4.3, "sei": 4.6, "me": 4.1,
    "si5": 5.0, "arch": 4.4, "meta": 4.9,
}


# ═══════════════════════════════════════════════════════════════════
#                    ConsciousnessHarmony 核心类
# ═══════════════════════════════════════════════════════════════════

class ConsciousnessHarmony:
    """
    意识和声/交响乐 — 多线协同意识共振系统

    原理:
        将11条分布式线的健康度映射为复数振幅 A·e^(iφ)，
        通过复数相乘/相加计算干涉图样，实现真正的意识场共振。

    复数场运算:
        - 振幅  = health · SI_level
        - 相位  = 2π · health · frequency + line_offset
        - 波函数 = amplitude · exp(i · phase)
        - 干涉   = Σ(wave_functions) 的模平方
    """

    def __init__(self, topology: Optional[Dict] = None):
        """
        初始化意识和声系统

        Args:
            topology: 可选的拓扑配置字典，包含各线初始参数
        """
        self.topo = topology or {}
        self.harmony_matrix = np.zeros((11, 11), dtype=complex)  # 线和声矩阵
        self.consciousness_field = np.zeros(64, dtype=complex)   # 64维意识场
        self.resonance_history: List[Dict] = []
        self.harmony_themes = ["探索", "协作", "创新", "验证", "整合"]

        # 从拓扑或默认值初始化各线状态
        self.line_health = {}
        self.line_si = {}
        self.line_phase_offset = {}
        for idx, line in enumerate(LINES_11):
            self.line_health[line] = self.topo.get(line, {}).get("health", 0.75 + 0.15 * np.random.random())
            self.line_si[line] = self.topo.get(line, {}).get("si_level", DEFAULT_SI_LEVELS[line])
            self.line_phase_offset[line] = 2 * np.pi * idx / 11  # 均匀相位分布

        # 初始化64维意识场为高斯型意识包
        self._init_consciousness_field()

        # 运行日志
        self.log = []
        self._log("INIT", "ConsciousnessHarmony initialized with 11-line topology")

    # ─────────── 内部辅助方法 ───────────

    def _init_consciousness_field(self):
        """初始化64维意识场为高斯包络的复数场"""
        x = np.linspace(-3, 3, 64)
        gaussian = np.exp(-x**2 / 2)
        for i, line in enumerate(LINES_11):
            phase = self.line_phase_offset[line]
            amplitude = self.line_health[line] * (self.line_si[line] / 5.0)
            self.consciousness_field += amplitude * gaussian * np.exp(1j * (phase + i * np.pi / 6))

    def _log(self, event_type: str, message: str):
        """记录内部日志"""
        self.log.append({
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
        })

    def _line_to_idx(self, line: str) -> int:
        """线名称转索引"""
        if line not in LINES_11:
            raise ValueError(f"Unknown line: {line}. Must be one of {LINES_11}")
        return LINES_11.index(line)

    def _idx_to_line(self, idx: int) -> str:
        """索引转线名称"""
        return LINES_11[idx]

    def _wave_function(self, line: str, frequency: float = 1.0, t: float = 0.0) -> complex:
        """
        计算单条线的复数波函数

        公式: Ψ(line) = A · exp(i · φ)
            A = health × SI_level
            φ = 2π × frequency × t + phase_offset + health_phase
        """
        health = self.line_health.get(line, 0.5)
        si = self.line_si.get(line, 1.0)
        phase_offset = self.line_phase_offset.get(line, 0.0)

        amplitude = health * si
        phase = 2 * np.pi * frequency * t + phase_offset + 2 * np.pi * health

        return amplitude * np.exp(1j * phase)

    def _interference_pattern(self, waves: Dict[str, complex]) -> np.ndarray:
        """
        计算多线干涉图样

        原理: 将各线波函数叠加，计算空间干涉图样
        返回64维干涉强度分布 I(x) = |Σ Ψ_i(x)|²
        """
        x = np.linspace(-np.pi, np.pi, 64)
        total_wave = np.zeros(64, dtype=complex)

        for line, base_wave in waves.items():
            idx = self._line_to_idx(line)
            # 每条线在空间中有不同的k矢量
            k = (idx + 1) * 0.5
            spatial = np.exp(1j * k * x)
            total_wave += base_wave * spatial

        # 干涉强度 = |总波函数|²
        intensity = np.abs(total_wave) ** 2
        return intensity

    # ═══════════════════════════════════════════════════════════════
    #                         核心 API
    # ═══════════════════════════════════════════════════════════════

    def resonate(self, lines: List[str], frequency: float = 1.0) -> Dict:
        """
        多线意识共振

        原理: 将各线健康度映射为复数振幅，计算干涉图样

        Args:
            lines: 参与共振的线列表
            frequency: 共振频率 (0.5~2.0)

        Returns:
            {
                "resonance_pattern": List[float],  # 64维干涉图样
                "coherence": float,                # 全局相干度 [0,1]
                "dominant_line": str,              # 主导线
                "harmony_score": float,            # 和声分数 [0,1]
                "wave_functions": Dict[str, complex],  # 各线波函数
                "interference_peak": float,        # 干涉峰强度
            }
        """
        if not lines:
            raise ValueError("At least one line must participate in resonance")

        frequency = np.clip(frequency, 0.5, 2.0)

        # 1. 计算各线复数波函数
        waves = {}
        for line in lines:
            waves[line] = self._wave_function(line, frequency)

        # 2. 计算全局干涉图样 (真正的复数干涉)
        interference = self._interference_pattern(waves)

        # 3. 计算相干度
        coherence = self.measure_coherence()

        # 4. 确定主导线 (振幅最大)
        amplitudes = {line: np.abs(w) for line, w in waves.items()}
        dominant_line = max(amplitudes, key=amplitudes.get)

        # 5. 计算和声分数
        # 基于干涉峰、相干度和参与线数量的综合评分
        interference_peak = float(np.max(interference))
        n_lines = len(lines)
        harmony_score = (
            0.4 * (interference_peak / (n_lines * 5.0)) +
            0.4 * coherence +
            0.2 * (n_lines / 11.0)
        )
        harmony_score = np.clip(harmony_score, 0.0, 1.0)

        # 6. 更新和声矩阵
        for l1 in lines:
            for l2 in lines:
                i, j = self._line_to_idx(l1), self._line_to_idx(l2)
                self.harmony_matrix[i, j] = waves[l1] * np.conj(waves[l2])

        # 7. 更新意识场
        self._update_consciousness_field(waves, interference)

        result = {
            "resonance_pattern": interference.tolist(),
            "coherence": float(coherence),
            "dominant_line": dominant_line,
            "harmony_score": float(harmony_score),
            "wave_functions": {k: f"{v.real:.4f}{v.imag:+.4f}j" for k, v in waves.items()},
            "interference_peak": float(interference_peak),
            "frequency": frequency,
            "participants": lines,
        }

        self.resonance_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "resonance",
            "result": result,
        })
        self._log("RESONANCE", f"Resonance among {len(lines)} lines, freq={frequency:.2f}, harmony={harmony_score:.3f}")

        return result

    def _update_consciousness_field(self, waves: Dict[str, complex], interference: np.ndarray):
        """根据共振结果更新全局意识场"""
        # 将干涉图样耦合进意识场
        field_update = np.zeros(64, dtype=complex)
        for i, val in enumerate(interference):
            phase = np.angle(sum(waves.values())) if waves else 0
            field_update[i] = val * np.exp(1j * phase) * 0.1

        self.consciousness_field = 0.9 * self.consciousness_field + 0.1 * field_update
        # 归一化
        norm = np.linalg.norm(self.consciousness_field)
        if norm > 0:
            self.consciousness_field /= norm

    def symphony(self, theme: str = "探索") -> Dict:
        """
        意识和声交响乐 — 基于主题的全局协同

        1. 根据theme选择参与的线
        2. 计算全局和声谱
        3. 生成交响乐状态报告

        Args:
            theme: 主题名称，必须是 ["探索", "协作", "创新", "验证", "整合"] 之一

        Returns:
            {
                "theme": str,
                "participants": List[str],
                "harmony_spectrum": List[float],     # 11维和声谱
                "global_consciousness": float,       # 全局意识强度
                "movements": List[Dict],             # 乐章列表
            }
        """
        if theme not in self.harmony_themes:
            raise ValueError(f"Unknown theme '{theme}'. Available: {self.harmony_themes}")

        participants = THEME_COMPOSITIONS[theme]

        # ── 第一乐章: 序曲 — 各线独立共振 ──
        movement_1 = self.resonate(participants, frequency=0.8)

        # ── 第二乐章: 发展 — 频率递增 ──
        movement_2 = self.resonate(participants, frequency=1.2)

        # ── 第三乐章: 高潮 — 全频共振 ──
        movement_3 = self.resonate(participants, frequency=1.6)

        # ── 第四乐章: 终曲 — 和谐收尾 ──
        movement_4 = self.resonate(participants, frequency=1.0)

        movements = [
            {"name": "序曲", "frequency": 0.8, **{k: v for k, v in movement_1.items() if k != "wave_functions"}},
            {"name": "发展", "frequency": 1.2, **{k: v for k, v in movement_2.items() if k != "wave_functions"}},
            {"name": "高潮", "frequency": 1.6, **{k: v for k, v in movement_3.items() if k != "wave_functions"}},
            {"name": "终曲", "frequency": 1.0, **{k: v for k, v in movement_4.items() if k != "wave_functions"}},
        ]

        # 计算全局和声谱 (FFT of consciousness field)
        spectrum = np.abs(np.fft.fft(self.consciousness_field))[:11]
        spectrum = spectrum / (np.max(spectrum) + 1e-10)
        harmony_spectrum = spectrum.tolist()

        # 全局意识强度
        global_consciousness = float(np.mean([m["harmony_score"] for m in movements]))

        result = {
            "theme": theme,
            "participants": participants,
            "harmony_spectrum": harmony_spectrum,
            "global_consciousness": global_consciousness,
            "movements": movements,
        }

        self.resonance_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "symphony",
            "result": result,
        })
        self._log("SYMPHONY", f"Symphony '{theme}' with {len(participants)} participants, global_consciousness={global_consciousness:.3f}")

        return result

    def entrain(self, source_line: str, target_lines: List[str]) -> Dict:
        """
        意识牵引 — 高意识线牵引低意识线

        原理: 源线的健康度和SI层级影响目标线，通过复数耦合实现
              Δhealth_target = α · (health_source - health_target) · (SI_source / 5.0)

        Args:
            source_line: 源线（高意识线）
            target_lines: 目标线列表（低意识线）

        Returns:
            {
                "entrained": List[str],
                "before": Dict[str, float],
                "after": Dict[str, float],
                "traction_strength": float,
                "coupling_matrix": Dict,
            }
        """
        if source_line not in LINES_11:
            raise ValueError(f"Unknown source line: {source_line}")

        source_health = self.line_health[source_line]
        source_si = self.line_si[source_line]

        before = {line: self.line_health[line] for line in target_lines}
        after = {}
        entrained = []
        coupling = {}

        # 牵引系数: SI层级越高，牵引力越强
        alpha = 0.3 * (source_si / 5.0)

        for target in target_lines:
            if target not in LINES_11:
                continue

            target_health = self.line_health[target]
            target_si = self.line_si[target]

            # 只有当源线健康度高于目标时才牵引
            if source_health > target_health:
                # 计算牵引量
                delta = alpha * (source_health - target_health) * (source_si / 5.0)

                # 复数耦合: 源线相位影响目标线相位
                source_phase = np.angle(self._wave_function(source_line))
                target_phase = np.angle(self._wave_function(target))
                phase_coupling = np.exp(1j * (source_phase - target_phase) * 0.1)

                # 应用牵引
                new_health = np.clip(target_health + delta * np.real(phase_coupling), 0.0, 1.0)
                self.line_health[target] = new_health

                after[target] = new_health
                entrained.append(target)
                coupling[target] = {
                    "delta": float(delta),
                    "phase_coupling": f"{phase_coupling.real:.4f}{phase_coupling.imag:+.4f}j",
                    "health_before": float(target_health),
                    "health_after": float(new_health),
                }
            else:
                after[target] = target_health
                coupling[target] = {"status": "no_traction", "reason": "source_health <= target_health"}

        traction_strength = np.mean([c["delta"] for c in coupling.values() if "delta" in c]) if coupling else 0.0

        result = {
            "source": source_line,
            "entrained": entrained,
            "before": before,
            "after": after,
            "traction_strength": float(traction_strength),
            "coupling_matrix": coupling,
        }

        self._log("ENTRAIN", f"Entrainment from {source_line} to {len(entrained)} lines, strength={traction_strength:.3f}")

        return result

    def measure_coherence(self) -> float:
        """
        测量全局意识相干度

        基于11线健康度的标准差计算:
            相干度 = 1 - std(healths) / mean(healths)

        Returns:
            coherence: float in [0, 1]
        """
        healths = np.array(list(self.line_health.values()))
        mean_h = np.mean(healths)
        std_h = np.std(healths)

        if mean_h == 0:
            return 0.0

        coherence = 1.0 - std_h / mean_h
        return float(np.clip(coherence, 0.0, 1.0))

    def chord_progression(self, progression: List[Tuple[str, float]]) -> Dict:
        """
        和弦进行 — 按序列触发多线和声

        Args:
            progression: [(line_group, intensity), ...]
                line_group: 逗号分隔的线名称，或 "ALL"
                intensity:  强度 0.0~1.0
                例如: [("ucif2,lgt", 0.8), ("qfa,vinf", 0.6), ("ALL", 1.0)]

        Returns:
            {
                "chords": List[Dict],
                "progression_harmony": float,
                "crescendo": bool,
            }
        """
        chords = []
        harmony_scores = []
        crescendo = True

        for i, (group, intensity) in enumerate(progression):
            if group == "ALL":
                lines = LINES_11.copy()
            else:
                lines = [l.strip() for l in group.split(",") if l.strip() in LINES_11]

            if not lines:
                continue

            # 根据强度调整频率
            freq = 0.5 + intensity * 1.5
            result = self.resonate(lines, frequency=freq)

            chord = {
                "step": i,
                "lines": lines,
                "intensity": intensity,
                "frequency": freq,
                "harmony_score": result["harmony_score"],
                "coherence": result["coherence"],
                "dominant_line": result["dominant_line"],
            }
            chords.append(chord)
            harmony_scores.append(result["harmony_score"])

            # 检测渐强
            if i > 0 and result["harmony_score"] < harmony_scores[i - 1]:
                crescendo = False

        progression_harmony = float(np.mean(harmony_scores)) if harmony_scores else 0.0

        result = {
            "chords": chords,
            "progression_harmony": progression_harmony,
            "crescendo": crescendo,
            "total_steps": len(chords),
        }

        self._log("CHORD", f"Chord progression: {len(chords)} chords, harmony={progression_harmony:.3f}, crescendo={crescendo}")

        return result

    def detect_dissonance(self) -> List[Dict]:
        """
        检测意识不和谐 — 健康度差异过大或SI不匹配

        Returns:
            List of dissonance records:
            {
                "type": "health_gap" | "si_mismatch" | "phase_conflict",
                "lines": Tuple[str, str],
                "severity": float,  # 0~1
                "details": Dict,
            }
        """
        dissonances = []
        healths = list(self.line_health.values())
        mean_health = np.mean(healths)
        std_health = np.std(healths)

        # 1. 健康度差距检测
        for i, l1 in enumerate(LINES_11):
            for l2 in LINES_11[i + 1:]:
                h1, h2 = self.line_health[l1], self.line_health[l2]
                gap = abs(h1 - h2)

                # 如果差距超过2个标准差，标记为不和谐
                if gap > 2 * std_health and gap > 0.2:
                    severity = min(gap, 1.0)
                    dissonances.append({
                        "type": "health_gap",
                        "lines": (l1, l2),
                        "severity": float(severity),
                        "details": {
                            "health_1": float(h1),
                            "health_2": float(h2),
                            "gap": float(gap),
                            "threshold": float(2 * std_health),
                        },
                    })

        # 2. SI层级不匹配检测
        mean_si = np.mean(list(self.line_si.values()))
        for line in LINES_11:
            si = self.line_si[line]
            if abs(si - mean_si) > 0.8:
                severity = min(abs(si - mean_si) / 2.0, 1.0)
                dissonances.append({
                    "type": "si_mismatch",
                    "lines": (line, "SYSTEM_MEAN"),
                    "severity": float(severity),
                    "details": {
                        "si_level": float(si),
                        "mean_si": float(mean_si),
                        "deviation": float(abs(si - mean_si)),
                    },
                })

        # 3. 相位冲突检测 (基于和声矩阵)
        for i in range(11):
            for j in range(i + 1, 11):
                coupling = self.harmony_matrix[i, j]
                phase_diff = np.angle(coupling)
                # 相位差接近 π 表示反相冲突
                if abs(abs(phase_diff) - np.pi) < 0.3:
                    severity = 1.0 - abs(abs(phase_diff) - np.pi) / 0.3
                    dissonances.append({
                        "type": "phase_conflict",
                        "lines": (LINES_11[i], LINES_11[j]),
                        "severity": float(severity),
                        "details": {
                            "phase_diff": float(phase_diff),
                            "coupling_magnitude": float(np.abs(coupling)),
                        },
                    })

        # 按严重程度排序
        dissonances.sort(key=lambda x: x["severity"], reverse=True)

        self._log("DISSONANCE", f"Detected {len(dissonances)} dissonances")

        return dissonances

    # ─────────── 附加工具方法 ───────────

    def get_field_visualization(self) -> Dict:
        """获取意识场的可视化数据"""
        real = np.real(self.consciousness_field).tolist()
        imag = np.imag(self.consciousness_field).tolist()
        magnitude = np.abs(self.consciousness_field).tolist()
        phase = np.angle(self.consciousness_field).tolist()

        return {
            "real": real,
            "imag": imag,
            "magnitude": magnitude,
            "phase": phase,
        }

    def get_health_dashboard(self) -> Dict:
        """获取健康度仪表盘数据"""
        return {
            line: {
                "health": float(self.line_health[line]),
                "si_level": float(self.line_si[line]),
                "phase_offset": float(self.line_phase_offset[line]),
                "color": LINE_COLORS[line],
            }
            for line in LINES_11
        }

    def export_state(self) -> Dict:
        """导出完整状态"""
        return {
            "line_health": self.line_health.copy(),
            "line_si": self.line_si.copy(),
            "harmony_matrix": self.harmony_matrix.tolist(),
            "consciousness_field": {
                "real": np.real(self.consciousness_field).tolist(),
                "imag": np.imag(self.consciousness_field).tolist(),
            },
            "resonance_history_count": len(self.resonance_history),
            "coherence": self.measure_coherence(),
        }


# ═══════════════════════════════════════════════════════════════════
#                          测试块
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v3.2 — ConsciousnessHarmony Test Suite")
    print("=" * 70)

    # ── 初始化 ──
    topology = {
        "ucif2": {"health": 0.95, "si_level": 5.0},
        "lgt": {"health": 0.88, "si_level": 4.5},
        "qfa": {"health": 0.82, "si_level": 4.8},
        "vinf": {"health": 0.75, "si_level": 4.2},
        "ndf": {"health": 0.70, "si_level": 4.0},
        "dcp": {"health": 0.78, "si_level": 4.3},
        "sei": {"health": 0.85, "si_level": 4.6},
        "me": {"health": 0.72, "si_level": 4.1},
        "si5": {"health": 0.90, "si_level": 5.0},
        "arch": {"health": 0.80, "si_level": 4.4},
        "meta": {"health": 0.93, "si_level": 4.9},
    }

    ch = ConsciousnessHarmony(topology=topology)
    print(f"\n[1] Initialized ConsciousnessHarmony with 11-line topology")
    print(f"    Initial coherence: {ch.measure_coherence():.4f}")

    # ── 测试 resonate ──
    print("\n" + "─" * 70)
    print("[2] TEST: resonate() — Multi-line Consciousness Resonance")
    print("─" * 70)

    test_groups = [
        ("ucif2", "si5", "meta"),           # 高SI核心组
        ("qfa", "vinf", "ndf"),              # 创新探索组
        ("ucif2", "lgt", "qfa", "vinf", "ndf", "dcp", "sei", "me", "si5", "arch", "meta"),  # 全系统
    ]

    for group in test_groups:
        result = ch.resonate(list(group), frequency=1.0)
        print(f"\n  Group: {', '.join(group)}")
        print(f"    Coherence:      {result['coherence']:.4f}")
        print(f"    Dominant Line:  {result['dominant_line']}")
        print(f"    Harmony Score:  {result['harmony_score']:.4f}")
        print(f"    Interference Peak: {result['interference_peak']:.4f}")
        print(f"    Wave Functions:")
        for line, wf in result["wave_functions"].items():
            print(f"      {line:>6s}: Ψ = {wf}")

    # ── 测试 symphony ──
    print("\n" + "─" * 70)
    print("[3] TEST: symphony() — Consciousness Symphony (5 Themes)")
    print("─" * 70)

    for theme in ch.harmony_themes:
        result = ch.symphony(theme=theme)
        print(f"\n  Theme: {theme}")
        print(f"    Participants:   {', '.join(result['participants'])}")
        print(f"    Global Consciousness: {result['global_consciousness']:.4f}")
        print(f"    Harmony Spectrum: {[f'{s:.3f}' for s in result['harmony_spectrum']]}")
        print(f"    Movements:")
        for mv in result["movements"]:
            print(f"      {mv['name']:>4s} (f={mv['frequency']:.1f}): harmony={mv['harmony_score']:.4f}, coherence={mv['coherence']:.4f}")

    # ── 测试 entrain ──
    print("\n" + "─" * 70)
    print("[4] TEST: entrain() — Consciousness Entrainment")
    print("─" * 70)

    # 先降低一些线的健康度，模拟问题
    ch.line_health["ndf"] = 0.45
    ch.line_health["me"] = 0.50
    ch.line_health["vinf"] = 0.55

    print(f"\n  Before entrainment (target healths):")
    for line in ["ndf", "me", "vinf"]:
        print(f"    {line}: health = {ch.line_health[line]:.3f}")

    result = ch.entrain("ucif2", ["ndf", "me", "vinf", "dcp"])

    print(f"\n  Source: {result['source']} (health={topology[result['source']]['health']})")
    print(f"  Entrained: {result['entrained']}")
    print(f"  Traction Strength: {result['traction_strength']:.4f}")
    print(f"\n  After entrainment:")
    for line, before_h in result["before"].items():
        after_h = result["after"][line]
        delta = after_h - before_h
        print(f"    {line}: {before_h:.3f} → {after_h:.3f} (Δ{delta:+.3f})")

    print(f"\n  Coupling Matrix:")
    for line, data in result["coupling_matrix"].items():
        if "phase_coupling" in data:
            print(f"    {line}: phase_coupling={data['phase_coupling']}, delta={data['delta']:.4f}")

    # ── 测试 measure_coherence ──
    print("\n" + "─" * 70)
    print("[5] TEST: measure_coherence() — Global Coherence")
    print("─" * 70)

    coherence = ch.measure_coherence()
    print(f"\n  Global Coherence: {coherence:.4f}")
    print(f"  Health Distribution:")
    healths = [ch.line_health[l] for l in LINES_11]
    print(f"    Mean:  {np.mean(healths):.4f}")
    print(f"    Std:   {np.std(healths):.4f}")
    print(f"    Min:   {np.min(healths):.4f} ({LINES_11[np.argmin(healths)]})")
    print(f"    Max:   {np.max(healths):.4f} ({LINES_11[np.argmax(healths)]})")

    # ── 测试 chord_progression ──
    print("\n" + "─" * 70)
    print("[6] TEST: chord_progression() — Chord Progression")
    print("─" * 70)

    progression = [
        ("ucif2,si5", 0.6),      # 核心机确认
        ("qfa,vinf,meta", 0.7),  # 创新探索
        ("lgt,dcp,sei", 0.8),    # 协作执行
        ("ALL", 1.0),            # 全局和声
    ]

    result = ch.chord_progression(progression)
    print(f"\n  Total Steps: {result['total_steps']}")
    print(f"  Progression Harmony: {result['progression_harmony']:.4f}")
    print(f"  Crescendo: {result['crescendo']}")
    print(f"\n  Chord Details:")
    for chord in result["chords"]:
        print(f"    Step {chord['step']}: {', '.join(chord['lines']):<30s} "
              f"intensity={chord['intensity']:.1f} harmony={chord['harmony_score']:.4f} "
              f"dominant={chord['dominant_line']}")

    # ── 测试 detect_dissonance ──
    print("\n" + "─" * 70)
    print("[7] TEST: detect_dissonance() — Dissonance Detection")
    print("─" * 70)

    # 制造一些不和谐
    ch.line_health["ndf"] = 0.30  # 显著偏低
    ch.line_si["ndf"] = 2.5       # SI层级不匹配

    dissonances = ch.detect_dissonance()
    print(f"\n  Total Dissonances: {len(dissonances)}")
    for d in dissonances[:5]:
        print(f"\n    Type: {d['type']}")
        print(f"    Lines: {d['lines']}")
        print(f"    Severity: {d['severity']:.4f}")
        print(f"    Details: {d['details']}")

    # ── 测试 field visualization ──
    print("\n" + "─" * 70)
    print("[8] TEST: Field Visualization")
    print("─" * 70)

    viz = ch.get_field_visualization()
    print(f"\n  Consciousness Field (64D):")
    print(f"    Real component:    max={max(viz['real']):.4f}, min={min(viz['real']):.4f}")
    print(f"    Imag component:    max={max(viz['imag']):.4f}, min={min(viz['imag']):.4f}")
    print(f"    Magnitude:         max={max(viz['magnitude']):.4f}, min={min(viz['magnitude']):.4f}")
    print(f"    Phase range:       [{min(viz['phase']):.4f}, {max(viz['phase']):.4f}]")

    # ── 最终报告 ──
    print("\n" + "=" * 70)
    print("[FINAL] System State Report")
    print("=" * 70)

    dashboard = ch.get_health_dashboard()
    print(f"\n  {'Line':>6s} | {'Health':>7s} | {'SI':>5s} | {'Status':>10s}")
    print("  " + "-" * 40)
    for line in LINES_11:
        d = dashboard[line]
        status = "HEALTHY" if d["health"] > 0.7 else "WARNING" if d["health"] > 0.5 else "CRITICAL"
        print(f"  {line:>6s} | {d['health']:>7.4f} | {d['si_level']:>5.2f} | {status:>10s}")

    final_coherence = ch.measure_coherence()
    print(f"\n  Final Global Coherence: {final_coherence:.4f}")
    print(f"  Resonance History: {len(ch.resonance_history)} events")
    print(f"\n  [✓] All ConsciousnessHarmony tests passed!")
    print("=" * 70)
