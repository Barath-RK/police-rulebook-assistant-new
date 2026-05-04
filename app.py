import streamlit as st
import tempfile
import os
import requests
from typing import List, Dict, Any

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

st.set_page_config(page_title="Police Rulebook Assistant", page_icon="👮", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .source-line {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid #eee;
    }
    .answer-text {
        font-size: 1rem;
        line-height: 1.6;
    }
    .doc-list {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.2rem 0;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Comprehensive RAG Assistant for Police SOPs, Complaint Manuals, Citizen Procedures & Cyber Laws</p>
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
if "pdf_list" not in st.session_state:
    st.session_state.pdf_list = []
if "total_chunks" not in st.session_state:
    st.session_state.total_chunks = 0

# ============================================================
# GITHUB CONFIGURATION
# ============================================================

# Your GitHub repository info
GITHUB_USERNAME = "Barath-RK"
GITHUB_REPO = "police-rulebook-assistant-new"
GITHUB_BRANCH = "main"
DOCUMENTS_FOLDER = "Documents"

# GitHub API URL to list files
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{DOCUMENTS_FOLDER}"

# Raw content URL base
RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{DOCUMENTS_FOLDER}/"

# ============================================================
# FUNCTIONS TO GET PDFS FROM GITHUB
# ============================================================

def get_pdf_files_from_github():
    """Get list of all PDF files from GitHub Documents folder"""
    try:
        response = requests.get(GITHUB_API_URL)
        if response.status_code == 200:
            files = response.json()
            pdf_files = []
            for file in files:
                if file['name'].lower().endswith('.pdf'):
                    pdf_files.append({
                        'name': file['name'],
                        'url': file['download_url'],
                        'raw_url': RAW_BASE_URL + file['name'],
                        'size': file.get('size', 0)
                    })
            return pdf_files
        else:
            st.error(f"Cannot access GitHub folder. Status: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error accessing GitHub: {e}")
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
        
        # Add metadata
        for doc in documents:
            doc.metadata["source"] = filename
            doc.metadata["filename"] = filename
        
        os.unlink(tmp_path)
        return documents
    except Exception as e:
        st.warning(f"Could not load {filename}: {str(e)[:100]}")
        return []

def load_all_documents():
    """Load all PDFs from GitHub Documents folder"""
    all_chunks = []
    loaded_files = []
    
    # Get list of PDFs
    pdf_files = get_pdf_files_from_github()
    
    if not pdf_files:
        st.error("No PDF files found in 'Documents' folder. Please add PDFs to your GitHub repository.")
        return [], []
    
    # Initialize embeddings
    if st.session_state.embeddings is None:
        with st.spinner("Loading AI model..."):
            st.session_state.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
    
    # Text splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, pdf_info in enumerate(pdf_files):
        status_text.text(f"Loading: {pdf_info['name']}...")
        
        documents = load_pdf_from_url(pdf_info['raw_url'], pdf_info['name'])
        
        if documents:
            chunks = splitter.split_documents(documents)
            for j, chunk in enumerate(chunks):
                chunk.metadata["chunk_id"] = j
                chunk.metadata["total_chunks"] = len(chunks)
                chunk.metadata["file_size"] = pdf_info['size']
            all_chunks.extend(chunks)
            loaded_files.append(pdf_info['name'])
            st.success(f"✅ Loaded {pdf_info['name']} ({len(chunks)} chunks)")
        
        progress_bar.progress((i + 1) / len(pdf_files))
    
    status_text.empty()
    progress_bar.empty()
    
    return all_chunks, loaded_files

# ============================================================
# LOAD DOCUMENTS ON STARTUP
# ============================================================

if not st.session_state.documents_loaded:
    with st.spinner("Loading police documents from GitHub..."):
        chunks, loaded_files = load_all_documents()
        
        if chunks:
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
            st.session_state.documents_loaded = True
            st.session_state.pdf_list = loaded_files
            st.session_state.total_chunks = len(chunks)
            st.success(f"✅ Loaded {len(loaded_files)} documents ({len(chunks)} chunks)")
        else:
            st.error("No documents could be loaded. Please check your GitHub 'Documents' folder.")

# ============================================================
# SIDEBAR - Show loaded documents
# ============================================================

with st.sidebar:
    st.markdown("## 📚 Knowledge Base")
    
    if st.session_state.documents_loaded:
        st.success(f"✅ {len(st.session_state.pdf_list)} documents loaded")
        st.caption(f"📊 Total chunks: {st.session_state.total_chunks}")
        
        st.markdown("### 📄 Documents Available:")
        for doc in st.session_state.pdf_list:
            st.markdown(f"- {doc}")
    else:
        st.warning("⚠️ Loading documents...")
    
    st.divider()
    
    st.markdown("## 💡 Sample Questions")
    st.caption("Try asking about:")
    st.markdown("- How to file a police complaint?")
    st.markdown("- What are the traffic violation procedures?")
    st.markdown("- Tell me about citizen rights")
    st.markdown("- Cyber crime reporting process")
    st.markdown("- Missing person report procedure")

# ============================================================
# SEARCH FUNCTIONS
# ============================================================

def search_documents(query: str, top_k: int = 5) -> List[Dict]:
    """Search for relevant documents"""
    if not st.session_state.vector_store:
        return []
    
    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": top_k})
    results = retriever.invoke(query)
    return results

def generate_detailed_answer(query: str, relevant_docs) -> tuple:
    """Generate detailed answer from relevant documents"""
    if not relevant_docs:
        return None, []
    
    query_words = set(query.lower().split())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'it', 'they', 'we', 'you', 'he', 'she', 'it', 'them', 'us'}
    
    important_words = [w for w in query_words if w not in stop_words and len(w) > 2]
    
    # Score documents
    scored_docs = []
    for doc in relevant_docs:
        content = doc.page_content
        doc_words = set(content.lower().split())
        
        if important_words:
            word_matches = sum(1 for w in important_words if w in doc_words)
            word_score = word_matches / len(important_words)
        else:
            word_score = 0
        
        scored_docs.append((word_score, doc))
    
    scored_docs.sort(reverse=True, key=lambda x: x[0])
    high_relevance = [doc for score, doc in scored_docs if score >= 0.25]
    
    if not high_relevance:
        return None, []
    
    # Build detailed answer
    answer_parts = []
    sources = []
    
    for doc in high_relevance[:3]:
        source = doc.metadata.get("source", "Unknown")
        sources.append(source)
        
        content = doc.page_content
        
        # Extract best sentences
        sentences = content.split('. ')
        best_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in important_words):
                best_sentences.append(sentence.strip())
        
        if best_sentences:
            answer_parts.extend(best_sentences[:2])
        else:
            answer_parts.append(content[:400])
    
    # Combine answer
    if answer_parts:
        seen = set()
        unique_parts = []
        for part in answer_parts:
            if part not in seen:
                seen.add(part)
                unique_parts.append(part)
        
        answer = ". ".join(unique_parts)
        if not answer.endswith('.'):
            answer += '.'
        
        return answer, list(set(sources))
    
    return None, []

# ============================================================
# MAIN CHAT AREA
# ============================================================

st.markdown("## 💬 Ask Questions")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Ask anything about police procedures...")

if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        if not st.session_state.documents_loaded:
            response = "⚠️ No documents loaded. Please add PDFs to the 'Documents' folder in GitHub."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            with st.spinner("🔍 Searching through police documents..."):
                try:
                    results = search_documents(prompt)
                    
                    if results:
                        answer, sources = generate_detailed_answer(prompt, results)
                        
                        if answer:
                            st.markdown(f'<div class="answer-text">{answer}</div>', unsafe_allow_html=True)
                            
                            if sources:
                                st.markdown(f'<div class="source-line">📄 Source: {", ".join(sources)}</div>', unsafe_allow_html=True)
                            
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer
                            })
                        else:
                            response = "I found some information but nothing highly relevant. Could you please rephrase your question?"
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        response = "No relevant information found. Try asking about police complaints, traffic procedures, citizen rights, or cyber laws."
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                except Exception as e:
                    st.error(f"Search error: {str(e)[:200]}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)[:200]}"})

# Footer
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.caption("Project PRJ-005 | Police Rulebook Assistant")
with col2:
    st.caption("Barath R K PDKV | 411623149004")
