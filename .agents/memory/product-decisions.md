# Memory: Product Decisions

> **Written by**: `/product-manager`
> **Read by**: `/strict-development`, `/ui-improvements`, `/llm-infra-expert`

---

## Usage Guide

This file records approved product decisions, the prioritized roadmap by phases, and active experiments.
The PM must update it at the end of any session that produces a decision or priority change.

---

## Product Roadmap (Prioritized Phases)

| Priority | Phase | Description | Status |
|-----------|------|-------------|--------|
| 1 (MUST)  | Phase 1 | Data Ingestion: Connect to EDGAR API and populate ChromaDB | Pending |
| 2 (MUST)  | Phase 2 | Core Pipeline: LangGraph Agents (Extractor + Auditor + Summarizer) | Pending |
| 3 (MUST)  | Phase 3 | Observability: LangSmith Faithfulness evals and traceability | Pending |
| 4 (MUST)  | Phase 4 | Streamlit UI: Graph status dashboard + Human-in-the-loop | Pending |
| 5 (SHOULD)| Post-MVP | Multi-company support: analyze multiple tickers in parallel | Backlog |
| 6 (COULD) | Post-MVP | Export final report to structured PDF/DOCX | Backlog |
| 7 (COULD) | Post-MVP | Analysis history: persist and compare previous reports | Backlog |

---

## Key Value Proposition

- **Reduce** the risk auditing cycle from 3 weeks to minutes.
- **Guarantee** traceability and human control (Human-in-the-loop) over critical decisions.
- **Prevent** LLM hallucinations through automatic evaluation with LangSmith.
- **Privacy**: 100% locally operable with Ollama + ChromaDB without cloud dependencies.

---

## Active A/B Experiments

_(No active experiments — project in MVP phase)_

---

## Decisions Made

## [2026-06-16] — MVP Definition: Sequential Pipeline with Mandatory Human-in-the-Loop

**Agent**: `/product-manager`
**Status**: `ACTIVE`
**Impact**: High

### Context
It was necessary to define the minimum product scope for the enterprise-grade demonstration described in `spec.md`.

### Decision
- The MVP consists of exactly 4 Phases according to `spec.md`.
- The `human_in_the_loop` node is **non-negotiable**: the system cannot generate the final executive report without explicit human approval. This is the key difference compared to fully autonomous AI pipelines.
- The Streamlit frontend must show in real-time which agent is active using `st.status` or `st.spinner`.
- The architecture must support the local/cloud switch from the start to facilitate offline demos.

---

## [2026-06-16] — Success Metrics of the Demo

**Agent**: `/product-manager`
**Status**: `ACTIVE`
**Impact**: Medium

### Context
To validate that the aria-10k demo meets the "enterprise" standard promised in `spec.md`.

### Decision
- **Functionality**: The complete pipeline (ingestion → extraction → auditing → approval → report) must execute end-to-end for at least 3 S&P 500 companies (e.g., AAPL, TSLA, MSFT).
- **Quality**: Average Faithfulness score >= 0.85 in the LangSmith dataset.
- **Performance**: Total graph execution time (excluding UI wait) < 120 seconds in cloud mode.
- **UX**: The human approval button must be visible and functional in Streamlit without page reloads.

---

## [2026-06-16] — Granular Stage Breakdown: 4 Phases → 7 Actionable Stages

**Agent**: `/product-manager`
**Status**: `ACTIVE`
**Impact**: High

### Context
The original 4-phase `feature_list.json` was too coarse for a coding agent to execute without ambiguity. Each phase contained multiple independent concerns with different test strategies.

### Decision
Broke the 4 phases into 7 granular, independently testable stages in `feature_list.json`:

| Stage ID | Name | Phase |
|---|---|---|
| `phase_1a_project_setup` | Project Setup & Environment | 1 |
| `phase_1b_data_ingestion` | Data Ingestion Pipeline (EDGAR → ChromaDB) | 1 |
| `phase_2a_state_and_llm_factory` | LangGraph State Schema & LLM Factory | 2 |
| `phase_2b_agent_nodes` | Agent Nodes (Extractor, Auditor, Summarizer) | 2 |
| `phase_2c_graph_wiring` | StateGraph Wiring & Human-in-the-Loop | 2 |
| `phase_3_langsmith_evals` | LangSmith Observability & Faithfulness Evals | 3 |
| `phase_4_streamlit_ui` | Streamlit UI, Real-Time Status & HitL Gate | 4 |

### Rationale
- Each stage produces a single verifiable artifact (one module + one test file).
- Dependencies are sequential within a phase, enabling clean handoffs between coding sessions.
- Phase 4 (Streamlit) now explicitly addresses LEG-01 and LEG-03 via a mandatory disclaimer banner.
- Acceptance criteria are written to be machine-verifiable (pytest, import checks, env flag tests).

### Pending Actions
- [ ] Start with `phase_1a_project_setup` — Owner: Coding Agent via `/strict-development`

---

## [2026-06-16] — Company Input and Ticker Validation

**Agent**: `/product-manager`
**Status**: `ACTIVE`
**Impact**: Medium

### Context
Determine how the system will specify and resolve the company identifier to generate the SEC 10-K risk report.

### Decision
- The Streamlit sidebar (`app.py`) will feature a free-text input where the user enters a company ticker symbol (e.g., "AAPL").
- Prior to launching the multi-agent graph, the system will run a validation step using a lightweight SEC EDGAR ticker lookup (`validate_ticker`).
- If valid, the Resolved Company Name (e.g., "Apple Inc.") and Ticker will be injected into the LangGraph state.
- If invalid, the UI will display a clean error message and block execution of the graph.

### Rationale
- Typing the ticker is highly flexible (Option C) compared to a restricted static dropdown of pre-approved tickers (Option B).
- Performing validation upfront avoids executing the graph with invalid identifiers, protecting the system from wasting API tokens or crashing during the execution of LangGraph agents.

### Impact on Other Domains
- **Product**: Prevents failure states on typos/invalid inputs; provides clean user feedback.
- **Frontend (Streamlit)**: Needs an input field and error display handling.
- **Data Ingestion**: Requires implementing `validate_ticker` in `src/ingestion.py`.

### Pending Actions
- [ ] Implement `validate_ticker(ticker: str) -> tuple[bool, str]` in `src/ingestion.py` — Owner: Coding Agent (`/strict-development`)
- [ ] Integrate ticker validation into `app.py` before executing the graph — Owner: Coding Agent (`/strict-development`)
