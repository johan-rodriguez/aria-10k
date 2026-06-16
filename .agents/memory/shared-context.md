# Shared Context — aria-10k (Cross-Domain)

> **File read by ALL agents when starting a session.**
> Only contains critical cross-domain information. Update with moderation.

---

## General Project State

- **Name**: SEC 10-K Autonomous Risk Analyzer (aria-10k)
- **Current Version**: Active development (MVP)
- **Purpose**: Autonomous multi-agent due diligence pipeline that extracts and validates risk factors from public financial reports (SEC 10-K) with a mathematically controlled hallucination rate.
- **Stack**:
  - **Core Orchestration**: LangChain
  - **Multi-Agent Orchestration**: LangGraph (Sequential Pipeline / StateGraph)
  - **Embeddings & Vector DB**: HuggingFace Embeddings + ChromaDB (Local) / Pinecone (Cloud)
  - **LLM Engine**: Ollama (Local: Llama-3/Mistral) / OpenAI API / Anthropic Claude (Cloud)
  - **Observability & Evals**: LangSmith (Faithfulness, anti-hallucination)
  - **UI & Tracking**: Streamlit (graph status visualization, Human-in-the-loop)
  - **Data Ingestion**: SEC EDGAR API (automatic download of 10-K forms)
- **Primary Market**: Financial sector / Due Diligence / Corporate risk auditing
- **Target Users**: Financial analysts, auditors, boards of directors

## Active Repository Structure

```
aria-10k/
├── data/           → PDFs / TXTs downloaded from EDGAR
├── vector_store/   → Local persistence of ChromaDB
├── src/
│   ├── ingestion.py  → SEC API connection + populating Vector DB
│   ├── agents.py     → Prompts and tools for each agent
│   ├── graph.py      → LangGraph StateGraph (nodes, edges, interrupts)
│   └── evals.py      → LangSmith scripts to measure Faithfulness
├── app.py            → Streamlit frontend + graph status tracking
├── .env.example      → Environment variables
└── requirements.txt  → Python dependencies
```

## Graph Agents (LangGraph Nodes)

| Node | Role | Status |
|------|-----|--------|
| `data_fetcher` | Downloads 10-K from EDGAR and vectorizes "Risk Factors" | Pending |
| `risk_extractor` | RAG → extracts top-5 financial/operational/legal risks | Pending |
| `compliance_auditor` | Contrasts risks vs. simulated investment policy | Pending |
| `human_in_the_loop` | Graph pause: human approval or re-evaluation | Pending |
| `executive_summarizer` | Writes final structured verdict for the board | Pending |

## Active Cross-Domain Constraints

- **Local vs. Cloud Mode**: The system must run 100% locally (Ollama + ChromaDB) OR in cloud mode (OpenAI/Anthropic + Pinecone). The switch is controlled via environment variables in `.env`.
- **Mandatory Human-in-the-loop**: The graph MUST always pause before `executive_summarizer`. Do not remove this interrupt node.
- **Hallucination Control**: All responses from `risk_extractor` and `compliance_auditor` must be evaluated with LangSmith Faithfulness score. Minimum acceptable threshold: 0.85.
- **EDGAR Data**: Only publicly accessible data via the SEC API is consumed. No proprietary company data is stored.

## Development Phases (Roadmap)

| Phase | Name | Status |
|------|--------|--------|
| Phase 1 | Data Configuration (Ingestion) | Pending |
| Phase 2 | Agent and Graph Construction | Pending |
| Phase 3 | Observability and Evals (LangSmith) | Pending |
| Phase 4 | Web Interface and Status Control (Streamlit) | Pending |

## Key Environment Variables (.env)

```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=aria-10k
USE_LOCAL_LLM=false       # true = Ollama, false = cloud API
LOCAL_LLM_MODEL=llama3    # Ollama model if USE_LOCAL_LLM=true
USE_LOCAL_VECTORDB=true   # true = ChromaDB, false = Pinecone
PINECONE_API_KEY=...
PINECONE_INDEX=aria-10k
```
