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
    .doc-badge { background: rgba(16,185,129,0.15); color: #10b981; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; margin: 0.25rem; }
    .upload-card { background: #131823; border-radius: 15px; padding: 1rem; margin-bottom: 1rem; border: 2px dashed rgba(220,38,38,0.4); text-align: center; }
    .stButton button { background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; border: none; border-radius: 10px; padding: 0.5rem 1rem; font-weight: 600; width: 100%; }
    .answer-section { background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%); padding: 1.2rem; border-radius: 15px; margin: 0.5rem 0; line-height: 1.7; border-left: 4px solid #10b981; color: #e6edf3; }
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
            chunk_size=800,
            chunk_overlap=150,
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
        chunk_size=800,
        chunk_overlap=150,
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

# ============================================================
# DIRECT IPC SEARCH FUNCTION
# ============================================================

def find_ipc_answer(query: str, all_chunks: List) -> str:
    """Directly search for IPC sections and punishments"""
    query_lower = query.lower()
    
    # Common IPC question mappings
    ipc_mappings = {
        "punishment for murder": "302",
        "murder punishment": "302",
        "murder": "302",
        "theft punishment": "378",
        "punishment for theft": "378",
        "robbery punishment": "392",
        "punishment for robbery": "392",
        "rape punishment": "376",
        "punishment for rape": "376",
        "cheating punishment": "420",
        "punishment for cheating": "420",
        "dowry death": "304b",
        "dowry death punishment": "304b",
        "criminal breach of trust": "406",
        "defamation punishment": "500",
        "hurt punishment": "323",
        "grievous hurt": "325",
    }
    
    # Find which section we need
    section_number = None
    for key, section in ipc_mappings.items():
        if key in query_lower:
            section_number = section
            break
    
    # If we know the section, search for it directly
    if section_number:
        search_pattern = f"section {section_number}"
        search_pattern2 = f"section {section_number}." if section_number.isdigit() else f"section {section_number}"
        
        best_chunk = None
        best_content = ""
        
        for chunk in all_chunks:
            content = chunk.page_content.lower()
            source = chunk.metadata.get("source", "").lower()
            
            # Check if this chunk contains the section
            if search_pattern in content or search_pattern2 in content:
                # Prefer IPC documents
                if "indian penal code" in source or "ipc" in source or "penal" in source:
                    best_chunk = chunk
                    break
                elif best_chunk is None:
                    best_chunk = chunk
        
        if best_chunk:
            content = best_chunk.page_content
            
            # Extract relevant part around the section
            lines = content.split('\n')
            relevant_lines = []
            found = False
            
            for i, line in enumerate(lines):
                if search_pattern in line.lower() or search_pattern2 in line.lower():
                    found = True
                    # Take this line and next 2-3 lines
                    for j in range(i, min(i + 4, len(lines))):
                        if lines[j].strip():
                            relevant_lines.append(lines[j].strip())
                    break
            
            if relevant_lines:
                answer = " ".join(relevant_lines)
                # Clean up
                answer = re.sub(r'\s+', ' ', answer)
                return answer
    
    # Fallback to general search
    best_chunks = []
    for chunk in all_chunks:
        content = chunk.page_content.lower()
        source = chunk.metadata.get("source", "").lower()
        
        # Check if content contains relevant keywords
        if any(word in content for word in ["punishment", "imprisonment", "death", "fine", "section"]):
            # Prioritize IPC
            if "indian penal code" in source or "ipc" in source or "penal" in source:
                best_chunks.append((3, chunk))
            else:
                best_chunks.append((1, chunk))
    
    best_chunks.sort(reverse=True, key=lambda x: x[0])
    
    if best_chunks:
        top_chunk = best_chunks[0][1]
        content = top_chunk.page_content
        
        # Extract sentences containing punishment keywords
        sentences = re.split(r'[.!?]\s+', content)
        relevant = []
        for sentence in sentences:
            if any(word in sentence.lower() for word in ["punishment", "section", "imprisonment", "death", "fine", "shall be punished"]):
                if len(sentence) > 20:
                    relevant.append(sentence.strip())
        
        if relevant:
            return ". ".join(relevant[:3])
        else:
            return content[:500]
    
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

prompt = st.chat_input("Ask about IPC sections, punishments, CrPC, or Cyber Laws...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if st.session_state.total_chunks_count == 0:
            response = "⚠️ No documents loaded. Please upload PDFs to continue."
            st.markdown(response)
        else:
            with st.spinner(f"🔍 Searching {st.session_state.total_chunks_count} legal documents..."):
                try:
                    # Use direct IPC search
                    answer = find_ipc_answer(prompt, st.session_state.all_chunks)
                    
                    if answer:
                        st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        response = "No specific information found. Try asking about specific IPC sections like 'punishment for murder under IPC'."
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
