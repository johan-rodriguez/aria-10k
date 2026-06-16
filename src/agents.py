import os
import re
from typing import List, Dict, Any
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from src.ingestion import get_vectorstore

def get_llm():
    """Factory function to get the appropriate LLM instance based on environment variables."""
    use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
    
    if use_local_llm:
        model_name = os.getenv("LOCAL_LLM_MODEL", "llama3")
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=model_name, base_url=ollama_url)
    else:
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        if openai_key:
            model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
            return ChatOpenAI(model=model_name, openai_api_key=openai_key)
        elif anthropic_key:
            model_name = os.getenv("ANTHROPIC_MODEL_NAME", "claude-3-haiku")
            return ChatAnthropic(model=model_name, api_key=anthropic_key)
        else:
            raise ValueError("No API keys configured for cloud LLM mode. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.")

def risk_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Risk Extractor Agent Node: extracts 5 financial/operational/legal risks using RAG."""
    ticker = state.get("ticker", "").upper().strip()
    empresa = state.get("empresa", "").strip()
    
    if not ticker:
        raise ValueError("Ticker is required in state to extract risks.")
        
    # Query Vector Store
    try:
        vs = get_vectorstore(ticker)
        docs = vs.similarity_search("financial, operational, and legal risks", k=5)
        context = "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        context = ""
        
    if not context.strip():
        return {
            "riesgos_extraidos": [
                "Failed to extract risks from filing data. Please re-run or inspect the source vector store."
            ]
        }
        
    prompt = f"""You are a senior financial analyst. Based ONLY on the following SEC 10-K "Risk Factors" context, extract exactly the top 5 most critical financial, operational, or legal risks for {empresa}.
Do not invent, extrapolate, or introduce external facts.
Provide the output as a bulleted list of 5 short, descriptive risk statements.

Context:
{context}

Top-5 Risks:"""

    messages = [
        SystemMessage(content="You are a precise financial analyzer. Extract exactly 5 risks based ONLY on the provided context. If context is empty, respond with a statement indicating no risks could be verified."),
        HumanMessage(content=prompt)
    ]
    
    try:
        llm = get_llm()
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        
        # Parse output into clean lines
        raw_lines = [re.sub(r'^\s*(?:\d+[\.\)]|[-*•])\s*', '', line).strip() for line in content.strip().split("\n") if line.strip()]
        risks = [line for line in raw_lines if len(line) > 10][:5]
        
        if not risks:
            risks = ["Failed to extract risks from filing data. Please re-run or inspect the source vector store."]
    except Exception as e:
        risks = [f"Extraction failed due to an error: {str(e)}"]
        
    return {"riesgos_extraidos": risks}

def compliance_auditor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compliance Auditor Agent Node: audits risks against simulated fund guidelines."""
    empresa = state.get("empresa", "").strip()
    risks = state.get("riesgos_extraidos", [])
    
    if not risks:
        return {"auditoria": ["Audit failed: no risk factors provided to compliance auditor."]}
        
    risks_text = "\n".join([f"{i+1}. {r}" for i, r in enumerate(risks)])
    
    prompt = f"""You are a senior compliance auditor for an investment fund.
Evaluate the following corporate risk factors against our fund's investment compliance policy:
- Policy 1: High exposure to pending litigation must be flagged.
- Policy 2: Supply chain bottlenecks or concentration must be flagged.
- Policy 3: Foreign currency fluctuations exceeding normal hedging operations must be flagged.

For each of the corporate risks below, analyze if it triggers any of the policy constraints, and output a concise audit verdict/comment (e.g., "[FLAGGED - Litigation] {empresa} has high exposure to IP litigation...").
If a risk does not trigger any policy constraint, state "[COMPLIANT] Ticker's risk is within normal parameters."
Produce exactly 5 comments, corresponding to the 5 input risks.

Corporate Risks to Audit:
{risks_text}

Audit Comments:"""

    messages = [
        SystemMessage(content="You are a compliance auditor. Output exactly 5 lines of audit verdicts corresponding to the 5 input risks."),
        HumanMessage(content=prompt)
    ]
    
    try:
        llm = get_llm()
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        
        raw_comments = [re.sub(r'^\s*(?:\d+[\.\)]|[-*•])\s*', '', line).strip() for line in content.strip().split("\n") if line.strip()]
        comments = [c for c in raw_comments if len(c) > 10][:5]
        
        if not comments:
            comments = ["Audit failed: compliance agent returned an empty response."]
    except Exception as e:
        comments = [f"Audit failed due to an error: {str(e)}"]
        
    return {"auditoria": comments}

def executive_summarizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Executive Summarizer Agent Node: creates final structured report for the board."""
    ticker = state.get("ticker", "").upper().strip()
    empresa = state.get("empresa", "").strip()
    risks = state.get("riesgos_extraidos", [])
    comments = state.get("auditoria", [])
    
    risks_text = "\n".join([f"- Risk: {r}\n  Audit: {c}" for r, c in zip(risks, comments)])
    
    prompt = f"""You are a senior executive summarizing financial audits. Write a structured executive board report for {empresa} ({ticker}) using the following audited risks and compliance comments.
Structure the report as follows:
1. Executive Summary (High-level verdict)
2. Top Risk Audit Details (A clear summary mapping each risk and its corresponding audit verdict)
3. Investment Recommendations (Actionable recommendation for the board based on the compliance audit)

Data:
{risks_text}

Structured Board Report:"""

    messages = [
        SystemMessage(content="You are an executive summarizer. Write a structured, professional, board-ready report in Markdown."),
        HumanMessage(content=prompt)
    ]
    
    try:
        llm = get_llm()
        response = llm.invoke(messages)
        report = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        report = f"# Executive Audit Report for {empresa} ({ticker})\n\nFailed to compile report due to LLM error: {str(e)}"
        
    return {"reporte_final": report}
