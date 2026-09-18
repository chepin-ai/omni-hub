#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OMNI-HUB v6.0 — FullPotentialExplorer
全量潜能探索器 — 遍历所有模块的所有功能，释放100%的潜在能力

Author: OMNI-HUB Architecture Team
Version: 6.0.0
Date: 2025

功能:
1. 扫描所有35个核心模块
2. 发现所有类和方法
3. 安全调用每个方法并记录结果
4. 生成能力图谱和潜能报告
5. 识别"沉睡"功能并提出唤醒建议
"""

__version__ = "11.0.0"
import ast
import importlib.util
import inspect
import json
import os
import sys
import time
import traceback
import types
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

# Add parent directory to path for imports
_HUB_DIR = os.environ.get('OMNI_HUB_DIR', '/mnt/agents/output/OMNI-HUB')
sys.path.insert(0, os.path.dirname(_HUB_DIR))


# =============================================================================
# 数据模型
# =============================================================================

class InvocationStatus(Enum):
    """方法调用状态"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    NOT_CALLABLE = "not_callable"
    INIT_REQUIRED = "init_required"


@dataclass
class MethodSignature:
    """方法签名信息"""
    name: str
    parameters: List[Dict[str, Any]]
    return_annotation: Optional[str]
    is_static: bool
    is_classmethod: bool
    is_property: bool
    docstring: Optional[str]
    source_file: Optional[str]
    line_number: Optional[int]


@dataclass
class InvocationResult:
    """方法调用结果"""
    module_name: str
    class_name: str
    method_name: str
    status: InvocationStatus
    result: Any = None
    exception: Optional[str] = None
    execution_time: float = 0.0
    args_used: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    module_name: str
    methods: List[MethodSignature] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    is_dataclass: bool = False
    is_enum: bool = False


@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    file_path: str
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[MethodSignature] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


# =============================================================================
# CapabilityMap — 能力图谱
# =============================================================================

class CapabilityMap:
    """
    能力图谱 — 记录所有模块的能力分布
    
    功能:
    - 记录每个方法的调用结果
    - 生成能力矩阵
    - 查找相似能力
    - 计算覆盖率
    """

    def __init__(self):
        self.capabilities: Dict[str, Dict[str, Dict[str, Dict]]] = {}
        self.invocation_log: List[InvocationResult] = []
        self.module_stats: Dict[str, Dict[str, Any]] = {}
        self._coverage_cache: Optional[float] = None

    def add_capability(self, module: str, class_name: str, method: str,
                       result: InvocationResult) -> None:
        """添加能力记录"""
        if module not in self.capabilities:
            self.capabilities[module] = {}
        if class_name not in self.capabilities[module]:
            self.capabilities[module][class_name] = {}
        
        self.capabilities[module][class_name][method] = {
            "status": result.status.value,
            "result_type": type(result.result).__name__ if result.result is not None else None,
            "result_summary": self._summarize_result(result.result),
            "execution_time": result.execution_time,
            "exception": result.exception,
            "timestamp": result.timestamp,
        }
        self.invocation_log.append(result)
        self._coverage_cache = None

    def _summarize_result(self, result: Any, max_len: int = 200) -> Any:
        """总结结果，避免过大"""
        if result is None:
            return None
            if isinstance(result, (int, float, bool, str)):
                return result
            if isinstance(result, (list, tuple)):
                return f"{type(result).__name__}[{len(result)}]"
            if isinstance(result, dict):
                return f"dict[{len(result)}]"
            if isinstance(result, np.ndarray):
                return f"ndarray{result.shape}"
            r = str(result)
            return r[:max_len] + "..." if len(r) > max_len else r
            return f"<{type(result).__name__}>"

    def get_module_capabilities(self, module: str) -> Dict:
        """获取模块能力"""
        return self.capabilities.get(module, {})

    def get_class_capabilities(self, module: str, class_name: str) -> Dict:
        """获取类能力"""
        return self.capabilities.get(module, {}).get(class_name, {})

    def find_similar_capabilities(self, query: str) -> List[Dict]:
        """查找相似能力（基于方法名和模块名模糊匹配）"""
        query = query.lower()
        matches = []
        for module, classes in self.capabilities.items():
            for class_name, methods in classes.items():
                for method_name, info in methods.items():
                    score = 0
                    text = f"{module} {class_name} {method_name}".lower()
                    if query in text:
                        score = len(query) / len(text)
                    words = query.split()
                    for word in words:
                        if word in text:
                            score += 0.3
                    if score > 0:
                        matches.append({
                            "module": module,
                            "class": class_name,
                            "method": method_name,
                            "score": score,
                            "info": info
                        })
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:20]

    def get_coverage(self) -> Dict[str, float]:
        """获取覆盖率统计"""
        total_methods = 0
        success_methods = 0
        failed_methods = 0
        skipped_methods = 0

        for module, classes in self.capabilities.items():
            for class_name, methods in classes.items():
                for method_name, info in methods.items():
                    total_methods += 1
                    status = info.get("status", "")
                    if status == "success":
                        success_methods += 1
                    elif status == "failed":
                        failed_methods += 1
                    elif status == "skipped":
                        skipped_methods += 1

        coverage = {
            "total_methods": total_methods,
            "success": success_methods,
            "failed": failed_methods,
            "skipped": skipped_methods,
            "success_rate": success_methods / total_methods if total_methods > 0 else 0.0,
            "exploration_rate": (success_methods + failed_methods) / total_methods if total_methods > 0 else 0.0,
        }
        return coverage

    def get_sleeping_capabilities(self, threshold: float = 0.3) -> List[Dict]:
        """识别沉睡功能（调用成功率低于阈值的方法）"""
        sleeping = []
        for module, classes in self.capabilities.items():
            module_success = 0
            module_total = 0
            for class_name, methods in classes.items():
                for method_name, info in methods.items():
                    module_total += 1
                    if info.get("status") == "success":
                        module_success += 1
            
            if module_total > 0:
                rate = module_success / module_total
                if rate < threshold:
                    sleeping.append({
                        "module": module,
                        "success_rate": rate,
                        "total_methods": module_total,
                        "success_count": module_success,
                        "recommendation": self._generate_recommendation(module, rate)
                    })
        
        sleeping.sort(key=lambda x: x["success_rate"])
        return sleeping

    def _generate_recommendation(self, module: str, rate: float) -> str:
        """生成唤醒建议"""
        if rate < 0.1:
            return f"模块 {module} 严重沉睡 — 建议检查依赖注入和初始化顺序"
        elif rate < 0.3:
            return f"模块 {module} 轻度沉睡 — 建议增加单元测试和参数适配"
        else:
            return f"模块 {module} 部分激活 — 建议优化异常处理"

    def export(self, filepath: Optional[str] = None) -> str:
        """导出为JSON"""
        data = {
            "capabilities": self.capabilities,
            "coverage": self.get_coverage(),
            "sleeping_capabilities": self.get_sleeping_capabilities(),
            "invocation_count": len(self.invocation_log),
            "export_time": datetime.now().isoformat(),
        }
        
        # 转换不可序列化的值
        def clean_value(v):
            if isinstance(v, (str, int, float, bool, type(None))):
                return v
            if isinstance(v, (list, tuple)):
                return [clean_value(x) for x in v]
            if isinstance(v, dict):
                return {k: clean_value(val) for k, val in v.items()}
            return str(v)
        
        data = clean_value(data)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        return json.dumps(data, indent=2, ensure_ascii=False)

    def get_heatmap_data(self) -> Dict[str, Dict[str, float]]:
        """生成热力图数据（模块×类 → 成功率）"""
        heatmap = {}
        for module, classes in self.capabilities.items():
            heatmap[module] = {}
            for class_name, methods in classes.items():
                success = sum(1 for m in methods.values() if m.get("status") == "success")
                total = len(methods)
                heatmap[module][class_name] = success / total if total > 0 else 0.0
        return heatmap


# =============================================================================
# MethodInvoker — 方法调用器
# =============================================================================

class MethodInvoker:
    """
    方法调用器 — 安全调用方法并生成测试参数
    
    功能:
    - 安全调用（try-except + timeout）
    - 智能参数生成（基于类型注解和默认值）
    - 结果记录和异常捕获
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.results: List[InvocationResult] = []
        self._instance_cache: Dict[str, Any] = {}
        self._type_generators = self._build_type_generators()

    def _build_type_generators(self) -> Dict[type, Callable]:
        """构建类型到测试值的生成器映射"""
        import numpy as np
        return {
            int: lambda: 42,
            float: lambda: 3.14,
            str: lambda: "test_string",
            bool: lambda: True,
            list: lambda: [1, 2, 3],
            dict: lambda: {"key": "value"},
            tuple: lambda: (1, 2),
            set: lambda: {1, 2, 3},
            np.ndarray: lambda: np.array([1.0, 2.0, 3.0]),
        }

    def generate_test_args(self, method: Callable, class_instance: Any = None) -> Dict[str, Any]:
        """
        为方法生成测试参数
        
        策略:
        1. 检查类型注解
        2. 检查默认值
        3. 使用类型推断生成值
        4. 对于self/cls参数，跳过
        """
        args = {}
        sig = inspect.signature(method)
        for param_name, param in sig.parameters.items():
                # Skip self/cls
                if param_name in ('self', 'cls'):
                    continue
                
                # Use default if available
                if param.default is not inspect.Parameter.empty:
                    args[param_name] = param.default
                    continue
                
                # Try type annotation
                if param.annotation is not inspect.Parameter.empty:
                    arg_value = self._generate_for_annotation(param.annotation)
                    if arg_value is not None:
                        args[param_name] = arg_value
                        continue
                
                # Fallback based on parameter name patterns
                args[param_name] = self._generate_from_name(param_name)
                pass
        
        return args

    def _generate_for_annotation(self, annotation: Any) -> Any:
        """根据类型注解生成测试值"""
        # Handle basic types
        origin = getattr(annotation, '__origin__', None)
        
        if origin is not None:
            # Handle typing generics
            args = getattr(annotation, '__args__', ())
            if origin is list or origin is set:
                return [1, 2, 3]
            elif origin is dict:
                return {"key": "value"}
            elif origin is tuple:
                return tuple([1, 2, 3][:len(args)]) if args else (1, 2)
            elif origin is Union:
                # For Optional[X], pick the first non-None type
                for arg in args:
                    if arg is not type(None):
                        return self._generate_for_annotation(arg)
                return None
            return None
        
        # Direct type match
        if isinstance(annotation, type):
            generator = self._type_generators.get(annotation)
            if generator:
                return generator()
        
        # Handle Enum
        if isinstance(annotation, type) and issubclass(annotation, Enum):
                return list(annotation)[0]
                return None
        
        return None

    def _generate_from_name(self, name: str) -> Any:
        """根据参数名生成测试值"""
        name_lower = name.lower()
        
        patterns = {
            'id': 'test-id-123',
            'name': 'test_name',
            'key': 'test_key',
            'value': 42,
            'count': 5,
            'index': 0,
            'size': 10,
            'length': 100,
            'width': 800,
            'height': 600,
            'x': 0.0,
            'y': 0.0,
            'z': 0.0,
            'ratio': 0.5,
            'rate': 1.0,
            'threshold': 0.5,
            'alpha': 0.5,
            'beta': 0.3,
            'gamma': 0.2,
            'level': 1,
            'depth': 3,
            'step': 1,
            'max': 100,
            'min': 0,
            'start': 0,
            'end': 10,
            'data': {'test': 'data'},
            'items': [1, 2, 3],
            'elements': ['a', 'b', 'c'],
            'config': {'setting': True},
            'options': {'option1': True},
            'path': '/tmp/test',
            'file': 'test.txt',
            'url': 'http://example.com',
            'text': 'Sample text',
            'message': 'Test message',
            'content': 'Test content',
            'title': 'Test Title',
            'description': 'Test description',
            'pattern': [0.1, 0.2, 0.3],
            'vector': [1.0, 2.0, 3.0],
            'matrix': [[1, 0], [0, 1]],
            'seed': 42,
            'timestamp': time.time(),
            'version': '1.0.0',
            'mode': 'test',
            'type': 'default',
            'state': 'active',
            'status': 'ok',
            'flag': True,
            'enabled': True,
            'visible': True,
            'debug': False,
            'force': False,
            'recursive': True,
            'async': False,
            'callback': lambda x: x,
            'handler': lambda: None,
            'context': {},
            'session': {'id': 'session-123'},
            'user': 'test_user',
            'owner': 'test_owner',
            'source': 'test_source',
            'target': 'test_target',
            'parent': 'parent-id',
            'child': 'child-id',
            'node': 'node-1',
            'edge': ('a', 'b'),
            'graph': {'nodes': [], 'edges': []},
            'tree': {'root': None},
            'field': {'value': 1.0},
            'tensor': [1.0, 2.0, 3.0],
            'quantum': {'state': 'ground'},
            'entropy': 0.5,
            'energy': 1.0,
            'frequency': 440.0,
            'amplitude': 1.0,
            'phase': 0.0,
            'wavelength': 500.0,
            'velocity': 1.0,
            'acceleration': 0.0,
            'mass': 1.0,
            'charge': 1.0,
            'spin': 0.5,
            'position': (0.0, 0.0),
            'direction': (1.0, 0.0),
            'color': '#FF0000',
            'opacity': 1.0,
            'scale': 1.0,
            'rotation': 0.0,
            'transform': [[1, 0], [0, 1]],
            'bounds': (0, 100),
            'range': (0, 10),
            'domain': (0, 1),
            'interval': 1.0,
            'duration': 1.0,
            'period': 1.0,
            'delay': 0.0,
            'timeout': 5.0,
            'retry': 3,
            'attempt': 1,
            'priority': 5,
            'weight': 1.0,
            'score': 0.5,
            'metric': {'accuracy': 0.9},
            'result': {},
            'output': 'test_output',
            'input': 'test_input',
            'query': 'test_query',
            'filter': {},
            'sort': 'asc',
            'order': 1,
            'limit': 100,
            'offset': 0,
            'page': 1,
            'total': 0,
            'progress': 0.5,
            'percentage': 50.0,
        }
        
        for pattern, value in patterns.items():
            if pattern in name_lower:
                return value
        
        return "test_value"

    def safe_invoke(self, module_name: str, class_name: str, method_name: str,
                    method: Callable, instance: Any = None,
                    args: Optional[Dict] = None) -> InvocationResult:
        """
        安全调用方法
        
        流程:
        1. 生成测试参数
        2. 在超时保护下调用
        3. 记录结果
        """
        start_time = time.time()
        
        if args is None:
            args = self.generate_test_args(method, instance)
        
        result = InvocationResult(
            module_name=module_name,
            class_name=class_name,
            method_name=method_name,
            status=InvocationStatus.SUCCESS,
            args_used=args
        )
        
        # Check if callable
        if not callable(method):
                result.status = InvocationStatus.NOT_CALLABLE
                result.result = None
                return result
            
        # For properties, just get the value
        if isinstance(method, property):
            result.status = InvocationStatus.SKIPPED
            result.result = None
            return result
            
            # Execute with timeout using threading
            import threading
            invocation_result = [None]
            exception_info = [None]
            
            def target():
                    if instance is not None:
                        invocation_result[0] = method(**args)
                    else:
                        invocation_result[0] = method(**args)
                    exception_info[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=self.timeout)
            
            if thread.is_alive():
                result.status = InvocationStatus.TIMEOUT
                result.exception = f"Execution exceeded {self.timeout} seconds"
            elif exception_info[0] is not None:
                result.status = InvocationStatus.FAILED
                result.exception = f"{type(exception_info[0]).__name__}: {str(exception_info[0])}"
                result.result = None
            else:
                result.status = InvocationStatus.SUCCESS
                result.result = invocation_result[0]
                
            result.status = InvocationStatus.FAILED
            result.exception = f"{type(e).__name__}: {str(e)}"
            result.result = None
        
        result.execution_time = time.time() - start_time
        self.results.append(result)
        return result

    def record_result(self, result: InvocationResult) -> None:
        """记录结果"""
        self.results.append(result)

    def get_success_rate(self) -> float:
        """获取成功率"""
        if not self.results:
            return 0.0
        success = sum(1 for r in self.results if r.status == InvocationStatus.SUCCESS)
        return success / len(self.results)


# =============================================================================
# FullPotentialExplorer — 全量潜能探索器
# =============================================================================

class FullPotentialExplorer:
    """
    全量潜能探索器
    
    遍历OMNI-HUB所有模块的所有功能，释放100%的潜在能力。
    
    核心流程:
    1. 扫描阶段: 发现所有模块/类/方法
    2. 分类阶段: 将方法分类（初始化/核心运算/查询/副作用）
    3. 调用阶段: 初始化实例，调用方法，记录输出
    4. 分析阶段: 统计成功率，识别异常，生成能力图谱
    """

    def __init__(self, hub_dir: str = '/mnt/agents/output/OMNI-HUB'):
        self.hub_dir = Path(hub_dir)
        self.core_dir = self.hub_dir / 'core'
        self.modules: Dict[str, ModuleInfo] = {}
        self.capability_map = CapabilityMap()
        self.method_invoker = MethodInvoker(timeout=10.0)
        
        # Statistics
        self.stats = {
            "total_modules": 0,
            "total_classes": 0,
            "total_methods": 0,
            "invoked_methods": 0,
            "successful_invocations": 0,
            "failed_invocations": 0,
            "skipped_methods": 0,
            "start_time": None,
            "end_time": None,
        }
        
        # Classification
        self.method_categories = {
            "init": [],
            "core": [],
            "query": [],
            "side_effect": [],
            "utility": [],
        }
        
        # Module blacklist (modules that are problematic to import)
        self.module_blacklist: Set[str] = set()
        
        # Loaded module objects
        self._loaded_modules: Dict[str, Any] = {}
        self._class_instances: Dict[str, Any] = {}

    def discover_modules(self) -> List[str]:
        """
        发现所有模块
        
        扫描core目录下的所有.py文件，排除__init__和当前文件。
        """
        modules = []
        if not self.core_dir.exists():
            logger.info(f"[WARN] Core directory not found: {self.core_dir}")
            return modules
        
        for file_path in sorted(self.core_dir.glob('*.py')):
            name = file_path.stem
            if name.startswith('__') or name == 'full_potential_explorer':
                continue
            modules.append(name)
        
        self.stats["total_modules"] = len(modules)
        logger.info(f"[DISCOVER] Found {len(modules)} modules")
        return modules

    def _load_module(self, module_name: str) -> Any:
        """动态加载模块"""
        if module_name in self._loaded_modules:
            return self._loaded_modules[module_name]
        
        file_path = self.core_dir / f"{module_name}.py"
        if not file_path.exists():
            return None
        
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return None
            
            module = importlib.util.module_from_spec(spec)
            # Add to sys.modules to handle internal imports
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            self._loaded_modules[module_name] = module
            return module
            logger.info(f"[WARN] Failed to load module {module_name}: {e}")
            self.module_blacklist.add(module_name)
            return None

    def discover_classes(self, module_path: str) -> List[ClassInfo]:
        """
        发现模块中的所有类
        
        使用inspect获取模块中定义的所有类。
        """
        module_name = Path(module_path).stem
        module = self._load_module(module_name)
        
        if module is None:
            return []
        
        classes = []
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Only include classes defined in this module
            if obj.__module__ != module_name:
                continue
            
            class_info = ClassInfo(
                name=name,
                module_name=module_name,
                bases=[b.__name__ for b in obj.__bases__ if b is not object],
                docstring=inspect.getdoc(obj),
                is_dataclass=hasattr(obj, '__dataclass_fields__'),
                is_enum=issubclass(obj, Enum)
            )
            
            # Discover methods
            class_info.methods = self.discover_methods(obj)
            classes.append(class_info)
        
        return classes

    def discover_methods(self, class_obj: type) -> List[MethodSignature]:
        """
        发现类中的所有方法
        
        使用inspect获取类的所有方法，包括实例方法、类方法、静态方法。
        """
        methods = []
        
        for name, obj in inspect.getmembers(class_obj):
            # Skip dunder methods (except __init__)
            if name.startswith('__') and name != '__init__':
                continue
            
            if inspect.isfunction(obj) or inspect.ismethod(obj):
                sig = self._analyze_signature(name, obj)
                methods.append(sig)
            elif isinstance(obj, property):
                sig = MethodSignature(
                    name=name,
                    parameters=[],
                    return_annotation=None,
                    is_static=False,
                    is_classmethod=False,
                    is_property=True,
                    docstring=obj.__doc__,
                    source_file=None,
                    line_number=None
                )
                methods.append(sig)
        
        return methods

    def _analyze_signature(self, name: str, method: Callable) -> MethodSignature:
        """分析方法签名"""
            sig = inspect.signature(method)
            params = []
            for param_name, param in sig.parameters.items():
                param_info = {
                    "name": param_name,
                    "kind": str(param.kind),
                    "default": str(param.default) if param.default is not inspect.Parameter.empty else None,
                    "annotation": str(param.annotation) if param.annotation is not inspect.Parameter.empty else None,
                }
                params.append(param_info)
            
            return_annotation = str(sig.return_annotation) if sig.return_annotation is not inspect.Parameter.empty else None
            
            return MethodSignature(
                name=name,
                parameters=params,
                return_annotation=return_annotation,
                is_static=isinstance(inspect.getattr_static(method.__class__ if hasattr(method, '__class__') else object, name, None), staticmethod),
                is_classmethod=isinstance(inspect.getattr_static(method.__class__ if hasattr(method, '__class__') else object, name, None), classmethod),
                is_property=False,
                docstring=inspect.getdoc(method),
                source_file=inspect.getfile(method) if hasattr(method, '__code__') else None,
                line_number=method.__code__.co_firstlineno if hasattr(method, '__code__') else None
            )
            return MethodSignature(
                name=name,
                parameters=[],
                return_annotation=None,
                is_static=False,
                is_classmethod=False,
                is_property=False,
                docstring=None,
                source_file=None,
                line_number=None
            )

    def discover_parameters(self, method: Callable) -> List[Dict[str, Any]]:
        """发现方法的所有参数"""
        sig = self._analyze_signature(method.__name__ if hasattr(method, '__name__') else 'unknown', method)
        return sig.parameters

    def _classify_method(self, method_name: str, method: Callable) -> str:
        """将方法分类"""
        if method_name == '__init__':
            return 'init'
        
        name_lower = method_name.lower()
        
        # Query methods
        query_patterns = ['get', 'find', 'search', 'query', 'lookup', 'fetch', 'read',
                         'check', 'is_', 'has_', 'can_', 'validate', 'verify', 'inspect',
                         'calculate', 'compute', 'evaluate', 'analyze', 'detect']
        if any(name_lower.startswith(p) or name_lower.startswith(p.replace('_', '')) for p in query_patterns):
            return 'query'
        
        # Side effect methods
        effect_patterns = ['set', 'write', 'update', 'delete', 'remove', 'add', 'insert',
                          'create', 'modify', 'change', 'trigger', 'emit', 'send',
                          'register', 'unregister', 'bind', 'unbind', 'attach', 'detach',
                          'start', 'stop', 'run', 'execute', 'perform', 'apply']
        if any(name_lower.startswith(p) or name_lower.startswith(p.replace('_', '')) for p in effect_patterns):
            return 'side_effect'
        
        # Core computation
        core_patterns = ['process', 'transform', 'convert', 'generate', 'build', 'construct',
                        'render', 'solve', 'optimize', 'train', 'predict', 'infer',
                        'encode', 'decode', 'encrypt', 'decrypt', 'hash', 'compress']
        if any(name_lower.startswith(p) for p in core_patterns):
            return 'core'
        
        return 'utility'

    def _get_or_create_instance(self, module_name: str, class_name: str, class_obj: type) -> Any:
        """获取或创建类实例"""
        cache_key = f"{module_name}.{class_name}"
        
        if cache_key in self._class_instances:
            return self._class_instances[cache_key]
        
            # Try to create instance with no args first
            instance = class_obj()
            self._class_instances[cache_key] = instance
            return instance
            pass
        
        # Try with generated args for __init__
            init_sig = inspect.signature(class_obj.__init__)
            init_args = {}
            for param_name, param in init_sig.parameters.items():
                if param_name == 'self':
                    continue
                if param.default is not inspect.Parameter.empty:
                    init_args[param_name] = param.default
                else:
                    init_args[param_name] = self.method_invoker._generate_from_name(param_name)
            
            instance = class_obj(**init_args)
            self._class_instances[cache_key] = instance
            return instance
            return None

    def invoke_method(self, module_name: str, class_name: str, method_name: str,
                     method: Callable, instance: Any = None,
                     args: Optional[Dict] = None) -> InvocationResult:
        """
        调用方法
        
        安全调用，捕获所有异常，记录结果到能力图谱。
        """
        result = self.method_invoker.safe_invoke(
            module_name=module_name,
            class_name=class_name,
            method_name=method_name,
            method=method,
            instance=instance,
            args=args
        )
        
        self.capability_map.add_capability(module_name, class_name, method_name, result)
        
        self.stats["invoked_methods"] += 1
        if result.status == InvocationStatus.SUCCESS:
            self.stats["successful_invocations"] += 1
        elif result.status == InvocationStatus.FAILED:
            self.stats["failed_invocations"] += 1
        elif result.status == InvocationStatus.SKIPPED:
            self.stats["skipped_methods"] += 1
        
        return result

    def explore_module(self, module_name: str, depth: str = 'full') -> Dict[str, Any]:
        """
        探索单个模块
        
        depth='full': 调用所有方法
        depth='quick': 只调用关键方法（非私有、非属性）
        """
        logger.info(f"\n[EXPLORE] Module: {module_name} (depth={depth})")
        
        module = self._load_module(module_name)
        if module is None:
            logger.info(f"[SKIP] Could not load module: {module_name}")
            return {"status": "failed", "reason": "load_failed"}
        
        results = {
            "module": module_name,
            "classes_explored": 0,
            "methods_invoked": 0,
            "success_count": 0,
            "fail_count": 0,
            "details": []
        }
        
        # Explore classes
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module_name:
                continue
            
            results["classes_explored"] += 1
            class_result = self._explore_class(module_name, name, obj, depth)
            results["methods_invoked"] += class_result["methods_invoked"]
            results["success_count"] += class_result["success_count"]
            results["fail_count"] += class_result["fail_count"]
            results["details"].append(class_result)
        
        # Explore module-level functions
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ != module_name:
                continue
            if name.startswith('_'):
                continue
            
            func_result = self._invoke_and_record(module_name, "<module>", name, obj, None)
            results["methods_invoked"] += 1
            if func_result.status == InvocationStatus.SUCCESS:
                results["success_count"] += 1
            else:
                results["fail_count"] += 1
        
        logger.info(f"[DONE] {module_name}: {results['success_count']}/{results['methods_invoked']} successful")
        return results

    def _explore_class(self, module_name: str, class_name: str,
                       class_obj: type, depth: str) -> Dict[str, Any]:
        """探索单个类"""
        result = {
            "class": class_name,
            "methods_invoked": 0,
            "success_count": 0,
            "fail_count": 0,
            "instance_created": False,
            "method_results": []
        }
        
        # Create instance (skip for Enum and exceptions)
        instance = None
        if not issubclass(class_obj, Enum) and not issubclass(class_obj, Exception):
            instance = self._get_or_create_instance(module_name, class_name, class_obj)
            if instance is not None:
                result["instance_created"] = True
        
        # Get methods
        methods = []
        for name, obj in inspect.getmembers(class_obj):
            if name.startswith('__') and name != '__init__':
                continue
            if not (inspect.isfunction(obj) or inspect.ismethod(obj)):
                continue
            
            # Skip if depth is quick and method is "private-like"
            if depth == 'quick' and name.startswith('_'):
                continue
            
            methods.append((name, obj))
        
        # Invoke methods
        for method_name, method_obj in methods:
            # Skip abstract methods
            if getattr(method_obj, '__isabstractmethod__', False):
                continue
            
            method_result = self._invoke_and_record(
                module_name, class_name, method_name, method_obj, instance
            )
            
            result["methods_invoked"] += 1
            if method_result.status == InvocationStatus.SUCCESS:
                result["success_count"] += 1
            else:
                result["fail_count"] += 1
            
            result["method_results"].append({
                "method": method_name,
                "status": method_result.status.value,
                "time": method_result.execution_time,
                "exception": method_result.exception
            })
        
        return result

    def _invoke_and_record(self, module_name: str, class_name: str,
                           method_name: str, method: Callable,
                           instance: Any) -> InvocationResult:
        """调用并记录结果"""
        args = self.method_invoker.generate_test_args(method, instance)
        
        # Prepare bound method
        if instance is not None:
            bound_method = getattr(instance, method_name, None)
            if bound_method is None or not callable(bound_method):
                bound_method = method
            result = self.invoke_method(
                module_name, class_name, method_name,
                bound_method, instance, args
            )
        else:
            result = self.invoke_method(
                module_name, class_name, method_name,
                method, None, args
            )
        
        return result

    def explore_all_modules(self, depth: str = 'full') -> Dict[str, Any]:
        """
        探索所有模块
        
        遍历所有模块，调用所有方法，生成完整的能力图谱。
        """
        self.stats["start_time"] = datetime.now().isoformat()
        
        logger.info("=" * 70)
        logger.info("OMNI-HUB v6.0 — FullPotentialExplorer")
        logger.info("全量潜能探索器启动")
        logger.info("=" * 70)
        
        modules = self.discover_modules()
        logger.info(f"\n[PHASE 1/4] 扫描完成 — 发现 {len(modules)} 个模块")
        
        logger.info(f"\n[PHASE 2/4] 开始探索模块 (depth={depth})")
        logger.info("-" * 70)
        
        all_results = {}
        for module_name in modules:
            if module_name in self.module_blacklist:
                continue
            result = self.explore_module(module_name, depth)
            all_results[module_name] = result
        
        logger.info("\n" + "=" * 70)
        logger.info("[PHASE 3/4] 探索完成 — 生成报告")
        logger.info("=" * 70)
        
        self.stats["end_time"] = datetime.now().isoformat()
        
        report = self.generate_potential_report()
        
        logger.info("\n" + "=" * 70)
        logger.info("[PHASE 4/4] 报告生成完成")
        logger.info("=" * 70)
        
        return {
            "stats": self.stats,
            "report": report,
            "module_results": all_results
        }

    def generate_capability_map(self) -> Dict[str, Any]:
        """
        生成能力图谱
        
        记录每个模块的每个方法的输出，生成能力矩阵。
        """
        coverage = self.capability_map.get_coverage()
        heatmap = self.capability_map.get_heatmap_data()
        sleeping = self.capability_map.get_sleeping_capabilities()
        
        # Count totals from discovered modules
        total_classes = sum(len(m.classes) for m in self.modules.values())
        total_methods = sum(
            len(c.methods) for m in self.modules.values() for c in m.classes
        )
        
        return {
            "coverage": coverage,
            "heatmap": heatmap,
            "sleeping_capabilities": sleeping,
            "total_modules": len(self.modules),
            "total_classes": total_classes,
            "total_methods": total_methods,
            "invocation_log_count": len(self.capability_map.invocation_log),
        }

    def generate_potential_report(self) -> str:
        """
        生成潜能报告
        
        统计：
        - 总模块数、总类数、总方法数
        - 已调用数、未调用数
        - 识别"沉睡"功能
        - 提出唤醒建议
        """
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("OMNI-HUB v6.0 — FullPotentialExplorer 潜能释放报告")
        lines.append("=" * 70)
        lines.append(f"生成时间: {datetime.now().isoformat()}")
        lines.append(f"探索深度: full")
        lines.append("")
        
        # Section 1: 总体统计
        lines.append("-" * 70)
        lines.append("【1. 总体统计】")
        lines.append("-" * 70)
        
        total_modules = self.stats["total_modules"]
        invoked = self.stats["invoked_methods"]
        success = self.stats["successful_invocations"]
        failed = self.stats["failed_invocations"]
        skipped = self.stats["skipped_methods"]
        
        lines.append(f"  总模块数:     {total_modules}")
        lines.append(f"  已调用方法:   {invoked}")
        lines.append(f"  成功调用:     {success}")
        lines.append(f"  失败调用:     {failed}")
        lines.append(f"  跳过方法:     {skipped}")
        
        if invoked > 0:
            success_rate = success / invoked * 100
            lines.append(f"  调用成功率:   {success_rate:.1f}%")
        
        # Section 2: 模块详情
        lines.append("")
        lines.append("-" * 70)
        lines.append("【2. 模块能力矩阵】")
        lines.append("-" * 70)
        
        for module_name in sorted(self.capability_map.capabilities.keys()):
            classes = self.capability_map.capabilities[module_name]
            total = 0
            success_count = 0
            for class_name, methods in classes.items():
                total += len(methods)
                success_count += sum(1 for m in methods.values() if m.get("status") == "success")
            
            rate = success_count / total * 100 if total > 0 else 0
            status_icon = "✓" if rate > 70 else "~" if rate > 30 else "✗"
            lines.append(f"  {status_icon} {module_name:40s} {success_count:3d}/{total:3d} ({rate:5.1f}%)")
        
        # Section 3: 沉睡功能
        lines.append("")
        lines.append("-" * 70)
        lines.append("【3. 沉睡功能识别】")
        lines.append("-" * 70)
        
        sleeping = self.capability_map.get_sleeping_capabilities(threshold=0.5)
        if sleeping:
            lines.append(f"  发现 {len(sleeping)} 个沉睡模块:")
            for item in sleeping[:10]:
                lines.append(f"    • {item['module']}: {item['success_rate']*100:.1f}% 成功率")
                lines.append(f"      建议: {item['recommendation']}")
        else:
            lines.append("  未发现沉睡模块（所有模块成功率 > 50%）")
        
        # Section 4: 能力热点
        lines.append("")
        lines.append("-" * 70)
        lines.append("【4. 能力热点分析】")
        lines.append("-" * 70)
        
        # Find most successful methods
        top_methods = []
        for result in self.method_invoker.results:
            if result.status == InvocationStatus.SUCCESS and result.execution_time > 0:
                top_methods.append({
                    "module": result.module_name,
                    "class": result.class_name,
                    "method": result.method_name,
                    "time": result.execution_time
                })
        
        top_methods.sort(key=lambda x: x["time"], reverse=True)
        lines.append("  执行时间最长的方法（Top 10）:")
        for m in top_methods[:10]:
            lines.append(f"    • {m['module']}.{m['class']}.{m['method']}: {m['time']:.3f}s")
        
        # Section 5: 异常分析
        lines.append("")
        lines.append("-" * 70)
        lines.append("【5. 异常分析】")
        lines.append("-" * 70)
        
        exceptions = {}
        for result in self.method_invoker.results:
            if result.exception:
                exc_type = result.exception.split(':')[0] if ':' in result.exception else 'Unknown'
                exceptions[exc_type] = exceptions.get(exc_type, 0) + 1
        
        if exceptions:
            lines.append("  异常类型统计:")
            for exc_type, count in sorted(exceptions.items(), key=lambda x: -x[1])[:10]:
                lines.append(f"    • {exc_type}: {count} 次")
        else:
            lines.append("  未发现异常")
        
        # Section 6: 唤醒建议
        lines.append("")
        lines.append("-" * 70)
        lines.append("【6. 唤醒建议汇总】")
        lines.append("-" * 70)
        
        lines.append("  1. 参数适配优化:")
        lines.append("     - 为需要复杂输入的方法提供智能参数生成器")
        lines.append("     - 增加类型注解覆盖率以提升参数推断准确率")
        lines.append("")
        lines.append("  2. 依赖注入优化:")
        lines.append("     - 检查模块间循环依赖")
        lines.append("     - 提供模拟依赖(mock)以支持独立测试")
        lines.append("")
        lines.append("  3. 初始化顺序优化:")
        lines.append("     - 确保基础模块先于高级模块初始化")
        lines.append("     - 为复杂类提供简化构造模式")
        lines.append("")
        lines.append("  4. 异常处理增强:")
        lines.append("     - 增加输入验证和边界检查")
        lines.append("     - 提供更详细的错误信息")
        
        # Section 7: 覆盖率总结
        lines.append("")
        lines.append("-" * 70)
        lines.append("【7. 覆盖率总结】")
        lines.append("-" * 70)
        
        coverage = self.capability_map.get_coverage()
        lines.append(f"  总方法数:        {coverage['total_methods']}")
        lines.append(f"  成功调用:        {coverage['success']}")
        lines.append(f"  失败调用:        {coverage['failed']}")
        lines.append(f"  跳过调用:        {coverage['skipped']}")
        lines.append(f"  调用成功率:      {coverage['success_rate']*100:.1f}%")
        lines.append(f"  探索覆盖率:      {coverage['exploration_rate']*100:.1f}%")
        
        lines.append("")
        lines.append("=" * 70)
        lines.append("报告结束")
        lines.append("=" * 70)
        
        return "\n".join(lines)

    def export_results(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """导出所有结果到文件"""
        if output_dir is None:
            output_dir = self.hub_dir / 'audit'
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export capability map
        cap_file = output_path / f"capability_map_{timestamp}.json"
        self.capability_map.export(str(cap_file))
        
        # Export report
        report_file = output_path / f"potential_report_{timestamp}.txt"
        report = self.generate_potential_report()
    with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Export statistics
        stats_file = output_path / f"explorer_stats_{timestamp}.json"
        stats_data = {
            "stats": self.stats,
            "coverage": self.capability_map.get_coverage(),
            "method_categories": {
                k: len(v) for k, v in self.method_categories.items()
            }
        }
    with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)
        
        return {
            "capability_map": str(cap_file),
            "report": str(report_file),
            "stats": str(stats_file)
        }


# =============================================================================
# 主程序入口
# =============================================================================

def main():
    """主程序"""
    logger.info("OMNI-HUB v6.0 — FullPotentialExplorer")
    logger.info("全量潜能探索器启动中...\n")
    
    explorer = FullPotentialExplorer()
    
    # Run full exploration
    results = explorer.explore_all_modules(depth='full')
    
    # Print report
    report = explorer.generate_potential_report()
    logger.info(str(report))
    
    # Export results
    logger.info("\n[EXPORT] 正在导出结果...")
    files = explorer.export_results()
    logger.info(f"[EXPORT] 能力图谱: {files['capability_map']}")
    logger.info(f"[EXPORT] 潜能报告: {files['report']}")
    logger.info(f"[EXPORT] 统计数据: {files['stats']}")
    
    return results


if __name__ == '__main__':
    main()
