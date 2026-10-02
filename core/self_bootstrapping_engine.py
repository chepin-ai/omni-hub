"""
OMNI-HUB v195 — SelfBootstrappingEngine
自举引擎

核心功能：
1. CapabilityExtender   — 能力扩展器
2. StructureMutator     — 结构变异器
3. DependencyResolver   — 依赖解析器
4. RollbackManager      — 回滚管理器
5. ValidationChecker    — 验证检查器
6. SelfBootstrappingEngine — 统合引擎

映射：
- 自举 = ātmātmānaṃ（自起）
- 扩展 = vistāra（广展）
- 变异 = pariṇāma（转变）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class MutationType(Enum):
    """变异类型"""
    EXTEND = "extend"
    REFACTOR = "refactor"
    MERGE = "merge"
    SPLIT = "split"
    OPTIMIZE = "optimize"


class ValidationResult(Enum):
    """验证结果"""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class Capability:
    """能力定义"""
    capability_id: str
    name: str
    inputs: List[str]
    outputs: List[str]
    complexity: float
    dependencies: List[str]


@dataclass
class Mutation:
    """变异记录"""
    mutation_id: str
    mutation_type: MutationType
    target: str
    description: str
    before_state: Dict
    after_state: Dict
    timestamp: float
    validation: ValidationResult


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 能力扩展器
# ═══════════════════════════════════════════════════════════════

class CapabilityExtender:
    """能力扩展器 — vistāra"""

    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self.extension_log: deque = deque(maxlen=500)

    def register(self, cap: Capability):
        """注册能力"""
        self.capabilities[cap.capability_id] = cap

    def extend(self, base_id: str, extension_name: str,
               new_inputs: List[str], new_outputs: List[str]) -> Optional[Capability]:
        """扩展现有能力"""
        base = self.capabilities.get(base_id)
        if not base:
            return None

        new_cap = Capability(
            capability_id=f"{base_id}_ext_{extension_name}",
            name=extension_name,
            inputs=list(set(base.inputs + new_inputs)),
            outputs=list(set(base.outputs + new_outputs)),
            complexity=min(1.0, base.complexity + 0.1),
            dependencies=list(set(base.dependencies + [base_id]))
        )
        self.capabilities[new_cap.capability_id] = new_cap
        self.extension_log.append({
            "base": base_id,
            "new": new_cap.capability_id,
            "timestamp": time.time()
        })
        return new_cap

    def find_gap(self, required_inputs: List[str],
                 required_outputs: List[str]) -> List[str]:
        """找到能力缺口"""
        available_inputs = set()
        available_outputs = set()
        for cap in self.capabilities.values():
            available_inputs.update(cap.inputs)
            available_outputs.update(cap.outputs)

        input_gaps = set(required_inputs) - available_inputs
        output_gaps = set(required_outputs) - available_outputs
        return list(input_gaps | output_gaps)

    def get_coverage(self) -> float:
        """计算能力覆盖率"""
        if not self.capabilities:
            return 0.0
        total_complexity = sum(c.complexity for c in self.capabilities.values())
        return min(1.0, total_complexity / 10.0)

    def get_report(self) -> Dict:
        return {
            "capabilities": len(self.capabilities),
            "coverage": self.get_coverage(),
            "extensions": len(self.extension_log),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 结构变异器
# ═══════════════════════════════════════════════════════════════

class StructureMutator:
    """结构变异器 — pariṇāma"""

    def __init__(self):
        self.mutations: deque = deque(maxlen=300)
        self.mutation_count = defaultdict(int)

    def mutate(self, target: str, mutation_type: MutationType,
               current_structure: Dict) -> Dict:
        """执行结构变异"""
        new_structure = dict(current_structure)

        if mutation_type == MutationType.EXTEND:
            # 添加新组件
            new_component = f"{target}_component_{self.mutation_count[target]}"
            new_structure["components"] = new_structure.get("components", []) + [new_component]

        elif mutation_type == MutationType.REFACTOR:
            # 重构：简化结构
            comps = new_structure.get("components", [])
            if len(comps) > 2:
                new_structure["components"] = comps[:len(comps)//2] + comps[len(comps)//2:]

        elif mutation_type == MutationType.MERGE:
            # 合并两个组件
            comps = new_structure.get("components", [])
            if len(comps) >= 2:
                merged = f"merged_{comps[0]}_{comps[1]}"
                new_structure["components"] = [merged] + comps[2:]

        elif mutation_type == MutationType.SPLIT:
            # 拆分一个组件
            comps = new_structure.get("components", [])
            if comps:
                split_a = f"{comps[0]}_a"
                split_b = f"{comps[0]}_b"
                new_structure["components"] = [split_a, split_b] + comps[1:]

        elif mutation_type == MutationType.OPTIMIZE:
            # 优化：提升效率标记
            new_structure["optimized"] = True
            new_structure["efficiency"] = new_structure.get("efficiency", 0.5) + 0.1

        self.mutation_count[target] += 1
        mutation = Mutation(
            mutation_id=f"mut_{target}_{self.mutation_count[target]}",
            mutation_type=mutation_type,
            target=target,
            description=f"{mutation_type.value} on {target}",
            before_state=current_structure,
            after_state=new_structure,
            timestamp=time.time(),
            validation=ValidationResult.PASS
        )
        self.mutations.append(mutation)
        return new_structure

    def get_mutation_rate(self, target: str) -> float:
        """获取目标变异率"""
        total = sum(self.mutation_count.values())
        if total == 0:
            return 0.0
        return self.mutation_count[target] / total

    def get_report(self) -> Dict:
        return {
            "total_mutations": sum(self.mutation_count.values()),
            "targets": len(self.mutation_count),
            "recent_mutations": len(self.mutations),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 依赖解析器
# ═══════════════════════════════════════════════════════════════

class DependencyResolver:
    """依赖解析器"""

    def __init__(self):
        self.dependencies: Dict[str, List[str]] = {}
        self.reverse_deps: Dict[str, List[str]] = {}

    def add(self, module: str, deps: List[str]):
        """添加依赖"""
        self.dependencies[module] = deps
        for d in deps:
            if d not in self.reverse_deps:
                self.reverse_deps[d] = []
            self.reverse_deps[d].append(module)

    def resolve(self, target: str) -> List[str]:
        """解析依赖顺序"""
        visited = set()
        result = []

        def visit(node):
            if node in visited:
                return
            visited.add(node)
            for dep in self.dependencies.get(node, []):
                visit(dep)
            result.append(node)

        visit(target)
        return result

    def find_cycles(self) -> List[List[str]]:
        """查找循环依赖"""
        cycles = []
        visited = set()
        path = []

        def dfs(node):
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for dep in self.dependencies.get(node, []):
                dfs(dep)
            path.pop()

        for node in list(self.dependencies.keys()):
            dfs(node)
        return cycles

    def get_report(self) -> Dict:
        return {
            "modules": len(self.dependencies),
            "total_dependencies": sum(len(d) for d in self.dependencies.values()),
            "cycles": len(self.find_cycles()),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 回滚管理器
# ═══════════════════════════════════════════════════════════════

class RollbackManager:
    """回滚管理器"""

    def __init__(self, max_snapshots: int = 50):
        self.snapshots: deque = deque(maxlen=max_snapshots)
        self.current_index = -1

    def snapshot(self, state: Dict, label: str = ""):
        """创建快照"""
        self.snapshots.append({
            "state": dict(state),
            "label": label,
            "timestamp": time.time()
        })
        self.current_index = len(self.snapshots) - 1

    def rollback(self, steps: int = 1) -> Optional[Dict]:
        """回滚指定步数"""
        target = self.current_index - steps
        if target < 0:
            target = 0
        if target >= len(self.snapshots):
            return None
        self.current_index = target
        return self.snapshots[target]["state"]

    def can_rollback(self) -> bool:
        return self.current_index > 0

    def get_history(self) -> List[Dict]:
        return list(self.snapshots)

    def get_report(self) -> Dict:
        return {
            "snapshots": len(self.snapshots),
            "current_index": self.current_index,
            "can_rollback": self.can_rollback(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 验证检查器
# ═══════════════════════════════════════════════════════════════

class ValidationChecker:
    """验证检查器"""

    def __init__(self):
        self.checks: deque = deque(maxlen=300)
        self.rules: List[Callable[[Dict], ValidationResult]] = []

    def add_rule(self, rule: Callable[[Dict], ValidationResult]):
        """添加验证规则"""
        self.rules.append(rule)

    def validate(self, state: Dict) -> ValidationResult:
        """验证状态"""
        worst = ValidationResult.PASS
        for rule in self.rules:
            result = rule(state)
            if result == ValidationResult.FAIL:
                worst = ValidationResult.FAIL
                break
            elif result == ValidationResult.WARNING and worst == ValidationResult.PASS:
                worst = ValidationResult.WARNING

        self.checks.append({
            "result": worst.name,
            "timestamp": time.time()
        })
        return worst

    def get_pass_rate(self) -> float:
        """获取通过率"""
        if not self.checks:
            return 1.0
        passed = sum(1 for c in self.checks if c["result"] == "PASS")
        return passed / len(self.checks)

    def get_report(self) -> Dict:
        return {
            "checks": len(self.checks),
            "rules": len(self.rules),
            "pass_rate": self.get_pass_rate(),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — SelfBootstrappingEngine v195
# ═══════════════════════════════════════════════════════════════

class SelfBootstrappingEngine:
    """
    OMNI-HUB v195 自举引擎

    ātmātmānaṃ · vistāra · pariṇāma — 自起、广展、转变
    """

    VERSION = "195.0.0"

    def __init__(self):
        self.extender = CapabilityExtender()
        self.mutator = StructureMutator()
        self.resolver = DependencyResolver()
        self.rollback = RollbackManager()
        self.validator = ValidationChecker()

        # 默认验证规则
        self.validator.add_rule(
            lambda s: ValidationResult.FAIL if s.get("health", 1.0) < 0.1 else ValidationResult.PASS
        )
        self.validator.add_rule(
            lambda s: ValidationResult.WARNING if s.get("coherence", 1.0) < 0.3 else ValidationResult.PASS
        )

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def bootstrap(self, module_states: Dict[str, Dict]) -> Dict:
        """执行自举"""
        # 1. 快照当前状态
        self.rollback.snapshot(module_states, f"cycle_{self.cycle_count}")

        # 2. 验证当前状态
        overall = {"health": 0.5, "coherence": 0.5}
        if module_states:
            overall["health"] = sum(s.get("health", 0.5) for s in module_states.values()) / len(module_states)
            overall["coherence"] = sum(s.get("coherence", 0.5) for s in module_states.values()) / len(module_states)

        validation = self.validator.validate(overall)

        # 3. 发现能力缺口
        gaps = self.extender.find_gap(
            required_inputs=["observation", "intention", "action"],
            required_outputs=["prediction", "optimization", "synthesis"]
        )

        # 4. 扩展能力（如有缺口）
        extensions = []
        if gaps:
            for gap in gaps[:3]:  # 最多扩展3个
                new_cap = self.extender.extend(
                    "base_capability", gap,
                    [gap], [f"{gap}_output"]
                )
                if new_cap:
                    extensions.append(new_cap.capability_id)

        # 5. 结构变异
        mutations = []
        mutation_types = list(MutationType)
        for module in list(module_states.keys())[:3]:
            mt = mutation_types[hash(module + str(self.cycle_count)) % len(mutation_types)]
            new_struct = self.mutator.mutate(module, mt, module_states.get(module, {}))
            mutations.append({"module": module, "type": mt.value, "result": new_struct})

        # 6. 依赖解析
        for module, state in module_states.items():
            deps = state.get("dependencies", [])
            self.resolver.add(module, deps)
        cycles = self.resolver.find_cycles()

        return {
            "validation": validation.name,
            "gaps_found": len(gaps),
            "extensions": extensions,
            "mutations": len(mutations),
            "cycles_found": len(cycles),
            "coverage": self.extender.get_coverage(),
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行自举周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.bootstrap(module_states)

        summary = {
            "cycle": self.cycle_count,
            **result,
            "snapshots": len(self.rollback.snapshots),
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "extender": self.extender.get_report(),
            "mutator": self.mutator.get_report(),
            "resolver": self.resolver.get_report(),
            "rollback": self.rollback.get_report(),
            "validator": self.validator.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_sbe_instance: Optional[SelfBootstrappingEngine] = None


def get_self_bootstrapping_engine() -> SelfBootstrappingEngine:
    global _sbe_instance
    if _sbe_instance is None:
        _sbe_instance = SelfBootstrappingEngine()
    return _sbe_instance


if __name__ == "__main__":
    sbe = SelfBootstrappingEngine()
    print(f"SelfBootstrappingEngine v{sbe.VERSION} initialized")
    print(f"Status: {json.dumps(sbe.get_status(), indent=2, default=str)}")
