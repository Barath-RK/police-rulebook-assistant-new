import streamlit as st
import tempfile
import os
import pickle
from datetime import datetime

# Try importing - but with fallbacks
try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    st.error("pypdf not installed")

st.set_page_config(page_title="Police Rulebook Assistant", page_icon="👮", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "documents" not in st.session_state:
    st.session_state.documents = {}  # filename -> content
if "chunks" not in st.session_state:
    st.session_state.chunks = []  # list of (text, filename)

st.title("👮 Police Rulebook Assistant")
st.caption("RAG Assistant for Police SOPs, Complaint Manuals & Citizen Procedures")

# Simple text extraction from PDF
def extract_text_from_pdf(file_path):
    """Extract text from PDF using pypdf"""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting text: {e}"

# Simple chunking
def chunk_text(text, filename, chunk_size=500, overlap=50):
    """Split text into chunks"""
    chunks = []
    words = text.split()
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        chunks.append({
            "text": chunk_text,
            "source": filename,
            "chunk_id": i // (chunk_size - overlap)
        })
    return chunks

# Simple search
def search_chunks(query, chunks):
    """Simple keyword search"""
    query_words = set(query.lower().split())
    results = []
    
    for chunk in chunks:
        chunk_words = set(chunk["text"].lower().split())
        matches = len(query_words & chunk_words)
        if matches > 0:
            results.append((matches, chunk))
    
    results.sort(reverse=True, key=lambda x: x[0])
    return [r[1] for r in results[:3]]

with st.sidebar:
    st.header("📁 Upload Documents")
    
    if not PDF_SUPPORT:
        st.error("⚠️ PDF support not available")
    
    uploaded_file = st.file_uploader("Upload Police PDF", type=["pdf"])
    
    if uploaded_file and st.button("📤 Upload"):
        with st.spinner("Processing..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                # Extract text
                text = extract_text_from_pdf(tmp_path)
                
                if text and text.strip():
                    # Store document
                    st.session_state.documents[uploaded_file.name] = text
                    
                    # Create chunks
                    new_chunks = chunk_text(text, uploaded_file.name)
                    st.session_state.chunks.extend(new_chunks)
                    
                    st.success(f"✅ Uploaded {uploaded_file.name}")
                    st.info(f"📄 Extracted {len(text)} characters, {len(new_chunks)} chunks")
                else:
                    st.error("No text found in PDF. Try a different file.")
                
                os.unlink(tmp_path)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.divider()
    st.metric("Documents", len(st.session_state.documents))
    st.metric("Text Chunks", len(st.session_state.chunks))
    
    if len(st.session_state.chunks) > 0:
        st.success("✅ Ready to answer questions")
    
    st.divider()
    st.subheader("💡 Sample Questions")
    sample_queries = [
        "How to file a complaint?",
        "What is the procedure?",
        "Tell me about citizen rights",
        "How to report a crime?"
    ]
    for q in sample_queries:
        if st.button(q, key=f"sample_{q[:20]}"):
            st.session_state.prompt = q
            st.rerun()

st.header("💬 Ask Questions")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("📚 Sources"):
                for s in msg["sources"]:
                    st.caption(f"📄 {s}")

# Handle sample query
if "prompt" in st.session_state:
    prompt = st.session_state.prompt
    del st.session_state.prompt
else:
    prompt = st.chat_input("Ask about police procedures...")

if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response
    with st.chat_message("assistant"):
        if len(st.session_state.chunks) == 0:
            response = "⚠️ Please upload a PDF document first using the sidebar."
            st.markdown(response)
            sources = []
        else:
            with st.spinner("Searching documents..."):
                results = search_chunks(prompt, st.session_state.chunks)
                
                if results:
                    response = "📋 **Based on the Police Rulebook:**\n\n"
                    sources = []
                    for i, result in enumerate(results):
                        response += f"**Source {i+1}:** {result['text'][:400]}...\n\n"
                        response += f"📄 *Source: {result['source']}*\n\n"
                        sources.append(result['source'])
                    st.markdown(response)
                else:
                    response = "No relevant information found. Try rephrasing your question or upload more documents."
                    st.markdown(response)
                    sources = []
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "sources": sources
        })

st.markdown("---")
st.caption("👨‍🎓 **Barath R K PDKV** | 411623149004 | PRJ-005 | Week 2 Complete")
st.caption("🔧 Features: PDF Upload | Keyword Search | Citations | No Complex Dependencies")
