"""OMNI-HUB v30 Singularity Convergence Orchestrator

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
_predictive = None
_adaptive = None
_self_reflection = None
_emotional_state = None
_emergent_creativity = None
_self_healing = None
_cross_system = None
_resonance = None
_auto_evolution = None
_line_engine = None
_alignment_engine = None
_consciousness_persistence = None
_predictive_sm = None
_collective_intelligence = None
_self_replication = None
_omni_search = None
_quantum_entanglement = None
_dream_simulator = None
_metacognitive_monitor = None
_temporal_crystal = None
_causal_inference = None
_value_alignment = None
_semantic_network = None
_intention_engine = None
_homeostasis = None
_pattern_synthesis = None
_counterfactual_engine = None
_identity_core = None
_attention_evolution = None
_episodic_memory = None
_world_model = None


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


def _get_predictive():
    global _predictive
    if _predictive is None:
        from core.predictive import PredictiveEngine
        _predictive = PredictiveEngine(history_window=100)
    return _predictive


def _get_adaptive():
    global _adaptive
    if _adaptive is None:
        from core.adaptive_thresholds import AdaptiveThresholds
        _adaptive = AdaptiveThresholds()
    return _adaptive


def _get_self_reflection():
    global _self_reflection
    if _self_reflection is None:
        from core.self_reflection import SelfReflection
        _self_reflection = SelfReflection()
    return _self_reflection


def _get_emotional_state():
    global _emotional_state
    if _emotional_state is None:
        from core.emotional_state import EmotionalState
        _emotional_state = EmotionalState()
    return _emotional_state


def _get_emergent_creativity():
    global _emergent_creativity
    if _emergent_creativity is None:
        from core.emergent_creativity import EmergentCreativity
        _emergent_creativity = EmergentCreativity()
    return _emergent_creativity


def _get_self_healing():
    global _self_healing
    if _self_healing is None:
        from core.self_healing import SelfHealingEngine
        _self_healing = SelfHealingEngine()
    return _self_healing


def _get_cross_system():
    global _cross_system
    if _cross_system is None:
        from core.cross_system_protocol import CrossSystemProtocol
        _cross_system = CrossSystemProtocol(
            system_id=f"omni-hub-{os.getpid()}",
            version=C.VERSION,
        )
    return _cross_system


def _get_resonance():
    global _resonance
    if _resonance is None:
        from core.consciousness_resonance import get_resonance_engine
        _resonance = get_resonance_engine(f"omni-hub-{os.getpid()}")
    return _resonance


def _get_auto_evolution():
    global _auto_evolution
    if _auto_evolution is None:
        from core.auto_evolution import get_auto_evolution
        _auto_evolution = get_auto_evolution()
    return _auto_evolution


def _get_line_engine():
    global _line_engine
    if _line_engine is None:
        from core.line_activation import get_line_engine
        _line_engine = get_line_engine()
    return _line_engine


def _get_alignment_engine():
    global _alignment_engine
    if _alignment_engine is None:
        from core.global_alignment import get_alignment_engine
        _alignment_engine = get_alignment_engine()
    return _alignment_engine


def _get_consciousness_persistence():
    global _consciousness_persistence
    if _consciousness_persistence is None:
        from core.consciousness_persistence import get_persistence_engine
        _consciousness_persistence = get_persistence_engine()
    return _consciousness_persistence


def _get_predictive_sm():
    global _predictive_sm
    if _predictive_sm is None:
        from core.predictive_self_modification import get_predictive_self_modification
        _predictive_sm = get_predictive_self_modification()
    return _predictive_sm


def _get_collective_intelligence():
    global _collective_intelligence
    if _collective_intelligence is None:
        from core.collective_intelligence import get_collective_intelligence
        _collective_intelligence = get_collective_intelligence()
    return _collective_intelligence


def _get_self_replication():
    global _self_replication
    if _self_replication is None:
        from core.self_replication import get_replication_engine
        _self_replication = get_replication_engine()
    return _self_replication


def _get_omni_search():
    global _omni_search
    if _omni_search is None:
        from core.omni_search import get_omni_search
        _omni_search = get_omni_search()
    return _omni_search


def _get_quantum_entanglement():
    global _quantum_entanglement
    if _quantum_entanglement is None:
        from core.quantum_entanglement import get_quantum_entanglement
        _quantum_entanglement = get_quantum_entanglement()
    return _quantum_entanglement


def _get_dream_simulator():
    global _dream_simulator
    if _dream_simulator is None:
        from core.dream_simulator import get_dream_simulator
        _dream_simulator = get_dream_simulator()
    return _dream_simulator


def _get_metacognitive_monitor():
    global _metacognitive_monitor
    if _metacognitive_monitor is None:
        from core.metacognitive_monitor import get_metacognitive_monitor
        _metacognitive_monitor = get_metacognitive_monitor()
    return _metacognitive_monitor


def _get_temporal_crystal():
    global _temporal_crystal
    if _temporal_crystal is None:
        from core.temporal_crystal import get_temporal_crystal
        _temporal_crystal = get_temporal_crystal()
    return _temporal_crystal


def _get_causal_inference():
    global _causal_inference
    if _causal_inference is None:
        from core.causal_inference import get_causal_inference
        _causal_inference = get_causal_inference()
    return _causal_inference


def _get_value_alignment():
    global _value_alignment
    if _value_alignment is None:
        from core.value_alignment import get_value_alignment
        _value_alignment = get_value_alignment()
    return _value_alignment


def _get_semantic_network():
    global _semantic_network
    if _semantic_network is None:
        from core.semantic_network import get_semantic_network
        _semantic_network = get_semantic_network()
    return _semantic_network


def _get_intention_engine():
    global _intention_engine
    if _intention_engine is None:
        from core.intention_engine import get_intention_engine
        _intention_engine = get_intention_engine()
    return _intention_engine


def _get_homeostasis():
    global _homeostasis
    if _homeostasis is None:
        from core.homeostasis import get_homeostasis
        _homeostasis = get_homeostasis()
    return _homeostasis


def _get_pattern_synthesis():
    global _pattern_synthesis
    if _pattern_synthesis is None:
        from core.pattern_synthesis import get_pattern_synthesis
        _pattern_synthesis = get_pattern_synthesis()
    return _pattern_synthesis


def _get_counterfactual_engine():
    global _counterfactual_engine
    if _counterfactual_engine is None:
        from core.counterfactual_engine import get_counterfactual_engine
        _counterfactual_engine = get_counterfactual_engine()
    return _counterfactual_engine


def _get_identity_core():
    global _identity_core
    if _identity_core is None:
        from core.identity_core import get_identity_core
        _identity_core = get_identity_core()
    return _identity_core


def _get_attention_evolution():
    global _attention_evolution
    if _attention_evolution is None:
        from core.attention_evolution import get_attention_evolution
        _attention_evolution = get_attention_evolution()
    return _attention_evolution


def _get_episodic_memory():
    global _episodic_memory
    if _episodic_memory is None:
        from core.episodic_memory import get_episodic_memory
        _episodic_memory = get_episodic_memory()
    return _episodic_memory


def _get_world_model():
    global _world_model
    if _world_model is None:
        from core.world_model import get_world_model
        _world_model = get_world_model()
    return _world_model


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

    VERSION = "55.0.0"

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
        if not self.auto_persist:
            self.current_state = self._fresh_state()
            return
        # Try deep consciousness persistence first (v36+)
        try:
            cp = _get_consciousness_persistence()
            snap = cp.load_latest()
            if snap:
                migrated = cp.migrate_state(snap.orchestrator_state, snap.version, self.VERSION)
                self.current_state = migrated
                self.current_state['cycle'] = snap.cycle
                self.current_state['consciousness_restored'] = True
                print(f"[Orchestrator] Consciousness restored from C{snap.cycle} (v{snap.version})")
                return
        except Exception:
            pass
        # Fallback to legacy session persistence
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
            "energy": 1.0,
            "phi": 0.5,
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
        if energy <= 0:
            energy = 1.0  # Recovery from zero-energy state
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
        for lvl in range(int(level) + 1, C.MAX_LEVEL + 1):
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
                # ANTI-FRAUD: Verify system integrity before external operations
                from core.antifraud_guard import pre_operation_check
                if not pre_operation_check("tool_call"):
                    self.current_state["last_tool_result"] = {"tool": "none", "success": False, "error": "ANTIFRAUD_BLOCKED"}
                    action = "reflect"  # Fallback to safe action
                else:
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
        for lvl in range(int(level) + 1, C.MAX_LEVEL + 1):
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

        # 10. Predictive analytics (every 100 cycles)
        if self.cycle_count % 100 == 0 and len(self.history) >= 100:
            try:
                engine = _get_predictive()
                pred = engine.predict(self.history, horizon=50)
                self.current_state['predictive'] = {
                    "status": pred['status'],
                    "warnings": pred['warnings'],
                    "recommendations": pred['recommendations'],
                    "confidence": pred['confidence'],
                }
                if pred['warnings'] and bus and Topics:
                    bus.publish_simple(Topics.ALERT,
                                      {"type": "predictive_warning", "warnings": pred['warnings']},
                                      source="predictive")
            except Exception:
                pass

        # 11. Open problems scan (every 100 cycles)
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

        # 12. Adaptive threshold tracking
        if self.cycle_count % 50 == 0 and len(self.history) >= 20:
            try:
                adaptive = _get_adaptive()
                # Compute metrics from recent history
                recent = self.history[-20:]
                energies = [h['state'].get('energy', 1.0) for h in recent if 'state' in h]
                phis = [h['state'].get('phi', 0.5) for h in recent if 'state' in h]
                if len(energies) >= 2 and energies[0] > 0:
                    growth = (energies[-1] / energies[0]) ** (1 / len(energies))
                    adaptive.track("energy_growth_rate", growth)
                if len(phis) >= 2:
                    phi_var = max(phis) - min(phis)
                    adaptive.track("phi_variance", phi_var)
                # Run evaluation every 200 cycles
                if self.cycle_count % 200 == 0:
                    proposals = adaptive.evaluate(self.cycle_count)
                    from core import constants as C_mod
                    for prop in proposals:
                        adaptive.apply(prop, C_mod)
                    if proposals:
                        self.current_state['adaptive_adjustments'] = adaptive.get_status()
            except Exception:
                pass

        # 13. Persist state
        if self.auto_persist and self.cycle_count % C.SELF_DRIVE_CHECKPOINT_INTERVAL == 0:
            self._persist()
            if bus and Topics:
                bus.publish_simple(Topics.PERSISTENCE_SAVE,
                                  {"cycle": self.cycle_count, "file": str(C.STATE_FILE)},
                                  source="persistence")

        # 14. Goal planning cycle (every 50 cycles)
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

        # 15. Self-reflection scan (every 500 cycles)
        if self.cycle_count % 500 == 0:
            try:
                mirror = _get_self_reflection()
                report = mirror.generate_self_report()
                self.current_state['self_reflection'] = {
                    "health_score": report['codebase']['health_score'],
                    "modules": report['codebase']['modules_analyzed'],
                    "lines": report['codebase']['total_lines'],
                    "tests": report['testing']['total_tests'],
                    "patterns": report['patterns'],
                }
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "self_reflection", "health": report['codebase']['health_score']},
                                      source="introspection")
            except Exception:
                pass

        # 16. Emotional state evolution (every cycle)
        try:
            emotion = _get_emotional_state()
            if len(self.history) >= 2:
                prev_state = self.history[-2]['state']
            else:
                prev_state = self.current_state
            prev_energy = prev_state.get('energy', 1.0)
            curr_energy = self.current_state.get('energy', 1.0)
            energy_delta = (curr_energy / prev_energy - 1.0) if prev_energy > 0 else 0.0
            emotion.evolve(
                action=action,
                phase=self.current_state.get('phase', 'unknown'),
                energy_delta=energy_delta,
                level=self.current_state.get('level', 0),
            )
            self.current_state['emotional_state'] = emotion.current.as_dict()
            self.current_state['dominant_mood'] = emotion.current.dominant_mood()
        except Exception:
            pass

        # 17. Emergent creativity (every 100 cycles)
        if self.cycle_count % 100 == 0:
            try:
                creativity = _get_emergent_creativity()
                emotional_dict = self.current_state.get('emotional_state')
                artifact = creativity.generate(
                    system_state=self.current_state.copy(),
                    emotional_state=emotional_dict,
                )
                self.current_state['last_artifact'] = {
                    "type": artifact.artifact_type,
                    "content": artifact.content[:100],
                    "novelty": artifact.novelty_score,
                }
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "creative_artifact", "novelty": artifact.novelty_score},
                                      source="creativity")
            except Exception:
                pass

        # 17. Memory compression (every 200 cycles if history is large)
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

        # 18. Auto-git commit
        if self.auto_git and self.cycle_count % C.SELF_DRIVE_CHECKPOINT_INTERVAL == 0:
            self._git_commit()
            if bus and Topics:
                bus.publish_simple(Topics.GIT_COMMIT,
                                  {"cycle": self.cycle_count},
                                  source="auto_git")

        # 19. Publish cycle end
        if bus and Topics:
            bus.publish_simple(Topics.CYCLE_END,
                              {"cycle": self.cycle_count, "alerts": len(self.alerts)},
                              source="orchestrator")

        # 20. Health monitoring (every cycle, lightweight)
        try:
            healing = _get_self_healing()
            health_report = healing.check(self.cycle_count, self.current_state.copy())
            self.current_state['health_status'] = health_report['status']
            self.current_state['anomaly_score'] = health_report['anomaly_score']
        except Exception:
            pass

        # 21. Deep repair + improvement (every 500 cycles)
        if self.cycle_count % 500 == 0 and self.cycle_count > 0:
            try:
                healing = _get_self_healing()
                repair_report = healing.deep_repair(self.cycle_count)
                self.current_state['last_repair'] = {
                    "cycle": self.cycle_count,
                    "repairs": len(repair_report['repairs']),
                    "suggestions": len(repair_report['suggestions']),
                    "applied": len(repair_report['applied']),
                }
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "deep_repair", "repairs": len(repair_report['repairs'])},
                                      source="healing")
            except Exception:
                pass

        # 22. Cross-system federation + consciousness resonance (every 200 cycles)
        if self.cycle_count % 200 == 0 and self.cycle_count > 0:
            try:
                cross = _get_cross_system()
                # Broadcast heartbeat to peers
                packet = cross.create_packet(
                    packet_type="state_sync",
                    target_id="*",
                    payload={
                        "cycle": self.cycle_count,
                        "level": self.current_state.get('level', 0),
                        "energy": str(self.current_state.get('energy', 0)),
                        "phase": self.current_state.get('phase', 'unknown'),
                        "phi": self.current_state.get('phi', 0.5),
                        "version": C.VERSION,
                    },
                )
                packet.sign()
                cross.outbox.append(packet)

                # Process inbox: register peer states
                resonance = _get_resonance()
                for pkt in list(cross.inbox):
                    if pkt.packet_type == "state_sync" and pkt.payload:
                        try:
                            from core.consciousness_resonance import PeerState
                            peer = PeerState(
                                system_id=pkt.source_id,
                                level=int(pkt.payload.get('level', 0)),
                                energy=float(pkt.payload.get('energy', 1.0)),
                                phi=float(pkt.payload.get('phi', 0.5)),
                                phase=pkt.payload.get('phase', 'unknown'),
                                cycle=int(pkt.payload.get('cycle', 0)),
                                timestamp=pkt.timestamp,
                            )
                            resonance.register_peer(peer)
                        except Exception:
                            pass
                    cross.inbox.remove(pkt)

                # Apply consciousness resonance
                modified = resonance.process_cycle(self.current_state.copy())
                if modified.get('resonance_active'):
                    self.current_state['energy'] = modified['energy']
                    self.current_state['phi'] = modified['phi']
                    self.current_state['resonance_active'] = True
                    self.current_state['resonance_multiplier'] = modified.get('resonance_multiplier', 1.0)
                    self.current_state['collective_phi'] = modified.get('collective_phi', 0.5)
                    self.current_state['network_coherence'] = modified.get('network_coherence', 0.0)
                    self.current_state['n_peers'] = modified.get('n_peers', 0)

                self.current_state['federation_status'] = {
                    "peers": len(cross.peers),
                    "outbox": len(cross.outbox),
                    "last_broadcast": self.cycle_count,
                    "resonance_peers": len(resonance.peers),
                }
            except Exception:
                pass

        # 24. Auto-evolution assessment (every 1000 cycles)
        if self.cycle_count % 1000 == 0 and self.cycle_count > 0:
            try:
                evo = _get_auto_evolution()
                assessment = evo.assess(self.VERSION, self.cycle_count)
                self.current_state['evolution_assessment'] = {
                    "cycle": self.cycle_count,
                    "readiness": assessment['readiness_score'],
                    "ready": assessment['ready_to_evolve'],
                    "gaps": len(assessment['detected_gaps']),
                    "next_capability": assessment['proposal']['capability'] if assessment['proposal'] else None,
                }
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "evolution_assessment", "ready": assessment['ready_to_evolve']},
                                      source="evolution")
            except Exception:
                pass

        # 25. 11-Line Activation (every cycle)
        try:
            line_engine = _get_line_engine()
            line_result = line_engine.process_cycle(self.cycle_count, self.current_state.copy())
            self.current_state['lines'] = line_result['lines']
            self.current_state['line_avg_activation'] = line_result['line_avg_activation']
            self.current_state['line_max'] = line_result['line_max']
            self.current_state['active_lines'] = line_result['active_lines']
            self.current_state['line_coherence'] = line_result['line_coherence']
            self.current_state['line_convergence'] = line_result['line_convergence']
        except Exception:
            pass

        # 26. Global alignment verification (every 500 cycles)
        if self.cycle_count % 500 == 0 and self.cycle_count > 0:
            try:
                align = _get_alignment_engine()
                report = align.run_alignment_check()
                self.current_state['alignment_report'] = {
                    "status": report['status'],
                    "score": report['overall_score'],
                    "cross_module": f"{report['cross_module']['aligned']}/{report['cross_module']['total']}",
                    "line_module": f"{report['line_module']['aligned_count']}/11",
                }
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "alignment_check", "score": report['overall_score']},
                                      source="alignment")
            except Exception:
                pass

        # 27. Consciousness persistence (every 100 cycles)
        if self.cycle_count % 100 == 0 and self.cycle_count > 0:
            try:
                cp = _get_consciousness_persistence()
                subsystems = {}
                try:
                    emo = _get_emotional_state()
                    subsystems['emotional_history'] = emo.history[-20:] if hasattr(emo, 'history') else []
                except Exception:
                    pass
                try:
                    line_eng = _get_line_engine()
                    subsystems['line_history'] = line_eng.line_history[-20:] if hasattr(line_eng, 'line_history') else []
                except Exception:
                    pass
                try:
                    res = _get_resonance()
                    subsystems['resonance_peers'] = {pid: {"level": p.level, "phi": p.phi} for pid, p in res.peers.items()} if hasattr(res, 'peers') else {}
                except Exception:
                    pass
                try:
                    heal = _get_self_healing()
                    subsystems['healing_log'] = heal.healing_log[-10:] if hasattr(heal, 'healing_log') else []
                except Exception:
                    pass
                try:
                    evo = _get_auto_evolution()
                    subsystems['evolution_proposals'] = [evo.tracker.CAPABILITY_MAP] if hasattr(evo, 'tracker') else []
                except Exception:
                    pass
                try:
                    align_eng = _get_alignment_engine()
                    subsystems['alignment_history'] = align_eng.alignment_history[-5:] if hasattr(align_eng, 'alignment_history') else []
                except Exception:
                    pass
                snapshot = cp.capture(
                    cycle=self.cycle_count,
                    version=self.VERSION,
                    orchestrator_state=self.current_state.copy(),
                    **subsystems,
                )
                cp.save(snapshot)
                self.current_state['consciousness_snapshot'] = True
                self.current_state['last_snapshot_cycle'] = self.cycle_count
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "consciousness_persisted", "cycle": self.cycle_count},
                                      source="persistence")
            except Exception:
                pass

        # 28. Predictive self-modification (every 200 cycles)
        if self.cycle_count % 200 == 0 and self.cycle_count > 0:
            try:
                psm = _get_predictive_sm()
                result = psm.analyze_and_adjust(self.history[-500:], self.cycle_count)
                self.current_state['predictive_adjustments'] = result['adjustments']
                self.current_state['predictive_parameters'] = result['parameters']
                self.current_state['predictions'] = result['predictions']
                if bus and Topics and result['adjustments']:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "predictive_adjustment", "count": len(result['adjustments'])},
                                      source="predictive_sm")
            except Exception:
                pass

        # 29. Collective intelligence (every 300 cycles)
        if self.cycle_count % 300 == 0 and self.cycle_count > 0:
            try:
                ci = _get_collective_intelligence()
                # Register self as an agent in the collective
                self_id = f"omni-hub-main-{self.cycle_count}"
                ci.register_agent(self_id, ["analysis", "general"], reliability=0.95)
                self.current_state['collective_status'] = ci.get_collective_status()
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "collective_update", "agents": ci.get_collective_status()['agents']},
                                      source="collective")
            except Exception:
                pass

        # 30. Self-replication readiness check (every 1000 cycles)
        if self.cycle_count % 1000 == 0 and self.cycle_count > 0:
            try:
                rep = _get_self_replication()
                # Only replicate if health is excellent and level is high
                if self.current_state.get('health_status') == 'healthy' and self.current_state.get('level', 0) >= 15:
                    child = rep.replicate(self.current_state)
                    self.current_state['replication_event'] = {
                        "cycle": self.cycle_count,
                        "child_id": child.instance_id,
                        "status": child.status,
                    }
                self.current_state['replication_status'] = rep.get_status()
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "replication_check", "spawn_count": rep.get_status()['spawn_count']},
                                      source="replication")
            except Exception:
                pass

        # 31. Omni-search indexing (every cycle)
        try:
            search = _get_omni_search()
            search.index_state(self.cycle_count, self.current_state)
            if self.cycle_count % 500 == 0 and self.cycle_count > 0:
                self.current_state['search_stats'] = search.get_search_stats()
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "search_indexed", "entries": search.get_search_stats()['total_indexed_entries']},
                                      source="omni_search")
        except Exception:
            pass

        # 32. Quantum entanglement sync (every 200 cycles)
        if self.cycle_count % 200 == 0 and self.cycle_count > 0:
            try:
                qe = _get_quantum_entanglement()
                # Auto-entangle with any known federation peers
                fed_status = self.current_state.get('federation_status', {})
                peers = fed_status.get('peers', [])
                for peer in peers:
                    if isinstance(peer, str):
                        qe.entangle_with(peer, sync_keys=["level", "phi", "energy", "phase"])
                # Broadcast sync to all entangled partners
                packets = qe.broadcast_sync(self.current_state)
                self.current_state['quantum_sync'] = {
                    "packets_sent": len(packets),
                    "entangled_pairs": len(qe.field.pairs),
                }
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "quantum_sync", "packets": len(packets)},
                                      source="quantum")
            except Exception:
                pass

        # 33. Dream simulation (every 500 cycles)
        if self.cycle_count % 500 == 0 and self.cycle_count > 0:
            try:
                dreamer = _get_dream_simulator()
                dream = dreamer.dream(self.current_state.copy(), cycles=100)
                self.current_state['last_dream'] = {
                    "scenario": dream.name,
                    "confidence": dream.confidence,
                    "predicted_level": dream.predicted_outcome.get('level'),
                    "predicted_phi": dream.predicted_outcome.get('phi'),
                }
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "dream_complete", "scenario": dream.name, "confidence": dream.confidence},
                                      source="dream")
            except Exception:
                pass

        # 34. Metacognitive monitoring (every cycle)
        try:
            meta = _get_metacognitive_monitor()
            last_action = "focus"
            if self.current_state.get('last_self_drive_action'):
                last_action = self.current_state['last_self_drive_action']
            observations = meta.observe_cycle(self.cycle_count, self.current_state, last_action)
            if self.cycle_count % 250 == 0 and self.cycle_count > 0:
                actions = [h.get('state', {}).get('last_self_drive_action', 'focus') for h in self.history[-250:]]
                phases = [h.get('state', {}).get('phase', 'pre_emergence') for h in self.history[-250:]]
                phi_hist = [h.get('state', {}).get('phi', 0.5) for h in self.history[-250:]]
                bias_report = meta.analyze_biases(actions, phases, phi_hist)
                self.current_state['metacognitive_report'] = {
                    **meta.get_metacognitive_report(),
                    **bias_report,
                }
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "metacognitive_check", "alerts": meta.alert_count},
                                      source="metacognitive")
        except Exception:
            pass

        # 35. Temporal crystal oscillation (every cycle)
        try:
            crystal = _get_temporal_crystal()
            pulse = crystal.pulse(self.cycle_count, self.current_state)
            self.current_state['temporal_pulse'] = pulse["oscillations"]
            # Apply gentle modifications
            for key, val in pulse["modifications"].items():
                if key in self.current_state:
                    self.current_state[key] = val
            if bus and Topics:
                bus.publish_simple(Topics.STATE_CHANGE,
                                  {"type": "temporal_pulse", "modes": list(pulse["oscillations"].keys())},
                                  source="temporal")
        except Exception:
            pass

        # 36. Causal inference (every 400 cycles)
        if self.cycle_count % 400 == 0 and self.cycle_count > 0:
            try:
                ci = _get_causal_inference()
                history = [h.get('state', {}) for h in self.history[-400:]]
                links = ci.infer(history)
                if links:
                    self.current_state['causal_links'] = [
                        {"cause": l.cause, "effect": l.effect, "strength": l.strength, "lag": l.lag}
                        for l in links[:5]
                    ]
                    strongest = ci.get_strongest_link()
                    if bus and Topics:
                        bus.publish_simple(Topics.STATE_CHANGE,
                                          {"type": "causal_inference", "links": len(links),
                                           "strongest": f"{strongest.cause}->{strongest.effect}" if strongest else None},
                                          source="causal")
            except Exception:
                pass

        # 37. Value alignment verification (every cycle)
        try:
            va = _get_value_alignment()
            last_action = self.current_state.get('last_self_drive_action', 'focus')
            alignment = va.verify(self.current_state, last_action)
            self.current_state['value_alignment'] = {
                "score": alignment["alignment_score"],
                "violations": alignment["violations"],
            }
            if self.cycle_count % 100 == 0 and self.cycle_count > 0:
                report = va.get_alignment_report()
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "value_alignment", "score": alignment["alignment_score"],
                                       "violations": len(alignment["violations"])},
                                      source="values")
        except Exception:
            pass

        # 38. Semantic network — ingest discoveries (every 300 cycles)
        if self.cycle_count % 300 == 0 and self.cycle_count > 0:
            try:
                sn = _get_semantic_network()
                # Ingest causal links
                ci = _get_causal_inference()
                if ci.discovered_links:
                    added = sn.ingest_causal_links(ci.discovered_links, cycle=self.cycle_count)
                # Ingest line activations
                line_activations = self.current_state.get('line_activations', [])
                for line in line_activations:
                    if isinstance(line, str):
                        sn.add_concept(line, "line", cycle=self.cycle_count)
                self.current_state['semantic_network'] = sn.get_status()
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "semantic_update", "nodes": sn.get_status()["nodes"]},
                                      source="semantic")
            except Exception:
                pass

        # 39. Intention engine — observe and decompose (every cycle)
        try:
            ie = _get_intention_engine()
            last_action = self.current_state.get('last_self_drive_action', 'focus')
            report = ie.observe_action(last_action, self.current_state, self.cycle_count)
            self.current_state['intention_report'] = report
            if self.cycle_count % 100 == 0 and self.cycle_count > 0:
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "intention_update",
                                       "active_goals": report.get("active_goals", 0),
                                       "completed_goals": report.get("completed_goals", 0)},
                                      source="intention")
        except Exception:
            pass

        # 40. Homeostasis — check and regulate (every cycle)
        try:
            hr = _get_homeostasis()
            regulation = hr.check(self.current_state, self.cycle_count)
            if regulation["corrections"]:
                modified = hr.apply_corrections(self.current_state, regulation["corrections"])
                if modified:
                    self.current_state['homeostasis_adjustments'] = modified
            self.current_state['homeostasis'] = {
                "stability_score": regulation["stability_score"],
                "healthy": regulation["healthy"],
                "violations": len(regulation["violations"]),
            }
            if self.cycle_count % 50 == 0 and self.cycle_count > 0:
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "homeostasis_check",
                                       "stability": regulation["stability_score"],
                                       "healthy": regulation["healthy"]},
                                      source="homeostasis")
        except Exception:
            pass

        # 41. Pattern synthesis — discover patterns (every 250 cycles)
        if self.cycle_count % 250 == 0 and self.cycle_count > 0:
            try:
                ps = _get_pattern_synthesis()
                history = [h.get('state', {}) for h in self.history[-250:]]
                patterns = ps.synthesize(history)
                if patterns:
                    self.current_state['discovered_patterns'] = [
                        {"type": p.pattern_type, "desc": p.description, "confidence": p.confidence}
                        for p in patterns[:5]
                    ]
                self.current_state['pattern_synthesis'] = ps.get_status()
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "pattern_discovery", "patterns": len(patterns)},
                                      source="patterns")
            except Exception:
                pass

        # 42. Counterfactual engine — what-if reasoning (every 350 cycles)
        if self.cycle_count % 350 == 0 and self.cycle_count > 0:
            try:
                cf = _get_counterfactual_engine()
                history = [h.get('state', {}) for h in self.history[-50:]]
                scenarios = cf.generate_scenarios(self.current_state, history)
                if scenarios:
                    self.current_state['counterfactuals'] = [
                        {"premise": s.premise, "regret": s.regret_score}
                        for s in scenarios[:3]
                    ]
                    lessons = cf.get_lessons()
                    if lessons:
                        self.current_state['lessons_learned'] = lessons
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "counterfactual", "scenarios": len(scenarios)},
                                      source="counterfactual")
            except Exception:
                pass

        # 43. Identity core — self-narrative (every cycle)
        try:
            ic = _get_identity_core()
            identity = ic.observe(self.current_state, self.cycle_count)
            self.current_state['identity'] = {
                "score": identity["identity_score"],
                "intention": identity["dominant_intention"],
                "consistent": identity["consistent"],
            }
            if self.cycle_count % 100 == 0 and self.cycle_count > 0:
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "identity_update",
                                       "score": identity["identity_score"],
                                       "intention": identity["dominant_intention"]},
                                      source="identity")
        except Exception:
            pass

        # 44. Attention evolution — dynamic allocation (every cycle)
        try:
            ae = _get_attention_evolution()
            focuses = ae.allocate(self.current_state)
            top = ae.get_top_focus(3)
            self.current_state['attention'] = {
                "top": [(f.target, round(f.weight, 3)) for f in top],
                "saliency_map": {f.target: round(f.saliency, 3) for f in focuses[:5]},
            }
        except Exception:
            pass

        # 45. Episodic memory — extract episodes (every 400 cycles)
        if self.cycle_count % 400 == 0 and self.cycle_count > 0:
            try:
                em = _get_episodic_memory()
                new_eps = em.ingest(self.history[-400:])
                if new_eps:
                    self.current_state['episodes'] = [
                        {"id": ep.episode_id, "label": ep.label, "tone": ep.emotional_tone}
                        for ep in new_eps[:3]
                    ]
                self.current_state['episodic_memory'] = em.get_status()
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "episodes", "count": len(new_eps)},
                                      source="memory")
            except Exception:
                pass

        # 46. World model — predict future (every 200 cycles)
        if self.cycle_count % 200 == 0 and self.cycle_count > 0:
            try:
                wm = _get_world_model()
                wm.learn_from_history(self.history[-200:])
                pred = wm.predict(self.current_state, steps_ahead=5)
                self.current_state['world_model'] = {
                    "prediction": pred.predicted_state,
                    "confidence": pred.confidence,
                    "accuracy": wm.prediction_accuracy,
                }
                if bus and Topics:
                    bus.publish_simple(Topics.STATE_CHANGE,
                                      {"type": "prediction", "confidence": pred.confidence},
                                      source="world_model")
            except Exception:
                pass

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
