import sys
from unittest.mock import MagicMock, patch

def test_app_imports_and_scaffolds():
    """Verify that app.py compiles and imports cleanly with mocked Streamlit interface."""
    mock_st = MagicMock()
    mock_st.sidebar.button.return_value = False
    mock_st.columns.return_value = (MagicMock(), MagicMock())
    
    # We patch sys.modules to feed a mocked streamlit module to app.py during import
    with patch.dict("sys.modules", {"streamlit": mock_st}):
        with patch("src.ingestion.validate_ticker") as mock_validate:
            with patch("src.graph.graph") as mock_graph:
                with patch.object(sys, "argv", ["streamlit"]):
                    # Import app inside the patched context
                    import app
                    assert app is not None
                    
                    # Verify page configs were set
                    mock_st.set_page_config.assert_called_once()
                    assert mock_st.markdown.call_count >= 2
