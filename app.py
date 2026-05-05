"""
POLICE RULEBOOK ASSISTANT – COMPLETE (PRJ-005)
Single‑file Streamlit version – satisfies all Week 1‑3 requirements
"""

import streamlit as st
import tempfile
import os
from datetime import datetime

# ✅ CORRECTED IMPORTS for newer LangChain versions
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Page config
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
    .main-header p { font-size: 0.95rem; color: #8b949e; }
    div[data-testid="stChatMessage"][data-testid*="user"] { background: linear-gradient(135deg, #1a0f0f 0%, #1f1414 100%); border: 1px solid rgba(220,38,38,0.3); border-radius: 20px 20px 5px 20px; }
    div[data-testid="stChatMessage"][data-testid*="assistant"] { background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%); border: 1px solid rgba(16,185,129,0.3); border-radius: 20px 20px 20px 5px; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0e1a 0%, #0d1117 100%); border-right: 1px solid #21262d; }
    .stat-card-red { background: #131823; border-radius: 15px; padding: 1rem; margin: 0.8rem 0; text-align: center; border: 1px solid rgba(220,38,38,0.3); }
    .stat-card-green { background: #131823; border-radius: 15px; padding: 1rem; margin: 0.8rem 0; text-align: center; border: 1px solid rgba(16,185,129,0.3); }
    .stat-number-red { font-size: 2rem; font-weight: 700; color: #dc2626; }
    .stat-number-green { font-size: 2rem; font-weight: 700; color: #10b981; }
    .stat-label { font-size: 0.7rem; color: #8b949e; margin-top: 0.3rem; }
    .doc-badge { background: rgba(16,185,129,0.15); color: #10b981; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; margin: 0.25rem; }
    .stButton button { background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; border: none; border-radius: 10px; padding: 0.5rem 1rem; font-weight: 600; width: 100%; transition: all 0.3s ease; }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(220,38,38,0.4); }
    .answer-section { background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%); padding: 1.5rem; border-radius: 15px; margin: 0.5rem 0; line-height: 1.8; border-left: 4px solid #10b981; color: #e6edf3; }
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

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "documents" not in st.session_state:
    st.session_state.documents = []
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None
if "admin_password" not in st.session_state:
    st.session_state.admin_password = "admin123"

# Load embedding model (cached)
@st.cache_resource
def load_embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Sidebar
with st.sidebar:
    st.markdown("## 🎯 Knowledge Base")
    
    # File upload
    uploaded_file = st.file_uploader("📤 Upload Police PDF", type=["pdf"])
    
    if uploaded_file and st.button("📥 Process & Index", use_container_width=True):
        with st.spinner("Processing document..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
                chunks = splitter.split_documents(docs)
                
                for i, chunk in enumerate(chunks):
                    chunk.metadata["source"] = uploaded_file.name
                    chunk.metadata["chunk_id"] = i
                    chunk.metadata["page"] = chunk.metadata.get("page", 1)
                
                if st.session_state.embeddings is None:
                    st.session_state.embeddings = load_embedding_model()
                
                if st.session_state.vector_store is None:
                    st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
                else:
                    st.session_state.vector_store.add_documents(chunks)
                
                st.session_state.documents.extend(chunks)
                os.unlink(tmp_path)
                st.success(f"✅ Indexed {len(chunks)} chunks from {uploaded_file.name}")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.divider()
    
    # Stats
    if st.session_state.vector_store:
        st.markdown(f"""
        <div class="stat-card-red">
            <div class="stat-number-red">{len(st.session_state.documents)}</div>
            <div class="stat-label">Text Chunks</div>
        </div>
        """, unsafe_allow_html=True)
        
        unique_sources = list(set([d.metadata.get("source", "Unknown") for d in st.session_state.documents]))
        st.markdown("### 📚 Documents")
        for src in unique_sources[:3]:
            st.markdown(f'<span class="doc-badge">📄 {src[:30]}{"..." if len(src) > 30 else ""}</span>', unsafe_allow_html=True)
    
    st.divider()
    
    # Admin Panel
    with st.expander("🔐 Admin Panel"):
        admin_pass = st.text_input("Admin Password", type="password", key="admin_pass_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                if admin_pass == st.session_state.admin_password:
                    if st.session_state.vector_store:
                        st.success(f"✅ Ready - {len(st.session_state.documents)} chunks loaded")
                    else:
                        st.warning("No documents loaded")
                else:
                    st.error("Wrong password")
        with col2:
            if st.button("🗑️ Clear KB", use_container_width=True):
                if admin_pass == st.session_state.admin_password:
                    st.session_state.vector_store = None
                    st.session_state.documents = []
                    st.session_state.messages = []
                    st.success("Knowledge base cleared")
                    st.rerun()
                else:
                    st.error("Wrong password")
    
    st.divider()
    st.caption("👨‍🎓 Barath R K PDKV | 411623149004 | PRJ-005")

# Main chat area
st.markdown("## 💬 Ask Questions")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            st.caption(f"📄 Sources: {', '.join(msg['sources'])}")

# Chat input
if prompt := st.chat_input("Ask about police procedures, IPC sections, punishments..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if st.session_state.vector_store is None:
            response = "⚠️ No documents loaded. Please upload a PDF using the sidebar."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
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
                        response = "No relevant information found. Try rephrasing your question."
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                except Exception as e:
                    st.error(f"Search error: {e}")

# Footer
st.markdown("""
<div class="footer">
    Police Rulebook Assistant | Project PRJ-005 | Week 1-3 Complete | LangChain + FAISS + Streamlit
</div>
""", unsafe_allow_html=True)
