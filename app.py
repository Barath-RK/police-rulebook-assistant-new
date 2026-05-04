import streamlit as st
import tempfile
import os
import numpy as np

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
    .source-line {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid #eee;
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

# Sidebar - Only upload
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
    
    # Simple info
    if st.session_state.vector_store:
        st.caption(f"✅ {len(st.session_state.documents)} chunks ready")

# Main chat area
st.markdown("## 💬 Ask Questions")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle prompt
prompt = st.chat_input("Ask anything about police procedures...")

# Process question
if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        if st.session_state.vector_store is None:
            response_message = "No documents uploaded yet. Please upload a PDF document using the sidebar."
            st.markdown(response_message)
            st.session_state.messages.append({"role": "assistant", "content": response_message})
        else:
            with st.spinner("Searching police rulebook..."):
                try:
                    # Smart retrieval - get more candidates and rerank
                    retriever = st.session_state.vector_store.as_retriever(
                        search_kwargs={"k": 8}  # Get more candidates for better matching
                    )
                    relevant_docs = retriever.invoke(prompt)
                    
                    if relevant_docs:
                        # Calculate semantic relevance using word vectors and synonyms
                        query_words = set(prompt.lower().split())
                        
                        # Stop words to ignore
                        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'it', 'they', 'we', 'you', 'he', 'she', 'it', 'them', 'us'}
                        
                        # Filter out stop words from query
                        important_query_words = [w for w in query_words if w not in stop_words and len(w) > 2]
                        
                        scored_docs = []
                        
                        for doc in relevant_docs:
                            doc_text_lower = doc.page_content.lower()
                            doc_words = set(doc_text_lower.split())
                            
                            # Remove stop words from doc
                            important_doc_words = [w for w in doc_words if w not in stop_words and len(w) > 2]
                            
                            # Calculate word overlap score
                            if len(important_query_words) > 0:
                                word_matches = sum(1 for w in important_query_words if w in important_doc_words)
                                word_score = word_matches / len(important_query_words)
                            else:
                                word_score = 0
                            
                            # Check for related terms (semantic synonyms)
                            related_terms = {
                                'complaint': ['filing', 'register', 'report', 'lodge', 'grievance'],
                                'procedure': ['process', 'steps', 'method', 'guidelines', 'protocol'],
                                'rights': ['entitlement', 'legal', 'law', 'provision', 'protection'],
                                'traffic': ['vehicle', 'driving', 'road', 'accident', 'violation'],
                                'police': ['officer', 'station', 'department', 'law enforcement'],
                                'citizen': ['public', 'person', 'individual', 'resident'],
                                'file': ['submit', 'register', 'lodge', 'deposit'],
                                'report': ['inform', 'notify', 'communicate', 'submit'],
                                'status': ['update', 'progress', 'tracking', 'follow-up']
                            }
                            
                            # Check for related terms
                            related_score = 0
                            for query_word in important_query_words:
                                for key, terms in related_terms.items():
                                    if query_word in key or query_word in terms:
                                        for term in terms:
                                            if term in doc_text_lower:
                                                related_score += 0.3
                            
                            # Check for exact phrase matches (higher weight)
                            phrase_score = 0
                            query_phrases = prompt.lower().split('.')
                            for phrase in query_phrases[:2]:  # Check first 2 phrases
                                if len(phrase.split()) > 2 and phrase in doc_text_lower:
                                    phrase_score += 0.5
                            
                            # Combined score
                            total_score = min(word_score + related_score + phrase_score, 1.0)
                            scored_docs.append((total_score, doc))
                        
                        # Sort by score
                        scored_docs.sort(reverse=True, key=lambda x: x[0])
                        
                        # Keep only docs with decent relevance (score >= 0.25)
                        relevant_docs = [(score, doc) for score, doc in scored_docs if score >= 0.25]
                        
                        if relevant_docs:
                            # Take top 2 most relevant documents
                            top_docs = relevant_docs[:2]
                            
                            # Build comprehensive answer
                            response_parts = []
                            source_files = []
                            
                            for score, doc in top_docs:
                                source_files.append(doc.metadata.get("source", "Unknown"))
                                
                                # Extract multiple relevant sentences
                                sentences = doc.page_content.split('. ')
                                relevant_sentences = []
                                
                                for sentence in sentences:
                                    sentence_lower = sentence.lower()
                                    # Check if sentence contains important query words
                                    contains_relevant = False
                                    for word in important_query_words:
                                        if word in sentence_lower:
                                            contains_relevant = True
                                            break
                                    # Also check for related terms
                                    for key, terms in related_terms.items():
                                        for term in terms:
                                            if term in sentence_lower:
                                                contains_relevant = True
                                                break
                                    
                                    if contains_relevant and len(sentence) > 30:
                                        relevant_sentences.append(sentence.strip())
                                
                                if relevant_sentences:
                                    # Take best 2-3 sentences
                                    response_parts.extend(relevant_sentences[:3])
                                else:
                                    # Fallback to first 300 chars
                                    response_parts.append(doc.page_content[:300])
                            
                            # Remove duplicates while preserving order
                            seen = set()
                            unique_response_parts = []
                            for part in response_parts:
                                if part not in seen:
                                    seen.add(part)
                                    unique_response_parts.append(part)
                            
                            # Combine response
                            if len(unique_response_parts) == 1:
                                response_message = unique_response_parts[0]
                            else:
                                response_message = " ".join(unique_response_parts)
                            
                            # Clean up response
                            response_message = response_message.strip()
                            if response_message and not response_message.endswith('.'):
                                response_message += '.'
                            
                            st.markdown(response_message)
                            
                            # Add source line
                            unique_sources = list(set(source_files))
                            st.markdown(f'<div class="source-line">📄 Source: {", ".join(unique_sources)}</div>', unsafe_allow_html=True)
                            
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response_message
                            })
                        else:
                            response_message = "I couldn't find specific information about that. Could you please rephrase your question or ask about police procedures like complaints, traffic violations, or citizen rights?"
                            st.markdown(response_message)
                            st.session_state.messages.append({"role": "assistant", "content": response_message})
                    else:
                        response_message = "I couldn't find any relevant information. Try asking about police complaints, traffic procedures, or citizen rights."
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
