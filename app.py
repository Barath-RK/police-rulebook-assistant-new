"""
POLICE RULEBOOK ASSISTANT - COMPLETE (Week 1 + Week 2)
Single file deployment ready for Streamlit Cloud
All features: Document upload, RAG search, Citations, Admin refresh, Supabase database
"""

import streamlit as st
import os
import tempfile
import pickle
from datetime import datetime
from typing import List, Dict, Any
import io
import re
import uuid

# ---------- Supabase Imports ----------
from supabase import create_client, Client

# ---------- LangChain & AI Imports ----------
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate

# ============================================================
# SUPABASE CONFIGURATION - YOUR CREDENTIALS
# ============================================================

SUPABASE_URL = "https://xprjddhltldjashaqlyv.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_lAL2XhaEThPAo1JMgdaAMg_qM7oHySt"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Police Rulebook Assistant",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stChatMessage { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .citation { font-size: 0.8rem; color: #666; background-color: #f0f0f0; padding: 0.3rem; border-radius: 0.3rem; }
    .confidence-high { color: green; font-weight: bold; }
    .confidence-medium { color: orange; font-weight: bold; }
    .confidence-low { color: red; font-weight: bold; }
    .admin-panel { background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; }
    .document-card { background-color: #f0f2f6; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "documents_loaded" not in st.session_state:
    st.session_state.documents_loaded = []
if "embeddings" not in st.session_state:
    with st.spinner("Loading AI model (first time only)..."):
        st.session_state.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
if "admin_password" not in st.session_state:
    st.session_state.admin_password = "admin123"
if "initialized" not in st.session_state:
    st.session_state.initialized = False

# ============================================================
# DATABASE FUNCTIONS (Supabase)
# ============================================================

def init_database():
    """Create tables if they don't exist"""
    try:
        # Create documents table using raw SQL
        sql_create_docs = """
        CREATE TABLE IF NOT EXISTS documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            filename TEXT UNIQUE NOT NULL,
            content TEXT,
            chunks TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        supabase.rpc('exec_sql', {'sql': sql_create_docs}).execute()
        
        # Create chunks table
        sql_create_chunks = """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
            chunk_text TEXT NOT NULL,
            chunk_index INTEGER,
            page_number INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        supabase.rpc('exec_sql', {'sql': sql_create_chunks}).execute()
        
        return True
    except Exception as e:
        # Tables might already exist or RPC not available
        print(f"Note: {e}")
        return True

def save_document_to_supabase(filename: str, content: str, chunks_list: list):
    """Save document and chunks to Supabase"""
    try:
        # Insert document
        doc_data = {
            "filename": filename,
            "content": content[:1000],  # Preview
            "chunks": str(len(chunks_list))
        }
        
        # Check if document already exists
        existing = supabase.table("documents").select("id").eq("filename", filename).execute()
        
        if existing.data:
            # Update existing
            doc_id = existing.data[0]['id']
            supabase.table("documents").update(doc_data).eq("id", doc_id).execute()
            # Delete old chunks
            supabase.table("document_chunks").delete().eq("document_id", doc_id).execute()
        else:
            # Insert new
            result = supabase.table("documents").insert(doc_data).execute()
            doc_id = result.data[0]['id']
        
        # Insert chunks
        for i, chunk in enumerate(chunks_list):
            chunk_data = {
                "document_id": doc_id,
                "chunk_text": chunk.page_content,
                "chunk_index": i,
                "page_number": chunk.metadata.get("page", 1)
            }
            supabase.table("document_chunks").insert(chunk_data).execute()
        
        return True, doc_id
    except Exception as e:
        return False, str(e)

def load_documents_from_supabase():
    """Load all documents from Supabase into vector store"""
    try:
        # Get all documents
        docs_result = supabase.table("documents").select("*").execute()
        
        if not docs_result.data:
            return 0
        
        all_chunks = []
        
        for doc in docs_result.data:
            # Get chunks for this document
            chunks_result = supabase.table("document_chunks").select("*").eq("document_id", doc['id']).execute()
            
            for chunk in chunks_result.data:
                # Recreate document object
                from langchain.schema import Document
                doc_obj = Document(
                    page_content=chunk['chunk_text'],
                    metadata={
                        'source': doc['filename'],
                        'page': chunk.get('page_number', 1),
                        'chunk_id': chunk['chunk_index']
                    }
                )
                all_chunks.append(doc_obj)
        
        if all_chunks:
            st.session_state.vector_store = FAISS.from_documents(all_chunks, st.session_state.embeddings)
            st.session_state.documents_loaded = all_chunks
        
        return len(all_chunks)
    except Exception as e:
        st.error(f"Error loading from Supabase: {e}")
        return 0

def delete_document_from_supabase(filename: str):
    """Delete document from Supabase"""
    try:
        # Find document
        doc_result = supabase.table("documents").select("id").eq("filename", filename).execute()
        
        if doc_result.data:
            doc_id = doc_result.data[0]['id']
            # Delete chunks (cascade should handle, but explicit for safety)
            supabase.table("document_chunks").delete().eq("document_id", doc_id).execute()
            # Delete document
            supabase.table("documents").delete().eq("id", doc_id).execute()
        
        return True
    except Exception as e:
        st.error(f"Delete error: {e}")
        return False

def get_all_documents():
    """Get list of all documents"""
    try:
        result = supabase.table("documents").select("filename, created_at, chunks").execute()
        return result.data if result.data else []
    except Exception as e:
        return []

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def chunk_document(documents, filename: str):
    """Split document into chunks"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    
    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = filename
        chunk.metadata["chunk_id"] = i
        chunk.metadata["page"] = chunk.metadata.get("page", 1)
        chunk.metadata["timestamp"] = datetime.now().isoformat()
    
    return chunks

def generate_answer(query: str, relevant_docs) -> tuple:
    """Generate answer with confidence score and citations"""
    if not relevant_docs:
        return "I couldn't find relevant information in the police rulebook. Please try rephrasing your question.", 0.0, []
    
    query_words = set(query.lower().split())
    all_context = " ".join([doc.page_content for doc in relevant_docs])
    all_context_words = set(all_context.lower().split())
    
    if len(query_words) > 0:
        common_words = query_words & all_context_words
        confidence = len(common_words) / len(query_words)
    else:
        confidence = 0.0
    
    answer_parts = []
    sources = []
    
    for i, doc in enumerate(relevant_docs[:3]):
        source_info = {
            "filename": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", 1),
            "chunk_id": doc.metadata.get("chunk_id", i),
            "excerpt": doc.page_content[:300] + "..."
        }
        sources.append(source_info)
        
        # Extract most relevant sentence
        sentences = doc.page_content.split('. ')
        best_sentence = ""
        max_overlap = 0
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = len(query_words & sentence_words)
            if overlap > max_overlap:
                max_overlap = overlap
                best_sentence = sentence
        
        if best_sentence:
            answer_parts.append(f"• {best_sentence} **[Source: {source_info['filename']}, Page {source_info['page']}]**")
        else:
            answer_parts.append(f"• {doc.page_content[:200]}... **[Source: {source_info['filename']}]**")
    
    if answer_parts:
        answer = "📋 **Based on the Police Rulebook:**\n\n" + "\n\n".join(answer_parts)
    else:
        answer = f"📋 **According to the police manual:**\n\n{relevant_docs[0].page_content[:300]}..."
    
    return answer, min(confidence, 0.95), sources

def process_uploaded_file(uploaded_file):
    """Process uploaded PDF file"""
    file_content = uploaded_file.read()
    
    # Save temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(file_content)
        tmp_path = tmp_file.name
    
    try:
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        
        chunks = chunk_document(documents, uploaded_file.name)
        
        # Extract full text for preview
        full_text = " ".join([doc.page_content[:200] for doc in documents])
        
        # Save to Supabase
        success, result = save_document_to_supabase(uploaded_file.name, full_text, chunks)
        
        if not success:
            return {"success": False, "error": result}
        
        # Update vector store
        if st.session_state.vector_store is None:
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
        else:
            st.session_state.vector_store.add_documents(chunks)
        
        st.session_state.documents_loaded.extend(chunks)
        
        return {
            "success": True,
            "chunks": len(chunks),
            "total": len(st.session_state.documents_loaded)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        os.unlink(tmp_path)

def refresh_knowledge_base():
    """Refresh knowledge base from Supabase"""
    with st.spinner("Refreshing knowledge base from Supabase..."):
        count = load_documents_from_supabase()
        return count

def clear_knowledge_base():
    """Clear local knowledge base"""
    st.session_state.vector_store = None
    st.session_state.documents_loaded = []
    return True

# ============================================================
# INITIALIZE DATABASE ON STARTUP
# ============================================================

if not st.session_state.initialized:
    with st.spinner("Connecting to Supabase..."):
        init_database()
        load_documents_from_supabase()
    st.session_state.initialized = True

# ============================================================
# MAIN UI
# ============================================================

st.title("👮 Police Rulebook Assistant")
st.caption("🚔 RAG Document Assistant for SOPs, Complaint Manuals & Citizen Procedures")
st.markdown("---")

# ============================================================
# SIDEBAR - Document Management
# ============================================================

with st.sidebar:
    st.header("📁 Document Management")
    
    # Supabase status
    try:
        test = supabase.table("documents").select("*").limit(1).execute()
        st.success("✅ Supabase Connected")
    except Exception as e:
        st.error("❌ Supabase Connection Error")
    
    # File Upload
    uploaded_file = st.file_uploader("Upload Police Document (PDF)", type=["pdf"])
    
    if uploaded_file:
        if st.button("📤 Upload to Knowledge Base", type="primary"):
            with st.spinner("Processing document..."):
                result = process_uploaded_file(uploaded_file)
                
                if result["success"]:
                    st.success(f"✅ Successfully uploaded {uploaded_file.name}")
                    st.info(f"📄 Created {result['chunks']} text chunks")
                    st.rerun()
                else:
                    st.error(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
    
    st.divider()
    
    # Document List
    st.subheader("📚 Uploaded Documents")
    documents = get_all_documents()
    
    if documents:
        for doc in documents:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"📄 **{doc.get('filename', 'Unknown')}**")
                st.caption(f"Chunks: {doc.get('chunks', '0')}")
            with col2:
                if st.button("🗑️", key=f"del_{doc.get('filename')}"):
                    if delete_document_from_supabase(doc.get('filename')):
                        st.success(f"Deleted {doc.get('filename')}")
                        refresh_knowledge_base()
                        st.rerun()
    else:
        st.info("No documents uploaded yet")
    
    st.divider()
    
    # ============================================================
    # ADMIN PANEL
    # ============================================================
    
    with st.expander("🔐 Admin Panel", expanded=False):
        admin_pass = st.text_input("Admin Password", type="password", key="admin_pass_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh KB"):
                if admin_pass == st.session_state.admin_password:
                    count = refresh_knowledge_base()
                    st.success(f"✅ Refreshed! {count} chunks loaded")
                    st.rerun()
                else:
                    st.error("Invalid password")
        
        with col2:
            if st.button("🗑️ Clear Local KB"):
                if admin_pass == st.session_state.admin_password:
                    clear_knowledge_base()
                    st.success("✅ Local knowledge base cleared")
                    st.rerun()
                else:
                    st.error("Invalid password")
        
        st.caption(f"📊 Local chunks: {len(st.session_state.documents_loaded)}")
    
    st.divider()
    
    # ============================================================
    # SYSTEM STATUS
    # ============================================================
    
    st.subheader("📊 System Status")
    
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        st.metric("Documents in KB", len(st.session_state.documents_loaded))
    with status_col2:
        st.metric("Supabase", "✅")
    
    if st.session_state.vector_store:
        st.success("✅ Vector Store Ready")
    else:
        st.warning("⚠️ Upload a document to start")
    
    st.divider()
    
    # ============================================================
    # SAMPLE QUESTIONS
    # ============================================================
    
    st.subheader("💡 Sample Questions")
    sample_queries = [
        "How to file a police complaint?",
        "What is the procedure for traffic violation?",
        "Tell me about citizen rights",
        "How to report a missing person?"
    ]
    
    for q in sample_queries:
        if st.button(q, key=f"sample_{q[:20]}"):
            st.session_state.sample_query = q
            st.rerun()

# ============================================================
# MAIN CHAT AREA
# ============================================================

st.header("💬 Ask Questions from Police Rulebook")

# Handle sample query
if "sample_query" in st.session_state:
    prompt = st.session_state.sample_query
    del st.session_state.sample_query
else:
    prompt = st.chat_input("Ask a question about police procedures...")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if "sources" in message and message["sources"]:
            with st.expander("📚 View Sources & Citations"):
                for source in message["sources"]:
                    st.markdown(f"**📄 File:** `{source.get('filename', 'Unknown')}`")
                    st.markdown(f"**📑 Page:** {source.get('page', 'N/A')}")
                    st.markdown(f"**📝 Excerpt:**")
                    st.markdown(f"> {source.get('excerpt', '')}")
                    st.divider()
        
        if "confidence" in message:
            conf = message["confidence"]
            if conf > 0.7:
                st.markdown(f"<span class='confidence-high'>🎯 Confidence: {conf:.0%}</span>", unsafe_allow_html=True)
            elif conf > 0.4:
                st.markdown(f"<span class='confidence-medium'>📊 Confidence: {conf:.0%}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span class='confidence-low'>⚠️ Confidence: {conf:.0%}</span>", unsafe_allow_html=True)

# Process new query
if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching police rulebook..."):
            if st.session_state.vector_store is None:
                response_text = "⚠️ No documents uploaded yet. Please upload a PDF document first using the sidebar."
                confidence = 0.0
                sources = []
            else:
                retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": 4})
                relevant_docs = retriever.get_relevant_documents(prompt)
                response_text, confidence, sources = generate_answer(prompt, relevant_docs)
            
            st.markdown(response_text)
            
            if confidence > 0:
                if confidence > 0.7:
                    st.markdown(f"<span class='confidence-high'>✅ Confidence: {confidence:.0%}</span>", unsafe_allow_html=True)
                elif confidence > 0.4:
                    st.markdown(f"<span class='confidence-medium'>📊 Confidence: {confidence:.0%}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span class='confidence-low'>⚠️ Low confidence: {confidence:.0%} - Try rephrasing</span>", unsafe_allow_html=True)
            
            if sources:
                with st.expander("📚 View Sources & Citations"):
                    for source in sources:
                        st.markdown(f"**📄 File:** `{source.get('filename', 'Unknown')}`")
                        st.markdown(f"**📑 Page:** {source.get('page', 'N/A')}")
                        st.markdown(f"**📝 Excerpt:**")
                        st.markdown(f"> {source.get('excerpt', '')}")
                        st.divider()
    
    # Add to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "sources": sources if sources else [],
        "confidence": confidence
    })

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🏆 **PRJ-005** | Police Rulebook Assistant")
with col2:
    st.caption("👨‍🎓 **Barath R K PDKV** | 411623149004")
with col3:
    st.caption("✅ **Week 1 + Week 2 Complete**")

st.caption("🔧 Features: PDF Upload | RAG Search | Citations | Confidence Scores | Admin Refresh | Supabase Database")