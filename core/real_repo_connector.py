"""
OMNI-HUB v152: Real Repo Connector (真实仓库连接器)
Establishes structured connection channels with real repositories.
Records metadata, activity, language, last update time. Computes connection health.
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Try to import event bus for integration
try:
    from core.event_bus import get_bus
    _EVENT_BUS_AVAILABLE = True
except Exception:
    _EVENT_BUS_AVAILABLE = False


@dataclass
class RepoConnection:
    """Represents a connection to a repository."""
    name: str
    metadata: Dict[str, Any]
    connected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    health: float = 1.0
    sync_count: int = 0
    last_sync: Optional[str] = None


class RealRepoConnector:
    """
    Real Repo Connector - establishes structured connections to actual repositories.
    Loads repo data from alliance_repos.json, connects to non-line alliance
    and external repos.
    """

    REQUIRED_NONLINE_REPOS: List[str] = [
        "vci-inbox", "ci-worker-01", "qlv-lib", "lgt-worker-01", "ci-yard",
        "vci-control", "qfos-autonomous-engine", "grand-synthesis",
        "prima-50-research", "ci-worker-02", "vci-library", "vci-playground",
        "vci-root", "vci-logs", "vci-code", "vci-bus",
    ]

    REQUIRED_EXTERNAL_REPOS: List[str] = [
        "langchain-ai/langchain", "microsoft/semantic-kernel",
        "openai/openai-python", "huggingface/transformers", "pytorch/pytorch",
    ]

    def __init__(self, repos_file: Optional[str] = None):
        """
        Initialize the Real Repo Connector.

        Args:
            repos_file: Path to alliance_repos.json. If None, uses default path.
        """
        self._connections: Dict[str, RepoConnection] = {}
        self._repo_data: Dict[str, Dict[str, Any]] = {}
        self._connect_count: int = 0
        self._last_connect: Optional[str] = None

        if repos_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            repos_file = os.path.join(base_dir, "data", "alliance_repos.json")

        self._load_repos(repos_file)

    def _load_repos(self, repos_file: str) -> None:
        """Load repository metadata from JSON file."""
        try:
            if os.path.exists(repos_file):
                with open(repos_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for category, repos in data.items():
                    for repo_name, meta in repos.items():
                        self._repo_data[repo_name] = dict(meta)
                        self._repo_data[repo_name]["category"] = category
            else:
                self._repo_data = {}
                self._emit_event("repo_connector.warning", {
                    "message": f"Repos file not found: {repos_file}",
                })
        except Exception as e:
            self._repo_data = {}
            self._emit_event("repo_connector.error", {
                "message": f"Failed to load repos file: {e}",
            })

    def _emit_event(self, topic: str, payload: Dict[str, Any]) -> None:
        """Emit an event to the event bus if available."""
        if _EVENT_BUS_AVAILABLE:
            try:
                bus = get_bus()
                bus.publish_simple(topic, payload, source="real_repo_connector")
            except Exception:
                pass

    def _compute_health(self, updated_str: Optional[str]) -> float:
        """
        Compute connection health based on last update recency.

        Health formula:
        - If updated today: health = 1.0
        - If updated within 7 days: health = 0.8
        - If updated within 30 days: health = 0.5
        - Otherwise: health = 0.2
        """
        if updated_str is None:
            return 1.0

        try:
            updated_date = datetime.strptime(updated_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return 1.0

        today = date.today()
        try:
            days_diff = (today - updated_date).days
        except Exception:
            return 1.0

        if days_diff <= 0:
            return 1.0
        elif days_diff <= 1:
            return 1.0
        elif days_diff <= 7:
            return 0.8
        elif days_diff <= 30:
            return 0.5
        else:
            return 0.2

    def connect(self, repo_name: str) -> Dict[str, Any]:
        """
        Establish a connection to a real repository.

        Args:
            repo_name: Name of the repository to connect to.

        Returns:
            Dict with connection result and metadata.
        """
        if not repo_name or not isinstance(repo_name, str):
            return {"success": False, "error": "Invalid repo name"}

        if repo_name in self._connections:
            conn = self._connections[repo_name]
            return {
                "success": True,
                "repo_name": repo_name,
                "message": "Already connected",
                "metadata": conn.metadata,
                "health": conn.health,
                "connected_at": conn.connected_at,
            }

        meta = self._repo_data.get(repo_name)
        if meta is None:
            meta = {"role": "unknown", "desc": "Unknown repository", "lang": None}

        updated_str = meta.get("updated")
        health = self._compute_health(updated_str)

        connection = RepoConnection(
            name=repo_name,
            metadata=dict(meta),
            health=health,
        )

        self._connections[repo_name] = connection
        self._connect_count += 1
        self._last_connect = datetime.now().isoformat()

        self._emit_event("repo_connector.connected", {
            "repo_name": repo_name,
            "health": health,
            "category": meta.get("category", "unknown"),
        })

        return {
            "success": True,
            "repo_name": repo_name,
            "metadata": connection.metadata,
            "health": health,
            "connected_at": connection.connected_at,
        }

    def batch_connect(self, repo_names: List[str]) -> Dict[str, Any]:
        """
        Connect to multiple repositories at once.

        Args:
            repo_names: List of repository names to connect to.

        Returns:
            Dict with batch connection results.
        """
        if not isinstance(repo_names, list):
            return {
                "success": False,
                "error": "repo_names must be a list",
                "connected": [],
                "failed": [],
            }

        connected = []
        failed = []

        for repo_name in repo_names:
            result = self.connect(repo_name)
            if result.get("success"):
                connected.append(repo_name)
            else:
                failed.append({
                    "name": repo_name,
                    "error": result.get("error", "Unknown error"),
                })

        self._emit_event("repo_connector.batch_connected", {
            "count": len(connected),
            "repos": connected,
        })

        return {
            "success": len(failed) == 0,
            "connected_count": len(connected),
            "failed_count": len(failed),
            "connected": connected,
            "failed": failed,
        }

    def sync_health(self, repo_name: str) -> Dict[str, Any]:
        """
        Synchronize and recompute connection health for a repository.

        Args:
            repo_name: Name of the repository to sync health for.

        Returns:
            Dict with sync result and updated health.
        """
        if not repo_name or not isinstance(repo_name, str):
            return {"success": False, "error": "Invalid repo name"}

        if repo_name not in self._connections:
            return {
                "success": False,
                "error": f"Repository '{repo_name}' not connected",
            }

        conn = self._connections[repo_name]
        meta = self._repo_data.get(repo_name, conn.metadata)

        updated_str = meta.get("updated")
        new_health = self._compute_health(updated_str)

        old_health = conn.health
        conn.health = new_health
        conn.sync_count += 1
        conn.last_sync = datetime.now().isoformat()

        self._emit_event("repo_connector.health_synced", {
            "repo_name": repo_name,
            "old_health": old_health,
            "new_health": new_health,
        })

        return {
            "success": True,
            "repo_name": repo_name,
            "old_health": old_health,
            "new_health": new_health,
            "sync_count": conn.sync_count,
            "last_sync": conn.last_sync,
        }

    def get_active_connections(self) -> List[Dict[str, Any]]:
        """
        Return all active connections with health scores.

        Returns:
            List of connection dicts with metadata and health.
        """
        result = []
        for name, conn in self._connections.items():
            result.append({
                "name": conn.name,
                "metadata": conn.metadata,
                "health": conn.health,
                "connected_at": conn.connected_at,
                "sync_count": conn.sync_count,
                "last_sync": conn.last_sync,
            })
        result.sort(key=lambda x: x["health"], reverse=True)
        return result

    def get_status(self) -> Dict[str, Any]:
        """
        Return connector status summary.

        Returns:
            Dict with connection count, avg health, strongest/weakest.
        """
        connections = self.get_active_connections()
        count = len(connections)

        if count == 0:
            return {
                "connection_count": 0,
                "avg_health": 0.0,
                "strongest_connection": None,
                "weakest_connection": None,
                "total_connects": self._connect_count,
                "last_connect": self._last_connect,
            }

        avg_health = sum(c["health"] for c in connections) / count
        strongest = connections[0]
        weakest = connections[-1]

        return {
            "connection_count": count,
            "avg_health": round(avg_health, 4),
            "strongest_connection": {
                "name": strongest["name"],
                "health": strongest["health"],
            },
            "weakest_connection": {
                "name": weakest["name"],
                "health": weakest["health"],
            },
            "total_connects": self._connect_count,
            "last_connect": self._last_connect,
        }

    def connect_all_required(self) -> Dict[str, Any]:
        """
        Connect to all required repositories (non-line alliance + external).

        Returns:
            Batch connection result.
        """
        all_required = self.REQUIRED_NONLINE_REPOS + self.REQUIRED_EXTERNAL_REPOS
        return self.batch_connect(all_required)


# Global singleton instance
_MODULE: Optional[RealRepoConnector] = None


def get_real_repo_connector() -> RealRepoConnector:
    """Get the global RealRepoConnector singleton instance."""
    global _MODULE
    if _MODULE is None:
        _MODULE = RealRepoConnector()
    return _MODULE


def reset_real_repo_connector() -> None:
    """Reset the global singleton (for testing)."""
    global _MODULE
    _MODULE = RealRepoConnector()
