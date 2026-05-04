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

st.set_page_config(page_title="Police Rulebook Assistant", page_icon="👮", layout="wide")

# Custom CSS - Fixed for dark/light mode compatibility
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: #f8f9fa !important;
        color: #1a1a2e !important;
    }
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .main-header h1, .main-header p {
        color: white !important;
    }
    .source-line {
        font-size: 0.8rem;
        color: #666666 !important;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid #dddddd;
    }
    .detailed-answer {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #1a1a2e !important;
    }
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] div {
        color: #1a1a2e !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Comprehensive RAG Assistant for Police SOPs, Complaint Manuals & Citizen Procedures</p>
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
if "needs_refresh" not in st.session_state:
    st.session_state.needs_refresh = False

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
    """Get list of all PDF files from GitHub Documents folder using direct raw access"""
    # Since GitHub API might have issues, try direct approach with known file names
    # First try to list via API, if fails, use manual list
    try:
        # Use GitHub API to list contents
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
        else:
            st.warning(f"GitHub API returned {response.status_code}. Please ensure 'Documents' folder exists.")
            return []
    except Exception as e:
        st.warning(f"Error accessing GitHub: {e}")
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
        st.warning(f"Could not load {filename}: {str(e)[:100]}")
        return []

def load_all_documents():
    """Load ALL PDFs from GitHub Documents folder into a single vector store"""
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
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, pdf_info in enumerate(pdf_files):
        status_text.text(f"Loading: {pdf_info['name']}...")
        
        documents = load_pdf_from_url(pdf_info['raw_url'], pdf_info['name'])
        
        if documents:
            chunks = splitter.split_documents(documents)
            for j, chunk in enumerate(chunks):
                chunk.metadata["source"] = pdf_info['name']
                chunk.metadata["chunk_id"] = j
                chunk.metadata["total_chunks"] = len(chunks)
            all_chunks.extend(chunks)
            loaded_files.append(pdf_info['name'])
            st.info(f"✓ Loaded {pdf_info['name']} ({len(chunks)} chunks)")
        else:
            st.warning(f"✗ Failed to load {pdf_info['name']}")
        
        progress_bar.progress((i + 1) / len(pdf_files))
    
    status_text.empty()
    progress_bar.empty()
    
    return all_chunks, loaded_files

# ============================================================
# ENHANCED SEARCH FUNCTIONS - SEARCHES ALL CHUNKS FROM ALL PDFS
# ============================================================

def search_across_all_documents(query: str, all_chunks: List, top_k: int = 15) -> List:
    """Search across ALL chunks from ALL PDFs using keyword matching as fallback"""
    if not all_chunks:
        return []
    
    query_words = set(query.lower().split())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these', 'those'}
    
    important_words = [w for w in query_words if w not in stop_words and len(w) > 2]
    
    scored_chunks = []
    for chunk in all_chunks:
        content = chunk.page_content.lower()
        score = 0
        
        # Word matching score
        for word in important_words:
            if word in content:
                score += 1
        
        # Normalize score
        if important_words:
            score = score / len(important_words)
        
        if score > 0:
            scored_chunks.append((score, chunk))
    
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    return [chunk for score, chunk in scored_chunks[:top_k]]

def generate_comprehensive_answer(query: str, relevant_chunks: List, all_pdfs: List) -> tuple:
    """Generate comprehensive answer from ALL relevant chunks across all PDFs"""
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
    query_words = set(query.lower().split())
    
    for source, chunks in sources_dict.items():
        all_sources.append(source)
        answer_parts.append(f"\n📄 **From {source}:**\n")
        
        # Combine content from this source
        combined_content = " ".join([chunk.page_content for chunk in chunks[:5]])
        sentences = combined_content.split('. ')
        
        relevant_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if len(sentence) > 30:
                if any(word in sentence_lower for word in query_words):
                    relevant_sentences.append(sentence.strip())
        
        # Remove duplicates
        seen = set()
        unique_sentences = []
        for sent in relevant_sentences:
            if sent not in seen:
                seen.add(sent)
                unique_sentences.append(sent)
        
        if unique_sentences:
            for sent in unique_sentences[:4]:
                answer_parts.append(f"  • {sent}.")
        else:
            # Take first chunk content
            preview = chunks[0].page_content[:400]
            if preview:
                answer_parts.append(f"  • {preview}...")
    
    if answer_parts:
        full_answer = "".join(answer_parts)
        full_answer = full_answer.replace("\n\n\n", "\n\n")
        
        # Add introduction showing which PDFs were searched
        intro = f"I searched through {len(all_pdfs)} documents and found the following information:\n\n"
        final_answer = intro + full_answer
        return final_answer, list(set(all_sources))
    
    return None, []

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### 📚 Knowledge Base")
    
    # Show current status
    if st.session_state.documents_loaded and st.session_state.pdf_list:
        st.success(f"✅ {len(st.session_state.pdf_list)} documents loaded")
        for doc in st.session_state.pdf_list:
            st.caption(f"📄 {doc}")
    
    st.divider()
    
    if st.button("🔄 Refresh & Reload ALL PDFs", type="primary", use_container_width=True):
        st.session_state.documents_loaded = False
        st.session_state.vector_store = None
        st.session_state.all_chunks = []
        st.session_state.pdf_list = []
        st.session_state.messages = []  # Clear chat history
        st.rerun()

# ============================================================
# LOAD DOCUMENTS
# ============================================================

if not st.session_state.documents_loaded:
    with st.spinner("📚 Loading ALL police documents from GitHub... This may take a moment."):
        chunks, loaded_files = load_all_documents()
        
        if chunks:
            st.session_state.all_chunks = chunks
            # Create vector store with ALL chunks
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
            st.session_state.documents_loaded = True
            st.session_state.pdf_list = loaded_files
            
            # Show success message with details
            st.success(f"✅ Successfully loaded {len(loaded_files)} documents!")
            st.info(f"📊 Total chunks created: {len(chunks)}")
            for doc in loaded_files:
                st.write(f"  - {doc}")
        else:
            st.error("No PDFs found in 'Documents' folder. Please:")
            st.markdown("1. Create a folder named 'Documents' in your GitHub repository")
            st.markdown("2. Upload your PDF files into that folder")
            st.markdown("3. Click the Refresh button above")

# ============================================================
# MAIN CHAT AREA
# ============================================================

st.markdown("## 💬 Ask Questions")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask anything about police procedures...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if not st.session_state.documents_loaded or not st.session_state.all_chunks:
            response = "No documents loaded. Please add PDFs to the 'Documents' folder and click Refresh."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            with st.spinner(f"🔍 Searching through {len(st.session_state.pdf_list)} documents ({len(st.session_state.all_chunks)} chunks)..."):
                try:
                    # Search across ALL chunks
                    relevant_chunks = search_across_all_documents(prompt, st.session_state.all_chunks, top_k=20)
                    
                    if relevant_chunks:
                        answer, sources = generate_comprehensive_answer(prompt, relevant_chunks, st.session_state.pdf_list)
                        
                        if answer:
                            st.markdown(f'<div class="detailed-answer">{answer}</div>', unsafe_allow_html=True)
                            
                            if sources:
                                st.markdown(f'<div class="source-line">📄 Sources: {", ".join(sources[:5])}</div>', unsafe_allow_html=True)
                            
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer
                            })
                        else:
                            response = f"I searched through {len(st.session_state.pdf_list)} documents but couldn't find specific information matching your query.\n\nTry asking about specific topics from your documents."
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        response = f"I searched through {len(st.session_state.pdf_list)} documents but found no relevant information.\n\nTry rephrasing your question or check if your PDFs contain the information you're looking for."
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                except Exception as e:
                    st.error(f"Search error: {str(e)[:300]}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)[:300]}"})

# Footer
st.markdown("---")
st.caption("👮 Project PRJ-005 | Police Rulebook Assistant | Barath R K PDKV | 411623149004")
