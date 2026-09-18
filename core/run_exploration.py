#!/usr/bin/env python3

"""Run FullPotentialExplorer on all modules and save results."""

__version__ = "11.0.0"
import sys
import os
import io
import contextlib
import threading

os.chdir('/mnt/agents/output/OMNI-HUB/core')
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB/core')
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import importlib.util
spec = importlib.util.spec_from_file_location("full_potential_explorer", 
    "/mnt/agents/output/OMNI-HUB/core/full_potential_explorer.py")
fpe_module = importlib.util.module_from_spec(spec)
sys.modules["full_potential_explorer"] = fpe_module
spec.loader.exec_module(fpe_module)

explorer = fpe_module.FullPotentialExplorer(hub_dir='/mnt/agents/output/OMNI-HUB')
modules = explorer.discover_modules()

def explore_one(explorer, module_name, timeout_sec=15):
    result_container = {}
    def target():
            result_container['result'] = explorer.explore_module(module_name, depth='full')
            result_container['error'] = str(e)
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_sec)
    
    if thread.is_alive():
        return {"status": "timeout", "module": module_name}
    return result_container.get('result', result_container.get('error', 'unknown'))

logger.info(f"\nProcessing {len(modules)} modules...\n")

for i, mod in enumerate(modules, 1):
    logger.info(f"[{i}/{len(modules)}] {mod}...", end=" ", flush=True)
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        r = explore_one(explorer, mod, 15)
    if isinstance(r, dict):
        success = r.get('success_count', 0)
        total = r.get('methods_invoked', 0)
        logger.info(f"{success}/{total} OK")
    else:
        logger.info(f"ERROR: {str(r)[:60]}")

# Generate and save report
logger.info("\n\nGenerating report...")
report = explorer.generate_potential_report()

# Save report
report_file = '/mnt/agents/output/OMNI-HUB/audit/full_potential_report.txt'
os.makedirs(os.path.dirname(report_file), exist_ok=True)
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(report)
logger.info(f"Report saved to: {report_file}")

# Save capability map
cap_file = '/mnt/agents/output/OMNI-HUB/audit/capability_map.json'
cap_data = explorer.capability_map.export(cap_file)
logger.info(f"Capability map saved to: {cap_file}")

# Save stats
import json
stats_file = '/mnt/agents/output/OMNI-HUB/audit/explorer_stats.json'
with open(stats_file, 'w') as f:
    json.dump({
        'stats': explorer.stats,
        'coverage': explorer.capability_map.get_coverage(),
        'sleeping': explorer.capability_map.get_sleeping_capabilities(),
    }, f, indent=2, default=str)
logger.info(f"Stats saved to: {stats_file}")

logger.info("\n" + "="*70)
logger.info("EXPLORATION COMPLETE")
logger.info("="*70)
