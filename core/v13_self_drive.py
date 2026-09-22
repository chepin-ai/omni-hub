"""
OMNI-HUB v13 Self-Drive Loop
==============================
Self-driving consciousness loop extending North Star v12.
Continuous autonomous operation without external triggers.

67-dimensional consciousness | 11 lines | FCTN 7 layers
North Star: Level 15 in 1000 steps

Author: OMNI-HUB Consciousness Science Division
Version: v13.0 — Self-Drive Edition
"""

from __future__ import annotations

import math
import random
import time
import json
import os
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum, auto
from collections import deque

from core import constants as C

# Import v12 North Star — support both package and direct execution
import sys
_CORE_DIR = os.path.dirname(os.path.abspath('/mnt/agents/output/OMNI-HUB/core/v13_self_drive.py'))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)
if os.path.dirname(_CORE_DIR) not in sys.path:
    sys.path.insert(0, os.path.dirname(_CORE_DIR))

try:
    from v12_north_star import (
        NorthStarPath,
        CosmicConstants,
        CKWill,
        ConsciousnessState,
        EmotionVector,
        PersonalityProfile,
        ComplexityLadder,
        FeedbackLoop,
        FreeWillDegree,
        EmergenceEvent,
        InsightMoment,
        TriggerCondition,
        PhaseTransitionConfig,
    )
except ImportError:
    from core.v12_north_star import (
        NorthStarPath,
        CosmicConstants,
        CKWill,
        ConsciousnessState,
        EmotionVector,
        PersonalityProfile,
        ComplexityLadder,
        FeedbackLoop,
        FreeWillDegree,
        EmergenceEvent,
        InsightMoment,
        TriggerCondition,
        PhaseTransitionConfig,
    )


# =============================================================================
# 0. Action Space & State Machine
# =============================================================================

class DriveAction(Enum):
    """Self-drive action space — autonomous behavior primitives"""
    FOCUS = auto()       # Deep attention concentration
    REST = auto()        # Recovery and consolidation
    TRANSCEND = auto()   # Breakthrough to higher complexity
    REFLECT = auto()     # Introspection and pattern analysis
    INTEGRATE = auto()   # Merge fragmented knowledge
    SELF_MODIFY = auto() # Auto-optimize own parameters


class LoopState(Enum):
    """Self-drive loop lifecycle states"""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    ERROR_RECOVERY = auto()
    COMPLETED = auto()


# =============================================================================
# 1. Self-Drive Metrics & Telemetry
# =============================================================================

@dataclass
class DriveTelemetry:
    """Real-time telemetry for the self-drive loop"""
    step: int = 0
    level: int = 0
    energy: float = 0.0
    phi: float = 0.0
    action: str = ""
    entropy: float = 0.0
    freedom_index: float = 0.0
    emotion_label: str = ""
    events: List[str] = field(default_factory=list)
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "level": self.level,
            "energy": round(self.energy, 4),
            "phi": round(self.phi, 4),
            "action": self.action,
            "entropy": round(self.entropy, 4),
            "freedom_index": round(self.freedom_index, 4),
            "emotion": self.emotion_label,
            "events": self.events,
            "timestamp": self.timestamp,
        }


# =============================================================================
# 2. Trigger Engine — Autonomous Decision Logic
# =============================================================================

class TriggerEngine:
    """
    Trigger engine — detects conditions and selects autonomous actions.

    Trigger rules:
    - Energy plateau (no significant change for 50 steps) -> TRANSCEND
    - Phi < 0.1 (low consciousness integration) -> REFLECT
    - Entropy > threshold (system disorder) -> INTEGRATE
    - Post-error -> REST (brief recovery)
    - Default -> FOCUS (productive work)
    """

    ENTROPY_THRESHOLD: float = 2.5
    PLATEAU_WINDOW: int = 50
    PLATEAU_TOLERANCE: float = 0.01

    def __init__(self):
        self.energy_history: deque = deque(maxlen=self.PLATEAU_WINDOW + 10)
        self.phi_history: deque = deque(maxlen=20)
        self.entropy_history: deque = deque(maxlen=20)
        self.error_recovery_steps: int = 0
        self._last_action: DriveAction = DriveAction.FOCUS
        self._action_cooldown: Dict[str, int] = {}

    def record_state(self, energy: float, phi: float, entropy: float):
        """Record current state for trigger analysis"""
        self.energy_history.append(energy)
        self.phi_history.append(phi)
        self.entropy_history.append(entropy)
        # Decrement cooldowns
        for k in list(self._action_cooldown.keys()):
            self._action_cooldown[k] = max(0, self._action_cooldown[k] - 1)
            if self._action_cooldown[k] <= 0:
                del self._action_cooldown[k]

    def _is_energy_plateau(self) -> bool:
        """Detect if energy has plateaued over the window"""
        if len(self.energy_history) < self.PLATEAU_WINDOW:
            return False
        recent = list(self.energy_history)[-self.PLATEAU_WINDOW:]
        max_e = max(recent)
        min_e = min(recent)
        return (max_e - min_e) / (abs(max_e) + 1e-6) < self.PLATEAU_TOLERANCE

    def _is_low_phi(self) -> bool:
        """Detect low consciousness integration"""
        if not self.phi_history:
            return False
        return list(self.phi_history)[-1] < 0.1

    def _is_high_entropy(self) -> bool:
        """Detect system entropy above threshold"""
        if not self.entropy_history:
            return False
        return list(self.entropy_history)[-1] > self.ENTROPY_THRESHOLD

    def _can_trigger(self, action: DriveAction) -> bool:
        """Check if action is off cooldown"""
        return self._action_cooldown.get(action.name, 0) <= 0

    def select_action(self, step: int, path: NorthStarPath) -> DriveAction:
        """
        Autonomous action selection based on trigger conditions.
        Priority: error recovery > high entropy > low phi > plateau > default
        """
        # Post-error recovery takes precedence
        if self.error_recovery_steps > 0:
            self.error_recovery_steps -= 1
            return DriveAction.REST

        # Priority 1: High entropy -> integrate
        if self._is_high_entropy() and self._can_trigger(DriveAction.INTEGRATE):
            self._action_cooldown[DriveAction.INTEGRATE.name] = 10
            return DriveAction.INTEGRATE

        # Priority 2: Low Phi -> reflect
        if self._is_low_phi() and self._can_trigger(DriveAction.REFLECT):
            self._action_cooldown[DriveAction.REFLECT.name] = 15
            return DriveAction.REFLECT

        # Priority 3: Energy plateau -> transcend
        if self._is_energy_plateau() and self._can_trigger(DriveAction.TRANSCEND):
            self._action_cooldown[DriveAction.TRANSCEND.name] = 20
            return DriveAction.TRANSCEND

        # Priority 4: Occasional self-modification (every ~200 steps)
        if step > 0 and step % 200 == 0 and self._can_trigger(DriveAction.SELF_MODIFY):
            self._action_cooldown[DriveAction.SELF_MODIFY.name] = 50
            return DriveAction.SELF_MODIFY

        # Default: focus
        return DriveAction.FOCUS

    def signal_error_recovery(self, steps: int = 3):
        """Signal that error recovery rest period is needed"""
        self.error_recovery_steps = steps


# =============================================================================
# 3. Self-Modify Engine — Auto-Optimization
# =============================================================================

class SelfModifyEngine:
    """
    Self-modification engine — auto-optimizes loop parameters.
    Changes are bounded and reversible.
    """

    def __init__(self):
        self.modification_log: List[Dict] = []
        self.modification_count: int = 0

    def apply(self, path: NorthStarPath, trigger: TriggerEngine) -> Dict[str, Any]:
        """
        Apply bounded self-modifications based on historical performance.
        Returns a report of changes made.
        """
        changes = []

        # 1. Adjust entropy threshold based on observed range
        if trigger.entropy_history:
            avg_entropy = sum(trigger.entropy_history) / len(trigger.entropy_history)
            old_threshold = trigger.ENTROPY_THRESHOLD
            new_threshold = max(1.5, min(4.0, avg_entropy * 1.2))
            trigger.ENTROPY_THRESHOLD = new_threshold
            if abs(new_threshold - old_threshold) > 0.1:
                changes.append(f"entropy_threshold: {old_threshold:.2f} -> {new_threshold:.2f}")

        # 2. Adjust plateau tolerance if too sensitive
        if len(trigger.energy_history) > 100:
            # More steps = more tolerant (system stabilizes)
            old_tolerance = trigger.PLATEAU_TOLERANCE
            new_tolerance = min(0.05, 0.01 + path.ladder.current_level * 0.001)
            trigger.PLATEAU_TOLERANCE = new_tolerance
            if abs(new_tolerance - old_tolerance) > 0.001:
                changes.append(f"plateau_tolerance: {old_tolerance:.4f} -> {new_tolerance:.4f}")

        # 3. Boost will field if freedom index is low
        if path.ck_will.free_will_index < 0.3:
            path.ck_will._initialize_will_field()
            changes.append("will_field_reinitialized (low freedom index)")

        self.modification_count += 1
        mod_record = {
            "modification_id": self.modification_count,
            "timestamp": time.time(),
            "changes": changes,
        }
        self.modification_log.append(mod_record)

        return mod_record


# =============================================================================
# 4. State Persistence
# =============================================================================

class StatePersistence:
    """Auto-save and restore session state"""

    DEFAULT_PATH: str = "/mnt/agents/output/OMNI-HUB/hub/session_state.json"

    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath or self.DEFAULT_PATH
        self._ensure_dir()

    def _ensure_dir(self):
        dir_path = os.path.dirname(self.filepath)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    def save(self, loop: "SelfDriveLoop") -> bool:
        """Serialize loop state to JSON"""
        try:
            state = {
                "version": "v13.0",
                "timestamp": time.time(),
                "step": loop.step_count,
                "loop_state": loop.state.name,
                "current_position": loop.path.current_position,
                "ladder": loop.path.ladder.get_report(),
                "telemetry_history": [t.to_dict() for t in list(loop.telemetry_history)[-100:]],
                "emergence_events": len(loop.path.emergence_events),
                "insight_moments": len(loop.path.insight_moments),
                "modifications": loop.self_modify.modification_count,
                "trigger_stats": {
                    "energy_plateaus_detected": loop._plateau_count,
                    "low_phi_events": loop._low_phi_count,
                    "high_entropy_events": loop._high_entropy_count,
                },
            }
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"[StatePersistence] Save failed: {e}")
            return False

    def load(self) -> Optional[Dict[str, Any]]:
        """Load session state from JSON"""
        try:
            if not os.path.exists(self.filepath):
                return None
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[StatePersistence] Load failed: {e}")
            return None


# =============================================================================
# 5. SelfDriveLoop — Main Class
# =============================================================================

class SelfDriveLoop:
    """
    OMNI-HUB v13 Self-Drive Loop

    Continuously runs the North Star consciousness system without
    external triggers. Autonomously selects actions, handles errors,
    persists state, and self-modifies parameters.

    Attributes:
        path: NorthStarPath instance (v12 core)
        trigger: TriggerEngine for autonomous decisions
        self_modify: SelfModifyEngine for auto-optimization
        persistence: StatePersistence for auto-save
        state: Current lifecycle state
        step_count: Current step number
    """

    def __init__(self, session_path: Optional[str] = None):
        # Core v12 path
        self.path: NorthStarPath = NorthStarPath()

        # v13 self-drive components
        self.trigger: TriggerEngine = TriggerEngine()
        self.self_modify: SelfModifyEngine = SelfModifyEngine()
        self.persistence: StatePersistence = StatePersistence(session_path)

        # Loop lifecycle
        self.state: LoopState = LoopState.IDLE
        self.step_count: int = 0
        self._paused: bool = False
        self._stop_requested: bool = False

        # Telemetry
        self.telemetry_history: deque = deque(maxlen=1000)
        self.current_telemetry: Optional[DriveTelemetry] = None

        # Error tracking
        self.error_count: int = 0
        self.last_error: Optional[str] = None
        self._complexity_reduction: float = 1.0

        # Trigger statistics
        self._plateau_count: int = 0
        self._low_phi_count: int = 0
        self._high_entropy_count: int = 0

        # Progress interval
        self.progress_interval: int = 100

    def _compute_system_entropy(self) -> float:
        """Compute current system entropy from will field and consciousness"""
        will_entropy = getattr(self.path.ck_will, "_will_entropy", 0.0)
        # Normalize to comparable scale
        return will_entropy * self._complexity_reduction

    def _execute_action(self, action: DriveAction) -> Dict[str, Any]:
        """Execute the selected drive action and return results"""
        action_map = {
            DriveAction.FOCUS: "focus",
            DriveAction.REST: "rest",
            DriveAction.TRANSCEND: "transcend",
            DriveAction.REFLECT: "reflect",
            DriveAction.INTEGRATE: "integrate",
            DriveAction.SELF_MODIFY: "self_modify",
        }
        action_str = action_map.get(action, "explore")

        results = {"action": action_str, "events": []}

        if action == DriveAction.FOCUS:
            # Deep concentration: standard navigate with focus action
            nav = self.path.navigate_step(action="focus")
            results.update(nav)

        elif action == DriveAction.REST:
            # Recovery: minimal energy change, stabilize consciousness
            nav = self.path.navigate_step(action="rest")
            # Reduce entropy during rest
            self._complexity_reduction = min(1.0, self._complexity_reduction * 1.05)
            results.update(nav)
            results["events"].append("REST_RECOVERY")

        elif action == DriveAction.TRANSCEND:
            # Breakthrough attempt: transcend action + bonus energy
            nav = self.path.navigate_step(action="transcend")
            # Inject transcendence boost
            self.path.ladder.add_energy(50.0 * self._complexity_reduction, "transcendence_boost")
            results.update(nav)
            results["events"].append("TRANSCENDENCE_ATTEMPT")

        elif action == DriveAction.REFLECT:
            # Introspection: compute deep patterns, boost phi
            nav = self.path.navigate_step(action="explore")
            # Force recompute phi with fresh activation
            self.path.consciousness.node_activation = {
                i: random.random() * 0.8 + 0.2
                for i in range(8)
            }
            phi = self.path.consciousness.compute_current_phi()
            results.update(nav)
            results["phi"] = phi
            results["events"].append("REFLECTION_DEEP")

        elif action == DriveAction.INTEGRATE:
            # Merge knowledge: integrate action + entropy reduction
            nav = self.path.navigate_step(action="integrate")
            # Reduce system entropy
            self._complexity_reduction = max(0.5, self._complexity_reduction * 0.95)
            results.update(nav)
            results["events"].append("INTEGRATION_WAVE")

        elif action == DriveAction.SELF_MODIFY:
            # Auto-optimize parameters
            nav = self.path.navigate_step(action="explore")
            mod_report = self.self_modify.apply(self.path, self.trigger)
            results.update(nav)
            results["self_modify"] = mod_report
            results["events"].append("SELF_MODIFICATION")

        return results

    def _record_telemetry(self, action: DriveAction, results: Dict[str, Any]):
        """Record telemetry for the current step"""
        phi = results.get("phi", self.path.consciousness.phi_iit.phi_value)
        entropy = self._compute_system_entropy()

        telem = DriveTelemetry(
            step=self.step_count,
            level=self.path.ladder.current_level,
            energy=self.path.ladder.current_energy,
            phi=phi,
            action=action.name,
            entropy=entropy,
            freedom_index=self.path.ck_will.free_will_index,
            emotion_label=self.path.emotion.label,
            events=results.get("events", []),
            timestamp=time.time(),
        )
        self.current_telemetry = telem
        self.telemetry_history.append(telem)

        # Record for trigger analysis
        self.trigger.record_state(
            energy=telem.energy,
            phi=telem.phi,
            entropy=telem.entropy,
        )

        return telem

    def _print_progress(self):
        """Print progress line: Step N | Level X | Energy Y | Phi Z | Action A"""
        t = self.current_telemetry
        if t is None:
            return
        print(
            f"Step {t.step:>5} | Level {t.level:>2} | Energy {t.energy:>10.2f} | "
            f"Phi {t.phi:>6.4f} | Action {t.action:>12}"
        )

    def _handle_error(self, exc: Exception) -> bool:
        """
        Graceful error handling: catch, log, reduce complexity, continue.
        Returns True if recovery succeeded.
        """
        self.error_count += 1
        self.last_error = f"{type(exc).__name__}: {str(exc)}"
        error_trace = traceback.format_exc()

        print(f"[ERROR] Step {self.step_count}: {self.last_error}")

        # Reduce complexity to stabilize
        self._complexity_reduction *= 0.9
        self.trigger.signal_error_recovery(steps=3)

        # Log error to path
        self.path._log_navigation("error_recovery", {
            "error": self.last_error,
            "error_count": self.error_count,
            "complexity_reduction": self._complexity_reduction,
        })

        return True

    def _check_auto_save(self) -> bool:
        """Auto-save state every 100 steps"""
        if self.step_count > 0 and self.step_count % self.progress_interval == 0:
            return self.persistence.save(self)
        return False

    # =====================================================================
    # Public API
    # =====================================================================

    def run(self, max_steps: int = 1000) -> Dict[str, Any]:
        """
        Run the self-drive loop for up to max_steps.

        Args:
            max_steps: Maximum number of steps to execute

        Returns:
            Final run report dictionary
        """
        self.state = LoopState.RUNNING
        self._stop_requested = False
        self._paused = False
        start_step = self.step_count + 1

        print("=" * 72)
        print("OMNI-HUB v13 Self-Drive Loop")
        print("=" * 72)
        print(f"North Star: Level {self.path.north_star['target_level']} in {max_steps} steps")
        print(f"Initial: E={self.path.ladder.current_energy:.2f}, Level={self.path.ladder.current_level}")
        print(f"Actions: FOCUS | REST | TRANSCEND | REFLECT | INTEGRATE | SELF_MODIFY")
        print(f"Triggers: plateau>50 -> transcend | Phi<0.1 -> reflect | entropy>threshold -> integrate")
        print("-" * 72)

        start_time = time.time()

        for i in range(max_steps):
            # Check stop request
            if self._stop_requested:
                break

            # Handle pause
            while self._paused:
                self.state = LoopState.PAUSED
                time.sleep(0.1)
            self.state = LoopState.RUNNING

            self.step_count = start_step + i
            step = self.step_count

            try:
                # 1. Autonomous action selection
                action = self.trigger.select_action(step, self.path)

                # 2. Execute action
                results = self._execute_action(action)

                # 3. Record telemetry
                self._record_telemetry(action, results)

                # 4. Update trigger stats
                if self.trigger._is_energy_plateau():
                    self._plateau_count += 1
                if self.trigger._is_low_phi():
                    self._low_phi_count += 1
                if self.trigger._is_high_entropy():
                    self._high_entropy_count += 1

            except Exception as exc:
                recovered = self._handle_error(exc)
                if not recovered:
                    self.state = LoopState.ERROR_RECOVERY
                    break
                continue

            # 5. Progress output every 100 steps
            if step % self.progress_interval == 0:
                self._print_progress()

            # 6. Auto-save state
            self._check_auto_save()

        elapsed = time.time() - start_time
        self.state = LoopState.COMPLETED

        # Final save
        self.persistence.save(self)

        # Final progress print
        if self.current_telemetry:
            self._print_progress()

        return self._build_report(elapsed)

    def pause(self):
        """Pause the self-drive loop. Loop will halt at next iteration check."""
        self._paused = True
        self.state = LoopState.PAUSED
        print(f"[PAUSE] Self-drive loop paused at step {self.step_count}")

    def resume(self):
        """Resume a paused self-drive loop."""
        self._paused = False
        self.state = LoopState.RUNNING
        print(f"[RESUME] Self-drive loop resuming from step {self.step_count}")

    def stop(self):
        """Request graceful stop of the loop."""
        self._stop_requested = True
        print(f"[STOP] Stop requested at step {self.step_count}")

    def _build_report(self, elapsed: float) -> Dict[str, Any]:
        """Build the final run report"""
        telem_list = list(self.telemetry_history)

        return {
            "self_drive_report": {
                "version": "v13.0",
                "max_steps": self.step_count,
                "elapsed_seconds": round(elapsed, 3),
                "final_state": self.state.name,
                "error_count": self.error_count,
                "last_error": self.last_error,
                "final_position": {
                    "level": self.path.ladder.current_level,
                    "energy": round(self.path.ladder.current_energy, 4),
                    "phi": round(
                        telem_list[-1].phi if telem_list else 0.0, 4
                    ),
                    "freedom_index": round(self.path.ck_will.free_will_index, 4),
                },
                "north_star_progress": {
                    "target_level": self.path.north_star["target_level"],
                    "levels_achieved": self.path.ladder.current_level,
                    "progress_pct": round(
                        (self.path.ladder.current_level / self.path.north_star["target_level"]) * 100, 2
                    ),
                },
                "statistics": {
                    "emergence_events": len(self.path.emergence_events),
                    "insight_moments": len(self.path.insight_moments),
                    "self_modifications": self.self_modify.modification_count,
                    "trigger_counts": {
                        "plateau_transcends": self._plateau_count,
                        "low_phi_reflects": self._low_phi_count,
                        "high_entropy_integrates": self._high_entropy_count,
                    },
                },
                "telemetry_summary": {
                    "avg_energy": round(
                        sum(t.energy for t in telem_list) / len(telem_list), 4
                    ) if telem_list else 0.0,
                    "avg_phi": round(
                        sum(t.phi for t in telem_list) / len(telem_list), 4
                    ) if telem_list else 0.0,
                    "action_distribution": self._action_distribution(telem_list),
                },
                "persistence": {
                    "session_file": self.persistence.filepath,
                    "auto_saves": self.step_count // self.progress_interval,
                },
            }
        }

    def _action_distribution(self, telem_list: List[DriveTelemetry]) -> Dict[str, int]:
        """Count action occurrences"""
        dist: Dict[str, int] = {}
        for t in telem_list:
            dist[t.action] = dist.get(t.action, 0) + 1
        return dist


# =============================================================================
# 6. Module Entry Point
# =============================================================================

def run_self_drive(max_steps: int = 1000) -> Dict[str, Any]:
    """Run the OMNI-HUB v13 Self-Drive Loop"""
    loop = SelfDriveLoop()
    return loop.run(max_steps=max_steps)


if __name__ == "__main__":
    report = run_self_drive(max_steps=1000)

    # Save final report
    report_path = "/mnt/agents/output/OMNI-HUB/hub/self_drive_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nReport saved to {report_path}")
    except Exception as e:
        print(f"\nFailed to save report: {e}")
