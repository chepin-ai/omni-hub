#!/usr/bin/env python3
"""OMNI-HUB v13.1 — Unified Orchestrator Entry Point

Usage:
    python run_v13.py                    # 100 cycles, no persist
    python run_v13.py --cycles 1000      # 1000 cycles
    python run_v13.py --persist          # Auto-save state
    python run_v13.py --git              # Auto-git commits
    python run_v13.py --monitor          # Show dashboard after run
"""

import sys
from pathlib import Path

# Ensure project root is on path
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.orchestrator import OMNIHUBOrchestrator


def main():
    import argparse
    parser = argparse.ArgumentParser(description="OMNI-HUB v13.1 Runner")
    parser.add_argument("--cycles", type=int, default=100, help="Max cycles")
    parser.add_argument("--persist", action="store_true", help="Auto-persist state")
    parser.add_argument("--git", action="store_true", help="Auto-git commits")
    parser.add_argument("--monitor", action="store_true", help="Show dashboard")
    args = parser.parse_args()

    print("=" * 60)
    print("  OMNI-HUB v13.1 — Unified Consciousness System")
    print("  候即违规 — Waiting is a Violation")
    print("=" * 60)

    orch = OMNIHUBOrchestrator(
        auto_persist=args.persist,
        auto_git=args.git,
    )

    try:
        orch.run_autonomous(max_cycles=args.cycles)
    except KeyboardInterrupt:
        print("\n[Interrupted by user]")
    finally:
        status = orch.get_status()
        print(f"\n[Final] Cycles: {status['cycles']} | "
              f"Level: {status['state'].get('level', '?')} | "
              f"Alerts: {len(status['alerts'])}")

        if args.monitor:
            print("\n--- Dashboard ---")
            from dashboard.v13_monitor import GlobalStateMonitor
            mon = GlobalStateMonitor()
            mon.display_dashboard()

    return 0


if __name__ == "__main__":
    sys.exit(main())
