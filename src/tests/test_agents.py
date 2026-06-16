import pytest
from unittest.mock import MagicMock, patch
from src.agents import risk_extractor_node, compliance_auditor_node, executive_summarizer_node
from langchain_core.documents import Document

@patch("src.agents.get_llm")
@patch("src.agents.get_vectorstore")
def test_risk_extractor_node(mock_get_vectorstore, mock_get_llm):
    # Mock Vector Store
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = [
        Document(page_content="Apple faces high supply chain risk in Asia."),
        Document(page_content="Litigation regarding patents is a primary concern.")
    ]
    mock_get_vectorstore.return_value = mock_vs
    
    # Mock LLM
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "1. Supply chain vulnerability\n2. High litigation costs\n3. Competitor pressures\n4. Regulatory oversight\n5. Intellectual property disputes"
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm
    
    state = {"ticker": "AAPL", "empresa": "Apple Inc."}
    result = risk_extractor_node(state)
    
    assert "riesgos_extraidos" in result
    assert len(result["riesgos_extraidos"]) == 5
    assert result["riesgos_extraidos"][0] == "Supply chain vulnerability"
    assert result["riesgos_extraidos"][4] == "Intel property disputes" or "Intellectual property disputes" in result["riesgos_extraidos"][4]

@patch("src.agents.get_llm")
def test_compliance_auditor_node(mock_get_llm):
    # Mock LLM
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "1. [FLAGGED - Supply Chain] Vulnerability detected.\n2. [FLAGGED - Litigation] Patent disputes are active.\n3. [COMPLIANT] Normal pressures.\n4. [COMPLIANT] Normal oversight.\n5. [FLAGGED - Litigation] IP disputes flagged."
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm
    
    state = {
        "empresa": "Apple Inc.",
        "riesgos_extraidos": [
            "Supply chain vulnerability",
            "High litigation costs",
            "Competitor pressures",
            "Regulatory oversight",
            "Intellectual property disputes"
        ]
    }
    result = compliance_auditor_node(state)
    
    assert "auditoria" in result
    assert len(result["auditoria"]) == 5
    assert "[FLAGGED - Supply Chain]" in result["auditoria"][0]
    assert "[COMPLIANT]" in result["auditoria"][2]

@patch("src.agents.get_llm")
def test_executive_summarizer_node(mock_get_llm):
    # Mock LLM
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "# Executive Audit Report\n\nAll compliant."
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm
    
    state = {
        "ticker": "AAPL",
        "empresa": "Apple Inc.",
        "riesgos_extraidos": ["Supply chain vulnerability"],
        "auditoria": ["[FLAGGED - Supply Chain] Vulnerability detected."]
    }
    result = executive_summarizer_node(state)
    
    assert "reporte_final" in result
    assert "# Executive Audit Report" in result["reporte_final"]
