"""
POLICE RULEBOOK ASSISTANT - ULTIMATE EDITION WITH GITHUB AUTO-LOAD
Project PRJ-005 | Barath R K PDKV | 411623149004

AUTO-LOADS ALL PDFs FROM GITHUB 'Documents' FOLDER ON STARTUP
"""

import streamlit as st
import tempfile
import os
import re
import requests
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Police Rulebook Assistant - Professional Edition",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# GITHUB CONFIGURATION - CHANGE THESE TO YOUR DETAILS
# ============================================================

GITHUB_USERNAME = "Barath-RK"
GITHUB_REPO = "police-rulebook-assistant-new"
GITHUB_BRANCH = "main"
DOCUMENTS_FOLDER = "Documents"

RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{DOCUMENTS_FOLDER}/"

# ============================================================
# COMPLETE IPC DATABASE (35+ Sections)
# ============================================================

IPC_DATABASE = {
    "murder": {"section": "302", "punishment": "Death or imprisonment for life + fine", "bailable": False, "description": "Whoever commits murder shall be punished with death or imprisonment for life."},
    "rape": {"section": "376", "punishment": "Rigorous imprisonment not less than 10 years up to life imprisonment + fine", "bailable": False, "description": "Whoever commits rape shall be punished with rigorous imprisonment for not less than 10 years."},
    "gang rape": {"section": "376D", "punishment": "Rigorous imprisonment not less than 20 years up to life imprisonment + fine", "bailable": False, "description": "Gang rape shall be punished with rigorous imprisonment for not less than 20 years."},
    "sexual harassment": {"section": "354A", "punishment": "Rigorous imprisonment up to 3 years + fine", "bailable": False, "description": "Physical contact, demand for sexual favours, showing pornography, making sexually coloured remarks."},
    "stalking": {"section": "354D", "punishment": "First conviction: up to 3 years; subsequent: up to 5 years + fine", "bailable": False, "description": "Following or contacting a woman despite clear disinterest."},
    "insult modesty of woman": {"section": "509", "punishment": "Simple imprisonment up to 3 years + fine", "bailable": True, "description": "Word, gesture or act intended to insult the modesty of a woman."},
    "criminal intimidation": {"section": "506", "punishment": "Imprisonment up to 2 years; if threat of death/grievous hurt, up to 7 years", "bailable": False, "description": "Threatening another with injury to person, reputation or property."},
    "theft": {"section": "379", "punishment": "Imprisonment up to 3 years + fine", "bailable": True, "description": "Whoever commits theft shall be punished with imprisonment up to 3 years."},
    "robbery": {"section": "392", "punishment": "Rigorous imprisonment up to 10 years + fine", "bailable": False, "description": "Theft or extortion accompanied by force or fear of instant death/hurt."},
    "dacoity": {"section": "395", "punishment": "Imprisonment for life or rigorous imprisonment up to 10 years + fine", "bailable": False, "description": "Robbery committed by 5 or more persons conjointly."},
    "cheating": {"section": "420", "punishment": "Imprisonment up to 7 years + fine", "bailable": False, "description": "Cheating and dishonestly inducing delivery of property."},
    "kidnapping": {"section": "363", "punishment": "Imprisonment up to 7 years + fine", "bailable": False, "description": "Kidnapping from India or from lawful guardianship."},
    "hurt": {"section": "323", "punishment": "Imprisonment up to 1 year or fine up to ₹1000 or both", "bailable": True, "description": "Whoever voluntarily causes hurt."},
    "grievous hurt": {"section": "325", "punishment": "Imprisonment up to 7 years + fine", "bailable": False, "description": "Whoever voluntarily causes grievous hurt."},
    "defamation": {"section": "500", "punishment": "Simple imprisonment up to 2 years + fine", "bailable": True, "description": "Making or publishing imputation concerning any person intending to harm reputation."},
    "criminal trespass": {"section": "447", "punishment": "Imprisonment up to 3 months + fine up to ₹500", "bailable": True, "description": "Entering property with intent to commit offence or intimidate."},
    "dowry death": {"section": "304B", "punishment": "Imprisonment not less than 7 years up to life imprisonment", "bailable": False, "description": "Where death of woman occurs within 7 years of marriage due to cruelty for dowry."},
    "attempt to murder": {"section": "307", "punishment": "Imprisonment up to 10 years + fine; if hurt caused, imprisonment for life", "bailable": False, "description": "Whoever attempts to murder shall be punished with imprisonment up to 10 years."},
    "forgery": {"section": "465", "punishment": "Imprisonment up to 2 years + fine", "bailable": True, "description": "Making false document with intent to cause damage or injury."},
    "rioting": {"section": "147", "punishment": "Imprisonment up to 2 years + fine", "bailable": True, "description": "Use of force or violence by an unlawful assembly."},
}

SYNONYMS = {
    "harassment": ["sexual harassment", "stalking", "criminal intimidation"],
    "murder": ["kill", "killing", "homicide", "death"],
    "theft": ["steal", "stolen", "stealing", "rob"],
    "rape": ["sexual assault"],
    "cheating": ["fraud", "scam", "deceive"],
}

# ============================================================
# ADVANCED CSS
# ============================================================

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0f1119 100%); }
    
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%);
        border-radius: 25px;
        margin-bottom: 2rem;
        border: 1px solid #21262d;
        animation: slideDown 0.5s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #dc2626, #10b981, #dc2626);
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #dc2626 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .main-header p {
        font-size: 1rem;
        color: #8b949e;
    }
    
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, #1a0f0f 0%, #1f1414 100%);
        border: 1px solid rgba(220,38,38,0.3);
        border-radius: 20px 20px 5px 20px;
        animation: fadeInRight 0.3s ease-out;
    }
    
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%);
        border: 1px solid rgba(16,185,129,0.3);
        border-radius: 20px 20px 20px 5px;
        animation: fadeInLeft 0.3s ease-out;
    }
    
    @keyframes fadeInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes fadeInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e1a 0%, #0d1117 100%);
        border-right: 1px solid #21262d;
    }
    
    .stat-card {
        background: #131823;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        text-align: center;
        border: 1px solid #21262d;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-3px);
        border-color: #10b981;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #10b981;
    }
    
    .stat-label {
        font-size: 0.7rem;
        color: #8b949e;
    }
    
    .doc-badge {
        background: rgba(16,185,129,0.15);
        color: #10b981;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.2rem;
        border: 1px solid rgba(16,185,129,0.3);
    }
    
    .stButton button {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(220,38,38,0.4);
    }
    
    .answer-section {
        background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        line-height: 1.8;
        border-left: 4px solid #10b981;
        font-size: 1rem;
    }
    
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #8b949e;
        font-size: 0.75rem;
        border-top: 1px solid #21262d;
        margin-top: 2rem;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #dc2626, #10b981);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Professional RAG Assistant for Indian Penal Code, Criminal Laws & Police Procedures</p>
    <p style="font-size: 0.85rem;">🔍 Auto-loads PDFs from GitHub | Semantic Search | 📚 Citations | ⚡ Real-time Answers</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "documents" not in st.session_state:
    st.session_state.documents = []
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None
if "pdf_list" not in st.session_state:
    st.session_state.pdf_list = []
if "documents_loaded" not in st.session_state:
    st.session_state.documents_loaded = False
if "admin_password" not in st.session_state:
    st.session_state.admin_password = "admin123"

# ============================================================
# GITHUB PDF LOADER FUNCTIONS
# ============================================================

def get_pdf_files_from_github():
    """Get list of all PDF files from GitHub Documents folder"""
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{DOCUMENTS_FOLDER}"
        response = requests.get(api_url)
        if response.status_code == 200:
            files = response.json()
            pdf_files = []
            for file in files:
                if file['name'].lower().endswith('.pdf'):
                    pdf_files.append({
                        'name': file['name'],
                        'raw_url': RAW_BASE_URL + file['name']
                    })
            return pdf_files
        return []
    except Exception as e:
        return []

def load_pdf_from_url(url: str, filename: str):
    """Download PDF from URL and load it"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        for doc in documents:
            doc.metadata["source"] = filename
        os.unlink(tmp_path)
        return documents
    except:
        return []

@st.cache_resource
def load_embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_all_documents_from_github():
    """Load ALL PDFs from GitHub Documents folder"""
    all_chunks = []
    loaded_files = []
    
    pdf_files = get_pdf_files_from_github()
    
    if not pdf_files:
        return [], []
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    for i, pdf_info in enumerate(pdf_files):
        status_text.text(f"📖 Loading: {pdf_info['name']}...")
        
        documents = load_pdf_from_url(pdf_info['raw_url'], pdf_info['name'])
        
        if documents:
            chunks = splitter.split_documents(documents)
            for j, chunk in enumerate(chunks):
                chunk.metadata["source"] = pdf_info['name']
                chunk.metadata["chunk_id"] = j
                chunk.metadata["page"] = chunk.metadata.get("page", 1)
            all_chunks.extend(chunks)
            loaded_files.append(pdf_info['name'])
        
        progress_bar.progress((i + 1) / len(pdf_files))
    
    status_text.empty()
    progress_bar.empty()
    
    return all_chunks, loaded_files

# ============================================================
# AUTO-LOAD DOCUMENTS FROM GITHUB ON STARTUP
# ============================================================

if not st.session_state.documents_loaded:
    with st.spinner("📚 Auto-loading PDFs from GitHub 'Documents' folder..."):
        chunks, loaded_files = load_all_documents_from_github()
        
        if chunks:
            if st.session_state.embeddings is None:
                st.session_state.embeddings = load_embedding_model()
            
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
            st.session_state.documents = chunks
            st.session_state.pdf_list = loaded_files
            st.session_state.documents_loaded = True
            st.success(f"✅ Auto-loaded {len(loaded_files)} documents from GitHub! ({len(chunks)} chunks)")
        else:
            st.info("📤 No PDFs found in GitHub 'Documents' folder. You can upload manually using sidebar.")

# ============================================================
# HELPER FUNCTIONS FOR ANSWERS
# ============================================================

def match_ipc_offence(query: str) -> Tuple[Optional[str], Optional[Dict]]:
    """Match query against IPC database"""
    query_lower = query.lower()
    
    for offence, details in IPC_DATABASE.items():
        if offence in query_lower:
            return offence, details
    
    for main_offence, synonyms in SYNONYMS.items():
        for syn in synonyms:
            if syn in query_lower:
                for offence, details in IPC_DATABASE.items():
                    if main_offence in offence:
                        return offence, details
    
    return None, None

def format_ipc_answer(offence: str, details: Dict) -> str:
    """Format IPC answer"""
    bail_status = "✅ Bailable Offence" if details["bailable"] else "❌ Non-Bailable Offence"
    return f"""
**📋 Section {details['section']} of the Indian Penal Code**

**Offence:** {offence.title()}

**Description:** {details['description']}

**Punishment:** {details['punishment']}

**{bail_status}**

*Source: Indian Penal Code, 1860*
"""

def search_pdf_documents(query: str, top_k: int = 4) -> List:
    """Search PDF documents"""
    if st.session_state.vector_store is None:
        return []
    
    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": top_k})
    return retriever.invoke(query)

def calculate_relevance(query: str, document) -> float:
    """Calculate relevance score"""
    query_words = set(query.lower().split())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
    keywords = [w for w in query_words if w not in stop_words and len(w) > 2]
    
    if not keywords:
        return 0.5
    
    content = document.page_content.lower()
    matches = sum(1 for kw in keywords if kw in content)
    return min(matches / len(keywords), 1.0)

def extract_answer_from_pdfs(query: str, documents: List) -> Tuple[Optional[str], List[str]]:
    """Extract best answer from PDFs"""
    if not documents:
        return None, []
    
    scored = [(calculate_relevance(query, doc), doc) for doc in documents]
    scored.sort(reverse=True, key=lambda x: x[0])
    
    relevant = [(score, doc) for score, doc in scored if score >= 0.2]
    
    if not relevant:
        return None, []
    
    answer_parts = []
    sources = []
    
    for score, doc in relevant[:2]:
        sources.append(doc.metadata.get("source", "Unknown"))
        content = doc.page_content
        
        sentences = re.split(r'[.!?]\s+', content)
        best_sentence = max(sentences, key=lambda s: sum(1 for w in query.lower().split() if w in s.lower()), default="")
        
        if len(best_sentence) > 30:
            answer_parts.append(f"• {best_sentence}")
        else:
            answer_parts.append(f"• {content[:300].strip()}...")
    
    if answer_parts:
        answer = "**Based on the document(s):**\n\n" + "\n\n".join(answer_parts)
        return answer, list(set(sources))
    
    return None, []

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🎯 Control Panel")
    
    # Show auto-loaded documents
    if st.session_state.documents_loaded and st.session_state.pdf_list:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(st.session_state.documents)}</div>
            <div class="stat-label">Text Chunks</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### ✅ Auto-Loaded from GitHub")
        for doc in st.session_state.pdf_list[:3]:
            short_name = doc[:35] + "..." if len(doc) > 35 else doc
            st.markdown(f'<span class="doc-badge">📄 {short_name}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Manual upload section
    st.markdown("### 📤 Manual Upload")
    uploaded_file = st.file_uploader("Add Additional PDF", type=["pdf"], key="pdf_uploader")
    
    if uploaded_file and st.button("📥 Process & Add", use_container_width=True):
        with st.spinner("Processing..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                
                splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                chunks = splitter.split_documents(docs)
                
                for i, chunk in enumerate(chunks):
                    chunk.metadata["source"] = uploaded_file.name
                    chunk.metadata["chunk_id"] = i
                
                if st.session_state.embeddings is None:
                    st.session_state.embeddings = load_embedding_model()
                
                if st.session_state.vector_store is None:
                    st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
                else:
                    st.session_state.vector_store.add_documents(chunks)
                
                st.session_state.documents.extend(chunks)
                if uploaded_file.name not in st.session_state.pdf_list:
                    st.session_state.pdf_list.append(uploaded_file.name)
                
                os.unlink(tmp_path)
                st.success(f"✅ Added {uploaded_file.name} ({len(chunks)} chunks)")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Admin Panel
    with st.expander("🔐 Admin Panel"):
        admin_pass = st.text_input("Password", type="password", key="admin_pass_input")
        
        if st.button("🔄 Refresh KB", use_container_width=True):
            if admin_pass == st.session_state.admin_password:
                st.success(f"✅ Ready: {len(st.session_state.documents)} chunks")
            else:
                st.error("Wrong password")
        
        if st.button("🗑️ Clear All", use_container_width=True):
            if admin_pass == st.session_state.admin_password:
                st.session_state.vector_store = None
                st.session_state.documents = []
                st.session_state.messages = []
                st.session_state.documents_loaded = False
                st.success("Cleared! Refresh page to reload from GitHub")
                st.rerun()
            else:
                st.error("Wrong password")
    
    st.markdown("---")
    st.caption("👮 Barath R K PDKV | 411623149004 | PRJ-005")

# ============================================================
# MAIN CHAT INTERFACE
# ============================================================

st.markdown("## 💬 Ask Legal Questions")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            st.caption(f"📚 Sources: {', '.join(msg['sources'])}")

prompt = st.chat_input("Ask about IPC sections, punishments, legal procedures...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching..."):
            try:
                # Step 1: Check IPC Database
                offence, details = match_ipc_offence(prompt)
                
                if details:
                    answer = format_ipc_answer(offence, details)
                    st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": []})
                
                # Step 2: Search PDFs
                elif st.session_state.vector_store is not None:
                    results = search_pdf_documents(prompt, top_k=4)
                    
                    if results:
                        answer, sources = extract_answer_from_pdfs(prompt, results)
                        if answer:
                            st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                            if sources:
                                st.caption(f"📚 Sources: {', '.join(sources)}")
                            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
                        else:
                            response = "No highly relevant information found. Try rephrasing."
                            st.markdown(response)
                    else:
                        response = "No relevant information found in documents."
                        st.markdown(response)
                else:
                    response = "⚠️ No documents loaded. Add PDFs to GitHub 'Documents' folder or upload manually."
                    st.markdown(response)
                    
            except Exception as e:
                st.error(f"Error: {e}")

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
    <p>Police Rulebook Assistant | Project PRJ-005 | Auto-loads PDFs from GitHub 'Documents' folder</p>
    <p>🔍 Semantic Search | 📄 PDF Upload | 📚 Citations | ⚡ Real-time Answers</p>
</div>
""", unsafe_allow_html=True)
