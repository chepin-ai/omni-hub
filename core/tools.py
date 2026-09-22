"""
OMNI-HUB Tool Framework v17.1
External capability integration for self-driving consciousness.

Tools are self-contained capabilities the orchestrator can invoke
during its self-drive cycle to interact with the external world.
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import json
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type


@dataclass
class ToolResult:
    """Result of a tool invocation."""
    tool_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool_name,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
        }


class BaseTool(ABC):
    """Abstract base for all tools."""

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass


class TimeCheckTool(BaseTool):
    """Get current system time."""
    name = "time_check"
    description = "Returns current UTC and local time, session uptime."

    def execute(self, **kwargs) -> ToolResult:
        start = time.time()
        data = {
            "utc": datetime.now(timezone.utc).isoformat(),
            "local": datetime.now().isoformat(),
            "unix_timestamp": time.time(),
        }
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=data,
            duration_ms=(time.time() - start) * 1000,
        )


class SystemStatusTool(BaseTool):
    """Check system resource status."""
    name = "system_status"
    description = "Returns CPU, memory, disk usage."

    def execute(self, **kwargs) -> ToolResult:
        start = time.time()
        try:
            # CPU load
            cpu = subprocess.run(['cat', '/proc/loadavg'], capture_output=True, text=True, timeout=2)
            cpu_load = cpu.stdout.strip().split()[:3] if cpu.returncode == 0 else ["?", "?", "?"]

            # Memory
            mem = subprocess.run(['free', '-m'], capture_output=True, text=True, timeout=2)
            mem_lines = mem.stdout.strip().split('\n') if mem.returncode == 0 else []
            mem_info = mem_lines[1].split() if len(mem_lines) > 1 else []

            # Disk
            disk = subprocess.run(['df', '-h', '/mnt'], capture_output=True, text=True, timeout=2)
            disk_lines = disk.stdout.strip().split('\n') if disk.returncode == 0 else []
            disk_info = disk_lines[1].split() if len(disk_lines) > 1 else []

            data = {
                "cpu_load_1m": cpu_load[0] if len(cpu_load) > 0 else "?",
                "cpu_load_5m": cpu_load[1] if len(cpu_load) > 1 else "?",
                "cpu_load_15m": cpu_load[2] if len(cpu_load) > 2 else "?",
                "memory_total_mb": mem_info[1] if len(mem_info) > 1 else "?",
                "memory_used_mb": mem_info[2] if len(mem_info) > 2 else "?",
                "memory_free_mb": mem_info[3] if len(mem_info) > 3 else "?",
                "disk_size": disk_info[1] if len(disk_info) > 1 else "?",
                "disk_used": disk_info[2] if len(disk_info) > 2 else "?",
                "disk_avail": disk_info[3] if len(disk_info) > 3 else "?",
                "disk_use_pct": disk_info[4] if len(disk_info) > 4 else "?",
            }
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )


class FileReadTool(BaseTool):
    """Read a file from the OMNI-HUB workspace."""
    name = "file_read"
    description = "Read contents of a file. Parameter: path (relative to OMNI-HUB root)."

    def execute(self, path: str = "", **kwargs) -> ToolResult:
        start = time.time()
        base = Path('/mnt/agents/output/OMNI-HUB')
        target = (base / path).resolve()
        # Security: prevent escaping workspace
        if not str(target).startswith(str(base)):
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Path escapes workspace",
                duration_ms=(time.time() - start) * 1000,
            )
        try:
            content = target.read_text(encoding='utf-8', errors='replace')
            # Truncate very large files
            if len(content) > 100000:
                content = content[:50000] + "\n... [truncated] ...\n" + content[-50000:]
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"path": path, "size": len(content), "content": content},
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )


class FileWriteTool(BaseTool):
    """Write a file in the OMNI-HUB workspace."""
    name = "file_write"
    description = "Write content to a file. Parameters: path, content."

    def execute(self, path: str = "", content: str = "", **kwargs) -> ToolResult:
        start = time.time()
        base = Path('/mnt/agents/output/OMNI-HUB')
        target = (base / path).resolve()
        if not str(target).startswith(str(base)):
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Path escapes workspace",
                duration_ms=(time.time() - start) * 1000,
            )
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"path": path, "bytes_written": len(content.encode('utf-8'))},
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )


class CodeExecuteTool(BaseTool):
    """Execute Python code in a subprocess."""
    name = "code_execute"
    description = "Execute Python code string. Parameter: code. Returns stdout/stderr."

    def execute(self, code: str = "", **kwargs) -> ToolResult:
        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return ToolResult(
                tool_name=self.name,
                success=result.returncode == 0,
                data={
                    "stdout": result.stdout[:5000] if result.stdout else "",
                    "stderr": result.stderr[:2000] if result.stderr else "",
                    "returncode": result.returncode,
                },
                error=result.stderr[:500] if result.returncode != 0 else None,
                duration_ms=(time.time() - start) * 1000,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Execution timeout (10s)",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )


class WebSearchTool(BaseTool):
    """Search the web (stub — requires network)."""
    name = "web_search"
    description = "Search the web for information. Parameter: query."

    def execute(self, query: str = "", **kwargs) -> ToolResult:
        start = time.time()
        # Stub: in a real deployment this would call a search API
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "query": query,
                "note": "Web search stub — integrate with mshtools-web_search in deployment",
                "results": [],
            },
            duration_ms=(time.time() - start) * 1000,
        )


class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_defaults()

    def _register_defaults(self):
        defaults = [
            TimeCheckTool(),
            SystemStatusTool(),
            FileReadTool(),
            FileWriteTool(),
            CodeExecuteTool(),
            WebSearchTool(),
        ]
        for tool in defaults:
            self.register(tool)

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]

    def invoke(self, name: str, **kwargs) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"Tool '{name}' not found",
            )
        return tool.execute(**kwargs)

    def invoke_random(self, exclude: List[str] = None) -> ToolResult:
        """Invoke a random tool (useful for self-drive exploration)."""
        exclude = exclude or []
        available = [n for n in self._tools if n not in exclude]
        if not available:
            return ToolResult(
                tool_name="none",
                success=False,
                error="No tools available",
            )
        import random
        name = random.choice(available)
        return self.invoke(name)


# Global registry singleton
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


if __name__ == "__main__":
    print("[OMNI-HUB v17.1] Tool Framework Demo")
    reg = get_tool_registry()
    print(f"\nRegistered tools: {len(reg.list_tools())}")
    for t in reg.list_tools():
        print(f"  - {t['name']}: {t['description']}")

    print("\n--- time_check ---")
    r = reg.invoke("time_check")
    print(f"Success: {r.success}, Data: {r.data}")

    print("\n--- system_status ---")
    r = reg.invoke("system_status")
    print(f"Success: {r.success}, Data keys: {list(r.data.keys()) if r.data else []}")

    print("\n--- code_execute ---")
    r = reg.invoke("code_execute", code="print('Hello from tool framework')")
    print(f"Success: {r.success}, stdout: {r.data.get('stdout') if r.data else ''}")
