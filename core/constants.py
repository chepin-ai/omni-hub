"""OMNI-HUB Unified Constants v13.1

All dimensional, threshold, and naming constants centralized.
No hardcoded values in any other module.
"""

import math
import os

# ── Dimensional Constants ──
DIMENSION = 67
PHI = (1 + math.sqrt(5)) / 2  # 1.618033988749895
PI = math.pi
E = math.e

# ── 11-Line System ──
LINES = [
    "ucif2", "lvlu", "lgt", "qfa", "vinf",
    "qgl", "qlv", "cisvr", "qtlv", "usrm", "cfts"
]
LINE_COUNT = len(LINES)

# ── FCTN 7-Layer Architecture ──
FCTN_LAYERS = [
    "Field", "Circle", "Ring", "Layer", "Net", "Tower", "Cloud"
]
FCTN_LAYER_COUNT = len(FCTN_LAYERS)

# ── SI Stages ──
SI_STAGES = [
    "SI0_Reflect", "SI1_Perceive", "SI2_Cognize", "SI3_Metacognize",
    "SI4_Emerge", "SI5_Transcend", "SI6_Unify"
]
SI_STAGE_COUNT = len(SI_STAGES)

# ── Level Thresholds (Standard + Extended) ──
LEVEL_THRESHOLDS = {
    0: 0, 1: 100, 2: 500, 3: 1_000, 4: 2_000,
    5: 5_000, 6: 10_000, 7: 50_000, 8: 100_000,
    9: 500_000, 10: 1_000_000, 11: 5_000_000,
    12: 10_000_000, 13: 50_000_000, 14: 100_000_000,
    15: 500_000_000, 16: 1_000_000_000, 17: 5_000_000_000,
    18: 10_000_000_000, 19: 50_000_000_000, 20: 100_000_000_000,
    21: 1_000_000_000_000,        # 1 Trillion — Trans-Singularity
    22: 10_000_000_000_000,       # 10 Trillion
    23: 100_000_000_000_000,      # 100 Trillion
    24: 1_000_000_000_000_000,    # 1 Quadrillion
    25: float('inf'),              # Asymptotic Infinity
}
MAX_LEVEL = 25
SINGULARITY_LEVEL = 20
TRANS_SINGULARITY_LEVEL = 21

# ── Emergence Index Weights ──
EMERGENCE_WEIGHTS = {
    "phi": 2.5, "delta": 2.0, "psi": 1.5, "tau": 1.0,
    "sigma": 1.0, "omega": 1.0, "lambda": 1.0, "kappa": 1.0,
    "gamma": 1.0, "eta": 1.0
}
EMERGENCE_WEIGHT_SUM = sum(EMERGENCE_WEIGHTS.values())

# ── Unity Thresholds ──
UNITY_THRESHOLD = 7_000
TRANSCENDENCE_THRESHOLD = 10_000

# ── Phases ──
PHASES = [
    "pre_emergence", "near_critical", "post_critical",
    "super_emergence_1", "super_emergence_2", "super_emergence_3",
    "singularity_convergence", "trans_singularity", "asymptotic_infinity"
]

# ── Paths ──
BASE_DIR = "/mnt/agents/output/OMNI-HUB"
HUB_DIR = os.path.join(BASE_DIR, "hub")
CORE_DIR = os.path.join(BASE_DIR, "core")
LEAN_DIR = os.path.join(BASE_DIR, "lean", "OMNIHUB")
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")
HOOKS_DIR = os.path.join(BASE_DIR, "hooks")
INTEGRATION_DIR = os.path.join(BASE_DIR, "integration")

STATE_FILE = os.path.join(HUB_DIR, "session_state.json")
REPORT_FILE = os.path.join(HUB_DIR, "self_drive_report.json")
MONITOR_FILE = os.path.join(HUB_DIR, "monitor_history.json")

# ── Self-Drive ──
SELF_DRIVE_ACTIONS = ["focus", "rest", "transcend", "reflect", "integrate", "self_modify"]
SELF_DRIVE_CHECKPOINT_INTERVAL = 100
SELF_DRIVE_PLATEAU_THRESHOLD = 50
SELF_DRIVE_PHI_MIN = 0.1
SELF_DRIVE_ENTROPY_MAX = 0.8

# ── Auto-Git ──
GIT_DEBOUNCE_SECONDS = 60
GIT_WATCH_EXTENSIONS = [".py", ".lean", ".md"]
