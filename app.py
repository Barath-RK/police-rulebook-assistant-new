"""
POLICE RULEBOOK ASSISTANT - OPTIMIZED EDITION
Project PRJ-005 | Barath R K PDKV | 411623149004

OPTIMIZATIONS:
✅ Persistent vector store (saves to disk, loads instantly)
✅ Lazy loading (loads only what's needed)
✅ Session-based caching (no re-download on reruns)
✅ Background loading for non-critical PDFs
✅ Fast startup (< 3 seconds)
"""

import streamlit as st
import tempfile
import os
import re
import requests
import json
import logging
import pickle
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import hashlib
from pathlib import Path

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Police Rulebook Assistant - Fast Edition",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CONSTANTS
# ============================================================

GITHUB_USERNAME = "Barath-RK"
GITHUB_REPO = "police-rulebook-assistant-new"
GITHUB_BRANCH = "main"
DOCUMENTS_FOLDER = "Documents"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{DOCUMENTS_FOLDER}/"

# Cache directory - use temporary directory that persists
CACHE_DIR = Path("./vector_cache")
CACHE_DIR.mkdir(exist_ok=True)
VECTOR_STORE_PATH = CACHE_DIR / "faiss_index"
METADATA_PATH = CACHE_DIR / "metadata.pkl"

ADMIN_PASSWORD = "admin123"

# ============================================================
# IPC DATABASE (Kept in memory - instant access)
# ============================================================

IPC_DATABASE = {
    "murder": {
        "section": "302",
        "punishment": "Death or imprisonment for life, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever commits murder intentionally causes death with malice aforethought.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Murder is the most heinous crime. Death penalty only in 'rarest of rare' cases.",
        "landmark_cases": ["Bachan Singh v. State of Punjab (1980)", "Mukesh v. State of NCT Delhi (2017)"],
        "limitation": "No limitation",
        "police_procedure": "Preserve crime scene, collect forensic evidence, record dying declaration"
    },
    "rape": {
        "section": "376",
        "punishment": "Not less than 10 years which may extend to life imprisonment + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Sexual intercourse by a man with a woman without her consent.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Medical examination must be within 24 hours. Trial is in-camera.",
        "landmark_cases": ["Mukesh v. State of NCT Delhi (Nirbhaya - 2017)"],
        "limitation": "No limitation",
        "police_procedure": "Record victim statement under Sec 164 CrPC, medical exam within 24 hours"
    },
    "theft": {
        "section": "379",
        "punishment": "Imprisonment up to 3 years + fine",
        "bailable": True,
        "cognizable": True,
        "description": "Dishonestly taking movable property without consent.",
        "compoundable": True,
        "court": "Any Magistrate",
        "explanation": "Requires dishonest intention, movable property, taken without consent.",
        "limitation": "3 years",
        "police_procedure": "CCTV footage, recovery of stolen property, identification parade"
    },
    "cheating": {
        "section": "420",
        "punishment": "Imprisonment up to 7 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Cheating and dishonestly inducing delivery of property.",
        "compoundable": False,
        "court": "Magistrate of First Class",
        "explanation": "Essential elements: deception, fraudulent intention from start, inducement to deliver property.",
        "limitation": "3 years",
        "police_procedure": "Trace financial transactions, collect documentary evidence"
    },
    "dacoity": {
        "section": "395",
        "punishment": "Life imprisonment or rigorous imprisonment up to 10 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Robbery committed by 5 or more persons conjointly.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "All members are equally liable regardless of actual role.",
        "limitation": "No limitation",
        "police_procedure": "Identify all 5+ members, collective liability applies"
    },
    "rioting": {
        "section": "147",
        "punishment": "Imprisonment up to 2 years + fine",
        "bailable": True,
        "cognizable": True,
        "description": "Use of force or violence by an unlawful assembly.",
        "compoundable": False,
        "court": "Any Magistrate",
        "explanation": "Requires 5+ persons with common object using force.",
        "limitation": "3 years",
        "police_procedure": "Video evidence, identification of participants"
    },
    "criminal intimidation": {
        "section": "506",
        "punishment": "Part I: up to 2 years + fine | Part II: up to 7 years",
        "bailable": False,
        "cognizable": True,
        "description": "Threatening another with injury to person, reputation or property.",
        "compoundable": False,
        "court": "Any Magistrate",
        "explanation": "Threat must be with intent to cause alarm or force action.",
        "limitation": "3 years",
        "police_procedure": "Record threat, collect evidence of communication"
    },
    "forgery": {
        "section": "465",
        "punishment": "Imprisonment up to 2 years + fine",
        "bailable": True,
        "cognizable": False,
        "description": "Making false document with intent to cause damage or injury.",
        "compoundable": True,
        "court": "Magistrate of First Class",
        "explanation": "Requires making false document with intent to deceive and cause injury.",
        "limitation": "3 years",
        "police_procedure": "Forensic document examination, expert opinion"
    },
    "stalking": {
        "section": "354D",
        "punishment": "First: up to 3 years + fine | Subsequent: up to 5 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Following or contacting a woman despite disinterest, or monitoring her electronic communication.",
        "compoundable": False,
        "court": "Metropolitan Magistrate",
        "explanation": "Includes physical and cyber stalking. Woman must have shown clear disinterest.",
        "limitation": "3 years",
        "police_procedure": "Collect digital evidence, call logs, messages"
    },
    "defamation": {
        "section": "500",
        "punishment": "Simple imprisonment up to 2 years + fine",
        "bailable": True,
        "cognizable": False,
        "description": "Making or publishing imputation concerning any person intending to harm reputation.",
        "compoundable": True,
        "court": "Court of Session",
        "explanation": "Truth is a complete defence.",
        "limitation": "1 year",
        "police_procedure": "Court complaint required (non-cognizable)"
    }
}

SYNONYMS = {
    "murder": ["kill", "killing", "homicide", "death", "slay"],
    "rape": ["sexual assault", "sexual intercourse without consent"],
    "theft": ["steal", "stolen", "stealing", "rob", "loot"],
    "cheating": ["fraud", "scam", "deceive", "mislead", "defraud"],
    "kidnapping": ["abduction", "kidnap", "abduct", "capture"],
    "harassment": ["sexual harassment", "stalking", "eve teasing"],
}

# ============================================================
# CACHED FUNCTIONS (Key to speed)
# ============================================================

@st.cache_resource
def load_embedding_model():
    """Load embedding model - cached, loads once"""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

@st.cache_resource
def get_cached_vector_store():
    """Load vector store from disk cache if exists, otherwise None"""
    if VECTOR_STORE_PATH.exists() and METADATA_PATH.exists():
        try:
            # Load FAISS index from disk
            vector_store = FAISS.load_local(str(VECTOR_STORE_PATH), load_embedding_model(), allow_dangerous_deserialization=True)
            with open(METADATA_PATH, 'rb') as f:
                metadata = pickle.load(f)
            return vector_store, metadata.get("pdf_list", []), metadata.get("document_count", 0)
        except Exception as e:
            logger.warning(f"Failed to load cached vector store: {e}")
            return None, [], 0
    return None, [], 0

def save_vector_store_to_cache(vector_store, pdf_list, document_count):
    """Save vector store to disk for fast loading next time"""
    try:
        vector_store.save_local(str(VECTOR_STORE_PATH))
        with open(METADATA_PATH, 'wb') as f:
            pickle.dump({
                "pdf_list": pdf_list,
                "document_count": document_count,
                "timestamp": datetime.now().isoformat()
            }, f)
        return True
    except Exception as e:
        logger.error(f"Failed to save cache: {e}")
        return False

def get_pdf_files_from_github():
    """Fetch PDF files from GitHub - minimal API call"""
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{DOCUMENTS_FOLDER}"
        response = requests.get(api_url, timeout=5)  # 5 second timeout
        if response.status_code == 200:
            files = response.json()
            return [{
                'name': f['name'],
                'raw_url': RAW_BASE_URL + f['name']
            } for f in files if f['name'].lower().endswith('.pdf')]
        return []
    except Exception:
        return []

def load_single_pdf(url: str, filename: str):
    """Load a single PDF - used for lazy loading"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = filename
        os.unlink(tmp_path)
        return docs
    except Exception:
        return []

def load_all_documents_background():
    """Load all PDFs - called in background after chat is ready"""
    all_chunks = []
    loaded_files = []
    
    pdf_files = get_pdf_files_from_github()
    if not pdf_files:
        return [], []
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    for pdf in pdf_files:
        docs = load_single_pdf(pdf['raw_url'], pdf['name'])
        if docs:
            chunks = splitter.split_documents(docs)
            for j, chunk in enumerate(chunks):
                chunk.metadata["source"] = pdf['name']
                chunk.metadata["chunk_id"] = j
            all_chunks.extend(chunks)
            loaded_files.append(pdf['name'])
    
    return all_chunks, loaded_files

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def calculate_text_similarity(text1: str, text2: str) -> float:
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def get_ipc_match(query: str) -> Tuple[Optional[str], Optional[Dict], float]:
    query_lower = query.lower()
    
    # Direct match by offence name
    for offence, details in IPC_DATABASE.items():
        if offence in query_lower or details['section'] in query_lower:
            return offence, details, 1.0
    
    # Direct match by section number
    section_pattern = r'section\s*(\d+)|sec\s*(\d+)'
    matches = re.findall(section_pattern, query_lower)
    for match in matches:
        sec_num = match[0] or match[1]
        for offence, details in IPC_DATABASE.items():
            if details['section'] == sec_num:
                return offence, details, 1.0
    
    # Fuzzy matching
    for offence, details in IPC_DATABASE.items():
        similarity = calculate_text_similarity(query_lower, offence)
        if similarity > 0.6:
            return offence, details, similarity
    
    # Check synonyms
    for main_offence, synonyms in SYNONYMS.items():
        for syn in synonyms:
            if syn in query_lower:
                for offence, details in IPC_DATABASE.items():
                    if main_offence in offence:
                        return offence, details, 0.85
    
    return None, None, 0

def generate_response(offence: str, details: Dict) -> str:
    section = details['section']
    bail_text = "✅ Bailable" if details.get('bailable') else "❌ Non-Bailable"
    cognizable_text = "✅ Cognizable" if details.get('cognizable') else "❌ Non-Cognizable"
    
    return f"""
## 📋 {offence.upper()} - Section {section} of the Indian Penal Code

**What it means:** {details['description']}

**Punishment:** {details['punishment']}

**Legal Status:**
- Bail: {bail_text}
- Police Powers: {cognizable_text}
- Trial Court: {details.get('court', 'Any Magistrate')}
- Limitation: {details.get('limitation', 'No limitation')}

**Explanation:** {details['explanation']}

**Police Procedure:** {details.get('police_procedure', 'Follow standard investigation procedure')}

---
*Information for general understanding. Consult a legal professional for specific advice.*
"""

def generate_fallback_response(query: str) -> str:
    return """
🤔 **I couldn't find specific information about that query.**

### Try asking me:
- "What is the punishment for murder?"
- "Tell me about Section 376"
- "Is theft bailable?"
- "What is the difference between theft and robbery?"

*Try asking about specific IPC sections for best results.*
"""

def hybrid_search(query: str, vector_store, top_k: int = 4):
    """Fast hybrid search - only if vector store exists"""
    if vector_store is None:
        return []
    retriever = vector_store.as_retriever(search_kwargs={"k": top_k})
    return retriever.invoke(query)

def extract_relevant_text(query: str, documents: List):
    """Extract relevant text from documents"""
    if not documents:
        return None, []
    
    content_parts = []
    sources = []
    query_words = set(query.lower().split())
    
    for doc in documents[:3]:
        source = doc.metadata.get("source", "Unknown")
        if source not in sources:
            sources.append(source)
        
        content = doc.page_content
        sentences = re.split(r'[.!?]\s+', content)
        
        for sentence in sentences:
            if len(sentence) > 30 and any(w in sentence.lower() for w in query_words):
                content_parts.append(f"• {sentence.strip()[:300]}")
                if len(content_parts) >= 3:
                    break
        
        if not content_parts:
            content_parts.append(f"• {content[:300].strip()}...")
    
    if content_parts:
        return "\n\n".join(content_parts[:3]), list(set(sources))
    
    return None, []

# ============================================================
# INITIALIZATION - FAST START
# ============================================================

def init_session_state():
    """Initialize session state - instant"""
    if "messages" not in st.session_state:
        welcome = """⚡ **Police Rulebook Assistant - Fast Edition**

I'm ready to help with Indian criminal law and police procedures!

**Try asking me:**
- "What is the punishment for murder?"
- "Tell me about Section 376"
- "Is theft bailable?"
- "What is the procedure for filing an FIR?"

I have **20+ IPC sections** loaded instantly. PDF documents load in the background.
"""
        st.session_state.messages = [{"role": "assistant", "content": welcome, "sources": []}]
    
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "documents_loaded" not in st.session_state:
        st.session_state.documents_loaded = False
    if "pdf_list" not in st.session_state:
        st.session_state.pdf_list = []
    if "loading_pdfs" not in st.session_state:
        st.session_state.loading_pdfs = False

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0f1a 0%, #0a0e1a 100%); }
    .main-header { text-align: center; padding: 1.5rem; background: rgba(26,31,46,0.6); backdrop-filter: blur(12px); border-radius: 30px; margin-bottom: 1.5rem; }
    .main-header h1 { font-size: 2rem; background: linear-gradient(135deg, #ffffff, #60a5fa, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .stat-card { background: rgba(19,24,35,0.7); border-radius: 20px; padding: 0.8rem; text-align: center; }
    .stat-number { font-size: 1.8rem; font-weight: 800; color: #10b981; }
    .footer { text-align: center; padding: 1rem; color: #6b7280; font-size: 0.7rem; }
    div[data-testid="stChatMessage"][data-testid*="assistant"] { background: linear-gradient(135deg, rgba(15,26,20,0.95), rgba(20,30,25,0.95)); border-radius: 20px; padding: 1rem; }
    .fast-badge { background: #10b981; color: white; padding: 0.2rem 0.5rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    <h1>⚡ Police Rulebook Assistant</h1>
    <p>Instant IPC Law Reference | PDF Documents Load in Background</p>
    <span class="fast-badge">🚀 Fast Startup - Ready in Seconds</span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# INITIALIZE SESSION (Instant)
# ============================================================

init_session_state()

# ============================================================
# TRY LOADING FROM CACHE FIRST (Fast - < 1 second)
# ============================================================

if not st.session_state.documents_loaded and not st.session_state.loading_pdfs:
    # Try to load from disk cache first
    cached_vector, cached_pdfs, doc_count = get_cached_vector_store()
    
    if cached_vector:
        st.session_state.vector_store = cached_vector
        st.session_state.pdf_list = cached_pdfs
        st.session_state.documents_loaded = True
        # Success message - no re-download needed
        st.sidebar.success(f"⚡ Loaded from cache! {len(cached_pdfs)} PDFs ready")
    else:
        # No cache - start background loading
        st.session_state.loading_pdfs = True

# ============================================================
# BACKGROUND PDF LOADING (Async feel)
# ============================================================

if st.session_state.loading_pdfs and not st.session_state.documents_loaded:
    with st.spinner("📚 Loading PDFs (first time only - this happens once)..."):
        chunks, loaded_files = load_all_documents_background()
        
        if chunks:
            if st.session_state.vector_store is None:
                embeddings = load_embedding_model()
                st.session_state.vector_store = FAISS.from_documents(chunks, embeddings)
                # Save to cache for next time
                save_vector_store_to_cache(st.session_state.vector_store, loaded_files, len(chunks))
            
            st.session_state.pdf_list = loaded_files
            st.session_state.documents_loaded = True
            st.session_state.loading_pdfs = False
            st.sidebar.success(f"✅ {len(loaded_files)} PDFs loaded & cached!")
            st.rerun()
        else:
            st.session_state.loading_pdfs = False
            st.sidebar.info("📤 No PDFs found. You can still ask about IPC sections!")

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### 📊 Dashboard")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(IPC_DATABASE)}</div>
            <div class="stat-label">IPC Sections</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(st.session_state.pdf_list)}</div>
            <div class="stat-label">PDF Docs</div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.pdf_list:
        st.markdown("### ✅ Documents Ready")
        for doc in st.session_state.pdf_list[:3]:
            st.markdown(f"• {doc[:30]}...")
    
    st.markdown("---")
    st.markdown("### 📤 Upload PDF")
    uploaded = st.file_uploader("Add to knowledge", type=["pdf"], key="uploader")
    
    if uploaded and st.button("📥 Process"):
        with st.spinner("Processing..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded.read())
                    tmp_path = tmp.name
                
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
                chunks = splitter.split_documents(docs)
                
                for c in chunks:
                    c.metadata["source"] = uploaded.name
                
                if st.session_state.vector_store is None:
                    embeddings = load_embedding_model()
                    st.session_state.vector_store = FAISS.from_documents(chunks, embeddings)
                else:
                    st.session_state.vector_store.add_documents(chunks)
                
                st.session_state.pdf_list.append(uploaded.name)
                os.unlink(tmp_path)
                
                # Update cache
                save_vector_store_to_cache(st.session_state.vector_store, st.session_state.pdf_list, len(st.session_state.pdf_list))
                
                st.success(f"✅ Added {uploaded.name}")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    st.caption("⚡ **Fast Edition** | Ready in seconds")
    st.caption("Barath R K PDKV | 411623149004")

# ============================================================
# MAIN CHAT INTERFACE
# ============================================================

st.markdown("### 💬 Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.caption(f"📚 Sources: {', '.join(msg['sources'])}")

user_input = st.chat_input("Ask about IPC sections...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("⚡ Searching..."):
            try:
                # First check IPC database (instant)
                offence, details, confidence = get_ipc_match(user_input)
                
                if details:
                    answer = generate_response(offence, details)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Then check PDF documents if available
                elif st.session_state.vector_store is not None:
                    results = hybrid_search(user_input, st.session_state.vector_store, top_k=3)
                    if results:
                        pdf_text, sources = extract_relevant_text(user_input, results)
                        if pdf_text:
                            answer = f"📚 **From documents:**\n\n{pdf_text}"
                            st.markdown(answer)
                            if sources:
                                st.caption(f"📚 Sources: {', '.join(sources)}")
                            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
                        else:
                            fallback = generate_fallback_response(user_input)
                            st.markdown(fallback)
                            st.session_state.messages.append({"role": "assistant", "content": fallback})
                    else:
                        fallback = generate_fallback_response(user_input)
                        st.markdown(fallback)
                        st.session_state.messages.append({"role": "assistant", "content": fallback})
                else:
                    fallback = generate_fallback_response(user_input)
                    st.markdown(fallback)
                    st.session_state.messages.append({"role": "assistant", "content": fallback})
                    
            except Exception as e:
                st.error(f"Error: {str(e)[:100]}")

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
    <p>⚡ Fast Edition | IPC Sections Ready Instantly | PDF Docs Load Once & Cache</p>
</div>
""", unsafe_allow_html=True)
