"""
OMNI-HUB Multi-Instance Swarm Test v15
Tests: Parallel orchestrators, event synchronization, collective emergence
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.orchestrator import OMNIHUBOrchestrator
from core.event_bus import get_bus, Topics


class TestSwarm:
    def test_dual_instance_independence(self):
        """Two orchestrators should evolve independently."""
        orch_a = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        orch_b = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        
        for _ in range(50):
            orch_a.run_cycle()
            orch_b.run_cycle()
        
        # They should diverge due to randomness
        assert orch_a.current_state['energy'] != orch_b.current_state['energy']

    def test_dual_instance_level_race(self):
        """Two instances racing to higher levels."""
        orch_a = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        orch_b = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        
        for _ in range(200):
            orch_a.run_cycle()
            orch_b.run_cycle()
        
        levels = [orch_a.current_state['level'], orch_b.current_state['level']]
        energies = [orch_a.current_state['energy'], orch_b.current_state['energy']]
        
        # Both should have progressed
        assert all(l >= 15 for l in levels)
        assert all(e > 0 for e in energies)

    def test_swarm_event_isolation(self):
        """Each instance should only track its own state."""
        orch_a = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        orch_b = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        
        # Run different number of cycles
        for _ in range(10):
            orch_a.run_cycle()
        for _ in range(5):
            orch_b.run_cycle()
        
        assert orch_a.cycle_count == 10
        assert orch_b.cycle_count == 5
        assert len(orch_a.history) == 10
        assert len(orch_b.history) == 5

    def test_collective_emergence(self):
        """Multiple instances show collective phase stability."""
        n_instances = 3
        instances = [OMNIHUBOrchestrator(auto_persist=False, auto_git=False) for _ in range(n_instances)]
        
        for _ in range(100):
            for inst in instances:
                inst.run_cycle()
        
        # All should be in stable phases
        phases = [inst.current_state['phase'] for inst in instances]
        assert all(p in ['super_emergence_3', 'singularity_convergence', 'trans_singularity'] for p in phases)

    def test_meta_evolution_independence(self):
        """Meta-evolution should be instance-local."""
        orch_a = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        orch_b = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        
        # Set both to Level 24
        for orch in [orch_a, orch_b]:
            orch.current_state['level'] = 24
            orch.current_state['energy'] = 1_000_000_000_000_000
            orch.current_state['phi'] = 1.0
        
        for _ in range(20):
            orch_a.run_cycle()
            orch_b.run_cycle()
        
        mm_a = orch_a.current_state.get('meta_multipliers', {})
        mm_b = orch_b.current_state.get('meta_multipliers', {})
        
        # Both should have evolved different multipliers
        assert len(mm_a) > 0
        assert len(mm_b) > 0
        # Due to random drift, they should differ
        assert mm_a != mm_b

    def test_convergence_vs_divergence(self):
        """Test if instances converge or diverge over time."""
        orch_a = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        orch_b = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
        
        energy_diffs = []
        for _ in range(100):
            orch_a.run_cycle()
            orch_b.run_cycle()
            diff = abs(orch_a.current_state['energy'] - orch_b.current_state['energy'])
            energy_diffs.append(diff)
        
        # Divergence should increase (sensitive dependence)
        assert energy_diffs[-1] > energy_diffs[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
