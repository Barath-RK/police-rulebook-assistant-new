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

# Police Light Theme CSS
st.markdown("""
<style>
    /* Police Light Theme - Professional & Clean */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fc 0%, #e8eef5 100%);
    }
    
    /* Header - Police style */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border-bottom: 4px solid #ffd700;
    }
    
    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    .police-badge {
        background: #ffd700;
        color: #1e3a5f;
        padding: 0.2rem 1rem;
        border-radius: 50px;
        display: inline-block;
        margin-top: 0.5rem;
        font-weight: 600;
        font-size: 0.8rem;
    }
    
    /* Chat Messages */
    .stChatMessage {
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* User message */
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
        color: white !important;
        border-radius: 18px 18px 5px 18px;
    }
    
    /* Assistant message */
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 18px 18px 18px 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Sidebar - Light Police Theme */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f0f4f8 100%);
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #1e3a5f !important;
    }
    
    /* Stat Cards */
    .stat-card {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.8rem 0;
        text-align: center;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    
    .stat-label {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 0.3rem;
    }
    
    /* Document Badges */
    .doc-badge {
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.25rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }
    
    /* Upload Section */
    .upload-card {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 2px dashed #1e3a5f;
        text-align: center;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(30,58,95,0.3);
    }
    
    /* Answer Section */
    .answer-section {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 4px solid #1e3a5f;
        line-height: 1.7;
    }
    
    /* Source Line */
    .source-line {
        font-size: 0.7rem;
        color: #64748b;
        margin-top: 1rem;
        padding-top: 0.8rem;
        border-top: 1px solid #e2e8f0;
    }
    
    /* File Uploader */
    .stFileUploader > div {
        background: #f8fafc;
        border-radius: 12px;
        padding: 0.5rem;
    }
    
    /* Input Field */
    .stTextInput input {
        border-radius: 30px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 0.7rem 1.2rem !important;
        font-size: 0.95rem !important;
    }
    
    .stTextInput input:focus {
        border-color: #1e3a5f !important;
        box-shadow: 0 0 0 2px rgba(30,58,95,0.1) !important;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #64748b;
        font-size: 0.75rem;
        border-top: 1px solid #e2e8f0;
        margin-top: 2rem;
    }
    
    /* Divider */
    hr {
        margin: 1rem 0;
        border-color: #e2e8f0;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #f8fafc;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Police Light Theme Header
st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Intelligent RAG Assistant for Police Documents, SOPs, Laws & Procedures</p>
    <div class="police-badge">🔍 Full Document Search • 📚 Complete Knowledge Base</div>
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

def load_pdf_from_url(url: str, filename: str) -> List:
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
    except Exception as e:
        return []

def process_uploaded_pdf(uploaded_file):
    """Process uploaded PDF and extract chunks"""
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
    except Exception as e:
        return []

def add_to_vector_store(chunks):
    """Add chunks to existing vector store"""
    if st.session_state.vector_store is None:
        st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
    else:
        st.session_state.vector_store.add_documents(chunks)
    
    st.session_state.all_chunks.extend(chunks)
    st.session_state.total_chunks_count = len(st.session_state.all_chunks)

def load_all_documents():
    """Load ALL PDFs from GitHub Documents folder"""
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
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, pdf_info in enumerate(pdf_files):
        status_text.markdown(f"📖 Loading: `{pdf_info['name']}`...")
        
        documents = load_pdf_from_url(pdf_info['raw_url'], pdf_info['name'])
        
        if documents:
            chunks = splitter.split_documents(documents)
            for j, chunk in enumerate(chunks):
                chunk.metadata["source"] = pdf_info['name']
                chunk.metadata["chunk_id"] = j
                chunk.metadata["total_chunks"] = len(chunks)
            all_chunks.extend(chunks)
            loaded_files.append(pdf_info['name'])
        
        progress_bar.progress((i + 1) / len(pdf_files))
    
    status_text.empty()
    progress_bar.empty()
    
    return all_chunks, loaded_files

def search_all_chunks(query: str, all_chunks: List, top_k: int = 30) -> List:
    """Search through ALL chunks from ALL PDFs - Deep search"""
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
        score = 0
        for word in important_words:
            if word in content:
                score += 1
        score = score / len(important_words) if important_words else 0
        
        # Bonus for exact phrase matches
        if query.lower() in content:
            score += 0.3
        
        if score > 0.1:
            scored_chunks.append((score, chunk))
    
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    return [chunk for score, chunk in scored_chunks[:top_k]]

def generate_comprehensive_answer(query: str, relevant_chunks: List, all_docs: List) -> tuple:
    """Generate comprehensive answer from ALL relevant chunks - FULL DOCUMENT EXTRACTION"""
    if not relevant_chunks:
        return None, []
    
    # Group by source document
    sources_dict = {}
    for chunk in relevant_chunks:
        source = chunk.metadata.get("source", "Unknown")
        if source not in sources_dict:
            sources_dict[source] = []
        sources_dict[source].append(chunk)
    
    answer_parts = []
    all_sources = []
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    for source, chunks in sources_dict.items():
        all_sources.append(source)
        answer_parts.append(f"\n### 📄 **{source}**\n")
        
        # Combine all chunks from this source for context
        full_content = " ".join([chunk.page_content for chunk in chunks[:8]])
        
        # Split into sentences
        sentences = full_content.replace('\n', ' ').split('. ')
        
        # Find relevant sentences
        relevant_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 40:  # Meaningful sentence length
                sentence_lower = sentence.lower()
                # Check if sentence contains query words
                if any(word in sentence_lower for word in query_words):
                    relevant_sentences.append(sentence)
                # Also check for related context
                elif len(query_words) > 0 and len(sentence) < 500:
                    relevant_sentences.append(sentence)
        
        # Remove duplicates
        seen = set()
        unique_sentences = []
        for sent in relevant_sentences:
            if sent not in seen:
                seen.add(sent)
                unique_sentences.append(sent)
        
        if unique_sentences:
            # Take up to 6 sentences per document for comprehensive answer
            for sent in unique_sentences[:6]:
                answer_parts.append(f"> {sent}.")
                answer_parts.append("")
        else:
            # Fallback: take first 400 chars of most relevant chunk
            best_chunk = max(chunks, key=lambda x: len(x.page_content))
            preview = best_chunk.page_content[:500]
            if preview:
                answer_parts.append(f"{preview}...")
                answer_parts.append("")
    
    if answer_parts:
        full_answer = "".join(answer_parts)
        full_answer = full_answer.replace("\n\n\n", "\n\n")
        
        # Add introduction showing search scope
        intro = f"🔍 **Searched through {len(all_docs)} documents ({len(relevant_chunks)} relevant sections found)**\n\n"
        intro += f"**Your question:** \"{query}\"\n\n"
        intro += "---\n\n"
        
        final_answer = intro + full_answer
        return final_answer, list(set(all_sources))
    
    return None, []

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 📋 Knowledge Dashboard")
    
    if st.session_state.documents_loaded and st.session_state.pdf_list:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(st.session_state.pdf_list)}</div>
            <div class="stat-label">Documents Loaded</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{st.session_state.total_chunks_count}</div>
            <div class="stat-label">Text Chunks</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📚 Document Library")
        for doc in st.session_state.pdf_list:
            st.markdown(f'<span class="doc-badge" title="{doc}">📄 {doc[:35]}{"..." if len(doc) > 35 else ""}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Upload Section
    st.markdown("## 📤 Upload Document")
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Add PDF to Knowledge Base", type=["pdf"], key="pdf_uploader")
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        with col1:
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
        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("## ⚙️ Controls")
    if st.button("🔄 Sync with GitHub", use_container_width=True):
        with st.spinner("Syncing..."):
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
            st.success(f"✅ Loaded {len(loaded_files)} documents from GitHub")
            st.rerun()

# ============================================================
# MAIN CHAT AREA
# ============================================================

st.markdown("## 💬 Ask Questions")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask any question about police procedures, laws, cyber crimes, citizen rights...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if st.session_state.total_chunks_count == 0:
            response = "⚠️ **No documents loaded.** Please upload PDFs to the GitHub 'Documents' folder or use the sidebar uploader."
            st.markdown(response)
        else:
            with st.spinner(f"🔍 Searching through {st.session_state.total_chunks_count} text segments across {len(st.session_state.pdf_list)} documents..."):
                try:
                    relevant_chunks = search_all_chunks(prompt, st.session_state.all_chunks, top_k=35)
                    
                    if relevant_chunks:
                        answer, sources = generate_comprehensive_answer(prompt, relevant_chunks, st.session_state.pdf_list)
                        
                        if answer:
                            st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                            
                            if sources:
                                source_badges = "".join([f'<span class="doc-badge">📄 {s[:30]}{"..." if len(s) > 30 else ""}</span>' for s in sources[:4]])
                                st.markdown(f'<div class="source-line">📚 Sources: {source_badges}</div>', unsafe_allow_html=True)
                            
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        else:
                            response = "No relevant information found. Try rephrasing your question with different keywords."
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        response = "No matches found. Try different keywords or upload more relevant documents."
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
