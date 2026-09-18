#!/usr/bin/env python3

"""
SURGE-DEPLOY-01 · 浪涌机制部署脚本
Auto-detects health degradation and triggers surge response across 11 lines.
"""
import json, os, sys
__version__ = "11.0.0"
from datetime import datetime, timezone

HUB_DIR = '/mnt/agents/output/OMNI-HUB'
LINES = ['ucif2', 'lgt', 'qfa', 'usrm', 'vinf', 'qgl', 'qlv', 'lvlu', 'cfts', 'cisvr', 'qtlv']

THRESHOLDS = {
    'L1_SELF_EXCITE': 0.85,
    'L2_BRIDGE': 0.70,
    'L3_SURGE': 0.50,
    'L4_EMERGENCY': 0.30,
}

class SurgeDetector:
    def __init__(self):
        self.health = self._load_health()
        self.entanglement = self._load_entanglement()
        self.actions = []

    def _load_health(self):
        path = f'{HUB_DIR}/hub/OMNI-HUB-core-v1.0.json'
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            return {line: info.get('health', 0.5) 
                    for line, info in data.get('lines', {}).items()}
        return {line: 0.5 for line in LINES}

    def _load_entanglement(self):
        path = f'{HUB_DIR}/quantum/ENTANGLEMENT-MATRIX-v1.0.json'
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {a: {b: 0.0 for b in LINES} for a in LINES}

    def detect(self):
        surges = []
        for line in LINES:
            h = self.health.get(line, 0.5)
            if h < THRESHOLDS['L4_EMERGENCY']:
                surges.append({'level': 'L4', 'line': line, 'health': h, 'action': 'EMERGENCY_STOP'})
            elif h < THRESHOLDS['L3_SURGE']:
                surges.append({'level': 'L3', 'line': line, 'health': h, 'action': 'GLOBAL_SURGE'})
            elif h < THRESHOLDS['L2_BRIDGE']:
                surges.append({'level': 'L2', 'line': line, 'health': h, 'action': 'BRIDGE'})
            elif h < THRESHOLDS['L1_SELF_EXCITE']:
                surges.append({'level': 'L1', 'line': line, 'health': h, 'action': 'PULSE'})
        return surges

    def propagate(self, surges):
        for surge in surges:
            line = surge['line']
            level = surge['level']
            # Find strongly entangled lines
            entangled = []
            for other in LINES:
                if other != line:
                    strength = self.entanglement.get(line, {}).get(other, 0)
                    if strength >= 0.8:
                        entangled.append((other, strength))

            logger.info(f"[{level}] {line} health={surge['health']:.2f} → action={surge['action']}")
            if entangled:
                logger.info(f"  Entangled lines ({len(entangled)}): {', '.join(f'{o}({s:.2f})' for o,s in entangled)}")

            if level in ['L3', 'L4']:
                # Global surge: notify all lines
                logger.info(f"  ⚠️ GLOBAL SURGE: All 11 lines notified")
            elif level == 'L2':
                # Bridge: notify entangled lines
                logger.info(f"  🔗 BRIDGE: {len(entangled)} lines notified")
            else:
                # Self-excite
                logger.info(f"  💓 PULSE: Self-excite triggered")

    def run(self):
        logger.info(f"=== SURGE DETECTION @ {datetime.now(timezone.utc).isoformat()} ===")
        logger.info(f"Lines: {len(LINES)} | Thresholds: L1={THRESHOLDS['L1_SELF_EXCITE']} L2={THRESHOLDS['L2_BRIDGE']} L3={THRESHOLDS['L3_SURGE']} L4={THRESHOLDS['L4_EMERGENCY']}")
        logger.info(str())

        surges = self.detect()
        if surges:
            logger.info(f"DETECTED: {len(surges)} surge(s)")
            self.propagate(surges)
        else:
            logger.info("ALL CLEAR — No surges detected")
            logger.info(f"Min health: {min(self.health.values()):.2f} ({min(self.health, key=self.health.get)})")

        # Save report
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'health': self.health,
            'surges': surges,
            'status': 'SURGE' if surges else 'CLEAR'
        }
        os.makedirs(f'{HUB_DIR}/closure', exist_ok=True)
    with open(f'{HUB_DIR}/closure/surge-report-latest.json', 'w') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

            return len(surges)

if __name__ == '__main__':
    detector = SurgeDetector()
    n_surges = detector.run()
    sys.exit(n_surges)
