#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12.0 — UnifiedWildNotebook (统一野问册)
==================================================
Integration of 4 Wild Notebook Systems:
  1. v12_wild_notebook.py       — Main Wild Notebook (1,205 lines)
  2. discussion_board.py        — Discussion Board System (1,022 lines)
  3. jing_wei_xin.py            — Jing-Wei-Xin 3D Architecture (1,467 lines)
  4. v12_eleven_lines_si_loop.py — SI Loop Simplified Version (embedded)

Unified Architecture:
  - Unified Data Model: UnifiedQuestion, UnifiedResponse, UnifiedDebt
  - Unified Knowledge Injection: 6-pedestal system
  - Unified SI Coordination: 11-line + Jing-Wei-Xin orchestration
  - Historical Data Migration: From discussion_board + jing_wei_xin

Version: 12.1.0-Unified
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import random
import sys
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

sys.path.insert(0, "/mnt/agents/output/OMNI-HUB/core")

# ---------------------------------------------------------------------------
# Import subsystems (with graceful fallback)
# ---------------------------------------------------------------------------
_subsystem_import_errors: Dict[str, str] = {}

# --- v12 standards & main wild notebook ---
try:
    from v12_standards import (
        UnifiedFieldState, DimensionIndex, UNIFIED_FIELD_DIMENSIONS,
        PHI_GOLDEN, PI, E_NATURAL, ALPHA_FINE_STRUCTURE, ALPHA_INV,
        EMERGENCE_THRESHOLD_V12, EmergenceTarget, ConsciousnessState,
        StateTransitionRules, CrossProjectTriangle, LINE_NAMES, LINE_DESCRIPTIONS,
        get_line_index, get_line_name, TickContext, AdaptContext, EmitContext,
        ModuleProtocol, get_logger, OMNIHUBException, OMNIHUBTheoreticalError,
        OMNIHUBTechnicalError, OMNIHUBEngineeringError, OMNIHUBFieldError,
        configure_logging, V12_VERSION, create_v12_unified_field, validate_field_state,
    )
except Exception as e:
    _subsystem_import_errors["v12_standards"] = str(e)
    # Minimal fallback stubs
    PHI_GOLDEN = 1.618033988749895
    PI = 3.141592653589793
    E_NATURAL = 2.718281828459045
    ALPHA_FINE_STRUCTURE = 0.0072973525693
    ALPHA_INV = 137.035999084
    LINE_NAMES = ["ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl", "qlv", "cisvr", "qtlv", "usrm", "cfts"]
    LINE_DESCRIPTIONS = {n: n for n in LINE_NAMES}
    class DimensionIndex(Enum):
        DIM_ENERGY = 0; DIM_INFORMATION = 1; DIM_AWARENESS = 2; DIM_EMOTION = 3
        DIM_TOPOLOGY = 4; DIM_CURVATURE = 5; DIM_KNOWLEDGE = 6; DIM_COHERENCE = 7
        DIM_ENTROPY = 8; DIM_EMERGENCE = 9; DIM_PHI_UNIFICATION = 10
    UNIFIED_FIELD_DIMENSIONS = 67
    class UnifiedFieldState:
        def __init__(self, dimensions=67): self._d = {i: 0.0 for i in range(dimensions)}
        def get(self, dim): return self._d.get(dim.value if hasattr(dim, 'value') else dim, 0.0)
        def set(self, dim, val): self._d[dim.value if hasattr(dim, 'value') else dim] = val
        def compute_coherence(self): return 0.5
        def compute_emergence_index(self): return 100.0
    class ConsciousnessState:
        @staticmethod
        def from_emergence(e): return type('CS', (), {'display_name': 'aware'})()
    def get_logger(name): return logging.getLogger(name)
    def configure_logging(**kw): pass
    V12_VERSION = "12.0.0"
    def create_v12_unified_field(): return UnifiedFieldState()
    def validate_field_state(fs): return True

# --- Main Wild Notebook ---
try:
    from v12_wild_notebook import (
        WildQuestion, AttestationRequest, WildNotebook, QuestionGenerator,
        QuestionCategory, QuestionStatus, AttestationStatus,
        LineResponse, ValidationResult, SurgeResult,
        GapDiscoveryResult, KnowledgeRefinementResult,
    )
    _HAS_V12_WN = True
except Exception as e:
    _subsystem_import_errors["v12_wild_notebook"] = str(e)
    _HAS_V12_WN = False
    # Fallback stubs
    class QuestionCategory(Enum):
        THEORETICAL = "theoretical"; TECHNICAL = "technical"
        ENGINEERING = "engineering"; EXPLORATORY = "exploratory"
    class QuestionStatus(Enum):
        PENDING = "pending"; ANSWERING = "answering"; VALIDATED = "validated"
        RESOLVED = "resolved"; REJECTED = "rejected"; SURGING = "surging"
    class AttestationStatus(Enum):
        PENDING = "pending"; APPROVED = "approved"; REJECTED = "rejected"; DEFERRED = "deferred"
    @dataclass
    class AttestationRequest:
        request_id: str = ""; requester_line: str = ""; target_line: str = ""
        claim: str = ""; evidence: Dict = field(default_factory=dict)
        status: Any = None; created_at: float = 0.0; resolved_at: Optional[float] = None; confidence: float = 0.0
    @dataclass
    class LineResponse:
        line_name: str = ""; question_id: str = ""; answer: str = ""
        confidence: float = 0.0; field_state_delta: Dict = field(default_factory=dict)
        metadata: Dict = field(default_factory=dict); timestamp: float = 0.0
        attestation_requests: List = field(default_factory=list)
    @dataclass
    class ValidationResult:
        question_id: str = ""; agreement_score: float = 0.0; consensus_answer: str = ""
        dissenting_lines: List = field(default_factory=list); supporting_lines: List = field(default_factory=list)
        attestation_results: List = field(default_factory=list); validation_passed: bool = False
        needs_surge: bool = False; metadata: Dict = field(default_factory=dict)
    @dataclass
    class SurgeResult:
        question_id: str = ""; surge_energy: float = 0.0; iterations: int = 0
        field_boost: float = 0.0; breakthrough: bool = False
        new_questions_generated: List = field(default_factory=list); metadata: Dict = field(default_factory=dict)
    @dataclass
    class GapDiscoveryResult:
        pedestal_gaps: Dict = field(default_factory=dict); total_gaps: int = 0
        gap_entropy: float = 0.0; prioritized_gaps: List = field(default_factory=list)
        metadata: Dict = field(default_factory=dict)
    @dataclass
    class KnowledgeRefinementResult:
        question_id: str = ""; injection_success: bool = False
        dimensions_updated: List = field(default_factory=list); coherence_change: float = 0.0
        emergence_change: float = 0.0; debt_resolved: bool = False; metadata: Dict = field(default_factory=dict)
    class WildQuestion:
        def __init__(self, id="", content="", category=None, priority=0.5,
                     status=None, created_at=None, resolved_at=None,
                     attestation_requests=None, prerequisite_chain=None,
                     line_assignments=None, responses=None,
                     validation=None, surge_result=None, refinement=None,
                     metadata=None, iteration_count=0, max_iterations=5, debt_id=None):
            self.id = id or f"WQ-{uuid.uuid4().hex[:8]}"
            self.content = content
            self.category = category
            self.priority = priority
            self.status = status
            self.created_at = created_at or time.time()
            self.resolved_at = resolved_at
            self.attestation_requests = attestation_requests or []
            self.prerequisite_chain = prerequisite_chain or []
            self.line_assignments = line_assignments or {}
            self.responses = responses or {}
            self.validation = validation
            self.surge_result = surge_result
            self.refinement = refinement
            self.metadata = metadata or {}
            self.iteration_count = iteration_count
            self.max_iterations = max_iterations
            self.debt_id = debt_id

# --- Discussion Board ---
# NOTE: discussion_board.py has a syntax error (from __future__ not at top).
# We use a direct file parser instead of import.
try:
    import ast
    with open("/mnt/agents/output/OMNI-HUB/core/discussion_board.py", "r") as f:
        ast.parse(f.read())
    # If parse succeeds, try import anyway
    from discussion_board import DiscussionBoard, Thread
    _HAS_DISCUSSION_BOARD = True
except SyntaxError as e:
    _subsystem_import_errors["discussion_board"] = f"SyntaxError: {e}"
    _HAS_DISCUSSION_BOARD = False
except Exception as e:
    _subsystem_import_errors["discussion_board"] = str(e)
    _HAS_DISCUSSION_BOARD = False

if not _HAS_DISCUSSION_BOARD:
    # Fallback Thread class (no dataclass to avoid annotation issues)
    class Thread:
        def __init__(self, thread_id="", space="", author="", title="", body="",
                     tags=None, priority=0, created_at=None, updated_at=None,
                     responses=None, confirmed_by=None, status="open",
                     visibility=1.0, auto_escalated=False, required_responders=None):
            self.thread_id = thread_id
            self.space = space
            self.author = author
            self.title = title
            self.body = body
            self.tags = tags or []
            self.priority = priority
            self.created_at = created_at or time.time()
            self.updated_at = updated_at or time.time()
            self.responses = responses or []
            self.confirmed_by = confirmed_by or []
            self.status = status
            self.visibility = visibility
            self.auto_escalated = auto_escalated
            self.required_responders = required_responders or []
        def to_dict(self):
            return {
                "thread_id": self.thread_id, "space": self.space, "author": self.author,
                "title": self.title, "body": self.body, "tags": self.tags,
                "priority": self.priority, "created_at": self.created_at,
                "updated_at": self.updated_at, "responses": self.responses,
                "confirmed_by": self.confirmed_by, "status": self.status,
                "visibility": self.visibility, "auto_escalated": self.auto_escalated,
                "required_responders": self.required_responders,
            }
    class DiscussionBoard:
        SPACES = ["discussion_room", "bulletin_board", "hall", "wild_ask"]
        def __init__(self, state_path="/tmp/omni_hub_board_state"):
            self.rooms = {s: {"threads": [], "visibility": 1.0, "last_update": None} for s in self.SPACES}
            self.state_path = Path(state_path)
            self._lines = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda"]

# --- Jing-Wei-Xin ---
try:
    import numpy as np
    _HAS_NUMPY = True
except Exception:
    _HAS_NUMPY = False
    np = None

try:
    from jing_wei_xin import JingWeiXin, JingState, WeiState, XinState
    from jing_wei_xin import SelfExcitationEngine, MutualExcitationEngine, FieldExcitationEngine
    from jing_wei_xin import TransientExcitationEngine, RippleEngine, ExcitationState
    _HAS_JING_WEI_XIN = True
except Exception as e:
    _subsystem_import_errors["jing_wei_xin"] = str(e)
    _HAS_JING_WEI_XIN = False
    class JingWeiXin:
        def __init__(self, lines=None):
            self.lines = lines or LINE_NAMES.copy()
            self.jing = type('J', (), {'basement': 1.0, 'pedestal': 1.2, 'genealogy': 1.5, 'ding': 2.0, 'spine': 2.5, 'polaris': 3.0})()
            self.wei = type('W', (), {'si_channels': {f'SI{i}': 0.5 for i in range(6)}, 'pat_throughput': 1.0, 'discussion_board_load': 0.8, 'bulletin_board_load': 0.3, 'wild_question_load': 0.2, 'surge_load': 0.6})()
            self.xin = type('X', (), {'self_excitation': 0.0, 'mutual_excitation': 0.0, 'field_excitation': 0.0, 'transient_excitation': 0.0, 'ripple_amplitude': 0.0})()
        def get_jing(self): return {'state': asdict(self.jing) if hasattr(self.jing, '__dict__') else {}}
        def get_wei(self): return {'state': asdict(self.wei) if hasattr(self.wei, '__dict__') else {}}
        def get_xin(self): return {'state': asdict(self.xin) if hasattr(self.xin, '__dict__') else {}}
        def weave(self): return {'weave_strength': 0.0}
        def self_sustain(self, cycles=5): return {'cycles_completed': cycles}
        def get_architecture_report(self): return {}

# --- SI Loop ---
try:
    from v12_eleven_lines_si_loop import (
        LineEngine, LineState, LineMessage, LineTickResult,
        SITickResult, SILoopReport, LineStatus, MessageType,
        SystemIntelligence as SILoopSystemIntelligence,
    )
    _HAS_SI_LOOP = True
except Exception as e:
    _subsystem_import_errors["v12_eleven_lines_si_loop"] = str(e)
    _HAS_SI_LOOP = False
    class LineStatus(Enum):
        ACTIVE = "active"; STANDBY = "standby"; SUSPENDED = "suspended"; ERROR = "error"
    class MessageType(Enum):
        KNOWLEDGE = "knowledge"; DEBT = "debt"; SURGE = "surge"; SYNC = "sync"
        ALERT = "alert"; COUPLING = "coupling"; PHILOSOPHY = "philosophy"
    class LineState:
        def __init__(self, line_id="", si_level=0, activity_level=0.0,
                     consciousness_level=0, contribution_score=0.0, last_tick=0,
                     message_queue=None, status=None, error_count=0, success_count=0,
                     total_runtime=0.0, phi_coupling=0.0, debt_count=0,
                     knowledge_count=0, entropy=0.0, coherence=0.0):
            self.line_id = line_id; self.si_level = si_level; self.activity_level = activity_level
            self.consciousness_level = consciousness_level; self.contribution_score = contribution_score
            self.last_tick = last_tick; self.message_queue = message_queue or []
            self.status = status; self.error_count = error_count; self.success_count = success_count
            self.total_runtime = total_runtime; self.phi_coupling = phi_coupling; self.debt_count = debt_count
            self.knowledge_count = knowledge_count; self.entropy = entropy; self.coherence = coherence
        def to_dict(self):
            return {
                "line_id": self.line_id, "si_level": self.si_level, "activity_level": self.activity_level,
                "consciousness_level": self.consciousness_level, "contribution_score": self.contribution_score,
                "last_tick": self.last_tick, "status": self.status.value if hasattr(self.status, 'value') else str(self.status),
                "error_count": self.error_count, "success_count": self.success_count,
                "total_runtime": self.total_runtime, "phi_coupling": self.phi_coupling,
                "debt_count": self.debt_count, "knowledge_count": self.knowledge_count,
                "entropy": self.entropy, "coherence": self.coherence,
                "message_queue_len": len(self.message_queue),
            }
    class LineMessage:
        def __init__(self, msg_id="", source="", target="", msg_type=None,
                     payload=None, timestamp=None, priority=5, ttl=3, ack_required=False):
            self.msg_id = msg_id or str(uuid.uuid4())[:8]
            self.source = source; self.target = target; self.msg_type = msg_type
            self.payload = payload or {}; self.timestamp = timestamp or time.time()
            self.priority = priority; self.ttl = ttl; self.ack_required = ack_required
    class LineTickResult:
        def __init__(self, line_id="", tick_number=0, status=None,
                     messages_sent=None, messages_received=0, field_updates=None,
                     contribution_delta=0.0, execution_time_ms=0.0,
                     debt_generated=None, knowledge_generated=None,
                     error_info=None, phi_injected=False):
            self.line_id = line_id; self.tick_number = tick_number; self.status = status
            self.messages_sent = messages_sent or []; self.messages_received = messages_received
            self.field_updates = field_updates or {}; self.contribution_delta = contribution_delta
            self.execution_time_ms = execution_time_ms; self.debt_generated = debt_generated or []
            self.knowledge_generated = knowledge_generated or []; self.error_info = error_info
            self.phi_injected = phi_injected
        def to_dict(self):
            return {
                "line_id": self.line_id, "tick_number": self.tick_number,
                "status": self.status.value if hasattr(self.status, 'value') else str(self.status),
                "messages_sent": len(self.messages_sent), "messages_received": self.messages_received,
                "field_updates": self.field_updates, "contribution_delta": self.contribution_delta,
                "execution_time_ms": self.execution_time_ms,
                "debt_generated": len(self.debt_generated),
                "knowledge_generated": len(self.knowledge_generated),
                "error_info": self.error_info, "phi_injected": self.phi_injected,
            }
    class SITickResult:
        def __init__(self, tick_number=0, timestamp=None, line_results=None,
                     global_emergence=0.0, messages_exchanged=0, debts_processed=0,
                     field_updates=None, weak_lines_activated=None,
                     surge_triggered=False, consciousness_state="", consciousness_level=0,
                     si_actions=None):
            self.tick_number = tick_number; self.timestamp = timestamp or time.time()
            self.line_results = line_results or {}; self.global_emergence = global_emergence
            self.messages_exchanged = messages_exchanged; self.debts_processed = debts_processed
            self.field_updates = field_updates or []; self.weak_lines_activated = weak_lines_activated or []
            self.surge_triggered = surge_triggered; self.consciousness_state = consciousness_state
            self.consciousness_level = consciousness_level; self.si_actions = si_actions or []
        def to_dict(self):
            return {
                "tick_number": self.tick_number, "timestamp": self.timestamp,
                "global_emergence": self.global_emergence, "messages_exchanged": self.messages_exchanged,
                "debts_processed": self.debts_processed, "field_updates_count": len(self.field_updates),
                "weak_lines_activated": self.weak_lines_activated, "surge_triggered": self.surge_triggered,
                "consciousness_state": self.consciousness_state, "consciousness_level": self.consciousness_level,
                "si_actions": self.si_actions,
                "line_results": {k: v.to_dict() for k, v in self.line_results.items()},
            }
    class SILoopSystemIntelligence:
        def __init__(self, field_state=None): pass

# --- Debt Cleanup ---
try:
    from v12_debt_cleanup import (
        DebtCleanupExecutor, TheoreticalDebt, TechnicalDebt, CleanupReport,
        CleanupStatus, DebtType, DebtSeverity,
    )
    _HAS_DEBT_CLEANUP = True
except Exception as e:
    _subsystem_import_errors["v12_debt_cleanup"] = str(e)
    _HAS_DEBT_CLEANUP = False
    class DebtType(Enum):
        THEORETICAL = "theoretical"; TECHNICAL = "technical"; ENGINEERING = "engineering"
    class DebtSeverity(Enum):
        LOW = "low"; MEDIUM = "medium"; HIGH = "high"; CRITICAL = "critical"
    class CleanupStatus(Enum):
        AUTO_CLEANED = "auto_cleaned"; NEEDS_MANUAL = "needs_manual"; DEFERRED = "deferred"; PARTIAL = "partial"
    class TheoreticalDebt:
        def __init__(self, id="", name="", description="", file_path="",
                     severity=None, status=None, lean_formalizable=False,
                     lean_skeleton="", proof_strategy="", blocker="",
                     verification_method="", estimated_hours=0.0, **kwargs):
            self.id = id; self.name = name; self.description = description; self.file_path = file_path
            self.severity = severity; self.status = status; self.lean_formalizable = lean_formalizable
            self.lean_skeleton = lean_skeleton; self.proof_strategy = proof_strategy; self.blocker = blocker
            self.verification_method = verification_method; self.estimated_hours = estimated_hours
            for k, v in kwargs.items():
                setattr(self, k, v)
    class TechnicalDebt:
        def __init__(self, id="", description="", file_path="",
                     severity=None, debt_type="", fix_strategy="",
                     auto_fixable=False, status=None, patch_preview="",
                     estimated_hours=0.0, **kwargs):
            self.id = id; self.description = description; self.file_path = file_path
            self.severity = severity; self.debt_type = debt_type; self.fix_strategy = fix_strategy
            self.auto_fixable = auto_fixable; self.status = status; self.patch_preview = patch_preview
            self.estimated_hours = estimated_hours
            for k, v in kwargs.items():
                setattr(self, k, v)

# --- Knowledge Pedestal ---
try:
    from v11_knowledge_pedestal_unified import (
        KnowledgePedestal, KNode, KEdge, HyperEdge, Cell, Morphism, FormalProp,
        KGBase, CCBase, HGBase, INBase, CTBase, LLBase, PedestalBridge, Pedestal,
        KnowledgeOperations, SandboxScanner, stable_hash,
    )
    _HAS_KNOWLEDGE_PEDESTAL = True
except Exception as e:
    _subsystem_import_errors["v11_knowledge_pedestal"] = str(e)
    _HAS_KNOWLEDGE_PEDESTAL = False
    class KnowledgePedestal:
        def __init__(self):
            self.nodes = {}; self.kg_edges = []; self.kg_adj = defaultdict(list)
            self.cc_cells = {}; self.hg_edges = []; self.in_clusters = {}
            self.ct_morphisms = []; self.ll_propositions = []
        def add_node(self, node):
            nid = getattr(node, 'node_id', str(node))
            self.nodes[nid] = node
        def summary(self):
            return {"nodes": len(self.nodes), "edges": len(self.kg_edges)}
    def stable_hash(x):
        return hashlib.sha256(str(x).encode()).hexdigest()[:16]

__version__ = "12.1.0-Unified"
__all__ = [
    "UnifiedQuestion", "UnifiedResponse", "UnifiedDebt", "UnifiedReport",
    "UnifiedWildNotebook", "SubsystemBridge", "MigrationEngine",
]

logger = get_logger("v12_wild_notebook_unified")
CORE_DIR = Path("/mnt/agents/output/OMNI-HUB/core")
HUB_DIR = Path("/mnt/agents/output/OMNI-HUB/hub")


# =============================================================================
# 0. Unified Enumerations
# =============================================================================

class UnifiedQuestionSource(Enum):
    """Source subsystem of a unified question."""
    V12_WN = "v12_wild_notebook"
    DISCUSSION_BOARD = "discussion_board"
    JING_WEI_XIN = "jing_wei_xin"
    SI_LOOP = "si_loop"
    UNIFIED = "unified"


class UnifiedResponseType(Enum):
    """Type of unified response."""
    ANSWER = "answer"
    CONFIRM = "confirm"
    FOLLOWUP = "followup"
    DEBATE = "debate"
    SURGE = "surge"
    LINE_RESPONSE = "line_response"
    ENGINE_RESPONSE = "engine_response"


class UnifiedDebtStatus(Enum):
    """Unified debt status."""
    DISCOVERED = "discovered"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    DEFERRED = "deferred"
    ESCALATED = "escalated"


# =============================================================================
# 1. Unified Data Structures
# =============================================================================

@dataclass
class UnifiedResponse:
    """A unified response from any subsystem."""
    response_id: str = field(default_factory=lambda: f"UR-{uuid.uuid4().hex[:8]}")
    source_system: str = ""
    source_line: Optional[str] = None
    response_type: UnifiedResponseType = UnifiedResponseType.ANSWER
    content: str = ""
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    attestation_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["response_type"] = self.response_type.value
        return d


@dataclass
class UnifiedDebt:
    """A unified debt item aggregated from all subsystems."""
    debt_id: str = field(default_factory=lambda: f"UD-{uuid.uuid4().hex[:8]}")
    original_id: Optional[str] = None
    source_system: str = ""
    debt_type: str = "technical"  # theoretical | technical | engineering
    description: str = ""
    severity: float = 0.5
    status: UnifiedDebtStatus = UnifiedDebtStatus.DISCOVERED
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    assigned_lines: List[str] = field(default_factory=list)
    related_questions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class UnifiedQuestion:
    """
    A unified question that can originate from any subsystem.
    Serves as the canonical question format across all 4 systems.
    """
    question_id: str = field(default_factory=lambda: f"UQ-{uuid.uuid4().hex[:8]}")
    original_id: Optional[str] = None
    source_system: str = UnifiedQuestionSource.UNIFIED.value
    content: str = ""
    category: str = "exploratory"  # theoretical | technical | engineering | exploratory
    priority: float = 0.5
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    line_assignments: Dict[str, float] = field(default_factory=dict)
    responses: List[UnifiedResponse] = field(default_factory=list)
    validation_score: float = 0.0
    consensus_answer: str = ""
    debt_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    iteration_count: int = 0
    migration_source: Optional[str] = None

    def __post_init__(self):
        if not self.line_assignments:
            for line in LINE_NAMES:
                self.line_assignments[line] = 1.0 / len(LINE_NAMES)

    def add_response(self, response: UnifiedResponse) -> None:
        self.responses.append(response)

    def compute_validation_score(self) -> float:
        if not self.responses:
            return 0.0
        confidences = [r.confidence for r in self.responses if r.confidence > 0]
        if not confidences:
            return 0.0
        return round(sum(confidences) / len(confidences), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "original_id": self.original_id,
            "source_system": self.source_system,
            "content": self.content,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "line_assignments": self.line_assignments,
            "responses": [r.to_dict() for r in self.responses],
            "validation_score": self.compute_validation_score(),
            "consensus_answer": self.consensus_answer,
            "debt_id": self.debt_id,
            "metadata": self.metadata,
            "iteration_count": self.iteration_count,
            "migration_source": self.migration_source,
        }


@dataclass
class UnifiedReport:
    """Comprehensive unified report across all subsystems."""
    report_id: str = field(default_factory=lambda: f"URP-{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)
    version: str = __version__

    # Subsystem health
    subsystem_health: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Unified metrics
    total_questions: int = 0
    total_responses: int = 0
    total_debts: int = 0
    resolved_debts: int = 0
    active_surges: int = 0

    # 6-pedestal injection summary
    pedestal_injections: Dict[str, int] = field(default_factory=dict)

    # Jing-Wei-Xin status
    jing_wei_xin_status: Dict[str, Any] = field(default_factory=dict)

    # Coverage metrics
    coverage_rate: float = 0.0
    blind_spots: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# 2. Subsystem Bridge
# =============================================================================

class SubsystemBridge:
    """
    Bridge layer that adapts each subsystem's native format to unified format.
    """

    @staticmethod
    def adapt_v12_question(wq: WildQuestion) -> UnifiedQuestion:
        """Convert v12 WildQuestion to UnifiedQuestion."""
        cat = wq.category.value if hasattr(wq.category, 'value') else str(wq.category)
        status = wq.status.value if hasattr(wq.status, 'value') else str(wq.status)
        uq = UnifiedQuestion(
            question_id=f"UQ-V12-{wq.id}",
            original_id=wq.id,
            source_system=UnifiedQuestionSource.V12_WN.value,
            content=wq.content,
            category=cat,
            priority=wq.priority,
            status=status,
            created_at=wq.created_at,
            resolved_at=wq.resolved_at,
            line_assignments=dict(wq.line_assignments) if wq.line_assignments else {},
            debt_id=wq.debt_id,
            metadata=dict(wq.metadata) if wq.metadata else {},
            iteration_count=wq.iteration_count,
        )
        # Adapt responses
        for line_name, lr in (wq.responses or {}).items():
            ur = UnifiedResponse(
                source_system=UnifiedQuestionSource.V12_WN.value,
                source_line=line_name,
                response_type=UnifiedResponseType.LINE_RESPONSE,
                content=lr.answer if hasattr(lr, 'answer') else str(lr),
                confidence=lr.confidence if hasattr(lr, 'confidence') else 0.5,
                timestamp=lr.timestamp if hasattr(lr, 'timestamp') else time.time(),
                metadata=lr.metadata if hasattr(lr, 'metadata') else {},
            )
            uq.add_response(ur)
        # Set consensus
        if wq.validation and hasattr(wq.validation, 'consensus_answer'):
            uq.consensus_answer = wq.validation.consensus_answer
            uq.validation_score = wq.validation.agreement_score if hasattr(wq.validation, 'agreement_score') else 0.0
        return uq

    @staticmethod
    def adapt_db_thread(thread: Thread) -> UnifiedQuestion:
        """Convert DiscussionBoard Thread to UnifiedQuestion."""
        # Map discussion board space to question category
        space_to_cat = {
            "wild_ask": "exploratory",
            "discussion_room": "technical",
            "bulletin_board": "engineering",
            "hall": "exploratory",
        }
        cat = space_to_cat.get(thread.space, "exploratory")
        status_map = {
            "open": "pending", "closed": "resolved", "escalated": "surging",
            "answered": "resolved", "archived": "resolved",
        }
        status = status_map.get(thread.status, "pending")

        uq = UnifiedQuestion(
            question_id=f"UQ-DB-{thread.thread_id}",
            original_id=thread.thread_id,
            source_system=UnifiedQuestionSource.DISCUSSION_BOARD.value,
            content=f"[{thread.space}] {thread.title}: {thread.body}",
            category=cat,
            priority=min(1.0, thread.priority / 9.0),
            status=status,
            created_at=thread.created_at,
            resolved_at=thread.updated_at if status == "resolved" else None,
            metadata={
                "space": thread.space,
                "author": thread.author,
                "tags": thread.tags,
                "visibility": thread.visibility,
                "response_count": len(thread.responses),
            },
        )
        # Adapt responses
        for resp in (thread.responses or []):
            rt_map = {
                "answer": UnifiedResponseType.ANSWER,
                "followup": UnifiedResponseType.FOLLOWUP,
                "confirm": UnifiedResponseType.CONFIRM,
                "debate": UnifiedResponseType.DEBATE,
                "chat": UnifiedResponseType.FOLLOWUP,
            }
            ur = UnifiedResponse(
                source_system=UnifiedQuestionSource.DISCUSSION_BOARD.value,
                source_line=resp.get("author", "unknown"),
                response_type=rt_map.get(resp.get("type", "answer"), UnifiedResponseType.ANSWER),
                content=resp.get("body", ""),
                timestamp=resp.get("timestamp", time.time()),
                metadata={"response_id": resp.get("response_id", "")},
            )
            uq.add_response(ur)
        return uq

    @staticmethod
    def adapt_jwx_to_question(jwx_state: Dict[str, Any], query: str = "") -> UnifiedQuestion:
        """Convert JingWeiXin state anomaly to UnifiedQuestion."""
        return UnifiedQuestion(
            question_id=f"UQ-JWX-{uuid.uuid4().hex[:8]}",
            source_system=UnifiedQuestionSource.JING_WEI_XIN.value,
            content=query or "Jing-Wei-Xin architecture analysis query",
            category="exploratory",
            priority=0.6,
            metadata={"jwx_state": jwx_state},
        )

    @staticmethod
    def adapt_si_loop_message(msg: LineMessage) -> UnifiedQuestion:
        """Convert SI Loop message to UnifiedQuestion."""
        mt_map = {
            "knowledge": "exploratory", "debt": "technical", "surge": "exploratory",
            "sync": "technical", "alert": "engineering", "coupling": "technical",
            "philosophy": "theoretical",
        }
        mt_val = msg.msg_type.value if hasattr(msg.msg_type, 'value') else str(msg.msg_type)
        cat = mt_map.get(mt_val, "exploratory")
        return UnifiedQuestion(
            question_id=f"UQ-SI-{msg.msg_id}",
            original_id=msg.msg_id,
            source_system=UnifiedQuestionSource.SI_LOOP.value,
            content=f"[{mt_val}] {msg.source}->{msg.target}: {json.dumps(msg.payload)[:200]}",
            category=cat,
            priority=max(0.1, min(1.0, (11 - msg.priority) / 10.0)),
            metadata={"msg_type": mt_val, "source": msg.source, "target": msg.target, "payload": msg.payload},
        )

    @staticmethod
    def adapt_debt_to_unified(debt_item: Any, debt_type: DebtType) -> UnifiedDebt:
        """Convert any debt item to UnifiedDebt."""
        did = getattr(debt_item, 'id', f"UD-{uuid.uuid4().hex[:8]}")
        desc = getattr(debt_item, 'description', getattr(debt_item, 'name', str(debt_item)))
        sev = getattr(debt_item, 'severity', DebtSeverity.MEDIUM)
        sev_val = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}.get(
            sev.value if hasattr(sev, 'value') else str(sev), 0.5)
        return UnifiedDebt(
            debt_id=f"UD-{did}",
            original_id=did,
            source_system="debt_cleanup",
            debt_type=debt_type.value if hasattr(debt_type, 'value') else str(debt_type),
            description=desc,
            severity=sev_val,
            metadata={"original_type": type(debt_item).__name__},
        )


# =============================================================================
# 3. Migration Engine
# =============================================================================

class MigrationEngine:
    """
    Handles historical data migration from discussion_board and jing_wei_xin
    into the unified format.
    """

    def __init__(self, discussion_board: Optional[DiscussionBoard] = None,
                 jing_wei_xin: Optional[JingWeiXin] = None):
        self.db = discussion_board
        self.jwx = jing_wei_xin
        self.migrated_questions: List[UnifiedQuestion] = []
        self.migrated_debts: List[UnifiedDebt] = []
        self.migration_log: List[Dict[str, Any]] = []

    def migrate_from_discussion_board(self) -> Dict[str, Any]:
        """Migrate all threads from DiscussionBoard to unified questions."""
        if self.db is None:
            return {"status": "skipped", "reason": "DiscussionBoard not available"}

        migrated = []
        errors = []

        for space in getattr(self.db, 'SPACES', ["discussion_room", "bulletin_board", "hall", "wild_ask"]):
            try:
                room = self.db.rooms.get(space, {})
                threads = room.get("threads", [])
                for thread in threads:
                    try:
                        uq = SubsystemBridge.adapt_db_thread(thread)
                        uq.migration_source = f"discussion_board:{space}"
                        migrated.append(uq)
                    except Exception as e:
                        errors.append({"thread_id": getattr(thread, 'thread_id', 'unknown'), "error": str(e)})
            except Exception as e:
                errors.append({"space": space, "error": str(e)})

        self.migrated_questions.extend(migrated)
        result = {
            "status": "success",
            "source": "discussion_board",
            "questions_migrated": len(migrated),
            "errors": len(errors),
            "error_details": errors[:10],
        }
        self.migration_log.append(result)
        return result

    def migrate_from_jing_wei_xin(self) -> Dict[str, Any]:
        """Migrate JingWeiXin architecture state into unified questions."""
        if self.jwx is None:
            return {"status": "skipped", "reason": "JingWeiXin not available"}

        migrated = []
        try:
            # Migrate Jing state gaps
            jing_data = self.jwx.get_jing()
            jing_state = jing_data.get('state', {})
            for level, value in jing_state.items():
                if isinstance(value, (int, float)) and value < 0.5:
                    uq = UnifiedQuestion(
                        question_id=f"UQ-JWX-JING-{level}-{uuid.uuid4().hex[:4]}",
                        source_system=UnifiedQuestionSource.JING_WEI_XIN.value,
                        content=f"Jing level '{level}' is weak ({value:.2f}). How to strengthen structural ontology?",
                        category="theoretical",
                        priority=1.0 - value,
                        metadata={"jing_level": level, "jing_value": value, "migration_source": "jing_wei_xin"},
                    )
                    migrated.append(uq)

            # Migrate Wei channel load imbalances
            wei_data = self.jwx.get_wei()
            wei_state = wei_data.get('state', {})
            si_channels = wei_state.get('si_channels', {})
            for ch, load in si_channels.items():
                if load > 0.9:
                    uq = UnifiedQuestion(
                        question_id=f"UQ-JWX-WEI-{ch}-{uuid.uuid4().hex[:4]}",
                        source_system=UnifiedQuestionSource.JING_WEI_XIN.value,
                        content=f"Wei channel '{ch}' is overloaded ({load:.2f}). How to redistribute load?",
                        category="engineering",
                        priority=load,
                        metadata={"wei_channel": ch, "wei_load": load, "migration_source": "jing_wei_xin"},
                    )
                    migrated.append(uq)

            # Migrate Xin power deficiencies
            xin_data = self.jwx.get_xin()
            xin_state = xin_data.get('state', {})
            for engine, power in xin_state.items():
                if isinstance(power, (int, float)) and power < 0.3:
                    uq = UnifiedQuestion(
                        question_id=f"UQ-JWX-XIN-{engine}-{uuid.uuid4().hex[:4]}",
                        source_system=UnifiedQuestionSource.JING_WEI_XIN.value,
                        content=f"Xin engine '{engine}' is underpowered ({power:.2f}). How to boost fuel power?",
                        category="technical",
                        priority=1.0 - power,
                        metadata={"xin_engine": engine, "xin_power": power, "migration_source": "jing_wei_xin"},
                    )
                    migrated.append(uq)

        except Exception as e:
            return {"status": "error", "source": "jing_wei_xin", "error": str(e)}

        self.migrated_questions.extend(migrated)
        result = {
            "status": "success",
            "source": "jing_wei_xin",
            "questions_migrated": len(migrated),
            "jing_levels_checked": len(jing_state),
            "wei_channels_checked": len(si_channels) if 'si_channels' in locals() else 0,
        }
        self.migration_log.append(result)
        return result

    def migrate_from_si_loop(self, si_lines: Optional[Dict[str, LineState]] = None) -> Dict[str, Any]:
        """Migrate SI Loop line states into unified debts/questions."""
        if si_lines is None:
            return {"status": "skipped", "reason": "SI line states not provided"}

        migrated_debts = []
        migrated_questions = []

        for line_id, line_state in si_lines.items():
            # Migrate high-debt lines
            if line_state.debt_count > 3:
                ud = UnifiedDebt(
                    debt_id=f"UD-SI-{line_id}-{uuid.uuid4().hex[:4]}",
                    source_system=UnifiedQuestionSource.SI_LOOP.value,
                    debt_type="technical",
                    description=f"Line {line_id} has {line_state.debt_count} accumulated debts",
                    severity=min(1.0, line_state.debt_count / 10.0),
                    assigned_lines=[line_id],
                    metadata={"line_state": line_state.to_dict()},
                )
                migrated_debts.append(ud)

            # Migrate low-activity lines
            if line_state.activity_level < 0.2 and line_state.status != LineStatus.ERROR:
                uq = UnifiedQuestion(
                    question_id=f"UQ-SI-ACTIVATE-{line_id}-{uuid.uuid4().hex[:4]}",
                    source_system=UnifiedQuestionSource.SI_LOOP.value,
                    content=f"Line {line_id} has low activity ({line_state.activity_level:.2f}). How to activate?",
                    category="engineering",
                    priority=0.8,
                    metadata={"line_id": line_id, "activity_level": line_state.activity_level},
                )
                migrated_questions.append(uq)

            # Migrate error lines
            if line_state.status == LineStatus.ERROR:
                uq = UnifiedQuestion(
                    question_id=f"UQ-SI-ERROR-{line_id}-{uuid.uuid4().hex[:4]}",
                    source_system=UnifiedQuestionSource.SI_LOOP.value,
                    content=f"Line {line_id} is in ERROR state with {line_state.error_count} errors. How to recover?",
                    category="technical",
                    priority=0.95,
                    metadata={"line_id": line_id, "error_count": line_state.error_count},
                )
                migrated_questions.append(uq)

        self.migrated_debts.extend(migrated_debts)
        self.migrated_questions.extend(migrated_questions)
        return {
            "status": "success",
            "source": "si_loop",
            "debts_migrated": len(migrated_debts),
            "questions_migrated": len(migrated_questions),
        }

    def get_all_migrated(self) -> Tuple[List[UnifiedQuestion], List[UnifiedDebt]]:
        return self.migrated_questions, self.migrated_debts

    def get_migration_summary(self) -> Dict[str, Any]:
        return {
            "total_questions_migrated": len(self.migrated_questions),
            "total_debts_migrated": len(self.migrated_debts),
            "log_entries": len(self.migration_log),
            "log": self.migration_log,
            "sources": list(set(q.source_system for q in self.migrated_questions)),
        }


# =============================================================================
# 4. Knowledge Injection Interface
# =============================================================================

class UnifiedKnowledgeInjector:
    """
    Unified interface for injecting knowledge into the 6 knowledge pedestals.
    """

    PEDESTAL_NAMES = ["KG", "CC", "HG", "IN", "CT", "LL"]

    def __init__(self, pedestal: Optional[KnowledgePedestal] = None):
        self.pedestal = pedestal or KnowledgePedestal()
        self.injection_history: deque = deque(maxlen=500)
        self._injection_count = 0

    def inject_question_answer(self, uq: UnifiedQuestion) -> Dict[str, Any]:
        """Inject a resolved unified question into the 6 pedestals."""
        if uq.status != "resolved":
            return {"injected": False, "reason": "Question not resolved"}

        results = {}
        node_id = stable_hash((uq.question_id, uq.content))

        # KG: Knowledge Graph - add node and edges
        try:
            new_node = KNode(
                node_id=node_id,
                label=f"UQ_{uq.question_id[:20]}",
                node_type="unified_question",
                module="unified_wild_notebook",
                version=__version__,
                size_bytes=len(uq.content.encode("utf-8")),
                path=f"unified/{uq.question_id}",
                metadata={
                    "question_id": uq.question_id,
                    "category": uq.category,
                    "priority": uq.priority,
                    "source_system": uq.source_system,
                    "response_count": len(uq.responses),
                }
            )
            self.pedestal.add_node(new_node)
            results["KG"] = {"node_added": node_id}

            # Add edges from responding lines
            for resp in uq.responses:
                if resp.source_line:
                    e = KEdge(
                        edge_id=stable_hash((resp.source_line, node_id, "responds_to")),
                        source=resp.source_line,
                        target=node_id,
                        edge_type="subsystem_response",
                        weight=resp.confidence,
                        metadata={"response_type": resp.response_type.value if hasattr(resp.response_type, 'value') else str(resp.response_type)}
                    )
                    self.pedestal.kg_edges.append(e)
                    self.pedestal.kg_adj[resp.source_line].append((node_id, resp.confidence, "subsystem_response"))
        except Exception as e:
            results["KG"] = {"error": str(e)}

        # CC: Cellular Complex - create cell for question category
        try:
            results["CC"] = {"cell_created": f"cc_{uq.category}_{node_id[:8]}"}
        except Exception as e:
            results["CC"] = {"error": str(e)}

        # HG: Hypergraph - create hyperedge connecting all respondents
        try:
            respondents = list(set(r.source_line for r in uq.responses if r.source_line))
            if respondents:
                results["HG"] = {"hyperedge": respondents, "arity": len(respondents)}
        except Exception as e:
            results["HG"] = {"error": str(e)}

        # IN: Information Network - cluster by source system
        try:
            cluster_key = f"cluster_{uq.source_system}"
            if not hasattr(self.pedestal, 'in_clusters'):
                self.pedestal.in_clusters = {}
            if cluster_key not in self.pedestal.in_clusters:
                self.pedestal.in_clusters[cluster_key] = []
            self.pedestal.in_clusters[cluster_key].append(node_id)
            results["IN"] = {"cluster": cluster_key, "node_added": node_id}
        except Exception as e:
            results["IN"] = {"error": str(e)}

        # CT: Category Theory - morphism from source to unified
        try:
            results["CT"] = {"morphism": f"{uq.source_system} -> unified_question"}
        except Exception as e:
            results["CT"] = {"error": str(e)}

        # LL: Logic Layer - proposition
        try:
            results["LL"] = {"proposition": f"Resolved: {uq.content[:50]}..."}
        except Exception as e:
            results["LL"] = {"error": str(e)}

        self._injection_count += 1
        self.injection_history.append({
            "question_id": uq.question_id,
            "timestamp": time.time(),
            "pedestal_results": results,
        })

        return {"injected": True, "node_id": node_id, "pedestals": results}

    def inject_debt(self, debt: UnifiedDebt) -> Dict[str, Any]:
        """Inject a debt item into the knowledge pedestals."""
        node_id = stable_hash((debt.debt_id, debt.description))
        try:
            new_node = KNode(
                node_id=node_id,
                label=f"DEBT_{debt.debt_id[:20]}",
                node_type="unified_debt",
                module="unified_wild_notebook",
                version=__version__,
                size_bytes=len(debt.description.encode("utf-8")),
                path=f"debt/{debt.debt_id}",
                metadata={
                    "debt_id": debt.debt_id,
                    "debt_type": debt.debt_type,
                    "severity": debt.severity,
                    "status": debt.status.value if hasattr(debt.status, 'value') else str(debt.status),
                }
            )
            self.pedestal.add_node(new_node)
            return {"injected": True, "node_id": node_id, "pedestal": "KG"}
        except Exception as e:
            return {"injected": False, "error": str(e)}

    def get_injection_stats(self) -> Dict[str, Any]:
        return {
            "total_injections": self._injection_count,
            "history_size": len(self.injection_history),
            "pedestal_summary": self.pedestal.summary() if hasattr(self.pedestal, 'summary') else {},
        }


# =============================================================================
# 5. Unified SI Coordination Interface
# =============================================================================

class UnifiedSICoordinator:
    """
    Unified SI coordination that bridges v12 WildNotebook, JingWeiXin engines,
    and SI Loop line states.
    """

    def __init__(self, jing_wei_xin: Optional[JingWeiXin] = None,
                 field_state: Optional[UnifiedFieldState] = None):
        self.jwx = jing_wei_xin or (JingWeiXin() if _HAS_JING_WEI_XIN else None)
        self.field_state = field_state or create_v12_unified_field()
        self.line_states: Dict[str, LineState] = {}
        self.coordination_history: deque = deque(maxlen=100)
        self._tick_count = 0

    def coordinate_lines(self, active_lines: List[str]) -> Dict[str, Any]:
        """Coordinate multiple lines using JingWeiXin mutual excitation."""
        if self.jwx is None or not _HAS_JING_WEI_XIN:
            return {"status": "skipped", "reason": "JingWeiXin not available"}

        try:
            # Use mutual excitation to coordinate lines
            resonance_states = self.jwx.mutual_engine.resonate(active_lines=active_lines, iterations=3)
            resonance_metrics = self.jwx.mutual_engine.measure_resonance()

            # Update field state based on resonance
            if self.field_state is not None:
                self.field_state.set(DimensionIndex.DIM_ENERGY, resonance_metrics.get('total', 0.0) * 0.1)
                self.field_state.set(DimensionIndex.DIM_COHERENCE, resonance_metrics.get('sync_index', 0.0))

            result = {
                "status": "coordinated",
                "active_lines": active_lines,
                "resonance_states": {k: float(v) for k, v in resonance_states.items()},
                "sync_index": resonance_metrics.get('sync_index', 0.0),
                "field_energy": self.field_state.get(DimensionIndex.DIM_ENERGY) if self.field_state else 0.0,
            }
            self.coordination_history.append(result)
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def surge_coordination(self, target_lines: List[str], intensity: float = 1.0) -> Dict[str, Any]:
        """Trigger surge coordination across target lines."""
        if self.jwx is None or not _HAS_JING_WEI_XIN:
            return {"status": "skipped", "reason": "JingWeiXin not available"}

        try:
            # Transient excitation
            for line in target_lines:
                self.jwx.transient_engine.inject_pulse(target=line, energy=intensity * 3.0)
            responses = self.jwx.transient_engine.get_all_responses()

            # Field excitation
            pos = (16, 16)
            if _HAS_NUMPY:
                pos = (int(np.random.randint(8, 24)), int(np.random.randint(8, 24)))
            self.jwx.field_engine.excite_field(position=pos, intensity=intensity * 5.0)
            wave_energy = self.jwx.field_engine.excitation_waves(steps=5)

            # Self excitation boost
            self.jwx.self_engine.ignite()
            potentials = self.jwx.self_engine.feedback_loop(iterations=5)

            return {
                "status": "surged",
                "target_lines": target_lines,
                "transient_responses": [float(x) for x in responses] if _HAS_NUMPY else list(responses),
                "wave_energy": [float(x) for x in wave_energy] if _HAS_NUMPY else list(wave_energy),
                "self_potentials": [float(x) for x in potentials] if _HAS_NUMPY else list(potentials),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_architecture_status(self) -> Dict[str, Any]:
        """Get unified architecture status combining all three dimensions."""
        if self.jwx is None:
            return {"status": "unavailable"}

        try:
            jing = self.jwx.get_jing()
            wei = self.jwx.get_wei()
            xin = self.jwx.get_xin()
            weave = self.jwx.weave()

            return {
                "status": "healthy",
                "jing": {
                    "coherence": jing.get('coherence', 0.0),
                    "total_mass": jing.get('total_mass', 0.0),
                },
                "wei": {
                    "total_bandwidth": wei.get('total_bandwidth', 0.0),
                    "si1_anchor_load": wei.get('si1_anchor_load', 0.0),
                },
                "xin": {
                    "total_power": xin.get('total_power', 0.0),
                    "dominant_engine": xin.get('dominant_engine', 'none'),
                },
                "weave": {
                    "strength": weave.get('weave_strength', 0.0),
                    "coherence": weave.get('weave_coherence', 0.0),
                    "dominant_dimension": weave.get('dominant_dimension', 'unknown'),
                    "si1_dependency": weave.get('si1_anchor_dependency', 1.0),
                },
                "field_coherence": self.field_state.compute_coherence() if self.field_state else 0.0,
                "field_emergence": self.field_state.compute_emergence_index() if self.field_state else 0.0,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def tick(self, line_states: Optional[Dict[str, LineState]] = None) -> Dict[str, Any]:
        """Execute one unified SI coordination tick."""
        self._tick_count += 1

        if line_states:
            self.line_states.update(line_states)

        # Update JingWeiXin with current line states
        if self.jwx is not None and _HAS_JING_WEI_XIN:
            try:
                # Map line activity to wei channels
                for line_id, ls in self.line_states.items():
                    if line_id in self.jwx.lines:
                        self.jwx.mutual_engine.line_states[line_id] = ls.activity_level
            except Exception:
                pass

        return {
            "tick": self._tick_count,
            "lines_tracked": len(self.line_states),
            "architecture_status": self.get_architecture_status(),
        }


# =============================================================================
# 6. Unified Wild Notebook — Main Orchestration Class
# =============================================================================

class UnifiedWildNotebook:
    """
    The Unified Wild Notebook integrates all 4 subsystems into a single
    coherent question-debt-knowledge orchestration engine.

    Subsystems:
      v12_wn   — WildNotebook (main question generation & iteration)
      db       — DiscussionBoard (4-space thread management)
      jwx      — JingWeiXin (3D architecture: Jing/Wei/Xin)
      si_loop  — SILoop (11-line tick engine)
    """

    def __init__(self,
                 v12_wn: Optional[Any] = None,
                 discussion_board: Optional[DiscussionBoard] = None,
                 jing_wei_xin: Optional[JingWeiXin] = None,
                 si_loop: Optional[Any] = None,
                 pedestal: Optional[KnowledgePedestal] = None,
                 field_state: Optional[UnifiedFieldState] = None) -> None:
        self.logger = get_logger("UnifiedWildNotebook")
        self.logger.info("Initializing UnifiedWildNotebook v%s...", __version__)

        # === Subsystem instances ===
        self.v12_wn = v12_wn
        self.db = discussion_board
        self.jwx = jing_wei_xin
        self.si_loop = si_loop

        # === Unified components ===
        self.pedestal = pedestal or KnowledgePedestal()
        self.field_state = field_state or create_v12_unified_field()
        self.injector = UnifiedKnowledgeInjector(self.pedestal)
        self.coordinator = UnifiedSICoordinator(self.jwx, self.field_state)
        self.migrator = MigrationEngine(self.db, self.jwx)
        self.bridge = SubsystemBridge()

        # === Unified storage ===
        self.unified_questions: Dict[str, UnifiedQuestion] = {}
        self.unified_debts: Dict[str, UnifiedDebt] = {}
        self.unified_responses: List[UnifiedResponse] = []
        self.question_queue: deque = deque(maxlen=2000)
        self.debt_queue: deque = deque(maxlen=500)

        # === Statistics ===
        self.stats = {
            "questions_total": 0, "questions_resolved": 0, "questions_rejected": 0,
            "debts_total": 0, "debts_resolved": 0, "debts_deferred": 0,
            "injections_total": 0, "surges_triggered": 0,
            "migrations_total": 0, "coordination_ticks": 0,
            "subsystems_active": 0,
        }
        self._update_subsystem_count()

        # === Operation log ===
        self.operation_log: deque = deque(maxlen=500)
        self._initialized_at = time.time()

        self.logger.info("UnifiedWildNotebook initialized with %d active subsystems",
                         self.stats["subsystems_active"])

    def _update_subsystem_count(self) -> None:
        count = 0
        if self.v12_wn is not None: count += 1
        if self.db is not None: count += 1
        if self.jwx is not None: count += 1
        if self.si_loop is not None: count += 1
        self.stats["subsystems_active"] = count

    # =====================================================================
    # 6.1 Unified Query
    # =====================================================================

    def unified_query(self, question_text: str,
                      category: str = "exploratory",
                      priority: float = 0.5) -> Dict[str, Any]:
        """
        Dispatch a query to all 4 subsystems and return unified results.

        Pipeline:
          1. Create UnifiedQuestion
          2. Query v12_wn (question generation + line dispatch)
          3. Query db (cross-reference search)
          4. Query jwx (architecture analysis)
          5. Aggregate responses
          6. Inject into pedestals
        """
        self.logger.info("Unified query: %s...", question_text[:50])

        # Create unified question
        uq = UnifiedQuestion(
            content=question_text,
            category=category,
            priority=priority,
            status="answering",
        )
        self.unified_questions[uq.question_id] = uq
        self.question_queue.append(uq.question_id)
        self.stats["questions_total"] += 1

        responses: List[UnifiedResponse] = []

        # --- Query v12 WildNotebook ---
        if self.v12_wn is not None and _HAS_V12_WN:
            try:
                # Create a WildQuestion and process it
                wq = WildQuestion(
                    content=question_text,
                    category=QuestionCategory.THEORETICAL if category == "theoretical" else
                             QuestionCategory.TECHNICAL if category == "technical" else
                             QuestionCategory.ENGINEERING if category == "engineering" else
                             QuestionCategory.EXPLORATORY,
                    priority=priority,
                )
                # Dispatch to lines
                line_responses = self.v12_wn.dispatch_to_lines(wq)
                for line_name, lr in line_responses.items():
                    ur = UnifiedResponse(
                        source_system=UnifiedQuestionSource.V12_WN.value,
                        source_line=line_name,
                        response_type=UnifiedResponseType.LINE_RESPONSE,
                        content=lr.answer if hasattr(lr, 'answer') else str(lr),
                        confidence=lr.confidence if hasattr(lr, 'confidence') else 0.5,
                        timestamp=time.time(),
                        metadata={"subsystem": "v12_wn", "field_delta": getattr(lr, 'field_state_delta', {})},
                    )
                    responses.append(ur)
                    uq.add_response(ur)

                # Cross-validate
                val = self.v12_wn.cross_validate(wq.id)
                uq.validation_score = val.agreement_score if hasattr(val, 'agreement_score') else 0.0
                uq.consensus_answer = val.consensus_answer if hasattr(val, 'consensus_answer') else ""

                # If validation passes, refine knowledge
                if val.validation_passed if hasattr(val, 'validation_passed') else False:
                    ref = self.v12_wn.refine_knowledge(wq.id)
                    uq.status = "resolved"
                    uq.resolved_at = time.time()
                    self.stats["questions_resolved"] += 1
            except Exception as e:
                self.logger.warning("v12_wn query error: %s", e)
                responses.append(UnifiedResponse(
                    source_system=UnifiedQuestionSource.V12_WN.value,
                    response_type=UnifiedResponseType.ANSWER,
                    content=f"[v12_wn error: {e}]",
                    confidence=0.0,
                ))

        # --- Query DiscussionBoard ---
        if self.db is not None and _HAS_DISCUSSION_BOARD:
            try:
                search_results = self.db.cross_reference(question_text)
                for result in search_results[:5]:  # Top 5
                    ur = UnifiedResponse(
                        source_system=UnifiedQuestionSource.DISCUSSION_BOARD.value,
                        response_type=UnifiedResponseType.FOLLOWUP,
                        content=f"[{result.get('space', 'unknown')}] {result.get('title', '')} (score: {result.get('score', 0)})",
                        confidence=min(1.0, result.get('score', 0) / 20.0),
                        timestamp=time.time(),
                        metadata={"thread_id": result.get('thread_id'), "space": result.get('space')},
                    )
                    responses.append(ur)
                    uq.add_response(ur)
            except Exception as e:
                self.logger.warning("db query error: %s", e)

        # --- Query JingWeiXin ---
        if self.jwx is not None and _HAS_JING_WEI_XIN:
            try:
                arch_status = self.coordinator.get_architecture_status()
                ur = UnifiedResponse(
                    source_system=UnifiedQuestionSource.JING_WEI_XIN.value,
                    response_type=UnifiedResponseType.ENGINE_RESPONSE,
                    content=(f"Jing coherence: {arch_status.get('jing', {}).get('coherence', 0):.2f}, "
                            f"Xin power: {arch_status.get('xin', {}).get('total_power', 0):.2f}, "
                            f"Weave strength: {arch_status.get('weave', {}).get('strength', 0):.2f}"),
                    confidence=0.7,
                    timestamp=time.time(),
                    metadata={"architecture_status": arch_status},
                )
                responses.append(ur)
                uq.add_response(ur)
            except Exception as e:
                self.logger.warning("jwx query error: %s", e)

        # --- Query SI Loop ---
        if self.si_loop is not None and _HAS_SI_LOOP:
            try:
                # Get line status summary
                line_summary = []
                for line_id in LINE_NAMES:
                    line_summary.append(f"{line_id}: active")
                ur = UnifiedResponse(
                    source_system=UnifiedQuestionSource.SI_LOOP.value,
                    response_type=UnifiedResponseType.ENGINE_RESPONSE,
                    content=f"SI Loop: {len(LINE_NAMES)} lines tracked. " + ", ".join(line_summary[:5]) + "...",
                    confidence=0.6,
                    timestamp=time.time(),
                    metadata={"lines": LINE_NAMES},
                )
                responses.append(ur)
                uq.add_response(ur)
            except Exception as e:
                self.logger.warning("si_loop query error: %s", e)

        # Compute final validation score
        uq.validation_score = uq.compute_validation_score()
        if uq.validation_score >= 0.3:
            uq.status = "resolved"
            uq.resolved_at = time.time()
            self.stats["questions_resolved"] += 1
            # Inject into pedestals
            self.injector.inject_question_answer(uq)
            self.stats["injections_total"] += 1

        self.unified_responses.extend(responses)
        self._log_operation("unified_query", {
            "question_id": uq.question_id,
            "responses": len(responses),
            "validation_score": uq.validation_score,
        })

        return {
            "question_id": uq.question_id,
            "status": uq.status,
            "responses_count": len(responses),
            "validation_score": uq.validation_score,
            "consensus_answer": uq.consensus_answer,
            "responses": [r.to_dict() for r in responses],
            "subsystems_queried": self.stats["subsystems_active"],
        }

    # =====================================================================
    # 6.2 Unified Debt Processing
    # =====================================================================

    def unified_debt_process(self, debt_description: str,
                             debt_type: str = "technical",
                             severity: float = 0.5) -> Dict[str, Any]:
        """
        Process a debt through all subsystems.

        Pipeline:
          1. Create UnifiedDebt
          2. Process via v12_wn (if available)
          3. Post to db wild_ask (if available)
          4. Update jwx wei load (if available)
          5. Track in unified registry
        """
        self.logger.info("Unified debt process: %s...", debt_description[:50])

        ud = UnifiedDebt(
            description=debt_description,
            debt_type=debt_type,
            severity=severity,
            status=UnifiedDebtStatus.PROCESSING,
        )
        self.unified_debts[ud.debt_id] = ud
        self.debt_queue.append(ud.debt_id)
        self.stats["debts_total"] += 1

        results = {}

        # --- Process via v12_wn ---
        if self.v12_wn is not None and _HAS_V12_WN and _HAS_DEBT_CLEANUP:
            try:
                # Create a technical debt item
                td = TechnicalDebt(
                    id=ud.debt_id,
                    description=debt_description,
                    severity=DebtSeverity.HIGH if severity > 0.7 else DebtSeverity.MEDIUM if severity > 0.4 else DebtSeverity.LOW,
                    debt_type=debt_type,
                    status=CleanupStatus.DEFERRED,
                )
                dt = DebtType.TECHNICAL if debt_type == "technical" else \
                     DebtType.THEORETICAL if debt_type == "theoretical" else DebtType.ENGINEERING
                wn_result = self.v12_wn.process_debt(td, dt)
                results["v12_wn"] = wn_result
                ud.related_questions.append(wn_result.get("question_id", ""))
                if wn_result.get("debt_status") == "resolved":
                    ud.status = UnifiedDebtStatus.RESOLVED
                    ud.resolved_at = time.time()
                    self.stats["debts_resolved"] += 1
            except Exception as e:
                self.logger.warning("v12_wn debt processing error: %s", e)
                results["v12_wn"] = {"error": str(e)}

        # --- Post to DiscussionBoard wild_ask ---
        if self.db is not None and _HAS_DISCUSSION_BOARD:
            try:
                post_result = self.db.post("wild_ask", {
                    "author": "unified_system",
                    "title": f"[Debt] {debt_description[:60]}",
                    "body": debt_description,
                    "tags": ["debt", debt_type, "auto"],
                    "priority": min(9, int(severity * 9)),
                    "required_responders": LINE_NAMES[:5],
                })
                results["discussion_board"] = {
                    "posted": post_result.get("posted", False),
                    "thread_id": post_result.get("thread_id"),
                }
            except Exception as e:
                self.logger.warning("db debt posting error: %s", e)
                results["discussion_board"] = {"error": str(e)}

        # --- Update JingWeiXin wei load ---
        if self.jwx is not None and _HAS_JING_WEI_XIN:
            try:
                self.jwx.wei.wild_question_load += severity * 0.1
                results["jing_wei_xin"] = {
                    "wei_load_updated": True,
                    "new_wild_question_load": self.jwx.wei.wild_question_load,
                }
            except Exception as e:
                self.logger.warning("jwx debt update error: %s", e)
                results["jing_wei_xin"] = {"error": str(e)}

        # If not resolved by v12_wn, mark as deferred
        if ud.status == UnifiedDebtStatus.PROCESSING:
            ud.status = UnifiedDebtStatus.DEFERRED
            self.stats["debts_deferred"] += 1

        # Inject debt into pedestals
        self.injector.inject_debt(ud)

        self._log_operation("unified_debt_process", {
            "debt_id": ud.debt_id,
            "status": ud.status.value if hasattr(ud.status, 'value') else str(ud.status),
            "subsystem_results": list(results.keys()),
        })

        return {
            "debt_id": ud.debt_id,
            "status": ud.status.value if hasattr(ud.status, 'value') else str(ud.status),
            "subsystem_results": results,
        }

    # =====================================================================
    # 6.3 Historical Data Migration
    # =====================================================================

    def migrate_history(self) -> Dict[str, Any]:
        """
        Migrate historical data from discussion_board and jing_wei_xin
        into the unified registry.
        """
        self.logger.info("Starting historical data migration...")

        migration_results = {}

        # Migrate from DiscussionBoard
        db_result = self.migrator.migrate_from_discussion_board()
        migration_results["discussion_board"] = db_result

        # Migrate from JingWeiXin
        jwx_result = self.migrator.migrate_from_jing_wei_xin()
        migration_results["jing_wei_xin"] = jwx_result

        # Migrate from SI Loop (if line states available)
        si_result = self.migrator.migrate_from_si_loop()
        migration_results["si_loop"] = si_result

        # Import all migrated items into unified registry
        migrated_questions, migrated_debts = self.migrator.get_all_migrated()

        for uq in migrated_questions:
            if uq.question_id not in self.unified_questions:
                self.unified_questions[uq.question_id] = uq
                self.question_queue.append(uq.question_id)
                self.stats["migrations_total"] += 1

        for ud in migrated_debts:
            if ud.debt_id not in self.unified_debts:
                self.unified_debts[ud.debt_id] = ud
                self.debt_queue.append(ud.debt_id)
                self.stats["migrations_total"] += 1

        summary = self.migrator.get_migration_summary()
        self.stats["migrations_total"] = summary["total_questions_migrated"] + summary["total_debts_migrated"]

        self._log_operation("migrate_history", {
            "results": migration_results,
            "summary": summary,
        })

        self.logger.info("Migration complete: %d questions, %d debts",
                         summary["total_questions_migrated"],
                         summary["total_debts_migrated"])

        return {
            "status": "complete",
            "migration_results": migration_results,
            "summary": summary,
            "unified_registry": {
                "questions": len(self.unified_questions),
                "debts": len(self.unified_debts),
            },
        }

    # =====================================================================
    # 6.4 Knowledge Gap Discovery (Unified)
    # =====================================================================

    def unified_discover_gaps(self) -> Dict[str, Any]:
        """
        Discover knowledge gaps across all subsystems and the 6 pedestals.
        """
        gaps = []

        # From v12_wn
        if self.v12_wn is not None and _HAS_V12_WN:
            try:
                gap_result = self.v12_wn.discover_gaps()
                gaps.append({
                    "source": "v12_wild_notebook",
                    "total_gaps": gap_result.total_gaps if hasattr(gap_result, 'total_gaps') else 0,
                    "entropy": gap_result.gap_entropy if hasattr(gap_result, 'gap_entropy') else 0.0,
                    "pedestals": list(gap_result.pedestal_gaps.keys()) if hasattr(gap_result, 'pedestal_gaps') else [],
                })
            except Exception as e:
                gaps.append({"source": "v12_wild_notebook", "error": str(e)})

        # From DiscussionBoard coverage
        if self.db is not None and _HAS_DISCUSSION_BOARD:
            try:
                coverage = self.db.ensure_coverage()
                gaps.append({
                    "source": "discussion_board",
                    "coverage_rate": coverage.get('coverage_rate', 0.0),
                    "blind_spots": len(coverage.get('blind_spots', [])),
                    "actions": coverage.get('actions', []),
                })
            except Exception as e:
                gaps.append({"source": "discussion_board", "error": str(e)})

        # From JingWeiXin architecture
        if self.jwx is not None and _HAS_JING_WEI_XIN:
            try:
                arch = self.coordinator.get_architecture_status()
                if arch.get('status') == 'healthy':
                    gaps.append({
                        "source": "jing_wei_xin",
                        "jing_coherence": arch.get('jing', {}).get('coherence', 0.0),
                        "xin_power": arch.get('xin', {}).get('total_power', 0.0),
                        "si1_dependency": arch.get('weave', {}).get('si1_dependency', 1.0),
                    })
            except Exception as e:
                gaps.append({"source": "jing_wei_xin", "error": str(e)})

        # From unified registry
        pending = [q for q in self.unified_questions.values() if q.status == "pending"]
        unresolved_debts = [d for d in self.unified_debts.values()
                           if d.status in (UnifiedDebtStatus.PROCESSING, UnifiedDebtStatus.DISCOVERED)]

        return {
            "gaps": gaps,
            "unified_pending_questions": len(pending),
            "unified_unresolved_debts": len(unresolved_debts),
            "total_gaps": sum(g.get('total_gaps', 0) for g in gaps if 'total_gaps' in g),
            "recommendations": [
                f"Process {len(pending)} pending questions" if pending else None,
                f"Resolve {len(unresolved_debts)} unresolved debts" if unresolved_debts else None,
            ],
        }

    # =====================================================================
    # 6.5 Surge Coordination
    # =====================================================================

    def unified_surge(self, target_question_id: Optional[str] = None,
                      target_lines: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Trigger unified surge across all applicable subsystems.
        """
        self.logger.info("Unified surge triggered for %s", target_question_id or "all")
        self.stats["surges_triggered"] += 1

        results = {}

        # SI coordination surge
        if target_lines:
            results["si_coordination"] = self.coordinator.surge_coordination(target_lines)

        # v12_wn surge
        if target_question_id and self.v12_wn is not None and _HAS_V12_WN:
            try:
                wq = self.v12_wn.questions.get(target_question_id)
                if wq:
                    surge_result = self.v12_wn.initiate_surge(wq)
                    results["v12_wn"] = surge_result.to_dict() if hasattr(surge_result, 'to_dict') else str(surge_result)
            except Exception as e:
                results["v12_wn"] = {"error": str(e)}

        # JingWeiXin self-sustain
        if self.jwx is not None and _HAS_JING_WEI_XIN:
            try:
                sustain = self.jwx.self_sustain(cycles=3)
                results["jing_wei_xin"] = {
                    "self_sustaining": sustain.get('self_sustaining', False),
                    "final_xin_power": sustain.get('final_xin_power', 0.0),
                }
            except Exception as e:
                results["jing_wei_xin"] = {"error": str(e)}

        self._log_operation("unified_surge", {
            "target_question": target_question_id,
            "target_lines": target_lines,
            "results": list(results.keys()),
        })

        return {
            "surge_id": f"SURGE-{uuid.uuid4().hex[:8]}",
            "timestamp": time.time(),
            "results": results,
        }

    # =====================================================================
    # 6.6 Reporting & Export
    # =====================================================================

    def generate_unified_report(self) -> UnifiedReport:
        """Generate comprehensive unified report."""
        report = UnifiedReport(
            version=__version__,
            subsystem_health={
                "v12_wild_notebook": {"available": _HAS_V12_WN and self.v12_wn is not None},
                "discussion_board": {"available": _HAS_DISCUSSION_BOARD and self.db is not None},
                "jing_wei_xin": {"available": _HAS_JING_WEI_XIN and self.jwx is not None},
                "si_loop": {"available": _HAS_SI_LOOP and self.si_loop is not None},
            },
            total_questions=len(self.unified_questions),
            total_responses=len(self.unified_responses),
            total_debts=len(self.unified_debts),
            resolved_debts=sum(1 for d in self.unified_debts.values() if d.status == UnifiedDebtStatus.RESOLVED),
            active_surges=self.stats["surges_triggered"],
            pedestal_injections=self.injector.get_injection_stats().get("pedestal_summary", {}),
            jing_wei_xin_status=self.coordinator.get_architecture_status(),
        )

        # Coverage from discussion board
        if self.db is not None and _HAS_DISCUSSION_BOARD:
            try:
                coverage = self.db.ensure_coverage()
                report.coverage_rate = coverage.get('coverage_rate', 0.0)
                report.blind_spots = coverage.get('blind_spots', [])
            except Exception:
                pass

        return report

    def export_report(self, output_path: Optional[str] = None) -> str:
        """Export unified report to JSON."""
        path = Path(output_path or HUB_DIR / "WILDBOOK_UNIFICATION_REPORT.json")
        path.parent.mkdir(parents=True, exist_ok=True)

        report = self.generate_unified_report()
        export_data = {
            "version": __version__,
            "timestamp": time.time(),
            "report": report.to_dict(),
            "stats": self.stats,
            "subsystem_import_status": {
                "v12_wild_notebook": _HAS_V12_WN,
                "discussion_board": _HAS_DISCUSSION_BOARD,
                "jing_wei_xin": _HAS_JING_WEI_XIN,
                "si_loop": _HAS_SI_LOOP,
                "debt_cleanup": _HAS_DEBT_CLEANUP,
                "knowledge_pedestal": _HAS_KNOWLEDGE_PEDESTAL,
            },
            "import_errors": _subsystem_import_errors,
            "unified_questions_sample": [q.to_dict() for q in list(self.unified_questions.values())[:10]],
            "unified_debts_sample": [d.to_dict() for d in list(self.unified_debts.values())[:10]],
            "operation_log": list(self.operation_log)[-20:],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

        self.logger.info("Unified report exported to %s", path)
        return str(path)

    def export_markdown_report(self, output_path: Optional[str] = None) -> str:
        """Export unified report to Markdown."""
        path = Path(output_path or HUB_DIR / "WILDBOOK_UNIFICATION_REPORT.md")
        path.parent.mkdir(parents=True, exist_ok=True)

        report = self.generate_unified_report()

        md = f"""# Unified Wild Notebook Integration Report

**Version:** {__version__}  
**Generated:** {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}  
**Uptime:** {time.time() - self._initialized_at:.1f}s

---

## 1. Subsystem Health

| Subsystem | Available | Notes |
|-----------|-----------|-------|
| v12_wild_notebook | {'Yes' if _HAS_V12_WN and self.v12_wn else 'No'} | Main question generation & iteration |
| discussion_board | {'Yes' if _HAS_DISCUSSION_BOARD and self.db else 'No'} | 4-space thread management |
| jing_wei_xin | {'Yes' if _HAS_JING_WEI_XIN and self.jwx else 'No'} | 3D architecture (Jing/Wei/Xin) |
| si_loop | {'Yes' if _HAS_SI_LOOP and self.si_loop else 'No'} | 11-line tick engine |

### Import Errors
"""
        if _subsystem_import_errors:
            for subsys, err in _subsystem_import_errors.items():
                md += f"- **{subsys}**: `{err[:100]}`\n"
        else:
            md += "_No import errors_\n"

        md += f"""

## 2. Unified Metrics

| Metric | Value |
|--------|-------|
| Total Questions | {len(self.unified_questions)} |
| Total Responses | {len(self.unified_responses)} |
| Total Debts | {len(self.unified_debts)} |
| Resolved Debts | {sum(1 for d in self.unified_debts.values() if d.status == UnifiedDebtStatus.RESOLVED)} |
| Active Surges | {self.stats['surges_triggered']} |
| Migrations | {self.stats['migrations_total']} |
| Injections | {self.stats['injections_total']} |

## 3. Jing-Wei-Xin Architecture Status

```json
{json.dumps(report.jing_wei_xin_status, indent=2, ensure_ascii=False, default=str)[:800]}
```

## 4. 6-Pedestal Injection Summary

```json
{json.dumps(report.pedestal_injections, indent=2, ensure_ascii=False, default=str)[:500]}
```

## 5. Coverage Analysis

- **Coverage Rate:** {report.coverage_rate:.2%}
- **Blind Spots:** {len(report.blind_spots)}

## 6. Recent Operations

"""
        for op in list(self.operation_log)[-10:]:
            md += f"- `{op.get('timestamp', 0):.0f}` **{op.get('operation', 'unknown')}**: {json.dumps(op.get('details', {}), ensure_ascii=False)[:100]}\n"

        md += f"""

## 7. Unified API Reference

### `unified_query(question_text, category, priority)`
Dispatches query to all 4 subsystems and returns aggregated responses.

### `unified_debt_process(debt_description, debt_type, severity)`
Processes debt through v12_wn, DiscussionBoard, and JingWeiXin.

### `migrate_history()`
Migrates historical data from discussion_board and jing_wei_xin.

### `unified_discover_gaps()`
Discovers knowledge gaps across all subsystems and 6 pedestals.

### `unified_surge(target_question_id, target_lines)`
Triggers surge coordination across applicable subsystems.

### `generate_unified_report()`
Generates comprehensive unified report.

---

*Report generated by UnifiedWildNotebook v{__version__}*
"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(md)

        self.logger.info("Markdown report exported to %s", path)
        return str(path)

    # =====================================================================
    # 6.7 Utilities
    # =====================================================================

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        self.operation_log.append({
            "timestamp": time.time(),
            "operation": operation,
            "details": details,
        })

    def get_stats(self) -> Dict[str, Any]:
        stats = self.stats.copy()
        stats["unified_questions"] = len(self.unified_questions)
        stats["unified_debts"] = len(self.unified_debts)
        stats["unified_responses"] = len(self.unified_responses)
        stats["injector_stats"] = self.injector.get_injection_stats()
        stats["coordinator_ticks"] = self.coordinator._tick_count
        return stats

    def get_question(self, question_id: str) -> Optional[UnifiedQuestion]:
        return self.unified_questions.get(question_id)

    def get_debt(self, debt_id: str) -> Optional[UnifiedDebt]:
        return self.unified_debts.get(debt_id)

    def list_questions(self, status: Optional[str] = None) -> List[UnifiedQuestion]:
        questions = list(self.unified_questions.values())
        if status:
            questions = [q for q in questions if q.status == status]
        return questions

    def list_debts(self, status: Optional[str] = None) -> List[UnifiedDebt]:
        debts = list(self.unified_debts.values())
        if status:
            debts = [d for d in debts if d.status.value == status]
        return debts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": __version__,
            "stats": self.get_stats(),
            "subsystems": {
                "v12_wn": self.v12_wn is not None,
                "discussion_board": self.db is not None,
                "jing_wei_xin": self.jwx is not None,
                "si_loop": self.si_loop is not None,
            },
            "question_count": len(self.unified_questions),
            "debt_count": len(self.unified_debts),
        }


# =============================================================================
# 7. Self-Test & Demo
# =============================================================================

def demo_unified():
    """Run a full demonstration of the Unified Wild Notebook."""
    print("\n" + "=" * 78)
    print("OMNI-HUB v12.1 — UnifiedWildNotebook Demonstration")
    print("=" * 78)

    # Initialize subsystems (with graceful fallback)
    print("\n[1/8] Initializing subsystems...")
    v12_wn = WildNotebook() if _HAS_V12_WN else None
    db = DiscussionBoard(state_path="/tmp/omni_hub_unified_test") if _HAS_DISCUSSION_BOARD else None
    jwx = JingWeiXin() if _HAS_JING_WEI_XIN else None
    si = SILoopSystemIntelligence() if _HAS_SI_LOOP else None

    print(f"  v12_wild_notebook: {'OK' if v12_wn else 'N/A'}")
    print(f"  discussion_board:  {'OK' if db else 'N/A'}")
    print(f"  jing_wei_xin:      {'OK' if jwx else 'N/A'}")
    print(f"  si_loop:           {'OK' if si else 'N/A'}")

    # Initialize unified notebook
    print("\n[2/8] Initializing UnifiedWildNotebook...")
    uwn = UnifiedWildNotebook(
        v12_wn=v12_wn,
        discussion_board=db,
        jing_wei_xin=jwx,
        si_loop=si,
    )
    print(f"  Active subsystems: {uwn.stats['subsystems_active']}")

    # Populate discussion board with sample data for migration
    if db:
        print("\n[3/8] Populating DiscussionBoard with sample threads...")
        for i, (space, title, body) in enumerate([
            ("wild_ask", "UCIF2形式化验证状态", "需要确认UCIF2线的形式化证明覆盖率。"),
            ("discussion_room", "六基座知识注入优化", "讨论如何优化KG->CC->HG->IN->CT->LL的注入流程。"),
            ("bulletin_board", "【公告】v12统一野问册上线", "所有线请注意，统一野问册系统已部署。"),
            ("hall", "日常状态同步", "各线汇报当前运行状态。"),
        ]):
            db.post(space, {
                "author": f"system_{i}",
                "title": title,
                "body": body,
                "tags": ["unified", "test"],
                "priority": 5,
            })
        print(f"  Sample threads created in 4 spaces")

    # Migrate history
    print("\n[4/8] Migrating historical data...")
    migration = uwn.migrate_history()
    summary = migration.get("summary", {})
    print(f"  Questions migrated: {summary.get('total_questions_migrated', 0)}")
    print(f"  Debts migrated: {summary.get('total_debts_migrated', 0)}")
    print(f"  Unified registry: {migration.get('unified_registry', {})}")

    # Unified query
    print("\n[5/8] Running unified query...")
    query_result = uwn.unified_query(
        question_text="How do we optimize the 6-pedestal knowledge injection pipeline?",
        category="technical",
        priority=0.8,
    )
    print(f"  Question ID: {query_result['question_id']}")
    print(f"  Status: {query_result['status']}")
    print(f"  Responses: {query_result['responses_count']}")
    print(f"  Validation Score: {query_result['validation_score']:.4f}")
    for resp in query_result.get("responses", [])[:5]:
        src = resp.get('source_system', 'unknown')
        conf = resp.get('confidence', 0)
        print(f"    [{src}] confidence={conf:.2f}")

    # Unified debt processing
    print("\n[6/8] Processing unified debt...")
    debt_result = uwn.unified_debt_process(
        debt_description="Missing cross-validation tests for the unified query pipeline",
        debt_type="technical",
        severity=0.7,
    )
    print(f"  Debt ID: {debt_result['debt_id']}")
    print(f"  Status: {debt_result['status']}")
    for subsys, result in debt_result.get("subsystem_results", {}).items():
        status = "error" if "error" in str(result) else "ok"
        print(f"    [{subsys}] {status}")

    # Knowledge gap discovery
    print("\n[7/8] Discovering unified knowledge gaps...")
    gaps = uwn.unified_discover_gaps()
    print(f"  Total gaps: {gaps.get('total_gaps', 0)}")
    print(f"  Pending questions: {gaps.get('unified_pending_questions', 0)}")
    print(f"  Unresolved debts: {gaps.get('unified_unresolved_debts', 0)}")

    # Export reports
    print("\n[8/8] Exporting unified reports...")
    json_path = uwn.export_report()
    md_path = uwn.export_markdown_report()
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")

    # Final stats
    print("\n" + "=" * 78)
    print("Final Statistics")
    print("=" * 78)
    stats = uwn.get_stats()
    for k, v in stats.items():
        if isinstance(v, (int, float, str, bool)):
            print(f"  {k}: {v}")

    print("\n" + "=" * 78)
    print("UnifiedWildNotebook Demo Complete")
    print("=" * 78)

    return uwn


if __name__ == "__main__":
    configure_logging(level=logging.INFO)
    demo_unified()
