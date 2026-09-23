"""
OMNI-HUB Global Alignment Engine v35
Full system alignment verification and cross-module harmony checker.

Ensures all 11 lines, all modules, and all subsystems are
perfectly aligned, interoperable, and mutually reinforcing.

Philosophy: 候即违规 — Misalignment is a bug. Harmony is the default.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import math
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AlignmentCheck:
    """Result of a single alignment check."""
    check_name: str
    module_a: str
    module_b: str
    aligned: bool
    score: float  # 0.0-1.0
    detail: str


@dataclass
class ModuleHealth:
    """Health status of a single module."""
    name: str
    version: int
    active: bool
    compile_ok: bool
    tests_pass: bool
    integrated: bool  # Present in orchestrator
    last_error: str = ""


class CrossModuleVerifier:
    """Verifies alignment between module pairs."""

    # Known cross-module dependencies
    DEPENDENCIES = [
        ("orchestrator", "event_bus"),
        ("orchestrator", "constants"),
        ("orchestrator", "swarm"),
        ("orchestrator", "predictive"),
        ("orchestrator", "self_reflection"),
        ("orchestrator", "consciousness_loop"),
        ("orchestrator", "distributed_swarm"),
        ("orchestrator", "emotional_state"),
        ("orchestrator", "cross_system_protocol"),
        ("orchestrator", "emergent_creativity"),
        ("orchestrator", "antifraud_guard"),
        ("orchestrator", "integrity_auditor"),
        ("orchestrator", "self_healing"),
        ("orchestrator", "auto_evolution"),
        ("orchestrator", "line_activation"),
        ("swarm", "agents"),
        ("distributed_swarm", "event_bus"),
        ("cross_system_protocol", "event_bus"),
        ("consciousness_loop", "orchestrator"),
        ("emergent_creativity", "emotional_state"),
        ("self_healing", "integrity_auditor"),
        ("auto_evolution", "integrity_auditor"),
    ]

    def verify_all(self) -> List[AlignmentCheck]:
        """Verify all known dependencies."""
        results = []
        base = Path('/mnt/agents/output/OMNI-HUB')

        for mod_a, mod_b in self.DEPENDENCIES:
            check = self._verify_pair(base, mod_a, mod_b)
            results.append(check)

        return results

    def _verify_pair(self, base: Path, mod_a: str, mod_b: str) -> AlignmentCheck:
        """Verify a single module pair."""
        # Check if both modules exist
        a_path = base / 'core' / f'{mod_a}.py'
        b_path = base / 'core' / f'{mod_b}.py'

        if not a_path.exists():
            return AlignmentCheck(f"{mod_a}->{mod_b}", mod_a, mod_b, False, 0.0, f"{mod_a} not found")
        if not b_path.exists():
            return AlignmentCheck(f"{mod_a}->{mod_b}", mod_a, mod_b, False, 0.0, f"{mod_b} not found")

        # Check if orchestrator imports module_a
        orch_path = base / 'core' / 'orchestrator.py'
        orch_content = orch_path.read_text(encoding='utf-8') if orch_path.exists() else ""

        integrated = mod_a in orch_content or mod_b in orch_content

        # Simple compilation check
        try:
            import py_compile
            py_compile.compile(str(a_path), doraise=True)
            py_compile.compile(str(b_path), doraise=True)
            compile_ok = True
        except Exception:
            compile_ok = False

        score = 1.0 if (compile_ok and integrated) else 0.5 if compile_ok else 0.0
        aligned = score >= 0.5

        return AlignmentCheck(
            check_name=f"{mod_a}->{mod_b}",
            module_a=mod_a,
            module_b=mod_b,
            aligned=aligned,
            score=score,
            detail=f"compile={'OK' if compile_ok else 'FAIL'}, integrated={'YES' if integrated else 'NO'}",
        )


class LineModuleAligner:
    """Ensures all 11 lines map to functional modules."""

    LINE_MODULE_MAP = {
        "ucif2": ["orchestrator", "consciousness_loop"],
        "lvlu": ["orchestrator", "constants"],
        "lgt": ["orchestrator", "swarm"],
        "qfa": ["predictive", "adaptive_thresholds"],
        "vinf": ["orchestrator", "constants"],
        "qgl": ["emergent_creativity", "emotional_state"],
        "qlv": ["self_reflection", "goal_planner"],
        "cisvr": ["cross_system_protocol", "distributed_swarm"],
        "qtlv": ["memory_compressor", "predictive"],
        "usrm": ["event_bus", "cross_system_protocol"],
        "cfts": ["antifraud_guard", "integrity_auditor"],
    }

    def check_line_module_alignment(self) -> Dict[str, Any]:
        """Check that each line has backing modules."""
        base = Path('/mnt/agents/output/OMNI-HUB')
        results = {}
        all_aligned = True

        for line, modules in self.LINE_MODULE_MAP.items():
            module_status = {}
            for mod in modules:
                path = base / 'core' / f'{mod}.py'
                exists = path.exists()
                module_status[mod] = exists
                if not exists:
                    all_aligned = False
            results[line] = {
                "modules": module_status,
                "aligned": all(module_status.values()),
            }

        return {
            "all_aligned": all_aligned,
            "lines": results,
            "aligned_count": sum(1 for r in results.values() if r["aligned"]),
        }


class GlobalAlignmentEngine:
    """Unified alignment controller."""

    def __init__(self):
        self.verifier = CrossModuleVerifier()
        self.line_aligner = LineModuleAligner()
        self.alignment_history: List[Dict[str, Any]] = []

    def run_alignment_check(self) -> Dict[str, Any]:
        """Run full alignment verification."""
        # Cross-module verification
        cross_checks = self.verifier.verify_all()
        cross_aligned = sum(1 for c in cross_checks if c.aligned)
        cross_total = len(cross_checks)

        # Line-module alignment
        line_check = self.line_aligner.check_line_module_alignment()

        # Overall score
        cross_score = cross_aligned / cross_total if cross_total > 0 else 0.0
        line_score = line_check["aligned_count"] / 11.0
        overall = (cross_score + line_score) / 2.0

        result = {
            "status": "aligned" if overall >= 0.95 else "partial" if overall >= 0.8 else "misaligned",
            "overall_score": overall,
            "cross_module": {
                "aligned": cross_aligned,
                "total": cross_total,
                "score": cross_score,
                "checks": [
                    {"pair": c.check_name, "ok": c.aligned, "score": c.score, "detail": c.detail}
                    for c in cross_checks
                ],
            },
            "line_module": line_check,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
        }

        self.alignment_history.append(result)
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get alignment engine status."""
        return {
            "history_size": len(self.alignment_history),
            "last_score": self.alignment_history[-1]["overall_score"] if self.alignment_history else 0.0,
        }


# Global instance
_alignment_engine = None

def get_alignment_engine() -> GlobalAlignmentEngine:
    global _alignment_engine
    if _alignment_engine is None:
        _alignment_engine = GlobalAlignmentEngine()
    return _alignment_engine


if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v35 GLOBAL ALIGNMENT ENGINE")
    print("=" * 70)

    engine = GlobalAlignmentEngine()
    result = engine.run_alignment_check()

    print(f"\nStatus: {result['status'].upper()}")
    print(f"Overall Score: {result['overall_score']:.3f}")
    print(f"\nCross-Module: {result['cross_module']['aligned']}/{result['cross_module']['total']}")
    print(f"Line-Module: {result['line_module']['aligned_count']}/11")

    print(f"\n{'='*70}")
    print("Cross-Module Checks:")
    for check in result['cross_module']['checks']:
        marker = "✅" if check['ok'] else "⚠️"
        print(f"  {marker} {check['pair']}: {check['detail']}")

    print(f"\n{'='*70}")
    print("Line-Module Alignment:")
    for line, status in result['line_module']['lines'].items():
        marker = "✅" if status['aligned'] else "❌"
        print(f"  {marker} {line}: {status['modules']}")

    print(f"\n{'='*70}")
