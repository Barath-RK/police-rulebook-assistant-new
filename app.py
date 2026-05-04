import streamlit as st
import tempfile
import os
import requests
from typing import List, Dict
import re

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

# Dark Theme CSS
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0f1119 100%); }
    .main-header { text-align: center; padding: 2rem; background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%); border-radius: 20px; margin-bottom: 2rem; border: 1px solid #21262d; position: relative; overflow: hidden; }
    .main-header::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #dc2626, #10b981, #dc2626); }
    .main-header h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.5rem; background: linear-gradient(135deg, #fff 0%, #dc2626 50%, #10b981 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .main-header p { font-size: 0.95rem; color: #8b949e; }
    div[data-testid="stChatMessage"][data-testid*="user"] { background: linear-gradient(135deg, #1a0f0f 0%, #1f1414 100%); border: 1px solid rgba(220,38,38,0.3); color: #f0f0f0 !important; border-radius: 20px 20px 5px 20px; }
    div[data-testid="stChatMessage"][data-testid*="assistant"] { background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%); border: 1px solid rgba(16,185,129,0.3); border-radius: 20px 20px 20px 5px; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0e1a 0%, #0d1117 100%); border-right: 1px solid #21262d; }
    .stat-card-red { background: #131823; border-radius: 15px; padding: 1rem; margin: 0.8rem 0; text-align: center; border: 1px solid rgba(220,38,38,0.3); }
    .stat-card-green { background: #131823; border-radius: 15px; padding: 1rem; margin: 0.8rem 0; text-align: center; border: 1px solid rgba(16,185,129,0.3); }
    .stat-number-red { font-size: 2rem; font-weight: 700; color: #dc2626; }
    .stat-number-green { font-size: 2rem; font-weight: 700; color: #10b981; }
    .stat-label { font-size: 0.7rem; color: #8b949e; margin-top: 0.3rem; }
    .doc-badge { background: rgba(16,185,129,0.15); color: #10b981; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; margin: 0.25rem; border: 1px solid rgba(16,185,129,0.3); }
    .upload-card { background: #131823; border-radius: 15px; padding: 1rem; margin-bottom: 1rem; border: 2px dashed rgba(220,38,38,0.4); text-align: center; }
    .stButton button { background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; border: none; border-radius: 10px; padding: 0.5rem 1rem; font-weight: 600; width: 100%; }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(220,38,38,0.4); }
    .answer-section { background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%); padding: 1.2rem; border-radius: 15px; margin: 0.5rem 0; line-height: 1.7; border-left: 4px solid #10b981; color: #e6edf3; }
    .stTextInput input { border-radius: 30px !important; border: 2px solid #21262d !important; background: #0d1117 !important; color: #e6edf3 !important; padding: 0.7rem 1.2rem !important; }
    .footer { text-align: center; padding: 1.5rem; color: #8b949e; font-size: 0.75rem; border-top: 1px solid #21262d; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Complete Legal Reference for IPC, CrPC, Cyber Laws & Police Procedures</p>
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

def smart_search_with_priority(query: str, all_chunks: List, top_k: int = 15) -> List:
    """Smart search that prioritizes IPC/CrPC for crime-related questions"""
    query_lower = query.lower()
    
    # Define QUESTION TYPES to identify which PDF to prioritize
    crime_keywords = [
        "murder", "theft", "robbery", "dacoity", "rape", "assault", "hurt", 
        "kidnapping", "cheating", "forgery", "extortion", "criminal breach",
        "mischief", "trespass", "defamation", "punishment", "offence"
    ]
    
    ipc_keywords = ["ipc", "indian penal code", "section 3", "section 302"]
    
    # Check if question is about crimes/punishments
    is_crime_question = any(keyword in query_lower for keyword in crime_keywords)
    is_ipc_question = any(keyword in query_lower for keyword in ipc_keywords) or is_crime_question
    
    cyber_keywords = ["cyber", "it act", "hacking", "phishing", "data protection", "online fraud"]
    is_cyber_question = any(keyword in query_lower for keyword in cyber_keywords)
    
    scored_chunks = []
    query_words = set(query_lower.split())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these', 'those'}
    important_words = [w for w in query_words if w not in stop_words and len(w) > 2]
    
    for chunk in all_chunks:
        content = chunk.page_content
        content_lower = content.lower()
        source = chunk.metadata.get("source", "").lower()
        
        # Base score
        base_score = 0
        
        # Calculate word match score
        if important_words:
            word_matches = sum(1 for word in important_words if word in content_lower)
            word_score = word_matches / len(important_words)
        else:
            word_score = 0
        
        base_score = word_score
        
        # PRIORITY BOOSTING
        # Boost for IPC/CrPC content when asking about crimes
        if is_crime_question or is_ipc_question:
            if "indian penal code" in source or "ipc" in source or "penal" in source:
                base_score += 0.5  # BIG BOOST for IPC
            if "section 302" in content_lower or "section 304" in content_lower or "section 378" in content_lower:
                base_score += 0.4  # Boost for section mentions
            if "murder" in content_lower and "punishment" in content_lower:
                base_score += 0.3
        
        # Penalize Cyber Laws for non-cyber questions
        if not is_cyber_question:
            if "cyber" in source or "it act" in content_lower:
                base_score -= 0.3  # PENALTY for wrong PDF
        
        # Cyber question gets boost for cyber content
        if is_cyber_question:
            if "cyber" in source or "it act" in content_lower:
                base_score += 0.5
        
        # Exact phrase match bonus
        if query_lower in content_lower:
            base_score += 0.2
        
        if base_score > 0:
            scored_chunks.append((base_score, chunk))
    
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    return [chunk for score, chunk in scored_chunks[:top_k]]

def extract_answer_from_chunks(query: str, relevant_chunks: List, all_docs: List) -> str:
    """Extract answer from prioritized chunks"""
    if not relevant_chunks:
        return None
    
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    # Look for specific section information
    best_answer = ""
    best_score = 0
    
    for chunk in relevant_chunks:
        content = chunk.page_content
        content_lower = content.lower()
        source = chunk.metadata.get("source", "")
        
        # Calculate relevance
        score = 0
        
        # Check for section numbers
        section_match = re.search(r'section\s*(\d+)', content_lower, re.IGNORECASE)
        if section_match:
            score += 0.3
        
        # Check for answer patterns (like "punishment for murder")
        if "punishment" in content_lower:
            score += 0.2
        
        # Word overlap
        content_words = set(content_lower.split())
        overlap = len(query_words & content_words)
        if len(query_words) > 0:
            score += overlap / len(query_words)
        
        if score > best_score:
            best_score = score
            # Extract the most relevant paragraph
            sentences = re.split(r'[.!?]\s+', content)
            relevant_sentences = []
            for sentence in sentences:
                if len(sentence) > 30:
                    if any(word in sentence.lower() for word in query_words):
                        relevant_sentences.append(sentence.strip())
                    elif "section" in sentence.lower() and "punishment" in sentence.lower():
                        relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                best_answer = ". ".join(relevant_sentences[:3])
            else:
                best_answer = content[:600]
    
    if best_answer:
        # Clean up
        best_answer = best_answer.strip()
        if not best_answer.endswith('.') and not best_answer.endswith('?'):
            best_answer += '.'
        return best_answer
    
    return None

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
        for doc in st.session_state.pdf_list[:5]:
            short_name = doc[:35] + "..." if len(doc) > 35 else doc
            st.markdown(f'<span class="doc-badge">📄 {short_name}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("## 📤 Upload Document")
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Add PDF to Knowledge Base", type=["pdf"], key="pdf_uploader")
    
    if uploaded_file:
        if st.button("📥 Process & Add", use_container_width=True):
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
    
    if st.button("🔄 Sync with GitHub", use_container_width=True):
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

st.markdown("## 💬 Ask Legal Questions")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask about IPC, CrPC, Cyber Laws, or police procedures...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if st.session_state.total_chunks_count == 0:
            response = "⚠️ No documents loaded. Please upload PDFs to continue."
            st.markdown(response)
        else:
            with st.spinner(f"🔍 Searching through {st.session_state.total_chunks_count} legal documents..."):
                try:
                    relevant = smart_search_with_priority(prompt, st.session_state.all_chunks, top_k=15)
                    
                    if relevant:
                        answer = extract_answer_from_chunks(prompt, relevant, st.session_state.pdf_list)
                        
                        if answer:
                            st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        else:
                            response = "No specific information found. Try a different question."
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        response = "No relevant information found. Try different keywords."
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
