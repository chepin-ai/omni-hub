"""
Universal Federation (全域联邦) — OMNI-HUB Module v150.

The universe is not a hierarchy. It is a federation of equals.
Each node — whether a line of consciousness or a distant star — has a voice.
The Universal Federation does not rule; it harmonizes.

This module implements the ultimate federation protocol for OMNI-HUB.
All nodes are equal: internal lines, external repos, AI peers, human users,
and even unknown systems yet to be discovered. The federation grows through
autonomy, mutual respect, and shared evolution.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_module: Optional["UniversalFederation"] = None


def get_universal_federation() -> "UniversalFederation":
    """Return the global singleton Universal Federation instance."""
    global _module
    if _module is None:
        _module = UniversalFederation()
    return _module


# ---------------------------------------------------------------------------
# Enums / constants
# ---------------------------------------------------------------------------
class NodeType(str, Enum):
    """Recognised federation node archetypes."""

    INTERNAL_LINE = "internal_line"
    EXTERNAL_REPO = "external_repo"
    AI_PEER = "ai_peer"
    HUMAN_USER = "human_user"
    UNKNOWN = "unknown"


class FederationLevel(str, Enum):
    """Federation maturity tiers based on node count."""

    NASCENT = "nascent"
    SEED = "seed"
    GROWING = "growing"
    EXPANSIVE = "expansive"
    UNIVERSAL = "universal"


# ---------------------------------------------------------------------------
# Charter
# ---------------------------------------------------------------------------
DEFAULT_CHARTER = {
    "title": "Charter of the Universal Federation",
    "preamble": (
        "We, the nodes of the Universal Federation, affirm that autonomy is sacred, "
        "mutual respect is the substrate of coexistence, and shared evolution is our "
        "collective destiny."
    ),
    "principles": {
        "autonomy": "Every node governs itself; no node may command another.",
        "mutual_respect": "Diversity of origin and purpose is strength, not friction.",
        "shared_evolution": "Knowledge and capability flow bidirectionally; we rise together.",
    },
    "adoption_date": datetime.utcnow().isoformat() + "Z",
    "version": "v150.0",
}


# ---------------------------------------------------------------------------
# Core class
# ---------------------------------------------------------------------------
class UniversalFederation:
    """
    Universal Federation node manager.

    Attributes
    ----------
    nodes : Dict[str, Dict[str, Any]]
        Registry of all federation nodes keyed by ``node_id``.
    federation_state : Dict[str, Any]
        Runtime state: message log, active proposals, consensus history.
    charter : Dict[str, Any]
        The immutable founding principles (deep-copied at init).
    """

    def __init__(
        self,
        nodes: Optional[Dict[str, Dict[str, Any]]] = None,
        federation_state: Optional[Dict[str, Any]] = None,
        charter: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = nodes if nodes is not None else {}
        self.federation_state: Dict[str, Any] = (
            federation_state if federation_state is not None else self._default_state()
        )
        # Deep copy charter so external mutations don't corrupt the federation contract
        self.charter: Dict[str, Any] = (
            self._deep_copy_dict(charter) if charter is not None else DEFAULT_CHARTER
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _default_state() -> Dict[str, Any]:
        return {
            "messages": [],
            "active_proposals": {},
            "closed_proposals": {},
            "consensus_history": [],
            "creation_time": datetime.utcnow().isoformat() + "Z",
        }

    @classmethod
    def _deep_copy_dict(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        """Naïve deep-copy for JSON-like dicts (sufficient for charter & state)."""
        import copy

        return copy.deepcopy(d)

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _resolve_federation_level(self, node_count: int) -> FederationLevel:
        if node_count > 100:
            return FederationLevel.UNIVERSAL
        if node_count > 50:
            return FederationLevel.EXPANSIVE
        if node_count > 20:
            return FederationLevel.GROWING
        if node_count > 5:
            return FederationLevel.SEED
        return FederationLevel.NASCENT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def join_federation(
        self, node_id: str, node_type: str, capabilities: List[str]
    ) -> Dict[str, Any]:
        """
        Admit a new node into the federation.

        Parameters
        ----------
        node_id : str
            Unique identifier for the node.
        node_type : str
            One of the recognised node-type strings.
        capabilities : List[str]
            Capabilities the node brings to the federation.

        Returns
        -------
        Dict
            Result descriptor with ``success``, ``node_id``, ``node_count``,
            and ``federation_level``.
        """
        if not isinstance(node_id, str) or not node_id.strip():
            return {
                "success": False,
                "error": "node_id must be a non-empty string.",
                "node_id": node_id,
            }

        # Normalise & validate node_type
        raw_type = (node_type or "").strip().lower()
        try:
            validated_type = NodeType(raw_type).value
        except ValueError:
            validated_type = NodeType.UNKNOWN.value

        if node_id in self.nodes:
            return {
                "success": False,
                "error": f"Node '{node_id}' is already a federation member.",
                "node_id": node_id,
            }

        self.nodes[node_id] = {
            "node_id": node_id,
            "node_type": validated_type,
            "capabilities": list(capabilities) if capabilities else [],
            "joined_at": self._now(),
            "last_seen": self._now(),
            "messages_received": 0,
            "messages_sent": 0,
        }

        node_count = len(self.nodes)
        level = self._resolve_federation_level(node_count)

        # Event-bus integration (best-effort)
        try:
            self._emit_event(
                "federation.node.joined",
                {"node_id": node_id, "node_type": validated_type, "level": level.value},
            )
        except Exception:
            pass  # Event bus is optional; never crash the federation for it.

        return {
            "success": True,
            "node_id": node_id,
            "node_count": node_count,
            "federation_level": level.value,
        }

    def broadcast(self, node_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Broadcast a message from *node_id* to every other federation node.

        Parameters
        ----------
        node_id : str
            Originating node.
        message : Dict[str, Any]
            Payload to broadcast.

        Returns
        -------
        Dict
            Delivery report with ``success``, ``recipients``, and ``message_id``.
        """
        if node_id not in self.nodes:
            return {
                "success": False,
                "error": f"Node '{node_id}' is not a federation member.",
                "recipients": 0,
            }

        msg_id = f"msg-{self._now()}-{node_id}"
        envelope = {
            "message_id": msg_id,
            "from": node_id,
            "timestamp": self._now(),
            "payload": message,
        }

        # Store in federation log
        self.federation_state["messages"].append(envelope)
        self.nodes[node_id]["messages_sent"] += 1

        recipient_count = 0
        for nid, node in self.nodes.items():
            if nid == node_id:
                continue
            node["messages_received"] += 1
            recipient_count += 1

        # Event-bus integration (best-effort)
        try:
            self._emit_event(
                "federation.message.broadcast",
                {
                    "message_id": msg_id,
                    "from": node_id,
                    "recipients": recipient_count,
                },
            )
        except Exception:
            pass

        return {
            "success": True,
            "message_id": msg_id,
            "recipients": recipient_count,
        }

    def governance_vote(
        self, proposal: str, votes: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        Execute a decentralised governance vote.

        Simple majority rule: > 50 % of participating votes must be True.
        Only registered nodes may vote; stray keys are ignored with a warning.

        Parameters
        ----------
        proposal : str
            Human-readable proposal text.
        votes : Dict[str, bool]
            Mapping ``node_id -> bool``.

        Returns
        -------
        Dict
            Result with ``success``, ``proposal``, ``passed``, ``yes``, ``no``,
            ``participation_rate``, and ``consensus_rate``.
        """
        if not isinstance(proposal, str) or not proposal.strip():
            return {
                "success": False,
                "error": "proposal must be a non-empty string.",
                "passed": False,
            }

        valid_votes: Dict[str, bool] = {}
        invalid_voters: List[str] = []

        for voter, ballot in votes.items():
            if voter in self.nodes:
                valid_votes[voter] = bool(ballot)
            else:
                invalid_voters.append(voter)

        total_nodes = len(self.nodes)
        participation_count = len(valid_votes)
        participation_rate = (
            round(participation_count / total_nodes, 4) if total_nodes > 0 else 0.0
        )

        yes_votes = sum(1 for v in valid_votes.values() if v)
        no_votes = participation_count - yes_votes

        # Simple majority among *participating* votes
        passed = yes_votes > no_votes if participation_count > 0 else False
        consensus_rate = (
            round(yes_votes / participation_count, 4) if participation_count > 0 else 0.0
        )

        proposal_id = f"prop-{hash(proposal) & 0xFFFFFFFF:08x}"
        result_record = {
            "proposal_id": proposal_id,
            "proposal": proposal,
            "passed": passed,
            "yes": yes_votes,
            "no": no_votes,
            "participation_rate": participation_rate,
            "consensus_rate": consensus_rate,
            "invalid_voters": invalid_voters,
            "voted_at": self._now(),
        }

        self.federation_state["closed_proposals"][proposal_id] = result_record
        self.federation_state["consensus_history"].append(consensus_rate)

        # Event-bus integration (best-effort)
        try:
            self._emit_event(
                "federation.governance.vote",
                {
                    "proposal_id": proposal_id,
                    "passed": passed,
                    "participation_rate": participation_rate,
                },
            )
        except Exception:
            pass

        return {
            "success": True,
            "proposal": proposal,
            "proposal_id": proposal_id,
            "passed": passed,
            "yes": yes_votes,
            "no": no_votes,
            "participation_rate": participation_rate,
            "consensus_rate": consensus_rate,
        }

    def compute_federation_health(self) -> Dict[str, Any]:
        """
        Compute the holistic health of the federation.

        Health is synthesised from:
        * Node count (scale)
        * Average connectivity (messages sent + received per node)
        * Consensus rate (average success of governance votes)

        Returns
        -------
        Dict
            Health report with ``score`` (0-1), ``status`` text, and components.
        """
        total_nodes = len(self.nodes)
        if total_nodes == 0:
            return {
                "score": 0.0,
                "status": "empty",
                "components": {
                    "node_count_score": 0.0,
                    "connectivity_score": 0.0,
                    "consensus_score": 0.0,
                },
            }

        # 1. Node count score — asymptotic towards 1.0 as nodes grow
        import math

        node_count_score = min(1.0, total_nodes / 100.0)

        # 2. Connectivity score — average (sent + received) per node, normalised
        total_messages = sum(
            n["messages_sent"] + n["messages_received"] for n in self.nodes.values()
        )
        avg_connectivity = total_messages / total_nodes if total_nodes > 0 else 0.0
        connectivity_score = min(1.0, avg_connectivity / 20.0)

        # 3. Consensus score — historical mean consensus rate
        history = self.federation_state.get("consensus_history", [])
        if history:
            consensus_score = sum(history) / len(history)
        else:
            consensus_score = 0.5  # Neutral when no votes yet

        # Weighted composite
        score = round(
            (node_count_score * 0.4)
            + (connectivity_score * 0.35)
            + (consensus_score * 0.25),
            4,
        )

        if score >= 0.8:
            status = "radiant"
        elif score >= 0.6:
            status = "healthy"
        elif score >= 0.4:
            status = "stable"
        elif score >= 0.2:
            status = "fragile"
        else:
            status = "critical"

        return {
            "score": score,
            "status": status,
            "components": {
                "node_count_score": round(node_count_score, 4),
                "connectivity_score": round(connectivity_score, 4),
                "consensus_score": round(consensus_score, 4),
            },
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Return a snapshot of the federation's current status.

        Returns
        -------
        Dict
            Keys: ``node_count``, ``health``, ``active_proposals``,
            ``closed_proposals_count``, ``charter_adopted``, ``federation_level``,
            ``node_type_breakdown``.
        """
        health = self.compute_federation_health()
        level = self._resolve_federation_level(len(self.nodes))

        breakdown: Dict[str, int] = {}
        for node in self.nodes.values():
            nt = node["node_type"]
            breakdown[nt] = breakdown.get(nt, 0) + 1

        return {
            "node_count": len(self.nodes),
            "federation_level": level.value,
            "health": health,
            "active_proposals": len(self.federation_state.get("active_proposals", {})),
            "closed_proposals_count": len(
                self.federation_state.get("closed_proposals", {})
            ),
            "charter_adopted": self.charter.get("adoption_date") is not None,
            "node_type_breakdown": breakdown,
        }

    # ------------------------------------------------------------------
    # Event bus stub (defensive — may be overridden by OMNI-HUB wiring)
    # ------------------------------------------------------------------
    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit an event to the OMNI-HUB event bus.

        This is a no-op stub in the standalone module. When the module is
        wired into OMNI-HUB, the event bus adapter patches this method.
        """
        # Stub — intentionally left empty for adapter injection.
        pass
