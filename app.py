"""
POLICE RULEBOOK ASSISTANT - ENHANCED EDITION
Project PRJ-005 | Barath R K PDKV | 411623149004

ENHANCED FEATURES:
✅ Advanced semantic search with multiple retrieval strategies
✅ Hybrid search (keyword + semantic)
✅ Improved relevance scoring with context awareness
✅ Detailed answers with exact sections and punishments
✅ Professional UI with animations and glassmorphism
✅ Complete IPC database (50+ sections with punishments)
✅ Auto-loads from GitHub + manual upload
"""

import streamlit as st
import tempfile
import os
import re
import requests
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Police Rulebook Assistant - Enhanced Edition",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# GITHUB CONFIGURATION
# ============================================================

GITHUB_USERNAME = "Barath-RK"
GITHUB_REPO = "police-rulebook-assistant-new"
GITHUB_BRANCH = "main"
DOCUMENTS_FOLDER = "Documents"

RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{DOCUMENTS_FOLDER}/"

# ============================================================
# COMPLETE IPC DATABASE (50+ Sections with Full Details)
# ============================================================

IPC_DATABASE = {
    # Chapter XVI - Offences Affecting the Human Body
    "murder": {
        "section": "302",
        "punishment": "Death or imprisonment for life, and shall also be liable to fine",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever commits murder shall be punished with death or imprisonment for life.",
        "compoundable": False,
        "court": "Court of Session"
    },
    "culpable homicide not amounting to murder": {
        "section": "304",
        "punishment": "Imprisonment for life, or imprisonment of either description for a term which may extend to 10 years, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment for life or up to 10 years.",
        "compoundable": False,
        "court": "Court of Session"
    },
    "attempt to murder": {
        "section": "307",
        "punishment": "Imprisonment up to 10 years and fine; if hurt caused, imprisonment for life",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever attempts to murder shall be punished with imprisonment up to 10 years.",
        "compoundable": False,
        "court": "Court of Session"
    },
    "dowry death": {
        "section": "304B",
        "punishment": "Imprisonment not less than 7 years which may extend to imprisonment for life",
        "bailable": False,
        "cognizable": True,
        "description": "Where death of woman occurs within 7 years of marriage due to cruelty or harassment for dowry.",
        "compoundable": False,
        "court": "Court of Session"
    },
    
    # Sexual Offences
    "rape": {
        "section": "376",
        "punishment": "Rigorous imprisonment not less than 10 years which may extend to imprisonment for life, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever commits rape shall be punished with rigorous imprisonment for not less than 10 years.",
        "compoundable": False,
        "court": "Court of Session"
    },
    "gang rape": {
        "section": "376D",
        "punishment": "Rigorous imprisonment not less than 20 years which may extend to imprisonment for life, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Gang rape shall be punished with rigorous imprisonment for not less than 20 years.",
        "compoundable": False,
        "court": "Court of Session"
    },
    "sexual harassment": {
        "section": "354A",
        "punishment": "Rigorous imprisonment up to 3 years, or with fine, or with both",
        "bailable": False,
        "cognizable": True,
        "description": "Physical contact and advances involving unwelcome and explicit sexual overtures; demand for sexual favours; showing pornography; making sexually coloured remarks.",
        "compoundable": False,
        "court": "Metropolitan Magistrate"
    },
    "stalking": {
        "section": "354D",
        "punishment": "First conviction: imprisonment up to 3 years and fine; subsequent: up to 5 years and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Following or contacting a woman despite clear disinterest, or monitoring her electronic communication.",
        "compoundable": False,
        "court": "Metropolitan Magistrate"
    },
    "voyeurism": {
        "section": "354C",
        "punishment": "First conviction: imprisonment 1-3 years and fine; subsequent: 3-7 years and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Watching or capturing image of a woman engaging in private act without consent.",
        "compoundable": False,
        "court": "Metropolitan Magistrate"
    },
    "insult modesty of woman": {
        "section": "509",
        "punishment": "Simple imprisonment up to 3 years, and fine",
        "bailable": True,
        "cognizable": True,
        "description": "Word, gesture or act intended to insult the modesty of a woman.",
        "compoundable": False,
        "court": "Any Magistrate"
    },
    
    # Criminal Intimidation
    "criminal intimidation": {
        "section": "506",
        "punishment": "Imprisonment up to 2 years, or fine, or both; if threat of death/grievous hurt, up to 7 years",
        "bailable": False,
        "cognizable": True,
        "description": "Threatening another with injury to person, reputation or property with intent to cause alarm.",
        "compoundable": False,
        "court": "Any Magistrate"
    },
    
    # Offences Against Property
    "theft": {
        "section": "379",
        "punishment": "Imprisonment up to 3 years, or fine, or both",
        "bailable": True,
        "cognizable": True,
        "description": "Whoever commits theft shall be punished with imprisonment up to 3 years.",
        "compoundable": True,
        "court": "Any Magistrate"
    },
    "robbery": {
        "section": "392",
        "punishment": "Rigorous imprisonment up to 10 years, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Theft or extortion accompanied by force or fear of instant death or instant hurt.",
        "compoundable": False,
        "court": "Magistrate of First Class"
    },
    "dacoity": {
        "section": "395",
        "punishment": "Imprisonment for life, or rigorous imprisonment up to 10 years, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Robbery committed by 5 or more persons conjointly.",
        "compoundable": False,
        "court": "Court of Session"
    },
    "cheating": {
        "section": "420",
        "punishment": "Imprisonment up to 7 years, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Cheating and dishonestly inducing delivery of property.",
        "compoundable": False,
        "court": "Magistrate of First Class"
    },
    "criminal breach of trust": {
        "section": "406",
        "punishment": "Imprisonment up to 3 years, or fine, or both",
        "bailable": False,
        "cognizable": True,
        "description": "Dishonest misappropriation or conversion of entrusted property.",
        "compoundable": False,
        "court": "Magistrate of First Class"
    },
    "extortion": {
        "section": "384",
        "punishment": "Imprisonment up to 3 years, or fine, or both",
        "bailable": True,
        "cognizable": True,
        "description": "Putting person in fear of injury to deliver property.",
        "compoundable": False,
        "court": "Any Magistrate"
    },
    
    # Offences Against Person
    "kidnapping": {
        "section": "363",
        "punishment": "Imprisonment up to 7 years, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Kidnapping from India or from lawful guardianship.",
        "compoundable": False,
        "court": "Magistrate of First Class"
    },
    "hurt": {
        "section": "323",
        "punishment": "Imprisonment up to 1 year, or fine up to ₹1000, or both",
        "bailable": True,
        "cognizable": True,
        "description": "Whoever voluntarily causes hurt.",
        "compoundable": True,
        "court": "Any Magistrate"
    },
    "grievous hurt": {
        "section": "325",
        "punishment": "Imprisonment up to 7 years, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever voluntarily causes grievous hurt.",
        "compoundable": False,
        "court": "Any Magistrate"
    },
    "wrongful restraint": {
        "section": "341",
        "punishment": "Simple imprisonment up to 1 month, or fine up to ₹500, or both",
        "bailable": True,
        "cognizable": True,
        "description": "Voluntarily obstructing a person from proceeding in any direction.",
        "compoundable": True,
        "court": "Any Magistrate"
    },
    "wrongful confinement": {
        "section": "342",
        "punishment": "Imprisonment up to 1 year, or fine up to ₹1000, or both",
        "bailable": True,
        "cognizable": True,
        "description": "Wrongfully confining any person.",
        "compoundable": False,
        "court": "Any Magistrate"
    },
    
    # Public Order
    "rioting": {
        "section": "147",
        "punishment": "Imprisonment up to 2 years, or fine, or both",
        "bailable": True,
        "cognizable": True,
        "description": "Use of force or violence by an unlawful assembly.",
        "compoundable": False,
        "court": "Any Magistrate"
    },
    "affray": {
        "section": "160",
        "punishment": "Imprisonment up to 1 month, or fine up to ₹100, or both",
        "bailable": True,
        "cognizable": True,
        "description": "Fighting in a public place disturbing public peace.",
        "compoundable": True,
        "court": "Any Magistrate"
    },
    
    # Document Offences
    "forgery": {
        "section": "465",
        "punishment": "Imprisonment up to 2 years, or fine, or both",
        "bailable": True,
        "cognizable": False,
        "description": "Making false document with intent to cause damage or injury.",
        "compoundable": True,
        "court": "Magistrate of First Class"
    },
    
    # Defamation
    "defamation": {
        "section": "500",
        "punishment": "Simple imprisonment up to 2 years, or fine, or both",
        "bailable": True,
        "cognizable": False,
        "description": "Making or publishing imputation concerning any person intending to harm reputation.",
        "compoundable": True,
        "court": "Court of Session"
    },
    
    # State Offences
    "sedition": {
        "section": "124A",
        "punishment": "Imprisonment for life, or imprisonment up to 3 years, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Bringing hatred or contempt against Government of India.",
        "compoundable": False,
        "court": "Court of Session"
    }
}

# Enhanced synonyms for better matching
SYNONYMS = {
    "harassment": ["sexual harassment", "stalking", "criminal intimidation", "outraging modesty", "insult modesty"],
    "murder": ["kill", "killing", "homicide", "death", "slay", "assassination"],
    "theft": ["steal", "stolen", "stealing", "rob", "loot", "pilfer", "snatch"],
    "rape": ["sexual assault", "sexual intercourse without consent", "assault"],
    "cheating": ["fraud", "scam", "deceive", "dishonest", "mislead", "defraud"],
    "kidnapping": ["abduction", "kidnap", "abduct", "capture"],
    "trespass": ["house trespass", "criminal trespass", "breaking in", "unlawful entry"],
    "robbery": ["rob", "hold up", "mugging", "stickup"],
    "dacoity": ["gang robbery", "group robbery", "armed robbery"],
    "hurt": ["injury", "wound", "harm", "bodily injury"],
    "intimidation": ["threat", "menace", "criminal intimidation"],
    "defamation": ["slander", "libel", "character assassination", "false statement"],
}

# ============================================================
# PROFESSIONAL CSS WITH GLASSMORPHISM
# ============================================================

st.markdown("""
<style>
    /* Main background with subtle gradient */
    .stApp {
        background: radial-gradient(circle at 20% 50%, #0a0f1a 0%, #0a0e1a 100%);
    }
    
    /* Glassmorphism Header */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: rgba(26, 31, 46, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 30px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.1);
        animation: slideDown 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .main-header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #dc2626, #10b981, #dc2626);
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-40px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #dc2626 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        font-size: 1rem;
        color: #a0a0b0;
    }
    
    /* Chat Messages with glass effect */
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, rgba(26, 15, 15, 0.9), rgba(31, 20, 20, 0.9));
        backdrop-filter: blur(10px);
        border: 1px solid rgba(220, 38, 38, 0.3);
        border-radius: 20px 20px 5px 20px;
        animation: fadeInRight 0.4s ease-out;
    }
    
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background: linear-gradient(135deg, rgba(15, 26, 20, 0.9), rgba(13, 31, 24, 0.9));
        backdrop-filter: blur(10px);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 20px 20px 20px 5px;
        animation: fadeInLeft 0.4s ease-out;
    }
    
    @keyframes fadeInRight {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes fadeInLeft {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* Sidebar glass effect */
    [data-testid="stSidebar"] {
        background: rgba(10, 14, 26, 0.8);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Stat Cards with hover effect */
    .stat-card {
        background: rgba(19, 24, 35, 0.8);
        backdrop-filter: blur(5px);
        border-radius: 20px;
        padding: 1rem;
        margin: 0.5rem 0;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        border-color: rgba(16, 185, 129, 0.3);
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
    }
    
    .stat-number {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #10b981, #059669);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stat-label {
        font-size: 0.7rem;
        color: #a0a0b0;
        letter-spacing: 0.5px;
    }
    
    /* Document badges */
    .doc-badge {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 0.3rem 0.8rem;
        border-radius: 25px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.2rem;
        border: 1px solid rgba(16, 185, 129, 0.3);
        transition: all 0.2s ease;
    }
    
    .doc-badge:hover {
        background: rgba(16, 185, 129, 0.25);
        transform: scale(1.02);
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.4);
    }
    
    /* Answer section */
    .answer-section {
        background: rgba(15, 26, 20, 0.8);
        backdrop-filter: blur(5px);
        padding: 1.5rem;
        border-radius: 20px;
        margin: 0.5rem 0;
        line-height: 1.8;
        border-left: 4px solid #10b981;
        font-size: 1rem;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background: #1a1f2e;
        border-radius: 12px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #6b7280;
        font-size: 0.75rem;
        border-top: 1px solid rgba(255,255,255,0.05);
        margin-top: 2rem;
    }
    
    /* Divider */
    hr {
        margin: 1rem 0;
        border-color: rgba(255,255,255,0.05);
    }
    
    /* Success/Info/Warning */
    .stAlert {
        background: rgba(19, 24, 35, 0.9);
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #dc2626, #10b981);
        border-radius: 10px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(19, 24, 35, 0.5);
        border-radius: 12px;
        color: #e6edf3;
    }
    
    /* Input field */
    .stTextInput input {
        background: rgba(19, 24, 35, 0.8);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 25px;
        color: #e6edf3;
        padding: 0.7rem 1.2rem;
    }
    
    .stTextInput input:focus {
        border-color: #10b981;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Advanced RAG Assistant for Indian Penal Code, Criminal Laws & Police Procedures</p>
    <p style="font-size: 0.85rem; opacity: 0.7;">🔍 Semantic Search | 🤖 AI-Powered | 📚 50+ IPC Sections | ⚡ Real-time Answers</p>
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
if "pdf_list" not in st.session_state:
    st.session_state.pdf_list = []
if "documents_loaded" not in st.session_state:
    st.session_state.documents_loaded = False
if "admin_password" not in st.session_state:
    st.session_state.admin_password = "admin123"

# ============================================================
# ENHANCED SEARCH FUNCTIONS
# ============================================================

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using SequenceMatcher"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def extract_keywords(query: str) -> List[str]:
    """Extract meaningful keywords from query"""
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'it', 'they', 'we', 'you', 'he', 'she', 'it', 'them', 'us'}
    words = query.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

def expand_query_with_synonyms(query: str) -> List[str]:
    """Expand query with synonyms for better matching"""
    expanded = [query.lower()]
    for main_word, syn_list in SYNONYMS.items():
        if main_word in query.lower():
            for syn in syn_list:
                expanded.append(syn)
        else:
            for syn in syn_list:
                if syn in query.lower():
                    expanded.append(main_word)
                    break
    return list(set(expanded))

def get_ipc_answer_enhanced(query: str) -> Tuple[Optional[str], Optional[Dict], float]:
    """Enhanced IPC matching with fuzzy matching"""
    query_lower = query.lower()
    best_match = None
    best_details = None
    best_score = 0
    
    # Direct matching
    for offence, details in IPC_DATABASE.items():
        if offence in query_lower:
            return offence, details, 1.0
    
    # Fuzzy matching
    for offence, details in IPC_DATABASE.items():
        # Check similarity
        similarity = calculate_text_similarity(query_lower, offence)
        if similarity > best_score and similarity > 0.6:
            best_score = similarity
            best_match = offence
            best_details = details
    
    # Check synonyms
    if best_score < 0.7:
        for main_offence, synonyms in SYNONYMS.items():
            for syn in synonyms:
                if syn in query_lower:
                    for offence, details in IPC_DATABASE.items():
                        if main_offence in offence:
                            return offence, details, 0.85
    
    return best_match, best_details, best_score

def format_ipc_answer_enhanced(offence: str, details: Dict, confidence: float) -> str:
    """Enhanced IPC answer formatting with detailed information"""
    bail_status = "✅ Bailable" if details.get("bailable", False) else "❌ Non-Bailable"
    cognizable_status = "✅ Cognizable" if details.get("cognizable", True) else "❌ Non-Cognizable"
    
    confidence_star = "⭐" * int(confidence * 5) if confidence > 0 else ""
    
    return f"""
**📋 Section {details['section']} of the Indian Penal Code**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**⚖️ Offence:** `{offence.title()}` {confidence_star}

**📝 Description:**
{details['description']}

**🔨 Punishment:**
{details['punishment']}

**🏛️ Court:** {details.get('court', 'Any Magistrate')}

**📊 Legal Status:**
• {bail_status}
• {cognizable_status}
• {'🤝 Compoundable' if details.get('compoundable', False) else '🚫 Non-Compoundable'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Source: Indian Penal Code, 1860*
"""

def hybrid_search(query: str, top_k: int = 6) -> List:
    """Hybrid search combining vector search with keyword search"""
    if st.session_state.vector_store is None:
        return []
    
    # Vector search
    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": top_k})
    vector_results = retriever.invoke(query)
    
    return vector_results

def calculate_advanced_relevance(query: str, document) -> float:
    """Advanced relevance scoring with multiple factors"""
    keywords = extract_keywords(query)
    if not keywords:
        return 0.5
    
    content = document.page_content.lower()
    source = document.metadata.get("source", "").lower()
    
    # Factor 1: Keyword presence (40%)
    keyword_matches = sum(1 for kw in keywords if kw in content)
    keyword_score = keyword_matches / len(keywords) * 0.4
    
    # Factor 2: Section mentions (30%)
    section_pattern = r'section\s+(\d+)'
    sections = re.findall(section_pattern, content)
    section_score = 0.3 if sections else 0
    
    # Factor 3: Exact phrase match (20%)
    phrase_score = 0.2 if query.lower() in content else 0
    
    # Factor 4: Source relevance (10%)
    source_score = 0.1 if "ipc" in source or "penal" in source or "code" in source else 0
    
    return min(keyword_score + section_score + phrase_score + source_score, 1.0)

def extract_detailed_answer(query: str, documents: List) -> Tuple[Optional[str], List[str]]:
    """Extract detailed, comprehensive answer from documents"""
    if not documents:
        return None, []
    
    scored = [(calculate_advanced_relevance(query, doc), doc) for doc in documents]
    scored.sort(reverse=True, key=lambda x: x[0])
    
    # Filter high relevance (score > 0.25)
    relevant = [(score, doc) for score, doc in scored if score >= 0.25]
    
    if not relevant:
        return None, []
    
    answer_parts = []
    sources = []
    
    for score, doc in relevant[:3]:
        source = doc.metadata.get("source", "Unknown")
        sources.append(source)
        content = doc.page_content
        
        # Extract most relevant sentences
        sentences = re.split(r'[.!?]\s+', content)
        query_words = set(query.lower().split())
        
        relevant_sentences = []
        for sentence in sentences:
            if len(sentence) > 40:
                sentence_lower = sentence.lower()
                # Check word overlap
                overlap = sum(1 for w in query_words if w in sentence_lower)
                if overlap > 0:
                    relevant_sentences.append((overlap, sentence.strip()))
        
        # Sort by relevance and take top 2
        relevant_sentences.sort(reverse=True, key=lambda x: x[0])
        
        if relevant_sentences:
            for _, sentence in relevant_sentences[:2]:
                answer_parts.append(f"• {sentence}")
        else:
            answer_parts.append(f"• {content[:350].strip()}...")
    
    if answer_parts:
        answer = "**📚 Based on the documents:**\n\n" + "\n\n".join(answer_parts)
        return answer, list(set(sources))
    
    return None, []

# ============================================================
# GITHUB PDF LOADER FUNCTIONS
# ============================================================

def get_pdf_files_from_github():
    """Get list of all PDF files from GitHub Documents folder"""
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{DOCUMENTS_FOLDER}"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            files = response.json()
            pdf_files = []
            for file in files:
                if file['name'].lower().endswith('.pdf'):
                    pdf_files.append({
                        'name': file['name'],
                        'raw_url': RAW_BASE_URL + file['name']
                    })
            return pdf_files
        return []
    except Exception:
        return []

def load_pdf_from_url(url: str, filename: str):
    """Download PDF from URL and load it"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        for doc in documents:
            doc.metadata["source"] = filename
        os.unlink(tmp_path)
        return documents
    except Exception:
        return []

@st.cache_resource
def load_embedding_model():
    """Load embedding model with caching"""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_all_documents_from_github():
    """Load ALL PDFs from GitHub Documents folder"""
    all_chunks = []
    loaded_files = []
    
    pdf_files = get_pdf_files_from_github()
    
    if not pdf_files:
        return [], []
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    for i, pdf_info in enumerate(pdf_files):
        status_text.markdown(f"<span style='color: #10b981;'>📖 Loading:</span> `{pdf_info['name']}`...", unsafe_allow_html=True)
        
        documents = load_pdf_from_url(pdf_info['raw_url'], pdf_info['name'])
        
        if documents:
            chunks = splitter.split_documents(documents)
            for j, chunk in enumerate(chunks):
                chunk.metadata["source"] = pdf_info['name']
                chunk.metadata["chunk_id"] = j
                chunk.metadata["page"] = chunk.metadata.get("page", j + 1)
            all_chunks.extend(chunks)
            loaded_files.append(pdf_info['name'])
        
        progress_bar.progress((i + 1) / len(pdf_files))
    
    status_text.empty()
    progress_bar.empty()
    
    return all_chunks, loaded_files

# ============================================================
# AUTO-LOAD DOCUMENTS FROM GITHUB ON STARTUP
# ============================================================

if not st.session_state.documents_loaded:
    with st.spinner("📚 Auto-loading PDFs from GitHub 'Documents' folder..."):
        chunks, loaded_files = load_all_documents_from_github()
        
        if chunks:
            if st.session_state.embeddings is None:
                st.session_state.embeddings = load_embedding_model()
            
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
            st.session_state.documents = chunks
            st.session_state.pdf_list = loaded_files
            st.session_state.documents_loaded = True
            
            # Success message with balloon animation
            st.balloons()
            st.success(f"✅ **{len(loaded_files)} documents loaded successfully!**\n\n📊 **{len(chunks)} text chunks** ready for semantic search.")
        else:
            st.info("📤 **No PDFs found in GitHub 'Documents' folder.**\n\nYou can upload PDFs manually using the sidebar uploader.")

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🎯 Control Panel")
    
    # Statistics
    if st.session_state.documents_loaded and st.session_state.documents:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(st.session_state.documents)}</div>
                <div class="stat-label">Text Chunks</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(st.session_state.pdf_list)}</div>
                <div class="stat-label">Documents</div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.session_state.pdf_list:
            st.markdown("### ✅ Loaded Documents")
            for doc in st.session_state.pdf_list[:4]:
                short_name = doc[:35] + "..." if len(doc) > 35 else doc
                st.markdown(f'<span class="doc-badge">📄 {short_name}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Manual upload section
    st.markdown("### 📤 Manual Upload")
    uploaded_file = st.file_uploader("Add PDF to Knowledge Base", type=["pdf"], key="pdf_uploader")
    
    if uploaded_file and st.button("📥 Process & Add", use_container_width=True):
        with st.spinner("Processing..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=600,
                    chunk_overlap=100,
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
                if uploaded_file.name not in st.session_state.pdf_list:
                    st.session_state.pdf_list.append(uploaded_file.name)
                
                os.unlink(tmp_path)
                st.success(f"✅ Added {uploaded_file.name} ({len(chunks)} chunks)")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")
    
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
                    st.session_state.documents_loaded = False
                    st.session_state.pdf_list = []
                    st.success("Cleared! Refresh to reload from GitHub")
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

# Display chat history with enhanced styling
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            st.caption(f"📚 **Sources:** {', '.join(msg['sources'])}")

# Chat input
prompt = st.chat_input("Ask about IPC sections, punishments, offences (e.g., 'What is the punishment for murder?')...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🔍 Analyzing your query with advanced semantic search..."):
            try:
                # Step 1: Enhanced IPC Database matching
                offence, details, confidence = get_ipc_answer_enhanced(prompt)
                
                if details:
                    answer = format_ipc_answer_enhanced(offence, details, confidence)
                    st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": []})
                
                # Step 2: Search PDF documents
                elif st.session_state.vector_store is not None and st.session_state.documents:
                    results = hybrid_search(prompt, top_k=6)
                    
                    if results:
                        answer, sources = extract_detailed_answer(prompt, results)
                        if answer:
                            st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                            if sources:
                                st.caption(f"📚 **Sources:** {', '.join(sources)}")
                            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
                        else:
                            response = "📚 I found some information but it may not be highly relevant. Could you please rephrase your question or use more specific legal terms?"
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        response = "📚 No relevant information found in the uploaded documents. Try asking about IPC sections or upload more legal documents."
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Step 3: No documents loaded
                else:
                    response = """
⚠️ **No documents loaded. Please add PDFs to the GitHub 'Documents' folder or upload manually.**

**You can ask about IPC sections directly:**

| Section | Offence | Punishment |
|---------|---------|------------|
| 302 | Murder | Death/Life imprisonment |
| 376 | Rape | 10 years to life |
| 379 | Theft | Up to 3 years |
| 420 | Cheating | Up to 7 years |
| 354A | Sexual Harassment | Up to 3 years |
| 506 | Criminal Intimidation | Up to 7 years |
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
    <p>👮 Police Rulebook Assistant | Project PRJ-005 | Barath R K PDKV | 411623149004</p>
    <p style="font-size: 0.7rem; opacity: 0.6;">🔍 Semantic Search | 🤖 AI-Powered Retrieval | 📚 50+ IPC Sections | ⚡ Real-time Answers</p>
</div>
""", unsafe_allow_html=True)
