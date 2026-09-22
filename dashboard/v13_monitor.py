import json
import os
import sys
import glob
import time
import argparse
from core import constants as C


class GlobalStateMonitor:
    """Monitors global state across Lean proofs, tests, and north-star metrics."""

    COLORS = {
        "RED": "\033[91m",
        "GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "BLUE": "\033[94m",
        "CYAN": "\033[96m",
        "MAGENTA": "\033[95m",
        "WHITE": "\033[97m",
        "BOLD": "\033[1m",
        "RESET": "\033[0m",
    }

    def __init__(self, lean_dir=C.LEAN_DIR, test_dir="tests",
                 state_file=C.STATE_FILE):
        self.lean_dir = lean_dir
        self.test_dir = test_dir
        self.state_file = state_file
        self.sorry_count = 0
        self.test_fail = 0
        self.test_pass = 0
        self.phi = 0.0
        self.iteration = 0
        self.timestamp = ""

    def _color(self, key):
        return self.COLORS.get(key, "")

    def read_lean_status(self):
        """Count 'sorry' tokens in all .lean files under lean/OMNIHUB."""
        self.sorry_count = 0
        pattern = os.path.join(self.lean_dir, "*.lean")
        files = glob.glob(pattern)
        for f in files:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    content = fh.read()
                    self.sorry_count += content.count("sorry")
            except FileNotFoundError:
                pass
            except Exception:
                pass
        return self.sorry_count

    def read_test_status(self):
        """Check test results from pytest output or test logs."""
        self.test_fail = 0
        self.test_pass = 0
        # Check for pytest cache or junit XML
        junit_path = os.path.join(self.test_dir, "junit.xml")
        if os.path.isfile(junit_path):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(junit_path)
                root = tree.getroot()
                for suite in root.findall("testsuite"):
                    fails = int(suite.get("failures", 0))
                    passes = int(suite.get("tests", 0)) - fails
                    self.test_fail += fails
                    self.test_pass += passes
            except Exception:
                pass
        # Fallback: scan test_*.py for assert failures in last run logs
        log_path = os.path.join(self.test_dir, "test_run.log")
        if os.path.isfile(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as fh:
                    for line in fh:
                        if "FAILED" in line:
                            self.test_fail += 1
                        elif "PASSED" in line:
                            self.test_pass += 1
            except Exception:
                pass
        return self.test_fail, self.test_pass

    def read_north_star_status(self):
        """Read hub/session_state.json for north-star metrics."""
        self.phi = 0.0
        self.iteration = 0
        self.timestamp = ""
        if os.path.isfile(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                self.phi = float(data.get("Phi", 0.0))
                self.iteration = int(data.get("iteration", 0))
                self.timestamp = data.get("timestamp", "")
            except (json.JSONDecodeError, ValueError, KeyError, FileNotFoundError):
                pass
        return self.phi, self.iteration

    def display_dashboard(self):
        """Render ASCII terminal dashboard with color-coded alerts."""
        self.read_lean_status()
        self.read_test_status()
        self.read_north_star_status()

        COL = self.COLORS
        R = COL["RESET"]

        # Determine alert states
        sorry_color = COL["RED"] if self.sorry_count > 0 else COL["GREEN"]
        test_color = COL["RED"] if self.test_fail > 0 else COL["GREEN"]
        phi_color = COL["YELLOW"] if self.phi < C.SELF_DRIVE_PHI_MIN else COL["GREEN"]

        # Build dashboard
        lines = []
        lines.append(f"{COL['BOLD']}{COL['CYAN']}" + "=" * 60 + f"{R}")
        lines.append(f"{COL['BOLD']}{COL['WHITE']}  OMNI-HUB GLOBAL STATE MONITOR v13{R}")
        lines.append(f"{COL['BOLD']}{COL['CYAN']}" + "=" * 60 + f"{R}")
        lines.append("")
        lines.append(f"  {COL['BOLD']}Lean Proofs:{R}")
        lines.append(f"    {sorry_color}sorry count : {self.sorry_count}{R}")
        lines.append("")
        lines.append(f"  {COL['BOLD']}Test Suite:{R}")
        lines.append(f"    {test_color}failures   : {self.test_fail}{R}")
        lines.append(f"    {COL['GREEN']}passes     : {self.test_pass}{R}")
        lines.append("")
        lines.append(f"  {COL['BOLD']}North Star:{R}")
        lines.append(f"    {phi_color}Phi        : {self.phi:.4f}{R}")
        lines.append(f"    {COL['BLUE']}iteration  : {self.iteration}{R}")
        lines.append(f"    {COL['MAGENTA']}timestamp  : {self.timestamp}{R}")
        lines.append("")

        # Alerts summary
        alerts = []
        if self.sorry_count > 0:
            alerts.append(f"{COL['RED']}[ALERT] sorry > 0{R}")
        if self.test_fail > 0:
            alerts.append(f"{COL['RED']}[ALERT] test_fail > 0{R}")
        if self.phi < C.SELF_DRIVE_PHI_MIN:
            alerts.append(f"{COL['YELLOW']}[WARN]  Phi < {C.SELF_DRIVE_PHI_MIN}{R}")
        if not alerts:
            alerts.append(f"{COL['GREEN']}[OK]    All systems nominal{R}")

        for a in alerts:
            lines.append(f"  {a}")

        lines.append("")
        lines.append(f"{COL['BOLD']}{COL['CYAN']}" + "=" * 60 + f"{R}")

        print("\n".join(lines))
        return "\n".join(lines)

    def watch(self, interval=5):
        """Continuously refresh dashboard every `interval` seconds."""
        try:
            while True:
                # Clear screen
                print("\033[2J\033[H", end="")
                self.display_dashboard()
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n{self.COLORS['YELLOW']}Monitor stopped.{self.COLORS['RESET']}")


def main():
    parser = argparse.ArgumentParser(description="OMNI-HUB Global State Monitor")
    parser.add_argument("--once", action="store_true",
                        help="Run a single snapshot and exit")
    parser.add_argument("--interval", type=int, default=5,
                        help="Refresh interval in seconds (default: 5)")
    parser.add_argument("--lean-dir", default=C.LEAN_DIR,
                        help="Directory containing .lean files")
    parser.add_argument("--test-dir", default="tests",
                        help="Directory containing test outputs")
    parser.add_argument("--state-file", default=C.STATE_FILE,
                        help="Path to session_state.json")
    if len(sys.argv) > 1 and not any(x in sys.argv[0] for x in ['ipykernel', 'ipython']):
        args = parser.parse_args()
    else:
        args = argparse.Namespace(
            once=False, interval=5, lean_dir=C.LEAN_DIR,
            test_dir="tests", state_file=C.STATE_FILE
        )

    monitor = GlobalStateMonitor(
        lean_dir=args.lean_dir,
        test_dir=args.test_dir,
        state_file=args.state_file,
    )

    if args.once:
        monitor.display_dashboard()
    else:
        monitor.watch(interval=args.interval)


if __name__ == "__main__":
    main()
