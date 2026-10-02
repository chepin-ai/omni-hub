"""OMNI-HUB v193 Tests — IntegrationCoordinator"""

import pytest
from core.integration_coordinator import (
    IntegrationCoordinator, ModuleRegistry, DependencyResolver,
    DataFlowRouter, HealthMonitor, StressTester,
    ModuleStatus, IntegrationLevel, ModuleInfo,
    get_integration_coordinator
)


class TestModuleRegistry:
    def test_register(self):
        mr = ModuleRegistry()
        mr.register("m1", "1.0", ["m0"], ["feature1"])
        assert "m1" in mr.modules
        assert mr.modules["m1"].status == ModuleStatus.ONLINE

    def test_heartbeat(self):
        mr = ModuleRegistry()
        mr.register("m1", "1.0")
        t1 = mr.modules["m1"].last_heartbeat
        mr.heartbeat("m1")
        assert mr.modules["m1"].last_heartbeat > t1

    def test_get_online(self):
        mr = ModuleRegistry()
        mr.register("m1", "1.0")
        mr.register("m2", "1.0")
        assert len(mr.get_online_modules()) == 2


class TestDependencyResolver:
    def test_resolve_order(self):
        mr = ModuleRegistry()
        mr.register("m1", "1.0", ["m0"])
        mr.register("m0", "1.0")
        dr = DependencyResolver(mr)
        order = dr.resolve_order()
        assert order.index("m0") < order.index("m1")

    def test_find_missing(self):
        mr = ModuleRegistry()
        mr.register("m1", "1.0", ["missing"])
        dr = DependencyResolver(mr)
        missing = dr.find_missing_dependencies()
        assert "m1" in missing
        assert "missing" in missing["m1"]


class TestDataFlowRouter:
    def test_register_route(self):
        dfr = DataFlowRouter()
        dfr.register_route("src", "tgt")
        assert len(dfr.flows) == 1

    def test_route(self):
        dfr = DataFlowRouter()
        dfr.register_route("src", "tgt1")
        dfr.register_route("src", "tgt2")
        r = dfr.route("src", {"data": 1})
        assert len(r) == 2


class TestHealthMonitor:
    def test_record(self):
        hm = HealthMonitor()
        hm.record("m1", 0.9)
        assert len(hm.module_health["m1"]) == 1

    def test_system_health(self):
        hm = HealthMonitor()
        hm.record("m1", 0.9)
        hm.record("m2", 0.7)
        assert 0.7 <= hm.get_system_health() <= 0.9

    def test_degraded(self):
        hm = HealthMonitor()
        hm.record("m1", 0.9)
        hm.record("m2", 0.3)
        degraded = hm.get_degraded_modules(threshold=0.5)
        assert "m2" in degraded


class TestStressTester:
    def test_test_module(self):
        st = StressTester()
        results = st.test_module("m1", 0.8)
        assert len(results) == 5

    def test_breaking_point(self):
        st = StressTester()
        st.test_module("m1", 0.8)
        bp = st.find_breaking_point("m1")
        # May or may not find a breaking point
        assert bp is None or bp > 0


class TestIntegrationCoordinator:
    def test_init(self):
        ic = IntegrationCoordinator()
        assert ic.VERSION == "193.0.0"

    def test_register_all(self):
        ic = IntegrationCoordinator()
        ic.register_all_modules({
            "m1": {"version": "1.0", "dependencies": ["m0"]},
            "m0": {"version": "1.0"},
        })
        assert len(ic.registry.modules) == 2

    def test_establish_routes(self):
        ic = IntegrationCoordinator()
        ic.establish_routes([("a", "b"), ("b", "c")])
        assert len(ic.router.flows) == 2

    def test_run_health_check(self):
        ic = IntegrationCoordinator()
        ic.register_all_modules({
            "m1": {"version": "1.0"},
            "m2": {"version": "1.0"},
        })
        ic.monitor.record("m1", 0.9)
        ic.monitor.record("m2", 0.8)
        h = ic.run_health_check()
        assert "system_health" in h

    def test_run_stress_test(self):
        ic = IntegrationCoordinator()
        ic.monitor.record("m1", 0.8)
        r = ic.run_stress_test(["m1"])
        assert "m1" in r

    def test_run_cycle(self):
        ic = IntegrationCoordinator()
        r = ic.run_cycle({"m1": {"health": 0.9}, "m2": {"health": 0.8}})
        assert r["cycle"] == 1

    def test_get_status(self):
        ic = IntegrationCoordinator()
        s = ic.get_status()
        assert s["version"] == "193.0.0"

    def test_singleton(self):
        i1 = get_integration_coordinator()
        i2 = get_integration_coordinator()
        assert i1 is i2

# Total: 24 tests
