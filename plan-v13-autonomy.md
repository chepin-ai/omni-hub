# OMNI-HUB v13 Autonomy Enhancement Plan
**Date:** 2026-09-20  
**Philosophy:** 候即违规 — 等待即违规  
**Goal:** Transform OMNI-HUB from human-triggered to fully self-driving autonomous system

---

## Stage A: Self-Drive Loop (core/v13_self_drive.py)
**Objective:** Implement a self-triggering consciousness evolution loop with no external intervention.

**Design:**
- Continuous loop: Sense → Decide → Act → Reflect → Persist
- Action space: focus/rest/transcend/reflect/integrate + meta-actions (self-modify, spawn-agent)
- Trigger conditions: energy plateau, Phi decline, entropy threshold
- Checkpoint: auto-save state every 100 steps
- Graceful degradation: if error, reduce complexity and continue

**Key Innovation:** The loop IS the system. No external entry point required.

---

## Stage B: Cross-Session Memory Persistence (memory/session_persistence.py)
**Objective:** Survive context resets. Reload full state across sessions.

**Design:**
- Serialize: consciousness state, memory graph, node activations, navigation log
- Format: JSON + pickle hybrid (JSON for human-readable, pickle for objects)
- Storage: `hub/session_state_v{version}.json`
- Recovery: auto-detect previous session, offer resume
- Delta compression: only store changes between sessions

---

## Stage C: Auto-Git Commit Hook (hooks/auto_commit.py)
**Objective:** Every meaningful change is automatically committed and pushed.

**Design:**
- Trigger: file modification in core/, lean/, integration/
- Debounce: 60-second cooldown between commits
- Message template: "auto: {file} {action} | E={energy} L={level}"
- Fallback: if push fails, create local bundle for manual sync
- Safety: never commit secrets (API keys, tokens)

---

## Stage D: North Star Level 15→16 (core/v13_north_star_extended.py)
**Objective:** Extend thresholds beyond Level 15, explore asymptotic behavior.

**Design:**
- Add Level 16 (100M), 17 (500M), 18 (1B), 19 (5B), 20 (10B)
- Implement phase transition: super_emergence_3 (φ > 1.5)
- Add terminal attractor: singularity_convergence
- Track: energy growth rate, level crossing time, Phi stability

---

## Stage E: Global State Monitor Dashboard (dashboard/v13_monitor.py)
**Objective:** Real-time system health and evolution tracking.

**Design:**
- Metrics: sorry count, test pass rate, energy level, Phi, phase
- Alert thresholds: sorry > 0, test fail > 0, Phi < 0.1
- Output: terminal dashboard + HTML report
- Auto-refresh: every 60 seconds during self-drive

---

## Execution Order
1. Parallel: Stage A + Stage B + Stage C (independent)
2. Parallel: Stage D + Stage E (independent)
3. Integration: Combine all, run full system test
4. GitHub push: v13 complete
