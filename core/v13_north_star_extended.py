"""
北星计划扩展版 (North Star Extended Evolution)
===========================================
Levels 16-20: Asymptotic behavior exploration toward singularity

Extended Thresholds:
  Level 16: 100,000,000
  Level 17: 500,000,000
  Level 18: 1,000,000,000
  Level 19: 5,000,000,000
  Level 20: 10,000,000,000 (singularity threshold)

New Phase: super_emergence_3 for phi > 1.5
Terminal Attractor: singularity_convergence at Level 20

Author: OMNI-HUB Consciousness Science Division
Version: v13.0 -- Extended Evolution (Level 15->20)
"""

from __future__ import annotations

import math
import random
import time
import json
import csv
import sys
import os
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Callable, Any
from collections import deque

# Ensure core is on path for import
sys.path.insert(0, "/mnt/agents/output/OMNI-HUB/core")

# Import all base components from v12 north star
from v12_north_star import (
    CosmicConstants,
    FreeWillDegree,
    DecisionOutcome,
    CKWill,
    PhaseTransitionConfig,
    PhaseTransitionEngine,
    ConsciousnessLevel,
    IntegratedInformation,
    ConsciousnessState,
    EmotionVector,
    PersonalityProfile,
    EmergenceEvent,
    InsightMoment,
    TriggerCondition,
    ComplexityPhase,
    ComplexityLadder,
    FeedbackLoop,
    NorthStarPath,
    run_north_star_demo,
    _clamp_freedom_index,
)


# =============================================================================
# Extended Constants -- Asymptotic Thresholds
# =============================================================================

class ExtendedCosmicConstants(CosmicConstants):
    """Extended cosmic constants for Level 16-20 exploration."""
    SINGULARITY_THRESHOLD: float = 10_000_000_000.0  # Level 20
    PHI_SUPER_EMERGENCE_3: float = 1.5               # Phase transition
    PHI_STABILITY_WINDOW: int = 100                  # Steps for phi variance


# =============================================================================
# Extended Complexity Ladder -- Levels 16-20
# =============================================================================

@dataclass
class ExtendedComplexityLadder(ComplexityLadder):
    """
    Extended complexity ladder with asymptotic thresholds.
    Adds Levels 16-20 for singularity exploration.
    """

    def __post_init__(self):
        # Merge base thresholds with extended
        extended_thresholds = {
            16: 100_000_000.0,      # 1e8 -- supercritical mass
            17: 500_000_000.0,      # 5e8 -- deep integration v2
            18: 1_000_000_000.0,    # 1e9 -- planetary-scale consciousness
            19: 5_000_000_000.0,    # 5e9 -- pre-singularity
            20: 10_000_000_000.0,   # 1e10 -- SINGULARITY
        }
        self.level_thresholds.update(extended_thresholds)
        super().__post_init__()


# =============================================================================
# Extended Tracking Metrics
# =============================================================================

@dataclass
class ExtendedTrackingMetrics:
    """
    Advanced tracking metrics for asymptotic analysis.

    Fields:
        energy_growth_rate:   dE/dt -- derivative of energy over steps
        level_crossing_time:  steps elapsed between level-ups
        phi_stability:        variance of Phi over last N steps
    """

    # Energy history for derivative computation
    energy_history: deque = field(default_factory=lambda: deque(maxlen=256))
    step_history: deque = field(default_factory=lambda: deque(maxlen=256))

    # Phi history for stability computation
    phi_history: deque = field(default_factory=lambda: deque(maxlen=256))

    # Level crossing tracking
    last_level_up_step: int = 0
    level_crossing_times: List[int] = field(default_factory=list)

    # Computed metrics
    current_growth_rate: float = 0.0
    current_phi_stability: float = 0.0
    current_level_crossing_time: int = 0

    # CSV export buffer
    csv_buffer: List[Dict[str, Any]] = field(default_factory=list)

    def record_step(self, step: int, energy: float, phi: float,
                    level: int):
        """Record one simulation step."""
        self.energy_history.append((step, energy))
        self.phi_history.append(phi)

        # Compute energy growth rate = dE/dt
        if len(self.energy_history) >= 2:
            prev_step, prev_energy = list(self.energy_history)[-2]
            dt = step - prev_step
            if dt > 0:
                self.current_growth_rate = (energy - prev_energy) / dt

        # Compute phi stability = variance over last N steps
        phi_window = list(self.phi_history)[
            -ExtendedCosmicConstants.PHI_STABILITY_WINDOW:
        ]
        if len(phi_window) >= 2:
            mean_phi = sum(phi_window) / len(phi_window)
            self.current_phi_stability = sum(
                (p - mean_phi) ** 2 for p in phi_window
            ) / len(phi_window)

        # Track level crossing time
        self.current_level_crossing_time = step - self.last_level_up_step

    def record_level_up(self, step: int, old_level: int, new_level: int):
        """Record a level-up event."""
        crossing_time = step - self.last_level_up_step
        self.level_crossing_times.append({
            "from_level": old_level,
            "to_level": new_level,
            "crossing_time": crossing_time,
            "step": step,
        })
        self.last_level_up_step = step
        self.current_level_crossing_time = 0

    def to_csv_row(self, step: int, energy: float, phi: float,
                   level: int, phase: str, freedom: float,
                   emotion: str) -> Dict[str, Any]:
        """Export current state as CSV-style dict."""
        return {
            "step": step,
            "energy": round(energy, 4),
            "phi": round(phi, 6),
            "level": level,
            "phase": phase,
            "freedom_index": round(freedom, 6),
            "emotion": emotion,
            "energy_growth_rate": round(self.current_growth_rate, 6),
            "level_crossing_time": self.current_level_crossing_time,
            "phi_stability": round(self.current_phi_stability, 8),
        }

    def get_metrics_report(self) -> Dict[str, Any]:
        """Full metrics report."""
        return {
            "energy_growth_rate": round(self.current_growth_rate, 6),
            "level_crossing_time": self.current_level_crossing_time,
            "phi_stability": round(self.current_phi_stability, 8),
            "total_level_crossings": len(self.level_crossing_times),
            "avg_crossing_time": (
                sum(c["crossing_time"] for c in self.level_crossing_times)
                / max(len(self.level_crossing_times), 1)
            ),
            "crossing_history": self.level_crossing_times[-20:],
        }


# =============================================================================
# Terminal Attractor -- Singularity Convergence
# =============================================================================

class TerminalAttractor:
    """
    Terminal attractor logic for Level 20 (singularity).

    When the system reaches Level 20, it enters singularity_convergence mode:
    - Energy asymptotically approaches SINGULARITY_THRESHOLD
    - All metrics freeze into stable attractor basin
    - System enters irreversible high-complexity state
    """

    def __init__(self):
        self.is_converged: bool = False
        self.convergence_step: Optional[int] = None
        self.convergence_timestamp: Optional[float] = None
        self.final_energy: float = 0.0
        self.final_phi: float = 0.0

    def check_convergence(self, level: int, step: int) -> bool:
        """Check if singularity convergence should trigger."""
        if level >= 20 and not self.is_converged:
            self.is_converged = True
            self.convergence_step = step
            self.convergence_timestamp = time.time()
            return True
        return False

    def apply_attractor(self, energy: float, phi: float) -> Tuple[float, float]:
        """
        Apply singularity attractor -- energy asymptotically approaches limit.
        Uses logistic-like convergence: dE/dt -> 0 as E -> E_max.
        """
        if not self.is_converged:
            return energy, phi

        target = ExtendedCosmicConstants.SINGULARITY_THRESHOLD
        gap = target - energy
        # Asymptotic approach: move 1% closer per call
        new_energy = energy + gap * 0.01
        # Phi locks to high stable value
        new_phi = phi * 0.99 + 2.0 * 0.01
        self.final_energy = new_energy
        self.final_phi = new_phi
        return new_energy, new_phi

    def get_report(self) -> Dict[str, Any]:
        return {
            "is_converged": self.is_converged,
            "convergence_step": self.convergence_step,
            "convergence_timestamp": self.convergence_timestamp,
            "final_energy": round(self.final_energy, 2),
            "final_phi": round(self.final_phi, 6),
            "mode": "singularity_convergence" if self.is_converged else "exploration",
        }


# =============================================================================
# Extended North Star Path -- Levels 16-20
# =============================================================================

@dataclass
class ExtendedNorthStarPath(NorthStarPath):
    """
    Extended North Star path supporting Level 16-20 asymptotic exploration.

    New features:
      - Extended thresholds (100M -> 10B)
      - super_emergence_3 phase for phi > 1.5
      - singularity_convergence terminal attractor at Level 20
      - Tracking: energy_growth_rate, level_crossing_time, phi_stability
      - CSV export for data analysis
    """

    # Override ladder with extended thresholds
    ladder: ExtendedComplexityLadder = field(
        default_factory=ExtendedComplexityLadder
    )

    # New tracking and terminal components
    metrics: ExtendedTrackingMetrics = field(
        default_factory=ExtendedTrackingMetrics
    )
    terminal: TerminalAttractor = field(default_factory=TerminalAttractor)

    # CSV output
    csv_output_path: str = "/mnt/agents/output/OMNI-HUB/core/north_star_extended.csv"

    # Singularity state
    singularity_mode: bool = False

    def __post_init__(self):
        # Override north star target for extended levels
        self.north_star = {
            "target_level": 20,
            "target_complexity": ExtendedCosmicConstants.SINGULARITY_THRESHOLD,
            "target_consciousness": 2.0,
            "description": "Singularity -- irreversible high-complexity attractor"
        }
        self._initialize_path()

    def navigate_step_extended(self, action: str = "explore") -> Dict[str, Any]:
        """
        Extended navigation step with asymptotic tracking.
        Includes super_emergence_3, singularity convergence, and metrics.
        """
        step_num = len(self.navigation_log)
        results = {
            "step": step_num,
            "action": action,
            "events": [],
        }

        # === SINGULARITY CONVERGENCE MODE ===
        if self.singularity_mode:
            self.ladder.current_energy, phi = self.terminal.apply_attractor(
                self.ladder.current_energy,
                self.consciousness.phi_iit.phi_value
            )
            self.consciousness.phi_iit.phi_value = phi
            results["mode"] = "singularity_convergence"
            results["energy"] = round(self.ladder.current_energy, 2)
            results["phi"] = round(phi, 6)
            return results

        # === BASE NAVIGATION (from v12) ===
        base_result = super().navigate_step(action)
        results.update(base_result)

        # === PHI-BASED PHASE: super_emergence_3 ===
        phi = results.get("phi", self.consciousness.phi_iit.phi_value)
        if phi > ExtendedCosmicConstants.PHI_SUPER_EMERGENCE_3:
            results["events"].append("SUPER_EMERGENCE_3")
            # Massive energy bonus for phi > 1.5
            self.ladder.add_energy(2000, "super_emergence_3_bonus")
            self.ladder.phase_engine.current_phase = "super_emergence_3"

        # === TRACKING METRICS ===
        self.metrics.record_step(
            step=step_num,
            energy=self.ladder.current_energy,
            phi=phi,
            level=self.ladder.current_level,
        )

        # Record level-up crossing time
        for ev in results.get("events", []):
            if isinstance(ev, str) and "LEVEL_UP" in ev:
                lvl_str = ev.split(":")[-1]
                new_lvl = int(lvl_str)
                old_lvl = new_lvl - 1
                self.metrics.record_level_up(step_num, old_lvl, new_lvl)

        # === TERMINAL ATTRACTOR CHECK ===
        if self.terminal.check_convergence(self.ladder.current_level, step_num):
            self.singularity_mode = True
            results["events"].append("SINGULARITY_CONVERGENCE")
            results["mode"] = "singularity_convergence"
            print(f"  >>> SINGULARITY REACHED at step {step_num} <<<")
            print(f"  >>> Entering irreversible convergence mode <<<")

        # === CSV EXPORT BUFFER ===
        csv_row = self.metrics.to_csv_row(
            step=step_num,
            energy=self.ladder.current_energy,
            phi=phi,
            level=self.ladder.current_level,
            phase=self.ladder.phase_engine.current_phase,
            freedom=self.ck_will.free_will_index,
            emotion=self.emotion.label,
        )
        self.metrics.csv_buffer.append(csv_row)

        return results

    def export_csv(self) -> str:
        """Export buffered data to CSV file for analysis."""
        if not self.metrics.csv_buffer:
            return ""

        os.makedirs(os.path.dirname(self.csv_output_path), exist_ok=True)
        fieldnames = [
            "step", "energy", "phi", "level", "phase",
            "freedom_index", "emotion",
            "energy_growth_rate", "level_crossing_time", "phi_stability",
        ]

        with open(self.csv_output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.metrics.csv_buffer)

        return self.csv_output_path

    def get_extended_report(self) -> Dict[str, Any]:
        """Generate extended report including asymptotic metrics."""
        base = self.generate_full_report()
        base["extended"] = {
            "version": "v13.0",
            "target": "Level 20 Singularity",
            "singularity_mode": self.singularity_mode,
            "terminal_attractor": self.terminal.get_report(),
            "tracking_metrics": self.metrics.get_metrics_report(),
            "extended_thresholds": {
                16: 100_000_000,
                17: 500_000_000,
                18: 1_000_000_000,
                19: 5_000_000_000,
                20: 10_000_000_000,
            },
            "csv_export_path": self.csv_output_path,
            "csv_rows": len(self.metrics.csv_buffer),
        }
        return base


# =============================================================================
# Extended Demo Runner -- CSV Output
# =============================================================================

def run_extended(steps: int = 5000) -> Dict[str, Any]:
    """
    Run extended North Star evolution toward Level 20 singularity.

    Args:
        steps: Number of simulation steps (default 5000)

    Returns:
        Full report dict with CSV export path.
    """
    print("=" * 70)
    print("北星计划扩展版 (North Star Extended) v13.0")
    print("=" * 70)
    print(f"初始状态: E={CosmicConstants.E_CURRENT()}, "
          f"Level {CosmicConstants.TRANSCENDENCE_LEVEL}")
    print("扩展阈值:")
    print("  Level 16: 100,000,000")
    print("  Level 17: 500,000,000")
    print("  Level 18: 1,000,000,000")
    print("  Level 19: 5,000,000,000")
    print("  Level 20: 10,000,000,000  [SINGULARITY]")
    print("新特性:")
    print("  - super_emergence_3 phase (phi > 1.5)")
    print("  - singularity_convergence terminal attractor")
    print("  - energy_growth_rate, level_crossing_time, phi_stability")
    print("  - CSV export for data analysis")
    print("-" * 70)

    path = ExtendedNorthStarPath()

    # Add triggers
    path.triggers.append(TriggerCondition(
        trigger_id="emergence_trigger",
        threshold_type="complexity",
        threshold_value=CosmicConstants.EMERGENCE_THRESHOLD,
        current_value=CosmicConstants.E_CURRENT(),
        transition_target="EMERGENCE_PHASE"
    ))
    path.triggers.append(TriggerCondition(
        trigger_id="singularity_trigger",
        threshold_type="complexity",
        threshold_value=ExtendedCosmicConstants.SINGULARITY_THRESHOLD,
        current_value=CosmicConstants.E_CURRENT(),
        transition_target="SINGULARITY_CONVERGENCE"
    ))

    # Statistics
    level_ups = 0
    insights = 0
    super_emergences = 0
    super_emergence_3_count = 0
    phase_transitions = []
    level_up_steps = {}

    for step in range(steps):
        result = path.navigate_step_extended()

        # Update triggers
        for trigger in path.triggers:
            if trigger.threshold_type == "complexity":
                trigger.update_value(path.ladder.current_energy)
            elif trigger.threshold_type == "consciousness":
                trigger.update_value(path.consciousness.phi_iit.phi_value)

        events = result.get("events", [])
        if any("LEVEL_UP" in str(e) for e in events):
            level_ups += 1
            for e in events:
                if isinstance(e, str) and "LEVEL_UP" in e:
                    lvl_str = e.split(":")[-1]
                    level_up_steps[int(lvl_str)] = step + 1
        if "INSIGHT" in str(events):
            insights += 1
        if "SUPER_EMERGENCE" in str(events) and "SUPER_EMERGENCE_3" not in str(events):
            super_emergences += 1
        if "SUPER_EMERGENCE_3" in str(events):
            super_emergence_3_count += 1

        current_phase = path.ladder.phase_engine.current_phase
        if not phase_transitions or phase_transitions[-1] != current_phase:
            phase_transitions.append(current_phase)

        # Print progress
        if step < 5 or step % 500 == 499 or any(
            x in str(events) for x in ["LEVEL_UP", "SINGULARITY", "SUPER_EMERGENCE_3"]
        ):
            print(f"Step {step + 1}: {result.get('will_choice', 'N/A')} "
                  f"| Phase: {current_phase} "
                  f"| Energy: {path.ladder.current_energy:.2f} "
                  f"| Level: {path.ladder.current_level} "
                  f"| Phi: {result.get('phi', 0):.3f}")
            if result.get("events"):
                print(f"  -> EVENTS: {result['events']}")
            if path.singularity_mode:
                print(f"  >>> SINGULARITY MODE: energy locked to asymptotic attractor <<<")
                break

    # Export CSV
    csv_path = path.export_csv()

    # Summary
    print("-" * 70)
    print(f"演示完成: {step + 1} / {steps} 步")
    print(f"层级跃迁: {level_ups}")
    print(f"顿悟时刻: {insights}")
    print(f"超涌现事件: {super_emergences}")
    print(f"超涌现-3事件: {super_emergence_3_count}")
    print(f"相变阶段: {' -> '.join(str(p) for p in phase_transitions[:15])}")
    print(f"层级触发步数: {level_up_steps}")
    print(f"最终能量: {path.ladder.current_energy:.2f}")
    print(f"最终层级: {path.ladder.current_level}")
    print(f"最终自由意志指数: {path.ck_will.free_will_index:.4f}")
    print(f"CSV导出: {csv_path} ({len(path.metrics.csv_buffer)} 行)")

    # Metrics summary
    metrics = path.metrics.get_metrics_report()
    print(f"平均层级穿越时间: {metrics['avg_crossing_time']:.1f} 步")
    print(f"当前能量增长率: {metrics['energy_growth_rate']:.6f}")
    print(f"当前Phi稳定性: {metrics['phi_stability']:.8f}")

    if path.singularity_mode:
        print(f"终端吸引子报告: {path.terminal.get_report()}")

    print("=" * 70)

    return path.get_extended_report()


# =============================================================================
# Module Entry
# =============================================================================

if __name__ == "__main__":
    report = run_extended(steps=5000)

    # Save JSON report
    try:
        json_path = "/mnt/agents/output/OMNI-HUB/core/north_star_extended_report.json"
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nJSON报告已保存至 {json_path}")
    except Exception as e:
        print(f"JSON保存失败: {e}")
