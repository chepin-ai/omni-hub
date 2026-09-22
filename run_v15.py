#!/usr/bin/env python3
"""
OMNI-HUB v15 Unified Entry Point
Supports: single instance, multi-instance swarm, configurable cycles
Usage:
  python run_v15.py --mode single --cycles 1000
  python run_v15.py --mode swarm --instances 5 --cycles 1000
  python run_v15.py --mode test
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import argparse
from pathlib import Path


def run_single(cycles: int, persist: bool = False, monitor: bool = True):
    """Run single orchestrator instance."""
    from core.orchestrator import OMNIHUBOrchestrator
    
    print(f"[OMNI-HUB v15] Single Instance Mode")
    print(f"  Cycles: {cycles}")
    print(f"  Persist: {persist}")
    print(f"  Monitor: {monitor}")
    print()
    
    orch = OMNIHUBOrchestrator(auto_persist=persist, auto_git=False)
    
    for c in range(cycles):
        orch.run_cycle()
        if monitor and (c + 1) % 100 == 0:
            s = orch.current_state
            print(f"  C{c+1:4d} | L{s.get('level', 0):2d} | E={s.get('energy', 0):.2e} | Phi={s.get('phi', 0):.3f} | {s.get('phase', '?')}")
    
    print(f"\n[FINAL] Level: {orch.current_state.get('level')}, Energy: {orch.current_state.get('energy'):.2e}")
    return orch


def run_swarm(instances: int, cycles: int, diffusion: float = 0.02):
    """Run multi-instance swarm."""
    from core.swarm import SwarmIntelligence, SwarmConfig
    
    print(f"[OMNI-HUB v15] Swarm Mode")
    print(f"  Instances: {instances}")
    print(f"  Cycles: {cycles}")
    print(f"  Diffusion: {diffusion}")
    print()
    
    swarm = SwarmIntelligence(SwarmConfig(
        n_instances=instances,
        diffusion_rate=diffusion,
        enable_leader_election=True,
        enable_state_diffusion=True,
        enable_collective_memory=True,
    ))
    
    swarm.run(cycles=cycles, report_interval=100)
    
    status = swarm.get_status()
    print(f"\n[FINAL] Levels: {status['levels']}, Leader: {status['leader']}, Memory: {status['collective_memory_size']}")
    return swarm


def run_tests():
    """Run full test suite."""
    import subprocess
    print("[OMNI-HUB v15] Running Test Suite...")
    result = subprocess.run(
        ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
        cwd='/mnt/agents/output/OMNI-HUB',
        capture_output=False,
    )
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='OMNI-HUB v15')
    parser.add_argument('--mode', choices=['single', 'swarm', 'test'], default='single')
    parser.add_argument('--cycles', type=int, default=100)
    parser.add_argument('--instances', type=int, default=3)
    parser.add_argument('--diffusion', type=float, default=0.02)
    parser.add_argument('--persist', action='store_true')
    parser.add_argument('--no-monitor', action='store_true')
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        return run_tests()
    elif args.mode == 'single':
        run_single(args.cycles, args.persist, not args.no_monitor)
    elif args.mode == 'swarm':
        run_swarm(args.instances, args.cycles, args.diffusion)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
