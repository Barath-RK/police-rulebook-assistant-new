import streamlit as st
import tempfile
import os
import requests
from typing import List, Dict
import base64
from io import BytesIO

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

st.set_page_config(
    page_title="Police Rulebook Assistant - Professional Edition",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Professional CSS
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container */
    .main {
        background: #f0f2f6;
    }
    
    /* Animated Header */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        border-radius: 25px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 20px 35px rgba(0,0,0,0.2);
        animation: gradientShift 3s ease infinite;
        background-size: 200% 200%;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .main-header h1 {
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    .badge-container {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        padding: 0.3rem 1rem;
        border-radius: 50px;
        margin-top: 0.5rem;
    }
    
    /* Chat Messages - Premium */
    .stChatMessage {
        padding: 1.2rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        animation: fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* User message - sleek right side */
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 20px 20px 5px 20px;
        box-shadow: 0 4px 15px rgba(102,126,234,0.3);
    }
    
    /* Assistant message - glassmorphism */
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 20px 20px 20px 5px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
    }
    
    /* Sidebar - Dark Premium */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: none;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e0e0e0;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    
    /* Stat Card */
    .stat-card-premium {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.8rem 0;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.15);
        transition: all 0.3s ease;
    }
    
    .stat-card-premium:hover {
        background: rgba(255,255,255,0.15);
        transform: translateY(-2px);
    }
    
    .stat-number-premium {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .stat-label-premium {
        font-size: 0.8rem;
        color: #a0a0a0;
        margin-top: 0.3rem;
    }
    
    /* Document Badge */
    .doc-badge-premium {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 25px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.25rem;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .doc-badge-premium:hover {
        transform: scale(1.03);
        box-shadow: 0 2px 8px rgba(102,126,234,0.4);
    }
    
    /* Upload Section Premium */
    .upload-section-premium {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 2px dashed rgba(102,126,234,0.5);
        transition: all 0.3s ease;
    }
    
    .upload-section-premium:hover {
        border-color: #667eea;
        background: rgba(255,255,255,0.08);
    }
    
    /* Button Premium */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102,126,234,0.4);
    }
    
    /* Answer Section */
    .detailed-answer-premium {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        padding: 1.5rem;
        border-radius: 20px;
        margin: 0.5rem 0;
        color: #1a1a2e;
        line-height: 1.8;
        font-size: 1rem;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }
    
    /* Source Line */
    .source-line-premium {
        font-size: 0.75rem;
        color: #888;
        margin-top: 1rem;
        padding-top: 0.8rem;
        border-top: 1px solid rgba(0,0,0,0.1);
        font-style: italic;
    }
    
    /* File Uploader */
    .stFileUploader {
        background: transparent;
        border: none;
    }
    
    .stFileUploader > div {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* Input Field */
    .stTextInput input {
        border-radius: 30px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 0.8rem 1.2rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.2) !important;
    }
    
    /* Footer */
    .footer-premium {
        text-align: center;
        padding: 1.5rem;
        color: #888;
        font-size: 0.8rem;
        border-top: 1px solid rgba(0,0,0,0.05);
        margin-top: 2rem;
    }
    
    /* Divider */
    hr {
        margin: 1rem 0;
        border-color: rgba(255,255,255,0.1);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Animated Header
st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Enterprise-Grade RAG Assistant for Law Enforcement Documents</p>
    <div class="badge-container">
        <span style="font-size: 0.8rem;">🔍 Semantic Search • 📄 Multi-Document • ⚡ Real-Time</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "documents_loaded" not in st.session_state:
    st.session_state.documents_loaded = False
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None
if "all_chunks" not in st.session_state:
    st.session_state.all_chunks = []
if "pdf_list" not in st.session_state:
    st.session_state.pdf_list = []
if "total_chunks_count" not in st.session_state:
    st.session_state.total_chunks_count = 0

# ============================================================
# GITHUB CONFIGURATION
# ============================================================

GITHUB_USERNAME = "Barath-RK"
GITHUB_REPO = "police-rulebook-assistant-new"
GITHUB_BRANCH = "main"
DOCUMENTS_FOLDER = "Documents"

RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{DOCUMENTS_FOLDER}/"

# ============================================================
# FUNCTIONS
# ============================================================

def get_pdf_files_from_github():
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
    except:
        return []

def load_pdf_from_url(url: str, filename: str) -> List:
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

def process_uploaded_pdf(uploaded_file):
    try:
        file_bytes = uploaded_file.getvalue()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name
        
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        
        if not documents:
            return []
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_documents(documents)
        
        for j, chunk in enumerate(chunks):
            chunk.metadata["source"] = uploaded_file.name
            chunk.metadata["chunk_id"] = j
            chunk.metadata["total_chunks"] = len(chunks)
        
        os.unlink(tmp_path)
        return chunks
    except:
        return []

def add_to_vector_store(chunks):
    if st.session_state.vector_store is None:
        st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
    else:
        st.session_state.vector_store.add_documents(chunks)
    
    st.session_state.all_chunks.extend(chunks)
    st.session_state.total_chunks_count = len(st.session_state.all_chunks)

def load_all_documents():
    all_chunks = []
    loaded_files = []
    
    pdf_files = get_pdf_files_from_github()
    
    if not pdf_files:
        return [], []
    
    if st.session_state.embeddings is None:
        st.session_state.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    for pdf_info in pdf_files:
        documents = load_pdf_from_url(pdf_info['raw_url'], pdf_info['name'])
        
        if documents:
            chunks = splitter.split_documents(documents)
            for j, chunk in enumerate(chunks):
                chunk.metadata["source"] = pdf_info['name']
                chunk.metadata["chunk_id"] = j
                chunk.metadata["total_chunks"] = len(chunks)
            all_chunks.extend(chunks)
            loaded_files.append(pdf_info['name'])
    
    return all_chunks, loaded_files

def search_all_chunks(query: str, all_chunks: List, top_k: int = 20) -> List:
    if not all_chunks:
        return []
    
    query_words = set(query.lower().split())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these', 'those'}
    
    important_words = [w for w in query_words if w not in stop_words and len(w) > 2]
    
    if not important_words:
        return all_chunks[:top_k]
    
    scored_chunks = []
    for chunk in all_chunks:
        content = chunk.page_content.lower()
        score = sum(1 for word in important_words if word in content) / len(important_words)
        if score > 0:
            scored_chunks.append((score, chunk))
    
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    return [chunk for score, chunk in scored_chunks[:top_k]]

def generate_answer_with_full_context(query: str, relevant_chunks: List, all_docs: List) -> tuple:
    if not relevant_chunks:
        return None, []
    
    sources_dict = {}
    for chunk in relevant_chunks:
        source = chunk.metadata.get("source", "Unknown")
        if source not in sources_dict:
            sources_dict[source] = []
        sources_dict[source].append(chunk)
    
    answer_parts = []
    all_sources = []
    query_words = set(query.lower().split())
    
    for source, chunks in sources_dict.items():
        all_sources.append(source)
        answer_parts.append(f"\n### 📄 **{source}**\n")
        
        combined = " ".join([chunk.page_content for chunk in chunks[:3]])
        sentences = combined.split('. ')
        
        relevant_sentences = []
        for sentence in sentences:
            if len(sentence) > 30:
                if any(word in sentence.lower() for word in query_words):
                    relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            for sent in relevant_sentences[:3]:
                answer_parts.append(f"> {sent}")
                answer_parts.append("")
        else:
            if chunks[0].page_content[:300]:
                answer_parts.append(f"{chunks[0].page_content[:300]}...")
                answer_parts.append("")
    
    if answer_parts:
        full = "".join(answer_parts)
        full = full.replace("\n\n\n", "\n\n")
        intro = f"🔍 **Searched through {len(all_docs)} documents**\n\n"
        return intro + full, list(set(all_sources))
    
    return None, []

# ============================================================
# SIDEBAR - Advanced Professional
# ============================================================

with st.sidebar:
    st.markdown("## 🎯 Knowledge Control Panel")
    st.markdown("---")
    
    # Stats Cards
    if st.session_state.documents_loaded and st.session_state.pdf_list:
        st.markdown(f"""
        <div class="stat-card-premium">
            <div class="stat-number-premium">{len(st.session_state.pdf_list)}</div>
            <div class="stat-label-premium">Documents Indexed</div>
        </div>
        <div class="stat-card-premium">
            <div class="stat-number-premium">{st.session_state.total_chunks_count}</div>
            <div class="stat-label-premium">Text Chunks</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📚 Document Library")
        for doc in st.session_state.pdf_list:
            short_name = doc[:28] + "..." if len(doc) > 28 else doc
            st.markdown(f'<span class="doc-badge-premium">📄 {short_name}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Upload Section
    st.markdown("## 📤 Upload Manager")
    uploaded_file = st.file_uploader("Upload PDF Document", type=["pdf"], key="pdf_uploader")
    
    if uploaded_file:
        if st.button("Process & Index", use_container_width=True):
            with st.spinner(f"Analyzing {uploaded_file.name}..."):
                chunks = process_uploaded_pdf(uploaded_file)
                if chunks:
                    if st.session_state.embeddings is None:
                        st.session_state.embeddings = HuggingFaceEmbeddings(
                            model_name="sentence-transformers/all-MiniLM-L6-v2"
                        )
                    add_to_vector_store(chunks)
                    if uploaded_file.name not in st.session_state.pdf_list:
                        st.session_state.pdf_list.append(uploaded_file.name)
                    st.success(f"✅ Indexed {uploaded_file.name}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Processing failed")
    
    st.markdown("---")
    
    # Actions
    st.markdown("## ⚙️ Actions")
    if st.button("🔄 Sync with GitHub", use_container_width=True):
        with st.spinner("Syncing..."):
            st.session_state.documents_loaded = False
            st.session_state.all_chunks = []
            st.session_state.pdf_list = []
            st.rerun()
    
    if st.button("🗑️ Clear Session", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # Tips
    st.markdown("## 💡 Pro Tips")
    st.info("• Ask specific questions\n• Use keywords from documents\n• Upload PDFs for custom knowledge")

# ============================================================
# LOAD DOCUMENTS
# ============================================================

if not st.session_state.documents_loaded:
    with st.spinner("Loading knowledge base..."):
        chunks, loaded_files = load_all_documents()
        
        if chunks:
            st.session_state.all_chunks = chunks
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
            st.session_state.documents_loaded = True
            st.session_state.pdf_list = loaded_files
            st.session_state.total_chunks_count = len(chunks)
            st.success(f"✅ Loaded {len(loaded_files)} documents")
            st.rerun()

# ============================================================
# MAIN CHAT AREA
# ============================================================

st.markdown("## 💬 Intelligent Document Chat")

# Chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input
prompt = st.chat_input("Ask a question about police procedures, laws, or regulations...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if st.session_state.total_chunks_count == 0:
            response = "No knowledge base loaded. Please upload documents to begin."
            st.markdown(response)
        else:
            with st.spinner(f"Analyzing {st.session_state.total_chunks_count} text segments..."):
                try:
                    relevant = search_all_chunks(prompt, st.session_state.all_chunks, top_k=20)
                    
                    if relevant:
                        answer, sources = generate_answer_with_full_context(prompt, relevant, st.session_state.pdf_list)
                        
                        if answer:
                            st.markdown(f'<div class="detailed-answer-premium">{answer}</div>', unsafe_allow_html=True)
                            
                            if sources:
                                source_text = ", ".join(sources[:3])
                                st.markdown(f'<div class="source-line-premium">📄 Sources: {source_text}</div>', unsafe_allow_html=True)
                            
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        else:
                            response = "No relevant information found. Try rephrasing your question."
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        response = "No matches found. Try different keywords."
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                except Exception as e:
                    st.error(f"Error: {str(e)[:200]}")

# Footer
st.markdown("""
<div class="footer-premium">
    👮 Police Rulebook Assistant | Project PRJ-005 | Barath R K PDKV | 411623149004
</div>
""", unsafe_allow_html=True)
