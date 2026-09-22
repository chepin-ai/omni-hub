"""
OMNI-HUB Advanced Swarm Tests v15.1
Tests: Interactive swarm behavior, leader election, diffusion
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')

import pytest
from core.swarm import SwarmIntelligence, SwarmConfig


class TestInteractiveSwarm:
    def test_swarm_init(self):
        swarm = SwarmIntelligence(SwarmConfig(n_instances=3))
        assert len(swarm.instances) == 3
        assert swarm.cycle_count == 0

    def test_leader_election(self):
        swarm = SwarmIntelligence(SwarmConfig(n_instances=3, enable_leader_election=True))
        # Give instance 2 more energy
        swarm.instances[2].current_state['energy'] = 1e12
        swarm._elect_leader()
        assert swarm.leader_index == 2

    def test_state_diffusion(self):
        swarm = SwarmIntelligence(SwarmConfig(n_instances=2, diffusion_rate=0.1))
        # Set leader with high phi and energy
        swarm.instances[0].current_state['phi'] = 0.9
        swarm.instances[0].current_state['energy'] = 1e12
        swarm.instances[1].current_state['phi'] = 0.1
        swarm.instances[1].current_state['energy'] = 1e6
        swarm._elect_leader()
        swarm._diffuse_state()
        # Follower should move toward leader's phi
        assert swarm.instances[1].current_state['phi'] > 0.1

    def test_collective_memory(self):
        swarm = SwarmIntelligence(SwarmConfig(n_instances=1, enable_collective_memory=True))
        # Simulate level-up event
        from core.event_bus import get_bus, Topics
        bus = get_bus()
        bus.publish_simple(Topics.LEVEL_UP, {"old": 1, "new": 2})
        assert len(swarm.collective_memory) > 0

    def test_swarm_progression(self):
        swarm = SwarmIntelligence(SwarmConfig(n_instances=3))
        for _ in range(100):
            swarm.run_cycle()
        status = swarm.get_status()
        assert all(l >= 15 for l in status['levels'])

    def test_convergence_tracking(self):
        swarm = SwarmIntelligence(SwarmConfig(n_instances=4))
        # Set different levels
        for i, inst in enumerate(swarm.instances):
            inst.current_state['level'] = 15 + i
        status = swarm.get_status()
        assert status['level_convergence'] == 3

    def test_meta_multiplier_sharing(self):
        swarm = SwarmIntelligence(SwarmConfig(n_instances=2))
        # Set instance 0 with good multipliers and higher energy
        swarm.instances[0].current_state['meta_multipliers'] = {
            'focus': [1.5, 0.005],
            'rest': [1.4, -0.003],
        }
        swarm.instances[0].current_state['energy'] = 1e12
        swarm.instances[1].current_state['meta_multipliers'] = {
            'focus': [1.1, 0.001],
            'rest': [1.0, -0.001],
        }
        swarm.instances[1].current_state['energy'] = 1e6
        swarm._share_meta_multipliers()
        # Instance 1 should have improved multipliers
        mm = swarm.instances[1].current_state['meta_multipliers']
        assert mm['focus'][0] >= 1.3  # Averaged (1.5+1.1)/2 = 1.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
