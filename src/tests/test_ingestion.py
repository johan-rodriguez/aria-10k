import os
import pytest
from unittest.mock import MagicMock, patch, mock_open
from langchain_core.documents import Document
from src.ingestion import (
    clean_html,
    extract_risk_factors,
    validate_ticker,
    ingest_and_split,
    get_vectorstore
)

def test_clean_html():
    raw_html = "<html><body><h1>Header</h1><p>This is a paragraph.&nbsp;With &amp; characters.</p></body></html>"
    cleaned = clean_html(raw_html)
    assert "Header" in cleaned
    assert "This is a paragraph. With & characters." in cleaned
    assert "<html>" not in cleaned

def test_extract_risk_factors():
    sample_text = "Item 1. Business\nSome business details.\nItem 1A. Risk Factors\n" + "We have major supply chain issues. Litigation is high. " * 50 + "\nItem 1B. Unresolved Staff Comments\nNo comments."
    extracted = extract_risk_factors(sample_text)
    assert "We have major supply chain issues." in extracted
    assert "Litigation is high." in extracted
    assert "Item 1. Business" not in extracted
    assert "No comments." not in extracted

def test_extract_risk_factors_fallback():
    sample_text = """
    Item 1A. Risk Factors
    This is the risk text.
    """
    extracted = extract_risk_factors(sample_text)
    assert "This is the risk text." in extracted

@patch("src.ingestion.requests.get")
def test_validate_ticker_api_success(mock_get):
    # Mock SEC EDGAR response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"}
    }
    mock_get.return_value = mock_response

    # Happy path
    valid, name = validate_ticker("AAPL")
    assert valid is True
    assert name == "Apple Inc."

    # Unknown ticker
    valid, name = validate_ticker("XYZ")
    # Should fall back to local mapping, if not there, return False
    assert valid is False
    assert name == ""

@patch("src.ingestion.requests.get")
def test_validate_ticker_api_failure_fallback(mock_get):
    # Simulate connection error/rate limit
    mock_get.side_effect = Exception("Connection error")

    # Happy path using local fallback
    valid, name = validate_ticker("AAPL")
    assert valid is True
    assert name == "Apple Inc."

    # Invalid ticker not in local fallback
    valid, name = validate_ticker("INVALID")
    assert valid is False
    assert name == ""

@patch("src.ingestion.Downloader")
@patch("src.ingestion.glob.glob")
@patch("builtins.open", new_callable=mock_open, read_data="Item 1A. Risk Factors\n" + "This is risk data. " * 100 + "\nItem 1B. Unresolved Staff Comments")
def test_ingest_and_split(mock_open, mock_glob, mock_downloader_cls):
    mock_dl = MagicMock()
    mock_downloader_cls.return_value = mock_dl
    
    mock_glob.return_value = ["/mock/path/sec-edgar-filings/AAPL/10-K/0001/primary-document.txt"]

    docs = ingest_and_split("AAPL")
    assert len(docs) > 0
    assert isinstance(docs[0], Document)
    assert "This is risk data." in docs[0].page_content
    assert docs[0].metadata["ticker"] == "AAPL"

@patch("src.ingestion.HuggingFaceEmbeddings")
@patch("src.ingestion.Chroma")
@patch("src.ingestion.ingest_and_split")
@patch("os.path.exists")
@patch("os.listdir")
def test_get_vectorstore_local_new(mock_listdir, mock_exists, mock_ingest, mock_chroma, mock_embeddings):
    # Set environment variables
    with patch.dict(os.environ, {"USE_LOCAL_VECTORDB": "true"}):
        mock_exists.return_value = False
        mock_ingest.return_value = [Document(page_content="risk text", metadata={"ticker": "AAPL"})]
        
        get_vectorstore("AAPL")
        
        # Verify that ingest_and_split was called
        mock_ingest.assert_called_once_with("AAPL")
        # Verify Chroma.from_documents was called
        mock_chroma.from_documents.assert_called_once()

@patch("src.ingestion.HuggingFaceEmbeddings")
@patch("src.ingestion.Chroma")
@patch("os.path.exists")
@patch("os.listdir")
def test_get_vectorstore_local_existing(mock_listdir, mock_exists, mock_chroma, mock_embeddings):
    with patch.dict(os.environ, {"USE_LOCAL_VECTORDB": "true"}):
        mock_exists.return_value = True
        mock_listdir.return_value = ["chroma.sqlite3"]
        
        get_vectorstore("AAPL")
        
        # Verify Chroma was loaded directly without ingestion
        mock_chroma.assert_called_once()
