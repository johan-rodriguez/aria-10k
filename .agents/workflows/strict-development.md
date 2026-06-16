---
description: Strict development flow to implement phases of the aria-10k pipeline. Invocable with /strict-development
---

# Strict Development Flow — aria-10k (Architecture, Engineering, and QA)

## 🧠 Step 0: Memory Load (MANDATORY — Always execute first)

Before assuming any role, you must load the persistent context of the project:

1. **Read** `.agents/memory/shared-context.md` — Global state of the pipeline, development phases, and full stack.
2. **Read** `.agents/memory/architecture-decisions.md` — Previous technical decisions (LangGraph state schema, dual-mode, Faithfulness gate).
3. **Read** `.agents/memory/product-decisions.md` — Prioritized roadmap and MVP success metrics.
4. If there is relevant context, mention to the user: _"Loaded previous context: [1-2 line summary]"_.

---

When the user requests to invoke this flow, you MUST strictly execute the following three roles in sequential order. Do not skip any step.

## 1. Role: Software Architect
**Goal:** Design the technical solution before writing code.
- Analyze the phase or user request deeply and critically.
- **Golden Rule (Configuration-First):** All configurable behavior must be controlled via environment variables in `.env`. Never hardcode API keys, model names, Pinecone indexes, or ChromaDB collection names.
- **Graph Rule:** Any modification to LangGraph's `StateGraph` MUST preserve the `interrupt_before=["executive_summarizer"]`. Explicitly justify if proposing to alter the interrupt point.
- **Dual-Mode Rule:** Any solution involving LLMs or Vector DBs must support both local mode (Ollama + ChromaDB) and cloud mode (OpenAI/Anthropic + Pinecone) via variables `USE_LOCAL_LLM` and `USE_LOCAL_VECTORDB`.
- **Quality Analysis:** For each node of the graph generating text with an LLM, the architect must explicitly answer in the `implementation_plan.md`:
  1. How are hallucinations prevented in this node? (RAG, prompt constraints, Faithfulness eval)
  2. What happens if the LLM returns an empty or malformed response? (error handling, fallback)
  3. Is the node traced by LangSmith? (mandatory for all nodes)
- **Privacy Rule:** Identify if the phase processes sensitive data. Document what is sent to external APIs in cloud mode.
- Write a detailed technical design in `implementation_plan.md`.
- **Mandatory Action:** You must stop and request the user's review and approval before writing any functional code.

## 2. Role: Senior Python Engineer
**Goal:** Implement the technical solution after plan approval.
- Assume this role automatically once the Architect receives "OK" from the user.
- **Engineering Rules:**
  - Apply **Clean Code**: small functions with single responsibility, explicit names in English (snake_case for Python).
  - Use **type hints** in all functions. Never use unjustified `Any`.
  - Respect the **Configuration-First** principle proposed by the architect.
  - **LangSmith Tracing:** All LLM calls must run under an active tracing context. Verify `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_PROJECT` are configured.
  - **Error Handling:** Catch exceptions from external APIs (timeouts, rate limits). The graph must not crash silently.
  - **Dual-Mode Factory:** The functions `get_llm()` and `get_vectorstore()` must be the single point of configuration for local/cloud mode.
- **Implementation Checklist (before completing):**
  - [ ] Critical environment variables (API keys, mode flags) are read once when initializing the module.
  - [ ] The `interrupt_before=["executive_summarizer"]` is present in the graph definition.
  - [ ] Graph nodes return only the keys of the state they modify (partial updates).
  - [ ] Code works with `USE_LOCAL_LLM=true` AND `USE_LOCAL_LLM=false`.
  - [ ] LangSmith is configured and traces are visible in the `aria-10k` project.
  - [ ] No API keys or configurations are hardcoded in the source code.
- Inform user about modified files with professional descriptions.

## 3. Role: QA Automation Engineer
**Goal:** Ensure the new phase/feature works and doesn't break the pipeline.
- Automatically assume this role after implementation.
- **Mandatory Test Update:** Any change in code requires new or updated tests.
- Write tests using **pytest** (the Python project framework).
- **Mocking Strategy:** External API calls (SEC EDGAR, OpenAI, Pinecone, Anthropic) MUST be mocked in tests using `unittest.mock.patch` or `pytest-mock`. Tests must not require internet connection or real API keys.
- Cover at least:
  - Happy path of each function/node.
  - Error handling (API timeout, empty LLM response, invalid ticker).
  - Correct state updates of the graph by each node.
- Run `pytest src/ -v` to verify all tests pass.

## 📝 Final Step: Memory Write (MANDATORY on closing each session)

On completing any session that produced approved technical decisions:

1. **Update** `.agents/memory/architecture-decisions.md` with a new entry using the standard format defined in `MEMORY_PROTOCOL.md`.
2. **Update** `.agents/harness/aria-10k-progress.md` with the current state and next steps.
3. If the phase was completed, **mark** its `"passes": true` in `.agents/harness/feature_list.json`.
4. If the decision has an impact on costs, product, or legal → also update `shared-context.md`.

---

> Agent Internal Note: If you are reading this file at the user's request, please execute Step 0 (Memory Load) and then enter PLANNING Mode, assuming Role 1.
