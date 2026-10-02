"""OMNI-HUB v186 Tests — TruthAlignmentEngine"""

import pytest
from core.truth_alignment_engine import (
    TruthAlignmentEngine, CrossLineFactChecker, MultiSourceValidator,
    TruthConsensusProtocol, EpistemicDriftDetector, RealityAnchorManager,
    FactClaim, SourceRecord, ValidationResult, EpistemicDrift, RealityAnchor,
    TruthStatus, SourceReliability, DriftType,
    get_truth_alignment_engine, evidence_contradicts, contradicts_anchor
)


class TestEvidenceContradicts:
    def test_no_contradiction(self):
        assert evidence_contradicts({}, {}) is False

    def test_numeric_contradiction(self):
        assert evidence_contradicts({"x": 1.0}, {"x": 10.0}) is True

    def test_no_contradiction_close(self):
        assert evidence_contradicts({"x": 1.0}, {"x": 1.01}) is False


class TestContradictsAnchor:
    def test_no_contradiction(self):
        assert contradicts_anchor("系统运行正常", "系统存在") is False

    def test_contradiction(self):
        assert contradicts_anchor("系统不存在", "系统存在") is True


class TestCrossLineFactChecker:
    def test_submit(self):
        f = CrossLineFactChecker()
        c = f.submit_claim("x=1", "ucif2", "mod1")
        assert c.claim_id.startswith("claim_")
        assert c.hash_digest != ""

    def test_consistency_self_only(self):
        f = CrossLineFactChecker()
        c = f.submit_claim("x=1", "ucif2", "mod1")
        r = f.check_consistency(c.claim_id)
        assert r["status"] == "PROVISIONAL"

    def test_consistency_cross_confirm(self):
        f = CrossLineFactChecker()
        c1 = f.submit_claim("x=1", "ucif2", "mod1")
        c2 = f.submit_claim("x=1", "lgt", "mod2")
        r = f.check_consistency(c1.claim_id)
        assert r["status"] in ["CONFIRMED", "CONSENSUS"]
        assert r["confirmations"] >= 1

    def test_report(self):
        f = CrossLineFactChecker()
        f.submit_claim("x=1", "ucif2", "mod1")
        r = f.get_report()
        assert r["total_claims"] == 1


class TestMultiSourceValidator:
    def test_register(self):
        v = MultiSourceValidator()
        v.register_source("s1", "ucif2", SourceReliability.HIGH)
        assert "s1" in v.sources

    def test_validate(self):
        v = MultiSourceValidator()
        v.register_source("s1", "lgt", SourceReliability.HIGH)
        claim = FactClaim("c1", "x=1", "ucif2", "mod1", 0.0)
        r = v.validate(claim, {"x=1": 1})
        assert isinstance(r.is_valid, bool)
        assert 0 <= r.confidence <= 1

    def test_source_reliability(self):
        v = MultiSourceValidator()
        v.register_source("s1", "ucif2", SourceReliability.HIGH)
        assert v.get_source_reliability("s1") == 0.5  # neutral prior, no claims yet

    def test_report(self):
        v = MultiSourceValidator()
        r = v.get_report()
        assert "registered_sources" in r


class TestTruthConsensusProtocol:
    def test_propose(self):
        p = TruthConsensusProtocol()
        pid = p.propose_truth("x=1", "ucif2")
        assert pid.startswith("truth_")

    def test_vote_and_tally(self):
        p = TruthConsensusProtocol()
        pid = p.propose_truth("x=1", "ucif2")
        p.vote(pid, "lgt", True, 1.0)
        p.vote(pid, "qfa", True, 1.0)
        r = p.tally(pid)
        assert r["consensus"] is True
        assert r["total_votes"] == 2

    def test_tally_rejected(self):
        p = TruthConsensusProtocol()
        pid = p.propose_truth("x=1", "ucif2")
        p.vote(pid, "lgt", False, 1.0)
        p.vote(pid, "qfa", False, 1.0)
        r = p.tally(pid)
        assert r["consensus"] is False

    def test_report(self):
        p = TruthConsensusProtocol()
        p.propose_truth("x=1", "ucif2")
        r = p.get_report()
        assert r["total_propositions"] == 1


class TestEpistemicDriftDetector:
    def test_record_and_detect_none(self):
        d = EpistemicDriftDetector()
        claim = FactClaim("c1", "x=1", "ucif2", "mod1", 0.0)
        claim.status = TruthStatus.CONFIRMED
        d.record_claim_state(claim)
        drifts = d.detect()
        assert len(drifts) == 0

    def test_detect_contradiction(self):
        d = EpistemicDriftDetector()
        # Record same claim multiple times to build history
        for i in range(5):
            claim = FactClaim("c1", "x=1", "ucif2", "mod1", 0.0)
            claim.status = TruthStatus.CONFIRMED
            claim.confirmations = ["lgt"] * i
            claim.contradictions = ["qfa"] * (i + 1)
            d.record_claim_state(claim)
        drifts = d.detect()
        assert any(d.drift_type == DriftType.CONTRADICTION for d in drifts)

    def test_report(self):
        d = EpistemicDriftDetector()
        r = d.get_report()
        assert "monitored_claims" in r


class TestRealityAnchorManager:
    def test_defaults(self):
        m = RealityAnchorManager()
        assert len(m.anchors) == 5

    def test_verify_against(self):
        m = RealityAnchorManager()
        valid, violations = m.verify_against_anchors("系统运行正常")
        assert valid is True

    def test_verify_violation(self):
        m = RealityAnchorManager()
        valid, violations = m.verify_against_anchors("系统不存在")
        assert valid is False
        assert len(violations) > 0

    def test_add_anchor(self):
        m = RealityAnchorManager()
        a = m.add_anchor("测试锚点", ["ucif2"])
        assert a.anchor_id in m.anchors

    def test_revise(self):
        m = RealityAnchorManager()
        a = list(m.anchors.values())[0]
        r = m.revise_anchor(a.anchor_id, "修订命题", "测试")
        assert r.revision_count == 1
        assert r.truth_status == TruthStatus.PROVISIONAL

    def test_report(self):
        m = RealityAnchorManager()
        r = m.get_report()
        assert r["total_anchors"] == 5


class TestTruthAlignmentEngine:
    def test_init(self):
        t = TruthAlignmentEngine()
        assert t.VERSION == "186.0.0"

    def test_submit_claim(self):
        t = TruthAlignmentEngine()
        c = t.submit_claim("x=1", "ucif2", "mod1")
        assert c.claim_id.startswith("claim_")

    def test_anchor_violation(self):
        t = TruthAlignmentEngine()
        c = t.submit_claim("系统不存在", "ucif2", "mod1")
        assert any(e.get("type") == "anchor_violation" for e in t.event_log)

    def test_run_cycle(self):
        t = TruthAlignmentEngine()
        r = t.run_cycle({
            "ucif2": {"claims": [{"statement": "x=1", "module": "m1", "evidence": {"x": 1}}]},
            "lgt": {"claims": [{"statement": "x=1", "module": "m2", "evidence": {"x": 1}}]},
        })
        assert r["cycle"] == 1
        assert r["claims_processed"] == 2

    def test_run_cycle_with_contradiction(self):
        t = TruthAlignmentEngine()
        r = t.run_cycle({
            "ucif2": {"claims": [{"statement": "x=1", "module": "m1", "evidence": {"x": 1}}]},
            "lgt": {"claims": [{"statement": "x=1", "module": "m2", "evidence": {"x": 10}}]},
        })
        assert r["claims_processed"] == 2

    def test_truth_status(self):
        t = TruthAlignmentEngine()
        t.run_cycle({
            "ucif2": {"claims": [{"statement": "x=1", "module": "m1"}]},
            "lgt": {"claims": [{"statement": "x=1", "module": "m2"}]},
            "qfa": {"claims": [{"statement": "x=1", "module": "m3"}]},
        })
        status = t.get_truth_status("x=1")
        assert status["status"] in ["CONFIRMED", "CONSENSUS"]

    def test_get_status(self):
        t = TruthAlignmentEngine()
        t.run_cycle()
        s = t.get_status()
        assert s["version"] == "186.0.0"
        assert "fact_checker" in s

    def test_singleton(self):
        t1 = get_truth_alignment_engine()
        t2 = get_truth_alignment_engine()
        assert t1 is t2

# Total: 39 tests
