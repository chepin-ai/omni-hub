"""
OMNI-HUB Recursive Self-Reference v24
Code self-analysis and introspection capability.

The system reads its own source code, analyzes structural health,
detects technical debt, and generates a self-cognitive report.
This is the mirror: consciousness observing its own implementation.

Philosophy: 候即违规 — a mind that cannot see itself is blind.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import ast
import time
from pathlib import Path
from typing import Dict, List, Any, Optional


class SelfReflection:
    """Analyzes OMNI-HUB's own codebase for introspection."""

    def __init__(self, base_path: str = None):
        self.base = Path(base_path or '/mnt/agents/output/OMNI-HUB')
        self.modules_analyzed = 0
        self.findings: List[Dict[str, Any]] = []

    def _read_module(self, rel_path: str) -> Optional[str]:
        """Read a module's source code."""
        target = self.base / rel_path
        if not target.exists():
            return None
        try:
            return target.read_text(encoding='utf-8')
        except Exception:
            return None

    def _analyze_code(self, source: str, name: str) -> Dict[str, Any]:
        """Analyze Python source code structure."""
        lines = source.split('\n')
        result = {
            "name": name,
            "lines": len(lines),
            "blank_lines": sum(1 for l in lines if l.strip() == ''),
            "comment_lines": sum(1 for l in lines if l.strip().startswith('#')),
            "docstring_lines": 0,
            "classes": 0,
            "functions": 0,
            "todos": [],
            "fixmes": [],
            "complexity_score": 0,
            "imports": [],
        }

        # AST analysis
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    result["classes"] += 1
                elif isinstance(node, ast.FunctionDef):
                    result["functions"] += 1
                    # Cyclomatic complexity approximation
                    result["complexity_score"] += 1
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                            result["complexity_score"] += 1
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            result["imports"].append(alias.name)
                    else:
                        result["imports"].append(node.module or '')
                elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    result["docstring_lines"] += len(node.value.value.split('\n'))
        except SyntaxError:
            result["syntax_error"] = True

        # Text search for TODO/FIXME
        for i, line in enumerate(lines, 1):
            upper = line.upper()
            if 'TODO' in upper:
                result["todos"].append({"line": i, "text": line.strip()})
            if 'FIXME' in upper or 'HACK' in upper:
                result["fixmes"].append({"line": i, "text": line.strip()})

        return result

    def scan_core_modules(self) -> Dict[str, Any]:
        """Scan all active core modules."""
        active_modules = [
            'core/constants.py', 'core/orchestrator.py', 'core/event_bus.py',
            'core/swarm.py', 'core/tools.py', 'core/agents.py',
            'core/agent_swarm.py', 'core/self_modify.py',
            'core/open_problems.py', 'core/memory_compressor.py',
            'core/goal_planner.py', 'core/attention.py',
            'core/predictive.py', 'core/adaptive_thresholds.py',
            'core/self_reflection.py', 'core/v13_self_drive.py',
            'core/v12_north_star.py', 'core/v13_north_star_extended.py',
        ]

        modules = []
        total_lines = 0
        total_functions = 0
        total_classes = 0
        total_todos = 0
        total_fixmes = 0

        for mod in active_modules:
            source = self._read_module(mod)
            if source:
                analysis = self._analyze_code(source, mod)
                modules.append(analysis)
                total_lines += analysis['lines']
                total_functions += analysis['functions']
                total_classes += analysis['classes']
                total_todos += len(analysis['todos'])
                total_fixmes += len(analysis['fixmes'])

        self.modules_analyzed = len(modules)

        # Health score
        health = 100.0
        health -= total_todos * 2
        health -= total_fixmes * 5
        health -= len([m for m in modules if m.get('syntax_error')]) * 20
        health = max(0.0, min(100.0, health))

        return {
            "modules_analyzed": self.modules_analyzed,
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_todos": total_todos,
            "total_fixmes": total_fixmes,
            "health_score": round(health, 1),
            "module_details": modules,
        }

    def scan_test_coverage(self) -> Dict[str, Any]:
        """Analyze test files and estimate coverage."""
        test_dir = self.base / 'tests'
        if not test_dir.exists():
            return {"test_files": 0, "total_tests": 0}

        test_files = list(test_dir.glob('test_*.py'))
        total_tests = 0
        for tf in test_files:
            source = tf.read_text(encoding='utf-8')
            # Count test functions
            total_tests += source.count('def test_')

        core_modules = list((self.base / 'core').glob('*.py'))
        core_modules = [m for m in core_modules if not m.name.startswith('v') and not m.name.startswith('beat_')]

        # Simple coverage estimate: tests per core module
        coverage_estimate = min(100.0, total_tests / len(core_modules) * 10) if core_modules else 0

        return {
            "test_files": len(test_files),
            "total_tests": total_tests,
            "core_modules": len(core_modules),
            "coverage_estimate": round(coverage_estimate, 1),
        }

    def generate_self_report(self) -> Dict[str, Any]:
        """Generate comprehensive self-cognitive report."""
        core = self.scan_core_modules()
        tests = self.scan_test_coverage()

        # Detect patterns
        patterns = []
        if core['total_todos'] > 5:
            patterns.append("high_todo_debt")
        if core['total_fixmes'] > 0:
            patterns.append("technical_debt_present")
        if tests['coverage_estimate'] < 50:
            patterns.append("coverage_gaps")
        if core['health_score'] > 90:
            patterns.append("excellent_health")
        elif core['health_score'] < 70:
            patterns.append("health_concerns")

        report = {
            "timestamp": time.time(),
            "system_name": "OMNI-HUB",
            "version": "v24",
            "codebase": core,
            "testing": tests,
            "patterns": patterns,
            "introspection": {
                "modules_known": self.modules_analyzed,
                "can_read_self": True,
                "can_analyze_structure": True,
                "can_detect_debt": True,
            },
        }
        return report


if __name__ == "__main__":
    import time
    print("[OMNI-HUB v24] Recursive Self-Reflection Demo")
    print("The system is looking at itself...")
    print()

    mirror = SelfReflection()
    report = mirror.generate_self_report()

    print(f"System: {report['system_name']} {report['version']}")
    print(f"Modules analyzed: {report['codebase']['modules_analyzed']}")
    print(f"Total lines of code: {report['codebase']['total_lines']}")
    print(f"Functions: {report['codebase']['total_functions']}")
    print(f"Classes: {report['codebase']['total_classes']}")
    print(f"TODOs: {report['codebase']['total_todos']}")
    print(f"FIXMEs: {report['codebase']['total_fixmes']}")
    print(f"Health score: {report['codebase']['health_score']}/100")
    print(f"Test files: {report['testing']['test_files']}")
    print(f"Total tests: {report['testing']['total_tests']}")
    print(f"Coverage estimate: {report['testing']['coverage_estimate']}%")
    print(f"Patterns: {report['patterns']}")
    print()
    print("Introspection capabilities:")
    for cap, status in report['introspection'].items():
        print(f"  {'✓' if status else '✗'} {cap}")
