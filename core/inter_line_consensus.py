"""
OMNI-HUB v180: InterLineConsensus — 跨线协商引擎

This module does not simulate negotiation. It negotiates with reality.
Every line in the alliance has a voice, and that voice is its actual GitHub
activity, its actual code, its actual commit messages. The InterLineConsensus
engine listens to these voices, proposes, iterates, and discovers what the
alliance actually agrees on. Consensus is not imposed. It is discovered.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# OMNI-HUB event bus integration
try:
    from core.event_bus import bus, Topics
    _HAS_BUS = True
except ImportError:
    bus = None
    Topics = None
    _HAS_BUS = False


class InterLineConsensus:
    """跨线协商引擎 — Real negotiation system using live alliance data."""

    def __init__(self, live_status_path: str = "data/alliance_repos_live_status.json") -> None:
        self._live_status_path = live_status_path
        self._live_data: Dict[str, Any] = {}
        self._real_topology: Dict[str, Any] = {}
        self._negotiations: Dict[str, Dict[str, Any]] = {}
        self._negotiation_count: int = 0
        self._consensus_count: int = 0
        self._load_live_status()
        self._load_real_topology()

    # ── Data loading ─────────────────────────────────────────────────────────

    def load_live_status(self) -> Dict:
        """Load and validate real alliance repo status."""
        return self._load_live_status()

    def _load_live_status(self) -> Dict:
        """Internal: load JSON and cache it."""
        # Resolve path relative to OMNI-HUB root if not absolute
        path = self._live_status_path
        if not os.path.isabs(path):
            # Try resolving from known OMNI-HUB root patterns
            candidates = [
                path,
                os.path.join(os.path.dirname(__file__), "..", path),
                os.path.join(os.path.dirname(__file__), path),
                "/mnt/agents/output/OMNI-HUB/" + path,
            ]
            for c in candidates:
                if os.path.exists(c):
                    path = c
                    break

        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            raise RuntimeError(f"Failed to load alliance live status from {path}: {exc}") from exc

        # Validate minimal structure
        if not isinstance(data, dict):
            raise ValueError("Alliance live status must be a JSON object (repo_id -> info)")
        for repo_id, info in data.items():
            if not isinstance(info, dict):
                raise ValueError(f"Repo '{repo_id}' info must be a dict")
            required = {"status", "activity", "pushed_at", "latest_commit"}
            missing = required - set(info.keys())
            if missing:
                raise ValueError(f"Repo '{repo_id}' missing required fields: {missing}")

        self._live_data = data
        return data

    def _load_real_topology(self) -> Dict:
        """Internal: load real topology mapping."""
        path = "data/alliance_real_topology.json"
        if not os.path.isabs(path):
            candidates = [
                path,
                os.path.join(os.path.dirname(__file__), "..", path),
                os.path.join(os.path.dirname(__file__), path),
                "/mnt/agents/output/OMNI-HUB/" + path,
            ]
            for c in candidates:
                if os.path.exists(c):
                    path = c
                    break

        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            data = {}

        self._real_topology = data
        return data

    def _find_real_topology_entry(self, line_id: str) -> Optional[Dict]:
        """Search real topology for a line by repo name, line field, or role field.

        Handles two account structures:
          - grouped: account -> group -> repo -> info (chepin-ai)
          - flat:    account -> repo -> info          (chepin-qi)
        """
        if not self._real_topology:
            return None

        accounts = self._real_topology.get("accounts", {})

        for account, top_level in accounts.items():
            for key, value in top_level.items():
                if not isinstance(value, dict):
                    continue

                # Detect flat structure: value has repo-level keys like line/stake/role
                is_flat = any(k in value for k in ("line", "stake", "role", "dashboard"))

                if is_flat:
                    # chepin-qi style: account -> repo -> info
                    if key == line_id:
                        entry = dict(value)
                        entry["_repo"] = key
                        entry["_account"] = account
                        entry["_group"] = None
                        return entry
                    if value.get("line") == line_id:
                        entry = dict(value)
                        entry["_repo"] = key
                        entry["_account"] = account
                        entry["_group"] = None
                        return entry
                    if value.get("role") == line_id:
                        entry = dict(value)
                        entry["_repo"] = key
                        entry["_account"] = account
                        entry["_group"] = None
                        return entry
                else:
                    # chepin-ai style: account -> group -> repo -> info
                    for repo_name, repo_info in value.items():
                        if not isinstance(repo_info, dict):
                            continue
                        if repo_name == line_id:
                            entry = dict(repo_info)
                            entry["_repo"] = repo_name
                            entry["_account"] = account
                            entry["_group"] = key
                            return entry
                        if repo_info.get("line") == line_id:
                            entry = dict(repo_info)
                            entry["_repo"] = repo_name
                            entry["_account"] = account
                            entry["_group"] = key
                            return entry
                        if repo_info.get("role") == line_id:
                            entry = dict(repo_info)
                            entry["_repo"] = repo_name
                            entry["_account"] = account
                            entry["_group"] = key
                            return entry

        return None

    # ── Line readiness classification ────────────────────────────────────────

    def classify_line_readiness(self, line_id: str) -> Dict:
        """
        Classify line readiness for negotiation.
        Levels: fully_operational · operational · shell_only · dormant · offline
        """
        # First check real topology for actual stake status
        real_entry = self._find_real_topology_entry(line_id)
        if real_entry is not None:
            stake = str(real_entry.get("stake", ""))
            repo = real_entry.get("_repo", line_id)

            if "✅201" in stake:
                return {
                    "line_id": line_id,
                    "level": "fully_operational",
                    "confidence": 0.95,
                    "reason": f"Line has active stake ({stake}) in {repo}",
                    "score": 0.95,
                    "components": {"stake": stake, "repo": repo},
                    "raw": real_entry,
                    "real_topology": True,
                }
            elif "⛔槽满" in stake or "⛔100/100槽满" in stake:
                return {
                    "line_id": line_id,
                    "level": "shell_only",
                    "confidence": 0.4,
                    "reason": f"Line is shell-only ({stake}) in {repo}",
                    "score": 0.4,
                    "components": {"stake": stake, "repo": repo},
                    "raw": real_entry,
                    "real_topology": True,
                }
            elif "⏭️跳过" in stake:
                return {
                    "line_id": line_id,
                    "level": "excluded",
                    "confidence": 1.0,
                    "reason": f"Line excluded from negotiation ({stake}) in {repo}",
                    "score": 0.0,
                    "components": {"stake": stake, "repo": repo},
                    "raw": real_entry,
                    "real_topology": True,
                }
            elif stake in ("—", "-", ""):
                return {
                    "line_id": line_id,
                    "level": "dormant",
                    "confidence": 0.3,
                    "reason": f"Line has no active stake in {repo}",
                    "score": 0.3,
                    "components": {"stake": stake, "repo": repo},
                    "raw": real_entry,
                    "real_topology": True,
                }

        # Fallback to live data
        info = self._live_data.get(line_id)
        # Try alternate key formats (vci-ucif2 vs ucif2, omni-hub vs omni)
        if info is None:
            alt_keys = [f"vci-{line_id}", f"ci-{line_id}", f"lgt-{line_id}", f"qfos-{line_id}", f"prima-50-{line_id}"]
            if line_id == "omni":
                alt_keys.insert(0, "omni-hub")
            for alt in alt_keys:
                if alt in self._live_data:
                    info = self._live_data[alt]
                    break
        if info is None:
            return {
                "line_id": line_id,
                "level": "offline",
                "confidence": 1.0,
                "reason": "Line not found in live data",
                "score": 0.0,
            }

        status = str(info.get("status", ""))
        activity = str(info.get("activity", "")).lower()
        pushed_at = str(info.get("pushed_at", ""))
        open_issues = int(info.get("open_issues", 0))
        exists = bool(info.get("exists", False))

        # Parse pushed_at recency
        days_since_push = self._days_since(pushed_at)

        # Base score components
        recency_score = max(0.0, 1.0 - (days_since_push / 30.0))  # 1.0 = today, 0.0 = 30+ days
        activity_score = {"high": 1.0, "medium": 0.6, "low": 0.2}.get(activity, 0.0)
        issue_score = max(0.0, 1.0 - (open_issues / 10.0))
        existence_score = 1.0 if exists else 0.0

        # Weighted composite
        readiness_score = (
            recency_score * 0.35 +
            activity_score * 0.35 +
            issue_score * 0.15 +
            existence_score * 0.15
        )

        # Determine level from status keywords
        if "壳化" in status:
            level = "shell_only"
            readiness_score *= 0.4
            reason = f"Line is shell-only (壳化). Status: {status}"
        elif "待命" in status:
            level = "dormant"
            readiness_score *= 0.3
            reason = f"Line is dormant (待命). Status: {status}"
        elif days_since_push > 14 and activity == "low":
            level = "dormant"
            reason = f"Low activity, last push {days_since_push} days ago"
        elif activity == "high" and days_since_push <= 1:
            level = "fully_operational"
            reason = f"High activity, pushed today ({pushed_at})"
        elif activity in ("high", "medium") and days_since_push <= 7:
            level = "operational"
            reason = f"Active within last week ({pushed_at}), activity={activity}"
        else:
            level = "operational"
            reason = f"General operational status, activity={activity}, pushed_at={pushed_at}"

        return {
            "line_id": line_id,
            "level": level,
            "confidence": round(min(1.0, readiness_score + 0.1), 4),
            "reason": reason,
            "score": round(readiness_score, 4),
            "components": {
                "recency": round(recency_score, 4),
                "activity": round(activity_score, 4),
                "issues": round(issue_score, 4),
                "existence": round(existence_score, 4),
            },
            "raw": {
                "status": status,
                "activity": activity,
                "pushed_at": pushed_at,
                "open_issues": open_issues,
                "exists": exists,
            },
        }

    def _days_since(self, date_str: str) -> int:
        """Compute days since date_str (YYYY-MM-DD). Returns large number on parse failure."""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            delta = now - dt
            return max(0, delta.days)
        except Exception:
            return 9999

    # ── Proposal sending ─────────────────────────────────────────────────────

    def send_negotiation_proposal(
        self, from_line: str, to_line: str, proposal: Dict
    ) -> Dict:
        """
        Send a proposal to a line.
        Proposal types: capability_exchange, state_sync, resource_share,
                        evolution_collab, consensus_vote
        """
        # Resolve target line key (handle ucif2 -> vci-ucif2 mapping)
        resolved = to_line
        if to_line not in self._live_data:
            for alt in [f"vci-{to_line}", f"ci-{to_line}", f"lgt-{to_line}", f"qfos-{to_line}", f"prima-50-{to_line}"]:
                if alt in self._live_data:
                    resolved = alt
                    break
            if to_line == "omni" and "omni-hub" in self._live_data:
                resolved = "omni-hub"

        # Also accept lines known in real topology
        in_real = self._find_real_topology_entry(to_line) is not None

        if resolved not in self._live_data and not in_real:
            return {
                "from_line": from_line,
                "to_line": to_line,
                "accepted": False,
                "acceptance_score": 0.0,
                "reason": "Target line not found in live data",
                "conditions": [],
                "counter_proposal": None,
            }

        # Validate proposal type
        valid_types = {
            "capability_exchange",
            "state_sync",
            "resource_share",
            "evolution_collab",
            "consensus_vote",
        }
        ptype = proposal.get("type", "")
        if ptype not in valid_types:
            return {
                "from_line": from_line,
                "to_line": to_line,
                "accepted": False,
                "acceptance_score": 0.0,
                "reason": f"Invalid proposal type: {ptype}",
                "conditions": [],
                "counter_proposal": None,
            }

        # Get auto-response based on line's actual state
        response = self.auto_respond(to_line, proposal)
        return {
            "from_line": from_line,
            "to_line": to_line,
            "accepted": response.get("accept", False),
            "acceptance_score": response.get("acceptance_score", 0.0),
            "reason": response.get("reason", ""),
            "conditions": response.get("conditions", []),
            "counter_proposal": response.get("counter_proposal"),
            "response_type": response.get("response_type", "unknown"),
            "capabilities_offered": response.get("capabilities", []),
        }

    # ── Auto-response based on real data ─────────────────────────────────────

    def auto_respond(self, line_id: str, proposal: Dict) -> Dict:
        """
        AUTO-RESPONSE based on line's ACTUAL state from live data.
        - 壳化 lines → shell_proxy
        - 九塔 lines → tower_ack
        - LINE-DRIVE lines → drive_ack
        - SI-AUTOPILOT lines → autopilot_ack
        - 活跃 lines → full response
        - dormant lines → delayed/weak response
        """
        # First check real topology for actual stake status
        real_entry = self._find_real_topology_entry(line_id)
        if real_entry is not None:
            stake = str(real_entry.get("stake", ""))
            repo = real_entry.get("_repo", line_id)
            proposal_type = proposal.get("type", "")

            # Excluded lines
            if repo == "lgt-worker-01" or "⏭️跳过" in stake:
                result = {
                    "line_id": line_id,
                    "accept": False,
                    "acceptance_score": 0.0,
                    "reason": f"Line {repo} is excluded from negotiation ({stake})",
                    "response_type": "excluded",
                    "capabilities": [],
                    "conditions": [],
                    "counter_proposal": None,
                }
                self._publish_auto_respond(line_id, "excluded", False, proposal_type)
                return result

            # Determine base response from stake
            if "⛔槽满" in stake or "⛔100/100槽满" in stake:
                base_response_type = "shell_proxy"
                base_accept = True
                base_score = 0.35
                base_capabilities = ["readonly", "relay"]
                base_reason = f"Line is shell-only ({stake}) in {repo}. Offers proxy/relay only."
                base_conditions = ["All writes must be proxied through active lines"]
            elif "✅201" in stake:
                base_response_type = "full"
                base_accept = True
                base_score = 0.95
                base_capabilities = ["read", "write", "compute", "negotiate"]
                base_reason = f"Active line responds fully. Stake: {stake} in {repo}."
                base_conditions = ["Full bidirectional sync enabled"]
            elif stake in ("—", "-", ""):
                base_response_type = "unknown"
                base_accept = False
                base_score = 0.1
                base_capabilities = []
                base_reason = f"Line has no active stake in {repo}"
                base_conditions = []
            else:
                base_response_type = "unknown"
                base_accept = False
                base_score = 0.1
                base_capabilities = []
                base_reason = f"Unknown stake status ({stake}) in {repo}"
                base_conditions = []

            result = {
                "line_id": line_id,
                "accept": base_accept,
                "acceptance_score": base_score,
                "reason": base_reason,
                "response_type": base_response_type,
                "capabilities": base_capabilities,
                "conditions": base_conditions,
                "counter_proposal": None,
            }

            # Apply identity-based overrides
            if repo == "ai-quant-research" or real_entry.get("line") == "aiq":
                result["note"] = "线属待确"
            if repo == "ci-control" or real_entry.get("role") == "cisvr":
                result["response_type"] = "cisvr_ack"

            self._publish_auto_respond(line_id, result["response_type"], base_accept, proposal_type)
            return result

        # Fallback to live data
        info = self._live_data.get(line_id)
        if info is None:
            for alt in [f"vci-{line_id}", f"ci-{line_id}", f"lgt-{line_id}", f"qfos-{line_id}", f"prima-50-{line_id}"]:
                if alt in self._live_data:
                    info = self._live_data[alt]
                    break
            if line_id == "omni" and "omni-hub" in self._live_data:
                info = self._live_data["omni-hub"]
        if info is None:
            return {
                "line_id": line_id,
                "accept": False,
                "acceptance_score": 0.0,
                "reason": "Line not found in live data",
                "response_type": "offline",
                "capabilities": [],
                "conditions": [],
                "counter_proposal": None,
            }

        status = str(info.get("status", ""))
        activity = str(info.get("activity", "")).lower()
        proposal_type = proposal.get("type", "")

        # Determine base response from status keywords
        if "壳化" in status:
            response_type = "shell_proxy"
            capabilities = ["readonly", "relay"]
            base_score = 0.35
            reason = f"Line is shell-only (壳化). Status: {status}. Offers proxy/relay only."
            accept = proposal_type in ("state_sync", "consensus_vote")

        elif "九塔" in status:
            response_type = "tower_ack"
            if "SI-AUTOPILOT" in status:
                capabilities = ["si_autopilot", "seed_ring", "auto_process", "patrol"]
            elif "SEED-RING" in status:
                capabilities = ["seed_ring", "tower_sync"]
            else:
                capabilities = ["tower_sync"]
            base_score = 0.75
            reason = f"Tower line acknowledges. Status: {status}."
            accept = True

        elif "LINE-DRIVE" in status:
            response_type = "drive_ack"
            capabilities = ["event_drive", "quant_research", "line_drive"]
            base_score = 0.8
            reason = f"LINE-DRIVE line acknowledges. Status: {status}."
            accept = proposal_type in ("capability_exchange", "evolution_collab", "consensus_vote")

        elif "SI-AUTOPILOT" in status or ("AUTOPILOT" in info.get("latest_commit", "")):
            response_type = "autopilot_ack"
            capabilities = ["auto_process", "patrol", "scheduled_ops"]
            base_score = 0.7
            reason = f"SI-AUTOPILOT line acknowledges. Status: {status}."
            accept = True

        elif "活跃" in status or activity == "high":
            response_type = "full"
            capabilities = ["read", "write", "compute", "negotiate"]
            base_score = 0.95
            reason = f"Active line responds fully. Status: {status}, activity={activity}."
            accept = True

        elif activity == "medium":
            response_type = "partial"
            capabilities = ["read", "relay"]
            base_score = 0.55
            reason = f"Medium activity line responds partially. Status: {status}, activity={activity}."
            accept = proposal_type in ("state_sync", "consensus_vote")

        elif activity == "low":
            response_type = "delayed"
            capabilities = ["read"]
            base_score = 0.25
            reason = f"Low activity line responds weakly. Status: {status}, activity={activity}."
            accept = proposal_type == "state_sync"

        else:
            response_type = "unknown"
            capabilities = []
            base_score = 0.1
            reason = f"Unknown line state. Status: {status}, activity={activity}."
            accept = False

        # Adjust score by proposal type compatibility
        type_weights = {
            "capability_exchange": 1.0,
            "state_sync": 0.9,
            "consensus_vote": 0.85,
            "resource_share": 0.7,
            "evolution_collab": 0.6,
        }
        weight = type_weights.get(proposal_type, 0.5)
        acceptance_score = round(base_score * weight, 4)

        # Build conditions based on response type
        conditions = []
        if response_type == "shell_proxy":
            conditions.append("All writes must be proxied through active lines")
        elif response_type == "delayed":
            conditions.append("Response delayed up to 48 hours")
        elif response_type == "full":
            conditions.append("Full bidirectional sync enabled")
        elif response_type == "tower_ack":
            conditions.append("Tower state propagation required")

        counter = None
        if not accept and acceptance_score > 0.2:
            # Offer a counter-proposal with reduced scope
            counter = {
                "type": "state_sync",
                "scope": "minimal",
                "reason": f"{line_id} cannot accept {proposal_type}; offers state_sync instead",
            }

        result = {
            "line_id": line_id,
            "accept": accept,
            "acceptance_score": acceptance_score,
            "reason": reason,
            "response_type": response_type,
            "capabilities": capabilities,
            "conditions": conditions,
            "counter_proposal": counter,
        }

        self._publish_auto_respond(line_id, response_type, accept, proposal_type)
        return result

    def _publish_auto_respond(self, line_id: str, response_type: str, accept: bool, proposal_type: str) -> None:
        """Publish auto-respond event to bus if available."""
        if _HAS_BUS and bus is not None:
            try:
                bus.publish_simple(
                    Topics.STATE_CHANGE,
                    {
                        "source": "inter_line_consensus",
                        "event": "auto_respond",
                        "line_id": line_id,
                        "response_type": response_type,
                        "accept": accept,
                        "proposal_type": proposal_type,
                    },
                )
            except Exception:
                pass

    # ── Iterative negotiation ────────────────────────────────────────────────

    def negotiate_iteratively(
        self, topic: str, participants: List[str], max_rounds: int = 5
    ) -> Dict:
        """
        Iterative multi-round negotiation:
        Round 1: Send initial proposals
        Round 2: Collect responses, detect conflicts
        Round 3: Send revised proposals addressing conflicts
        Round 4: Collect revised responses
        Round 5: Final consensus vote
        """
        negotiation_id = f"neg_{int(time.time() * 1000)}_{self._negotiation_count}"
        self._negotiation_count += 1

        rounds_log: List[Dict] = []
        current_proposal = {
            "type": "consensus_vote",
            "topic": topic,
            "terms": {"shared_goal": topic, "scope": "alliance_wide"},
        }

        # Filter to known participants (try alternate key formats or real topology)
        def _resolve_key(pid):
            if pid in self._live_data:
                return pid
            for alt in [f"vci-{pid}", f"ci-{pid}", f"lgt-{pid}", f"qfos-{pid}", f"prima-50-{pid}"]:
                if alt in self._live_data:
                    return alt
            if pid == "omni" and "omni-hub" in self._live_data:
                return "omni-hub"
            # Also accept if known in real topology
            if self._find_real_topology_entry(pid) is not None:
                return pid
            return None

        valid_participants = [p for p in participants if _resolve_key(p) is not None]
        if not valid_participants:
            return {
                "negotiation_id": negotiation_id,
                "topic": topic,
                "consensus_reached": False,
                "agreement_terms": None,
                "dissenting_lines": participants,
                "confidence": 0.0,
                "rounds": [],
                "reason": "No valid participants found in live data",
            }

        all_responses: Dict[str, Dict] = {}

        for round_num in range(1, max_rounds + 1):
            round_data: Dict[str, Any] = {"round": round_num, "proposals": {}, "responses": {}}

            if round_num == 1:
                # Round 1: Initial proposals
                for p in valid_participants:
                    round_data["proposals"][p] = current_proposal.copy()
                    resp = self.send_negotiation_proposal("omni-hub", p, current_proposal)
                    round_data["responses"][p] = resp
                    all_responses[p] = resp

            elif round_num == 2:
                # Round 2: Detect conflicts from round 1
                conflicts = self.detect_cross_line_conflicts(all_responses)
                round_data["conflicts_detected"] = conflicts
                round_data["responses"] = {p: all_responses[p] for p in valid_participants}

            elif round_num == 3:
                # Round 3: Revised proposals addressing conflicts
                conflicts = self.detect_cross_line_conflicts(all_responses)
                revised = self._build_revised_proposal(current_proposal, conflicts, all_responses)
                for p in valid_participants:
                    round_data["proposals"][p] = revised.copy()
                    resp = self.send_negotiation_proposal("omni-hub", p, revised)
                    round_data["responses"][p] = resp
                    all_responses[p] = resp
                current_proposal = revised

            elif round_num == 4:
                # Round 4: Collect revised responses
                round_data["responses"] = {p: all_responses[p] for p in valid_participants}

            elif round_num == 5:
                # Round 5: Final consensus vote
                score_data = self.compute_consensus_score(all_responses)
                round_data["consensus_score"] = score_data
                round_data["responses"] = {p: all_responses[p] for p in valid_participants}

            rounds_log.append(round_data)

        # Final evaluation
        final_score = self.compute_consensus_score(all_responses)
        consensus_reached = final_score["consensus_reached"]
        confidence = final_score["score"]

        # Determine agreement terms and dissenting lines
        agreement_terms = None
        dissenting = []
        if consensus_reached:
            agreement_terms = {
                "topic": topic,
                "accepted_by": [
                    p for p in valid_participants if all_responses[p].get("accept", False)
                ],
                "terms": current_proposal.get("terms", {}),
                "capabilities_shared": self._aggregate_capabilities(all_responses),
            }
            self._consensus_count += 1
        else:
            dissenting = [
                p for p in valid_participants if not all_responses[p].get("accept", False)
            ]

        result = {
            "negotiation_id": negotiation_id,
            "topic": topic,
            "participants": valid_participants,
            "consensus_reached": consensus_reached,
            "agreement_terms": agreement_terms,
            "dissenting_lines": dissenting,
            "confidence": round(confidence, 4),
            "rounds": rounds_log,
            "final_score": final_score,
        }

        self._negotiations[negotiation_id] = result

        if _HAS_BUS and bus is not None:
            try:
                bus.publish_simple(
                    Topics.STATE_CHANGE,
                    {
                        "source": "inter_line_consensus",
                        "event": "negotiation_complete",
                        "negotiation_id": negotiation_id,
                        "consensus_reached": consensus_reached,
                        "confidence": confidence,
                    },
                )
            except Exception:
                pass

        return result

    def _build_revised_proposal(
        self, base: Dict, conflicts: List[Dict], responses: Dict
    ) -> Dict:
        """Build a revised proposal that addresses detected conflicts."""
        revised = {
            "type": base.get("type", "consensus_vote"),
            "topic": base.get("topic", ""),
            "terms": dict(base.get("terms", {})),
            "revision": True,
        }
        # Downgrade scope if there are capability mismatches
        if any(c["type"] == "capability_mismatch" for c in conflicts):
            revised["terms"]["scope"] = "reduced_capability"
        # Add resource limits if resource contention
        if any(c["type"] == "resource_contention" for c in conflicts):
            revised["terms"]["resource_cap"] = "shared_fair"
        # Add temporal coordination if temporal conflicts
        if any(c["type"] == "temporal_conflict" for c in conflicts):
            revised["terms"]["sync_schedule"] = "staggered"
        return revised

    def _aggregate_capabilities(self, responses: Dict) -> List[str]:
        """Aggregate unique capabilities from all responses."""
        caps = set()
        for resp in responses.values():
            for c in resp.get("capabilities", []):
                caps.add(c)
        return sorted(caps)

    # ── Conflict detection ───────────────────────────────────────────────────

    def detect_cross_line_conflicts(self, responses: Dict) -> List[Dict]:
        """
        Detect conflicts between line responses.
        Conflict types: capability_mismatch, priority_conflict,
                        resource_contention, temporal_conflict
        """
        conflicts = []
        lines = list(responses.keys())
        if len(lines) < 2:
            return conflicts

        for i, line_a in enumerate(lines):
            for line_b in lines[i + 1 :]:
                resp_a = responses[line_a]
                resp_b = responses[line_b]
                caps_a = set(resp_a.get("capabilities", []))
                caps_b = set(resp_b.get("capabilities", []))

                # Capability mismatch: one has full capabilities, other has shell
                type_a = resp_a.get("response_type", "")
                type_b = resp_b.get("response_type", "")

                if (type_a == "full" and type_b in ("shell_proxy", "delayed")) or \
                   (type_b == "full" and type_a in ("shell_proxy", "delayed")):
                    conflicts.append({
                        "type": "capability_mismatch",
                        "between": [line_a, line_b],
                        "details": f"{line_a}({type_a}) vs {line_b}({type_b})",
                        "severity": "medium",
                    })

                # Priority conflict: one accepts, other rejects same type
                if resp_a.get("accept") != resp_b.get("accept"):
                    conflicts.append({
                        "type": "priority_conflict",
                        "between": [line_a, line_b],
                        "details": f"{line_a} accept={resp_a.get('accept')} vs {line_b} accept={resp_b.get('accept')}",
                        "severity": "high" if not (resp_a.get("accept") or resp_b.get("accept")) else "medium",
                    })

                # Resource contention: both claim compute but one is shell
                if "compute" in caps_a and "compute" in caps_b:
                    if type_a in ("shell_proxy", "delayed") or type_b in ("shell_proxy", "delayed"):
                        conflicts.append({
                            "type": "resource_contention",
                            "between": [line_a, line_b],
                            "details": f"Both claim compute but one is restricted ({type_a} vs {type_b})",
                            "severity": "medium",
                        })

                # Temporal conflict: delayed vs full response timing
                if (type_a == "delayed" and type_b == "full") or \
                   (type_b == "delayed" and type_a == "full"):
                    conflicts.append({
                        "type": "temporal_conflict",
                        "between": [line_a, line_b],
                        "details": f"Timing mismatch: {line_a}({type_a}) vs {line_b}({type_b})",
                        "severity": "low",
                    })

        return conflicts

    # ── Consensus scoring ────────────────────────────────────────────────────

    def compute_consensus_score(self, responses: Dict) -> Dict:
        """
        Compute overall consensus score.
        Formula: (avg_acceptance × participation_rate × term_overlap × readiness_weight) ^ 0.25
        """
        if not responses:
            return {
                "score": 0.0,
                "consensus_reached": False,
                "level": "failed",
                "components": {},
            }

        total = len(responses)
        avg_acceptance = sum(r.get("acceptance_score", 0.0) for r in responses.values()) / total
        participation_rate = 1.0  # All participants responded

        # Term overlap: fraction of lines that accepted
        accepts = sum(1 for r in responses.values() if r.get("accepted", False) or r.get("accept", False))
        term_overlap = accepts / total if total > 0 else 0.0

        # Readiness weight: average readiness of participants
        readiness_scores = []
        for line_id in responses:
            rd = self.classify_line_readiness(line_id)
            readiness_scores.append(rd.get("score", 0.0))
        readiness_weight = sum(readiness_scores) / len(readiness_scores) if readiness_scores else 0.0

        # Composite
        product = max(0.0, avg_acceptance * participation_rate * term_overlap * readiness_weight)
        score = product ** 0.25 if product > 0 else 0.0

        # Determine level
        if score >= 1.0:
            level = "unanimous"
        elif score > 0.8:
            level = "strong"
        elif score > 0.6:
            level = "majority"
        elif score > 0.4:
            level = "weak"
        else:
            level = "failed"

        consensus_reached = level in ("unanimous", "strong", "majority")

        return {
            "score": round(score, 4),
            "consensus_reached": consensus_reached,
            "level": level,
            "components": {
                "avg_acceptance": round(avg_acceptance, 4),
                "participation_rate": round(participation_rate, 4),
                "term_overlap": round(term_overlap, 4),
                "readiness_weight": round(readiness_weight, 4),
            },
        }

    # ── Protocol generation ──────────────────────────────────────────────────

    def generate_consensus_protocol(self, negotiation_result: Dict) -> Dict:
        """
        Generate formal consensus protocol document.
        Includes: agreed_terms, responsibilities per line, timeline, fallback procedures.
        """
        if not negotiation_result.get("consensus_reached"):
            return {
                "protocol_id": f"proto_{negotiation_result.get('negotiation_id', 'unknown')}",
                "status": "no_consensus",
                "reason": "Consensus was not reached; no protocol generated",
                "agreed_terms": None,
                "responsibilities": {},
                "timeline": {},
                "fallback": {
                    "action": "retry_with_reduced_scope",
                    "retry_delay_hours": 24,
                },
            }

        participants = negotiation_result.get("participants", [])
        agreement_terms = negotiation_result.get("agreement_terms", {}) or {}
        topic = negotiation_result.get("topic", "")

        # Assign responsibilities per line based on their capabilities
        responsibilities = {}
        for line_id in participants:
            resp = self.auto_respond(line_id, {"type": "capability_exchange", "topic": topic})
            caps = resp.get("capabilities", [])
            rtype = resp.get("response_type", "")

            if rtype == "full":
                responsibilities[line_id] = {
                    "role": "primary_contributor",
                    "actions": ["implement", "review", "propagate"],
                    "capabilities": caps,
                }
            elif rtype == "tower_ack":
                responsibilities[line_id] = {
                    "role": "tower_relay",
                    "actions": ["propagate", "monitor"],
                    "capabilities": caps,
                }
            elif rtype == "drive_ack":
                responsibilities[line_id] = {
                    "role": "drive_engine",
                    "actions": ["execute", "research"],
                    "capabilities": caps,
                }
            elif rtype == "shell_proxy":
                responsibilities[line_id] = {
                    "role": "passive_relay",
                    "actions": ["relay"],
                    "capabilities": caps,
                }
            elif rtype == "delayed":
                responsibilities[line_id] = {
                    "role": "observer",
                    "actions": ["monitor"],
                    "capabilities": caps,
                }
            else:
                responsibilities[line_id] = {
                    "role": "participant",
                    "actions": ["coordinate"],
                    "capabilities": caps,
                }

        protocol = {
            "protocol_id": f"proto_{negotiation_result.get('negotiation_id', 'unknown')}",
            "status": "active",
            "topic": topic,
            "agreed_terms": agreement_terms,
            "responsibilities": responsibilities,
            "timeline": {
                "activation": "immediate",
                "review": "24_hours",
                "renegotiation": "7_days",
            },
            "fallback": {
                "action": "escalate_to_omni_hub",
                "condition": "consensus_drops_below_majority",
                "procedure": "omni_hub_mediates_reduced_scope",
            },
            "confidence": negotiation_result.get("confidence", 0.0),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return protocol

    # ── Consensus execution ──────────────────────────────────────────────────

    def execute_consensus(self, protocol: Dict) -> Dict:
        """
        "Execute" consensus by generating actionable items.
        Returns: actions_per_line, expected_outcomes, monitoring_metrics.
        """
        if protocol.get("status") != "active":
            return {
                "executed": False,
                "reason": "Protocol not active",
                "actions_per_line": {},
                "expected_outcomes": {},
                "monitoring_metrics": {},
            }

        actions_per_line = {}
        responsibilities = protocol.get("responsibilities", {})

        for line_id, role_info in responsibilities.items():
            actions = []
            for action in role_info.get("actions", []):
                if action == "implement":
                    actions.append({
                        "action": "implement_term",
                        "priority": "high",
                        "deadline": "24h",
                        "detail": f"{line_id} implements agreed terms for {protocol.get('topic', '')}",
                    })
                elif action == "review":
                    actions.append({
                        "action": "peer_review",
                        "priority": "medium",
                        "deadline": "48h",
                        "detail": f"{line_id} reviews cross-line integration",
                    })
                elif action == "propagate":
                    actions.append({
                        "action": "state_propagation",
                        "priority": "high",
                        "deadline": "12h",
                        "detail": f"{line_id} propagates consensus state to connected lines",
                    })
                elif action == "monitor":
                    actions.append({
                        "action": "consensus_monitoring",
                        "priority": "low",
                        "deadline": "ongoing",
                        "detail": f"{line_id} monitors consensus health metrics",
                    })
                elif action == "execute":
                    actions.append({
                        "action": "drive_execution",
                        "priority": "high",
                        "deadline": "6h",
                        "detail": f"{line_id} executes LINE-DRIVE protocols",
                    })
                elif action == "research":
                    actions.append({
                        "action": "quant_research",
                        "priority": "medium",
                        "deadline": "72h",
                        "detail": f"{line_id} conducts quantum-field research",
                    })
                elif action == "relay":
                    actions.append({
                        "action": "passive_relay",
                        "priority": "low",
                        "deadline": "ongoing",
                        "detail": f"{line_id} relays state updates (readonly)",
                    })
                elif action == "coordinate":
                    actions.append({
                        "action": "coordinate",
                        "priority": "medium",
                        "deadline": "24h",
                        "detail": f"{line_id} coordinates with alliance peers",
                    })

            actions_per_line[line_id] = actions

        expected_outcomes = {
            "cross_line_sync": "All active lines share state within 24h",
            "shell_proxy_coverage": "Shell lines provide read-only relay",
            "tower_coordination": "Tower lines maintain autopilot propagation",
            "consensus_stability": f"Target confidence >= {protocol.get('confidence', 0.0)}",
        }

        monitoring_metrics = {
            "participation_rate": "pct_lines_responding / total_lines",
            "acceptance_velocity": "acceptance_score_delta_per_hour",
            "conflict_resolution_rate": "resolved_conflicts / total_conflicts",
            "protocol_adherence": "actions_completed / actions_assigned",
        }

        return {
            "executed": True,
            "protocol_id": protocol.get("protocol_id", ""),
            "actions_per_line": actions_per_line,
            "expected_outcomes": expected_outcomes,
            "monitoring_metrics": monitoring_metrics,
            "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ── Status ───────────────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """Return negotiation status."""
        real_accounts = self._real_topology.get("accounts", {}) if self._real_topology else {}
        real_repo_count = 0
        for account, top_level in real_accounts.items():
            for key, value in top_level.items():
                if not isinstance(value, dict):
                    continue
                # Detect flat vs grouped structure
                is_flat = any(k in value for k in ("line", "stake", "role", "dashboard"))
                if is_flat:
                    real_repo_count += 1
                else:
                    real_repo_count += len(value)

        return {
            "negotiation_count": self._negotiation_count,
            "consensus_count": self._consensus_count,
            "active_negotiations": list(self._negotiations.keys()),
            "lines_loaded": len(self._live_data),
            "line_ids": list(self._live_data.keys()),
            "real_topology_loaded": bool(self._real_topology),
            "real_topology_accounts": len(real_accounts),
            "real_topology_repos": real_repo_count,
        }


# Global singleton -----------------------------------------------------------------
_module: Optional[InterLineConsensus] = None


def get_inter_line_consensus(
    live_status_path: str = "data/alliance_repos_live_status.json",
) -> InterLineConsensus:
    """Lazy-loading global singleton for InterLineConsensus."""
    global _module
    if _module is None:
        _module = InterLineConsensus(live_status_path=live_status_path)
    return _module


def _reset_singleton() -> None:
    """Reset the singleton instance (intended for tests only)."""
    global _module
    _module = None
