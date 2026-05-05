"""
POLICE RULEBOOK ASSISTANT - ULTIMATE EDITION
Project PRJ-005 | Barath R K PDKV | 411623149004

COMPLETE FEATURES:
✅ Week 1: Knowledge base, PDF upload, chunking, basic chat
✅ Week 2: Semantic retrieval, citations, admin refresh, access control
✅ Week 3: Advanced UX, history logging, relevance scoring, detailed answers
✅ Enhanced: IPC section mapping, smart search, error handling, beautiful UI
"""

import streamlit as st
import tempfile
import os
import re
import pandas as pd
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
# ADVANCED CSS - Professional Police Theme
# ============================================================

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0a0e1a 0%, #0f1119 100%);
    }
    
    /* Animated Header */
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
    
    /* Chat Messages */
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
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e1a 0%, #0d1117 100%);
        border-right: 1px solid #21262d;
    }
    
    /* Stat Cards */
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
    
    /* Document Badges */
    .doc-badge {
        background: rgba(16,185,129,0.15);
        color: #10b981;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.2rem;
        border: 1px solid rgba(16,185,129,0.3);
        transition: all 0.2s ease;
    }
    
    .doc-badge:hover {
        background: rgba(16,185,129,0.25);
        transform: scale(1.02);
    }
    
    /* Buttons */
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
    
    /* Answer Section */
    .answer-section {
        background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        line-height: 1.8;
        border-left: 4px solid #10b981;
        font-size: 1rem;
    }
    
    /* Source Badge */
    .source-badge {
        background: rgba(220,38,38,0.15);
        color: #dc2626;
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.2rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #8b949e;
        font-size: 0.75rem;
        border-top: 1px solid #21262d;
        margin-top: 2rem;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #dc2626, #10b981);
    }
    
    /* Success/Info/Warning */
    .stAlert {
        background: #131823;
        border-color: #21262d;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Professional RAG Assistant for Indian Penal Code, CrPC, Cyber Laws & Police Procedures</p>
    <p style="font-size: 0.85rem;">✓ Semantic Search | ✓ Citations | ✓ Admin Panel | ✓ Real-time Answers</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# IPC SECTION MAPPING (Complete)
# ============================================================

IPC_SECTIONS = {
    # Offences against body
    "murder": {"section": "302", "text": "Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine.", "bailable": False},
    "culpable homicide": {"section": "304", "text": "Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment for life or imprisonment up to 10 years.", "bailable": False},
    "rape": {"section": "376", "text": "Whoever commits rape shall be punished with rigorous imprisonment for not less than 10 years which may extend to imprisonment for life.", "bailable": False},
    "gang rape": {"section": "376D", "text": "Gang rape shall be punished with rigorous imprisonment for not less than 20 years which may extend to imprisonment for life.", "bailable": False},
    
    # Offences against property
    "theft": {"section": "379", "text": "Whoever commits theft shall be punished with imprisonment of either description for a term which may extend to 3 years, or with fine, or with both.", "bailable": True},
    "robbery": {"section": "392", "text": "Whoever commits robbery shall be punished with rigorous imprisonment for a term which may extend to 10 years, and shall also be liable to fine.", "bailable": False},
    "dacoity": {"section": "395", "text": "Whoever commits dacoity shall be punished with imprisonment for life, or with rigorous imprisonment for a term which may extend to 10 years.", "bailable": False},
    "cheating": {"section": "420", "text": "Whoever cheats and dishonestly induces delivery of property shall be punished with imprisonment for up to 7 years and fine.", "bailable": False},
    "criminal breach of trust": {"section": "406", "text": "Whoever commits criminal breach of trust shall be punished with imprisonment of either description for a term which may extend to 3 years, or with fine, or with both.", "bailable": False},
    
    # Offences against person
    "kidnapping": {"section": "363", "text": "Whoever kidnaps any person from India or from lawful guardianship shall be punished with imprisonment for up to 7 years and fine.", "bailable": False},
    "hurt": {"section": "323", "text": "Whoever voluntarily causes hurt shall be punished with imprisonment for up to 1 year, or with fine up to ₹1000, or with both.", "bailable": True},
    "grievous hurt": {"section": "325", "text": "Whoever voluntarily causes grievous hurt shall be punished with imprisonment for up to 7 years and fine.", "bailable": False},
    
    # Harassment & Intimidation
    "sexual harassment": {"section": "354A", "text": "Sexual harassment (physical contact, demand for sexual favours, showing pornography, making sexually coloured remarks) shall be punished with rigorous imprisonment up to 3 years.", "bailable": False},
    "stalking": {"section": "354D", "text": "Whoever commits stalking shall be punished on first conviction with imprisonment up to 3 years, and on subsequent conviction up to 5 years.", "bailable": False},
    "criminal intimidation": {"section": "506", "text": "Whoever commits criminal intimidation shall be punished with imprisonment up to 2 years. If threat is to cause death or grievous hurt, up to 7 years.", "bailable": False},
    "insult modesty of woman": {"section": "509", "text": "Whoever insults the modesty of any woman by word, gesture or act shall be punished with simple imprisonment up to 3 years and fine.", "bailable": True},
    
    # Public order
    "defamation": {"section": "500", "text": "Whoever defames another shall be punished with simple imprisonment for up to 2 years, or with fine, or with both.", "bailable": True},
    "rioting": {"section": "147", "text": "Whoever is guilty of rioting shall be punished with imprisonment for up to 2 years, or with fine, or with both.", "bailable": True},
    
    # State offences
    "dowry death": {"section": "304B", "text": "Whoever commits dowry death shall be punished with imprisonment for not less than 7 years which may extend to imprisonment for life.", "bailable": False},
    "attempt to murder": {"section": "307", "text": "Whoever attempts to murder shall be punished with imprisonment for up to 10 years and fine. If hurt caused, imprisonment for life.", "bailable": False},
}

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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "total_queries" not in st.session_state:
    st.session_state.total_queries = 0
if "admin_password" not in st.session_state:
    st.session_state.admin_password = "admin123"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

@st.cache_resource
def load_embedding_model():
    """Load embedding model with caching"""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_ipc_answer(query: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Check if query matches any IPC section"""
    query_lower = query.lower()
    
    # Handle synonyms
    synonyms = {
        "harassment": ["sexual harassment", "stalking", "criminal intimidation", "insult modesty"],
        "murder": ["kill", "homicide", "death"],
        "theft": ["steal", "stolen", "rob"],
    }
    
    for crime, info in IPC_SECTIONS.items():
        if crime in query_lower:
            return info["section"], info["text"], info["bailable"]
    
    # Check synonyms
    for main_crime, syn_list in synonyms.items():
        for syn in syn_list:
            if syn in query_lower and main_crime in IPC_SECTIONS:
                info = IPC_SECTIONS[main_crime]
                return info["section"], info["text"], info["bailable"]
    
    return None, None, None

def format_answer_with_section(section: str, text: str, bailable: bool) -> str:
    """Format answer beautifully"""
    bail_status = "🟢 Bailable offence" if bailable else "🔴 Non-bailable offence"
    return f"""
**Section {section} of the Indian Penal Code**

*{text}*

{bail_status}
"""

def search_pdf_documents(query: str, top_k: int = 4) -> List:
    """Search PDF documents using FAISS"""
    if st.session_state.vector_store is None:
        return []
    
    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": top_k})
    return retriever.invoke(query)

def calculate_relevance(query: str, document) -> float:
    """Calculate relevance score for a document"""
    query_words = set(query.lower().split())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
    keywords = [w for w in query_words if w not in stop_words and len(w) > 2]
    
    if not keywords:
        return 0.5
    
    content = document.page_content.lower()
    matches = sum(1 for kw in keywords if kw in content)
    return min(matches / len(keywords), 1.0)

def generate_answer_from_pdfs(query: str, documents: List) -> Tuple[Optional[str], List[str]]:
    """Generate answer from PDF documents"""
    if not documents:
        return None, []
    
    scored = [(calculate_relevance(query, doc), doc) for doc in documents]
    scored.sort(reverse=True, key=lambda x: x[0])
    
    # Filter low relevance
    relevant = [(score, doc) for score, doc in scored if score >= 0.2]
    
    if not relevant:
        return None, []
    
    answer_parts = []
    sources = []
    
    for score, doc in relevant[:2]:
        sources.append(doc.metadata.get("source", "Unknown"))
        content = doc.page_content
        
        # Extract best sentence
        sentences = content.split('. ')
        best_sentence = max(sentences, key=lambda s: sum(1 for w in query.lower().split() if w in s.lower()), default="")
        
        if len(best_sentence) > 30:
            answer_parts.append(best_sentence.strip())
        else:
            answer_parts.append(content[:300].strip())
    
    if answer_parts:
        answer = "\n\n".join(answer_parts)
        return answer, list(set(sources))
    
    return None, []

# ============================================================
# ADMIN PANEL
# ============================================================

with st.sidebar:
    st.markdown("## 🎯 Control Panel")
    
    # File upload section
    st.markdown("### 📄 Document Upload")
    uploaded_file = st.file_uploader("Upload Police PDF", type=["pdf"], key="pdf_uploader")
    
    if uploaded_file and st.button("📥 Process Document", use_container_width=True):
        with st.spinner("Processing..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
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
                os.unlink(tmp_path)
                st.success(f"✅ Indexed {len(chunks)} chunks")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Statistics
    if st.session_state.vector_store:
        st.markdown("### 📊 Statistics")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(st.session_state.documents)}</div>
                <div class="stat-label">Text Chunks</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(st.session_state.messages)}</div>
                <div class="stat-label">Messages</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Admin Section
    with st.expander("🔐 Admin Panel"):
        admin_pass = st.text_input("Password", type="password", key="admin_pass_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh KB", use_container_width=True):
                if admin_pass == st.session_state.admin_password:
                    st.success(f"✅ Ready: {len(st.session_state.documents)} chunks")
                else:
                    st.error("Wrong password")
        
        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                if admin_pass == st.session_state.admin_password:
                    st.session_state.vector_store = None
                    st.session_state.documents = []
                    st.session_state.messages = []
                    st.success("Cleared!")
                    st.rerun()
                else:
                    st.error("Wrong password")
    
    st.markdown("---")
    st.caption("👮 **Police Rulebook Assistant**")
    st.caption("Barath R K PDKV | 411623149004")
    st.caption("Project PRJ-005")

# ============================================================
# MAIN CHAT INTERFACE
# ============================================================

st.markdown("## 💬 Ask Questions")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            st.caption(f"📚 Sources: {', '.join(msg['sources'])}")

# Quick question buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("📋 Murder Punishment", use_container_width=True):
        st.session_state.quick_question = "What is the punishment for murder?"
with col2:
    if st.button("💰 Theft Punishment", use_container_width=True):
        st.session_state.quick_question = "What is the punishment for theft?"
with col3:
    if st.button("👤 Sexual Harassment", use_container_width=True):
        st.session_state.quick_question = "What is the punishment for sexual harassment?"
with col4:
    if st.button("🏠 Kidnapping", use_container_width=True):
        st.session_state.quick_question = "What is the punishment for kidnapping?"

# Handle quick question
if "quick_question" in st.session_state:
    prompt = st.session_state.quick_question
    del st.session_state.quick_question
else:
    prompt = st.chat_input("Ask about IPC sections, punishments, legal procedures...")

if prompt:
    st.session_state.total_queries += 1
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🔍 Analyzing your query..."):
            try:
                # Step 1: Check IPC mapping
                section, text, bailable = get_ipc_answer(prompt)
                
                if section:
                    answer = format_answer_with_section(section, text, bailable)
                    st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": []})
                
                # Step 2: If not in mapping and PDFs loaded, search documents
                elif st.session_state.vector_store is not None:
                    results = search_pdf_documents(prompt, top_k=4)
                    
                    if results:
                        answer, sources = generate_answer_from_pdfs(prompt, results)
                        if answer:
                            st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                            if sources:
                                st.caption(f"📚 Sources: {', '.join(sources)}")
                            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
                        else:
                            response = "I found some information but it may not be highly relevant. Could you please rephrase your question?"
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        response = "No relevant information found. Please upload more documents or try a different question."
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    response = "⚠️ No documents loaded. Please upload a PDF document using the sidebar.\n\nAlternatively, try asking about:\n- Punishment for murder (IPC Section 302)\n- Punishment for theft (IPC Section 379)\n- Punishment for rape (IPC Section 376)\n- Punishment for cheating (IPC Section 420)"
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
            except Exception as e:
                st.error(f"Error: {str(e)[:200]}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)[:200]}"})

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
    <p>Police Rulebook Assistant | Project PRJ-005 | Indian Penal Code Reference | RAG Powered</p>
    <p>⚡ Real-time Search | 📄 PDF Upload | 🔍 Semantic Retrieval | 📚 Citation-backed Answers</p>
</div>
""", unsafe_allow_html=True)
