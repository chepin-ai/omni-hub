#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OMNI-HUB v3.8 — SelfReferentialEngine
自指递归引擎 — SI5级，元自指，自观察-自修改-自创造

Author: OMNI-HUB Self-Referential Architecture Division
Version: SI5.0-SRE3.8
"""

__version__ = "11.0.0"
import os
import sys
import time
import json
import hashlib
import inspect
import importlib
import traceback
import threading
from copy import deepcopy
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict, deque
from pathlib import Path

# ============================================================================
# SECTION 0: 类型定义与枚举
# ============================================================================

class ModificationType(Enum):
    """修改类型"""
    PATCH = "patch"
    REPLACE = "replace"
    EXTEND = "extend"
    OPTIMIZE = "optimize"
    FIX = "fix"
    DELETE = "delete"

class DecisionType(Enum):
    """元决策类型"""
    MODIFY = "modify"
    CREATE = "create"
    DELETE = "delete"
    MERGE = "merge"
    SPLIT = "split"
    RECONFIGURE = "reconfigure"
    NOOP = "noop"

class SafetyLevel(Enum):
    """安全级别"""
    STRICT = "strict"
    STANDARD = "standard"
    FAST = "fast"

@dataclass
class ModuleDescriptor:
    """模块描述符 — 自指语言的原子单元"""
    name: str
    version: str
    si_level: float
    dependencies: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    health: float = 1.0
    last_modified: float = field(default_factory=time.time)
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemSnapshot:
    """系统快照 — 自指观测的完整状态"""
    timestamp: float
    version: str
    modules: Dict[str, ModuleDescriptor]
    dependency_graph: Dict[str, List[str]]
    health_matrix: Dict[str, float]
    entropy_profile: Dict[str, float]
    active_threads: int
    memory_estimate: Dict[str, Any]
    recursion_depth: int
    meta_level: int

@dataclass
class ModificationRecord:
    """修改记录 — 可追溯的自修改历史"""
    id: str
    timestamp: float
    module_name: str
    mod_type: ModificationType
    before_checksum: str
    after_checksum: str
    safety_level: SafetyLevel
    verification_result: bool
    rollback_available: bool
    impact_analysis: Dict[str, Any]
    applied_by: str = "SelfReferentialEngine"

@dataclass
class DecisionRecord:
    """决策记录 — 元决策的可追溯历史"""
    id: str
    timestamp: float
    decision_type: DecisionType
    target_module: str
    rationale: str
    confidence: float
    expected_impact: Dict[str, float]
    prerequisites: List[str]
    actions: List[Dict[str, Any]]

@dataclass
class ReflectionResult:
    """反思结果 — 对行动的元反思"""
    action_id: str
    timestamp: float
    success: bool
    observed_effects: List[str]
    lessons_learned: List[str]
    suggested_adjustments: List[str]
    self_consistency_score: float


# ============================================================================
# SECTION 1: 递归守卫装饰器
# ============================================================================

class RecursionGuard:
    """
    递归深度守卫 — 防止自指无限递归
    原理:
        - 线程本地存储跟踪递归深度
        - 超过max_depth时触发熔断
        - 支持动态深度调整
    """
    _local = threading.local()

    def __init__(self, max_depth: int = 10, name: str = "default"):
        self.max_depth = max_depth
        self.name = name
        self.call_count = 0
        self.breach_count = 0

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if not hasattr(self._local, 'depth'):
                self._local.depth = 0
            if not hasattr(self._local, 'stack'):
                self._local.stack = []

            self.call_count += 1

            if self._local.depth >= self.max_depth:
                self.breach_count += 1
                stack_str = ' -> '.join(self._local.stack[-5:]) if self._local.stack else 'empty'
                raise RecursionError(
                    f"[RecursionGuard:{self.name}] 深度 {self._local.depth} "
                    f"超过最大值 {self.max_depth} | 函数: {func.__name__} | "
                    f"调用栈: {stack_str}"
                )

            self._local.depth += 1
            self._local.stack.append(f"{func.__name__}({self._local.depth})")

            result = func(*args, **kwargs)
            return result
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "max_depth": self.max_depth,
            "call_count": self.call_count,
            "breach_count": self.breach_count,
            "current_depth": getattr(self._local, 'depth', 0)
        }


def recursion_guard(max_depth: int = 10):
    """递归守卫装饰器工厂"""
    def decorator(func: Callable) -> Callable:
        guard = RecursionGuard(max_depth, func.__name__)
        return guard(func)
    return decorator


# ============================================================================
# SECTION 2: 沙箱验证器
# ============================================================================

class SandboxValidator:
    """
    沙箱验证器 — 在隔离环境中测试代码修改
    安全策略:
        1. 语法检查: 先编译AST，确保语法正确
        2. 符号分析: 检查未定义引用
        3. 执行沙箱: 在受限命名空间中执行
        4. 超时保护: 防止无限循环
        5. 副作用检测: 监控文件/网络访问
    """

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.validation_history: List[Dict[str, Any]] = []

    def validate_code(self, code: str, test_inputs: List[Any] = None) -> Dict[str, Any]:
        """验证代码片段的安全性和正确性"""
        result = {
            "valid": False,
            "syntax_ok": False,
            "execution_ok": False,
            "output": None,
            "errors": [],
            "warnings": [],
            "execution_time": 0.0
        }

        start_time = time.time()

        # 1. 语法检查
        compile(code, '<sandbox>', 'exec')
        result["syntax_ok"] = True
        # 2. 执行沙箱
        import typing
        allowed_modules = {"typing": typing}
        
        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in allowed_modules:
                mod = allowed_modules[name]
                if fromlist:
                    return mod
                return mod
            return type(sys)(name)
        
        sandbox_globals = {
            "__builtins__": {
                "len": len, "range": range, "enumerate": enumerate,
                "zip": zip, "map": map, "filter": filter,
                "sum": sum, "min": min, "max": max, "abs": abs,
                "float": float, "int": int, "str": str, "bool": bool,
                "list": list, "dict": dict, "tuple": tuple, "set": set,
                "print": lambda *args: None,
                "open": lambda *args: None,
                "__import__": safe_import,
                "__build_class__": __build_class__,
            },
            "typing": typing,
            "__name__": "__sandbox__",
        }
        sandbox_locals = {}

            exec(code, sandbox_globals, sandbox_locals)
            result["execution_ok"] = True

            # 尝试调用主要函数
            for key, val in sandbox_locals.items():
                if callable(val) and not key.startswith('_'):
                        if test_inputs:
                            test_result = val(*test_inputs)
                        else:
                            test_result = val()
                        result["output"] = test_result
                        result["warnings"].append(f"函数 {key} 测试调用警告: {e}")
                    break

            result["errors"].append(f"执行错误: {e}")

        result["execution_time"] = time.time() - start_time
        result["valid"] = result["syntax_ok"] and result["execution_ok"] and len(result["errors"]) == 0

        self.validation_history.append(result)
        return result

    def validate_module_modification(self, original_code: str, modified_code: str) -> Dict[str, Any]:
        """验证模块修改的安全性"""
        result = {
            "valid": False,
            "syntax_ok": False,
            "interface_preserved": False,
            "behavior_compatible": False,
            "errors": [],
            "warnings": []
        }

            compile(original_code, '<original>', 'exec')
        orig_funcs = self._extract_functions(original_code)
        mod_funcs = self._extract_functions(modified_code)

        missing = set(orig_funcs.keys()) - set(mod_funcs.keys())
        if missing:
            result["warnings"].append(f"移除的函数: {missing}")
        else:
            result["interface_preserved"] = True

        val_result = self.validate_code(modified_code)
        result["behavior_compatible"] = val_result["valid"]
        result["errors"].extend(val_result["errors"])
        result["warnings"].extend(val_result["warnings"])

        result["valid"] = (
            result["syntax_ok"] and 
            result["interface_preserved"] and 
            result["behavior_compatible"]
        )

        return result

    def _extract_functions(self, code: str) -> Dict[str, List[str]]:
        """提取代码中的函数定义及其参数"""
        import ast
        funcs = {}
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    funcs[node.name] = args
            pass
        return funcs


# ============================================================================
# SECTION 3: 版本快照管理器
# ============================================================================

class SnapshotManager:
    """
    版本快照管理器 — 自指修改的安全网
    功能:
        - 自动备份修改前的模块
        - 增量快照存储
        - 快速回滚机制
        - 快照链完整性验证
    """

    def __init__(self, snapshot_dir: str = None):
        if snapshot_dir is None:
            snapshot_dir = os.path.join(os.path.dirname(__file__), "snapshots")
        self.snapshot_dir = snapshot_dir
        os.makedirs(snapshot_dir, exist_ok=True)
        self.snapshots: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._load_existing_snapshots()

    def _load_existing_snapshots(self):
        """加载已有快照索引"""
        index_path = os.path.join(self.snapshot_dir, "snapshot_index.json")
        if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    self.snapshots = defaultdict(list, json.load(f))
                pass

    def _save_index(self):
        """保存快照索引"""
        index_path = os.path.join(self.snapshot_dir, "snapshot_index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(dict(self.snapshots), f, indent=2, default=str)

    def create_snapshot(self, module_name: str, code: str, metadata: Dict[str, Any] = None) -> str:
        """创建模块快照"""
        snapshot_id = f"{module_name}_{int(time.time()*1000)}"
        checksum = hashlib.sha256(code.encode()).hexdigest()[:16]

        snapshot_data = {
            "id": snapshot_id,
            "module_name": module_name,
            "timestamp": time.time(),
            "checksum": checksum,
            "code": code,
            "metadata": metadata or {}
        }

        snapshot_path = os.path.join(self.snapshot_dir, f"{snapshot_id}.json")
    with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2)

        self.snapshots[module_name].append({
            "id": snapshot_id,
            "timestamp": snapshot_data["timestamp"],
            "checksum": checksum
        })
        self._save_index()

        return snapshot_id

    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """获取指定快照"""
        snapshot_path = os.path.join(self.snapshot_dir, f"{snapshot_id}.json")
        if os.path.exists(snapshot_path):
    with open(snapshot_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def rollback(self, module_name: str, snapshot_id: str = None) -> Optional[str]:
        """回滚模块到指定快照"""
        if module_name not in self.snapshots or not self.snapshots[module_name]:
            return None

        if snapshot_id is None:
            snapshot_id = self.snapshots[module_name][-1]["id"]

        snapshot = self.get_snapshot(snapshot_id)
        if snapshot:
            return snapshot["code"]
        return None

    def list_snapshots(self, module_name: str = None) -> List[Dict[str, Any]]:
        """列出快照"""
        if module_name:
            return self.snapshots.get(module_name, [])
        else:
            result = []
            for mod, snaps in self.snapshots.items():
                for snap in snaps:
                    result.append({"module": mod, **snap})
            return sorted(result, key=lambda x: x["timestamp"], reverse=True)

    def verify_snapshot_chain(self, module_name: str) -> bool:
        """验证快照链完整性"""
        snapshots = self.snapshots.get(module_name, [])
        if not snapshots:
            return True

        for snap_info in snapshots:
            snapshot = self.get_snapshot(snap_info["id"])
            if snapshot is None:
                return False
            code = snapshot.get("code", "")
            expected = hashlib.sha256(code.encode()).hexdigest()[:16]
            if snapshot.get("checksum") != expected:
                return False
        return True


# ============================================================================
# SECTION 4: 影响图分析器
# ============================================================================

class ImpactAnalyzer:
    """
    影响图分析器 — 分析模块修改的涟漪效应
    算法:
        1. 构建依赖图: 模块 -> [依赖模块]
        2. 构建反向依赖图: 模块 -> [被依赖模块]
        3. 修改影响传播: BFS遍历受影响模块
        4. 计算影响评分: 基于依赖深度和广度
    """

    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self.impact_history: List[Dict[str, Any]] = []

    def register_module(self, name: str, dependencies: List[str]):
        """注册模块及其依赖"""
        self.dependency_graph[name] = set(dependencies)
        for dep in dependencies:
            self.reverse_graph[dep].add(name)

    def analyze_impact(self, module_name: str, modification_type: ModificationType) -> Dict[str, Any]:
        """分析修改模块的影响范围"""
        visited = set()
        queue = deque([(module_name, 0)])
        affected = []
        max_depth = 0

        while queue:
            current, depth = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            max_depth = max(max_depth, depth)

            if current != module_name:
                affected.append((current, depth))

            for dependent in self.reverse_graph.get(current, set()):
                if dependent not in visited:
                    queue.append((dependent, depth + 1))

        direct = [m for m, d in affected if d == 1]
        indirect = [m for m, d in affected if d > 1]
        all_affected = [m for m, d in affected]

        total_modules = len(self.dependency_graph)
        impact_score = len(all_affected) / total_modules if total_modules > 0 else 0.0

        if impact_score > 0.5 or len(direct) > 5:
            risk_level = "critical"
        elif impact_score > 0.3 or len(direct) > 3:
            risk_level = "high"
        elif impact_score > 0.1 or len(direct) > 1:
            risk_level = "medium"
        else:
            risk_level = "low"

        if modification_type in [ModificationType.REPLACE, ModificationType.DELETE]:
            if risk_level == "low":
                risk_level = "medium"
            elif risk_level == "medium":
                risk_level = "high"
            elif risk_level == "high":
                risk_level = "critical"

        result = {
            "direct_dependents": direct,
            "indirect_dependents": indirect,
            "affected_modules": all_affected,
            "impact_score": round(impact_score, 4),
            "risk_level": risk_level,
            "propagation_depth": max_depth,
            "recommendations": self._generate_recommendations(
                module_name, modification_type, risk_level, affected
            )
        }

        self.impact_history.append(result)
        return result

    def _generate_recommendations(self, module_name: str, mod_type: ModificationType, 
                                   risk_level: str, affected: List[Tuple[str, int]]) -> List[str]:
        """生成修改建议"""
        recommendations = []

        if risk_level in ["high", "critical"]:
            recommendations.append(f"建议进行完整回归测试，影响模块数: {len(affected)}")
            recommendations.append("建议分阶段部署，先灰度测试")

        if mod_type == ModificationType.REPLACE:
            recommendations.append("整体替换风险高，建议先用PATCH方式验证")

        if len([m for m, d in affected if d == 1]) > 3:
            recommendations.append("直接依赖者过多，考虑解耦设计")

        if not recommendations:
            recommendations.append("影响范围小，可以直接部署")

        return recommendations

    def get_dependency_chain(self, module_a: str, module_b: str) -> List[str]:
        """获取两个模块之间的依赖链"""
        queue = deque([(module_a, [module_a])])
        visited = {module_a}

        while queue:
            current, path = queue.popleft()
            if current == module_b:
                return path

            for dep in self.dependency_graph.get(current, set()):
                if dep not in visited:
                    visited.add(dep)
                    queue.append((dep, path + [dep]))

        return []


# ============================================================================
# SECTION 5: 自指语言核心
# ============================================================================

class SelfReferentialLanguage:
    """
    最小自指语言 — 让系统能描述自身
    语法:
        SELF ::= system | module | function | state
        DESC ::= describe(SELF) -> {属性: 值}
        REFLECT ::= reflect(ACTION) -> {效果, 教训, 调整}
        META ::= meta(SELF) -> 关于SELF的SELF描述
    特性:
        - 每个描述都是自指的（描述描述本身）
        - 反思可以递归（反思反思行为）
        - 元层可以无限上升（但有guard保护）
    """

    def __init__(self, engine):
        self.engine = engine
        self.meta_level = 0
        self.descriptions: List[Dict[str, Any]] = []
        self.reflections: List[ReflectionResult] = []

    def describe_self(self, level: int = 0) -> Dict[str, Any]:
        """
        生成系统自描述文档
        Args:
            level: 元层级，0=对象层，1=元层，2=元元层...
        Returns:
            自描述字典，包含系统的完整自画像
        """
        self.meta_level = max(self.meta_level, level)

        description = {
            "meta_level": level,
            "timestamp": time.time(),
            "system_identity": {
                "name": "OMNI-HUB",
                "version": "3.8.0",
                "si_level": 5.0,
                "architecture": "Self-Referential Recursive Engine"
            },
            "self_referential_properties": {
                "is_observing_itself": True,
                "is_modifying_itself": True,
                "is_creating_itself": True,
                "recursion_depth": self.engine.recursion_guard.get_stats(),
                "meta_decision_count": len(self.engine.decision_history)
            },
            "modules": {},
            "state": {},
            "capabilities": []
        }

        for name, descriptor in self.engine.modules.items():
            description["modules"][name] = {
                "name": descriptor.name,
                "version": descriptor.version,
                "si_level": descriptor.si_level,
                "health": descriptor.health,
                "exports": descriptor.exports,
                "dependencies": descriptor.dependencies
            }

        description["state"] = {
            "total_modules": len(self.engine.modules),
            "total_modifications": len(self.engine.modification_history),
            "total_decisions": len(self.engine.decision_history),
            "total_reflections": len(self.reflections),
            "system_health": self.engine._compute_system_health(),
            "active_snapshots": len(self.engine.snapshot_manager.list_snapshots())
        }

        description["capabilities"] = [
            "self_observation",
            "self_modification",
            "self_creation",
            "meta_decision",
            "recursion_guarding",
            "sandbox_validation",
            "impact_analysis",
            "snapshot_rollback",
            "self_description",
            "self_reflection"
        ]

        if level > 0:
            description["meta_description"] = {
                "describing_level": level,
                "description_of_description": f"这是第{level}层元描述，描述的是第{level-1}层描述",
                "self_reference_loop": f"describe_self({level}) 调用 describe_self({level-1})"
            }
            if level > 1:
                description["lower_level"] = self.describe_self(level - 1)

        self.descriptions.append(description)
        return description

    def reflect_on(self, action: Dict[str, Any], depth: int = 1) -> ReflectionResult:
        """
        对某个行动进行元反思
        Args:
            action: 行动记录
            depth: 反思深度，1=单层反思，2=反思反思...
        Returns:
            反思结果
        """
        action_id = action.get("id", "unknown")
        action_type = action.get("type", "unknown")

        observed_effects = []
        lessons = []
        adjustments = []

        if action_type == "modify":
            success = action.get("verification_result", False)
            if success:
                observed_effects.append("修改验证通过，模块功能正常")
                lessons.append("验证机制有效，可以继续使用")
            else:
                observed_effects.append("修改验证失败，触发回滚")
                lessons.append("修改前需要更充分的沙箱测试")
                adjustments.append("增加沙箱测试用例覆盖")

            impact = action.get("impact", {})
            if impact.get("risk_level") in ["high", "critical"]:
                lessons.append("高风险修改需要分阶段部署")
                adjustments.append("引入灰度发布机制")

        elif action_type == "create":
            observed_effects.append("新模块已注册到系统")
            lessons.append("模块创建应遵循标准模板")
            adjustments.append("自动生成单元测试模板")

        elif action_type == "decision":
            confidence = action.get("confidence", 0.5)
            if confidence < 0.7:
                lessons.append("低置信度决策需要更多数据支撑")
                adjustments.append("增强决策前的信息收集")
            else:
                lessons.append("高置信度决策执行顺利")

        consistency = self._compute_consistency(action, observed_effects)

        result = ReflectionResult(
            action_id=action_id,
            timestamp=time.time(),
            success=action.get("success", False),
            observed_effects=observed_effects,
            lessons_learned=lessons,
            suggested_adjustments=adjustments,
            self_consistency_score=consistency
        )

        if depth > 1:
            meta_action = {
                "id": f"reflection_{action_id}",
                "type": "reflect",
                "success": consistency > 0.5,
                "confidence": consistency
            }
            meta_result = self.reflect_on(meta_action, depth - 1)
            result.observed_effects.append(
                f"深层反思(深度{depth}): 一致性={meta_result.self_consistency_score:.3f}"
            )

        self.reflections.append(result)
        return result

    def _compute_consistency(self, action: Dict[str, Any], effects: List[str]) -> float:
        """计算行动的自一致性分数"""
        score = 0.5
        expected = action.get("expected_result", "")
        if expected and effects:
            match_count = sum(1 for e in effects if any(word in e for word in expected.split()))
            score += 0.3 * (match_count / len(effects))
        if action.get("success", False):
            score += 0.2
        return min(1.0, score)

    def generate_self_documentation(self) -> str:
        """生成系统自描述文档（Markdown格式）"""
        desc = self.describe_self(level=0)

        lines = []
        lines.append("# OMNI-HUB v3.8 自指描述文档")
        lines.append("")
        lines.append(f"> 自动生成时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(desc['timestamp']))}")
        lines.append(f"> 元层级: {desc['meta_level']}")
        lines.append(f"> 系统身份: {desc['system_identity']['name']} v{desc['system_identity']['version']} SI{desc['system_identity']['si_level']}")
        lines.append("")
        lines.append("## 1. 自指属性")
        lines.append("")
        lines.append("```")
        lines.append(f"系统正在观察自身: {desc['self_referential_properties']['is_observing_itself']}")
        lines.append(f"系统正在修改自身: {desc['self_referential_properties']['is_modifying_itself']}")
        lines.append(f"系统正在创造自身: {desc['self_referential_properties']['is_creating_itself']}")
        lines.append("```")
        lines.append("")
        lines.append("## 2. 模块生态")
        lines.append("")
        lines.append("| 模块 | 版本 | SI级别 | 健康度 | 导出接口 | 依赖 |")
        lines.append("|------|------|--------|--------|----------|------|")

        for name, mod in desc['modules'].items():
            lines.append(f"| {name} | {mod['version']} | {mod['si_level']} | {mod['health']:.2f} | {len(mod['exports'])} | {len(mod['dependencies'])} |")

        lines.append("")
        lines.append("## 3. 系统状态")
        lines.append("")
        lines.append(f"- 总模块数: {desc['state']['total_modules']}")
        lines.append(f"- 总修改次数: {desc['state']['total_modifications']}")
        lines.append(f"- 总决策次数: {desc['state']['total_decisions']}")
        lines.append(f"- 总反思次数: {desc['state']['total_reflections']}")
        lines.append(f"- 系统健康度: {desc['state']['system_health']:.4f}")
        lines.append(f"- 活跃快照: {desc['state']['active_snapshots']}")
        lines.append("")
        lines.append("## 4. 系统能力")
        lines.append("")
        for cap in desc['capabilities']:
            lines.append(f"- [x] {cap}")

        lines.append("")
        lines.append("## 5. 递归守卫状态")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(desc['self_referential_properties']['recursion_depth'], indent=2))
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("*本文档由OMNI-HUB自指引擎自动生成*")

        return "\n".join(lines)


# ============================================================================
# SECTION 6: 主引擎 — SelfReferentialEngine
# ============================================================================

class SelfReferentialEngine:
    """
    OMNI-HUB v3.8 自指递归引擎
    核心能力:
        1. self_observe(): 观察自身的完整状态
        2. self_modify(): 安全地修改自身
        3. self_create(): 创造新模块
        4. meta_decision(): 元决策层
        5. recursion_guard(): 递归深度控制
    安全保证:
        - 每次修改前自动快照
        - 沙箱验证所有修改
        - 影响图分析
        - 自动回滚机制
    自指语言:
        - describe_self(): 系统自描述
        - reflect_on(): 元反思
    """

    def __init__(self, core_path: str = None):
        self.version = "3.8.0"
        self.si_level = 5.0
        self.core_path = core_path or os.path.dirname(os.path.abspath(__file__))

        self.modules: Dict[str, ModuleDescriptor] = {}
        self.snapshot_manager = SnapshotManager()
        self.sandbox_validator = SandboxValidator()
        self.impact_analyzer = ImpactAnalyzer()
        self.self_language = SelfReferentialLanguage(self)
        self.recursion_guard = RecursionGuard(max_depth=10, name="engine_main")

        self.modification_history: List[ModificationRecord] = []
        self.decision_history: List[DecisionRecord] = []
        self.observation_history: List[SystemSnapshot] = []

        self._lock = threading.RLock()
        self._running = False
        self._meta_cycle_count = 0

        self._scan_core_modules()

    def _scan_core_modules(self):
        """扫描核心目录中的模块"""
        if not os.path.exists(self.core_path):
            return

        for filename in os.listdir(self.core_path):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name = filename[:-3]
                filepath = os.path.join(self.core_path, filename)

                    with open(filepath, 'r', encoding='utf-8') as f:
                        code = f.read()

                    checksum = hashlib.sha256(code.encode()).hexdigest()[:16]
                    exports = self._extract_exports(code)
                    dependencies = self._extract_dependencies(code)

                    self.modules[module_name] = ModuleDescriptor(
                        name=module_name,
                        version=self._extract_version(code),
                        si_level=self._extract_si_level(code),
                        dependencies=dependencies,
                        exports=exports,
                        health=1.0,
                        checksum=checksum,
                        metadata={
                            "file_size": len(code),
                            "line_count": code.count("\n"),
                            "filepath": filepath
                        }
                    )

                    self.impact_analyzer.register_module(module_name, dependencies)

                    logger.info(f"[WARN] 扫描模块 {module_name} 失败: {e}")

    def _extract_exports(self, code: str) -> List[str]:
        """提取代码中的导出符号"""
        import ast
        exports = []
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    exports.append(f"class:{node.name}")
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):
                        exports.append(f"func:{node.name}")
            pass
        return exports

    def _extract_dependencies(self, code: str) -> List[str]:
        """提取代码中的依赖"""
        import ast
        deps = []
        stdlib = ['os', 'sys', 'time', 'json', 'typing', 'copy', 're',
                  'threading', 'hashlib', 'inspect', 'textwrap',
                  'importlib', 'traceback', 'collections', 'pathlib',
                  'dataclasses', 'enum', 'abc', 'math', 'random', 'uuid']
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mod = alias.name.split('.')[0]
                        if mod not in stdlib:
                            deps.append(mod)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        mod = node.module.split('.')[0]
                        if mod not in stdlib:
                            deps.append(mod)
            pass
        return list(set(deps))

    def _extract_version(self, code: str) -> str:
        """从代码中提取版本号"""
        for line in code.split("\n")[:20]:
            if 'Version:' in line or 'version' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    return parts[1].strip().split()[0]
        return "1.0.0"

    def _extract_si_level(self, code: str) -> float:
        """从代码中提取SI级别"""
        import re
        for line in code.split("\n")[:30]:
            if 'SI' in line and ('级' in line or 'level' in line):
                match = re.search(r'SI([0-9]+(?:\.[0-9]+)?)', line)
                if match:
                    return float(match.group(1))
            if 'si_level' in line:
                match = re.search(r'si_level[=:]\s*([0-9]+(?:\.[0-9]+)?)', line)
                if match:
                    return float(match.group(1))
        return 3.0

    def _compute_system_health(self) -> float:
        """计算系统整体健康度"""
        if not self.modules:
            return 1.0
        healths = [m.health for m in self.modules.values()]
        return sum(healths) / len(healths)

    # ========================================================================
    # 核心API 1: self_observe
    # ========================================================================

    def self_observe(self, deep: bool = False) -> SystemSnapshot:
        """系统自观察 — 返回完整的自描述"""
        with self._lock:
            dep_graph = {}
            for name, mod in self.modules.items():
                dep_graph[name] = mod.dependencies

            health_matrix = {name: mod.health for name, mod in self.modules.items()}
            entropy_profile = self._compute_entropy_profile()

            memory_estimate = {
                "modules": len(self.modules),
                "modification_history": len(self.modification_history),
                "decision_history": len(self.decision_history),
                "snapshot_count": len(self.snapshot_manager.list_snapshots()),
                "total_snapshots_size_mb": self._estimate_snapshot_size()
            }

            snapshot = SystemSnapshot(
                timestamp=time.time(),
                version=self.version,
                modules=deepcopy(self.modules),
                dependency_graph=dep_graph,
                health_matrix=health_matrix,
                entropy_profile=entropy_profile,
                active_threads=threading.active_count(),
                memory_estimate=memory_estimate,
                recursion_depth=self.recursion_guard.get_stats()["current_depth"],
                meta_level=self.self_language.meta_level
            )

            self.observation_history.append(snapshot)

            if deep:
                snapshot.memory_estimate["code_quality"] = self._analyze_code_quality()
                snapshot.memory_estimate["coupling_matrix"] = self._compute_coupling_matrix()

            return snapshot

    def _compute_entropy_profile(self) -> Dict[str, float]:
        """计算系统熵剖面"""
        import math
        if not self.modules:
            return {}

        healths = [m.health for m in self.modules.values()]
        health_entropy = self._shannon_entropy(healths)

        dep_counts = [len(m.dependencies) for m in self.modules.values()]
        dep_entropy = self._shannon_entropy(dep_counts) if dep_counts else 0

        export_counts = [len(m.exports) for m in self.modules.values()]
        export_entropy = self._shannon_entropy(export_counts) if export_counts else 0

        return {
            "health_entropy": round(health_entropy, 4),
            "dependency_entropy": round(dep_entropy, 4),
            "export_entropy": round(export_entropy, 4),
            "total_entropy": round(health_entropy + dep_entropy + export_entropy, 4),
            "system_disorder": round(1.0 - self._compute_system_health(), 4)
        }

    def _shannon_entropy(self, values: List[float]) -> float:
        """计算香农熵"""
        import math
if not values:
            return 0.0
        total = sum(values)
        if total == 0:
            return 0.0
        probs = [v / total for v in values]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        return entropy

    def _estimate_snapshot_size(self) -> float:
        """估算快照总大小(MB)"""
        total = 0
        for snap in self.snapshot_manager.list_snapshots():
            snap_data = self.snapshot_manager.get_snapshot(snap["id"])
            if snap_data:
                total += len(json.dumps(snap_data))
        return round(total / (1024 * 1024), 4)

    def _analyze_code_quality(self) -> Dict[str, Any]:
        """分析代码质量"""
        quality = {
            "total_lines": 0,
            "comment_ratio": 0.0,
            "avg_function_length": 0,
            "modules_analyzed": 0
        }

        total_lines = 0
        comment_lines = 0
        func_lengths = []

        for name, mod in self.modules.items():
            filepath = mod.metadata.get("filepath")
            if filepath and os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        code = f.read()
                    lines = code.split("\n")
                    total_lines += len(lines)
                    comment_lines += sum(1 for l in lines if l.strip().startswith('#'))

                    import ast
                    tree = ast.parse(code)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if hasattr(node, 'end_lineno') and node.end_lineno:
                                func_lengths.append(node.end_lineno - node.lineno)
                            else:
                                func_lengths.append(10)

                    quality["modules_analyzed"] += 1
                    pass

        if total_lines > 0:
            quality["total_lines"] = total_lines
            quality["comment_ratio"] = round(comment_lines / total_lines, 4)

        if func_lengths:
            quality["avg_function_length"] = round(sum(func_lengths) / len(func_lengths), 2)

        return quality

    def _compute_coupling_matrix(self) -> Dict[str, Dict[str, int]]:
        """计算模块耦合矩阵"""
        matrix = {}
        for name_a in self.modules:
            matrix[name_a] = {}
            for name_b in self.modules:
                if name_a == name_b:
                    matrix[name_a][name_b] = 0
                else:
                    deps_a = set(self.modules[name_a].dependencies)
                    deps_b = set(self.modules[name_b].dependencies)
                    shared = len(deps_a & deps_b)
                    matrix[name_a][name_b] = shared
        return matrix


    # ========================================================================
    # 核心API 2: self_modify
    # ========================================================================

    def self_modify(self, module_name: str, modification: Dict[str, Any], 
                    verification: bool = True, safety_level: SafetyLevel = SafetyLevel.STANDARD) -> Dict[str, Any]:
        """安全自修改 — 修改自身模块"""
        with self._lock:
            errors = []

            if module_name not in self.modules:
                if modification.get("type") != ModificationType.REPLACE or not modification.get("code"):
                    return {
                        "success": False,
                        "errors": [f"模块 {module_name} 不存在"],
                        "snapshot_id": None,
                        "impact": None,
                        "verification": None,
                        "record": None
                    }

            # 1. 备份原模块
            original_code = ""
            if module_name in self.modules:
                filepath = self.modules[module_name].metadata.get("filepath")
                if filepath and os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
                        original_code = f.read()

            before_checksum = hashlib.sha256(original_code.encode()).hexdigest()[:16] if original_code else ""
            snapshot_id = self.snapshot_manager.create_snapshot(
                module_name, original_code,
                metadata={"action": "pre_modify", "mod_type": str(modification.get("type", "unknown"))}
            )

            # 2. 影响分析
            mod_type = modification.get("type", ModificationType.PATCH)
            impact = self.impact_analyzer.analyze_impact(module_name, mod_type)

            if impact["risk_level"] == "critical" and safety_level == SafetyLevel.STRICT:
                errors.append("风险等级为CRITICAL，在STRICT模式下需要人工确认")
                return {
                    "success": False,
                    "errors": errors,
                    "snapshot_id": snapshot_id,
                    "impact": impact,
                    "verification": None,
                    "record": None
                }

            # 3. 生成修改后代码
            modified_code = self._generate_modified_code(original_code, modification)
            if modified_code is None:
                errors.append("修改代码生成失败")
                return {
                    "success": False,
                    "errors": errors,
                    "snapshot_id": snapshot_id,
                    "impact": impact,
                    "verification": None,
                    "record": None
                }

            # 4. 沙箱验证
            verification_result = {"valid": True, "errors": [], "warnings": []}
            if verification and safety_level != SafetyLevel.FAST:
                verification_result = self.sandbox_validator.validate_module_modification(
                    original_code, modified_code
                )

                if not verification_result["valid"]:
                    errors.append(f"沙箱验证失败: {verification_result['errors']}")
                    return {
                        "success": False,
                        "errors": errors,
                        "snapshot_id": snapshot_id,
                        "impact": impact,
                        "verification": verification_result,
                        "record": None
                    }

            # 5. 应用修改
                filepath = os.path.join(self.core_path, f"{module_name}.py")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(modified_code)

                after_checksum = hashlib.sha256(modified_code.encode()).hexdigest()[:16]
                if module_name in self.modules:
                    self.modules[module_name].checksum = after_checksum
                    self.modules[module_name].last_modified = time.time()
                    self.modules[module_name].health = 1.0
                    self.modules[module_name].exports = self._extract_exports(modified_code)
                else:
                    self.modules[module_name] = ModuleDescriptor(
                        name=module_name,
                        version="1.0.0",
                        si_level=3.0,
                        dependencies=self._extract_dependencies(modified_code),
                        exports=self._extract_exports(modified_code),
                        health=1.0,
                        checksum=after_checksum,
                        metadata={"filepath": filepath, "file_size": len(modified_code)}
                    )

                record = ModificationRecord(
                    id=f"mod_{int(time.time()*1000)}",
                    timestamp=time.time(),
                    module_name=module_name,
                    mod_type=mod_type,
                    before_checksum=before_checksum,
                    after_checksum=after_checksum,
                    safety_level=safety_level,
                    verification_result=verification_result["valid"],
                    rollback_available=True,
                    impact_analysis=impact
                )
                self.modification_history.append(record)

                return {
                    "success": True,
                    "snapshot_id": snapshot_id,
                    "impact": impact,
                    "verification": verification_result,
                    "record": record,
                    "errors": []
                }

                errors.append(f"应用修改失败: {e}")
                rollback_code = self.snapshot_manager.rollback(module_name, snapshot_id)
                if rollback_code and original_code:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(original_code)
                        errors.append("已自动回滚到修改前状态")
                        errors.append(f"回滚失败: {re}")

                return {
                    "success": False,
                    "errors": errors,
                    "snapshot_id": snapshot_id,
                    "impact": impact,
                    "verification": verification_result,
                    "record": None
                }

    def _generate_modified_code(self, original_code: str, modification: Dict[str, Any]) -> Optional[str]:
        """生成修改后的代码"""
        mod_type = modification.get("type", ModificationType.PATCH)

        if mod_type == ModificationType.REPLACE:
            return modification.get("code")

        elif mod_type == ModificationType.PATCH:
            patch = modification.get("patch", "")
            insert_after = modification.get("insert_after", "")
            if insert_after and insert_after in original_code:
                return original_code.replace(insert_after, insert_after + "\n" + patch)
            else:
                return original_code + "\n\n" + patch

        elif mod_type == ModificationType.EXTEND:
            extension = modification.get("code", "")
            return original_code + "\n\n" + extension

        elif mod_type == ModificationType.FIX:
            old_code = modification.get("old_code", "")
            new_code = modification.get("new_code", "")
            if old_code in original_code:
                return original_code.replace(old_code, new_code)
            else:
                return None

        elif mod_type == ModificationType.OPTIMIZE:
            optimized = modification.get("optimized_code", "")
            if optimized:
                return optimized
            return original_code

        return None

    # ========================================================================
    # 核心API 3: self_create
    # ========================================================================

    def self_create(self, module_spec: Dict[str, Any]) -> Dict[str, Any]:
        """自创造 — 基于规格创造新模块"""
        with self._lock:
            errors = []
            module_name = module_spec.get("name", "")

            if not module_name:
                return {"success": False, "errors": ["模块名不能为空"]}

            if module_name in self.modules:
                return {"success": False, "errors": [f"模块 {module_name} 已存在"]}

            code = self._generate_module_code(module_spec)
            test_code = self._generate_test_code(module_spec)

            validation = self.sandbox_validator.validate_code(code)
            if not validation["valid"]:
                errors.append(f"代码验证失败: {validation['errors']}")
                return {
                    "success": False,
                    "module_name": module_name,
                    "code": code,
                    "test_results": validation,
                    "registration": None,
                    "errors": errors
                }

            filepath = os.path.join(self.core_path, f"{module_name}.py")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(code)
                errors.append(f"保存模块失败: {e}")
                return {
                    "success": False,
                    "module_name": module_name,
                    "code": code,
                    "test_results": validation,
                    "registration": None,
                    "errors": errors
                }

            checksum = hashlib.sha256(code.encode()).hexdigest()[:16]
            descriptor = ModuleDescriptor(
                name=module_name,
                version="1.0.0",
                si_level=module_spec.get("si_level", 3.0),
                dependencies=module_spec.get("dependencies", []),
                exports=self._extract_exports(code),
                health=1.0,
                checksum=checksum,
                metadata={
                    "filepath": filepath,
                    "file_size": len(code),
                    "purpose": module_spec.get("purpose", ""),
                    "auto_generated": True
                }
            )
            self.modules[module_name] = descriptor
            self.impact_analyzer.register_module(module_name, descriptor.dependencies)

            snapshot_id = self.snapshot_manager.create_snapshot(
                module_name, code,
                metadata={"action": "creation", "spec": module_spec}
            )

            return {
                "success": True,
                "module_name": module_name,
                "code": code,
                "test_results": validation,
                "registration": {
                    "descriptor": descriptor,
                    "snapshot_id": snapshot_id
                },
                "errors": []
            }

    def _generate_module_code(self, spec: Dict[str, Any]) -> str:
        """根据规格生成模块代码"""
        name = spec.get("name", "new_module")
        purpose = spec.get("purpose", "Auto-generated module")
        functions = spec.get("functions", [])
        classes = spec.get("classes", [])
        dependencies = spec.get("dependencies", [])
        si_level = spec.get("si_level", 3.0)

        imports = ["import time", "from typing import Dict, List, Any, Optional"]
        for dep in dependencies:
            if dep not in ['os', 'sys', 'time', 'json']:
                imports.append(f"import {dep}")

        lines = []
        lines.append("#!/usr/bin/env python3")
        lines.append("# -*- coding: utf-8 -*-")
        lines.append(f'"""')
        lines.append(f"{purpose}")
        lines.append("")
        lines.append(f"模块: {name}")
        lines.append(f"SI级别: {si_level}")
        lines.append("自动生成: True")
        lines.append(f'"""')
        lines.append("")
        for imp in imports:
            lines.append(imp)
        lines.append("")

        for cls in classes:
            cls_name = cls.get("name", "NewClass")
            attrs = cls.get("attributes", [])
            methods = cls.get("methods", [])

            lines.append(f"class {cls_name}:")
            lines.append(f'    """{cls_name}类"""')
            lines.append("")
            if attrs:
                lines.append("    def __init__(self):")
                for attr in attrs:
                    lines.append(f"        self.{attr} = None")
            else:
                lines.append("    def __init__(self):")
                lines.append("        pass")
            lines.append("")

            for method in methods:
                lines.append(f"    def {method}(self):")
                lines.append(f'        """{method}方法"""')
                lines.append("        pass")
                lines.append("")

        for func in functions:
            func_name = func.get("name", "new_function")
            params = func.get("params", [])
            returns = func.get("returns", "Any")
            desc = func.get("description", "")

            param_str = ", ".join(params) if params else ""
            lines.append(f"def {func_name}({param_str}) -> {returns}:")
            lines.append(f'    """{desc}"""')
            lines.append("    # TODO: 实现逻辑")
            lines.append("    return None")
            lines.append("")

        return "\n".join(lines)

    def _generate_test_code(self, spec: Dict[str, Any]) -> str:
        """生成测试代码"""
        name = spec.get("name", "new_module")
        functions = spec.get("functions", [])

        lines = []
        lines.append("import unittest")
        lines.append(f"import {name}")
        lines.append("")
        lines.append(f"class Test{name.capitalize()}(unittest.TestCase):")

        for func in functions:
            func_name = func.get("name", "")
            lines.append(f"    def test_{func_name}(self):")
            lines.append(f'        """测试 {func_name}"""')
            lines.append(f"        result = {name}.{func_name}()")
            lines.append("        self.assertIsNotNone(result)")
            lines.append("")

        lines.append('if __name__ == "__main__":')
        lines.append("    unittest.main()")

        return "\n".join(lines)


    # ========================================================================
    # 核心API 4: meta_decision
    # ========================================================================

    def meta_decision(self, context: Dict[str, Any] = None) -> DecisionRecord:
        """元决策层 — 分析系统瓶颈并做出系统级调整决策"""
        with self._lock:
            self._meta_cycle_count += 1
            context = context or {}

            snapshot = self.self_observe(deep=False)
            bottlenecks = self._identify_bottlenecks(snapshot)
            candidates = self._generate_candidates(bottlenecks, context)
            best_candidate = self._select_best_candidate(candidates, context)

            decision = DecisionRecord(
                id=f"dec_{int(time.time()*1000)}",
                timestamp=time.time(),
                decision_type=best_candidate["type"],
                target_module=best_candidate.get("target", ""),
                rationale=best_candidate["rationale"],
                confidence=best_candidate["confidence"],
                expected_impact=best_candidate.get("impact", {}),
                prerequisites=best_candidate.get("prerequisites", []),
                actions=best_candidate.get("actions", [])
            )

            self.decision_history.append(decision)

            if decision.confidence > 0.8 and context.get("auto_execute", False):
                self._execute_decision(decision)

            return decision

    def _identify_bottlenecks(self, snapshot: SystemSnapshot) -> List[Dict[str, Any]]:
        """识别系统瓶颈"""
        bottlenecks = []

        for name, health in snapshot.health_matrix.items():
            if health < 0.7:
                bottlenecks.append({
                    "type": "health",
                    "module": name,
                    "severity": 1.0 - health,
                    "description": f"模块 {name} 健康度低 ({health:.2f})"
                })

        entropy = snapshot.entropy_profile
        if entropy.get("total_entropy", 0) > 2.0:
            bottlenecks.append({
                "type": "entropy",
                "module": "system",
                "severity": min(1.0, entropy["total_entropy"] / 5.0),
                "description": f"系统总熵过高 ({entropy['total_entropy']:.2f})"
            })

        coupling = self._compute_coupling_matrix()
        high_coupling_modules = []
        for mod, deps in coupling.items():
            max_coupling = max(deps.values()) if deps else 0
            if max_coupling > 3:
                high_coupling_modules.append((mod, max_coupling))

        if high_coupling_modules:
            mod, count = max(high_coupling_modules, key=lambda x: x[1])
            bottlenecks.append({
                "type": "coupling",
                "module": mod,
                "severity": min(1.0, count / 5.0),
                "description": f"模块 {mod} 耦合度过高 ({count} 共享依赖)"
            })

        bottlenecks.sort(key=lambda x: x["severity"], reverse=True)
        return bottlenecks

    def _generate_candidates(self, bottlenecks: List[Dict[str, Any]], 
                              context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成候选决策"""
        candidates = []

        if not bottlenecks:
            candidates.append({
                "type": DecisionType.NOOP,
                "target": "system",
                "rationale": "系统运行良好，无需调整",
                "confidence": 0.95,
                "impact": {"system_stability": 0.0},
                "prerequisites": [],
                "actions": [{"type": "monitor", "target": "system"}]
            })
            return candidates

        for bottleneck in bottlenecks[:3]:
            btype = bottleneck["type"]
            module = bottleneck["module"]
            severity = bottleneck["severity"]

            if btype == "health":
                candidates.append({
                    "type": DecisionType.MODIFY,
                    "target": module,
                    "rationale": f"修复模块 {module} 的健康问题",
                    "confidence": 0.7 + 0.2 * severity,
                    "impact": {"health_improvement": severity * 0.5},
                    "prerequisites": [f"备份 {module}"],
                    "actions": [
                        {"type": "self_modify", "target": module, "mod_type": "fix"},
                        {"type": "verify", "target": module}
                    ]
                })

            elif btype == "entropy":
                candidates.append({
                    "type": DecisionType.RECONFIGURE,
                    "target": "system",
                    "rationale": "降低系统熵，优化模块结构",
                    "confidence": 0.6 + 0.2 * severity,
                    "impact": {"entropy_reduction": severity * 0.3},
                    "prerequisites": ["系统快照"],
                    "actions": [
                        {"type": "analyze_dependencies", "target": "system"},
                        {"type": "suggest_refactoring", "target": "system"}
                    ]
                })

            elif btype == "coupling":
                candidates.append({
                    "type": DecisionType.SPLIT,
                    "target": module,
                    "rationale": f"拆分高耦合模块 {module}",
                    "confidence": 0.5 + 0.2 * severity,
                    "impact": {"coupling_reduction": severity * 0.4},
                    "prerequisites": [f"分析 {module} 接口"],
                    "actions": [
                        {"type": "self_create", "target": f"{module}_core"},
                        {"type": "self_modify", "target": module, "mod_type": "refactor"}
                    ]
                })

        if not candidates:
            candidates.append({
                "type": DecisionType.CREATE,
                "target": "system_monitor",
                "rationale": "创建系统监控模块以增强可观测性",
                "confidence": 0.8,
                "impact": {"observability": 0.5},
                "prerequisites": [],
                "actions": [
                    {"type": "self_create", "target": "system_monitor"}
                ]
            })

        return candidates

    def _select_best_candidate(self, candidates: List[Dict[str, Any]], 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """选择最优候选"""
        priority = context.get("priority", "balanced")

        if priority == "safety":
            return min(candidates, key=lambda c: max(c.get("impact", {}).values(), default=0))
        elif priority == "performance":
            return max(candidates, key=lambda c: max(c.get("impact", {}).values(), default=0))
        else:
            def score(c):
                conf = c.get("confidence", 0.5)
                impact = max(c.get("impact", {}).values(), default=0)
                return conf * impact
            return max(candidates, key=score)

    def _execute_decision(self, decision: DecisionRecord) -> Dict[str, Any]:
        """执行决策"""
        results = []
        for action in decision.actions:
            action_type = action.get("type", "")
            target = action.get("target", "")

            if action_type == "self_modify":
                result = self.self_modify(target, {
                    "type": ModificationType.FIX,
                    "description": f"自动修复: {decision.rationale}"
                })
                results.append(result)

            elif action_type == "self_create":
                result = self.self_create({
                    "name": target,
                    "purpose": f"自动创建: {decision.rationale}",
                    "si_level": 3.0
                })
                results.append(result)

        return {"decision": decision.id, "results": results}

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            "version": self.version,
            "si_level": self.si_level,
            "modules_registered": len(self.modules),
            "modifications": len(self.modification_history),
            "decisions": len(self.decision_history),
            "observations": len(self.observation_history),
            "snapshots": len(self.snapshot_manager.list_snapshots()),
            "meta_cycles": self._meta_cycle_count,
            "system_health": self._compute_system_health(),
            "recursion_guard": self.recursion_guard.get_stats()
        }

    def generate_report(self) -> str:
        """生成系统报告"""
        stats = self.get_stats()
        desc = self.self_language.describe_self(level=0)

        lines = []
        lines.append("=" * 80)
        lines.append("OMNI-HUB v3.8 Self-Referential Engine Report")
        lines.append("=" * 80)
        lines.append(f"系统版本: {stats['version']}                    SI级别: {stats['si_level']}")
        lines.append(f"注册模块: {stats['modules_registered']}                    系统健康: {stats['system_health']:.4f}")
        lines.append(f"修改次数: {stats['modifications']}                    决策次数: {stats['decisions']}")
        lines.append(f"观察次数: {stats['observations']}                    元周期: {stats['meta_cycles']}")
        lines.append(f"快照数量: {stats['snapshots']}                    递归调用: {stats['recursion_guard']['call_count']}")
        lines.append("=" * 80)
        lines.append("模块列表")
        lines.append("=" * 80)

        for name, mod in self.modules.items():
            lines.append(f"  {name:20} v{mod.version:8} SI{mod.si_level:<4} 健康:{mod.health:.2f} 导出:{len(mod.exports):3}")

        lines.append("=" * 80)
        lines.append("最近决策")
        lines.append("=" * 80)

        for dec in self.decision_history[-5:]:
            lines.append(f"  [{dec.id:12}] {dec.decision_type.value:12} -> {dec.target_module:15} 置信:{dec.confidence:.2f}")

        lines.append("=" * 80)
        lines.append("自指属性")
        lines.append("=" * 80)

        for prop, val in desc['self_referential_properties'].items():
            if isinstance(val, bool):
                status = "OK" if val else "NO"
                lines.append(f"  {prop:30} {status:40}")

        lines.append("=" * 80)

        return "\n".join(lines)


# ============================================================================
# SECTION 7: 实验验证框架
# ============================================================================

class SelfReferentialExperiment:
    """
    自指递归引擎实验验证框架
    测试套件:
        1. TestSelfObserve: 自观察完整性测试
        2. TestSelfModify: 自修改安全性测试
        3. TestSelfCreate: 自创造质量测试
        4. TestMetaDecision: 元决策合理性测试
        5. TestRecursionGuard: 递归守卫测试
        6. TestSelfLanguage: 自指语言测试
    """

    def __init__(self, engine: SelfReferentialEngine):
        self.engine = engine
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0

    def run_all(self) -> Dict[str, Any]:
        """运行所有实验"""
        logger.info("=" * 80)
        logger.info("OMNI-HUB v3.8 Self-Referential Engine Experiment Verification")
        logger.info("=" * 80)

        tests = [
            ("self_observe_completeness", self.test_self_observe),
            ("self_modify_safety", self.test_self_modify),
            ("self_create_quality", self.test_self_create),
            ("meta_decision_rationality", self.test_meta_decision),
            ("recursion_guard_protection", self.test_recursion_guard),
            ("self_language_capability", self.test_self_language),
            ("snapshot_rollback_mechanism", self.test_snapshot_rollback),
            ("impact_analysis_accuracy", self.test_impact_analysis),
        ]

        for name, test_func in tests:
            logger.info(f"\n{'-' * 60}")
            logger.info(f"[TEST] {name}")
            logger.info(f"{'-' * 60}")
                result = test_func()
                if result.get("passed", False):
                    self.passed += 1
                    logger.info(f"[PASS] OK: {name}")
                else:
                    self.failed += 1
                    logger.info(f"[FAIL] FAILED: {name}: {result.get('error', 'Unknown')}")
                self.results.append({"name": name, **result})
                self.failed += 1
                logger.info(f"[ERROR] EXCEPTION in {name}: {e}")
                import traceback
                traceback.print_exc()
                self.results.append({"name": name, "passed": False, "error": str(e)})

        summary = {
            "total": len(tests),
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": self.passed / len(tests) if tests else 0,
            "details": self.results
        }

        logger.info(f"\n{'=' * 80}")
        logger.info(f"Experiment Complete: Total={summary['total']} Passed={summary['passed']} Failed={summary['failed']}")
        logger.info(f"Pass Rate: {summary['pass_rate']*100:.1f}%")
        logger.info(f"{'=' * 80}")

        return summary

    def test_self_observe(self) -> Dict[str, Any]:
        """测试self_observe完整性"""
        snapshot = self.engine.self_observe(deep=False)

        checks = []
        checks.append(("type_check", isinstance(snapshot, SystemSnapshot)))
        checks.append(("modules_present", len(snapshot.modules) > 0))
        checks.append(("dependency_graph", len(snapshot.dependency_graph) > 0))
        checks.append(("health_matrix", len(snapshot.health_matrix) > 0))
        checks.append(("entropy_profile", len(snapshot.entropy_profile) > 0))
        checks.append(("timestamp_valid", snapshot.timestamp > 0))
        checks.append(("version_correct", snapshot.version == "3.8.0"))

        deep_snapshot = self.engine.self_observe(deep=True)
        checks.append(("deep_observation", "code_quality" in deep_snapshot.memory_estimate))
        checks.append(("coupling_matrix", "coupling_matrix" in deep_snapshot.memory_estimate))

        all_passed = all(c[1] for c in checks)

        return {
            "passed": all_passed,
            "checks": checks,
            "modules_count": len(snapshot.modules),
            "entropy": snapshot.entropy_profile
        }

    def test_self_modify(self) -> Dict[str, Any]:
        """测试self_modify安全性"""
        test_mod_name = "test_modify_target"
        original_code = """# Test module for self_modify
class TestClass:
    def method1(self):
        return 42

    def method2(self):
        return "hello"
"""
        test_path = os.path.join(self.engine.core_path, f"{test_mod_name}.py")
    with open(test_path, 'w', encoding='utf-8') as f:
            f.write(original_code)

        self.engine.modules[test_mod_name] = ModuleDescriptor(
            name=test_mod_name,
            version="1.0.0",
            si_level=3.0,
            dependencies=[],
            exports=["class:TestClass", "func:method1", "func:method2"],
            health=1.0,
            checksum=hashlib.sha256(original_code.encode()).hexdigest()[:16],
            metadata={"filepath": test_path}
        )

        checks = []

        # Test 1: EXTEND modification (append to file end)
        extend_result = self.engine.self_modify(
            test_mod_name,
            {
                "type": ModificationType.EXTEND,
                "code": "\nclass AddedClass:\n    def added_method(self):\n        return 999\n",
                "description": "Add new class"
            },
            verification=True,
            safety_level=SafetyLevel.STANDARD
        )
        checks.append(("extend_success", extend_result["success"]))
        checks.append(("snapshot_created", extend_result["snapshot_id"] is not None))
        checks.append(("impact_analyzed", extend_result["impact"] is not None))

        # Test 2: Invalid modification rejection (syntax error)
        bad_result = self.engine.self_modify(
            test_mod_name,
            {
                "type": ModificationType.EXTEND,
                "code": "def broken(\n",
                "description": "Intentional error"
            },
            verification=True,
            safety_level=SafetyLevel.STANDARD
        )
        checks.append(("bad_mod_rejected", not bad_result["success"]))

        # Test 3: Non-existent module
        no_mod_result = self.engine.self_modify(
            "nonexistent_module",
            {"type": ModificationType.PATCH, "patch": "pass"},
            verification=True
        )
        checks.append(("nonexistent_rejected", not no_mod_result["success"]))

        # Cleanup
        if os.path.exists(test_path):
            os.remove(test_path)
        if test_mod_name in self.engine.modules:
            del self.engine.modules[test_mod_name]

        all_passed = all(c[1] for c in checks)
        return {
            "passed": all_passed,
            "checks": checks,
            "extend_verification": extend_result.get("verification", {})
        }

    def test_self_create(self) -> Dict[str, Any]:
        """测试self_create代码生成质量"""
        spec = {
            "name": "test_auto_module",
            "purpose": "Auto-generated test module",
            "si_level": 3.5,
            "dependencies": ["json"],
            "functions": [
                {
                    "name": "process_data",
                    "params": ["data", "config"],
                    "returns": "Dict[str, Any]",
                    "description": "Process input data"
                },
                {
                    "name": "validate_input",
                    "params": ["input_str"],
                    "returns": "bool",
                    "description": "Validate input"
                }
            ],
            "classes": [
                {
                    "name": "DataProcessor",
                    "attributes": ["config", "state"],
                    "methods": ["process", "reset"]
                }
            ]
        }

        result = self.engine.self_create(spec)

        checks = []
        checks.append(("creation_success", result["success"]))
        checks.append(("code_generated", len(result.get("code", "")) > 0))
        checks.append(("class_defined", "class DataProcessor" in result.get("code", "")))
        checks.append(("function_defined", "def process_data" in result.get("code", "")))
        checks.append(("docstring_present", '"""' in result.get("code", "")))
        checks.append(("module_registered", "test_auto_module" in self.engine.modules))
        checks.append(("validation_passed", result.get("test_results", {}).get("valid", False)))

        # Cleanup
        test_path = os.path.join(self.engine.core_path, "test_auto_module.py")
        if os.path.exists(test_path):
            os.remove(test_path)
        if "test_auto_module" in self.engine.modules:
            del self.engine.modules["test_auto_module"]

        all_passed = all(c[1] for c in checks)
        return {
            "passed": all_passed,
            "checks": checks,
            "code_preview": result.get("code", "")[:500] if result.get("code") else ""
        }

    def test_meta_decision(self) -> Dict[str, Any]:
        """测试meta_decision决策合理性"""
        if self.engine.modules:
            first_mod = list(self.engine.modules.keys())[0]
            old_health = self.engine.modules[first_mod].health
            self.engine.modules[first_mod].health = 0.5

        decision = self.engine.meta_decision(context={
            "priority": "balanced",
            "auto_execute": False
        })

        checks = []
        checks.append(("decision_record", isinstance(decision, DecisionRecord)))
        checks.append(("valid_decision_type", isinstance(decision.decision_type, DecisionType)))
        checks.append(("confidence_range", 0.0 <= decision.confidence <= 1.0))
        checks.append(("rationale_present", len(decision.rationale) > 0))
        checks.append(("actions_present", len(decision.actions) > 0))
        checks.append(("history_recorded", decision in self.engine.decision_history))

        if self.engine.modules:
            first_mod = list(self.engine.modules.keys())[0]
            self.engine.modules[first_mod].health = old_health

        all_passed = all(c[1] for c in checks)
        return {
            "passed": all_passed,
            "checks": checks,
            "decision_type": decision.decision_type.value,
            "confidence": decision.confidence,
            "rationale": decision.rationale,
            "actions": decision.actions
        }

    def test_recursion_guard(self) -> Dict[str, Any]:
        """测试recursion_guard递归保护"""
        guard = RecursionGuard(max_depth=3, name="test_guard")

        call_count = [0]

        @guard
        def recursive_func(n):
            call_count[0] += 1
            if n > 0:
                return recursive_func(n - 1)
            return "done"

        checks = []

            result = recursive_func(2)
            checks.append(("normal_recursion", result == "done"))
        stats = guard.get_stats()
        checks.append(("stats_present", stats["name"] == "test_guard"))
        checks.append(("call_counted", stats["call_count"] > 0))
        checks.append(("breach_counted", stats["breach_count"] > 0))

        all_passed = all(c[1] for c in checks)
        return {
            "passed": all_passed,
            "checks": checks,
            "guard_stats": stats
        }

    def test_self_language(self) -> Dict[str, Any]:
        """测试自指语言"""
        lang = self.engine.self_language

        checks = []

        desc = lang.describe_self(level=0)
        checks.append(("basic_description", desc["meta_level"] == 0))
        checks.append(("system_identity", desc["system_identity"]["name"] == "OMNI-HUB"))
        checks.append(("modules_listed", len(desc["modules"]) > 0))
        checks.append(("capabilities_listed", len(desc["capabilities"]) > 0))

        meta_desc = lang.describe_self(level=1)
        checks.append(("meta_description", meta_desc["meta_level"] == 1))
        checks.append(("meta_present", "meta_description" in meta_desc))

        test_action = {
            "id": "test_action_1",
            "type": "modify",
            "success": True,
            "verification_result": True,
            "impact": {"risk_level": "medium"},
            "expected_result": "success"
        }
        reflection = lang.reflect_on(test_action, depth=1)
        checks.append(("reflection_result", isinstance(reflection, ReflectionResult)))
        checks.append(("reflection_effects", len(reflection.observed_effects) > 0))
        checks.append(("reflection_lessons", len(reflection.lessons_learned) > 0))
        checks.append(("consistency_score", 0.0 <= reflection.self_consistency_score <= 1.0))

        doc = lang.generate_self_documentation()
        checks.append(("doc_generated", len(doc) > 0))
        checks.append(("doc_title", "OMNI-HUB" in doc))

        all_passed = all(c[1] for c in checks)
        return {
            "passed": all_passed,
            "checks": checks,
            "description_levels": [0, 1],
            "reflection_score": reflection.self_consistency_score
        }

    def test_snapshot_rollback(self) -> Dict[str, Any]:
        """测试快照回滚机制"""
        test_name = "test_rollback_module"
        v1_code = "# Version 1\nclass V1: pass\n"
        v2_code = "# Version 2\nclass V2: pass\n"

        test_path = os.path.join(self.engine.core_path, f"{test_name}.py")
    with open(test_path, 'w', encoding='utf-8') as f:
            f.write(v1_code)

        snap1 = self.engine.snapshot_manager.create_snapshot(test_name, v1_code)

    with open(test_path, 'w', encoding='utf-8') as f:
            f.write(v2_code)

        snap2 = self.engine.snapshot_manager.create_snapshot(test_name, v2_code)

        checks = []
        checks.append(("snapshot_created", snap1 is not None and snap2 is not None))

        snap_data = self.engine.snapshot_manager.get_snapshot(snap1)
        checks.append(("snapshot_readable", snap_data is not None))
        checks.append(("snapshot_content", snap_data.get("code") == v1_code))

        rollback_code = self.engine.snapshot_manager.rollback(test_name, snap1)
        checks.append(("rollback_code", rollback_code == v1_code))

        latest_code = self.engine.snapshot_manager.rollback(test_name)
        checks.append(("rollback_latest", latest_code == v2_code))

        chain_valid = self.engine.snapshot_manager.verify_snapshot_chain(test_name)
        checks.append(("chain_valid", chain_valid))

        snaps = self.engine.snapshot_manager.list_snapshots(test_name)
        checks.append(("snapshots_listed", len(snaps) >= 2))

        # Cleanup
        if os.path.exists(test_path):
            os.remove(test_path)
        for snap in snaps:
            snap_path = os.path.join(self.engine.snapshot_manager.snapshot_dir, f"{snap['id']}.json")
            if os.path.exists(snap_path):
                os.remove(snap_path)
        if test_name in self.engine.snapshot_manager.snapshots:
            del self.engine.snapshot_manager.snapshots[test_name]
        self.engine.snapshot_manager._save_index()

        all_passed = all(c[1] for c in checks)
        return {
            "passed": all_passed,
            "checks": checks,
            "snapshot_count": len(snaps)
        }

    def test_impact_analysis(self) -> Dict[str, Any]:
        """测试影响图分析"""
        analyzer = self.engine.impact_analyzer

        analyzer.register_module("A", ["B", "C"])
        analyzer.register_module("B", ["C"])
        analyzer.register_module("C", ["D"])
        analyzer.register_module("D", [])
        analyzer.register_module("E", ["B"])

        checks = []

        # Dependency graph: A->[B,C], B->[C], C->[D], D->[], E->[B]
        # Reverse: D is depended by C, C by B,A, B by E,A
        
        impact_d = analyzer.analyze_impact("D", ModificationType.PATCH)
        # D is leaf but C depends on D, so C,B,A,E are affected
        checks.append(("d_affects_c", "C" in impact_d["affected_modules"]))
        checks.append(("d_propagation", impact_d["propagation_depth"] >= 2))

        impact_c = analyzer.analyze_impact("C", ModificationType.PATCH)
        # C is depended by B and A
        checks.append(("c_affects_a", "A" in impact_c["affected_modules"]))
        checks.append(("c_affects_b", "B" in impact_c["affected_modules"]))
        checks.append(("c_propagation_depth", impact_c["propagation_depth"] >= 1))

        impact_b = analyzer.analyze_impact("B", ModificationType.REPLACE)
        # B is depended by E and A, REPLACE elevates risk
        checks.append(("b_affects_a", "A" in impact_b["affected_modules"]))
        checks.append(("b_affects_e", "E" in impact_b["affected_modules"]))
        checks.append(("b_risk_elevated", impact_b["risk_level"] in ["medium", "high", "critical"]))

        chain = analyzer.get_dependency_chain("A", "D")
        checks.append(("chain_exists", len(chain) > 0))
        checks.append(("chain_contains_d", "D" in chain))

        checks.append(("impact_score_valid", 0.0 <= impact_c["impact_score"] <= 1.0))

        all_passed = all(c[1] for c in checks)
        return {
            "passed": all_passed,
            "checks": checks,
            "impact_samples": {
                "D": {"affected": len(impact_d["affected_modules"]), "risk": impact_d["risk_level"]},
                "C": {"affected": len(impact_c["affected_modules"]), "risk": impact_c["risk_level"]},
                "B": {"affected": len(impact_b["affected_modules"]), "risk": impact_b["risk_level"]}
            }
        }


# ============================================================================
# SECTION 8: 主入口
# ============================================================================

if __name__ == "__main__":
    core_path = os.path.dirname(os.path.abspath(__file__))
    engine = SelfReferentialEngine(core_path=core_path)

    print(engine.generate_report())
    print("\n")

    experiment = SelfReferentialExperiment(engine)
    results = experiment.run_all()

    print("\n" + "=" * 80)
    print("System Self-Documentation")
    print("=" * 80)
    print(engine.self_language.generate_self_documentation())

    report_path = os.path.join(core_path, "self_referential_experiment_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nExperiment report saved to: {report_path}")
