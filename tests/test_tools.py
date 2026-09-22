"""
OMNI-HUB Tool Framework Tests v17.1
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.tools import (
    ToolRegistry, ToolResult,
    TimeCheckTool, SystemStatusTool,
    FileReadTool, FileWriteTool, CodeExecuteTool,
    get_tool_registry,
)


class TestToolRegistry:
    def test_singleton(self):
        r1 = get_tool_registry()
        r2 = get_tool_registry()
        assert r1 is r2

    def test_default_tools_registered(self):
        reg = ToolRegistry()
        tools = reg.list_tools()
        names = [t['name'] for t in tools]
        assert "time_check" in names
        assert "system_status" in names
        assert "file_read" in names
        assert "file_write" in names
        assert "code_execute" in names
        assert "web_search" in names

    def test_invoke_unknown_tool(self):
        reg = ToolRegistry()
        result = reg.invoke("nonexistent_tool")
        assert not result.success
        assert "not found" in result.error

    def test_invoke_random(self):
        reg = ToolRegistry()
        result = reg.invoke_random()
        assert isinstance(result, ToolResult)
        assert result.tool_name != "none"

    def test_invoke_random_with_exclude(self):
        reg = ToolRegistry()
        # Exclude all tools
        all_names = [t['name'] for t in reg.list_tools()]
        result = reg.invoke_random(exclude=all_names)
        assert not result.success


class TestTimeCheckTool:
    def test_execute(self):
        tool = TimeCheckTool()
        result = tool.execute()
        assert result.success
        assert "utc" in result.data
        assert "local" in result.data
        assert "unix_timestamp" in result.data


class TestSystemStatusTool:
    def test_execute(self):
        tool = SystemStatusTool()
        result = tool.execute()
        assert result.success
        assert "cpu_load_1m" in result.data
        assert "memory_total_mb" in result.data
        assert "disk_use_pct" in result.data


class TestFileReadTool:
    def test_execute_success(self):
        # First write a test file
        write_tool = FileWriteTool()
        write_tool.execute(path="test_data/tool_test.txt", content="hello tools")

        tool = FileReadTool()
        result = tool.execute(path="test_data/tool_test.txt")
        assert result.success
        assert result.data["content"] == "hello tools"

    def test_execute_not_found(self):
        tool = FileReadTool()
        result = tool.execute(path="nonexistent_file_xyz.txt")
        assert not result.success

    def test_execute_escape_workspace(self):
        tool = FileReadTool()
        result = tool.execute(path="../../../etc/passwd")
        assert not result.success
        assert "escapes" in result.error


class TestFileWriteTool:
    def test_execute_success(self):
        tool = FileWriteTool()
        result = tool.execute(path="test_data/write_test.txt", content="written")
        assert result.success
        assert result.data["bytes_written"] > 0

    def test_execute_escape_workspace(self):
        tool = FileWriteTool()
        result = tool.execute(path="/tmp/outside.txt", content="x")
        assert not result.success


class TestCodeExecuteTool:
    def test_execute_success(self):
        tool = CodeExecuteTool()
        result = tool.execute(code="print(2+2)")
        assert result.success
        assert "4" in result.data["stdout"]
        assert result.data["returncode"] == 0

    def test_execute_error(self):
        tool = CodeExecuteTool()
        result = tool.execute(code="raise ValueError('test')")
        assert not result.success
        assert "ValueError" in result.data["stderr"]

    def test_execute_timeout(self):
        tool = CodeExecuteTool()
        result = tool.execute(code="import time; time.sleep(20)")
        assert not result.success
        assert "timeout" in result.error.lower()


class TestToolResult:
    def test_to_dict(self):
        result = ToolResult(tool_name="test", success=True, data={"x": 1})
        d = result.to_dict()
        assert d["tool"] == "test"
        assert d["success"] is True
        assert d["data"]["x"] == 1
