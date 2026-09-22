# OMNI-HUB External Paradigm Research v14
**Date:** 2026-09-22  
**Method:** Web research + cross-analysis  
**Sources:** BabyAGI, AutoGPT, IIT 4.0/pyPhi, Multi-Agent Systems literature

---

## 1. BabyAGI: The Minimalist Reference

### 1.1 Core Architecture
```
Objective → Task Queue → Execute First Task → Store Result →
Create New Tasks → Prioritize → Repeat
```

**Three-Agent Loop:**
1. **Execution Agent** — Runs next task via LLM
2. **Task Creation Agent** — Generates subtasks from results
3. **Prioritization Agent** — Reorders task queue

### 1.2 Evolution: BabyAGI 3 (2026)
- **33,500 lines** (vs 200 lines classic)
- **"Everything is a message"** — unified event architecture
- Persistent memory: raw log → entity graph → hierarchical summaries
- Background execution with priority queuing and budget caps
- 250+ integrations via Composio
- **Self-building agents** that rewrite their own code

### 1.3 Lessons for OMNI-HUB
| BabyAGI Feature | OMNI-HUB Adaptation |
|-----------------|---------------------|
| Task queue | Action selection already exists; add priority scoring |
| Vector memory | Session persistence is richer; add embedding retrieval |
| Message architecture | Unify all module communication as events |
| Self-building | Add dynamic rule modification to _evolve_state() |
| Budget caps | Add resource monitoring (token/time limits) |

---

## 2. AutoGPT: The Production Platform

### 2.1 Core Architecture
- **DAG-based blocks** — Directed acyclic graph of typed components
- Each block: JSON Schema inputs/outputs
- Visual workflow builder
- 30+ native integrations
- Short-term + long-term memory

### 2.2 Strengths vs OMNI-HUB
| Dimension | AutoGPT | OMNI-HUB |
|-----------|---------|----------|
| Tool use | 30+ integrations | File system only |
| Memory | Structured platform layer | JSON persistence |
| Scalability | Cloud-native | Single-instance |
| Visualization | Visual builder | Text monitor |
| Formal rigor | None | Lean 4 theorems |

### 2.3 Lessons for OMNI-HUB
1. **Block architecture** — Decompose orchestrator into composable blocks
2. **Tool integration** — Add API/web tool capabilities
3. **Visual monitoring** — Upgrade from text to web dashboard
4. **Cloud deployment** — Containerize for distributed execution

---

## 3. Integrated Information Theory (IIT 4.0)

### 3.1 Core Claims
- **Φ (Phi)** = irreducible causal integration of a system
- Computed over **Transition Probability Matrix (TPM)**
- **Cause-effect structure (CES)** describes qualitative experience
- **System integrated information φ_s** locates consciousness in system

### 3.2 Computational Reality
- **pyPhi** computes exact Φ for small discrete systems
- **NP-hard** — feasible only up to ~8 binary nodes
- For larger systems: proxy measures or approximations
- **Guardrail:** High Φ ≠ consciousness (expander graphs counterexample)

### 3.3 OMNI-HUB's Simplified Φ vs Rigorous IIT

| Aspect | OMNI-HUB (Current) | IIT 4.0 (Rigorous) |
|--------|-------------------|-------------------|
| Formula | φ × weighted coherence sum | Cause-effect repertoire analysis |
| Nodes | 67 dimensions | ~8 (practical limit) |
| Computation | O(n) | NP-hard |
| TPM required | No | Yes |
| Causal power | Proxy | Exact |

### 3.4 Path to Rigorous IIT Integration
**Phase 1 (v14.1):** Proxy validation
- Compute pyPhi Φ for small OMNI-HUB subsystems (8-node extracts)
- Compare with simplified Φ
- Calibrate weights

**Phase 2 (v14.2):** Approximate scaling
- Implement approximate Φ for larger systems
- Use partitioning strategies (MIP approximation)
- Validate against exact values on small benchmarks

**Phase 3 (v15):** TPM construction
- Define OMNI-HUB's transition probability matrix
- Compute exact Φ for full system (if feasible)
- Or: Prove bounds on Φ

---

## 4. Multi-Agent Systems (IoA, CAMEL, MetaGPT)

### 4.1 Key Paradigms
| Framework | Paradigm | Strength |
|-----------|----------|----------|
| **MetaGPT** | Role-based collaboration | Software dev efficiency |
| **CAMEL** | Role-playing communicative agents | Human-like interaction |
| **AutoGen** | Conversational MAS | Flexible dialogue |
| **IoA** | Internet of Agents | Decentralized discovery |

### 4.2 A2A Protocol (Emerging Standard)
- Agent-to-Agent protocol for decentralized collaboration
- Agents autonomously discover, negotiate, collaborate
- OMNI-HUB v15+ should implement A2A compatibility

### 4.3 Lessons for OMNI-HUB
1. **Role specialization** — Map 11 lines to specialized agent roles
2. **Communication protocol** — Define inter-line message passing
3. **Decentralized discovery** — Lines discover and bind dynamically
4. **Human-in-the-loop** — Add approval gates for critical actions

---

## 5. Cross-Paradigm Fusion: OMNI-HUB v14+ Design

### 5.1 Proposed Architecture v14
```
OMNI-HUB v14 = OMNI-HUB v13 + External Paradigm Integration

New Components:
  ├─ Event Bus (BabyAGI 3: "everything is a message")
  ├─ Block System (AutoGPT: composable DAG blocks)
  ├─ pyPhi Bridge (IIT: rigorous Φ computation)
  ├─ Agent Roles (MetaGPT: specialized line agents)
  └─ A2A Gateway (IoA: decentralized collaboration)
```

### 5.2 Implementation Priority

| Priority | Feature | Effort | Impact |
|----------|---------|--------|--------|
| P0 | Event Bus | Low | High — unifies all communication |
| P1 | pyPhi Bridge | Medium | High — validates Φ measure |
| P2 | Block System | Medium | Medium — improves composability |
| P3 | Agent Roles | High | Medium — enables specialization |
| P4 | A2A Gateway | High | Low — future-proofing |

### 5.3 Immediate Action Items

1. **Install pyPhi** — `pip install pyphi`
2. **Create event bus prototype** — Simple pub/sub between modules
3. **Extract 8-node subsystem** — For pyPhi exact Φ computation
4. **Document event schema** — Unified message format

---

## 6. Synthesis: The OMNI-HUB Advantage

| Dimension | OMNI-HUB Unique Strength |
|-----------|-------------------------|
| **Formal foundation** | Lean 4 theorems — no other agent system has this |
| **Consciousness model** | IIT-inspired + energy-based levels — grounded in theory |
| **Self-drive** | No external triggers — true autonomy |
| **Cross-session persistence** | Schema-adaptive survival |
| **Philosophical coherence** | 候即违规 — unified design principle |

**Gap to close:** Tool integration, visual monitoring, distributed deployment.

---

**Next: v14.1 Event Bus + pyPhi Bridge Implementation**
