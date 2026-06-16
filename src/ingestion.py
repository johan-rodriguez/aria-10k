import os
import re
import glob
import requests
from typing import Tuple, List
from sec_edgar_downloader import Downloader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

def clean_html(html_content: str) -> str:
    """Clean HTML tags and replace common entities with plain text."""
    # Replace common block tags with newlines
    text = re.sub(r'(?i)</?(?:p|div|tr|h1|h2|h3|h4|h5|h6|br)[^>]*>', '\n', html_content)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Replace HTML entities
    entities = {
        '&nbsp;': ' ',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&rsquo;': "'",
        '&lsquo;': "'",
        '&ldquo;': '"',
        '&rdquo;': '"',
        '&ndash;': '-',
        '&mdash;': '-'
    }
    for ent, val in entities.items():
        text = text.replace(ent, val)
    # Collapse multiple spaces and trim
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()

def extract_risk_factors(text: str) -> str:
    """Extract Item 1A (Risk Factors) from raw SEC 10-K filing text/HTML."""
    clean_text = clean_html(text)
    
    # Try to find headers matching Item 1A. We look for 'Item 1A' with or without 'Risk Factors'
    start_matches = list(re.finditer(r'(?i)\bitem\s+1a\.?\s*(?:risk\s+factors)?\b', clean_text))
    end_matches = list(re.finditer(r'(?i)\bitem\s+1b\.?\s*(?:unresolved\s+staff\s+comments)?\b', clean_text))
    
    if not end_matches:
        end_matches = list(re.finditer(r'(?i)\bitem\s+2\.?\s*(?:properties)?\b', clean_text))
        
    best_text = ""
    for start in start_matches:
        start_idx = start.end()
        for end in end_matches:
            end_idx = end.start()
            if end_idx > start_idx:
                span_text = clean_text[start_idx:end_idx].strip()
                # We want the longest valid-looking risk section, avoiding TOC matches (typically short)
                if len(span_text) > len(best_text):
                    best_text = span_text
                    
    if len(best_text) > 1000:
        return best_text
        
    # Fallback 1: take text after the last Item 1A match
    if start_matches:
        start_idx = start_matches[-1].end()
        fallback_text = clean_text[start_idx:start_idx+100000].strip()
        if len(fallback_text) > 1000:
            return fallback_text
            
    # Fallback 2: return first 100k characters of the document
    return clean_text[:100000]

def validate_ticker(ticker: str) -> Tuple[bool, str]:
    """Validate a stock ticker symbol against SEC EDGAR or local mapping."""
    ticker_upper = ticker.upper().strip()
    if not ticker_upper:
        return False, ""
        
    user_agent = os.getenv("SEC_API_USER_AGENT", "AriaAgent aria-agent@example.com")
    headers = {"User-Agent": user_agent}
    
    try:
        response = requests.get(
            "https://www.sec.gov/files/company_tickers.json", 
            headers=headers, 
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            for item in data.values():
                if item.get("ticker", "").upper() == ticker_upper:
                    return True, item.get("title", "")
    except Exception:
        # Fall back to local map on network failure
        pass
        
    # Local fallback for demo-able tickers
    local_mapping = {
        "AAPL": "Apple Inc.",
        "TSLA": "Tesla, Inc.",
        "MSFT": "Microsoft Corporation",
        "NVDA": "NVIDIA Corporation",
        "AMZN": "Amazon.com, Inc.",
        "GOOGL": "Alphabet Inc."
    }
    if ticker_upper in local_mapping:
        return True, local_mapping[ticker_upper]
        
    return False, ""

def ingest_and_split(ticker: str) -> List[Document]:
    """Download SEC 10-K, extract risk factors, and split into LangChain documents."""
    ticker_upper = ticker.upper().strip()
    user_agent = os.getenv("SEC_API_USER_AGENT", "AriaAgent aria-agent@example.com")
    download_folder = os.path.join(".", "data")
    
    # Download filing
    dl = Downloader("AriaAgent", user_agent, download_folder)
    dl.get("10-K", ticker_upper, after="2020-01-01", limit=1)
    
    # Find downloaded files (.txt or .html) recursively
    search_path = os.path.join(download_folder, "sec-edgar-filings", ticker_upper, "10-K", "**", "*.txt")
    files = glob.glob(search_path, recursive=True)
    if not files:
        search_path = os.path.join(download_folder, "sec-edgar-filings", ticker_upper, "10-K", "**", "*.html")
        files = glob.glob(search_path, recursive=True)
        
    if not files:
        raise ValueError(f"No downloaded 10-K filing found for {ticker_upper} in {download_folder}")
        
    filepath = files[0]
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        raw_content = f.read()
        
    # Extract Risk Factors section
    risk_factors_text = extract_risk_factors(raw_content)
    if not risk_factors_text or len(risk_factors_text.strip()) < 100:
        raise ValueError(f"Failed to extract meaningful Risk Factors section for {ticker_upper}")
        
    # Split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.create_documents(
        texts=[risk_factors_text],
        metadatas=[{"ticker": ticker_upper, "source": filepath}]
    )
    return docs

def get_vectorstore(ticker: str):
    """Retrieve or build the vector store for a company ticker."""
    ticker_upper = ticker.upper().strip()
    if not ticker_upper:
        raise ValueError("Ticker cannot be empty")
        
    use_local_vectordb = os.getenv("USE_LOCAL_VECTORDB", "true").lower() == "true"
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    if use_local_vectordb:
        persist_dir = os.path.join(".", "vector_store", ticker_upper)
        
        # Check if database files exist
        db_exists = False
        if os.path.exists(persist_dir):
            files = os.listdir(persist_dir)
            if any(f.endswith(".sqlite3") or f == "chroma.sqlite3" for f in files) or len(files) > 1:
                db_exists = True
                
        if db_exists:
            return Chroma(persist_directory=persist_dir, embedding_function=embeddings)
        else:
            docs = ingest_and_split(ticker_upper)
            return Chroma.from_documents(docs, embeddings, persist_directory=persist_dir)
    else:
        # Pinecone Cloud Mode
        from langchain_community.vectorstores import Pinecone
        from pinecone import Pinecone as PineconeClient
        
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX", "aria-10k")
        if not api_key:
            raise ValueError("PINECONE_API_KEY must be set in cloud vector DB mode.")
            
        pc = PineconeClient(api_key=api_key)
        # Verify index exists or initialize
        return Pinecone.from_existing_index(index_name=index_name, embedding=embeddings)
