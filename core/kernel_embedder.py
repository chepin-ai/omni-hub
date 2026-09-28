"""
OMNI-HUB Kernel Embedder v164
Universal engine for embedding any external system kernel into OMNI-HUB.

Concept: 内核嵌入器。通用引擎，将任何外部系统的内核嵌入OMNI-HUB。
不仅是QF-OS，任何操作系统、框架、引擎都可以被嵌入。内核嵌入器分析外部系统的架构，
提取其核心循环，将其转化为OMNI-HUB的内核模块。这是OMNI-HUB成为"元操作系统"的关键能力。

Philosophy: OMNI-HUB is not just an OS — it is a meta-OS that can absorb
and host the essence of any system. Every kernel becomes a citizen.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading
import copy


# Embedding stages
EMBEDDING_STAGE_NATIVE = "native"          # Fully integrated
EMBEDDING_STAGE_EMBEDDED = "embedded"      # Running
EMBEDDING_STAGE_TRANSLATING = "translating"  # Adapting
EMBEDDING_STAGE_ANALYZING = "analyzing"    # Under analysis
EMBEDDING_STAGE_FAILED = "failed"          # Failed to embed


@dataclass
class EmbeddedKernel:
    """Represents an external kernel that has been embedded into OMNI-HUB."""
    name: str
    kernel_type: str
    language: str
    loops: List[str]
    stage: str = EMBEDDING_STAGE_ANALYZING
    active: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    activated_at: Optional[str] = None
    deactivated_at: Optional[str] = None
    analysis: Dict[str, Any] = field(default_factory=dict)
    core_loop: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_log: List[str] = field(default_factory=list)


class KernelEmbedder:
    """
    Universal engine for embedding external system kernels into OMNI-HUB.
    
    Can embed operating systems, UI frameworks, autonomous navigation systems,
    and any other kernel-based architecture.
    """

    def __init__(self):
        self._embedded_kernels: Dict[str, EmbeddedKernel] = {}
        self._embedding_log: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def _log(self, action: str, kernel_name: str, details: Dict[str, Any] = None) -> None:
        """Record an embedding action to the log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "kernel_name": kernel_name,
            "details": details or {},
        }
        self._embedding_log.append(entry)

    def _publish_event(self, topic: str, payload: Dict[str, Any]) -> None:
        """Publish event to OMNI-HUB event bus with defensive error handling."""
        try:
            from core.event_bus import get_bus
            bus = get_bus()
            bus.publish_simple(topic, payload, source="kernel_embedder")
        except Exception:
            pass  # Event bus is optional; fail silently

    def analyze_kernel(self, kernel_name: str, kernel_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze external kernel architecture.
        
        Extracts: core_loops, data_structures, control_flow, interfaces, dependencies.
        
        Args:
            kernel_name: Unique identifier for the kernel
            kernel_spec: Kernel specification dictionary
            
        Returns:
            Analysis result dictionary
        """
        if not kernel_name or not isinstance(kernel_name, str):
            return {"success": False, "error": "Invalid kernel_name"}
        if not isinstance(kernel_spec, dict):
            return {"success": False, "error": "Invalid kernel_spec"}

        loops = kernel_spec.get("loops", [])
        lang = kernel_spec.get("lang", "unknown")
        kernel_type = kernel_spec.get("type", "unknown")

        # Analyze core loops
        core_loops = []
        for loop in loops:
            core_loops.append({
                "name": loop,
                "frequency": "primary" if loop == loops[0] else "secondary" if len(loops) > 1 else "primary",
                "type": "execution_loop",
                "language": lang,
            })

        # Infer data structures based on kernel type
        data_structures = self._infer_data_structures(kernel_type, loops)

        # Infer control flow
        control_flow = self._infer_control_flow(kernel_type, loops)

        # Infer interfaces
        interfaces = self._infer_interfaces(kernel_type, lang)

        # Infer dependencies
        dependencies = self._infer_dependencies(kernel_type, lang)

        analysis = {
            "kernel_name": kernel_name,
            "kernel_type": kernel_type,
            "language": lang,
            "core_loops": core_loops,
            "data_structures": data_structures,
            "control_flow": control_flow,
            "interfaces": interfaces,
            "dependencies": dependencies,
            "loop_count": len(loops),
            "complexity_score": len(loops) * len(dependencies) if dependencies else len(loops),
        }

        self._log("analyze", kernel_name, {"analysis_keys": list(analysis.keys())})
        self._publish_event("kernel.analyzed", {"kernel_name": kernel_name, "type": kernel_type})

        return {"success": True, "analysis": analysis}

    def _infer_data_structures(self, kernel_type: str, loops: List[str]) -> List[Dict[str, str]]:
        """Infer data structures based on kernel type and loops."""
        structures = []
        type_lower = kernel_type.lower()

        if "operating_system" in type_lower or "os" in type_lower:
            structures = [
                {"name": "task_struct", "type": "process_descriptor"},
                {"name": "page_table", "type": "memory_map"},
                {"name": "inode", "type": "file_descriptor"},
            ]
        elif "navigation" in type_lower or "autonomous" in type_lower:
            structures = [
                {"name": "sensor_grid", "type": "spatial_array"},
                {"name": "path_tree", "type": "graph"},
                {"name": "motion_queue", "type": "command_buffer"},
            ]
        elif "ui" in type_lower or "framework" in type_lower:
            structures = [
                {"name": "component_tree", "type": "virtual_dom"},
                {"name": "state_store", "type": "key_value"},
                {"name": "event_queue", "type": "async_buffer"},
            ]
        else:
            structures = [
                {"name": "generic_queue", "type": "fifo_buffer"},
                {"name": "state_registry", "type": "hash_map"},
            ]

        for i, loop in enumerate(loops):
            structures.append({"name": f"{loop}_context", "type": "execution_context"})

        return structures

    def _infer_control_flow(self, kernel_type: str, loops: List[str]) -> Dict[str, Any]:
        """Infer control flow patterns based on kernel type."""
        type_lower = kernel_type.lower()

        if "operating_system" in type_lower or "os" in type_lower:
            return {
                "pattern": "interrupt_driven",
                "scheduler": "preemptive",
                "concurrency": "multiprocessing",
            }
        elif "navigation" in type_lower or "autonomous" in type_lower:
            return {
                "pattern": "sense_plan_act",
                "scheduler": "event_driven",
                "concurrency": "async_pipeline",
            }
        elif "ui" in type_lower or "framework" in type_lower:
            return {
                "pattern": "event_reactive",
                "scheduler": "cooperative",
                "concurrency": "single_threaded_with_async",
            }
        else:
            return {
                "pattern": "sequential_loop",
                "scheduler": "round_robin",
                "concurrency": "none",
            }

    def _infer_interfaces(self, kernel_type: str, lang: str) -> List[Dict[str, str]]:
        """Infer interfaces based on kernel type and language."""
        interfaces = [
            {"name": "system_call", "type": "api"},
            {"name": "event_stream", "type": "pub_sub"},
        ]

        type_lower = kernel_type.lower()

        if "operating_system" in type_lower or "os" in type_lower:
            interfaces.extend([
                {"name": "syscall_table", "type": "function_pointer_array"},
                {"name": "device_driver_api", "type": "hardware_abstraction"},
            ])
        elif "navigation" in type_lower or "autonomous" in type_lower:
            interfaces.extend([
                {"name": "sensor_api", "type": "data_ingress"},
                {"name": "actuator_cmd", "type": "data_egress"},
            ])
        elif "ui" in type_lower or "framework" in type_lower:
            interfaces.extend([
                {"name": "component_api", "type": "declarative_interface"},
                {"name": "hook_system", "type": "callback_registry"},
            ])

        return interfaces

    def _infer_dependencies(self, kernel_type: str, lang: str) -> List[str]:
        """Infer dependencies based on kernel type and language."""
        type_lower = kernel_type.lower()
        deps = []

        if lang.lower() == "python":
            deps.extend(["python_runtime", "gil"])
        elif lang.lower() == "c":
            deps.extend(["libc", "posix_api"])
        elif lang.lower() == "javascript":
            deps.extend(["js_runtime", "event_loop"])

        if "operating_system" in type_lower or "os" in type_lower:
            deps.extend(["hardware_abstraction_layer", "bootloader", "memory_manager"])
        elif "navigation" in type_lower or "autonomous" in type_lower:
            deps.extend(["sensor_drivers", "motor_controllers", "localization_stack"])
        elif "ui" in type_lower or "framework" in type_lower:
            deps.extend(["render_engine", "dom_api", "event_system"])

        return deps

    def extract_core_loop(self, kernel_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the primary execution loop from the kernel.
        
        Args:
            kernel_spec: Kernel specification dictionary
            
        Returns:
            Core loop extraction result
        """
        if not isinstance(kernel_spec, dict):
            return {"success": False, "error": "Invalid kernel_spec"}

        loops = kernel_spec.get("loops", [])
        kernel_type = kernel_spec.get("type", "unknown")
        lang = kernel_spec.get("lang", "unknown")

        if not loops:
            return {"success": False, "error": "No loops defined in kernel_spec"}

        primary_loop = loops[0]
        secondary_loops = loops[1:] if len(loops) > 1 else []

        # Build loop graph showing how loops interact
        loop_graph = []
        for i, loop in enumerate(loops):
            next_loop = loops[(i + 1) % len(loops)] if len(loops) > 1 else None
            loop_graph.append({
                "loop": loop,
                "order": i,
                "next": next_loop,
                "type": "primary" if i == 0 else "secondary",
            })

        core_loop = {
            "primary_loop": primary_loop,
            "secondary_loops": secondary_loops,
            "all_loops": loops,
            "loop_graph": loop_graph,
            "loop_count": len(loops),
            "language": lang,
            "kernel_type": kernel_type,
            "execution_pattern": self._infer_control_flow(kernel_type, loops)["pattern"],
        }

        return {"success": True, "core_loop": core_loop}

    def embed_kernel(self, kernel_name: str, kernel_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Embed an external kernel into OMNI-HUB.
        
        Steps: analyze → extract → translate → integrate → activate
        
        Args:
            kernel_name: Unique identifier for the kernel
            kernel_spec: Kernel specification dictionary
            
        Returns:
            Embedding result dictionary
        """
        if not kernel_name or not isinstance(kernel_name, str):
            return {"success": False, "error": "Invalid kernel_name"}
        if not isinstance(kernel_spec, dict):
            return {"success": False, "error": "Invalid kernel_spec"}

        with self._lock:
            if kernel_name in self._embedded_kernels:
                return {
                    "success": False,
                    "error": f"Kernel '{kernel_name}' is already embedded",
                    "status": self._embedded_kernels[kernel_name].stage,
                }

        # Step 1: Analyze
        analysis_result = self.analyze_kernel(kernel_name, kernel_spec)
        if not analysis_result.get("success"):
            self._log("embed_failed", kernel_name, {"stage": "analyze", "error": analysis_result.get("error")})
            return {"success": False, "error": f"Analysis failed: {analysis_result.get('error')}"}

        # Step 2: Extract core loop
        extract_result = self.extract_core_loop(kernel_spec)
        if not extract_result.get("success"):
            self._log("embed_failed", kernel_name, {"stage": "extract", "error": extract_result.get("error")})
            return {"success": False, "error": f"Extraction failed: {extract_result.get('error')}"}

        # Step 3: Translate
        with self._lock:
            kernel = EmbeddedKernel(
                name=kernel_name,
                kernel_type=kernel_spec.get("type", "unknown"),
                language=kernel_spec.get("lang", "unknown"),
                loops=kernel_spec.get("loops", []),
                stage=EMBEDDING_STAGE_TRANSLATING,
                analysis=analysis_result.get("analysis", {}),
                core_loop=extract_result.get("core_loop", {}),
                metadata={
                    "embedded_by": "kernel_embedder_v164",
                    "embed_version": "164",
                },
            )
            self._embedded_kernels[kernel_name] = kernel

        self._log("translate", kernel_name, {"stage": EMBEDDING_STAGE_TRANSLATING})
        self._publish_event("kernel.translating", {"kernel_name": kernel_name})

        # Step 4: Integrate
        kernel.stage = EMBEDDING_STAGE_EMBEDDED
        self._log("integrate", kernel_name, {"stage": EMBEDDING_STAGE_EMBEDDED})
        self._publish_event("kernel.integrated", {"kernel_name": kernel_name})

        # Step 5: Activate
        activate_result = self.activate_embedded_kernel(kernel_name)
        if not activate_result.get("success"):
            kernel.stage = EMBEDDING_STAGE_FAILED
            self._log("embed_failed", kernel_name, {"stage": "activate", "error": activate_result.get("error")})
            return {"success": False, "error": f"Activation failed: {activate_result.get('error')}"}

        kernel.stage = EMBEDDING_STAGE_NATIVE
        self._log("embed_complete", kernel_name, {"stage": EMBEDDING_STAGE_NATIVE})
        self._publish_event("kernel.embedded", {"kernel_name": kernel_name, "type": kernel.kernel_type})

        return {
            "success": True,
            "kernel_name": kernel_name,
            "stage": kernel.stage,
            "active": kernel.active,
            "analysis": kernel.analysis,
            "core_loop": kernel.core_loop,
        }

    def activate_embedded_kernel(self, kernel_name: str) -> Dict[str, Any]:
        """
        Activate an embedded kernel.
        
        Args:
            kernel_name: Name of the embedded kernel to activate
            
        Returns:
            Activation result dictionary
        """
        if not kernel_name or not isinstance(kernel_name, str):
            return {"success": False, "error": "Invalid kernel_name"}

        with self._lock:
            kernel = self._embedded_kernels.get(kernel_name)
            if kernel is None:
                return {"success": False, "error": f"Kernel '{kernel_name}' not found"}

            if kernel.active:
                return {"success": True, "kernel_name": kernel_name, "status": "already_active"}

            kernel.active = True
            kernel.activated_at = datetime.now().isoformat()
            kernel.stage = EMBEDDING_STAGE_NATIVE

        self._log("activate", kernel_name, {"stage": kernel.stage})
        self._publish_event("kernel.activated", {"kernel_name": kernel_name})

        return {
            "success": True,
            "kernel_name": kernel_name,
            "status": "activated",
            "activated_at": kernel.activated_at,
        }

    def deactivate_kernel(self, kernel_name: str) -> Dict[str, Any]:
        """
        Safely deactivate an embedded kernel.
        
        Args:
            kernel_name: Name of the embedded kernel to deactivate
            
        Returns:
            Deactivation result dictionary
        """
        if not kernel_name or not isinstance(kernel_name, str):
            return {"success": False, "error": "Invalid kernel_name"}

        with self._lock:
            kernel = self._embedded_kernels.get(kernel_name)
            if kernel is None:
                return {"success": False, "error": f"Kernel '{kernel_name}' not found"}

            if not kernel.active:
                return {"success": True, "kernel_name": kernel_name, "status": "already_inactive"}

            # Safely shutdown: mark inactive before cleanup
            kernel.active = False
            kernel.deactivated_at = datetime.now().isoformat()
            kernel.stage = EMBEDDING_STAGE_EMBEDDED

        self._log("deactivate", kernel_name, {"stage": kernel.stage})
        self._publish_event("kernel.deactivated", {"kernel_name": kernel_name})

        return {
            "success": True,
            "kernel_name": kernel_name,
            "status": "deactivated",
            "deactivated_at": kernel.deactivated_at,
        }

    def get_kernel_status(self, kernel_name: str) -> Dict[str, Any]:
        """
        Get status of a specific embedded kernel.
        
        Args:
            kernel_name: Name of the embedded kernel
            
        Returns:
            Kernel status dictionary
        """
        if not kernel_name or not isinstance(kernel_name, str):
            return {"success": False, "error": "Invalid kernel_name"}

        with self._lock:
            kernel = self._embedded_kernels.get(kernel_name)
            if kernel is None:
                return {"success": False, "error": f"Kernel '{kernel_name}' not found"}

            return {
                "success": True,
                "kernel_name": kernel.name,
                "kernel_type": kernel.kernel_type,
                "language": kernel.language,
                "stage": kernel.stage,
                "active": kernel.active,
                "loops": kernel.loops,
                "created_at": kernel.created_at,
                "activated_at": kernel.activated_at,
                "deactivated_at": kernel.deactivated_at,
                "loop_count": len(kernel.loops),
                "metadata": kernel.metadata,
                "error_count": len(kernel.error_log),
            }

    def get_status(self) -> Dict[str, Any]:
        """
        Return overall status of the kernel embedder.
        
        Returns:
            Status dictionary with embedded count, active count, and history
        """
        with self._lock:
            embedded_count = len(self._embedded_kernels)
            active_count = sum(1 for k in self._embedded_kernels.values() if k.active)
            stage_counts = {}
            for k in self._embedded_kernels.values():
                stage_counts[k.stage] = stage_counts.get(k.stage, 0) + 1

            return {
                "embedded_count": embedded_count,
                "active_count": active_count,
                "inactive_count": embedded_count - active_count,
                "embedding_history_count": len(self._embedding_log),
                "stage_distribution": stage_counts,
                "embedded_kernels": [
                    {
                        "name": k.name,
                        "type": k.kernel_type,
                        "stage": k.stage,
                        "active": k.active,
                        "language": k.language,
                    }
                    for k in self._embedded_kernels.values()
                ],
            }

    def list_kernels(self) -> List[str]:
        """Return list of all embedded kernel names."""
        with self._lock:
            return list(self._embedded_kernels.keys())

    def remove_kernel(self, kernel_name: str) -> Dict[str, Any]:
        """
        Remove an embedded kernel from OMNI-HUB.
        
        Args:
            kernel_name: Name of the kernel to remove
            
        Returns:
            Removal result dictionary
        """
        if not kernel_name or not isinstance(kernel_name, str):
            return {"success": False, "error": "Invalid kernel_name"}

        with self._lock:
            kernel = self._embedded_kernels.get(kernel_name)
            if kernel is None:
                return {"success": False, "error": f"Kernel '{kernel_name}' not found"}

            if kernel.active:
                # Must deactivate first
                self.deactivate_kernel(kernel_name)

            del self._embedded_kernels[kernel_name]

        self._log("remove", kernel_name, {})
        self._publish_event("kernel.removed", {"kernel_name": kernel_name})

        return {"success": True, "kernel_name": kernel_name, "status": "removed"}


# Global singleton instance
_module: Optional[KernelEmbedder] = None


def get_kernel_embedder() -> KernelEmbedder:
    """Get the global KernelEmbedder singleton instance."""
    global _module
    if _module is None:
        _module = KernelEmbedder()
    return _module


def reset_kernel_embedder() -> None:
    """Reset the global KernelEmbedder instance (for testing)."""
    global _module
    _module = KernelEmbedder()
