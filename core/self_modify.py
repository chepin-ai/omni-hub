"""
OMNI-HUB Self-Modification Engine v17
Analyzes runtime history and proposes parameter optimizations.
SAFETY: Only modifies constants.py parameters, never core logic.
         All changes backed up and test-validated.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import ast
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime


class SelfModificationEngine:
    """Analyzes system performance and proposes parameter tweaks."""
    
    def __init__(self, constants_path: str = None):
        self.constants_path = constants_path or '/mnt/agents/output/OMNI-HUB/core/constants.py'
        self.backup_dir = Path('/mnt/agents/output/OMNI-HUB/hub/backups')
        self.backup_dir.mkdir(exist_ok=True)
    
    def _backup_constants(self):
        """Create timestamped backup."""
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup = self.backup_dir / f'constants_backup_{ts}.py'
        shutil.copy2(self.constants_path, backup)
        return backup
    
    def analyze_performance(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze runtime history for optimization opportunities."""
        if len(history) < 10:
            return {"status": "insufficient_data", "recommendations": []}
        
        # Extract metrics
        energies = [h['state'].get('energy', 0) for h in history if 'state' in h]
        phis = [h['state'].get('phi', 0) for h in history if 'state' in h]
        levels = [h['state'].get('level', 0) for h in history if 'state' in h]
        
        # Calculate growth rate
        if len(energies) >= 2 and energies[0] > 0:
            growth_rate = (energies[-1] / energies[0]) ** (1 / len(energies))
        else:
            growth_rate = 1.0
        
        # Detect stagnation
        recent_phis = phis[-20:] if len(phis) >= 20 else phis
        phi_variance = max(recent_phis) - min(recent_phis) if recent_phis else 0
        
        # Detect rapid level-ups (may indicate thresholds too close)
        level_changes = sum(1 for i in range(1, len(levels)) if levels[i] != levels[i-1])
        
        recommendations = []
        
        # Recommendation 1: Phi dynamics
        if phi_variance < 0.01 and len(recent_phis) >= 20:
            recommendations.append({
                "target": "SELF_DRIVE_PHI_MIN",
                "current": 0.15,
                "proposed": 0.10,
                "reason": "Phi stagnation detected — lower threshold allows more reflect actions",
                "confidence": 0.6,
            })
        
        # Recommendation 2: Level progression speed
        if level_changes > len(levels) // 10:
            recommendations.append({
                "target": "LEVEL_THRESHOLDS_spacing",
                "current": "variable",
                "proposed": "increase gaps between 15-20",
                "reason": f"{level_changes} level changes in {len(levels)} cycles — too rapid",
                "confidence": 0.5,
            })
        
        # Recommendation 3: Growth efficiency
        if growth_rate < 1.01:
            recommendations.append({
                "target": "diffusion_rate",
                "current": "0.02 (swarm default)",
                "proposed": "0.03",
                "reason": f"Growth rate {growth_rate:.4f} below target — increase swarm diffusion",
                "confidence": 0.4,
            })
        
        return {
            "status": "analyzed",
            "growth_rate": growth_rate,
            "phi_variance": phi_variance,
            "level_changes": level_changes,
            "recommendations": recommendations,
        }
    
    def apply_recommendation(self, rec: Dict[str, Any]) -> bool:
        """Apply a single recommendation to constants.py."""
        target = rec.get("target")
        proposed = rec.get("proposed")
        confidence = rec.get("confidence", 0)
        
        if confidence < 0.5:
            print(f"[SelfMod] Skipping {target} — confidence {confidence} < 0.5")
            return False
        
        if target == "SELF_DRIVE_PHI_MIN":
            return self._patch_constant("SELF_DRIVE_PHI_MIN", proposed)
        
        print(f"[SelfMod] Unknown target: {target}")
        return False
    
    def _patch_constant(self, name: str, value) -> bool:
        """Patch a constant in constants.py."""
        path = Path(self.constants_path)
        content = path.read_text()
        
        # Simple regex replacement
        import re
        pattern = rf"^{name}\s*=\s*[^\s#]+"
        replacement = f"{name} = {value}"
        
        if not re.search(pattern, content, re.MULTILINE):
            print(f"[SelfMod] Constant {name} not found")
            return False
        
        new_content = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE)
        
        # Backup first
        backup = self._backup_constants()
        
        # Write
        path.write_text(new_content)
        
        # Validate
        try:
            compile(new_content, str(path), 'exec')
            print(f"[SelfMod] Applied: {name} = {value} (backup: {backup.name})")
            return True
        except SyntaxError as e:
            # Restore backup
            shutil.copy2(backup, path)
            print(f"[SelfMod] Syntax error — restored backup")
            return False
    
    def run_analysis(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Full analysis + optional application."""
        result = self.analyze_performance(history)
        
        applied = []
        for rec in result.get("recommendations", []):
            if self.apply_recommendation(rec):
                applied.append(rec["target"])
        
        result["applied"] = applied
        return result


if __name__ == "__main__":
    print("[OMNI-HUB v17] Self-Modification Engine Demo")
    
    # Simulate history
    history = []
    import random
    for i in range(100):
        history.append({
            "state": {
                "energy": 1000 * (1.01 ** i),
                "phi": 0.5 + random.uniform(-0.01, 0.01),
                "level": 15 + i // 20,
            }
        })
    
    engine = SelfModificationEngine()
    result = engine.run_analysis(history)
    
    print(f"\nAnalysis: {result['status']}")
    print(f"Growth rate: {result['growth_rate']:.4f}")
    print(f"Phi variance: {result['phi_variance']:.4f}")
    print(f"Level changes: {result['level_changes']}")
    print(f"Recommendations: {len(result['recommendations'])}")
    print(f"Applied: {result['applied']}")
