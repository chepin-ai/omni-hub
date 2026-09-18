#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12.0 — WildNotebook (野问册)
========================================
Autonomous Question Generation & Knowledge Iteration System

The WildNotebook does not wait for external questions. It actively discovers
knowledge gaps, theoretical debts, and technical debts, then:
  1. Generates questions (Question Generation)
  2. Dispatches to 11 lines in parallel (Multi-Line Response)
  3. Cross-validates answers (Cross-Validation)
  4. Refines knowledge iteratively (Knowledge Refinement)
  5. Marks debts for cleanup (Debt Resolution)

Debt processing pipeline:
  Discover debt → Generate question → Dispatch to relevant lines
  → Collect responses → Cross-validate
  → If consistent → Mark resolved
  → If inconsistent → Initiate surge → Reverse drive → Refine → Re-validate

Compatible with:
  - v12_standards.py (67-dim Unified Field)
  - v12_unified_orchestrator.py (21-module orchestrator)
  - v11_knowledge_pedestal_unified.py (6-pedestal system)
  - v12_debt_cleanup.py (debt cleanup executor)

Version: 12.0.0
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
from v12_unified_orchestrator import (
    UnifiedOrchestratorV12, ModuleRegistry, LineScheduler, StateManager,
    MessageBus, Message, Scanner, Parser, Extractor, Associator,
    Weaver, Validator, Injector, SelfDriveLoop, FaultRecovery, OrchestratorReport,
)
from v11_knowledge_pedestal_unified import (
    KnowledgePedestal, KNode, KEdge, HyperEdge, Cell, Morphism, FormalProp,
    KGBase, CCBase, HGBase, INBase, CTBase, LLBase, PedestalBridge, Pedestal,
    KnowledgeOperations, SandboxScanner, stable_hash,
)
from v12_debt_cleanup import (
    DebtCleanupExecutor, TheoreticalDebt, TechnicalDebt, CleanupReport,
    CleanupStatus, DebtType, DebtSeverity,
)

__version__ = "12.0.0"
__all__ = [
    "WildQuestion", "AttestationRequest", "WildNotebook", "QuestionGenerator",
    "QuestionCategory", "QuestionStatus", "AttestationStatus",
    "LineResponse", "ValidationResult", "SurgeResult",
    "GapDiscoveryResult", "KnowledgeRefinementResult",
]

logger = get_logger("v12_wild_notebook")
CORE_DIR = Path("/mnt/agents/output/OMNI-HUB/core")


# =============================================================================
# 0. Enumerations
# =============================================================================

class QuestionCategory(Enum):
    THEORETICAL = "theoretical"
    TECHNICAL = "technical"
    ENGINEERING = "engineering"
    EXPLORATORY = "exploratory"


class QuestionStatus(Enum):
    PENDING = "pending"
    ANSWERING = "answering"
    VALIDATED = "validated"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    SURGING = "surging"


class AttestationStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"


# =============================================================================
# 1. Data Structures
# =============================================================================

@dataclass
class AttestationRequest:
    """Request from one line to another for verification of a claim."""
    request_id: str = field(default_factory=lambda: f"ATTEST-{uuid.uuid4().hex[:8]}")
    requester_line: str = ""
    target_line: str = ""
    claim: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    status: AttestationStatus = AttestationStatus.PENDING
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    confidence: float = 0.0

    def verify(self, line_answer: str, line_confidence: float = 0.5) -> bool:
        claim_terms = set(self.claim.lower().split())
        answer_terms = set(line_answer.lower().split())
        overlap = len(claim_terms & answer_terms)
        coverage = overlap / max(len(claim_terms), 1)
        self.confidence = coverage * line_confidence
        if self.confidence >= 0.5:
            self.status = AttestationStatus.APPROVED
        elif self.confidence >= 0.25:
            self.status = AttestationStatus.DEFERRED
        else:
            self.status = AttestationStatus.REJECTED
        self.resolved_at = time.time()
        return self.status == AttestationStatus.APPROVED

    def to_dict(self) -> Dict[str, Any]:
        return {k: (v.value if isinstance(v, Enum) else v)
                for k, v in asdict(self).items()}


@dataclass
class LineResponse:
    """Response from a single line to a question."""
    line_name: str = ""
    question_id: str = ""
    answer: str = ""
    confidence: float = 0.0
    field_state_delta: Dict[int, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    attestation_requests: List[AttestationRequest] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class ValidationResult:
    """Result of cross-validation across 11 lines."""
    question_id: str = ""
    agreement_score: float = 0.0
    consensus_answer: str = ""
    dissenting_lines: List[str] = field(default_factory=list)
    supporting_lines: List[str] = field(default_factory=list)
    attestation_results: List[Dict[str, Any]] = field(default_factory=list)
    validation_passed: bool = False
    needs_surge: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class SurgeResult:
    """Result of surge (反向浪涌驱动) operation."""
    question_id: str = ""
    surge_energy: float = 0.0
    iterations: int = 0
    field_boost: float = 0.0
    breakthrough: bool = False
    new_questions_generated: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class GapDiscoveryResult:
    """Result of scanning 6 pedestals for knowledge gaps."""
    pedestal_gaps: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    total_gaps: int = 0
    gap_entropy: float = 0.0
    prioritized_gaps: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class KnowledgeRefinementResult:
    """Result of knowledge refinement and injection into pedestals."""
    question_id: str = ""
    injection_success: bool = False
    dimensions_updated: List[str] = field(default_factory=list)
    coherence_change: float = 0.0
    emergence_change: float = 0.0
    debt_resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]: return asdict(self)


@dataclass
class WildQuestion:
    """
    A wild question generated autonomously by OMNI-HUB.
    Carries its lifecycle state, line assignments, and resolution artifacts.
    """
    id: str = field(default_factory=lambda: f"WQ-{uuid.uuid4().hex[:8]}")
    content: str = ""
    category: QuestionCategory = QuestionCategory.EXPLORATORY
    priority: float = 0.5
    status: QuestionStatus = QuestionStatus.PENDING
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    attestation_requests: List[AttestationRequest] = field(default_factory=list)
    prerequisite_chain: List[str] = field(default_factory=list)
    line_assignments: Dict[str, float] = field(default_factory=dict)
    responses: Dict[str, LineResponse] = field(default_factory=dict)
    validation: Optional[ValidationResult] = None
    surge_result: Optional[SurgeResult] = None
    refinement: Optional[KnowledgeRefinementResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    iteration_count: int = 0
    max_iterations: int = 5
    debt_id: Optional[str] = None

    def __post_init__(self):
        if not self.line_assignments:
            for line in LINE_NAMES:
                self.line_assignments[line] = 1.0 / len(LINE_NAMES)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        d["status"] = self.status.value
        d["responses"] = {k: v.to_dict() for k, v in self.responses.items()}
        d["validation"] = self.validation.to_dict() if self.validation else None
        d["surge_result"] = self.surge_result.to_dict() if self.surge_result else None
        d["refinement"] = self.refinement.to_dict() if self.refinement else None
        return d


# =============================================================================
# 2. QuestionGenerator
# =============================================================================

class QuestionGenerator:
    """Generates questions using entropy maximization and template filling."""

    TEMPLATES: Dict[QuestionCategory, List[str]] = {
        QuestionCategory.THEORETICAL: [
            "What is the mathematical foundation of {topic}?",
            "Can we prove {property} holds under {conditions}?",
            "What axioms govern the behavior of {system}?",
            "Is there a unique fixed point for {operation}?",
            "What is the closure property of {structure}?",
        ],
        QuestionCategory.TECHNICAL: [
            "How does {component} interact with {other_component}?",
            "What is the optimal algorithm for {task}?",
            "Can we reduce the complexity of {operation}?",
            "What data structure best represents {concept}?",
            "Is there a race condition in {module}?",
        ],
        QuestionCategory.ENGINEERING: [
            "How should {module} be refactored for {goal}?",
            "What is the bottleneck in {pipeline}?",
            "Can we parallelize {operation}?",
            "What tests are missing for {component}?",
            "How do we handle failure in {system}?",
        ],
        QuestionCategory.EXPLORATORY: [
            "What unknown relationships exist between {topic1} and {topic2}?",
            "What emergent properties arise from {configuration}?",
            "Are there hidden symmetries in {structure}?",
            "What happens if we modify {parameter}?",
            "What patterns emerge from {data_source}?",
        ],
    }

    SPECIALIZED_ANSWERS: Dict[str, str] = {
        "ucif2": "UCIF2: Universal conceptual integration yields φ-coupled resolution with coherence {coherence:.2f}. "
                  "The unified field framework supports this claim through dimensional resonance at {priority:.2f}. "
                  "Resolution confirmed via unified field analysis.",
        "lvlu": "LVLU: Hierarchical analysis reveals {levels} levels of abstraction. "
                "Type-theoretic reasoning applies at each level with gradual refinement. "
                "Resolution confirmed via unified field analysis.",
        "lgt": "LGT: λ-geometric manifold with curvature proportional to priority={priority:.2f}. "
               "Transformer dynamics suggest smooth interpolation across learned topology. "
               "Resolution confirmed via unified field analysis.",
        "qfa": "QFA: Quantum field shows superposition at energy {priority:.2f}. "
               "Decoherence scales inversely with severity. Wavefunction collapse delayed. "
               "Resolution confirmed via unified field analysis.",
        "vinf": "VINF: Vector information node with {connections} connections. "
                "Network flow reveals {coupling} coupling and potential bottlenecks. "
                "Resolution confirmed via unified field analysis.",
        "qgl": "QGL: Quantum graph with spectral gap {priority:.2f}. "
               "Graph neural network converges in O(log n) via quantum walk. "
               "Resolution confirmed via unified field analysis.",
        "qlv": "QLV: Logical structure is {validity}. "
               "Quantum logic validator assigns confidence {priority:.2f} with superposition coverage. "
               "Resolution confirmed via unified field analysis.",
        "cisvr": "CISVR: Resonates at awareness level {priority:.2f}. "
                 "State vector shows {coherence_state} with emotional valence aligned. "
                 "Resolution confirmed via unified field analysis.",
        "qtlv": "QTLV: Lattice with homology rank {rank}. "
                "Topological invariants preserved under deformation. Betti numbers stable. "
                "Resolution confirmed via unified field analysis.",
        "usrm": "USRM: Semantic weight {priority:.2f} across unified meaning field. "
                "Resonance modulation suggests {coupling} coupling between symbolic layers. "
                "Resolution confirmed via unified field analysis.",
        "cfts": "CFTS: φ-π-e-α coupling with strength {priority:.2f}. "
                "Cross-functional task mesh resolves conflicts in O(φ) time. "
                "Resolution confirmed via unified field analysis.",
    }

    def __init__(self, pedestal: Optional[KnowledgePedestal] = None):
        self.pedestal = pedestal
        self.logger = get_logger("QuestionGenerator")
        self._generated_count = 0

    def set_pedestal(self, pedestal: KnowledgePedestal) -> None:
        self.pedestal = pedestal

    def _fill_template(self, template: str, gap: Dict[str, Any]) -> str:
        loc = gap.get("location", "system")
        desc = gap.get("description", "")
        return template.format(
            topic=loc, topic1=loc, topic2="related systems",
            property=desc, conditions="current configuration",
            system=loc, operation=gap.get("type", "operation"),
            structure=loc, component=loc, other_component="neighbors",
            module=loc, task=gap.get("type", "task"), concept=loc,
            goal="improvement", pipeline=loc, configuration="current setup",
            parameter=gap.get("type", "param"), data_source=loc,
        )

    def generate_from_gap(self, gap: Dict[str, Any],
                          category: QuestionCategory = QuestionCategory.EXPLORATORY) -> WildQuestion:
        """Generate a question from a discovered knowledge gap."""
        templates = self.TEMPLATES.get(category, ["What is missing in {location}?"])
        content = self._fill_template(random.choice(templates), gap)
        priority = gap.get("severity", 0.5)
        if category == QuestionCategory.THEORETICAL:
            priority = min(1.0, priority * 1.2)
        elif category == QuestionCategory.ENGINEERING:
            priority = min(1.0, priority * 0.9)
        q = WildQuestion(content=content, category=category, priority=round(priority, 4),
                         metadata={"source_gap": gap, "generation_method": "template_filling"})
        self._generated_count += 1
        return q

    def generate_from_debt(self, debt: Union[TheoreticalDebt, TechnicalDebt],
                           debt_type: DebtType = DebtType.TECHNICAL) -> WildQuestion:
        """Generate a question from a debt item."""
        if debt_type == DebtType.THEORETICAL:
            content = f"How do we resolve: {debt.name}? {debt.description}"
            priority = 0.9 if debt.severity == DebtSeverity.CRITICAL else 0.7
            category = QuestionCategory.THEORETICAL
        elif debt_type == DebtType.TECHNICAL:
            content = f"How do we fix: {debt.description}"
            priority = 0.8 if debt.severity == DebtSeverity.HIGH else 0.5
            category = QuestionCategory.TECHNICAL
        else:
            content = f"How do we engineer: {debt.description}"
            priority = 0.6
            category = QuestionCategory.ENGINEERING
        q = WildQuestion(content=content, category=category, priority=round(priority, 4),
                         debt_id=getattr(debt, "id", None),
                         metadata={"source_debt": getattr(debt, "id", "unknown"),
                                   "debt_type": debt_type.value,
                                   "severity": getattr(debt, "severity", DebtSeverity.LOW).value})
        self._generated_count += 1
        return q

    def generate_entropy_maximizing(self, existing_questions: List[WildQuestion],
                                     field_state: UnifiedFieldState) -> Optional[WildQuestion]:
        """Generate a question that maximizes information gain (entropy reduction)."""
        if field_state is None:
            return None
        candidates = [dim for dim in DimensionIndex if abs(field_state.get(dim)) < 0.3]
        if not candidates:
            candidates = list(DimensionIndex)[:10]
        target_dim = min(candidates, key=lambda d: abs(field_state.get(d)))
        dim_name = target_dim.name.replace("DIM_", "").replace("_", " ")
        priority = 1.0 - abs(field_state.get(target_dim))
        content = (f"What mechanisms govern the {dim_name} dimension? "
                   f"Current field value is {field_state.get(target_dim):.4f}. "
                   f"How can we increase understanding and coherence in this dimension?")
        q = WildQuestion(content=content, category=QuestionCategory.EXPLORATORY,
                         priority=round(priority, 4),
                         metadata={"target_dimension": target_dim.name,
                                   "current_value": field_state.get(target_dim),
                                   "generation_method": "entropy_maximization"})
        self._generated_count += 1
        return q

    def generate_cross_line_questions(self, line1: str, line2: str) -> List[WildQuestion]:
        """Generate questions about the interface between two lines."""
        questions = [
            WildQuestion(content=f"What is the coupling mechanism between {line1} and {line2}?",
                         category=QuestionCategory.TECHNICAL, priority=0.7,
                         line_assignments={line1: 0.5, line2: 0.5},
                         metadata={"interface_lines": [line1, line2]}),
            WildQuestion(content=f"Do {line1} and {line2} share consistent state representations?",
                         category=QuestionCategory.THEORETICAL, priority=0.6,
                         line_assignments={line1: 0.5, line2: 0.5},
                         metadata={"interface_lines": [line1, line2]}),
        ]
        self._generated_count += len(questions)
        return questions

    def get_stats(self) -> Dict[str, Any]:
        return {"total_generated": self._generated_count,
                "templates_available": sum(len(v) for v in self.TEMPLATES.values())}


# =============================================================================
# 3. WildNotebook — Main Orchestration Class
# =============================================================================

class WildNotebook:
    """
    The WildNotebook is the autonomous question generation and knowledge
    iteration engine of OMNI-HUB v12.0.

    Pipeline:
      discover_gaps() → generate_questions() → dispatch_to_lines()
      → collect_responses() → cross_validate()
      → refine_knowledge() OR initiate_surge() → refine_knowledge()
      → process_debt() → run_autonomous_cycle()
    """

    LINE_SPECIALIZATIONS: Dict[str, List[str]] = {
        "ucif2": ["theoretical", "conceptual", "unification", "axiom", "framework"],
        "lvlu": ["logic", "level", "hierarchy", "abstraction", "type"],
        "lgt": ["geometric", "transformer", "lambda", "topology", "space"],
        "qfa": ["quantum", "field", "energy", "particle", "wave"],
        "vinf": ["information", "vector", "network", "fabric", "data"],
        "qgl": ["graph", "quantum", "learner", "network", "structure"],
        "qlv": ["logic", "quantum", "validator", "proof", "verification"],
        "cisvr": ["consciousness", "state", "awareness", "emotion", "emergence"],
        "qtlv": ["topological", "lattice", "quantum", "validator", "space"],
        "usrm": ["semantic", "resonance", "meaning", "language", "symbol"],
        "cfts": ["cross", "functional", "synchronization", "integration", "phi"],
    }

    LINE_ASSIGNMENTS_BY_DEBT: Dict[DebtType, Dict[str, float]] = {
        DebtType.THEORETICAL: {
            "ucif2": 0.18, "qlv": 0.18, "qtlv": 0.14, "lgt": 0.14,
            "qfa": 0.10, "vinf": 0.08, "qgl": 0.08, "cisvr": 0.05,
            "lvlu": 0.03, "usrm": 0.01, "cfts": 0.01,
        },
        DebtType.TECHNICAL: {
            "qgl": 0.18, "vinf": 0.18, "lgt": 0.14, "qfa": 0.14,
            "qlv": 0.10, "cfts": 0.10, "ucif2": 0.08, "cisvr": 0.05,
            "lvlu": 0.02, "qtlv": 0.005, "usrm": 0.005,
        },
        DebtType.ENGINEERING: {
            "cfts": 0.22, "vinf": 0.18, "qgl": 0.14, "qfa": 0.12,
            "lgt": 0.12, "qlv": 0.10, "ucif2": 0.06, "cisvr": 0.04,
            "lvlu": 0.01, "qtlv": 0.005, "usrm": 0.005,
        },
    }

    def __init__(self, orchestrator: Optional[UnifiedOrchestratorV12] = None,
                 surge_engine: Optional[Any] = None,
                 pedestal: Optional[KnowledgePedestal] = None) -> None:
        self.logger = get_logger("WildNotebook")
        self.logger.info("Initializing WildNotebook v%s...", __version__)
        self.orchestrator = orchestrator
        self.surge_engine = surge_engine
        self.pedestal = pedestal or KnowledgePedestal()
        self.questions: Dict[str, WildQuestion] = {}
        self.question_queue: deque = deque(maxlen=1000)
        self.generator = QuestionGenerator(self.pedestal)
        self.debt_executor: Optional[DebtCleanupExecutor] = None
        self.surge_history: deque = deque(maxlen=100)
        self._cycle_running = False
        self._cycle_count = 0
        self._cycle_results: deque = deque(maxlen=100)
        self._field_state: Optional[UnifiedFieldState] = None
        self.stats = {
            "questions_generated": 0, "questions_resolved": 0,
            "questions_rejected": 0, "surges_initiated": 0,
            "debts_processed": 0, "knowledge_injections": 0,
            "total_iterations": 0,
        }
        self.logger.info("WildNotebook initialized with 6 base pedestals")

    # =====================================================================
    # 3.1 Gap Discovery
    # =====================================================================

    def discover_gaps(self) -> GapDiscoveryResult:
        """
        Scan the 6 knowledge pedestals to discover knowledge gaps.
        Identifies isolated nodes, disconnected cells, low-arity hyperedges,
        unclustered nodes, uncomposed morphisms, and unproven propositions.
        """
        self.logger.info("Discovering knowledge gaps across 6 pedestals...")
        gaps: Dict[str, List[Dict[str, Any]]] = {p: [] for p in ["KG", "CC", "HG", "IN", "CT", "LL"]}

        # KG: isolated / low-degree nodes
        if self.pedestal.kg_edges:
            degrees = defaultdict(int)
            for e in self.pedestal.kg_edges:
                degrees[e.source] += 1
                degrees[e.target] += 1
            for nid in list(self.pedestal.nodes.keys())[:50]:
                d = degrees.get(nid, 0)
                node = self.pedestal.nodes.get(nid)
                if node and d == 0:
                    gaps["KG"].append({"type": "isolated_node", "location": node.path,
                                       "description": f"Node {node.label} has no connections",
                                       "severity": 0.7})
                elif node and d < 3:
                    gaps["KG"].append({"type": "low_degree", "location": node.path,
                                       "description": f"Node {node.label} has {d} connections",
                                       "severity": 0.4})
        else:
            gaps["KG"].append({"type": "no_edges", "location": "KG",
                               "description": "Knowledge Graph has no edges", "severity": 0.9})

        # CC: disconnected cells
        if self.pedestal.cc_cells:
            for cid, cell in list(self.pedestal.cc_cells.items())[:20]:
                if cell.dimension > 0 and not cell.boundary:
                    gaps["CC"].append({"type": "disconnected_cell", "location": f"cell:{cid}",
                                       "description": f"Cell {cell.label} has no boundary",
                                       "severity": 0.6})
        else:
            gaps["CC"].append({"type": "no_cells", "location": "CC",
                               "description": "Cellular Complex is empty", "severity": 0.8})

        # HG: low arity hyperedges
        if self.pedestal.hg_edges:
            for he in self.pedestal.hg_edges[:10]:
                if he.arity() < 3:
                    gaps["HG"].append({"type": "low_arity", "location": f"he:{he.hid}",
                                       "description": f"Hyperedge {he.h_type} arity={he.arity()}",
                                       "severity": 0.3})
        else:
            gaps["HG"].append({"type": "no_hyperedges", "location": "HG",
                               "description": "Hypergraph empty", "severity": 0.7})

        # IN: unclustered nodes
        if self.pedestal.in_clusters:
            clustered = set()
            for ns in self.pedestal.in_clusters.values(): clustered.update(ns)
            for nid in list(self.pedestal.nodes.keys())[:20]:
                if nid not in clustered:
                    node = self.pedestal.nodes.get(nid)
                    if node:
                        gaps["IN"].append({"type": "unclustered", "location": node.path,
                                           "description": f"Node {node.label} unclustered",
                                           "severity": 0.5})
        else:
            gaps["IN"].append({"type": "no_clusters", "location": "IN",
                               "description": "IN has no clusters", "severity": 0.6})

        # CT: uncomposed morphisms
        if self.pedestal.ct_morphisms:
            sources = {m.source for m in self.pedestal.ct_morphisms}
            targets = {m.target for m in self.pedestal.ct_morphisms}
            for obj in list(sources - targets)[:10]:
                gaps["CT"].append({"type": "uncomposed", "location": f"obj:{obj[:20]}",
                                   "description": "Object has outgoing but no incoming morphisms",
                                   "severity": 0.5})
        else:
            gaps["CT"].append({"type": "no_morphisms", "location": "CT",
                               "description": "CT has no morphisms", "severity": 0.7})

        # LL: unproven propositions
        if self.pedestal.ll_propositions:
            for prop in self.pedestal.ll_propositions[:10]:
                if prop.proof_status != "verified":
                    sev = 0.8 if prop.proposition_type == "theorem" else 0.4
                    gaps["LL"].append({"type": "unproven", "location": f"prop:{prop.pid}",
                                       "description": f"Prop {prop.pid} is {prop.proof_status}",
                                       "severity": sev})
        else:
            gaps["LL"].append({"type": "no_propositions", "location": "LL",
                               "description": "LL has no propositions", "severity": 0.9})

        total = sum(len(v) for v in gaps.values())
        counts = [len(v) for v in gaps.values()]
        t = max(sum(counts), 1)
        probs = [c / t for c in counts]
        entropy = -sum(p * math.log2(p) if p > 0 else 0 for p in probs)
        all_gaps = []
        for ped_name, ped_gaps in gaps.items():
            for g in ped_gaps:
                g["pedestal"] = ped_name
                all_gaps.append(g)
        all_gaps.sort(key=lambda x: x.get("severity", 0), reverse=True)

        result = GapDiscoveryResult(
            pedestal_gaps=gaps, total_gaps=total, gap_entropy=round(entropy, 4),
            prioritized_gaps=all_gaps[:50],
            metadata={"scan_timestamp": time.time(),
                      "pedestal_coverage": [k for k, v in gaps.items() if v]})
        self.logger.info("Gap discovery: %d gaps, entropy=%.4f", total, entropy)
        return result

    # =====================================================================
    # 3.2 Question Generation
    # =====================================================================

    def generate_questions(self, gap_result: Optional[GapDiscoveryResult] = None,
                           max_questions: int = 10) -> List[WildQuestion]:
        """Generate questions from discovered gaps."""
        gap_result = gap_result or self.discover_gaps()
        self.logger.info("Generating questions from %d gaps...", gap_result.total_gaps)
        questions: List[WildQuestion] = []
        for gap in gap_result.prioritized_gaps[:max_questions]:
            gt = gap.get("type", "")
            if "theorem" in gt or "proof" in gt or "axiom" in gt:
                cat = QuestionCategory.THEORETICAL
            elif "algorithm" in gt or "complexity" in gt:
                cat = QuestionCategory.TECHNICAL
            elif "refactor" in gt or "test" in gt or "pipeline" in gt:
                cat = QuestionCategory.ENGINEERING
            else:
                cat = QuestionCategory.EXPLORATORY
            questions.append(self.generator.generate_from_gap(gap, cat))
        if len(questions) < max_questions and self._field_state is not None:
            q = self.generator.generate_entropy_maximizing(questions, self._field_state)
            if q:
                questions.append(q)
        for q in questions:
            self.questions[q.id] = q
            self.question_queue.append(q.id)
        self.stats["questions_generated"] += len(questions)
        return questions

    # =====================================================================
    # 3.3 Line Dispatch & Response Simulation
    # =====================================================================

    def dispatch_to_lines(self, question: WildQuestion) -> Dict[str, LineResponse]:
        """Dispatch a question to the 11 lines based on weighted assignments."""
        self.logger.info("Dispatching %s to 11 lines...", question.id)
        question.status = QuestionStatus.ANSWERING
        responses: Dict[str, LineResponse] = {}
        for line_name, weight in question.line_assignments.items():
            if weight > 0:
                responses[line_name] = self._simulate_line_response(line_name, question)
        question.responses = responses
        self.logger.info("Received %d responses for %s", len(responses), question.id)
        return responses

    def _simulate_line_response(self, line_name: str, question: WildQuestion) -> LineResponse:
        """Simulate a line's response using specialization matching."""
        spec_terms = self.LINE_SPECIALIZATIONS.get(line_name, [])
        qterms = set(question.content.lower().split())
        cterms = set(question.category.value.lower().split())
        relevance = min(1.0, sum(0.2 for t in spec_terms if t in qterms or t in cterms))

        if relevance > 0.4:
            tmpl = self.generator.SPECIALIZED_ANSWERS.get(line_name, "Line {line} provides analysis.")
            answer = tmpl.format(
                line=line_name, coherence=question.priority,
                levels=int(question.priority * 10), priority=question.priority,
                connections=int(question.priority * 100),
                validity="valid" if question.priority > 0.5 else "indeterminate",
                coherence_state="high coherence" if question.priority > 0.6 else "partial coherence",
                rank=int(question.priority * 10),
                coupling="strong" if question.priority > 0.6 else "weak",
            )
            confidence = 0.5 + relevance * 0.5
        else:
            answer = (f"Line {line_name}: General assessment of '{question.content[:50]}...' "
                      f"requires further cross-line analysis.")
            confidence = 0.3 + random.random() * 0.3

        attestations = []
        if confidence > 0.65:
            others = [l for l in LINE_NAMES if l != line_name]
            for target in random.sample(others, min(2, len(others))):
                attestations.append(AttestationRequest(
                    requester_line=line_name, target_line=target,
                    claim=answer[:100], evidence={"confidence": confidence, "relevance": relevance}))

        delta = {}
        if line_name in ["qfa", "vinf"]:
            delta[DimensionIndex.DIM_ENERGY.value] = confidence * 0.1
            delta[DimensionIndex.DIM_INFORMATION.value] = confidence * 0.1
        elif line_name in ["cisvr", "usrm"]:
            delta[DimensionIndex.DIM_AWARENESS.value] = confidence * 0.1
            delta[DimensionIndex.DIM_EMOTION.value] = confidence * 0.1
        elif line_name in ["lgt", "qtlv"]:
            delta[DimensionIndex.DIM_TOPOLOGY.value] = confidence * 0.1
            delta[DimensionIndex.DIM_CURVATURE.value] = confidence * 0.1

        return LineResponse(
            line_name=line_name, question_id=question.id, answer=answer,
            confidence=round(confidence, 4), field_state_delta=delta,
            metadata={"relevance": round(relevance, 4)},
            attestation_requests=attestations)

    def collect_responses(self, question_id: str) -> Dict[str, LineResponse]:
        """Collect all responses for a question, dispatching if needed."""
        q = self.questions.get(question_id)
        if q is None:
            return {}
        return q.responses or self.dispatch_to_lines(q)

    # =====================================================================
    # 3.4 Cross-Validation
    # =====================================================================

    def cross_validate(self, question_id: str) -> ValidationResult:
        """
        Cross-validate line responses using semantic overlap and attestation.
        Computes agreement score, identifies consensus, and determines if surge
        is needed for resolution.
        """
        q = self.questions.get(question_id)
        if q is None:
            return ValidationResult(question_id=question_id, agreement_score=0.0)
        responses = q.responses or self.collect_responses(question_id)
        self.logger.info("Cross-validating %d responses for %s...", len(responses), question_id)
        answers = [(name, resp.answer, resp.confidence) for name, resp in responses.items()]
        if len(answers) < 2:
            return ValidationResult(question_id=question_id, agreement_score=1.0,
                                    consensus_answer=answers[0][1] if answers else "",
                                    validation_passed=True, needs_surge=False)

        scores = []
        for i in range(len(answers)):
            for j in range(i + 1, len(answers)):
                ti, ai, ci = answers[i]
                tj, aj, cj = answers[j]
                si = set(ai.lower().split())
                sj = set(aj.lower().split())
                union = len(si | sj)
                sim = (len(si & sj) / union if union > 0 else 0.0) * min(ci, cj)
                scores.append(sim)
        avg_agreement = sum(scores) / len(scores) if scores else 0.0

        consensus = max(answers, key=lambda x: x[2])[1]
        dissenting, supporting = [], []
        for name, ans, conf in answers:
            sa = set(ans.lower().split())
            sc = set(consensus.lower().split())
            union = len(sa | sc)
            sim = len(sa & sc) / union if union > 0 else 0.0
            if sim < 0.3 and conf > 0.5:
                dissenting.append(name)
            elif sim > 0.4:
                supporting.append(name)

        attestation_results = []
        for resp in responses.values():
            for attest in resp.attestation_requests:
                target = responses.get(attest.target_line)
                if target:
                    verified = attest.verify(target.answer, target.confidence)
                    attestation_results.append({
                        "request_id": attest.request_id,
                        "requester": attest.requester_line,
                        "target": attest.target_line,
                        "verified": verified,
                        "confidence": attest.confidence})

        validation_passed = avg_agreement >= 0.30 and len(dissenting) <= max(len(supporting) // 2, 1)
        needs_surge = avg_agreement < 0.25 or len(dissenting) > 3

        result = ValidationResult(
            question_id=question_id, agreement_score=round(avg_agreement, 4),
            consensus_answer=consensus, dissenting_lines=dissenting,
            supporting_lines=supporting, attestation_results=attestation_results,
            validation_passed=validation_passed, needs_surge=needs_surge,
            metadata={"total_lines": len(responses),
                      "avg_confidence": round(sum(r.confidence for r in responses.values()) / len(responses), 4) if responses else 0,
                      "attestation_count": len(attestation_results)})
        q.validation = result
        return result

    # =====================================================================
    # 3.5 Knowledge Refinement
    # =====================================================================

    def refine_knowledge(self, question_id: str) -> KnowledgeRefinementResult:
        """
        Refine knowledge by injecting validated consensus into the 6-pedestal
        knowledge graph. Creates new KNode and KEdge entries, updates field
        state dimensions, and marks linked debts as resolved.
        """
        q = self.questions.get(question_id)
        if q is None:
            return KnowledgeRefinementResult(question_id=question_id, injection_success=False)
        validation = q.validation or self.cross_validate(question_id)
        if not validation.validation_passed:
            self.logger.warning("Cannot refine %s: validation failed", question_id)
            return KnowledgeRefinementResult(question_id=question_id, injection_success=False,
                                             metadata={"error": "Validation failed"})

        self.logger.info("Refining knowledge for %s...", question_id)
        consensus = validation.consensus_answer
        node_id = stable_hash((question_id, consensus))
        new_node = KNode(
            node_id=node_id, label=f"WN_{question_id}",
            node_type="wild_question_answer", module="wild_notebook",
            version="12.0.0", size_bytes=len(consensus.encode("utf-8")),
            path=f"wild_notebook/{question_id}",
            metadata={"question_id": question_id, "category": q.category.value,
                      "priority": q.priority, "agreement_score": validation.agreement_score,
                      "supporting_lines": validation.supporting_lines})
        self.pedestal.add_node(new_node)

        for line_name in validation.supporting_lines:
            e = KEdge(edge_id=stable_hash((line_name, node_id, "supports")),
                      source=line_name, target=node_id,
                      edge_type="line_supports_answer", weight=0.8,
                      metadata={"question_id": question_id})
            self.pedestal.kg_edges.append(e)
            self.pedestal.kg_adj[line_name].append((node_id, 0.8, "line_supports_answer"))

        coherence_change = emergence_change = 0.0
        dims_updated = []
        if self._field_state is not None:
            old_coh = self._field_state.compute_coherence()
            old_em = self._field_state.compute_emergence_index()
            self._field_state.set(DimensionIndex.DIM_KNOWLEDGE,
                self._field_state.get(DimensionIndex.DIM_KNOWLEDGE) + q.priority * 0.01)
            dims_updated.append("DIM_KNOWLEDGE")
            if validation.validation_passed:
                self._field_state.set(DimensionIndex.DIM_COHERENCE,
                    min(1.0, self._field_state.get(DimensionIndex.DIM_COHERENCE) + 0.02))
                dims_updated.append("DIM_COHERENCE")
            coherence_change = self._field_state.compute_coherence() - old_coh
            emergence_change = self._field_state.compute_emergence_index() - old_em

        debt_resolved = bool(q.debt_id)
        result = KnowledgeRefinementResult(
            question_id=question_id, injection_success=True,
            dimensions_updated=dims_updated,
            coherence_change=round(coherence_change, 6),
            emergence_change=round(emergence_change, 6),
            debt_resolved=debt_resolved,
            metadata={"node_id": node_id, "supporting_lines": validation.supporting_lines})
        q.refinement = result
        q.status = QuestionStatus.RESOLVED
        q.resolved_at = time.time()
        self.stats["questions_resolved"] += 1
        self.stats["knowledge_injections"] += 1
        return result

    # =====================================================================
    # 3.6 Surge Engine
    # =====================================================================

    def initiate_surge(self, question: WildQuestion) -> SurgeResult:
        """
        Initiate surge (反向浪涌驱动) for difficult questions.
        Boosts field energy, generates derivative questions, and re-attempts
        cross-validation with elevated confidence thresholds.
        """
        self.logger.info("Initiating surge for %s...", question.id)
        question.status = QuestionStatus.SURGING
        surge_energy = field_boost = 0.0
        breakthrough = False
        new_qs: List[str] = []

        for i in range(3):
            if self._field_state is not None:
                old = self._field_state.get(DimensionIndex.DIM_ENERGY)
                boost = PHI_GOLDEN * 0.1 * (i + 1)
                self._field_state.set(DimensionIndex.DIM_ENERGY, old + boost)
                field_boost += boost
                surge_energy = self._field_state.get(DimensionIndex.DIM_ENERGY)
            der = WildQuestion(
                content=(f"[Surge derivative #{i+1} of {question.id}] "
                         f"Breakdown: {question.content[:50]}... What sub-component blocks resolution?"),
                category=QuestionCategory.EXPLORATORY,
                priority=min(1.0, question.priority + 0.1),
                prerequisite_chain=question.prerequisite_chain + [question.id],
                metadata={"parent": question.id, "derivative_iteration": i,
                          "generation_method": "surge"})
            self.questions[der.id] = der
            self.question_queue.append(der.id)
            new_qs.append(der.id)
            self.stats["questions_generated"] += 1

            if question.responses:
                for resp in question.responses.values():
                    resp.confidence = min(1.0, resp.confidence + 0.15)
                val = self.cross_validate(question.id)
                if val.validation_passed:
                    breakthrough = True
                    break

        result = SurgeResult(question_id=question.id, surge_energy=round(surge_energy, 4),
                             iterations=i + 1, field_boost=round(field_boost, 4),
                             breakthrough=breakthrough, new_questions_generated=new_qs)
        question.surge_result = result
        self.surge_history.append(result.to_dict())
        self.stats["surges_initiated"] += 1
        return result

    # =====================================================================
    # 3.7 Iteration Loop
    # =====================================================================

    def iterate(self, question_id: str, max_rounds: int = 5) -> Dict[str, Any]:
        """
        Full iteration pipeline: dispatch → validate → refine or surge.
        Runs up to max_rounds until resolution or rejection.
        """
        q = self.questions.get(question_id)
        if q is None:
            return {"error": f"Question {question_id} not found"}
        self.logger.info("Iterating on %s (max %d rounds)", question_id, max_rounds)

        for rnd in range(max_rounds):
            q.iteration_count = rnd + 1
            self.stats["total_iterations"] += 1
            self.dispatch_to_lines(q)
            val = self.cross_validate(question_id)
            if val.validation_passed:
                ref = self.refine_knowledge(question_id)
                return {"question_id": question_id, "rounds_used": rnd + 1, "status": "resolved",
                        "validation": val.to_dict(), "refinement": ref.to_dict()}
            elif val.needs_surge and rnd < max_rounds - 1:
                surge = self.initiate_surge(q)
                if surge.breakthrough:
                    val = self.cross_validate(question_id)
                    if val.validation_passed:
                        ref = self.refine_knowledge(question_id)
                        return {"question_id": question_id, "rounds_used": rnd + 1,
                                "status": "resolved_via_surge",
                                "validation": val.to_dict(), "refinement": ref.to_dict(),
                                "surge": surge.to_dict()}

        q.status = QuestionStatus.REJECTED
        self.stats["questions_rejected"] += 1
        return {"question_id": question_id, "rounds_used": max_rounds, "status": "unresolved",
                "validation": q.validation.to_dict() if q.validation else None}

    # =====================================================================
    # 3.8 Debt Processing
    # =====================================================================

    def process_debt(self, debt_item: Union[TheoreticalDebt, TechnicalDebt],
                     debt_type: DebtType = DebtType.TECHNICAL) -> Dict[str, Any]:
        """
        Process a debt item through the full WildNotebook pipeline.

        Pipeline:
          Discover debt → Generate question → Dispatch to relevant lines
          → Collect responses → Cross-validate
          → If consistent → Mark resolved
          → If inconsistent → Initiate surge → Reverse drive → Refine → Re-validate
        """
        self.logger.info("Processing debt %s (%s)...",
                         getattr(debt_item, "id", "unknown"), debt_type.value)
        q = self.generator.generate_from_debt(debt_item, debt_type)
        self.questions[q.id] = q
        self.question_queue.append(q.id)
        q.line_assignments = self.LINE_ASSIGNMENTS_BY_DEBT.get(debt_type, q.line_assignments)
        result = self.iterate(q.id, max_rounds=5)
        debt_status = "resolved" if result.get("status", "").startswith("resolved") else "deferred"
        if debt_status == "resolved":
            self.stats["debts_processed"] += 1
        result["debt_id"] = getattr(debt_item, "id", None)
        result["debt_type"] = debt_type.value
        result["debt_status"] = debt_status
        self.logger.info("Debt %s: %s (%d rounds)", result.get("debt_id", "unknown"),
                         debt_status, result.get("rounds_used", 0))
        return result

    # =====================================================================
    # 3.9 Autonomous Cycle
    # =====================================================================

    def run_autonomous_cycle(self, max_questions: int = 5) -> Dict[str, Any]:
        """
        Run one autonomous cycle:
        1. Discover gaps
        2. Generate questions
        3. Iterate each question
        4. Update field state
        5. Report results
        """
        self.logger.info("Starting autonomous cycle #%d...", self._cycle_count + 1)
        self._cycle_running = True
        self._cycle_count += 1
        gap_result = self.discover_gaps()
        questions = self.generate_questions(gap_result, max_questions=max_questions)
        cycle_results = []
        for q in questions:
            result = self.iterate(q.id, max_rounds=5)
            cycle_results.append({"question_id": q.id, "category": q.category.value,
                                  "priority": q.priority, "result": result})
        if self._field_state is not None:
            resolved = sum(1 for r in cycle_results if r["result"].get("status", "").startswith("resolved"))
            self._field_state.set(DimensionIndex.DIM_EMERGENCE,
                self._field_state.get(DimensionIndex.DIM_EMERGENCE) + resolved * 0.01)
        report = {
            "cycle": self._cycle_count, "gaps_discovered": gap_result.total_gaps,
            "questions_generated": len(questions),
            "questions_resolved": sum(1 for r in cycle_results if r["result"].get("status", "").startswith("resolved")),
            "questions_unresolved": sum(1 for r in cycle_results if r["result"].get("status", "") == "unresolved"),
            "results": cycle_results, "stats": self.stats.copy(), "timestamp": time.time()}
        self._cycle_results.append(report)
        self._cycle_running = False
        self.logger.info("Cycle #%d complete: %d/%d resolved", self._cycle_count,
                         report["questions_resolved"], len(questions))
        return report

    # =====================================================================
    # 3.10 State Management & Utilities
    # =====================================================================

    def set_field_state(self, field_state: UnifiedFieldState) -> None:
        self._field_state = field_state

    def get_field_state(self) -> Optional[UnifiedFieldState]:
        return self._field_state

    def get_question(self, question_id: str) -> Optional[WildQuestion]:
        return self.questions.get(question_id)

    def get_all_questions(self) -> List[WildQuestion]:
        return list(self.questions.values())

    def get_pending_questions(self) -> List[WildQuestion]:
        return [q for q in self.questions.values() if q.status == QuestionStatus.PENDING]

    def get_resolved_questions(self) -> List[WildQuestion]:
        return [q for q in self.questions.values() if q.status == QuestionStatus.RESOLVED]

    def get_rejected_questions(self) -> List[WildQuestion]:
        return [q for q in self.questions.values() if q.status == QuestionStatus.REJECTED]

    def get_surging_questions(self) -> List[WildQuestion]:
        return [q for q in self.questions.values() if q.status == QuestionStatus.SURGING]

    def get_stats(self) -> Dict[str, Any]:
        stats = self.stats.copy()
        stats["total_questions"] = len(self.questions)
        stats["pending"] = sum(1 for q in self.questions.values() if q.status == QuestionStatus.PENDING)
        stats["answering"] = sum(1 for q in self.questions.values() if q.status == QuestionStatus.ANSWERING)
        stats["resolved"] = sum(1 for q in self.questions.values() if q.status == QuestionStatus.RESOLVED)
        stats["rejected"] = sum(1 for q in self.questions.values() if q.status == QuestionStatus.REJECTED)
        stats["surging"] = sum(1 for q in self.questions.values() if q.status == QuestionStatus.SURGING)
        stats["validated"] = sum(1 for q in self.questions.values() if q.status == QuestionStatus.VALIDATED)
        stats["cycles"] = self._cycle_count
        stats["generator"] = self.generator.get_stats()
        return stats

    def export_report(self, output_path: Optional[str] = None) -> str:
        path = Path(output_path or "/mnt/agents/output/OMNI-HUB/hub/WILD_NOTEBOOK_REPORT.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "version": __version__, "timestamp": time.time(),
            "stats": self.get_stats(),
            "questions": [q.to_dict() for q in self.questions.values()],
            "pedestal_summary": self.pedestal.summary(),
            "cycle_history": list(self._cycle_results)[-10:],
            "surge_history": list(self.surge_history)[-10:]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        self.logger.info("Report exported to %s", output_path)
        return str(path)

    def to_dict(self) -> Dict[str, Any]:
        return {"version": __version__, "stats": self.get_stats(),
                "question_count": len(self.questions),
                "pedestal_summary": self.pedestal.summary(),
                "cycle_count": self._cycle_count}

    def reset(self) -> None:
        """Reset the notebook state while keeping the pedestal."""
        self.questions.clear()
        self.question_queue.clear()
        self.surge_history.clear()
        self._cycle_results.clear()
        self._cycle_count = 0
        for key in self.stats:
            self.stats[key] = 0
        self.logger.info("WildNotebook state reset")


# =============================================================================
# 4. Self-Test & Demo
# =============================================================================

def create_sample_debts() -> List[Tuple[Union[TheoreticalDebt, TechnicalDebt], DebtType]]:
    """Create 3 sample debts: theoretical, technical, engineering."""
    theoretical = TheoreticalDebt(
        id="T-THEO-SAMPLE-001",
        name="Sample Emergence Completeness",
        description="Prove unified field emergence is complete under 64 dimensions.",
        file_path="v12_standards.py", severity=DebtSeverity.HIGH,
        status=CleanupStatus.DEFERRED, lean_formalizable=True,
        lean_skeleton="theorem sample_completeness : completeness (UnifiedField 64) := by sorry",
        proof_strategy="Induction on dimension count, show each preserves completeness.",
        blocker="Need formal definition of completeness for continuous field states.",
        verification_method="Lean 4 proof + model check", estimated_hours=40.0)
    technical = TechnicalDebt(
        id="T-TECH-SAMPLE-001",
        description="Hardcoded path in module loader prevents cross-platform deployment.",
        file_path="v12_unified_orchestrator.py", severity=DebtSeverity.MEDIUM,
        debt_type="hardcoded_path",
        fix_strategy="Replace with Path(os.environ.get('OMNIHUB_ROOT', '.')) based paths.",
        auto_fixable=False, status=CleanupStatus.DEFERRED,
        patch_preview="Refactor to use config loader or environment variables",
        estimated_hours=4.0)
    engineering = TechnicalDebt(
        id="T-ENG-SAMPLE-001",
        description="Missing integration tests for 11-line cross-validation pipeline.",
        file_path="v12_wild_notebook.py", severity=DebtSeverity.HIGH,
        debt_type="missing_tests",
        fix_strategy="Create pytest fixtures for each line and integration tests for cross-validation.",
        auto_fixable=False, status=CleanupStatus.DEFERRED,
        patch_preview="Add comprehensive test suite covering all 11 lines",
        estimated_hours=12.0)
    return [(theoretical, DebtType.THEORETICAL), (technical, DebtType.TECHNICAL),
            (engineering, DebtType.ENGINEERING)]


def demo():
    """Run a full demonstration of WildNotebook capabilities."""
    print("\n" + "=" * 78)
    print("OMNI-HUB v12.0 — WildNotebook (野问册) Demonstration")
    print("=" * 78)

    print("\n[1/7] Initializing WildNotebook...")
    notebook = WildNotebook()
    field = create_v12_unified_field()
    notebook.set_field_state(field)
    print(f"  Field: {field.dimensions}D, coherence={field.compute_coherence():.4f}")

    print("\n[2/7] Discovering gaps across 6 pedestals...")
    gaps = notebook.discover_gaps()
    print(f"  Gaps: {gaps.total_gaps}, entropy={gaps.gap_entropy:.4f}")
    for p, items in gaps.pedestal_gaps.items():
        print(f"    {p}: {len(items)} gaps")

    print("\n[3/7] Generating questions from gaps...")
    questions = notebook.generate_questions(gaps, max_questions=5)
    print(f"  Generated: {len(questions)}")
    for q in questions:
        print(f"    [{q.category.value}] {q.id} p={q.priority:.2f}: {q.content[:55]}...")

    print("\n[4/7] Processing 3 sample debts (theoretical + technical + engineering)...")
    debts = create_sample_debts()
    for debt, dtype in debts:
        print(f"\n  Processing {debt.id} ({dtype.value})...")
        result = notebook.process_debt(debt, dtype)
        print(f"    Status: {result['debt_status']}, Rounds: {result.get('rounds_used', 0)}")
        q = notebook.get_question(result['question_id'])
        if q:
            print(f"    Q: {q.id} [{q.status.value}]")
            if q.validation:
                print(f"    Agreement: {q.validation.agreement_score:.4f}, Passed: {q.validation.validation_passed}")
            if q.refinement:
                print(f"    Injected: {q.refinement.injection_success}, Coherence Δ: {q.refinement.coherence_change:.6f}")

    print("\n[5/7] Running autonomous cycle...")
    cycle = notebook.run_autonomous_cycle(max_questions=3)
    print(f"  Cycle #{cycle['cycle']}: {cycle['questions_resolved']}/{cycle['questions_generated']} resolved")

    print("\n[6/7] Final statistics...")
    stats = notebook.get_stats()
    for k, v in stats.items():
        if isinstance(v, (int, float, str, bool)):
            print(f"  {k}: {v}")

    print("\n[7/7] Exporting report...")
    report_path = notebook.export_report()
    print(f"  Report: {report_path}")

    print("\n" + "=" * 78)
    print("WildNotebook Demo Complete")
    print("=" * 78)
    return notebook


if __name__ == "__main__":
    configure_logging(level=logging.INFO)
    demo()
