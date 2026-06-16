# Memory: Architecture and Technical Decisions

> **Written by**: `/strict-development` and `/ui-improvements`
> **Read by**: All technical agents

---

## Usage Guide

This file records significant technical decisions made in aria-10k.
The Software Architect must update it upon closing each approved `implementation_plan.md`.

---

## System Design Decisions

### Graph Pattern: Sequential Pipeline with Interrupt

**Status**: `ACTIVE`

The LangGraph follow an **Assembly Line** pattern:

```
data_fetcher → risk_extractor → compliance_auditor → [INTERRUPT] → executive_summarizer
```

- The interrupt point is `interrupt_before=["executive_summarizer"]`.
- The graph state is a `TypedDict` with fields: `empresa`, `ticker`, `riesgos_extraidos`, `auditoria`, `aprobado_por_humano`, `reporte_final`.
- The Streamlit UI manages resuming the graph via `graph.update_state(config, {"aprobado_por_humano": True})`.

---

### Vector DB Strategy: Dual Mode (Local / Cloud)

**Status**: `ACTIVE`

- **Local**: ChromaDB persisted in `./vector_store/`. No external dependencies. Recommended for development.
- **Cloud**: Pinecone. Activated with `USE_LOCAL_VECTORDB=false` in `.env`.
- Embeddings always use `HuggingFaceEmbeddings` (model: `all-MiniLM-L6-v2`) for cross-mode compatibility.
- The `src/ingestion.py` module abstracts the vector DB backend with a factory function.

---

### LLM Strategy: Dual Mode (Local / Cloud)

**Status**: `ACTIVE`

- **Local**: Ollama running at `http://localhost:11434`. Supported models: `llama3`, `mistral`.
- **Cloud**: OpenAI (`gpt-4o-mini` by default) or Anthropic Claude (`claude-3-haiku` by default).
- The switch is controlled via `USE_LOCAL_LLM=true/false` in `.env`.
- `src/agents.py` initializes the correct LLM using a `get_llm()` function that reads environment variables.

---

### Quality Control: Faithfulness as Production Gate

**Status**: `ACTIVE`

- LangSmith is used to trace **all** graph runs.
- The automatic `Faithfulness` evaluator runs post-execution on the test dataset.
- **Minimum threshold**: Score >= 0.85. Below this threshold, the execution is marked as failed in the dashboard.
- The reference dataset in LangSmith contains questions such as:
  - "What are Apple's supply chain risks?"
  - "Does Tesla have exposure to regulatory litigation?"

---

## [2026-06-16] — Agent Harness Initialization (Agent Infrastructure)

**Agent**: `/strict-development`
**Status**: `ACTIVE`
**Impact**: High

### Context
It was required to establish a framework ("Harness") to coordinate robust executions of the aria-10k pipeline, adapted to the LangGraph + LangChain + Python development pattern.

### Decision / Finding
- Create the environment under `.agents/harness/` to avoid cluttering the source code (`src/`).
- Implement an initialization script (`init.sh`) that creates the virtual environment, installs dependencies from `requirements.txt`, and validates the environment configuration.
- Record the pipeline phases backlog in strict JSON format (`feature_list.json`).
- Create lifecycle prompt templates (`initializer.md` and `coding-agent.md`) adapted to the Python/LangChain stack.

### Pending Actions
- [x] Implement `src/ingestion.py` (Phase 1) — Owner: Coding Agent
- [ ] Implement `src/agents.py` and `src/graph.py` (Phase 2) — Owner: Coding Agent
- [ ] Configure LangSmith project and `src/evals.py` (Phase 3) — Owner: Coding Agent
- [ ] Build `app.py` with Streamlit (Phase 4) — Owner: Coding Agent

---

## [2026-06-16] — Data Ingestion Pipeline & Project Scaffold Setup

**Agent**: `/strict-development`
**Status**: `ACTIVE`
**Impact**: High

### Context
Initialize the scaffold and ingestion pipeline supporting SEC 10-K document downloading, parsing, text splitting, and local vector store storage.

### Decision / Finding
- Built `requirements.txt` listing all necessary packages (LangChain, LangGraph, Chroma, etc.).
- Created `.env.example` defining configuration and credential placeholders.
- Created `src/ingestion.py` encapsulating the following components:
  1. `validate_ticker`: Queries SEC EDGAR (`company_tickers.json`) with the required User-Agent to validate stock tickers and resolve official names, with local fallback for S&P 500 demo tickers.
  2. `extract_risk_factors`: Cleans HTML tags/entities and extracts text between "Item 1A" and "Item 1B" or "Item 2".
  3. `get_vectorstore`: Factory that instantiates a persistent Chroma DB collection under `vector_store/{ticker}/` with `all-MiniLM-L6-v2` embeddings in local mode, or Pinecone in cloud mode.
- Created `src/tests/test_ingestion.py` containing 8 tests verifying parser mechanics, API mocks, and mode switches.

### Rationale
- Isolation of the "Risk Factors" section prevents RAG retrieval contamination (hallucinations) in downstream LLM agents.
- Ticker validation upfront avoids launching graphs on typos.
- Full unittest mocking ensures test suites run quickly and with no internet/API credentials required.

### Impact on Other Domains
- **Product**: Enables reliable company inputs and quick validation feedback.
- **Frontend (Streamlit)**: Can utilize `validate_ticker` and `get_vectorstore` directly.

### Pending Actions
- [x] Implement `src/ingestion.py` (Phase 1) — Owner: Coding Agent
- [x] Propose and implement Phase 2 (LangGraph Core Pipeline) — Owner: Software Architect & Coding Agent
- [ ] Implement LangSmith evaluations (Phase 3) — Owner: Coding Agent

---

## [2026-06-16] — LangGraph Core Pipeline Implementation

**Agent**: `/strict-development`
**Status**: `ACTIVE`
**Impact**: High

### Context
Implement the core LangGraph multi-agent pipeline composed of state schema, LLM switching factories, Extractor/Auditor/Summarizer nodes, and wiring with memory checkpointers and human-in-the-loop interrupts.

### Decision / Finding
- Defined `AriaState` state TypedDict in `src/graph.py`.
- Developed `get_llm()` factory in `src/agents.py` supporting:
  - Local mode: `ChatOllama` running at the configured URL and model name.
  - Cloud mode: `ChatOpenAI` or `ChatAnthropic` dynamically resolved from environment keys.
- Implemented core nodes in `src/agents.py`:
  - `risk_extractor_node`: Performs vector store RAG searches and extracts exactly 5 risk statements from filings using a robust regex numbered list parsing filter.
  - `compliance_auditor_node`: Audits the extracted risks against three mock fund rules (litigation, supply chain, FX).
  - `executive_summarizer_node`: Compiles a Markdown board report summarizing corporate verdicts and recommendations.
- Wired the graph in `src/graph.py` to pause at `interrupt_before=["executive_summarizer"]`.
- Added 9 unit/integration tests (`test_state.py`, `test_agents.py`, `test_graph.py`) verifying all nodes and interrupt state transitions.

### Rationale
- Parsing list items using regex-based prefix stripping ensures consistency in data representation and assertions.
- Interrupting before the summarizer node enforces mandatory Human-in-the-Loop review, serving as the required liability checkpoint.

### Impact on Other Domains
- **Product**: Assures a completely traced, auditable workflow before generating the final verdict.
- **Frontend (Streamlit)**: Can load and run `graph` directly, utilizing standard checkpoints.

### Pending Actions
- [x] Propose and implement Phase 2 (LangGraph Core Pipeline) — Owner: Software Architect & Coding Agent
- [x] Propose and implement Phase 3 (LangSmith Evals) — Owner: Software Architect & Coding Agent
- [ ] Propose and implement Phase 4 (Streamlit UI) — Owner: Software Architect & Coding Agent

---

## [2026-06-16] — LangSmith Observability & Evals Implementation

**Agent**: `/strict-development`
**Status**: `ACTIVE`
**Impact**: High

### Context
Integrate LangSmith tracing, set up evaluation datasets, and construct a faithfulness evaluation runner with threshold alerts.

### Decision / Finding
- Created `src/evals.py` featuring:
  - `create_eval_dataset`: Check if dataset `aria-10k-risk-evals` exists; if not, populate it with 5 QA examples about SEC 10-K risks.
  - `get_faithfulness_evaluator`: Instantiates a Criteria-based string evaluator judging "faithfulness" using `get_llm()` as the evaluator model.
  - `run_faithfulness_eval`: Runs the evaluation against the dataset, aggregates scores, and raises a `ValueError` if the average score falls below `0.85`.
- Created `src/tests/test_evals.py` verifying dataset creation, offline mocks, and threshold checking.

### Rationale
- Setting the evaluation judge to the model returned by `get_llm()` ensures evaluations can run 100% locally when `USE_LOCAL_LLM=true`, complying with local-only deployment mandates.
- Full unittest mocking of LangSmith endpoints prevents network requests and API key requirements during test suites.

### Impact on Other Domains
- **Product**: Guarantees RAG quality constraints.
- **LLM/Costs**: Evaluating locally on Ollama prevents cloud token costs during development.

### Pending Actions
- [x] Propose and implement Phase 3 (LangSmith Evals) — Owner: Software Architect & Coding Agent
- [ ] Propose and implement Phase 4 (Streamlit UI) — Owner: Software Architect & Coding Agent
