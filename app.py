"""
POLICE RULEBOOK ASSISTANT – GITHUB PDF LOADER
Auto-loads all PDFs from GitHub 'Documents' folder on startup
"""

import streamlit as st
import tempfile
import os
import requests
from typing import List

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

# Custom CSS
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0f1119 100%); }
    .main-header { text-align: center; padding: 2rem; background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%); border-radius: 20px; margin-bottom: 2rem; border: 1px solid #21262d; }
    .main-header h1 { font-size: 2.2rem; background: linear-gradient(135deg, #fff 0%, #dc2626 50%, #10b981 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .stat-card-red { background: #131823; border-radius: 15px; padding: 1rem; margin: 0.8rem 0; text-align: center; border: 1px solid rgba(220,38,38,0.3); }
    .stat-number-red { font-size: 2rem; font-weight: 700; color: #dc2626; }
    .stat-label { font-size: 0.7rem; color: #8b949e; }
    .doc-badge { background: rgba(16,185,129,0.15); color: #10b981; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; margin: 0.25rem; }
    .stButton button { background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; border: none; border-radius: 10px; padding: 0.5rem 1rem; font-weight: 600; width: 100%; }
    div[data-testid="stChatMessage"][data-testid*="user"] { background: linear-gradient(135deg, #1a0f0f 0%, #1f1414 100%); border: 1px solid rgba(220,38,38,0.3); border-radius: 20px 20px 5px 20px; }
    div[data-testid="stChatMessage"][data-testid*="assistant"] { background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%); border: 1px solid rgba(16,185,129,0.3); border-radius: 20px 20px 20px 5px; }
    .footer { text-align: center; padding: 1.5rem; color: #8b949e; font-size: 0.75rem; border-top: 1px solid #21262d; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Auto-loading PDFs from GitHub Documents Folder</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# GITHUB CONFIGURATION - CHANGE THESE TO YOUR DETAILS
# ============================================================

GITHUB_USERNAME = "Barath-RK"
GITHUB_REPO = "police-rulebook-assistant-new"
GITHUB_BRANCH = "main"
DOCUMENTS_FOLDER = "Documents"

RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{DOCUMENTS_FOLDER}/"

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
        st.warning(f"Cannot access GitHub: {e}")
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
    except Exception as e:
        return []

@st.cache_resource
def load_embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_all_documents():
    """Load ALL PDFs from GitHub Documents folder"""
    all_chunks = []
    loaded_files = []
    
    pdf_files = get_pdf_files_from_github()
    
    if not pdf_files:
        return [], []
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    for i, pdf_info in enumerate(pdf_files):
        status_text.text(f"Loading: {pdf_info['name']}...")
        
        documents = load_pdf_from_url(pdf_info['raw_url'], pdf_info['name'])
        
        if documents:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = splitter.split_documents(documents)
            for j, chunk in enumerate(chunks):
                chunk.metadata["source"] = pdf_info['name']
                chunk.metadata["chunk_id"] = j
            all_chunks.extend(chunks)
            loaded_files.append(pdf_info['name'])
        
        progress_bar.progress((i + 1) / len(pdf_files))
    
    status_text.empty()
    progress_bar.empty()
    
    return all_chunks, loaded_files

# ============================================================
# LOAD DOCUMENTS ON STARTUP
# ============================================================

if not st.session_state.documents_loaded:
    with st.spinner("📚 Loading PDFs from GitHub Documents folder..."):
        chunks, loaded_files = load_all_documents()
        
        if chunks:
            if st.session_state.embeddings is None:
                st.session_state.embeddings = load_embedding_model()
            
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
            st.session_state.documents = chunks
            st.session_state.pdf_list = loaded_files
            st.session_state.documents_loaded = True
            st.success(f"✅ Loaded {len(loaded_files)} documents from GitHub!")
        else:
            st.info("📤 No PDFs found in GitHub 'Documents' folder")

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🎯 Knowledge Base")
    
    if st.session_state.documents_loaded:
        st.markdown(f"""
        <div class="stat-card-red">
            <div class="stat-number-red">{len(st.session_state.documents)}</div>
            <div class="stat-label">Text Chunks</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📚 Documents from GitHub")
        for doc in st.session_state.pdf_list[:5]:
            short_name = doc[:35] + "..." if len(doc) > 35 else doc
            st.markdown(f'<span class="doc-badge">📄 {short_name}</span>', unsafe_allow_html=True)
    
    st.divider()
    
    # Admin Refresh Button
    with st.expander("🔐 Admin Panel"):
        admin_pass = st.text_input("Admin Password", type="password", key="admin_pass")
        
        if st.button("🔄 Refresh from GitHub", use_container_width=True):
            if admin_pass == "admin123":
                with st.spinner("Refreshing documents from GitHub..."):
                    st.session_state.documents_loaded = False
                    st.session_state.vector_store = None
                    st.session_state.documents = []
                    st.rerun()
            else:
                st.error("Wrong password")
    
    st.divider()
    st.caption("👨‍🎓 Barath R K PDKV | 411623149004 | PRJ-005")

# ============================================================
# MAIN CHAT AREA
# ============================================================

st.markdown("## 💬 Ask Questions")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            st.caption(f"📄 Sources: {', '.join(msg['sources'])}")

if prompt := st.chat_input("Ask about police procedures, IPC sections, punishments..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if not st.session_state.documents_loaded:
            response = "⚠️ No documents loaded. Please add PDFs to the 'Documents' folder in GitHub."
            st.markdown(response)
        else:
            with st.spinner("🔍 Searching..."):
                try:
                    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": 3})
                    docs = retriever.invoke(prompt)
                    
                    if docs:
                        response = "📋 **Based on the documents:**\n\n"
                        sources = []
                        for i, doc in enumerate(docs):
                            response += f"**Source {i+1}:** {doc.page_content[:400]}...\n\n"
                            source_name = doc.metadata.get('source', 'Unknown')
                            response += f"📄 *Source: {source_name}*\n\n"
                            sources.append(source_name)
                        st.markdown(response)
                        st.caption(f"📚 Sources: {', '.join(sources)}")
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "sources": sources
                        })
                    else:
                        response = "No relevant information found."
                        st.markdown(response)
                        
                except Exception as e:
                    st.error(f"Search error: {e}")

# Footer
st.markdown("""
<div class="footer">
    Police Rulebook Assistant | Project PRJ-005 | Auto-loads PDFs from GitHub Documents folder
</div>
""", unsafe_allow_html=True)
