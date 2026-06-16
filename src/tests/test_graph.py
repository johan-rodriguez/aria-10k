import pytest
from unittest.mock import MagicMock, patch
from src.graph import graph
from langchain_core.documents import Document

@patch("src.graph.validate_ticker")
@patch("src.graph.get_vectorstore")
@patch("src.agents.get_vectorstore")
@patch("src.agents.get_llm")
def test_graph_execution_flow(mock_get_llm, mock_agents_vs, mock_graph_vs, mock_validate_ticker):
    # Setup mocks
    mock_validate_ticker.return_value = (True, "Apple Inc.")
    
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = [
        Document(page_content="Supply chain vulnerability context.", metadata={}),
        Document(page_content="Patent dispute context.", metadata={})
    ]
    mock_graph_vs.return_value = mock_vs
    mock_agents_vs.return_value = mock_vs
    
    # Mock LLM calls for each node
    mock_llm = MagicMock()
    
    # We want mock_llm.invoke to return different values for different calls:
    # 1st call (risk extractor): returns list of 5 risks
    # 2nd call (compliance auditor): returns list of 5 audit comments
    # 3rd call (executive summarizer): returns final summary report
    mock_resp1 = MagicMock()
    mock_resp1.content = "1. Supply chain vulnerability\n2. Patent litigation\n3. Competition\n4. Regulatory shifts\n5. Foreign currency fluctuations risk"
    
    mock_resp2 = MagicMock()
    mock_resp2.content = "1. [FLAGGED] Supply Chain issue\n2. [FLAGGED] Patent litigation\n3. [COMPLIANT] Normal competition\n4. [COMPLIANT] Regulatory ok\n5. [COMPLIANT] FX fluctuations normal"
    
    mock_resp3 = MagicMock()
    mock_resp3.content = "# Executive Audit Report\nSummary content for Apple Inc."
    
    mock_llm.invoke.side_effect = [mock_resp1, mock_resp2, mock_resp3]
    mock_get_llm.return_value = mock_llm
    
    # Execution setup
    config = {"configurable": {"thread_id": "test-thread-id"}}
    initial_state = {"ticker": "AAPL"}
    
    # 1. Run the graph up to the interrupt gate
    # StateGraph runs data_fetcher -> risk_extractor -> compliance_auditor, then pauses
    state_before = graph.invoke(initial_state, config)
    
    # 2. Assert that the graph paused before executive_summarizer
    current_state = graph.get_state(config)
    assert current_state.next == ("executive_summarizer",)
    
    # Assert intermediate results are in the state
    assert current_state.values["empresa"] == "Apple Inc."
    assert len(current_state.values["riesgos_extraidos"]) == 5
    assert len(current_state.values["auditoria"]) == 5
    assert current_state.values.get("reporte_final") is None or current_state.values.get("reporte_final") == ""
    
    # 3. Simulate human approval by updating the state
    graph.update_state(config, {"aprobado_por_humano": True}, as_node="compliance_auditor")
    
    # 4. Resume the graph (null input resumes from the checkpoint)
    state_after = graph.invoke(None, config)
    
    # 5. Assert that the graph completed and generated the report
    final_state = graph.get_state(config)
    assert not final_state.next  # Should be empty (graph completed)
    assert final_state.values["aprobado_por_humano"] is True
    assert "# Executive Audit Report" in final_state.values["reporte_final"]
    assert "Apple Inc." in final_state.values["reporte_final"]
