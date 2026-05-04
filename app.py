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
    /* Hide default sidebar elements if any */
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Smart RAG Assistant for Police SOPs, Complaint Manuals & Citizen Procedures</p>
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

# ============================================================
# GITHUB CONFIGURATION
# ============================================================

GITHUB_USERNAME = "Barath-RK"
GITHUB_REPO = "police-rulebook-assistant-new"
GITHUB_BRANCH = "main"
DOCUMENTS_FOLDER = "Documents"

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{DOCUMENTS_FOLDER}"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{DOCUMENTS_FOLDER}/"

# ============================================================
# FUNCTIONS
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
                        'raw_url': RAW_BASE_URL + file['name']
                    })
            return pdf_files
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
        
        for doc in documents:
            doc.metadata["source"] = filename
        
        os.unlink(tmp_path)
        return documents
    except Exception as e:
        return []

def load_all_documents():
    """Load all PDFs from GitHub Documents folder"""
    all_chunks = []
    
    pdf_files = get_pdf_files_from_github()
    
    if not pdf_files:
        return [], []
    
    if st.session_state.embeddings is None:
        st.session_state.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    for pdf_info in pdf_files:
        documents = load_pdf_from_url(pdf_info['raw_url'], pdf_info['name'])
        
        if documents:
            chunks = splitter.split_documents(documents)
            for j, chunk in enumerate(chunks):
                chunk.metadata["chunk_id"] = j
            all_chunks.extend(chunks)
    
    return all_chunks, [f['name'] for f in pdf_files]

# ============================================================
# LOAD DOCUMENTS ON STARTUP
# ============================================================

if not st.session_state.documents_loaded:
    with st.spinner("📚 Loading police documents..."):
        chunks, loaded_files = load_all_documents()
        
        if chunks:
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
            st.session_state.documents_loaded = True
        else:
            st.warning("No PDFs found in 'Documents' folder. Please add PDF files.")

# ============================================================
# SIDEBAR - COMPLETELY EMPTY (No content)
# ============================================================

# Empty sidebar - nothing shown
with st.sidebar:
    pass  # Intentionally empty - no content displayed

# ============================================================
# SEARCH FUNCTIONS
# ============================================================

def search_documents(query: str, top_k: int = 5) -> List:
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
    
    answer_parts = []
    sources = []
    
    for doc in high_relevance[:3]:
        source = doc.metadata.get("source", "Unknown")
        sources.append(source)
        content = doc.page_content
        
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
st.caption("Project PRJ-005 | Police Rulebook Assistant | Barath R K PDKV | 411623149004")
