"""
OMNI-HUB Recursive Self-Reflection Tests v24
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.self_reflection import SelfReflection


class TestSelfReflection:
    def test_reads_module(self):
        mirror = SelfReflection()
        source = mirror._read_module('core/constants.py')
        assert source is not None
        assert 'LEVEL_THRESHOLDS' in source

    def test_analyzes_code_structure(self):
        mirror = SelfReflection()
        source = mirror._read_module('core/constants.py')
        analysis = mirror._analyze_code(source, 'constants.py')
        assert analysis['lines'] > 0
        assert analysis['functions'] >= 0
        assert analysis['classes'] >= 0

    def test_detects_todos(self):
        mirror = SelfReflection()
        source = "# TODO: fix this\n# FIXME: broken\nprint(1)"
        analysis = mirror._analyze_code(source, 'test.py')
        assert len(analysis['todos']) == 1
        assert len(analysis['fixmes']) == 1

    def test_scan_core_modules(self):
        mirror = SelfReflection()
        result = mirror.scan_core_modules()
        assert result['modules_analyzed'] > 0
        assert result['total_lines'] > 0
        assert result['health_score'] >= 0
        assert result['health_score'] <= 100

    def test_scan_test_coverage(self):
        mirror = SelfReflection()
        result = mirror.scan_test_coverage()
        assert result['test_files'] > 0
        assert result['total_tests'] > 0

    def test_generate_self_report(self):
        mirror = SelfReflection()
        report = mirror.generate_self_report()
        assert report['system_name'] == 'OMNI-HUB'
        assert 'codebase' in report
        assert 'testing' in report
        assert 'patterns' in report
        assert 'introspection' in report
        assert report['introspection']['can_read_self']

    def test_syntax_error_handling(self):
        mirror = SelfReflection()
        bad_source = "def foo(\n    print(1)"
        analysis = mirror._analyze_code(bad_source, 'bad.py')
        assert analysis.get('syntax_error') is True
