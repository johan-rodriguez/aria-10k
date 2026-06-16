import os
import pytest
from unittest.mock import patch
from typing import get_type_hints
from src.graph import AriaState
from src.agents import get_llm
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

def test_aria_state_schema():
    """Verify that AriaState schema contains all required fields with correct types."""
    type_hints = get_type_hints(AriaState)
    assert "empresa" in type_hints
    assert "ticker" in type_hints
    assert "riesgos_extraidos" in type_hints
    assert "auditoria" in type_hints
    assert "aprobado_por_humano" in type_hints
    assert "reporte_final" in type_hints
    
    assert type_hints["empresa"] == str
    assert type_hints["ticker"] == str
    assert type_hints["riesgos_extraidos"] == list[str] or type_hints["riesgos_extraidos"].__origin__ == list
    assert type_hints["auditoria"] == list[str] or type_hints["auditoria"].__origin__ == list
    assert type_hints["aprobado_por_humano"] == bool
    assert type_hints["reporte_final"] == str

def test_get_llm_local():
    """Verify get_llm returns ChatOllama when USE_LOCAL_LLM is true."""
    with patch.dict(os.environ, {"USE_LOCAL_LLM": "true", "LOCAL_LLM_MODEL": "llama3"}):
        llm = get_llm()
        assert isinstance(llm, ChatOllama)
        assert llm.model == "llama3"

def test_get_llm_openai():
    """Verify get_llm returns ChatOpenAI when USE_LOCAL_LLM is false and OpenAI key is provided."""
    with patch.dict(os.environ, {
        "USE_LOCAL_LLM": "false",
        "OPENAI_API_KEY": "sk-mock-key",
        "OPENAI_MODEL_NAME": "gpt-4o-mini"
    }):
        llm = get_llm()
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4o-mini"

def test_get_llm_anthropic():
    """Verify get_llm returns ChatAnthropic when USE_LOCAL_LLM is false and Anthropic key is provided (and OpenAI key is missing)."""
    with patch.dict(os.environ, {
        "USE_LOCAL_LLM": "false",
        "OPENAI_API_KEY": "",
        "ANTHROPIC_API_KEY": "mock-anthropic-key",
        "ANTHROPIC_MODEL_NAME": "claude-3-haiku"
    }):
        llm = get_llm()
        assert isinstance(llm, ChatAnthropic)
        assert llm.model == "claude-3-haiku"

def test_get_llm_value_error():
    """Verify get_llm raises ValueError if cloud LLM is requested but no keys are configured."""
    with patch.dict(os.environ, {
        "USE_LOCAL_LLM": "false",
        "OPENAI_API_KEY": "",
        "ANTHROPIC_API_KEY": ""
    }):
        with pytest.raises(ValueError, match="No API keys configured for cloud LLM mode"):
            get_llm()
