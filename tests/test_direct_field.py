"""
OMNI-HUB v176 DirectField (直通场) Tests

Test suite for the quantum-base direct connection field.
"""

import sys
import time

sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.direct_field import (
    DirectField,
    get_direct_field,
    CORE_LINES,
    NON_LINE_NODES,
    EXTERNAL_NODES,
    ALLIANCE_LAYERS,
    FIELD_STATE_THRESHOLDS,
)


class TestDirectFieldInitialization:
    def test_field_initialization(self):
        df = DirectField()
        assert df.field_state is not None
        assert df.field_state["coherence"] == 0.95
        assert df.field_state["pulse_count"] == 0
        assert len(df.nodes) == 0
        assert len(df.coupling_matrix) == 0

    def test_layer_index_prebuilt(self):
        df = DirectField()
        # Core lines from ALLIANCE_LAYERS should be indexed
        for layer, nodes in ALLIANCE_LAYERS.items():
            for nid in nodes:
                assert df._get_layer(nid) == layer

    def test_node_type_inference(self):
        df = DirectField()
        assert df._node_type_from_id("ucif2") == "core_line"
        assert df._node_type_from_id("omni") == "core_line"
        assert df._node_type_from_id("inbox") == "non_line"
        assert df._node_type_from_id("langchain") == "external"
        assert df._node_type_from_id("unknown_thing") == "unknown"


class TestRegisterNode:
    def test_register_single_node(self):
        df = DirectField()
        result = df.register_node(
            node_id="ucif2",
            node_type="core_line",
            layer="consciousness_layer",
            capabilities=["consciousness", "awareness", "perception"],
        )
        assert result["success"] is True
        assert result["node_id"] == "ucif2"
        assert result["layer"] == "consciousness_layer"
        assert "ucif2" in df.nodes

    def test_register_duplicate_fails(self):
        df = DirectField()
        df.register_node(
            node_id="ucif2",
            node_type="core_line",
            layer="consciousness_layer",
            capabilities=["consciousness"],
        )
        result = df.register_node(
            node_id="ucif2",
            node_type="core_line",
            layer="consciousness_layer",
            capabilities=["consciousness"],
        )
        assert result["success"] is False
        assert "already registered" in result["error"]

    def test_register_multiple_nodes(self):
        df = DirectField()
        nodes = [
            ("ucif2", "core_line", "consciousness_layer", ["consciousness", "awareness"]),
            ("lvlu", "core_line", "consciousness_layer", ["value", "language"]),
            ("lgt", "core_line", "logic_layer", ["logic", "truth", "reasoning"]),
        ]
        for nid, ntype, layer, caps in nodes:
            result = df.register_node(nid, ntype, layer, caps)
            assert result["success"] is True
        assert len(df.nodes) == 3

    def test_couplings_established_on_register(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.register_node("lvlu", "core_line", "consciousness_layer", ["value"])
        # Both should have coupling entries for each other
        assert "lvlu" in df.coupling_matrix["ucif2"]
        assert "ucif2" in df.coupling_matrix["lvlu"]

    def test_register_all_33_nodes(self):
        df = DirectField()
        caps_map = {
            "ucif2": ["consciousness", "awareness", "perception"],
            "lvlu": ["value", "language", "meaning"],
            "lgt": ["logic", "truth", "reasoning"],
            "qfa": ["quantum", "awareness", "field"],
            "vinf": ["value", "infinity", "research"],
            "qgl": ["quantum", "gravity", "logic"],
            "qlv": ["quantum", "light", "velocity"],
            "qtlv": ["quantum", "temporal", "time"],
            "usrm": ["reality", "mesh", "universe"],
            "cfts": ["field", "translation", "synthesis"],
            "aiq": ["ai", "research", "quantum"],
            "omni": ["orchestration", "meta", "synthesis"],
        }
        for nid in CORE_LINES:
            layer = None
            for lname, lnodes in ALLIANCE_LAYERS.items():
                if nid in lnodes:
                    layer = lname
                    break
            df.register_node(
                nid, "core_line", layer or "unknown",
                caps_map.get(nid, ["general"])
            )
        for nid in NON_LINE_NODES:
            df.register_node(nid, "non_line", "service_layer", ["service", "worker"])
        for nid in EXTERNAL_NODES:
            df.register_node(nid, "external", "external_layer", ["external", "api"])

        assert len(df.nodes) == 33
        # 网 (Net): full mesh should have 33*32 = 1056 directed couplings
        total_couplings = sum(len(v) for v in df.coupling_matrix.values())
        assert total_couplings == 33 * 32  # 33 nodes, each coupled to 32 others


class TestComputeFieldCoupling:
    def test_coupling_same_layer(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.register_node("lvlu", "core_line", "consciousness_layer", ["value"])
        result = df.compute_field_coupling("ucif2", "lvlu")
        assert result["strength"] > 0.0
        assert result["factors"]["same_layer"] == 0.3

    def test_coupling_complementary_caps(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness", "awareness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic", "truth", "reasoning"])
        result = df.compute_field_coupling("ucif2", "lgt")
        assert result["factors"]["complementary_caps"] == 0.3

    def test_coupling_line_resonance(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["x"])
        df.register_node("lgt", "core_line", "logic_layer", ["y"])
        result = df.compute_field_coupling("ucif2", "lgt")
        assert result["factors"]["line_resonance"] == 0.2

    def test_coupling_unregistered_nodes(self):
        df = DirectField()
        result = df.compute_field_coupling("a", "b")
        assert result["strength"] == 0.0
        assert "error" in result

    def test_coupling_minimum_nonzero(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["a"])
        df.register_node("lgt", "core_line", "logic_layer", ["b"])
        # Different layer, no complementary caps, but same type -> line_resonance
        result = df.compute_field_coupling("ucif2", "lgt")
        assert result["strength"] >= 0.05

    def test_coupling_clamped_to_one(self):
        df = DirectField()
        # Max possible: same_layer(0.3) + complementary(0.3) + line_resonance(0.2) + recency(0.2) = 1.0
        df.register_node(
            "ucif2", "core_line", "consciousness_layer",
            ["consciousness", "awareness", "perception"]
        )
        df.register_node(
            "lgt", "core_line", "consciousness_layer",
            ["logic", "truth", "reasoning"]
        )
        result = df.compute_field_coupling("ucif2", "lgt")
        assert result["strength"] <= 1.0


class TestTransmitFieldSignal:
    def test_transmit_success(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic"])
        signal = {"type": "awareness_pulse", "data": "hello field"}
        result = df.transmit_field_signal("ucif2", "lgt", signal)
        assert result["success"] is True
        assert result["source"] == "ucif2"
        assert result["target"] == "lgt"
        assert result["field_speed"] is True
        assert result["signal"] == signal

    def test_transmit_missing_source(self):
        df = DirectField()
        df.register_node("lgt", "core_line", "logic_layer", ["logic"])
        result = df.transmit_field_signal("missing", "lgt", {})
        assert result["success"] is False
        assert "missing" in result["error"]

    def test_transmit_missing_target(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        result = df.transmit_field_signal("ucif2", "missing", {})
        assert result["success"] is False
        assert "missing" in result["error"]

    def test_transmit_updates_activity(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic"])
        before = df.nodes["ucif2"]["signal_count"]
        df.transmit_field_signal("ucif2", "lgt", {"type": "test"})
        assert df.nodes["ucif2"]["signal_count"] == before + 1

    def test_transmit_increases_coherence(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic"])
        before = df.field_state["coherence"]
        df.transmit_field_signal("ucif2", "lgt", {"type": "test"})
        assert df.field_state["coherence"] > before


class TestSenseFieldState:
    def test_sense_unregistered_observer(self):
        df = DirectField()
        result = df.sense_field_state("nobody")
        assert result["success"] is False
        assert "not registered" in result["error"]

    def test_sense_empty_field(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        result = df.sense_field_state("ucif2")
        assert result["success"] is True
        assert result["node_count"] == 1
        assert result["observer"] == "ucif2"
        assert "field_strength" in result
        assert "field_state" in result

    def test_sense_multi_node_field(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic"])
        df.register_node("inbox", "non_line", "service_layer", ["service"])
        result = df.sense_field_state("ucif2")
        assert result["node_count"] == 3
        assert result["coupling_count"] == 6  # 3*2 directed
        assert "observer_couplings" in result
        assert "lgt" in result["observer_couplings"]
        assert "inbox" in result["observer_couplings"]

    def test_field_state_categories(self):
        df = DirectField()
        # Just one node: very low field strength -> decoherent
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        result = df.sense_field_state("ucif2")
        assert result["field_state"] in FIELD_STATE_THRESHOLDS.keys()


class TestDetectFieldDisturbance:
    def test_empty_field_stable(self):
        df = DirectField()
        result = df.detect_field_disturbance()
        assert result["field_stable"] is True
        assert result["disturbance_count"] == 0

    def test_inactive_node_detected(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        # Manually set last_active to the past
        df.nodes["ucif2"]["last_active"] = time.time() - 400
        result = df.detect_field_disturbance()
        assert result["disturbance_count"] >= 1
        types = [d["type"] for d in result["disturbances"]]
        assert "inactive_node" in types

    def test_low_coherence_detected(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.field_state["coherence"] = 0.2
        result = df.detect_field_disturbance()
        types = [d["type"] for d in result["disturbances"]]
        assert "low_coherence" in types

    def test_recommendations_generated(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.nodes["ucif2"]["last_active"] = time.time() - 400
        result = df.detect_field_disturbance()
        assert len(result["recommendations"]) > 0


class TestComputeFieldTensor:
    def test_tensor_empty(self):
        df = DirectField()
        result = df.compute_field_tensor()
        assert result["success"] is True
        assert result["dimensions"]["nodes"] == 0
        assert result["dimensions"]["capabilities"] == 0
        assert result["tensor_shape"] == [1, 0, 0]

    def test_tensor_with_nodes(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness", "awareness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic", "truth"])
        result = df.compute_field_tensor()
        assert result["dimensions"]["nodes"] == 2
        assert result["dimensions"]["capabilities"] == 4
        assert result["tensor_shape"] == [1, 2, 4]
        # Check tensor data structure: time x nodes x caps
        assert len(result["tensor_data"]) == 1
        assert len(result["tensor_data"][0]) == 2
        assert len(result["tensor_data"][0][0]) == 4

    def test_tensor_history_accumulates(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.compute_field_tensor()  # history=[], n_time=1, then history=[snapshot]
        df.compute_field_tensor()  # history=[s1], n_time=2, then history=[s1,s2]
        result = df.compute_field_tensor()  # history=[s1,s2], n_time=3, then history=[s1,s2,s3]
        assert result["dimensions"]["time"] == 3


class TestInstantSync:
    def test_sync_two_nodes(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness", "awareness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic", "truth"])
        result = df.instant_sync(["ucif2", "lgt"])
        assert result["success"] is True
        assert result["node_count"] == 2
        assert "consciousness" in result["shared_capabilities"]
        assert "logic" in result["shared_capabilities"]

    def test_sync_missing_node(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        result = df.instant_sync(["ucif2", "missing"])
        assert result["success"] is False
        assert "missing" in result["error"]

    def test_sync_boosts_coupling(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic"])
        before = df.coupling_matrix["ucif2"]["lgt"]
        result = df.instant_sync(["ucif2", "lgt"])
        assert result["coupling_delta"] > 0
        assert df.coupling_matrix["ucif2"]["lgt"] > before

    def test_sync_increases_coherence(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic"])
        before = df.field_state["coherence"]
        df.instant_sync(["ucif2", "lgt"])
        assert df.field_state["coherence"] > before

    def test_sync_multiple_nodes(self):
        df = DirectField()
        for nid in ["ucif2", "lvlu", "lgt", "qfa"]:
            layer = "consciousness_layer" if nid in ["ucif2", "lvlu", "qfa"] else "logic_layer"
            df.register_node(nid, "core_line", layer, ["general"])
        result = df.instant_sync(["ucif2", "lvlu", "lgt", "qfa"])
        assert result["node_count"] == 4
        assert result["success"] is True


class TestGetStatus:
    def test_status_empty(self):
        df = DirectField()
        status = df.get_status()
        assert status["node_count"] == 0
        assert status["coupling_count"] == 0
        assert status["field_strength"] == 0.0
        assert status["disturbances"] == 0

    def test_status_with_nodes(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic"])
        status = df.get_status()
        assert status["node_count"] == 2
        assert status["coupling_count"] == 2
        assert "field_strength" in status
        assert "field_state" in status
        assert "coherence" in status
        assert "avg_coupling" in status

    def test_status_field_state_thresholds(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic"])
        df.register_node("qlv", "core_line", "quantum_layer", ["quantum"])
        status = df.get_status()
        assert status["field_state"] in FIELD_STATE_THRESHOLDS.keys()

    def test_status_after_transmission(self):
        df = DirectField()
        df.register_node("ucif2", "core_line", "consciousness_layer", ["consciousness"])
        df.register_node("lgt", "core_line", "logic_layer", ["logic"])
        df.transmit_field_signal("ucif2", "lgt", {"type": "test"})
        status = df.get_status()
        assert status["active_transmissions"] == 1
        assert status["pulse_count"] > 0


class TestSingleton:
    def test_singleton_returns_same_instance(self):
        df1 = get_direct_field()
        df2 = get_direct_field()
        assert df1 is df2

    def test_singleton_is_direct_field(self):
        df = get_direct_field()
        assert isinstance(df, DirectField)


class TestAllianceStructure:
    def test_alliance_counts(self):
        assert len(CORE_LINES) == 12
        assert len(NON_LINE_NODES) == 16
        assert len(EXTERNAL_NODES) == 5
        total = len(CORE_LINES) + len(NON_LINE_NODES) + len(EXTERNAL_NODES)
        assert total == 33  # 12 + 16 + 5

    def test_layers_cover_core_lines(self):
        covered = set()
        for nodes in ALLIANCE_LAYERS.values():
            covered.update(nodes)
        # ALLIANCE_LAYERS covers all core lines
        assert covered == set(CORE_LINES)


class TestFieldStateThresholds:
    def test_threshold_order(self):
        values = list(FIELD_STATE_THRESHOLDS.values())
        assert values == sorted(values, reverse=True)

    def test_all_states_present(self):
        assert "supercritical" in FIELD_STATE_THRESHOLDS
        assert "coherent" in FIELD_STATE_THRESHOLDS
        assert "stable" in FIELD_STATE_THRESHOLDS
        assert "fluctuating" in FIELD_STATE_THRESHOLDS
        assert "decoherent" in FIELD_STATE_THRESHOLDS
