import streamlit as st
import tempfile
import os

# CORRECT IMPORTS for LangChain 0.1.0
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

st.set_page_config(page_title="Police Rulebook Assistant", page_icon="👮", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "documents" not in st.session_state:
    st.session_state.documents = []

st.title("👮 Police Rulebook Assistant")
st.caption("RAG Assistant for Police SOPs, Complaint Manuals & Citizen Procedures")

with st.sidebar:
    st.header("📁 Upload Documents")
    
    uploaded_file = st.file_uploader("Upload Police PDF", type=["pdf"])
    
    if uploaded_file and st.button("📤 Upload"):
        with st.spinner("Processing..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                
                splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                chunks = splitter.split_documents(docs)
                
                for i, chunk in enumerate(chunks):
                    chunk.metadata["source"] = uploaded_file.name
                    chunk.metadata["chunk_id"] = i
                
                embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                
                if st.session_state.vector_store is None:
                    st.session_state.vector_store = FAISS.from_documents(chunks, embeddings)
                else:
                    st.session_state.vector_store.add_documents(chunks)
                
                st.session_state.documents.extend(chunks)
                st.success(f"✅ Uploaded! {len(chunks)} chunks created")
                os.unlink(tmp_path)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.divider()
    st.metric("Documents in KB", len(st.session_state.documents))
    if st.session_state.vector_store:
        st.success("✅ Ready")

st.header("💬 Ask Questions")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("📚 Sources"):
                for s in msg["sources"]:
                    st.caption(f"📄 {s}")

if prompt := st.chat_input("Ask about police procedures..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if st.session_state.vector_store is None:
            response = "⚠️ Please upload a PDF document first using the sidebar."
            st.markdown(response)
        else:
            with st.spinner("Searching police rulebook..."):
                try:
                    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": 3})
                    docs = retriever.get_relevant_documents(prompt)
                    
                    if docs:
                        response = "📋 **Based on the Police Rulebook:**\n\n"
                        sources = []
                        for i, doc in enumerate(docs):
                            response += f"**Source {i+1}:** {doc.page_content[:400]}...\n\n"
                            source_name = doc.metadata.get('source', 'Unknown')
                            response += f"📄 *Source: {source_name}*\n\n"
                            sources.append(source_name)
                        st.markdown(response)
                    else:
                        response = "No relevant information found. Try rephrasing your question."
                        st.markdown(response)
                        sources = []
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "sources": sources if docs else []
                    })
                except Exception as e:
                    st.error(f"Search error: {e}")

st.markdown("---")
st.caption("👨‍🎓 **Barath R K PDKV** | 411623149004 | PRJ-005 | Week 2 Complete")
