# Memory: Infrastructure and Cost Decisions

> **Written by**: `/llm-infra-expert`
> **Read by**: `/strict-development`, `/product-manager`

---

## Usage Guide

This file records applied optimizations, recommended configurations, and cost/latency benchmarks for the aria-10k project.
Update upon completing audits or recommending infrastructure changes.

---

## Baseline Configurations

### Local Mode (Default for Development)
| Resource | Configuration | Estimated Cost |
|---|---|---|
| LLM Engine | Ollama (`llama3`) | $0 (local) |
| Vector DB | ChromaDB (filesystem) | $0 (local) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` | $0 (local) |
| Observability | LangSmith (free tier) | $0 / 5K traces |

### Cloud Mode (For Demo / Production)
| Resource | Configuration | Estimated Cost |
|---|---|---|
| LLM Engine | OpenAI `gpt-4o-mini` | ~$0.15 / 1M input tokens, $0.60 / 1M output |
| LLM Engine Alt | Anthropic `claude-3-haiku`| ~$0.25 / 1M input, $1.25 / 1M output |
| Vector DB | Pinecone (Starter) | $0 / up to 100K vectors |
| Observability | LangSmith (Plus plan) | $39/month (10M traces) |

---

## Pipeline Execution Cost Analysis

**Estimation for a complete 10-K (section "Risk Factors" ≈ 5,000 tokens)**:

- **Ingestion tokens** (chunking + embedding): $0 in local mode, ~$0.003 in cloud (ada-002).
- **Risk Extractor tokens** (RAG → LLM): ~2,000 input tokens + 500 output tokens → ~$0.0006 (gpt-4o-mini).
- **Compliance Auditor tokens**: ~1,500 input tokens + 300 output tokens → ~$0.0004.
- **Executive Summarizer tokens**: ~2,500 input tokens + 800 output tokens → ~$0.0009.
- **Total estimated cost per complete analysis (cloud)**: < $0.01 per analyzed company.

---

## Applied Optimizations

_(No optimizations recorded yet — project in initial phase)_

---

## Infrastructure Recommendations for Scalability

## [2026-06-16] — Selection of Local-First Stack for MVP

**Agent**: `/llm-infra-expert`
**Status**: `ACTIVE`
**Impact**: High

### Context
The `spec.md` requires that the system run 100% locally (without cloud dependencies) to guarantee data privacy and operability without connectivity.

### Decision
- Use **ChromaDB** (persisted in `./vector_store/`) as the default Vector DB for local development and demos.
- Use **Ollama** with `llama3` or `mistral` as the default local LLM.
- The `USE_LOCAL_LLM` and `USE_LOCAL_VECTORDB` switches in `.env` allow migrating to the cloud without code changes.
- For production or high-load demos, scale to Pinecone + OpenAI gpt-4o-mini as a cost-efficient combination.

### Rationale
- **Privacy**: The financial sector is highly sensitive. A 100% local mode is a critical sales differentiator.
- **Cost**: The cost per analysis in the cloud is < $0.01, making it viable even at scale.
- **LangSmith**: Always required even in local mode for observability. The free plan supports up to 5K traces (sufficient for the MVP).
