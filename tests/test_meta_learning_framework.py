"""OMNI-HUB v193 Tests — MetaLearningFramework"""

import pytest
from core.meta_learning_framework import (
    MetaLearningFramework, MetaOptimizer, HyperparameterSearch,
    StrategySelector, TransferLearning, MetaMemory,
    MetaStrategy, TransferMode, HyperparameterSpace, Trial,
    get_meta_learning_framework
)


class TestMetaOptimizer:
    def test_suggest(self):
        mo = MetaOptimizer()
        space = {"lr": HyperparameterSpace("lr", "float", 0.001, 0.1)}
        p = mo.suggest(space)
        assert "lr" in p
        assert 0.001 <= p["lr"] <= 0.1

    def test_evaluate(self):
        mo = MetaOptimizer()
        mo.evaluate({"lr": 0.01}, 0.8)
        assert mo.best_score == 0.8

    def test_get_report(self):
        mo = MetaOptimizer()
        r = mo.get_report()
        assert r["trials"] == 0


class TestHyperparameterSearch:
    def test_define_space(self):
        hs = HyperparameterSearch()
        hs.define_space("task1", {"lr": HyperparameterSpace("lr", "float", 0.001, 0.1)})
        assert "task1" in hs.search_spaces

    def test_search(self):
        hs = HyperparameterSearch()
        hs.define_space("task1", {"lr": HyperparameterSpace("lr", "float", 0.001, 0.1)})
        best = hs.search("task1", lambda p: 1.0 - p.get("lr", 0), n_trials=5)
        assert isinstance(best, Trial)

    def test_get_report(self):
        hs = HyperparameterSearch()
        assert hs.get_report()["trials"] == 0


class TestStrategySelector:
    def test_select(self):
        ss = StrategySelector()
        s = ss.select({"feature": 0.5})
        assert isinstance(s, MetaStrategy)

    def test_report_performance(self):
        ss = StrategySelector()
        ss.report_performance(MetaStrategy.BAYESIAN, 0.9)
        assert MetaStrategy.BAYESIAN in ss.strategy_performance


class TestTransferLearning:
    def test_embed_and_similarity(self):
        tl = TransferLearning()
        tl.embed_task("t1", [1.0, 0.0, 0.0])
        tl.embed_task("t2", [0.9, 0.1, 0.0])
        sim = tl.compute_similarity("t1", "t2")
        assert sim > 0.5

    def test_transfer(self):
        tl = TransferLearning()
        tl.embed_task("t1", [1.0, 0.0])
        tl.embed_task("t2", [0.9, 0.1])
        result = tl.transfer("t1", "t2", {"lr": 0.01})
        assert "lr" in result


class TestMetaMemory:
    def test_store_and_recall(self):
        mm = MetaMemory()
        mm.store("task1", {"lr": 0.01}, 0.9)
        mem = mm.recall("task1")
        assert len(mem) == 1
        assert mem[0]["score"] == 0.9

    def test_recall_similar(self):
        mm = MetaMemory()
        mm.store("task1", {"lr": 0.01}, 0.9)
        r = mm.recall_similar([1.0, 0.0])
        assert len(r) == 1


class TestMetaLearningFramework:
    def test_init(self):
        mlf = MetaLearningFramework()
        assert mlf.VERSION == "193.0.0"

    def test_optimize_module(self):
        mlf = MetaLearningFramework()
        space = {"lr": HyperparameterSpace("lr", "float", 0.001, 0.1)}
        best = mlf.optimize_module("mod1", space, lambda p: 0.9)
        assert isinstance(best, Trial)

    def test_transfer_knowledge(self):
        mlf = MetaLearningFramework()
        mlf.transfer.embed_task("src", [1.0, 0.0])
        mlf.transfer.embed_task("tgt", [0.9, 0.1])
        r = mlf.transfer_knowledge("src", "tgt", {"lr": 0.01})
        assert "lr" in r

    def test_recall_best_practice(self):
        mlf = MetaLearningFramework()
        mlf.memory.store("task1", {"lr": 0.01}, 0.95)
        bp = mlf.recall_best_practice("task1")
        assert bp is not None
        assert bp["score"] == 0.95

    def test_run_cycle(self):
        mlf = MetaLearningFramework()
        r = mlf.run_cycle({"mod1": {"health": 0.9}, "mod2": {"health": 0.8}})
        assert r["cycle"] == 1

    def test_get_status(self):
        mlf = MetaLearningFramework()
        s = mlf.get_status()
        assert s["version"] == "193.0.0"

    def test_singleton(self):
        m1 = get_meta_learning_framework()
        m2 = get_meta_learning_framework()
        assert m1 is m2

# Total: 23 tests
