import streamlit as st
import tempfile
import os
import requests
from typing import List, Dict

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

st.set_page_config(
    page_title="Police Rulebook Assistant",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme with Red/Green Accents CSS
st.markdown("""
<style>
    /* Dark Theme Variables */
    :root {
        --bg-dark: #0a0e1a;
        --bg-card: #131823;
        --bg-sidebar: #0d1117;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
        --police-blue: #1f6e8c;
        --police-red: #dc2626;
        --police-green: #10b981;
        --accent-red: #ef4444;
        --accent-green: #22c55e;
        --border-color: #21262d;
    }
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main container */
    .stApp {
        background: linear-gradient(135deg, #0a0e1a 0%, #0f1119 100%);
    }
    
    /* Header - Dark Police Style */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%);
        border-radius: 20px;
        margin-bottom: 2rem;
        border: 1px solid var(--border-color);
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #dc2626, #10b981, #dc2626);
    }
    
    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #fff 0%, #dc2626 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .main-header p {
        font-size: 0.95rem;
        color: var(--text-secondary);
    }
    
    .badge-container {
        display: inline-flex;
        gap: 0.5rem;
        margin-top: 0.8rem;
    }
    
    .badge-red {
        background: rgba(220,38,38,0.2);
        color: #ef4444;
        padding: 0.2rem 1rem;
        border-radius: 50px;
        font-size: 0.7rem;
        font-weight: 600;
        border: 1px solid rgba(220,38,38,0.3);
    }
    
    .badge-green {
        background: rgba(16,185,129,0.2);
        color: #10b981;
        padding: 0.2rem 1rem;
        border-radius: 50px;
        font-size: 0.7rem;
        font-weight: 600;
        border: 1px solid rgba(16,185,129,0.3);
    }
    
    /* Chat Messages */
    .stChatMessage {
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        animation: fadeInUp 0.3s ease-out;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(15px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* User message - Red accent */
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, #1a0f0f 0%, #1f1414 100%);
        border: 1px solid rgba(220,38,38,0.3);
        color: #f0f0f0 !important;
        border-radius: 20px 20px 5px 20px;
        box-shadow: 0 4px 12px rgba(220,38,38,0.1);
    }
    
    /* Assistant message - Green accent */
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%);
        border: 1px solid rgba(16,185,129,0.3);
        border-radius: 20px 20px 20px 5px;
        box-shadow: 0 4px 12px rgba(16,185,129,0.1);
    }
    
    /* Sidebar - Dark Theme */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e1a 0%, #0d1117 100%);
        border-right: 1px solid var(--border-color);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary);
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #e6edf3 !important;
    }
    
    /* Stat Cards */
    .stat-card-red {
        background: #131823;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.8rem 0;
        text-align: center;
        border: 1px solid rgba(220,38,38,0.3);
        transition: all 0.3s ease;
    }
    
    .stat-card-red:hover {
        transform: translateY(-2px);
        border-color: #dc2626;
        box-shadow: 0 8px 20px rgba(220,38,38,0.15);
    }
    
    .stat-card-green {
        background: #131823;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.8rem 0;
        text-align: center;
        border: 1px solid rgba(16,185,129,0.3);
        transition: all 0.3s ease;
    }
    
    .stat-card-green:hover {
        transform: translateY(-2px);
        border-color: #10b981;
        box-shadow: 0 8px 20px rgba(16,185,129,0.15);
    }
    
    .stat-number-red {
        font-size: 2rem;
        font-weight: 700;
        color: #dc2626;
    }
    
    .stat-number-green {
        font-size: 2rem;
        font-weight: 700;
        color: #10b981;
    }
    
    .stat-label {
        font-size: 0.7rem;
        color: var(--text-secondary);
        margin-top: 0.3rem;
    }
    
    /* Document Badges */
    .doc-badge-red {
        background: rgba(220,38,38,0.15);
        color: #ef4444;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.25rem;
        border: 1px solid rgba(220,38,38,0.3);
        transition: all 0.2s ease;
    }
    
    .doc-badge-red:hover {
        background: rgba(220,38,38,0.25);
    }
    
    .doc-badge-green {
        background: rgba(16,185,129,0.15);
        color: #10b981;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.25rem;
        border: 1px solid rgba(16,185,129,0.3);
        transition: all 0.2s ease;
    }
    
    .doc-badge-green:hover {
        background: rgba(16,185,129,0.25);
    }
    
    /* Upload Section */
    .upload-card {
        background: #131823;
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 2px dashed rgba(220,38,38,0.4);
        text-align: center;
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
        box-shadow: 0 5px 15px rgba(220,38,38,0.4);
    }
    
    /* Answer Section */
    .answer-section {
        background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%);
        padding: 1.2rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        line-height: 1.7;
        border-left: 4px solid #10b981;
    }
    
    .answer-section p, .answer-section div {
        color: #e6edf3;
    }
    
    /* Source Line */
    .source-line {
        font-size: 0.7rem;
        color: var(--text-secondary);
        margin-top: 1rem;
        padding-top: 0.8rem;
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    
    /* File Uploader */
    .stFileUploader > div {
        background: #0d1117;
        border-radius: 12px;
        padding: 0.5rem;
    }
    
    /* Input Field */
    .stTextInput input {
        border-radius: 30px !important;
        border: 2px solid #21262d !important;
        background: #0d1117 !important;
        color: #e6edf3 !important;
        padding: 0.7rem 1.2rem !important;
        font-size: 0.95rem !important;
    }
    
    .stTextInput input:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 2px rgba(16,185,129,0.2) !important;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: var(--text-secondary);
        font-size: 0.75rem;
        border-top: 1px solid var(--border-color);
        margin-top: 2rem;
    }
    
    /* Divider */
    hr {
        margin: 1rem 0;
        border-color: var(--border-color);
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #dc2626, #10b981);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0d1117;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #dc2626, #10b981);
        border-radius: 10px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #131823;
        border-radius: 10px;
        color: #e6edf3;
    }
    
    /* Info/Warning/Success messages */
    .stAlert {
        background: #131823;
        border-color: var(--border-color);
    }
</style>
""", unsafe_allow_html=True)

# Dark Theme Header with Red/Green Accents
st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Advanced RAG Assistant for Police SOPs, Laws, Cyber Crimes & Citizen Rights</p>
    <div class="badge-container">
        <span class="badge-red">🔴 Semantic Search</span>
        <span class="badge-green">🟢 Multi-Document</span>
        <span class="badge-red">🔴 Real-Time</span>
        <span class="badge-green">🟢 Full Text</span>
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

def search_all_chunks(query: str, all_chunks: List, top_k: int = 30) -> List:
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
        if query.lower() in content:
            score += 0.3
        if score > 0.1:
            scored_chunks.append((score, chunk))
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    return [chunk for score, chunk in scored_chunks[:top_k]]

def generate_comprehensive_answer(query: str, relevant_chunks: List, all_docs: List) -> tuple:
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
        full_content = " ".join([chunk.page_content for chunk in chunks[:8]])
        sentences = full_content.replace('\n', ' ').split('. ')
        relevant_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 40:
                if any(word in sentence.lower() for word in query_words):
                    relevant_sentences.append(sentence)
        seen = set()
        unique_sentences = []
        for sent in relevant_sentences:
            if sent not in seen:
                seen.add(sent)
                unique_sentences.append(sent)
        if unique_sentences:
            for sent in unique_sentences[:6]:
                answer_parts.append(f"> {sent}.")
                answer_parts.append("")
        else:
            best_chunk = max(chunks, key=lambda x: len(x.page_content))
            if best_chunk.page_content[:500]:
                answer_parts.append(f"{best_chunk.page_content[:500]}...")
                answer_parts.append("")
    if answer_parts:
        full_answer = "".join(answer_parts)
        full_answer = full_answer.replace("\n\n\n", "\n\n")
        intro = f"🔍 **Searched through {len(all_docs)} documents**\n\n"
        final_answer = intro + full_answer
        return final_answer, list(set(all_sources))
    return None, []

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🎯 Knowledge Dashboard")
    
    if st.session_state.documents_loaded and st.session_state.pdf_list:
        st.markdown(f"""
        <div class="stat-card-red">
            <div class="stat-number-red">{len(st.session_state.pdf_list)}</div>
            <div class="stat-label">Documents Loaded</div>
        </div>
        <div class="stat-card-green">
            <div class="stat-number-green">{st.session_state.total_chunks_count}</div>
            <div class="stat-label">Text Chunks</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📚 Document Library")
        for doc in st.session_state.pdf_list:
            st.markdown(f'<span class="doc-badge-green">📄 {doc[:35]}{"..." if len(doc) > 35 else ""}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("## 📤 Upload Document")
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Add PDF to Knowledge Base", type=["pdf"], key="pdf_uploader")
    
    if uploaded_file:
        if st.button("📥 Process", use_container_width=True):
            with st.spinner(f"Processing {uploaded_file.name}..."):
                chunks = process_uploaded_pdf(uploaded_file)
                if chunks:
                    if st.session_state.embeddings is None:
                        st.session_state.embeddings = HuggingFaceEmbeddings(
                            model_name="sentence-transformers/all-MiniLM-L6-v2"
                        )
                    add_to_vector_store(chunks)
                    if uploaded_file.name not in st.session_state.pdf_list:
                        st.session_state.pdf_list.append(uploaded_file.name)
                    st.success(f"✅ Added {uploaded_file.name}")
                    st.rerun()
                else:
                    st.error("Processing failed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("## ⚙️ Controls")
    if st.button("🔄 Sync GitHub", use_container_width=True):
        st.session_state.documents_loaded = False
        st.session_state.all_chunks = []
        st.session_state.pdf_list = []
        st.rerun()
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ============================================================
# LOAD DOCUMENTS
# ============================================================

if not st.session_state.documents_loaded:
    with st.spinner("📚 Loading knowledge base from GitHub..."):
        chunks, loaded_files = load_all_documents()
        if chunks:
            if st.session_state.embeddings is None:
                st.session_state.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
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

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask about police procedures, cyber laws, citizen rights, traffic rules...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if st.session_state.total_chunks_count == 0:
            response = "⚠️ **No documents loaded.** Please upload PDFs to the GitHub 'Documents' folder."
            st.markdown(response)
        else:
            with st.spinner(f"🔍 Searching {st.session_state.total_chunks_count} text segments..."):
                try:
                    relevant = search_all_chunks(prompt, st.session_state.all_chunks, top_k=30)
                    if relevant:
                        answer, sources = generate_comprehensive_answer(prompt, relevant, st.session_state.pdf_list)
                        if answer:
                            st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                            if sources:
                                st.markdown(f'<div class="source-line">📚 Sources: {", ".join(sources[:3])}</div>', unsafe_allow_html=True)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        else:
                            response = "No relevant information found. Try rephrasing."
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
<div class="footer">
    👮 Police Rulebook Assistant | Project PRJ-005 | Barath R K PDKV | 411623149004
</div>
""", unsafe_allow_html=True)
