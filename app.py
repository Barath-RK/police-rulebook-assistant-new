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
    /* Force dark text for all content - fixes white text issue */
    .stChatMessage, .stMarkdown, .stAlert, .stSuccess, .stInfo, .stWarning {
        color: #1a1a2e !important;
    }
    
    .stChatMessage p, .stMarkdown p, .stChatMessage div, .stMarkdown div {
        color: #1a1a2e !important;
    }
    
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: #f8f9fa !important;
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
    
    .detailed-answer p, .detailed-answer div, .detailed-answer span {
        color: #1a1a2e !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] div {
        color: #1a1a2e !important;
    }
    
    /* Input text styling */
    .stTextInput input, .stTextArea textarea {
        color: #1a1a2e !important;
    }
    
    /* Fix for any remaining white text */
    .element-container, .row-widget, .stAlertContent {
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
if "force_reload" not in st.session_state:
    st.session_state.force_reload = False
if "all_chunks" not in st.session_state:
    st.session_state.all_chunks = []
if "pdf_list" not in st.session_state:
    st.session_state.pdf_list = []

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
        else:
            st.warning(f"Cannot access GitHub folder. Status: {response.status_code}")
            return []
    except Exception as e:
        st.warning(f"Cannot connect to GitHub: {e}")
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

def load_all_documents(show_progress=True):
    """Load all PDFs from GitHub Documents folder"""
    all_chunks = []
    loaded_files = []
    
    pdf_files = get_pdf_files_from_github()
    
    if not pdf_files:
        return [], []
    
    if st.session_state.embeddings is None:
        with st.spinner("Loading AI model..."):
            st.session_state.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    if show_progress:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    for i, pdf_info in enumerate(pdf_files):
        if show_progress:
            status_text.text(f"Loading: {pdf_info['name']}...")
        
        documents = load_pdf_from_url(pdf_info['raw_url'], pdf_info['name'])
        
        if documents:
            chunks = splitter.split_documents(documents)
            for j, chunk in enumerate(chunks):
                chunk.metadata["chunk_id"] = j
                chunk.metadata["total_chunks"] = len(chunks)
                chunk.metadata["doc_name"] = pdf_info['name']
            all_chunks.extend(chunks)
            loaded_files.append(pdf_info['name'])
        
        if show_progress:
            progress_bar.progress((i + 1) / len(pdf_files))
    
    if show_progress:
        status_text.empty()
        progress_bar.empty()
    
    return all_chunks, loaded_files

# ============================================================
# ENHANCED SEARCH FUNCTIONS
# ============================================================

def search_documents_deep(query: str, top_k: int = 10) -> List:
    """Search for relevant documents - returns more results for deeper analysis"""
    if not st.session_state.vector_store:
        return []
    
    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": top_k})
    results = retriever.invoke(query)
    return results

def calculate_relevance_score(query: str, content: str) -> float:
    """Calculate detailed relevance score between query and content"""
    query_words = set(query.lower().split())
    content_lower = content.lower()
    content_words = set(content_lower.split())
    
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'it', 'they', 'we', 'you', 'he', 'she', 'it', 'them', 'us'}
    
    important_query = [w for w in query_words if w not in stop_words and len(w) > 2]
    
    if not important_query:
        return 0.0
    
    word_matches = sum(1 for w in important_query if w in content_words)
    word_score = word_matches / len(important_query) if important_query else 0
    phrase_score = 1.0 if query.lower() in content_lower else 0.0
    length_factor = min(len(content) / 1000, 1.0)
    total_score = (word_score * 0.5) + (phrase_score * 0.3) + (length_factor * 0.2)
    
    return min(total_score, 1.0)

def generate_detailed_answer_enhanced(query: str, all_chunks: List, top_k: int = 8) -> tuple:
    """Generate comprehensive detailed answer from all chunks"""
    if not all_chunks:
        return None, []
    
    scored_chunks = []
    for chunk in all_chunks:
        score = calculate_relevance_score(query, chunk.page_content)
        if score > 0:
            scored_chunks.append((score, chunk))
    
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    top_chunks = scored_chunks[:top_k]
    
    if not top_chunks:
        return None, []
    
    sources_dict = {}
    for score, chunk in top_chunks:
        source = chunk.metadata.get("source", "Unknown")
        if source not in sources_dict:
            sources_dict[source] = []
        sources_dict[source].append((score, chunk))
    
    answer_parts = []
    all_sources = []
    
    for source, chunks_list in sources_dict.items():
        all_sources.append(source)
        chunks_list.sort(reverse=True, key=lambda x: x[0])
        answer_parts.append(f"\n📄 **From {source}:**\n")
        
        for score, chunk in chunks_list[:3]:
            content = chunk.page_content
            sentences = content.split('. ')
            query_words = set(query.lower().split())
            relevant_sentences = []
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if len(sentence) > 30:
                    if any(word in sentence_lower for word in query_words):
                        relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                for sent in relevant_sentences[:2]:
                    if sent and len(sent) > 20:
                        answer_parts.append(f"  • {sent}.")
            else:
                preview = content[:300]
                if preview:
                    answer_parts.append(f"  • {preview}...")
    
    if answer_parts:
        full_answer = "".join(answer_parts)
        full_answer = full_answer.replace("\n\n\n", "\n\n")
        intro = "I found the following information related to your question:\n\n"
        final_answer = intro + full_answer
        return final_answer, list(set(all_sources))
    
    return None, []

def generate_answer_with_all_context(query: str, relevant_docs) -> tuple:
    """Alternative: Use all relevant docs to generate comprehensive answer"""
    if not relevant_docs:
        return None, []
    
    all_content = []
    sources = []
    
    for doc in relevant_docs[:10]:
        sources.append(doc.metadata.get("source", "Unknown"))
        all_content.append(doc.page_content)
    
    combined_content = " ".join(all_content)
    
    query_words = set(query.lower().split())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these', 'those'}
    
    important_words = [w for w in query_words if w not in stop_words and len(w) > 2]
    
    sentences = combined_content.split('. ')
    relevant_sentences = []
    
    for sentence in sentences:
        if len(sentence) > 30:
            sentence_lower = sentence.lower()
            if important_words:
                if any(word in sentence_lower for word in important_words):
                    relevant_sentences.append(sentence.strip())
            else:
                relevant_sentences.append(sentence.strip())
    
    seen = set()
    unique_sentences = []
    for sent in relevant_sentences:
        if sent not in seen:
            seen.add(sent)
            unique_sentences.append(sent)
    
    if unique_sentences:
        answer = "Based on the police documents:\n\n"
        for i, sent in enumerate(unique_sentences[:7], 1):
            answer += f"{i}. {sent}.\n"
        
        return answer, list(set(sources))
    
    return None, []

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### 📚 Knowledge Base")
    
    if st.button("🔄 Refresh & Reload All PDFs", type="primary", use_container_width=True):
        st.session_state.force_reload = True
        st.session_state.documents_loaded = False
        st.session_state.vector_store = None
        st.session_state.all_chunks = []
        st.rerun()
    
    st.divider()
    
    if st.session_state.documents_loaded and st.session_state.pdf_list:
        st.success(f"✅ {len(st.session_state.pdf_list)} documents loaded")
        st.caption(f"📊 Total: {len(st.session_state.all_chunks)} chunks")
        
        with st.expander("📄 View Documents"):
            for doc in st.session_state.pdf_list:
                st.markdown(f"- {doc}")

# ============================================================
# LOAD DOCUMENTS
# ============================================================

if not st.session_state.documents_loaded or st.session_state.force_reload:
    with st.spinner("📚 Loading all police documents from GitHub..."):
        chunks, loaded_files = load_all_documents()
        
        if chunks:
            st.session_state.all_chunks = chunks
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
            st.session_state.documents_loaded = True
            st.session_state.pdf_list = loaded_files
            st.session_state.force_reload = False
            st.success(f"✅ Loaded {len(loaded_files)} documents ({len(chunks)} chunks)")
        else:
            st.warning("No PDFs found in 'Documents' folder. Please add PDF files and click Refresh.")

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
            with st.spinner("Deep searching through all police documents..."):
                try:
                    answer, sources = generate_detailed_answer_enhanced(prompt, st.session_state.all_chunks, top_k=10)
                    
                    if not answer:
                        vector_results = search_documents_deep(prompt, top_k=15)
                        answer, sources = generate_answer_with_all_context(prompt, vector_results)
                    
                    if answer:
                        st.markdown(f'<div class="detailed-answer">{answer}</div>', unsafe_allow_html=True)
                        
                        if sources:
                            st.markdown(f'<div class="source-line">📄 Sources: {", ".join(sources[:5])}</div>', unsafe_allow_html=True)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })
                    else:
                        response = "I couldn't find specific information matching your query in the loaded documents.\n\nSuggestions:\n1. Try rephrasing your question with different keywords\n2. Make sure your PDFs contain relevant information\n3. Try asking about specific topics like:\n   - Complaint filing procedures\n   - Traffic violation rules\n   - Citizen rights\n   - Cyber crime reporting\n   - Missing person protocols\n\nExample questions:\n- What is the procedure to file a police complaint?\n- How to report a cyber crime online?\n- What are the rights of citizens during police investigation?"
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                except Exception as e:
                    st.error(f"Search error: {str(e)[:300]}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)[:300]}"})

# Footer
st.markdown("---")
st.caption("👮 Project PRJ-005 | Police Rulebook Assistant | Barath R K PDKV | 411623149004")
