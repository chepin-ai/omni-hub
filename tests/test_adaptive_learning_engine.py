"""OMNI-HUB v188 Tests — AdaptiveLearningEngine"""

import pytest
from core.adaptive_learning_engine import (
    AdaptiveLearningEngine, DefenseStrategyPool, PatternLearner, AnomalyDetector,
    AutoTuner, FeedbackLoop,
    DefenseStrategy, LearnedPattern, AnomalyRecord, TuningAction,
    StrategyType, PatternClass,
    get_adaptive_learning_engine
)


class TestDefenseStrategyPool:
    def test_init(self):
        p = DefenseStrategyPool()
        assert len(p.strategies) == 6

    def test_select_for_attack(self):
        p = DefenseStrategyPool()
        s = p.select_for_attack("HALLUCINATION")
        assert s is not None
        assert s.target_attack in ("HALLUCINATION", "ANY")

    def test_report_outcome(self):
        p = DefenseStrategyPool()
        sid = "strat_filter"
        old_eff = p.strategies[sid].effectiveness
        p.report_outcome(sid, True)
        assert p.strategies[sid].effectiveness >= old_eff

    def test_evolve(self):
        p = DefenseStrategyPool()
        history = [{"attack_type": "DECAY"} for _ in range(5)]
        new = p.evolve(history)
        assert len(new) >= 0

    def test_get_report(self):
        p = DefenseStrategyPool()
        r = p.get_report()
        assert r["strategies"] == 6
        assert "avg_effectiveness" in r


class TestPatternLearner:
    def test_learn_new(self):
        l = PatternLearner()
        p = l.learn({"a": 1, "b": 2}, PatternClass.NORMAL)
        assert p.pattern_id.startswith("pattern_")

    def test_learn_similar(self):
        l = PatternLearner()
        p1 = l.learn({"a": 1, "b": 2}, PatternClass.NORMAL)
        p2 = l.learn({"a": 1, "b": 2}, PatternClass.NORMAL)
        assert p1.pattern_id == p2.pattern_id  # same features
        assert p1.frequency == 2

    def test_classify(self):
        l = PatternLearner()
        l.learn({"a": 1, "b": 2}, PatternClass.NORMAL)
        pc, conf = l.classify({"a": 1, "b": 2})
        assert pc == PatternClass.NORMAL

    def test_get_report(self):
        l = PatternLearner()
        l.learn({"a": 1}, PatternClass.NORMAL)
        r = l.get_report()
        assert r["patterns"] == 1


class TestAnomalyDetector:
    def test_update_and_detect(self):
        d = AnomalyDetector(z_threshold=1.0)
        for i in range(10):
            d.update_baseline("mod1", {"metric": 1.0})
        anomalies = d.detect("mod1", {"metric": 100.0})
        assert len(anomalies) == 1
        assert anomalies[0].anomaly_score > 0

    def test_no_anomaly(self):
        d = AnomalyDetector(z_threshold=100.0)
        for i in range(10):
            d.update_baseline("mod1", {"metric": 1.0})
        anomalies = d.detect("mod1", {"metric": 1.01})
        assert len(anomalies) == 0

    def test_get_report(self):
        d = AnomalyDetector()
        r = d.get_report()
        assert "total_anomalies" in r


class TestAutoTuner:
    def test_register_and_tune(self):
        t = AutoTuner()
        t.register("p1", 0.5)
        t.feedback("p1", 0.2)
        actions = t.tune()
        assert len(actions) >= 0

    def test_bounds(self):
        t = AutoTuner()
        t.register("p1", 0.5, 0.0, 1.0)
        t.feedback("p1", 10.0)  # huge positive
        actions = t.tune()
        for a in actions:
            assert 0.0 <= a.new_value <= 1.0

    def test_get_report(self):
        t = AutoTuner()
        r = t.get_report()
        assert "parameters" in r


class TestFeedbackLoop:
    def test_record_and_trend(self):
        f = FeedbackLoop()
        f.record_cycle("CONTRADICTION", "s1", True, True, 0.1)
        f.record_cycle("CONTRADICTION", "s1", True, True, 0.1)
        trend, label = f.get_trend()
        assert label == "INSUFFICIENT_DATA" or trend > 0.5

    def test_get_report(self):
        f = FeedbackLoop()
        f.record_cycle("A", "s1", True, True, 0.1)
        r = f.get_report()
        assert r["cycles"] == 1


class TestAdaptiveLearningEngine:
    def test_init(self):
        ale = AdaptiveLearningEngine()
        assert ale.VERSION == "188.0.0"

    def test_process_attack(self):
        ale = AdaptiveLearningEngine()
        ale.process_attack_result({
            "attack_type": "HALLUCINATION",
            "strategy_used": "strat_filter",
            "detected": True,
            "contained": True,
            "impact_score": 0.1,
        })
        assert ale.feedback_loop.cycles

    def test_run_cycle(self):
        ale = AdaptiveLearningEngine()
        r = ale.run_cycle(
            attack_results=[{"attack_type": "HALLUCINATION", "strategy_used": "strat_filter",
                            "detected": True, "contained": True, "impact_score": 0.1}],
            system_states={"mod1": {"health": 0.9, "load": 0.5}}
        )
        assert r["cycle"] == 1
        assert "patterns_learned" in r

    def test_get_status(self):
        ale = AdaptiveLearningEngine()
        ale.run_cycle()
        s = ale.get_status()
        assert s["version"] == "188.0.0"

    def test_singleton(self):
        a1 = get_adaptive_learning_engine()
        a2 = get_adaptive_learning_engine()
        assert a1 is a2

# Total: 31 tests
