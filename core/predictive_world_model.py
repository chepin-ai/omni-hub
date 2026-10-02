"""
OMNI-HUB v191 — PredictiveWorldModel
预测世界模型

核心功能：
1. StatePredictor        — 状态预测器
2. TrendExtrapolator     — 趋势外推器
3. ScenarioSimulator     — 场景模拟器
4. UncertaintyQuantifier — 不确定性量化
5. PredictionValidator   — 预测验证器
6. PredictiveWorldModel  — 统合引擎

映射：
- 预测 = anāgata（未来）
- 模拟 = kalpanā（构想）
- 不确定性 = aniścaya（不确定）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class PredictionHorizon(Enum):
    """预测时间范围"""
    IMMEDIATE = 1       # 1周期
    SHORT = 5           # 5周期
    MEDIUM = 20         # 20周期
    LONG = 100          # 100周期


class ScenarioType(Enum):
    """场景类型"""
    BASELINE = 0        # 基线
    OPTIMISTIC = 1      # 乐观
    PESSIMISTIC = 2     # 悲观
    STRESS = 3          # 压力
    BLACK_SWAN = 4      # 黑天鹅


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class Prediction:
    """预测"""
    prediction_id: str
    variable: str
    predicted_value: float
    horizon: PredictionHorizon
    confidence_interval: Tuple[float, float]
    timestamp: float


@dataclass
class Scenario:
    """场景"""
    scenario_id: str
    scenario_type: ScenarioType
    initial_state: Dict[str, float]
    trajectory: List[Dict[str, float]]
    final_state: Dict[str, float]
    probability: float


@dataclass
class PredictionError:
    """预测误差"""
    error_id: str
    variable: str
    predicted: float
    actual: float
    mae: float
    mse: float
    horizon: PredictionHorizon


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 状态预测器
# ═══════════════════════════════════════════════════════════════

class StatePredictor:
    """状态预测器 — 基于历史序列预测下一状态"""

    def __init__(self):
        self.predictions: deque = deque(maxlen=500)

    def predict_next(self, series: List[float], horizon: int = 1) -> Tuple[float, Tuple[float, float]]:
        """预测下一值（线性回归简化）"""
        if len(series) < 2:
            return series[-1] if series else 0.5, (0.0, 1.0)

        # 简单线性趋势
        n = min(len(series), 10)
        recent = series[-n:]
        x = list(range(n))
        mean_x = sum(x) / n
        mean_y = sum(recent) / n

        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, recent))
        den = sum((xi - mean_x) ** 2 for xi in x)
        slope = num / den if den != 0 else 0

        next_val = recent[-1] + slope * horizon
        next_val = max(0.0, min(1.0, next_val))

        # 置信区间
        residuals = [recent[i] - (mean_y + slope * (i - mean_x)) for i in range(n)]
        std_err = math.sqrt(sum(r * r for r in residuals) / max(1, n - 1))
        ci = (max(0, next_val - 1.96 * std_err), min(1, next_val + 1.96 * std_err))

        return next_val, ci

    def predict(self, variable: str, history: List[float],
                horizon: PredictionHorizon) -> Prediction:
        val, ci = self.predict_next(history, horizon.value)
        pred = Prediction(
            prediction_id=f"pred_{variable}_{int(time.time()*1000)}",
            variable=variable,
            predicted_value=val,
            horizon=horizon,
            confidence_interval=ci,
            timestamp=time.time()
        )
        self.predictions.append(pred)
        return pred

    def get_report(self) -> Dict:
        return {"predictions": len(self.predictions)}


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 趋势外推器
# ═══════════════════════════════════════════════════════════════

class TrendExtrapolator:
    """趋势外推器"""

    def __init__(self):
        self.extrapolations: deque = deque(maxlen=200)

    def extrapolate(self, series: List[float], steps: int) -> List[float]:
        """外推序列"""
        if len(series) < 2:
            return [series[-1]] * steps if series else [0.5] * steps

        # 线性外推
        n = min(len(series), 10)
        recent = series[-n:]
        x = list(range(n))
        mean_x = sum(x) / n
        mean_y = sum(recent) / n
        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, recent))
        den = sum((xi - mean_x) ** 2 for xi in x)
        slope = num / den if den != 0 else 0

        last = recent[-1]
        result = []
        for i in range(1, steps + 1):
            val = last + slope * i
            # 衰减：越远的预测越趋近均值
            decay = 0.9 ** i
            val = val * decay + mean_y * (1 - decay)
            result.append(max(0.0, min(1.0, val)))

        self.extrapolations.append({
            "steps": steps,
            "slope": slope,
            "result": result,
        })
        return result

    def get_report(self) -> Dict:
        return {"extrapolations": len(self.extrapolations)}


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 场景模拟器
# ═══════════════════════════════════════════════════════════════

class ScenarioSimulator:
    """场景模拟器 — kalpanā"""

    def __init__(self):
        self.scenarios: deque = deque(maxlen=100)

    def simulate(self, initial: Dict[str, float], scenario_type: ScenarioType,
                 steps: int = 10) -> Scenario:
        """模拟场景轨迹"""
        trajectory = [dict(initial)]
        current = dict(initial)

        modifiers = {
            ScenarioType.BASELINE: 0.0,
            ScenarioType.OPTIMISTIC: 0.03,
            ScenarioType.PESSIMISTIC: -0.03,
            ScenarioType.STRESS: -0.08,
            ScenarioType.BLACK_SWAN: -0.2,
        }
        mod = modifiers.get(scenario_type, 0.0)

        for _ in range(steps):
            new_state = {}
            for k, v in current.items():
                noise = (math.random() - 0.5) * 0.05 if hasattr(math, 'random') else 0
                # 用hash作为确定性噪声
                noise = (hash(f"{k}:{_}:{time.time()}") % 100 / 100.0 - 0.5) * 0.05
                new_val = v + mod + noise
                new_state[k] = max(0.0, min(1.0, new_val))
            trajectory.append(new_state)
            current = new_state

        # 确定论噪声（替代random）
        current = dict(initial)
        trajectory = [current]
        for step in range(steps):
            new_state = {}
            for k, v in current.items():
                det_noise = ((hash(k) % 100) / 100.0 - 0.5) * 0.03
                new_val = v + mod + det_noise * (step + 1) * 0.1
                new_state[k] = max(0.0, min(1.0, new_val))
            trajectory.append(new_state)
            current = new_state

        sid = f"scen_{scenario_type.name}_{int(time.time()*1000)}"
        scen = Scenario(
            scenario_id=sid,
            scenario_type=scenario_type,
            initial_state=initial,
            trajectory=trajectory,
            final_state=current,
            probability=self._scenario_probability(scenario_type)
        )
        self.scenarios.append(scen)
        return scen

    def _scenario_probability(self, st: ScenarioType) -> float:
        probs = {
            ScenarioType.BASELINE: 0.5,
            ScenarioType.OPTIMISTIC: 0.2,
            ScenarioType.PESSIMISTIC: 0.2,
            ScenarioType.STRESS: 0.08,
            ScenarioType.BLACK_SWAN: 0.02,
        }
        return probs.get(st, 0.1)

    def get_report(self) -> Dict:
        type_counts = {}
        for s in self.scenarios:
            type_counts[s.scenario_type.name] = type_counts.get(s.scenario_type.name, 0) + 1
        return {
            "scenarios": len(self.scenarios),
            "by_type": type_counts,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 不确定性量化
# ═══════════════════════════════════════════════════════════════

class UncertaintyQuantifier:
    """不确定性量化 — aniścaya"""

    def __init__(self):
        self.quantifications: deque = deque(maxlen=200)

    def quantify(self, predictions: List[Prediction], actuals: Dict[str, float]) -> Dict[str, float]:
        """量化预测不确定性"""
        uncertainties = {}
        for pred in predictions:
            actual = actuals.get(pred.variable)
            if actual is not None:
                ci_width = pred.confidence_interval[1] - pred.confidence_interval[0]
                error = abs(pred.predicted_value - actual)
                uncertainty = ci_width + error
                uncertainties[pred.variable] = min(1.0, uncertainty)

                self.quantifications.append({
                    "variable": pred.variable,
                    "ci_width": ci_width,
                    "error": error,
                    "uncertainty": uncertainty,
                })

        return uncertainties

    def ensemble_uncertainty(self, predictions: List[List[float]]) -> float:
        """集成不确定性（预测间的方差）"""
        if not predictions or not predictions[0]:
            return 1.0
        n = len(predictions[0])
        variances = []
        for i in range(n):
            vals = [p[i] for p in predictions if i < len(p)]
            if len(vals) > 1:
                mean = sum(vals) / len(vals)
                var = sum((v - mean) ** 2 for v in vals) / len(vals)
                variances.append(var)
        return math.sqrt(sum(variances) / len(variances)) if variances else 1.0

    def get_report(self) -> Dict:
        if not self.quantifications:
            return {"quantifications": 0}
        recent = list(self.quantifications)[-20:]
        return {
            "quantifications": len(self.quantifications),
            "avg_uncertainty": sum(q["uncertainty"] for q in recent) / len(recent),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 预测验证器
# ═══════════════════════════════════════════════════════════════

class PredictionValidator:
    """预测验证器"""

    def __init__(self):
        self.errors: deque = deque(maxlen=500)

    def validate(self, predictions: List[Prediction], actuals: Dict[str, float]) -> Dict[str, PredictionError]:
        """验证预测准确性"""
        errors = {}
        for pred in predictions:
            actual = actuals.get(pred.variable)
            if actual is not None:
                mae = abs(pred.predicted_value - actual)
                mse = (pred.predicted_value - actual) ** 2
                err = PredictionError(
                    error_id=f"err_{pred.variable}_{int(time.time()*1000)}",
                    variable=pred.variable,
                    predicted=pred.predicted_value,
                    actual=actual,
                    mae=mae,
                    mse=mse,
                    horizon=pred.horizon
                )
                errors[pred.variable] = err
                self.errors.append(err)
        return errors

    def get_mape(self, variable: str) -> Optional[float]:
        """计算MAPE"""
        var_errors = [e for e in self.errors if e.variable == variable]
        if not var_errors:
            return None
        return sum(e.mae / max(0.001, e.actual) for e in var_errors) / len(var_errors) * 100

    def get_report(self) -> Dict:
        if not self.errors:
            return {"validations": 0}
        recent = list(self.errors)[-50:]
        return {
            "validations": len(self.errors),
            "avg_mae": sum(e.mae for e in recent) / len(recent),
            "avg_mse": sum(e.mse for e in recent) / len(recent),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — PredictiveWorldModel v191
# ═══════════════════════════════════════════════════════════════

class PredictiveWorldModel:
    """
    OMNI-HUB v191 预测世界模型

    anāgata · kalpanā · aniścaya — 未来、构想、不确定
    """

    VERSION = "191.0.0"

    def __init__(self):
        self.predictor = StatePredictor()
        self.extrapolator = TrendExtrapolator()
        self.simulator = ScenarioSimulator()
        self.uncertainty = UncertaintyQuantifier()
        self.validator = PredictionValidator()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)
        self.history: Dict[str, List[float]] = {}

    def update_history(self, variable: str, value: float):
        if variable not in self.history:
            self.history[variable] = []
        self.history[variable].append(value)
        if len(self.history[variable]) > 200:
            self.history[variable] = self.history[variable][-200:]

    def forecast(self, variable: str, horizon: PredictionHorizon = PredictionHorizon.SHORT) -> Prediction:
        """预测变量"""
        hist = self.history.get(variable, [0.5])
        return self.predictor.predict(variable, hist, horizon)

    def forecast_all(self, variables: List[str], horizon: PredictionHorizon = PredictionHorizon.SHORT) -> Dict[str, Prediction]:
        return {v: self.forecast(v, horizon) for v in variables}

    def simulate_scenario(self, variables: List[str], scenario_type: ScenarioType,
                          steps: int = 10) -> Scenario:
        """模拟场景"""
        initial = {v: self.history.get(v, [0.5])[-1] for v in variables}
        return self.simulator.simulate(initial, scenario_type, steps)

    def validate_predictions(self, predictions: Dict[str, Prediction], actuals: Dict[str, float]) -> Dict:
        """验证预测"""
        pred_list = list(predictions.values())
        errors = self.validator.validate(pred_list, actuals)
        uncertainties = self.uncertainty.quantify(pred_list, actuals)
        return {
            "errors": {k: {"mae": v.mae, "mse": v.mse} for k, v in errors.items()},
            "uncertainties": uncertainties,
        }

    def run_cycle(self, current_state: Dict[str, float] = None) -> Dict:
        """运行完整预测周期"""
        self.cycle_count += 1
        current_state = current_state or {}

        # 1. 更新历史
        for var, val in current_state.items():
            self.update_history(var, val)

        # 2. 预测
        variables = list(current_state.keys())
        predictions = self.forecast_all(variables, PredictionHorizon.SHORT)

        # 3. 模拟基线场景
        baseline = self.simulate_scenario(variables, ScenarioType.BASELINE, steps=5)

        # 4. 模拟压力场景
        stress = self.simulate_scenario(variables, ScenarioType.STRESS, steps=5)

        summary = {
            "cycle": self.cycle_count,
            "predictions": {v: p.predicted_value for v, p in predictions.items()},
            "baseline_final": baseline.final_state,
            "stress_final": stress.final_state,
            "scenario_probs": {"baseline": baseline.probability, "stress": stress.probability},
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "predictor": self.predictor.get_report(),
            "extrapolator": self.extrapolator.get_report(),
            "simulator": self.simulator.get_report(),
            "uncertainty": self.uncertainty.get_report(),
            "validator": self.validator.get_report(),
            "tracked_variables": len(self.history),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_pwm_instance: Optional[PredictiveWorldModel] = None


def get_predictive_world_model() -> PredictiveWorldModel:
    global _pwm_instance
    if _pwm_instance is None:
        _pwm_instance = PredictiveWorldModel()
    return _pwm_instance


if __name__ == "__main__":
    pwm = PredictiveWorldModel()
    print(f"PredictiveWorldModel v{pwm.VERSION} initialized")
    print(f"Status: {json.dumps(pwm.get_status(), indent=2, default=str)}")
