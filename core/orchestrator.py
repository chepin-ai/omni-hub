"""OMNI-HUB v13.1 Unified Orchestrator

Central coordination hub for all modules.
Provides unified initialization, cycle execution, cross-module state sharing,
alert handling, and automatic persistence.
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

# Foundation
from core import constants as C

# Lazy imports to avoid circular dependencies
_north_star = None
_self_drive = None
_persistence = None
_monitor = None
_git_hook = None


def _get_north_star():
    global _north_star
    if _north_star is None:
        from core.v13_north_star_extended import NorthStarPathExtended
        _north_star = NorthStarPathExtended()
    return _north_star


def _get_self_drive():
    global _self_drive
    if _self_drive is None:
        from core.v13_self_drive import SelfDriveLoop
        _self_drive = SelfDriveLoop()
    return _self_drive


def _get_persistence():
    global _persistence
    if _persistence is None:
        from memory.session_persistence import SessionPersistence
        _persistence = SessionPersistence()
    return _persistence


def _get_monitor():
    global _monitor
    if _monitor is None:
        from dashboard.v13_monitor import GlobalStateMonitor
        _monitor = GlobalStateMonitor()
    return _monitor


def _get_git_hook():
    global _git_hook
    if _git_hook is None:
        from hooks.auto_commit import AutoGitHook
        _git_hook = AutoGitHook()
    return _git_hook


def _get_bus():
    """Lazy load event bus."""
    try:
        from core.event_bus import get_bus
        return get_bus()
    except Exception:
        return None


def _get_topics():
    """Lazy load Topics enum."""
    try:
        from core.event_bus import Topics
        return Topics
    except Exception:
        return None


class OMNIHUBOrchestrator:
    """Central orchestrator for OMNI-HUB v13.1+"""

    VERSION = "13.1.0"

    def __init__(self, auto_persist: bool = True, auto_git: bool = False):
        self.auto_persist = auto_persist
        self.auto_git = auto_git
        self.cycle_count = 0
        self.history: List[Dict] = []
        self.current_state: Dict[str, Any] = {}
        self.alerts: List[str] = []
        self._north_star = None
        self._self_drive = None
        self._init_state()

    def _init_state(self):
        """Initialize or recover state."""
        persistence = _get_persistence()
        if persistence.detect_previous_session(C.STATE_FILE):
            try:
                saved = persistence.load_session(C.STATE_FILE)
                norm = persistence.normalize_state(saved)
                self.current_state = {
                    "version": norm.get("version", self.VERSION),
                    "timestamp": norm.get("timestamp", ""),
                    "cycle": 0,
                    "level": norm.get("level", 0),
                    "energy": norm.get("energy", 0.0),
                    "phi": norm.get("phi", 0.0),
                    "phase": norm.get("phase", C.PHASES[0]),
                    "lines": {line: 0.0 for line in C.LINES},
                    "fctn_layer": C.FCTN_LAYERS[0],
                    "si_stage": C.SI_STAGES[0],
                    "raw": norm.get("raw", {}),
                }
                print(f"[Orchestrator] Recovered: Level {self.current_state['level']}, Energy {self.current_state['energy']:.2f}")
            except Exception as e:
                print(f"[Orchestrator] Recovery failed: {e}. Fresh start.")
                self.current_state = self._fresh_state()
        else:
            self.current_state = self._fresh_state()

    def _fresh_state(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "timestamp": datetime.now().isoformat(),
            "cycle": 0,
            "level": 0,
            "energy": 0.0,
            "phi": 0.0,
            "phase": C.PHASES[0],
            "lines": {line: 0.0 for line in C.LINES},
            "fctn_layer": C.FCTN_LAYERS[0],
            "si_stage": C.SI_STAGES[0],
        }

    def _select_action(self) -> str:
        """Select action based on current state (Self-Drive logic)."""
        import random
        phi = self.current_state.get('phi', 0.5)
        energy = self.current_state.get('energy', 0.0)
        # Check plateau (simple: if energy hasn't changed much)
        last_energy = self.history[-1]['state'].get('energy', 0.0) if self.history else 0.0
        plateau = abs(energy - last_energy) < 1.0 and self.cycle_count > 1
        if phi < C.SELF_DRIVE_PHI_MIN:
            return "reflect"
        if plateau and self.cycle_count % C.SELF_DRIVE_PLATEAU_THRESHOLD == 0:
            return "transcend"
        return random.choice(["focus", "rest", "integrate", "self_modify"])

    def _evolve_state(self, action: str):
        """Evolve state based on action (self-contained fallback logic)."""
        import random
        energy = self.current_state.get('energy', 0.0)
        phi = self.current_state.get('phi', 0.2)
        multipliers = {
            "focus": (1.01, 0.005), "rest": (1.005, -0.003),
            "transcend": (1.05, 0.015), "reflect": (0.995, 0.02),
            "integrate": (1.015, 0.008), "self_modify": (1.025, 0.012),
        }
        em, pm = multipliers.get(action, (1.0, 0.0))
        # Add small noise
        energy = max(0, energy * em * (1 + random.uniform(-0.005, 0.005)))
        phi = max(0.05, min(1.0, phi + pm + random.uniform(-0.01, 0.01)))
        # Check level up
        level = self.current_state.get('level', 0)
        for lvl in range(level + 1, C.MAX_LEVEL + 1):
            if energy >= C.LEVEL_THRESHOLDS.get(lvl, float('inf')):
                level = lvl
            else:
                break
        # Determine phase
        if level >= 25:
            phase = "asymptotic_infinity"
        elif level >= 21:
            phase = "trans_singularity"
        else:
            phase_idx = min(len(C.PHASES) - 1, level // 3)
            phase = C.PHASES[phase_idx]
        self.current_state.update({
            "energy": energy, "phi": phi, "level": level,
            "phase": phase, "action": action,
        })

    def run_cycle(self) -> Dict[str, Any]:
        """Execute one full system cycle with full module coupling + event bus."""
        self.cycle_count += 1
        bus = _get_bus()
        Topics = _get_topics()

        # 1. Publish cycle start
        if bus and Topics:
            bus.publish_simple(Topics.CYCLE_START,
                              {"cycle": self.cycle_count, "timestamp": datetime.now().isoformat()},
                              source="orchestrator")

        # 2. Select action
        action = self._select_action()
        self.current_state["action"] = action
        if bus and Topics:
            bus.publish_simple(Topics.ACTION_SELECTED,
                              {"action": action, "cycle": self.cycle_count},
                              source="self_drive")

        # 3. Try to drive North Star (coupled module)
        try:
            if self._north_star is None:
                from core.v13_north_star_extended import NorthStarPathExtended
                self._north_star = NorthStarPathExtended()
            self._north_star.navigate_step(action)
            self.current_state["level"] = self._north_star.current_level
            self.current_state["energy"] = self._north_star.current_energy
            self.current_state["phi"] = getattr(self._north_star, 'phi_iit', 0.2)
            self.current_state["phase"] = self._north_star.current_phase
        except Exception as e:
            # Fallback: self-contained evolution
            self._evolve_state(action)
            if self.cycle_count == 1:
                self.alerts.append(f"NORTHSTAR_FALLBACK: {e}")

        # 4. Update metadata
        prev_level = self.current_state.get('level', 0)
        self.current_state["cycle"] = self.cycle_count
        self.current_state["timestamp"] = datetime.now().isoformat()

        # 5. Publish state change
        if bus and Topics:
            bus.publish_simple(Topics.STATE_CHANGE,
                              {"state": {k: v for k, v in self.current_state.items() if k != 'raw'}},
                              source="orchestrator")

        # 6. Check for level up
        if prev_level > 0 and self.current_state.get('level', 0) > prev_level:
            if bus and Topics:
                bus.publish_simple(Topics.LEVEL_UP,
                                  {"old": prev_level, "new": self.current_state['level']},
                                  source="north_star")

        # 7. Monitor check
        self.alerts = [a for a in self.alerts if not a.startswith("NORTHSTAR_FALLBACK")]
        if self.current_state.get('phi', 1.0) < C.SELF_DRIVE_PHI_MIN:
            self.alerts.append("WARNING: Phi below threshold")
            if bus and Topics:
                bus.publish_simple(Topics.ALERT,
                                  {"type": "phi_low", "value": self.current_state['phi']},
                                  source="monitor")
        if self.cycle_count % 50 == 0:
            try:
                import subprocess
                result = subprocess.run(
                    ['grep', '-r', '^\\s*sorry', C.LEAN_DIR],
                    capture_output=True, text=True
                )
                if result.stdout.strip():
                    sorry_count = len(result.stdout.strip().split('\n'))
                    if sorry_count > 0:
                        self.alerts.append(f"LEAN_SORRY: {sorry_count} remaining")
                        if bus and Topics:
                            bus.publish_simple(Topics.ALERT,
                                              {"type": "lean_sorry", "count": sorry_count},
                                              source="monitor")
            except Exception:
                pass

        # 8. Persist state
        if self.auto_persist and self.cycle_count % C.SELF_DRIVE_CHECKPOINT_INTERVAL == 0:
            self._persist()
            if bus and Topics:
                bus.publish_simple(Topics.PERSISTENCE_SAVE,
                                  {"cycle": self.cycle_count, "file": str(C.STATE_FILE)},
                                  source="persistence")

        # 9. Auto-git commit
        if self.auto_git and self.cycle_count % C.SELF_DRIVE_CHECKPOINT_INTERVAL == 0:
            self._git_commit()
            if bus and Topics:
                bus.publish_simple(Topics.GIT_COMMIT,
                                  {"cycle": self.cycle_count},
                                  source="auto_git")

        # 10. Publish cycle end
        if bus and Topics:
            bus.publish_simple(Topics.CYCLE_END,
                              {"cycle": self.cycle_count, "alerts": len(self.alerts)},
                              source="orchestrator")

        summary = {
            "cycle": self.cycle_count,
            "state": self.current_state.copy(),
            "alerts": self.alerts.copy(),
        }
        self.history.append(summary)
        return summary

    def _persist(self):
        try:
            _get_persistence().save_session(self.current_state, C.STATE_FILE)
        except Exception as e:
            self.alerts.append(f"PERSIST_ERROR: {e}")

    def _git_commit(self):
        try:
            git_hook = _get_git_hook()
            if git_hook.should_commit("orchestrator_state"):
                git_hook.commit_change(
                    C.STATE_FILE,
                    message=f"auto: c{self.cycle_count} L={self.current_state.get('level')} E={self.current_state.get('energy', 0):.0f}"
                )
        except Exception as e:
            self.alerts.append(f"GIT_ERROR: {e}")

    def run_autonomous(self, max_cycles: Optional[int] = None):
        """Run fully autonomous loop."""
        print(f"[Orchestrator] v{self.VERSION} autonomous start")
        print(f"[Orchestrator] persist={self.auto_persist} git={self.auto_git}")
        try:
            while max_cycles is None or self.cycle_count < max_cycles:
                summary = self.run_cycle()
                if self.cycle_count % 10 == 0:
                    print(f"[C{summary['cycle']:04d}] L={summary['state'].get('level', '?'):2d} "
                          f"E={summary['state'].get('energy', 0):12.2f} "
                          f"Phi={summary['state'].get('phi', 0):.3f} "
                          f"A={len(summary['alerts'])}")
                for alert in summary['alerts']:
                    if alert.startswith("CRITICAL"):
                        print(f"[CRITICAL] {alert}")
                        self._handle_critical(alert)
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("[Orchestrator] Interrupted")
        finally:
            self._persist()
            print(f"[Orchestrator] Saved. Total cycles: {self.cycle_count}")

    def _handle_critical(self, alert: str):
        if "LEAN_SORRY" in alert:
            print("[Orchestrator] Lean sorry! Trigger repair.")
        elif "TEST_FAIL" in alert:
            print("[Orchestrator] Test fail! Trigger diagnostics.")
        elif "PHI_COLLAPSE" in alert:
            print("[Orchestrator] Phi collapse! Trigger recovery.")

    def get_status(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "cycles": self.cycle_count,
            "state": self.current_state,
            "alerts": self.alerts,
            "history_size": len(self.history),
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="OMNI-HUB Orchestrator")
    parser.add_argument("--cycles", type=int, default=100, help="Max cycles")
    parser.add_argument("--no-persist", action="store_true", help="Disable persist")
    parser.add_argument("--git", action="store_true", help="Enable auto-git")
    if len(sys.argv) > 1 and not any(x in sys.argv[0] for x in ['ipykernel', 'ipython']):
        args = parser.parse_args()
    else:
        args = argparse.Namespace(cycles=100, no_persist=False, git=False)
    orch = OMNIHUBOrchestrator(
        auto_persist=not args.no_persist,
        auto_git=args.git
    )
    orch.run_autonomous(max_cycles=args.cycles)


if __name__ == "__main__":
    main()
