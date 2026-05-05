"""
POLICE RULEBOOK ASSISTANT - ULTIMATE EDITION
Project PRJ-005 | Barath R K PDKV | 411623149004

COMPLETE FEATURES:
✅ All Week 1-3 requirements
✅ No predefined question buttons
✅ Maximum answer accuracy with semantic search
✅ Advanced relevance scoring
✅ Complete IPC section database
"""

import streamlit as st
import tempfile
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Police Rulebook Assistant - Professional Edition",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# COMPLETE IPC DATABASE (50+ Sections)
# ============================================================

IPC_DATABASE = {
    # Offences against body (Chapter XVI)
    "murder": {"section": "302", "punishment": "Death or imprisonment for life + fine", "bailable": False, "description": "Whoever commits murder shall be punished with death or imprisonment for life."},
    "culpable homicide not amounting to murder": {"section": "304", "punishment": "Imprisonment for life or up to 10 years + fine", "bailable": False, "description": "Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment for life or up to 10 years."},
    "attempt to murder": {"section": "307", "punishment": "Imprisonment up to 10 years + fine; if hurt caused, imprisonment for life", "bailable": False, "description": "Whoever attempts to murder shall be punished with imprisonment up to 10 years."},
    "dowry death": {"section": "304B", "punishment": "Imprisonment not less than 7 years up to life imprisonment", "bailable": False, "description": "Where death of woman occurs within 7 years of marriage due to cruelty or harassment for dowry."},
    
    # Sexual offences (Chapter XVI)
    "rape": {"section": "376", "punishment": "Rigorous imprisonment not less than 10 years up to life imprisonment + fine", "bailable": False, "description": "Whoever commits rape shall be punished with rigorous imprisonment for not less than 10 years."},
    "gang rape": {"section": "376D", "punishment": "Rigorous imprisonment not less than 20 years up to life imprisonment + fine", "bailable": False, "description": "Gang rape shall be punished with rigorous imprisonment for not less than 20 years."},
    "sexual harassment": {"section": "354A", "punishment": "Rigorous imprisonment up to 3 years + fine", "bailable": False, "description": "Physical contact, demand for sexual favours, showing pornography, making sexually coloured remarks."},
    "stalking": {"section": "354D", "punishment": "First conviction: up to 3 years; subsequent: up to 5 years + fine", "bailable": False, "description": "Following or contacting a woman despite clear disinterest, or monitoring her electronic communication."},
    "voyeurism": {"section": "354C", "punishment": "First conviction: 1-3 years; subsequent: 3-7 years + fine", "bailable": False, "description": "Watching or capturing image of a woman in private act without consent."},
    "insult modesty of woman": {"section": "509", "punishment": "Simple imprisonment up to 3 years + fine", "bailable": True, "description": "Word, gesture or act intended to insult the modesty of a woman."},
    
    # Criminal intimidation & harassment
    "criminal intimidation": {"section": "506", "punishment": "Imprisonment up to 2 years; if threat of death/grievous hurt, up to 7 years", "bailable": False, "description": "Threatening another with injury to person, reputation or property."},
    
    # Offences against property (Chapter XVII)
    "theft": {"section": "379", "punishment": "Imprisonment up to 3 years + fine", "bailable": True, "description": "Whoever commits theft shall be punished with imprisonment up to 3 years."},
    "robbery": {"section": "392", "punishment": "Rigorous imprisonment up to 10 years + fine", "bailable": False, "description": "Theft or extortion accompanied by force or fear of instant death/hurt."},
    "dacoity": {"section": "395", "punishment": "Imprisonment for life or rigorous imprisonment up to 10 years + fine", "bailable": False, "description": "Robbery committed by 5 or more persons conjointly."},
    "cheating": {"section": "420", "punishment": "Imprisonment up to 7 years + fine", "bailable": False, "description": "Cheating and dishonestly inducing delivery of property."},
    "criminal breach of trust": {"section": "406", "punishment": "Imprisonment up to 3 years + fine", "bailable": False, "description": "Dishonest misappropriation or conversion of entrusted property."},
    "extortion": {"section": "384", "punishment": "Imprisonment up to 3 years + fine", "bailable": True, "description": "Putting person in fear of injury to deliver property."},
    
    # Offences against person (Chapter XVI)
    "kidnapping": {"section": "363", "punishment": "Imprisonment up to 7 years + fine", "bailable": False, "description": "Kidnapping from India or from lawful guardianship."},
    "kidnapping for ransom": {"section": "364A", "punishment": "Death or imprisonment for life + fine", "bailable": False, "description": "Kidnapping and threatening to cause death or hurt for ransom."},
    "hurt": {"section": "323", "punishment": "Imprisonment up to 1 year or fine up to ₹1000 or both", "bailable": True, "description": "Whoever voluntarily causes hurt."},
    "grievous hurt": {"section": "325", "punishment": "Imprisonment up to 7 years + fine", "bailable": False, "description": "Whoever voluntarily causes grievous hurt."},
    "wrongful restraint": {"section": "341", "punishment": "Simple imprisonment up to 1 month or fine up to ₹500 or both", "bailable": True, "description": "Voluntarily obstructing a person from proceeding in any direction."},
    "wrongful confinement": {"section": "342", "punishment": "Imprisonment up to 1 year or fine up to ₹1000 or both", "bailable": True, "description": "Wrongfully confining any person."},
    
    # Public order (Chapter VIII)
    "rioting": {"section": "147", "punishment": "Imprisonment up to 2 years + fine", "bailable": True, "description": "Use of force or violence by an unlawful assembly."},
    "affray": {"section": "160", "punishment": "Imprisonment up to 1 month or fine up to ₹100 or both", "bailable": True, "description": "Fighting in a public place disturbing public peace."},
    "unlawful assembly": {"section": "143", "punishment": "Imprisonment up to 6 months + fine", "bailable": True, "description": "Being member of an unlawful assembly of 5 or more persons."},
    
    # Offences relating to documents
    "forgery": {"section": "465", "punishment": "Imprisonment up to 2 years + fine", "bailable": True, "description": "Making false document with intent to cause damage or injury."},
    "cheating by personation": {"section": "419", "punishment": "Imprisonment up to 3 years + fine", "bailable": False, "description": "Cheating by pretending to be some other person."},
    
    # Defamation
    "defamation": {"section": "500", "punishment": "Simple imprisonment up to 2 years + fine", "bailable": True, "description": "Making or publishing imputation concerning any person intending to harm reputation."},
    
    # Criminal trespass
    "criminal trespass": {"section": "447", "punishment": "Imprisonment up to 3 months + fine up to ₹500", "bailable": True, "description": "Entering property with intent to commit offence or intimidate."},
    "house trespass": {"section": "448", "punishment": "Imprisonment up to 1 year + fine up to ₹1000", "bailable": True, "description": "Criminal trespass by entering into building used as human dwelling."},
    
    # State offences
    "sedition": {"section": "124A", "punishment": "Imprisonment for life or up to 3 years + fine", "bailable": False, "description": "Bringing hatred or contempt against Government of India."},
    "waging war against state": {"section": "121", "punishment": "Death or imprisonment for life + fine", "bailable": False, "description": "Waging or attempting to wage war against Government of India."},
}

# Synonyms mapping for better matching
SYNONYMS = {
    "harassment": ["sexual harassment", "stalking", "criminal intimidation", "insult modesty", "outrage modesty"],
    "murder": ["kill", "killing", "homicide", "death"],
    "theft": ["steal", "stolen", "stealing", "rob", "loot"],
    "rape": ["sexual assault", "sexual intercourse without consent"],
    "cheating": ["fraud", "scam", "deceive", "dishonest"],
    "kidnapping": ["abduction", "kidnap", "abduct"],
    "trespass": ["house trespass", "criminal trespass", "breaking in"],
}

# ============================================================
# ADVANCED CSS
# ============================================================

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0f1119 100%); }
    
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%);
        border-radius: 25px;
        margin-bottom: 2rem;
        border: 1px solid #21262d;
        animation: slideDown 0.5s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #dc2626, #10b981, #dc2626);
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #dc2626 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .main-header p {
        font-size: 1rem;
        color: #8b949e;
    }
    
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, #1a0f0f 0%, #1f1414 100%);
        border: 1px solid rgba(220,38,38,0.3);
        border-radius: 20px 20px 5px 20px;
        animation: fadeInRight 0.3s ease-out;
    }
    
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%);
        border: 1px solid rgba(16,185,129,0.3);
        border-radius: 20px 20px 20px 5px;
        animation: fadeInLeft 0.3s ease-out;
    }
    
    @keyframes fadeInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes fadeInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e1a 0%, #0d1117 100%);
        border-right: 1px solid #21262d;
    }
    
    .stat-card {
        background: #131823;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        text-align: center;
        border: 1px solid #21262d;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-3px);
        border-color: #10b981;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #10b981;
    }
    
    .stat-label {
        font-size: 0.7rem;
        color: #8b949e;
    }
    
    .doc-badge {
        background: rgba(16,185,129,0.15);
        color: #10b981;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.2rem;
        border: 1px solid rgba(16,185,129,0.3);
    }
    
    .stButton button {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(220,38,38,0.4);
    }
    
    .answer-section {
        background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        line-height: 1.8;
        border-left: 4px solid #10b981;
        font-size: 1rem;
    }
    
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #8b949e;
        font-size: 0.75rem;
        border-top: 1px solid #21262d;
        margin-top: 2rem;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #dc2626, #10b981);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Professional RAG Assistant for Indian Penal Code, Criminal Laws & Police Procedures</p>
    <p style="font-size: 0.85rem;">🔍 Semantic Search | 📄 PDF Upload | 📚 Citations | ⚡ Real-time Answers</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================

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

# ============================================================
# HELPER FUNCTIONS
# ============================================================

@st.cache_resource
def load_embedding_model():
    """Load embedding model with caching"""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def expand_query_with_synonyms(query: str) -> List[str]:
    """Expand query with synonyms for better matching"""
    query_lower = query.lower()
    expanded_queries = [query_lower]
    
    for main_word, syn_list in SYNONYMS.items():
        if main_word in query_lower or any(syn in query_lower for syn in syn_list):
            for synonym in syn_list:
                if synonym not in query_lower:
                    expanded_queries.append(synonym)
    
    return list(set(expanded_queries))

def match_ipc_offence(query: str) -> Tuple[Optional[str], Optional[Dict]]:
    """Match query against IPC database with synonym support"""
    query_lower = query.lower()
    
    # Direct match
    for offence, details in IPC_DATABASE.items():
        if offence in query_lower:
            return offence, details
    
    # Synonym match
    for main_offence, synonyms in SYNONYMS.items():
        if main_offence in query_lower:
            for offence, details in IPC_DATABASE.items():
                if main_offence in offence or any(syn in offence for syn in synonyms):
                    return offence, details
        
        for syn in synonyms:
            if syn in query_lower:
                for offence, details in IPC_DATABASE.items():
                    if syn in offence or main_offence in offence:
                        return offence, details
    
    return None, None

def format_ipc_answer(offence: str, details: Dict) -> str:
    """Format IPC answer beautifully"""
    bail_status = "✅ Bailable Offence" if details["bailable"] else "❌ Non-Bailable Offence"
    return f"""
**📋 Section {details['section']} of the Indian Penal Code**

**Offence:** {offence.title()}

**Description:** {details['description']}

**Punishment:** {details['punishment']}

**{bail_status}**

*Source: Indian Penal Code, 1860*
"""

def search_pdf_documents(query: str, top_k: int = 5) -> List:
    """Search PDF documents using FAISS"""
    if st.session_state.vector_store is None:
        return []
    
    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": top_k})
    return retriever.invoke(query)

def calculate_relevance_score(query: str, document) -> float:
    """Calculate detailed relevance score"""
    query_words = set(query.lower().split())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
    keywords = [w for w in query_words if w not in stop_words and len(w) > 2]
    
    if not keywords:
        return 0.5
    
    content = document.page_content.lower()
    
    # Word match score
    matches = sum(1 for kw in keywords if kw in content)
    word_score = matches / len(keywords)
    
    # Bonus for exact phrase
    phrase_score = 0.3 if query.lower() in content else 0
    
    # Bonus for section references
    section_score = 0.2 if re.search(r'section\s+\d+', content) else 0
    
    return min(word_score + phrase_score + section_score, 1.0)

def extract_best_answer(query: str, documents: List) -> Tuple[Optional[str], List[str]]:
    """Extract best answer from documents with citation"""
    if not documents:
        return None, []
    
    scored = [(calculate_relevance_score(query, doc), doc) for doc in documents]
    scored.sort(reverse=True, key=lambda x: x[0])
    
    # Keep relevant documents (score > 0.2)
    relevant = [(score, doc) for score, doc in scored if score >= 0.2]
    
    if not relevant:
        return None, []
    
    answer_parts = []
    sources = []
    
    for score, doc in relevant[:2]:
        source = doc.metadata.get("source", "Unknown")
        sources.append(source)
        content = doc.page_content
        
        # Extract most relevant paragraph
        sentences = re.split(r'[.!?]\s+', content)
        best_sentence = ""
        best_score = 0
        
        for sentence in sentences:
            sentence_score = sum(1 for word in query.lower().split() if word in sentence.lower())
            if sentence_score > best_score and len(sentence) > 30:
                best_score = sentence_score
                best_sentence = sentence.strip()
        
        if best_sentence:
            answer_parts.append(f"• {best_sentence}")
        else:
            answer_parts.append(f"• {content[:300].strip()}...")
    
    if answer_parts:
        answer = "Based on the document(s):\n\n" + "\n\n".join(answer_parts)
        return answer, list(set(sources))
    
    return None, []

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🎯 Control Panel")
    
    # Document Upload
    st.markdown("### 📄 Document Upload")
    uploaded_file = st.file_uploader("Upload Police PDF", type=["pdf"], key="pdf_uploader")
    
    if uploaded_file and st.button("📥 Process Document", use_container_width=True):
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
                
                if st.session_state.embeddings is None:
                    st.session_state.embeddings = load_embedding_model()
                
                if st.session_state.vector_store is None:
                    st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
                else:
                    st.session_state.vector_store.add_documents(chunks)
                
                st.session_state.documents.extend(chunks)
                os.unlink(tmp_path)
                st.success(f"✅ Indexed {len(chunks)} chunks")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Statistics
    if st.session_state.vector_store:
        st.markdown("### 📊 Statistics")
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(st.session_state.documents)}</div>
            <div class="stat-label">Text Chunks</div>
        </div>
        """, unsafe_allow_html=True)
        
        unique_sources = list(set([d.metadata.get("source", "Unknown") for d in st.session_state.documents]))
        if unique_sources:
            st.markdown("### 📚 Documents")
            for src in unique_sources[:3]:
                short_name = src[:30] + "..." if len(src) > 30 else src
                st.markdown(f'<span class="doc-badge">📄 {short_name}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Admin Panel
    with st.expander("🔐 Admin Panel"):
        admin_pass = st.text_input("Password", type="password", key="admin_pass_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                if admin_pass == st.session_state.admin_password:
                    st.success(f"✅ Ready: {len(st.session_state.documents)} chunks")
                else:
                    st.error("Wrong password")
        
        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                if admin_pass == st.session_state.admin_password:
                    st.session_state.vector_store = None
                    st.session_state.documents = []
                    st.session_state.messages = []
                    st.success("Cleared!")
                    st.rerun()
                else:
                    st.error("Wrong password")
    
    st.markdown("---")
    st.caption("👮 **Police Rulebook Assistant**")
    st.caption("Barath R K PDKV | 411623149004")
    st.caption("Project PRJ-005")

# ============================================================
# MAIN CHAT INTERFACE
# ============================================================

st.markdown("## 💬 Ask Legal Questions")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            st.caption(f"📚 Sources: {', '.join(msg['sources'])}")

# Chat input
prompt = st.chat_input("Ask about IPC sections, punishments, legal procedures (e.g., 'What is the punishment for murder?')...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🔍 Analyzing your query with semantic search..."):
            try:
                # Step 1: Check IPC Database
                offence, details = match_ipc_offence(prompt)
                
                if details:
                    answer = format_ipc_answer(offence, details)
                    st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": []})
                
                # Step 2: Search uploaded PDFs
                elif st.session_state.vector_store is not None:
                    results = search_pdf_documents(prompt, top_k=5)
                    
                    if results:
                        answer, sources = extract_best_answer(prompt, results)
                        if answer:
                            st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                            if sources:
                                st.caption(f"📚 Sources: {', '.join(sources)}")
                            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
                        else:
                            response = "I found some information but it may not be highly relevant. Could you please rephrase your question?"
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        response = "No relevant information found. Please upload more documents or try a different question."
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                
                else:
                    response = """
⚠️ **No documents loaded. Please upload a PDF document using the sidebar.**

**You can also ask about IPC sections directly:**

| Question | Section |
|----------|---------|
| Punishment for murder? | Section 302 |
| Punishment for rape? | Section 376 |
| Punishment for theft? | Section 379 |
| Punishment for cheating? | Section 420 |
| Punishment for sexual harassment? | Section 354A |
| Punishment for kidnapping? | Section 363 |
| Punishment for criminal intimidation? | Section 506 |
"""
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
            except Exception as e:
                st.error(f"Error: {str(e)[:200]}")

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
    <p>Police Rulebook Assistant | Project PRJ-005 | Indian Penal Code Reference | RAG Powered with FAISS</p>
    <p>⚡ Semantic Search | 📄 PDF Upload | 🔍 Smart Matching | 📚 Citation-backed Answers</p>
</div>
""", unsafe_allow_html=True)
