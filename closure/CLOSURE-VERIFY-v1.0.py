#!/usr/bin/env python3

"""
UCIF2-Kernel 闭环验证脚本 v1.0
LOCAL FULL DIMENSION AUTONOMY 模式

功能：
1. 读取所有实验文件
2. 检查每个实验的validation字段
3. 验证cross_line一致性
4. 检查deepening action是否可执行
5. 输出闭环验证报告
6. 标记需要修正的项目

用法：
    python3 CLOSURE-VERIFY-v1.0.py [--output-dir PATH] [--verbose]

依赖：
    Python 3.7+ (仅使用标准库)
"""

__version__ = "11.0.0"
import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

# === 配置 ===
DEFAULT_EXPERIMENT_DIR = "/mnt/agents/output/SI-MAX-01/experiments"
DEFAULT_VALIDATION_FILE = os.getenv("OMNIHUB_PATH", "/mnt/agents/output/SI-MAX-01/validation/VAL-01-SI-MAX-comprehensive.json")
DEFAULT_OUTPUT_DIR = "/mnt/agents/output/OMNI-HUB/closure"

EXPERIMENT_FILES = [
    "EXP-011-lgt-k200-3200orbits.json",
    "EXP-012-qfa-quantum-self-bootstrap.json",
    "EXP-013-usrm-cubic-to-variable-gamma.json",
    "EXP-014-vinf-gyroid-percolation-MC.json",
    "EXP-015-qgl-M-series-full-stats.json",
    "EXP-016-qlv-binmap-v3-O_S.json",
    "EXP-017-lvlu-EVALR2-automation.json",
    "EXP-018-cfts-F4-QLV-dequarantine.json",
]

LINES = ["ucif2", "lgt", "qfa", "usrm", "vinf", "qgl", "qlv", "lvlu", "cfts"]


class Colors:
    """终端颜色输出"""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"

    @classmethod
    def disable(cls):
        cls.GREEN = cls.YELLOW = cls.RED = cls.BLUE = cls.CYAN = cls.BOLD = cls.END = ""


def color(text: str, color_code: str) -> str:
    return f"{color_code}{text}{Colors.END}"


class ClosureVerifier:
    """闭环验证器主类"""

    def __init__(self, experiment_dir: str, validation_file: str, output_dir: str, verbose: bool = False):
        self.experiment_dir = Path(experiment_dir)
        self.validation_file = Path(validation_file)
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.experiments: Dict[str, Dict] = {}
        self.validation: Dict = {}
        self.issues: List[Dict] = []
        self.cross_line_pairs: List[Dict] = []
        self.si_audit: Dict[str, Dict] = {}

    def log(self, msg: str, level: str = "INFO"):
        """日志输出"""
        if not self.verbose and level == "DEBUG":
            return
        prefix = {"INFO": "[INFO]", "WARN": color("[WARN]", Colors.YELLOW),
                  "ERROR": color("[ERROR]", Colors.RED), "DEBUG": "[DEBUG]",
                  "PASS": color("[PASS]", Colors.GREEN), "FAIL": color("[FAIL]", Colors.RED)}.get(level, "[INFO]")
        logger.info(f"{prefix} {msg}")

    def load_all(self) -> bool:
        """加载所有实验文件和验证文件"""
        self.log("开始加载实验文件...", "INFO")
        all_loaded = True

        for filename in EXPERIMENT_FILES:
            filepath = self.experiment_dir / filename
            with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            exp_id = data.get("exp_id", filename.split('-')[0] + '-' + filename.split('-')[1])
            self.experiments[exp_id] = data
            self.log(f"已加载 {exp_id}: {filepath}", "DEBUG")
            self.log(f"加载失败 {filepath}: {e}", "ERROR")
            all_loaded = False

            with open(self.validation_file, 'r', encoding='utf-8') as f:
                self.validation = json.load(f)
            self.log(f"已加载验证文件: {self.validation_file}", "DEBUG")
            self.log(f"加载验证文件失败: {e}", "ERROR")
            all_loaded = False

        self.log(f"共加载 {len(self.experiments)} 个实验文件", "INFO")
        return all_loaded

    # ============================================================
    # STEP 1: CHECK — 假设合理性与数据完整性检查
    # ============================================================
    def step_check(self) -> Dict[str, Any]:
        """检查阶段：验证假设合理性和数据完整性"""
        self.log("=" * 60, "INFO")
        self.log("STEP 1: CHECK — 假设与数据完整性检查", "INFO")
        results = {}

        for exp_id, exp in sorted(self.experiments.items()):
            line = exp.get("line", "UNKNOWN")
            si_before = exp.get("si_before", "UNKNOWN")
            si_target = exp.get("si_target", "UNKNOWN")
            hypothesis = exp.get("hypothesis", "")
            results_data = exp.get("results", {})

            check_result = {
                "exp_id": exp_id,
                "line": line,
                "si_upgrade": f"{si_before} -> {si_target}",
                "checks": {},
                "status": "PASS",
                "issues": []
            }

            # 1.1 假设存在性
            if not hypothesis or len(hypothesis) < 10:
                check_result["checks"]["hypothesis_exists"] = "FAIL"
                check_result["issues"].append("假设描述缺失或过短")
                check_result["status"] = "FAIL"
            else:
                check_result["checks"]["hypothesis_exists"] = "PASS"

            # 1.2 results字段完整性
            if not results_data:
                check_result["checks"]["results_complete"] = "FAIL"
                check_result["issues"].append("results字段缺失")
                check_result["status"] = "FAIL"
            else:
                check_result["checks"]["results_complete"] = "PASS"

            # 1.3 数值合理性检查（基于各实验特定规则）
            numeric_issues = self._check_numeric_reasonableness(exp_id, results_data)
            if numeric_issues:
                check_result["issues"].extend(numeric_issues)
                check_result["checks"]["numeric_reasonableness"] = "WARNING"
                if check_result["status"] == "PASS":
                    check_result["status"] = "WARNING"
            else:
                check_result["checks"]["numeric_reasonableness"] = "PASS"

            # 1.4 方法学描述
            methodology = exp.get("methodology", "")
            if not methodology:
                check_result["checks"]["methodology"] = "FAIL"
                check_result["issues"].append("methodology字段缺失")
                check_result["status"] = "FAIL"
            else:
                check_result["checks"]["methodology"] = "PASS"

            results[exp_id] = check_result

            status_color = Colors.GREEN if check_result["status"] == "PASS" else \
                          Colors.YELLOW if check_result["status"] == "WARNING" else Colors.RED
            self.log(f"{exp_id} ({line}): CHECK = {color(check_result['status'], status_color)}", "INFO")
            for issue in check_result["issues"]:
                self.log(f"  -> {issue}", "WARN")

        return results

    def _check_numeric_reasonableness(self, exp_id: str, results: Dict) -> List[str]:
        """检查数值合理性"""
        issues = []

        if exp_id == "EXP-011":
            # lgt: 收敛率检查
            conv = results.get("convergence", {})
            if "n=3200" not in conv:
                issues.append("缺少n=3200收敛数据")
            if results.get("convergence_rate") != "O(1/sqrt(n))":
                issues.append("收敛率标记异常")
            if abs(results.get("vs_n1600_delta_pct", 0)) > 0.05:
                issues.append("vs_n1600变化超过0.05% gate")

        elif exp_id == "EXP-012":
            # qfa: 形式化验证检查
            if results.get("coq_check", "").startswith("FAILED"):
                issues.append("Coq验证失败")
            if results.get("lean_check", "").startswith("FAILED"):
                issues.append("Lean验证失败")
            if results.get("theorem_coverage_pct", 0) < 100:
                issues.append(f"定理覆盖率不足: {results.get('theorem_coverage_pct')}%")

        elif exp_id == "EXP-013":
            # usrm: AIC检查
            best = results.get("best_model", "")
            if not best:
                issues.append("未指定最优模型")
            if results.get("bootstrap_n", 0) < 1000:
                issues.append(f"bootstrap次数过少: {results.get('bootstrap_n')}")

        elif exp_id == "EXP-014":
            # vinf: FSS检查
            p_c = results.get("p_c_estimates", {})
            if "extrapolated_FSS" not in p_c:
                issues.append("缺少FSS外推值")
            if results.get("n_samples", 0) < 10000:
                issues.append(f"样本量不足: {results.get('n_samples')}")

        elif exp_id == "EXP-015":
            # qgl: 统计检验
            ks = results.get("ks_test", {})
            if ks.get("p_value", 0) < 0.05:
                issues.append(f"KS检验未通过: p={ks.get('p_value')}")
            if results.get("n_events", 0) < 50:
                issues.append(f"事件数过少: {results.get('n_events')}")

        elif exp_id == "EXP-016":
            # qlv: kappa检查
            if results.get("human_agreement_kappa", 0) < 0.8:
                issues.append(f"人工一致性kappa过低: {results.get('human_agreement_kappa')}")
            if results.get("loo_accuracy", 0) < 0.85:
                issues.append(f"LOO准确率过低: {results.get('loo_accuracy')}")

        elif exp_id == "EXP-017":
            # lvlu: kappa检查
            kappa = results.get("validation_vs_manual", {}).get("cohens_kappa", 0)
            if kappa < 0.8:
                issues.append(f"Cohen kappa过低: {kappa}")
            components = results.get("automation_components", {})
            for comp, info in components.items():
                if info.get("status") != "ACTIVE":
                    issues.append(f"自动化组件 {comp} 状态非ACTIVE")

        elif exp_id == "EXP-018":
            # cfts: F4完成度
            f4 = results.get("f4_status", {})
            total_pct = results.get("f4_total_percent", 0)
            if total_pct < 100:
                issues.append(f"F4完成度不足: {total_pct}%")
            for task, info in f4.items():
                if not info.get("completed", False):
                    issues.append(f"F4子任务未完成: {task}")
            qlv_dq = results.get("qlv_dequarantine", {})
            for check, info in qlv_dq.items():
                if not info.get("passed", False):
                    issues.append(f"QLV解隔离检查未通过: {check}")

        return issues

    # ============================================================
    # STEP 2: COMMUNICATE — 跨线沟通检查
    # ============================================================
    def step_communicate(self) -> Dict[str, Any]:
        """沟通阶段：验证cross_line一致性"""
        self.log("=" * 60, "INFO")
        self.log("STEP 2: COMMUNICATE — 跨线沟通检查", "INFO")
        results = {}

        # 构建跨线验证矩阵
        cross_matrix = {line: {} for line in LINES}

        for exp_id, exp in sorted(self.experiments.items()):
            line = exp.get("line", "UNKNOWN")
            validation = exp.get("validation", {})
            cross_line = validation.get("cross_line", "")
            status = validation.get("status", "UNKNOWN")
            delta_pct = validation.get("delta_pct", None)

            comm_result = {
                "exp_id": exp_id,
                "line": line,
                "cross_line": cross_line,
                "status": status,
                "delta_pct": delta_pct,
                "issues": [],
                "bidirectional": False
            }

            # 检查cross_line是否有效
            if not cross_line:
                comm_result["issues"].append("未指定cross_line")
                comm_result["status"] = "FAIL"
            elif cross_line not in LINES:
                comm_result["issues"].append(f"无效的cross_line: {cross_line}")
                comm_result["status"] = "FAIL"
            else:
                cross_matrix[line][cross_line] = {
                    "exp_id": exp_id,
                    "status": status,
                    "delta_pct": delta_pct
                }

            # 检查delta是否在阈值内
            if delta_pct is not None and abs(delta_pct) > 1.0:
                comm_result["issues"].append(f"跨线差异过大: {delta_pct}%")
                if comm_result["status"] != "FAIL":
                    comm_result["status"] = "WARNING"

            results[exp_id] = comm_result

            status_color = Colors.GREEN if comm_result["status"] == "PASSED" else \
                          Colors.YELLOW if comm_result["status"] == "WARNING" else Colors.RED
            self.log(f"{exp_id} ({line} -> {cross_line}): COMM = {color(comm_result['status'], status_color)}", "INFO")
            for issue in comm_result["issues"]:
                self.log(f"  -> {issue}", "WARN")

        # 双向验证检查
        self.log("--- 双向一致性检查 ---", "INFO")
        bidirectional_pairs = [
            ("EXP-011", "EXP-013"),  # lgt <-> usrm (k200)
            ("EXP-014", "EXP-015"),  # vinf <-> qgl (gamma exponent)
        ]

        for exp_a, exp_b in bidirectional_pairs:
            if exp_a in self.experiments and exp_b in self.experiments:
                val_a = self.experiments[exp_a].get("validation", {})
                val_b = self.experiments[exp_b].get("validation", {})
                line_a = self.experiments[exp_a].get("line", "")
                line_b = self.experiments[exp_b].get("line", "")

                # 检查是否互为cross_line
                is_bidirectional = val_a.get("cross_line") == line_b and val_b.get("cross_line") == line_a
                if is_bidirectional:
                    self.log(f"双向验证通过: {exp_a} <-> {exp_b}", "PASS")
                    results[exp_a]["bidirectional"] = True
                    results[exp_b]["bidirectional"] = True
                else:
                    self.log(f"双向验证不完整: {exp_a} <-> {exp_b}", "WARN")

        self.cross_line_pairs = self._build_cross_line_matrix()
        return results

    def _build_cross_line_matrix(self) -> List[Dict]:
        """构建完整的跨线验证对列表"""
        pairs = []
        for exp_id, exp in self.experiments.items():
            line = exp.get("line", "")
            val = exp.get("validation", {})
            cross = val.get("cross_line", "")
            if cross:
                pairs.append({
                    "from": line,
                    "to": cross,
                    "exp_id": exp_id,
                    "status": val.get("status", "UNKNOWN"),
                    "note": val.get("note", "")
                })
        return pairs

    # ============================================================
    # STEP 3: IMPLEMENT — 落实检查
    # ============================================================
    def step_implement(self) -> Dict[str, Any]:
        """落实阶段：检查deepening action可执行性"""
        self.log("=" * 60, "INFO")
        self.log("STEP 3: IMPLEMENT — 落实检查", "INFO")
        results = {}

        total_actions = 0
        pending_actions = 0
        blocked_actions = 0

        for exp_id, exp in sorted(self.experiments.items()):
            line = exp.get("line", "")
            deepening = exp.get("deepening", [])

            impl_result = {
                "exp_id": exp_id,
                "line": line,
                "total_actions": len(deepening),
                "actions": [],
                "status": "PENDING",
                "issues": []
            }

            for idx, action in enumerate(deepening, 1):
                total_actions += 1
                pending_actions += 1

                action_result = {
                    "action_id": f"IMPL-{exp_id.split('-')[1]}-{idx:02d}",
                    "description": action,
                    "status": "PENDING",
                    "blockers": [],
                    "executable": True
                }

                # 检查action是否包含跨线依赖
                if "全线" in action or "API" in action:
                    action_result["blockers"].append("需ucif2协调跨线资源")
                    action_result["executable"] = False
                    blocked_actions += 1

                if "BRIDGE" in action:
                    action_result["blockers"].append("需BRIDGE接口定义")
                    action_result["executable"] = False
                    blocked_actions += 1

                impl_result["actions"].append(action_result)

            if not deepening:
                impl_result["issues"].append("无deepening action")
                impl_result["status"] = "WARNING"
            else:
                all_blocked = all(not a["executable"] for a in impl_result["actions"])
                if all_blocked:
                    impl_result["status"] = "BLOCKED"
                else:
                    impl_result["status"] = "PENDING"

            results[exp_id] = impl_result

            status_color = Colors.GREEN if impl_result["status"] == "COMPLETED" else \
                          Colors.YELLOW if impl_result["status"] == "PENDING" else \
                          Colors.RED if impl_result["status"] == "BLOCKED" else Colors.YELLOW
            self.log(f"{exp_id}: {len(deepening)} actions, status = {color(impl_result['status'], status_color)}", "INFO")

        self.log(f"总计: {total_actions}项 deepening action, {pending_actions}项 PENDING, {blocked_actions}项 BLOCKED", "INFO")
        return results

    # ============================================================
    # STEP 4: VERIFY — 验证检查
    # ============================================================
    def step_verify(self) -> Dict[str, Any]:
        """验证阶段：综合验证"""
        self.log("=" * 60, "INFO")
        self.log("STEP 4: VERIFY — 验证检查", "INFO")
        results = {}

        val_results = self.validation.get("results", {})

        for exp_id, exp in sorted(self.experiments.items()):
            line = exp.get("line", "")
            self_val = exp.get("validation", {})
            comprehensive_val = val_results.get(exp_id, {})

            verify_result = {
                "exp_id": exp_id,
                "line": line,
                "self_validation": self_val.get("status", "UNKNOWN"),
                "comprehensive_validation": comprehensive_val.get("overall", "UNKNOWN"),
                "checks": {},
                "status": "PASS",
                "issues": []
            }

            # 4.1 自验证状态
            if self_val.get("status") != "PASSED":
                verify_result["checks"]["self_validation"] = "FAIL"
                verify_result["issues"].append(f"自验证未通过: {self_val.get('status')}")
                verify_result["status"] = "FAIL"
            else:
                verify_result["checks"]["self_validation"] = "PASS"

            # 4.2 综合验证状态
            if comprehensive_val.get("overall") != "PASSED":
                verify_result["checks"]["comprehensive_validation"] = "FAIL"
                verify_result["issues"].append(f"综合验证未通过: {comprehensive_val.get('overall')}")
                verify_result["status"] = "FAIL"
            else:
                verify_result["checks"]["comprehensive_validation"] = "PASS"

            # 4.3 边界测试
            boundary = comprehensive_val.get("boundary_tests", "")
            if "PASSED" not in boundary and "pass" not in boundary.lower():
                verify_result["checks"]["boundary_tests"] = "FAIL"
                verify_result["issues"].append("边界测试未通过")
                verify_result["status"] = "FAIL"
            else:
                verify_result["checks"]["boundary_tests"] = "PASS"

            # 4.4 cross_line验证
            cross_checks = [k for k in comprehensive_val.keys() if k.startswith("cross_")]
            if not cross_checks:
                verify_result["checks"]["cross_line_tests"] = "WARNING"
                verify_result["issues"].append("无cross_line验证记录")
            else:
                failed_cross = [c for c in cross_checks if "PASSED" not in comprehensive_val.get(c, "")]
                if failed_cross:
                    verify_result["checks"]["cross_line_tests"] = "FAIL"
                    verify_result["issues"].append(f"跨线验证失败: {failed_cross}")
                    verify_result["status"] = "FAIL"
                else:
                    verify_result["checks"]["cross_line_tests"] = "PASS"

            results[exp_id] = verify_result

            status_color = Colors.GREEN if verify_result["status"] == "PASS" else Colors.RED
            self.log(f"{exp_id}: VERIFY = {color(verify_result['status'], status_color)}", "INFO")
            for issue in verify_result["issues"]:
                self.log(f"  -> {issue}", "WARN")

        return results

    # ============================================================
    # STEP 5: FIX — 修正措施
    # ============================================================
    def step_fix(self, check_results, comm_results, impl_results, verify_results) -> Dict[str, Any]:
        """修正阶段：标记需要修正的项目"""
        self.log("=" * 60, "INFO")
        self.log("STEP 5: FIX — 修正措施", "INFO")
        results = {}

        for exp_id in sorted(self.experiments.keys()):
            fix_result = {
                "exp_id": exp_id,
                "issues": [],
                "fixes": [],
                "severity_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
            }

            # 汇总各阶段问题
            for issue in check_results.get(exp_id, {}).get("issues", []):
                fix_result["issues"].append({"phase": "CHECK", "severity": "MEDIUM", "description": issue})
                fix_result["severity_counts"]["MEDIUM"] += 1

            for issue in comm_results.get(exp_id, {}).get("issues", []):
                fix_result["issues"].append({"phase": "COMMUNICATE", "severity": "HIGH", "description": issue})
                fix_result["severity_counts"]["HIGH"] += 1

            for issue in impl_results.get(exp_id, {}).get("issues", []):
                fix_result["issues"].append({"phase": "IMPLEMENT", "severity": "MEDIUM", "description": issue})
                fix_result["severity_counts"]["MEDIUM"] += 1

            for issue in verify_results.get(exp_id, {}).get("issues", []):
                fix_result["issues"].append({"phase": "VERIFY", "severity": "HIGH", "description": issue})
                fix_result["severity_counts"]["HIGH"] += 1

            # 生成修正措施
            line = self.experiments[exp_id].get("line", "")

            # 针对各实验的特定修正
            if exp_id == "EXP-011":
                fix_result["fixes"].append({
                    "severity": "LOW",
                    "action": "增加qfa作为第二验证线，对FSS模型进行形式化验证",
                    "responsible": "qfa"
                })
                fix_result["severity_counts"]["LOW"] += 1

            elif exp_id == "EXP-012":
                fix_result["fixes"].append({
                    "severity": "LOW",
                    "action": "在文档中明确Godel边界限制（有限域内完备）",
                    "responsible": "qfa"
                })
                fix_result["severity_counts"]["LOW"] += 1

            elif exp_id == "EXP-013":
                fix_result["fixes"].append({
                    "severity": "INFO",
                    "action": "扩展gamma参数空间至0.95~1.20",
                    "responsible": "usrm"
                })
                fix_result["severity_counts"]["INFO"] += 1

            elif exp_id == "EXP-014":
                fix_result["fixes"].append({
                    "severity": "INFO",
                    "action": "增加L=512数据点增强FSS稳健性",
                    "responsible": "vinf"
                })
                fix_result["severity_counts"]["INFO"] += 1

            elif exp_id == "EXP-015":
                fix_result["fixes"].append({
                    "severity": "LOW",
                    "action": "扩展M-SERIES事件数至200+",
                    "responsible": "qgl"
                })
                fix_result["severity_counts"]["LOW"] += 1

            elif exp_id == "EXP-016":
                fix_result["fixes"].append({
                    "severity": "MEDIUM",
                    "action": "分析cfts O_S=0.2704异常偏高的根因",
                    "responsible": "qlv/cfts"
                })
                fix_result["severity_counts"]["MEDIUM"] += 1

            elif exp_id == "EXP-017":
                fix_result["fixes"].append({
                    "severity": "MEDIUM",
                    "action": "启动lvlu自评估流程，解决self_eval_needed告警",
                    "responsible": "lvlu"
                })
                fix_result["severity_counts"]["MEDIUM"] += 1

            elif exp_id == "EXP-018":
                fix_result["fixes"].append({
                    "severity": "MEDIUM",
                    "action": "分析voice latency_p99=45.6ms长尾延迟根因",
                    "responsible": "cfts"
                })
                fix_result["severity_counts"]["MEDIUM"] += 1

            # 通用修正：deepening未执行
            if impl_results.get(exp_id, {}).get("status") == "PENDING":
                fix_result["fixes"].append({
                    "severity": "HIGH",
                    "action": f"执行{len(self.experiments[exp_id].get('deepening', []))}项deepening action",
                    "responsible": line
                })
                fix_result["severity_counts"]["HIGH"] += 1

            results[exp_id] = fix_result

            total_issues = sum(fix_result["severity_counts"].values())
            self.log(f"{exp_id}: {total_issues}项问题/修正", "INFO")
            for fix in fix_result["fixes"]:
                sev_color = Colors.RED if fix["severity"] == "HIGH" else \
                           Colors.YELLOW if fix["severity"] == "MEDIUM" else Colors.BLUE
                self.log(f"  [{color(fix['severity'], sev_color)}] {fix['action']} (@{fix['responsible']})", "INFO")

        return results

    # ============================================================
    # SI升级审计
    # ============================================================
    def audit_si_upgrades(self) -> Dict[str, Any]:
        """审计SI升级的合理性"""
        self.log("=" * 60, "INFO")
        self.log("SI升级真实审计", "INFO")
        audit = {}

        for exp_id, exp in sorted(self.experiments.items()):
            line = exp.get("line", "")
            si_before = exp.get("si_before", "")
            si_target = exp.get("si_target", "")
            results = exp.get("results", {})
            validation = exp.get("validation", {})

            # 解析SI数值
            def parse_si(si_str):
                    return float(si_str.replace("SI", ""))
                    return 0.0

            si_before_val = parse_si(si_before)
            si_target_val = parse_si(si_target)
            si_delta = si_target_val - si_before_val

            # 数据充分性评分
            data_score = self._score_data_sufficiency(exp_id, results)
            # 验证充分性评分
            verify_score = self._score_verification_sufficiency(exp_id, validation)
            # 形式化程度评分
            formal_score = self._score_formalization(exp_id, results)
            # 边界测试评分
            boundary_score = self._score_boundary_tests(exp_id)

            # 综合评分
            overall_score = (data_score + verify_score + formal_score + boundary_score) / 4

            # 判定
            if overall_score >= 0.85:
                verdict = "充分论证"
            elif overall_score >= 0.7:
                verdict = "条件充分"
            else:
                verdict = "需补充论证"

            audit[exp_id] = {
                "line": line,
                "si_upgrade": f"{si_before} -> {si_target} (delta={si_delta:+.1f})",
                "scores": {
                    "data_sufficiency": data_score,
                    "verification_sufficiency": verify_score,
                    "formalization": formal_score,
                    "boundary_tests": boundary_score
                },
                "overall_score": overall_score,
                "verdict": verdict,
                "recommendations": self._si_recommendations(exp_id, overall_score)
            }

            score_color = Colors.GREEN if overall_score >= 0.85 else \
                         Colors.YELLOW if overall_score >= 0.7 else Colors.RED
            self.log(f"{exp_id} ({line}): 综合评分={color(f'{overall_score:.2f}', score_color)}, 判定={color(verdict, score_color)}", "INFO")

        self.si_audit = audit
        return audit

    def _score_data_sufficiency(self, exp_id: str, results: Dict) -> float:
        """数据充分性评分 (0-1)"""
        if exp_id == "EXP-011":
            return 0.95 if results.get("n_orbits", 0) >= 3200 else 0.7
        elif exp_id == "EXP-012":
            return 1.0 if results.get("coq_check", "").startswith("PASSED") else 0.5
        elif exp_id == "EXP-013":
            return 0.9 if results.get("bootstrap_n", 0) >= 10000 else 0.6
        elif exp_id == "EXP-014":
            return 0.85 if results.get("n_samples", 0) >= 100000 else 0.6
        elif exp_id == "EXP-015":
            return 0.75 if results.get("n_events", 0) >= 125 else 0.5
        elif exp_id == "EXP-016":
            return 0.9 if results.get("n_basis", 0) >= 2048 else 0.6
        elif exp_id == "EXP-017":
            return 0.95 if results.get("validation_vs_manual", {}).get("cohens_kappa", 0) >= 0.8 else 0.6
        elif exp_id == "EXP-018":
            return 0.95 if results.get("f4_total_percent", 0) == 100 else 0.5
        return 0.5

    def _score_verification_sufficiency(self, exp_id: str, validation: Dict) -> float:
        """验证充分性评分"""
        cross_line = validation.get("cross_line", "")
        if not cross_line:
            return 0.3
        # 检查VAL-01中是否有额外验证
        val_results = self.validation.get("results", {}).get(exp_id, {})
        cross_checks = [k for k in val_results.keys() if k.startswith("cross_")]
        if len(cross_checks) >= 2:
            return 0.95
        elif len(cross_checks) == 1:
            return 0.75
        return 0.5

    def _score_formalization(self, exp_id: str, results: Dict) -> float:
        """形式化程度评分"""
        if exp_id == "EXP-012":
            coq = results.get("coq_check", "")
            lean = results.get("lean_check", "")
            if "PASSED" in coq and "PASSED" in lean:
                return 1.0
            return 0.7
        # 其他实验不涉及形式化验证
        return 0.8  # 默认中等偏上

    def _score_boundary_tests(self, exp_id: str) -> float:
        """边界测试评分"""
        val_results = self.validation.get("results", {}).get(exp_id, {})
        boundary = val_results.get("boundary_tests", "")
        if "PASSED" in boundary:
            return 0.95
        return 0.5

    def _si_recommendations(self, exp_id: str, score: float) -> List[str]:
        """SI升级建议"""
        recs = []
        if score < 0.7:
            recs.append("建议补充实验数据后再评估SI升级")
        if score < 0.85:
            if exp_id == "EXP-011":
                recs.append("建议增加第二验证线")
            elif exp_id == "EXP-014":
                recs.append("建议扩大模拟尺度")
            elif exp_id == "EXP-015":
                recs.append("建议增加样本量")
        return recs

    # ============================================================
    # 生成报告
    # ============================================================
    def generate_report(self, check_results, comm_results, impl_results, verify_results, fix_results, si_audit) -> str:
        """生成Markdown格式的闭环验证报告"""
        lines = []
        lines.append("# 闭环验证自动报告")
        lines.append(f"**生成时间**: {datetime.now().isoformat()}Z")
        lines.append(f"**验证实验数**: {len(self.experiments)}")
        lines.append("")

        # 总体统计
        total_pass = sum(1 for r in verify_results.values() if r["status"] == "PASS")
        lines.append("## 总体统计")
        lines.append(f"- 验证通过: {total_pass}/{len(self.experiments)}")
        lines.append(f"- 跨线验证对: {len(self.cross_line_pairs)}")
        lines.append(f"- Deepening Actions: {sum(len(self.experiments[e].get('deepening', [])) for e in self.experiments)}项")
        lines.append("")

        # 各实验详情
        lines.append("## 各实验闭环状态")
        lines.append("")
        for exp_id in sorted(self.experiments.keys()):
            exp = self.experiments[exp_id]
            line = exp.get("line", "")
            si = f"{exp.get('si_before', '')} -> {exp.get('si_target', '')}"

            c_status = check_results.get(exp_id, {}).get("status", "UNKNOWN")
            m_status = comm_results.get(exp_id, {}).get("status", "UNKNOWN")
            i_status = impl_results.get(exp_id, {}).get("status", "UNKNOWN")
            v_status = verify_results.get(exp_id, {}).get("status", "UNKNOWN")

            lines.append(f"### {exp_id} ({line}) — SI: {si}")
            lines.append(f"| 阶段 | 状态 |")
            lines.append(f"|------|------|")
            lines.append(f"| CHECK | {c_status} |")
            lines.append(f"| COMMUNICATE | {m_status} |")
            lines.append(f"| IMPLEMENT | {i_status} |")
            lines.append(f"| VERIFY | {v_status} |")
            lines.append("")

            # 问题列表
            issues = fix_results.get(exp_id, {}).get("issues", [])
            if issues:
                lines.append("**发现问题**:")
                for issue in issues:
                    lines.append(f"- [{issue['phase']}] {issue['description']}")
                lines.append("")

            # 修正措施
            fixes = fix_results.get(exp_id, {}).get("fixes", [])
            if fixes:
                lines.append("**修正措施**:")
                for fix in fixes:
                    lines.append(f"- [{fix['severity']}] {fix['action']} (@{fix['responsible']})")
                lines.append("")

        # SI审计
        lines.append("## SI升级审计")
        lines.append("")
        lines.append("| 实验 | 升级 | 数据充分性 | 验证充分性 | 形式化 | 边界测试 | 综合 | 判定 |")
        lines.append("|------|------|------------|------------|--------|----------|------|------|")
        for exp_id, audit in sorted(si_audit.items()):
            scores = audit["scores"]
            lines.append(f"| {exp_id} | {audit['si_upgrade']} | {scores['data_sufficiency']:.2f} | ")
            f"{scores['verification_sufficiency']:.2f} | {scores['formalization']:.2f} | "
            f"{scores['boundary_tests']:.2f} | {audit['overall_score']:.2f} | {audit['verdict']} |"
        lines.append("")

        # 跨线验证矩阵
        lines.append("## 跨线验证矩阵")
        lines.append("")
        lines.append("| 源线 | 目标线 | 实验 | 状态 |")
        lines.append("|------|--------|------|------|")
        for pair in self.cross_line_pairs:
            lines.append(f"| {pair['from']} | {pair['to']} | {pair['exp_id']} | {pair['status']} |")
        lines.append("")

        return "\n".join(lines)

    def generate_json_report(self, check_results, comm_results, impl_results, verify_results, fix_results, si_audit) -> Dict:
        """生成JSON格式的闭环验证报告"""
        return {
            "report_id": "CLOSURE-VERIFY-AUTO",
            "timestamp": datetime.now().isoformat() + "Z",
            "mode": "LOCAL_FULL_DIMENSION_AUTONOMY",
            "experiments": {exp_id: {
                "line": self.experiments[exp_id].get("line", ""),
                "si_upgrade": f"{self.experiments[exp_id].get('si_before', '')} -> {self.experiments[exp_id].get('si_target', '')}",
                "check": check_results.get(exp_id, {}),
                "communicate": comm_results.get(exp_id, {}),
                "implement": impl_results.get(exp_id, {}),
                "verify": verify_results.get(exp_id, {}),
                "fix": fix_results.get(exp_id, {}),
                "si_audit": si_audit.get(exp_id, {})
            } for exp_id in sorted(self.experiments.keys())},
            "summary": {
                "total_experiments": len(self.experiments),
                "check_passed": sum(1 for r in check_results.values() if r["status"] in ("PASS", "WARNING")),
                "verify_passed": sum(1 for r in verify_results.values() if r["status"] == "PASS"),
                "deepening_pending": sum(len(self.experiments[e].get("deepening", [])) for e in self.experiments),
                "cross_line_pairs": len(self.cross_line_pairs),
                "si_fully_justified": sum(1 for a in si_audit.values() if a["verdict"] == "充分论证"),
                "si_conditionally_justified": sum(1 for a in si_audit.values() if a["verdict"] == "条件充分")
            }
        }

    # ============================================================
    # 主流程
    # ============================================================
    def run(self) -> bool:
        """执行完整闭环验证流程"""
        self.log("=" * 60, "INFO")
        self.log("UCIF2-Kernel 闭环验证启动", "INFO")
        self.log(f"实验目录: {self.experiment_dir}", "INFO")
        self.log(f"验证文件: {self.validation_file}", "INFO")
        self.log(f"输出目录: {self.output_dir}", "INFO")

        # 加载数据
        if not self.load_all():
            self.log("数据加载失败，终止验证", "ERROR")
            return False

        # 五步闭环
        check_results = self.step_check()
        comm_results = self.step_communicate()
        impl_results = self.step_implement()
        verify_results = self.step_verify()
        fix_results = self.step_fix(check_results, comm_results, impl_results, verify_results)
        si_audit = self.audit_si_upgrades()

        # 生成报告
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Markdown报告
        md_report = self.generate_report(check_results, comm_results, impl_results, verify_results, fix_results, si_audit)
        md_path = self.output_dir / "CLOSURE-VERIFY-REPORT-AUTO.md"
    with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_report)
    self.log(f"Markdown报告已生成: {md_path}", "INFO")

        # JSON报告
    json_report = self.generate_json_report(check_results, comm_results, impl_results, verify_results, fix_results, si_audit)
    json_path = self.output_dir / "CLOSURE-VERIFY-REPORT-AUTO.json"
    with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)
    self.log(f"JSON报告已生成: {json_path}", "INFO")

        # 总结
    self.log("=" * 60, "INFO")
    self.log("闭环验证完成", "INFO")
    self.log(f"验证通过: {sum(1 for r in verify_results.values() if r['status'] == 'PASS')}/{len(self.experiments)}", "INFO")
    self.log(f"需修正问题: {sum(len(fix_results[e].get('issues', [])) for e in fix_results)}", "INFO")
    self.log(f"待落实action: {sum(len(self.experiments[e].get('deepening', [])) for e in self.experiments)}项", "INFO")

    return True


def main():
    parser = argparse.ArgumentParser(description="UCIF2-Kernel 闭环验证脚本")
    parser.add_argument("--experiment-dir", default=DEFAULT_EXPERIMENT_DIR, help="实验文件目录")
    parser.add_argument("--validation-file", default=DEFAULT_VALIDATION_FILE, help="验证文件路径")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="输出目录")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    parser.add_argument("--no-color", action="store_true", help="禁用颜色输出")
    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    verifier = ClosureVerifier(
        experiment_dir=args.experiment_dir,
        validation_file=args.validation_file,
        output_dir=args.output_dir,
        verbose=args.verbose
    )

    success = verifier.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
