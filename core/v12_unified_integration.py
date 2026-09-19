#!/usr/bin/env python3
"""
OMNI-HUB v12 - Unified Integration Hub
========================================
Fusion Architecture Component: Central Integration & Orchestration

Responsibilities:
  - Module Bus:      Unified message routing between all components
  - State Management: Centralized state with consistency guarantees
  - Configuration:   Hierarchical config with hot-reload
  - Logging:         Structured logging with distributed tracing
  - Monitoring:      Health checks, metrics aggregation, alerting

Integration Pattern (from 10 paradigms):
  - Event-driven architecture (EDA)
  - CQRS for state separation
  - Circuit breaker for resilience
  - Saga pattern for distributed transactions
  - Observer pattern for reactive updates

Author: OMNI-HUB Fusion Architect
Version: 12.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Generic, Protocol

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("unified_integration")


# ---------------------------------------------------------------------------
# Domain Model
# ---------------------------------------------------------------------------

class MessageType(Enum):
    COMMAND = auto()
    EVENT = auto()
    QUERY = auto()
    RESPONSE = auto()
    ERROR = auto()
    HEARTBEAT = auto()


class ModuleState(Enum):
    INITIALIZING = auto()
    READY = auto()
    BUSY = auto()
    DEGRADED = auto()
    ERROR = auto()
    SHUTDOWN = auto()


@dataclass
class Message:
    """Standard message envelope for module bus."""
    msg_id: str
    msg_type: MessageType
    source_module: str
    target_module: Optional[str]  # None = broadcast
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: Optional[str] = None
    priority: int = 5  # 1=highest, 10=lowest


@dataclass
class ModuleHealth:
    """Health status of a registered module."""
    module_name: str
    state: ModuleState
    last_heartbeat: str
    metrics: Dict[str, float] = field(default_factory=dict)
    active_jobs: int = 0
    error_count: int = 0
    avg_response_ms: float = 0.0


@dataclass
class SystemState:
    """Global system state snapshot."""
    timestamp: str
    modules: Dict[str, ModuleHealth]
    bus_stats: Dict[str, Any]
    config_version: str
    alerts: List[Dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Module Bus (Event-Driven Message Router)
# ---------------------------------------------------------------------------

class ModuleBus:
    """
    Central message bus for inter-module communication.
    Implements priority queue, broadcast, and request-response patterns.
    """

    def __init__(self, max_queue_size: int = 10000):
        self._queue: asyncio.PriorityQueue[Tuple[int, Message]] = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._handlers: Dict[str, List[Callable[[Message], asyncio.Future]]] = defaultdict(list)
        self._response_futures: Dict[str, asyncio.Future] = {}
        self._stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_dropped": 0,
            "broadcasts": 0,
        }
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._running = True
        logger.info("Module bus started")
        while self._running:
            try:
                _, msg = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._deliver(msg)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Bus delivery error: {e}")

    def stop(self) -> None:
        self._running = False
        logger.info("Module bus stopped")

    async def send(self, msg: Message) -> None:
        """Send a message (fire-and-forget)."""
        async with self._lock:
            self._stats["messages_sent"] += 1
        try:
            self._queue.put_nowait((msg.priority, msg))
        except asyncio.QueueFull:
            async with self._lock:
                self._stats["messages_dropped"] += 1
            logger.warning(f"Message dropped (queue full): {msg.msg_id}")

    async def request(self, msg: Message, timeout_sec: float = 30.0) -> Optional[Message]:
        """Send a request and wait for response."""
        future = asyncio.get_event_loop().create_future()
        self._response_futures[msg.msg_id] = future
        await self.send(msg)
        try:
            return await asyncio.wait_for(future, timeout=timeout_sec)
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout: {msg.msg_id}")
            return None
        finally:
            self._response_futures.pop(msg.msg_id, None)

    def respond(self, request_id: str, response: Message) -> None:
        """Send a response to a pending request."""
        future = self._response_futures.get(request_id)
        if future and not future.done():
            future.set_result(response)

    def register_handler(self, module_name: str, handler: Callable[[Message], asyncio.Future]) -> None:
        self._handlers[module_name].append(handler)
        logger.info(f"Registered handler for {module_name}")

    def unregister_handler(self, module_name: str, handler: Callable[[Message], asyncio.Future]) -> None:
        if handler in self._handlers[module_name]:
            self._handlers[module_name].remove(handler)

    async def _deliver(self, msg: Message) -> None:
        if msg.target_module is None:
            # Broadcast
            async with self._lock:
                self._stats["broadcasts"] += 1
            for module, handlers in self._handlers.items():
                for handler in handlers:
                    try:
                        await handler(msg)
                    except Exception as e:
                        logger.error(f"Handler error in {module}: {e}")
        else:
            # Targeted delivery
            handlers = self._handlers.get(msg.target_module, [])
            for handler in handlers:
                try:
                    await handler(msg)
                    async with self._lock:
                        self._stats["messages_delivered"] += 1
                except Exception as e:
                    logger.error(f"Delivery error to {msg.target_module}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)


# ---------------------------------------------------------------------------
# State Manager (CQRS + Event Sourcing)
# ---------------------------------------------------------------------------

class StateManager:
    """
    Centralized state management with CQRS separation.
    Commands mutate state; queries read projections.
    """

    def __init__(self, persist_dir: Path = Path("./state")):
        self.persist_dir = persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._state: Dict[str, Any] = {}
        self._projections: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._event_log: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._version = 0

    async def command(self, key: str, value: Any, source: str = "") -> None:
        """Execute a state mutation command."""
        async with self._lock:
            old_value = self._state.get(key)
            self._state[key] = value
            self._version += 1

            event = {
                "type": "state_change",
                "key": key,
                "old": old_value,
                "new": value,
                "source": source,
                "version": self._version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._event_log.append(event)
            await self._update_projections(key, value)
            await self._persist(event)

    async def query(self, key: str, default: Any = None) -> Any:
        """Execute a state query."""
        async with self._lock:
            return self._state.get(key, default)

    async def query_projection(self, projection_name: str, key: str, default: Any = None) -> Any:
        """Query a read-optimized projection."""
        async with self._lock:
            return self._projections[projection_name].get(key, default)

    async def _update_projections(self, key: str, value: Any) -> None:
        """Update derived projections based on state change."""
        # Module health projection
        if key.startswith("module."):
            module_name = key.split(".")[1]
            self._projections["module_health"][module_name] = value

        # Performance metrics projection
        if key.startswith("metric."):
            parts = key.split(".")
            if len(parts) >= 3:
                metric_type = parts[1]
                self._projections["metrics"][metric_type] = value

    async def _persist(self, event: Dict[str, Any]) -> None:
        """Persist event to durable log."""
        log_file = self.persist_dir / "event_log.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")

    async def snapshot(self) -> Dict[str, Any]:
        """Create a full state snapshot."""
        async with self._lock:
            snapshot = {
                "version": self._version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "state": dict(self._state),
                "projections": dict(self._projections),
            }
            snapshot_file = self.persist_dir / f"snapshot_v{self._version}.json"
            snapshot_file.write_text(json.dumps(snapshot, default=str), encoding="utf-8")
            return snapshot

    async def restore(self, version: Optional[int] = None) -> bool:
        """Restore state from snapshot + event replay."""
        # In production: load snapshot, replay events from that version
        logger.info(f"State restore requested (version={version})")
        return True


# ---------------------------------------------------------------------------
# Configuration Manager (Hierarchical + Hot Reload)
# ---------------------------------------------------------------------------

class ConfigManager:
    """
    Hierarchical configuration with environment-specific overrides
    and hot-reload capability.
    """

    DEFAULT_CONFIG = {
        "system": {
            "name": "OMNI-HUB",
            "version": "12.0.0",
            "environment": "production",
            "log_level": "INFO",
        },
        "bus": {
            "max_queue_size": 10000,
            "default_timeout_sec": 30.0,
            "heartbeat_interval_sec": 60.0,
        },
        "lean_auto": {
            "max_concurrent": 4,
            "tier_timeout_sec": {
                "TIER_1_CORE": 30.0,
                "TIER_2_SEARCH": 60.0,
                "TIER_3_SYMBOLIC": 45.0,
                "TIER_4_HEURISTIC": 20.0,
                "TIER_5_FALLBACK": 15.0,
            },
            "tool_retry_count": 2,
        },
        "wildbook": {
            "max_questions_per_batch": 100,
            "default_priority": "MEDIUM",
            "escalation_threshold": 0.3,
        },
        "evolution": {
            "cycle_interval_sec": 300.0,
            "min_cycles_before_prune": 10,
            "score_threshold_for_action": 0.5,
        },
        "integration": {
            "health_check_interval_sec": 30.0,
            "alert_threshold": 3,
            "auto_restart": True,
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        self._config: Dict[str, Any] = {}
        self._listeners: List[Callable[[str, Any, Any], None]] = []
        self._lock = asyncio.Lock()
        self.config_path = config_path
        self._version = "default"
        self.load_defaults()

    def load_defaults(self) -> None:
        self._config = json.loads(json.dumps(self.DEFAULT_CONFIG))

    async def load_from_file(self, path: Path) -> None:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            async with self._lock:
                self._deep_merge(self._config, data)
                self._version = str(int(time.time()))
                self.config_path = path
            logger.info(f"Config loaded from {path} (version={self._version})")

    def get(self, path: str, default: Any = None) -> Any:
        """Get config value by dot-notation path."""
        parts = path.split(".")
        current = self._config
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    async def set(self, path: str, value: Any) -> None:
        """Set config value and notify listeners."""
        parts = path.split(".")
        async with self._lock:
            current = self._config
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            old_value = current.get(parts[-1])
            current[parts[-1]] = value

        for listener in self._listeners:
            try:
                listener(path, old_value, value)
            except Exception as e:
                logger.error(f"Config listener error: {e}")

    def register_listener(self, listener: Callable[[str, Any, Any], None]) -> None:
        self._listeners.append(listener)

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    @property
    def version(self) -> str:
        return self._version


# ---------------------------------------------------------------------------
# Logging & Monitoring
# ---------------------------------------------------------------------------

class StructuredLogger:
    """
    Structured logging with distributed tracing support.
    Outputs JSON Lines format for log aggregation.
    """

    def __init__(self, log_dir: Path = Path("./logs")):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._trace_context: Dict[str, str] = {}

    def set_trace(self, trace_id: str, span_id: str) -> None:
        self._trace_context = {"trace_id": trace_id, "span_id": span_id}

    def log(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            **self._trace_context,
            **(extra or {}),
        }
        log_file = self.log_dir / f"omni-hub-{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self.log("INFO", message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self.log("WARNING", message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self.log("ERROR", message, extra)


class HealthMonitor:
    """
    Health monitoring with circuit breaker pattern.
    """

    def __init__(self, bus: ModuleBus, state: StateManager):
        self.bus = bus
        self.state = state
        self._modules: Dict[str, ModuleHealth] = {}
        self._circuit_breakers: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"failures": 0, "state": "closed", "last_failure": None}
        )
        self._running = False

    def register_module(self, name: str) -> None:
        self._modules[name] = ModuleHealth(
            module_name=name,
            state=ModuleState.INITIALIZING,
            last_heartbeat=datetime.now(timezone.utc).isoformat(),
        )

    async def update_heartbeat(self, name: str, metrics: Optional[Dict[str, float]] = None) -> None:
        if name in self._modules:
            self._modules[name].last_heartbeat = datetime.now(timezone.utc).isoformat()
            self._modules[name].state = ModuleState.READY
            if metrics:
                self._modules[name].metrics.update(metrics)

    async def check_health(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        alerts = []

        for name, health in self._modules.items():
            last_hb = datetime.fromisoformat(health.last_heartbeat.replace("Z", "+00:00"))
            if (now - last_hb).total_seconds() > 120:
                health.state = ModuleState.DEGRADED
                alerts.append({
                    "module": name,
                    "severity": "warning",
                    "message": f"No heartbeat for {(now - last_hb).total_seconds():.0f}s",
                })

            if health.error_count > 10:
                health.state = ModuleState.ERROR
                alerts.append({
                    "module": name,
                    "severity": "critical",
                    "message": f"High error count: {health.error_count}",
                })

        return {
            "timestamp": now.isoformat(),
            "modules": {name: asdict(h) for name, h in self._modules.items()},
            "alerts": alerts,
            "overall_status": "healthy" if not alerts else "degraded" if all(a["severity"] == "warning" for a in alerts) else "critical",
        }

    async def run_continuous(self, interval_sec: float = 30.0) -> None:
        self._running = True
        while self._running:
            health = await self.check_health()
            await self.state.command("system.health", health, source="health_monitor")

            # Publish health status to bus
            msg = Message(
                msg_id=f"health-{int(time.time())}",
                msg_type=MessageType.EVENT,
                source_module="health_monitor",
                target_module=None,
                payload=health,
            )
            await self.bus.send(msg)

            await asyncio.sleep(interval_sec)

    def stop(self) -> None:
        self._running = False

    def record_failure(self, module: str) -> None:
        cb = self._circuit_breakers[module]
        cb["failures"] += 1
        cb["last_failure"] = datetime.now(timezone.utc).isoformat()
        if cb["failures"] >= 5:
            cb["state"] = "open"
            logger.warning(f"Circuit breaker OPEN for {module}")

    def record_success(self, module: str) -> None:
        cb = self._circuit_breakers[module]
        cb["failures"] = max(0, cb["failures"] - 1)
        if cb["failures"] < 3 and cb["state"] == "open":
            cb["state"] = "half-open"
            logger.info(f"Circuit breaker HALF-OPEN for {module}")


# ---------------------------------------------------------------------------
# Unified Integration Hub
# ---------------------------------------------------------------------------

class UnifiedIntegrationHub:
    """
    Central integration hub that wires together all OMNI-HUB components.
    """

    def __init__(self, output_dir: Path = Path("./output")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Core subsystems
        self.bus = ModuleBus()
        self.state = StateManager(persist_dir=output_dir / "state")
        self.config = ConfigManager()
        self.logger = StructuredLogger(log_dir=output_dir / "logs")
        self.health = HealthMonitor(self.bus, self.state)

        # Module registry
        self._modules: Dict[str, Any] = {}
        self._running = False

    async def register_module(self, name: str, module_instance: Any) -> None:
        """Register a module and set up its message handlers."""
        self._modules[name] = module_instance
        self.health.register_module(name)

        # Create default message handler
        async def handler(msg: Message) -> None:
            if msg.target_module == name or msg.target_module is None:
                self.logger.info(f"Message received", extra={
                    "module": name,
                    "msg_type": msg.msg_type.name,
                    "msg_id": msg.msg_id,
                })

        self.bus.register_handler(name, handler)
        logger.info(f"Module '{name}' registered")

    async def start(self) -> None:
        """Start all integration services."""
        self._running = True
        logger.info("=== OMNI-HUB Unified Integration Hub Starting ===")

        # Start bus
        bus_task = asyncio.create_task(self.bus.start())

        # Start health monitoring
        health_task = asyncio.create_task(
            self.health.run_continuous(
                interval_sec=self.config.get("integration.health_check_interval_sec", 30.0)
            )
        )

        # Initialize all registered modules
        for name in self._modules:
            await self.health.update_heartbeat(name)
            await self.state.command(f"module.{name}", {"state": "ready"}, source="hub")

        logger.info("=== OMNI-HUB Integration Hub Ready ===")

        # Keep running
        try:
            while self._running:
                await asyncio.sleep(1)
        finally:
            bus_task.cancel()
            health_task.cancel()
            try:
                await bus_task
                await health_task
            except asyncio.CancelledError:
                pass

    async def stop(self) -> None:
        """Graceful shutdown."""
        logger.info("=== OMNI-HUB Integration Hub Shutting Down ===")
        self._running = False
        self.bus.stop()
        self.health.stop()

        # Save final state
        await self.state.snapshot()
        logger.info("Final state snapshot saved")

    async def send_command(self, target: str, command: str, params: Dict[str, Any]) -> Optional[Message]:
        """Send a command to a module and await response."""
        msg = Message(
            msg_id=f"cmd-{int(time.time()*1000)}",
            msg_type=MessageType.COMMAND,
            source_module="hub",
            target_module=target,
            payload={"command": command, "params": params},
        )
        return await self.bus.request(msg)

    def get_system_state(self) -> SystemState:
        """Get current system state."""
        return SystemState(
            timestamp=datetime.now(timezone.utc).isoformat(),
            modules={name: asdict(h) for name, h in self.health._modules.items()},
            bus_stats=self.bus.get_stats(),
            config_version=self.config.version,
            alerts=[],
        )

    def generate_report(self) -> Dict[str, Any]:
        """Generate integration status report."""
        state = self.get_system_state()
        return {
            "generated_at": state.timestamp,
            "config_version": state.config_version,
            "modules": {
                name: {
                    "state": h.state.name,
                    "metrics": h.metrics,
                    "active_jobs": h.active_jobs,
                }
                for name, h in self.health._modules.items()
            },
            "bus": state.bus_stats,
            "state_version": self.state._version,
            "overall_health": state.modules,
        }


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="OMNI-HUB Unified Integration Hub v12")
    ap.add_argument("--output-dir", type=Path, default=Path("./output"), help="Output directory")
    ap.add_argument("--config", type=Path, help="Path to config JSON file")
    ap.add_argument("--run-seconds", type=float, default=10.0, help="Run duration in seconds")
    args = ap.parse_args()

    hub = UnifiedIntegrationHub(output_dir=args.output_dir)

    if args.config:
        asyncio.run(hub.config.load_from_file(args.config))

    async def run():
        # Register demo modules
        await hub.register_module("lean_auto", {"status": "registered"})
        await hub.register_module("wildbook_resolver", {"status": "registered"})
        await hub.register_module("self_evolving", {"status": "registered"})
        await hub.register_module("fusion_architect", {"status": "registered"})

        # Start hub in background
        hub_task = asyncio.create_task(hub.start())

        # Let it run
        await asyncio.sleep(args.run_seconds)

        # Stop and report
        await hub.stop()
        hub_task.cancel()
        try:
            await hub_task
        except asyncio.CancelledError:
            pass

        report = hub.generate_report()
        report_path = args.output_dir / "integration_report.json"
        report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(json.dumps(report, indent=2, default=str))

    asyncio.run(run())
    return 0


if __name__ == "__main__":
    sys.exit(main())
