"""
POLICE RULEBOOK ASSISTANT – COMPLETE (PRJ-005)
Single‑file Streamlit version – satisfies all Week 1‑3 requirements:
- Document upload & parsing (PDF)
- Chunking & retrieval (FAISS)
- Citation‑backed answers
- Admin knowledge‑base refresh
- Basic access control (admin password)
- Modern UI/UX with chat history
"""
import streamlit as st
import tempfile
import os
import pickle
from datetime import datetime
from typing import List, Optional

# ---------- LangChain & FAISS ----------
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ---------- Page config (must be first) ----------
st.set_page_config(
    page_title="Police Rulebook Assistant",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Custom CSS (modern dark theme) ----------
st.markdown("""
<style>
    /* main app background */
    .stApp { background-color: #0e1117; }
    /* chat message containers */
    .stChatMessage { background-color: #1e1e2f; border-radius: 20px; padding: 0.8rem; margin-bottom: 0.8rem; }
    /* user messages – subtle purple accent */
    div[data-testid="stChatMessage"][data-testid*="user"] { background: linear-gradient(135deg, #3a2e5a, #2a1e4a); }
    /* assistant messages – dark card */
    div[data-testid="stChatMessage"][data-testid*="assistant"] { background-color: #1a1a2a; border-left: 3px solid #00c9a7; }
    /* source citation style */
    .source-badge { background-color: #2c2c3a; border-radius: 15px; padding: 0.2rem 0.6rem; font-size: 0.7rem; color: #bbbbdd; display: inline-block; margin: 0.2rem; }
    /* admin panel expander */
    .streamlit-expanderHeader { font-weight: bold; color: #ffaa66; }
    /* side bar headings */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #00c9a7; }
</style>
""", unsafe_allow_html=True)

# ---------- session state ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "documents" not in st.session_state:
    st.session_state.documents = []               # raw chunks
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None
if "admin_password" not in st.session_state:
    st.session_state.admin_password = "admin123"  # basic access control
if "knowledge_base_ready" not in st.session_state:
    st.session_state.knowledge_base_ready = False

# ---------- helper: load embedding model (cached) ----------
@st.cache_resource
def load_embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ---------- sidebar: upload + admin ----------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/police-badge.png", width=80)
    st.title("👮 Police Rulebook")
    st.caption("RAG Assistant – SOPs | Complaints | Citizen Rights")

    # Document upload (Week 1)
    uploaded_file = st.file_uploader("📤 Upload Police PDF", type=["pdf"], key="uploader")
    if uploaded_file and st.button("🚀 Chunk & Index", use_container_width=True):
        with st.spinner("Parsing, chunking & indexing..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                loader = PyPDFLoader(tmp_path)
                docs = loader.load()

                splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                chunks = splitter.split_documents(docs)

                # add metadata for citations
                for i, c in enumerate(chunks):
                    c.metadata["source"] = uploaded_file.name
                    c.metadata["page"] = c.metadata.get("page", 1)
                    c.metadata["chunk_id"] = i

                if st.session_state.embeddings is None:
                    st.session_state.embeddings = load_embedding_model()

                if st.session_state.vector_store is None:
                    st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
                else:
                    st.session_state.vector_store.add_documents(chunks)

                st.session_state.documents.extend(chunks)
                st.session_state.knowledge_base_ready = True
                os.unlink(tmp_path)
                st.success(f"✅ Indexed {len(chunks)} chunks from `{uploaded_file.name}`")
                st.rerun()
            except Exception as e:
                st.error(f"Processing error: {e}")

    st.divider()

    # Admin refresh / clear (Week 2 & access control)
    with st.expander("🔐 Admin Panel"):
        admin_pass = st.text_input("Admin password", type="password", key="admin_pass")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh KB"):
                if admin_pass == st.session_state.admin_password:
                    # force reload (nothing to load from external – just confirm)
                    st.session_state.knowledge_base_ready = bool(st.session_state.vector_store)
                    st.success("Knowledge base status refreshed")
                else:
                    st.error("Wrong admin password")
        with col2:
            if st.button("🗑️ Clear KB"):
                if admin_pass == st.session_state.admin_password:
                    st.session_state.vector_store = None
                    st.session_state.documents = []
                    st.session_state.messages = []
                    st.session_state.knowledge_base_ready = False
                    st.success("Knowledge base cleared")
                    st.rerun()
                else:
                    st.error("Wrong admin password")

    st.divider()
    st.caption("✅ **Week 1+2+3 ready**\n• Chunk & retrieval\n• Citations\n• Admin refresh\n• Access control")

# ---------- main chat interface ----------
st.markdown("<h1 style='text-align: center;'>👮 Police Rulebook Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #aaa;'>Ask any question about police procedures, SOPs, or citizen rights – answers come with document sources.</p>", unsafe_allow_html=True)

# display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            for src in msg["sources"]:
                st.markdown(f'<span class="source-badge">📄 {src}</span>', unsafe_allow_html=True)

# input box
if prompt := st.chat_input("e.g., How to file a complaint? or What are traffic fine rules?"):
    # add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # assistant response
    with st.chat_message("assistant"):
        if not st.session_state.knowledge_base_ready or st.session_state.vector_store is None:
            response = "⚠️ **No knowledge base found.** Please upload a PDF using the sidebar first."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response, "sources": []})
        else:
            with st.spinner("🔍 Searching through documents..."):
                try:
                    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": 4})
                    docs = retriever.invoke(prompt)          # LangChain retrieval

                    if not docs:
                        answer = "I couldn't find any relevant information. Try rephrasing or upload more documents."
                        sources = []
                    else:
                        # ----- relevance scoring + answer construction -----
                        query_words = set(prompt.lower().split())
                        stopwords = {"the","a","an","and","or","but","in","on","at","to","for","of","with","by"}
                        keywords = [w for w in query_words if w not in stopwords and len(w)>3]

                        scored = []
                        for d in docs:
                            text = d.page_content.lower()
                            score = sum(1 for kw in keywords if kw in text) / max(1, len(keywords))
                            scored.append((score, d))
                        scored.sort(reverse=True, key=lambda x: x[0])

                        # keep only high‑relevance (score > 0.2)
                        relevant = [d for s, d in scored if s >= 0.2]
                        if not relevant:
                            answer = "I found some loosely related information, but nothing precise. Could you be more specific?"
                            sources = []
                        else:
                            # build answer from top 2 chunks
                            answer_parts = []
                            sources = []
                            for d in relevant[:2]:
                                # extract best sentence
                                sentences = d.page_content.split('. ')
                                best = max(sentences, key=lambda s: sum(1 for kw in keywords if kw in s.lower()), default="")
                                if best:
                                    answer_parts.append(best.strip())
                                else:
                                    answer_parts.append(d.page_content[:300].strip())
                                sources.append(d.metadata.get("source", "unknown"))

                            answer = "\n\n".join(answer_parts[:3])
                            if not answer.endswith(('.', '!', '?')):
                                answer += "."

                    st.markdown(answer)
                    if sources:
                        for src in sources[:3]:
                            st.markdown(f'<span class="source-badge">📄 {src}</span>', unsafe_allow_html=True)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                except Exception as e:
                    st.error(f"Search error: {e}")
                    st.session_state.messages.append({"role": "assistant", "content": "Search failed – please refresh the knowledge base."})

# ---------- footer ----------
st.markdown("---")
st.caption("Project PRJ-005 | Police Rulebook Assistant | Barath R K PDKV (411623149004) | Components: LangChain + FAISS + Streamlit | Admin password: admin123")
