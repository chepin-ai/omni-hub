"""
OMNI-HUB Open Problems Tracker v17.2
Autonomous self-diagnosis and issue management.

The system continuously scans its own health, tests, formal verification
status, and operational state. Detected issues are tracked with automatic
severity assignment, deduplication, and resolution detection.

Philosophy: 候即违规 — a problem known but untracked is a violation.
"""

import json
import subprocess
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class OpenProblem:
    """A single tracked issue."""
    id: str
    title: str
    description: str
    severity: str  # critical, high, medium, low
    category: str  # test, git, lean, system, code, network
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    resolution: Optional[str] = None
    cycle_detected: int = 0
    auto: bool = True  # Auto-detected vs manually filed

    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['status'] = 'RESOLVED' if self.is_resolved() else 'OPEN'
        return d


class OpenProblemsTracker:
    """Autonomous issue tracker for OMNI-HUB self-monitoring."""

    SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    def __init__(self, hub_dir: str = None):
        self.hub_dir = Path(hub_dir or '/mnt/agents/output/OMNI-HUB/hub')
        self.hub_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.hub_dir / 'open_problems.json'
        self.problems: Dict[str, OpenProblem] = {}
        self.cycle_count = 0
        self._load()

    def _load(self):
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                for p in data.get('problems', []):
                    prob = OpenProblem(**{k: v for k, v in p.items() if k in OpenProblem.__dataclass_fields__})
                    self.problems[prob.id] = prob
            except Exception:
                pass

    def _save(self):
        data = {
            "updated_at": datetime.now().isoformat(),
            "total": len(self.problems),
            "open": len([p for p in self.problems.values() if not p.is_resolved()]),
            "problems": [p.to_dict() for p in self.problems.values()],
        }
        self.state_file.write_text(json.dumps(data, indent=2, default=str))

    def _generate_id(self, category: str, title: str) -> str:
        """Deterministic ID for deduplication."""
        import hashlib
        h = hashlib.md5(f"{category}:{title}".encode()).hexdigest()[:8]
        return f"{category}-{h}"

    def register(self, title: str, description: str, severity: str, category: str, cycle: int = 0) -> str:
        """Register or update a problem."""
        pid = self._generate_id(category, title)
        if pid in self.problems:
            # Already exists — update if not resolved
            prob = self.problems[pid]
            if not prob.is_resolved():
                prob.description = description
                prob.severity = severity
            return pid
        prob = OpenProblem(
            id=pid, title=title, description=description,
            severity=severity, category=category, cycle_detected=cycle,
        )
        self.problems[pid] = prob
        return pid

    def resolve(self, pid: str, resolution: str = "Auto-resolved") -> bool:
        """Mark a problem as resolved."""
        if pid not in self.problems:
            return False
        prob = self.problems[pid]
        if prob.is_resolved():
            return False
        prob.resolved_at = time.time()
        prob.resolution = resolution
        return True

    def resolve_by_category(self, category: str, resolution: str = "Auto-resolved") -> int:
        """Resolve all open problems in a category."""
        count = 0
        for pid, prob in self.problems.items():
            if prob.category == category and not prob.is_resolved():
                prob.resolved_at = time.time()
                prob.resolution = resolution
                count += 1
        return count

    def scan(self, cycle: int = 0) -> Dict[str, Any]:
        """Full system scan — detect all open problems."""
        self.cycle_count = cycle
        base = Path('/mnt/agents/output/OMNI-HUB')
        detected = []

        # 1. Test health
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', str(base / 'tests'), '-q', '--tb=no'],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                # Parse failure count
                failed = 0
                for line in result.stdout.split('\n'):
                    if 'failed' in line:
                        parts = line.split()
                        for i, p in enumerate(parts):
                            if p == 'failed' and i > 0:
                                try:
                                    failed = int(parts[i-1])
                                except ValueError:
                                    pass
                detected.append(('test-failures', f'{failed} test(s) failing', 'high', 'test'))
            else:
                self.resolve_by_category('test', 'All tests passing')
        except Exception as e:
            detected.append(('test-unreachable', f'Cannot run tests: {e}', 'critical', 'test'))

        # 2. Git status — unpushed commits
        try:
            result = subprocess.run(
                ['git', '-C', str(base), 'log', '--oneline', '@{u}..HEAD'],
                capture_output=True, text=True, timeout=10,
            )
            if result.stdout.strip():
                count = len([l for l in result.stdout.strip().split('\n') if l])
                detected.append(('git-unpushed', f'{count} commit(s) not pushed to origin', 'medium', 'git'))
            else:
                self.resolve_by_category('git', 'All commits pushed')
        except Exception:
            pass  # May not have upstream configured

        # 3. Lean formal verification — sorry count
        try:
            lean_dir = base / 'lean' / 'OMNIHUB'
            if lean_dir.exists():
                result = subprocess.run(
                    ['grep', '-r', '^\\s*sorry', str(lean_dir)],
                    capture_output=True, text=True, timeout=10,
                )
                sorry_lines = [l for l in result.stdout.split('\n') if l.strip()]
                if sorry_lines:
                    detected.append(('lean-sorry', f'{len(sorry_lines)} sorry axiom(s) in Lean proofs', 'high', 'lean'))
                else:
                    self.resolve_by_category('lean', 'No sorrys remaining')
        except Exception:
            pass

        # 4. System resources
        try:
            df = subprocess.run(['df', '-h', '/mnt'], capture_output=True, text=True, timeout=5)
            if df.returncode == 0:
                lines = df.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    use_pct = parts[4] if len(parts) > 4 else "0%"
                    pct_val = int(use_pct.replace('%', '')) if use_pct.replace('%', '').isdigit() else 0
                    if pct_val > 90:
                        detected.append(('disk-critical', f'Disk usage {use_pct}', 'critical', 'system'))
                    elif pct_val > 75:
                        detected.append(('disk-warning', f'Disk usage {use_pct}', 'medium', 'system'))
                    else:
                        self.resolve_by_category('system', 'Disk space OK')
        except Exception:
            pass

        # 5. Legacy code audit
        legacy_files = list(base.glob('v[0-9]*.py')) + list(base.glob('core/v[0-9]*.py'))
        if len(legacy_files) > 20:
            detected.append(('legacy-debt', f'{len(legacy_files)} legacy Python files (v1-v11)', 'low', 'code'))
        else:
            self.resolve_by_category('code', 'Legacy debt reduced')

        # 6. Python syntax errors
        try:
            # Scan only active modules (whitelist approach)
            active_modules = [
                'core/constants.py', 'core/orchestrator.py', 'core/event_bus.py',
                'core/swarm.py', 'core/tools.py', 'core/self_modify.py',
                'core/open_problems.py', 'core/v13_self_drive.py',
                'core/v12_north_star.py', 'core/v13_north_star_extended.py',
                'memory/session_persistence.py', 'hooks/auto_commit.py',
                'dashboard/v13_monitor.py', 'dashboard/web_dashboard.py',
                'run_v15.py',
            ]
            syntax_errors = 0
            for mod in active_modules:
                f = base / mod
                if f.exists():
                    try:
                        compile(f.read_text(), str(f), 'exec')
                    except SyntaxError:
                        syntax_errors += 1
            if syntax_errors > 0:
                detected.append(('syntax-errors', f'{syntax_errors} active module(s) with syntax errors', 'critical', 'code'))
            else:
                self.resolve_by_category('code', 'All active modules compile cleanly')
        except Exception:
            pass

        # Register all detected
        for title, desc, sev, cat in detected:
            self.register(title, desc, sev, cat, cycle)

        self._save()

        open_probs = [p for p in self.problems.values() if not p.is_resolved()]
        return {
            "cycle": cycle,
            "open_count": len(open_probs),
            "critical": len([p for p in open_probs if p.severity == 'critical']),
            "high": len([p for p in open_probs if p.severity == 'high']),
            "medium": len([p for p in open_probs if p.severity == 'medium']),
            "low": len([p for p in open_probs if p.severity == 'low']),
            "problems": [p.to_dict() for p in sorted(open_probs, key=lambda x: self.SEVERITY_ORDER.get(x.severity, 99))],
        }

    def get_status(self) -> Dict[str, Any]:
        open_probs = [p for p in self.problems.values() if not p.is_resolved()]
        return {
            "total_tracked": len(self.problems),
            "open": len(open_probs),
            "by_severity": {
                "critical": len([p for p in open_probs if p.severity == 'critical']),
                "high": len([p for p in open_probs if p.severity == 'high']),
                "medium": len([p for p in open_probs if p.severity == 'medium']),
                "low": len([p for p in open_probs if p.severity == 'low']),
            },
        }


if __name__ == "__main__":
    import sys
    print("[OMNI-HUB v17.2] Open Problems Tracker Demo")
    tracker = OpenProblemsTracker()
    result = tracker.scan(cycle=1)
    print(f"\nScan complete:")
    print(f"  Open problems: {result['open_count']}")
    print(f"  Critical: {result['critical']}, High: {result['high']}, Medium: {result['medium']}, Low: {result['low']}")
    if result['problems']:
        print(f"\n  Top issues:")
        for p in result['problems'][:5]:
            print(f"    [{p['severity'].upper()}] {p['title']}: {p['description']}")
