"""
POLICE RULEBOOK ASSISTANT - COMPLETE
Week 1 + Week 2: RAG Document Assistant for Police SOPs
Deployment Ready for Streamlit Cloud
"""

import streamlit as st
import tempfile
import os
from datetime import datetime

# LangChain imports - Correct for version 0.1.0
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Page configuration
st.set_page_config(
    page_title="Police Rulebook Assistant",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .st-emotion-cache-1v0mbdj {
        background-color: #f0f2f6;
    }
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .source-badge {
        background-color: #e8f4f8;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.2rem;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        background-color: #d4edda;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        background-color: #fff3cd;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        background-color: #f8d7da;
    }
</style>
""", unsafe_allow_html=True)

# Header with gradient
st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>RAG Document Assistant for SOPs, Complaint Manuals & Citizen Procedures</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "documents" not in st.session_state:
    st.session_state.documents = []
if "embeddings_loaded" not in st.session_state:
    st.session_state.embeddings_loaded = False

# Load embeddings once
if not st.session_state.embeddings_loaded:
    with st.spinner("🔄 Loading AI model (first time only)... This may take 1-2 minutes."):
        try:
            st.session_state.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            st.session_state.embeddings_loaded = True
        except Exception as e:
            st.error(f"Error loading embeddings: {e}")

# Sidebar
with st.sidebar:
    st.markdown("## 📁 Document Management")
    
    # Upload section
    uploaded_file = st.file_uploader("📄 Upload Police PDF", type=["pdf"], help="Upload any police procedure document")
    
    if uploaded_file and st.button("📤 Upload to Knowledge Base", type="primary", use_container_width=True):
        with st.spinner("📖 Processing document..."):
            try:
                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                # Load PDF
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                
                # Chunk document
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
                chunks = splitter.split_documents(docs)
                
                # Add metadata
                for i, chunk in enumerate(chunks):
                    chunk.metadata["source"] = uploaded_file.name
                    chunk.metadata["chunk_id"] = i
                    chunk.metadata["page"] = chunk.metadata.get("page", 1)
                
                # Create or update vector store
                if st.session_state.vector_store is None:
                    st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
                else:
                    st.session_state.vector_store.add_documents(chunks)
                
                st.session_state.documents.extend(chunks)
                
                # Show success
                st.success(f"✅ Successfully uploaded **{uploaded_file.name}**")
                st.info(f"📊 Created **{len(chunks)}** text chunks")
                
                # Cleanup
                os.unlink(tmp_path)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)[:200]}")
    
    st.divider()
    
    # Document list
    st.markdown("## 📚 Uploaded Documents")
    if st.session_state.documents:
        unique_sources = list(set([doc.metadata.get("source", "Unknown") for doc in st.session_state.documents]))
        for source in unique_sources:
            chunk_count = sum(1 for doc in st.session_state.documents if doc.metadata.get("source") == source)
            st.markdown(f"📄 **{source}**")
            st.caption(f"   {chunk_count} chunks")
    else:
        st.info("No documents uploaded yet")
    
    st.divider()
    
    # System status
    st.markdown("## 📊 System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📄 Documents", len(st.session_state.documents) if st.session_state.documents else 0)
    with col2:
        if st.session_state.vector_store:
            st.markdown("✅ **Vector Store**")
            st.caption("FAISS Ready")
        else:
            st.markdown("⏳ **Vector Store**")
            st.caption("Waiting for upload")
    
    st.divider()
    
    # Sample questions
    st.markdown("## 💡 Sample Questions")
    sample_queries = [
        "How to file a police complaint?",
        "What is the procedure for traffic violation?",
        "Tell me about citizen rights",
        "How to report a missing person?",
        "What documents are needed for complaint?"
    ]
    
    for q in sample_queries:
        if st.button(f"🔍 {q}", key=f"sample_{q[:20]}", use_container_width=True):
            st.session_state.prompt = q
            st.rerun()

# Main chat area
st.markdown("## 💬 Ask Questions from Police Rulebook")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if "sources" in message and message["sources"]:
            with st.expander("📚 View Sources & Citations"):
                for source in message["sources"]:
                    st.markdown(f"📄 **File:** `{source.get('filename', 'Unknown')}`")
                    if source.get("page"):
                        st.markdown(f"📑 **Page:** {source.get('page')}")
                    st.markdown(f"📝 **Excerpt:**")
                    st.markdown(f"> {source.get('excerpt', '')[:200]}...")
                    st.divider()
        
        if "confidence" in message:
            conf = message["confidence"]
            if conf > 0.7:
                st.markdown(f'<span class="confidence-high">🎯 Confidence: {conf:.0%}</span>', unsafe_allow_html=True)
            elif conf > 0.4:
                st.markdown(f'<span class="confidence-medium">📊 Confidence: {conf:.0%}</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="confidence-low">⚠️ Confidence: {conf:.0%}</span>', unsafe_allow_html=True)

# Handle prompt
if "prompt" in st.session_state:
    prompt = st.session_state.prompt
    del st.session_state.prompt
else:
    prompt = st.chat_input("Type your question about police procedures...")

# Process question
if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        if st.session_state.vector_store is None:
            response_message = "⚠️ **No documents uploaded yet.**\n\nPlease upload a PDF document using the sidebar to start asking questions."
            st.markdown(response_message)
            st.session_state.messages.append({"role": "assistant", "content": response_message})
        else:
            with st.spinner("🔍 Searching through police rulebook..."):
                try:
                    # Retrieve relevant documents
                    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": 3})
                    relevant_docs = retriever.get_relevant_documents(prompt)
                    
                    if relevant_docs:
                        # Calculate confidence
                        query_words = set(prompt.lower().split())
                        all_text = " ".join([doc.page_content for doc in relevant_docs])
                        all_words = set(all_text.lower().split())
                        
                        if len(query_words) > 0:
                            common = len(query_words & all_words)
                            confidence = min(common / len(query_words), 0.95)
                        else:
                            confidence = 0.0
                        
                        # Build response
                        response_parts = ["📋 **Based on the Police Rulebook:**\n"]
                        sources = []
                        
                        for i, doc in enumerate(relevant_docs):
                            # Get best sentence
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
                                response_parts.append(f"**Source {i+1}:** {best_sentence}.")
                            else:
                                response_parts.append(f"**Source {i+1}:** {doc.page_content[:300]}...")
                            
                            source_info = {
                                "filename": doc.metadata.get("source", "Unknown"),
                                "page": doc.metadata.get("page", 1),
                                "excerpt": doc.page_content[:200] + "..."
                            }
                            sources.append(source_info)
                            response_parts.append(f"📄 *Source: {source_info['filename']} (Page {source_info['page']})*\n")
                        
                        response_message = "\n\n".join(response_parts)
                        st.markdown(response_message)
                        
                        # Show confidence
                        if confidence > 0.7:
                            st.markdown(f'<span class="confidence-high">✅ High confidence: {confidence:.0%}</span>', unsafe_allow_html=True)
                        elif confidence > 0.4:
                            st.markdown(f'<span class="confidence-medium">📊 Medium confidence: {confidence:.0%}</span>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<span class="confidence-low">⚠️ Low confidence: {confidence:.0%} - Try rephrasing</span>', unsafe_allow_html=True)
                        
                        # Show sources expander
                        with st.expander("📚 View Detailed Sources"):
                            for source in sources:
                                st.markdown(f"**📄 File:** `{source['filename']}`")
                                st.markdown(f"**📑 Page:** {source['page']}")
                                st.markdown(f"**📝 Excerpt:**")
                                st.markdown(f"> {source['excerpt']}")
                                st.divider()
                        
                        # Save to history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_message,
                            "sources": sources,
                            "confidence": confidence
                        })
                    else:
                        response_message = "❌ **No relevant information found.**\n\nPlease try rephrasing your question or upload more relevant documents."
                        st.markdown(response_message)
                        st.session_state.messages.append({"role": "assistant", "content": response_message})
                        
                except Exception as e:
                    st.error(f"Search error: {str(e)[:200]}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)[:200]}"})

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🏆 **Project PRJ-005** | Police Rulebook Assistant")
with col2:
    st.caption("👨‍🎓 **Barath R K PDKV** | 411623149004")
with col3:
    st.caption("✅ **Week 1 + Week 2 Complete** | RAG System")

st.caption("🔧 **Features:** PDF Upload | RAG Search | Citations | Confidence Scores | FAISS Vector Store")
