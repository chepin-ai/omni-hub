"""
OMNI-HUB v198 — IntegrationVerifier
集成验证器

核心功能：
1. EndToEndTester      — 端到端测试器
2. InterfaceChecker    — 接口检查器
3. DataFlowValidator   — 数据流验证器
4. PipelineVerifier    — 流水线验证器
5. SemanticChecker     — 语义检查器
6. IntegrationVerifier — 统合引擎

映射：
- 集成 = saṃyojana（联结）
- 端到端 = anta-antara（端至端）
- 语义 = artha（义）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class TestResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    TIMEOUT = "timeout"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 端到端测试器
# ═══════════════════════════════════════════════════════════════

class EndToEndTester:
    """端到端测试器 — anta-antara"""

    def __init__(self):
        self.tests: deque = deque(maxlen=300)
        self.latencies: deque = deque(maxlen=100)

    def run_test(self, pipeline: List[str], input_data: Dict) -> Dict:
        """运行端到端测试"""
        start = time.time()
        current = dict(input_data)
        failures = []

        for i, module in enumerate(pipeline):
            # 模拟模块处理
            if hash(module + str(i)) % 20 == 0:  # 5% 失败率模拟
                failures.append(module)
                break
            # 传递数据
            current[f"processed_by_{module}"] = True

        latency = time.time() - start
        self.latencies.append(latency)

        result = {
            "pipeline": pipeline,
            "latency": latency,
            "failures": failures,
            "result": TestResult.FAIL if failures else TestResult.PASS,
        }
        self.tests.append(result)
        return result

    def get_avg_latency(self) -> float:
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    def get_report(self) -> Dict:
        return {
            "tests": len(self.tests),
            "avg_latency": self.get_avg_latency(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 接口检查器
# ═══════════════════════════════════════════════════════════════

class InterfaceChecker:
    """接口检查器"""

    def __init__(self):
        self.interface_tests: deque = deque(maxlen=300)

    def check_interface(self, module: str, expected: Dict,
                        actual: Dict) -> List[Dict]:
        """检查接口"""
        mismatches = []

        for key, expected_type in expected.items():
            if key not in actual:
                mismatches.append({
                    "module": module,
                    "field": key,
                    "issue": "missing",
                    "expected": expected_type,
                })
            elif type(actual[key]).__name__ != expected_type:
                mismatches.append({
                    "module": module,
                    "field": key,
                    "issue": "type_mismatch",
                    "expected": expected_type,
                    "actual": type(actual[key]).__name__,
                })

        self.interface_tests.extend(mismatches)
        return mismatches

    def get_report(self) -> Dict:
        return {
            "mismatches": len(self.interface_tests),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 数据流验证器
# ═══════════════════════════════════════════════════════════════

class DataFlowValidator:
    """数据流验证器"""

    def __init__(self):
        self.flow_checks: deque = deque(maxlen=300)

    def validate_flow(self, source: str, target: str,
                      data: Any, schema: Dict) -> Dict:
        """验证数据流"""
        errors = []

        if schema.get("required"):
            for field in schema["required"]:
                if isinstance(data, dict) and field not in data:
                    errors.append(f"Missing required field: {field}")

        if schema.get("types"):
            for field, expected_type in schema["types"].items():
                if isinstance(data, dict) and field in data:
                    actual = type(data[field]).__name__
                    if actual != expected_type:
                        errors.append(f"Type mismatch for {field}: expected {expected_type}, got {actual}")

        valid = len(errors) == 0
        check = {
            "source": source,
            "target": target,
            "valid": valid,
            "errors": errors,
        }
        self.flow_checks.append(check)
        return check

    def get_report(self) -> Dict:
        return {
            "flows_checked": len(self.flow_checks),
            "valid_rate": sum(1 for f in self.flow_checks if f["valid"]) / max(1, len(self.flow_checks)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 流水线验证器
# ═══════════════════════════════════════════════════════════════

class PipelineVerifier:
    """流水线验证器"""

    def __init__(self):
        self.pipeline_tests: deque = deque(maxlen=300)

    def verify_pipeline(self, stages: List[str],
                        dependencies: Dict[str, List[str]]) -> List[Dict]:
        """验证流水线"""
        issues = []

        # 检查缺失的阶段依赖
        for i, stage in enumerate(stages):
            deps = dependencies.get(stage, [])
            for dep in deps:
                if dep not in stages:
                    issues.append({
                        "stage": stage,
                        "issue": "missing_dependency",
                        "missing": dep,
                    })
                elif stages.index(dep) >= i:
                    issues.append({
                        "stage": stage,
                        "issue": "dependency_after_stage",
                        "dependency": dep,
                    })

        self.pipeline_tests.extend(issues)
        return issues

    def get_report(self) -> Dict:
        return {
            "pipelines_checked": len(self.pipeline_tests),
            "issues": len(self.pipeline_tests),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 语义检查器
# ═══════════════════════════════════════════════════════════════

class SemanticChecker:
    """语义检查器 — artha"""

    def __init__(self):
        self.semantic_checks: deque = deque(maxlen=300)

    def check_semantic_coherence(self, module_a: str, output_a: Dict,
                                  module_b: str, input_b: Dict) -> float:
        """检查语义一致性"""
        # 计算键的重叠度
        keys_a = set(output_a.keys())
        keys_b = set(input_b.keys())

        if not keys_a or not keys_b:
            return 0.0

        overlap = len(keys_a & keys_b)
        total = len(keys_a | keys_b)
        coherence = overlap / max(1, total)

        self.semantic_checks.append({
            "from": module_a,
            "to": module_b,
            "coherence": coherence,
        })
        return coherence

    def get_avg_coherence(self) -> float:
        if not self.semantic_checks:
            return 1.0
        recent = list(self.semantic_checks)[-50:]
        return sum(c["coherence"] for c in recent) / len(recent)

    def get_report(self) -> Dict:
        return {
            "checks": len(self.semantic_checks),
            "avg_coherence": self.get_avg_coherence(),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — IntegrationVerifier v198
# ═══════════════════════════════════════════════════════════════

class IntegrationVerifier:
    """
    OMNI-HUB v198 集成验证器

    saṃyojana · anta-antara · artha — 联结、端至端、义
    """

    VERSION = "198.0.0"

    def __init__(self):
        self.e2e = EndToEndTester()
        self.interface = InterfaceChecker()
        self.dataflow = DataFlowValidator()
        self.pipeline = PipelineVerifier()
        self.semantic = SemanticChecker()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def verify(self, module_states: Dict[str, Dict]) -> Dict:
        """执行集成验证"""
        results = []

        modules = list(module_states.keys())

        # 1. 端到端测试
        for i in range(min(5, len(modules))):
            pipeline = modules[i:i+3]
            if len(pipeline) >= 2:
                test = self.e2e.run_test(pipeline, {"test_id": i})
                results.append(test)

        # 2. 接口检查
        interface_mismatches = []
        for module in modules:
            expected = module_states[module].get("expected_interface", {})
            actual = module_states[module].get("actual_interface", {})
            mismatches = self.interface.check_interface(module, expected, actual)
            interface_mismatches.extend(mismatches)

        # 3. 数据流验证
        for i in range(len(modules) - 1):
            a, b = modules[i], modules[i + 1]
            data = module_states[a].get("output", {})
            schema = module_states[b].get("input_schema", {})
            self.dataflow.validate_flow(a, b, data, schema)

        # 4. 流水线验证
        deps = {k: v.get("dependencies", []) for k, v in module_states.items()}
        pipeline_issues = self.pipeline.verify_pipeline(modules, deps)

        # 5. 语义检查
        for i in range(len(modules) - 1):
            a, b = modules[i], modules[i + 1]
            output_a = module_states[a].get("output", {})
            input_b = module_states[b].get("input", {})
            self.semantic.check_semantic_coherence(a, output_a, b, input_b)

        pass_count = sum(1 for r in results if r["result"] == TestResult.PASS)
        total_tests = len(results)

        return {
            "e2e_tests": total_tests,
            "e2e_passed": pass_count,
            "interface_mismatches": len(interface_mismatches),
            "pipeline_issues": len(pipeline_issues),
            "semantic_coherence": self.semantic.get_avg_coherence(),
            "dataflow_valid_rate": self.dataflow.get_report()["valid_rate"],
            "integration_ready": pass_count == total_tests and len(interface_mismatches) == 0,
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行集成验证周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.verify(module_states)

        summary = {
            "cycle": self.cycle_count,
            **result,
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "e2e": self.e2e.get_report(),
            "interface": self.interface.get_report(),
            "dataflow": self.dataflow.get_report(),
            "pipeline": self.pipeline.get_report(),
            "semantic": self.semantic.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_iv_instance: Optional[IntegrationVerifier] = None


def get_integration_verifier() -> IntegrationVerifier:
    global _iv_instance
    if _iv_instance is None:
        _iv_instance = IntegrationVerifier()
    return _iv_instance


if __name__ == "__main__":
    iv = IntegrationVerifier()
    print(f"IntegrationVerifier v{iv.VERSION} initialized")
    print(f"Status: {json.dumps(iv.get_status(), indent=2, default=str)}")
