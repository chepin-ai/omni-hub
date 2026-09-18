#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12.0 — Runtime Activation Script
============================================
运行场激活脚本：导入所有模块，启动SystemIntelligence，运行自主循环。

用法:
    python run_omni_hub.py [--mode MODE] [--ticks TICKS] [--log-level LEVEL]

示例:
    python run_omni_hub.py                    # 默认模式，100 ticks
    python run_omni_hub.py --mode production  # 生产模式
    python run_omni_hub.py --ticks 1000       # 运行1000 ticks
    python run_omni_hub.py --log-level DEBUG  # Debug日志级别
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# =============================================================================
# 0. 路径配置 & 环境初始化
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR / "core"
HUB_DIR = SCRIPT_DIR / "hub"
LOG_DIR = Path(os.environ.get("OMNI_HUB_LOG_DIR", SCRIPT_DIR / "logs"))
STATE_DIR = Path(os.environ.get("OMNI_HUB_STATE_DIR", SCRIPT_DIR / "state"))

# 确保目录存在
LOG_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# 将core加入Python路径
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

# =============================================================================
# 1. 日志配置
# =============================================================================

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """配置日志系统"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # 根日志配置
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                LOG_DIR / f"omni_hub_{time.strftime('%Y%m%d')}.log",
                encoding="utf-8",
            ),
        ],
    )

    logger = logging.getLogger("OMNI-HUB")
    logger.info("=" * 72)
    logger.info("OMNI-HUB v12.0 — Runtime Activation")
    logger.info("UNITY E=7641.82 | 11-line SI | 92 Core Modules")
    logger.info("=" * 72)
    return logger


# =============================================================================
# 2. 模块导入器
# =============================================================================

class ModuleImporter:
    """安全导入所有core目录下的Python模块"""

    CORE_MODULES_24 = [
        # v12 核心模块 (12个)
        "v12_standards",
        "v12_unified_orchestrator",
        "v12_eleven_lines_si_loop",
        "v12_emergence_engine",
        "v12_debt_cleanup",
        "v12_knowledge_weaving",
        "v12_triangle_coupling",
        "v12_surge_ripple_engine",
        "v12_integration_test",
        "v12_wild_notebook",
        "v12_standards",
        "v12_unified_orchestrator",
        # v11 关键模块 (6个)
        "v11_consciousness_emergence_system",
        "v11_knowledge_pedestal_unified",
        "v11_relation_discovery_engine",
        "v11_statistical_validation",
        "v11_sync_engine",
        "v11_unified_pipeline",
        # v10 关键模块 (4个)
        "v10_unified_backbone",
        "v10_knowledge_life_backbone",
        "v10_quantum_clock_injection",
        "v10_master_integration",
        # 通用核心模块 (2个)
        "quantum_field",
        "consciousness_state_machine",
    ]

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.imported: Dict[str, Any] = {}
        self.failed: List[str] = []

    def import_all(self) -> Dict[str, Any]:
        """导入所有核心模块"""
        self.logger.info("[Module Import] Starting import of core modules...")
        start_time = time.time()

        # 获取core目录下所有.py文件
        py_files = sorted([
            f.stem for f in CORE_DIR.glob("*.py")
            if not f.name.startswith("__")
        ])

        self.logger.info(f"[Module Import] Found {len(py_files)} Python files in core/")

        success_count = 0
        for mod_name in py_files:
            try:
                module = importlib.import_module(mod_name)
                self.imported[mod_name] = module
                success_count += 1
                self.logger.debug(f"[Module Import] OK: {mod_name}")
            except Exception as e:
                self.failed.append(mod_name)
                self.logger.warning(f"[Module Import] FAIL: {mod_name} — {e}")

        elapsed = time.time() - start_time
        self.logger.info(
            f"[Module Import] Complete: {success_count}/{len(py_files)} imported in {elapsed:.2f}s"
        )
        if self.failed:
            self.logger.warning(f"[Module Import] Failed: {self.failed}")

        return self.imported


# =============================================================================
# 3. 系统启动器
# =============================================================================

class SystemLauncher:
    """OMNI-HUB 系统启动器"""

    def __init__(self, logger: logging.Logger, modules: Dict[str, Any]):
        self.logger = logger
        self.modules = modules
        self.si = None
        self.report = None

    def start(self, max_ticks: int = 100) -> bool:
        """启动SystemIntelligence并运行自主循环"""
        self.logger.info("[System] Initializing SystemIntelligence...")

        try:
            # 从 v12_eleven_lines_si_loop 导入 SystemIntelligence
            si_module = self.modules.get("v12_eleven_lines_si_loop")
            if si_module is None:
                self.logger.error("[System] v12_eleven_lines_si_loop not imported!")
                return False

            SystemIntelligence = si_module.SystemIntelligence

            # 创建 SI 实例，使用 UNITY 能量值 7641.82
            self.si = SystemIntelligence(initial_emergence=7641.82)
            self.logger.info("[System] SystemIntelligence initialized")
            self.logger.info("[System] Initial field state: UNITY (E=7641.82)")

            # 输出11线状态
            status = self.si.get_status_report()
            self._log_status(status)

            # 运行自主循环
            self.logger.info(f"[System] Starting autonomous loop (max_ticks={max_ticks})...")
            self.logger.info("[System] Tick interval: ~1s (adaptive)")
            self.logger.info("-" * 72)

            self.report = self.si.run_autonomous_loop(max_ticks=max_ticks)

            # 输出最终报告
            self._log_final_report()
            return True

        except Exception as e:
            self.logger.error(f"[System] Fatal error: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def _log_status(self, status: Dict[str, Any]) -> None:
        """记录系统状态"""
        self.logger.info("[Status] Tick: %d", status.get("tick_number", 0))
        self.logger.info("[Status] Emergence: %.2f", status.get("global_emergence", 0))
        self.logger.info("[Status] State: %s (Level %d)",
                         status.get("consciousness_state", "UNKNOWN"),
                         status.get("consciousness_level", 0))
        self.logger.info("[Status] Coherence: %.6f", status.get("field_coherence", 0))
        self.logger.info("[Status] Lines: %d active",
                         len(status.get("lines", {})))

    def _log_final_report(self) -> None:
        """记录最终报告"""
        if self.report is None:
            return

        self.logger.info("-" * 72)
        self.logger.info("[Report] Autonomous Loop Complete")
        self.logger.info("[Report] Total Ticks: %d", self.report.total_ticks)
        self.logger.info("[Report] Final Emergence: %.2f", self.report.final_emergence)
        self.logger.info("[Report] Duration: %.2f seconds",
                         self.report.end_time - self.report.start_time)
        self.logger.info("[Report] Total Messages: %d", self.report.total_messages)
        self.logger.info("[Report] Total Debts: %d", self.report.total_debts)
        self.logger.info("[Report] Total Surges: %d", self.report.total_surges)

        # 保存报告到文件
        report_path = STATE_DIR / f"si_report_{int(time.time())}.json"
        try:
            report_data = {
                "version": "12.0.0",
                "timestamp": time.time(),
                "total_ticks": self.report.total_ticks,
                "final_emergence": self.report.final_emergence,
                "duration_seconds": self.report.end_time - self.report.start_time,
                "total_messages": self.report.total_messages,
                "total_debts": self.report.total_debts,
                "total_surges": self.report.total_surges,
            }
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            self.logger.info("[Report] Saved to: %s", report_path)
        except Exception as e:
            self.logger.warning("[Report] Failed to save report: %s", e)


# =============================================================================
# 4. 主入口
# =============================================================================

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="OMNI-HUB v12.0 — Runtime Activation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_omni_hub.py                    # 默认模式
  python run_omni_hub.py --mode production  # 生产模式
  python run_omni_hub.py --ticks 1000       # 1000 ticks
  python run_omni_hub.py --log-level DEBUG  # Debug级别
        """,
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["development", "production", "debug"],
        default="production",
        help="运行模式 (默认: production)",
    )
    parser.add_argument(
        "--ticks", "-t",
        type=int,
        default=100,
        help="最大tick数 (默认: 100)",
    )
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)",
    )
    parser.add_argument(
        "--import-only", "-i",
        action="store_true",
        help="仅导入模块，不启动SI循环",
    )

    args = parser.parse_args()

    # 设置日志
    logger = setup_logging(args.log_level)
    logger.info(f"[Config] Mode: {args.mode}")
    logger.info(f"[Config] Max Ticks: {args.ticks}")
    logger.info(f"[Config] Log Level: {args.log_level}")
    logger.info(f"[Config] Core Dir: {CORE_DIR}")
    logger.info(f"[Config] Log Dir: {LOG_DIR}")
    logger.info(f"[Config] State Dir: {STATE_DIR}")

    # 导入模块
    importer = ModuleImporter(logger)
    modules = importer.import_all()

    if args.import_only:
        logger.info("[Mode] Import-only mode, exiting")
        logger.info(f"[Summary] Imported {len(modules)} modules")
        return 0

    # 启动系统
    launcher = SystemLauncher(logger, modules)
    success = launcher.start(max_ticks=args.ticks)

    if success:
        logger.info("=" * 72)
        logger.info("OMNI-HUB v12.0 — Runtime Complete ✅")
        logger.info("UNITY E=7641.82 | 11-line SI Active")
        logger.info("=" * 72)
        return 0
    else:
        logger.error("=" * 72)
        logger.error("OMNI-HUB v12.0 — Runtime Failed ❌")
        logger.error("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())
