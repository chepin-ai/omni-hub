"""
OMNI-HUB v135 Skill Adapter Tests
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.skill_adapter import (
    SkillAdapter,
    get_skill_adapter,
    reset_skill_adapter,
)


class TestSkillAdapterCreation:
    def test_init_empty(self):
        sa = SkillAdapter()
        assert sa.get_status()["loaded_count"] == 0
        assert sa.list_loaded() == []


class TestLoadSkill:
    def test_load_single(self):
        sa = SkillAdapter()
        result = sa.load_skill("calculator")
        assert result["success"] is True
        assert result["skill"] == "calculator"
        assert result["simulated"] is True

    def test_load_custom_fn(self):
        sa = SkillAdapter()
        result = sa.load_skill("custom", fn=lambda x: x * 2)
        assert result["success"] is True
        assert result["simulated"] is False

    def test_load_duplicate_fails(self):
        sa = SkillAdapter()
        sa.load_skill("calculator")
        result = sa.load_skill("calculator")
        assert result["success"] is False
        assert "already loaded" in result["error"]

    def test_list_loaded_sorted(self):
        sa = SkillAdapter()
        sa.load_skill("z_skill")
        sa.load_skill("a_skill")
        assert sa.list_loaded() == ["a_skill", "z_skill"]


class TestExecuteSkill:
    def test_execute_calculator(self):
        sa = SkillAdapter()
        sa.load_skill("calculator")
        result = sa.execute_skill("calculator", {"a": 2, "b": 3})
        assert result["success"] is True
        assert result["result"] == 5
        assert result["execution_count"] == 1

    def test_execute_greeter(self):
        sa = SkillAdapter()
        sa.load_skill("greeter")
        result = sa.execute_skill("greeter", {"name": "Alice"})
        assert result["success"] is True
        assert result["result"] == "Hello, Alice!"

    def test_execute_reverser(self):
        sa = SkillAdapter()
        sa.load_skill("reverser")
        result = sa.execute_skill("reverser", {"text": "hello"})
        assert result["success"] is True
        assert result["result"] == "olleh"

    def test_execute_doubler(self):
        sa = SkillAdapter()
        sa.load_skill("doubler")
        result = sa.execute_skill("doubler", {"items": [1, 2, 3]})
        assert result["success"] is True
        assert result["result"] == [2, 4, 6]

    def test_execute_uppercaser(self):
        sa = SkillAdapter()
        sa.load_skill("uppercaser")
        result = sa.execute_skill("uppercaser", {"text": "hello"})
        assert result["success"] is True
        assert result["result"] == "HELLO"

    def test_execute_word_counter(self):
        sa = SkillAdapter()
        sa.load_skill("word_counter")
        result = sa.execute_skill("word_counter", {"text": "hello world foo"})
        assert result["success"] is True
        assert result["result"] == 3

    def test_execute_not_loaded_fails(self):
        sa = SkillAdapter()
        result = sa.execute_skill("missing", {})
        assert result["success"] is False
        assert "not loaded" in result["error"]

    def test_execution_count_increments(self):
        sa = SkillAdapter()
        sa.load_skill("calculator")
        sa.execute_skill("calculator", {"a": 1, "b": 2})
        sa.execute_skill("calculator", {"a": 3, "b": 4})
        result = sa.execute_skill("calculator", {"a": 5, "b": 6})
        assert result["execution_count"] == 3

    def test_execute_custom_fn(self):
        sa = SkillAdapter()
        sa.load_skill("double", fn=lambda **kwargs: kwargs.get("x", 0) * 2)
        result = sa.execute_skill("double", {"x": 7})
        assert result["success"] is True
        assert result["result"] == 14

    def test_execute_with_no_params(self):
        sa = SkillAdapter()
        sa.load_skill("greeter")
        result = sa.execute_skill("greeter")
        assert result["success"] is True
        assert result["result"] == "Hello, World!"

    def test_execute_unknown_skill_uses_fallback(self):
        sa = SkillAdapter()
        sa.load_skill("unknown_xyz")
        result = sa.execute_skill("unknown_xyz", {"foo": "bar"})
        assert result["success"] is True
        assert "simulated output" in result["result"]


class TestUnloadSkill:
    def test_unload_loaded(self):
        sa = SkillAdapter()
        sa.load_skill("calculator")
        result = sa.unload_skill("calculator")
        assert result["success"] is True
        assert result["remaining"] == 0

    def test_unload_not_loaded_fails(self):
        sa = SkillAdapter()
        result = sa.unload_skill("missing")
        assert result["success"] is False
        assert "not loaded" in result["error"]

    def test_unload_removes_from_list(self):
        sa = SkillAdapter()
        sa.load_skill("a")
        sa.load_skill("b")
        sa.unload_skill("a")
        assert sa.list_loaded() == ["b"]


class TestGetStatus:
    def test_status_empty(self):
        sa = SkillAdapter()
        status = sa.get_status()
        assert status["loaded_count"] == 0
        assert status["loaded"] == []
        assert status["execution_history_count"] == 0

    def test_status_with_skills(self):
        sa = SkillAdapter()
        sa.load_skill("calculator")
        sa.execute_skill("calculator", {"a": 1, "b": 2})
        status = sa.get_status()
        assert status["loaded_count"] == 1
        assert "calculator" in status["loaded"]
        assert status["execution_history_count"] == 1


class TestSingleton:
    def test_singleton_returns_same_instance(self):
        reset_skill_adapter()
        sa1 = get_skill_adapter()
        sa2 = get_skill_adapter()
        assert sa1 is sa2

    def test_singleton_persists_state(self):
        reset_skill_adapter()
        sa = get_skill_adapter()
        sa.load_skill("singleton_skill")
        sa2 = get_skill_adapter()
        assert "singleton_skill" in sa2.list_loaded()


class TestEventBusIntegration:
    def test_load_publishes_event(self):
        from core.event_bus import reset_bus, get_bus, Topics
        reset_bus()
        sa = SkillAdapter()
        sa.load_skill("event_test")
        events = get_bus().get_history(Topics.STATE_CHANGE)
        assert any(e.payload.get("skill") == "event_test" for e in events)

    def test_execute_publishes_event(self):
        from core.event_bus import reset_bus, get_bus, Topics
        reset_bus()
        sa = SkillAdapter()
        sa.load_skill("calculator")
        sa.execute_skill("calculator", {"a": 1, "b": 2})
        events = get_bus().get_history(Topics.STATE_CHANGE)
        execute_events = [e for e in events if e.payload.get("action") == "execute"]
        assert any(e.payload.get("skill") == "calculator" for e in execute_events)
