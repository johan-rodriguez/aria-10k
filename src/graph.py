from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.ingestion import validate_ticker, get_vectorstore
from src.agents import (
    risk_extractor_node,
    compliance_auditor_node,
    executive_summarizer_node
)

class AriaState(TypedDict):
    empresa: str
    ticker: str
    riesgos_extraidos: List[str]
    auditoria: List[str]
    aprobado_por_humano: bool
    reporte_final: str

def data_fetcher_node(state: AriaState) -> dict:
    """Download SEC 10-K, resolve company name, and populate/verify the vector store."""
    ticker = state.get("ticker", "").upper().strip()
    empresa = state.get("empresa", "").strip()
    
    if not ticker:
        raise ValueError("Ticker is required in state to fetch data.")
        
    # Resolve company name if empty
    if not empresa:
        valid, resolved_name = validate_ticker(ticker)
        if valid:
            empresa = resolved_name
        else:
            empresa = f"{ticker} Corporation"
            
    # Trigger ingestion to populate vector store
    get_vectorstore(ticker)
    
    return {"empresa": empresa, "ticker": ticker}

# Build and wire the StateGraph workflow
workflow = StateGraph(AriaState)

# Add Nodes
workflow.add_node("data_fetcher", data_fetcher_node)
workflow.add_node("risk_extractor", risk_extractor_node)
workflow.add_node("compliance_auditor", compliance_auditor_node)
workflow.add_node("executive_summarizer", executive_summarizer_node)

# Set Entry Point
workflow.set_entry_point("data_fetcher")

# Connect Nodes Sequentially
workflow.add_edge("data_fetcher", "risk_extractor")
workflow.add_edge("risk_extractor", "compliance_auditor")
workflow.add_edge("compliance_auditor", "executive_summarizer")
workflow.add_edge("executive_summarizer", END)

# Compile with memory saving checkpoint and human interrupt before final report
graph = workflow.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["executive_summarizer"]
)
