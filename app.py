import streamlit as st
import tempfile
import os

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

st.set_page_config(page_title="Police Rulebook Assistant", page_icon="👮", layout="wide")

# Custom CSS for clean UI
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
    .answer-text {
        font-size: 1rem;
        line-height: 1.5;
    }
    .source-line {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
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
    with st.spinner("Loading AI model... This may take 1-2 minutes."):
        try:
            st.session_state.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            st.session_state.embeddings_loaded = True
        except Exception as e:
            st.error(f"Error loading embeddings: {e}")

# Sidebar - Clean version with only upload and sample questions
with st.sidebar:
    st.markdown("## 📄 Document Upload")
    
    uploaded_file = st.file_uploader("Upload Police PDF", type=["pdf"])
    
    if uploaded_file and st.button("Upload", type="primary", use_container_width=True):
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
                
                if st.session_state.vector_store is None:
                    st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
                else:
                    st.session_state.vector_store.add_documents(chunks)
                
                st.session_state.documents.extend(chunks)
                
                st.success(f"Uploaded: {uploaded_file.name}")
                st.info(f"Created {len(chunks)} chunks")
                
                os.unlink(tmp_path)
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)[:200]}")
    
    st.divider()
    
    # Sample questions only
    st.markdown("## 💡 Sample Questions")
    sample_queries = [
        "How to file a police complaint?",
        "What is the procedure for traffic violation?",
        "Tell me about citizen rights",
        "How to report a missing person?",
        "What are cyber laws in India?"
    ]
    
    for q in sample_queries:
        if st.button(q, key=f"sample_{q[:20]}", use_container_width=True):
            st.session_state.prompt = q
            st.rerun()

# Main chat area
st.markdown("## 💬 Ask Questions")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

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
            response_message = "No documents uploaded yet. Please upload a PDF document using the sidebar to start asking questions."
            st.markdown(response_message)
            st.session_state.messages.append({"role": "assistant", "content": response_message})
        else:
            with st.spinner("Searching police rulebook..."):
                try:
                    # Retrieve relevant documents
                    retriever = st.session_state.vector_store.as_retriever(
                        search_kwargs={"k": 5}
                    )
                    relevant_docs = retriever.invoke(prompt)
                    
                    if relevant_docs:
                        # Calculate relevance score for each document
                        query_words = set(prompt.lower().split())
                        scored_docs = []
                        
                        for doc in relevant_docs:
                            doc_words = set(doc.page_content.lower().split())
                            if len(query_words) > 0:
                                overlap = len(query_words & doc_words)
                                score = overlap / len(query_words)
                            else:
                                score = 0
                            scored_docs.append((score, doc))
                        
                        # Sort by score and filter low relevance
                        scored_docs.sort(reverse=True, key=lambda x: x[0])
                        
                        # Only keep high relevance answers (score >= 0.3)
                        high_relevance_docs = [(score, doc) for score, doc in scored_docs if score >= 0.3]
                        
                        if high_relevance_docs:
                            # Use top 2 most relevant documents
                            top_docs = high_relevance_docs[:2]
                            
                            # Build response
                            response_parts = []
                            
                            for score, doc in top_docs:
                                # Extract the most relevant sentence
                                sentences = doc.page_content.split('. ')
                                best_sentence = ""
                                best_score = 0
                                
                                for sentence in sentences:
                                    sentence_words = set(sentence.lower().split())
                                    overlap = len(query_words & sentence_words)
                                    if overlap > best_score:
                                        best_score = overlap
                                        best_sentence = sentence
                                
                                if best_sentence and best_score > 0:
                                    response_parts.append(best_sentence)
                                else:
                                    response_parts.append(doc.page_content[:400])
                            
                            # Combine responses
                            if len(response_parts) == 1:
                                response_message = response_parts[0]
                            else:
                                response_message = "\n\n".join(response_parts)
                            
                            st.markdown(response_message)
                            
                            # Add source line
                            source_files = list(set([doc.metadata.get("source", "Unknown") for score, doc in top_docs]))
                            if source_files:
                                st.caption(f"Source: {', '.join(source_files)}")
                            
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response_message
                            })
                        else:
                            # No high relevance answers
                            response_message = "I couldn't find highly relevant information. Please try rephrasing your question."
                            st.markdown(response_message)
                            st.session_state.messages.append({"role": "assistant", "content": response_message})
                    else:
                        response_message = "No information found. Please try rephrasing your question."
                        st.markdown(response_message)
                        st.session_state.messages.append({"role": "assistant", "content": response_message})
                        
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
