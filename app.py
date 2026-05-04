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

# Premium Custom CSS
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Chat messages */
    .stChatMessage {
        padding: 1.2rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* User message styling */
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 20px 20px 5px 20px;
    }
    
    /* Assistant message styling */
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #e0e0e0;
        border-radius: 20px 20px 20px 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #1e3c72 100%);
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        animation: slideDown 0.5s ease-out;
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        letter-spacing: 2px;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Source line styling */
    .source-line {
        font-size: 0.8rem;
        color: #6c757d !important;
        margin-top: 1rem;
        padding-top: 0.8rem;
        border-top: 1px solid #dee2e6;
        font-style: italic;
    }
    
    /* Detailed answer styling */
    .detailed-answer {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        color: #1a1a2e !important;
        line-height: 1.7;
        font-size: 1rem;
        border-left: 4px solid #2a5298;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        border-right: 1px solid #dee2e6;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #1e3c72 !important;
    }
    
    /* Document badge */
    .doc-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.2rem;
    }
    
    /* Stats card */
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin: 0.5rem 0;
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #2a5298;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: #6c757d;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102,126,234,0.4);
    }
    
    /* Input field styling */
    .stTextInput input, .stTextArea textarea {
        border-radius: 25px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102,126,234,0.2) !important;
    }
    
    /* Loading animation */
    .loading-spinner {
        text-align: center;
        padding: 2rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #6c757d;
        font-size: 0.8rem;
        border-top: 1px solid #dee2e6;
        margin-top: 2rem;
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Animated Header
st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Advanced RAG Assistant for Police SOPs, Complaint Manuals & Citizen Procedures</p>
    <p style="font-size: 0.9rem; margin-top: 0.5rem;">🔍 Searching across all documents | 📚 Complete knowledge base | ⚡ Real-time answers</p>
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
        status_text.markdown(f"📖 **Loading:** `{pdf_info['name']}`...")
        
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

def search_all_chunks(query: str, all_chunks: List, top_k: int = 25) -> List:
    """Search through ALL chunks from ALL PDFs"""
    if not all_chunks:
        return []
    
    query_words = set(query.lower().split())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these', 'those'}
    
    important_words = [w for w in query_words if w not in stop_words and len(w) > 2]
    
    scored_chunks = []
    for chunk in all_chunks:
        content = chunk.page_content.lower()
        score = 0
        
        for word in important_words:
            if word in content:
                score += 1
        
        if important_words and score > 0:
            score = score / len(important_words)
            scored_chunks.append((score, chunk))
    
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    return [chunk for score, chunk in scored_chunks[:top_k]]

def generate_answer_with_full_context(query: str, relevant_chunks: List, all_docs: List) -> tuple:
    """Generate comprehensive answer from ALL relevant chunks"""
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
        
        combined = " ".join([chunk.page_content for chunk in chunks[:5]])
        sentences = combined.split('. ')
        
        relevant_sentences = []
        for sentence in sentences:
            if len(sentence) > 30:
                if any(word in sentence.lower() for word in query_words):
                    relevant_sentences.append(sentence.strip())
        
        seen = set()
        unique = []
        for sent in relevant_sentences:
            if sent not in seen:
                seen.add(sent)
                unique.append(sent)
        
        if unique:
            for sent in unique[:5]:
                answer_parts.append(f"> {sent}")
                answer_parts.append("")
        else:
            preview = chunks[0].page_content[:500]
            if preview:
                answer_parts.append(f"{preview}...")
                answer_parts.append("")
    
    if answer_parts:
        full = "".join(answer_parts)
        full = full.replace("\n\n\n", "\n\n")
        intro = f"🔍 **Searched through {len(all_docs)} documents**\n\n"
        final = intro + full
        return final, list(set(all_sources))
    
    return None, []

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 📚 Knowledge Base")
    
    if st.session_state.documents_loaded and st.session_state.pdf_list:
        st.markdown('<div class="stat-card"><div class="stat-number">{}</div><div class="stat-label">Documents Loaded</div></div>'.format(len(st.session_state.pdf_list)), unsafe_allow_html=True)
        st.markdown('<div class="stat-card"><div class="stat-number">{}</div><div class="stat-label">Text Chunks</div></div>'.format(st.session_state.total_chunks_count), unsafe_allow_html=True)
        
        st.markdown("### 📄 Documents Indexed")
        for doc in st.session_state.pdf_list:
            st.markdown(f'<span class="doc-badge">📄 {doc[:40]}{"..." if len(doc) > 40 else ""}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🔄 Refresh & Reload", use_container_width=True):
        st.session_state.documents_loaded = False
        st.session_state.all_chunks = []
        st.session_state.pdf_list = []
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.markdown("- Ask detailed questions")
    st.markdown("- Be specific for better results")
    st.markdown("- Use keywords from documents")

# ============================================================
# LOAD DOCUMENTS
# ============================================================

if not st.session_state.documents_loaded:
    with st.spinner("📚 Loading all police documents..."):
        chunks, loaded_files = load_all_documents()
        
        if chunks:
            st.session_state.all_chunks = chunks
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
            st.session_state.documents_loaded = True
            st.session_state.pdf_list = loaded_files
            st.session_state.total_chunks_count = len(chunks)
            
            st.balloons()
            st.success(f"✅ **Success!** Loaded {len(loaded_files)} documents with {len(chunks)} text chunks")
            st.info(f"📚 Documents: {', '.join(loaded_files)}")
            st.rerun()
        else:
            st.error("No PDFs found. Please add PDFs to the 'Documents' folder in GitHub.")

# ============================================================
# MAIN CHAT AREA
# ============================================================

st.markdown("## 💬 Ask Questions")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask anything about police procedures, cyber laws, citizen rights...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if not st.session_state.documents_loaded:
            response = "⚠️ **No documents loaded.** Please ensure PDFs are in the 'Documents' folder and click Refresh."
            st.markdown(response)
        else:
            with st.spinner(f"🔍 Searching through {st.session_state.total_chunks_count} chunks across {len(st.session_state.pdf_list)} documents..."):
                try:
                    relevant = search_all_chunks(prompt, st.session_state.all_chunks, top_k=30)
                    
                    if relevant:
                        answer, sources = generate_answer_with_full_context(prompt, relevant, st.session_state.pdf_list)
                        
                        if answer:
                            st.markdown(f'<div class="detailed-answer">{answer}</div>', unsafe_allow_html=True)
                            
                            if sources:
                                st.markdown(f'<div class="source-line">📄 Source documents: {", ".join(sources[:5])}</div>', unsafe_allow_html=True)
                            
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        else:
                            response = f"⚠️ **No relevant information found.**\n\nI searched through {len(st.session_state.pdf_list)} documents but couldn't find content matching your query. Try rephrasing or asking about different topics."
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        response = f"⚠️ **No matches found.**\n\nI analyzed {st.session_state.total_chunks_count} chunks but found nothing relevant. Try different keywords."
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                except Exception as e:
                    st.error(f"Error: {str(e)[:300]}")

# Footer
st.markdown("""
<div class="footer">
    👮 Project PRJ-005 | Police Rulebook Assistant | Barath R K PDKV | 411623149004
</div>
""", unsafe_allow_html=True)
