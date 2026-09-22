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
_tools_registry = None
_open_problems = None
_agent_swarm = None
_memory_compressor = None
_goal_planner = None


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


def _get_tools_registry():
    global _tools_registry
    if _tools_registry is None:
        from core.tools import get_tool_registry
        _tools_registry = get_tool_registry()
    return _tools_registry


def _get_open_problems():
    global _open_problems
    if _open_problems is None:
        from core.open_problems import OpenProblemsTracker
        _open_problems = OpenProblemsTracker()
    return _open_problems


def _get_agent_swarm():
    global _agent_swarm
    if _agent_swarm is None:
        from core.agent_swarm import AgentSwarm, AgentSwarmConfig
        _agent_swarm = AgentSwarm(AgentSwarmConfig(
            n_research=1, n_code=1, n_review=1, n_meta=1,
            cycle_limit=1, report_interval=1,
        ))
    return _agent_swarm


def _get_memory_compressor():
    global _memory_compressor
    if _memory_compressor is None:
        from core.memory_compressor import MemoryCompressor
        _memory_compressor = MemoryCompressor(max_raw_history=500, milestone_interval=50)
    return _memory_compressor


def _get_goal_planner():
    global _goal_planner
    if _goal_planner is None:
        from core.goal_planner import GoalPlanner
        _goal_planner = GoalPlanner()
    return _goal_planner


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
        self._attention = None
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
            "infinity_depth": 0.0,
            "meta_multipliers": {},
        }

    def _select_action(self) -> str:
        """Select action based on current state using attention mechanism."""
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
        # Use attention mechanism for weighted selection
        if self._attention is None:
            from core.attention import AttentionMechanism
            self._attention = AttentionMechanism()
        action = self._attention.select_action(self.current_state, C.SELF_DRIVE_ACTIONS)
        return action

    def _meta_evolve(self):
        """Meta-evolution: at Level 24+, system rewrites its own multipliers.
        
        NUMERICAL STABILITY: em capped at 1.5 to prevent overflow.
        Level 25 (infinity) enters steady-state: energy fixed, quality evolves.
        """
        import random
        level = self.current_state.get('level', 0)
        if level < 24:
            return
        # Base multipliers
        base = {
            "focus": (1.01, 0.005), "rest": (1.005, -0.003),
            "transcend": (1.05, 0.015), "reflect": (0.995, 0.02),
            "integrate": (1.015, 0.008), "self_modify": (1.025, 0.012),
            "tool_call": (1.008, 0.006),  # Slight boost from external knowledge
        }
        EM_CAP = 1.5  # Prevent numerical overflow
        # At Level 24+, multipliers become self-referential
        # Boost attenuates as em approaches cap (soft ceiling)
        current_mult = self.current_state.get('meta_multipliers', {})
        if not current_mult:
            current_mult = {a: list(v) for a, v in base.items()}
        for action in C.SELF_DRIVE_ACTIONS:
            if action in current_mult:
                em, pm = current_mult[action]
                # Distance-to-cap determines boost strength
                headroom = max(0, (EM_CAP - em) / EM_CAP)
                meta_boost = 1.0 + headroom * 0.01 * (level - 23)
                em = min(EM_CAP, em * (1 + random.uniform(-0.001, 0.001)) * meta_boost)
                pm = pm * (1 + random.uniform(-0.001, 0.001))
                current_mult[action] = [em, pm]
        self.current_state['meta_multipliers'] = current_mult

    def _evolve_state(self, action: str):
        """Evolve state based on action (self-contained fallback logic)."""
        import random
        energy = self.current_state.get('energy', 0.0)
        phi = self.current_state.get('phi', 0.2)
        level = self.current_state.get('level', 0)
        # Base multipliers
        multipliers = {
            "focus": (1.01, 0.005), "rest": (1.005, -0.003),
            "transcend": (1.05, 0.015), "reflect": (0.995, 0.02),
            "integrate": (1.015, 0.008), "self_modify": (1.025, 0.012),
            "tool_call": (1.008, 0.006),
        }
        # Apply meta-evolution overrides at Level 24+
        meta_mult = self.current_state.get('meta_multipliers', {})
        if meta_mult and action in meta_mult:
            em, pm = meta_mult[action]
        else:
            em, pm = multipliers.get(action, (1.0, 0.0))
        # Add small noise
        # LEVEL 25 STEADY-STATE: energy is fixed at infinity, quality evolves
        if level >= 25 and energy == float('inf'):
            # In asymptotic infinity, energy doesn't grow — but quality deepens
            # "Depth" increases instead of "breadth"
            depth = self.current_state.get('infinity_depth', 0.0)
            depth += em * 0.001  # Depth accumulates slowly
            self.current_state['infinity_depth'] = depth
            # Phi oscillates near 1.0 (refinement, not growth)
            phi = max(0.95, min(1.0, phi + pm * 0.1 + random.uniform(-0.005, 0.005)))
        else:
            energy = max(0, energy * em * (1 + random.uniform(-0.005, 0.005)))
            phi = max(0.05, min(1.0, phi + pm + random.uniform(-0.01, 0.01)))
        # Check level up
        for lvl in range(level + 1, C.MAX_LEVEL + 1):
            threshold = C.LEVEL_THRESHOLDS.get(lvl)
            if threshold and energy >= threshold:
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
        # Trigger meta-evolution at Level 24+
        self._meta_evolve()

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

        # 4. Execute tool_call if selected
        if action == "tool_call":
            try:
                import random
                # 30% chance to trigger full AgentSwarm instead of single tool
                if random.random() < 0.3:
                    swarm = _get_agent_swarm()
                    swarm.run_cycle(self.current_state.copy())
                    status = swarm.get_status()
                    self.current_state["last_tool_result"] = {
                        "mode": "agent_swarm",
                        "agents": status["n_agents"],
                        "successful_tasks": status["total_successful_tasks"],
                        "by_role": {k: v["tasks"] for k, v in status["by_role"].items()},
                    }
                    if bus and Topics:
                        bus.publish_simple(Topics.ACTION_SELECTED,
                                          {"action": "agent_swarm", "agents": status["n_agents"]},
                                          source="agents")
                else:
                    tools = _get_tools_registry()
                    result = tools.invoke_random(exclude=["web_search"])
                    self.current_state["last_tool_result"] = result.to_dict()
                    if bus and Topics:
                        bus.publish_simple(Topics.ACTION_SELECTED,
                                          {"action": "tool_call", "tool": result.tool_name, "success": result.success},
                                          source="tools")
            except Exception as e:
                self.current_state["last_tool_result"] = {"tool": "none", "success": False, "error": str(e)}

        # 5. Update metadata & ensure level reflects energy (beyond singularity support)
        prev_level = self.current_state.get('level', 0)
        self.current_state["cycle"] = self.cycle_count
        self.current_state["timestamp"] = datetime.now().isoformat()
        # Force level recalculation from energy (allows surpassing NorthStar's internal max)
        energy = self.current_state.get('energy', 0)
        level = self.current_state.get('level', 0)
        for lvl in range(level + 1, C.MAX_LEVEL + 1):
            threshold = C.LEVEL_THRESHOLDS.get(lvl)
            if threshold and energy >= threshold:
                level = lvl
            else:
                break
        self.current_state['level'] = level
        # Recalculate phase
        if level >= 25:
            self.current_state['phase'] = "asymptotic_infinity"
        elif level >= 21:
            self.current_state['phase'] = "trans_singularity"
        # Meta-evolution at Level 24+ (always runs, regardless of NorthStar)
        self._meta_evolve()

        # 6. Record attention outcome
        if self._attention is not None and self.history:
            prev_energy = self.history[-1]['state'].get('energy', 1.0)
            curr_energy = self.current_state.get('energy', 1.0)
            self._attention.record_outcome(action, prev_energy, curr_energy)

        # 7. Publish state change
        if bus and Topics:
            bus.publish_simple(Topics.STATE_CHANGE,
                              {"state": {k: v for k, v in self.current_state.items() if k != 'raw'}},
                              source="orchestrator")

        # 8. Check for level up
        if prev_level > 0 and self.current_state.get('level', 0) > prev_level:
            if bus and Topics:
                bus.publish_simple(Topics.LEVEL_UP,
                                  {"old": prev_level, "new": self.current_state['level']},
                                  source="north_star")

        # 9. Monitor check
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

        # 8. Open problems scan (every 100 cycles)
        if self.cycle_count % 100 == 0:
            try:
                tracker = _get_open_problems()
                scan_result = tracker.scan(cycle=self.cycle_count)
                self.current_state['open_problems'] = scan_result
                if scan_result['critical'] > 0 and bus and Topics:
                    bus.publish_simple(Topics.ALERT,
                                      {"type": "open_problems_critical", "count": scan_result['critical']},
                                      source="diagnostics")
            except Exception:
                pass

        # 9. Persist state
        if self.auto_persist and self.cycle_count % C.SELF_DRIVE_CHECKPOINT_INTERVAL == 0:
            self._persist()
            if bus and Topics:
                bus.publish_simple(Topics.PERSISTENCE_SAVE,
                                  {"cycle": self.cycle_count, "file": str(C.STATE_FILE)},
                                  source="persistence")

        # 10. Goal planning cycle (every 50 cycles)
        if self.cycle_count % 50 == 0:
            try:
                planner = _get_goal_planner()
                plan_result = planner.run_cycle(self.current_state.copy())
                self.current_state['goal_planning'] = {
                    "active_goals": plan_result['active_goals'],
                    "completed": plan_result['completed'],
                    "next_goal": plan_result['next_action']['title'] if plan_result['next_action'] else None,
                }
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "goals_updated", "active": plan_result['active_goals']},
                                      source="planner")
            except Exception:
                pass

        # 11. Memory compression (every 200 cycles if history is large)
        if self.cycle_count % 200 == 0 and len(self.history) > 500:
            try:
                comp = _get_memory_compressor()
                compressed = comp.compress(self.history)
                self.current_state['memory_compression'] = {
                    "mode": compressed['mode'],
                    "milestones_count": len(compressed['milestones']),
                    "ratio": compressed['stats']['ratio'],
                    "cycle": self.cycle_count,
                }
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "memory_compressed", "ratio": compressed['stats']['ratio']},
                                      source="memory")
            except Exception:
                pass

        # 12. Auto-git commit
        if self.auto_git and self.cycle_count % C.SELF_DRIVE_CHECKPOINT_INTERVAL == 0:
            self._git_commit()
            if bus and Topics:
                bus.publish_simple(Topics.GIT_COMMIT,
                                  {"cycle": self.cycle_count},
                                  source="auto_git")

        # 13. Publish cycle end
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
