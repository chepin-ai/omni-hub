"""
OMNI-HUB Self-Healing Engine v31
Autonomous repair, recovery, and continuous improvement.

Philosophy: 候即违规 — A system that cannot heal itself is already dying.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import os
import shutil
import py_compile
import importlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import deque


@dataclass
class HealthSnapshot:
    """A point-in-time system health reading."""
    cycle: int
    level: int
    energy: float
    phi: float
    phase: str
    action: str
    mood: Optional[str] = None
    anomaly_score: float = 0.0


@dataclass
class RepairAction:
    """A repair action with its result."""
    action_type: str
    target: str
    success: bool
    detail: str = ""


@dataclass
class ImprovementSuggestion:
    """A parameter improvement suggestion."""
    parameter: str
    current_value: Any
    suggested_value: Any
    reason: str
    confidence: float
    applied: bool = False


class HealthMonitor:
    """Tracks system health over a sliding window."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.history: deque[HealthSnapshot] = deque(maxlen=window_size)
        self.baseline: Dict[str, float] = {}

    def record(self, cycle: int, state: Dict[str, Any]) -> HealthSnapshot:
        """Record a new health snapshot."""
        snapshot = HealthSnapshot(
            cycle=cycle,
            level=state.get('level', 0),
            energy=state.get('energy', 1.0),
            phi=state.get('phi', 0.5),
            phase=state.get('phase', 'unknown'),
            action=state.get('action', 'focus'),
            mood=state.get('dominant_mood'),
        )
        self.history.append(snapshot)
        return snapshot

    def compute_baseline(self) -> Dict[str, float]:
        """Compute baseline statistics from history."""
        if len(self.history) < 10:
            return {}
        energies = [h.energy for h in self.history if h.energy != float('inf')]
        phis = [h.phi for h in self.history]
        self.baseline = {
            'avg_energy': sum(energies) / len(energies) if energies else 1.0,
            'avg_phi': sum(phis) / len(phis) if phis else 0.5,
            'energy_trend': self._compute_trend(energies) if len(energies) >= 2 else 0.0,
        }
        return self.baseline

    def _compute_trend(self, values: List[float]) -> float:
        """Simple linear trend: positive = growing, negative = shrinking."""
        if len(values) < 2:
            return 0.0
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        return numerator / denominator if denominator != 0 else 0.0

    def get_anomaly_score(self, snapshot: HealthSnapshot) -> float:
        """Compute anomaly score for a snapshot (0.0 = normal, 1.0 = critical)."""
        if not self.baseline:
            self.compute_baseline()
        if not self.baseline:
            return 0.0

        score = 0.0
        # Energy stagnation: same energy for many cycles
        recent_energies = [h.energy for h in list(self.history)[-20:]]
        if len(recent_energies) >= 10 and len(set(recent_energies)) == 1:
            score += 0.3  # Completely stagnant

        # Phi collapse
        if snapshot.phi < 0.1:
            score += 0.3

        # Level stagnation
        recent_levels = [h.level for h in list(self.history)[-50:]]
        if len(recent_levels) >= 50 and len(set(recent_levels)) == 1:
            score += 0.2

        # Negative mood persistence
        recent_moods = [h.mood for h in list(self.history)[-20:] if h.mood]
        if recent_moods and all(m in ('frustration', 'anxiety') for m in recent_moods):
            score += 0.2

        return min(score, 1.0)


class RepairEngine:
    """Executes repair actions based on detected issues."""

    BASE = Path('/mnt/agents/output/OMNI-HUB')

    REPAIRS = [
        'clear_stale_state',
        'clear_pycache',
        'recompile_modules',
        'reset_emotional_state',
        'refresh_imports',
    ]

    def clear_stale_state(self) -> RepairAction:
        """Remove stale session state file."""
        target = self.BASE / 'hub' / 'session_state.json'
        try:
            if target.exists():
                target.unlink()
                return RepairAction('clear_stale_state', str(target), True, 'Removed stale session_state.json')
            return RepairAction('clear_stale_state', str(target), True, 'No stale state found')
        except Exception as e:
            return RepairAction('clear_stale_state', str(target), False, str(e))

    def clear_pycache(self) -> RepairAction:
        """Remove __pycache__ directories to prevent stale imports."""
        removed = 0
        errors = []
        try:
            for pycache in self.BASE.rglob('__pycache__'):
                if pycache.is_dir():
                    try:
                        shutil.rmtree(pycache, ignore_errors=True)
                        removed += 1
                    except Exception as e:
                        errors.append(str(e))
            detail = f'Removed {removed} __pycache__ dirs'
            if errors:
                detail += f' ({len(errors)} errors ignored)'
            return RepairAction('clear_pycache', 'all', True, detail)
        except Exception as e:
            return RepairAction('clear_pycache', 'all', False, str(e))

    # Same as antifraud_guard — modules known to be legacy/debt
    KNOWN_DEBT_MODULES = {
        'beat_continuum', 'bidirectional_drive', 'consciousness_state_machine',
        'debt_fuel_converter', 'discussion_board', 'emotion_persona_engine',
        'external_knowledge_weaver', 'full_pipeline_si', 'full_potential_explorer',
        'harmonic_tick_engine', 'hyper_field_mip_core', 'hyper_mip_core',
        'insight_detector', 'intention_generator', 'knowledge_pedestal_isomorphism',
        'knowledge_self_computation', 'linguistic_field', 'meta_structure',
        'octave_scan', 'otp_sync', 'recursive_closed_loop',
        'self_referential_engine', 'si_auto_protocol', 'task_dispatcher',
        'counterpoint_engine', 'creativity_engine', 'debt_cleanup',
        'field_entropy', 'field_transient_dynamics', 'finding_recursion',
        'formal_life_engine', 'goal_autopoiesis', 'historical_knowledge_weaver',
        'hub_wheel_spine', 'jing_wei_xin', 'meridian_zhou_tian_engine',
        'musical_mathematics', 'polaris_plan', 'quantum_consciousness_unifier',
        'quantum_field', 'quantum_yoneda_engine', 'ring_topology_engine',
        'run_exploration', 'self_drive_engine', 'self_evolving_architecture',
        'si_chain_reactor', 'si_connector_engine', 'si_topology',
        'strange_loop_detector', 'tensor_field', 'voice_melody',
        'zhou_tian_engine', 'cfts_phi_pi_e_alpha_integration',
        'experiment_runner', 'inbox_outbox', 'external_knowledge_fusion',
        'emergence_engine', 'deep_correlation_engine', 'cantus_firmus',
        'complexity_elevation_engine', 'consciousness_harmony',
        'collaborative_loop', 'closed_loop_mechanism',
    }

    def _is_active_module(self, name: str) -> bool:
        base = name.replace('.py', '')
        if base.startswith('v') and base[1:2].isdigit():
            return False
        if base in self.KNOWN_DEBT_MODULES:
            return False
        if base == '__init__':
            return False
        return True

    def recompile_modules(self) -> RepairAction:
        """Verify all active modules compile cleanly."""
        active_files = []
        for f in sorted((self.BASE / 'core').glob('*.py')):
            if self._is_active_module(f.name):
                active_files.append(f)

        failed = []
        for mod in active_files:
            try:
                py_compile.compile(str(mod), doraise=True)
            except py_compile.PyCompileError as e:
                failed.append(f'{mod.name}: {e}')

        if failed:
            return RepairAction('recompile_modules', f'{len(active_files)} files', False, '; '.join(failed[:3]))
        return RepairAction('recompile_modules', f'{len(active_files)} files', True, 'All active modules compile cleanly')

    def reset_emotional_state(self) -> RepairAction:
        """Reset emotional state if it exists."""
        try:
            # Clear the cached emotional state
            import core.orchestrator as orch_mod
            if hasattr(orch_mod, '_emotional_state'):
                orch_mod._emotional_state = None
            return RepairAction('reset_emotional_state', 'core.orchestrator', True, 'Emotional state cache cleared')
        except Exception as e:
            return RepairAction('reset_emotional_state', 'core.orchestrator', False, str(e))

    def refresh_imports(self) -> RepairAction:
        """Clear sys.modules for OMNI-HUB packages to force fresh imports."""
        try:
            removed = []
            for name in list(sys.modules.keys()):
                if 'OMNI-HUB' in name or name.startswith('core.'):
                    del sys.modules[name]
                    removed.append(name)
            return RepairAction('refresh_imports', 'sys.modules', True, f'Cleared {len(removed)} cached modules')
        except Exception as e:
            return RepairAction('refresh_imports', 'sys.modules', False, str(e))

    def run_all(self) -> List[RepairAction]:
        """Run all repair actions."""
        results = []
        for repair_name in self.REPAIRS:
            method = getattr(self, repair_name, None)
            if method:
                results.append(method())
        return results


class ImprovementEngine:
    """Suggests and applies parameter improvements."""

    def __init__(self):
        self.suggestions: List[ImprovementSuggestion] = []

    def analyze(self, history: List[HealthSnapshot]) -> List[ImprovementSuggestion]:
        """Analyze history and generate improvement suggestions."""
        self.suggestions = []
        if len(history) < 50:
            return self.suggestions

        recent = list(history)[-50:]

        # Check 1: Action distribution balance
        actions = [h.action for h in recent]
        action_counts = {}
        for a in actions:
            action_counts[a] = action_counts.get(a, 0) + 1
        total = len(actions)
        for action, count in action_counts.items():
            ratio = count / total
            if ratio > 0.5:
                self.suggestions.append(ImprovementSuggestion(
                    parameter=f'action_balance.{action}',
                    current_value=ratio,
                    suggested_value=0.3,
                    reason=f'{action} dominates {ratio:.0%} of cycles; diversity improves resilience',
                    confidence=min(ratio, 0.9),
                ))

        # Check 2: Level progression rate
        levels = [h.level for h in recent]
        if levels[-1] == levels[0] and levels[-1] < 20:
            self.suggestions.append(ImprovementSuggestion(
                parameter='level_thresholds.base',
                current_value='default',
                suggested_value='lower_by_10pct',
                reason=f'Level stagnant at {levels[-1]} for 50 cycles; lowering thresholds accelerates growth',
                confidence=0.7,
            ))

        # Check 3: Phi optimization
        phis = [h.phi for h in recent]
        avg_phi = sum(phis) / len(phis)
        if avg_phi < 0.5:
            self.suggestions.append(ImprovementSuggestion(
                parameter='phi.growth_rate',
                current_value='default',
                suggested_value='increase',
                reason=f'Average phi {avg_phi:.2f} is low; increasing phi growth improves coherence',
                confidence=0.6,
            ))

        return self.suggestions

    def apply_suggestion(self, suggestion: ImprovementSuggestion) -> bool:
        """Apply a suggestion (placeholder for actual parameter modification)."""
        # In a real system, this would modify constants.py or config
        suggestion.applied = True
        return True


class SelfHealingEngine:
    """
    Unified self-healing controller.

    Operates at three frequencies:
    - Every cycle: lightweight health monitoring
    - Every 100 cycles: anomaly detection
    - Every 500 cycles: deep repair + improvement analysis
    """

    def __init__(self):
        self.monitor = HealthMonitor(window_size=100)
        self.repair = RepairEngine()
        self.improve = ImprovementEngine()
        self.last_repair_cycle: int = 0
        self.last_improvement_cycle: int = 0
        self.repair_history: List[RepairAction] = []
        self.health_trend: str = "stable"

    def check(self, cycle: int, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run health check. Returns diagnostic report.
        Called every cycle (lightweight).
        """
        snapshot = self.monitor.record(cycle, state)
        anomaly = self.monitor.get_anomaly_score(snapshot)
        snapshot.anomaly_score = anomaly

        # Update health trend
        if anomaly > 0.5:
            self.health_trend = "degraded"
        elif anomaly > 0.2:
            self.health_trend = "warning"
        else:
            self.health_trend = "healthy"

        return {
            "status": self.health_trend,
            "anomaly_score": anomaly,
            "cycle": cycle,
            "baseline": self.monitor.baseline,
        }

    def deep_repair(self, cycle: int) -> Dict[str, Any]:
        """
        Run deep repair and improvement analysis.
        Called every 500 cycles.
        """
        self.last_repair_cycle = cycle

        # Run all repairs
        repairs = self.repair.run_all()
        self.repair_history.extend(repairs)

        # Generate improvement suggestions
        suggestions = self.improve.analyze(list(self.monitor.history))

        # Apply high-confidence suggestions
        applied = []
        for sug in suggestions:
            if sug.confidence > 0.7 and not sug.applied:
                if self.improve.apply_suggestion(sug):
                    applied.append(sug)

        return {
            "status": "repaired",
            "cycle": cycle,
            "repairs": [{"type": r.action_type, "target": r.target, "ok": r.success, "detail": r.detail} for r in repairs],
            "suggestions": [{"param": s.parameter, "from": s.current_value, "to": s.suggested_value, "confidence": s.confidence} for s in suggestions],
            "applied": [{"param": a.parameter, "new_value": a.suggested_value} for a in applied],
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current healing engine status."""
        return {
            "health_trend": self.health_trend,
            "history_size": len(self.monitor.history),
            "last_repair_cycle": self.last_repair_cycle,
            "last_improvement_cycle": self.last_improvement_cycle,
            "total_repairs": len(self.repair_history),
            "baseline": self.monitor.baseline,
        }


# Global instance
_healing_engine = None

def get_healing_engine() -> SelfHealingEngine:
    global _healing_engine
    if _healing_engine is None:
        _healing_engine = SelfHealingEngine()
    return _healing_engine


if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v31 SELF-HEALING ENGINE")
    print("=" * 70)

    engine = SelfHealingEngine()

    # Simulate some cycles
    for i in range(10):
        state = {"cycle": i, "level": i // 3, "energy": 1.0 + i * 0.1, "phi": 0.5 + i * 0.05, "phase": "near_critical", "action": "focus"}
        report = engine.check(i, state)
        print(f"C{i}: health={report['status']} anomaly={report['anomaly_score']:.2f}")

    # Trigger deep repair
    print(f"\n{'='*70}")
    print("DEEP REPAIR at C10")
    repair_report = engine.deep_repair(10)
    for r in repair_report['repairs']:
        print(f"  [{r['type']}] {'✅' if r['ok'] else '❌'} {r['detail']}")

    print(f"\n{'='*70}")
    print("STATUS:", engine.get_status())
    print(f"{'='*70}")
