import time
"""OMNI-HUB v192 Tests — CognitiveMirror"""

import pytest
from core.cognitive_mirror import (
    CognitiveMirror, SelfModel, OtherModel,
    PerspectiveTaker, BeliefTracker, IntentionInferencer,
    MirrorDepth, Perspective, BeliefState, Intention,
    get_cognitive_mirror
)


class TestSelfModel:
    def test_update_belief(self):
        sm = SelfModel("agent1")
        sm.update_belief("sky is blue", 0.9)
        assert len(sm.beliefs) == 1

    def test_set_intention(self):
        sm = SelfModel("agent1")
        sm.set_intention("align", 0.8)
        assert len(sm.intentions) == 1

    def test_self_awareness(self):
        sm = SelfModel("agent1")
        sm.update_belief("test", 0.9)
        sm.set_capability("reasoning", 0.8)
        assert sm.self_awareness_score > 0


class TestOtherModel:
    def test_observe(self):
        om = OtherModel()
        om.observe("agent2", "action1")
        assert "agent2" in om.models

    def test_infer_intention(self):
        om = OtherModel()
        intentions = om.infer_intention("agent2", ["a", "a", "b"])
        assert len(intentions) >= 1
        assert intentions[0].goal == "frequent:a"


class TestPerspectiveTaker:
    def test_take_perspective(self):
        pt = PerspectiveTaker()
        pm = pt.take_perspective("self", "other", {"key": "value"})
        assert pm.perspective_type == Perspective.OTHER
        assert len(pm.beliefs) == 1

    def test_compare_perspectives(self):
        pt = PerspectiveTaker()
        p1 = pt.take_perspective("a", "b", {"x": 1})
        p2 = pt.take_perspective("a", "c", {"x": 1})
        sim = pt.compare_perspectives(p1, p2)
        assert 0 <= sim <= 1


class TestBeliefTracker:
    def test_track(self):
        bt = BeliefTracker()
        b = BeliefState("b1", "a1", "test", 0.8, time.time())
        bt.track("a1", b)
        assert len(bt.belief_history) == 1

    def test_find_consensus(self):
        bt = BeliefTracker()
        for i in range(3):
            b = BeliefState(f"b{i}", f"a{i}", "common", 0.8, time.time())
            bt.track(f"a{i}", b)
        c = bt.find_consensus(min_agents=2)
        assert "common" in c


class TestIntentionInferencer:
    def test_infer_align(self):
        ii = IntentionInferencer()
        ints = ii.infer("a1", ["align_action"])
        assert any(i.goal == "alignment" for i in ints)

    def test_infer_default(self):
        ii = IntentionInferencer()
        ints = ii.infer("a1", ["unknown"])
        assert len(ints) >= 1


class TestCognitiveMirror:
    def test_init(self):
        cm = CognitiveMirror()
        assert cm.VERSION == "192.0.0"

    def test_reflect(self):
        cm = CognitiveMirror()
        r = cm.reflect({"health": 0.9})
        assert r["agent_id"] == "omni_hub"

    def test_observe_other(self):
        cm = CognitiveMirror()
        cm.observe_other("agent2", "action1")
        assert "agent2" in cm.other_model.models

    def test_infer_team_intentions(self):
        cm = CognitiveMirror()
        r = cm.infer_team_intentions({"a1": ["align", "optimize"]})
        assert "a1" in r

    def test_take_team_perspective(self):
        cm = CognitiveMirror()
        cm.observe_other("agent2", "action1")
        r = cm.take_team_perspective({"situation": "test"})
        assert "agent2" in r

    def test_run_cycle(self):
        cm = CognitiveMirror()
        r = cm.run_cycle(
            self_observation={"health": 0.9},
            other_observations={"agent2": ["align"]}
        )
        assert r["cycle"] == 1
        assert "self_awareness" in r

    def test_get_status(self):
        cm = CognitiveMirror()
        s = cm.get_status()
        assert s["version"] == "192.0.0"

    def test_singleton(self):
        c1 = get_cognitive_mirror()
        c2 = get_cognitive_mirror()
        assert c1 is c2

# Total: 24 tests
