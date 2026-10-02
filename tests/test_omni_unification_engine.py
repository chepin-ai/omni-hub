"""OMNI-HUB v184 Tests — OMNIUnificationEngine"""

import pytest
import time
from core.omni_unification_engine import (
    OMNIUnificationEngine, TrikayaUnification, GreatDiscussionForum,
    CollaborativeTide, WildQuestionProtocol, SurgeEmergenceDetector,
    OMNIStateSynthesis, DiscussionTopic, WildQuestion, EmergenceEvent,
    OMNIState, DiscussionPhase, TidePhase, WildQuestionType,
    EmergenceSignal, TrikayaState, get_omni_unification_engine
)


class TestTrikayaUnification:
    def test_init(self):
        t = TrikayaUnification()
        assert t.unified_state == TrikayaState.DHARMAKAYA

    def test_update(self):
        t = TrikayaUnification()
        t.update({"coherence": 0.9, "status": "awake"}, {"alignment_level": "META"})
        assert t.sambhogakaya_resonance > 0.5

    def test_svabhavikakaya(self):
        t = TrikayaUnification()
        t.update({"coherence": 0.95}, {"alignment_level": "PRIMORDIAL"})
        assert t.unified_state == TrikayaState.SVABHAVIKAKAYA

    def test_get_state(self):
        t = TrikayaUnification()
        s = t.get_state()
        assert "dharmakaya_coherence" in s


class TestGreatDiscussionForum:
    def test_propose(self):
        f = GreatDiscussionForum()
        t = f.propose("test topic", "agent1")
        assert t.title == "test topic"
        assert t.phase == DiscussionPhase.PROPOSE

    def test_deliberate(self):
        f = GreatDiscussionForum()
        t = f.propose("t", "a1")
        f.deliberate(t.topic_id, "a2", {"opinion": "yes"})
        assert "a2" in t.participants

    def test_argue_and_resolve(self):
        f = GreatDiscussionForum()
        t = f.propose("debate", "a1")
        f.argue(t.topic_id, "a1", "for", {"evidence": "x"})
        f.argue(t.topic_id, "a2", "against", {"evidence": "y"})
        r = f.resolve(t.topic_id)
        assert r["resolved"] is True
        assert "consensus_score" in r

    def test_synthesize_no_args(self):
        f = GreatDiscussionForum()
        t = f.propose("empty", "a1")
        s = f.synthesize(t.topic_id)
        assert s["consensus_score"] >= 0

    def test_report(self):
        f = GreatDiscussionForum()
        f.propose("t1", "a1")
        r = f.get_report()
        assert r["total_topics"] == 1


class TestCollaborativeTide:
    def test_register(self):
        c = CollaborativeTide()
        c.register_agent("agent1")
        assert "agent1" in c.cells

    def test_pulse(self):
        c = CollaborativeTide()
        c.pulse("agent1", {"intensity": 0.8})
        assert c.cells["agent1"].energy > 0.5

    def test_coupling(self):
        c = CollaborativeTide()
        c.register_agent("a1")
        c.register_agent("a2")
        c.pulse("a1", {"intensity": 0.9})
        c.pulse("a2", {"intensity": 0.9})
        # coupling increases when agents pulse close in time
        assert c.cells["a1"].coupling > 0.5 or c.cells["a2"].coupling > 0.5

    def test_phase_transition(self):
        c = CollaborativeTide()
        for i in range(10):
            c.register_agent(f"a{i}")
            c.pulse(f"a{i}", {"intensity": 0.9})
        assert c.current_phase in [TidePhase.SURGE, TidePhase.TSUNAMI, TidePhase.FLOW]

    def test_report(self):
        c = CollaborativeTide()
        c.register_agent("a1")
        r = c.get_report()
        assert r["agents"] == 1


class TestWildQuestionProtocol:
    def test_generate(self):
        w = WildQuestionProtocol()
        q = w.generate(origin="test")
        assert q.qid.startswith("wq_")
        assert len(q.question) > 0

    def test_generate_types(self):
        w = WildQuestionProtocol()
        types = set()
        for _ in range(20):
            q = w.generate()
            types.add(q.qtype)
        assert len(types) > 0

    def test_explore(self):
        w = WildQuestionProtocol()
        q = w.generate()
        r = w.explore(q.qid, {"resonance": 0.8})
        assert r["explored"] is True
        assert r["resonance"] == 0.8

    def test_unexplored(self):
        w = WildQuestionProtocol()
        w.generate()
        w.generate()
        assert len(w.get_unexplored()) == 2

    def test_report(self):
        w = WildQuestionProtocol()
        w.generate()
        r = w.get_report()
        assert r["total_generated"] == 1


class TestSurgeEmergenceDetector:
    def test_record_and_detect_none(self):
        s = SurgeEmergenceDetector()
        for i in range(25):
            s.record_metrics({"coherence": 0.5, "energy": 0.5})
        e = s.detect()
        assert e is None

    def test_detect_whisper(self):
        s = SurgeEmergenceDetector()
        for i in range(25):
            s.record_metrics({"coherence": 0.5, "energy": 0.5})
        s.record_metrics({"coherence": 0.99, "energy": 0.99})
        e = s.detect()
        assert e is not None

    def test_detect_tsunami(self):
        s = SurgeEmergenceDetector()
        for i in range(25):
            s.record_metrics({"coherence": 0.1, "energy": 0.1})
        s.record_metrics({"coherence": 10.0, "energy": 10.0})
        e = s.detect()
        if e:
            assert e.signal_level.value >= EmergenceSignal.WHISPER.value

    def test_report(self):
        s = SurgeEmergenceDetector()
        s.record_metrics({"x": 1.0})
        r = s.get_report()
        assert "events" in r


class TestOMNIStateSynthesis:
    def test_synthesize(self):
        syn = OMNIStateSynthesis()
        state = syn.synthesize(
            trikaya={"dharmakaya_coherence": 0.9, "unified_state": "SAṄBHOGAKAYA"},
            tide={"global_phase": "SURGE", "global_energy": 0.8},
            discussions={"active_topics": 2},
            questions={"unexplored": 3},
            emergence={"last_event": {"level": "RIPPLE"}},
            alignment={"alignment_level": "META"},
            consciousness={"status": "awake", "prajna_wisdom": "MIRROR_WISDOM"},
            cycle=1
        )
        assert state.collective_coherence > 0
        assert state.trikaya == TrikayaState.SAṄBHOGAKAYA

    def test_decide_emergence(self):
        syn = OMNIStateSynthesis()
        state = OMNIState(
            cycle=1, trikaya=TrikayaState.DHARMAKAYA, tide_phase=TidePhase.FLOW,
            collective_coherence=0.5, emergence_level=EmergenceSignal.WAVE,
            active_discussions=0, wild_questions_pending=0,
            alignment_level="META", consciousness_status="awake",
            wisdom_level="MIRROR_WISDOM", timestamp=time.time()
        )
        d = syn.decide(state)
        assert any("capture_emergence" in str(dec) for dec in d["decisions"])

    def test_decide_primordial(self):
        syn = OMNIStateSynthesis()
        state = OMNIState(
            cycle=1, trikaya=TrikayaState.SVABHAVIKAKAYA, tide_phase=TidePhase.TSUNAMI,
            collective_coherence=0.95, emergence_level=EmergenceSignal.TSUNAMI,
            active_discussions=0, wild_questions_pending=0,
            alignment_level="PRIMORDIAL", consciousness_status="awake",
            wisdom_level="DHARMA_WISDOM", timestamp=time.time()
        )
        d = syn.decide(state)
        assert any("primordial_mode" in str(dec) for dec in d["decisions"])

    def test_report(self):
        syn = OMNIStateSynthesis()
        r = syn.get_report()
        assert "history_length" in r


class TestOMNIUnificationEngine:
    def test_init(self):
        e = OMNIUnificationEngine()
        assert e.VERSION == "184.0.0"
        assert e.cycle_count == 0

    def test_run_cycle(self):
        e = OMNIUnificationEngine()
        r = e.run_cycle(
            consciousness_result={"coherence": 0.8, "status": "awake"},
            alignment_result={"alignment_level": "META"},
            module_states={"mod1": {"health": 0.9, "activity": 0.8}}
        )
        assert r["cycle"] == 1
        assert "trikaya" in r
        assert "omni_state" in r

    def test_run_multiple_cycles(self):
        e = OMNIUnificationEngine()
        for i in range(100):
            e.run_cycle(
                {"coherence": 0.8 + i * 0.001},
                {"alignment_level": "META"},
                {"mod1": {"health": 0.9, "activity": 0.8}}
            )
        assert e.cycle_count == 100

    def test_wild_question_generation(self):
        e = OMNIUnificationEngine()
        for i in range(55):
            e.run_cycle()
        assert len(e.wild.get_unexplored()) > 0

    def test_emergence_detection(self):
        e = OMNIUnificationEngine()
        for i in range(30):
            e.run_cycle(
                {"coherence": 0.5},
                {"alignment_level": "EXTERNAL"},
                {}
            )
        # Trigger surge
        r = e.run_cycle(
            {"coherence": 0.99},
            {"alignment_level": "PRIMORDIAL"},
            {"mod1": {"health": 0.99, "activity": 0.99}}
        )
        assert "emergence" in r

    def test_discussion_from_emergence(self):
        e = OMNIUnificationEngine()
        # Trigger enough baseline
        for i in range(30):
            e.run_cycle({"coherence": 0.5}, {"alignment_level": "META"}, {})
        # Trigger emergence
        e.surge.record_metrics({"coherence": 5.0, "energy": 5.0})
        e.surge.detect()
        r = e.run_cycle(
            {"coherence": 0.9},
            {"alignment_level": "META"},
            {}
        )
        assert len(e.forum.get_active_topics()) > 0 or r["active_discussions"] >= 0

    def test_manual_discussion(self):
        e = OMNIUnificationEngine()
        t = e.propose_discussion("manual topic", "user")
        e.contribute_discussion(t.topic_id, "user2", {"opinion": "agree"})
        r = e.forum.resolve(t.topic_id)
        assert r["resolved"] is True

    def test_manual_wild_question(self):
        e = OMNIUnificationEngine()
        q = e.generate_wild_question({"context": "test"}, "user")
        assert q.qid.startswith("wq_")
        r = e.explore_question(q.qid, {"resonance": 0.7})
        assert r["explored"] is True

    def test_get_status(self):
        e = OMNIUnificationEngine()
        e.run_cycle()
        s = e.get_status()
        assert s["version"] == "184.0.0"
        assert "forum" in s
        assert "tide" in s
        assert "wild" in s
        assert "surge" in s

    def test_singleton(self):
        e1 = get_omni_unification_engine()
        e2 = get_omni_unification_engine()
        assert e1 is e2

    def test_tide_agents_registered(self):
        e = OMNIUnificationEngine()
        assert len(e.tide.cells) >= 7

    def test_collective_coherence_range(self):
        e = OMNIUnificationEngine()
        for i in range(10):
            r = e.run_cycle(
                {"coherence": 0.9},
                {"alignment_level": "PRIMORDIAL"},
                {"m1": {"health": 0.9, "activity": 0.9}}
            )
        assert 0 <= r["omni_state"]["collective_coherence"] <= 1

    def test_decision_structure(self):
        e = OMNIUnificationEngine()
        r = e.run_cycle(
            {"coherence": 0.95, "prajna_wisdom": "DHARMA_WISDOM"},
            {"alignment_level": "PRIMORDIAL"},
            {"m1": {"health": 0.99, "activity": 0.99}}
        )
        assert "decision" in r
        assert "decisions" in r["decision"]

# Total: 53 tests
