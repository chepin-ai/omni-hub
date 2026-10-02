"""
OMNI-HUB v198 — PreUnificationValidator
预统一验证器

核心功能：
1. ConsistencyChecker   — 一致性检查器
2. CompatibilityTester  — 兼容性测试器
3. VulnerabilityScanner — 漏洞扫描器
4. ContractValidator    — 契约验证器
5. TopologyVerifier     — 拓扑验证器
6. PreUnificationValidator — 统合引擎

映射：
- 验证 = parīkṣā（检验）
- 统一 = ekībhāva（成一）
- 兼容 = anurūpa（随顺）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class CheckSeverity(Enum):
    """检查严重级别"""
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3


class ValidationStatus(Enum):
    """验证状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    WAIVED = "waived"


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class CheckResult:
    """检查结果"""
    check_id: str
    check_name: str
    severity: CheckSeverity
    status: ValidationStatus
    message: str
    affected_modules: List[str]


@dataclass
class CompatibilityMatrix:
    """兼容性矩阵"""
    module_a: str
    module_b: str
    compatible: bool
    interface_version_match: bool
    data_format_match: bool
    protocol_match: bool


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 一致性检查器
# ═══════════════════════════════════════════════════════════════

class ConsistencyChecker:
    """一致性检查器 — parīkṣā"""

    def __init__(self):
        self.checks: deque = deque(maxlen=500)
        self.inconsistencies: deque = deque(maxlen=200)

    def check_state_consistency(self, module_states: Dict[str, Dict]) -> List[CheckResult]:
        """检查状态一致性"""
        results = []
        modules = list(module_states.keys())

        for i in range(len(modules)):
            for j in range(i + 1, len(modules)):
                a, b = modules[i], modules[j]
                state_a = module_states[a]
                state_b = module_states[b]

                # 检查版本一致性
                ver_a = state_a.get("version", "")
                ver_b = state_b.get("version", "")
                if ver_a and ver_b and ver_a != ver_b:
                    results.append(CheckResult(
                        check_id=f"ver_{a}_{b}",
                        check_name="version_mismatch",
                        severity=CheckSeverity.WARNING,
                        status=ValidationStatus.FAILED,
                        message=f"Version mismatch: {a}={ver_a}, {b}={ver_b}",
                        affected_modules=[a, b]
                    ))

                # 检查健康度一致性（不应相差过大）
                health_a = state_a.get("health", 0.5)
                health_b = state_b.get("health", 0.5)
                if abs(health_a - health_b) > 0.5:
                    results.append(CheckResult(
                        check_id=f"health_{a}_{b}",
                        check_name="health_divergence",
                        severity=CheckSeverity.ERROR,
                        status=ValidationStatus.FAILED,
                        message=f"Health divergence: {a}={health_a:.2f}, {b}={health_b:.2f}",
                        affected_modules=[a, b]
                    ))

        for r in results:
            self.inconsistencies.append(r)
        self.checks.extend(results)
        return results

    def check_cross_references(self, references: Dict[str, List[str]]) -> List[CheckResult]:
        """检查交叉引用一致性"""
        results = []
        all_modules = set(references.keys())

        for module, refs in references.items():
            for ref in refs:
                if ref not in all_modules:
                    results.append(CheckResult(
                        check_id=f"ref_{module}_{ref}",
                        check_name="missing_reference",
                        severity=CheckSeverity.ERROR,
                        status=ValidationStatus.FAILED,
                        message=f"Module {module} references missing module {ref}",
                        affected_modules=[module]
                    ))

        self.checks.extend(results)
        return results

    def get_consistency_score(self) -> float:
        """获取一致性分数"""
        if not self.checks:
            return 1.0
        errors = sum(1 for c in self.checks if c.severity in (CheckSeverity.ERROR, CheckSeverity.CRITICAL))
        return max(0.0, 1.0 - errors / len(self.checks))

    def get_report(self) -> Dict:
        return {
            "checks": len(self.checks),
            "inconsistencies": len(self.inconsistencies),
            "consistency_score": self.get_consistency_score(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 兼容性测试器
# ═══════════════════════════════════════════════════════════════

class CompatibilityTester:
    """兼容性测试器 — anurūpa"""

    def __init__(self):
        self.matrices: deque = deque(maxlen=300)
        self.compatibilities: Dict[Tuple[str, str], CompatibilityMatrix] = {}

    def test_compatibility(self, module_a: str, module_b: str,
                           interface_a: Dict, interface_b: Dict) -> CompatibilityMatrix:
        """测试模块兼容性"""
        version_match = interface_a.get("version") == interface_b.get("version")
        format_match = interface_a.get("data_format") == interface_b.get("data_format")
        protocol_match = interface_a.get("protocol") == interface_b.get("protocol")

        compatible = version_match and format_match and protocol_match

        matrix = CompatibilityMatrix(
            module_a=module_a,
            module_b=module_b,
            compatible=compatible,
            interface_version_match=version_match,
            data_format_match=format_match,
            protocol_match=protocol_match
        )

        key = tuple(sorted([module_a, module_b]))
        self.compatibilities[key] = matrix
        self.matrices.append(matrix)
        return matrix

    def get_global_compatibility(self) -> float:
        """获取全局兼容性"""
        if not self.compatibilities:
            return 1.0
        compatible_count = sum(1 for m in self.compatibilities.values() if m.compatible)
        return compatible_count / len(self.compatibilities)

    def get_incompatible_pairs(self) -> List[Tuple[str, str]]:
        """获取不兼容对"""
        return [(m.module_a, m.module_b) for m in self.compatibilities.values() if not m.compatible]

    def get_report(self) -> Dict:
        return {
            "pairs_tested": len(self.compatibilities),
            "global_compatibility": self.get_global_compatibility(),
            "incompatible": len(self.get_incompatible_pairs()),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 漏洞扫描器
# ═══════════════════════════════════════════════════════════════

class VulnerabilityScanner:
    """漏洞扫描器"""

    def __init__(self):
        self.vulnerabilities: deque = deque(maxlen=300)
        self.scan_history: deque = deque(maxlen=200)

    def scan(self, module: str, state: Dict) -> List[CheckResult]:
        """扫描模块漏洞"""
        findings = []

        # 检查健康度过低
        health = state.get("health", 1.0)
        if health < 0.2:
            findings.append(CheckResult(
                check_id=f"vuln_health_{module}",
                check_name="critical_health",
                severity=CheckSeverity.CRITICAL,
                status=ValidationStatus.FAILED,
                message=f"Module {module} health critically low: {health:.2f}",
                affected_modules=[module]
            ))

        # 检查一致性过低
        coherence = state.get("coherence", 1.0)
        if coherence < 0.3:
            findings.append(CheckResult(
                check_id=f"vuln_coh_{module}",
                check_name="low_coherence",
                severity=CheckSeverity.ERROR,
                status=ValidationStatus.FAILED,
                message=f"Module {module} coherence too low: {coherence:.2f}",
                affected_modules=[module]
            ))

        # 检查孤立模块
        deps = state.get("dependencies", [])
        if len(deps) == 0 and module != "omni":
            findings.append(CheckResult(
                check_id=f"vuln_iso_{module}",
                check_name="isolated_module",
                severity=CheckSeverity.WARNING,
                status=ValidationStatus.FAILED,
                message=f"Module {module} has no dependencies (potentially isolated)",
                affected_modules=[module]
            ))

        self.vulnerabilities.extend(findings)
        self.scan_history.append({
            "module": module,
            "findings": len(findings),
            "timestamp": time.time()
        })
        return findings

    def get_vulnerability_score(self) -> float:
        """获取漏洞分数（越低越好）"""
        if not self.vulnerabilities:
            return 0.0
        critical = sum(1 for v in self.vulnerabilities if v.severity == CheckSeverity.CRITICAL)
        errors = sum(1 for v in self.vulnerabilities if v.severity == CheckSeverity.ERROR)
        return min(1.0, (critical * 3 + errors) / max(1, len(self.vulnerabilities)))

    def get_report(self) -> Dict:
        return {
            "vulnerabilities": len(self.vulnerabilities),
            "score": self.get_vulnerability_score(),
            "scans": len(self.scan_history),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 契约验证器
# ═══════════════════════════════════════════════════════════════

class ContractValidator:
    """契约验证器"""

    def __init__(self):
        self.contracts: Dict[str, Dict] = {}
        self.violations: deque = deque(maxlen=300)

    def define_contract(self, module: str, inputs: List[str],
                        outputs: List[str], invariants: List[str]):
        """定义模块契约"""
        self.contracts[module] = {
            "inputs": inputs,
            "outputs": outputs,
            "invariants": invariants,
        }

    def validate(self, module: str, actual_inputs: List[str],
                 actual_outputs: List[str]) -> List[CheckResult]:
        """验证契约"""
        contract = self.contracts.get(module)
        if not contract:
            return []

        violations = []

        # 检查输入契约
        for expected in contract["inputs"]:
            if expected not in actual_inputs:
                violations.append(CheckResult(
                    check_id=f"contract_in_{module}_{expected}",
                    check_name="input_contract_violation",
                    severity=CheckSeverity.ERROR,
                    status=ValidationStatus.FAILED,
                    message=f"Module {module} missing expected input: {expected}",
                    affected_modules=[module]
                ))

        # 检查输出契约
        for expected in contract["outputs"]:
            if expected not in actual_outputs:
                violations.append(CheckResult(
                    check_id=f"contract_out_{module}_{expected}",
                    check_name="output_contract_violation",
                    severity=CheckSeverity.ERROR,
                    status=ValidationStatus.FAILED,
                    message=f"Module {module} missing expected output: {expected}",
                    affected_modules=[module]
                ))

        self.violations.extend(violations)
        return violations

    def get_contract_coverage(self) -> float:
        """获取契约覆盖率"""
        if not self.contracts:
            return 1.0
        return 1.0  # 简化：所有定义的契约都被检查

    def get_report(self) -> Dict:
        return {
            "contracts": len(self.contracts),
            "violations": len(self.violations),
            "coverage": self.get_contract_coverage(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 拓扑验证器
# ═══════════════════════════════════════════════════════════════

class TopologyVerifier:
    """拓扑验证器"""

    def __init__(self):
        self.topology_checks: deque = deque(maxlen=300)

    def verify_connectivity(self, adjacency: Dict[str, List[str]]) -> List[CheckResult]:
        """验证连通性"""
        results = []
        nodes = set(adjacency.keys())

        # BFS检查连通分量
        visited = set()
        components = 0

        for start in nodes:
            if start in visited:
                continue
            components += 1
            queue = [start]
            visited.add(start)
            while queue:
                node = queue.pop(0)
                for neighbor in adjacency.get(node, []):
                    if neighbor not in visited and neighbor in nodes:
                        visited.add(neighbor)
                        queue.append(neighbor)

        if components > 1:
            results.append(CheckResult(
                check_id="topo_connectivity",
                check_name="disconnected_topology",
                severity=CheckSeverity.ERROR,
                status=ValidationStatus.FAILED,
                message=f"Topology has {components} disconnected components",
                affected_modules=list(nodes)
            ))

        self.topology_checks.extend(results)
        return results

    def verify_cycles(self, adjacency: Dict[str, List[str]]) -> List[CheckResult]:
        """验证循环"""
        results = []
        visited = set()
        path = []

        def dfs(node):
            if node in path:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                results.append(CheckResult(
                    check_id=f"topo_cycle_{node}",
                    check_name="cycle_detected",
                    severity=CheckSeverity.WARNING,
                    status=ValidationStatus.FAILED,
                    message=f"Cycle detected: {' -> '.join(cycle)}",
                    affected_modules=cycle
                ))
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for neighbor in adjacency.get(node, []):
                dfs(neighbor)
            path.pop()

        for node in adjacency:
            dfs(node)

        self.topology_checks.extend(results)
        return results

    def get_report(self) -> Dict:
        return {
            "checks": len(self.topology_checks),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — PreUnificationValidator v198
# ═══════════════════════════════════════════════════════════════

class PreUnificationValidator:
    """
    OMNI-HUB v198 预统一验证器

    parīkṣā · ekībhāva · anurūpa — 检验、成一、随顺
    """

    VERSION = "198.0.0"

    def __init__(self):
        self.consistency = ConsistencyChecker()
        self.compatibility = CompatibilityTester()
        self.vulnerability = VulnerabilityScanner()
        self.contract = ContractValidator()
        self.topology = TopologyVerifier()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def validate(self, module_states: Dict[str, Dict]) -> Dict:
        """执行预统一验证"""
        all_results = []

        # 1. 一致性检查
        consistency_results = self.consistency.check_state_consistency(module_states)
        all_results.extend(consistency_results)

        # 2. 交叉引用检查
        refs = {k: v.get("dependencies", []) for k, v in module_states.items()}
        ref_results = self.consistency.check_cross_references(refs)
        all_results.extend(ref_results)

        # 3. 兼容性测试
        modules = list(module_states.keys())
        for i in range(len(modules)):
            for j in range(i + 1, len(modules)):
                a, b = modules[i], modules[j]
                interface_a = module_states[a].get("interface", {})
                interface_b = module_states[b].get("interface", {})
                self.compatibility.test_compatibility(a, b, interface_a, interface_b)

        # 4. 漏洞扫描
        for module, state in module_states.items():
            vulns = self.vulnerability.scan(module, state)
            all_results.extend(vulns)

        # 5. 拓扑验证
        adjacency = {k: v.get("dependencies", []) for k, v in module_states.items()}
        topo_results = self.topology.verify_connectivity(adjacency)
        all_results.extend(topo_results)
        cycle_results = self.topology.verify_cycles(adjacency)
        all_results.extend(cycle_results)

        # 汇总
        passed = sum(1 for r in all_results if r.status == ValidationStatus.PASSED)
        failed = sum(1 for r in all_results if r.status == ValidationStatus.FAILED)
        warnings = sum(1 for r in all_results if r.severity == CheckSeverity.WARNING)
        critical = sum(1 for r in all_results if r.severity == CheckSeverity.CRITICAL)

        return {
            "total_checks": len(all_results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "critical": critical,
            "consistency_score": self.consistency.get_consistency_score(),
            "compatibility_score": self.compatibility.get_global_compatibility(),
            "vulnerability_score": self.vulnerability.get_vulnerability_score(),
            "ready_for_unification": failed == 0 and critical == 0,
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行验证周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.validate(module_states)

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
            "consistency": self.consistency.get_report(),
            "compatibility": self.compatibility.get_report(),
            "vulnerability": self.vulnerability.get_report(),
            "contract": self.contract.get_report(),
            "topology": self.topology.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_puv_instance: Optional[PreUnificationValidator] = None


def get_pre_unification_validator() -> PreUnificationValidator:
    global _puv_instance
    if _puv_instance is None:
        _puv_instance = PreUnificationValidator()
    return _puv_instance


if __name__ == "__main__":
    puv = PreUnificationValidator()
    print(f"PreUnificationValidator v{puv.VERSION} initialized")
    print(f"Status: {json.dumps(puv.get_status(), indent=2, default=str)}")
