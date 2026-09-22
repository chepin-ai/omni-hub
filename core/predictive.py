"""
OMNI-HUB Predictive Analytics v22
Trend forecasting and early warning based on historical state data.

The system learns from its own trajectory to anticipate future states,
detect impending stagnation, and recommend preemptive actions.

Philosophy: 候即违规 — reacting is slow; predicting is fast.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import math
from typing import Dict, List, Any, Optional


class PredictiveEngine:
    """Forecasts system state from historical trajectory."""

    def __init__(self, history_window: int = 100):
        self.history_window = history_window

    def _extract_series(self, history: List[Dict[str, Any]], key: str) -> List[float]:
        """Extract a numeric time series from history."""
        series = []
        for entry in history:
            state = entry.get('state', {})
            val = state.get(key)
            if val is not None and not math.isinf(val) and not math.isnan(val):
                series.append(float(val))
        return series

    def _linear_trend(self, series: List[float]) -> Dict[str, float]:
        """Compute linear trend: y = a*x + b."""
        n = len(series)
        if n < 2:
            return {"slope": 0.0, "intercept": series[0] if series else 0.0, "r2": 0.0}
        # Overflow protection: cap extremely large values
        capped = [min(v, 1e308) if v == v else 0.0 for v in series]  # NaN check
        x_mean = (n - 1) / 2
        y_mean = sum(capped) / n
        ss_xy = sum((i - x_mean) * (capped[i] - y_mean) for i in range(n))
        ss_xx = sum((i - x_mean) ** 2 for i in range(n))
        if ss_xx == 0:
            return {"slope": 0.0, "intercept": y_mean, "r2": 0.0}
        slope = ss_xy / ss_xx
        intercept = y_mean - slope * x_mean
        # R-squared with overflow protection
        try:
            ss_tot = sum(min((y - y_mean) ** 2, 1e308) for y in capped)
            ss_res = sum(min((capped[i] - (slope * i + intercept)) ** 2, 1e308) for i in range(n))
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        except OverflowError:
            r2 = 0.0
        return {"slope": slope, "intercept": intercept, "r2": max(0.0, r2)}

    def _exponential_growth_rate(self, series: List[float]) -> float:
        """Compute average exponential growth rate."""
        if len(series) < 2:
            return 0.0
        # Use log-linear regression for exponential fit
        log_series = [math.log(max(v, 1e-10)) for v in series]
        trend = self._linear_trend(log_series)
        return trend["slope"]  # This is the continuous growth rate

    def predict(self, history: List[Dict[str, Any]], horizon: int = 50) -> Dict[str, Any]:
        """Predict future state based on historical trajectory."""
        if len(history) < 10:
            return {"status": "insufficient_data", "horizon": horizon}

        recent = history[-self.history_window:]
        energy_series = self._extract_series(recent, 'energy')
        phi_series = self._extract_series(recent, 'phi')
        level_series = self._extract_series(recent, 'level')

        predictions = {}
        warnings = []
        recommendations = []

        # Energy prediction
        if len(energy_series) >= 10:
            energy_trend = self._linear_trend(energy_series)
            current_energy = energy_series[-1]
            pred_energy = energy_trend["slope"] * horizon + energy_trend["intercept"]
            if pred_energy <= current_energy * 1.001:
                warnings.append("energy_stagnation_predicted")
                recommendations.append("transcend")
            predictions["energy"] = {
                "current": current_energy,
                "predicted": pred_energy,
                "trend_slope": energy_trend["slope"],
                "r2": energy_trend["r2"],
            }

        # Phi prediction
        if len(phi_series) >= 10:
            phi_trend = self._linear_trend(phi_series)
            current_phi = phi_series[-1]
            pred_phi = phi_trend["slope"] * horizon + phi_trend["intercept"]
            pred_phi = max(0.0, min(1.0, pred_phi))
            if pred_phi < 0.3:
                warnings.append("phi_crash_predicted")
                recommendations.append("reflect")
            predictions["phi"] = {
                "current": current_phi,
                "predicted": pred_phi,
                "trend_slope": phi_trend["slope"],
                "r2": phi_trend["r2"],
            }

        # Level prediction (extrapolate from energy trend using thresholds)
        if len(level_series) >= 10 and "energy" in predictions:
            from core import constants as C
            pred_energy = predictions["energy"]["predicted"]
            pred_level = level_series[-1]
            for lvl in range(int(pred_level) + 1, C.MAX_LEVEL + 1):
                threshold = C.LEVEL_THRESHOLDS.get(lvl)
                if threshold and pred_energy >= threshold:
                    pred_level = lvl
                else:
                    break
            predictions["level"] = {
                "current": level_series[-1],
                "predicted": pred_level,
            }
            if pred_level > level_series[-1]:
                recommendations.append("focus")

        # Growth rate
        if len(energy_series) >= 10:
            growth_rate = self._exponential_growth_rate(energy_series)
            predictions["growth_rate"] = growth_rate
            if growth_rate < 0.001:
                warnings.append("growth_stagnation")
                recommendations.append("self_modify")

        return {
            "status": "predicted",
            "horizon": horizon,
            "predictions": predictions,
            "warnings": warnings,
            "recommendations": list(set(recommendations)),
            "confidence": min(1.0, len(history) / 500),  # More history = higher confidence
        }

    def detect_anomaly(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalous cycles (sudden drops, crashes)."""
        if len(history) < 20:
            return []
        energies = self._extract_series(history, 'energy')
        if len(energies) < 20:
            return []

        # Compute moving average and std
        window = 10
        anomalies = []
        for i in range(window, len(energies)):
            recent = energies[i - window:i]
            mean = sum(recent) / len(recent)
            variance = sum((x - mean) ** 2 for x in recent) / len(recent)
            std = math.sqrt(variance) if variance > 0 else 0
            if std > 0:
                z_score = (energies[i] - mean) / std
                if z_score < -2.0:  # Significant drop
                    anomalies.append({
                        "cycle": history[i].get('cycle', i),
                        "type": "energy_drop",
                        "z_score": round(z_score, 2),
                        "energy": energies[i],
                        "expected": round(mean, 2),
                    })
        return anomalies


if __name__ == "__main__":
    print("[OMNI-HUB v22] Predictive Analytics Demo")

    # Simulate history
    history = []
    import random
    energy = 1000.0
    phi = 0.5
    level = 15
    for i in range(300):
        energy *= 1.01
        phi = max(0.15, min(0.95, phi + random.uniform(-0.02, 0.02)))
        if energy > 2000 and level == 15:
            level = 16
        history.append({
            "cycle": i + 1,
            "state": {"energy": energy, "phi": phi, "level": level, "phase": "super_emergence_3"}
        })

    engine = PredictiveEngine(history_window=100)
    result = engine.predict(history, horizon=50)

    print(f"\nPrediction (horizon=50):")
    print(f"  Status: {result['status']}")
    print(f"  Confidence: {result['confidence']:.1%}")
    if 'energy' in result['predictions']:
        p = result['predictions']['energy']
        print(f"  Energy: {p['current']:.2f} → {p['predicted']:.2f} (slope={p['trend_slope']:.2f}, r²={p['r2']:.3f})")
    if 'phi' in result['predictions']:
        p = result['predictions']['phi']
        print(f"  Phi: {p['current']:.3f} → {p['predicted']:.3f}")
    if 'level' in result['predictions']:
        p = result['predictions']['level']
        print(f"  Level: {p['current']} → {p['predicted']}")
    print(f"  Warnings: {result['warnings']}")
    print(f"  Recommendations: {result['recommendations']}")

    anomalies = engine.detect_anomaly(history)
    print(f"\nAnomalies detected: {len(anomalies)}")
