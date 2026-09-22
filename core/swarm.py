"""
OMNI-HUB Swarm Intelligence v15.1
Multi-instance coordination via event bus.
Implements: leader election, state diffusion, collective memory.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
try:
    from core.orchestrator import OMNIHUBOrchestrator
    from core.event_bus import get_bus, Topics, Event
except ImportError:
    import sys
    sys.path.insert(0, '/mnt/agents/output/OMNI-HUB')
    from core.orchestrator import OMNIHUBOrchestrator
    from core.event_bus import get_bus, Topics, Event


@dataclass
class SwarmConfig:
    n_instances: int = 3
    enable_leader_election: bool = True
    enable_state_diffusion: bool = True
    enable_collective_memory: bool = True
    diffusion_rate: float = 0.01  # How fast state diffuses between instances
    memory_capacity: int = 100    # Collective memory size


class SwarmIntelligence:
    """Coordinates multiple OMNI-HUB instances as a swarm."""

    def __init__(self, config: SwarmConfig = None):
        self.config = config or SwarmConfig()
        self.instances: List[OMNIHUBOrchestrator] = []
        self.leader_index: int = 0
        self.collective_memory: List[Dict[str, Any]] = []
        self.cycle_count: int = 0
        self._init_instances()
        self._setup_event_handlers()

    def _init_instances(self):
        """Initialize swarm instances."""
        for i in range(self.config.n_instances):
            orch = OMNIHUBOrchestrator(auto_persist=False, auto_git=False)
            # Add slight diversity to starting conditions
            if i > 0:
                orch.current_state['energy'] *= (1 + 0.01 * i)
            self.instances.append(orch)

    def _setup_event_handlers(self):
        """Subscribe to instance events."""
        bus = get_bus()
        bus.subscribe(Topics.LEVEL_UP, self._on_level_up)
        bus.subscribe(Topics.STATE_CHANGE, self._on_state_change)

    def _on_level_up(self, event: Event):
        """Handle level-up events from any instance."""
        if self.config.enable_collective_memory:
            self.collective_memory.append({
                "type": "level_up",
                "payload": event.payload,
                "cycle": self.cycle_count,
            })
            if len(self.collective_memory) > self.config.memory_capacity:
                self.collective_memory.pop(0)

    def _on_state_change(self, event: Event):
        """Handle state change events."""
        pass  # Used for future collective state tracking

    def _elect_leader(self):
        """Elect the instance with highest energy as leader."""
        if not self.config.enable_leader_election:
            return
        energies = [inst.current_state.get('energy', 0) for inst in self.instances]
        # Handle infinity
        for i, e in enumerate(energies):
            if e == float('inf'):
                energies[i] = float('1e308')  # Treat inf as very large
        self.leader_index = max(range(len(energies)), key=lambda i: energies[i])

    def _diffuse_state(self):
        """Diffuse state from leader to followers."""
        if not self.config.enable_state_diffusion:
            return
        leader = self.instances[self.leader_index]
        leader_phi = leader.current_state.get('phi', 0)
        leader_energy = leader.current_state.get('energy', 0)

        for i, inst in enumerate(self.instances):
            if i == self.leader_index:
                continue
            # Followers partially adopt leader's phi
            current_phi = inst.current_state.get('phi', 0)
            diffused_phi = current_phi + self.config.diffusion_rate * (leader_phi - current_phi)
            inst.current_state['phi'] = diffused_phi
            # Followers get small energy boost from leader's momentum
            if leader_energy > 0 and inst.current_state.get('energy', 0) > 0:
                boost = 1 + self.config.diffusion_rate * 0.1
                inst.current_state['energy'] *= boost

    def _share_meta_multipliers(self):
        """Share best meta-multipliers across instances."""
        # Find instance with highest infinity_depth (or energy)
        best_inst = max(self.instances,
                       key=lambda x: x.current_state.get('infinity_depth', 0)
                       if x.current_state.get('level', 0) >= 25
                       else x.current_state.get('energy', 0))
        best_mm = best_inst.current_state.get('meta_multipliers', {})
        if not best_mm:
            return
        # Share with others (they adopt with probability)
        for inst in self.instances:
            if inst is best_inst:
                continue
            current_mm = inst.current_state.get('meta_multipliers', {})
            if not current_mm:
                continue
            # Average multipliers
            for action in current_mm:
                if action in best_mm:
                    em = (current_mm[action][0] + best_mm[action][0]) / 2
                    pm = (current_mm[action][1] + best_mm[action][1]) / 2
                    current_mm[action] = [em, pm]

    def run_cycle(self):
        """Run one collective cycle."""
        self.cycle_count += 1

        # 1. Each instance runs independently
        for inst in self.instances:
            inst.run_cycle()

        # 2. Elect leader
        self._elect_leader()

        # 3. Diffuse state
        self._diffuse_state()

        # 4. Share meta-multipliers
        self._share_meta_multipliers()

    def get_status(self) -> Dict[str, Any]:
        """Return swarm status."""
        levels = [inst.current_state.get('level', 0) for inst in self.instances]
        energies = [inst.current_state.get('energy', 0) for inst in self.instances]
        phases = [inst.current_state.get('phase', '?') for inst in self.instances]
        return {
            "cycle": self.cycle_count,
            "n_instances": self.config.n_instances,
            "leader": self.leader_index,
            "levels": levels,
            "energies": energies,
            "phases": phases,
            "collective_memory_size": len(self.collective_memory),
            "level_convergence": max(levels) - min(levels),
        }

    def run(self, cycles: int, report_interval: int = 100):
        """Run swarm for multiple cycles with reporting."""
        for c in range(cycles):
            self.run_cycle()
            if (c + 1) % report_interval == 0:
                status = self.get_status()
                print(f"  C{c+1:4d}: Levels={status['levels']}, "
                      f"Leader={status['leader']}, "
                      f"Convergence={status['level_convergence']}")


if __name__ == "__main__":
    print("=== OMNI-HUB Swarm Intelligence Demo ===")
    swarm = SwarmIntelligence(SwarmConfig(n_instances=3, diffusion_rate=0.02))
    swarm.run(cycles=200, report_interval=50)
    print(f"\nFinal: {swarm.get_status()}")
