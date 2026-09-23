"""
OMNI-HUB ANTI-FRAUD Guard Tests v30.1
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.antifraud_guard import ANTI_FRAUD_Guard, VerificationResult, get_guard, pre_operation_check


class TestVerificationResult:
    def test_creation(self):
        vr = VerificationResult("test.py", True, True, True, True)
        assert vr.target == "test.py"
        assert vr.exists is True


class TestANTI_FRAUD_Guard:
    def test_initialization(self):
        guard = ANTI_FRAUD_Guard()
        assert guard.BASE.exists()

    def test_verify_file_exists(self):
        guard = ANTI_FRAUD_Guard()
        result = guard.verify_file('core/constants.py')
        assert result.exists is True
        assert result.readable is True
        assert result.compiles is True
        assert result.has_syntax is True

    def test_verify_file_missing(self):
        guard = ANTI_FRAUD_Guard()
        result = guard.verify_file('core/nonexistent_xyz.py')
        assert result.exists is False
        assert result.compiles is False

    def test_verify_all_active(self):
        guard = ANTI_FRAUD_Guard()
        all_pass, results = guard.verify_all_active()
        assert all_pass is True
        assert len(results) > 0
        for r in results:
            assert r.compiles is True

    def test_pre_operation_check(self):
        guard = ANTI_FRAUD_Guard()
        result = guard.pre_operation_check("test_operation")
        assert result is True

    def test_is_active_module(self):
        guard = ANTI_FRAUD_Guard()
        assert guard.is_active_module('orchestrator.py') is True
        assert guard.is_active_module('v12_north_star.py') is False
        assert guard.is_active_module('beat_continuum.py') is False

    def test_get_status(self):
        guard = ANTI_FRAUD_Guard()
        status = guard.get_status()
        assert "all_pass" in status
        assert status["all_pass"] is True
        assert status["passed"] == status["total_files"]

    def test_critical_markers(self):
        guard = ANTI_FRAUD_Guard()
        result = guard.verify_file('core/orchestrator.py')
        assert result.has_syntax is True  # Critical markers found

    def test_global_guard(self):
        g = get_guard()
        assert g is not None
        assert pre_operation_check("any_op") is True
