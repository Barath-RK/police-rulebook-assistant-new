import streamlit as st
import os

# Supabase import
from supabase import create_client, Client

# LangChain imports
from langchain_community.embeddings import HuggingFaceEmbeddings

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
    .sidebar-info {
        text-align: center;
        padding: 0.5rem;
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

# ============================================================
# SUPABASE CONFIGURATION
# ============================================================

# For Streamlit Cloud - Add these to Secrets
# For local testing - Create .env file

SUPABASE_URL = "https://xprjddhltldjashaqlyv.supabase.co"
SUPABASE_KEY = "sb_publishable_lAL2XhaEThPAo1JMgdaAMg_qM7oHySt"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "embeddings_loaded" not in st.session_state:
    st.session_state.embeddings_loaded = False
if "documents_count" not in st.session_state:
    st.session_state.documents_count = 0

# Load embeddings once
if not st.session_state.embeddings_loaded:
    with st.spinner("Loading AI model..."):
        try:
            st.session_state.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            st.session_state.embeddings_loaded = True
        except Exception as e:
            st.error(f"Error loading embeddings: {e}")

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_documents_count():
    """Get total documents in Supabase"""
    try:
        result = supabase.table("documents").select("count", count="exact").execute()
        return result.count if result.count else 0
    except:
        return 0

def search_supabase(query: str, top_k: int = 5):
    """Search Supabase for relevant documents using embeddings"""
    try:
        # Generate embedding for query
        query_embedding = st.session_state.embeddings.embed_query(query)
        
        # Call Supabase match function
        result = supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.5,
                "match_count": top_k
            }
        ).execute()
        
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Search error: {e}")
        return []

def generate_answer(query: str, search_results) -> tuple:
    """Generate answer from search results"""
    if not search_results:
        return None, []
    
    query_words = set(query.lower().split())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'it', 'they', 'we', 'you', 'he', 'she', 'it', 'them', 'us'}
    
    important_query_words = [w for w in query_words if w not in stop_words and len(w) > 2]
    
    # Score and filter results
    scored_results = []
    for result in search_results:
        content = result.get('content', '')
        filename = result.get('filename', 'Unknown')
        similarity = result.get('similarity', 0)
        
        content_words = set(content.lower().split())
        
        if len(important_query_words) > 0:
            word_matches = sum(1 for w in important_query_words if w in content_words)
            word_score = word_matches / len(important_query_words)
        else:
            word_score = 0
        
        total_score = (similarity * 0.6) + (word_score * 0.4)
        
        scored_results.append({
            'score': total_score,
            'content': content,
            'filename': filename,
            'similarity': similarity
        })
    
    # Filter by score
    high_relevance = [r for r in scored_results if r['score'] >= 0.35]
    high_relevance.sort(reverse=True, key=lambda x: x['score'])
    
    if not high_relevance:
        return None, []
    
    # Build answer
    answer_parts = []
    sources = []
    
    for result in high_relevance[:3]:
        sources.append(result['filename'])
        content = result['content']
        
        # Find best sentence
        sentences = content.split('. ')
        best_sentence = ""
        best_score = 0
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = len(important_query_words & sentence_words)
            if overlap > best_score:
                best_score = overlap
                best_sentence = sentence
        
        if best_sentence and best_score > 0:
            answer_parts.append(best_sentence)
        else:
            answer_parts.append(content[:400])
    
    if answer_parts:
        if len(answer_parts) == 1:
            answer = answer_parts[0]
        else:
            answer = ". ".join(answer_parts)
        
        if answer and not answer.endswith('.'):
            answer += '.'
        
        return answer, list(set(sources))
    
    return None, []

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 📚 Knowledge Base")
    
    # Get document count
    if st.session_state.documents_count == 0:
        with st.spinner("Loading..."):
            st.session_state.documents_count = get_documents_count()
    
    if st.session_state.documents_count > 0:
        st.success(f"✅ {st.session_state.documents_count} documents loaded")
    else:
        st.warning("⚠️ No documents in knowledge base")
        st.info("Contact admin to upload documents to Supabase")
    
    st.divider()
    
    st.markdown("## 📖 Available Topics")
    st.markdown("""
    - Police Complaint Procedures
    - Traffic Violation SOPs
    - Citizen Rights
    - Cyber Laws
    - Missing Person Reports
    - Emergency Response
    """)
    
    st.divider()
    
    st.caption("🔒 Data stored securely in Supabase")

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
        if st.session_state.documents_count == 0:
            response = "⚠️ No documents available in the knowledge base. Please contact admin to upload police procedure documents."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            with st.spinner("Searching police rulebook database..."):
                try:
                    # Search Supabase
                    search_results = search_supabase(prompt)
                    
                    if search_results:
                        answer, sources = generate_answer(prompt, search_results)
                        
                        if answer:
                            st.markdown(answer)
                            
                            if sources:
                                st.markdown(f'<div class="source-line">📄 Source: {", ".join(sources)}</div>', unsafe_allow_html=True)
                            
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer
                            })
                        else:
                            response = "I couldn't find specific information about that. Try asking about police complaints, traffic procedures, citizen rights, or cyber laws."
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        response = "No relevant information found in the knowledge base. Try asking about police complaints, traffic violations, or citizen rights."
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
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
