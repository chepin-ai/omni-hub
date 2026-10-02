"""OMNI-HUB v187 Tests — OracleNetwork"""

import pytest
from core.oracle_network import (
    OracleNetwork, OracleRegistry, MultiOracleAggregator, OracleReputationTracker,
    ChainDataBridge, OracleConsensusEngine,
    OracleSource, OracleReading, AggregatedResult, OracleReputation,
    OracleStatus, AggregationMethod, DataDomain,
    get_oracle_network
)


class TestOracleRegistry:
    def test_register(self):
        r = OracleRegistry()
        o = OracleSource("s1", "Test", "url", DataDomain.PRICE, OracleStatus.ONLINE)
        assert r.register(o) is True
        assert "s1" in r.oracles

    def test_deregister(self):
        r = OracleRegistry()
        o = OracleSource("s1", "Test", "url", DataDomain.PRICE)
        r.register(o)
        assert r.deregister("s1") is True
        assert "s1" not in r.oracles

    def test_get_by_domain(self):
        r = OracleRegistry()
        r.register(OracleSource("s1", "T1", "u1", DataDomain.PRICE, OracleStatus.ONLINE))
        r.register(OracleSource("s2", "T2", "u2", DataDomain.WEATHER, OracleStatus.ONLINE))
        assert len(r.get_by_domain(DataDomain.PRICE)) == 1

    def test_get_online(self):
        r = OracleRegistry()
        r.register(OracleSource("s1", "T1", "u1", DataDomain.PRICE, OracleStatus.ONLINE))
        r.register(OracleSource("s2", "T2", "u2", DataDomain.PRICE, OracleStatus.OFFLINE))
        assert len(r.get_online()) == 1

    def test_report(self):
        r = OracleRegistry()
        r.register(OracleSource("s1", "T1", "u1", DataDomain.PRICE, OracleStatus.ONLINE))
        rep = r.get_report()
        assert rep["total"] == 1
        assert rep["online"] == 1


class TestMultiOracleAggregator:
    def test_aggregate_numeric(self):
        a = MultiOracleAggregator()
        readings = [
            OracleReading("r1", "s1", "q1", 1.0, 0.0),
            OracleReading("r2", "s2", "q1", 1.1, 0.0),
            OracleReading("r3", "s3", "q1", 1.2, 0.0),
        ]
        result = a.aggregate(readings, method=AggregationMethod.MEAN)
        assert result is not None
        assert result.consensus_reached is True
        assert 1.0 <= result.aggregated_value <= 1.2

    def test_aggregate_median(self):
        a = MultiOracleAggregator()
        readings = [
            OracleReading("r1", "s1", "q1", 1.0, 0.0),
            OracleReading("r2", "s2", "q1", 2.0, 0.0),
            OracleReading("r3", "s3", "q1", 3.0, 0.0),
        ]
        result = a.aggregate(readings, method=AggregationMethod.MEDIAN)
        assert result.aggregated_value == 2.0

    def test_aggregate_weighted(self):
        a = MultiOracleAggregator()
        readings = [
            OracleReading("r1", "s1", "q1", 1.0, 0.0),
            OracleReading("r2", "s2", "q1", 2.0, 0.0),
        ]
        result = a.aggregate(readings, method=AggregationMethod.WEIGHTED_MEAN,
                             weights={"s1": 1.0, "s2": 3.0})
        assert result is not None

    def test_aggregate_empty(self):
        a = MultiOracleAggregator()
        assert a.aggregate([]) is None

    def test_aggregate_non_numeric(self):
        a = MultiOracleAggregator()
        readings = [
            OracleReading("r1", "s1", "q1", "YES", 0.0),
            OracleReading("r2", "s2", "q1", "YES", 0.0),
            OracleReading("r3", "s3", "q1", "NO", 0.0),
        ]
        result = a.aggregate(readings)
        assert result.aggregated_value == "YES"

    def test_report(self):
        a = MultiOracleAggregator()
        r = a.get_report()
        assert "total_aggregations" in r


class TestOracleReputationTracker:
    def test_register(self):
        t = OracleReputationTracker()
        t.register("s1")
        assert "s1" in t.reputations

    def test_evaluate_correct(self):
        t = OracleReputationTracker()
        t.evaluate("s1", 1.0, 1.0)
        assert t.get_reputation("s1") > 0.5

    def test_evaluate_incorrect(self):
        t = OracleReputationTracker()
        t.evaluate("s1", 1.0, 2.0)
        assert t.get_reputation("s1") < 1.0

    def test_top_oracles(self):
        t = OracleReputationTracker()
        t.evaluate("s1", 1.0, 1.0)
        t.evaluate("s2", 2.0, 2.0)
        top = t.get_top_oracles(2)
        assert len(top) == 2

    def test_report(self):
        t = OracleReputationTracker()
        t.evaluate("s1", 1.0, 1.0)
        r = t.get_report()
        assert r["oracles_tracked"] == 1


class TestChainDataBridge:
    def test_register_bridge(self):
        b = ChainDataBridge()
        b.register_bridge("b1", "api", {"url": "http://test"})
        assert "b1" in b.bridges

    def test_submit_and_confirm(self):
        b = ChainDataBridge()
        b.register_bridge("b1", "api", {})
        tx = b.submit_offchain("b1", {"key": "value"})
        assert len(b.pending) == 1
        assert b.confirm(tx) is True
        assert len(b.confirmed) == 1

    def test_report(self):
        b = ChainDataBridge()
        r = b.get_report()
        assert "bridges" in r


class TestOracleConsensusEngine:
    def test_propose(self):
        c = OracleConsensusEngine()
        pid = c.propose("q1", 1.0, "proposer")
        assert pid.startswith("prop_")

    def test_vote_and_finalize(self):
        c = OracleConsensusEngine()
        pid = c.propose("q1", 1.0, "p1")
        c.vote(pid, "v1", 1.0, 1.0)
        c.vote(pid, "v2", 1.0, 1.0)
        r = c.finalize(pid)
        assert r["consensus"] is True

    def test_finalize_rejected(self):
        c = OracleConsensusEngine()
        pid = c.propose("q1", 1.0, "p1")
        c.vote(pid, "v1", 0.0, 1.0)
        c.vote(pid, "v2", 2.0, 1.0)
        r = c.finalize(pid)
        assert r["consensus"] is False

    def test_report(self):
        c = OracleConsensusEngine()
        c.propose("q1", 1.0, "p1")
        r = c.get_report()
        assert r["total_proposals"] == 1


class TestOracleNetwork:
    def test_init(self):
        on = OracleNetwork()
        assert on.VERSION == "187.0.0"

    def test_query(self):
        on = OracleNetwork()
        result = on.query("test_query")
        assert result is not None
        assert result.consensus_reached is True

    def test_run_cycle(self):
        on = OracleNetwork()
        r = on.run_cycle(["q1", "q2"])
        assert r["cycle"] == 1
        assert r["queries_processed"] == 2

    def test_get_status(self):
        on = OracleNetwork()
        on.run_cycle()
        s = on.get_status()
        assert s["version"] == "187.0.0"
        assert "registry" in s

    def test_singleton(self):
        o1 = get_oracle_network()
        o2 = get_oracle_network()
        assert o1 is o2

# Total: 34 tests
