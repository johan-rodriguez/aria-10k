import streamlit as st
import os
import uuid
import pandas as pd
from src.ingestion import validate_ticker
from src.graph import graph

# Page configuration
st.set_page_config(page_title="SEC 10-K Risk Analyzer", layout="wide")

# Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght=300;400;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}
.legal-disclaimer {
    padding: 15px;
    border: 1px dashed #FF4B4B;
    border-radius: 8px;
    background-color: rgba(255, 75, 75, 0.05);
    color: #FF4B4B;
    margin-bottom: 20px;
    font-size: 0.95em;
}
.title-header {
    font-weight: 700;
    font-size: 2.2em;
    margin-bottom: 5px;
    background: linear-gradient(90deg, #1b3d6c 0%, #3a7bd5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
</style>
""", unsafe_allow_html=True)

# Main Title and Disclaimer
st.markdown("<div class='title-header'>SEC 10-K Autonomous Risk Analyzer (aria-10k)</div>", unsafe_allow_html=True)
st.write("Autonomous Multi-Agent Due Diligence Pipeline")
st.markdown("<div class='legal-disclaimer'><strong>⚠️ Legal Disclaimer:</strong> This analysis is for informational purposes only. It does not constitute financial or legal advice.</div>", unsafe_allow_html=True)

# Initialize Session State
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())
if "graph_state" not in st.session_state:
    st.session_state["graph_state"] = "idle"
if "node_statuses" not in st.session_state:
    st.session_state["node_statuses"] = {
        "data_fetcher": "Pending",
        "risk_extractor": "Pending",
        "compliance_auditor": "Pending",
        "executive_summarizer": "Pending"
    }
if "empresa" not in st.session_state:
    st.session_state["empresa"] = ""
if "active_ticker" not in st.session_state:
    st.session_state["active_ticker"] = ""

# Sidebar Settings
st.sidebar.header("Configuration")
mode = st.sidebar.radio(
    "Execution Mode",
    ["Local Mode (Ollama + ChromaDB)", "Cloud Mode (OpenAI/Anthropic + Pinecone)"],
    index=0
)

# Apply settings dynamically
if "Local" in mode:
    os.environ["USE_LOCAL_LLM"] = "true"
    os.environ["USE_LOCAL_VECTORDB"] = "true"
else:
    os.environ["USE_LOCAL_LLM"] = "false"
    os.environ["USE_LOCAL_VECTORDB"] = "false"

ticker_input = st.sidebar.text_input("Stock Ticker Symbol", placeholder="e.g. AAPL", max_chars=5).upper().strip()

# Run Graph trigger button
analyze_clicked = st.sidebar.button("Start Analysis")

if analyze_clicked:
    if not ticker_input:
        st.sidebar.error("Please enter a stock ticker symbol.")
    else:
        # Validate ticker
        with st.spinner("Validating ticker..."):
            valid, resolved_name = validate_ticker(ticker_input)
        if not valid:
            st.sidebar.error(f"Ticker '{ticker_input}' is invalid or not found on SEC EDGAR.")
        else:
            # Setup new execution
            st.session_state["thread_id"] = str(uuid.uuid4())
            st.session_state["graph_state"] = "running"
            st.session_state["empresa"] = resolved_name
            st.session_state["active_ticker"] = ticker_input
            st.session_state["node_statuses"] = {
                "data_fetcher": "Running",
                "risk_extractor": "Pending",
                "compliance_auditor": "Pending",
                "executive_summarizer": "Pending"
            }

# Status tracker panel placeholder
status_placeholder = st.empty()

def render_statuses():
    with status_placeholder.container():
        st.subheader("Agent Execution Progress")
        col1, col2 = st.columns(2)
        
        node_display = [
            ("data_fetcher", "1. Data Ingestion & Ticker Validation"),
            ("risk_extractor", "2. Risk Extractor Agent"),
            ("compliance_auditor", "3. Compliance Auditor Agent"),
            ("executive_summarizer", "4. Executive Summarizer Agent")
        ]
        
        # Split display between two columns for cleaner layout
        for i, (node_id, display_name) in enumerate(node_display):
            target_col = col1 if i < 2 else col2
            status = st.session_state["node_statuses"][node_id]
            with target_col:
                if status == "Pending":
                    st.info(f"⚪ {display_name} — Pending")
                elif status == "Running":
                    st.info(f"⚡ {display_name} — Running...")
                elif status == "Completed":
                    st.success(f"✅ {display_name} — Completed")
                elif status == "Error":
                    st.error(f"❌ {display_name} — Failed")

# Trigger status render
render_statuses()

config = {"configurable": {"thread_id": st.session_state["thread_id"]}}

# Running state handler
if st.session_state["graph_state"] == "running":
    ticker = st.session_state["active_ticker"]
    empresa = st.session_state["empresa"]
    initial_state = {"ticker": ticker, "empresa": empresa}
    
    try:
        # Stream the graph execution
        for event in graph.stream(initial_state, config):
            for node_name in event:
                st.session_state["node_statuses"][node_name] = "Completed"
                # Update next nodes to Running
                current_state = graph.get_state(config)
                next_nodes = current_state.next
                for n in next_nodes:
                    st.session_state["node_statuses"][n] = "Running"
                render_statuses()
                
        # Post-execution state check
        current_state = graph.get_state(config)
        if current_state.next and "executive_summarizer" in current_state.next:
            st.session_state["graph_state"] = "paused"
        else:
            st.session_state["graph_state"] = "completed"
        st.rerun()
    except Exception as e:
        for node_id, status in st.session_state["node_statuses"].items():
            if status == "Running":
                st.session_state["node_statuses"][node_id] = "Error"
        st.session_state["graph_state"] = "idle"
        render_statuses()
        st.error(f"Pipeline execution failed: {str(e)}")

# Resuming state handler (Approved by user)
elif st.session_state["graph_state"] == "resuming":
    try:
        # Update graph with human approval state change
        graph.update_state(config, {"aprobado_por_humano": True}, as_node="compliance_auditor")
        st.session_state["node_statuses"]["executive_summarizer"] = "Running"
        render_statuses()
        
        # Resume execution (yields from current checkpoint)
        for event in graph.stream(None, config):
            for node_name in event:
                st.session_state["node_statuses"][node_name] = "Completed"
                render_statuses()
                
        st.session_state["graph_state"] = "completed"
        st.rerun()
    except Exception as e:
        st.session_state["node_statuses"]["executive_summarizer"] = "Error"
        st.session_state["graph_state"] = "idle"
        render_statuses()
        st.error(f"Failed to compile report: {str(e)}")

# Paused state handler (Human-in-the-Loop)
elif st.session_state["graph_state"] == "paused":
    st.divider()
    st.subheader("👨‍⚖️ Human-in-the-Loop Audit Gate Required")
    st.write(f"The sequential pipeline has paused. Please audit the extracted risks for **{st.session_state['empresa']}**:")
    
    current_state = graph.get_state(config)
    risks = current_state.values.get("riesgos_extraidos", [])
    comments = current_state.values.get("auditoria", [])
    
    # Render table of risks and audits
    if risks:
        df = pd.DataFrame({
            "Corporate Risk Factor": risks,
            "Compliance Audit Verdict": comments
        })
        st.table(df)
    else:
        st.warning("No risks extracted to review.")
        
    col1, col2 = st.columns(2)
    with col1:
        approve = st.button("✅ Approve & Generate Board Report", use_container_width=True)
    with col2:
        reject = st.button("🔄 Reject & Reset Analysis", use_container_width=True)
        
    if approve:
        st.session_state["graph_state"] = "resuming"
        st.rerun()
    if reject:
        # Reset execution state
        st.session_state["graph_state"] = "idle"
        st.session_state["node_statuses"] = {
            "data_fetcher": "Pending",
            "risk_extractor": "Pending",
            "compliance_auditor": "Pending",
            "executive_summarizer": "Pending"
        }
        st.rerun()

# Completed state handler
elif st.session_state["graph_state"] == "completed":
    st.divider()
    st.subheader("📋 Final Executive Board Report")
    
    current_state = graph.get_state(config)
    report = current_state.values.get("reporte_final", "")
    
    if report:
        st.markdown(report)
        st.divider()
        st.download_button(
            label="💾 Download Board Report (.md)",
            data=report,
            file_name=f"{st.session_state['active_ticker']}_executive_risk_report.md",
            mime="text/markdown"
        )
    else:
        st.error("Report content is missing from state.")
