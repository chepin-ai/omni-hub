"""
OMNI-HUB v132: Consensus Engine (共识引擎)
Byzantine fault-tolerant consensus for distributed decisions.
"""

import hashlib
import time
from typing import Any, Dict, List, Optional

# OMNI-HUB event bus integration
try:
    from core.event_bus import bus, Topics
    _HAS_BUS = True
except ImportError:
    bus = None
    Topics = None
    _HAS_BUS = False


class ConsensusEngine:
    """Byzantine fault-tolerant consensus engine for distributed proposals."""

    def __init__(self) -> None:
        self._proposals: Dict[str, Dict[str, Any]] = {}
        self._votes: Dict[str, Dict[str, bool]] = {}
        self._resolved: Dict[str, Dict[str, Any]] = {}
        self._proposal_count: int = 0
        self._resolved_count: int = 0

    def propose(self, topic: str, value: Any) -> str:
        """Create a new proposal; return its unique proposal_id (SHA-256 hash)."""
        try:
            timestamp = str(time.time_ns())
            raw = f"{topic}:{value}:{timestamp}"
            proposal_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()

            self._proposals[proposal_id] = {
                "topic": topic,
                "value": value,
                "timestamp": timestamp,
                "status": "pending",
            }
            self._votes[proposal_id] = {}
            self._proposal_count += 1

            if _HAS_BUS and bus is not None:
                try:
                    bus.publish_simple(
                        Topics.STATE_CHANGE,
                        {
                            "source": "consensus_engine",
                            "event": "proposal_created",
                            "proposal_id": proposal_id,
                            "topic": topic,
                        },
                    )
                except Exception:
                    pass  # event bus best-effort

            return proposal_id
        except Exception as exc:
            raise RuntimeError(f"Failed to create proposal: {exc}") from exc

    def vote(self, proposal_id: str, node_id: str, approve: bool) -> Dict[str, Any]:
        """Cast a vote for a proposal; return current vote tally."""
        try:
            if proposal_id not in self._proposals:
                raise KeyError(f"Proposal not found: {proposal_id}")
            if proposal_id in self._resolved:
                raise RuntimeError(f"Proposal already resolved: {proposal_id}")

            self._votes[proposal_id][node_id] = approve

            tally = self._compute_tally(proposal_id)

            if _HAS_BUS and bus is not None:
                try:
                    bus.publish_simple(
                        Topics.STATE_CHANGE,
                        {
                            "source": "consensus_engine",
                            "event": "vote_cast",
                            "proposal_id": proposal_id,
                            "node_id": node_id,
                            "approve": approve,
                        },
                    )
                except Exception:
                    pass

            return tally
        except Exception:
            raise

    def _compute_tally(self, proposal_id: str) -> Dict[str, Any]:
        """Internal helper: compute approve/reject counts and ratios."""
        votes = self._votes.get(proposal_id, {})
        total = len(votes)
        approvals = sum(1 for v in votes.values() if v)
        rejections = total - approvals
        ratio = approvals / total if total > 0 else 0.0
        return {
            "proposal_id": proposal_id,
            "total_votes": total,
            "approvals": approvals,
            "rejections": rejections,
            "approval_ratio": round(ratio, 4),
        }

    def resolve(self, proposal_id: str) -> Dict[str, Any]:
        """Check if >2/3 of voters approve; return final consensus status."""
        try:
            if proposal_id not in self._proposals:
                raise KeyError(f"Proposal not found: {proposal_id}")
            if proposal_id in self._resolved:
                return self._resolved[proposal_id]

            tally = self._compute_tally(proposal_id)
            total = tally["total_votes"]
            approvals = tally["approvals"]

            if total == 0:
                consensus_reached = False
                result = "pending"
            else:
                consensus_reached = (approvals / total) > (2 / 3)
                result = "approved" if consensus_reached else "rejected"

            status = {
                "proposal_id": proposal_id,
                "topic": self._proposals[proposal_id]["topic"],
                "value": self._proposals[proposal_id]["value"],
                "total_votes": total,
                "approvals": approvals,
                "rejections": tally["rejections"],
                "approval_ratio": tally["approval_ratio"],
                "consensus_reached": consensus_reached,
                "result": result,
                "status": "resolved",
            }

            if result != "pending":
                self._resolved[proposal_id] = status
                self._proposals[proposal_id]["status"] = "resolved"
                self._resolved_count += 1

                if _HAS_BUS and bus is not None:
                    try:
                        bus.publish_simple(
                            Topics.STATE_CHANGE,
                            {
                                "source": "consensus_engine",
                                "event": "proposal_resolved",
                                "proposal_id": proposal_id,
                                "result": result,
                            },
                        )
                    except Exception:
                        pass

            return status
        except Exception:
            raise

    def get_status(self) -> Dict[str, Any]:
        """Return engine status: proposal count, resolved count, pending count."""
        return {
            "proposal_count": self._proposal_count,
            "resolved_count": self._resolved_count,
            "pending_count": self._proposal_count - self._resolved_count,
            "proposal_ids": list(self._proposals.keys()),
            "resolved_ids": list(self._resolved.keys()),
        }

    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve proposal details by id."""
        return self._proposals.get(proposal_id)

    def get_votes(self, proposal_id: str) -> Dict[str, bool]:
        """Retrieve raw votes map for a proposal."""
        return self._votes.get(proposal_id, {}).copy()

    def list_proposals(self) -> List[str]:
        """Return all proposal ids."""
        return list(self._proposals.keys())


# Global singleton -----------------------------------------------------------------
_module: Optional[ConsensusEngine] = None


def get_consensus_engine() -> ConsensusEngine:
    """Lazy-loading global singleton for ConsensusEngine."""
    global _module
    if _module is None:
        _module = ConsensusEngine()
    return _module


def _reset_singleton() -> None:
    """Reset the singleton instance (intended for tests only)."""
    global _module
    _module = None
